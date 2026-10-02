"""Frozen periodic reference cycle with accepted local temporal chemistry.

Dark-equilibrium nonuniqueness is retained as a regression, not initialization.
Concentrations: molecule cm^-3; tendencies: molecule cm^-3 s^-1.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from functools import lru_cache
from types import FunctionType, SimpleNamespace

import numpy as np

from .historical_2020 import fluxes, kinetics, local_closure, qssa, uv_geometry
from .historical_2020.background import load_baseline_background
from .historical_2020.config import DYNAMIC_SPECIES
from .historical_2020.local_closure import close_local_chemistry
from .historical_2020.local_types import (
    AlgebraicState,
    LocalBackground,
    LocalForcing,
    LocalState,
    _validate_scalar,
)
from .historical_2020.stoichiometry import TENDENCY_COEFFICIENTS
from .historical_2020.uv_geometry import spherical_shell_paths
from .historical_2020.uv_radiation import compute_uv_photolysis, local_forcing_from_uv


def _reference_shell_paths(sza_deg):
    """Accepted geometry with explicit grazing-radius roundoff repair only.

    The accepted illumination tolerance can admit impact just below Earth.
    Its sub-millimetre Earth chord then breaks shell-length closure. Snap only
    that tolerance interval to the tangent radius; leave all other rays exact.
    """
    try:
        return spherical_shell_paths(sza_deg)
    except FloatingPointError as error:
        if str(error) != "shell lengths do not close to distance-to-top":
            raise
    earth = uv_geometry.EARTH_RADIUS_KM
    radius = earth+uv_geometry.CHEMISTRY_ALTITUDES_KM
    theta = np.deg2rad(sza_deg)
    u0, impact = radius*np.cos(theta), radius*np.sin(theta)
    tolerance = 16*np.finfo(float).eps*earth
    illuminated = ~((sza_deg > 90) & (impact < earth-tolerance))
    grazing = illuminated & (np.abs(impact-earth) <= tolerance)
    if not np.any(grazing):
        raise FloatingPointError("non-grazing geometry closure failure")
    impact[grazing] = earth
    top = np.sqrt((earth+uv_geometry.TOP_OF_COLUMN_KM)**2-impact**2)
    distance = np.where(illuminated, top-u0, 0.)
    path = np.zeros((51, 150))
    edges = earth+uv_geometry.SHELL_EDGES_KM
    for index in np.flatnonzero(illuminated):
        root = np.sqrt(np.maximum(edges**2-impact[index]**2, 0.))
        length = np.minimum(top[index], root)-np.maximum(u0[index], -root)
        cumulative = np.where((edges >= impact[index]-tolerance) & (length > 0), length, 0.)
        path[index] = np.diff(cumulative)
    if np.any(path < 0) or not np.allclose(path.sum(axis=1), distance, rtol=2e-13, atol=2e-10):
        raise FloatingPointError("repaired grazing geometry failed closure")
    return uv_geometry.SphericalPathGeometry(sza_deg, illuminated, path, distance)


_uv_namespace = dict(compute_uv_photolysis.__globals__)
_uv_namespace["spherical_shell_paths"] = _reference_shell_paths
_reference_uv = FunctionType(compute_uv_photolysis.__code__, _uv_namespace,
                             compute_uv_photolysis.__name__, compute_uv_photolysis.__defaults__)
_reference_uv.__kwdefaults__ = compute_uv_photolysis.__kwdefaults__


class InitializationBlocker(RuntimeError):
    """The requested equilibrium cannot determine a unique physical state."""

    def __init__(self, witnesses: tuple[LocalState, LocalState]):
        super().__init__(
            "INITIALIZATION BLOCKER: zero forcing admits a continuum "
            "[O=0, O3=c, H=0, R_H=0, Delta=0], c>=0"
        )
        self.witnesses = witnesses


def local_rhs(
    time_s: float,
    concentrations: object,
    *,
    background: LocalBackground,
    forcing: LocalForcing,
    chemistry=close_local_chemistry,
) -> np.ndarray:
    """Pure five-species RHS in accepted order, without clipping or new chemistry.

    The caller supplies instantaneous forcing. Invalid concentrations or QSSA
    states raise their original errors; Delta is supplied as a dynamic value.
    """
    if not np.isfinite(time_s):
        raise ValueError("time_s must be finite")
    values = np.asarray(concentrations, dtype=float)
    if values.shape != (5,):
        raise ValueError("concentrations must have shape (5,)")
    state = LocalState(**dict(zip(DYNAMIC_SPECIES, values, strict=True)))
    result = chemistry(state, background, forcing)
    tendency = np.array([getattr(result.tendencies, s) for s in DYNAMIC_SPECIES])
    if not np.all(np.isfinite(tendency)):
        raise FloatingPointError("nonfinite temporal tendency")
    return tendency


class CachedLocalClosure:
    """Same accepted function bytecode with cached scalar coefficient calls.

    Private namespaces preserve the original modules untouched. No QSSA equation,
    root guard, topology or tolerance is replaced. Cache accepts scalar arguments
    only; it memoizes the original RATE_LAWS evaluators, never rounded T or M.
    """

    def __init__(self):
        coefficients = dict(vars(kinetics))
        for law in kinetics.RATE_LAWS.values():
            coefficients[law.identifier] = lru_cache(maxsize=256)(law.evaluator)
        frozen_kinetics = SimpleNamespace(**coefficients)
        replacements = {}
        for module in (qssa, fluxes, local_closure):
            namespace = dict(vars(module))
            namespace.update(replacements)
            namespace["kinetics"] = frozen_kinetics
            for name, original in vars(module).items():
                if isinstance(original, FunctionType) and original.__module__ == module.__name__:
                    clone = FunctionType(
                        original.__code__, namespace, original.__name__,
                        original.__defaults__, original.__closure__,
                    )
                    clone.__kwdefaults__ = original.__kwdefaults__
                    namespace[name] = clone
            if module is qssa:
                original_guard = qssa.find_unique_physical_root
                oh_equation = namespace["_oh_production_loss"]

                def batched_guard(residual, *, samples=257):
                    # Same 257-point ambiguity scan and original Brent guard.
                    # Evaluate the accepted array-compatible OH expression in
                    # one batch; endpoint singular limits use original callbacks.
                    if (getattr(residual, "__name__", "") != "residual_fraction"
                            or set(residual.__code__.co_freevars) !=
                            {"state", "background", "forcing", "o1d"}):
                        return original_guard(residual, samples=samples)
                    closed = dict(zip(residual.__code__.co_freevars,
                                      (cell.cell_contents for cell in residual.__closure__), strict=True))
                    state, bg, f, o1d = (closed[k] for k in ("state", "background", "forcing", "o1d"))
                    points = np.array([index/(samples-1) for index in range(samples)])
                    oh = points * state.R_H
                    ho2 = state.R_H-oh
                    production = frozen_kinetics.k_ho2_ho2(bg.T,bg.M)*ho2**2
                    loss = f.J_H2O2+frozen_kinetics.k_oh_h2o2()*oh
                    peroxide = np.divide(production,loss,out=np.zeros_like(loss),where=loss>0)
                    p_oh, loss_oh = oh_equation(state,bg,f,o1d,oh,ho2,peroxide)
                    values = p_oh-loss_oh
                    values[0], values[-1] = residual(0.0), residual(1.0)
                    # Recheck nearly exact sampled roots scalarly so floating
                    # vector evaluation cannot alter the ambiguity decision.
                    threshold = 1e-12*max(float(np.max(np.abs(values))),np.finfo(float).tiny)
                    for index in np.flatnonzero(np.abs(values)<=threshold):
                        values[index]=residual(float(points[index]))
                    memo = dict(zip(points,values,strict=True))
                    def sampled(fraction):
                        if fraction in memo:
                            return float(memo[fraction])
                        return residual(fraction)
                    return original_guard(sampled,samples=samples)
                namespace["find_unique_physical_root"] = batched_guard
            replacements.update({name: value for name, value in namespace.items()
                                 if isinstance(value, FunctionType)
                                 and name in vars(module)
                                 and isinstance(vars(module)[name], FunctionType)
                                 and vars(module)[name].__module__ == module.__name__})
        self.close = replacements["close_local_chemistry"]


TEMPORAL_SPECIES = ("O", "O3", "H", "OH", "HO2", "Delta")
OH_EVENT_COEFFICIENTS = {
    "H_O3":1., "O_HO2":1., "HO2_O3":1., "H_HO2_2OH":2.,
    "H2O2_PHOTOLYSIS":2., "H2O_PHOTOLYSIS_A":1., "O1D_H2O":2., "O1D_H2":1.,
    "O_OH":-1., "OH_O3":-1., "OH_H2":-1., "OH_OH":-2.,
    "OH_HO2":-1., "OH_H2O2":-1.,
}


@dataclass(frozen=True)
class TemporalState:
    """M5-only six prognostic species, exact OH+HO2 family diagnostic."""

    O: float  # noqa: E741
    O3: float
    H: float
    OH: float
    HO2: float
    Delta: float

    @property
    def R_H(self):
        return self.OH+self.HO2

    def __post_init__(self):
        for name in TEMPORAL_SPECIES:
            _validate_scalar(f"temporal_state.{name}", getattr(self, name))
        _validate_scalar("temporal_state.R_H", self.R_H)


class TemporalClosure:
    """Original closure body with supplied OH/HO2, four original QSSA retained."""

    def __init__(self):
        namespace = dict(CachedLocalClosure().close.__globals__)
        original_hox_globals = namespace["solve_hox_qssa"].__globals__
        peroxide = original_hox_globals["solve_h2o2_qssa"]
        oh_equation = original_hox_globals["_oh_production_loss"]

        def supplied_hox(state, background, forcing, o1d):
            result = peroxide(state.OH, state.HO2, background, forcing)
            production, loss = oh_equation(state, background, forcing, o1d,
                                          state.OH, state.HO2, result.value)
            return qssa.HoxQSSA(
                state.OH, state.HO2, result.value, production, loss,
                result.production, result.loss_frequency, production-loss,
                result.residual, 0., state.R_H==0.)

        namespace["LocalState"] = TemporalState
        namespace["solve_hox_qssa"] = supplied_hox
        self.close = FunctionType(close_local_chemistry.__code__, namespace)
        coefficients = {
            species:tuple((event,row[species]) for event,row in TENDENCY_COEFFICIENTS.items()
                          if row[species] != 0.)
            for species in DYNAMIC_SPECIES}

        def velocity(state, background, forcing):
            # Same accepted scalar solvers and event evaluator; omit only the
            # large diagnostic/contribution trace on routine ODE evaluations.
            o1d = namespace["solve_o1d_qssa"](state,background,forcing)
            h2o2 = peroxide(state.OH,state.HO2,background,forcing)
            b1 = namespace["solve_b1_qssa"](state,background,forcing,o1d.value)
            _, barth = namespace["barth_sources"](state,background)
            b0 = namespace["solve_b0_qssa"](state,background,forcing,o1d.value,b1.value,barth)
            algebraic = AlgebraicState(o1d.value,state.OH,state.HO2,h2o2.value,b0.value,b1.value)
            events = namespace["evaluate_fluxes"](state,background,forcing,algebraic)
            totals = {species:sum(events[event]*weight for event,weight in rows)
                      for species,rows in coefficients.items()}
            production = sum(events[event]*weight for event,weight in OH_EVENT_COEFFICIENTS.items()
                             if weight > 0)
            loss = sum(events[event]*(-weight) for event,weight in OH_EVENT_COEFFICIENTS.items()
                       if weight < 0)
            oh = production-loss
            return np.array([totals["O"],totals["O3"],totals["H"],oh,totals["R_H"]-oh,
                             totals["Delta"]])

        self.close.temporal_velocity = velocity


close_temporal_chemistry = TemporalClosure().close


def temporal_rhs(time_s, concentrations, *, background, forcing,
                 chemistry=close_temporal_chemistry):
    """Six-species RHS; only the accepted OH equilibrium timescale is relaxed."""
    if not np.isfinite(time_s):
        raise ValueError("time_s must be finite")
    values = np.asarray(concentrations, dtype=float)
    if values.shape != (6,):
        raise ValueError("temporal concentrations must have shape (6,)")
    state = TemporalState(*values)
    if hasattr(chemistry,"temporal_velocity"):
        result = chemistry.temporal_velocity(state,background,forcing)
    else:
        closure = chemistry(state, background, forcing)
        old = closure.tendencies
        oh = closure.diagnostics.P_OH-closure.diagnostics.L_OH
        result = np.array([old.O, old.O3, old.H, oh, old.R_H-oh, old.Delta])
    if not np.all(np.isfinite(result)):
        raise FloatingPointError("nonfinite temporal tendency")
    return result


@dataclass(frozen=True)
class ReferenceEquinoxSolarCycle:
    """Frozen reference, not calendar astronomy: 45N, declination 0, LST 0..24h."""

    period_s: float = 86400.0

    def __post_init__(self):
        if self.period_s != 86400.0:
            raise ValueError("the authorized reference period is 86400 seconds")

    def sza(self, time_s):
        t = np.asarray(time_s, dtype=float)
        if not np.all(np.isfinite(t)):
            raise ValueError("time_s must be finite")
        hour_angle = 2 * np.pi * (np.remainder(t, self.period_s) / self.period_s - 0.5)
        cosine = np.cos(np.deg2rad(45.0)) * np.cos(hour_angle)
        return np.rad2deg(np.arccos(cosine))

    def dawn_window_s(self):
        return tuple(float((0.5 - np.arccos(np.cos(np.deg2rad(sza)) /
                     np.cos(np.deg2rad(45.0))) / (2 * np.pi)) * self.period_s)
                     for sza in (99.0, 60.0))


def bootstrap_seeds(background=None):
    """Three factor-100-separated numerical seeds, never physical initialization."""
    bg = load_baseline_background() if background is None else background
    m = bg.chemical.M_cm3
    native = bg.radiative.msis_O_native_cm3[50:101]
    oxygen = np.where(np.isfinite(native), native, 1e-10 * m)
    nominal = np.column_stack((oxygen, bg.radiative.O3_socrates_reference_cm3[50:101],
                              1e-14 * m, 1e-10 * m, 1e-10 * m))
    if np.any(nominal <= 0):
        raise ValueError("bootstrap log coordinates require strictly positive seeds")
    return tuple(nominal * factor for factor in (1.0, 0.1, 10.0))


class PhysicalClosureFailure(RuntimeError):
    """A full physical state has no accepted local QSSA; keeps reproducible data."""

    def __init__(self, time_s, altitude_km, state, forcing, cause):
        super().__init__(f"QSSA failure at t={time_s:.9g}s, z={altitude_km:g}km: {cause}")
        self.time_s = float(time_s)
        self.altitude_km = float(altitude_km)
        self.state = state.copy()
        self.forcing = forcing
        self.cause = cause


def qssa_domain_witness(state, background, forcing):
    """Capture the original OH guard's exact samples without changing chemistry."""
    samples = []

    def capture(residual, *, samples_count=257):
        samples.extend(residual(index/(samples_count-1)) for index in range(samples_count))
        return qssa.find_unique_physical_root(residual, samples=samples_count)

    namespace = dict(qssa.solve_hox_qssa.__globals__)
    namespace["find_unique_physical_root"] = capture
    solve = FunctionType(qssa.solve_hox_qssa.__code__, namespace)
    o1d = qssa.solve_o1d_qssa(state, background, forcing).value
    try:
        solve(state, background, forcing, o1d)
    except qssa.QSSAError as error:
        status = str(error)
    else:
        status = "PASS"
    return dict(original_guard=status, sample_count=len(samples),
                residual_min=min(samples) if samples else None,
                residual_max=max(samples) if samples else None,
                residual_OH_equals_RH=samples[-1] if samples else None)


