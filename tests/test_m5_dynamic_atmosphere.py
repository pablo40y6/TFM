"""Runtime backgrounds and API contracts, independent of costly NIR generation."""
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from tfm_photochem.dynamic_atmosphere import (
    ActivityDrivers,
    DynamicMSISAtmosphere,
    QuietReferenceActivity,
    background_from_msis,
)
from tfm_photochem.dynamic_radiation import DynamicNIRForcing, snapshot_transfer
from tfm_photochem.m4d_reconstruction.cia import HistoricalCIA
from tfm_photochem.m5_dynamic import DynamicAtmosphereColumnRHS, previous_solar_noon
from tfm_photochem.m5_simulation import simulate
from tfm_photochem.m5_temporal import (
    DynamicPeroxideState,
    NIRForcingTable,
    close_dynamic_peroxide_chemistry,
    dynamic_peroxide_rhs,
)
from tfm_photochem.solar_geometry import DatetimeSolarGeometry, solar_position

from .test_historical_2020_local_closure import BASE_FORCING
from .test_m4d_reconstruction import synthetic_lines, synthetic_sources

START=datetime(2020,3,20,12,tzinfo=timezone.utc)


def synthetic_raw(count=2):
    raw=np.ones((count,151,11))
    raw[:,:,0]=1e-5
    raw[:,:,1:9]=1e20
    raw[:,:73,3]=np.nan
    raw[:,:73,5]=np.nan
    raw[:,:,8]=1e28  # anomalous oxygen is excluded from ordinary M
    raw[:,:,10]=250.
    return raw


def test_units_fixed_vmrs_external_oxygen_and_anomalous_exclusion():
    bg=background_from_msis(synthetic_raw()[0],{})
    assert bg.chemical.M_cm3[0]==5e14
    assert bg.chemical.M_cm3[-1]==7e14
    assert np.isnan(bg.radiative.msis_O_native_cm3[50])
    assert bg.radiative.msis_O_native_cm3[80]==1e14
    np.testing.assert_array_equal(bg.chemical.O2_cm3,.21*bg.chemical.M_cm3)
    np.testing.assert_array_equal(bg.chemical.N2_cm3,.78*bg.chemical.M_cm3)
    np.testing.assert_array_equal(bg.chemical.CO2_cm3,405e-6*bg.chemical.M_cm3)
    np.testing.assert_array_equal(bg.radiative.O3_socrates_reference_cm3,
                                 bg.radiative.O3_socrates_reference_vmr*bg.radiative.M_cm3)


def test_explicit_activity_interpolation_validation_and_immutability():
    values=[100.,200.]
    drivers=ActivityDrivers((START,START+timedelta(hours=2)),values,[150.,170.],[0.,8.])
    values[0]=999.
    f,fa,ap=drivers.at([START+timedelta(hours=1)])
    assert (f[0],fa[0],ap[0])==(150.,160.,4.)
    with pytest.raises(ValueError):
        drivers.at([START-timedelta(seconds=1)])
    for args in ((0,150,4),(150,np.nan,4),(150,150,-1)):
        with pytest.raises(ValueError):
            QuietReferenceActivity(*args)


def test_precomputed_background_linear_interpolation_and_no_runtime_msis(monkeypatch):
    raw=synthetic_raw()
    raw[1,:,10]=350.
    raw[1,:,1:8]*=2
    p=DynamicMSISAtmosphere(START,START+timedelta(hours=1),45,0,raw=raw)
    monkeypatch.setattr('tfm_photochem.dynamic_atmosphere.run_dynamic_msis',
                        lambda *a,**k:pytest.fail('MSIS in runtime query'))
    assert p.at(1800).chemical.T_K[0]==300.
    assert p.at(1800).chemical.M_cm3[0]==7.5e14
    assert p.msis_calls==0
    assert p.at(1800) is p.at(1800)
    with pytest.raises(ValueError):
        p.at(3601)
    changed=raw.copy()
    changed[1,50,3]=0.
    with pytest.raises(ValueError,match='availability'):
        DynamicMSISAtmosphere(START,START+timedelta(hours=1),45,0,raw=changed)


@pytest.mark.parametrize('longitude',[-180.,-75.,0.,120.,180.])
def test_previous_apparent_noon_utc_and_longitude(longitude):
    noon=previous_solar_noon(START,longitude)
    assert 0<=(START-noon).total_seconds()<86420
    minutes=noon.hour*60+noon.minute+noon.second/60+noon.microsecond/6e7
    angle=(minutes+solar_position(noon,45,longitude)['equation_of_time_min']+4*longitude)/4-180
    assert abs((angle+180)%360-180)<1e-6
    assert noon.tzinfo==timezone.utc


