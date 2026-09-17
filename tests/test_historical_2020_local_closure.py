"""Flux, stoichiometry, diagnostics, and validation tests through M4B."""

from __future__ import annotations

import math
from dataclasses import fields, replace

import numpy as np
import pytest

from tfm_photochem.historical_2020 import (
    BARTH_B0_ASSUMPTION,
    SPECIAL_FLUX_RULES,
    TENDENCY_COEFFICIENTS,
    LocalBackground,
    LocalForcing,
    LocalState,
    close_local_chemistry,
)
from tfm_photochem.historical_2020.reactions import REACTION_BY_ID
from tfm_photochem.historical_2020.stoichiometry import assemble_tendencies

BASE_STATE = LocalState(O=2e11, O3=2e8, H=2e7, R_H=5e7, Delta=1e8)
BASE_BACKGROUND = LocalBackground(
    T=200.0,
    M=2e13,
    O2=4e12,
    N2=1.5e13,
    CO2=8e9,
    H2O=2e7,
    H2=1e8,
)
BASE_FORCING = LocalForcing(
    JH=8e-3,
    J_SRC=2e-8,
    J_LYA=3e-9,
    J_O2_TOTAL=2.3e-8,
    J_O3_TOTAL=8e-3,
    J_H2O2=2e-5,
    J_H2O_A=2e-8,
    J_H2O_B=1e-9,
    gA=1e-9,
    gB=2e-10,
    gIRA=3e-9,
)
FORCING_OFF = LocalForcing(
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
)


def test_branch_conservation_and_o1d_loss_not_duplicated() -> None:
    result = close_local_chemistry(BASE_STATE, BASE_BACKGROUND, BASE_FORCING)
    flux = result.fluxes
    assert flux["O1D_O2_B1"] + flux["O1D_O2_B0"] == pytest.approx(
        flux["O1D_O2_TOTAL"], rel=2e-15
    )
    assert flux["O1D_O2_B1"] == pytest.approx(0.8 * flux["O1D_O2_TOTAL"])
    assert flux["O1D_O2_B0"] == pytest.approx(0.2 * flux["O1D_O2_TOTAL"])
    o1d_losses = (
        flux["O1D_RADIATIVE"]
        + flux["O1D_N2"]
        + flux["O1D_O2_TOTAL"]
        + flux["O1D_H2O"]
        + flux["O1D_H2"]
    )
    assert result.diagnostics.P_O1D == pytest.approx(o1d_losses, rel=2e-15)


def test_hartley_total_loss_is_partitioned_without_double_counting() -> None:
    result = close_local_chemistry(BASE_STATE, BASE_BACKGROUND, BASE_FORCING)
    gross = BASE_FORCING.JH * BASE_STATE.O3
    assert result.fluxes["O3_HARTLEY_GROSS"] == gross
    assert result.fluxes["O3_HARTLEY_PRODUCTS"] == pytest.approx(0.9 * gross)
    assert result.fluxes["O3_PHOTOLYSIS_GROUND_EFFECTIVE"] == pytest.approx(
        0.1 * gross
    )
    assert result.contributions["O3_HARTLEY_PRODUCTS"]["Delta"] == pytest.approx(
        0.9 * gross
    )
    assert "O3_HARTLEY_GROSS" not in result.contributions
    total_o3_loss = -sum(
        row["O3"]
        for key, row in result.contributions.items()
        if key in {"O3_HARTLEY_PRODUCTS", "O3_PHOTOLYSIS_GROUND_EFFECTIVE"}
    )
    assert total_o3_loss == pytest.approx(BASE_FORCING.J_O3_TOTAL * BASE_STATE.O3)
    assert result.diagnostics.P_O1D >= 0.9 * gross


def test_lyman_alpha_uses_only_represented_product_yield() -> None:
    result = close_local_chemistry(BASE_STATE, BASE_BACKGROUND, BASE_FORCING)
    gross = BASE_FORCING.J_LYA * BASE_BACKGROUND.O2
    assert result.fluxes["O2_LYMAN_ALPHA_GROSS"] == gross
    assert result.fluxes["O2_LYMAN_ALPHA"] == pytest.approx(0.44 * gross)
    assert result.contributions["O2_LYMAN_ALPHA"]["O"] == pytest.approx(
        0.44 * gross
    )
    expected_ground = (
        BASE_FORCING.J_O2_TOTAL
        - BASE_FORCING.J_SRC
        - 0.44 * BASE_FORCING.J_LYA
    ) * BASE_BACKGROUND.O2
    assert result.fluxes["O2_PHOTOLYSIS_GROUND_EFFECTIVE"] == pytest.approx(
        expected_ground
    )
    assert result.diagnostics.lyman_alpha_untracked == pytest.approx(0.56 * gross)


