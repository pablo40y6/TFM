#!/usr/bin/env python3
"""Rerun the existing workflow's CIA geometry witness outside the Git checkout.

This is the historical HITRAN2012 thin-weight geometry diagnostic, never a
replacement for HITRAN2016 line transfer or retained-rate M4D closure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path


def checked(path: Path, size: int | None, sha256: str):
    data = path.read_bytes()
    if (size is not None and len(data) != size) or hashlib.sha256(
        data
    ).hexdigest() != sha256:
        raise ValueError(f"historical diagnostic identity failed: {path.name}")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sources",
        type=Path,
        required=True,
        help="directory containing both historical CIA and 07_hit12.par witnesses",
    )
    parser.add_argument(
        "--work",
        type=Path,
        required=True,
        help="external scratch directory, never a directory inside the repository",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    work = args.work.resolve()
    if work == root or root in work.parents:
        raise ValueError("restricted source witnesses must remain outside Git")
    checked(
        args.sources / "07_hit12.par",
        2263950,
        "ad2cadf91cb985bec4074ce0bf47cdcfa7aab627ea15de2ac85de731873417a4",
    )
    checked(
        args.sources / "O2-O2_2011.cia",
        1938473,
        "8cc3ecc87bf7a02492b385ecc71abf279b058da853aea768825deb81237d5ee3",
    )
    asset = Path(
        "src/tfm_photochem/assets/historical_2020/midlatitude_equinox_quiet_radiative_background.csv"
    )
    checked(
        root / asset,
        None,
        "217fe7187c42a4ca8f590e1fa382ef815adffae6f5f1429816cea739f27c604f",
    )
    workflow = (root / ".github/workflows/m4d-source-acquisition.yml").read_text()
    code = textwrap.dedent(
        workflow.split("cat > acquisition/analyze.py <<'PY'\n", 1)[1].split(
            "\n          PY", 1
        )[0]
    )
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    if code_hash != "bc73629391971039d23ed0ac99739d17051655d4479ee56f7943e6967de7bc00":
        raise ValueError("existing CIA diagnostic changed; audit before executing")
    (work / "acquisition").mkdir(parents=True, exist_ok=True)
    for name in ("07_hit12.par", "O2-O2_2011.cia"):
        shutil.copyfile(args.sources / name, work / "acquisition" / name)
    (work / asset).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / asset, work / asset)
    script = work / "acquisition/analyze.py"
    script.write_text(code, encoding="utf-8")
    subprocess.run([sys.executable, str(script)], cwd=work, check=True)
    result = json.loads((work / "acquisition/cia_diagnostic.json").read_text())
    summary = {
        key: result[key]
        for key in (
            "sources",
            "source_meta",
            "diagnostic_semantics",
            "spatial_refinement",
            "summary_0125",
        )
    }
    summary["scope"] = (
        "existing HITRAN2012 thin-weight geometry witness; not retained gIRA"
    )
    summary["extracted_existing_diagnostic_sha256"] = code_hash
    summary["cases_per_spacing"] = 357
    summary["M4D_frozen"] = False
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(
        (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )


if __name__ == "__main__":
    main()
