"""Literal NumPy port of the spherical geometry in ``pathleng.m``."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .parameters import value


def _validate_geometry_inputs(
    heights_km: ArrayLike, solar_zenith_angle_deg: float
) -> tuple[NDArray[np.float64], float]:
    heights = np.asarray(heights_km, dtype=np.float64).reshape(-1)
    if heights.size < 2:
        raise ValueError("At least two altitude levels are required")
    if not np.all(np.isfinite(heights)) or np.any(np.diff(heights) <= 0):
        raise ValueError("Altitude levels must be finite and strictly increasing")
    sza = float(solar_zenith_angle_deg)
    if not np.isfinite(sza) or not 0.0 <= sza <= 180.0:
        raise ValueError("Solar zenith angle must be finite and in [0, 180] degrees")
    return heights, sza


def pathleng(
    heights_km: ArrayLike, solar_zenith_angle_deg: float
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Reproduce both outputs of Anqi Li's 2017 ``pathleng.m``.

    Rows are target altitudes and columns are atmospheric layers. The first
    result is the path used for optical-depth calculations. Units are km.
    The second result reproduces the legacy diagnostic ``columnpathl`` array.

    This is intentionally a literal compatibility implementation, including
    the 6370 km Earth radius, exact ``SZA == 90`` branch, layer indexing, Earth
    shadow treatment, and NaN cleanup order of the MATLAB listing.
    """

    original_heights, sza = _validate_geometry_inputs(
        heights_km, solar_zenith_angle_deg
    )
    delta_z = np.diff(original_heights)
    delta_z = np.concatenate((delta_z, delta_z[-1:]))
    heights = np.concatenate(
        (original_heights, [original_heights.max() + delta_z[-1]])
    )
    n_heights = heights.size
    earth_radius = float(value("earth_radius"))

    if sza == 90.0:
        tangent_altitude = heights.copy()
    else:
        tangent_altitude = (
            (earth_radius + heights) * np.sin(np.deg2rad(sza)) - earth_radius
        )

    path = np.zeros((n_heights, n_heights), dtype=np.float64)
    with np.errstate(invalid="ignore"):
        for j in range(n_heights):
            h = heights[j:]
            z_tangent = tangent_altitude[j]
            path[j, j:] = np.sqrt(
                h * h
                + 2.0 * earth_radius * (h - z_tangent)
                - z_tangent * z_tangent
            )

    # MATLAB evaluates the right-hand side before assigning it back.
    path[:, :-1] = path[:, 1:].copy() - path[:, :-1].copy()
    path = np.triu(path[:-1, :-1])

    heights = heights[:-1]
    n_heights -= 1

    if sza > 90.0:
        for j in range(n_heights):
            if tangent_altitude[j] > 0.0:
                indices = np.flatnonzero(
                    (heights < heights[j]) & (heights > tangent_altitude[j])
                )
                if indices.size == 0:
                    indices = np.array([max(0, j - 1)], dtype=int)
                else:
                    indices = np.concatenate(
                        ([max(int(indices[0]) - 1, 0)], indices)
                    )

                h = heights[indices] + delta_z[indices]
                z_tangent = tangent_altitude[j]
                with np.errstate(invalid="ignore"):
                    path[j, indices] = np.sqrt(
                        h * h
                        + 2.0 * earth_radius * (h - z_tangent)
                        - z_tangent * z_tangent
                    )

                if not np.any(indices == 0):
                    previous = np.maximum(indices - 1, 0)
                    path[j, indices] = path[j, indices] - path[j, previous]
                else:
                    non_first = indices[indices != 0]
                    previous = np.maximum(non_first - 1, 0)
                    path[j, non_first] = path[j, non_first] - path[j, previous]
            elif tangent_altitude[j] <= 0.0:
                path[j, :] = 0.0

    reverse_path = np.fliplr(path)
    second_leg = np.triu(path.T, k=1).T
    second_leg[np.isnan(path)] = 0.0

    path_length = path + second_leg
    column_path = np.concatenate((reverse_path, second_leg), axis=1)
    return path_length, column_path


def path_length_matrix(
    heights_km: ArrayLike, solar_zenith_angle_deg: float
) -> NDArray[np.float64]:
    """Return only the legacy optical-depth path matrix, in km."""

    return pathleng(heights_km, solar_zenith_angle_deg)[0]

