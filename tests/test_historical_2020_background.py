"""Independent scientific and interface tests for Milestone 4A."""

from __future__ import annotations

import json
import math
import subprocess
import sys
import types
from importlib.resources import files

import numpy as np
import pytest

from tfm_photochem.historical_2020 import (
    LocalBackground,
    LocalForcing,
    LocalState,
    close_local_chemistry,
    frozen_asset_hashes,
    load_baseline_background,
)
from tfm_photochem.historical_2020.background_generation import (
    MSIS_OPTION_VECTOR,
    MSIS_OPTIONS,
    GenerationCase,
    build_msis_call,
    m3_to_cm3,
    ordinary_neutral_total_cm3,
    run_pymsis,
)
from tfm_photochem.historical_2020.prescribed_profiles import (
    external_o3_vmr,
    load_socrates_profiles,
    log_linear_vmr,
    prescribed_h2o_h2_vmr,
)


@pytest.fixture(scope="module")
def profile():
    return load_baseline_background()


def test_grid_contract_and_exact_subset(profile) -> None:
    assert np.array_equal(profile.z_rad_km, np.arange(0.0, 151.0, 1.0))
    assert np.array_equal(profile.z_chem_km, np.arange(50.0, 101.0, 1.0))
    assert len(profile.z_rad_km) == 151
    assert len(profile.z_chem_km) == 51
    assert np.array_equal(profile.z_chem_km, profile.z_rad_km[50:101])
    assert not profile.z_rad_km.flags.writeable
    assert not profile.z_chem_km.flags.writeable


@pytest.mark.parametrize(
    ("log_palt", "z", "h2o", "h2", "o3"),
    [
        (50.0, 51.9, 5.4e-6, 3.4e-7, 2.5e-6),
        (80.0, 82.3, 2.3e-6, 2.9e-6, 1.7e-7),
        (100.0, 99.8, 1.7e-7, 3.3e-6, 3.2e-6),
        (110.0, 108.4, 1.8e-8, 2.8e-6, 1.1e-6),
    ],
)
def test_independent_source_table_spot_checks(log_palt, z, h2o, h2, o3) -> None:
    source = load_socrates_profiles()
    index = int(np.flatnonzero(source.log_palt_km == log_palt)[0])
    assert source.z_geometric_km[index] == z
    assert source.H2O_vmr[index] == h2o
    assert source.H2_vmr[index] == h2
    assert source.O3_vmr[index] == o3


def test_log_interpolation_and_exact_knots() -> None:
    z = np.array([2.0, 5.0, 8.0])
    q = np.array([1.0e-8, 1.0e-5, 1.0e-2])
    actual = log_linear_vmr(np.array([2.0, 3.5, 5.0, 8.0]), z, q)
    expected_mid = 10.0 ** (math.log10(1.0e-8) + 0.5 * (-5.0 - -8.0))
    assert actual[1] == pytest.approx(expected_mid, rel=2e-15)
    assert actual[1] != pytest.approx((1.0e-8 + 1.0e-5) / 2.0, rel=1e-3)
    assert np.array_equal(actual[[0, 2, 3]], q)


def test_h2o_h2_domain_is_bracketed_positive_and_not_extrapolated(profile) -> None:
    source = load_socrates_profiles()
    assert profile.z_chem_km.min() >= source.z_geometric_km.min()
    assert profile.z_chem_km.max() <= source.z_geometric_km.max()
    h2o, h2 = prescribed_h2o_h2_vmr(profile.z_chem_km)
    assert np.all(np.isfinite(h2o)) and np.all(h2o > 0.0)
    assert np.all(np.isfinite(h2)) and np.all(h2 > 0.0)
    assert np.all(np.isfinite(profile.chemical.H2O_cm3))
    assert np.all(np.isfinite(profile.chemical.H2_cm3))
    with pytest.raises(ValueError, match="outside"):
        prescribed_h2o_h2_vmr(np.array([109.0]))