def test_identical_reactants_use_event_flux_without_half_factor() -> None:
    result = close_local_chemistry(BASE_STATE, BASE_BACKGROUND, BASE_FORCING)
    a = result.algebraic
    t, m = BASE_BACKGROUND.T, BASE_BACKGROUND.M
    expected_oh = 1.8e-12 * a.OH**2
    k_ho2 = 3.0e-13 * math.exp(460.0 / t)
    k_ho2 += 2.1e-33 * m * math.exp(920.0 / t)
    expected_ho2 = k_ho2 * a.HO2**2
    expected_barth = 4.7e-33 * (300.0 / t) ** 2 * BASE_STATE.O**2 * m
    assert result.fluxes["OH_OH"] == pytest.approx(expected_oh)
    assert result.fluxes["HO2_HO2"] == pytest.approx(expected_ho2)
    assert result.fluxes["BARTH_RECOMBINATION"] == pytest.approx(expected_barth)
    assert result.contributions["OH_OH"]["R_H"] == pytest.approx(-2 * expected_oh)
    assert result.contributions["HO2_HO2"]["R_H"] == pytest.approx(
        -2 * expected_ho2
    )
    assert result.contributions["BARTH_RECOMBINATION"]["O"] == pytest.approx(
        -2 * expected_barth
    )


@pytest.mark.parametrize(
    ("reaction_id", "expected"),
    [
        ("O_HO2", 0.0),
        ("OH_O3", 0.0),
        ("HO2_O3", 0.0),
        ("OH_H2O2", 0.0),
        ("OH_HO2", -2.0),
        ("HO2_HO2", -2.0),
        ("H_HO2_2OH", 1.0),
    ],
)
def test_rh_family_coefficients_are_exact(
    reaction_id: str, expected: float
) -> None:
    assert TENDENCY_COEFFICIENTS[reaction_id]["R_H"] == expected


def test_delta_is_dynamic_not_replaced_by_equilibrium() -> None:
    low = close_local_chemistry(
        replace(BASE_STATE, Delta=2.0e7), BASE_BACKGROUND, BASE_FORCING
    )
    high = close_local_chemistry(
        replace(BASE_STATE, Delta=9.0e7), BASE_BACKGROUND, BASE_FORCING
    )
    assert low.diagnostics.P_Delta == pytest.approx(high.diagnostics.P_Delta)
    assert low.diagnostics.L_Delta == pytest.approx(high.diagnostics.L_Delta)
    expected_change = -low.diagnostics.L_Delta * (9.0e7 - 2.0e7)
    actual_change = high.tendencies.Delta - low.tendencies.Delta
    assert actual_change == pytest.approx(expected_change, rel=1e-14)
    assert "Delta_eq" not in {field.name for field in fields(low.diagnostics)}


def test_delta_o3_topology_contributes_minus_delta_minus_o3_plus_o() -> None:
    result = close_local_chemistry(BASE_STATE, BASE_BACKGROUND, BASE_FORCING)
    event = result.fluxes["DELTA_O3"]
    row = result.contributions["DELTA_O3"]
    assert REACTION_BY_ID["DELTA_O3"].products == (("O", 1), ("O2", 2))
    assert row["Delta"] == -event
    assert row["O3"] == -event
    assert row["O"] == event


def test_b0_o3_li_routing_has_zero_net_ozone_and_delta_source() -> None:
    result = close_local_chemistry(BASE_STATE, BASE_BACKGROUND, BASE_FORCING)
    event = result.fluxes["B0_O3"]
    row = result.contributions["B0_O3"]
    assert REACTION_BY_ID["B0_O3"].products == (("Delta", 1), ("O3", 1))
    assert row["Delta"] == event
    assert row["O3"] == 0.0


