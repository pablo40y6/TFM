#!/usr/bin/env python3
"""Emit deterministic, machine-readable Milestone-4C validation evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from importlib.resources import files

import numpy as np
from scipy.io import loadmat

from tfm_photochem.historical_2020 import (
    J_NAMES,
    LocalState,
    close_local_chemistry,
    compute_uv_photolysis,
    frozen_asset_hashes,
    h2o2_cross_section,
    h2o_channel_yields,
    h2o_cross_section,
    load_baseline_background,
    load_historical_uv_assets,
    local_forcing_from_uv,
    partition_odd_oxygen_photolysis,
    spherical_shell_paths,
    uv_asset_hashes,
)

SZA_VALUES = (0.0, 60.0, 85.0, 89.9, 95.0, 99.0)
RATE_FLOOR = 1.0e-12


def _baseline_inputs():
    case = load_baseline_background()
    oxygen = np.nan_to_num(case.radiative.msis_O_native_cm3[50:101], nan=0.0)
    ozone = case.radiative.O3_socrates_reference_cm3[50:101]
    return case, oxygen, ozone


def _source_identity() -> dict[str, object]:
    resource = files("tfm_photochem").joinpath("assets", "legacy_2017", "sigma.mat")
    with resource.open("rb") as stream:
        source_bytes = stream.read()
    with resource.open("rb") as stream:
        source = loadmat(stream, squeeze_me=True)
    backbone = load_historical_uv_assets().backbone
    mapping = {
        "wave": "wavelength_nm",
        "irrad": "solar_photon_irradiance_per_element",
        "sO": "sigma_O_cm2",
        "sO2": "sigma_O2_cm2",
        "sO3": "sigma_O3_cm2",
        "sN2": "sigma_N2_cm2",
    }
    equality = {
        source_name: bool(
            np.array_equal(
                np.asarray(source[source_name]).reshape(-1),
                getattr(backbone, target_name),
            )
        )
        for source_name, target_name in mapping.items()
    }
    if not all(equality.values()):
        raise RuntimeError("UV backbone differs from source sigma.mat")
    return {
        "sigma_mat_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "array_equal": equality,
        "source_rows": 125,
        "matlab_element_28_nm": float(backbone.wavelength_nm[27]),
        "duplicate_117_30308_matlab_indices": [21, 22],
    }


def _unattenuated_anchors() -> dict[str, float]:
    assets = load_historical_uv_assets()
    b = assets.backbone
    wavelength = b.wavelength_nm
    flux = b.solar_photon_irradiance_per_element
    o2 = flux * b.sigma_O2_cm2
    o3 = flux * b.sigma_O3_cm2
    sigma_h2o = h2o_cross_section(wavelength)
    yield_a, yield_b = h2o_channel_yields(wavelength)
    sigma_h2o2_298, _, _ = h2o2_cross_section(wavelength, 298.0)
    sigma_h2o2_200, _, _ = h2o2_cross_section(wavelength, 200.0)
    return {
        "JH": float(np.sum(o3[(wavelength > 210.0) & (wavelength < 310.0)])),
        "J_SRC": float(np.sum(o2[(wavelength >= 130.0) & (wavelength <= 175.0)])),
        "J_LYA": float(o2[27]),
        "J_O2_TOTAL": float(np.sum(o2)),
        "J_O3_TOTAL": float(np.sum(o3)),
        "J_H2O_A": float(np.sum(flux * sigma_h2o * yield_a)),
        "J_H2O_B": float(np.sum(flux * sigma_h2o * yield_b)),
        "J_H2O_REPRESENTED_TOTAL": float(np.sum(flux * sigma_h2o)),
        "J_H2O2_298K": float(np.sum(flux * sigma_h2o2_298)),
        "J_H2O2_200K": float(np.sum(flux * sigma_h2o2_200)),
        "J_H2O2_LYA_ABS_UPPER": float(flux[27] * 9.8e-18),
    }


def _h2o_provenance_correction() -> dict[str, object]:
    """Validate the JPL18 199-to-189 nm correction against the frozen CSV."""

    root = files("tfm_photochem").joinpath("assets", "historical_2020")
    with root.joinpath("jpl18_h2o_cross_sections_298k.csv").open(
        "r", encoding="utf-8", newline=""
    ) as stream:
        rows = list(csv.DictReader(stream))
    wavelengths = [float(row["wavelength_nm"]) for row in rows]
    corrected = [row for row in rows if float(row["wavelength_nm"]) == 189.0]
    if len(corrected) != 1 or float(corrected[0]["sigma_cm2"]) != 1.08e-20:
        raise RuntimeError("corrected JPL18 189 nm H2O row is absent or changed")
    if 199.0 in wavelengths:
        raise RuntimeError("printed JPL18 199 nm typographical row reached the asset")

    with root.joinpath("jpl18_uv_cross_sections_metadata.json").open(
        "r", encoding="utf-8"
    ) as stream:
        metadata = json.load(stream)
    correction = metadata["h2o"]["source_corrections"][0]
    expected_printed = {"sigma_cm2": 1.08e-20, "wavelength_nm": 199.0}
    expected_implemented = {"sigma_cm2": 1.08e-20, "wavelength_nm": 189.0}
    if correction["classification"] != "typographical correction":
        raise RuntimeError("JPL18 H2O correction classification changed")
    if correction["printed_entry"] != expected_printed:
        raise RuntimeError("printed JPL18 correction evidence changed")
    if correction["implemented_entry"] != expected_implemented:
        raise RuntimeError("implemented JPL18 correction evidence changed")
    if correction["numerical_source_configuration"] != {
        "configuration": "historical_2020",
        "numerical_source": "JPL Publication 15-10 / Evaluation 18 / Table 4B-3",
    }:
        raise RuntimeError("historical numerical-source designation changed")
    corroboration = correction["corroborating_source"]
    if corroboration["role"] != "corroboration only; not a numerical source":
        raise RuntimeError("JPL20 role is not corroboration-only")
    return {
        "classification": correction["classification"],
        "source": correction["source"],
        "printed_entry": expected_printed,
        "implemented_entry": expected_implemented,
        "implemented_asset_has_189_nm": True,
        "implemented_asset_has_no_199_nm": True,
        "evidence": correction["evidence"],
        "numerical_source_configuration": correction[
            "numerical_source_configuration"
        ],
        "corroborating_source": corroboration,
    }


def _tail_sensitivity(case, oxygen, ozone) -> dict[str, object]:
    metrics: dict[str, dict[str, object]] = {}
    profiles = []
    for sza in SZA_VALUES:
        baseline = compute_uv_photolysis(oxygen, ozone, sza, background=case)
        alternative = compute_uv_photolysis(
            oxygen,
            ozone,
            sza,
            background=case,
            external_o3_mode="zero_above_109_km",
        )
        profiles.append((sza, baseline, alternative))
    for name in J_NAMES:
        best_absolute = (-1.0, 0.0, 0.0)
        best_relative = (-1.0, 0.0, 0.0)
        for sza, baseline, alternative in profiles:
            base = getattr(baseline, name)
            alt = getattr(alternative, name)
            absolute = np.abs(base - alt)
            absolute_index = int(np.argmax(absolute))
            if absolute[absolute_index] > best_absolute[0]:
                best_absolute = (
                    float(absolute[absolute_index]),
                    float(50 + absolute_index),
                    sza,
                )
            denominator = np.maximum(np.abs(base), np.abs(alt))
            meaningful = denominator >= RATE_FLOOR
            relative = np.zeros(51)
            relative[meaningful] = absolute[meaningful] / denominator[meaningful]
            relative_index = int(np.argmax(relative))
            if relative[relative_index] > best_relative[0]:
                best_relative = (
                    float(relative[relative_index]),
                    float(50 + relative_index),
                    sza,
                )
        metrics[name] = {
            "max_absolute_s-1": best_absolute[0],
            "max_absolute_at_z_km": best_absolute[1],
            "max_absolute_at_sza_deg": best_absolute[2],
            "max_relative_at_rate_floor": best_relative[0],
            "max_relative_at_z_km": best_relative[1],
            "max_relative_at_sza_deg": best_relative[2],
        }
    principal = ("JH", "J_SRC", "J_LYA", "J_O2_TOTAL", "J_O3_TOTAL")
    material = any(
        metrics[name]["max_relative_at_rate_floor"] > 0.01 for name in principal
    )
    return {
        "alternative": "prescribed external O3 nodes z>=109 km set to zero",
        "rate_floor_s-1": RATE_FLOOR,
        "sza_deg": list(SZA_VALUES),
        "metrics": metrics,
        "principal_rate_change_over_1_percent": material,
        "classification": "material"
        if material
        else "not material at specified threshold",
    }


def _profile_evidence(
    case, oxygen, ozone
) -> tuple[dict[str, object], dict[str, object]]:
    summaries = {}
    max_lya_ratio = (-1.0, 0.0, 0.0)
    invariant_ok = True
    for sza in SZA_VALUES:
        profile = compute_uv_photolysis(oxygen, ozone, sza, background=case)
        for index in range(51):
            partition_odd_oxygen_photolysis(
                JH=float(profile.JH[index]),
                J_SRC=float(profile.J_SRC[index]),
                J_LYA=float(profile.J_LYA[index]),
                J_O2_TOTAL=float(profile.J_O2_TOTAL[index]),
                J_O3_TOTAL=float(profile.J_O3_TOTAL[index]),
            )
        summaries[str(sza)] = {
            "illuminated_level_count": int(np.count_nonzero(profile.illuminated)),
            "rates_s-1": {
                name: {
                    "min": float(np.min(getattr(profile, name))),
                    "max": float(np.max(getattr(profile, name))),
                }
                for name in J_NAMES
            },
        }
        meaningful = profile.J_H2O2 >= RATE_FLOOR
        ratio = np.zeros(51)
        ratio[meaningful] = (
            profile.diagnostics.J_H2O2_LYA_ABS_UPPER[meaningful]
            / profile.J_H2O2[meaningful]
        )
        index = int(np.argmax(ratio))
        if ratio[index] > max_lya_ratio[0]:
            max_lya_ratio = (float(ratio[index]), float(50 + index), sza)
    if not invariant_ok:
        raise RuntimeError("actual M4C profiles violate M4B gross-subset invariants")

    profile = compute_uv_photolysis(oxygen, ozone, 60.0, background=case)
    index = 30
    forcing = local_forcing_from_uv(profile, index, gA=1e-9, gB=2e-10, gIRA=3e-9)
    result = close_local_chemistry(
        LocalState(
            O=float(oxygen[index]), O3=float(ozone[index]), H=2e7, R_H=5e7, Delta=1e8
        ),
        case.local_background_at(80.0),
        forcing,
    )
    smoke_finite = all(
        math.isfinite(value) for value in result.tendencies.__dict__.values()
    )
    if not smoke_finite:
        raise RuntimeError("M4B closure smoke returned non-finite tendencies")
    lya = {
        "production_definition_includes_lya": False,
        "unattenuated_upper_s-1": 3.7436e-6,
        "max_upper_to_production_ratio_at_rate_floor": max_lya_ratio[0],
        "max_ratio_at_z_km": max_lya_ratio[1],
        "max_ratio_at_sza_deg": max_lya_ratio[2],
        "scientific_follow_up_over_10_percent": max_lya_ratio[0] > 0.10,
    }
    return summaries, {
        "gross_subset_invariants_all_profiles": invariant_ok,
        "actual_local_closure_smoke_at_80km_sza60": smoke_finite,
        "synthetic_external_g_s-1": {"gA": 1e-9, "gB": 2e-10, "gIRA": 3e-9},
        "h2o2_lya": lya,
    }


def main() -> None:
    case, oxygen, ozone = _baseline_inputs()
    profiles, consistency = _profile_evidence(case, oxygen, ozone)
    thresholds = {}
    for z_km in (50.0, 80.0, 100.0):
        threshold = 180.0 - math.degrees(math.asin(6370.0 / (6370.0 + z_km)))
        row = int(z_km - 50.0)
        thresholds[str(int(z_km))] = {
            "sza_deg": threshold,
            "below_illuminated": bool(
                spherical_shell_paths(threshold - 1e-7).illuminated[row]
            ),
            "at_illuminated": bool(spherical_shell_paths(threshold).illuminated[row]),
            "above_shadowed": bool(
                not spherical_shell_paths(threshold + 1e-7).illuminated[row]
            ),
        }
    geometry = {
        "earth_radius_km": 6370.0,
        "top_km": 150.0,
        "path_sum_km": {
            f"z{z}_sza{sza}": float(
                spherical_shell_paths(sza).path_length_km[z - 50].sum()
            )
            for z, sza in ((50, 0.0), (80, 60.0), (80, 90.0), (80, 95.0), (100, 99.0))
        },
        "shadow_thresholds": thresholds,
    }
    payload = {
        "configuration": "historical_2020",
        "milestone": "4C-R2",
        "scope": "eight UV/VUV photolysis J rates; direct beam; supplied SZA",
        "not_implemented": ["gA", "gB", "gIRA", "astronomy", "temporal solver"],
        "source_identity": _source_identity(),
        "uv_asset_sha256": uv_asset_hashes(),
        "m4a_asset_sha256": frozen_asset_hashes(),
        "jpl18_source_pdf_sha256": "149a4bab985402c67419e02ff8ca80202d1ba55f5383fbf69692e2184b68da08",
        "h2o_jpl18_typographical_correction": _h2o_provenance_correction(),
        "unattenuated_anchors_s-1": _unattenuated_anchors(),
        "geometry": geometry,
        "baseline_profile_summaries": profiles,
        "m4b_compatibility": consistency,
        "h2o2_clamped_level_count": int(np.count_nonzero(case.chemical.T_K < 200.0)),
        "o3_upper_tail_sensitivity": _tail_sensitivity(case, oxygen, ozone),
        "interpretation": (
            "provenance plus synthetic/regression evidence; not atmospheric validation"
        ),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
