"""Emit deterministic Milestone-4B odd-oxygen conservation evidence."""

from __future__ import annotations

import json
import math
from dataclasses import asdict

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
    values = {name: 0.0 for name in LocalForcing.__dataclass_fields__}
    values.update(changes)
    return LocalForcing(**values)


def evaluate_case(rates: LocalForcing) -> dict[str, object]:
    result = close_local_chemistry(STATE, BACKGROUND, rates)
    partition = partition_odd_oxygen_photolysis(
        JH=rates.JH,
        J_SRC=rates.J_SRC,
        J_LYA=rates.J_LYA,
        J_O2_TOTAL=rates.J_O2_TOTAL,
        J_O3_TOTAL=rates.J_O3_TOTAL,
    )
    o2_direct = (
        result.contributions["O2_SRC"]["O"]
        + result.contributions["O2_LYMAN_ALPHA"]["O"]
        + result.contributions["O2_PHOTOLYSIS_GROUND_EFFECTIVE"]["O"]
    )
    o2_o1d = partition.J2_star * BACKGROUND.O2
    o2_expected = 2.0 * rates.J_O2_TOTAL * BACKGROUND.O2
    o3_loss = (
        result.contributions["O3_HARTLEY_PRODUCTS"]["O3"]
        + result.contributions["O3_PHOTOLYSIS_GROUND_EFFECTIVE"]["O3"]
    )
    o3_direct = result.contributions["O3_PHOTOLYSIS_GROUND_EFFECTIVE"]["O"]
    o3_o1d = partition.J3_star * STATE.O3
    return {
        "forcing_s-1": asdict(rates),
        "partition_s-1": asdict(partition),
        "fluxes_molecule_cm-3_s-1": {
            name: result.fluxes[name]
            for name in (
                "O3_HARTLEY_GROSS",
                "O3_HARTLEY_PRODUCTS",
                "O3_PHOTOLYSIS_GROUND_EFFECTIVE",
                "O2_SRC",
                "O2_LYMAN_ALPHA",
                "O2_PHOTOLYSIS_GROUND_EFFECTIVE",
            )
        },
        "O2_identity": {
            "direct_O": o2_direct,
            "algebraic_O1D": o2_o1d,
            "expected_two_atoms": o2_expected,
            "residual": o2_direct + o2_o1d - o2_expected,
        },
        "O3_identity": {
            "O3_loss": o3_loss,
            "direct_O": o3_direct,
            "algebraic_O1D": o3_o1d,
            "residual": o3_loss + o3_direct + o3_o1d,
        },
        "Delta_direct_Hartley": result.contributions[
            "O3_HARTLEY_PRODUCTS"
        ]["Delta"],
    }


def invalid_case(**changes: float) -> dict[str, object]:
    try:
        forcing(**changes)
    except ValueError as error:
        return {"raised": True, "error": str(error)}
    return {"raised": False, "error": None}


def invalid_excited_partition_case() -> dict[str, object]:
    try:
        partition_odd_oxygen_photolysis(
            JH=1.0,
            J_SRC=0.0,
            J_LYA=0.0,
            J_O2_TOTAL=0.0,
            J_O3_TOTAL=1.0,
            yield_hartley_o1d=1.1,
        )
    except ValueError as error:
        return {"raised": True, "error": str(error)}
    return {"raised": False, "error": None}


def main() -> None:
    payload = {
        "configuration": "historical_2020",
        "scope": "M4B injected-forcing bookkeeping; no radiation calculation",
        "formulas": {
            "J2_star": "J_SRC + 0.44*J_LYA",
            "J2_ground": "J_O2_TOTAL - J2_star",
            "J3_star": "0.9*JH",
            "J3_ground": "J_O3_TOTAL - J3_star",
        },
        "gross_subset_contract": {
            "O2": "J_O2_TOTAL >= J_SRC + J_LYA",
            "O3": "J_O3_TOTAL >= JH",
            "relative_tolerance": GROSS_SUBSET_RELATIVE_TOLERANCE,
            "meaning": (
                "gross parent photodissociation subsets, before product yields"
            ),
        },
        "boundary_partitions": {
            "exact_gross_subset_equality": asdict(
                partition_odd_oxygen_photolysis(
                    JH=1.0,
                    J_SRC=2.0,
                    J_LYA=1.0,
                    J_O2_TOTAL=3.0,
                    J_O3_TOTAL=1.0,
                )
            ),
            "one_ulp_below_gross_subset_equality": asdict(
                partition_odd_oxygen_photolysis(
                    JH=1.0,
                    J_SRC=2.0,
                    J_LYA=1.0,
                    J_O2_TOTAL=math.nextafter(3.0, 0.0),
                    J_O3_TOTAL=math.nextafter(1.0, 0.0),
                )
            ),
        },
        "cases": {
            "hartley_only": evaluate_case(
                forcing(JH=8.0e-3, J_O3_TOTAL=8.0e-3)
            ),
            "lyman_only": evaluate_case(
                forcing(J_LYA=3.0e-9, J_O2_TOTAL=3.0e-9)
            ),
            "src_only": evaluate_case(
                forcing(J_SRC=2.0e-8, J_O2_TOTAL=2.0e-8)
            ),
            "mixed": evaluate_case(
                forcing(
                    JH=8.0e-3,
                    J_SRC=2.0e-8,
                    J_LYA=3.0e-9,
                    J_O2_TOTAL=2.8e-8,
                    J_O3_TOTAL=9.0e-3,
                )
            ),
        },
        "invalid_partitions": {
            "O3_total_below_gross_subset": invalid_case(
                JH=1.0, J_O3_TOTAL=0.95
            ),
            "O2_total_below_lyman_gross_subset": invalid_case(
                J_LYA=1.0, J_O2_TOTAL=0.5
            ),
            "O2_total_below_combined_gross_subset": invalid_case(
                J_SRC=1.0, J_LYA=1.0, J_O2_TOTAL=1.5
            ),
            "total_below_represented_excited_channel": (
                invalid_excited_partition_case()
            ),
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