def test_barth_assumption_flux_source_and_o_consumption() -> None:
    result = close_local_chemistry(BASE_STATE, BASE_BACKGROUND, BASE_FORCING)
    total = 4.7e-33 * (300.0 / 200.0) ** 2 * (2e11) ** 2 * 2e13
    b0 = total * 4e12 / (6.6 * 4e12 + 19.0 * 2e11)
    assert BARTH_B0_ASSUMPTION.statement == (
        "M3 baseline model assumption: effective Barth source -> B0"
    )
    assert result.fluxes["BARTH_RECOMBINATION"] == pytest.approx(total)
    assert result.fluxes["BARTH_B0_EFFECTIVE"] == pytest.approx(b0)
    assert result.contributions["BARTH_RECOMBINATION"]["O"] == pytest.approx(
        -2 * total
    )
    assert "BARTH_TRANSFER" not in result.fluxes
    assert "BARTH_O2STAR_QUENCH" not in result.fluxes


def test_forcing_off_removes_solar_sources_but_not_nightglow_or_delta_loss() -> None:
    result = close_local_chemistry(BASE_STATE, BASE_BACKGROUND, FORCING_OFF)
    for flux_id in (
        "O3_HARTLEY_GROSS",
        "O3_HARTLEY_PRODUCTS",
        "O3_PHOTOLYSIS_GROUND_EFFECTIVE",
        "O2_SRC",
        "O2_LYMAN_ALPHA",
        "O2_PHOTOLYSIS_GROUND_EFFECTIVE",
        "H2O2_PHOTOLYSIS",
        "H2O_PHOTOLYSIS_A",
        "H2O_PHOTOLYSIS_B",
        "O2_A_BAND",
        "O2_B_BAND",
        "O2_IRA_BAND",
    ):
        assert result.fluxes[flux_id] == 0.0
    assert result.fluxes["BARTH_RECOMBINATION"] > 0.0
    assert result.fluxes["BARTH_B0_EFFECTIVE"] > 0.0
    assert result.fluxes["DELTA_RADIATIVE"] > 0.0


def test_every_tendency_is_exact_sum_of_reported_reaction_contributions() -> None:
    result = close_local_chemistry(BASE_STATE, BASE_BACKGROUND, BASE_FORCING)
    for species in ("O", "O3", "H", "R_H", "Delta"):
        reconstructed = sum(row[species] for row in result.contributions.values())
        assert getattr(result.tendencies, species) == reconstructed


def test_totals_match_independent_frozen_aggregate_equations() -> None:
    result = close_local_chemistry(BASE_STATE, BASE_BACKGROUND, BASE_FORCING)
    r = result.fluxes
    expected_o = (
        -r["O_ASSOCIATION"]
        - r["O_O3"]
        - 2 * r["BARTH_RECOMBINATION"]
        - r["O_OH"]
        - r["O_HO2"]
        + r["H_HO2_H2O_O"]
        + r["OH_OH"]
        + r["O2_SRC"]
        + r["O2_LYMAN_ALPHA"]
        + 2 * r["O2_PHOTOLYSIS_GROUND_EFFECTIVE"]
        + r["O3_PHOTOLYSIS_GROUND_EFFECTIVE"]
        + r["O1D_RADIATIVE"]
        + r["O1D_N2"]
        + r["O1D_O2_TOTAL"]
        + r["B1_O3"]
        + r["DELTA_O3"]
    )
    expected_o3 = (
        r["O_ASSOCIATION"]
        - r["O_O3"]
        - r["H_O3"]
        - r["OH_O3"]
        - r["HO2_O3"]
        - r["O3_HARTLEY_PRODUCTS"]
        - r["O3_PHOTOLYSIS_GROUND_EFFECTIVE"]
        - r["B1_O3"]
        - r["DELTA_O3"]
    )
    expected_h = (
        -r["H_O2_ASSOCIATION"]
        - r["H_O3"]
        + r["O_OH"]
        + r["OH_H2"]
        - r["H_HO2_2OH"]
        - r["H_HO2_H2O_O"]
        - r["H_HO2_H2_O2"]
        + r["H2O_PHOTOLYSIS_A"]
        + r["O1D_H2"]
    )
    expected_rh = (
        r["H_O2_ASSOCIATION"]
        + r["H_O3"]
        - r["O_OH"]
        - r["OH_H2"]
        + r["H_HO2_2OH"]
        - r["H_HO2_H2O_O"]
        - r["H_HO2_H2_O2"]
        - 2 * r["OH_OH"]
        - 2 * r["OH_HO2"]
        - 2 * r["HO2_HO2"]
        + 2 * r["H2O2_PHOTOLYSIS"]
        + r["H2O_PHOTOLYSIS_A"]
        + 2 * r["O1D_H2O"]
        + r["O1D_H2"]
    )
    expected_delta = (
        r["O3_HARTLEY_PRODUCTS"]
        + r["O2_IRA_BAND"]
        + r["B0_N2"]
        + r["B0_O2"]
        + r["B0_O"]
        + r["B0_O3"]
        + r["B0_CO2"]
        - r["DELTA_RADIATIVE"]
        - r["DELTA_O2"]
        - r["DELTA_N2"]
        - r["DELTA_O"]
        - r["DELTA_O3"]
    )
    assert result.tendencies.O == pytest.approx(expected_o, rel=2e-15)
    assert result.tendencies.O3 == pytest.approx(expected_o3, rel=2e-15)
    assert result.tendencies.H == pytest.approx(expected_h, rel=2e-15)
    assert result.tendencies.R_H == pytest.approx(expected_rh, rel=2e-15)
    assert result.tendencies.Delta == pytest.approx(expected_delta, rel=2e-15)


