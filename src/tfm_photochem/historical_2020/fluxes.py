"""Auditable scalar reaction/event flux evaluation through Milestone 4B."""

from __future__ import annotations

from types import MappingProxyType

from . import kinetics
from .config import CONFIGURATION
from .local_types import (
    AlgebraicState,
    LocalBackground,
    LocalForcing,
    LocalState,
    ModelAssumption,
)
from .photolysis_budget import partition_odd_oxygen_photolysis
from .qssa import barth_sources
from .reactions import SCALAR_PARAMETERS

BARTH_B0_ASSUMPTION = ModelAssumption(
    identifier="barth_effective_source_to_b0",
    statement="M3 baseline model assumption: effective Barth source -> B0",
    reference="TFM 2.0 Milestone-3 handoff; effective structure from McDade et al. (1986)",
    year=2026,
    configuration=CONFIGURATION,
)

ODD_OXYGEN_PHOTOLYSIS_ASSUMPTION = ModelAssumption(
    identifier="reduced_two_channel_odd_oxygen_photolysis",
    statement=(
        "Detailed unretained O2/O3 photoproducts are folded into effective "
        "ground channels that close the reduced O + O1D + O3 atom budget."
    ),
    reference=(
        "Anqi Li thesis (2017), Sect. 3.2 and Eqs. 3.4/3.7; Brasseur and "
        "Solomon (2005), Sect. 5.2.1; excited-state yields from JPL18"
    ),
    year=2026,
    configuration=CONFIGURATION,
)

MODEL_ASSUMPTIONS = MappingProxyType(
    {
        BARTH_B0_ASSUMPTION.identifier: BARTH_B0_ASSUMPTION,
        ODD_OXYGEN_PHOTOLYSIS_ASSUMPTION.identifier: (
            ODD_OXYGEN_PHOTOLYSIS_ASSUMPTION
        ),
    }
)


