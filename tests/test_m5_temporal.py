"""Accepted temporal chemistry, periodic numerics and physical domain regressions."""

from dataclasses import replace

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from tfm_photochem.historical_2020 import kinetics
from tfm_photochem.historical_2020.background import load_baseline_background
from tfm_photochem.historical_2020.uv_geometry import spherical_shell_paths
from tfm_photochem.m5_temporal import (
    CachedLocalClosure,
    InitializationBlocker,
    NIRForcingTable,
    ReferenceColumnRHS,
    ReferenceEquinoxSolarCycle,
    bootstrap_seeds,
    cycle_difference,
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


def test_reference_cycle_exact_anchors_period_and_dawn_window():
    cycle = ReferenceEquinoxSolarCycle()
    np.testing.assert_allclose(cycle.sza([0, 21600, 43200, 64800, 86400]),
                               [135, 90, 45, 90, 135], atol=1e-13)
    np.testing.assert_array_equal(cycle.sza(np.arange(1000)),
                                  cycle.sza(np.arange(1000)+86400))
    start, end = cycle.dawn_window_s()
    np.testing.assert_allclose(cycle.sza([start, end]), [99, 60], atol=1e-13)
    assert 0 < start < end < 43200


def test_cached_chemistry_preserves_original_bytecode_and_every_result():
    from tfm_photochem.historical_2020.local_closure import close_local_chemistry

    cached = CachedLocalClosure()
    assert cached.close.__code__ is close_local_chemistry.__code__
    for factor in (0.1, 1.0, 10.0):
        state = replace(BASE_STATE, O=BASE_STATE.O*factor, R_H=BASE_STATE.R_H*factor)
        for forcing in (FORCING_OFF, BASE_FORCING):
            expected = close_local_chemistry(state, BASE_BACKGROUND, forcing)
            actual = cached.close(state, BASE_BACKGROUND, forcing)
            assert actual == expected


def test_nir_table_nodes_nonnegative_and_exact_shadow():
    angles = np.array([45, 60, 99, 101])
    rate = np.ones((4, 51, 3)) * 1e-10
    for i, angle in enumerate(angles):
        rate[i, ~spherical_shell_paths(angle).illuminated] = 0
    table = NIRForcingTable(angles, rate)
    for angle, expected in zip(angles, rate, strict=True):
        np.testing.assert_array_equal(table(angle), expected)
    assert np.all(table(93) >= 0)
    np.testing.assert_array_equal(table(135), np.zeros((51,3)))
    with pytest.raises(ValueError):
        table(30)


def test_log_column_rhs_matches_accepted_local_rhs_and_preserves_dynamic_uv():
    rhs = ReferenceColumnRHS(lambda sza: np.ones((51, 3))*1e-10)
    seed = bootstrap_seeds(rhs.background)[0]
    # At night, exactly zero forcing. Positive log trial states use no clipping.
    log_derivative = rhs(0, np.log(seed).ravel()).reshape(51,5)
    for i in (0, 30, 50):
        expected = local_rhs(0, seed[i], background=rhs.locals[i], forcing=FORCING_OFF)
        np.testing.assert_allclose(log_derivative[i]*seed[i], expected, rtol=2e-13)
    uv, _ = rhs.forcing(43200, seed)
    perturbed = seed.copy()
    perturbed[:,1] *= 10
    other, _ = rhs.forcing(43200, perturbed)
    assert np.any(other.JH < uv.JH)
    with pytest.raises(ValueError):
        rhs(0, np.ones(254))


def test_cycle_near_zero_criterion_uses_absolute_error():
    initial = np.ones((51,5))*1e8
    changed = initial.copy()
    initial[0, 0]=1e-20
    changed[0, 0]=1e-10
    stats = cycle_difference(initial, changed)
    assert stats['relative_max'][0] == 0
    assert stats['near_zero_absolute_max'][0] == pytest.approx(1e-10)


@pytest.mark.parametrize('method', ['BDF', 'Radau'])
def test_invalid_trial_is_rejected_without_projection(method):
    from scipy.sparse import eye

    from tfm_photochem.m5_temporal import _integrate_physical_segment

    rejected = []

    def rhs(t, y):
        if t > 0.05 and not rejected:
            rejected.append((t, y.copy()))
            raise FloatingPointError('synthetic invalid Newton trial')
        return -10*y

    result = _integrate_physical_segment(
        rhs, 0.0, 1.0, np.array([1.0]), method=method, rtol=1e-9,
        atol=1e-12, max_step=0.1, sparsity=eye(1, format='csc'))
    assert result.trial_rejections == 1
    np.testing.assert_allclose(result.sol([0.0, 0.5, 1.0])[0],
                               np.exp(-10*np.array([0.0, 0.5, 1.0])),
                               rtol=2e-6, atol=1e-10)


def test_grouped_log_jacobian_matches_independent_analytic_matrix():
    from scipy.sparse import csr_matrix

    from tfm_photochem.m5_temporal import _sparse_log_jacobian

    matrix = np.array([[2., 0., 3., 0.], [0., 5., 0., 7.],
                       [11., 0., 13., 0.], [0., 17., 0., 19.]])
    state = np.array([.2, .4, .6, .8])
    def rhs(t, y):
        return matrix @ np.exp(y)
    actual = _sparse_log_jacobian(rhs, csr_matrix(matrix != 0))(0., state).toarray()
    np.testing.assert_allclose(actual, matrix * np.exp(state), rtol=6e-5, atol=1e-10)


def test_domain_jacobian_uses_physical_side_at_a_boundary():
    from tfm_photochem.m5_temporal import _domain_difference

    trials = []

    def function(y):
        trials.append(y.copy())
        if y[0] > 1:
            raise FloatingPointError('outside synthetic physical domain')
        return y**2

    actual = _domain_difference(function, np.array([1.]), 0, 1e-5, np.array([1.]))
    np.testing.assert_allclose(actual, [2.], rtol=6e-6)
    assert trials[0][0] > 1
    assert trials[1][0] < 1


@pytest.mark.parametrize('case_index', [0, 1, 2])
def test_recorded_temporal_qssa_domain_exit_matches_original_scalar_chemistry(case_index):
    import json
    from pathlib import Path

    from tfm_photochem.historical_2020.local_closure import close_local_chemistry
    from tfm_photochem.historical_2020.local_types import LocalForcing, LocalState
    from tfm_photochem.historical_2020.qssa import NoPhysicalRootError
    from tfm_photochem.m5_temporal import qssa_domain_witness

    evidence = json.loads((Path(__file__).resolve().parents[1] /
                           'evidence/m5_temporal_evidence.json').read_text())
    case = evidence['independent_probes'][case_index]
    state = LocalState(*case['state'])
    background = load_baseline_background().local_background_at(case['z'])
    forcing = LocalForcing(**case['forcing'])
    with pytest.raises(NoPhysicalRootError):
        close_local_chemistry(state, background, forcing)
    actual = qssa_domain_witness(state, background, forcing)
    assert actual['sample_count'] == 257
    assert actual['residual_min'] > 0
    np.testing.assert_allclose(actual['residual_min'], case['QSSA']['residual_min'],
                               rtol=1e-8, atol=1e-14)


@pytest.mark.parametrize('linear_species', [(4,), tuple(range(5))])
def test_illuminated_linear_state_is_exact_coordinate_change_without_clipping(linear_species):
    from tfm_photochem.m5_temporal import _CycleCoordinates

    rhs = ReferenceColumnRHS(lambda sza: np.ones((51, 3))*1e-10)
    seed = bootstrap_seeds(rhs.background)[0]
    # Synthetic interior family state: the bootstrap need not have a physical
    # QSSA root when exposed directly to noon forcing without temporal spin-up.
    seed[:, 2] = 1e6
    seed[:, 3] = 1e12
    coordinates = _CycleCoordinates(rhs, np.ones(51, dtype=bool), linear_species=linear_species)
    encoded = coordinates.encode(seed)
    np.testing.assert_allclose(coordinates.decode(encoded), seed, rtol=2e-15)
    expected = rhs.physical_tendencies(43200, seed)
    actual = coordinates(43200, encoded).reshape(51, 5)
    actual *= np.where(coordinates.linear, coordinates.scale, seed)
    np.testing.assert_allclose(actual, expected, rtol=2e-13)
    invalid = encoded.copy()
    invalid[4] = -1e-15
    with pytest.raises(FloatingPointError, match='no clipping'):
        coordinates(43200, invalid)


def test_boundary_directional_witness_exits_qssa_beyond_floating_roundoff():
    import json
    from pathlib import Path

    from tfm_photochem.historical_2020.local_closure import close_local_chemistry
    from tfm_photochem.historical_2020.local_types import LocalForcing, LocalState
    from tfm_photochem.historical_2020.qssa import NoPhysicalRootError
    from tfm_photochem.m5_temporal import qssa_domain_witness

    evidence = json.loads((Path(__file__).resolve().parents[1] /
                           'evidence/m5_temporal_evidence.json').read_text())
    diagnostic = evidence['boundary_directional_diagnostic']
    assert diagnostic['original_boundary_QSSA']['original_guard'] == 'PASS'
    case = diagnostic['checks'][1]
    state = LocalState(*case['state_cm3'])
    background = load_baseline_background().local_background_at(100)
    forcing = LocalForcing(**case['forcing_s1'])
    with pytest.raises(NoPhysicalRootError):
        close_local_chemistry(state, background, forcing)
    assert qssa_domain_witness(state, background, forcing)['residual_min'] > 1e-6
    assert case['d_endpoint_residual_dt'] > .1


def test_reference_grazing_geometry_closes_and_preserves_accepted_ordinary_rays():
    from tfm_photochem.m5_temporal import _reference_shell_paths

    angles = 180-np.rad2deg(np.arcsin(6370/(6370+np.arange(50,101))))
    for angle in angles:
        for perturbation in (0., -1e-12, 1e-12):
            result = _reference_shell_paths(float(angle+perturbation))
            np.testing.assert_allclose(result.path_length_km.sum(axis=1),
                                       result.distance_to_top_km, rtol=2e-13, atol=2e-10)
            assert np.all(result.path_length_km >= 0)
    for angle in (0,45,60,85,90,95,99,135):
        expected = spherical_shell_paths(angle)
        actual = _reference_shell_paths(angle)
        np.testing.assert_array_equal(actual.path_length_km, expected.path_length_km)
        np.testing.assert_array_equal(actual.illuminated, expected.illuminated)


def test_newton_chemical_blocks_match_full_night_jacobian_and_do_not_change_rhs():
    rhs = ReferenceColumnRHS()
    log_state = np.log(bootstrap_seeds(rhs.background)[0]).ravel()
    before = rhs(0., log_state)
    jacobian = rhs.newton_jacobian(0., log_state).toarray()
    for column in (0, 4, 120, 124, 250, 254):
        perturbed = log_state.copy()
        perturbed[column] += 1e-4
        expected = (rhs(0., perturbed)-before)/1e-4
        np.testing.assert_allclose(jacobian[:,column], expected, rtol=2e-7, atol=1e-8)
    np.testing.assert_array_equal(rhs(0., log_state), before)


def test_batched_scan_matches_golden_all_reference_heights_and_qssa_errors():
    from tfm_photochem.historical_2020.local_closure import close_local_chemistry
    from tfm_photochem.historical_2020.local_types import LocalState
    from tfm_photochem.historical_2020.qssa import QSSAError
    from tfm_photochem.historical_2020.uv_radiation import (
        compute_uv_photolysis,
        local_forcing_from_uv,
    )

    bg = load_baseline_background()
    cached = CachedLocalClosure()
    for seed in bootstrap_seeds(bg):
        uv = compute_uv_photolysis(seed[:,0],seed[:,1],60,background=bg)
        for i,z in enumerate(bg.z_chem_km):
            state = LocalState(*seed[i])
            for forcing in (FORCING_OFF,local_forcing_from_uv(uv,i,gA=1e-9,gB=1e-10,gIRA=1e-10)):
                local = bg.local_background_at(z)
                try:
                    golden = close_local_chemistry(state,local,forcing)
                except QSSAError as error:
                    with pytest.raises(type(error)):
                        cached.close(state,local,forcing)
                else:
                    actual = cached.close(state,local,forcing)
                    for result_field in ('algebraic','tendencies','diagnostics'):
                        from dataclasses import asdict
                        np.testing.assert_allclose(
                            list(asdict(getattr(actual,result_field)).values()),
                            list(asdict(getattr(golden,result_field)).values()),
                            rtol=2e-13,atol=1e-15)
                    np.testing.assert_allclose(list(actual.fluxes.values()),list(golden.fluxes.values()),
                                               rtol=2e-13,atol=1e-15)
