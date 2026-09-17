"""Pure SOCRATES profile loading and logarithmic interpolation."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from importlib.resources import files

import numpy as np
from numpy.typing import ArrayLike, NDArray

SOURCE_ASSET = "socrates_prescribed_vmr.csv"


def _readonly(values: object) -> NDArray[np.float64]:
    array = np.array(values, dtype=np.float64, copy=True)
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class SocratesProfiles:
    log_palt_km: NDArray[np.float64]
    z_geometric_km: NDArray[np.float64]
    H2O_vmr: NDArray[np.float64]
    H2_vmr: NDArray[np.float64]
    O3_vmr: NDArray[np.float64]

    def __post_init__(self) -> None:
        lengths = {np.asarray(getattr(self, name)).size for name in self.__dataclass_fields__}
        if lengths != {23}:
            raise ValueError("SOCRATES source table must contain exactly 23 rows")
        for name in self.__dataclass_fields__:
            object.__setattr__(self, name, _readonly(getattr(self, name)))


def source_asset_path():
    """Return the packaged SOCRATES table resource."""

    return files("tfm_photochem").joinpath("assets", "historical_2020", SOURCE_ASSET)


def load_socrates_profiles() -> SocratesProfiles:
    """Load the Appendix-6 VMR table without interpolation or network access."""

    with source_asset_path().open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    columns = {
        name: np.array([float(row[name]) for row in rows], dtype=np.float64)
        for name in (
            "log_palt_km",
            "z_geometric_km",
            "H2O_vmr",
            "H2_vmr",
            "O3_vmr",
        )
    }
    return SocratesProfiles(**columns)


def log_linear_vmr(
    z_km: ArrayLike,
    source_z_km: ArrayLike,
    source_vmr: ArrayLike,
    *,
    extrapolate_above: bool = False,
) -> NDArray[np.float64]:
    """Interpolate positive VMR linearly in log10(VMR) versus geometric z."""

    z = np.asarray(z_km, dtype=np.float64)
    source_z = np.asarray(source_z_km, dtype=np.float64)
    source_q = np.asarray(source_vmr, dtype=np.float64)
    if source_z.ndim != 1 or source_q.shape != source_z.shape or source_z.size < 2:
        raise ValueError("source_z_km and source_vmr must be equal 1-D arrays")
    if not np.all(np.isfinite(source_z)) or not np.all(np.diff(source_z) > 0.0):
        raise ValueError("source_z_km must be finite and strictly increasing")
    if not np.all(np.isfinite(source_q)) or not np.all(source_q > 0.0):
        raise ValueError("source_vmr must be finite and strictly positive")
    if not np.all(np.isfinite(z)):
        raise ValueError("z_km must be finite")
    if np.any(z < source_z[0]) or (np.any(z > source_z[-1]) and not extrapolate_above):
        raise ValueError("requested altitude lies outside the source domain")

    log_q = np.log10(source_q)
    result_log = np.interp(z, source_z, log_q)
    if extrapolate_above:
        upper = z > source_z[-1]
        slope = (log_q[-1] - log_q[-2]) / (source_z[-1] - source_z[-2])
        result_log = np.where(
            upper, log_q[-1] + slope * (z - source_z[-1]), result_log
        )
    result = np.asarray(10.0**result_log, dtype=np.float64)
    for knot_z, knot_q in zip(source_z, source_q, strict=True):
        result = np.where(z == knot_z, knot_q, result)
    return result


def prescribed_h2o_h2_vmr(z_chem_km: ArrayLike):
    """Return non-extrapolated H2O/H2 VMR on the chemistry grid."""

    source = load_socrates_profiles()
    return (
        log_linear_vmr(z_chem_km, source.z_geometric_km, source.H2O_vmr),
        log_linear_vmr(z_chem_km, source.z_geometric_km, source.H2_vmr),
    )


def external_o3_vmr(z_rad_km: ArrayLike) -> NDArray[np.float64]:
    """Return SOCRATES O3 with the frozen last-two-knot upper extension."""

    source = load_socrates_profiles()
    return log_linear_vmr(
        z_rad_km,
        source.z_geometric_km,
        source.O3_vmr,
        extrapolate_above=True,
    )
