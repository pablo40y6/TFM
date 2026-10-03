"""M5C orchestration and background-aware RHS, using golden chemistry code."""
from __future__ import annotations

from dataclasses import fields
from datetime import timedelta
from inspect import signature
from types import FunctionType, SimpleNamespace

import numpy as np
from scipy.optimize import brentq

from .historical_2020 import kinetics
from .historical_2020.local_types import LocalBackground, LocalForcing
from .m5_temporal import (
    DynamicPeroxideColumnRHS,
    _reference_uv,
    reference_noon_initialization,
)
from .solar_geometry import solar_position, utc_datetime


def previous_solar_noon(start_datetime,longitude):
    """Latest apparent solar noon (hour angle zero), including polar geometry."""
    start=utc_datetime(start_datetime)
    midnight=start.replace(hour=0,minute=0,second=0,microsecond=0)
    candidates=[]
    for day in range(-2,2):
        origin=midnight+timedelta(days=day)
        def hour_angle(minutes):
            instant=origin+timedelta(minutes=float(minutes))
            return minutes+solar_position(instant,0.,longitude)['equation_of_time_min']+4*longitude-720
        minutes=brentq(hour_angle,-60.,1500.,xtol=1e-8)
        noon=origin+timedelta(minutes=float(minutes))
        if noon<=start:
            candidates.append(noon)
    return max(candidates)


class DynamicAtmosphereColumnRHS(DynamicPeroxideColumnRHS):
    """Accepted seven-species kernel, with exact coefficients at interpolated T/M."""
    def __init__(self,atmosphere,nir_provider,cycle,*,offset_s=0.,progress=None):
        self.atmosphere_provider=atmosphere
        self.atmosphere_offset_s=offset_s
        self.dynamic_nir=nir_provider
        super().__init__(None,background=atmosphere.at(offset_s),cycle=cycle,progress=progress)
        coefficients=vars(self.column_kernel.o1d.__globals__['kinetics'])
        self._coefficient_updates=tuple((wrapped,getattr(kinetics,name),
            tuple(signature(getattr(kinetics,name)).parameters))
            for name,wrapped in coefficients.items())
        self._atmosphere_time=None
        self._update_background(0.)

    def _update_background(self,time_s):
        absolute=time_s+self.atmosphere_offset_s
        if absolute==self._atmosphere_time:
            return
        self.background=self.atmosphere_provider.at(absolute)
        self.locals=tuple(self.background.local_background_at(z) for z in self.background.z_chem_km)
        kernel=self.column_kernel
        kernel.locals=self.locals
        kernel.background=SimpleNamespace(**{f.name:np.array([getattr(b,f.name) for b in self.locals])
                                             for f in fields(LocalBackground)})
        for wrapped,fn,parameters in self._coefficient_updates:
            args=[kernel.background.T if p=='temperature_k' else kernel.background.M
                  for p in parameters]
            wrapped.__kwdefaults__['value']=np.asarray(fn(*args))
        self._atmosphere_time=absolute

    def forcing(self,time_s,concentration,illumination_limit=None):
        self._update_background(time_s)
        sza=float(self.cycle.sza(time_s))
        uv=_reference_uv(concentration[:,0],concentration[:,1],sza,background=self.background)
        nir=self.dynamic_nir(time_s+self.atmosphere_offset_s,sza)
        if nir.shape!=(51,3) or not np.all(np.isfinite(nir)) or np.any(nir<0):
            raise ValueError('nonphysical dynamic NIR frequencies')
        if np.any(nir[~uv.illuminated]!=0):
            raise ValueError('dynamic NIR shadow must be exact')
        from .historical_2020.uv_radiation import local_forcing_from_uv
        forcings=tuple(local_forcing_from_uv(uv,i,gA=nir[i,0],gB=nir[i,1],gIRA=nir[i,2]) for i in range(51))
        if illumination_limit is not None:
            mismatch=np.asarray(illumination_limit)!=uv.illuminated
            tangent=180-np.rad2deg(np.arcsin(6370/(6370+np.arange(50,101))))
            if np.any(mismatch&(abs(tangent-sza)>1e-8)):
                raise ValueError('illumination-limit mismatch away from dynamic tangent')
            forcings=tuple(f if lit else LocalForcing(**{k.name:0. for k in fields(LocalForcing)})
                           for f,lit in zip(forcings,illumination_limit,strict=True))
        return uv,forcings