class ReferenceColumnRHS:
    """255 concentrations with dynamic UV self-shielding and prescribed NIR.

    Log coordinates guarantee positive solver trial concentrations without
    concentration clipping: d(log y)/dt = local_rhs(y)/y. The scalar chemical
    bytecode and root guard are accepted originals with memoized coefficients.
    """

    species_count = 5
    local_velocity = staticmethod(local_rhs)

    def __init__(self, nir_provider=None, background=None, cycle=None, progress=None):
        self.background = load_baseline_background() if background is None else background
        self.cycle = ReferenceEquinoxSolarCycle() if cycle is None else cycle
        self.nir_provider = nir_provider
        self.chemistry = CachedLocalClosure().close
        self.locals = tuple(self.background.local_background_at(z)
                            for z in self.background.z_chem_km)
        self.evaluations = 0
        self.progress = progress
        self.next_progress_s = 0.0

    def forcing(self, time_s, concentration, illumination_limit=None):
        sza = float(self.cycle.sza(time_s))
        uv = _reference_uv(concentration[:, 0], concentration[:, 1], sza,
                                  background=self.background)
        nir = np.zeros((51, 3))
        if np.any(uv.illuminated):
            if self.nir_provider is None:
                raise ValueError("an illuminated RHS requires precomputed NIR forcing")
            nir = np.asarray(self.nir_provider(sza), dtype=float)
            if nir.shape != (51, 3) or not np.all(np.isfinite(nir)) or np.any(nir < 0):
                raise ValueError("invalid NIR forcing")
            if np.any(nir[~uv.illuminated] != 0):
                raise ValueError("NIR shadow forcing must be exactly zero")
        forcings = tuple(local_forcing_from_uv(uv, i, gA=nir[i, 0], gB=nir[i, 1],
                                               gIRA=nir[i, 2]) for i in range(51))
        if illumination_limit is not None:
            # One-sided forcing at a split tangent endpoint. The value at an
            # isolated discontinuity has no effect on the ODE integral, but an
            # outgoing dark segment must not fit the incoming finite source.
            mismatch = np.asarray(illumination_limit) != uv.illuminated
            tangent = 180-np.rad2deg(np.arcsin(6370/(6370+np.arange(50,101))))
            if np.any(mismatch & (np.abs(tangent-sza) > 1e-8)):
                raise ValueError("illumination-limit mismatch away from tangent endpoint")
            forcings = tuple(f if lit else LocalForcing(**{k.name:0. for k in fields(LocalForcing)})
                             for f, lit in zip(forcings, illumination_limit, strict=True))
        return uv, forcings

    def __call__(self, time_s, log_state):
        values = np.asarray(log_state, dtype=float)
        if values.shape != (255,) or not np.all(np.isfinite(values)):
            raise ValueError("log_state must have 255 finite values")
        if np.any(values < -700) or np.any(values > 700):
            raise FloatingPointError("log-state representation range exceeded; no clipping")
        concentration = np.exp(values).reshape(51, 5)
        return (self.physical_tendencies(time_s, concentration) / concentration).ravel()

    def physical_tendencies(self, time_s, concentration, illumination_limit=None):
        """Untransformed accepted chemistry, including dynamic UV feedback."""
        _, forcings = self.forcing(time_s, concentration, illumination_limit)
        derivative = np.empty_like(concentration)
        self.evaluations += 1
        for i, (bg, forcing) in enumerate(zip(self.locals, forcings, strict=True)):
            try:
                derivative[i] = self.local_velocity(time_s, concentration[i], background=bg,
                                          forcing=forcing, chemistry=self.chemistry)
            except qssa.QSSAError as error:
                failure = PhysicalClosureFailure(time_s, i + 50, concentration[i], forcing, error)
                failure.column_state_cm3 = concentration.copy()
                raise failure from error
        if self.progress is not None and (time_s >= self.next_progress_s
                                          or self.evaluations % 1000 == 0):
            self.progress(time_s,self.evaluations,float(self.cycle.sza(time_s)))
            self.next_progress_s = time_s + 1800.0
        return derivative

    def newton_jacobian(self, time_s, log_state):
        """Block chemical iteration Jacobian; full dynamic UV remains in RHS.

        Radiation derivatives are omitted only from Newton's preconditioner,
        never from residual evaluations. Independent method/tolerance agreement
        is required before accepting a trajectory with this approximation.
        """
        from scipy.sparse import block_diag, csc_matrix

        concentration = np.exp(log_state).reshape(51, 5)
        _, forcings = self.forcing(time_s, concentration)
        blocks = []
        increment = 1e-4
        for level, (background, forcing) in enumerate(zip(self.locals, forcings, strict=True)):
            state = concentration[level]
            base = local_rhs(time_s, state, background=background,
                             forcing=forcing, chemistry=self.chemistry)/state
            block = np.empty((5, 5))
            for column in range(5):
                perturbed = state.copy()
                perturbed[column] *= np.exp(increment)
                value = local_rhs(time_s, perturbed, background=background,
                                  forcing=forcing, chemistry=self.chemistry)/perturbed
                block[:, column] = (value-base)/increment
            blocks.append(block)
        return block_diag([csc_matrix(block) for block in blocks], format="csc")


