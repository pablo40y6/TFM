"""Analytic and independent numerical ray tests for M4C geometry."""

from __future__ import annotations

import math

import numpy as np
import pytest

from tfm_photochem.historical_2020 import spherical_shell_paths

R = 6370.0
RTOP = 6520.0


def _independent_distance(z_km: float, sza_deg: float) -> float:
    theta = math.radians(sza_deg)
    radius = R + z_km
    return -radius * math.cos(theta) + math.sqrt(
        RTOP**2 - (radius * math.sin(theta)) ** 2
    )


def _numerical_shell_lengths(z_km: float, sza_deg: float, samples: int = 400_000):
    """Midpoint ray tracer independent of production shell intersections."""

    total = _independent_distance(z_km, sza_deg)
    ds = total / samples
    s = (np.arange(samples, dtype=np.float64) + 0.5) * ds
    theta = math.radians(sza_deg)
    radius0 = R + z_km
    radius = np.sqrt(radius0**2 + s**2 + 2.0 * radius0 * s * math.cos(theta))
    shell = np.floor(radius - R).astype(int)
    valid = (shell >= 0) & (shell < 150)
    return np.bincount(shell[valid], minlength=150) * ds


def test_vertical_paths_are_exact_one_kilometre_shells() -> None:
    geometry = spherical_shell_paths(0.0)
    for row, altitude in enumerate(range(50, 101)):
        assert np.array_equal(
            geometry.path_length_km[row, :altitude], np.zeros(altitude)
        )
        assert np.array_equal(
            geometry.path_length_km[row, altitude:], np.ones(150 - altitude)
        )
        assert geometry.distance_to_top_km[row] == 150.0 - altitude


@pytest.mark.parametrize("sza", [12.0, 60.0, 89.9, 90.0, 95.0])
def test_total_path_matches_independent_quadratic_solution(sza) -> None:
    geometry = spherical_shell_paths(sza)
    for row in (0, 15, 30, 50):
        if geometry.illuminated[row]:
            expected = _independent_distance(50.0 + row, sza)
            assert geometry.path_length_km[row].sum() == pytest.approx(
                expected, rel=3e-13, abs=3e-10
            )


def test_exact_ninety_degree_tangent_geometry() -> None:
    geometry = spherical_shell_paths(90.0)
    assert np.all(geometry.illuminated)
    for row, altitude in enumerate(range(50, 101)):
        expected = math.sqrt(RTOP**2 - (R + altitude) ** 2)
        assert geometry.distance_to_top_km[row] == pytest.approx(expected, rel=3e-15)
        assert np.all(geometry.path_length_km[row, :altitude] == 0.0)


@pytest.mark.parametrize(
    ("z_km", "expected"),
    [(50.0, 97.1554571394), (80.0, 99.0334297975), (100.0, 100.0866383840)],
)
def test_altitude_specific_shadow_transition(z_km, expected) -> None:
    threshold = 180.0 - math.degrees(math.asin(R / (R + z_km)))
    assert threshold == pytest.approx(expected, abs=6e-10)
    row = int(z_km - 50.0)
    assert spherical_shell_paths(threshold - 1e-7).illuminated[row]
    assert spherical_shell_paths(threshold).illuminated[row]
    assert not spherical_shell_paths(threshold + 1e-7).illuminated[row]


def test_one_sza_can_shadow_lower_levels_only() -> None:
    geometry = spherical_shell_paths(99.0)
    assert not geometry.illuminated[0]
    assert geometry.illuminated[-1]
    assert np.all(geometry.path_length_km[~geometry.illuminated] == 0.0)
    assert np.all(geometry.distance_to_top_km[~geometry.illuminated] == 0.0)


def test_twilight_ray_traverses_lower_shells_twice() -> None:
    geometry = spherical_shell_paths(95.0)
    row = 30  # target 80 km; illuminated and sunward ray initially descends
    assert geometry.illuminated[row]
    assert geometry.path_length_km[row, 60] > 2.0
    assert geometry.path_length_km[row, 90] > 1.0


@pytest.mark.parametrize(
    "z_km,sza", [(50.0, 89.9), (80.0, 90.0), (80.0, 95.0), (100.0, 99.0)]
)
def test_independent_high_resolution_numerical_ray_trace(z_km, sza) -> None:
    geometry = spherical_shell_paths(sza)
    row = int(z_km - 50.0)
    assert geometry.illuminated[row]
    numerical = _numerical_shell_lengths(z_km, sza)
    assert np.max(np.abs(numerical - geometry.path_length_km[row])) < 0.012
    assert numerical.sum() == pytest.approx(geometry.distance_to_top_km[row], abs=0.012)


@pytest.mark.parametrize("bad", [-1.0, 180.1, np.nan, np.inf])
def test_invalid_sza_is_rejected(bad) -> None:
    with pytest.raises(ValueError, match=r"\[0, 180\]"):
        spherical_shell_paths(bad)
