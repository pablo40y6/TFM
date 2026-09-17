"""Independent tests for the six Milestone-3 algebraic relations."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from tfm_photochem.historical_2020 import (
    LocalBackground,
    LocalForcing,
    LocalState,
    MultiplePhysicalRootsError,
    NoPhysicalRootError,
    SingularQSSAError,
    close_local_chemistry,
)
from tfm_photochem.historical_2020.qssa import (
    barth_sources,
    find_unique_physical_root,
    solve_b0_qssa,
    solve_b1_qssa,
    solve_h2o2_qssa,
    solve_hox_qssa,
    solve_o1d_qssa,
)


def state(**changes: float) -> LocalState:
    return replace(
        LocalState(O=2.0e11, O3=2.0e8, H=2.0e7, R_H=5.0e7, Delta=1.0e8),
        **changes,
    )


def background(**changes: float) -> LocalBackground:
    return replace(
        LocalBackground(
            T=200.0,
            M=2.0e13,
            O2=4.0e12,
            N2=1.5e13,
            CO2=8.0e9,
            H2O=2.0e7,
            H2=1.0e8,
        ),
        **changes,
    )


def forcing(**changes: float) -> LocalForcing:
    return replace(
        LocalForcing(
            JH=8.0e-3,
            J_SRC=2.0e-8,
            J_LYA=3.0e-9,
            J_O2_TOTAL=2.3e-8,
            J_O3_TOTAL=8.0e-3,
            J_H2O2=2.0e-5,
            J_H2O_A=2.0e-8,
            J_H2O_B=1.0e-9,
            gA=1.0e-9,
            gB=2.0e-10,
            gIRA=3.0e-9,
        ),
        **changes,
    )


def forcing_off() -> LocalForcing:
    return LocalForcing(
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    )


def test_o1d_qssa_matches_independent_direct_calculation() -> None:
    s, b, f = state(), background(), forcing()
    p = 0.9 * f.JH * s.O3 + f.J_SRC * b.O2 + 0.44 * f.J_LYA * b.O2
    p += f.J_H2O_B * b.H2O
    loss = 6.81e-3
    loss += 2.15e-11 * math.exp(110.0 / b.T) * b.N2
    loss += 3.3e-11 * math.exp(55.0 / b.T) * b.O2
    loss += 1.63e-10 * math.exp(60.0 / b.T) * b.H2O
    loss += 1.2e-10 * b.H2

    result = solve_o1d_qssa(s, b, f)

    assert result.production == pytest.approx(p, rel=2e-15)
    assert result.loss_frequency == pytest.approx(loss, rel=2e-15)
    assert result.value == pytest.approx(p / loss, rel=2e-15)
    assert abs(result.residual) <= 5e-10


def test_o1d_o2_loss_is_counted_once_and_zero_forcing_gives_zero() -> None:
    s, b = state(), background()
    result = solve_o1d_qssa(s, b, forcing_off())
    expected_loss = (
        6.81e-3
        + 2.15e-11 * math.exp(110.0 / b.T) * b.N2
        + 3.3e-11 * math.exp(55.0 / b.T) * b.O2
        + 1.63e-10 * math.exp(60.0 / b.T) * b.H2O
        + 1.2e-10 * b.H2
    )
    assert result.production == 0.0
    assert result.value == 0.0
    assert result.loss_frequency == pytest.approx(expected_loss, rel=2e-15)


def test_h2o2_qssa_has_no_half_factor() -> None:
    b, f = background(), forcing()
    oh, ho2 = 3.0e7, 2.0e7
    k_self = 3.0e-13 * math.exp(460.0 / b.T)
    k_self += 2.1e-33 * b.M * math.exp(920.0 / b.T)
    production = k_self * ho2**2
    loss = f.J_H2O2 + 1.8e-12 * oh

    result = solve_h2o2_qssa(oh, ho2, b, f)

    assert result.production == pytest.approx(production, rel=2e-15)
    assert result.loss_frequency == pytest.approx(loss, rel=2e-15)
    assert result.value == pytest.approx(production / loss, rel=2e-15)


def test_h2o2_zero_source_and_loss_boundary_is_zero() -> None:
    result = solve_h2o2_qssa(0.0, 0.0, background(), forcing_off())
    assert result.value == result.production == result.loss_frequency == 0.0
    assert result.residual == 0.0


def test_h2o2_positive_production_and_zero_loss_is_explicit_error() -> None:
    with pytest.raises(SingularQSSAError, match="positive production and zero loss"):
        solve_h2o2_qssa(0.0, 1.0e7, background(), forcing_off())


@pytest.mark.parametrize(
    ("s", "f"),
    [
        (state(), forcing()),
        (state(O=8.0e10, O3=5.0e8, R_H=2.0e7), forcing(JH=2.0e-3)),
        (state(H=8.0e7, R_H=1.2e8), forcing(J_H2O2=0.0)),
    ],
)
def test_hox_partition_is_physical_and_closes_one_oh_equation(
    s: LocalState, f: LocalForcing
) -> None:
    b = background()
    o1d = solve_o1d_qssa(s, b, f).value
    result = solve_hox_qssa(s, b, f, o1d)
    scale = max(result.P_OH, result.L_OH, 1.0)
    assert result.OH >= 0.0
    assert result.HO2 >= 0.0
    assert result.OH + result.HO2 == pytest.approx(s.R_H, abs=1e-8)
    assert abs(result.res_OH) / scale < 2e-13
    assert abs(result.res_H2O2) <= 1e-10
    assert result.res_family == pytest.approx(0.0, abs=1e-8)


def test_zero_rh_is_explicit_dynamic_boundary_not_forced_oh_root() -> None:
    result = close_local_chemistry(state(R_H=0.0), background(), forcing())
    assert result.algebraic.OH == 0.0
    assert result.algebraic.HO2 == 0.0
    assert result.algebraic.H2O2 == 0.0
    assert result.residuals.res_family == 0.0
    assert result.residuals.res_OH > 0.0
    assert result.tendencies.R_H > 0.0


def test_unique_root_helper_rejects_absence_and_multiplicity() -> None:
    with pytest.raises(NoPhysicalRootError, match="no physical root"):
        find_unique_physical_root(lambda x: x + 1.0)
    with pytest.raises(MultiplePhysicalRootsError, match="multiple physical roots"):
        find_unique_physical_root(lambda x: (x - 0.25) * (x - 0.75))


def test_hox_solver_reports_actual_no_root_case_without_clipping() -> None:
    isolated_family = state(O=0.0, O3=0.0, H=0.0, Delta=0.0)
    inert_background = background(O2=0.0, N2=0.0, CO2=0.0, H2O=0.0, H2=0.0)
    with pytest.raises(NoPhysicalRootError, match="no physical root"):
        solve_hox_qssa(isolated_family, inert_background, forcing_off(), 0.0)


def test_b1_qssa_sources_branch_and_losses_independently() -> None:
    s, b, f, o1d = state(), background(), forcing(), 1200.0
    total = 3.3e-11 * math.exp(55.0 / b.T) * o1d * b.O2
    production = f.gB * b.O2 + 0.8 * total
    loss = 7.2e-2
    loss += 2.2e-11 * math.exp(-115.0 / b.T) * b.O2
    loss += 7.0e-13 * b.N2 + 4.5e-12 * s.O + 3.0e-10 * s.O3

    result = solve_b1_qssa(s, b, f, o1d)

    assert result.production == pytest.approx(production, rel=2e-15)
    assert result.loss_frequency == pytest.approx(loss, rel=2e-15)
    assert result.value == pytest.approx(production / loss, rel=2e-15)


def test_b0_qssa_sources_branch_cascade_barth_and_losses_independently() -> None:
    s, b, f, o1d, b1, barth_b0 = state(), background(), forcing(), 900.0, 4e3, 700.0
    total = 3.3e-11 * math.exp(55.0 / b.T) * o1d * b.O2
    production = f.gA * b.O2 + 0.2 * total
    production += 2.2e-11 * math.exp(-115.0 / b.T) * b1 * b.O2
    production += 7.0e-13 * b1 * b.N2 + barth_b0
    loss = 8.34e-2
    loss += 1.8e-15 * math.exp(45.0 / b.T) * b.N2
    loss += 3.9e-17 * b.O2 + 8.0e-14 * s.O
    loss += 3.5e-11 * math.exp(-135.0 / b.T) * s.O3
    loss += 4.2e-13 * b.CO2

    result = solve_b0_qssa(s, b, f, o1d, b1, barth_b0)

    assert result.production == pytest.approx(production, rel=2e-15)
    assert result.loss_frequency == pytest.approx(loss, rel=2e-15)
    assert result.value == pytest.approx(production / loss, rel=2e-15)


def test_barth_source_formula_and_zero_edge_case() -> None:
    s, b = state(), background()
    k = 4.7e-33 * (300.0 / b.T) ** 2
    total = k * s.O**2 * b.M
    expected_b0 = total * b.O2 / (6.6 * b.O2 + 19.0 * s.O)
    actual_total, actual_b0 = barth_sources(s, b)
    assert actual_total == pytest.approx(total, rel=2e-15)
    assert actual_b0 == pytest.approx(expected_b0, rel=2e-15)
    assert barth_sources(state(O=0.0), background(O2=0.0)) == (0.0, 0.0)
