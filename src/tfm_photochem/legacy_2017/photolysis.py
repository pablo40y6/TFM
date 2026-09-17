"""Numerical reproduction of the spectral calculations in ``Jfactors.m``."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .geometry import path_length_matrix
from .parameters import value
from .sigma import LegacySigma, load_legacy_sigma


@dataclass(frozen=True)
class LegacyJFactors:
    """Legacy photolysis frequencies and wavelength-resolved contributions."""

    j_hart_s1: NDArray[np.float64]
    j_src_s1: NDArray[np.float64]
    j_lya_s1: NDArray[np.float64]
    j_o3_total_s1: NDArray[np.float64]
    j_o2_total_s1: NDArray[np.float64]
    jo3_spectral_s1: NDArray[np.float64]
    jo2_spectral_s1: NDArray[np.float64]
    optical_depth: NDArray[np.float64]


def _profile(name: str, values: ArrayLike, size: int) -> NDArray[np.float64]:
    result = np.asarray(values, dtype=np.float64).reshape(-1)
    if result.shape != (size,):
        raise ValueError(f"{name} must have shape ({size},), got {result.shape}")
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} contains non-finite values")
    return result


def optical_depth(
    o_cm3: ArrayLike,
    o2_cm3: ArrayLike,
    o3_cm3: ArrayLike,
    n2_cm3: ArrayLike,
    heights_km: ArrayLike,
    solar_zenith_angle_deg: float,
    *,
    sigma: LegacySigma | None = None,
) -> NDArray[np.float64]:
    """Return wavelength-by-altitude optical depth exactly as in ``Jfactors.m``."""

    heights = np.asarray(heights_km, dtype=np.float64).reshape(-1)
    size = heights.size
    o = _profile("O", o_cm3, size)
    o2 = _profile("O2", o2_cm3, size)
    o3 = _profile("O3", o3_cm3, size)
    n2 = _profile("N2", n2_cm3, size)
    spectrum = sigma if sigma is not None else load_legacy_sigma()

    path_cm = path_length_matrix(heights, solar_zenith_angle_deg) * float(
        value("km_to_cm")
    )
    absorbers = (
        np.outer(o, spectrum.sigma_o_cm2)
        + np.outer(o2, spectrum.sigma_o2_cm2)
        + np.outer(o3, spectrum.sigma_o3_cm2)
        + np.outer(n2, spectrum.sigma_n2_cm2)
    )
    # Direct translation of MATLAB: (absorbers)' * pathl'.
    return absorbers.T @ path_cm.T


def j_factors(
    o_cm3: ArrayLike,
    o2_cm3: ArrayLike,
    o3_cm3: ArrayLike,
    n2_cm3: ArrayLike,
    heights_km: ArrayLike,
    solar_zenith_angle_deg: float,
    *,
    sigma: LegacySigma | None = None,
) -> LegacyJFactors:
    """Reproduce the five numerical outputs of ``Jfactors.m``.

    MATLAB's final ``ndgrid(x, y, J, t)`` packaging is intentionally omitted;
    this function returns its physically meaningful vertical vectors. The
    wavelength masks, Lyman-alpha element, sums, and ``tau == 0`` shadow mask
    are literal reproductions.
    """

    spectrum = sigma if sigma is not None else load_legacy_sigma()
    tau = optical_depth(
        o_cm3,
        o2_cm3,
        o3_cm3,
        n2_cm3,
        heights_km,
        solar_zenith_angle_deg,
        sigma=spectrum,
    )
    attenuated = spectrum.irradiance[:, None] * np.exp(-tau)
    jo3 = spectrum.sigma_o3_cm2[:, None] * attenuated
    jo2 = spectrum.sigma_o2_cm2[:, None] * attenuated

    # Exact legacy shadow convention. This also masks any genuinely zero-tau
    # spectral/altitude element; it is intentionally not generalized here.
    zero_tau = tau == 0.0
    jo3[zero_tau] = 0.0
    jo2[zero_tau] = 0.0

    wave = spectrum.wave_nm
    hartley = (wave > float(value("hartley_lower_exclusive"))) & (
        wave < float(value("hartley_upper_exclusive"))
    )
    src = (wave > float(value("src_lower_exclusive"))) & (
        wave < float(value("src_upper_exclusive"))
    )
    lya = int(value("lya_matlab_index")) - 1

    return LegacyJFactors(
        j_hart_s1=np.sum(jo3[hartley, :], axis=0),
        j_src_s1=np.sum(jo2[src, :], axis=0),
        j_lya_s1=jo2[lya, :].copy(),
        j_o3_total_s1=np.sum(jo3, axis=0),
        j_o2_total_s1=np.sum(jo2, axis=0),
        jo3_spectral_s1=jo3,
        jo2_spectral_s1=jo2,
        optical_depth=tau,
    )
