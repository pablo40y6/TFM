"""Run the final thesis campaign with the accepted model; never alter chemistry.

Local atmosphere/NIR/full-run caches are restartable and deliberately untracked.
Only compact dawn fields, configurations and provenance are published.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import platform
import subprocess
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from scipy.optimize import brentq, minimize_scalar

from scripts.validate_m5_temporal import retained_closure_audit
from tfm_photochem.dynamic_atmosphere import DynamicMSISAtmosphere
from tfm_photochem.dynamic_radiation import DynamicNIRForcing, HistoricalNIRInputs
from tfm_photochem.m5_dynamic import DynamicAtmosphereColumnRHS, previous_solar_noon
from tfm_photochem.m5_simulation import SimulationResult, simulate
from tfm_photochem.m5_temporal import DynamicPeroxideState
from tfm_photochem.solar_geometry import DatetimeSolarGeometry

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "6637b20eb4dafa35d68c766ff4370241c750def2"
TAG = "tfm-temporal-model-v1"
CASES = {
    "reference": ("2020-03-20", 45.),
    "summer": ("2020-06-21", 45.),
    "autumn": ("2020-09-22", 45.),
    "winter": ("2020-12-21", 45.),
    "equatorial": ("2020-03-20", 0.),
    "high_latitude": ("2020-03-20", 70.),
}
CONTROLS = dict(method="BDF", rtol=2e-6, atol=1e-8,
                max_step_s=120., output_step_s=300.)
TIME_FIX_HELPER_AST = "acb7d425d490d8209f500b68a8d1ddbe6d3d92f72aa9fd07aef1ddb0367941ea"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def background_key(background):
    digest = hashlib.sha256()
    for field in ("T_K", "M_cm3", "O2_model_cm3", "N2_model_cm3"):
        digest.update(np.ascontiguousarray(getattr(background.radiative, field)).tobytes())
    return digest.hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def scenario(name):
    """Find next dawn and its actual attainable SZA interval, with no extrapolation."""
    date, lat = CASES[name]
    start = datetime.fromisoformat(date).replace(hour=20, tzinfo=timezone.utc)
    clock = DatetimeSolarGeometry(start, lat, 0.)
    minimum = minimize_scalar(clock.sza, bounds=(12*3600., 18*3600.),
                              method="bounded", options={"xatol": 1e-5})
    night = minimize_scalar(lambda t: -float(clock.sza(t)), bounds=(0., 8*3600.),
                            method="bounded")
    dawn = brentq(lambda t: float(clock.sza(t))-99., night.x, minimum.x)
    if minimum.fun <= 60.:
        end_s = brentq(lambda t: float(clock.sza(t))-60., dawn, minimum.x)
    else:
        end_s = float(minimum.x)
    end = start + timedelta(seconds=end_s)
    return dict(case=name, date=date, latitude_deg=lat, longitude_deg_east=0.,
                start_datetime_utc=start.isoformat(), end_datetime_utc=end.isoformat(),
                previous_noon_utc=previous_solar_noon(start, 0.).isoformat(),
                dawn_start_utc=(start+timedelta(seconds=dawn)).isoformat(),
                attainable_minimum_sza_deg=float(minimum.fun),
                reaches_sza60=bool(minimum.fun <= 60.), atmosphere="dynamic_msis",
                initialization="reference_noon; approximate bootstrap, not climatology",
                activity=dict(F107=150., F107a=150., Ap=4.),
                background_step_s=300., NIR_step_s=3600., solver=CONTROLS,
                baseline_git_sha=BASELINE, baseline_tag=TAG)


def load_result(path):
    with np.load(path, allow_pickle=False) as data:
        extras = {k: data[k].copy() for k in data.files
                  if k.startswith(("background_", "radiative_"))}
        return SimulationResult(*(data[k].copy() for k in
            ("time_s", "altitude_km", "sza_deg", "state_cm3", "R_H_cm3",
             "algebraic_cm3", "forcing_s1")), tuple(data["forcing_names"]),
            json.loads(str(data["metadata"])), extras or None)


def compact_metadata(metadata):
    """Keep initializer certification, avoiding duplication of full NPZ seed logs."""
    result = json.loads(json.dumps(metadata))
    record = result.get("initialization", {})
    levels = record.pop("levels", None)
    if levels:
        record["multiseed_certification"] = dict(levels=len(levels),
            minimum_physical_convergences=min(sum(seed["passed"] for seed in row["seeds"])
                                              for row in levels),
            maximum_root_relative_spread=max(row["root_relative_spread"] for row in levels),
            maximum_normalized_residual=max(seed["normalized_residual"] for row in levels
                                           for seed in row["seeds"] if seed["passed"]),
            full_seed_log="preserved in canonical NPZ metadata")
    return result


def normalized_source_proof():
    """Require identical scientific Python ASTs to the accepted M5C commit.

    The consolidated checkout changes line endings. This is an explicit proof,
    not a rewrite of historical byte fingerprints.
    """
    proofs = {}
    for path in sorted((ROOT / "src/tfm_photochem").rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        historical = subprocess.check_output(
            ["git", "show", f"dbb5878:{relative}"], cwd=ROOT).decode("utf8")
        current = path.read_text(encoding="utf8")
        old_ast = ast.dump(ast.parse(historical), include_attributes=False)
        current_tree = ast.parse(current)
        new_ast = ast.dump(current_tree, include_attributes=False)
        roundoff_fix = False
        if old_ast != new_ast and path.name in ("dynamic_atmosphere.py", "dynamic_radiation.py"):
            # Explicit compatibility exception for the demonstrated one-ULP
            # datetime bug; remove ONLY the fingerprinted helper and its calls.
            roundoff_fix = True
            if path.name == "dynamic_atmosphere.py":
                helper = next(n for n in current_tree.body if isinstance(n,ast.FunctionDef)
                              and n.name=="_time_within_coverage")
                digest = hashlib.sha256(ast.dump(helper,include_attributes=False).encode()).hexdigest()
                if digest != TIME_FIX_HELPER_AST:
                    raise ValueError("time normalization helper changed beyond reviewed patch")
                current_tree.body.remove(helper)
                target_class, target_method = "DynamicMSISAtmosphere", "raw_at"
                call = "time_s = _time_within_coverage(time_s, 0., self.times[-1])"
            else:
                helper_import = next(n for n in current_tree.body if isinstance(n,ast.ImportFrom)
                                     and n.module=="dynamic_atmosphere"
                                     and [a.name for a in n.names]==["_time_within_coverage"])
                current_tree.body.remove(helper_import)
                target_class, target_method = "DynamicNIRForcing", "__call__"
                call = "time_s = _time_within_coverage(time_s, times[0], times[-1])"
            cls = next(n for n in current_tree.body if isinstance(n,ast.ClassDef) and n.name==target_class)
            method = next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==target_method)
            expected = ast.dump(ast.parse(call).body[0],include_attributes=False)
            matches = [n for n in method.body if ast.dump(n,include_attributes=False)==expected]
            if len(matches)!=1:
                raise ValueError("time normalization call does not match reviewed patch")
            method.body.remove(matches[0])
        comparable_ast = ast.dump(current_tree, include_attributes=False)
        if old_ast != comparable_ast:
            raise ValueError(f"accepted scientific source differs: {relative}")
        proofs[relative] = dict(current_bytes_sha256=sha(path),
            historical_bytes_sha256=hashlib.sha256(historical.encode()).hexdigest(),
            AST_sha256=hashlib.sha256(new_ast.encode()).hexdigest(),
            accepted_AST_sha256=hashlib.sha256(old_ast.encode()).hexdigest(),
            one_ULP_datetime_fix_only=roundoff_fix)
    return proofs


def audit_result(result, provider, nir, start):
    states = result.state_cm3
    if not np.all(np.isfinite(states)) or np.any(states < 0):
        raise ValueError("nonphysical trajectory")
    np.testing.assert_array_equal(result.R_H_cm3, states[:, :, 3]+states[:, :, 4])
    if not np.all(np.isfinite(result.algebraic_cm3)) or np.any(result.algebraic_cm3 < 0):
        raise ValueError("nonphysical algebraic species")
    if not np.all(np.isfinite(result.forcing_s1)) or np.any(result.forcing_s1 < 0):
        raise ValueError("nonphysical forcing")
    clock = DatetimeSolarGeometry(start, provider.latitude, provider.longitude)
    rhs = DynamicAtmosphereColumnRHS(provider, nir, clock,
        offset_s=(start-provider.start).total_seconds())
    audit = retained_closure_audit(rhs, result.time_s, states)
    for i, (t, column) in enumerate(zip(result.time_s, states, strict=True)):
        _, frequencies = rhs.forcing(float(t), column)
        expected = np.array([[asdict(f)[name] for name in result.forcing_names] for f in frequencies])
        np.testing.assert_array_equal(expected, result.forcing_s1[i])
        if result.background_fields:
            for field in ("T_K", "M_cm3", "O2_cm3", "N2_cm3", "CO2_cm3", "H2O_cm3", "H2_cm3"):
                np.testing.assert_array_equal(result.background_fields["background_"+field][i],
                                              getattr(rhs.background.chemical, field))
    tangent = 180-np.rad2deg(np.arcsin(6370/(6370+result.altitude_km)))
    shadow = result.sza_deg[:, None] > tangent[None, :]
    if np.any(result.forcing_s1[shadow] != 0):
        raise ValueError("shadow forcing must be exactly zero")
    audit.update(finite_nonnegative=True, exact_R_H=True, algebraic_physical=True,
                 exact_shadow=True, no_clipping_or_state_reset=True,
                 stored_forcing_recomputed_bitwise=True,
                 stored_chemical_background_recomputed_bitwise=bool(result.background_fields),
                 output_samples=len(result.time_s))
    return audit


def dawn_subset(result, config, rhs):
    """Retain native time samples and explicit SZA99 boundary by interpolation.

    Tables describe interpolation of saved outputs, not a new chemistry solve.
    The final SZA60/minimum boundary is an actual integration endpoint.
    """
    start = datetime.fromisoformat(config["start_datetime_utc"])
    boundary = (datetime.fromisoformat(config["dawn_start_utc"])-start).total_seconds()
    times = np.r_[boundary, result.time_s[result.time_s > boundary]]

    def interpolate(a):
        return np.stack([np.interp(times, result.time_s, column)
                         for column in a.reshape(len(a), -1).T], axis=1).reshape(
                             (len(times),)+a.shape[1:])

    states = interpolate(result.state_cm3)
    metadata = dict(result.metadata, campaign=config,
        saved_output_interpolation="linear time interpolation only at SZA99 boundary",
        absolute_time_origin_utc=start.isoformat())
    algebraic = interpolate(result.algebraic_cm3)
    forcing = interpolate(result.forcing_s1)
    # Reevaluate accepted radiation and QSSA at the interpolated boundary state.
    # Interpolating forcing across a shell tangent would smear exact shadow.
    _, frequencies = rhs.forcing(float(times[0]), states[0])
    forcing[0] = [[asdict(f)[name] for name in result.forcing_names] for f in frequencies]
    for j, (state, bg, f) in enumerate(zip(states[0], rhs.locals, frequencies, strict=True)):
        closure = rhs.chemistry(DynamicPeroxideState(*state), bg, f)
        a = closure.algebraic
        algebraic[0, j] = a.O1D, a.B0, a.B1
    backgrounds = {k: interpolate(v) if k != "radiative_altitude_km" else v.copy()
                   for k, v in (result.background_fields or {}).items()}
    # Background interpolation knots need not coincide with output-time knots.
    # Preserve the exact accepted provider at the new boundary, just like forcing.
    if backgrounds:
        case = rhs.background
        for field in ("T_K", "M_cm3", "O2_cm3", "N2_cm3", "CO2_cm3", "H2O_cm3", "H2_cm3"):
            backgrounds["background_"+field][0] = getattr(case.chemical, field)
        backgrounds["radiative_background_T_K"][0] = case.radiative.T_K
        backgrounds["radiative_background_M_cm3"][0] = case.radiative.M_cm3
        backgrounds["radiative_O3_reference_cm3"][0] = case.radiative.O3_socrates_reference_cm3
        raw = rhs.atmosphere_provider.raw_at(float(times[0])+rhs.atmosphere_offset_s)
        backgrounds["radiative_MSIS_O_native_cm3"][0] = raw[:,3]*1e-6
        backgrounds["radiative_MSIS_H_native_cm3"][0] = raw[:,5]*1e-6
    return SimulationResult(times, result.altitude_km,
        DatetimeSolarGeometry(start, config["latitude_deg"], 0.).sza(times), states,
        states[:, :, 3]+states[:, :, 4], algebraic,
        forcing, result.forcing_names, metadata,
        backgrounds or None)


def run_case(args):
    name = args.case
    config = scenario(name)
    write_json(ROOT / f"results/configs/{name}.json", config)
    cache = args.cache / name
    cache.mkdir(parents=True, exist_ok=True)
    start = datetime.fromisoformat(config["start_datetime_utc"])
    end = datetime.fromisoformat(config["end_datetime_utc"])
    begin = datetime.fromisoformat(config["previous_noon_utc"])
    reused = []
    proof = None
    old_result = None
    # Keep the accepted reference grid's origin and unchanged snapshots.
    if name == "reference" and args.accepted_cache is not None:
        proof = normalized_source_proof()
        begin = datetime(2020, 3, 20, 12, tzinfo=timezone.utc)
        old_result = load_result(args.accepted_cache / "bootstrap-reference.npz")
        if (old_result.metadata["initialization"]["noon_datetime_utc"] !=
                config["previous_noon_utc"]):
            raise ValueError("reference initializer mismatch")
        start = datetime.fromisoformat(old_result.metadata["start_datetime_utc"])
        if start.isoformat() != config["start_datetime_utc"]:
            raise ValueError("reference start mismatch")
        reused.append(dict(path="accepted M5C local bootstrap-reference.npz",
                           sha256=sha(args.accepted_cache / "bootstrap-reference.npz")))
    raw_path = cache / "atmosphere.npz"
    raw = None
    if raw_path.exists():
        with np.load(raw_path, allow_pickle=False) as d:
            raw = d["raw"]
            if str(d["config_sha256"]) != sha(ROOT/f"results/configs/{name}.json"):
                raise ValueError("cached atmosphere config mismatch")
    provider = DynamicMSISAtmosphere(begin, end, config["latitude_deg"], 0.,
                                     step_s=300., raw=raw)
    if old_result is not None:
        with np.load(args.accepted_cache / "atmosphere-300.npz") as d:
            np.testing.assert_array_equal(provider.raw[:len(d["raw"])], d["raw"])
    if raw is None:
        np.savez_compressed(raw_path, raw=provider.raw,
                           config_sha256=sha(ROOT/f"results/configs/{name}.json"))
    snapshots = provider.sampled(3600.)
    geometry = DatetimeSolarGeometry(begin, config["latitude_deg"], 0.)
    nir_path = cache / "nir.npz"
    if nir_path.exists():
        nir = DynamicNIRForcing.load(nir_path, snapshots, geometry)
    else:
        inputs = HistoricalNIRInputs(args.sources, args.hitran)
        reused_tables = {}
        if old_result is not None:
            old_end = datetime.fromisoformat(old_result.metadata["end_datetime_utc"])
            with np.load(args.accepted_cache / "atmosphere-300.npz") as d:
                old_provider = DynamicMSISAtmosphere(begin, old_end, 45., 0.,
                                                     step_s=300., raw=d["raw"])
            old_nir = DynamicNIRForcing.load(args.accepted_cache / "nir-3600.npz",
                                            old_provider.sampled(3600.), geometry)
            for t, table, audit in zip(old_nir.atmosphere.times, old_nir.tables,
                                        old_nir.audits, strict=True):
                digest = background_key(old_nir.atmosphere.at(float(t)))
                reused_tables[digest] = (table, audit)
            reused.append(dict(path="accepted M5C local nir-3600.npz",
                               sha256=sha(args.accepted_cache / "nir-3600.npz")))

        class ReusingAcceptedTables(DynamicNIRForcing):
            def _build(self, background, nodes):
                # Four unchanged fields entirely determine the NIR background.
                key = background_key(background)
                if key in reused_tables:
                    table, audit = reused_tables[key]
                    if nodes[0] >= table.sza_deg[0] and nodes[-1] <= table.sza_deg[-1]:
                        return table, dict(audit, reused_accepted_table=True)
                return super()._build(background, nodes)

        nir = ReusingAcceptedTables(snapshots, geometry, inputs, cache=cache / "profiles",
            progress=lambda i, n, a: print(json.dumps(dict(case=name, snapshot=i,
                total=n, audit=a)), flush=True))
        nir.save(nir_path)
    full_path = cache / "full.npz"
    if full_path.exists():
        result = load_result(full_path)
    elif old_result is not None:
        old_end = datetime.fromisoformat(old_result.metadata["end_datetime_utc"])
        extension = simulate(old_end, end, 45., 0., old_result.state_cm3[-1],
            atmosphere="dynamic_msis", atmosphere_provider=provider, dynamic_nir=nir,
            initialization_metadata=dict(policy="continuation of accepted automatic reference bootstrap"),
            **CONTROLS)
        shift = (old_end-start).total_seconds()
        result = SimulationResult(np.r_[old_result.time_s, extension.time_s[1:]+shift],
            old_result.altitude_km, np.r_[old_result.sza_deg, extension.sza_deg[1:]],
            np.concatenate([old_result.state_cm3, extension.state_cm3[1:]]),
            np.concatenate([old_result.R_H_cm3, extension.R_H_cm3[1:]]),
            np.concatenate([old_result.algebraic_cm3, extension.algebraic_cm3[1:]]),
            np.concatenate([old_result.forcing_s1, extension.forcing_s1[1:]]),
            old_result.forcing_names, dict(old_result.metadata,
                end_datetime_utc=end.isoformat(), continuation_solver=extension.metadata["solver"]),
            {k: np.concatenate([v, extension.background_fields[k][1:]])
             if v.shape[0] == len(old_result.time_s) else v
             for k, v in old_result.background_fields.items()})
        result.save(full_path)
    else:
        result = simulate(start, end, config["latitude_deg"], 0.,
            initialization="reference_noon", atmosphere="dynamic_msis",
            atmosphere_provider=provider, dynamic_nir=nir, **CONTROLS,
            progress=lambda t, n, s: print(json.dumps(dict(case=name, time_s=t,
                                          nfev=n, SZA_deg=s)), flush=True))
        result.save(full_path)
    audit = audit_result(result, provider, nir, start)
    output = ROOT / f"results/tables/{name}_dawn.npz"
    output.parent.mkdir(parents=True, exist_ok=True)
    rhs = DynamicAtmosphereColumnRHS(provider, nir,
        DatetimeSolarGeometry(start, config["latitude_deg"], 0.),
        offset_s=(start-provider.start).total_seconds())
    dawn = dawn_subset(result, config, rhs)
    dawn_audit = audit_result(dawn, provider, nir, start)
    dawn.save(output)
    with np.load(output, allow_pickle=False) as data:
        fields = {k: data[k].copy() for k in data.files}
    fields["datetime_utc"] = [(start+timedelta(seconds=float(t))).isoformat() for t in dawn.time_s]
    np.savez_compressed(output, **fields)
    fingerprints = {p.name: sha(p) for p in [args.hitran, args.sources / "hapi.py",
        args.sources / "wehrli85.txt", args.sources / "O2-O2_2011.cia"]}
    write_json(ROOT/f"results/manifests/{name}.json", dict(config=config, QA=audit, dawn_QA=dawn_audit,
        production_git_sha=subprocess.check_output(["git", "rev-parse", "HEAD"],cwd=ROOT).decode().strip(),
        publication_runner_sha256=sha(Path(__file__)), accepted_model_git_sha=BASELINE,
        software=dict(python=platform.python_version(), numpy=np.__version__,
                      scipy=__import__("scipy").__version__, pymsis="0.12.0"),
        external_sources_sha256=fingerprints, reused_accepted_artifacts=reused,
        scientific_source_compatibility=proof, full_local_output_sha256=sha(full_path),
        output=dict(path=output.relative_to(ROOT).as_posix(), sha256=sha(output),
                    bytes=output.stat().st_size), full_trajectory_metadata=compact_metadata(result.metadata)))
    print(json.dumps(dict(case=name, status="PASS", QA=audit)), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--cache", type=Path, default=ROOT / "work/final-results")
    parser.add_argument("--accepted-cache", type=Path)
    parser.add_argument("--sources", type=Path)
    parser.add_argument("--hitran", type=Path)
    args = parser.parse_args()
    if args.plan:
        for name in CASES:
            config = scenario(name)
            write_json(ROOT/f"results/configs/{name}.json", config)
            print(json.dumps(config))
        return
    if not args.case or args.sources is None or args.hitran is None:
        parser.error("execution requires --case, --sources and authorized --hitran")
    run_case(args)


if __name__ == "__main__":
    main()
