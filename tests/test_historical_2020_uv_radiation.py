"""Optical, dynamic-column, and chemistry-interface tests for M4C."""

from __future__ import annotations

import math

import numpy as np
import pytest

from tfm_photochem.historical_2020 import (
    J_NAMES,
    LocalState,
    SlantColumns,
    UVSpectralBackbone,
    attenuated_photon_flux,
    close_local_chemistry,
    compute_uv_photolysis,
    load_baseline_background,
    load_historical_uv_assets,
    local_forcing_from_uv,
    optical_depth,
    partition_odd_oxygen_photolysis,
    slant_columns,
    spherical_shell_paths,
)


@pytest.fixture(scope="module")
def baseline_inputs():
    case = load_baseline_background()
    oxygen = np.nan_to_num(case.radiative.msis_O_native_cm3[50:101], nan=0.0)
    ozone = case.radiative.O3_socrates_reference_cm3[50:101]
    return case, oxygen, ozone


def _synthetic_backbone() -> UVSpectralBackbone:
    zero = np.zeros(125)
    irrad = np.zeros(125)
    irrad[:3] = [10.0, 20.0, 30.0]
    sigma_o = zero.copy()
    sigma_o[0] = 1e-20
    sigma_o2 = zero.copy()
    sigma_o2[1] = 2e-20
    sigma_o3 = zero.copy()
    sigma_o3[2] = 3e-20
    sigma_n2 = zero.copy()
    sigma_n2[:3] = 4e-22
    return UVSpectralBackbone(
        np.arange(1, 126),
        np.arange(125.0),
        irrad,
        sigma_o,
        sigma_o2,
        sigma_o3,
        sigma_n2,
    )


def test_optical_depth_zero_one_and_multiple_absorbers() -> None:
    backbone = _synthetic_backbone()
    zero = np.zeros(51)
    columns = SlantColumns(zero, zero, zero, zero)
    tau = optical_depth(columns, backbone)
    assert np.array_equal(tau, np.zeros((51, 125)))
    flux = attenuated_photon_flux(backbone, tau, np.ones(51, dtype=bool))
    assert np.array_equal(
        flux, np.broadcast_to(backbone.solar_photon_irradiance_per_element, flux.shape)
    )

    columns = SlantColumns(
        np.full(51, 2e20), np.full(51, 3e20), np.full(51, 5e20), np.full(51, 7e20)
    )
    tau = optical_depth(columns, backbone)
    expected = 2e20 * 1e-20 + 7e20 * 4e-22
    assert tau[0, 0] == pytest.approx(expected)
    assert tau[0, 1] == pytest.approx(3e20 * 2e-20 + 7e20 * 4e-22)
    assert tau[0, 2] == pytest.approx(5e20 * 3e-20 + 7e20 * 4e-22)
    assert flux[0, 0] == 10.0  # the earlier zero-column result is unattenuated
    attenuated = attenuated_photon_flux(backbone, tau, np.ones(51, dtype=bool))
    assert attenuated[0, 0] == pytest.approx(10.0 * math.exp(-expected))
    assert np.all(
        attenuated_photon_flux(backbone, tau + 1.0, np.ones(51, dtype=bool))
        <= attenuated
    )


def test_huge_tau_and_shadow_are_exactly_safe() -> None:
    backbone = _synthetic_backbone()
    tau = np.full((51, 125), 1e6)
    illuminated = np.ones(51, dtype=bool)
    illuminated[10] = False
    flux = attenuated_photon_flux(backbone, tau, illuminated)
    assert np.all(flux >= 0.0)
    assert np.all(flux == 0.0)
    zero_tau = np.zeros((51, 125))
    flux = attenuated_photon_flux(backbone, zero_tau, illuminated)
    assert np.all(flux[10] == 0.0)


def test_km_to_cm_and_endpoint_shell_mean_are_explicit() -> None:
    geometry = spherical_shell_paths(0.0)
    nodes = np.arange(151.0) + 1.0
    columns = slant_columns(
        geometry,
        O_cm3=nodes,
        O2_cm3=np.zeros(151),
        O3_cm3=np.zeros(151),
        N2_cm3=np.zeros(151),
    )
    expected = np.sum(0.5 * (nodes[50:150] + nodes[51:151])) * 1e5
    assert columns.O[0] == expected
    tau = optical_depth(columns, _synthetic_backbone())
    assert tau[0, 0] == pytest.approx(1e-20 * expected)


def test_atomic_oxygen_composition_and_dynamic_validation(baseline_inputs) -> None:
    case, _, _ = baseline_inputs
    first = np.arange(51.0)
    second = first + 1000.0
    a = case.compose_radiative_atomic_oxygen(first)
    b = case.compose_radiative_atomic_oxygen(second)
    assert np.array_equal(a[50:101], first)
    assert np.array_equal(a[:50], b[:50]) and np.array_equal(a[101:], b[101:])
    assert np.all(a[:50] == 0.0)  # unavailable native O below the MSIS support
    assert not a.flags.writeable
    for bad in (
        np.ones(50),
        np.r_[np.ones(50), -1.0],
        np.r_[np.ones(50), np.nan],
        np.r_[np.ones(50), np.inf],
    ):
        with pytest.raises(ValueError):
            case.compose_radiative_atomic_oxygen(bad)


