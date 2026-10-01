#!/usr/bin/env python3
"""Audit sourced principal A transfer and report unresolved scientific blockers.

Exit 2: principal/source checks passed, full A scientifically blocked.
Exit 1: a source/numerical verification failed. Never certifies M4D closure.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import warnings
from dataclasses import replace
from pathlib import Path

import numpy as np
from scipy.integrate import quad
from validate_m4d_mapping import validate as validate_mapping

from tfm_photochem.m4d_reconstruction.a_band import (
    GALATRY_BLOCKER,
    LM_BLOCKER,
    APolicy,
    PrincipalA,
    PrincipalAColumn,
    compute_a_rates,
    compute_principal_a_rates,
)
from tfm_photochem.m4d_reconstruction.sources import (
    SourceError,
    load_bands,
    load_solar,
    load_tips,
    verified_bytes,
)
from tfm_photochem.m4d_reconstruction.spectroscopy import (
    SpectralSources,
    complex_sdv,
    mixing_y,
)
from tfm_photochem.m4d_reconstruction.transfer import atmosphere, path_lengths


def historical_sdv_audit(tree):
    """Execute only reviewed math functions from hash-verified historical HAPI.

    Do not import/run HAPI's module, database setup, network or table-loading code.
    Retain its actual default CPF implementation (hum1_wei), not scipy wofz.
    Source loading at runtime continues to parse literal tables only.
    """
    functions = {"pcqsdhc", "cpf3", "cef", "hum1_wei"}
    constants = {"zone", "zi", "tt", "pipwoeronehalf", "weideman"}
    selected = [
        node
        for node in tree.body
        if (isinstance(node, ast.FunctionDef) and node.name in functions)
        or (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id in constants
                for target in node.targets
            )
        )
    ]
    if len(selected) != 9:
        raise SourceError("historical HAPI math function selection changed")
    namespace = {
        name: getattr(np, name)
        for name in (
            "array",
            "ndarray",
            "zeros",
            "sqrt",
            "log",
            "pi",
            "abs",
            "exp",
            "arange",
            "tan",
            "real",
            "flipud",
            "polyval",
            "place",
            "maximum",
            "minimum",
        )
    }
    namespace.update(
        {
            "__ComplexType__": np.complex128,
            "__FloatType__": np.float64,
            "fft": np.fft.fft,
            "fftshift": np.fft.fftshift,
        }
    )
    exec(
        compile(
            ast.Module(body=selected, type_ignores=[]), "verified-HAPI-math", "exec"
        ),
        namespace,
    )
    namespace["VARIABLES"] = {"CPF": namespace["hum1_wei"]}
    return namespace["pcqsdhc"]


def validate(source_dir, hitran):
    # Reuse the existing full byte/quantum audit before any spectroscopy.
    mapping = validate_mapping(source_dir, hitran)
    from tfm_photochem.m4d_reconstruction.mapping import parse_drouin, parse_supplement

    drouin = parse_drouin(source_dir / "PMC5103325.xml")
    mixing, _ = parse_supplement(source_dir / "1-s2.0-S0022407316301108-mmc1.pdf")
    grid, tables = load_tips(source_dir / "hapi.py")
    sources = SpectralSources(grid, tables, load_solar(source_dir / "wehrli85.txt"))
    all_lines = load_bands(hitran)["A"]
    principal = tuple(line for line in all_lines if line.isotope == 1)
    model = PrincipalA(principal, sources, drouin, mixing)
    hapi = verified_bytes(source_dir / "hapi.py", "hapi.py").decode("utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        tree = ast.parse(hapi)
    galatry_functions = sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and "galatry" in node.name.lower()
    )
    if galatry_functions:
        raise SourceError("review newly found Galatry implementation before proceeding")
    pinned_sdv = historical_sdv_audit(tree)
    maximum_error, comparisons, areas = 0.0, 0, []
    for t in (180.0, 200.0, 296.0, 340.0):
        for p in (1e-6, 0.1, 1.0):
            _, sigma, gamma, gamma2, _, _ = model.parameters(t, p, 0.21 * p)
            for i, line in enumerate(model.selected_lines):
                if line.flag != "d":
                    continue
                delta = np.array([-10.0, -1.0, -0.1, 0.0, 0.1, 1.0, 10.0]) * max(
                    sigma[i], gamma[i]
                )
                # The historical vector routine misindexes mixed PART2/PART4
                # masks. Single-node calls preserve its equations unchanged.
                pairs = [
                    pinned_sdv(
                        0.0,
                        sigma[i] * np.sqrt(2 * np.log(2)),
                        gamma[i],
                        gamma2[i],
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        np.array([node]),
                    )
                    for node in delta
                ]
                real = np.array([pair[0][0] for pair in pairs])
                imag = np.array([pair[1][0] for pair in pairs])
                actual = complex_sdv(delta, sigma[i], gamma[i], gamma2[i])
                reference = real + 1j * imag
                error = float(
                    np.max(np.abs(actual - reference)) / np.max(np.abs(actual))
                )
                maximum_error = max(maximum_error, error)
                comparisons += 1
            # Source-driven area checks, no finite-support renormalization.
            for i in (0, 45, 90):
                if model.selected_lines[i].flag != "d":
                    continue
                area, _ = quad(
                    lambda delta: (
                        complex_sdv(delta, sigma[i], gamma[i], gamma2[i]).real
                    ),
                    -np.inf,
                    np.inf,
                    epsabs=2e-9,
                )
                areas.append(float(area))
    if maximum_error > 1e-3 or max(abs(area - 1) for area in areas) > 1e-6:
        raise AssertionError(f"SDV reference/area failed: {maximum_error}, {areas}")
    for values in mixing.values():
        for t, value in zip((200.0, 250.0, 296.0, 340.0), values):
            if mixing_y(values, t) != value:
                raise AssertionError("Table-22 source node not exactly recovered")

    centres = np.array([line.nu for line in all_lines])
    nodes = np.unique(
        np.concatenate(
            [
                centres + delta
                for delta in (-10.0, -1.0, -0.1, -0.01, 0.0, 0.01, 0.1, 1.0, 10.0)
            ]
        )
    )
    physical_failures, minimum = [], np.inf
    reverse = replace(model, lines=tuple(reversed(principal)))
    for t in (180.0, 200.0, 296.0, 340.0):
        for p in (0.0, 1e-6, 0.1, 1.0):
            opacity = model.contributions(nodes, t, p, 0.21 * p).sum(axis=1)
            minimum = min(minimum, float(opacity.min()))
            if not np.array_equal(
                opacity, reverse.contributions(nodes, t, p, 0.21 * p).sum(axis=1)
            ):
                raise AssertionError("source order changed principal opacity")
            if np.any(opacity < 0):
                physical_failures.append(
                    {
                        "temperature_K": t,
                        "pressure_atm": p,
                        "minimum_cm2_molecule": float(opacity.min()),
                        "wavenumber_cm1": float(nodes[np.argmin(opacity)]),
                    }
                )
    shells = atmosphere(0.125)
    hot = shells.temperature > 340
    _, lengths = path_lengths(50.0, 0.0, shells.edges)
    used = lengths * shells.oxygen > 0
    try:
        PrincipalAColumn(model, shells, used_shells=used)
    except ValueError as error:
        hot_blocker = str(error)
        if "DESIGN BLOCKER" not in hot_blocker:
            raise
    else:
        raise AssertionError("actual hot-shell policy did not fail closed")
    try:
        compute_a_rates()
    except SourceError as error:
        if str(error) != GALATRY_BLOCKER + "; " + LM_BLOCKER:
            raise
    try:
        compute_principal_a_rates(model, [(50.0, 0.0)])
    except SourceError as error:
        if str(error) != LM_BLOCKER:
            raise
    else:
        raise AssertionError(
            "unverified Table-22 normalization reached nominal transfer"
        )
    shadow = compute_principal_a_rates(model, [(50.0, 180.0), (100.0, 180.0)])
    if np.any(shadow["principal"] != 0):
        raise AssertionError("shadow must be exactly zero")
    # Sensitivity dispatch is checked on a supported physical state, without
    # reporting these cross sections as full-column rate sensitivities.
    policy_counts = {
        "nominal": len(model.selected_lines),
        "without_no_y": len(
            replace(model, policy=APolicy(include_no_y=False)).selected_lines
        ),
        "without_q": len(
            replace(model, policy=APolicy(include_quadrupoles=False)).selected_lines
        ),
    }
    root = Path(__file__).resolve().parents[1]
    paths = [
        root / "src/tfm_photochem/m4d_reconstruction/a_band.py",
        root / "src/tfm_photochem/m4d_reconstruction/spectroscopy.py",
        Path(__file__),
    ]
    return {
        "decision": "SCIENTIFIC BLOCKER",
        "M4D_frozen": False,
        "M5_started": False,
        "scope": "principal SDV and candidate LM algebra only; not full 430-line gA closure",
        "mapping": {
            key: mapping[key]
            for key in (
                "status",
                "drouin_sdv",
                "published_lm",
                "dipoles_outside_lm",
                "quadrupoles",
                "rare_galatry",
                "auxiliary_matches",
                "unmatched",
                "duplicates",
                "ambiguities",
            )
        },
        "sdv_hapi_default_cpf": {
            "status": "PASS",
            "comparisons": comparisons,
            "maximum_profile_scaled_complex_error": maximum_error,
            "tolerance": 1e-3,
            "method": "hash-verified math-only AST; pinned hum1_wei/pcqsdhc, no module import",
        },
        "sdv_unit_area": {
            "status": "PASS",
            "checks": len(areas),
            "max_error": max(abs(area - 1) for area in areas),
        },
        "table22_source_nodes": {"status": "PASS", "checks": 280},
        "candidate_algebra_opacity_probes": {
            "status": "DESIGN BLOCKER" if physical_failures else "PASS",
            "nodes": len(nodes),
            "states": 16,
            "minimum_cm2_molecule": minimum,
            "negative_states": physical_failures,
            "clipping": False,
            "source_order_invariance": "PASS",
        },
        "principal_shadow": "PASS",
        "line_mixing_normalization": {
            "status": "SOURCE CONVENTION BLOCKER",
            "exception": LM_BLOCKER,
            "source_table_units": "cm^-1 atm^-1",
            "required": "historical demonstration of numeric Y normalization with F/F-prime",
            "nominal_rate_gate": "PASS; unverified normalization rejected",
        },
        "sensitivity_population_counts": policy_counts,
        "hot_shells": {
            "status": "DESIGN BLOCKER",
            "shell_step_km": 0.125,
            "count": int(hot.sum()),
            "active_in_vertical_50km": int((hot & used).sum()),
            "first_lower_edge_km": float(shells.edges[:-1][hot].min()),
            "maximum_temperature_K": float(shells.temperature.max()),
            "exception": hot_blocker,
        },
        "rare_galatry": {
            "status": "SOURCE CONVENTION BLOCKER",
            "mapped_lines": 280,
            "pinned_hapi_galatry_functions": galatry_functions,
            "missing": [
                "exact beta/profile frequency convention",
                "historical beta(T,p) law",
            ],
            "limits_area_and_nonnegativity": "NOT RUN; no authorized evaluator",
        },
        "full_domain_rate_convergence": "NOT RUN; LM normalization, hot-shell and Galatry blockers",
        "low_T_no_Y_q_rate_sensitivities": "NOT RUN on full accepted column",
        "code_sha256": {
            str(path.relative_to(root)).replace("\\", "/"): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in paths
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--hitran", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = validate(args.sources, args.hitran)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(
        (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