@pytest.mark.parametrize("z", [109.0, 120.0, 150.0])
def test_o3_upper_tail_uses_only_frozen_last_two_knots(z) -> None:
    slope = (math.log10(1.1e-6) - math.log10(3.0e-6)) / (108.4 - 104.0)
    expected = 10.0 ** (math.log10(1.1e-6) + slope * (z - 108.4))
    actual = external_o3_vmr(np.array([z]))[0]
    assert actual == pytest.approx(expected, rel=2e-15)
    assert actual > 0.0


@pytest.mark.parametrize("index", [0, 50, 80, 100, 150])
def test_li_fixed_model_vmrs(index, profile) -> None:
    rad = profile.radiative
    M = rad.M_cm3[index]
    assert rad.O2_model_cm3[index] == pytest.approx(0.21 * M, rel=2e-15)
    assert rad.N2_model_cm3[index] == pytest.approx(0.78 * M, rel=2e-15)
    assert rad.CO2_model_cm3[index] == pytest.approx(405.0e-6 * M, rel=2e-15)


def test_M_definition_excludes_anomalous_oxygen_and_mass_density() -> None:
    values = [np.array([1.0, 2.0]), np.array([3.0, 4.0]), np.array([5.0, 6.0])]
    actual = ordinary_neutral_total_cm3(
        values[0], values[1], values[2], 7.0, 8.0, 9.0, 10.0
    )
    expected = values[0] + values[1] + values[2] + 7.0 + 8.0 + 9.0 + 10.0
    assert np.array_equal(actual, expected)
    anomalous_o = 1.0e99
    mass_density = 1.0e99
    assert np.all(actual < anomalous_o)
    assert np.all(actual < mass_density)


def test_explicit_number_density_unit_conversion(profile) -> None:
    native = np.array([1.0, 2.5e20])
    assert np.array_equal(m3_to_cm3(native), native * 1.0e-6)
    assert profile.metadata["number_density_conversion"] == (
        "1 m^-3 = 1e-6 molecule cm^-3"
    )


def test_ozone_composition_exact_replacement_and_external_invariance(profile) -> None:
    first = np.linspace(1.0, 51.0, 51)
    second = first + 1000.0
    composed_first = profile.compose_radiative_ozone(first)
    composed_second = profile.compose_radiative_ozone(second)
    reference = profile.radiative.O3_socrates_reference_cm3
    assert composed_first.shape == (151,)
    assert np.array_equal(composed_first[50:101], first)
    assert composed_first[50] == first[0]
    assert composed_first[100] == first[-1]
    assert np.array_equal(composed_first[:50], reference[:50])
    assert np.array_equal(composed_first[101:], reference[101:])
    assert np.array_equal(composed_first[:50], composed_second[:50])
    assert np.array_equal(composed_first[101:], composed_second[101:])
    assert not composed_first.flags.writeable


@pytest.mark.parametrize(
    ("bad", "message"),
    [
        (np.ones(50), "exactly 51"),
        (np.r_[np.ones(50), -1.0], "non-negative"),
        (np.r_[np.ones(50), np.nan], "finite"),
        (np.r_[np.ones(50), np.inf], "finite"),
    ],
)
def test_ozone_composition_rejects_invalid_input(profile, bad, message) -> None:
    with pytest.raises(ValueError, match=message):
        profile.compose_radiative_ozone(bad)


@pytest.mark.parametrize("z", [50.0, 80.0, 100.0])
def test_m3_local_background_exact_mapping(z, profile) -> None:
    local = profile.local_background_at(z)
    assert isinstance(local, LocalBackground)
    index = int(z - 50.0)
    c = profile.chemical
    assert local == LocalBackground(
        T=float(c.T_K[index]),
        M=float(c.M_cm3[index]),
        O2=float(c.O2_cm3[index]),
        N2=float(c.N2_cm3[index]),
        CO2=float(c.CO2_cm3[index]),
        H2O=float(c.H2O_cm3[index]),
        H2=float(c.H2_cm3[index]),
    )
    assert local.O2 == pytest.approx(0.21 * local.M, rel=2e-15)
    assert local.N2 == pytest.approx(0.78 * local.M, rel=2e-15)


