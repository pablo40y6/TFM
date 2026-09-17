"""Structural and provenance tests for the M2 reaction registry."""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

import pytest

from tfm_photochem.historical_2020.config import (
    BIMOLECULAR_RATE_UNIT,
    CHEMICAL_SPECIES,
    CONFIGURATION,
    FIRST_ORDER_RATE_UNIT,
    IMPLEMENTED_COEFFICIENT,
    PENDING_INPUT,
    TERMOLECULAR_RATE_UNIT,
    VALID_IMPLEMENTATION_STATUSES,
    VALID_REACTION_TYPES,
)
from tfm_photochem.historical_2020.kinetics import RATE_LAWS
from tfm_photochem.historical_2020.reactions import (
    REACTION_BY_ID,
    REACTIONS,
    SCALAR_PARAMETERS,
)


def test_registry_has_unique_stable_ids_and_index() -> None:
    identifiers = [reaction.identifier for reaction in REACTIONS]
    assert len(identifiers) == len(set(identifiers))
    assert set(REACTION_BY_ID) == set(identifiers)
    assert all(identifier == identifier.upper() for identifier in identifiers)


def test_registry_records_complete_structure_and_provenance() -> None:
    for reaction in REACTIONS:
        assert reaction.equation
        assert reaction.reactants
        assert reaction.products
        assert reaction.modifies
        assert reaction.reaction_type in VALID_REACTION_TYPES
        assert reaction.status in VALID_IMPLEMENTATION_STATUSES
        assert reaction.configuration == CONFIGURATION
        assert reaction.reference.strip()
        assert reaction.year > 1900
        assert reaction.provenance_note.strip()
        assert reaction.li2020_link.strip()
        assert reaction.coefficient_unit.strip()
        for species, stoichiometry in reaction.reactants + reaction.products:
            assert species in CHEMICAL_SPECIES
            assert stoichiometry > 0
        assert set(reaction.modifies) <= CHEMICAL_SPECIES


def test_coefficient_status_is_explicit_and_consistent() -> None:
    for reaction in REACTIONS:
        if reaction.status == IMPLEMENTED_COEFFICIENT:
            assert reaction.coefficient_id in RATE_LAWS
            assert reaction.coefficient_unit == RATE_LAWS[reaction.coefficient_id].unit
        else:
            assert reaction.status == PENDING_INPUT
            assert reaction.coefficient_id is None
            assert "PENDING INPUT" in reaction.provenance_note


def test_no_unexplained_duplicate_stoichiometric_processes() -> None:
    groups: dict[tuple[object, ...], list[object]] = defaultdict(list)
    for reaction in REACTIONS:
        signature = (
            tuple(sorted(reaction.reactants)),
            tuple(sorted(reaction.products)),
            reaction.reaction_type,
        )
        groups[signature].append(reaction)
    duplicates = [group for group in groups.values() if len(group) > 1]
    assert len(duplicates) == 1
    assert {reaction.identifier for reaction in duplicates[0]} == {
        "O2_SRC",
        "O2_LYMAN_ALPHA",
    }
    assert all(
        "distinct spectral" in reaction.provenance_note for reaction in duplicates[0]
    )


def test_rate_law_metadata_is_complete() -> None:
    assert len(RATE_LAWS) == len(set(RATE_LAWS))
    for identifier, law in RATE_LAWS.items():
        assert law.identifier == identifier
        assert law.expression.strip()
        assert law.unit.strip()
        assert law.reference.strip()
        assert law.year > 1900
        assert law.configuration == CONFIGURATION
        assert law.note.strip()
        assert law.molecular_order in {1, 2, 3}


@pytest.mark.parametrize(
    "reaction", REACTIONS, ids=lambda reaction: reaction.identifier
)
def test_coefficient_units_match_process_order(reaction: object) -> None:
    if reaction.status == PENDING_INPUT:
        return
    law = RATE_LAWS[reaction.coefficient_id]
    if reaction.reaction_type == "termolecular":
        assert law.unit == TERMOLECULAR_RATE_UNIT
        assert law.molecular_order == 3
    elif reaction.reaction_type == "radiative":
        assert law.unit == FIRST_ORDER_RATE_UNIT
        assert law.molecular_order == 1
    else:
        assert law.unit == BIMOLECULAR_RATE_UNIT
        assert law.molecular_order == 2


def test_photolysis_and_excitation_pending_inputs_are_first_order() -> None:
    for reaction in REACTIONS:
        if (
            reaction.status == PENDING_INPUT
            and ("photon", 1) in reaction.reactants
            and reaction.reaction_type
            in {
                "photolysis",
                "excitation",
            }
        ):
            assert reaction.coefficient_unit == FIRST_ORDER_RATE_UNIT


def test_efficiencies_and_barth_parameters_have_full_provenance() -> None:
    for name, parameter in SCALAR_PARAMETERS.items():
        assert name
        assert parameter.unit
        assert parameter.reference
        assert parameter.year > 1900
        assert parameter.configuration == CONFIGURATION
        assert parameter.note
    used_efficiencies = {
        reaction.efficiency_id for reaction in REACTIONS if reaction.efficiency_id
    }
    assert used_efficiencies <= set(SCALAR_PARAMETERS)
    assert SCALAR_PARAMETERS["branch_o1d_o2_b1"].value == pytest.approx(0.8)
    assert SCALAR_PARAMETERS["branch_o1d_o2_b0"].value == pytest.approx(0.2)
    assert sum(
        SCALAR_PARAMETERS[name].value
        for name in ("branch_o1d_o2_b1", "branch_o1d_o2_b0")
    ) == pytest.approx(1.0)


def test_photolysis_efficiencies_are_product_yields_not_total_loss_factors() -> None:
    for name, reactant in (
        ("yield_o3_hartley_delta_o1d", "O3"),
        ("yield_o2_lya_o1d", "O2"),
    ):
        note = SCALAR_PARAMETERS[name].note
        assert "Product-channel yield" in note
        assert f"must not scale the future total {reactant} photolysis loss" in note


def test_b0_o3_keeps_li_routing_with_jpl_total_coefficient() -> None:
    reaction = REACTION_BY_ID["B0_O3"]
    assert reaction.reactants == (("B0", 1), ("O3", 1))
    assert reaction.products == (("Delta", 1), ("O3", 1))
    assert reaction.reference == "JPL Publication 15-10, Evaluation 18"
    assert "total temperature-dependent" in reaction.provenance_note
    assert "Li 2020 model-routing assumption" in reaction.provenance_note
    assert "not a claim" in reaction.provenance_note


def test_delta_o3_topology_is_jpl18_not_li_printed_topology() -> None:
    reaction = REACTION_BY_ID["DELTA_O3"]
    assert reaction.reactants == (("Delta", 1), ("O3", 1))
    assert reaction.products == (("O", 1), ("O2", 2))
    assert reaction.modifies == ("Delta", "O3", "O")
    assert reaction.reference == "JPL Publication 15-10, Evaluation 18"
    assert "JPL topology and rate law" in reaction.provenance_note
    assert "-O3 and +O" in reaction.provenance_note


def test_historical_kinetics_does_not_import_legacy_numerics() -> None:
    source = Path("src/tfm_photochem/historical_2020/kinetics.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_modules |= {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert not any("legacy_2017" in module for module in imported_modules)


def test_m4a_does_not_contain_future_column_or_radiation_modules() -> None:
    package = Path("src/tfm_photochem/historical_2020")
    forbidden = {
        "rhs.py",
        "periodic.py",
        "radiation.py",
        "column.py",
        "integrator.py",
    }
    assert not ({path.name for path in package.iterdir()} & forbidden)
