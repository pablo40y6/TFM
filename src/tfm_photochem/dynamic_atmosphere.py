"""M5C MSIS-00 runtime provider; accepted M4A assets remain immutable.

Public pymsis units/options: https://swxtrec.github.io/pymsis/reference/
Explicit drivers prevent pymsis automatic space-weather lookup/download.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

import numpy as np

from .historical_2020.background_generation import MSIS_OPTION_VECTOR
from .historical_2020.background_types import (
    BackgroundCase,
    ChemicalBackground,
    RadiativeBackground,
)
from .historical_2020.prescribed_profiles import external_o3_vmr, prescribed_h2o_h2_vmr
from .solar_geometry import utc_datetime, validate_location


@dataclass(frozen=True)
class QuietReferenceActivity:
    f107: float = 150.
    f107a: float = 150.
    ap: float = 4.

    def __post_init__(self):
        if (not all(np.isfinite(v) for v in (self.f107,self.f107a,self.ap))
                or self.f107<=0 or self.f107a<=0 or self.ap<0):
            raise ValueError("activity requires positive finite F107/F107a and nonnegative finite Ap")
        for name in ('f107','f107a','ap'):
            object.__setattr__(self,name,float(getattr(self,name)))

    def at(self, dates):
        return (np.full(len(dates),self.f107),np.full(len(dates),self.f107a),
                np.full(len(dates),self.ap))

    def metadata(self):
        return dict(policy="explicit constant quiet reference, no downloads",**asdict(self))


@dataclass(frozen=True)
class ActivityDrivers:
    """Explicit time series: linear interpolation within supplied UTC coverage.

    f107 denotes the previous-day flux; f107a the 81-day mean; ap daily Ap.
    Users supply these values, not civil-time labels or implicit observations.
    """
    dates_utc: tuple[datetime, ...]
    f107: tuple[float, ...]
    f107a: tuple[float, ...]
    ap: tuple[float, ...]

    def __post_init__(self):
        dates=tuple(utc_datetime(d) for d in self.dates_utc)
        if len(dates)<2 or any(b<=a for a,b in zip(dates[:-1],dates[1:],strict=True)):
            raise ValueError("activity times must strictly increase; at least two required")
        for values in (self.f107,self.f107a,self.ap):
            if len(values)!=len(dates):
                raise ValueError("activity arrays must match dates")
        for values in zip(self.f107,self.f107a,self.ap,strict=True):
            QuietReferenceActivity(*values)
        object.__setattr__(self,"dates_utc",dates)
        for name in ('f107','f107a','ap'):
            object.__setattr__(self,name,tuple(float(v) for v in getattr(self,name)))

    def at(self, dates):
        x=np.array([utc_datetime(d).timestamp() for d in dates])
        nodes=np.array([d.timestamp() for d in self.dates_utc])
        if np.any(x<nodes[0]) or np.any(x>nodes[-1]):
            raise ValueError("explicit activity drivers do not cover bootstrap/simulation")
        return tuple(np.interp(x,nodes,values) for values in (self.f107,self.f107a,self.ap))

    def metadata(self):
        return dict(policy="explicit time-series drivers; linear interpolation; no downloads",
                    dates_utc=[d.isoformat() for d in self.dates_utc],
                    f107=list(self.f107),f107a=list(self.f107a),ap=list(self.ap))


def run_dynamic_msis(dates, latitude, longitude, activity, altitude_km=None):
    import pymsis
    from pymsis import msis
    if pymsis.__version__!="0.12.0":
        raise RuntimeError("M5C requires the accepted pymsis==0.12.0")
    validate_location(latitude,longitude)
    dates=[utc_datetime(d) for d in dates]
    z=np.arange(151.) if altitude_km is None else np.asarray(altitude_km,dtype=float)
    if z.ndim!=1 or not np.all(np.isfinite(z)) or np.any(z<0) or np.any(z>150):
        raise ValueError("MSIS radiative altitudes must lie in [0,150] km")
    f,fa,ap=activity.at(dates)
    utc=np.array([d.replace(tzinfo=None) for d in dates],dtype='datetime64[us]')
    # Flattened flythrough avoids Cartesian ambiguity, including one time/altitude.
    n=len(z)
    raw=msis.run(dates=np.repeat(utc,n),lons=np.full(len(dates)*n,longitude),
        lats=np.full(len(dates)*n,latitude),alts=np.tile(z,len(dates)),
        f107s=np.repeat(f,n),f107as=np.repeat(fa,n),
        aps=np.repeat(np.repeat(ap[:,None],7,axis=1),n,axis=0),
        options=list(MSIS_OPTION_VECTOR),version=0)
    raw=np.asarray(raw,dtype=float).reshape(len(dates),n,11)
    if (not np.all(np.isfinite(raw[:,:,0])) or np.any(raw[:,:,0]<=0)
            or not np.all(np.isfinite(raw[:,:,10])) or np.any(raw[:,:,10]<=0)):
        raise ValueError("MSIS produces nonphysical temperature/mass density")
    native=raw[:,:,1:9]
    if np.any(np.isinf(native)) or np.any(np.isfinite(native)&(native<0)):
        raise ValueError("MSIS native number densities must be nonnegative or unavailable NaN")
    return raw


def background_from_msis(raw, metadata):
    raw=np.asarray(raw,dtype=float)
    if raw.shape!=(151,11):
        raise ValueError("MSIS background requires 151 nodes x 11 native fields")
    if np.any(raw[:,0]<=0) or not np.all(np.isfinite(raw[:,0])):
        raise ValueError("nonphysical MSIS mass density")
    native=raw[:,1:9]*1e-6
    if np.any(np.isinf(native)) or np.any(np.isfinite(native)&(native<0)):
        raise ValueError("nonphysical MSIS native number density")
    ordinary=np.where(np.isfinite(native[:,:7]),native[:,:7],0.)
    M=ordinary.sum(axis=1)
    T=raw[:,10]
    if np.any(M<=0) or not np.all(np.isfinite(M)) or np.any(T<=0) or not np.all(np.isfinite(T)):
        raise ValueError("nonphysical MSIS ordinary-neutral total/temperature")
    z=np.arange(151.)
    q=external_o3_vmr(z)
    rad=RadiativeBackground(z,T,M,.21*M,.78*M,405e-6*M,native[:,2],q,q*M)
    h2o,h2=prescribed_h2o_h2_vmr(np.arange(50.,101.))
    sl=slice(50,101)
    chem=ChemicalBackground(z[sl],T[sl],M[sl],.21*M[sl],.78*M[sl],405e-6*M[sl],
                            h2o,h2o*M[sl],h2,h2*M[sl])
    return BackgroundCase("dynamic_msis",metadata,rad,chem)


class DynamicMSISAtmosphere:
    """Precompute once; every runtime query is in-memory linear interpolation."""
    def __init__(self,start_datetime,end_datetime,latitude,longitude,*,activity=None,
                 step_s=3600.,raw=None):
        self.start=utc_datetime(start_datetime)
        self.end=utc_datetime(end_datetime)
        validate_location(latitude,longitude)
        if self.end<=self.start or not np.isfinite(step_s) or step_s<=0:
            raise ValueError("positive duration and atmosphere step required")
        self.latitude,self.longitude=latitude,longitude
        self.activity=QuietReferenceActivity() if activity is None else activity
        self.step_s=float(step_s)
        duration=(self.end-self.start).total_seconds()
        self.times=np.unique(np.r_[np.arange(0,duration,step_s),duration])
        self.dates=[self.start+timedelta(seconds=float(t)) for t in self.times]
        self.raw=(run_dynamic_msis(self.dates,latitude,longitude,self.activity) if raw is None
                  else np.array(raw,dtype=float,copy=True))
        if self.raw.shape!=(len(self.times),151,11):
            raise ValueError("precomputed MSIS data do not match time/altitude grid")
        mask=np.isfinite(self.raw[:,:,1:9])
        if np.any(mask!=mask[:1]):
            raise ValueError("native MSIS availability changes across interpolation nodes")
        self.native_available=mask[0]
        for row in self.raw:
            background_from_msis(row,{})
        for values in (self.raw,self.times,self.native_available):
            values.setflags(write=False)
        self.msis_calls=1 if raw is None else 0
        self._last_time=None
        self._last_background=None

    def raw_at(self,time_s):
        if not np.isfinite(time_s) or time_s<0 or time_s>self.times[-1]:
            raise ValueError("time outside precomputed atmosphere coverage")
        i=min(int(np.searchsorted(self.times,time_s,side='right'))-1,len(self.times)-2)
        w=(time_s-self.times[i])/(self.times[i+1]-self.times[i])
        return (1-w)*self.raw[i]+w*self.raw[i+1]

    def at(self,time_s):
        if time_s!=self._last_time:
            self._last_background=background_from_msis(self.raw_at(time_s),self.metadata())
            self._last_time=time_s
        return self._last_background

    def sampled(self,step_s):
        """Coarser exact subset for costly radiation snapshots, without MSIS calls."""
        if not np.isfinite(step_s) or step_s<=0:
            raise ValueError('positive radiation step required')
        times=np.unique(np.r_[np.arange(0,self.times[-1],step_s),self.times[-1]])
        indices=np.searchsorted(self.times,times)
        if np.any(indices>=len(self.times)) or not np.array_equal(self.times[indices],times):
            raise ValueError('radiation times must be an exact subset of the atmosphere grid')
        return DynamicMSISAtmosphere(self.start,self.end,self.latitude,self.longitude,
            activity=self.activity,step_s=step_s,raw=self.raw[indices])

    def validate_radiation_background(self,other):
        """Require identical geometry/drivers and exact common native snapshots."""
        if (self.start!=other.start or self.end!=other.end or
                self.latitude!=other.latitude or self.longitude!=other.longitude or
                self.activity.metadata()!=other.activity.metadata()):
            raise ValueError('dynamic NIR/atmosphere provider mismatch')
        indices=np.searchsorted(self.times,other.times)
        if (np.any(indices>=len(self.times)) or
                not np.array_equal(self.times[indices],other.times) or
                not np.array_equal(self.raw[indices],other.raw,equal_nan=True)):
            raise ValueError('dynamic NIR requires identical native snapshots on an exact atmosphere subset')

    def metadata(self):
        return dict(policy="dynamic_msis",model="NRLMSISE-00",pymsis_version="0.12.0",
            msis_version=0,options=list(MSIS_OPTION_VECTOR),activity=self.activity.metadata(),
            start_datetime_utc=self.start.isoformat(),end_datetime_utc=self.end.isoformat(),
            latitude_deg=self.latitude,longitude_deg_east=self.longitude,step_s=self.step_s,
            interpolation="linear native densities and temperature; no RHS MSIS calls",
            number_density_units="cm^-3; native m^-3 times 1e-6",ordinary_M="sum N2/O2/O/He/H/Ar/N; unavailable=0; anomalous O excluded",
            external_O_unavailable="exact zero",O2_vmr=.21,N2_vmr=.78,CO2_vmr=405e-6,
            H2O_H2="accepted prescribed VMR profiles",external_O3="accepted SOCRATES fixed VMR times dynamic M; not date-dependent climatology")
