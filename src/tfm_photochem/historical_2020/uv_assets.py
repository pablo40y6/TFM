"""Validated immutable source data for the historical-2020 UV model."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass, fields
from functools import lru_cache
from importlib.resources import files

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]

ASSET_ROOT = ("assets", "historical_2020")
BACKBONE_FILENAME = "uv_spectral_backbone_2017.csv"
BACKBONE_METADATA_FILENAME = "uv_spectral_backbone_2017_metadata.json"
H2O_FILENAME = "jpl18_h2o_cross_sections_298k.csv"
H2O2_FILENAME = "jpl18_h2o2_cross_sections_298k.csv"
JPL_METADATA_FILENAME = "jpl18_uv_cross_sections_metadata.json"


def _readonly(value: object, length: int, name: str) -> FloatArray:
    array = np.array(value, dtype=np.float64, copy=True)
    if array.shape != (length,) or not np.all(np.isfinite(array)):
        raise ValueError(f"invalid {name} array")
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class UVSpectralBackbone:
    source_matlab_index: FloatArray
    wavelength_nm: FloatArray
    solar_photon_irradiance_per_element: FloatArray
    sigma_O_cm2: FloatArray
    sigma_O2_cm2: FloatArray
    sigma_O3_cm2: FloatArray
    sigma_N2_cm2: FloatArray

    def __post_init__(self) -> None:
        for field in fields(self):
            object.__setattr__(
                self, field.name, _readonly(getattr(self, field.name), 125, field.name)
            )


@dataclass(frozen=True)
class CrossSectionTable:
    wavelength_nm: FloatArray
    sigma_cm2: FloatArray

    def __post_init__(self) -> None:
        size = np.asarray(self.wavelength_nm).size
        object.__setattr__(
            self, "wavelength_nm", _readonly(self.wavelength_nm, size, "wavelength_nm")
        )
        object.__setattr__(
            self, "sigma_cm2", _readonly(self.sigma_cm2, size, "sigma_cm2")
        )
        if size < 2 or np.any(np.diff(self.wavelength_nm) <= 0.0):
            raise ValueError("cross-section wavelengths must be strictly increasing")
        if np.any(self.sigma_cm2 < 0.0):
            raise ValueError("cross sections must be non-negative")


@dataclass(frozen=True)
class HistoricalUVAssets:
    backbone: UVSpectralBackbone
    h2o: CrossSectionTable
    h2o2: CrossSectionTable


def _asset(name: str):
    return files("tfm_photochem").joinpath(*ASSET_ROOT, name)


def _sha256(name: str) -> str:
    digest = hashlib.sha256()
    with _asset(name).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_csv(name: str) -> dict[str, FloatArray]:
    with _asset(name).open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"empty UV asset: {name}")
    return {
        key: np.array([float(row[key]) for row in rows], dtype=np.float64)
        for key in rows[0]
    }


def _verify_metadata(name: str) -> None:
    with _asset(name).open("r", encoding="utf-8") as stream:
        metadata = json.load(stream)
    if name == BACKBONE_METADATA_FILENAME:
        expected_hashes = {metadata["derived_asset"]: metadata["derived_asset_sha256"]}
    else:
        expected_hashes = {
            metadata[species]["asset"]: metadata[species]["asset_sha256"]
            for species in ("h2o", "h2o2")
        }
    for asset_name, expected in expected_hashes.items():
        if _sha256(asset_name) != expected:
            raise ValueError(f"packaged UV asset hash mismatch for {asset_name}")


@lru_cache(maxsize=1)
def load_historical_uv_assets() -> HistoricalUVAssets:
    """Load and validate the packaged M4C spectral source assets."""

    _verify_metadata(BACKBONE_METADATA_FILENAME)
    _verify_metadata(JPL_METADATA_FILENAME)
    raw = _read_csv(BACKBONE_FILENAME)
    backbone = UVSpectralBackbone(**raw)
    if not np.array_equal(backbone.source_matlab_index, np.arange(1, 126)):
        raise ValueError("backbone source indices are not exactly 1..125")
    if backbone.wavelength_nm[27] != 121.567:
        raise ValueError("MATLAB source element 28 is not exactly 121.567 nm")
    if not (backbone.wavelength_nm[20] == backbone.wavelength_nm[21] == 117.30308):
        raise ValueError("the duplicate 117.30308-nm source rows were not preserved")
    h2o_raw = _read_csv(H2O_FILENAME)
    h2o2_raw = _read_csv(H2O2_FILENAME)
    h2o = CrossSectionTable(h2o_raw["wavelength_nm"], h2o_raw["sigma_cm2"])
    h2o2 = CrossSectionTable(h2o2_raw["wavelength_nm"], h2o2_raw["sigma_cm2"])
    if h2o.wavelength_nm.size != 98 or h2o2.wavelength_nm.size != 33:
        raise ValueError("unexpected JPL 18 table length")
    return HistoricalUVAssets(backbone, h2o, h2o2)


def uv_asset_hashes() -> dict[str, str]:
    """Return SHA256 values for all five packaged M4C source assets."""

    names = (
        BACKBONE_FILENAME,
        BACKBONE_METADATA_FILENAME,
        H2O_FILENAME,
        H2O2_FILENAME,
        JPL_METADATA_FILENAME,
    )
    return {name: _sha256(name) for name in names}
