"""Six-species scalar QSSA closure for ``historical_2020``."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from scipy.optimize import brentq

from . import kinetics
from .local_types import LocalBackground, LocalForcing, LocalState
from .reactions import SCALAR_PARAMETERS


class QSSAError(RuntimeError):
    """Base class for an algebraic closure failure."""


class SingularQSSAError(QSSAError):
    """Raised when positive QSSA production has exactly zero loss."""


class NoPhysicalRootError(QSSAError):
    """Raised when a residual has no root in its physical interval."""


class MultiplePhysicalRootsError(QSSAError):
    """Raised when more than one physical root is detected."""


@dataclass(frozen=True)
class ScalarQSSA:
    value: float
    production: float
    loss_frequency: float
    residual: float


@dataclass(frozen=True)
class HoxQSSA:
    OH: float
    HO2: float
    H2O2: float
    P_OH: float
    L_OH: float
    P_H2O2: float
    L_H2O2: float
    res_OH: float
    res_H2O2: float
    res_family: float
    boundary_R_H_zero: bool


def find_unique_physical_root(
    residual: Callable[[float], float], *, samples: int = 257
) -> float:
    """Find one root on [0, 1], rejecting absent or multiple roots.

    A fixed exploratory grid detects distinct sign-changing roots before Brent's
    method is applied. This is an ambiguity guard, not a root-selection rule.
    """

    if samples < 3:
        raise ValueError("samples must be at least 3")
    points = [index / (samples - 1) for index in range(samples)]
    values = [float(residual(point)) for point in points]
    if not all(math.isfinite(value) for value in values):
        raise QSSAError("physical-root residual must remain finite on [0, 1]")

    exact = [point for point, value in zip(points, values, strict=True) if value == 0]
    brackets: list[tuple[float, float]] = []
    for left, right, f_left, f_right in zip(
        points[:-1], points[1:], values[:-1], values[1:], strict=True
    ):
        if f_left != 0.0 and f_right != 0.0 and f_left * f_right < 0.0:
            brackets.append((left, right))

    roots = exact + [
        float(brentq(residual, left, right, xtol=5e-15, rtol=1e-14))
        for left, right in brackets
    ]
    unique: list[float] = []
    for root in sorted(roots):
        if not unique or abs(root - unique[-1]) > 1e-10:
            unique.append(root)
    if not unique:
        raise NoPhysicalRootError("OH QSSA has no physical root on 0 <= OH/R_H <= 1")
    if len(unique) > 1:
        raise MultiplePhysicalRootsError(
            "OH QSSA has multiple physical roots on 0 <= OH/R_H <= 1"
        )
    root = unique[0]
    if not 0.0 <= root <= 1.0:
        raise NoPhysicalRootError("root solver returned a value outside [0, 1]")
    return root


def solve_o1d_qssa(
    state: LocalState, background: LocalBackground, forcing: LocalForcing
) -> ScalarQSSA:
    """Close O(1D) from its exact frozen production/loss relation."""

    yield_hartley = float(SCALAR_PARAMETERS["yield_o3_hartley_delta_o1d"].value)
    yield_lya = float(SCALAR_PARAMETERS["yield_o2_lya_o1d"].value)
    production = (
        yield_hartley * forcing.JH * state.O3
        + forcing.J_SRC * background.O2
        + yield_lya * forcing.J_LYA * background.O2
        + forcing.J_H2O_B * background.H2O
    )
    loss = (
        kinetics.a_o1d()
        + kinetics.k_o1d_n2(background.T) * background.N2
        + kinetics.k_o1d_o2(background.T) * background.O2
        + kinetics.k_o1d_h2o(background.T) * background.H2O
        + kinetics.k_o1d_h2() * background.H2
    )
    value = production / loss
    return ScalarQSSA(value, production, loss, production - loss * value)


def solve_h2o2_qssa(
    oh: float,
    ho2: float,
    background: LocalBackground,
    forcing: LocalForcing,
) -> ScalarQSSA:
    """Close H2O2 with the frozen HO2 self-reaction event convention."""

    if oh < 0.0 or ho2 < 0.0 or not math.isfinite(oh + ho2):
        raise ValueError("oh and ho2 must be finite and non-negative")
    production = kinetics.k_ho2_ho2(background.T, background.M) * ho2**2
    loss = forcing.J_H2O2 + kinetics.k_oh_h2o2() * oh
    if loss == 0.0:
        if production == 0.0:
            return ScalarQSSA(0.0, 0.0, 0.0, 0.0)
        raise SingularQSSAError("H2O2 QSSA has positive production and zero loss")
    value = production / loss
    return ScalarQSSA(value, production, loss, production - loss * value)


def _oh_production_loss(
    state: LocalState,
    background: LocalBackground,
    forcing: LocalForcing,
    o1d: float,
    oh: float,
    ho2: float,
    h2o2: float,
) -> tuple[float, float]:
    production = (
        kinetics.k_h_o3(background.T) * state.H * state.O3
        + kinetics.k_o_ho2(background.T) * state.O * ho2
        + kinetics.k_ho2_o3(background.T) * ho2 * state.O3
        + 2.0 * kinetics.k_h_ho2_2oh() * state.H * ho2
        + 2.0 * forcing.J_H2O2 * h2o2
        + forcing.J_H2O_A * background.H2O
        + 2.0 * kinetics.k_o1d_h2o(background.T) * o1d * background.H2O
        + kinetics.k_o1d_h2() * o1d * background.H2
    )
    loss = (
        kinetics.k_o_oh(background.T) * state.O * oh
        + kinetics.k_oh_o3(background.T) * oh * state.O3
        + kinetics.k_oh_h2(background.T) * oh * background.H2
        + 2.0 * kinetics.k_oh_oh() * oh**2
        + kinetics.k_oh_ho2(background.T) * oh * ho2
        + kinetics.k_oh_h2o2() * oh * h2o2
    )
    return production, loss


def solve_hox_qssa(
    state: LocalState,
    background: LocalBackground,
    forcing: LocalForcing,
    o1d: float,
) -> HoxQSSA:
    """Partition R_H into OH/HO2 with one bounded OH equation."""

    if state.R_H == 0.0:
        production, loss = _oh_production_loss(
            state, background, forcing, o1d, 0.0, 0.0, 0.0
        )
        return HoxQSSA(
            0.0,
            0.0,
            0.0,
            production,
            loss,
            0.0,
            forcing.J_H2O2,
            production - loss,
            0.0,
            0.0,
            True,
        )

    def residual_fraction(fraction: float) -> float:
        oh = fraction * state.R_H
        ho2 = state.R_H - oh
        try:
            peroxide = solve_h2o2_qssa(oh, ho2, background, forcing)
            production, loss = _oh_production_loss(
                state, background, forcing, o1d, oh, ho2, peroxide.value
            )
        except SingularQSSAError:
            if fraction != 0.0:
                raise
            # At J_H2O2=OH=0 and HO2>0, H2O2 itself is singular, but the
            # limiting OH+H2O2 loss flux equals its HO2+HO2 production.
            peroxide_production = (
                kinetics.k_ho2_ho2(background.T, background.M) * ho2**2
            )
            production, loss_without_peroxide = _oh_production_loss(
                state, background, forcing, o1d, oh, ho2, 0.0
            )
            loss = loss_without_peroxide + peroxide_production
        return production - loss

    fraction = find_unique_physical_root(residual_fraction)
    oh = fraction * state.R_H
    ho2 = state.R_H - oh
    peroxide = solve_h2o2_qssa(oh, ho2, background, forcing)
    production, loss = _oh_production_loss(
        state, background, forcing, o1d, oh, ho2, peroxide.value
    )
    return HoxQSSA(
        oh,
        ho2,
        peroxide.value,
        production,
        loss,
        peroxide.production,
        peroxide.loss_frequency,
        production - loss,
        peroxide.residual,
        oh + ho2 - state.R_H,
        False,
    )


def solve_b1_qssa(
    state: LocalState,
    background: LocalBackground,
    forcing: LocalForcing,
    o1d: float,
) -> ScalarQSSA:
    """Close B1, applying the 0.8 O1D+O2 branch exactly once."""

    branch = float(SCALAR_PARAMETERS["branch_o1d_o2_b1"].value)
    o1d_o2_total = kinetics.k_o1d_o2(background.T) * o1d * background.O2
    production = forcing.gB * background.O2 + branch * o1d_o2_total
    loss = (
        kinetics.a_b1()
        + kinetics.k_b1_o2(background.T) * background.O2
        + kinetics.k_b1_n2() * background.N2
        + kinetics.k_b1_o() * state.O
        + kinetics.k_b1_o3() * state.O3
    )
    value = production / loss
    return ScalarQSSA(value, production, loss, production - loss * value)


def barth_sources(
    state: LocalState, background: LocalBackground
) -> tuple[float, float]:
    """Return recombination event flux and assumed effective B0 source."""

    total = kinetics.k_o_o_m_barth(background.T) * state.O**2 * background.M
    if total == 0.0:
        return 0.0, 0.0
    c_o2 = float(SCALAR_PARAMETERS["barth_c_o2"].value)
    c_o = float(SCALAR_PARAMETERS["barth_c_o"].value)
    denominator = c_o2 * background.O2 + c_o * state.O
    if denominator == 0.0:
        raise SingularQSSAError("positive Barth event flux has zero transfer denominator")
    return total, total * background.O2 / denominator


def solve_b0_qssa(
    state: LocalState,
    background: LocalBackground,
    forcing: LocalForcing,
    o1d: float,
    b1: float,
    barth_b0: float,
) -> ScalarQSSA:
    """Close B0 from direct, cascade, O1D-branch, and effective Barth sources."""

    branch = float(SCALAR_PARAMETERS["branch_o1d_o2_b0"].value)
    o1d_o2_total = kinetics.k_o1d_o2(background.T) * o1d * background.O2
    production = (
        forcing.gA * background.O2
        + branch * o1d_o2_total
        + kinetics.k_b1_o2(background.T) * b1 * background.O2
        + kinetics.k_b1_n2() * b1 * background.N2
        + barth_b0
    )
    loss = (
        kinetics.a_b0()
        + kinetics.k_b0_n2(background.T) * background.N2
        + kinetics.k_b0_o2() * background.O2
        + kinetics.k_b0_o() * state.O
        + kinetics.k_b0_o3(background.T) * state.O3
        + kinetics.k_b0_co2() * background.CO2
    )
    value = production / loss
    return ScalarQSSA(value, production, loss, production - loss * value)
