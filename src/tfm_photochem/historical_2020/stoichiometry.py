"""Registry-derived dynamic tendency coefficients and scalar assembly."""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from .config import DYNAMIC_SPECIES
from .local_types import LocalTendencies, freeze_nested_mapping
from .reactions import REACTION_BY_ID

_UNEVALUATED_EFFECTIVE_STEPS = frozenset(
    {"BARTH_TRANSFER", "BARTH_O2STAR_QUENCH", "O3_HARTLEY"}
)
_DIAGNOSTIC_FLUX_IDS = frozenset(
    {
        "O3_HARTLEY_GROSS",
        "O3_HARTLEY_UNTRACKED",
        "O2_LYMAN_ALPHA_GROSS",
        "O2_LYMAN_ALPHA_UNTRACKED",
        "O1D_O2_TOTAL",
        "BARTH_B0_EFFECTIVE",
    }
)


def _net_stoichiometry(reaction_id: str, species: str) -> float:
    reaction = REACTION_BY_ID[reaction_id]
    products = sum(value for name, value in reaction.products if name == species)
    reactants = sum(value for name, value in reaction.reactants if name == species)
    return products - reactants


def _dynamic_coefficients(reaction_id: str) -> dict[str, float]:
    coefficients = {
        species: _net_stoichiometry(reaction_id, species)
        for species in ("O", "O3", "H", "Delta")
    }
    coefficients["R_H"] = _net_stoichiometry(
        reaction_id, "OH"
    ) + _net_stoichiometry(reaction_id, "HO2")
    return {species: coefficients[species] for species in DYNAMIC_SPECIES}


_coefficients = {
    reaction_id: _dynamic_coefficients(reaction_id)
    for reaction_id in REACTION_BY_ID
    if reaction_id not in _UNEVALUATED_EFFECTIVE_STEPS
}

# The retained special key is now the actual 0.9 excited-channel event. The
# gross JH*O3 diagnostic is never assembled as an additional parent loss.
_coefficients["O3_HARTLEY_PRODUCTS"] = {
    "O": 0.0,
    "O3": -1.0,
    "H": 0.0,
    "R_H": 0.0,
    "Delta": 1.0,
}

TENDENCY_COEFFICIENTS: Mapping[str, Mapping[str, float]] = freeze_nested_mapping(
    _coefficients
)
SPECIAL_FLUX_RULES = MappingProxyType(
    {
        "O3_HARTLEY_PRODUCTS": (
            "Actual reduced 0.9 excited Hartley event attached to registered "
            "O3_HARTLEY: -O3, +Delta, and algebraic +O1D."
        )
    }
)


def assemble_tendencies(
    fluxes: Mapping[str, float],
) -> tuple[LocalTendencies, Mapping[str, Mapping[str, float]]]:
    """Assemble five totals from per-event coefficients and return the trace."""

    missing = set(TENDENCY_COEFFICIENTS) - set(fluxes)
    if missing:
        raise KeyError(f"missing fluxes for tendency assembly: {sorted(missing)}")
    contributions = {
        flux_id: {
            species: coefficient * fluxes[flux_id]
            for species, coefficient in coefficients.items()
        }
        for flux_id, coefficients in TENDENCY_COEFFICIENTS.items()
    }
    totals = {
        species: sum(row[species] for row in contributions.values())
        for species in DYNAMIC_SPECIES
    }
    return LocalTendencies(**totals), freeze_nested_mapping(contributions)


def diagnostic_flux_ids() -> frozenset[str]:
    """Return flux keys intentionally excluded from dynamic assembly."""

    return _DIAGNOSTIC_FLUX_IDS
