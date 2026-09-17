"""Immutable data contracts for the frozen Milestone-4A background."""

from __future__ import annotations

from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import Mapping

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


def _readonly_1d(name: str, value: object, length: int) -> FloatArray:
    array = np.array(value, dtype=np.float64, copy=True)
    if array.shape != (length,):
        raise ValueError(f"{name} must contain exactly {length} values")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    array.setflags(write=False)
    return array


def _readonly_native_o(value: object) -> FloatArray:
    """Validate the partly unavailable native-MSIS O field."""

    array = np.array(value, dtype=np.float64, copy=True)
    if array.shape != (151,):
        raise ValueError("msis_O_native_cm3 must contain exactly 151 values")
    finite = np.isfinite(array)
    if np.any(finite & (array < 0.0)) or np.any(np.isinf(array)):
        raise ValueError("msis_O_native_cm3 must contain non-negative values or NaN")
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class RadiativeBackground:
    """Static 0--150 km profile nodes; no radiative geometry is implied."""

    z_km: FloatArray
    T_K: FloatArray
    M_cm3: FloatArray
    O2_model_cm3: FloatArray
    N2_model_cm3: FloatArray
    CO2_model_cm3: FloatArray
    msis_O_native_cm3: FloatArray
    O3_socrates_reference_vmr: FloatArray
    O3_socrates_reference_cm3: FloatArray

    def __post_init__(self) -> None:
        for field in fields(self):
            if field.name == "msis_O_native_cm3":
                object.__setattr__(self, field.name, _readonly_native_o(getattr(self, field.name)))
                continue
            object.__setattr__(
                self, field.name, _readonly_1d(field.name, getattr(self, field.name), 151)
            )


@dataclass(frozen=True)
class ChemicalBackground:
    """Static prescribed fields on the exact 50--100 km chemistry grid."""

    z_km: FloatArray
    T_K: FloatArray
    M_cm3: FloatArray
    O2_cm3: FloatArray
    N2_cm3: FloatArray
    CO2_cm3: FloatArray
    H2O_vmr: FloatArray
    H2O_cm3: FloatArray
    H2_vmr: FloatArray
    H2_cm3: FloatArray

    def __post_init__(self) -> None:
        for field in fields(self):
            object.__setattr__(
                self, field.name, _readonly_1d(field.name, getattr(self, field.name), 51)
            )


@dataclass(frozen=True)
class BackgroundCase:
    """A named frozen M4A case and its two aligned profile products."""

    case_name: str
    metadata: Mapping[str, object]
    radiative: RadiativeBackground
    chemical: ChemicalBackground

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def z_rad_km(self) -> FloatArray:
        return self.radiative.z_km

    @property
    def z_chem_km(self) -> FloatArray:
        return self.chemical.z_km

    def local_background_at(self, z_km: float):
        """Construct the accepted M3 scalar background at an exact grid level."""

        from .local_types import LocalBackground

        matches = np.flatnonzero(self.chemical.z_km == float(z_km))
        if matches.size != 1:
            raise ValueError("z_km must be one exact chemical-grid level (50..100 km)")
        index = int(matches[0])
        c = self.chemical
        return LocalBackground(
            T=float(c.T_K[index]),
            M=float(c.M_cm3[index]),
            O2=float(c.O2_cm3[index]),
            N2=float(c.N2_cm3[index]),
            CO2=float(c.CO2_cm3[index]),
            H2O=float(c.H2O_cm3[index]),
            H2=float(c.H2_cm3[index]),
        )

    def compose_radiative_ozone(self, o3_dynamic_cm3: object) -> FloatArray:
        """Replace exactly 50--100 km of the prescribed 151-node O3 profile."""

        dynamic = np.asarray(o3_dynamic_cm3, dtype=np.float64)
        if dynamic.shape != (51,):
            raise ValueError("o3_dynamic_cm3 must contain exactly 51 values")
        if not np.all(np.isfinite(dynamic)):
            raise ValueError("o3_dynamic_cm3 must contain only finite values")
        if np.any(dynamic < 0.0):
            raise ValueError("o3_dynamic_cm3 must be non-negative")
        composed = np.array(
            self.radiative.O3_socrates_reference_cm3, dtype=np.float64, copy=True
        )
        composed[50:101] = dynamic
        composed.setflags(write=False)
        return composed

    def compose_radiative_atomic_oxygen(self, o_dynamic_cm3: object) -> FloatArray:
        """Compose O from dynamic 50--100 km values and native MSIS elsewhere.

        Native MSIS values that are unavailable (NaN) outside the dynamic domain
        are represented as exactly zero, as specified for historical_2020 M4C.
        """

        dynamic = np.asarray(o_dynamic_cm3, dtype=np.float64)
        if dynamic.shape != (51,):
            raise ValueError("o_dynamic_cm3 must contain exactly 51 values")
        if not np.all(np.isfinite(dynamic)):
            raise ValueError("o_dynamic_cm3 must contain only finite values")
        if np.any(dynamic < 0.0):
            raise ValueError("o_dynamic_cm3 must be non-negative")
        native = self.radiative.msis_O_native_cm3
        finite = np.isfinite(native)
        if np.any(finite & (native < 0.0)):
            raise ValueError("finite native MSIS O values must be non-negative")
        composed = np.where(finite, native, 0.0)
        composed[50:101] = dynamic
        composed.setflags(write=False)
        return composed
