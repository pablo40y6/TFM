"""Loader and integrity checks for the frozen January 2017 spectrum asset."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from scipy.io import loadmat

EXPECTED_SHA256 = "a98567c4f971721cec4197ad7ea17182e95df78c3a0eea880acb08fc6d560424"
EXPECTED_VARIABLES = ("irrad", "sN2", "sO", "sO2", "sO3", "wave")
EXPECTED_LENGTH = 125
LYA_ZERO_BASED_INDEX = 27
LYA_WAVELENGTH_NM = 121.567


@dataclass(frozen=True)
class LegacySigma:
    """Spectral grid, irradiance, and absorption cross sections."""

    wave_nm: NDArray[np.float64]
    irradiance: NDArray[np.float64]
    sigma_n2_cm2: NDArray[np.float64]
    sigma_o_cm2: NDArray[np.float64]
    sigma_o2_cm2: NDArray[np.float64]
    sigma_o3_cm2: NDArray[np.float64]
    sha256: str
    source_path: Path


def default_sigma_path() -> Path:
    """Return the packaged legacy asset path."""

    return Path(files("tfm_photochem").joinpath("assets/legacy_2017/sigma.mat"))


def _readonly_vector(raw: object, name: str) -> NDArray[np.float64]:
    vector = np.asarray(raw, dtype=np.float64).ravel(order="F").copy()
    if vector.shape != (EXPECTED_LENGTH,):
        raise ValueError(f"{name} must contain {EXPECTED_LENGTH} values; got {vector.shape}")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} contains non-finite values")
    vector.setflags(write=False)
    return vector


def load_legacy_sigma(
    path: str | Path | None = None, *, verify_hash: bool = True
) -> LegacySigma:
    """Load and validate the unmodified MATLAB 5.0 legacy asset.

    The hash check is enabled by default so accidental resaves or substitutions
    fail loudly. Set ``verify_hash=False`` only for explicit diagnostic work.
    """

    source = Path(path) if path is not None else default_sigma_path()
    digest = sha256(source.read_bytes()).hexdigest()
    if verify_hash and digest != EXPECTED_SHA256:
        raise ValueError(
            f"Unexpected sigma.mat SHA256 {digest}; expected {EXPECTED_SHA256}"
        )

    raw = loadmat(source)
    missing = sorted(set(EXPECTED_VARIABLES) - set(raw))
    if missing:
        raise ValueError(f"sigma.mat is missing variables: {missing}")

    wave = _readonly_vector(raw["wave"], "wave")
    irradiance = _readonly_vector(raw["irrad"], "irrad")
    sigma_n2 = _readonly_vector(raw["sN2"], "sN2")
    sigma_o = _readonly_vector(raw["sO"], "sO")
    sigma_o2 = _readonly_vector(raw["sO2"], "sO2")
    sigma_o3 = _readonly_vector(raw["sO3"], "sO3")

    if wave[0] != 7.5 or wave[-1] != 360.0:
        raise ValueError("Legacy wavelength endpoints are not 7.5 and 360 nm")
    if np.any(np.diff(wave) < 0):
        raise ValueError("Legacy wavelength grid must be nondecreasing")
    if wave[LYA_ZERO_BASED_INDEX] != LYA_WAVELENGTH_NM:
        raise ValueError("MATLAB element 28 is not the 121.567 nm Lyman-alpha bin")
    for name, vector in {
        "irrad": irradiance,
        "sN2": sigma_n2,
        "sO": sigma_o,
        "sO2": sigma_o2,
        "sO3": sigma_o3,
    }.items():
        if np.any(vector < 0):
            raise ValueError(f"{name} contains negative values")

    return LegacySigma(
        wave_nm=wave,
        irradiance=irradiance,
        sigma_n2_cm2=sigma_n2,
        sigma_o_cm2=sigma_o,
        sigma_o2_cm2=sigma_o2,
        sigma_o3_cm2=sigma_o3,
        sha256=digest,
        source_path=source,
    )