def dynamic_reference_noon_initialization(rhs):
    """Reuse golden multistart four-equation initializer with current native atoms."""
    rhs._update_background(0.)
    raw=rhs.atmosphere_provider.raw_at(rhs.atmosphere_offset_s)
    native=raw[50:101][:,[3,5]]*1e-6
    finite=np.isfinite(native)
    def atoms(background,*,atom_factor=1.,missing_fraction=0.):
        if atom_factor!=1. or missing_fraction!=0.:
            raise ValueError('M5C reference bootstrap uses nominal native-atom policy only')
        return np.where(finite,native,0.),finite
    initializer_rhs=SimpleNamespace(background=rhs.background,locals=rhs.locals,
        chemistry=rhs.chemistry,forcing=lambda time_s,state:rhs.forcing(0.,state))
    namespace=dict(reference_noon_initialization.__globals__)
    namespace['reference_noon_atom_profiles']=atoms
    initialize=FunctionType(reference_noon_initialization.__code__,namespace,
                            reference_noon_initialization.__name__,reference_noon_initialization.__defaults__)
    initialize.__kwdefaults__=reference_noon_initialization.__kwdefaults__
    initial,record=initialize(initializer_rhs)
    record.update(policy='reference_noon; approximate bootstrap, not climatology',
        date=rhs.cycle.start_datetime.isoformat(),latitude_deg=rhs.cycle.latitude,
        longitude_deg=rhs.cycle.longitude,SZA_deg=float(rhs.cycle.sza(0.)),
        unavailable_native_O_H='exact zero; no extrapolation')
    return initial,record


