"""Independent stoichiometry, physical boundaries and golden M3 comparisons."""

from dataclasses import asdict

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from tfm_photochem.historical_2020.background import load_baseline_background
from tfm_photochem.historical_2020.local_closure import close_local_chemistry
from tfm_photochem.historical_2020.local_types import LocalState
from tfm_photochem.historical_2020.qssa import SingularQSSAError
from tfm_photochem.historical_2020.reactions import REACTION_BY_ID
from tfm_photochem.historical_2020.stoichiometry import TENDENCY_COEFFICIENTS
from tfm_photochem.m5_temporal import (
    OH_EVENT_COEFFICIENTS,
    TemporalColumnRHS,
    TemporalState,
    _CycleCoordinates,
    _positive_anderson_candidate,
    bootstrap_seeds,
    close_temporal_chemistry,
    temporal_bootstrap_seeds,
    temporal_rhs,
)

from .test_historical_2020_local_closure import (
    BASE_BACKGROUND,
    BASE_FORCING,
    FORCING_OFF,
)


@pytest.mark.parametrize("event", tuple(TENDENCY_COEFFICIENTS))
def test_reaction_by_reaction_oh_ho2_identity(event):
    reaction = REACTION_BY_ID.get(event)
    def net(species):
        if reaction is None:
            return 0.
        return (sum(n for s, n in reaction.products if s == species)
                - sum(n for s, n in reaction.reactants if s == species))
    oh = OH_EVENT_COEFFICIENTS.get(event, 0.)
    assert oh == net("OH")
    assert TENDENCY_COEFFICIENTS[event]["R_H"] - oh == net("HO2")


def test_random_state_preserves_all_accepted_chemistry_and_family_budget():
    random = np.random.default_rng(20261002)
    for values in 10.**random.uniform(0, 12, (100, 6)):
        state = TemporalState(*values)
        closure = close_temporal_chemistry(state, BASE_BACKGROUND, BASE_FORCING)
        derivative = temporal_rhs(0, values, background=BASE_BACKGROUND, forcing=BASE_FORCING)
        audited = temporal_rhs(0,values,background=BASE_BACKGROUND,forcing=BASE_FORCING,
                               chemistry=lambda *args: close_temporal_chemistry(*args))
        np.testing.assert_array_equal(derivative,audited)
        flux = closure.fluxes
        scale = max(sum(abs(v) for v in flux.values()), 1.)
        independent_oh = sum(flux[k]*v for k, v in OH_EVENT_COEFFICIENTS.items())
        independent_ho2 = sum(flux[k]*(v["R_H"]-OH_EVENT_COEFFICIENTS.get(k, 0.))
                              for k, v in TENDENCY_COEFFICIENTS.items())
        assert abs(derivative[3]-independent_oh) <= 20*np.finfo(float).eps*scale
        assert abs(derivative[4]-independent_ho2) <= 20*np.finfo(float).eps*scale
        assert abs(derivative[3]+derivative[4]-closure.tendencies.R_H) <= 2*np.finfo(float).eps*scale
        np.testing.assert_array_equal(derivative[[0,1,2,5]],
                                      [closure.tendencies.O, closure.tendencies.O3,
                                       closure.tendencies.H, closure.tendencies.Delta])
        assert state.R_H == state.OH+state.HO2


@pytest.mark.parametrize("boundary", [3, 4])
def test_positivity_boundaries_in_finite_closure_domain(boundary):
    random = np.random.default_rng(45)
    for values in 10.**random.uniform(0, 12, (100, 6)):
        values[boundary] = 0.
        closure = close_temporal_chemistry(TemporalState(*values), BASE_BACKGROUND, BASE_FORCING)
        derivative = temporal_rhs(0, values, background=BASE_BACKGROUND, forcing=BASE_FORCING)
        scale = max(sum(abs(v) for v in closure.fluxes.values()), 1.)
        assert derivative[boundary] >= -20*np.finfo(float).eps*scale
        if boundary == 3:
            assert closure.diagnostics.L_OH == 0.
            assert derivative[3] == closure.diagnostics.P_OH >= 0.
        else:
            expected = closure.fluxes["H_O2_ASSOCIATION"]+closure.fluxes["OH_O3"]
            assert abs(derivative[4]-expected) <= 20*np.finfo(float).eps*scale


