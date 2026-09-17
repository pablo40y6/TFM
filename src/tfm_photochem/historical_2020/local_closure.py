"""Orchestration of the Milestone-4B single-level chemical closure."""

from __future__ import annotations

from . import kinetics
from .fluxes import evaluate_fluxes
from .local_types import (
    AlgebraicState,
    LocalBackground,
    LocalClosureResult,
    LocalForcing,
    LocalState,
    ProductionLossDiagnostics,
    QSSAResiduals,
    freeze_mapping,
)
from .qssa import (
    barth_sources,
    solve_b0_qssa,
    solve_b1_qssa,
    solve_hox_qssa,
    solve_o1d_qssa,
)
from .stoichiometry import assemble_tendencies


def close_local_chemistry(
    state: LocalState,
    background: LocalBackground,
    forcing: LocalForcing,
) -> LocalClosureResult:
    """Close fast species and assemble local tendencies without time stepping."""

    if not isinstance(state, LocalState):
        raise TypeError("state must be a LocalState")
    if not isinstance(background, LocalBackground):
        raise TypeError("background must be a LocalBackground")
    if not isinstance(forcing, LocalForcing):
        raise TypeError("forcing must be a LocalForcing")

    o1d = solve_o1d_qssa(state, background, forcing)
    hox = solve_hox_qssa(state, background, forcing, o1d.value)
    b1 = solve_b1_qssa(state, background, forcing, o1d.value)
    barth_total, barth_b0 = barth_sources(state, background)
    b0 = solve_b0_qssa(
        state, background, forcing, o1d.value, b1.value, barth_b0
    )
    algebraic = AlgebraicState(
        O1D=o1d.value,
        OH=hox.OH,
        HO2=hox.HO2,
        H2O2=hox.H2O2,
        B0=b0.value,
        B1=b1.value,
    )
    flux_values = evaluate_fluxes(state, background, forcing, algebraic)
    tendencies, contributions = assemble_tendencies(flux_values)

    p_o1d = (
        flux_values["O3_HARTLEY_PRODUCTS"]
        + flux_values["O2_SRC"]
        + flux_values["O2_LYMAN_ALPHA"]
        + flux_values["H2O_PHOTOLYSIS_B"]
    )
    l_o1d = (
        kinetics.a_o1d()
        + kinetics.k_o1d_n2(background.T) * background.N2
        + kinetics.k_o1d_o2(background.T) * background.O2
        + kinetics.k_o1d_h2o(background.T) * background.H2O
        + kinetics.k_o1d_h2() * background.H2
    )
    p_oh = (
        flux_values["H_O3"]
        + flux_values["O_HO2"]
        + flux_values["HO2_O3"]
        + 2.0 * flux_values["H_HO2_2OH"]
        + 2.0 * flux_values["H2O2_PHOTOLYSIS"]
        + flux_values["H2O_PHOTOLYSIS_A"]
        + 2.0 * flux_values["O1D_H2O"]
        + flux_values["O1D_H2"]
    )
    l_oh = (
        flux_values["O_OH"]
        + flux_values["OH_O3"]
        + flux_values["OH_H2"]
        + 2.0 * flux_values["OH_OH"]
        + flux_values["OH_HO2"]
        + flux_values["OH_H2O2"]
    )
    p_b1 = flux_values["O2_B_BAND"] + flux_values["O1D_O2_B1"]
    l_b1 = (
        kinetics.a_b1()
        + kinetics.k_b1_o2(background.T) * background.O2
        + kinetics.k_b1_n2() * background.N2
        + kinetics.k_b1_o() * state.O
        + kinetics.k_b1_o3() * state.O3
    )
    p_b0 = (
        flux_values["O2_A_BAND"]
        + flux_values["O1D_O2_B0"]
        + flux_values["B1_O2"]
        + flux_values["B1_N2"]
        + flux_values["BARTH_B0_EFFECTIVE"]
    )
    l_b0 = (
        kinetics.a_b0()
        + kinetics.k_b0_n2(background.T) * background.N2
        + kinetics.k_b0_o2() * background.O2
        + kinetics.k_b0_o() * state.O
        + kinetics.k_b0_o3(background.T) * state.O3
        + kinetics.k_b0_co2() * background.CO2
    )
    p_delta = (
        flux_values["O3_HARTLEY_PRODUCTS"]
        + flux_values["O2_IRA_BAND"]
        + flux_values["B0_N2"]
        + flux_values["B0_O2"]
        + flux_values["B0_O"]
        + flux_values["B0_O3"]
        + flux_values["B0_CO2"]
    )
    l_delta = (
        kinetics.a_delta()
        + kinetics.k_delta_o2(background.T) * background.O2
        + kinetics.k_delta_n2() * background.N2
        + kinetics.k_delta_o() * state.O
        + kinetics.k_delta_o3(background.T) * state.O3
    )
    diagnostics = ProductionLossDiagnostics(
        P_O1D=p_o1d,
        L_O1D=l_o1d,
        P_OH=p_oh,
        L_OH=l_oh,
        P_H2O2=flux_values["HO2_HO2"],
        L_H2O2=forcing.J_H2O2 + kinetics.k_oh_h2o2() * algebraic.OH,
        P_B1=p_b1,
        L_B1=l_b1,
        P_B0=p_b0,
        L_B0=l_b0,
        P_Delta=p_delta,
        L_Delta=l_delta,
        hartley_gross=flux_values["O3_HARTLEY_GROSS"],
        hartley_products=flux_values["O3_HARTLEY_PRODUCTS"],
        hartley_untracked=flux_values["O3_HARTLEY_UNTRACKED"],
        lyman_alpha_gross=flux_values["O2_LYMAN_ALPHA_GROSS"],
        lyman_alpha_products=flux_values["O2_LYMAN_ALPHA"],
        lyman_alpha_untracked=flux_values["O2_LYMAN_ALPHA_UNTRACKED"],
        barth_total=barth_total,
        barth_b0=barth_b0,
    )
    residuals = QSSAResiduals(
        res_O1D=p_o1d - l_o1d * algebraic.O1D,
        res_OH=p_oh - l_oh,
        res_family=algebraic.OH + algebraic.HO2 - state.R_H,
        res_H2O2=(
            flux_values["HO2_HO2"]
            - diagnostics.L_H2O2 * algebraic.H2O2
        ),
        res_B1=p_b1 - l_b1 * algebraic.B1,
        res_B0=p_b0 - l_b0 * algebraic.B0,
    )
    return LocalClosureResult(
        algebraic=algebraic,
        fluxes=freeze_mapping(flux_values),
        residuals=residuals,
        diagnostics=diagnostics,
        contributions=contributions,
        tendencies=tendencies,
    )
