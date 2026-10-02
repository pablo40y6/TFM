"""Frozen periodic reference validation, with optional accepted dark regression."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from types import FunctionType

import numpy as np
from scipy.integrate import solve_ivp

from tfm_photochem.historical_2020 import kinetics
from tfm_photochem.historical_2020.background import load_baseline_background
from tfm_photochem.historical_2020.local_closure import close_local_chemistry
from tfm_photochem.historical_2020.local_types import LocalForcing, LocalState
from tfm_photochem.historical_2020.uv_radiation import (
    compute_uv_photolysis,
    local_forcing_from_uv,
)
from tfm_photochem.m4d_reconstruction.cia import load_cia
from tfm_photochem.m4d_reconstruction.sources import load_bands, load_solar, load_tips
from tfm_photochem.m4d_reconstruction.spectroscopy import SpectralSources
from tfm_photochem.m4d_reconstruction.transfer import VoigtColumn, compute_classic_rates
from tfm_photochem.m5_temporal import (
    DYNAMIC_PEROXIDE_SPECIES as TEMPORAL_SPECIES,
)
from tfm_photochem.m5_temporal import (
    DynamicPeroxideColumnRHS as TemporalColumnRHS,
)
from tfm_photochem.m5_temporal import (
    DynamicPeroxideState as TemporalState,
)
from tfm_photochem.m5_temporal import (
    InitializationBlocker,
    NIRForcingTable,
    PhysicalClosureFailure,
    TemporalPositivityBlocker,
    cycle_difference,
    dark_oh_positivity_preflight,
    integrate_reference_cycle,
    local_rhs,
    periodic_spinup,
    qssa_domain_witness,
    reject_nonunique_dark_equilibrium,
)
from tfm_photochem.m5_temporal import (
    TemporalColumnRHS as HistoricalColumnRHS,
)
from tfm_photochem.m5_temporal import (
    TemporalState as HistoricalState,
)
from tfm_photochem.m5_temporal import (
    dynamic_peroxide_bootstrap_seeds as temporal_bootstrap_seeds,
)
from tfm_photochem.m5_temporal import (
    dynamic_peroxide_rhs as temporal_rhs,
)
from tfm_photochem.m5_temporal import (
    temporal_rhs as historical_rhs,
)


def dark_regression(args) -> int:
    background = load_baseline_background()
    oxygen = background.radiative.msis_O_native_cm3[50:101]
    # This is exactly the accepted unavailable-O boundary convention, a seed
    # for UV opacity only. It does not select an initial dynamic concentration.
    oxygen_seed = np.where(np.isfinite(oxygen), oxygen, 0.0)
    ozone_seed = background.radiative.O3_socrates_reference_cm3[50:101]
    uv = compute_uv_photolysis(oxygen_seed, ozone_seed, 99, background=background)
    indices = np.flatnonzero(~uv.illuminated)
    cases = [(float(background.z_chem_km[i]), 99.0) for i in indices]
    bands = load_bands(args.hitran)
    sources = SpectralSources(
        *load_tips(args.sources / "hapi.py"), load_solar(args.sources / "wehrli85.txt")
    )
    cia = load_cia(args.sources / "O2-O2_2011.cia")
    rates = {
        "gA": compute_classic_rates(bands["A"], sources, cases)["monomer"],
        "gB": compute_classic_rates(bands["B"], sources, cases)["monomer"],
        "gIRA": compute_classic_rates(bands["IRA"], sources, cases, cia=cia)["cia_nominal"],
    }
    evidence = []
    for row, i in enumerate(indices):
        altitude = float(background.z_chem_km[i])
        local_background = background.local_background_at(altitude)
        forcing = local_forcing_from_uv(
            uv, int(i), **{name: float(value[row]) for name, value in rates.items()}
        )
        assert all(value == 0 for value in asdict(forcing).values())
        try:
            reject_nonunique_dark_equilibrium(local_background, forcing, ozone_seed[i])
        except InitializationBlocker as error:
            records = []
            for witness in error.witnesses:
                initial = np.array(list(asdict(witness).values()))
                closure = close_local_chemistry(witness, local_background, forcing)
                solution = solve_ivp(
                    lambda t, y: local_rhs(t, y, background=local_background, forcing=forcing),
                    (0, 86400), initial, method="BDF", rtol=1e-9, atol=1e-8,
                    max_step=3600, jac=np.zeros((5, 5)),
                )
                # Iteration Jacobian only, for exact constant boundary roots.
                # Finite-difference QSSA trials need not be physically admissible;
                # neither this check nor its Jacobian establishes attraction.
                if not solution.success:
                    raise RuntimeError(solution.message)
                departure = float(np.max(np.abs(solution.y - initial[:, None])))
                assert departure == 0.0
                assert np.all(np.isfinite(solution.y)) and np.all(solution.y >= 0)
                records.append({
                    "state_cm3": asdict(witness),
                    "five_tendencies_cm3_s1": asdict(closure.tendencies),
                    "six_QSSA_residuals": asdict(closure.residuals),
                    "BDF_86400s_max_absolute_departure_cm3": departure,
                })
            evidence.append({"altitude_km": altitude, "forcing_s1": asdict(forcing), "roots": records})
        else:
            raise AssertionError("expected nonunique dark equilibrium")
    print(json.dumps({
        "decision": "PASS / accepted nonunique dark continuum regression",
        "policy": "reference_twilight_equilibrium",
        "SZA_deg": 99,
        "direct_forcing": "accepted M4C plus M4D A0/B/IRA with CIA attenuation",
        "nonunique_heights_km": [case[0] for case in cases],
        "equilibrium_family": "[0,c,0,0,0], c>=0",
        "seed_O3_factors": [0.1, 10.0],
        "BDF_persistence_interval_s": 86400,
        "unique_attractor": False,
        "attraction_verification": "fails: distinct O3 perturbations remain at distinct exact roots",
        "witnesses": evidence,
    }, indent=2, allow_nan=False))
    return 0


def prepare_nir(args):
    """Direct rates plus midpoint refinement; derived cache never holds raw HITRAN."""
    bands = load_bands(args.hitran)
    sources = SpectralSources(
        *load_tips(args.sources / "hapi.py"), load_solar(args.sources / "wehrli85.txt")
    )
    cia = load_cia(args.sources / "O2-O2_2011.cia")
    root = Path(__file__).resolve().parents[1]
    code = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (root / "src/tfm_photochem/m4d_reconstruction").glob("*.py")}
    fingerprint = hashlib.sha256(json.dumps(
        {"code": code, "controls": [0.125, 64, 12, 3.84, 4, 0.0625],
         "edition": "verified HITRAN2016/TIPS2017/Wehrli1985/historical CIA"},
        sort_keys=True).encode()).hexdigest()
    args.cache.mkdir(parents=True, exist_ok=True)
    known = {}
    closure = json.loads((root / "evidence/m4d_closure.json").read_text())
    if closure["code_sha256"] == code:
        for angle in (60.0, 85.0, 89.0, 89.9, 95.0, 99.0):
            indices = [closure["cases_z_sza"].index([float(z), angle]) for z in range(50, 101)]
            known[angle] = np.column_stack([
                np.array(closure["rates"][model]["base"][field])[indices]
                for model, field in (("A0", "monomer"), ("B", "monomer"), ("IRA", "cia_nominal"))
            ])
    cache_file = args.cache / f"nir-direct-{fingerprint}.npz"
    if cache_file.exists():
        with np.load(cache_file, allow_pickle=False) as loaded:
            for angle, rates in zip(loaded["sza"], loaded["rates"], strict=True):
                known[float(angle)] = rates

    # Only invariant opacity is persisted, never a state-dependent UV field.
    # Private function namespace leaves the accepted transfer function intact.
    opacity_folder = args.cache / "opacity"
    opacity_folder.mkdir(exist_ok=True)
    class CachedVoigtColumn(VoigtColumn):
        def __post_init__(self):
            # Shell-local profiles are independent. Cache the complete frozen
            # atmosphere once, then select the original active shells on return.
            self.output_shell_mask = self.used_shells
            self.used_shells = None
            super().__post_init__()
            digest = hashlib.sha256(fingerprint.encode())
            for value in (self.nu, self.strength, self.sigma, self.gamma, self.shift, self.gamma2):
                digest.update(np.ascontiguousarray(value).tobytes())
            self.opacity_identity = digest.hexdigest()

        def cross_section(self, nodes, order=8, near_cm1=2.0, exact=False):
            digest = hashlib.sha256(self.opacity_identity.encode())
            digest.update(np.ascontiguousarray(nodes).tobytes())
            digest.update(repr((order, near_cm1, exact)).encode())
            path = opacity_folder / (digest.hexdigest()+".npy")
            if not path.exists():
                value = super().cross_section(nodes, order, near_cm1, exact)
                temporary = path.with_suffix(".tmp")
                with temporary.open("wb") as stream:
                    np.save(stream, value, allow_pickle=False)
                temporary.replace(path)
            value = np.load(path, mmap_mode="r", allow_pickle=False)
            return value if self.output_shell_mask is None else value[:,self.output_shell_mask]
    namespace = dict(compute_classic_rates.__globals__)
    namespace["VoigtColumn"] = CachedVoigtColumn
    cached_rates = FunctionType(compute_classic_rates.__code__, namespace,
                               compute_classic_rates.__name__, compute_classic_rates.__defaults__)

    def evaluate(angles):
        missing = [float(a) for a in angles if float(a) not in known]
        if missing:
            cases = [(float(z), angle) for angle in missing for z in range(50, 101)]
            def band_rate(band):
                result = cached_rates(
                    bands[band], sources, cases, core_order=64, wing_order=12,
                    support=3.84, far_order=4, cia=cia if band == "IRA" else None,
                )
                return result["cia_nominal" if band == "IRA" else "monomer"]
            print(f"Computing direct NIR: {len(missing)} new SZA nodes", file=sys.stderr, flush=True)
            with ThreadPoolExecutor(max_workers=3) as pool:
                columns = list(pool.map(band_rate, ("A", "B", "IRA")))
            values = np.column_stack(columns).reshape(len(missing), 51, 3)
            known.update(zip(missing, values, strict=True))
            ordered = sorted(known)
            np.savez(cache_file, sza=ordered, rates=np.array([known[a] for a in ordered]))
        return np.array([known[float(a)] for a in angles])

    tangent = float(180 - np.degrees(np.arcsin(6370 / 6470)))
    nodes = sorted(set([45.0, 60.0, 75.0, 85.0, 89.0, 89.9, 90.0, 92.0, 94.0,
                        95.0, 96.0, 97.0, 98.0, 99.0, 100.0, tangent, tangent + 1e-7]
                       + (180-np.rad2deg(np.arcsin(6370/(6370+np.arange(50,101))))).tolist()))
    audit = None
    for _ in range(10):
        direct = evaluate(nodes)
        table = NIRForcingTable(nodes, direct)
        middle = 0.5 * (np.array(nodes[1:]) + nodes[:-1])
        reference = evaluate(middle)
        trial = np.array([table(a) for a in middle])
        delta = np.abs(reference - trial)
        floor = np.maximum(1e-15, 1e-4 * np.max(direct, axis=(0, 1)))
        relevant = np.maximum(reference, trial) > floor
        relative = np.divide(delta, np.maximum(reference, floor),
                             out=np.zeros_like(delta), where=relevant)
        bad = np.any((relevant & (relative > .005)) | (~relevant & (delta > 1e-15)), axis=(1, 2))
        audit = dict(nodes=len(nodes), relative_max=float(relative.max()),
                     near_zero_absolute_max_s1=float(np.max(np.where(relevant, 0, delta))),
                     method="direct midpoint audit; adaptive piecewise linear SZA; all 51 tangent nodes; exact shadow")
        print('NIR interpolation audit '+json.dumps(audit), file=sys.stderr, flush=True)
        if not np.any(bad):
            return table, audit
        nodes = sorted(set(nodes + middle[bad].tolist()))
    raise RuntimeError("NIR interpolation refinement did not reach 0.5%")


def positivity_preflight():
    """Mandatory stop: a real retained QSSA obstruction in natural reference night."""
    rhs = HistoricalColumnRHS()
    local = rhs.background.local_background_at(100)
    try:
        dark_oh_positivity_preflight(local)
    except TemporalPositivityBlocker as error:
        evidence = error.evidence
    else:
        raise AssertionError("expected explicit dark OH/peroxide domain obstruction")
    initial = np.asarray(evidence["initial_state_cm3"])
    target = initial[3]*.01
    column = np.broadcast_to(initial,(51,6)).copy()
    _, forcings = rhs.forcing(0.,column)
    dark = forcings[-1]
    assert all(v == 0. for forcing in forcings for v in asdict(forcing).values())
    probes = []
    for method,tolerance in (("BDF",2e-6),("BDF",2e-9),("Radau",2e-9)):
        def derivative(time,state):
            return historical_rhs(time,state,background=local,forcing=dark)
        def event(time,state):
            return state[3]-target
        event.terminal = True
        event.direction = -1
        result = solve_ivp(derivative,(0.,10000.),initial,method=method,rtol=tolerance,
                           atol=[1e-16,1e-16,1e-16,tolerance*1e-3,tolerance,1e-16],
                           max_step=10.,events=event)
        if (not result.success or len(result.t_events[0]) != 1
                or not np.all(np.isfinite(result.y)) or np.any(result.y < 0)):
            raise RuntimeError("independent dark-boundary integration failed")
        time = float(result.t[-1])
        state = result.y[:,-1]
        _, actual = rhs.forcing(time,np.broadcast_to(state,(51,6)))
        assert all(v == 0. for f in actual for v in asdict(f).values())
        closure = rhs.chemistry(HistoricalState(*state),local,dark)
        boundary = state.copy()
        boundary[3] = 0.
        try:
            rhs.chemistry(HistoricalState(*boundary),local,dark)
        except Exception as error:
            from tfm_photochem.historical_2020.qssa import SingularQSSAError
            if not isinstance(error,SingularQSSAError):
                raise
            boundary_error = str(error)
        else:
            raise AssertionError("missing retained H2O2 boundary failure")
        probes.append(dict(method=method,rtol=tolerance,time_s=time,
                           SZA_deg=float(rhs.cycle.sza(time)),state_cm3=state.tolist(),
                           dOH_cm3_s1=float(derivative(time,state)[3]),
                           H2O2_cm3=closure.algebraic.H2O2,boundary_error=boundary_error,
                           nfev=result.nfev))
    spread = max(p["time_s"] for p in probes)-min(p["time_s"] for p in probes)
    assert spread < .005*probes[-1]["time_s"]
    return dict(**evidence,threshold_OH_cm3=target,probes=probes,
                independent_event_time_spread_s=spread,
                forcing="exact natural dark portion of ReferenceEquinoxSolarCycle, all 11 frequencies zero",
                interpretation="Boundary preflight counterexample; not a claim of domain exit in nominal spin-up")


def dynamic_peroxide_preflight():
    """Physical boundaries, retained denominators, and natural-night witness crossing."""
    rhs = TemporalColumnRHS()
    dark = LocalForcing(**{key:0. for key in asdict(BASE_PREFLIGHT_FORCING())})
    rng = np.random.default_rng(7517)
    minimum = np.full(3, np.inf)
    boundary_scaled_min = np.zeros(7)
    for local in rhs.locals:
        for _ in range(12):
            state = 10**rng.uniform(-8,np.log10(local.M)-3,7)
            for forcing in (dark, BASE_PREFLIGHT_FORCING()):
                for index in range(7):
                    trial = state.copy()
                    trial[index] = 0.
                    c = rhs.chemistry(TemporalState(*trial),local,forcing)
                    d = temporal_rhs(0.,trial,background=local,forcing=forcing,chemistry=rhs.chemistry)
                    scale = max(sum(abs(v) for v in c.fluxes.values()),1e-30)
                    boundary_scaled_min[index] = min(boundary_scaled_min[index],d[index]/scale)
                    minimum = np.minimum(minimum,[c.diagnostics.L_O1D,c.diagnostics.L_B0,c.diagnostics.L_B1])
    if np.min(boundary_scaled_min) < -32*np.finfo(float).eps or np.min(minimum)<=0:
        raise RuntimeError("physical positivity / remaining QSSA denominator blocker")
    local = rhs.locals[-1]
    production = float(kinetics.k_ho2_ho2(local.T,local.M)*1000.**2)
    peroxide = 1e-5*local.M
    oh = production/(kinetics.k_oh_h2o2()*peroxide)
    initial = np.array([0.,0.,0.,oh,1000.,peroxide,0.])
    times = np.unique(np.r_[np.linspace(0.,10000.,101),4289.881963453,4333.22845])
    probes = []
    for method,tolerance in (("BDF",2e-6),("BDF",2e-9),("Radau",2e-9)):
        result = solve_ivp(lambda t,y:temporal_rhs(t,y,background=local,forcing=dark),
                           (0.,10000.),initial,method=method,rtol=tolerance,
                           atol=[1e-16,1e-16,1e-16,tolerance*1e-3,tolerance,
                                 tolerance*100.,1e-16],max_step=10.,t_eval=times)
        if not result.success or np.any(result.y<0) or not np.all(np.isfinite(result.y)):
            raise RuntimeError("dynamic peroxide natural-night witness numerical / positivity blocker")
        probes.append(dict(method=method,rtol=tolerance,state_cm3=result.y.T.tolist(),nfev=result.nfev))
    ref = np.array(probes[1]["state_cm3"])
    comparisons = []
    for index in (0,2):
        trial = np.array(probes[index]["state_cm3"])
        relevant = np.maximum(ref,trial)>1e-8
        relative = np.divide(abs(trial-ref),np.maximum(ref,trial),out=np.zeros_like(ref),where=relevant)
        comparisons.append(float(relative.max()))
    if max(comparisons)>.005:
        raise RuntimeError("night crossing convergence exceeds 0.5%")
    for t in times:
        _,forcing = rhs.forcing(t,np.broadcast_to(initial,(51,7)))
        assert all(v==0. for f in forcing for v in asdict(f).values())
    return dict(decision="PASS seven-species positivity / remaining QSSA / dark witness crossing",
                boundary_scaled_min=boundary_scaled_min.tolist(),
                remaining_denominator_min_s1=minimum.tolist(),
                initial_state_cm3=initial.tolist(),time_s=times.tolist(),probes=probes,
                BDF_base_tight_relative_max=comparisons[0],BDF_Radau_relative_max=comparisons[1])


def BASE_PREFLIGHT_FORCING():
    # Nonnegative forcing respecting accepted gross spectral subset bookkeeping.
    return LocalForcing(JH=1e-3,J_SRC=1e-7,J_LYA=1e-8,J_O2_TOTAL=2e-7,
                        J_O3_TOTAL=2e-3,J_H2O2=1e-5,J_H2O_A=1e-8,J_H2O_B=1e-9,
                        gA=1e-8,gB=1e-8,gIRA=1e-8)


def retained_closure_audit(rhs, times, states):
    """Audit the three remaining QSSA, exact shadow and dynamic HOx budget."""
    residual_max = family_max = 0.
    for time, column in zip(times, states, strict=True):
        uv, forcings = rhs.forcing(time, column)
        if any(any(value != 0. for value in asdict(f).values())
               for f,lit in zip(forcings,uv.illuminated,strict=True) if not lit):
            raise RuntimeError("shadow forcing is not exactly zero")
        for level, forcing in enumerate(forcings):
            c = rhs.chemistry(TemporalState(*column[level]), rhs.locals[level], forcing)
            d, a, r = c.diagnostics, c.algebraic, c.residuals
            residual = [r.res_O1D, r.res_B1, r.res_B0]
            scales = [max(d.P_O1D,d.L_O1D*a.O1D,1e-20),
                      max(d.P_B1,d.L_B1*a.B1,1e-20),
                      max(d.P_B0,d.L_B0*a.B0,1e-20)]
            residual_max = max(residual_max,float(np.max(np.abs(residual)/scales)))
            dy = temporal_rhs(time,column[level],background=rhs.locals[level],
                              forcing=forcing,chemistry=rhs.chemistry)
            flux_scale = max(sum(abs(v) for v in c.fluxes.values()),1e-20)
            family_max = max(family_max,abs(dy[3]+dy[4]-c.tendencies.R_H)/flux_scale)
    if residual_max > 1e-10 or family_max > 1e-12:
        raise RuntimeError("retained QSSA / dynamic HOx budget audit failed")
    return dict(retained_QSSA_scaled_max=residual_max, family_budget_scaled_max=family_max)


def onset_validation(rhs, cache):
    """Reproduce the old anchor, then evolve OH/HO2 through the former domain exit."""
    evidence = json.loads((Path(__file__).resolve().parents[1]/
                           "evidence/m5_temporal_evidence.json").read_text())
    anchor = evidence["probe_anchor"]
    time = anchor["time_s"]
    old = np.array(anchor["column_state_cm3"])
    _, forcings = rhs.forcing(time,old)
    initial = np.empty((51,7))
    golden_max = 0.
    for level, forcing in enumerate(forcings):
        golden = close_local_chemistry(LocalState(*old[level]),rhs.locals[level],forcing)
        initial[level] = [*old[level,:3],golden.algebraic.OH,golden.algebraic.HO2,golden.algebraic.H2O2,old[level,4]]
        new = rhs.chemistry(TemporalState(*initial[level]),rhs.locals[level],forcing)
        golden_max = max(golden_max,max(abs(getattr(new.algebraic,k)-v)
                                       for k,v in asdict(golden.algebraic).items()))
    times = np.unique(np.r_[np.linspace(time,19300.,61),19223.755728382974,19260.])
    trajectories = []
    for method, rtol, atol in (("BDF",2e-6,1e-8),("BDF",2e-8,1e-10),("Radau",2e-8,1e-10)):
        solution, states = integrate_reference_cycle(
            rhs,initial,method=method,rtol=rtol,atol_log=atol,start_time_s=time,
            end_time_s=19300.,output_times_s=times,max_step_s=1.)
        trajectories.append(states)
    audit = retained_closure_audit(rhs,times,trajectories[-1])
    comparisons = []
    for trial in (trajectories[0],trajectories[2]):
        comparisons.append(max(float(np.max(cycle_difference(a,b)["relative_max"]))
                               for a,b in zip(trajectories[1],trial,strict=True)))
    if max(comparisons) > .005:
        raise RuntimeError("onset numerical convergence exceeds 0.5%")
    np.savez_compressed(cache/"seven-species-onset.npz",time_s=times,state_cm3=trajectories[-1],
                        state_names=TEMPORAL_SPECIES)
    return dict(decision="PASS old dawn blocker crossed",start_time_s=time,end_time_s=19300.,
                golden_algebraic_absolute_max=golden_max,
                BDF_base_tight_relative_max=comparisons[0], BDF_Radau_relative_max=comparisons[1],
                physical_min_cm3=float(trajectories[-1].min()),
                top_OH_HO2_cm3=trajectories[-1][:,-1,3:5].tolist(),time_s=times.tolist(),**audit)


def periodicity_regression(rhs, args):
    """Replay the observed one-day obstruction with independent solver traces.

    Matching local caches only avoid repeating completed integrations; all
    physical closure, budget, shadow and trajectory comparisons are rechecked.
    An empty cache recomputes the three methods from the consolidated witness.
    """
    evidence = json.loads((Path(__file__).resolve().parents[1]/
                           "evidence/m5_temporal_evidence.json").read_text())
    witness = evidence["blocker"]
    initial = np.array(witness["initial_state_cm3"])
    expected = np.array(witness["reference_end_state_cm3"])
    code_sha = hashlib.sha256((Path(__file__).resolve().parents[1]/
                              "src/tfm_photochem/m5_temporal.py").read_bytes()).hexdigest()
    trajectories, audits, periods = [], [], []
    common_times = None
    for label, method, rtol, atol, step in (("base","BDF",2e-6,1e-8,120.),
                                           ("tight","BDF",2e-8,1e-10,60.),
                                           ("Radau","Radau",2e-8,1e-10,60.)):
        path = args.cache/f"seven-full-day-{label}.npz"
        saved = None
        if path.exists():
            with np.load(path) as data:
                if ("source_sha256" in data and str(data["source_sha256"]) == code_sha
                        and np.array_equal(data["initial"],initial)):
                    saved = (data["time"].copy(),data["state"].copy())
        if saved is None:
            solution, states = integrate_reference_cycle(
                rhs,initial,method=method,rtol=rtol,atol_log=atol,max_step_s=step)
            times = solution.t
            np.savez_compressed(path,initial=initial,time=times,state=states,source_sha256=code_sha)
        else:
            times, states = saved
        if (states.shape != (len(times),51,7) or times[0] != 0 or times[-1] != 86400
                or np.any(np.diff(times)<=0) or not np.all(np.isfinite(states))
                or np.any(states<0)):
            raise RuntimeError("invalid independent witness trajectory")
        np.testing.assert_allclose(states[0],initial,rtol=5e-15,atol=0)
        if common_times is not None and not np.array_equal(times,common_times):
            raise RuntimeError("independent witness time grids differ")
        common_times = times
        audits.append(retained_closure_audit(rhs,times,states))
        periods.append({key:value.tolist() for key,value in cycle_difference(initial,states[-1]).items()})
        if abs(states[-1,35,1]-initial[35,1])/max(states[-1,35,1],initial[35,1])<.5:
            raise RuntimeError("recorded 85-km alternating-day witness not reproduced")
        endpoint = cycle_difference(expected,states[-1])
        if (np.max(endpoint["relative_max"])>.005
                or np.any(endpoint["near_zero_absolute_max"]>.005*endpoint["relevance_floor_cm3"])):
            raise RuntimeError("witness endpoint differs from independent reference")
        trajectories.append(states)
    comparisons = []
    reference = trajectories[1]
    floor = np.maximum(1.,1e-6*np.max(reference,axis=(0,1)))
    for trial in (trajectories[0],trajectories[2]):
        relevant = np.maximum(reference,trial)>floor
        delta = abs(trial-reference)
        relative = np.divide(delta,np.maximum(reference,trial),out=np.zeros_like(delta),where=relevant)
        maximum = np.max(relative,axis=(0,1))
        absolute = np.max(np.where(relevant,0,delta),axis=(0,1))
        if np.any(maximum>.005) or np.any(absolute>.005*floor):
            raise RuntimeError("one-day independent solver convergence exceeds 0.5%")
        comparisons.append(dict(relative_max=maximum.tolist(),near_zero_absolute_max_cm3=absolute.tolist()))
    print(json.dumps(dict(decision="PASS alternating-day obstruction regression",
                         historical_daily_initialization_decision="24-hour initialization failed; no longer an a priori requirement",
                         comparisons=comparisons,periodicity=periods,audits=audits,
                         source_sha256=code_sha),indent=2))
    return 0


def lag_analysis(states):
    """D1..D4 for complete same-solar-phase states; no day-map acceleration."""
    result = []
    for day in range(1, len(states)):
        row = {"ordinary_day": day}
        for lag in range(1, min(4, day)+1):
            row[f"D{lag}"] = {k: v.tolist() for k,v in
                              cycle_difference(states[day-lag],states[day]).items()}
        result.append(row)
    return result


def lag_pass(metric, tolerance=.005):
    relative = np.array(metric["relative_max"])
    absolute = np.array(metric["near_zero_absolute_max"])
    floor = np.array(metric["relevance_floor_cm3"])
    return bool(np.all(relative <= tolerance) and np.all(absolute <= tolerance*floor))


def certify_period2_lags(states):
    """Certification requires stable lag-2/4 and absence of ten-day phase drift."""
    history = lag_analysis(states)
    tail = history[-6:]
    phase_drift = [] if len(states)<12 else [cycle_difference(states[-11],states[-1]),
                                            cycle_difference(states[-12],states[-2])]
    stationary = len(states)>=21 and len(tail)==6 and all("D4" in r and lag_pass(r["D2"]) and
        lag_pass(r["D4"]) and max(r["D1"]["relative_max"])>.02 and
        max(r["D3"]["relative_max"])>.02 for r in tail)
    drift = [{k:v.tolist() for k,v in x.items()} for x in phase_drift]
    return dict(period2_candidate_pass=bool(stationary and len(drift)==2 and
                all(lag_pass(x) for x in drift)),lag_history=history,
                ten_day_phase_drift=drift)


def compare_phase_pairs(reference, trial):
    """Match two full column phases with only a common parity swap allowed."""
    alternatives = []
    for swap in (False,True):
        metrics = [{k:v.tolist() for k,v in cycle_difference(reference[i],
                   trial[1-i if swap else i]).items()} for i in range(2)]
        score = max(max(m["relative_max"])/.005 for m in metrics)
        score = max(score,max(np.max(np.array(m["near_zero_absolute_max"])/
                                    (.005*np.array(m["relevance_floor_cm3"]))) for m in metrics))
        errors = []
        for i,m in enumerate(metrics):
            a,b = np.asarray(reference[i]),np.asarray(trial[1-i if swap else i])
            denominator = np.maximum(np.maximum(a,b),m["relevance_floor_cm3"])
            errors.append((abs(a-b)/(.005*denominator)).ravel())
        rms = float(np.sqrt(np.mean(np.concatenate(errors)**2)))
        alternatives.append(dict(parity_swapped=swap,normalized_max=score,
                                 alignment_rms_normalized=rms,
                                 phases=metrics,pass_=all(lag_pass(m) for m in metrics)))
    valid = [x for x in alternatives if x["pass_"]]
    return min(valid or alternatives,key=lambda x:x["alignment_rms_normalized"])


def assess_ordinary_period2(cache):
    """Finite-horizon lag and phase audit; uncertified patterns stay diagnostics."""
    families, endpoints = [], []
    for family in range(3):
        with np.load(Path(cache)/f"period2-ordinary-family-{family}.npz") as data:
            states = data["endpoints"]
            audits = json.loads(str(data["audits"]))
            previous_index = int(data["previous_map_index"])
            fingerprint = str(data["fingerprint"])
        certificate = certify_period2_lags(states)
        endpoints.append(states[-2:])
        window = states[-11:]
        hydrogen = states[:,:,2]+states[:,:,3]+states[:,:,4]+2*states[:,:,5]
        summary = dict(family=family,ordinary_days=len(states)-1,
            previous_candidate_map_index=previous_index,acceleration=False,
            fingerprint=fingerprint,**certificate,
            physical_audit=dict(finite_nonnegative=all(x["finite_nonnegative"] for x in audits),
                retained_QSSA_scaled_max=max(x["retained_QSSA_scaled_max"] for x in audits),
                family_budget_scaled_max=max(x["family_budget_scaled_max"] for x in audits),
                exact_shadow=True),
            H_100km_first_last_cm3=states[[0,-1],50,2].tolist(),
            hydrogen_inventory_first_last_cm3=hydrogen[[0,-1]].tolist(),
            H_100km_last_ten_day_growth_cm3=float(window[-1,50,2]-window[0,50,2]),
            O3_85km_last_twelve_cm3=states[-12:,35,1].tolist(),
            starting_state_cm3=states[0].tolist(),
            provisional_phase_A_cm3=states[-2].tolist(),provisional_phase_B_cm3=states[-1].tolist())
        families.append(summary)
    if len({x["fingerprint"] for x in families}) != 1:
        raise RuntimeError("seed families used different equations or frozen inputs")
    matches = [dict(family=family,**compare_phase_pairs(endpoints[0],endpoints[family]))
               for family in (1,2)]
    certified = all(x["period2_candidate_pass"] for x in families)
    independent = certified and all(x["pass_"] for x in matches)
    decision = ("period-2 candidate PASS; 48-hour solvers and perturbations still required"
                if independent else "MULTIPLE ATTRACTOR BLOCKER" if certified else
                "NO-GO / period-2 not certified in tested ordinary-day horizon")
    return dict(decision=decision,interpretation="frozen-reference reduced model; no transport",
                families=families,phase_pair_comparisons=matches,
                seed_independence_pass=independent,ordinary_period2_pass=certified,
                trajectory_solver_verification_48h="pending certified candidate",
                perturbation_recovery="pending certified candidate",
                dawn_A_B="not accepted without full attractor certification")


def ordinary_period2_candidate(rhs, cache, family, *, days=30):
    """Continue each original seed lineage using consecutive physical days only.

    Retain every endpoint and trajectory, audit all sampled states, and never
    substitute an extrapolated or algebraically reset endpoint.
    """
    if days < 20:
        raise ValueError("period-2 certification requires at least 20 ordinary days")
    cache = Path(cache)
    identity = hashlib.sha256()
    identity.update((Path(__file__).resolve().parents[1]/
                     "src/tfm_photochem/m5_temporal.py").read_bytes())
    identity.update(np.ascontiguousarray(rhs.nir_provider.sza_deg).tobytes())
    identity.update(np.ascontiguousarray(rhs.nir_provider.rates_s1).tobytes())
    identity.update(json.dumps([asdict(x) for x in rhs.locals],sort_keys=True).encode())
    fingerprint = identity.hexdigest()
    path = cache/f"period2-ordinary-family-{family}.npz"
    if path.exists():
        with np.load(path) as data:
            if str(data["fingerprint"]) != fingerprint:
                raise RuntimeError("ordinary continuation fingerprint changed")
            endpoints = list(data["endpoints"])
            audits = json.loads(str(data["audits"]))
            previous_index = int(data["previous_map_index"])
    else:
        original_checkpoint = cache/f"seven-seed-{family}-latest.npz"
        if original_checkpoint.exists():
            with np.load(original_checkpoint) as data:
                endpoints = [data["state"].copy()]
                previous_index = int(data["day"])
        else:
            evidence = json.loads((Path(__file__).resolve().parents[1]/
                                  "evidence/m5_temporal_evidence.json").read_text())
            retained = evidence["period2_certification"]["families"][family]
            endpoints = [np.array(retained["starting_state_cm3"])]
            previous_index = retained["previous_candidate_map_index"]
        audits = []
    for day in range(len(endpoints),days+1):
        initial = endpoints[-1]
        solution, curve = integrate_reference_cycle(rhs,initial)
        audit = retained_closure_audit(rhs,solution.t,curve)
        audit.update(finite_nonnegative=bool(np.all(np.isfinite(curve)) and np.all(curve>=0)),
                     minimum_cm3=float(curve.min()),nfev=int(solution.nfev),
                     trial_rejections=int(solution.trial_rejections))
        endpoints.append(curve[-1].copy())
        audits.append(audit)
        np.savez_compressed(cache/f"period2-family-{family}-day-{day}.npz",
                            time=solution.t,state=curve,initial=initial,fingerprint=fingerprint)
        np.savez_compressed(path,endpoints=np.array(endpoints),audits=json.dumps(audits),
                            previous_map_index=previous_index,fingerprint=fingerprint)
        row = lag_analysis(endpoints)[-1]
        print("ORDINARY_PERIOD2",family,json.dumps(row),flush=True)
    certificate = certify_period2_lags(endpoints)
    result = dict(family=family,ordinary_days=len(endpoints)-1,previous_map_index=previous_index,
                  acceleration=False,physical_audits=audits,fingerprint=fingerprint,**certificate)
    (cache/f"period2-family-{family}.json").write_text(json.dumps(result,indent=2)+"\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--hitran", type=Path, required=True)
    parser.add_argument("--mode", choices=("periodic", "onset", "positivity-regression", "dark-regression", "domain-regression", "periodicity-regression", "period2-certification", "period2-assessment", "forcing"), default="period2-certification")
    parser.add_argument("--cache", type=Path, default=Path(".m5-derived-cache"))
    parser.add_argument("--family", type=int, choices=(0,1,2), default=0)
    parser.add_argument("--ordinary-days", type=int, default=30)
    parser.add_argument("--output", type=Path, default=Path("evidence/m5_reference_cycle.npz"))
    parser.add_argument("--seed-cycles-dir", type=Path,
                        help="Reuse local spin-up trajectories; recheck physical closure, period and seeds")
    parser.add_argument("--accelerate-periodic", action="store_true",
                        help="Accelerate positive day-map guesses; certify three consecutive ordinary cycles")
    args = parser.parse_args()
    if args.mode == "period2-certification" and args.accelerate_periodic:
        parser.error("period-2 certification uses ordinary physical days only")
    if args.mode == "period2-assessment":
        result = assess_ordinary_period2(args.cache)
        print(json.dumps(result,indent=2))
        return 0 if result["seed_independence_pass"] else 2
    if args.mode == "positivity-regression":
        print(json.dumps(positivity_preflight(),indent=2))
        return 0
    if args.mode == "dark-regression":
        return dark_regression(args)
    if args.mode == "domain-regression":
        from tfm_photochem.historical_2020.qssa import NoPhysicalRootError

        evidence = json.loads((Path(__file__).resolve().parents[1] /
                               "evidence/m5_temporal_evidence.json").read_text())
        background = load_baseline_background()
        cases = evidence["independent_probes"]
        for case in cases:
            state = LocalState(*case["state"])
            local = background.local_background_at(case["z"])
            forcing = LocalForcing(**case["forcing"])
            witness = qssa_domain_witness(state, local, forcing)
            assert witness["sample_count"] == 257 and witness["residual_min"] > 0
            try:
                close_local_chemistry(state, local, forcing)
            except NoPhysicalRootError:
                pass
            else:
                raise AssertionError("original scalar closure no longer rejects the recorded state")
        print(json.dumps({"decision":"PASS recorded OH/HO2 domain-exit regression",
                          "historical_M5_decision":"NO-GO before temporal OH/HO2 relaxation",
                          "independent_cases":len(cases)}))
        return 0
    preflight = dynamic_peroxide_preflight()
    print("Dynamic peroxide preflight "+json.dumps(preflight),file=sys.stderr,flush=True)
    table, audit = prepare_nir(args)
    if args.mode == "forcing":
        print(json.dumps({"decision": "PASS forcing preparation only", "NIR": audit}))
        return 0
    rhs = TemporalColumnRHS(table,progress=lambda t,n,sza:
                             print(f"RHS t={t:.3f}s SZA={sza:.6f} evaluations={n}",file=sys.stderr,flush=True))
    if args.mode == "period2-certification":
        result = ordinary_period2_candidate(rhs,args.cache,args.family,days=args.ordinary_days)
        print(json.dumps(result,indent=2))
        return 0 if result["period2_candidate_pass"] else 2
    if args.mode == "periodicity-regression":
        return periodicity_regression(rhs,args)
    onset = onset_validation(rhs,args.cache)
    print("Onset validation "+json.dumps(onset),file=sys.stderr,flush=True)
    if args.mode == "onset":
        print(json.dumps(onset,indent=2))
        return 0
    def rejected_trial(t, state, step, error, count):
        if count <= 10 or count & (count-1) == 0:
            print(f"Rejected trial {count}: accepted t={t:.12g}s step={step:.6g}s "
                  f"accepted log range=[{state.min():.6g},{state.max():.6g}] cause={error}",
                  file=sys.stderr,flush=True)
    rhs.rejected_trial = rejected_trial
    accepted_count = 0
    def accepted_step(t, state):
        nonlocal accepted_count
        accepted_count += 1
        if accepted_count % 100 == 0:
            np.savez_compressed(args.cache / "latest-accepted-step.npz",
                                time_s=t, log_state=state)
            print(f"Accepted step {accepted_count}: t={t:.12g}s "
                  f"log range=[{state.min():.6g},{state.max():.6g}]",
                  file=sys.stderr,flush=True)
    rhs.accepted_step = accepted_step
    results = []
    if args.seed_cycles_dir is not None:
        common_times = None
        code_sha = hashlib.sha256((Path(__file__).resolve().parents[1]/
                                   "src/tfm_photochem/m5_temporal.py").read_bytes()).hexdigest()
        for family in range(3):
            with np.load(args.seed_cycles_dir/f"seven-seed-{family}-converged.npz") as saved:
                if ("code_sha256" not in saved or str(saved["code_sha256"]) != code_sha
                        or float(saved["bootstrap_factor"]) != (1.,.1,10.)[family]):
                    raise ValueError("spin-up cache does not match current temporal source / seed family")
                states, times = saved["state"], saved["time"]
                initial = saved["initial"]
                if (states.shape != (len(times),51,7) or not np.all(np.isfinite(states))
                        or np.any(states <= 0) or times[0] != 0 or times[-1] != 86400
                        or not np.all(np.isfinite(times)) or np.any(np.diff(times) <= 0)):
                    raise ValueError("invalid locally generated spin-up trajectory")
                if common_times is not None and not np.array_equal(times,common_times):
                    raise ValueError("seed trajectories require the same reference time grid")
                common_times = times.copy()
                np.testing.assert_allclose(states[0],initial,rtol=5e-15,atol=0)
                error = cycle_difference(initial,states[-1])
                if (np.max(error["relative_max"]) > .001
                        or np.max(error["near_zero_absolute_max"]) > 1.):
                    raise RuntimeError("cached trajectory is not periodic")
                retained_closure_audit(rhs,times,states)
                results.append(dict(cycles=int(saved["cycles"]),state=states,
                                    convergence=[error],
                                    acceleration=bool(saved["acceleration"]) if "acceleration" in saved else False,
                                    certification_cycles=int(saved["certification_cycles"])
                                    if "certification_cycles" in saved else 1))
                if results[-1]["acceleration"] and results[-1]["certification_cycles"] < 3:
                    raise RuntimeError("accelerated guesses require three ordinary certification cycles")
    for family, seed in enumerate(() if results else temporal_bootstrap_seeds(rhs)):
        last_error = {}
        def progress(day, error):
            last_error.update(day=day,comparison={key:value.tolist() for key,value in error.items()})
            print(f"Seed {family} day {day}: relative={error['relative_max'].tolist()}",
                  file=sys.stderr, flush=True)
        try:
            results.append(periodic_spinup(rhs, seed, progress=progress,
                                           acceleration=args.accelerate_periodic))
        except PhysicalClosureFailure as error:
            print(json.dumps({"decision": "NO-GO / physical QSSA domain failure",
                              "seed_family": family, "time_s": error.time_s,
                              "SZA_deg": float(rhs.cycle.sza(error.time_s)),
                              "altitude_km": error.altitude_km,
                              "physical_state_cm3": error.state.tolist(),
                              "forcing_s1": asdict(error.forcing),
                              "cause": str(error.cause), "NIR": audit, "onset":onset,
                              "species":TEMPORAL_SPECIES}, indent=2))
            return 2
        except RuntimeError as error:
            if "cycle convergence not attained" not in str(error):
                raise
            print(json.dumps(dict(decision="NO-GO / 24-hour periodic initialization not certified",
                                  seed_family=family,last_cycle=last_error,
                                  interpretation="Finite-horizon failure; not a proof that no mathematical periodic orbit exists",
                                  NIR=audit,onset=onset),indent=2))
            return 2

    def comparison(reference, trial):
        floor = np.maximum(1.0, 1e-6*np.max(reference, axis=(0,1)))
        relevant = np.maximum(reference,trial) > floor
        delta = np.abs(trial-reference)
        relative = np.divide(delta,np.maximum(reference,trial),
                             out=np.zeros_like(delta),where=relevant)
        absolute = np.max(np.where(relevant,0,delta),axis=(0,1))
        maximum = np.max(relative,axis=(0,1))
        return {"relative_max":maximum.tolist(), "near_zero_absolute_max_cm3":absolute.tolist(),
                "floor_cm3":floor.tolist(),
                "pass":bool(np.all(maximum<=.005) and np.all(absolute<=.005*floor))}
    reference = results[0]["state"]
    seed_comparison = [comparison(reference,r["state"]) for r in results[1:]]
    if not all(r["pass"] for r in seed_comparison):
        print(json.dumps({"decision":"PERIODIC INITIALIZATION BLOCKER: seed-dependent cycles",
                          "seed_comparison":seed_comparison},indent=2))
        return 2
    initial = reference[-1]
    _, baseline = integrate_reference_cycle(rhs,initial)
    _, tighter = integrate_reference_cycle(rhs,initial,rtol=2e-8,atol_log=1e-10,max_step_s=60)
    solution, independent = integrate_reference_cycle(rhs,initial,method="Radau",rtol=2e-8,
                                                       atol_log=1e-10,max_step_s=60)
    final_periodicity = [cycle_difference(initial,trajectory[-1])
                        for trajectory in (baseline,tighter,independent)]
    if any(np.max(error["relative_max"]) > .001
           or np.max(error["near_zero_absolute_max"]) > 1. for error in final_periodicity):
        raise RuntimeError("reference cycle is not periodic under current RHS / independent solvers")
    tolerance_check = comparison(baseline,tighter)
    radau_check = comparison(tighter,independent)
    if not tolerance_check["pass"] or not radau_check["pass"]:
        print(json.dumps({"decision":"NO-GO solver convergence","tighter":tolerance_check,
                          "Radau":radau_check},indent=2))
        return 2
    algebraic = np.empty((len(solution.t),51,6))
    frequencies = np.empty((len(solution.t),51,11))
    hydrogen_budget_max = 0.0
    for time_index, (time_s, state) in enumerate(zip(solution.t,independent,strict=True)):
        uv, forcings = rhs.forcing(time_s,state)
        for level, forcing in enumerate(forcings):
            closure = rhs.chemistry(TemporalState(*state[level]),rhs.locals[level],forcing)
            algebraic[time_index,level]=list(asdict(closure.algebraic).values())
            frequencies[time_index,level]=list(asdict(forcing).values())
            f=closure.fluxes
            budget=2*(f['H2O2_PHOTOLYSIS']+f['H2O_PHOTOLYSIS_A']+f['O1D_H2O']+f['O1D_H2']
                      -f['H_HO2_H2O_O']-f['H_HO2_H2_O2']-f['OH_OH']-f['OH_HO2']-f['HO2_HO2'])
            actual=closure.tendencies.H+closure.tendencies.R_H
            hydrogen_budget_max=max(hydrogen_budget_max,abs(actual-budget)/
                                    max(abs(actual),abs(budget),sum(abs(v) for v in f.values()),1e-20))
        assert np.all(frequencies[time_index,~uv.illuminated]==0)
    retained = retained_closure_audit(rhs,solution.t,independent)
    if hydrogen_budget_max>1e-12:
        raise RuntimeError("QSSA/family budget failed")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(args.output,time_s=solution.t,altitude_km=rhs.background.z_chem_km,
                        sza_deg=rhs.cycle.sza(solution.t),state_cm3=independent,
                        state_names=TEMPORAL_SPECIES,R_H_cm3=independent[:,:,3]+independent[:,:,4],
                        algebraic_cm3=algebraic[:,:,[0,4,5]],
                        algebraic_names=["O1D","B0","B1"],
                        forcing_s1=frequencies,forcing_names=list(asdict(forcings[0])),
                        dawn_window_s=rhs.cycle.dawn_window_s())
    print(json.dumps({"decision":"GO M5A","cycles":[r["cycles"] for r in results],
                      "day_map_acceleration":[r["acceleration"] for r in results],
                      "ordinary_certification_cycles":[r["certification_cycles"] for r in results],
                      "final_solver_periodicity":[{k:v.tolist() for k,v in error.items()}
                                                   for error in final_periodicity],
                      "cycle_to_cycle":[{k:v.tolist() for k,v in r["convergence"][-1].items()} for r in results],
                      "seed_comparison":seed_comparison,"tighter_BDF":tolerance_check,
                      "BDF_Radau":radau_check,
                      "hydrogen_budget_max":hydrogen_budget_max,"NIR":audit,
                      "series":str(args.output), "onset":onset, "preflight":preflight,
                      **retained},indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