def test_dark_peroxide_singularity_is_not_silently_regularized():
    with pytest.raises(SingularQSSAError):
        close_temporal_chemistry(TemporalState(1., 1., 1., 0., 1., 1.),
                                BASE_BACKGROUND, FORCING_OFF)


@pytest.mark.parametrize("altitude", range(50, 101))
def test_golden_root_equivalence_and_dark_continuum(altitude):
    background = load_baseline_background()
    local = background.local_background_at(altitude)
    for seed in bootstrap_seeds(background):
        old_state = LocalState(*seed[altitude-50])
        old = close_local_chemistry(old_state, local, FORCING_OFF)
        state = TemporalState(old_state.O, old_state.O3, old_state.H,
                              old.algebraic.OH, old.algebraic.HO2, old_state.Delta)
        new = close_temporal_chemistry(state, local, FORCING_OFF)
        assert asdict(new.algebraic) == asdict(old.algebraic)
        assert asdict(new.tendencies) == asdict(old.tendencies)
        assert new.fluxes == old.fluxes
    for ozone in (1., 1e8, 1e12):
        derivative = temporal_rhs(0, [0,ozone,0,0,0,0], background=local, forcing=FORCING_OFF)
        np.testing.assert_array_equal(derivative, np.zeros(6))


def test_negative_concentrations_are_rejected_without_clipping():
    for index in range(6):
        values = np.ones(6)
        values[index] = -1e-30
        with pytest.raises(ValueError):
            temporal_rhs(0, values, background=BASE_BACKGROUND, forcing=BASE_FORCING)


def test_new_dark_continuum_survives_24h_bdf_exactly():
    initial = np.array([0.,1e8,0.,0.,0.,0.])
    # Constant exact root: an identity Newton preconditioner avoids the undefined
    # off-manifold OH=0, HO2>0 dark peroxide direction of a numerical Jacobian.
    result = solve_ivp(lambda t,y: temporal_rhs(t,y,background=BASE_BACKGROUND,forcing=FORCING_OFF),
                       (0.,86400.),initial,method="BDF",rtol=1e-9,atol=1e-12,jac=np.eye(6))
    assert result.success
    np.testing.assert_array_equal(result.y,np.broadcast_to(initial[:,None],result.y.shape))


def test_306_coordinates_and_positive_trial_rejection():
    rhs = TemporalColumnRHS()
    seed = temporal_bootstrap_seeds(rhs)[0]
    coordinates = _CycleCoordinates(rhs,np.zeros(51,dtype=bool),linear_species=range(6))
    encoded = coordinates.encode(seed)
    assert encoded.shape == (306,)
    np.testing.assert_allclose(coordinates.decode(encoded),seed,rtol=2e-15)
    np.testing.assert_allclose(coordinates(0.,encoded),rhs(0.,encoded),rtol=1e-14)
    assert rhs.newton_jacobian(0.,encoded).shape == (306,306)
    linear = _CycleCoordinates(rhs,np.ones(51,dtype=bool),linear_species=range(6))
    trial = linear.encode(seed)
    trial[3] = -1e-20
    with pytest.raises(FloatingPointError):
        linear.decode(trial)


def test_positive_secant_iteration_finds_known_contracting_day_map():
    target = np.array([[4.,7.]])
    state = np.array([[1.,2.]])
    history = []
    # A known log-linear contraction with a unique positive attracting root.
    for _ in range(5):
        mapped = .9*np.log(state)+.1*np.log(target)
        history.append((np.log(state),mapped))
        state = _positive_anderson_candidate(history,upper_cm3=np.array([[100.]]))
        assert np.all(state > 0)
    np.testing.assert_allclose(state,target,rtol=1e-12)


def test_block_secants_handle_independent_fast_and_slow_contracting_levels():
    target = np.array([[4.,7.],[3.,5.]])
    state = np.ones((2,2))
    contraction = np.array([[.999],[.1]])
    history = []
    for _ in range(6):
        mapped = contraction*np.log(state)+(1-contraction)*np.log(target)
        history.append((np.log(state),mapped))
        state = _positive_anderson_candidate(history)
    np.testing.assert_allclose(state,target,rtol=1e-11)