def simulate_with_background(start_datetime,end_datetime,latitude,longitude,*,
        initial_state,initialization,atmosphere,activity,background_step_s,radiation_step_s,
        radiation_inputs,cache,atmosphere_provider,dynamic_nir,**solver):
    """Reference bootstrap (optional) followed by a continuous prescribed-background run."""
    from .dynamic_atmosphere import DynamicMSISAtmosphere
    from .dynamic_radiation import DynamicNIRForcing
    from .historical_2020.background import _read_numeric_csv, load_baseline_background
    from .historical_2020.background_generation import RAD_FILENAME
    from .m5_simulation import _simulate_frozen, frozen_reference_nir
    from .solar_geometry import DatetimeSolarGeometry, validate_location
    start,end=utc_datetime(start_datetime),utc_datetime(end_datetime)
    validate_location(latitude,longitude)
    if end<=start:
        raise ValueError('end must be after start')
    if solver.get('geometry') is not None:
        raise ValueError('dynamic/automatic initialization uses real UTC solar geometry')
    begin=previous_solar_noon(start,longitude) if initialization is not None else start
    if atmosphere=='dynamic_msis':
        if atmosphere_provider is None:
            provider=DynamicMSISAtmosphere(begin,end,latitude,longitude,activity=activity,
                                            step_s=background_step_s)
        else:
            provider=atmosphere_provider
            if provider.latitude!=latitude or provider.longitude!=longitude:
                raise ValueError('precomputed atmosphere location mismatch')
            if provider.start>begin or provider.end<end:
                raise ValueError('precomputed atmosphere does not cover initialization and simulation')
            if activity is not None and provider.activity.metadata()!=activity.metadata():
                raise ValueError('precomputed atmosphere activity drivers mismatch')
        if dynamic_nir is None:
            if radiation_inputs is None:
                raise ValueError('dynamic_msis requires explicit authorized HistoricalNIRInputs or precomputed dynamic_nir')
            snapshots=provider.sampled(radiation_step_s)
            nir=DynamicNIRForcing(snapshots,DatetimeSolarGeometry(provider.start,latitude,longitude),
                                  radiation_inputs,cache=cache)
        else:
            nir=dynamic_nir
            if hasattr(nir,'atmosphere'):
                provider.validate_radiation_background(nir.atmosphere)
    else:
        case=load_baseline_background()
        raw_csv=_read_numeric_csv(RAD_FILENAME)
        raw=np.zeros((151,11))
        raw[:,3]=raw_csv['msis_O_native_cm3']*1e6
        raw[:,5]=raw_csv['msis_H_native_cm3']*1e6
        provider=SimpleNamespace(start=begin,end=end,latitude=latitude,longitude=longitude,
            at=lambda t:case,raw_at=lambda t:raw,
            metadata=lambda:dict(policy='frozen_reference M4A',activity='not applied'))
        frozen=solver.pop('nir_provider',None)
        frozen=frozen_reference_nir() if frozen is None else frozen
        def nir(t,sza):
            return frozen(sza)
    if atmosphere=='dynamic_msis' and solver.pop('nir_provider',None) is not None:
        raise ValueError('dynamic_msis does not accept a frozen SZA-only nir_provider; use dynamic_nir')
    def run(a,b,y,controls):
        offset=(a-provider.start).total_seconds()
        def factory(nir_provider,*,cycle,progress):
            return DynamicAtmosphereColumnRHS(provider,nir,cycle,offset_s=offset,progress=progress)
        namespace=dict(_simulate_frozen.__globals__)
        namespace['DynamicPeroxideColumnRHS']=factory
        integrate=FunctionType(_simulate_frozen.__code__,namespace,
                                 _simulate_frozen.__name__,_simulate_frozen.__defaults__)
        integrate.__kwdefaults__=_simulate_frozen.__kwdefaults__
        # The injected RHS supplies dynamic NIR; this argument is never evaluated.
        return integrate(a,b,latitude,longitude,y,nir_provider=lambda s:None,**controls)
    record=solver.pop('initialization_metadata',None)
    if initialization is not None:
        clock=DatetimeSolarGeometry(begin,latitude,longitude)
        rhs=DynamicAtmosphereColumnRHS(provider,nir,clock,
                                       offset_s=(begin-provider.start).total_seconds())
        initial_state,record=dynamic_reference_noon_initialization(rhs)
        if start>begin:
            controls={k:v for k,v in solver.items() if k not in ('output_times_s','output_step_s','geometry')}
            bootstrap=run(begin,start,initial_state,controls)
            initial_state=bootstrap.state_cm3[-1].copy()
            record['bootstrap_solver']=bootstrap.metadata['solver']
        record.update(noon_datetime_utc=begin.isoformat(),simulation_start_datetime_utc=start.isoformat(),
                      bootstrap_duration_s=(start-begin).total_seconds(),climatologically_validated=False)
    result=run(start,end,initial_state,solver)
    result.metadata.update(atmosphere=provider.metadata(),atmosphere_tracks_location=atmosphere=='dynamic_msis',
        initialization=record or {'policy':'explicit supplied initial_state; bootstrap completely skipped'},
        radiation={'UV':'accepted M4C with current prescribed background and dynamic chemical O/O3',
                   'NIR':nir.metadata() if isinstance(nir,DynamicNIRForcing) else 'explicit provider'},
        dynamic_atmosphere=atmosphere=='dynamic_msis')
    if atmosphere=='dynamic_msis':
        data={name:[] for name in ('background_T_K','background_M_cm3','background_O2_cm3',
            'background_N2_cm3','background_CO2_cm3','background_H2O_cm3','background_H2_cm3',
            'radiative_background_T_K','radiative_background_M_cm3','radiative_MSIS_O_native_cm3',
            'radiative_MSIS_H_native_cm3','radiative_O3_reference_cm3')}
        offset=(start-provider.start).total_seconds()
        for t in result.time_s:
            case=provider.at(float(t)+offset)
            for key,field in (('T_K','T_K'),('M_cm3','M_cm3'),('O2_cm3','O2_cm3'),
                              ('N2_cm3','N2_cm3'),('CO2_cm3','CO2_cm3'),('H2O_cm3','H2O_cm3'),('H2_cm3','H2_cm3')):
                data['background_'+key].append(getattr(case.chemical,field))
            data['radiative_background_T_K'].append(case.radiative.T_K)
            data['radiative_background_M_cm3'].append(case.radiative.M_cm3)
            data['radiative_O3_reference_cm3'].append(case.radiative.O3_socrates_reference_cm3)
            raw=provider.raw_at(float(t)+offset)
            data['radiative_MSIS_O_native_cm3'].append(raw[:,3]*1e-6)
            data['radiative_MSIS_H_native_cm3'].append(raw[:,5]*1e-6)
        result.background_fields={k:np.array(v) for k,v in data.items()}
        result.background_fields['radiative_altitude_km']=np.arange(151.)
    return result
