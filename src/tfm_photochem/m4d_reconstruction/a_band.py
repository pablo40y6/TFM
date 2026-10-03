"""Isolated principal A transfer; full A fails closed on rare Galatry provenance.

Executable scope and scientific gates: docs/m4d_a_advanced_transfer_execution.md.
No accepted M4C API imports this module.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..historical_2020.background import load_baseline_background
from .mapping import unique_rows
from .sources import Line, SourceError
from .spectroscopy import (
    K_B,
    SpectralSources,
    classic_parameters,
    complex_voigt,
    doppler_sigma,
    drouin_mixed_profile,
    drouin_parameters,
    mixing_y,
)
from .transfer import Atmosphere, atmosphere, path_lengths, target_quadrature

GALATRY_BLOCKER = (
    "SOURCE CONVENTION BLOCKER: historical Galatry beta/profile conversion and "
    "temperature law are not established by frozen sources; no rare-line fallback"
)
LM_BLOCKER = (
    "SOURCE CONVENTION BLOCKER: Table-22 Y unit annotation does not establish "
    "dimensionless p*Y normalization against complex SDV; frozen HAPI has no LM evaluator"
)


@dataclass(frozen=True)
class APolicy:
    """Explicit diagnostics, applied identically to excitation and attenuation."""

    low_temperature: str = "clamp"
    line_mixing: bool = True
    include_no_y: bool = True
    include_quadrupoles: bool = True

    def __post_init__(self):
        if self.low_temperature not in ("clamp", "linear", "zero"):
            raise ValueError("unknown low-temperature Y policy")


@dataclass(frozen=True)
class PrincipalA:
    """Verified 150-line principal population, with separable diagnostics.

    LM-enabled contributions are the pre-existing candidate algebra, not an
    accepted transfer convention. Nominal rates fail closed until normalization
    is demonstrated. Construct using source loaders and audit_mapping for full
    byte/430-line verification; this constructor checks the principal map too.
    """

    lines: tuple[Line, ...]
    sources: SpectralSources
    drouin: dict[str, tuple]
    mixing: dict[str, tuple]
    policy: APolicy = APolicy()

    def __post_init__(self):
        unique_rows(((line.key, line) for line in self.lines), "principal A")
        if any(
            line.isotope != 1
            or (line.upper, line.lower) != ("b 0", "X 0")
            or line.flag not in ("d", "q")
            for line in self.lines
        ):
            raise SourceError("principal A requires only principal b(0)-X(0) d/q lines")
        labels = set(
            unique_rows(
                ((line.dipole_label, line) for line in self.lines if line.flag == "d"),
                "principal A dipole labels",
            )
        )
        if (
            len(self.lines) != 150
            or len(labels) != 91
            or set(self.drouin) != labels
            or len(self.mixing) != 70
            or not set(self.mixing) <= labels
        ):
            raise SourceError("MAPPING BLOCKER: principal A requires 91/70/21/59")
        for row in self.drouin.values():
            if len(row) != 12 or not np.all(np.isfinite(row)):
                raise SourceError("invalid Drouin parameter row")
        for values in self.mixing.values():
            if len(values) != 4 or not np.all(np.isfinite(values)):
                raise SourceError("invalid Table-22 parameter row")

    @property
    def selected_lines(self) -> tuple[Line, ...]:
        return tuple(
            sorted(
                (
                    line
                    for line in self.lines
                    if (
                        self.policy.include_quadrupoles
                        if line.flag == "q"
                        else self.policy.include_no_y
                        or line.dipole_label in self.mixing
                    )
                ),
                key=lambda line: line.key,
            )
        )

    def parameters(self, temperature, pressure_atm, oxygen_pressure_atm, shifts=True):
        lines = self.selected_lines
        # Shared validation and target-edition q-line pressure semantics.
        gamma, shift = classic_parameters(
            lines, temperature, pressure_atm, oxygen_pressure_atm, shifts
        )
        gamma2 = np.zeros(len(lines))
        y = np.zeros(len(lines))
        for i, line in enumerate(lines):
            if line.flag == "d":
                label = line.dipole_label
                gamma[i], gamma2[i], shift[i] = drouin_parameters(
                    self.drouin[label], temperature, pressure_atm, shifts
                )
                if self.policy.line_mixing and label in self.mixing:
                    y[i] = mixing_y(
                        self.mixing[label], temperature, self.policy.low_temperature
                    )
        return (
            self.sources.strengths(lines, temperature),
            doppler_sigma(lines, temperature),
            gamma,
            gamma2,
            shift,
            y,
        )

    def contributions(
        self,
        nodes,
        temperature,
        pressure_atm,
        oxygen_pressure_atm,
        shifts=True,
        owners=None,
    ):
        """Signed line contributions; optionally only quadrature-owner lines.

        Check positivity after summing lines, never by clipping each line.
        Output is node x line if owners is None, otherwise one value per node.
        """
        nu = np.asarray(nodes, dtype=float)
        if nu.ndim != 1 or not np.all(np.isfinite(nu)):
            raise ValueError("spectral nodes must be a finite vector")
        lines = self.selected_lines
        strength, sigma, gamma, gamma2, shift, y = self.parameters(
            temperature, pressure_atm, oxygen_pressure_atm, shifts
        )
        if owners is not None:
            owners = np.asarray(owners)
            if (
                owners.shape != nu.shape
                or owners.dtype.kind not in "iu"
                or np.any(owners < 0)
                or np.any(owners >= len(lines))
            ):
                raise ValueError("invalid target quadrature owners")
        out = np.zeros((len(nu), len(lines))) if owners is None else np.zeros(len(nu))
        for i, line in enumerate(lines):
            use = slice(None) if owners is None else owners == i
            delta = nu[use] - line.nu - shift[i]
            if line.flag == "d":
                profile = drouin_mixed_profile(
                    delta, sigma[i], gamma[i], gamma2[i], y[i], pressure_atm
                )
            else:
                profile = complex_voigt(delta, sigma[i], gamma[i]).real
            if owners is None:
                out[:, i] = strength[i] * profile
            else:
                out[use] = strength[i] * profile
        if not np.all(np.isfinite(out)):
            raise FloatingPointError("invalid principal A contributions")
        return out

    def cross_section(
        self, nodes, temperature, pressure_atm, oxygen_pressure_atm, shifts=True
    ):
        out = self.contributions(
            nodes, temperature, pressure_atm, oxygen_pressure_atm, shifts
        ).sum(axis=1)
        if np.any(out < 0):
            raise FloatingPointError(
                "DESIGN BLOCKER: negative summed principal A opacity"
            )
        return out


@dataclass
class PrincipalAColumn:
    model: PrincipalA
    shells: Atmosphere
    shifts: bool = True
    used_shells: np.ndarray | None = None

    def __post_init__(self):
        self.indices = (
            np.arange(len(self.shells.temperature))
            if self.used_shells is None
            else np.flatnonzero(self.used_shells)
        )
        # Fail before expensive quadrature if an active shell violates Y policy.
        for i in self.indices:
            try:
                self.model.parameters(
                    self.shells.temperature[i],
                    self.shells.pressure[i],
                    self.shells.oxygen_pressure[i],
                    self.shifts,
                )
            except ValueError as error:
                raise ValueError(f"A shell {i}: {error}") from error

    def cross_section(self, nodes):
        out = np.empty((len(nodes), len(self.indices)))
        for j, i in enumerate(self.indices):
            out[:, j] = self.model.cross_section(
                nodes,
                self.shells.temperature[i],
                self.shells.pressure[i],
                self.shells.oxygen_pressure[i],
                self.shifts,
            )
        return out


def compute_principal_a_rates(
    model: PrincipalA,
    cases: list[tuple[float, float]],
    step_km: float = 0.125,
    core_order: int = 64,
    wing_order: int = 12,
    support: float = 3.84,
    shifts: bool = True,
    block_size: int = 1024,
    progress=None,
) -> dict:
    """Principal-only direct-beam experiment; never a complete 430-line gA.

    Every selected absorber contributes exactly at every quadrature node.
    Block size bounds memory; no far-wing approximation or source cutoff.
    """
    if not cases or block_size < 1:
        raise ValueError("nonempty cases and positive block size required")
    shells = atmosphere(step_km)
    geometry = [path_lengths(z, sza, shells.edges) for z, sza in cases]
    lit = np.array([item[0] for item in geometry])
    result = {
        "principal": np.zeros(len(cases)),
        "unattenuated": np.zeros(len(cases)),
        "illuminated": lit,
        "scope": "principal-only; rare Galatry excluded",
        "selected_lines": len(model.selected_lines),
        "M4D_frozen": False,
    }
    if not np.any(lit):
        return result
    if model.policy.line_mixing:
        raise SourceError(LM_BLOCKER)
    result["scope"] = "principal-only SDV/q; LM-off diagnostic; rare Galatry excluded"
    columns = np.array([item[1] for item in geometry]).T * 1e5 * shells.oxygen[:, None]
    used = np.any(columns > 0, axis=1)
    column = PrincipalAColumn(model, shells, shifts, used)
    columns = columns[used]
    nodes, weights, owners = target_quadrature(
        model.selected_lines, core_order, wing_order, support
    )
    bg = load_baseline_background().radiative
    targets = {}
    for (z, _), illuminated in zip(cases, lit):
        if not illuminated or z in targets:
            continue
        t = float(np.interp(z, bg.z_km, bg.T_K))
        factor = 1e6 * K_B * t / 101325
        p = float(np.interp(z, bg.z_km, bg.M_cm3)) * factor
        po2 = float(np.interp(z, bg.z_km, bg.O2_model_cm3)) * factor
        model.parameters(t, p, po2, shifts)
        targets[z] = (t, p, po2)
    for start in range(0, len(nodes), block_size):
        end = min(start + block_size, len(nodes))
        nu = nodes[start:end]
        tau = column.cross_section(nu) @ columns
        flux_weights = weights[start:end] * model.sources.photons(nu)
        target_weights = {}
        for z, state in targets.items():
            # Target excitation is a signed line decomposition of a physical
            # total band. Check that total before integrating the decomposition.
            model.cross_section(nu, *state, shifts)
            target_weights[z] = (
                model.contributions(nu, *state, shifts, owners[start:end])
                * flux_weights
            )
        for j, (z, _) in enumerate(cases):
            if lit[j]:
                result["unattenuated"][j] += target_weights[z].sum()
                result["principal"][j] += np.sum(target_weights[z] * np.exp(-tau[:, j]))
        if progress is not None:
            progress(end, len(nodes))
    for name in ("principal", "unattenuated"):
        if not np.all(np.isfinite(result[name])) or np.any(result[name] < 0):
            raise FloatingPointError("DESIGN BLOCKER: invalid summed principal A rate")
    return result


def compute_a_rates(*args, **kwargs):
    """Full-band entry point stays blocked; never substitutes a Voigt rare profile."""
    raise SourceError(GALATRY_BLOCKER + "; " + LM_BLOCKER)
