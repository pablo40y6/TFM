"""Independent numerical checks for the historical_2020 rate laws."""

from __future__ import annotations

import math

import numpy as np
import pytest

from tfm_photochem.historical_2020 import kinetics

T = 205.0
M = 2.5e13

# These expressions intentionally do not use production helpers or metadata.
EXPECTED = {
    "k_o_o2_m": lambda: 6.0e-34 * (300.0 / T) ** 2.4,
    "k_o_o3": lambda: 8.0e-12 * math.exp(-2060.0 / T),
    "k_o_o_m_barth": lambda: 4.7e-33 * (300.0 / T) ** 2,
    "k_h_o2_m": lambda: 4.4e-32 * (300.0 / T) ** 1.3,
    "k_h_o3": lambda: 1.4e-10 * math.exp(-470.0 / T),
    "k_o_oh": lambda: 1.8e-11 * math.exp(180.0 / T),
    "k_o_ho2": lambda: 3.0e-11 * math.exp(200.0 / T),
    "k_oh_o3": lambda: 1.7e-12 * math.exp(-940.0 / T),
    "k_ho2_o3": lambda: 1.0e-14 * math.exp(-490.0 / T),
    "k_oh_h2": lambda: 2.8e-12 * math.exp(-1800.0 / T),
    "k_h_ho2_2oh": lambda: 7.2e-11,
    "k_h_ho2_h2o_o": lambda: 1.6e-12,
    "k_h_ho2_h2_o2": lambda: 6.9e-12,
    "k_oh_oh": lambda: 1.8e-12,
    "k_oh_ho2": lambda: 4.8e-11 * math.exp(250.0 / T),
    "k_ho2_ho2": lambda: (
        3.0e-13 * math.exp(460.0 / T) + 2.1e-33 * M * math.exp(920.0 / T)
    ),
    "k_oh_h2o2": lambda: 1.8e-12,
    "a_o1d": lambda: 6.81e-3,
    "a_b0": lambda: 8.34e-2,
    "a_b1": lambda: 7.2e-2,
    "a_delta": lambda: 2.26e-4,
    "k_o1d_n2": lambda: 2.15e-11 * math.exp(110.0 / T),
    "k_o1d_o2": lambda: 3.3e-11 * math.exp(55.0 / T),
    "k_o1d_h2o": lambda: 1.63e-10 * math.exp(60.0 / T),
    "k_o1d_h2": lambda: 1.2e-10,
    "k_b1_o2": lambda: 2.2e-11 * math.exp(-115.0 / T),
    "k_b1_n2": lambda: 7.0e-13,
    "k_b1_o": lambda: 4.5e-12,
    "k_b1_o3": lambda: 3.0e-10,
    "k_b0_n2": lambda: 1.8e-15 * math.exp(45.0 / T),
    "k_b0_o2": lambda: 3.9e-17,
    "k_b0_o": lambda: 8.0e-14,
    "k_b0_o3": lambda: 3.5e-11 * math.exp(-135.0 / T),
    "k_b0_co2": lambda: 4.2e-13,
    "k_delta_o2": lambda: 3.6e-18 * math.exp(-220.0 / T),
    "k_delta_n2": lambda: 1.0e-20,
    "k_delta_o": lambda: 2.0e-16,
    "k_delta_o3": lambda: 5.2e-11 * math.exp(-2840.0 / T),
}


@pytest.mark.parametrize("identifier", sorted(EXPECTED))
def test_each_rate_law_against_published_expression(identifier: str) -> None:
    law = kinetics.RATE_LAWS[identifier]
    arguments = {"temperature_k": T, "m_cm3": M}
    actual = law.evaluator(*(arguments[name] for name in law.arguments))
    assert actual == pytest.approx(EXPECTED[identifier](), rel=2e-15)


def test_reference_table_covers_every_production_rate_law() -> None:
    assert set(EXPECTED) == set(kinetics.RATE_LAWS)


@pytest.mark.parametrize(
    "identifier",
    [
        "k_o_o2_m",
        "k_o_o_m_barth",
        "k_h_o2_m",
        "k_o_oh",
        "k_o_ho2",
        "k_oh_ho2",
        "k_ho2_ho2",
        "k_o1d_n2",
        "k_o1d_o2",
        "k_o1d_h2o",
        "k_b0_n2",
    ],
)
def test_inverse_temperature_laws_decrease_with_temperature(identifier: str) -> None:
    law = kinetics.RATE_LAWS[identifier]
    extra = (M,) if "m_cm3" in law.arguments else ()
    assert law.evaluator(180.0, *extra) > law.evaluator(260.0, *extra)


