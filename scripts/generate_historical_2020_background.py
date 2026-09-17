#!/usr/bin/env python3
"""Generate or byte-compare the frozen Milestone-4A background assets."""

from __future__ import annotations

import argparse
import filecmp
import json
import tempfile
from pathlib import Path

from tfm_photochem.historical_2020.background_generation import (
    CHEM_FILENAME,
    METADATA_FILENAME,
    RAD_FILENAME,
    generate_background_assets,
    generation_environment,
)


def _check_against_frozen() -> None:
    package_assets = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "tfm_photochem"
        / "assets"
        / "historical_2020"
    )
    with tempfile.TemporaryDirectory(prefix="tfm_m4a_regen_") as directory:
        generated = generate_background_assets(Path(directory))
        comparisons = {
            key: filecmp.cmp(path, package_assets / path.name, shallow=False)
            for key, path in generated.items()
        }
    payload = {
        "check_against_frozen": comparisons,
        "generation_environment": generation_environment(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not all(comparisons.values()):
        raise SystemExit("regenerated M4A assets differ from frozen package assets")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--output-dir", type=Path)
    group.add_argument("--check-against-frozen", action="store_true")
    args = parser.parse_args()
    if args.check_against_frozen:
        _check_against_frozen()
        return
    paths = generate_background_assets(args.output_dir)
    print(
        json.dumps(
            {
                "files": {key: str(path) for key, path in paths.items()},
                "expected_filenames": [RAD_FILENAME, CHEM_FILENAME, METADATA_FILENAME],
                "generation_environment": generation_environment(),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
