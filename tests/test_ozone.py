import unittest

import numpy as np

from tests.sample_profiles import legacy_column
from tfm_photochem.legacy_2017.geometry import path_length_matrix
from tfm_photochem.legacy_2017.ozone import mkozone, mkozone_iterations
from tfm_photochem.legacy_2017.sigma import load_legacy_sigma


class LegacyOzoneTests(unittest.TestCase):
    def test_regression_values_for_deterministic_column(self):
        z, o, o2, _, n2, temperature = legacy_column()
        ozone = mkozone(o, o2, n2, temperature, z, 60.0)
        np.testing.assert_allclose(
            ozone[[0, 30, 50, 100]],
            [
                5.7560219609173e11,
                8.325166168343959e9,
                5.269352202762813e7,
                3.597832916437647e-3,
            ],
            rtol=5e-13,
        )

    def test_matches_independent_literal_three_pass_calculation(self):
        z, o, o2, _, n2, temperature = legacy_column()
        sigma = load_legacy_sigma()
        path_cm = path_length_matrix(z, 60.0) * 1.0e5
        k_a = 6.0e-34 * np.exp(300.0 / temperature) ** 2.3
        k_b = 8.0e-12 * np.exp(-2060.0 / temperature)
        m = o2 + n2

        previous = None
        estimates = []
        j_values = []
        for _ in range(3):
            absorber = (
                np.outer(o, sigma.sigma_o_cm2)
                + np.outer(o2, sigma.sigma_o2_cm2)
                + np.outer(n2, sigma.sigma_n2_cm2)
            )
            if previous is not None:
                absorber += np.outer(previous, sigma.sigma_o3_cm2)
            tau = absorber.T @ path_cm.T
            j_o3 = np.sum(
                sigma.irradiance[:, None]
                * sigma.sigma_o3_cm2[:, None]
                * np.exp(-tau),
                axis=0,
            )
            previous = k_a * m * o2 * o / (j_o3 + k_b * o)
            j_values.append(j_o3)
            estimates.append(previous)

        result = mkozone_iterations(o, o2, n2, temperature, z, 60.0, sigma=sigma)
        np.testing.assert_allclose(result.iteration_1_cm3, estimates[0], rtol=4e-15)
        np.testing.assert_allclose(result.iteration_2_cm3, estimates[1], rtol=4e-15)
        np.testing.assert_allclose(result.iteration_3_cm3, estimates[2], rtol=4e-15)
        np.testing.assert_allclose(result.j_o3_iteration_3_s1, j_values[2], rtol=4e-15)
        np.testing.assert_allclose(
            mkozone(o, o2, n2, temperature, z, 60.0, sigma=sigma), estimates[2], rtol=4e-15
        )

    def test_no_artificial_clipping_and_positive_physical_case(self):
        z, o, o2, _, n2, temperature = legacy_column()
        ozone = mkozone(o, o2, n2, temperature, z, 80.0)
        self.assertTrue(np.all(np.isfinite(ozone)))
        self.assertTrue(np.all(ozone > 0.0))

    def test_rejects_nonphysical_temperature(self):
        z, o, o2, _, n2, temperature = legacy_column()
        temperature[4] = 0.0
        with self.assertRaisesRegex(ValueError, "Temperature"):
            mkozone(o, o2, n2, temperature, z, 60.0)

    def test_zero_tau_semantics_differ_from_jfactors_as_in_matlab(self):
        z = np.arange(50.0, 55.0)
        zeros = np.zeros_like(z)
        temperature = np.full_like(z, 200.0)
        result = mkozone_iterations(zeros, zeros, zeros, temperature, z, 60.0)
        self.assertTrue(np.all(result.j_o3_iteration_1_s1 > 0.0))
        np.testing.assert_equal(result.iteration_3_cm3, 0.0)


if __name__ == "__main__":
    unittest.main()
