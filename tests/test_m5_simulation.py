from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from tfm_photochem.m5_simulation import frozen_reference_nir, simulate


def test_polar_dark_continuum_explicit_zeros_and_solver_agreement():
    start=datetime(2020,12,21,12,tzinfo=timezone.utc)
    state=np.zeros((51,7))
    state[:,1]=np.linspace(1e6,1e8,51)
    def unused_nir(angle):
        raise AssertionError('polar night must not request illuminated NIR')
    results=[simulate(start,start+timedelta(hours=1),90,0,state,nir_provider=unused_nir,
                      method=method,rtol=2e-8,atol=1e-10,max_step_s=60) for method in ('BDF','Radau')]
    for result in results:
        np.testing.assert_allclose(result.state_cm3,np.broadcast_to(state,result.state_cm3.shape),rtol=2e-14,atol=0.)
        assert np.all(result.forcing_s1==0)
        assert np.all(result.algebraic_cm3==0)
        assert np.all(result.R_H_cm3==0)
        assert result.metadata['initialization']['policy'].startswith('explicit supplied')
        assert result.metadata['atmosphere_tracks_location'] is False
        assert result.metadata['geometry']['origin_utc'].endswith('+00:00')
    np.testing.assert_array_equal(state[:,0],0.)


def test_api_rejects_missing_or_nonphysical_initialization_and_unsupported_atmosphere():
    start=datetime(2020,3,20,12,tzinfo=timezone.utc)
    base=dict(start_datetime=start,end_datetime=start+timedelta(seconds=10),latitude=45,
              longitude=0,initial_state=np.ones((51,7)),nir_provider=lambda s:np.zeros((51,3)))
    for change in ({'initial_state':None},{'initial_state':np.full((51,7),-1.)},
                   {'atmosphere':'dynamic'},{'end_datetime':start},
                   {'start_datetime':start.replace(tzinfo=None)},{'method':'RK45'},
                   {'output_times_s':[0,0,10]}):
        with pytest.raises(ValueError):
            simulate(**(base|change))
    with pytest.raises(ValueError):
        simulate(start,start+timedelta(seconds=10),45,0,nir_provider=base['nir_provider'])


def test_bundled_frozen_nir_full_zenith_coverage_and_shadow():
    table=frozen_reference_nir()
    assert table.sza_deg[0]==0
    assert table.metadata['model']=='A0/B/IRA'
    assert table.metadata['audit']['relative_max']<=.005
    for angle in (0.,20.,45.,60.,90.,99.,180.):
        value=table(angle)
        assert value.shape==(51,3) and np.all(np.isfinite(value)) and np.all(value>=0)
    np.testing.assert_array_equal(table(180.),0.)


def test_polar_day_real_geometry_uses_default_provider_and_returns_all_fields():
    from pathlib import Path
    with np.load(Path(__file__).resolve().parents[1]/'evidence/m5_reference_cycle.npz') as g:
        state=g['state_cm3'][0].copy()
    start=datetime(2020,6,21,12,tzinfo=timezone.utc)
    result=simulate(start,start+timedelta(seconds=10),90,0,state,output_step_s=5,
                    rtol=2e-8,atol=1e-10,max_step_s=1)
    assert result.state_cm3.shape==(3,51,7)
    assert result.algebraic_cm3.shape==(3,51,3)
    assert result.forcing_s1.shape==(3,51,11)
    assert np.all(result.sza_deg<90)
    assert result.metadata['radiation']['NIR']['model']=='A0/B/IRA'
    np.testing.assert_array_equal(result.R_H_cm3,result.state_cm3[:,:,3]+result.state_cm3[:,:,4])