def test_single_reaction_switch_uses_the_coefficient_table() -> None:
    fluxes = {reaction_id: 0.0 for reaction_id in TENDENCY_COEFFICIENTS}
    fluxes["O_ASSOCIATION"] = 7.0
    tendencies, contributions = assemble_tendencies(fluxes)
    assert tendencies.O == -7.0
    assert tendencies.O3 == 7.0
    assert tendencies.H == tendencies.R_H == tendencies.Delta == 0.0
    assert contributions["O_ASSOCIATION"]["O"] == -7.0
    assert contributions["O_ASSOCIATION"]["O3"] == 7.0


def test_every_tendency_term_is_registered_or_explicit_special_rule() -> None:
    allowed = set(REACTION_BY_ID) | set(SPECIAL_FLUX_RULES)
    assert set(TENDENCY_COEFFICIENTS) <= allowed
    assert set(SPECIAL_FLUX_RULES) == {"O3_HARTLEY_PRODUCTS"}


def test_all_six_qssa_residual_diagnostics_close_for_regular_case() -> None:
    result = close_local_chemistry(BASE_STATE, BASE_BACKGROUND, BASE_FORCING)
    residuals = result.residuals
    scales = {
        "res_O1D": max(result.diagnostics.P_O1D, 1.0),
        "res_OH": max(result.diagnostics.P_OH, 1.0),
        "res_H2O2": max(result.diagnostics.P_H2O2, 1.0),
        "res_B1": max(result.diagnostics.P_B1, 1.0),
        "res_B0": max(result.diagnostics.P_B0, 1.0),
    }
    for name, scale in scales.items():
        assert abs(getattr(residuals, name)) / scale < 2e-13
    assert residuals.res_family == pytest.approx(0.0, abs=1e-8)


@pytest.mark.parametrize("bad", [-1.0, float("nan"), float("inf")])
@pytest.mark.parametrize("field", ["O", "O3", "H", "R_H", "Delta"])
def test_state_rejects_negative_or_nonfinite_density(field: str, bad: float) -> None:
    with pytest.raises(ValueError, match=f"state.{field}"):
        replace(BASE_STATE, **{field: bad})


@pytest.mark.parametrize("bad", [-1.0, float("nan"), float("inf")])
@pytest.mark.parametrize("field", ["M", "O2", "N2", "CO2", "H2O", "H2"])
def test_background_rejects_negative_or_nonfinite_density(
    field: str, bad: float
) -> None:
    with pytest.raises(ValueError, match=f"background.{field}"):
        replace(BASE_BACKGROUND, **{field: bad})


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan"), float("inf")])
def test_background_rejects_invalid_temperature(bad: float) -> None:
    with pytest.raises(ValueError, match="background.T"):
        replace(BASE_BACKGROUND, T=bad)


@pytest.mark.parametrize("bad", [-1.0, float("nan"), float("inf")])
@pytest.mark.parametrize(
    "field",
    [
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
    ],
)
def test_forcing_rejects_negative_or_nonfinite_rate(field: str, bad: float) -> None:
    with pytest.raises(ValueError, match=f"forcing.{field}"):
        replace(BASE_FORCING, **{field: bad})


def test_local_api_rejects_arrays_and_wrong_container_types() -> None:
    with pytest.raises(ValueError, match="finite scalar"):
        replace(BASE_STATE, O=np.array([1.0]))
    with pytest.raises(TypeError, match="state must be"):
        close_local_chemistry({}, BASE_BACKGROUND, BASE_FORCING)  # type: ignore[arg-type]
