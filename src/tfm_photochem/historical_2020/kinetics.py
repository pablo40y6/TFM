"""Historical rate coefficients used by the Milestone-2 reaction registry.

All coefficients are in molecule--centimetre--second units.  The functions
return coefficients only: termolecular functions do *not* multiply by ``M``.
The sole exception is :func:`k_ho2_ho2`, whose published JPL expression is an
effective bimolecular coefficient containing an explicit ``M`` term.

No function in this module imports numerical content from ``legacy_2017``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .config import (
    BIMOLECULAR_RATE_UNIT,
    CONFIGURATION,
    FIRST_ORDER_RATE_UNIT,
    TERMOLECULAR_RATE_UNIT,
)

ScalarOrArray = float | NDArray[np.float64]


@dataclass(frozen=True)
class RateLaw:
    """A callable coefficient together with audit-ready provenance."""

    identifier: str
    evaluator: Callable[..., ScalarOrArray]
    expression: str
    unit: str
    molecular_order: int
    reference: str
    year: int
    configuration: str
    note: str
    arguments: tuple[str, ...]


def _validated(name: str, value: ArrayLike, *, strictly_positive: bool) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    if strictly_positive and np.any(array <= 0.0):
        raise ValueError(f"{name} must be strictly positive")
    if not strictly_positive and np.any(array < 0.0):
        raise ValueError(f"{name} must be non-negative")
    return array


def _temperature(temperature_k: ArrayLike) -> np.ndarray:
    return _validated("temperature_k", temperature_k, strictly_positive=True)


def _number_density(name: str, value: ArrayLike) -> np.ndarray:
    return _validated(name, value, strictly_positive=False)


def _result(value: np.ndarray | np.float64 | float) -> ScalarOrArray:
    array = np.asarray(value, dtype=float)
    return float(array) if array.ndim == 0 else array


def k_o_o2_m(temperature_k: ArrayLike) -> ScalarOrArray:
    """O + O2 + M -> O3 + M, JPL 18 Table 2-1."""

    temperature = _temperature(temperature_k)
    return _result(6.0e-34 * (300.0 / temperature) ** 2.4)


def k_o_o3(temperature_k: ArrayLike) -> ScalarOrArray:
    """O + O3 -> 2 O2, JPL 18 Table 1A (Ox)."""

    temperature = _temperature(temperature_k)
    return _result(8.0e-12 * np.exp(-2060.0 / temperature))


def k_o_o_m_barth(temperature_k: ArrayLike) -> ScalarOrArray:
    """2 O + M -> O2* + M in the effective Barth mechanism."""

    temperature = _temperature(temperature_k)
    return _result(4.7e-33 * (300.0 / temperature) ** 2.0)


def k_h_o2_m(temperature_k: ArrayLike) -> ScalarOrArray:
    """H + O2 + M -> HO2 + M, JPL 18 Table 2-1 low-pressure limit."""

    temperature = _temperature(temperature_k)
    return _result(4.4e-32 * (300.0 / temperature) ** 1.3)


def k_h_o3(temperature_k: ArrayLike) -> ScalarOrArray:
    temperature = _temperature(temperature_k)
    return _result(1.4e-10 * np.exp(-470.0 / temperature))


def k_o_oh(temperature_k: ArrayLike) -> ScalarOrArray:
    temperature = _temperature(temperature_k)
    return _result(1.8e-11 * np.exp(180.0 / temperature))


def k_o_ho2(temperature_k: ArrayLike) -> ScalarOrArray:
    temperature = _temperature(temperature_k)
    return _result(3.0e-11 * np.exp(200.0 / temperature))


def k_oh_o3(temperature_k: ArrayLike) -> ScalarOrArray:
    temperature = _temperature(temperature_k)
    return _result(1.7e-12 * np.exp(-940.0 / temperature))


def k_ho2_o3(temperature_k: ArrayLike) -> ScalarOrArray:
    temperature = _temperature(temperature_k)
    return _result(1.0e-14 * np.exp(-490.0 / temperature))


def k_oh_h2(temperature_k: ArrayLike) -> ScalarOrArray:
    temperature = _temperature(temperature_k)
    return _result(2.8e-12 * np.exp(-1800.0 / temperature))


def k_h_ho2_2oh() -> float:
    return 7.2e-11


def k_h_ho2_h2o_o() -> float:
    return 1.6e-12


def k_h_ho2_h2_o2() -> float:
    return 6.9e-12


def k_oh_oh() -> float:
    return 1.8e-12


def k_oh_ho2(temperature_k: ArrayLike) -> ScalarOrArray:
    temperature = _temperature(temperature_k)
    return _result(4.8e-11 * np.exp(250.0 / temperature))


def k_ho2_ho2(temperature_k: ArrayLike, m_cm3: ArrayLike) -> ScalarOrArray:
    """Effective HO2 self-reaction coefficient, JPL 18 Table 1B.

    The optional water-complex enhancement described in JPL 18 is not part of
    the frozen baseline expression and is therefore not applied here.
    """

    temperature = _temperature(temperature_k)
    m = _number_density("m_cm3", m_cm3)
    try:
        temperature, m = np.broadcast_arrays(temperature, m)
    except ValueError as exc:
        raise ValueError(
            "temperature_k and m_cm3 are not broadcast-compatible"
        ) from exc
    value = 3.0e-13 * np.exp(460.0 / temperature)
    value += 2.1e-33 * m * np.exp(920.0 / temperature)
    return _result(value)


def k_oh_h2o2() -> float:
    return 1.8e-12


def a_o1d() -> float:
    return 6.81e-3


def a_b0() -> float:
    return 8.34e-2


def a_b1() -> float:
    return 7.2e-2


def a_delta() -> float:
    return 2.26e-4


def k_o1d_n2(temperature_k: ArrayLike) -> ScalarOrArray:
    temperature = _temperature(temperature_k)
    return _result(2.15e-11 * np.exp(110.0 / temperature))


def k_o1d_o2(temperature_k: ArrayLike) -> ScalarOrArray:
    temperature = _temperature(temperature_k)
    return _result(3.3e-11 * np.exp(55.0 / temperature))


def k_o1d_h2o(temperature_k: ArrayLike) -> ScalarOrArray:
    temperature = _temperature(temperature_k)
    return _result(1.63e-10 * np.exp(60.0 / temperature))


def k_o1d_h2() -> float:
    return 1.2e-10


def k_b1_o2(temperature_k: ArrayLike) -> ScalarOrArray:
    temperature = _temperature(temperature_k)
    return _result(2.2e-11 * np.exp(-115.0 / temperature))


def k_b1_n2() -> float:
    return 7.0e-13


def k_b1_o() -> float:
    return 4.5e-12


def k_b1_o3() -> float:
    return 3.0e-10


def k_b0_n2(temperature_k: ArrayLike) -> ScalarOrArray:
    """B0 + N2 total loss, JPL 18 Table 1A A86."""

    temperature = _temperature(temperature_k)
    return _result(1.8e-15 * np.exp(45.0 / temperature))


def k_b0_o2() -> float:
    return 3.9e-17


def k_b0_o() -> float:
    return 8.0e-14


def k_b0_o3(temperature_k: ArrayLike) -> ScalarOrArray:
    """B0 + O3 total loss, JPL 18 Table 1A A82."""

    temperature = _temperature(temperature_k)
    return _result(3.5e-11 * np.exp(-135.0 / temperature))


def k_b0_co2() -> float:
    return 4.2e-13


def k_delta_o2(temperature_k: ArrayLike) -> ScalarOrArray:
    temperature = _temperature(temperature_k)
    return _result(3.6e-18 * np.exp(-220.0 / temperature))


def k_delta_n2() -> float:
    return 1.0e-20


def k_delta_o() -> float:
    return 2.0e-16


def k_delta_o3(temperature_k: ArrayLike) -> ScalarOrArray:
    temperature = _temperature(temperature_k)
    return _result(5.2e-11 * np.exp(-2840.0 / temperature))


JPL18 = "JPL Publication 15-10, Evaluation 18"
LI2020 = "Li et al., Atmospheric Measurement Techniques 13 (2020), Table A1"
BS2005 = "Brasseur and Solomon (2005), Aeronomy, Table 4.5"


def _law(
    identifier: str,
    evaluator: Callable[..., ScalarOrArray],
    expression: str,
    unit: str,
    order: int,
    reference: str,
    year: int,
    note: str,
    arguments: tuple[str, ...] = ("temperature_k",),
) -> RateLaw:
    return RateLaw(
        identifier=identifier,
        evaluator=evaluator,
        expression=expression,
        unit=unit,
        molecular_order=order,
        reference=reference,
        year=year,
        configuration=CONFIGURATION,
        note=note,
        arguments=arguments,
    )


_JPL_TABLE_1 = "JPL 18 Table 1; A exp(-E/R/T), molecule-cm-s units."
_LI_A1 = "Li 2020 Table A1; retained as the approved historical topology."
_B1_LI_A1 = (
    "Li 2020 Table A1 adoption via the Yankovsky et al. (2016) reference "
    "compilation; value retained without a numerical update."
)

RATE_LAWS = {
    law.identifier: law
    for law in (
        _law(
            "k_o_o2_m",
            k_o_o2_m,
            "6.0e-34*(300/T)^2.4",
            TERMOLECULAR_RATE_UNIT,
            3,
            JPL18,
            2015,
            "JPL 18 Table 2-1, Ox A1.",
        ),
        _law(
            "k_o_o3",
            k_o_o3,
            "8.0e-12*exp(-2060/T)",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 Table 1A, Ox A1.",
        ),
        _law(
            "k_o_o_m_barth",
            k_o_o_m_barth,
            "4.7e-33*(300/T)^2",
            TERMOLECULAR_RATE_UNIT,
            3,
            BS2005,
            2005,
            "Li prints exp(300/T); the power law is explicit in Brasseur and Solomon Table 4.5 and Anqi's executable 2017 listing.",
        ),
        _law(
            "k_h_o2_m",
            k_h_o2_m,
            "4.4e-32*(300/T)^1.3",
            TERMOLECULAR_RATE_UNIT,
            3,
            JPL18,
            2015,
            "JPL 18 Table 2-1 low-pressure limit, HOx B1.",
        ),
        _law(
            "k_h_o3",
            k_h_o3,
            "1.4e-10*exp(-470/T)",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            _JPL_TABLE_1,
        ),
        _law(
            "k_o_oh",
            k_o_oh,
            "1.8e-11*exp(+180/T)",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            _JPL_TABLE_1,
        ),
        _law(
            "k_o_ho2",
            k_o_ho2,
            "3.0e-11*exp(+200/T)",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            _JPL_TABLE_1,
        ),
        _law(
            "k_oh_o3",
            k_oh_o3,
            "1.7e-12*exp(-940/T)",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            _JPL_TABLE_1,
        ),
        _law(
            "k_ho2_o3",
            k_ho2_o3,
            "1.0e-14*exp(-490/T)",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            _JPL_TABLE_1,
        ),
        _law(
            "k_oh_h2",
            k_oh_h2,
            "2.8e-12*exp(-1800/T)",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            _JPL_TABLE_1,
        ),
        _law(
            "k_h_ho2_2oh",
            k_h_ho2_2oh,
            "7.2e-11",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 Table 1B, HOx B5, channel 2 OH.",
            (),
        ),
        _law(
            "k_h_ho2_h2o_o",
            k_h_ho2_h2o_o,
            "1.6e-12",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 Table 1B, HOx B5, channel H2O + O.",
            (),
        ),
        _law(
            "k_h_ho2_h2_o2",
            k_h_ho2_h2_o2,
            "6.9e-12",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 Table 1B, HOx B5, channel H2 + O2.",
            (),
        ),
        _law(
            "k_oh_oh",
            k_oh_oh,
            "1.8e-12",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 Table 1B, HOx B9.",
            (),
        ),
        _law(
            "k_oh_ho2",
            k_oh_ho2,
            "4.8e-11*exp(+250/T)",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            _JPL_TABLE_1,
        ),
        _law(
            "k_ho2_ho2",
            k_ho2_ho2,
            "3.0e-13*exp(+460/T) + 2.1e-33*M*exp(+920/T)",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 Table 1B, HOx B13; effective second-order coefficient; frozen baseline omits the separate H2O enhancement.",
            ("temperature_k", "m_cm3"),
        ),
        _law(
            "k_oh_h2o2",
            k_oh_h2o2,
            "1.8e-12",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 Note B11 recommendation for 200-300 K.",
            (),
        ),
        _law(
            "a_o1d",
            a_o1d,
            "6.81e-3",
            FIRST_ORDER_RATE_UNIT,
            1,
            LI2020,
            2020,
            _LI_A1,
            (),
        ),
        _law(
            "a_b0", a_b0, "8.34e-2", FIRST_ORDER_RATE_UNIT, 1, LI2020, 2020, _LI_A1, ()
        ),
        _law(
            "a_b1", a_b1, "7.2e-2", FIRST_ORDER_RATE_UNIT, 1, LI2020, 2020, _LI_A1, ()
        ),
        _law(
            "a_delta",
            a_delta,
            "2.26e-4",
            FIRST_ORDER_RATE_UNIT,
            1,
            LI2020,
            2020,
            "Li 2020 Table A1. The project convention is the 1.27 micrometre band; the table typesets 1.24 micrometres.",
            (),
        ),
        _law(
            "k_o1d_n2",
            k_o1d_n2,
            "2.15e-11*exp(+110/T)",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 Table 1A, O(1D) A7. Li prints the opposite exponent sign.",
        ),
        _law(
            "k_o1d_o2",
            k_o1d_o2,
            "3.3e-11*exp(+55/T)",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 Table 1A, O(1D) A3. Li prints the opposite exponent sign; Li's 0.8/0.2 B1/B0 routing is retained separately.",
        ),
        _law(
            "k_o1d_h2o",
            k_o1d_h2o,
            "1.63e-10*exp(+60/T)",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 Table 1A, O(1D) A6.",
        ),
        _law(
            "k_o1d_h2",
            k_o1d_h2,
            "1.2e-10",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 Table 1A, O(1D) A5.",
            (),
        ),
        _law(
            "k_b1_o2",
            k_b1_o2,
            "2.2e-11*exp(-115/T)",
            BIMOLECULAR_RATE_UNIT,
            2,
            LI2020,
            2020,
            _B1_LI_A1,
        ),
        _law(
            "k_b1_n2",
            k_b1_n2,
            "7.0e-13",
            BIMOLECULAR_RATE_UNIT,
            2,
            LI2020,
            2020,
            _B1_LI_A1,
            (),
        ),
        _law(
            "k_b1_o",
            k_b1_o,
            "4.5e-12",
            BIMOLECULAR_RATE_UNIT,
            2,
            LI2020,
            2020,
            _B1_LI_A1,
            (),
        ),
        _law(
            "k_b1_o3",
            k_b1_o3,
            "3.0e-10",
            BIMOLECULAR_RATE_UNIT,
            2,
            LI2020,
            2020,
            _B1_LI_A1,
            (),
        ),
        _law(
            "k_b0_n2",
            k_b0_n2,
            "1.8e-15*exp(+45/T)",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 Table 1A A86 total coefficient; Li's Delta-product routing is recorded in the reaction registry.",
        ),
        _law(
            "k_b0_o2",
            k_b0_o2,
            "3.9e-17",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 Table 1A, singlet O2 A81; Li routes the product to Delta.",
            (),
        ),
        _law(
            "k_b0_o",
            k_b0_o,
            "8.0e-14",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 Table 1A, singlet O2 A80; Li routes the product to Delta.",
            (),
        ),
        _law(
            "k_b0_o3",
            k_b0_o3,
            "3.5e-11*exp(-135/T)",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 Table 1A A82 total loss coefficient. Its use with Li's non-destructive Delta-product routing is a model assumption, not a JPL branching claim.",
        ),
        _law(
            "k_b0_co2",
            k_b0_co2,
            "4.2e-13",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 Table 1A, singlet O2 A88; Li routes the product to Delta.",
            (),
        ),
        _law(
            "k_delta_o2",
            k_delta_o2,
            "3.6e-18*exp(-220/T)",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 Table 1A, singlet O2 A74.",
        ),
        _law(
            "k_delta_n2",
            k_delta_n2,
            "1.0e-20",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 A78 gives <1e-20; historical_2020 retains Li's boundary value.",
            (),
        ),
        _law(
            "k_delta_o",
            k_delta_o,
            "2.0e-16",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 A73 gives <2e-16; historical_2020 retains Li's boundary value.",
            (),
        ),
        _law(
            "k_delta_o3",
            k_delta_o3,
            "5.2e-11*exp(-2840/T)",
            BIMOLECULAR_RATE_UNIT,
            2,
            JPL18,
            2015,
            "JPL 18 Table 1A, singlet O2 A75. Li prints the opposite exponent sign.",
        ),
    )
}
