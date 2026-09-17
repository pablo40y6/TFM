"""Exact spherical-shell solar paths for the historical-2020 UV column."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
EARTH_RADIUS_KM = 6370.0
TOP_OF_COLUMN_KM = 150.0
CHEMISTRY_ALTITUDES_KM = np.arange(50.0, 101.0)
SHELL_EDGES_KM = np.arange(0.0, 151.0)
CHEMISTRY_ALTITUDES_KM.setflags(write=False)
SHELL_EDGES_KM.setflags(write=False)


def _freeze(value: object, shape: tuple[int, ...], name: str) -> FloatArray:
    array = np.array(value, dtype=np.float64, copy=True)
    if array.shape != shape or not np.all(np.isfinite(array)):
        raise ValueError(f"invalid {name}")
    if np.any(array < 0.0):
        raise ValueError(f"{name} must be non-negative")
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class SphericalPathGeometry:
    """Sunward path lengths through 150 one-kilometre shells."""

    sza_deg: float
    illuminated: NDArray[np.bool_]
    path_length_km: FloatArray
    distance_to_top_km: FloatArray

    def __post_init__(self) -> None:
        illuminated = np.array(self.illuminated, dtype=np.bool_, copy=True)
        if illuminated.shape != (51,):
            raise ValueError("illuminated must contain 51 values")
        illuminated.setflags(write=False)
        object.__setattr__(self, "illuminated", illuminated)
        object.__setattr__(
            self,
            "path_length_km",
            _freeze(self.path_length_km, (51, 150), "path_length_km"),
        )
        object.__setattr__(
            self,
            "distance_to_top_km",
            _freeze(self.distance_to_top_km, (51,), "distance_to_top_km"),
        )


def spherical_shell_paths(sza_deg: float) -> SphericalPathGeometry:
    """Return exact ray/shell intersection lengths from 50--100 to 150 km.

    The ray coordinate is ``u = r_target*cos(SZA) + s``.  For SZA > 90
    degrees a target is shadowed only when its impact parameter is strictly
    below the solid-Earth radius; a tangent ray remains illuminated.
    """

    sza = float(sza_deg)
    if not np.isfinite(sza) or not 0.0 <= sza <= 180.0:
        raise ValueError("sza_deg must be finite and in [0, 180]")
    theta = np.deg2rad(sza)
    target_radius = EARTH_RADIUS_KM + CHEMISTRY_ALTITUDES_KM
    u0 = target_radius * np.cos(theta)
    impact = target_radius * np.sin(theta)
    tolerance = 16.0 * np.finfo(np.float64).eps * EARTH_RADIUS_KM
    shadowed = (sza > 90.0) & (impact < EARTH_RADIUS_KM - tolerance)
    illuminated = ~shadowed

    top_radius = EARTH_RADIUS_KM + TOP_OF_COLUMN_KM
    u_top = np.sqrt(np.maximum(top_radius**2 - impact**2, 0.0))
    distance = np.where(illuminated, u_top - u0, 0.0)
    path = np.zeros((51, 150), dtype=np.float64)

    for index in np.flatnonzero(illuminated):
        inner = EARTH_RADIUS_KM + SHELL_EDGES_KM[:-1]
        outer = EARTH_RADIUS_KM + SHELL_EDGES_KM[1:]

        def cumulative(radius: FloatArray) -> FloatArray:
            root = np.sqrt(np.maximum(radius**2 - impact[index] ** 2, 0.0))
            present = radius >= impact[index] - tolerance
            length = np.minimum(u_top[index], root) - np.maximum(u0[index], -root)
            length = np.where(present & (length > 0.0), length, 0.0)
            return length

        shell_length = cumulative(outer) - cumulative(inner)
        if np.min(shell_length) < -tolerance:
            raise FloatingPointError("negative spherical-shell path length")
        shell_length[np.abs(shell_length) <= tolerance] = 0.0
        path[index] = shell_length

    if not np.allclose(path.sum(axis=1), distance, rtol=2e-13, atol=2e-10):
        raise FloatingPointError("shell lengths do not close to distance-to-top")
    return SphericalPathGeometry(sza, illuminated, path, distance)
