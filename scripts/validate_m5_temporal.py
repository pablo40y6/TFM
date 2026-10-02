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
    TEMPORAL_SPECIES,
    InitializationBlocker,
    NIRForcingTable,
    PhysicalClosureFailure,
    TemporalColumnRHS,
    TemporalPositivityBlocker,
    TemporalState,
    cycle_difference,
    dark_oh_positivity_preflight,
    integrate_reference_cycle,
    local_rhs,
    periodic_spinup,
    qssa_domain_witness,
    reject_nonunique_dark_equilibrium,
    temporal_bootstrap_seeds,
    temporal_rhs,
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
    rhs = TemporalColumnRHS()
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
            return temporal_rhs(time,state,background=local,forcing=dark)
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
        closure = rhs.chemistry(TemporalState(*state),local,dark)
        boundary = state.copy()
        boundary[3] = 0.
        try:
            rhs.chemistry(TemporalState(*boundary),local,dark)
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


def retained_closure_audit(rhs, times, states):
    """Four QSSA only; the OH residual is now its exact temporal derivative."""
    residual_max = family_max = 0.
    for time, column in zip(times, states, strict=True):
        _, forcings = rhs.forcing(time, column)
        for level, forcing in enumerate(forcings):
            c = rhs.chemistry(TemporalState(*column[level]), rhs.locals[level], forcing)
            d, a, r = c.diagnostics, c.algebraic, c.residuals
            residual = [r.res_O1D, r.res_H2O2, r.res_B1, r.res_B0]
            scales = [max(d.P_O1D,d.L_O1D*a.O1D,1e-20),
                      max(d.P_H2O2,d.L_H2O2*a.H2O2,1e-20),
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
    initial = np.empty((51,6))
    golden_max = 0.
    for level, forcing in enumerate(forcings):
        golden = close_local_chemistry(LocalState(*old[level]),rhs.locals[level],forcing)
        initial[level] = [*old[level,:3],golden.algebraic.OH,golden.algebraic.HO2,old[level,4]]
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
    np.savez_compressed(cache/"six-species-onset.npz",time_s=times,state_cm3=trajectories[-1],
                        state_names=TEMPORAL_SPECIES)
    return dict(decision="PASS old dawn blocker crossed",start_time_s=time,end_time_s=19300.,
                golden_algebraic_absolute_max=golden_max,
                BDF_base_tight_relative_max=comparisons[0], BDF_Radau_relative_max=comparisons[1],
                physical_min_cm3=float(trajectories[-1].min()),
                top_OH_HO2_cm3=trajectories[-1][:,-1,3:5].tolist(),time_s=times.tolist(),**audit)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--hitran", type=Path, required=True)
    parser.add_argument("--mode", choices=("periodic", "onset", "positivity-regression", "dark-regression", "domain-regression", "forcing"), default="periodic")
    parser.add_argument("--cache", type=Path, default=Path(".m5-derived-cache"))
    parser.add_argument("--output", type=Path, default=Path("evidence/m5_reference_cycle.npz"))
    parser.add_argument("--seed-cycles-dir", type=Path,
                        help="Reuse local spin-up trajectories; recheck physical closure, period and seeds")
    parser.add_argument("--accelerate-periodic", action="store_true",
                        help="Accelerate positive day-map guesses; certify three consecutive ordinary cycles")
    args = parser.parse_args()
    if args.mode in ("periodic","positivity-regression"):
        print(json.dumps(positivity_preflight(),indent=2))
        return 0 if args.mode == "positivity-regression" else 2
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
    table, audit = prepare_nir(args)
    if args.mode == "forcing":
        print(json.dumps({"decision": "PASS forcing preparation only", "NIR": audit}))
        return 0
    rhs = TemporalColumnRHS(table,progress=lambda t,n,sza:
                             print(f"RHS t={t:.3f}s SZA={sza:.6f} evaluations={n}",file=sys.stderr,flush=True))
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
            with np.load(args.seed_cycles_dir/f"seed-{family}-converged.npz") as saved:
                if ("code_sha256" not in saved or str(saved["code_sha256"]) != code_sha
                        or float(saved["bootstrap_factor"]) != (1.,.1,10.)[family]):
                    raise ValueError("spin-up cache does not match current temporal source / seed family")
                states, times = saved["state"], saved["time"]
                initial = saved["initial"]
                if (states.shape != (len(times),51,6) or not np.all(np.isfinite(states))
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
        def progress(day, error):
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
                        algebraic_cm3=algebraic[:,:,[0,3,4,5]],
                        algebraic_names=["O1D","H2O2","B0","B1"],
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
                      "series":str(args.output), "onset":onset,
                      **retained},indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