class TemporalColumnRHS(ReferenceColumnRHS):
    """M5-only 306 equations; accepted radiation and four retained QSSA."""

    species_count = 6
    local_velocity = staticmethod(temporal_rhs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chemistry = TemporalClosure().close

    def __call__(self, time_s, log_state):
        values = np.asarray(log_state, dtype=float)
        if values.shape != (306,) or not np.all(np.isfinite(values)):
            raise ValueError("log_state must have 306 finite values")
        if np.any(np.abs(values) > 700):
            raise FloatingPointError("log-state representation range exceeded; no clipping")
        concentration = np.exp(values).reshape(51, 6)
        return (self.physical_tendencies(time_s, concentration)/concentration).ravel()

    def newton_jacobian(self, time_s, log_state):
        coordinates = _CycleCoordinates(self, np.zeros(51, dtype=bool),
                                        linear_species=())
        return coordinates.newton_jacobian(time_s, log_state)


def temporal_bootstrap_seeds(rhs):
    """Partition numerical night seeds using the golden closure, never a closure in time."""
    result = []
    for old in bootstrap_seeds(rhs.background):
        _, forcings = rhs.forcing(0., old)
        six = np.empty((51, 6))
        for level, forcing in enumerate(forcings):
            algebraic = close_local_chemistry(
                LocalState(*old[level]), rhs.locals[level], forcing).algebraic
            six[level] = [*old[level, :3], algebraic.OH, algebraic.HO2, old[level, 4]]
        if np.any(six <= 0):
            raise ValueError("night bootstrap needs positive OH/HO2 seeds")
        result.append(six)
    return tuple(result)


class _CycleCoordinates:
    """Exact coordinate change: selected illuminated species linear, others log.

    Linear Delta avoids the artificial dy/y singularity when a finite solar
    source appears at a previously dark, almost empty excited-state population.
    Negative linear trial values are rejected, never clipped or extrapolated.
    """

    def __init__(self, rhs, illuminated, delta_scale=1e6, linear_species=(4,)):
        self.rhs = rhs
        self.shape = (51, getattr(rhs, "species_count", 5))
        self.illuminated = np.asarray(illuminated)
        self.linear = np.zeros(self.shape, dtype=bool)
        self.linear[:, list(linear_species)] = np.asarray(illuminated)[:,None]
        self.scale = np.broadcast_to(delta_scale, self.shape)

    def encode(self, concentration):
        result = np.empty(self.shape)
        result[~self.linear] = np.log(concentration[~self.linear])
        result[self.linear] = concentration[self.linear]/self.scale[self.linear]
        return result.ravel()

    def decode(self, values):
        values = np.asarray(values).reshape(self.shape)
        if (np.any(values[self.linear] < 0) or not np.all(np.isfinite(values))
                or np.any(np.abs(values[~self.linear]) > 700)):
            raise FloatingPointError("invalid coordinate trial; no clipping")
        result = np.empty(self.shape)
        result[~self.linear] = np.exp(values[~self.linear])
        result[self.linear] = values[self.linear]*self.scale[self.linear]
        return result

    def __call__(self, time, values):
        state = self.decode(values)
        denominator = np.where(self.linear, self.scale, state)
        return (self.rhs.physical_tendencies(time, state, self.illuminated)/denominator).ravel()

    def newton_jacobian(self, time, values):
        from scipy.sparse import block_diag, csc_matrix

        state = self.decode(values)
        _, forcings = self.rhs.forcing(time, state, self.illuminated)
        blocks = []
        for level, (background, forcing) in enumerate(zip(self.rhs.locals, forcings, strict=True)):
            def velocity(coordinates):
                physical = np.exp(np.where(self.linear[level], 0, coordinates))
                physical[self.linear[level]] = (coordinates[self.linear[level]] *
                                               self.scale[level,self.linear[level]])
                denominator = np.where(self.linear[level], self.scale[level], physical)
                try:
                    return self.rhs.local_velocity(time, physical, background=background, forcing=forcing,
                                     chemistry=self.rhs.chemistry)/denominator
                except qssa.QSSAError as error:
                    raise PhysicalClosureFailure(time, level+50, physical, forcing, error) from error

            coordinates = np.asarray(values).reshape(self.shape)[level]
            base = velocity(coordinates)
            block = np.empty((self.shape[1], self.shape[1]))
            for column in range(self.shape[1]):
                increment = (max(1e-10, abs(coordinates[column])*1e-4)
                             if self.linear[level,column] else 1e-4)
                block[:, column] = _domain_difference(velocity, coordinates, column, increment, base)
            blocks.append(block)
        return block_diag([csc_matrix(block) for block in blocks], format="csc")

    def rejected_trial(self, time, values, step, error, count):
        if hasattr(self.rhs, "rejected_trial"):
            self.rhs.rejected_trial(time, np.log(self.decode(values)).ravel(), step, error, count)

    def accepted_step(self, time, values):
        if hasattr(self.rhs, "accepted_step"):
            self.rhs.accepted_step(time, np.log(self.decode(values)).ravel())


class NIRForcingTable:
    """Nonnegative piecewise-linear SZA table; exact accepted shadow at query time."""

    def __init__(self, sza_deg, rates_s1):
        self.sza_deg = np.array(sza_deg, dtype=float, copy=True)
        self.rates_s1 = np.array(rates_s1, dtype=float, copy=True)
        if (self.sza_deg.ndim != 1 or len(self.sza_deg) < 2
                or np.any(np.diff(self.sza_deg) <= 0)
                or not np.all(np.isfinite(self.sza_deg))
                or self.rates_s1.shape != (len(self.sza_deg), 51, 3)
                or not np.all(np.isfinite(self.rates_s1)) or np.any(self.rates_s1 < 0)):
            raise ValueError("invalid NIR SZA table")
        for angle, row in zip(self.sza_deg, self.rates_s1, strict=True):
            if np.any(row[~spherical_shell_paths(angle).illuminated] != 0):
                raise ValueError("direct NIR table violates shadow")
        self.sza_deg.setflags(write=False)
        self.rates_s1.setflags(write=False)

    def __call__(self, sza_deg):
        geometry = _reference_shell_paths(sza_deg)
        result = np.zeros((51, 3))
        if not np.any(geometry.illuminated):
            return result
        if not self.sza_deg[0] <= sza_deg <= self.sza_deg[-1]:
            raise ValueError("illuminated SZA outside verified NIR table")
        for altitude in np.flatnonzero(geometry.illuminated):
            for band in range(3):
                result[altitude, band] = np.interp(
                    sza_deg, self.sza_deg, self.rates_s1[:, altitude, band])
        return result


def cycle_difference(reference, trial, absolute_floor_cm3=1.0):
    """Per-species max relative/absolute error with a declared near-zero floor."""
    a, b = np.asarray(reference), np.asarray(trial)
    if a.ndim != 2 or a.shape[0] != 51 or a.shape[1] not in (5, 6) or b.shape != a.shape:
        raise ValueError("cycle states must have shape (51,5) or (51,6)")
    floor = np.maximum(absolute_floor_cm3, 1e-6 * np.max(a, axis=0))
    relevant = np.maximum(a, b) > floor
    absolute = np.abs(b - a)
    relative = np.divide(absolute, np.maximum(a, b), out=np.zeros_like(a), where=relevant)
    return dict(relative_max=np.max(relative, axis=0),
                near_zero_absolute_max=np.max(np.where(relevant, 0, absolute), axis=0),
                relevance_floor_cm3=floor)


def _domain_difference(function, state, column, increment, base):
    """Use a physical one-sided numerical derivative at QSSA domain edges."""
    last_error = None
    for shrink in range(10):
        for sign in (1., -1.):
            step = sign*increment*10.**(-shrink)
            perturbed = state.copy()
            perturbed[column] += step
            try:
                return (function(perturbed)-base)/step
            except (PhysicalClosureFailure, FloatingPointError) as error:
                last_error = error
    raise RuntimeError("no physical finite-difference side for Newton Jacobian") from last_error


def _sparse_log_jacobian(rhs, sparsity, increment=1e-4):
    """Grouped one-sided log perturbations, above scalar QSSA roundoff.

    Group columns only when their declared row supports are disjoint. Log
    perturbations retain positive concentrations without clipping. This is a
    Newton iteration Jacobian, not an alteration of the physical RHS.
    """
    from scipy.sparse import csc_matrix

    mask = sparsity.toarray().astype(bool)
    groups, occupied = [], []
    for column in range(mask.shape[1]):
        for group, rows in zip(groups, occupied, strict=True):
            if not np.any(rows & mask[:, column]):
                group.append(column)
                rows |= mask[:, column]
                break
        else:
            groups.append([column])
            occupied.append(mask[:, column].copy())

    def jacobian(time, state):
        base = rhs(time, state)
        result = np.zeros(mask.shape)
        for group in groups:
            h = increment
            for attempt in range(6):
                perturbed = state.copy()
                perturbed[group] += h
                try:
                    delta = (rhs(time, perturbed)-base)/h
                    break
                except PhysicalClosureFailure:
                    if attempt == 5:
                        raise
                    h /= 10
            for column in group:
                result[mask[:, column], column] = delta[mask[:, column]]
        return csc_matrix(result)

    return jacobian


def _integrate_physical_segment(rhs, start, end, initial, *, method, rtol,
                                atol, max_step, sparsity):
    """Reject invalid Newton trials by restarting from the last accepted state.

    No trial is projected into the physical domain. Repeated failure at a
    vanishing step propagates the original error for scientific diagnosis.
    """
    from scipy.integrate import BDF, OdeSolution, Radau

    solver_class = {"BDF": BDF, "Radau": Radau}[method]
    times, interpolants = [start], []
    state = initial.copy()
    nfev = njev = rejections = 0
    step_limit = max_step
    first_step = None
    last_error = None
    jacobian = (rhs.newton_jacobian if hasattr(rhs, "newton_jacobian")
                else _sparse_log_jacobian(rhs, sparsity))
    while times[-1] < end:
        solver = solver_class(rhs, times[-1], state, end, rtol=rtol, atol=atol,
                              max_step=step_limit, first_step=first_step,
                              jac=jacobian)
        restart = False
        accepted_steps = 0
        while solver.status == "running":
            previous_t, previous_y = solver.t, solver.y.copy()
            attempted_step = min(solver.h_abs, end-previous_t)
            try:
                message = solver.step()
            except (FloatingPointError, PhysicalClosureFailure) as error:
                last_error = error
                rejections += 1
                if hasattr(rhs, "rejected_trial"):
                    rhs.rejected_trial(previous_t, previous_y, attempted_step, error, rejections)
                step_limit = attempted_step / 2
                if step_limit < max(1e-9, 100*np.spacing(previous_t)):
                    if isinstance(last_error, PhysicalClosureFailure):
                        last_error.last_accepted_time_s = previous_t
                        if hasattr(rhs, "decode"):
                            last_error.last_accepted_state_cm3 = rhs.decode(previous_y)
                            last_error.partial_solution = OdeSolution(times, interpolants)
                            last_error.partial_decode = rhs.decode
                    raise last_error
                state = previous_y
                first_step = step_limit
                restart = True
                break
            if solver.status == "failed":
                raise RuntimeError(f"{method}: {message}")
            times.append(solver.t)
            interpolants.append(solver.dense_output())
            state = solver.y.copy()
            if hasattr(rhs, "accepted_step"):
                rhs.accepted_step(solver.t, state)
            accepted_steps += 1
            if accepted_steps >= 8:
                solver.max_step = max_step
        nfev += solver.nfev
        njev += solver.njev
        if not restart:
            break
    return SimpleNamespace(t=np.asarray(times),initial_y=initial.copy(),
                           y=state[:, None], sol=OdeSolution(times, interpolants),
                           nfev=nfev, njev=njev, trial_rejections=rejections,
                           success=True)


def integrate_reference_cycle(rhs, initial_cm3, *, method="BDF", rtol=2e-6,
                              atol_log=1e-8, max_step_s=120, output_times_s=None,
                              start_time_s=0.0, end_time_s=86400.0):
    """Frozen reference day (or diagnostic subinterval), all species dynamic."""
    from scipy.sparse import csr_matrix, eye, kron

    initial = np.asarray(initial_cm3, dtype=float)
    count = getattr(rhs, "species_count", 5)
    dimension = 51*count
    if initial.shape != (51, count) or not np.all(np.isfinite(initial)) or np.any(initial <= 0):
        raise ValueError(f"log-coordinate initial state must be finite and positive (51,{count})")
    if method not in ("BDF", "Radau"):
        raise ValueError("use BDF or Radau")
    if not 0 <= start_time_s < end_time_s <= 86400:
        raise ValueError("integration interval must lie inside one reference day")
    # UV depends on every O/O3 node. Other local state variables only couple
    # their own height. This structural sparsity keeps all radiation feedback.
    pattern = np.zeros((dimension, dimension), dtype=bool)
    pattern[:, np.arange(dimension) % count < 2] = True
    for level in range(51):
        pattern[level*count:(level+1)*count, level*count:(level+1)*count] = True
    # Restart at every physical tangent event to change coordinates exactly.
    shadow_sza = 180-np.rad2deg(np.arcsin(6370/(6370+np.arange(50,101))))
    morning = ((0.5-np.arccos(np.cos(np.deg2rad(shadow_sza)) /
                 np.cos(np.deg2rad(45)))/(2*np.pi))*86400)
    boundaries = np.sort(np.r_[0., morning, 86400-morning, 86400.])
    boundaries = np.r_[start_time_s,
                       boundaries[(boundaries>start_time_s)&(boundaries<end_time_s)],
                       end_time_s]
    block = kron(eye(51), csr_matrix(np.ones((count,count))), format="csc")
    current = initial.copy()
    segments = []
    for index, (start, end) in enumerate(zip(boundaries[:-1], boundaries[1:], strict=True)):
        illuminated = _reference_shell_paths(float(rhs.cycle.sza((start+end)/2))).illuminated
        scales = ([1e10,1e10,1e4,1e5,1e6] if count == 5 else
                  [1e10,1e10,1e4,1e5,1e5,1e6])
        if count == 6:
            # Control small OH/HO2 directly instead of imposing a 0.001 cm^-3
            # absolute error on populations many orders of magnitude below it.
            scales = np.broadcast_to(scales, (51,6)).copy()
            scales[:,3:5] = np.maximum(1.,current[:,3:5])
        coordinates = _CycleCoordinates(rhs, illuminated,
                                        delta_scale=np.array(scales),
                                        linear_species=range(count))
        part = _integrate_physical_segment(
            coordinates, start, end, coordinates.encode(current), method=method,
            rtol=rtol, atol=atol_log, max_step=max_step_s,
            sparsity=csr_matrix(pattern) if np.any(illuminated) else block)
        if not part.success:
            raise RuntimeError(f"{method}: {part.message}")
        current = coordinates.decode(part.y[:, -1])
        segments.append((part, coordinates))

    def dense(time_s):
        query = np.atleast_1d(np.asarray(time_s, dtype=float))
        if np.any(query < start_time_s) or np.any(query > end_time_s):
            raise ValueError("dense query outside reference cycle")
        result = np.empty((dimension, len(query)))
        for index, (part, coordinates) in enumerate(segments):
            mask = (query >= boundaries[index]) & (query <= boundaries[index+1])
            if np.any(mask):
                columns = []
                for time, value in zip(query[mask],part.sol(query[mask]).T,strict=True):
                    if time == part.t[0]:
                        value = part.initial_y
                    elif time == part.t[-1]:
                        value = part.y[:,-1]
                    physical = coordinates.decode(value)
                    if np.any(physical == 0):
                        raise FloatingPointError(
                            f"zero dense concentration at t={time}; indices "
                            f"{np.argwhere(physical == 0).tolist()}; no clipping")
                    columns.append(np.log(physical).ravel())
                result[:,mask] = np.column_stack(columns)
        return result[:,0] if np.ndim(time_s)==0 else result

    times = (np.unique(np.r_[np.arange(0,86401,300), rhs.cycle.dawn_window_s(), boundaries])
             if output_times_s is None else np.asarray(output_times_s))
    times = times[(times>=start_time_s)&(times<=end_time_s)]
    result = SimpleNamespace(t=times, y=dense(times), sol=dense,
                             nfev=sum(p.nfev for p, _ in segments),
                             njev=sum(p.njev for p, _ in segments), success=True)
    result.trial_rejections = sum(p.trial_rejections for p, _ in segments)
    state = np.exp(result.y).T.reshape(-1, 51, count)
    if not np.all(np.isfinite(state)) or np.any(state <= 0):
        raise FloatingPointError("invalid physical cycle state")
    return result, state


def periodic_spinup(rhs, initial_cm3, *, max_cycles=100, tolerance=0.001,
                    absolute_tolerance_cm3=1.0, progress=None, **solver):
    """Consecutive complete days; seed independence is a separate required check."""
    current = np.array(initial_cm3, dtype=float, copy=True)
    history = []
    for day in range(1, max_cycles + 1):
        rhs.next_progress_s = 0.0
        result, states = integrate_reference_cycle(rhs, current, **solver)
        difference = cycle_difference(current, states[-1], absolute_tolerance_cm3)
        history.append(difference)
        if hasattr(rhs,"cycle_completed"):
            rhs.cycle_completed(day,states[-1],difference)
        if progress is not None:
            progress(day, difference)
        if (np.all(difference["relative_max"] <= tolerance)
                and np.all(difference["near_zero_absolute_max"] <= absolute_tolerance_cm3)):
            return dict(cycles=day, solution=result, state=states, convergence=history)
        current = states[-1].copy()
    raise RuntimeError("PERIODIC INITIALIZATION BLOCKER: cycle convergence not attained")


def reject_nonunique_dark_equilibrium(
    background: LocalBackground,
    forcing: LocalForcing,
    ozone_seed_cm3: float,
) -> None:
    """Equilibrium preflight: reject two exact roots before numerical optimization.

    Positive O3 reference values are counterexample seeds only. No initialization
    profile is accepted or returned. Nonzero forcing needs a separate root search;
    passing this guard is not a claim of equilibrium existence or uniqueness.
    """
    if not np.isfinite(ozone_seed_cm3) or ozone_seed_cm3 <= 0:
        raise ValueError("ozone_seed_cm3 must be finite and positive")
    if any(getattr(forcing, field.name) != 0 for field in fields(forcing)):
        return
    witnesses = tuple(
        LocalState(O=0.0, O3=factor * ozone_seed_cm3, H=0.0, R_H=0.0, Delta=0.0)
        for factor in (0.1, 10.0)
    )
    for state in witnesses:
        closure = close_local_chemistry(state, background, forcing)
        residuals = closure.residuals
        if any(getattr(closure.tendencies, name) != 0 for name in DYNAMIC_SPECIES):
            raise AssertionError("dark stationary witness changed: re-audit chemistry")
        if any(getattr(residuals, f.name) != 0 for f in fields(residuals)):
            raise AssertionError("dark witness violates accepted QSSA")
    raise InitializationBlocker(witnesses)