def test_dynamic_ozone_self_shielding_is_controlled(baseline_inputs) -> None:
    case, oxygen, ozone = baseline_inputs
    first = compute_uv_photolysis(oxygen, ozone, 60.0, background=case)
    second = compute_uv_photolysis(oxygen, 2.0 * ozone, 60.0, background=case)
    assert np.all(second.JH <= first.JH)
    assert np.all(second.J_O3_TOTAL <= first.J_O3_TOTAL)
    assert np.any(second.JH < first.JH)


@pytest.mark.parametrize("sza", [0.0, 60.0, 85.0, 89.9, 95.0, 99.0, 120.0])
def test_actual_profiles_are_finite_nonnegative_and_obey_m4b_invariants(
    sza, baseline_inputs
) -> None:
    case, oxygen, ozone = baseline_inputs
    profile = compute_uv_photolysis(oxygen, ozone, sza, background=case)
    for name in J_NAMES:
        values = getattr(profile, name)
        assert np.all(np.isfinite(values)) and np.all(values >= 0.0)
        assert np.all(values[~profile.illuminated] == 0.0)
    for index in range(51):
        partition_odd_oxygen_photolysis(
            JH=float(profile.JH[index]),
            J_SRC=float(profile.J_SRC[index]),
            J_LYA=float(profile.J_LYA[index]),
            J_O2_TOTAL=float(profile.J_O2_TOTAL[index]),
            J_O3_TOTAL=float(profile.J_O3_TOTAL[index]),
        )
    assert np.allclose(
        profile.J_H2O_A + profile.J_H2O_B,
        profile.diagnostics.J_H2O_REPRESENTED_TOTAL,
        rtol=2e-15,
        atol=1e-30,
    )


def test_h2o2_diagnostics_clamp_and_lya_are_separate(baseline_inputs) -> None:
    case, oxygen, ozone = baseline_inputs
    profile = compute_uv_photolysis(oxygen, ozone, 0.0, background=case)
    assert np.count_nonzero(profile.diagnostics.h2o2_T_clamped_to_200K) == 13
    assert np.all(profile.diagnostics.h2o2_temperature_K_used >= 200.0)
    expected = profile.diagnostics.attenuated_photon_flux[:, 27] * 9.8e-18
    assert np.array_equal(profile.diagnostics.J_H2O2_LYA_ABS_UPPER, expected)
    assert np.all(profile.J_H2O2 >= 0.0)


def test_actual_m4b_local_closure_smoke_and_no_g_calculation(baseline_inputs) -> None:
    case, oxygen, ozone = baseline_inputs
    profile = compute_uv_photolysis(oxygen, ozone, 60.0, background=case)
    index = 30
    forcing = local_forcing_from_uv(profile, index, gA=1e-9, gB=2e-10, gIRA=3e-9)
    assert forcing.gA == 1e-9 and forcing.gB == 2e-10 and forcing.gIRA == 3e-9
    state = LocalState(
        O=float(oxygen[index]), O3=float(ozone[index]), H=2e7, R_H=5e7, Delta=1e8
    )
    result = close_local_chemistry(state, case.local_background_at(80.0), forcing)
    assert all(math.isfinite(value) for value in result.tendencies.__dict__.values())
    with pytest.raises(TypeError):
        local_forcing_from_uv(profile, index)  # type: ignore[call-arg]


def test_outputs_and_cached_assets_are_immutable(baseline_inputs) -> None:
    case, oxygen, ozone = baseline_inputs
    first = load_historical_uv_assets()
    second = load_historical_uv_assets()
    assert first is second
    assert not first.backbone.wavelength_nm.flags.writeable
    profile = compute_uv_photolysis(oxygen, ozone, 0.0, background=case)
    with pytest.raises(ValueError):
        profile.JH[0] = 0.0
    with pytest.raises(ValueError):
        profile.diagnostics.optical_depth[0, 0] = 0.0


def test_alternative_tail_does_not_mutate_frozen_background(baseline_inputs) -> None:
    case, oxygen, ozone = baseline_inputs
    before = case.radiative.O3_socrates_reference_cm3.copy()
    alternative = compute_uv_photolysis(
        oxygen, ozone, 89.9, background=case, external_o3_mode="zero_above_109_km"
    )
    baseline = compute_uv_photolysis(oxygen, ozone, 89.9, background=case)
    assert np.array_equal(case.radiative.O3_socrates_reference_cm3, before)
    assert np.any(
        alternative.diagnostics.columns_cm2.O3 != baseline.diagnostics.columns_cm2.O3
    )
    with pytest.raises(ValueError, match="external_o3_mode"):
        compute_uv_photolysis(
            oxygen, ozone, 0.0, background=case, external_o3_mode="bad"
        )
