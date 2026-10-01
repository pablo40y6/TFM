"""Physical witnesses for the authorized twilight-equilibrium uniqueness gate."""

from dataclasses import replace

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from tfm_photochem.historical_2020 import kinetics
from tfm_photochem.historical_2020.background import load_baseline_background
from tfm_photochem.historical_2020.uv_geometry import spherical_shell_paths
from tfm_photochem.m5_temporal import (
    InitializationBlocker,
    local_rhs,
    reject_nonunique_dark_equilibrium,
)

from .test_historical_2020_local_closure import (
    BASE_BACKGROUND,
    BASE_FORCING,
    BASE_STATE,
    FORCING_OFF,
)


def test_rhs_delta_remains_dynamic_and_hartley_budget_is_retained():
    state = np.array([getattr(BASE_STATE, s) for s in ("O", "O3", "H", "R_H", "Delta")])
    first = local_rhs(0, state, background=BASE_BACKGROUND, forcing=BASE_FORCING)
    np.testing.assert_array_equal(
        first, local_rhs(0, state, background=BASE_BACKGROUND, forcing=BASE_FORCING)
    )
    changed = state.copy()
    changed[4] += 1e8
    other = local_rhs(0, changed, background=BASE_BACKGROUND, forcing=BASE_FORCING)
    loss = (
        kinetics.a_delta()
        + kinetics.k_delta_o2(BASE_BACKGROUND.T) * BASE_BACKGROUND.O2
        + kinetics.k_delta_n2() * BASE_BACKGROUND.N2
        + kinetics.k_delta_o() * BASE_STATE.O
        + kinetics.k_delta_o3(BASE_BACKGROUND.T) * BASE_STATE.O3
    )
    assert other[4] - first[4] == pytest.approx(-loss * 1e8, rel=1e-12)
    hartley_only = replace(FORCING_OFF, JH=1e-3, J_O3_TOTAL=1e-3)
    no_h = np.array([0.0, 1e8, 0.0, 0.0, 0.0])
    tendency = local_rhs(0, no_h, background=BASE_BACKGROUND, forcing=hartley_only)
    bg = BASE_BACKGROUND
    o1d = 0.9e5 / (
        kinetics.a_o1d() + kinetics.k_o1d_n2(bg.T) * bg.N2
        + kinetics.k_o1d_o2(bg.T) * bg.O2
        + kinetics.k_o1d_h2o(bg.T) * bg.H2O + kinetics.k_o1d_h2() * bg.H2
    )
    b1 = 0.8 * kinetics.k_o1d_o2(bg.T) * o1d * bg.O2 / (
        kinetics.a_b1() + kinetics.k_b1_o2(bg.T) * bg.O2
        + kinetics.k_b1_n2() * bg.N2 + kinetics.k_b1_o3() * no_h[1]
    )
    assert tendency[1] == pytest.approx(-1e5 - kinetics.k_b1_o3() * b1 * no_h[1])
    assert tendency[4] >= 0.9e5


@pytest.mark.parametrize("state", [[-1, 1, 1, 1, 1], [1, 1, np.nan, 1, 1], [1, 2]])
def test_rhs_rejects_invalid_states_without_clipping(state):
    with pytest.raises(ValueError):
        local_rhs(0, state, background=BASE_BACKGROUND, forcing=FORCING_OFF)


@pytest.mark.parametrize("altitude", range(50, 80))
def test_every_shadowed_height_has_distinct_exact_physical_roots(altitude):
    case = load_baseline_background()
    geometry = spherical_shell_paths(99)
    assert not geometry.illuminated[altitude - 50]
    ozone = case.radiative.O3_socrates_reference_cm3[altitude]
    with pytest.raises(InitializationBlocker) as error:
        reject_nonunique_dark_equilibrium(
            case.local_background_at(altitude), FORCING_OFF, ozone
        )
    assert error.value.witnesses[1].O3 / error.value.witnesses[0].O3 == pytest.approx(100)


def test_bdf_preserves_distinct_roots_for_one_day_not_a_unique_attractor():
    background = load_baseline_background().local_background_at(60)
    outcomes = []
    for ozone in (1e8, 1e10):
        initial = np.array([0.0, ozone, 0.0, 0.0, 0.0])
        result = solve_ivp(
            lambda t, y: local_rhs(t, y, background=background, forcing=FORCING_OFF),
            (0, 86400), initial, method="BDF", rtol=1e-9, atol=1e-8,
            max_step=3600, jac=np.zeros((5, 5)),
        )
        # Zero is an iteration Jacobian for this exact constant trajectory only;
        # it makes no stability claim or physical Jacobian approximation.
        assert result.success
        np.testing.assert_array_equal(result.y, np.repeat(initial[:, None], len(result.t), axis=1))
        outcomes.append(result.y[:, -1])
    assert outcomes[0][1] != outcomes[1][1]
