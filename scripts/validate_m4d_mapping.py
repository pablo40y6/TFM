#!/usr/bin/env python3
"""Reproduce source-to-transition mapping without redistributing source data."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import pymupdf

from tfm_photochem.m4d_reconstruction.mapping import (
    audit_mapping,
    parse_drouin,
    parse_galatry,
    parse_supplement,
)
from tfm_photochem.m4d_reconstruction.sources import (
    BAND_IDENTITIES,
    SOURCE_IDENTITIES,
    load_bands,
    load_solar,
    load_tips,
    verified_bytes,
)


def validate(source_dir: Path, hitran: Path) -> dict:
    bands = load_bands(hitran)
    drouin = parse_drouin(source_dir / "PMC5103325.xml")
    mixing, supplement = parse_supplement(
        source_dir / "1-s2.0-S0022407316301108-mmc1.pdf"
    )
    auxiliary = parse_galatry(source_dir / "07_hit12_0.76mic_Galatry.par")
    report = audit_mapping(bands["A"], drouin, mixing, auxiliary, supplement)
    report["runtime"] = {
        "python": platform.python_version(),
        "pymupdf": pymupdf.VersionBind,
    }
    matrix_labels = {
        label
        for table in supplement["matrix_tables"].values()
        for label in table["quantum_labels"]
    }
    if matrix_labels != set(mixing):
        raise AssertionError("published matrix and Table-22 coverage differ")
    report["matrix_table22_coverage_identical"] = True
    verified_bytes(source_dir / "07_A-band_SDF.dat", "07_A-band_SDF.dat")
    tips_grid, tips = load_tips(source_dir / "hapi.py")
    solar = load_solar(source_dir / "wehrli85.txt")
    report["expected_source_identities"] = {
        name: {"bytes": size, "sha256": sha}
        for name, (size, sha) in SOURCE_IDENTITIES.items()
    }
    report["verified_sources"] = sorted(set(SOURCE_IDENTITIES) - {"O2-O2_2011.cia"})
    report["bands"] = {
        name: {"records": count, "canonical_sha256": sha}
        for name, (count, sha) in BAND_IDENTITIES.items()
    }
    report["tips_grid_points"] = len(tips_grid)
    report["solar_grid_points"] = len(solar)
    # Hash means only; retain source uncertainties in the original XML.
    report["derived_transcription"] = {
        "drouin_means_sha256": hashlib.sha256(
            json.dumps(drouin, sort_keys=True).encode()
        ).hexdigest(),
        "table22_sha256": hashlib.sha256(
            json.dumps(mixing, sort_keys=True).encode()
        ).hexdigest(),
        "tips_sha256": hashlib.sha256(
            json.dumps(
                {iso: list(table) for iso, table in tips.items()}, sort_keys=True
            ).encode()
        ).hexdigest(),
        "algorithm": "scripts/validate_m4d_mapping.py; original means, no OCR, no row-order join",
    }
    return report


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
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key
                in (
                    "status",
                    "drouin_sdv",
                    "published_lm",
                    "dipoles_outside_lm",
                    "quadrupoles",
                    "rare_galatry",
                    "unmatched",
                    "duplicates",
                    "ambiguities",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
