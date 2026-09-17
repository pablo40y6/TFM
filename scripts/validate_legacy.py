#!/usr/bin/env python3
"""Run a deterministic smoke validation of the first implementation milestone."""

from __future__ import annotations

import json

import numpy as np

from tfm_photochem.legacy_2017 import j_factors, load_legacy_sigma, mkozone


def main() -> None:
    z = np.arange(50.0, 151.0)
    total = 2.5e19 * np.exp(-z / 7.0)
    o2 = 0.21 * total
    n2 = 0.78 * total
    o = 1.0e8 + 4.0e11 * np.exp(-((z - 96.0) / 17.0) ** 2)
    o3_seed = 1.0e6 + 2.0e8 * np.exp(-((z - 73.0) / 10.0) ** 2)
    temperature = 185.0 + 0.018 * (z - 82.0) ** 2

    sigma = load_legacy_sigma()
    rates = j_factors(o, o2, o3_seed, n2, z, 60.0, sigma=sigma)
    ozone = mkozone(o, o2, n2, temperature, z, 60.0, sigma=sigma)
    indices = [0, 30, 50, 100]
    print(
        json.dumps(
            {
                "configuration": "legacy_2017",
                "sigma_sha256": sigma.sha256,
                "sza_deg": 60.0,
                "altitude_km": z[indices].tolist(),
                "j_hart_s-1": rates.j_hart_s1[indices].tolist(),
                "j_src_s-1": rates.j_src_s1[indices].tolist(),
                "j_lya_s-1": rates.j_lya_s1[indices].tolist(),
                "j_o3_total_s-1": rates.j_o3_total_s1[indices].tolist(),
                "j_o2_total_s-1": rates.j_o2_total_s1[indices].tolist(),
                "mkozone_cm-3": ozone[indices].tolist(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

