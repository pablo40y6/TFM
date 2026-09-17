"""Independent acceptance tests for the Milestone-4B odd-oxygen budget."""

from __future__ import annotations

import math
from dataclasses import fields, replace

import pytest

from tfm_photochem.historical_2020 import (
    LocalBackground,
    LocalForcing,
    LocalState,
    close_local_chemistry,
)
from tfm_photochem.historical_2020.photolysis_budget import (
    GROSS_SUBSET_RELATIVE_TOLERANCE,
    partition_odd_oxygen_photolysis,
)
from tfm_photochem.historical_2020.reactions import REACTION_BY_ID

STATE = LocalState(O=2.0e11, O3=2.0e8, H=2.0e7, R_H=5.0e7, Delta=1.0e8)
BACKGROUND = LocalBackground(
    T=200.0,
    M=2.0e13,
    O2=4.0e12,
    N2=1.5e13,
    CO2=8.0e9,
    H2O=2.0e7,
    H2=1.0e8,
)


def forcing(**changes: float) -> LocalForcing:
    values = {
        "JH": 0.0,
        "J_SRC": 0.0,
        "J_LYA": 0.0,
        "J_O2_TOTAL": 0.0,
        "J_O3_TOTAL": 0.0,
        "J_H2O2": 0.0,
        "J_H2O_A": 0.0,
        "J_H2O_B": 0.0,
        "gA": 0.0,
        "gB": 0.0,
        "gIRA": 0.0,
    }
    values.update(changes)
    return LocalForcing(**values)


def test_local_forcing_schema_is_exactly_the_eleven_injected_rates() -> None:
    assert [field.name for field in fields(LocalForcing)] == [
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
    ]


def test_partition_formulas_match_independent_arithmetic() -> None:
    result = partition_odd_oxygen_photolysis(
        JH=8.0e-3,
        J_SRC=2.0e-8,
        J_LYA=3.0e-9,
        J_O2_TOTAL=2.3e-8,
        J_O3_TOTAL=8.1e-3,
    )
    expected_j2_star = 2.0e-8 + 0.44 * 3.0e-9
    expected_j3_star = 0.9 * 8.0e-3
    assert result.J2_star == expected_j2_star
    assert result.J2_ground == 2.3e-8 - expected_j2_star
    assert result.J3_star == expected_j3_star
    assert result.J3_ground == 8.1e-3 - expected_j3_star


def test_hartley_only_total_budget() -> None:
    jh = 2.0e-3
    result = close_local_chemistry(
        STATE, BACKGROUND, forcing(JH=jh, J_O3_TOTAL=jh)
    )
    gross = jh * STATE.O3
    excited = result.fluxes["O3_HARTLEY_PRODUCTS"]
    ground = result.fluxes["O3_PHOTOLYSIS_GROUND_EFFECTIVE"]
    assert excited == pytest.approx(0.9 * gross, rel=2e-15)
    assert ground == pytest.approx(0.1 * gross, rel=2e-15)
    assert result.diagnostics.P_O1D == pytest.approx(0.9 * gross, rel=2e-15)
    assert result.contributions["O3_HARTLEY_PRODUCTS"]["Delta"] == pytest.approx(
        0.9 * gross, rel=2e-15
    )
    assert result.contributions["O3_PHOTOLYSIS_GROUND_EFFECTIVE"]["O"] == (
        ground
    )
    o3_photolysis = (
        result.contributions["O3_HARTLEY_PRODUCTS"]["O3"]
        + result.contributions["O3_PHOTOLYSIS_GROUND_EFFECTIVE"]["O3"]
    )
    assert o3_photolysis == pytest.approx(-gross, rel=2e-15)


