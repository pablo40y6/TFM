"""One full-domain M4D closure audit under the explicitly revised user policy.

Raw HITRAN and historical tables stay local. Cache is derived rates only and
keyed by code, source identities, cases and controls; it is not evidence itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from tfm_photochem.m4d_reconstruction.cia import load_cia
from tfm_photochem.m4d_reconstruction.mapping import parse_drouin, parse_supplement
from tfm_photochem.m4d_reconstruction.sources import (
    SOURCE_IDENTITIES,
    load_bands,
    load_solar,
    load_tips,
)
from tfm_photochem.m4d_reconstruction.spectroscopy import SpectralSources
from tfm_photochem.m4d_reconstruction.transfer import (
    VoigtColumn,
    atmosphere,
    compute_classic_rates,
    path_lengths,
)

FLOOR = 1e-15  # s^-1; relative comparisons below this have no stable meaning.
TOL = 0.005


def stats(reference, trial, cases):
    a, b = np.asarray(reference), np.asarray(trial)
    floor = max(FLOOR, 1e-4 * float(a.max()))
    relevant = np.maximum(a, b) > floor
    delta = np.abs(b - a)
    relative = delta[relevant] / a[relevant]
    indices = np.flatnonzero(relevant)
    maximum = indices[np.argmax(relative)] if len(indices) else 0
    return {
        "relevance_floor_s1": floor,
        "relevance_definition": "max(1e-15 s^-1, 0.01% of reference band maximum)",
        "relative_max": float(relative.max()) if len(relative) else 0.0,
        "relative_p50_p90_p99": np.percentile(relative, [50, 90, 99]).tolist()
        if len(relative)
        else [0.0] * 3,
        "maximum_case_z_sza": list(cases[maximum]),
        "maximum_case_reference_trial_s1": [float(a[maximum]), float(b[maximum])],
        "relevant_cases": int(relevant.sum()),
        "absolute_max_s1": float(delta.max()),
        "absolute_max_fraction_of_reference_peak": float(delta.max() / a.max())
        if a.max()
        else 0.0,
        "absolute_max_case_z_sza": list(cases[int(np.argmax(delta))]),
        "near_zero_cases": int((~relevant).sum()),
        "near_zero_absolute_p50_p90_p99_s1": np.percentile(
            delta[~relevant], [50, 90, 99]
        ).tolist()
        if np.any(~relevant)
        else [0.0, 0.0, 0.0],
        "near_zero_absolute_max_s1": float(delta[~relevant].max())
        if np.any(~relevant)
        else 0.0,
        "near_zero_absolute_max_case_z_sza": list(
            cases[int(np.flatnonzero(~relevant)[np.argmax(delta[~relevant])])]
        )
        if np.any(~relevant)
        else None,
        "signed_relative_min_max": [
            float(((b - a)[relevant] / a[relevant]).min()),
            float(((b - a)[relevant] / a[relevant]).max()),
        ]
        if np.any(relevant)
        else [0.0, 0.0],
    }


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", required=True, type=Path)
    parser.add_argument("--hitran", required=True, type=Path)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    bands = load_bands(args.hitran)
    sources = SpectralSources(
        *load_tips(args.sources / "hapi.py"), load_solar(args.sources / "wehrli85.txt")
    )
    cia = load_cia(args.sources / "O2-O2_2011.cia")
    drouin = parse_drouin(args.sources / "PMC5103325.xml")
    mixing, _ = parse_supplement(args.sources / "1-s2.0-S0022407316301108-mmc1.pdf")
    tangent = float(180 - np.degrees(np.arcsin(6370 / 6470)))
    cases = [
        (float(z), float(sza))
        for z in range(50, 101)
        for sza in (0, 60, 85, 89, 89.9, 95, 99)
    ]
    cases += [(100.0, tangent), (100.0, tangent + 1e-7)]
    root = Path(__file__).resolve().parents[1]
    code = {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (root / "src/tfm_photochem/m4d_reconstruction").glob("*.py")
    }
    report = {
        "policy": "pragmatic complete Voigt baseline; SDV sensitivity; no LM/Galatry",
        "M4D_frozen": False,
        "M5_started": False,
        "floor_s1": FLOOR,
        "convergence_target": TOL,
        "source_identities": SOURCE_IDENTITIES,
        "hitran_records": 14085,
        "bands": {k: len(v) for k, v in bands.items()},
        "code_sha256": code,
        "validator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cases_z_sza": cases,
        "rates": {},
        "convergence": {},
        "sensitivities": {},
    }
    variants = {
        "base": dict(step_km=0.125, core_order=64, wing_order=12, support=3.84),
        "spatial": dict(step_km=0.0625, core_order=64, wing_order=12, support=3.84),
        "spectral": dict(step_km=0.125, core_order=128, wing_order=24, support=3.84),
        "support": dict(step_km=0.125, core_order=128, wing_order=24, support=7.68),
    }
    report["controls"] = {
        "variants": variants,
        "far_order": 4,
        "near_cm1": 2.0,
        "shifts": True,
        "diluent": "requested_partial",
        "cia_step_base_km": 0.0625,
        "cia_step_spatial_km": 0.03125,
        "CIA_role": "attenuation only; nO2*(nO2+nN2)",
        "line_mixing": False,
        "Galatry": False,
    }

    def run(label, lines, config, advanced=False, collision=False, run_cases=cases):
        controls = dict(
            config,
            far_order=4,
            block_size=512,
            **({"drouin": drouin} if advanced else {}),
        )
        if collision and config.get("step_km") == 0.0625:
            controls["cia_step_km"] = 0.03125
        identity = {
            "code": code,
            "sources": SOURCE_IDENTITIES,
            "line_keys": [list(x.key) for x in lines],
            "controls": controls,
            "cases": run_cases,
            "cia": collision,
        }
        digest = hashlib.sha256(
            json.dumps(identity, sort_keys=True).encode()
        ).hexdigest()
        cache = args.cache / f"{digest}.json"
        if cache.exists():
            result = json.loads(cache.read_text())
            print(f"{label}: verified cache", flush=True)
        else:
            begin, last = time.perf_counter(), [0.0]

            def progress(done, total):
                now = time.perf_counter()
                if now - last[0] > 30:
                    print(f"{label}: {done}/{total}; {now - begin:.0f}s", flush=True)
                    last[0] = now

            result = compute_classic_rates(
                lines,
                sources,
                run_cases,
                cia=cia if collision else None,
                progress=progress,
                **controls,
            )
            result = {k: v.tolist() for k, v in result.items()}
            save(cache, result)
            print(f"{label}: completed {time.perf_counter() - begin:.0f}s", flush=True)
        for key, value in result.items():
            a = np.asarray(value)
            if key != "illuminated":
                assert np.all(np.isfinite(a)) and np.all(a >= 0)
                assert np.all(a[~np.asarray(result["illuminated"])] == 0)
        assert result["illuminated"][-2:] == [True, False]
        return result

    populations = (("A0", "A"), ("A1", "A"), ("B", "B"), ("IRA", "IRA"))
    with ThreadPoolExecutor(max_workers=3) as pool:
        pending = {}
        for label, band in populations:
            for variant, config in variants.items():
                pending[label, variant] = pool.submit(
                    run,
                    f"{label}/{variant}",
                    bands[band],
                    config,
                    advanced=label == "A1",
                    collision=label == "IRA",
                )
            pending[label, "reverse"] = pool.submit(
                run,
                f"{label}/reverse",
                tuple(reversed(bands[band])),
                variants["base"],
                advanced=label == "A1",
                collision=label == "IRA",
            )
        for label, band in populations:
            report["rates"][label] = {}
            for variant in variants:
                report["rates"][label][variant] = pending[label, variant].result()
                save(args.output, report)
            key = "cia_nominal" if label == "IRA" else "monomer"
            r = report["rates"][label]
            report["convergence"][label] = {
                "spatial": stats(r["base"][key], r["spatial"][key], cases),
                "spectral": stats(r["base"][key], r["spectral"][key], cases),
                "support": stats(r["spectral"][key], r["support"][key], cases),
            }
            # Reversed source order is an independent full-domain calculation.
            reverse = pending[label, "reverse"].result()
            report["convergence"][label]["source_order"] = stats(
                r["base"][key], reverse[key], cases
            )
            if label == "IRA":
                report["CIA_auxiliary_convergence"] = {
                    name: {
                        "spatial": stats(r["base"][name], r["spatial"][name], cases),
                        "spectral": stats(r["base"][name], r["spectral"][name], cases),
                        "support": stats(
                            r["spectral"][name], r["support"][name], cases
                        ),
                        "source_order": stats(r["base"][name], reverse[name], cases),
                    }
                    for name in (
                        "monomer",
                        "cia_envelope_min",
                        "cia_envelope_max",
                        "cia_raw",
                    )
                }
            save(args.output, report)

    report["sensitivities"]["A1_vs_A0"] = stats(
        report["rates"]["A0"]["support"]["monomer"],
        report["rates"]["A1"]["support"]["monomer"],
        cases,
    )
    removals = {
        "21_no_Y": lambda x: (
            x.isotope == 1 and x.flag == "d" and x.dipole_label not in mixing
        ),
        "59_q": lambda x: x.isotope == 1 and x.flag == "q",
        "280_rare": lambda x: x.isotope != 1,
    }
    with ThreadPoolExecutor(max_workers=3) as pool:
        pending = {}
        counts = {}
        for name, remove in removals.items():
            selected = tuple(x for x in bands["A"] if not remove(x))
            counts[name] = 430 - len(selected)
            for label in ("A0", "A1"):
                pending[label, name] = pool.submit(
                    run,
                    f"{label}/omit_{name}",
                    selected,
                    variants["support"],
                    advanced=label == "A1",
                )
        for (label, name), task in pending.items():
            r = task.result()
            report["sensitivities"][f"{label}_omit_{name}"] = stats(
                report["rates"][label]["support"]["monomer"], r["monomer"], cases
            )
            report["sensitivities"][f"{label}_omit_{name}"]["removed_lines"] = counts[
                name
            ]
            save(args.output, report)

    ira = report["rates"]["IRA"]["support"]
    report["cia"] = {
        key: stats(ira["monomer"], ira[key], cases)
        for key in ("cia_nominal", "cia_envelope_min", "cia_envelope_max", "cia_raw")
    }
    report["cia"]["envelope_spread"] = stats(
        ira["cia_nominal"], ira["cia_envelope_min"], cases
    )
    report["cia"]["envelope_spread_other"] = stats(
        ira["cia_nominal"], ira["cia_envelope_max"], cases
    )

    # Bound far-approximation error pointwise at every active shell. A bound on
    # |delta tau| bounds relative transmission error by exp(bound)-1, avoiding
    # an expensive second full-domain exact transfer when the bound is tiny.
    shells = atmosphere(0.125)
    paths = np.array([path_lengths(z, sza, shells.edges)[1] for z, sza in cases])
    used = np.any(paths > 0, axis=0)
    columns = (paths[:, used] * 1e5 * shells.oxygen[used]).T
    # Every positive normalized Voigt is a convolution with a Gaussian, hence
    # its peak cannot exceed that Gaussian's peak. Sum individual peak bounds
    # to bound the effect of deleting *all* >340 K A0 opacity on any ray.
    from tfm_photochem.m4d_reconstruction.spectroscopy import doppler_sigma

    hot = shells.temperature > 340
    peak_bound = np.array(
        [
            np.sum(
                sources.strengths(bands["A"], t)
                / (np.sqrt(2 * np.pi) * doppler_sigma(bands["A"], t))
            )
            for t in shells.temperature[hot]
        ]
    )
    hot_columns = (paths[:, hot] * 1e5 * shells.oxygen[hot]).T
    report["hot_shell_A0_bound"] = {
        "shells": int(hot.sum()),
        "minimum_shell_edge_km": float(shells.edges[:-1][hot].min()),
        "maximum_pressure_atm": float(shells.pressure[hot].max()),
        "all_hot_absorption_deleted_relative_bound": float(
            np.expm1((peak_bound @ hot_columns).max())
        ),
        "interpretation": "rigorous Voigt transmission bound; no claim about arbitrary unsourced Y",
    }
    report["far_approximation"] = {}
    classic_a_probe = None
    for label, band in (("A0", "A"), ("A1", "A"), ("B", "B"), ("IRA", "IRA")):
        lines = bands[band]
        centres = np.array([x.nu for x in lines])
        nodes = np.unique(
            np.r_[
                centres[::5],
                centres[::5] + 2,
                centres[::5] - 2,
                np.linspace(centres.min() - 7.68, centres.max() + 7.68, 150),
            ]
        )
        column = VoigtColumn(
            lines,
            sources,
            shells,
            used_shells=used,
            drouin=drouin if label == "A1" else None,
        )
        exact = column.cross_section(nodes, exact=True)
        error = np.abs(column.cross_section(nodes, order=4) - exact)
        nominal = np.asarray(
            report["rates"][label]["base"][
                "cia_nominal" if label == "IRA" else "monomer"
            ]
        )
        relevant = nominal > max(FLOOR, 1e-4 * float(nominal.max()))
        per_case_bound = error.max(axis=0) @ columns
        tau_bound = float(per_case_bound[relevant].max())
        if label == "A0":
            classic_a_probe = exact
        if label == "A1":
            active_hot = shells.temperature[used] > 340
            delta_hot = np.abs(exact[:, active_hot] - classic_a_probe[:, active_hot])
            report["hot_shell_A1_vs_A0"] = {
                "sampled_transmission_relative_bound": float(
                    np.expm1((delta_hot.max(axis=0) @ columns[active_hot]).max())
                ),
                "scope": "all hot shells; sampled exact SDV versus Voigt; no LM assumed",
            }
        report["far_approximation"][label] = {
            "probe_nodes": len(nodes),
            "active_shells": int(used.sum()),
            "sampled_max_opacity_relative": float(
                (error / np.maximum(exact, 1e-300)).max()
            ),
            "sampled_shellwise_transmission_bound": float(np.expm1(tau_bound)),
            "sampled_all_cases_optical_depth_bound": float(per_case_bound.max()),
            "scope": "sampled-node bound, not rigorous continuum bound",
        }
        save(args.output, report)
    artifact = root / "artifacts/accepted/m4c-r2/tfm-photochem-milestone4c-r2.zip"
    report["M4C_R2_sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert (
        report["M4C_R2_sha256"]
        == "2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe"
    )
    report["decision"] = (
        "GO provisional"
        if all(
            value["relative_max"] <= TOL
            for band in report["convergence"].values()
            for value in band.values()
        )
        and all(
            value["relative_max"] <= TOL
            for band in report["CIA_auxiliary_convergence"].values()
            for value in band.values()
        )
        and all(
            value["sampled_shellwise_transmission_bound"] <= TOL
            for value in report["far_approximation"].values()
        )
        else "NO-GO provisional: investigate numerical convergence"
    )
    save(args.output, report)
    print(report["decision"], flush=True)


if __name__ == "__main__":
    main()
