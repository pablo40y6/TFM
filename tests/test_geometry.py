import unittest

import numpy as np

from tfm_photochem.legacy_2017.geometry import path_length_matrix, pathleng

EARTH_RADIUS_KM = 6370.0


def _independent_ray_shell_path(z, target_index, sza_deg):
    """Analytic path by ray-shell intersections, independent of geometry.py."""

    z = np.asarray(z, dtype=float)
    widths = np.concatenate((np.diff(z), np.diff(z)[-1:]))
    inner = EARTH_RADIUS_KM + z
    outer = inner + widths
    target_radius = inner[target_index]
    impact_parameter = target_radius * np.sin(np.deg2rad(sza_deg))
    result = np.zeros(z.size)

    if sza_deg > 90.0 and impact_parameter <= EARTH_RADIUS_KM:
        return result

    for layer in range(target_index, z.size):
        inner_root = np.sqrt(inner[layer] ** 2 - impact_parameter**2)
        outer_root = np.sqrt(outer[layer] ** 2 - impact_parameter**2)
        result[layer] = outer_root - inner_root

    if sza_deg > 90.0:
        for layer in range(target_index):
            if outer[layer] <= impact_parameter:
                continue
            inner_root = (
                np.sqrt(inner[layer] ** 2 - impact_parameter**2)
                if inner[layer] >= impact_parameter
                else 0.0
            )
            outer_root = np.sqrt(outer[layer] ** 2 - impact_parameter**2)
            result[layer] = 2.0 * (outer_root - inner_root)

    return result


class LegacyGeometryTests(unittest.TestCase):
    def test_overhead_uniform_grid_is_upper_triangular_one_km(self):
        z = np.arange(50.0, 151.0)
        path = path_length_matrix(z, 0.0)
        expected = np.triu(np.ones((z.size, z.size)))
        np.testing.assert_allclose(path, expected, rtol=0.0, atol=2e-12)

    def test_tangent_diagonal_matches_shell_geometry(self):
        z = np.arange(50.0, 151.0)
        path = path_length_matrix(z, 90.0)
        radius = 6370.0
        expected_diagonal = np.sqrt((radius + z + 1.0) ** 2 - (radius + z) ** 2)
        np.testing.assert_allclose(np.diag(path), expected_diagonal, rtol=2e-14)
        np.testing.assert_equal(np.tril(path, -1), 0.0)

    def test_slant_column_increases_toward_terminator(self):
        z = np.arange(50.0, 151.0)
        row = 30  # 80 km target altitude
        totals = [path_length_matrix(z, angle)[row].sum() for angle in (0.0, 60.0, 80.0)]
        self.assertLess(totals[0], totals[1])
        self.assertLess(totals[1], totals[2])

    def test_required_sza_cases_preserve_shapes_and_finite_paths(self):
        z = np.arange(50.0, 151.0)
        for sza in (0.0, 60.0, 89.999, 90.0, 90.001, 95.0, 100.0):
            with self.subTest(sza=sza):
                path, column = pathleng(z, sza)
                self.assertEqual(path.shape, (101, 101))
                self.assertEqual(column.shape, (101, 202))
                self.assertTrue(np.all(np.isfinite(path)))
                self.assertTrue(np.all(path >= 0.0))

    def test_day_side_matches_independent_ray_sphere_intersections(self):
        z = np.arange(50.0, 151.0)
        target_index = 30
        for sza in (0.0, 60.0, 89.999):
            with self.subTest(sza=sza):
                expected = _independent_ray_shell_path(z, target_index, sza)
                actual = path_length_matrix(z, sza)[target_index]
                np.testing.assert_allclose(
                    actual, expected, rtol=5e-10, atol=5e-8
                )

    def test_twilight_matches_independent_geometry_away_from_fallback(self):
        z = np.arange(50.0, 151.0)
        for sza, target_index in ((90.001, 50), (95.0, 50), (100.0, 100)):
            with self.subTest(sza=sza, altitude=z[target_index]):
                expected = _independent_ray_shell_path(z, target_index, sza)
                actual = path_length_matrix(z, sza)[target_index]
                np.testing.assert_allclose(
                    actual, expected, rtol=5e-10, atol=5e-8
                )

    def test_earth_shadow_is_altitude_dependent(self):
        z = np.arange(50.0, 151.0)
        path = path_length_matrix(z, 100.0)
        np.testing.assert_equal(path[0], 0.0)
        self.assertGreater(path[-1].sum(), 0.0)

    def test_exact_geometric_transition_to_earth_shadow(self):
        z = np.arange(50.0, 151.0)
        critical_sza = np.rad2deg(
            np.pi - np.arcsin(EARTH_RADIUS_KM / (EARTH_RADIUS_KM + z[0]))
        )
        tangent_at_transition = (EARTH_RADIUS_KM + z[0]) * np.sin(
            np.deg2rad(critical_sza)
        ) - EARTH_RADIUS_KM
        self.assertEqual(tangent_at_transition, 0.0)
        self.assertGreater(
            path_length_matrix(z, critical_sza - 1.0e-6)[0].sum(), 0.0
        )
        np.testing.assert_equal(path_length_matrix(z, critical_sza)[0], 0.0)
        np.testing.assert_equal(
            path_length_matrix(z, critical_sza + 1.0e-6)[0], 0.0
        )

    def test_empty_index_fallback_preserves_legacy_below_grid_path(self):
        z = np.arange(50.0, 151.0)
        sza = 95.0
        target_radius = EARTH_RADIUS_KM + z[0]
        impact_parameter = target_radius * np.sin(np.deg2rad(sza))
        self.assertGreater(impact_parameter, EARTH_RADIUS_KM)
        self.assertLess(impact_parameter, target_radius)

        actual = path_length_matrix(z, sza)[0, 0]
        legacy_fallback = np.sqrt(
            (EARTH_RADIUS_KM + z[0] + 1.0) ** 2 - impact_parameter**2
        )
        represented_shell_only = legacy_fallback - np.sqrt(
            target_radius**2 - impact_parameter**2
        )
        self.assertAlmostEqual(actual, legacy_fallback, places=9)
        self.assertGreater(actual, represented_shell_only)

    def test_columnpathl_shape_matches_matlab_diagnostic(self):
        z = np.arange(50.0, 55.0)
        path, column = pathleng(z, 95.0)
        self.assertEqual(path.shape, (5, 5))
        self.assertEqual(column.shape, (5, 10))


if __name__ == "__main__":
    unittest.main()