def test_lyman_alpha_only_total_budget() -> None:
    jlya = 3.0e-9
    result = close_local_chemistry(
        STATE, BACKGROUND, forcing(J_LYA=jlya, J_O2_TOTAL=jlya)
    )
    gross = jlya * BACKGROUND.O2
    excited = result.fluxes["O2_LYMAN_ALPHA"]
    ground = result.fluxes["O2_PHOTOLYSIS_GROUND_EFFECTIVE"]
    direct_o = excited + 2.0 * ground
    assert excited == pytest.approx(0.44 * gross, rel=2e-15)
    assert ground == pytest.approx(0.56 * gross, rel=2e-15)
    assert direct_o == pytest.approx(1.56 * gross, rel=2e-15)
    assert result.diagnostics.P_O1D == pytest.approx(0.44 * gross, rel=2e-15)
    assert direct_o + result.diagnostics.P_O1D == pytest.approx(
        2.0 * gross, rel=2e-15
    )


def test_src_only_total_budget() -> None:
    jsrc = 2.0e-8
    result = close_local_chemistry(
        STATE, BACKGROUND, forcing(J_SRC=jsrc, J_O2_TOTAL=jsrc)
    )
    gross = jsrc * BACKGROUND.O2
    assert result.fluxes["O2_SRC"] == gross
    assert result.fluxes["O2_PHOTOLYSIS_GROUND_EFFECTIVE"] == 0.0
    assert result.contributions["O2_SRC"]["O"] == gross
    assert result.diagnostics.P_O1D == gross
    assert result.contributions["O2_SRC"]["O"] + result.diagnostics.P_O1D == (
        2.0 * gross
    )


def test_mixed_o2_photolysis_has_exact_two_atom_source_identity() -> None:
    rates = forcing(J_SRC=2.0e-8, J_LYA=3.0e-9, J_O2_TOTAL=2.8e-8)
    result = close_local_chemistry(STATE, BACKGROUND, rates)
    direct_o = (
        result.contributions["O2_SRC"]["O"]
        + result.contributions["O2_LYMAN_ALPHA"]["O"]
        + result.contributions["O2_PHOTOLYSIS_GROUND_EFFECTIVE"]["O"]
    )
    algebraic_o1d = (
        rates.J_SRC + 0.44 * rates.J_LYA
    ) * BACKGROUND.O2
    expected = 2.0 * rates.J_O2_TOTAL * BACKGROUND.O2
    assert direct_o + algebraic_o1d == pytest.approx(expected, rel=2e-15)


def test_mixed_o3_photolysis_exactly_redistributes_reduced_odd_oxygen() -> None:
    rates = forcing(JH=8.0e-3, J_O3_TOTAL=9.0e-3)
    result = close_local_chemistry(STATE, BACKGROUND, rates)
    o3_loss = (
        result.contributions["O3_HARTLEY_PRODUCTS"]["O3"]
        + result.contributions["O3_PHOTOLYSIS_GROUND_EFFECTIVE"]["O3"]
    )
    direct_o = result.contributions["O3_PHOTOLYSIS_GROUND_EFFECTIVE"]["O"]
    algebraic_o1d = 0.9 * rates.JH * STATE.O3
    scale = rates.J_O3_TOTAL * STATE.O3
    assert o3_loss == pytest.approx(-scale, rel=2e-15)
    assert abs(o3_loss + direct_o + algebraic_o1d) <= 2e-15 * scale


def test_invalid_total_below_excited_partition_raises_without_clipping() -> None:
    with pytest.raises(ValueError, match="represented excited-channel rate"):
        partition_odd_oxygen_photolysis(
            JH=1.0,
            J_SRC=0.0,
            J_LYA=0.0,
            J_O2_TOTAL=0.0,
            J_O3_TOTAL=1.0,
            yield_hartley_o1d=1.1,
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"JH": 1.0, "J_O3_TOTAL": 0.95},
        {"J_LYA": 1.0, "J_O2_TOTAL": 0.50},
        {"J_SRC": 1.0, "J_LYA": 1.0, "J_O2_TOTAL": 1.5},
    ],
)
def test_total_below_known_gross_spectral_subset_is_rejected(
    changes: dict[str, float],
) -> None:
    with pytest.raises(ValueError, match="known gross spectral subset"):
        forcing(**changes)


def test_exact_gross_subset_equalities_preserve_product_yield_complements() -> None:
    result = partition_odd_oxygen_photolysis(
        JH=1.0,
        J_SRC=2.0,
        J_LYA=1.0,
        J_O2_TOTAL=3.0,
        J_O3_TOTAL=1.0,
    )
    assert result.J3_ground == pytest.approx(0.1, rel=2e-15)
    assert result.J2_ground == pytest.approx(0.56, rel=2e-15)


