#!/usr/bin/env python3
"""Emit deterministic evidence from packaged M4A assets without pymsis."""

from __future__ import annotations

import json
import math
from dataclasses import asdict

import numpy as np

from tfm_photochem.historical_2020 import frozen_asset_hashes, load_baseline_background


def main() -> None:
    profile = load_baseline_background()
    rad = profile.radiative
    chem = profile.chemical
    fixed_vmr_checks = {
        "O2": bool(np.allclose(rad.O2_model_cm3, 0.21 * rad.M_cm3, rtol=1e-15)),
        "N2": bool(np.allclose(rad.N2_model_cm3, 0.78 * rad.M_cm3, rtol=1e-15)),
        "CO2": bool(
            np.allclose(rad.CO2_model_cm3, 405.0e-6 * rad.M_cm3, rtol=1e-15)
        ),
    }
    if not all(fixed_vmr_checks.values()):
        raise RuntimeError("fixed-VMR validation failed")
    rad_anchors = {
        str(z): {
            "T_K": float(rad.T_K[z]),
            "M_cm3": float(rad.M_cm3[z]),
            "O3_reference_vmr": float(rad.O3_socrates_reference_vmr[z]),
            "O3_reference_cm3": float(rad.O3_socrates_reference_cm3[z]),
        }
        for z in (0, 50, 80, 100, 150)
    }
    chem_anchors = {
        str(z): {
            "H2O_vmr": float(chem.H2O_vmr[z - 50]),
            "H2O_cm3": float(chem.H2O_cm3[z - 50]),
            "H2_vmr": float(chem.H2_vmr[z - 50]),
            "H2_cm3": float(chem.H2_cm3[z - 50]),
        }
        for z in (50, 80, 100)
    }
    dynamic = np.arange(51, dtype=np.float64) + 1.0
    composed = profile.compose_radiative_ozone(dynamic)
    composition = {
        "dynamic_50": float(composed[50]),
        "dynamic_100": float(composed[100]),
        "external_49_preserved": bool(
            composed[49] == rad.O3_socrates_reference_cm3[49]
        ),
        "external_101_preserved": bool(
            composed[101] == rad.O3_socrates_reference_cm3[101]
        ),
    }
    local_mapping = {
        str(z): asdict(profile.local_background_at(float(z)))
        for z in (50, 80, 100)
    }
    if not np.all(np.isfinite(chem.H2O_cm3)) or not np.all(chem.H2O_cm3 > 0.0):
        raise RuntimeError("invalid prescribed H2O profile")
    if not np.all(np.isfinite(chem.H2_cm3)) or not np.all(chem.H2_cm3 > 0.0):
        raise RuntimeError("invalid prescribed H2 profile")
    if not math.isfinite(rad_anchors["150"]["O3_reference_vmr"]):
        raise RuntimeError("invalid O3 upper-tail anchor")
    payload = {
        "configuration": profile.metadata["configuration"],
        "case_name": profile.case_name,
        "asset_sha256": frozen_asset_hashes(),
        "metadata_inputs": {
            key: profile.metadata[key]
            for key in (
                "source_model",
                "generator_package_version",
                "model_version_argument",
                "datetime_utc",
                "latitude_deg",
                "longitude_deg",
                "derived_local_solar_time_hours",
                "f107_previous_day",
                "f107a_81day",
                "daily_Ap",
                "aps_vector",
                "msis_options",
                "msis_option_vector",
            )
        },
        "z_rad_count": len(profile.z_rad_km),
        "z_chem_count": len(profile.z_chem_km),
        "radiative_anchors": rad_anchors,
        "prescribed_H2O_H2_anchors": chem_anchors,
        "fixed_vmr_checks": fixed_vmr_checks,
        "ozone_composition": composition,
        "M3_LocalBackground_mapping": local_mapping,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
