"""Reduced two-channel odd-oxygen photolysis partition for Milestone 4B."""

from __future__ import annotations

import sys
from dataclasses import dataclass

PARTITION_RELATIVE_TOLERANCE = 64.0 * sys.float_info.epsilon
GROSS_SUBSET_RELATIVE_TOLERANCE = PARTITION_RELATIVE_TOLERANCE


@dataclass(frozen=True)
class OddOxygenPhotolysisPartition:
    """Specific excited channels and effective ground-channel complements."""

    J2_star: float
    J2_ground: float
    J3_star: float
    J3_ground: float


def _validate_gross_subset(
    total: float, known_gross_subset: float, label: str
) -> None:
    difference = total - known_gross_subset
    scale = max(abs(total), abs(known_gross_subset), sys.float_info.min)
    tolerance = GROSS_SUBSET_RELATIVE_TOLERANCE * scale
    if difference < -tolerance:
        raise ValueError(
            f"{label}_TOTAL must be >= its known gross spectral subset; "
            f"got total={total!r}, known_gross_subset={known_gross_subset!r}"
        )


def _ground_complement(total: float, excited: float, label: str) -> float:
    difference = total - excited
    scale = max(abs(total), abs(excited), sys.float_info.min)
    tolerance = PARTITION_RELATIVE_TOLERANCE * scale
    if difference < -tolerance:
        raise ValueError(
            f"{label}_TOTAL must be >= its represented excited-channel rate; "
            f"got total={total!r}, excited={excited!r}"
        )
    if difference < 0.0:
        # This is an explicit floating-equality normalization, not clipping of
        # an invalid partition. Differences below -tolerance raise above.
        return 0.0
    return difference


def partition_odd_oxygen_photolysis(
    *,
    JH: float,
    J_SRC: float,
    J_LYA: float,
    J_O2_TOTAL: float,
    J_O3_TOTAL: float,
    yield_hartley_o1d: float = 0.9,
    yield_lya_o1d: float = 0.44,
) -> OddOxygenPhotolysisPartition:
    """Partition injected totals without calculating any radiative rate.

    Detailed VUV products not explicitly retained are folded into effective
    ground channels that close the reduced O + O1D + O3 atom budget.
    """

    # JH, J_SRC and J_LYA count gross parent photodissociations. Product
    # yields partition those events but do not reduce the gross subsets that
    # must be contained in the corresponding total photolysis coefficients.
    _validate_gross_subset(J_O2_TOTAL, J_SRC + J_LYA, "J_O2")
    _validate_gross_subset(J_O3_TOTAL, JH, "J_O3")

    j2_star = J_SRC + yield_lya_o1d * J_LYA
    j3_star = yield_hartley_o1d * JH
    return OddOxygenPhotolysisPartition(
        J2_star=j2_star,
        J2_ground=_ground_complement(J_O2_TOTAL, j2_star, "J_O2"),
        J3_star=j3_star,
        J3_ground=_ground_complement(J_O3_TOTAL, j3_star, "J_O3"),
    )
