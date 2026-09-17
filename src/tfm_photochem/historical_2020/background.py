"""Runtime-only loading and validation of frozen Milestone-4A assets."""

from __future__ import annotations

import csv
import hashlib
import json
from importlib.resources import files

import numpy as np

from .background_generation import (
    CASE_NAME,
    CHEM_FILENAME,
    METADATA_FILENAME,
    RAD_FILENAME,
)
from .background_types import BackgroundCase, ChemicalBackground, RadiativeBackground
from .prescribed_profiles import SOURCE_ASSET

ASSET_ROOT = ("assets", "historical_2020")


def _asset(name: str):
    return files("tfm_photochem").joinpath(*ASSET_ROOT, name)


def _sha256_resource(resource) -> str:
    digest = hashlib.sha256()
    with resource.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_numeric_csv(name: str) -> dict[str, np.ndarray]:
    with _asset(name).open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"empty packaged background asset: {name}")
    return {
        column: np.array([float(row[column]) for row in rows], dtype=np.float64)
        for column in rows[0]
    }


def load_baseline_background() -> BackgroundCase:
    """Load the frozen case with no pymsis import, time input, or network."""

    with _asset(METADATA_FILENAME).open("r", encoding="utf-8") as stream:
        metadata = json.load(stream)
    for name, expected in metadata["generated_asset_sha256"].items():
        actual = _sha256_resource(_asset(name))
        if actual != expected:
            raise ValueError(f"packaged asset hash mismatch for {name}")

    rad = _read_numeric_csv(RAD_FILENAME)
    chem = _read_numeric_csv(CHEM_FILENAME)
    radiative = RadiativeBackground(
        **{
            name: rad[name]
            for name in RadiativeBackground.__dataclass_fields__
        }
    )
    chemical = ChemicalBackground(
        **{name: chem[name] for name in ChemicalBackground.__dataclass_fields__}
    )
    if not np.array_equal(radiative.z_km, np.arange(151, dtype=np.float64)):
        raise ValueError("invalid radiative-support grid")
    if not np.array_equal(chemical.z_km, np.arange(50, 101, dtype=np.float64)):
        raise ValueError("invalid chemical grid")
    shared = slice(50, 101)
    pairs = (
        (chemical.T_K, radiative.T_K[shared]),
        (chemical.M_cm3, radiative.M_cm3[shared]),
        (chemical.O2_cm3, radiative.O2_model_cm3[shared]),
        (chemical.N2_cm3, radiative.N2_model_cm3[shared]),
        (chemical.CO2_cm3, radiative.CO2_model_cm3[shared]),
    )
    if any(not np.array_equal(left, right) for left, right in pairs):
        raise ValueError("chemical and radiative assets disagree at shared levels")
    return BackgroundCase(CASE_NAME, metadata, radiative, chemical)


def frozen_asset_hashes() -> dict[str, str]:
    """Return hashes for all four packaged M4A assets."""

    names = (SOURCE_ASSET, RAD_FILENAME, CHEM_FILENAME, METADATA_FILENAME)
    return {name: _sha256_resource(_asset(name)) for name in names}
