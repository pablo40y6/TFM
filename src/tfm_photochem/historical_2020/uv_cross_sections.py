"""JPL Evaluation 18 H2O and H2O2 cross-section treatment."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .uv_assets import CrossSectionTable, load_historical_uv_assets

FloatArray = NDArray[np.float64]
H2O2_LYMAN_ALPHA_SIGMA_CM2 = 9.8e-18
H2O2_A = np.array(
    [
        6.4761e4,
        -9.2170972e2,
        4.535649,
        -4.4589016e-3,
        -4.035101e-5,
        1.6878206e-7,
        -2.652014e-10,
        1.5534675e-13,
    ]
)
H2O2_B = np.array([6.8123e3, -5.1351e1, 1.1522e-1, -3.0493e-5, -1.0924e-7])
H2O2_A.setflags(write=False)
H2O2_B.setflags(write=False)


def h2o_cross_section(wavelength_nm: object) -> FloatArray:
    """Linearly interpolate JPL18 Table 4B-3; return zero outside 121--198 nm."""

    wavelength = np.asarray(wavelength_nm, dtype=np.float64)
    if not np.all(np.isfinite(wavelength)):
        raise ValueError("wavelength_nm must be finite")
    table = load_historical_uv_assets().h2o
    sigma = np.zeros_like(wavelength)
    mask = (wavelength >= 121.0) & (wavelength <= 198.0)
    sigma[mask] = np.interp(wavelength[mask], table.wavelength_nm, table.sigma_cm2)
    return sigma


def h2o_channel_yields(wavelength_nm: object) -> tuple[FloatArray, FloatArray]:
    """Return the frozen historical_2020 reduced two-channel H2O yields.

    These Brasseur/JPL-informed model approximations are not exact JPL18
    quantum yields and do not introduce any additional product channels.
    """

    wavelength = np.asarray(wavelength_nm, dtype=np.float64)
    if not np.all(np.isfinite(wavelength)):
        raise ValueError("wavelength_nm must be finite")
    yield_a = np.zeros_like(wavelength)
    yield_b = np.zeros_like(wavelength)
    short = (wavelength >= 121.0) & (wavelength < 147.0)
    long = (wavelength >= 147.0) & (wavelength <= 198.0)
    yield_a[short], yield_b[short] = 0.89, 0.11
    yield_a[long] = 1.0
    return yield_a, yield_b


def _h2o2_polynomial(
    wavelength_nm: FloatArray, temperature_K: FloatArray
) -> FloatArray:
    chi = 1.0 / (1.0 + np.exp(-1265.0 / temperature_K))
    polynomial_a = np.polynomial.polynomial.polyval(wavelength_nm, H2O2_A)
    polynomial_b = np.polynomial.polynomial.polyval(wavelength_nm, H2O2_B)
    return 1.0e-21 * (chi * polynomial_a + (1.0 - chi) * polynomial_b)


def h2o2_cross_section(
    wavelength_nm: object,
    temperature_K: object,
    *,
    table: CrossSectionTable | None = None,
) -> tuple[FloatArray, FloatArray, NDArray[np.bool_]]:
    """Evaluate JPL18 Tables 4B-5/4B-6 with the specified cold clamp.

    Returns ``(sigma_cm2, temperature_used_K, clamped_to_200K)`` with the
    broadcast shape of wavelength and temperature.
    """

    wavelength, temperature = np.broadcast_arrays(
        np.asarray(wavelength_nm, dtype=np.float64),
        np.asarray(temperature_K, dtype=np.float64),
    )
    if not np.all(np.isfinite(wavelength)) or not np.all(np.isfinite(temperature)):
        raise ValueError("wavelength_nm and temperature_K must be finite")
    if np.any(temperature <= 0.0):
        raise ValueError("temperature_K must be strictly positive")
    if np.any(temperature > 400.0):
        raise ValueError("JPL18 H2O2 parameterization is invalid above 400 K")
    used = np.maximum(temperature, 200.0)
    clamped = temperature < 200.0
    sigma = np.zeros_like(wavelength)
    source = load_historical_uv_assets().h2o2 if table is None else table
    tabulated = (wavelength >= 190.0) & (wavelength < 260.0)
    sigma[tabulated] = np.interp(
        wavelength[tabulated], source.wavelength_nm, source.sigma_cm2
    )
    polynomial = (wavelength >= 260.0) & (wavelength <= 350.0)
    sigma[polynomial] = _h2o2_polynomial(wavelength[polynomial], used[polynomial])
    if np.any(sigma < 0.0) or not np.all(np.isfinite(sigma)):
        raise FloatingPointError("invalid H2O2 cross section")
    return sigma, used, clamped