def test_dynamic_kernel_matches_golden_scalar_after_temperature_density_change():
    raw=synthetic_raw()
    raw[1,:,10]=350.
    raw[1,:,1:8]*=1.5
    p=DynamicMSISAtmosphere(START,START+timedelta(hours=1),45,0,raw=raw)
    rhs=DynamicAtmosphereColumnRHS(p,lambda t,s:np.zeros((51,3)),
                                  DatetimeSolarGeometry(START,45,0))
    rng=np.random.default_rng(5103)
    state=10**rng.uniform(2,7,(51,7))
    for time in (0.,1800.,3600.):
        rhs._update_background(time)
        actual=rhs.column_kernel(state,(BASE_FORCING,)*51)
        expected=np.array([dynamic_peroxide_rhs(time,y,background=b,forcing=BASE_FORCING)
                           for y,b in zip(state,rhs.locals,strict=True)])
        np.testing.assert_allclose(actual,expected,rtol=3e-14,atol=1e-10)


def test_api_initialization_exclusivity_and_prevalidation_before_msis(monkeypatch):
    monkeypatch.setattr('tfm_photochem.dynamic_atmosphere.run_dynamic_msis',
                        lambda *a,**k:pytest.fail('invalid API request called MSIS'))
    args=(START,START+timedelta(seconds=1),45,0)
    for kw in ({},{'initial_state':np.ones((51,7)),'initialization':'reference_noon'},
               {'initialization':'climatology'},
               {'initial_state':np.full((51,7),-1.),'atmosphere':'dynamic_msis'}):
        with pytest.raises(ValueError):
            simulate(*args,**kw)


def test_explicit_state_skips_noon_bootstrap_in_dynamic_dark_run(monkeypatch):
    start=datetime(2020,12,21,12,tzinfo=timezone.utc)
    end=start+timedelta(seconds=10)
    p=DynamicMSISAtmosphere(start,end,90,0,raw=synthetic_raw())
    monkeypatch.setattr('tfm_photochem.m5_dynamic.previous_solar_noon',
                        lambda *a:pytest.fail('explicit state invoked bootstrap'))
    state=np.zeros((51,7))
    state[:,1]=12345.
    result=simulate(start,end,90,0,state,atmosphere='dynamic_msis',atmosphere_provider=p,
                    dynamic_nir=lambda t,s:np.zeros((51,3)),output_step_s=5.)
    np.testing.assert_allclose(result.state_cm3,np.broadcast_to(state,result.state_cm3.shape),rtol=1e-14,atol=0.)
    assert result.metadata['dynamic_atmosphere']
    assert result.background_fields['background_T_K'].shape==(3,51)
    assert result.background_fields['radiative_MSIS_O_native_cm3'].shape==(3,151)


@pytest.mark.parametrize('date,latitude,longitude',[
    (START,45,0),(START.replace(month=6,day=21),45,0),
    (START.replace(month=12,day=21),-45,0),(START,45,-75),
    (START.replace(month=6,day=21),70,0)])
def test_actual_msis_cases_explicit_activity_never_downloads(monkeypatch,date,latitude,longitude):
    pytest.importorskip('pymsis')
    monkeypatch.setattr('pymsis.msis.get_f107_ap',lambda *a,**k:pytest.fail('space weather lookup'))
    p=DynamicMSISAtmosphere(date,date+timedelta(hours=2),latitude,longitude)
    b=p.at(3600)
    assert p.msis_calls==1
    assert np.all(b.chemical.T_K>0) and np.all(b.chemical.M_cm3>0)
    np.testing.assert_array_equal(b.chemical.O2_cm3,.21*b.chemical.M_cm3)
    rng=np.random.default_rng(5104)
    for z in range(50,101):
        local=b.local_background_at(z)
        state=10**rng.uniform(-4,8,7)
        for index in range(7):
            edge=state.copy()
            edge[index]=0.
            closure=close_dynamic_peroxide_chemistry(DynamicPeroxideState(*edge),local,BASE_FORCING)
            d=closure.diagnostics
            assert min(d.L_O1D,d.L_B0,d.L_B1)>0
            velocity=dynamic_peroxide_rhs(0.,edge,background=local,forcing=BASE_FORCING)
            scale=max(sum(abs(v) for v in closure.fluxes.values()),1e-30)
            assert velocity[index]>=-32*np.finfo(float).eps*scale
    if date==START and latitude==45 and longitude==0:
        from tfm_photochem.historical_2020.background import load_baseline_background
        golden=load_baseline_background()
        np.testing.assert_allclose(p.at(0).radiative.M_cm3,golden.radiative.M_cm3,rtol=2e-6)
        np.testing.assert_allclose(p.at(0).radiative.T_K,golden.radiative.T_K,rtol=1e-6)


