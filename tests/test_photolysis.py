import unittest

import numpy as np

from tests.sample_profiles import legacy_column
from tfm_photochem.legacy_2017.geometry import path_length_matrix
from tfm_photochem.legacy_2017.photolysis import j_factors
from tfm_photochem.legacy_2017.sigma import load_legacy_sigma


class LegacyPhotolysisTests(unittest.TestCase):
    def test_regression_values_for_deterministic_column(self):
        z, o, o2, o3, n2, _ = legacy_column()
        result = j_factors(o, o2, o3, n2, z, 60.0)
        selected = [0, 30, 50, 100]
        np.testing.assert_allclose(
            result.j_hart_s1[selected],
            [
                7.901060075276741e-3,
                7.943298912613521e-3,
                7.950799890467177e-3,
                7.951370570121479e-3,
            ],
            rtol=5e-13,
        )
        np.testing.assert_allclose(
            result.j_src_s1[selected],
            [
                1.4729438260423653e-307,
                9.562150252425877e-15,
                2.6712220862792937e-8,
                3.636571535539284e-6,
            ],
            rtol=5e-13,
            atol=0.0,
        )
        np.testing.assert_allclose(
            result.j_lya_s1[selected],
            [
                3.838733007144621e-36,
                1.6186877815710608e-9,
                3.6361272783339067e-9,
                3.819962471375554e-9,
            ],
            rtol=5e-13,
            atol=0.0,
        )

    def test_matches_literal_matrix_translation(self):
        z, o, o2, o3, n2, _ = legacy_column()
        sigma = load_legacy_sigma()
        path_cm = path_length_matrix(z, 60.0) * 1.0e5
        absorbers = (
            np.outer(o, sigma.sigma_o_cm2)
            + np.outer(o2, sigma.sigma_o2_cm2)
            + np.outer(o3, sigma.sigma_o3_cm2)
            + np.outer(n2, sigma.sigma_n2_cm2)
        )
        # This is the direct MATLAB expression: absorbers' * pathl'.
        tau = absorbers.T @ path_cm.T
        jo3 = sigma.irradiance[:, None] * sigma.sigma_o3_cm2[:, None] * np.exp(-tau)
        jo2 = sigma.irradiance[:, None] * sigma.sigma_o2_cm2[:, None] * np.exp(-tau)
        jo3[tau == 0.0] = 0.0
        jo2[tau == 0.0] = 0.0

        result = j_factors(o, o2, o3, n2, z, 60.0, sigma=sigma)
        np.testing.assert_allclose(result.optical_depth, tau, rtol=3e-15, atol=0.0)
        np.testing.assert_allclose(result.j_o3_total_s1, jo3.sum(axis=0), rtol=1e-12)
        np.testing.assert_allclose(result.j_o2_total_s1, jo2.sum(axis=0), rtol=1e-12)
        np.testing.assert_allclose(
            result.j_hart_s1,
            jo3[(sigma.wave_nm > 210.0) & (sigma.wave_nm < 310.0)].sum(axis=0),
            rtol=1e-12,
        )
        np.testing.assert_allclose(
            result.j_src_s1,
            jo2[(sigma.wave_nm > 122.0) & (sigma.wave_nm < 175.0)].sum(axis=0),
            rtol=1e-12,
        )
        np.testing.assert_allclose(result.j_lya_s1, jo2[27], rtol=1e-12)

    def test_shadow_rows_are_zero_by_legacy_convention(self):
        z, o, o2, o3, n2, _ = legacy_column()
        result = j_factors(o, o2, o3, n2, z, 100.0)
        self.assertEqual(result.j_o3_total_s1[0], 0.0)
        self.assertEqual(result.j_o2_total_s1[0], 0.0)
        self.assertGreater(result.j_o3_total_s1[-1], 0.0)

    def test_zero_tau_in_daylight_forces_all_legacy_j_values_to_zero(self):
        z = np.arange(50.0, 55.0)
        zeros = np.zeros_like(z)
        result = j_factors(zeros, zeros, zeros, zeros, z, 60.0)
        np.testing.assert_equal(result.optical_depth, 0.0)
        np.testing.assert_equal(result.j_hart_s1, 0.0)
        np.testing.assert_equal(result.j_src_s1, 0.0)
        np.testing.assert_equal(result.j_lya_s1, 0.0)
        np.testing.assert_equal(result.j_o3_total_s1, 0.0)
        np.testing.assert_equal(result.j_o2_total_s1, 0.0)

    def test_photolysis_frequencies_are_finite_and_nonnegative(self):
        z, o, o2, o3, n2, _ = legacy_column()
        result = j_factors(o, o2, o3, n2, z, 89.9)
        for vector in (
            result.j_hart_s1,
            result.j_src_s1,
            result.j_lya_s1,
            result.j_o3_total_s1,
            result.j_o2_total_s1,
        ):
            self.assertTrue(np.all(np.isfinite(vector)))
            self.assertTrue(np.all(vector >= 0.0))


if __name__ == "__main__":
    unittest.main()
