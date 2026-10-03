"""Finite-horizon noon policy: frozen native inputs, fast roots and free evolution."""
from dataclasses import asdict
from pathlib import Path

import numpy as np

from tfm_photochem.historical_2020.background import (
    _read_numeric_csv,
    load_baseline_background,
)
from tfm_photochem.historical_2020.background_generation import RAD_FILENAME
from tfm_photochem.historical_2020.local_types import LocalForcing
from tfm_photochem.historical_2020.reactions import REACTION_BY_ID
from tfm_photochem.m5_temporal import (
    DynamicPeroxideState,
    ReferenceEquinoxSolarCycle,
    close_dynamic_peroxide_chemistry,
    dynamic_peroxide_rhs,
    reference_noon_atom_profiles,
)


def test_native_atom_policy_has_explicit_missing_zeros_and_separable_bound():
    background=load_baseline_background()
    raw=_read_numeric_csv(RAD_FILENAME)
    baseline,finite=reference_noon_atom_profiles()
    assert np.array_equal(~finite[:,0],~finite[:,1])
    assert np.flatnonzero(~finite[:,0]).tolist()==list(range(23))
    for k,name in enumerate(('msis_O_native_cm3','msis_H_native_cm3')):
        np.testing.assert_array_equal(baseline[finite[:,k],k],raw[name][50:101][finite[:,k]])
    np.testing.assert_array_equal(baseline[~finite],0.)
    for factor in (.5,2.):
        variant,_=reference_noon_atom_profiles(atom_factor=factor)
        np.testing.assert_array_equal(variant,factor*baseline)
    bounded,_=reference_noon_atom_profiles(missing_fraction=1e-8)
    np.testing.assert_array_equal(bounded[finite],baseline[finite])
    np.testing.assert_array_equal(bounded[:23],np.repeat((background.chemical.M_cm3[:23]*1e-8)[:,None],2,axis=1))


def test_finite_horizon_noon_reference_and_dawn_field_mapping():
    path=Path(__file__).resolve().parents[1]/'evidence/m5_reference_cycle.npz'
    with np.load(path) as data:
        state=data['state_cm3']
        times=data['time_s']
        forcing=data['forcing_s1']
        names=data['forcing_names'].tolist()
        species=data['species'].tolist()
        assert species==['O','O3','H','OH','HO2','H2O2','Delta']
        assert len(names)==11 and {'gA','gB','gIRA'}.issubset(names)
        assert data['algebraic_species'].tolist()==['O1D','B0','B1']
        assert times[0]==43200 and times[-1]==118800
        assert np.all(np.diff(times)>0) and np.all(np.isfinite(state)) and np.all(state>=0)
        np.testing.assert_array_equal(data['R_H_cm3'],state[:,:,3]+state[:,:,4])
        np.testing.assert_allclose(data['SZA_deg'],ReferenceEquinoxSolarCycle().sza(times),rtol=1e-14)
        np.testing.assert_allclose(data['SZA_deg'][data['dawn_mask']][[0,-1]],[99.,60.],atol=1e-12)
    atoms,_=reference_noon_atom_profiles()
    np.testing.assert_allclose(state[0][:,[0,2]],atoms,rtol=1e-14,atol=0)
    np.testing.assert_allclose(state[0,:,1],load_baseline_background().radiative.O3_socrates_reference_cm3[50:101],rtol=1e-14)
    assert np.all(state[1,:23,0]>0) and np.all(state[1,:23,2]>0)
    assert np.any(state[1,:,3:]!=state[0,:,3:])
    background=load_baseline_background()
    for level in range(51):
        f=LocalForcing(**dict(zip(names,forcing[0,level],strict=True)))
        b=background.local_background_at(level+50)
        y=state[0,level]
        c=close_dynamic_peroxide_chemistry(DynamicPeroxideState(*y),b,f)
        derivative=dynamic_peroxide_rhs(times[0],y,background=b,forcing=f)
        ho2_scale=0.
        for event,reaction in REACTION_BY_ID.items():
            coefficient=dict(reaction.products).get('HO2',0)-dict(reaction.reactants).get('HO2',0)
            ho2_scale+=abs(coefficient)*c.fluxes.get(event,0.)
        d=c.diagnostics
        scales=[d.P_OH+d.L_OH,ho2_scale,d.P_H2O2+d.L_H2O2*y[5],d.P_Delta+d.L_Delta*y[6]]
        assert max(abs(derivative[3:])/np.array(scales))<1e-9
        assert min(d.L_O1D,d.L_B0,d.L_B1)>0
        assert all(value>=0 for value in asdict(c.algebraic).values())