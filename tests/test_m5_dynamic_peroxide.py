"""Seven-species temporal model: unchanged fluxes, physical boundaries, golden reference."""
from dataclasses import asdict

import numpy as np
import pytest

from tfm_photochem.m5_temporal import (
    DynamicPeroxideColumnRHS,
    DynamicPeroxideState,
    LocalState,
    bootstrap_seeds,
    close_dynamic_peroxide_chemistry,
    close_local_chemistry,
    dynamic_peroxide_bootstrap_seeds,
    dynamic_peroxide_rhs,
    load_baseline_background,
)

from .test_historical_2020_local_closure import BASE_FORCING, FORCING_OFF


@pytest.mark.parametrize("z", range(50,101))
def test_seven_boundaries_and_remaining_denominators(z):
    b=load_baseline_background().local_background_at(z)
    rng=np.random.default_rng(517+z)
    for forcing in (BASE_FORCING, FORCING_OFF):
        for _ in range(8):
            y=10**rng.uniform(-8,np.log10(b.M)-3,7)
            for index in range(7):
                state=y.copy()
                state[index]=0.
                c=close_dynamic_peroxide_chemistry(DynamicPeroxideState(*state),b,forcing)
                dy=dynamic_peroxide_rhs(0.,state,background=b,forcing=forcing)
                scale=max(sum(abs(v) for v in c.fluxes.values()),1e-30)
                assert dy[index]>=-32*np.finfo(float).eps*scale
                assert min(c.diagnostics.L_O1D,c.diagnostics.L_B0,c.diagnostics.L_B1)>0
                expected=c.fluxes["HO2_HO2"]-c.fluxes["H2O2_PHOTOLYSIS"]-c.fluxes["OH_H2O2"]
                assert dy[5]==expected
                assert abs(dy[3]+dy[4]-c.tendencies.R_H)<=8*np.finfo(float).eps*scale
                assert c.algebraic.H2O2==state[5]
                assert np.all(np.isfinite(list(asdict(c.algebraic).values())))

@pytest.mark.parametrize("family", range(3))
def test_seven_golden_fluxes_and_tendencies(family):
    bg=load_baseline_background()
    for i,y in enumerate(bootstrap_seeds(bg)[family]):
        b=bg.local_background_at(50+i)
        old=close_local_chemistry(LocalState(*y),b,FORCING_OFF)
        a=old.algebraic
        state=DynamicPeroxideState(*y[:3],a.OH,a.HO2,a.H2O2,y[4])
        new=close_dynamic_peroxide_chemistry(state,b,FORCING_OFF)
        assert asdict(a)==asdict(new.algebraic)
        assert old.fluxes==new.fluxes
        assert old.tendencies==new.tendencies
        d=dynamic_peroxide_rhs(0.,list(asdict(state).values()),background=b,forcing=FORCING_OFF)
        scale=max(sum(abs(v) for v in old.fluxes.values()),1e-30)
        assert abs(d[3])<1e-8*scale
        assert abs(d[5])<1e-14*scale
        # Original family coordinate evolves even when OH is in QSSA.
        assert abs(d[4]-old.tendencies.R_H)<1e-8*scale

@pytest.mark.parametrize("z", range(50,101))
def test_seven_exact_dark_continuum(z):
    b=load_baseline_background().local_background_at(z)
    y=np.array([0.,12345.,0.,0.,0.,0.,0.])
    np.testing.assert_array_equal(dynamic_peroxide_rhs(0.,y,background=b,forcing=FORCING_OFF),np.zeros(7))

@pytest.mark.parametrize("index", range(7))
def test_no_clipping(index):
    y=np.ones(7)
    y[index]=-1.
    with pytest.raises(ValueError):
        DynamicPeroxideState(*y)

