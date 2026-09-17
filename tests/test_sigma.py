import unittest
from hashlib import sha256

import numpy as np

from tfm_photochem.legacy_2017.sigma import (
    EXPECTED_SHA256,
    load_legacy_sigma,
)


class LegacySigmaTests(unittest.TestCase):
    def test_asset_hash_and_structure(self):
        sigma = load_legacy_sigma()
        self.assertEqual(sigma.sha256, EXPECTED_SHA256)
        self.assertEqual(sha256(sigma.source_path.read_bytes()).hexdigest(), EXPECTED_SHA256)
        for vector in (
            sigma.wave_nm,
            sigma.irradiance,
            sigma.sigma_n2_cm2,
            sigma.sigma_o_cm2,
            sigma.sigma_o2_cm2,
            sigma.sigma_o3_cm2,
        ):
            self.assertEqual(vector.shape, (125,))
            self.assertEqual(vector.dtype, np.float64)
            self.assertFalse(vector.flags.writeable)

    def test_wavelength_masks_and_lya_element(self):
        sigma = load_legacy_sigma()
        np.testing.assert_equal(sigma.wave_nm[[0, 27, -1]], [7.5, 121.567, 360.0])
        # The file contains one intentional duplicate at MATLAB elements 21-22.
        self.assertTrue(np.all(np.diff(sigma.wave_nm) >= 0.0))
        self.assertEqual(np.count_nonzero(np.diff(sigma.wave_nm) == 0.0), 1)
        self.assertEqual(np.count_nonzero((sigma.wave_nm > 210) & (sigma.wave_nm < 310)), 30)
        self.assertEqual(np.count_nonzero((sigma.wave_nm > 122) & (sigma.wave_nm < 175)), 36)


if __name__ == "__main__":
    unittest.main()
