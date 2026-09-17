"""Literal three-pass ozone equilibrium calculation from ``mkozone.m``."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .geometry import path_length_matrix
from .parameters import value
from .photolysis import _profile
from .sigma import LegacySigma, load_legacy_sigma


@dataclass(frozen=True)
class LegacyOzoneIterations:
    """The three fixed-point estimates produced by the MATLAB routine."""

    iteration_1_cm3: NDArray[np.float64]
    iteration_2_cm3: NDArray[np.float64]
    iteration_3_cm3: NDArray[np.float64]
    j_o3_iteration_1_s1: NDArray[np.float64]
    j_o3_iteration_2_s1: NDArray[np.float64]
    j_o3_iteration_3_s1: NDArray[np.float64]


def _j_o3_without_legacy_shadow_mask(
    o: NDArray[np.float64],
    o2: NDArray[np.float64],
    o3: NDArray[np.float64] | None,
    n2: NDArray[np.float64],
    path_cm: NDArray[np.float64],
    spectrum: LegacySigma,
) -> NDArray[np.float64]:
    absorbers = (
        np.outer(o, spectrum.sigma_o_cm2)
        + np.outer(o2, spectrum.sigma_o2_cm2)
        + np.outer(n2, spectrum.sigma_n2_cm2)
    )
    if o3 is not None:
        absorbers = absorbers + np.outer(o3, spectrum.sigma_o3_cm2)
    tau = absorbers.T @ path_cm.T
    # mkozone.m does not contain Jfactors.m's JO3(tau == 0) = 0 line.
    return np.sum(
        spectrum.irradiance[:, None]
        * spectrum.sigma_o3_cm2[:, None]
        * np.exp(-tau),
        axis=0,
    )


def mkozone_iterations(
    o_cm3: ArrayLike,
    o2_cm3: ArrayLike,
    n2_cm3: ArrayLike,
    temperature_k: ArrayLike,
    heights_km: ArrayLike,
    solar_zenith_angle_deg: float,
    *,
    sigma: LegacySigma | None = None,
) -> LegacyOzoneIterations:
    """Return all three literal fixed-point passes of ``mkozone.m``."""

    heights = np.asarray(heights_km, dtype=np.float64).reshape(-1)
    size = heights.size
    o = _profile("O", o_cm3, size)
    o2 = _profile("O2", o2_cm3, size)
    n2 = _profile("N2", n2_cm3, size)
    temperature = _profile("T", temperature_k, size)
    if np.any(temperature <= 0.0):
        raise ValueError("Temperature must be strictly positive")

    spectrum = sigma if sigma is not None else load_legacy_sigma()
    path_cm = path_length_matrix(heights, solar_zenith_angle_deg) * float(
        value("km_to_cm")
    )

    # Literal legacy law: 6e-34 * exp(300/T)^2.3.
    k_a = float(value("o_o2_m_preexponential")) * np.exp(
        float(value("o_o2_m_temperature_scale")) / temperature
    ) ** float(value("o_o2_m_exponential_power"))
    k_b = float(value("o_o3_preexponential")) * np.exp(
        -float(value("o_o3_activation_temperature")) / temperature
    )
    m = o2 + n2

    estimates: list[NDArray[np.float64]] = []
    j_values: list[NDArray[np.float64]] = []
    previous: NDArray[np.float64] | None = None
    for _ in range(int(value("mkozone_fixed_point_passes"))):
        j_o3 = _j_o3_without_legacy_shadow_mask(
            o, o2, previous, n2, path_cm, spectrum
        )
        previous = k_a * m * o2 * o / (j_o3 + k_b * o)
        j_values.append(j_o3)
        estimates.append(previous)

    return LegacyOzoneIterations(
        iteration_1_cm3=estimates[0],
        iteration_2_cm3=estimates[1],
        iteration_3_cm3=estimates[2],
        j_o3_iteration_1_s1=j_values[0],
        j_o3_iteration_2_s1=j_values[1],
        j_o3_iteration_3_s1=j_values[2],
    )


def mkozone(
    o_cm3: ArrayLike,
    o2_cm3: ArrayLike,
    n2_cm3: ArrayLike,
    temperature_k: ArrayLike,
    heights_km: ArrayLike,
    solar_zenith_angle_deg: float,
    *,
    sigma: LegacySigma | None = None,
) -> NDArray[np.float64]:
    """Return the third and final ozone estimate from ``mkozone.m``."""

    return mkozone_iterations(
        o_cm3,
        o2_cm3,
        n2_cm3,
        temperature_k,
        heights_km,
        solar_zenith_angle_deg,
        sigma=sigma,
    ).iteration_3_cm3