def test_one_ulp_below_gross_subset_is_accepted_without_zeroing_complement() -> None:
    jh = 1.0
    jsrc = 2.0
    jlya = 1.0
    result = partition_odd_oxygen_photolysis(
        JH=jh,
        J_SRC=jsrc,
        J_LYA=jlya,
        J_O2_TOTAL=math.nextafter(jsrc + jlya, 0.0),
        J_O3_TOTAL=math.nextafter(jh, 0.0),
    )
    assert result.J3_ground == pytest.approx(
        math.nextafter(jh, 0.0) - 0.9 * jh, rel=2e-15
    )
    assert result.J2_ground == pytest.approx(
        math.nextafter(jsrc + jlya, 0.0) - (jsrc + 0.44 * jlya),
        rel=2e-15,
    )
    assert result.J3_ground > 0.0
    assert result.J2_ground > 0.0


def test_gross_subset_tolerance_is_tiny_and_documented_constant() -> None:
    assert GROSS_SUBSET_RELATIVE_TOLERANCE == 64.0 * math.ulp(1.0)


def test_new_totals_do_not_change_o1d_qssa_or_nonphotolysis_fluxes() -> None:
    base = forcing(
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
    )
    expanded = replace(base, J_O2_TOTAL=4.0e-8, J_O3_TOTAL=1.0e-2)
    old = close_local_chemistry(STATE, BACKGROUND, base)
    new = close_local_chemistry(STATE, BACKGROUND, expanded)
    assert old.algebraic == new.algebraic
    assert old.diagnostics.P_O1D == new.diagnostics.P_O1D
    excluded = {
        "O3_HARTLEY_GROSS",
        "O3_HARTLEY_PRODUCTS",
        "O3_HARTLEY_UNTRACKED",
        "O3_PHOTOLYSIS_GROUND_EFFECTIVE",
        "O2_SRC",
        "O2_LYMAN_ALPHA",
        "O2_LYMAN_ALPHA_GROSS",
        "O2_LYMAN_ALPHA_UNTRACKED",
        "O2_PHOTOLYSIS_GROUND_EFFECTIVE",
    }
    for flux_id in old.fluxes.keys() - excluded:
        assert old.fluxes[flux_id] == new.fluxes[flux_id]


def test_hartley_gross_is_diagnostic_not_a_second_parent_loss() -> None:
    result = close_local_chemistry(
        STATE, BACKGROUND, forcing(JH=8.0e-3, J_O3_TOTAL=8.0e-3)
    )
    assert "O3_HARTLEY_GROSS" not in result.contributions
    photolysis_loss = sum(
        row["O3"]
        for key, row in result.contributions.items()
        if key in {"O3_HARTLEY_PRODUCTS", "O3_PHOTOLYSIS_GROUND_EFFECTIVE"}
    )
    assert photolysis_loss == pytest.approx(
        -8.0e-3 * STATE.O3, rel=2e-15
    )


def test_registry_marks_effective_channels_as_corrective_not_li_table_a1() -> None:
    for reaction_id, equation_reference in (
        ("O2_PHOTOLYSIS_GROUND_EFFECTIVE", "Eq. 3.4"),
        ("O3_PHOTOLYSIS_GROUND_EFFECTIVE", "Eq. 3.7"),
    ):
        reaction = REACTION_BY_ID[reaction_id]
        assert "Anqi Li thesis (2017)" in reaction.reference
        assert equation_reference in reaction.reference
        assert "Brasseur and Solomon (2005)" in reaction.reference
        assert "not from Li 2020 Table A1" in reaction.provenance_note


@pytest.mark.parametrize("field", [field.name for field in fields(LocalForcing)])
@pytest.mark.parametrize("bad", [-1.0, float("nan"), float("inf")])
def test_every_forcing_field_still_rejects_negative_or_nonfinite_values(
    field: str, bad: float
) -> None:
    base = forcing()
    with pytest.raises(ValueError, match=f"forcing.{field}"):
        replace(base, **{field: bad})
