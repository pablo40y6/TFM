#!/usr/bin/env python3
"""Verify the first retained CIA stop-gate counterexample, without claiming closure.

Exit 2 means the requested scientific DESIGN BLOCKER was reproduced. Exit 1
means numerical/source verification failed. Exit 0 only means this stop probe
did not trigger; it never means full-domain M4D acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np
import scipy

from tfm_photochem.historical_2020 import spherical_shell_paths
from tfm_photochem.m4d_reconstruction.cia import BLOCK_IDENTITIES, load_cia
from tfm_photochem.m4d_reconstruction.sources import (
    BAND_IDENTITIES,
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
    target_quadrature,
)

GATE = 1e-3
FLOOR = 1e-15
CASE = (50.0, 95.0)
VARIANTS = {
    "baseline": dict(
        step_km=0.125, cia_step_km=0.0625, core_order=64, wing_order=8, support=3.84
    ),
    "spatial": dict(
        step_km=0.0625, cia_step_km=0.03125, core_order=64, wing_order=8, support=3.84
    ),
    "spectral_order": dict(
        step_km=0.125, cia_step_km=0.0625, core_order=128, wing_order=16, support=3.84
    ),
    "spectral_support": dict(
        step_km=0.125, cia_step_km=0.0625, core_order=128, wing_order=16, support=7.68
    ),
}
CONTROLS = {
    "case": list(CASE),
    "far_order": 4,
    "near_cm1": 2.0,
    "shifts": True,
    "diluent": "requested_partial",
    "cia": "historical_nominal_envelope_raw",
}
ANCHORS = np.array(
    [
        [6.1914394520e-9, 3.5752856768e-10, 1.4549983481e-10],
        [6.1963256585e-9, 3.5805572358e-10, 1.4573674701e-10],
        [6.1999597393e-9, 3.5852735538e-10, 1.4593873602e-10],
        [6.2025842093e-9, 3.5895153697e-10, 1.4611114500e-10],
        [6.2043175651e-9, 3.5933010076e-10, 1.4625641629e-10],
        [6.2051968875e-9, 3.5966103384e-10, 1.4637502395e-10],
        [6.2052846913e-9, 3.5988913888e-10, 1.4645036484e-10],
    ]
)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )


def code_identity():
    root = Path(__file__).resolve().parents[1]
    files = sorted((root / "src/tfm_photochem/m4d_reconstruction").glob("*.py"))
    return {
        str(p.relative_to(root)).replace("\\", "/"): hashlib.sha256(
            p.read_bytes()
        ).hexdigest()
        for p in files
    }


def preliminary_checks(bands, sources):
    temperatures = (180, 200, 220, 240, 260, 280, 296)
    actual = np.array(
        [
            [
                np.sum(
                    sources.strengths(bands[name], t)
                    * sources.photons(np.array([line.nu for line in bands[name]]))
                )
                for name in ("A", "B", "IRA")
            ]
            for t in temperatures
        ]
    )
    anchor_error = float(np.max(np.abs(actual - ANCHORS) / ANCHORS))
    if anchor_error > 1e-9:
        raise AssertionError("historical unattenuated regression anchor failed")

    edges = atmosphere(0.125).edges
    absolute_error = 0.0
    illuminated_count = 0
    for sza in (0, 60, 85, 89, 89.9, 95, 99):
        accepted = spherical_shell_paths(sza)
        for i, z in enumerate(range(50, 101)):
            illuminated, path = path_lengths(z, sza, edges)
            if illuminated != accepted.illuminated[i]:
                raise AssertionError("accepted physical shadow changed")
            illuminated_count += int(illuminated)
            error = np.max(
                np.abs(path.reshape(150, 8).sum(axis=1) - accepted.path_length_km[i])
            )
            absolute_error = max(absolute_error, float(error))
    if absolute_error > 1e-8:
        raise AssertionError("accepted geometry changed")
    tangent = 180 - np.degrees(np.arcsin(6370 / 6470))
    if not path_lengths(100, tangent, edges)[0]:
        raise AssertionError("illuminated tangent was shadowed")
    shadow, lengths = path_lengths(100, tangent + 1e-7, edges)
    if shadow or np.any(lengths):
        raise AssertionError("immediately shadowed boundary is not exactly zero")
    shadow_rates = compute_classic_rates(
        bands["IRA"], sources, [(100.0, tangent + 1e-7)]
    )
    if any(np.any(value) for value in shadow_rates.values()):
        raise AssertionError("immediately shadowed IRA rates are not exactly zero")

    # All active reference shells, every isotope/branch population and both
    # line cores and between-line regions; compare directly with all-line wofz.
    shells = atmosphere(0.0625)
    used = path_lengths(*CASE, shells.edges)[1] > 0
    column = VoigtColumn(bands["IRA"], sources, shells, used_shells=used)
    nodes, _, _ = target_quadrature(bands["IRA"], 128, 16, 7.68)
    centres = np.array([line.nu for line in bands["IRA"]])
    probe = np.unique(
        np.r_[
            np.linspace(nodes.min(), nodes.max(), 100),
            nodes[::1000],
            centres[::5],
            centres[::5] + 2.0,
        ]
    )
    exact = column.cross_section(probe, exact=True)
    errors = {
        str(order): float(
            np.max(np.abs(column.cross_section(probe, order=order) - exact) / exact)
        )
        for order in (4, 6, 8)
    }
    if errors["4"] > 1e-6:
        raise AssertionError("distant-contribution evaluator needs refinement")
    return {
        "unattenuated_anchors": {
            "temperatures_K": temperatures,
            "bands": ["A", "B", "IRA"],
            "rates_s1": actual.tolist(),
            "max_relative_difference": anchor_error,
        },
        "geometry": {
            "cases": 357,
            "illuminated": illuminated_count,
            "max_absolute_accepted_shell_difference_km": absolute_error,
            "tangent_sza_deg": float(tangent),
            "tangent_illuminated": True,
            "immediately_shadowed_path_exact_zero": True,
            "immediately_shadowed_IRA_rate_exact_zero": True,
        },
        "all_line_opacity": {
            "nodes": len(probe),
            "active_shells": int(used.sum()),
            "max_relative_difference_from_direct_wofz": errors,
            "selected_moment_order": 4,
            "near_radius_cm1": 2.0,
            "absorber_cutoff": "none; every accepted line contributes",
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--hitran", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--checkpoints",
        type=Path,
        help="optional derived-rate cache; sources are reverified",
    )
    args = parser.parse_args()
    bands = load_bands(args.hitran)
    sources = SpectralSources(
        *load_tips(args.sources / "hapi.py"), load_solar(args.sources / "wehrli85.txt")
    )
    cia = load_cia(args.sources / "O2-O2_2011.cia")
    identity = code_identity()
    report = {
        "scope": "isolated retained IRA stop probe, not full-domain closure",
        "case": {"altitude_km": CASE[0], "sza_deg": CASE[1]},
        "gate_relative": GATE,
        "diagnostic_floor_s1": FLOOR,
        "code_sha256": identity,
        "validator_script_sha256": hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest(),
        "controls": CONTROLS,
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "verified_source_identities": {
            name: {
                "bytes": SOURCE_IDENTITIES[name][0],
                "sha256": SOURCE_IDENTITIES[name][1],
            }
            for name in (
                "guest1593878592.txt",
                "hapi.py",
                "wehrli85.txt",
                "O2-O2_2011.cia",
            )
        },
        "bands": {
            name: {"lines": count, "canonical_sha256": sha}
            for name, (count, sha) in BAND_IDENTITIES.items()
        },
        "historical_cia_blocks": {
            str(t): {"points": count, "sha256": sha}
            for t, (count, sha) in BLOCK_IDENTITIES.items()
        },
        "preliminary_checks": preliminary_checks(bands, sources),
        "variants": {},
        "not_run_after_stop": [
            "full-domain A/B/IRA rate closure",
            "A SDV+LM coupled transfer and rare Galatry evaluator",
            "A low-temperature/no-Y/quadrupole sensitivities",
            "B corrected source-based qSDV sensitivity",
            "pressure-shift sensitivity",
            "full-domain spectral/spatial maxima",
            "illuminated tangent RATE closure (tangent/shadow geometry and shadow rate passed)",
        ],
    }
    for name, configuration in VARIANTS.items():
        checkpoint = args.checkpoints / f"{name}.json" if args.checkpoints else None
        cached = (
            json.loads(checkpoint.read_text())
            if checkpoint and checkpoint.exists()
            else None
        )
        if (
            cached
            and cached.get("code_sha256") == identity
            and cached.get("configuration") == configuration
            and cached.get("controls") == CONTROLS
        ):
            result = cached["result"]
            producer = cached["producer_validator_sha256"]
            print(f"{name}: verified checkpoint", flush=True)
        else:
            print(f"{name}: {configuration}", flush=True)
            begin, last = time.perf_counter(), [0.0]

            def progress(done, total):
                now = time.perf_counter()
                if now - last[0] >= 30:
                    print(
                        f"{name}: nodes {done}/{total}, elapsed {now - begin:.1f}s",
                        flush=True,
                    )
                    last[0] = now

            rates = compute_classic_rates(
                bands["IRA"],
                sources,
                [CASE],
                cia=cia,
                far_order=CONTROLS["far_order"],
                near_cm1=CONTROLS["near_cm1"],
                shifts=CONTROLS["shifts"],
                diluent=CONTROLS["diluent"],
                progress=progress,
                **configuration,
            )
            result = {
                "rates_s1": {
                    key: float(value[0])
                    for key, value in rates.items()
                    if key != "illuminated"
                },
                "illuminated": bool(rates["illuminated"][0]),
            }
            producer = report["validator_script_sha256"]
            if checkpoint:
                write_json(
                    checkpoint,
                    {
                        "code_sha256": identity,
                        "configuration": configuration,
                        "controls": CONTROLS,
                        "producer_validator_sha256": producer,
                        "result": result,
                    },
                )
        report["variants"][name] = {
            "configuration": configuration,
            "producer_validator_sha256": producer,
            **result,
        }
        print(f"{name}: {result}", flush=True)

    comparisons = {}
    for old, new in (
        ("baseline", "spatial"),
        ("baseline", "spectral_order"),
        ("spectral_order", "spectral_support"),
    ):
        a, b = (report["variants"][n]["rates_s1"] for n in (old, new))
        errors = {key: abs(a[key] - b[key]) / b[key] for key in a if b[key] > FLOOR}
        comparisons[f"{old}_to_{new}"] = {
            "relative_differences": errors,
            "max_relative_difference": max(errors.values()),
            "status": "PASS" if max(errors.values()) <= GATE else "FAIL",
        }
    report["counterexample_convergence"] = comparisons
    numerical_pass = all(item["status"] == "PASS" for item in comparisons.values())
    reference = report["variants"]["spectral_support"]["rates_s1"]
    monomer = reference["monomer"]
    reductions = {
        key: 1 - value / monomer
        for key, value in reference.items()
        if key.startswith("cia_")
    }
    report["cia_relative_reductions"] = reductions
    retained = monomer > FLOOR and reference["cia_nominal"] > FLOOR
    report["retained_above_floor"] = retained
    envelope_changes_decision = (
        reductions["cia_envelope_min"] <= GATE < reductions["cia_envelope_max"]
    )
    report["measured_temperature_envelope_changes_decision"] = envelope_changes_decision
    blocker = retained and (
        reductions["cia_nominal"] > GATE or envelope_changes_decision
    )
    report["decision"] = (
        "NUMERICAL VERIFICATION BLOCKER"
        if not numerical_pass
        else "DESIGN BLOCKER"
        if blocker
        else "STOP PROBE DOES NOT TRIGGER"
    )
    report["M4D_frozen"] = False
    write_json(args.output, report)
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "decision",
                    "retained_above_floor",
                    "cia_relative_reductions",
                    "counterexample_convergence",
                )
            },
            indent=2,
        )
    )
    return 1 if not numerical_pass else 2 if blocker else 0


if __name__ == "__main__":
    raise SystemExit(main())