def test_357_coordinates_and_positive_seed_families():
    rhs=DynamicPeroxideColumnRHS()
    for seed in dynamic_peroxide_bootstrap_seeds(rhs):
        assert seed.shape==(51,7) and np.all(seed>0)
        value=rhs(0.,np.log(seed).ravel())
        assert value.shape==(357,) and np.all(np.isfinite(value))


def test_peroxide_reaction_stoichiometry_independent():
    from tfm_photochem.historical_2020.reactions import REACTION_BY_ID
    coefficients = {}
    for name,reaction in REACTION_BY_ID.items():
        products=dict(reaction.products)
        reactants=dict(reaction.reactants)
        value=products.get("H2O2",0)-reactants.get("H2O2",0)
        if value:
            coefficients[name]=value
    assert coefficients=={"HO2_HO2":1,"H2O2_PHOTOLYSIS":-1,"OH_H2O2":-1}
    reaction=REACTION_BY_ID["OH_H2O2"]
    products,reactants=dict(reaction.products),dict(reaction.reactants)
    assert products.get("OH",0)-reactants.get("OH",0)==-1
    assert products.get("HO2",0)-reactants.get("HO2",0)==1


def test_random_full_trace_matches_lean_velocity():
    rng=np.random.default_rng(732)
    b=load_baseline_background().local_background_at(80)
    for _ in range(100):
        y=10**rng.uniform(-6,9,7)
        c=close_dynamic_peroxide_chemistry(DynamicPeroxideState(*y),b,BASE_FORCING)
        traced=dynamic_peroxide_rhs(0.,y,background=b,forcing=BASE_FORCING,
                                    chemistry=lambda s,b,f:close_dynamic_peroxide_chemistry(s,b,f))
        lean=dynamic_peroxide_rhs(0.,y,background=b,forcing=BASE_FORCING)
        np.testing.assert_array_equal(traced,lean)
        expected=np.array([c.tendencies.O,c.tendencies.O3,c.tendencies.H,c.tendencies.Delta])
        np.testing.assert_array_equal(lean[[0,1,2,6]],expected)


def test_negative_stoichiometry_requires_consumed_dynamic_reactant():
    """Analytic mass-action boundary check, independent of sampled flux values."""
    from tfm_photochem.historical_2020.reactions import REACTION_BY_ID
    species=("O","O3","H","OH","HO2","H2O2","Delta")
    for reaction in REACTION_BY_ID.values():
        reactants,products=dict(reaction.reactants),dict(reaction.products)
        for name in species:
            if products.get(name,0)-reactants.get(name,0)<0:
                assert reactants.get(name,0)>0


def test_illuminated_golden_reference():
    from .test_historical_2020_local_closure import BASE_BACKGROUND, BASE_STATE
    c=close_local_chemistry(BASE_STATE,BASE_BACKGROUND,BASE_FORCING)
    a=c.algebraic
    state=DynamicPeroxideState(BASE_STATE.O,BASE_STATE.O3,BASE_STATE.H,a.OH,a.HO2,a.H2O2,BASE_STATE.Delta)
    new=close_dynamic_peroxide_chemistry(state,BASE_BACKGROUND,BASE_FORCING)
    assert new.algebraic==c.algebraic
    assert new.fluxes==c.fluxes
    assert new.tendencies==c.tendencies


def test_vector_column_is_identical_to_golden_scalar_kernel():
    from dataclasses import replace
    rhs=DynamicPeroxideColumnRHS()
    rng=np.random.default_rng(875)
    for _ in range(12):
        column=10**rng.uniform(-8,11,(51,7))
        forcing=[replace(BASE_FORCING, J_H2O2=10**rng.uniform(-10,-3)) for _ in range(51)]
        batch=rhs.column_kernel(column,forcing)
        scalar=np.array([dynamic_peroxide_rhs(0.,state,background=b,forcing=f,chemistry=rhs.chemistry)
                         for state,b,f in zip(column,rhs.locals,forcing,strict=True)])
        np.testing.assert_array_equal(batch,scalar)
