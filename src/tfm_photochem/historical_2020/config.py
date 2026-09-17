"""Neutral, frozen conventions for the ``historical_2020`` configuration.

This module deliberately contains no atmospheric profiles. It provides stable
names and unit conventions shared by the registry, rate laws, and scalar M3
local closure.
"""

from __future__ import annotations

CONFIGURATION = "historical_2020"

CHEMISTRY_ALTITUDE_KM = (50.0, 100.0)
CHEMISTRY_SPACING_KM = 1.0
FUTURE_LEVEL_COUNT = 51

CONCENTRATION_UNIT = "molecule cm^-3"
TIME_UNIT = "s"
BIMOLECULAR_RATE_UNIT = "cm^3 molecule^-1 s^-1"
TERMOLECULAR_RATE_UNIT = "cm^6 molecule^-2 s^-1"
FIRST_ORDER_RATE_UNIT = "s^-1"
DIMENSIONLESS_UNIT = "1"

DYNAMIC_SPECIES = ("O", "O3", "H", "R_H", "Delta")
ALGEBRAIC_SPECIES = ("O1D", "OH", "HO2", "H2O2", "B0", "B1")
PRESCRIBED_SPECIES = ("T", "M", "O2", "N2", "CO2", "H2O", "H2")

# O2* is the unspecified excited intermediate in the effective Barth scheme.
AUXILIARY_SPECIES = ("O2star", "B_unspecified", "quenched_products", "photon")

CHEMICAL_SPECIES = frozenset(
    {
        "O",
        "O1D",
        "O2",
        "O3",
        "H",
        "OH",
        "HO2",
        "H2O2",
        "H2O",
        "H2",
        "N2",
        "CO2",
        "M",
        "B0",
        "B1",
        "Delta",
        "O2star",
        "B_unspecified",
        "quenched_products",
        "photon",
    }
)

VALID_REACTION_TYPES = frozenset(
    {
        "bimolecular",
        "termolecular",
        "photolysis",
        "radiative",
        "quenching",
        "excitation",
    }
)

IMPLEMENTED_COEFFICIENT = "implemented coefficient"
PENDING_INPUT = "PENDING INPUT"
VALID_IMPLEMENTATION_STATUSES = frozenset({IMPLEMENTED_COEFFICIENT, PENDING_INPUT})
