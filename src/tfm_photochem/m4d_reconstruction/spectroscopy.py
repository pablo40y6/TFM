"""Historical temperature/solar conventions and isolated profile primitives."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import wofz

from .sources import Line

C2 = 1.4387768775039336
K_B = 1.380649e-23
H = 6.62607015e-34
C = 299792458.0
AMU = 1.66053906660e-27
MASSES = {1: 31.98983, 2: 33.994076, 3: 32.994045}


@dataclass(frozen=True)
class SpectralSources:
    temperatures: np.ndarray
    partition_tables: dict[int, np.ndarray]
    solar_table: np.ndarray

    def partition(self, temperature: float, isotope: int) -> float:
        t = float(temperature)
        grid = self.temperatures
        if not np.isfinite(t) or not grid[0] <= t <= grid[-1]:
            raise ValueError("temperature outside historical TIPS support")
        # Pinned HAPI AtoB: three points at the ends, four in the interior.
        upper = max(1, int(np.searchsorted(grid, t, side="left")))
        if upper == 1:
            indices = np.arange(3)
        elif upper == len(grid) - 1:
            indices = np.arange(len(grid) - 3, len(grid))
        else:
            indices = np.arange(upper - 2, upper + 2)
        nodes = grid[indices]
        result = 0.0
        for j, index in enumerate(indices):
            others = np.delete(nodes, j)
            result += self.partition_tables[isotope][index] * np.prod(
                (t - others) / (nodes[j] - others)
            )
        return float(result)

    def strengths(self, lines: tuple[Line, ...], temperature: float) -> np.ndarray:
        t = float(temperature)
        qratios = {
            iso: self.partition(296.0, iso) / self.partition(t, iso)
            for iso in (1, 2, 3)
        }
        nu = np.array([line.nu for line in lines])
        energy = np.array([line.elower for line in lines])
        return (
            np.array([line.sw * qratios[line.isotope] for line in lines])
            * np.exp(-C2 * energy * (1 / t - 1 / 296.0))
            * (-np.expm1(-C2 * nu / t))
            / (-np.expm1(-C2 * nu / 296.0))
        )

    def photons(self, nu: np.ndarray) -> np.ndarray:
        wavelength = 1e7 / np.asarray(nu, dtype=float)
        table = self.solar_table
        if np.any(wavelength < table[0, 0]) or np.any(wavelength > table[-1, 0]):
            raise ValueError("solar interpolation outside Wehrli support")
        irradiance = np.interp(wavelength, table[:, 0], table[:, 1])
        return irradiance / (H * C / (wavelength * 1e-9)) / 1e4 * wavelength**2 / 1e7


def doppler_sigma(lines: tuple[Line, ...], temperature: float) -> np.ndarray:
    """Gaussian standard deviation in cm^-1 (not HWHM)."""
    mass = np.array([MASSES[line.isotope] for line in lines]) * AMU
    return np.array([line.nu for line in lines]) / C * np.sqrt(K_B * temperature / mass)


def classic_parameters(
    lines: tuple[Line, ...],
    temperature: float,
    pressure_atm: float,
    oxygen_pressure_atm: float,
    shifts: bool = True,
    diluent: str = "requested_partial",
) -> tuple:
    t, p, po2 = float(temperature), float(pressure_atm), float(oxygen_pressure_atm)
    if not np.all(np.isfinite([t, p, po2])) or t <= 0 or not 0 <= po2 <= p:
        raise ValueError("invalid shell temperature/partial pressure")
    air = np.array([line.gamma_air for line in lines])
    self_width = np.array([line.gamma_self for line in lines])
    power = (296 / t) ** np.array([line.n_air for line in lines])
    if diluent == "requested_partial":
        gamma = power * (air * (p - po2) + self_width * po2)
    elif diluent == "branch_air_only":
        gamma = power * air * p
    else:
        raise ValueError("unknown diluent convention")
    shift = np.array([line.delta_air * p if shifts else 0.0 for line in lines])
    return gamma, shift


def complex_voigt(detuning, sigma, gamma):
    return wofz(
        (np.asarray(detuning) + 1j * np.asarray(gamma))
        / (np.asarray(sigma) * np.sqrt(2))
    ) / (np.asarray(sigma) * np.sqrt(2 * np.pi))


def complex_sdv(detuning, sigma: float, gamma: float, gamma2: float):
    """Independent zero-narrowing Tran/Drouin reduction, stable rational root.

    Gam2=S*Gam0, Shift2=0, anuVC=eta=0. Sigma is Gaussian standard deviation.
    Dispersion sign agrees with the imaginary part of the pinned HAPI profile.
    """
    if sigma <= 0 or gamma < 0 or not 0 <= gamma2 < gamma / 1.5 and gamma2 != 0:
        raise ValueError("invalid SDV profile parameters")
    if gamma2 == 0:
        return complex_voigt(detuning, sigma, gamma)
    width = sigma * np.sqrt(2)
    x = (gamma - 1.5 * gamma2 - 1j * np.asarray(detuning)) / gamma2
    yroot = width / (2 * gamma2)
    root = np.sqrt(x + yroot * yroot)
    z1 = x / (root + yroot)  # avoids subtracting nearly equal large numbers
    z2 = root + yroot
    return (wofz(1j * z1) - wofz(1j * z2)) / (width * np.sqrt(np.pi))


def drouin_parameters(
    row: tuple, temperature: float, pressure_atm: float, shifts: bool = True
) -> tuple[float, float, float]:
    _, _, _, gf, nf, gs, ns, df, dft, ds, dst, speed = row
    gamma = pressure_atm * (
        0.79 * gf * (296 / temperature) ** nf + 0.21 * gs * (296 / temperature) ** ns
    )
    shift = (
        pressure_atm
        * (
            0.79 * (df + (temperature - 296) * dft)
            + 0.21 * (ds + (temperature - 296) * dst)
        )
        if shifts
        else 0.0
    )
    return gamma, speed * gamma, shift


def mixing_y(values: tuple, temperature: float, low_policy: str = "clamp") -> float:
    t = float(temperature)
    if not np.isfinite(t) or t <= 0 or t > 340:
        raise ValueError("DESIGN BLOCKER: Y temperature outside supported policy")
    if low_policy not in ("clamp", "linear", "zero"):
        raise ValueError("unknown low-temperature Y policy")
    if t < 200:
        if low_policy == "zero":
            return 0.0
        if low_policy == "linear":
            return float(values[0] + (values[1] - values[0]) * (t - 200) / 50)
    return float(np.interp(t, [200, 250, 296, 340], values))


def drouin_mixed_profile(
    detuning,
    sigma: float,
    gamma: float,
    gamma2: float,
    y_per_atm: float,
    pressure_atm: float,
) -> np.ndarray:
    """Drouin SDV with first-order Rosenkranz line mixing.

    The historical Table-22 coefficient is pressure-normalized. Following the
    executable Rosenkranz convention used with the complex qSD/HT profile, the
    dimensionless in-profile coefficient is Y = y_per_atm * pressure_atm and
    absorption is Re(F) + Y*Im(F).

    ``detuning`` is already relative to the pressure-shifted line centre.
    Individual first-order mixed-line contributions are not required to remain
    nonnegative in their far wings; physical nonnegativity is a property of the
    summed band opacity and is checked at the transfer layer.
    """
    p = float(pressure_atm)
    y = float(y_per_atm)
    if not np.isfinite(p) or p < 0 or not np.isfinite(y):
        raise ValueError("invalid line-mixing pressure/coefficient")
    profile = complex_sdv(detuning, sigma, gamma, gamma2)
    return profile.real + (p * y) * profile.imag


def voigt_sum(
    nodes,
    lines: tuple[Line, ...],
    sources: SpectralSources,
    temperature: float,
    pressure_atm: float,
    oxygen_pressure_atm: float,
    shifts: bool = True,
    diluent: str = "requested_partial",
) -> np.ndarray:
    strengths = sources.strengths(lines, temperature)
    sigma = doppler_sigma(lines, temperature)
    gamma, shift = classic_parameters(
        lines, temperature, pressure_atm, oxygen_pressure_atm, shifts, diluent
    )
    out = np.zeros_like(nodes, dtype=float)
    for i, line in enumerate(lines):
        out += (
            strengths[i]
            * complex_voigt(
                np.asarray(nodes) - line.nu - shift[i], sigma[i], gamma[i]
            ).real
        )
    return out