def test_automatic_bootstrap_continuity_and_honest_metadata(monkeypatch):
    start=datetime(2020,12,21,13,tzinfo=timezone.utc)
    end=start+timedelta(seconds=10)
    state=np.zeros((51,7))
    state[:,1]=12345.
    def initializer(rhs):
        assert float(rhs.cycle.sza(0))>100  # test plumbing, not a dark equilibrium claim
        return state.copy(),dict(policy='test reference root')
    monkeypatch.setattr('tfm_photochem.m5_dynamic.dynamic_reference_noon_initialization',initializer)
    result=simulate(start,end,90,0,initialization='reference_noon',output_step_s=5.)
    record=result.metadata['initialization']
    assert record['bootstrap_duration_s']>3000
    assert record['climatologically_validated'] is False
    assert 'bootstrap_solver' in record
    np.testing.assert_allclose(result.state_cm3,np.broadcast_to(state,result.state_cm3.shape),rtol=1e-14,atol=0.)


def test_numeric_nir_persistence_rejects_wrong_atmosphere(tmp_path):
    p=DynamicMSISAtmosphere(START,START+timedelta(hours=1),45,0,raw=synthetic_raw())
    geometry=DatetimeSolarGeometry(START,45,0)
    instance=DynamicNIRForcing.__new__(DynamicNIRForcing)
    instance.atmosphere,instance.geometry=p,geometry
    instance.tables=[NIRForcingTable([0.,180.],np.zeros((2,51,3))) for _ in p.times]
    instance.audits=[dict(relative_max=0.,near_zero_absolute_max_s1=0.) for _ in p.times]
    path=tmp_path/'derived.npz'
    instance.save(path)
    loaded=DynamicNIRForcing.load(path,p,geometry)
    np.testing.assert_array_equal(loaded(1800.,60.),0.)
    altered=synthetic_raw()
    altered[:,:,10]=260.
    other=DynamicMSISAtmosphere(START,START+timedelta(hours=1),45,0,raw=altered)
    with pytest.raises(ValueError,match='identity'):
        DynamicNIRForcing.load(path,other,geometry)


def test_radiation_subset_reuses_exact_msis_and_rejects_mismatch():
    raw=np.repeat(synthetic_raw()[:1],5,axis=0)
    raw[:,:,10]+=np.arange(5)[:,None]
    p=DynamicMSISAtmosphere(START,START+timedelta(hours=1),45,0,step_s=900.,raw=raw)
    coarse=p.sampled(1800.)
    np.testing.assert_array_equal(coarse.raw,p.raw[::2])
    assert coarse.msis_calls==0
    p.validate_radiation_background(coarse)
    with pytest.raises(ValueError,match='subset'):
        p.sampled(1000.)
    altered=coarse.raw.copy()
    altered[:,:,10]+=1.
    other=DynamicMSISAtmosphere(START,p.end,45,0,step_s=1800.,raw=altered)
    with pytest.raises(ValueError,match='identical'):
        p.validate_radiation_background(other)


@pytest.mark.parametrize('with_cia',[False,True])
def test_nominal_transfer_specialization_preserves_every_retained_output(with_cia):
    bg=background_from_msis(synthetic_raw()[0],{})
    cia=HistoricalCIA({t:np.array([[7780.,1e-45*t],[7850.,1e-45*t]]) for t in (253,273,296)}) if with_cia else None
    controls=dict(core_order=8,wing_order=4,support=.12,far_order=8,near_cm1=.25,cia=cia)
    cases=[(50.,60.),(75.,95.),(100.,99.),(50.,180.)]
    original=snapshot_transfer(bg)(synthetic_lines(),synthetic_sources(),cases,**controls)
    nominal=snapshot_transfer(bg,nominal_only=True)(synthetic_lines(),synthetic_sources(),cases,**controls)
    assert set(nominal)=={'monomer','unattenuated','illuminated'}|({'cia_nominal'} if with_cia else set())
    for name,value in nominal.items():
        np.testing.assert_array_equal(value,original[name])
