"""Shell-local classic Voigt transfer, with all accepted absorbers at every node.

The optional moment evaluator accelerates distant *contributions*, never drops
lines. Its order/range must be validated against exact scipy Voigt before use.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import roots_legendre

from ..historical_2020.background import load_baseline_background
from ..historical_2020.uv_geometry import EARTH_RADIUS_KM, TOP_OF_COLUMN_KM
from .cia import HistoricalCIA, temperature_weights
from .sources import Line
from .spectroscopy import (
    K_B,
    SpectralSources,
    classic_parameters,
    complex_voigt,
    doppler_sigma,
)


@dataclass(frozen=True)
class Atmosphere:
    edges: np.ndarray
    temperature: np.ndarray
    pressure: np.ndarray
    oxygen_pressure: np.ndarray
    oxygen: np.ndarray
    nitrogen: np.ndarray


def atmosphere(step_km: float) -> Atmosphere:
    if (
        not np.isfinite(step_km)
        or step_km <= 0
        or abs(150 / step_km - round(150 / step_km)) > 1e-10
    ):
        raise ValueError("step must exactly subdivide the accepted column")
    source = load_baseline_background().radiative
    edges = np.linspace(0, 150, round(150 / step_km) + 1)
    mids = (edges[:-1] + edges[1:]) / 2
    t = np.interp(mids, source.z_km, source.T_K)
    m = np.interp(mids, source.z_km, source.M_cm3)
    o2 = np.interp(mids, source.z_km, source.O2_model_cm3)
    n2 = np.interp(mids, source.z_km, source.N2_model_cm3)
    return Atmosphere(
        edges, t, m * 1e6 * K_B * t / 101325, o2 * 1e6 * K_B * t / 101325, o2, n2
    )


def path_lengths(
    target_z: float, sza_deg: float, edges: np.ndarray
) -> tuple[bool, np.ndarray]:
    if not (
        np.isfinite(target_z)
        and 0 <= target_z <= TOP_OF_COLUMN_KM
        and np.isfinite(sza_deg)
        and 0 <= sza_deg <= 180
    ):
        raise ValueError("invalid target or solar angle")
    radius = EARTH_RADIUS_KM + target_z
    theta = np.deg2rad(sza_deg)
    u0, impact = radius * np.cos(theta), radius * np.sin(theta)
    tolerance = 16 * np.finfo(float).eps * EARTH_RADIUS_KM
    if sza_deg > 90 and impact < EARTH_RADIUS_KM - tolerance:
        return False, np.zeros(len(edges) - 1)
    top = np.sqrt(max((EARTH_RADIUS_KM + TOP_OF_COLUMN_KM) ** 2 - impact**2, 0))
    radii = EARTH_RADIUS_KM + edges
    root = np.sqrt(np.maximum(radii**2 - impact**2, 0))
    cumulative = np.where(
        radii >= impact - tolerance,
        np.maximum(np.minimum(top, root) - np.maximum(u0, -root), 0),
        0,
    )
    lengths = np.diff(cumulative)
    if np.min(lengths) < -tolerance or not np.isclose(
        lengths.sum(), top - u0, rtol=2e-13, atol=2e-10
    ):
        raise FloatingPointError("spherical intersections failed closure")
    lengths[np.abs(lengths) <= tolerance] = 0
    return True, lengths


def target_quadrature(
    lines: tuple[Line, ...],
    core_order: int = 64,
    wing_order: int = 12,
    support: float = 3.84,
) -> tuple:
    if support < 0.12 or core_order < 8 or wing_order < 4:
        raise ValueError("invalid spectral quadrature")
    positive = [0.06]
    while positive[-1] < support:
        positive.append(min(2 * positive[-1], support))
    segments = [(-0.06, 0.06, core_order)]
    for low, high in zip(positive[:-1], positive[1:]):
        segments.extend([(-high, -low, wing_order), (low, high, wing_order)])
    delta, weights = [], []
    for low, high, order in segments:
        x, w = roots_legendre(order)
        delta.extend((low + high) / 2 + x * (high - low) / 2)
        weights.extend(w * (high - low) / 2)
    delta, weights = np.array(delta), np.array(weights)
    indices = np.repeat(np.arange(len(lines)), len(delta))
    nu = np.array([line.nu for line in lines])
    return (
        nu[indices] + np.tile(delta, len(lines)),
        np.tile(weights, len(lines)),
        indices,
    )


@dataclass
class VoigtColumn:
    lines: tuple[Line, ...]
    sources: SpectralSources
    shells: Atmosphere
    shifts: bool = True
    diluent: str = "requested_partial"
    used_shells: np.ndarray | None = None

    def __post_init__(self):
        if self.used_shells is not None:
            selected = self.used_shells
            original = self.shells
            self.shells = Atmosphere(
                original.edges,
                *(
                    getattr(original, field)[selected]
                    for field in (
                        "temperature",
                        "pressure",
                        "oxygen_pressure",
                        "oxygen",
                        "nitrogen",
                    )
                ),
            )
        self.nu = np.array([line.nu for line in self.lines])
        self.strength = np.array(
            [self.sources.strengths(self.lines, t) for t in self.shells.temperature]
        )
        self.sigma = np.array(
            [doppler_sigma(self.lines, t) for t in self.shells.temperature]
        )
        parameters = [
            classic_parameters(self.lines, t, p, po2, self.shifts, self.diluent)
            for t, p, po2 in zip(
                self.shells.temperature,
                self.shells.pressure,
                self.shells.oxygen_pressure,
            )
        ]
        self.gamma = np.array([pair[0] for pair in parameters])
        self.shift = np.array([pair[1] for pair in parameters])
        self._far_coefficients = {}

    def cross_section(
        self,
        nodes: np.ndarray,
        order: int = 8,
        near_cm1: float = 2.0,
        exact: bool = False,
    ) -> np.ndarray:
        """Return node x shell cross sections; all lines included in either mode."""
        nodes = np.asarray(nodes)
        out = np.zeros((len(nodes), len(self.shells.temperature)))
        if not exact:
            # E[(u+shift-i*gamma)^m], u Gaussian with variance sigma^2.
            # The distant Voigt series is Re[i*sum M_m/detuning^(m+1)]/pi.
            if order < 2 or near_cm1 <= 0:
                raise ValueError("invalid distant-profile controls")
            distance = nodes[:, None] - self.nu[None, :]
            inverse = np.divide(
                1,
                distance,
                out=np.zeros_like(distance),
                where=np.abs(distance) >= near_cm1,
            )
            power = inverse.copy()
            if order not in self._far_coefficients:
                c = self.shift - 1j * self.gamma
                previous = np.ones_like(c)
                current = c.copy()
                coefficients = []
                for m in range(1, order + 1):
                    coefficients.append(self.strength * (-current.imag) / np.pi)
                    previous, current = (
                        current,
                        c * current + m * self.sigma**2 * previous,
                    )
                self._far_coefficients[order] = coefficients
            for coefficient in self._far_coefficients[order]:
                power *= inverse
                out += power @ coefficient.T
        for i, centre in enumerate(self.nu):
            use = (
                np.ones(len(nodes), dtype=bool)
                if exact
                else np.abs(nodes - centre) < near_cm1
            )
            if not np.any(use):
                continue
            detuning = nodes[use, None] - centre - self.shift[None, :, i]
            profiles = complex_voigt(
                detuning, self.sigma[None, :, i], self.gamma[None, :, i]
            ).real
            out[use] += profiles * self.strength[None, :, i]
        if not np.all(np.isfinite(out)) or np.any(out < 0):
            raise FloatingPointError("invalid total Voigt absorption")
        return out


def cia_path_coefficients(shells: Atmosphere, cases: list[tuple]) -> tuple:
    lengths = np.array([path_lengths(z, sza, shells.edges)[1] for z, sza in cases])
    binary_column = lengths * 1e5 * shells.oxygen * (shells.oxygen + shells.nitrogen)
    weights = temperature_weights(shells.temperature)
    outside = (shells.temperature < 253) | (shells.temperature > 296)
    return (
        binary_column @ weights,
        binary_column[:, ~outside] @ weights[~outside],
        binary_column[:, outside].sum(axis=1),
    )


def compute_classic_rates(
    lines: tuple[Line, ...],
    sources: SpectralSources,
    cases: list[tuple[float, float]],
    step_km: float = 0.125,
    core_order: int = 64,
    wing_order: int = 12,
    support: float = 3.84,
    shifts: bool = True,
    diluent: str = "requested_partial",
    cia: HistoricalCIA | None = None,
    cia_step_km: float = 0.0625,
    far_order: int = 8,
    near_cm1: float = 2.0,
    block_size: int = 1024,
    progress=None,
) -> dict[str, np.ndarray]:
    if not cases or not lines:
        raise ValueError("at least one target and transition are required")
    shells = atmosphere(step_km)
    geometry = [path_lengths(z, sza, shells.edges) for z, sza in cases]
    illuminated = np.array([item[0] for item in geometry])
    columns = np.array([item[1] for item in geometry]).T * 1e5 * shells.oxygen[:, None]
    names = ["monomer", "unattenuated"]
    if cia is not None:
        names += ["cia_nominal", "cia_envelope_min", "cia_envelope_max", "cia_raw"]
    result = {name: np.zeros(len(cases)) for name in names}
    if not np.any(illuminated):
        result["illuminated"] = illuminated
        return result
    used = np.any(columns > 0, axis=1)
    # Unused shells have exactly zero geometric weight for every requested ray.
    columns = columns[used]
    column = (
        VoigtColumn(lines, sources, shells, shifts, diluent, used)
        if np.any(used)
        else None
    )
    centres = np.array([line.nu for line in lines])
    nodes, weights, owners = target_quadrature(lines, core_order, wing_order, support)
    bg = load_baseline_background().radiative
    target_temperatures = {z: float(np.interp(z, bg.z_km, bg.T_K)) for z, _ in cases}
    target_parameters = {}
    for z, t in target_temperatures.items():
        density = float(np.interp(z, bg.z_km, bg.M_cm3))
        oxygen = float(np.interp(z, bg.z_km, bg.O2_model_cm3))
        p, po2 = density * 1e6 * K_B * t / 101325, oxygen * 1e6 * K_B * t / 101325
        gamma, shift = classic_parameters(lines, t, p, po2, shifts, diluent)
        target_parameters[z] = (
            sources.strengths(lines, t),
            doppler_sigma(lines, t),
            gamma,
            shift,
        )
    if cia is not None:
        cia_coeff, cia_in, cia_out = cia_path_coefficients(
            atmosphere(cia_step_km), cases
        )
    for start in range(0, len(nodes), block_size):
        end = min(start + block_size, len(nodes))
        nu, index = nodes[start:end], owners[start:end]
        tau = (
            column.cross_section(nu, far_order, near_cm1) @ columns
            if column is not None
            else np.zeros((len(nu), len(cases)))
        )
        if cia is not None:
            k = cia.at_nodes(nu)
            raw = cia.at_nodes(nu, clip_source_nodes=False)
            tau_cia = {
                "cia_nominal": np.maximum(k.T @ cia_coeff.T, 0),
                "cia_envelope_min": np.maximum(
                    k.T @ cia_in.T + np.min(k, axis=0)[:, None] * cia_out, 0
                ),
                "cia_envelope_max": np.maximum(
                    k.T @ cia_in.T + np.max(k, axis=0)[:, None] * cia_out, 0
                ),
                "cia_raw": np.maximum(raw.T @ cia_coeff.T, 0),
            }
        flux_weight = weights[start:end] * sources.photons(nu)
        target_weights = {}
        for z, (strength, sigma, gamma, shift) in target_parameters.items():
            profile = complex_voigt(
                nu - centres[index] - shift[index], sigma[index], gamma[index]
            ).real
            target_weights[z] = profile * strength[index] * flux_weight
        for j, (z, _) in enumerate(cases):
            if not illuminated[j]:
                continue
            source_weight = target_weights[z]
            result["unattenuated"][j] += source_weight.sum()
            transmitted = source_weight * np.exp(-tau[:, j])
            result["monomer"][j] += transmitted.sum()
            if cia is not None:
                for name, extra_tau in tau_cia.items():
                    result[name][j] += np.sum(transmitted * np.exp(-extra_tau[:, j]))
        if progress is not None:
            progress(end, len(nodes))
    for value in result.values():
        if not np.all(np.isfinite(value)) or np.any(value < 0):
            raise FloatingPointError("invalid reconstructed rates")
    result["illuminated"] = illuminated
    return result
