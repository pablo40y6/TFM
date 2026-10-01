"""Accepted local temporal RHS and exact dark-equilibrium uniqueness witness.

No initial state is selected when the authorized equilibrium is nonunique.
Concentrations: molecule cm^-3; tendencies: molecule cm^-3 s^-1.
"""

from __future__ import annotations

from dataclasses import fields

import numpy as np

from .historical_2020.config import DYNAMIC_SPECIES
from .historical_2020.local_closure import close_local_chemistry
from .historical_2020.local_types import LocalBackground, LocalForcing, LocalState


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
    result = close_local_chemistry(state, background, forcing)
    tendency = np.array([getattr(result.tendencies, s) for s in DYNAMIC_SPECIES])
    if not np.all(np.isfinite(tendency)):
        raise FloatingPointError("nonfinite temporal tendency")
    return tendency


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
