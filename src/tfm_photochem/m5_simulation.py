"""M5B finite-horizon simulation with explicit initial state and frozen atmosphere.

Chemistry and numerical segment solver are the accepted M5A implementations.
Only the time-to-SZA provider and its physical tangent times are generalized.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix, eye, kron

from .m5_temporal import (
    DYNAMIC_PEROXIDE_SPECIES,
    DynamicPeroxideColumnRHS,
    DynamicPeroxideState,
    NIRForcingTable,
    ReferenceEquinoxSolarCycle,
    _CycleCoordinates,
    _integrate_physical_segment,
    _reference_shell_paths,
)
from .solar_geometry import DatetimeSolarGeometry, utc_datetime, validate_location

FROZEN_NIR_SHA256 = "085e1238671dfe56e69e89b1e7c477bf8a2af587f452dee7f6dec97411a54b23"


def frozen_reference_nir():
    """Verified derived A0/B/IRA table, SZA 0 through highest shell tangent.

    Raw HITRAN is not distributed. This table belongs only to the explicitly
    frozen M4A atmosphere; it is not a global atmospheric radiation database.
    """
    path = Path(__file__).parent / "assets/m5_reference/nir_a0_b_ira.npz"
    if hashlib.sha256(path.read_bytes()).hexdigest() != FROZEN_NIR_SHA256:
        raise ValueError("frozen reference NIR asset SHA256 mismatch")
    with np.load(path,allow_pickle=False) as data:
        table = NIRForcingTable(data["sza_deg"],data["rates_s1"])
        table.metadata = json.loads(str(data["metadata"]))
    return table


@dataclass(frozen=True)
class ReferenceElapsedGeometry:
    """Explicit regression adapter; leaves ReferenceEquinoxSolarCycle untouched."""
    phase_s: float = 43200.

    def sza(self, time_s):
        return ReferenceEquinoxSolarCycle().sza(np.asarray(time_s) + self.phase_s)

    def breakpoints(self, duration_s, zeniths):
        return DatetimeSolarGeometry.breakpoints(self, duration_s, zeniths)

    def metadata(self):
        return dict(algorithm="ReferenceEquinoxSolarCycle golden regression",
                    phase_s=self.phase_s, latitude_deg=45., declination_deg=0.)


@dataclass
class SimulationResult:
    time_s: np.ndarray
    altitude_km: np.ndarray
    sza_deg: np.ndarray
    state_cm3: np.ndarray
    R_H_cm3: np.ndarray
    algebraic_cm3: np.ndarray
    forcing_s1: np.ndarray
    forcing_names: tuple[str, ...]
    metadata: dict

    def save(self, path):
        """Derived time-height output only; contains no raw spectral source data."""
        np.savez_compressed(path, time_s=self.time_s, altitude_km=self.altitude_km,
            sza_deg=self.sza_deg, state_cm3=self.state_cm3,
            state_names=DYNAMIC_PEROXIDE_SPECIES, R_H_cm3=self.R_H_cm3,
            algebraic_cm3=self.algebraic_cm3, algebraic_names=("O1D","B0","B1"),
            forcing_s1=self.forcing_s1, forcing_names=self.forcing_names,
            metadata=json.dumps(self.metadata,sort_keys=True))


def simulate(start_datetime, end_datetime, latitude, longitude, initial_state, *,
             atmosphere="frozen_reference", nir_provider=None, geometry=None,
             method="BDF", rtol=2e-6, atol=1e-8, max_step_s=120.,
             output_step_s=300., output_times_s=None,
             initialization_metadata=None, progress=None):
    """Integrate seven species [cm^-3], shape (51,7), from an explicit state.

    Datetimes must be aware and are normalized to UTC. NIR defaults to the
    verified derived frozen-reference A0/B/IRA table; an explicit provider
    can override it for documented sensitivities.
    Its illuminated SZA coverage must include the requested trajectory; an
    out-of-range table raises instead of extrapolating. No automatic arbitrary
    date/location chemical initializer is implied by geometry or atmosphere.
    A geometry override is reserved for explicit reference regression.
    """
    start, end = utc_datetime(start_datetime), utc_datetime(end_datetime)
    validate_location(latitude,longitude)
    duration = (end-start).total_seconds()
    if duration <= 0:
        raise ValueError("end_datetime must be after start_datetime")
    if atmosphere != "frozen_reference":
        raise ValueError("M5B implements only the explicit frozen_reference atmosphere")
    if method not in ("BDF","Radau"):
        raise ValueError("method must be BDF or Radau")
    if any(not np.isfinite(v) or v<=0 for v in (rtol,atol,max_step_s,output_step_s)):
        raise ValueError("solver controls and output step must be positive and finite")
    initial = np.array(initial_state,dtype=float,copy=True)
    if initial.shape != (51,7) or not np.all(np.isfinite(initial)) or np.any(initial<0):
        raise ValueError("explicit initial_state must be finite/nonnegative, shape (51,7)")
    clock = DatetimeSolarGeometry(start,latitude,longitude) if geometry is None else geometry
    if geometry is not None and not isinstance(geometry,ReferenceElapsedGeometry):
        raise ValueError("geometry override is reserved for the golden reference")
    if geometry is not None and (latitude !=45 or longitude !=0):
        raise ValueError("golden geometry requires the declared reference location 45N/0E")
    if nir_provider is None:
        nir_provider = frozen_reference_nir()
    rhs = DynamicPeroxideColumnRHS(nir_provider,cycle=clock,progress=progress)
    tangent = 180-np.rad2deg(np.arcsin(6370/(6370+np.arange(50,101))))
    boundaries = clock.breakpoints(duration,tangent)
    times = (np.unique(np.r_[np.arange(0,duration,output_step_s),duration])
             if output_times_s is None else np.asarray(output_times_s,dtype=float))
    if (times.ndim!=1 or len(times)<2 or times[0]!=0 or times[-1]!=duration
            or not np.all(np.isfinite(times)) or np.any(np.diff(times)<=0)):
        raise ValueError("output times must strictly increase from 0 to duration")
    dimension = 357
    pattern = np.zeros((dimension,dimension),dtype=bool)
    pattern[:,np.arange(dimension)%7<2] = True
    for level in range(51):
        pattern[level*7:(level+1)*7,level*7:(level+1)*7] = True
    sparse = csr_matrix(pattern)
    block = kron(eye(51),csr_matrix(np.ones((7,7))),format="csc")
    states = np.empty((len(times),51,7))
    current = initial.copy()
    statistics = dict(nfev=0,njev=0,trial_rejections=0,segments=len(boundaries)-1)
    for index,(a,b) in enumerate(zip(boundaries[:-1],boundaries[1:],strict=True)):
        illuminated = _reference_shell_paths(float(clock.sza((a+b)/2))).illuminated
        scales = np.broadcast_to([1e10,1e10,1e4,1e5,1e5,1e5,1e6],(51,7)).copy()
        scales[:,3:6] = np.maximum(1.,current[:,3:6])
        coordinates = _CycleCoordinates(rhs,illuminated,delta_scale=scales,linear_species=range(7))
        # Exact zeros supplied during polar night are valid. Positive dark
        # populations retain the golden log coordinates; zeros use linear.
        coordinates.linear |= current==0
        part = _integrate_physical_segment(coordinates,a,b,coordinates.encode(current),
            method=method,rtol=rtol,atol=atol,max_step=max_step_s,
            sparsity=sparse if np.any(illuminated) else block)
        current = coordinates.decode(part.y[:,-1])
        mask = (times>=a)&((times<=b) if index==len(boundaries)-2 else (times<b))
        for i in np.flatnonzero(mask):
            value = part.initial_y if times[i]==a else part.sol(times[i])
            states[i] = coordinates.decode(value)
        for name in ("nfev","njev","trial_rejections"):
            statistics[name] += getattr(part,name)
    if not np.all(np.isfinite(states)) or np.any(states<0):
        raise FloatingPointError("nonphysical time-height output; no clipping")
    algebraic = np.empty((len(times),51,3))
    forcing = np.empty((len(times),51,11))
    forcing_names = None
    for i,(t,column) in enumerate(zip(times,states,strict=True)):
        uv,frequencies = rhs.forcing(t,column)
        forcing_names = tuple(asdict(frequencies[0]))
        forcing[i] = [[asdict(f)[name] for name in forcing_names] for f in frequencies]
        if np.any(forcing[i,~uv.illuminated]!=0):
            raise AssertionError("solid-Earth shadow must be exact")
        for j,(state,bg,f) in enumerate(zip(column,rhs.locals,frequencies,strict=True)):
            closure = rhs.chemistry(DynamicPeroxideState(*state),bg,f)
            if min(closure.diagnostics.L_O1D,closure.diagnostics.L_B0,closure.diagnostics.L_B1)<=0:
                raise FloatingPointError("remaining QSSA denominator is not positive")
            alg = closure.algebraic
            algebraic[i,j] = alg.O1D,alg.B0,alg.B1
    metadata = dict(start_datetime_utc=start.isoformat(),end_datetime_utc=end.isoformat(),
        geometry=clock.metadata(),atmosphere="frozen_reference M4A 2020-03-20 45N/0E",
        atmosphere_tracks_location=False,initialization=initialization_metadata or
        {"policy":"explicit supplied initial_state; no climatological initializer"},
        radiation=dict(UV="accepted dynamic M4C UV",NIR=getattr(nir_provider,"metadata",
            {"policy":"explicit supplied NIR provider; caller declares its provenance"})),
        dynamic_atmosphere=False,transport=False,solver=dict(method=method,rtol=rtol,
        atol=atol,max_step_s=max_step_s,**statistics))
    return SimulationResult(times,rhs.background.z_chem_km.copy(),clock.sza(times),states,
        states[:,:,3]+states[:,:,4],algebraic,forcing,forcing_names,metadata)