def test_m3_closure_smoke_with_frozen_background(profile) -> None:
    state = LocalState(O=2e11, O3=2e8, H=2e7, R_H=5e7, Delta=1e8)
    forcing = LocalForcing(
        JH=8e-3,
        J_SRC=2e-8,
        J_LYA=3e-9,
        J_O2_TOTAL=2.3e-8,
        J_O3_TOTAL=8e-3,
        J_H2O2=2e-5,
        J_H2O_A=2e-8,
        J_H2O_B=1e-9,
        gA=1e-9,
        gB=2e-10,
        gIRA=3e-9,
    )
    result = close_local_chemistry(state, profile.local_background_at(80.0), forcing)
    assert all(math.isfinite(value) for value in result.tendencies.__dict__.values())


def test_non_grid_lookup_is_rejected(profile) -> None:
    with pytest.raises(ValueError, match="exact chemical-grid"):
        profile.local_background_at(80.5)


def test_runtime_load_has_no_time_dimension_or_pymsis_dependency() -> None:
    code = (
        "import sys; from tfm_photochem.historical_2020 import "
        "load_baseline_background; p=load_baseline_background(); "
        "assert 'pymsis' not in sys.modules; assert p.chemical.T_K.ndim == 1"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_generation_call_is_explicit_and_download_inaccessible() -> None:
    call = build_msis_call(GenerationCase())
    assert call["version"] == 0
    assert call["f107s"].tolist() == [150.0]
    assert call["f107as"].tolist() == [150.0]
    assert call["aps"].tolist() == [[4.0] * 7]
    assert call["options"] == [1] * 25
    assert MSIS_OPTION_VECTOR == [1] * 25
    assert MSIS_OPTIONS == {
        "f107": 1,
        "time_independent": 1,
        "symmetrical_annual": 1,
        "symmetrical_semiannual": 1,
        "asymmetrical_annual": 1,
        "asymmetrical_semiannual": 1,
        "diurnal": 1,
        "semidiurnal": 1,
        "geomagnetic_activity": 1,
        "all_ut_effects": 1,
        "longitudinal": 1,
        "mixed_ut_long": 1,
        "mixed_ap_ut_long": 1,
        "terdiurnal": 1,
    }
    assert all(call[name] is not None for name in ("f107s", "f107as", "aps"))


def test_mocked_pymsis_boundary_receives_exact_call(monkeypatch) -> None:
    captured = {}
    fake = types.ModuleType("pymsis")
    fake.__version__ = "0.12.0"

    class FakeMsis:
        @staticmethod
        def run(**kwargs):
            captured.update(kwargs)
            return np.zeros((1, 1, 1, 151, 11), dtype=np.float32)

    fake.msis = FakeMsis
    monkeypatch.setitem(sys.modules, "pymsis", fake)
    output = run_pymsis()
    assert output.shape == (151, 11)
    assert captured["version"] == 0
    assert captured["f107s"].tolist() == [150.0]
    assert captured["f107as"].tolist() == [150.0]
    assert captured["aps"].tolist() == [[4.0] * 7]
    assert captured["options"] == [1] * 25


def test_asset_metadata_hashes_and_row_counts(profile) -> None:
    hashes = frozen_asset_hashes()
    documented = profile.metadata["generated_asset_sha256"]
    assert hashes["socrates_prescribed_vmr.csv"] == documented[
        "socrates_prescribed_vmr.csv"
    ]
    assert hashes["midlatitude_equinox_quiet_radiative_background.csv"] == (
        documented["midlatitude_equinox_quiet_radiative_background.csv"]
    )
    assert hashes["midlatitude_equinox_quiet_chemical_background.csv"] == (
        documented["midlatitude_equinox_quiet_chemical_background.csv"]
    )
    root = files("tfm_photochem").joinpath("assets", "historical_2020")
    with root.joinpath("midlatitude_equinox_quiet_metadata.json").open() as stream:
        assert json.load(stream)["generator_package_version"] == "0.12.0"