def evaluate_fluxes(
    state: LocalState,
    background: LocalBackground,
    forcing: LocalForcing,
    algebraic: AlgebraicState,
) -> dict[str, float]:
    """Evaluate event fluxes in molecule cm^-3 s^-1.

    Registry IDs are used wherever a registered process exists. Suffix keys are
    explicit diagnostics or the documented Hartley product-yield split.
    """

    t = background.T
    o1d, oh, ho2, h2o2, b0, b1 = (
        algebraic.O1D,
        algebraic.OH,
        algebraic.HO2,
        algebraic.H2O2,
        algebraic.B0,
        algebraic.B1,
    )
    hartley_yield = float(
        SCALAR_PARAMETERS["yield_o3_hartley_delta_o1d"].value
    )
    lya_yield = float(SCALAR_PARAMETERS["yield_o2_lya_o1d"].value)
    b1_branch = float(SCALAR_PARAMETERS["branch_o1d_o2_b1"].value)
    b0_branch = float(SCALAR_PARAMETERS["branch_o1d_o2_b0"].value)
    photolysis = partition_odd_oxygen_photolysis(
        JH=forcing.JH,
        J_SRC=forcing.J_SRC,
        J_LYA=forcing.J_LYA,
        J_O2_TOTAL=forcing.J_O2_TOTAL,
        J_O3_TOTAL=forcing.J_O3_TOTAL,
        yield_hartley_o1d=hartley_yield,
        yield_lya_o1d=lya_yield,
    )

    hartley_gross = forcing.JH * state.O3
    lya_gross = forcing.J_LYA * background.O2
    o1d_o2_total = kinetics.k_o1d_o2(t) * o1d * background.O2
    barth_total, barth_b0 = barth_sources(state, background)

    return {
        "O_ASSOCIATION": kinetics.k_o_o2_m(t)
        * state.O
        * background.O2
        * background.M,
        "O_O3": kinetics.k_o_o3(t) * state.O * state.O3,
        "BARTH_RECOMBINATION": barth_total,
        "H_O2_ASSOCIATION": kinetics.k_h_o2_m(t)
        * state.H
        * background.O2
        * background.M,
        "H_O3": kinetics.k_h_o3(t) * state.H * state.O3,
        "O_OH": kinetics.k_o_oh(t) * state.O * oh,
        "O_HO2": kinetics.k_o_ho2(t) * state.O * ho2,
        "OH_O3": kinetics.k_oh_o3(t) * oh * state.O3,
        "HO2_O3": kinetics.k_ho2_o3(t) * ho2 * state.O3,
        "OH_H2": kinetics.k_oh_h2(t) * oh * background.H2,
        "H_HO2_2OH": kinetics.k_h_ho2_2oh() * state.H * ho2,
        "H_HO2_H2O_O": kinetics.k_h_ho2_h2o_o() * state.H * ho2,
        "H_HO2_H2_O2": kinetics.k_h_ho2_h2_o2() * state.H * ho2,
        "OH_OH": kinetics.k_oh_oh() * oh**2,
        "OH_HO2": kinetics.k_oh_ho2(t) * oh * ho2,
        "HO2_HO2": kinetics.k_ho2_ho2(t, background.M) * ho2**2,
        "OH_H2O2": kinetics.k_oh_h2o2() * oh * h2o2,
        "H2O2_PHOTOLYSIS": forcing.J_H2O2 * h2o2,
        "H2O_PHOTOLYSIS_A": forcing.J_H2O_A * background.H2O,
        "H2O_PHOTOLYSIS_B": forcing.J_H2O_B * background.H2O,
        "O3_HARTLEY_GROSS": hartley_gross,
        "O3_HARTLEY_PRODUCTS": photolysis.J3_star * state.O3,
        "O3_HARTLEY_UNTRACKED": (1.0 - hartley_yield) * hartley_gross,
        "O3_PHOTOLYSIS_GROUND_EFFECTIVE": photolysis.J3_ground * state.O3,
        "O2_SRC": forcing.J_SRC * background.O2,
        "O2_LYMAN_ALPHA": lya_yield * lya_gross,
        "O2_LYMAN_ALPHA_GROSS": lya_gross,
        "O2_LYMAN_ALPHA_UNTRACKED": (1.0 - lya_yield) * lya_gross,
        "O2_PHOTOLYSIS_GROUND_EFFECTIVE": photolysis.J2_ground * background.O2,
        "O2_A_BAND": forcing.gA * background.O2,
        "O2_B_BAND": forcing.gB * background.O2,
        "O2_IRA_BAND": forcing.gIRA * background.O2,
        "O1D_RADIATIVE": kinetics.a_o1d() * o1d,
        "B0_RADIATIVE": kinetics.a_b0() * b0,
        "B1_RADIATIVE": kinetics.a_b1() * b1,
        "DELTA_RADIATIVE": kinetics.a_delta() * state.Delta,
        "O1D_N2": kinetics.k_o1d_n2(t) * o1d * background.N2,
        "O1D_O2_TOTAL": o1d_o2_total,
        "O1D_O2_B1": b1_branch * o1d_o2_total,
        "O1D_O2_B0": b0_branch * o1d_o2_total,
        "O1D_H2O": kinetics.k_o1d_h2o(t) * o1d * background.H2O,
        "O1D_H2": kinetics.k_o1d_h2() * o1d * background.H2,
        "B1_O2": kinetics.k_b1_o2(t) * b1 * background.O2,
        "B1_N2": kinetics.k_b1_n2() * b1 * background.N2,
        "B1_O": kinetics.k_b1_o() * b1 * state.O,
        "B1_O3": kinetics.k_b1_o3() * b1 * state.O3,
        "B0_N2": kinetics.k_b0_n2(t) * b0 * background.N2,
        "B0_O2": kinetics.k_b0_o2() * b0 * background.O2,
        "B0_O": kinetics.k_b0_o() * b0 * state.O,
        "B0_O3": kinetics.k_b0_o3(t) * b0 * state.O3,
        "B0_CO2": kinetics.k_b0_co2() * b0 * background.CO2,
        "DELTA_O2": kinetics.k_delta_o2(t) * state.Delta * background.O2,
        "DELTA_N2": kinetics.k_delta_n2() * state.Delta * background.N2,
        "DELTA_O": kinetics.k_delta_o() * state.Delta * state.O,
        "DELTA_O3": kinetics.k_delta_o3(t) * state.Delta * state.O3,
        "BARTH_B0_EFFECTIVE": barth_b0,
    }