@pytest.mark.parametrize(
    "identifier",
    [
        "k_o_o3",
        "k_h_o3",
        "k_oh_o3",
        "k_ho2_o3",
        "k_oh_h2",
        "k_b1_o2",
        "k_b0_o3",
        "k_delta_o2",
        "k_delta_o3",
    ],
)
def test_activated_laws_increase_with_temperature(identifier: str) -> None:
    evaluator = kinetics.RATE_LAWS[identifier].evaluator
    assert evaluator(180.0) < evaluator(260.0)


@pytest.mark.parametrize(
    "identifier",
    [
        name
        for name, law in kinetics.RATE_LAWS.items()
        if "temperature_k" in law.arguments
    ],
)
def test_temperature_laws_accept_vectors_and_preserve_shape(identifier: str) -> None:
    law = kinetics.RATE_LAWS[identifier]
    temperature = np.array([160.0, 200.0, 260.0])
    arguments = {"temperature_k": temperature, "m_cm3": np.full(3, M)}
    value = law.evaluator(*(arguments[name] for name in law.arguments))
    assert isinstance(value, np.ndarray)
    assert value.shape == temperature.shape
    assert np.all(np.isfinite(value))
    assert np.all(value >= 0.0)


@pytest.mark.parametrize(
    "identifier",
    [
        name
        for name, law in kinetics.RATE_LAWS.items()
        if "temperature_k" in law.arguments
    ],
)
@pytest.mark.parametrize("invalid_temperature", [0.0, -1.0, float("nan")])
def test_temperature_laws_reject_invalid_temperature(
    identifier: str, invalid_temperature: float
) -> None:
    law = kinetics.RATE_LAWS[identifier]
    extra = (M,) if "m_cm3" in law.arguments else ()
    with pytest.raises(ValueError, match="temperature_k"):
        law.evaluator(invalid_temperature, *extra)


@pytest.mark.parametrize("invalid_m", [-1.0, float("nan"), float("inf")])
def test_ho2_self_reaction_rejects_invalid_number_density(invalid_m: float) -> None:
    with pytest.raises(ValueError, match="m_cm3"):
        kinetics.k_ho2_ho2(200.0, invalid_m)


def test_ho2_self_reaction_broadcasts_compatible_inputs() -> None:
    result = kinetics.k_ho2_ho2(np.array([180.0, 220.0]), M)
    assert isinstance(result, np.ndarray)
    assert result.shape == (2,)


def test_ho2_self_reaction_rejects_incompatible_shapes() -> None:
    with pytest.raises(ValueError, match="broadcast-compatible"):
        kinetics.k_ho2_ho2(np.ones(2) * 200.0, np.ones(3) * M)


def test_scalar_input_returns_python_float() -> None:
    assert isinstance(kinetics.k_o_o3(200.0), float)
    assert isinstance(kinetics.k_ho2_ho2(200.0, M), float)
    assert isinstance(kinetics.k_b0_n2(200.0), float)
    assert isinstance(kinetics.k_b0_o3(200.0), float)


@pytest.mark.parametrize("temperature_k", [150.0, 160.0, 180.0, 200.0, 220.0, 298.0])
def test_b0_n2_against_jpl18_reference_values(temperature_k: float) -> None:
    expected = 1.8e-15 * math.exp(45.0 / temperature_k)
    assert kinetics.k_b0_n2(temperature_k) == pytest.approx(expected, rel=2e-15)


@pytest.mark.parametrize("temperature_k", [150.0, 160.0, 180.0, 200.0, 220.0, 298.0])
def test_b0_o3_against_jpl18_reference_values(temperature_k: float) -> None:
    expected = 3.5e-11 * math.exp(-135.0 / temperature_k)
    assert kinetics.k_b0_o3(temperature_k) == pytest.approx(expected, rel=2e-15)


def test_corrected_li_signs_are_numerically_distinguishable() -> None:
    assert kinetics.k_o1d_n2(200.0) > 2.15e-11
    assert kinetics.k_o1d_o2(200.0) > 3.3e-11
    assert kinetics.k_delta_o3(200.0) < 5.2e-11
