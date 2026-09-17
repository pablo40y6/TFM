"""Scalar data contracts for local chemistry through Milestone 4B."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real
from types import MappingProxyType
from typing import Mapping

from .config import CONFIGURATION
from .photolysis_budget import partition_odd_oxygen_photolysis


def _validate_scalar(name: str, value: float, *, positive: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite scalar")
    scalar = float(value)
    if not math.isfinite(scalar):
        raise ValueError(f"{name} must be finite")
    if positive and scalar <= 0.0:
        raise ValueError(f"{name} must be strictly positive")
    if not positive and scalar < 0.0:
        raise ValueError(f"{name} must be non-negative")


@dataclass(frozen=True)
class LocalState:
    """Five dynamic concentrations at one altitude and one instant."""

    O: float  # noqa: E741 - frozen scientific species name
    O3: float
    H: float
    R_H: float
    Delta: float

    def __post_init__(self) -> None:
        for name in ("O", "O3", "H", "R_H", "Delta"):
            _validate_scalar(f"state.{name}", getattr(self, name))


@dataclass(frozen=True)
class LocalBackground:
    """Prescribed scalar background; M4B does not calculate these fields."""

    T: float
    M: float
    O2: float
    N2: float
    CO2: float
    H2O: float
    H2: float

    def __post_init__(self) -> None:
        _validate_scalar("background.T", self.T, positive=True)
        for name in ("M", "O2", "N2", "CO2", "H2O", "H2"):
            _validate_scalar(f"background.{name}", getattr(self, name))


@dataclass(frozen=True)
class LocalForcing:
    """Eleven injected first-order photolysis/excitation frequencies in s^-1."""

    JH: float
    J_SRC: float
    J_LYA: float
    J_O2_TOTAL: float
    J_O3_TOTAL: float
    J_H2O2: float
    J_H2O_A: float
    J_H2O_B: float
    gA: float
    gB: float
    gIRA: float

    def __post_init__(self) -> None:
        for name in (
            "JH",
            "J_SRC",
            "J_LYA",
            "J_O2_TOTAL",
            "J_O3_TOTAL",
            "J_H2O2",
            "J_H2O_A",
            "J_H2O_B",
            "gA",
            "gB",
            "gIRA",
        ):
            _validate_scalar(f"forcing.{name}", getattr(self, name))
        partition_odd_oxygen_photolysis(
            JH=self.JH,
            J_SRC=self.J_SRC,
            J_LYA=self.J_LYA,
            J_O2_TOTAL=self.J_O2_TOTAL,
            J_O3_TOTAL=self.J_O3_TOTAL,
        )


@dataclass(frozen=True)
class AlgebraicState:
    """Six concentrations closed algebraically by M3."""

    O1D: float
    OH: float
    HO2: float
    H2O2: float
    B0: float
    B1: float


@dataclass(frozen=True)
class LocalTendencies:
    """Five local chemical tendencies in molecule cm^-3 s^-1."""

    O: float  # noqa: E741 - frozen scientific species name
    O3: float
    H: float
    R_H: float
    Delta: float


@dataclass(frozen=True)
class QSSAResiduals:
    """Algebraic residuals in molecule cm^-3 s^-1, except family constraint."""

    res_O1D: float
    res_OH: float
    res_family: float
    res_H2O2: float
    res_B1: float
    res_B0: float


@dataclass(frozen=True)
class ProductionLossDiagnostics:
    """Auditable production and pseudo-first-order loss diagnostics."""

    P_O1D: float
    L_O1D: float
    P_OH: float
    L_OH: float
    P_H2O2: float
    L_H2O2: float
    P_B1: float
    L_B1: float
    P_B0: float
    L_B0: float
    P_Delta: float
    L_Delta: float
    hartley_gross: float
    hartley_products: float
    hartley_untracked: float
    lyman_alpha_gross: float
    lyman_alpha_products: float
    lyman_alpha_untracked: float
    barth_total: float
    barth_b0: float


@dataclass(frozen=True)
class ModelAssumption:
    """A non-kinetic model-reduction decision with provenance."""

    identifier: str
    statement: str
    reference: str
    year: int
    configuration: str = CONFIGURATION


@dataclass(frozen=True)
class LocalClosureResult:
    """Complete result of one scalar local chemistry evaluation."""

    algebraic: AlgebraicState
    fluxes: Mapping[str, float]
    residuals: QSSAResiduals
    diagnostics: ProductionLossDiagnostics
    contributions: Mapping[str, Mapping[str, float]]
    tendencies: LocalTendencies


def freeze_mapping(values: Mapping[str, float]) -> Mapping[str, float]:
    """Return an immutable shallow copy for frozen result objects."""

    return MappingProxyType(dict(values))


def freeze_nested_mapping(
    values: Mapping[str, Mapping[str, float]],
) -> Mapping[str, Mapping[str, float]]:
    """Return an immutable two-level mapping."""

    return MappingProxyType(
        {name: MappingProxyType(dict(inner)) for name, inner in values.items()}
    )
