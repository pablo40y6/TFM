"""Independent transcription and spectral-definition tests for M4C."""

from __future__ import annotations

import csv
import hashlib
import json
from importlib.resources import files

import numpy as np
import pytest
from scipy.io import loadmat

from tfm_photochem.historical_2020 import (
    h2o2_cross_section,
    h2o_channel_yields,
    h2o_cross_section,
    load_historical_uv_assets,
    uv_asset_hashes,
)

SIGMA_SHA256 = "a98567c4f971721cec4197ad7ea17182e95df78c3a0eea880acb08fc6d560424"
BACKBONE_SHA256 = "a398b97e7b2ae68efa9c72353444317e8a73f836870f0bd2cd6f21a5b1c7b135"
H2O_SHA256 = "d70d7d79405cb4b86de2186d1fd1212c332eb1eb362279f117b99daa00ce2e2c"
H2O2_SHA256 = "bec01ae613d088455bdb64657b46f33bfe3cdb3b6e294c6f41fd21cbd611f4a1"


def test_backbone_is_numerically_identical_to_all_six_sigma_arrays() -> None:
    resource = files("tfm_photochem").joinpath("assets", "legacy_2017", "sigma.mat")
    with resource.open("rb") as stream:
        raw_bytes = stream.read()
    assert hashlib.sha256(raw_bytes).hexdigest() == SIGMA_SHA256
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
    for source_name, field_name in mapping.items():
        assert np.array_equal(
            np.asarray(source[source_name]).reshape(-1), getattr(backbone, field_name)
        )
    assert uv_asset_hashes()["uv_spectral_backbone_2017.csv"] == BACKBONE_SHA256


def test_source_indices_duplicate_and_masks_are_exact() -> None:
    b = load_historical_uv_assets().backbone
    assert b.source_matlab_index[27] == 28
    assert b.wavelength_nm[27] == 121.567
    assert b.wavelength_nm[20] == b.wavelength_nm[21] == 117.30308
    hartley = np.flatnonzero((b.wavelength_nm > 210.0) & (b.wavelength_nm < 310.0))
    src = np.flatnonzero((b.wavelength_nm >= 130.0) & (b.wavelength_nm <= 175.0))
    assert np.array_equal(hartley, np.arange(84, 114))
    assert np.array_equal(src, np.arange(39, 65))
    assert 27 not in src
    assert np.all(b.sigma_O2_cm2[[20, 21]] > 0.0)


def test_unattenuated_o_o2_o3_anchors_without_production_helpers() -> None:
    b = load_historical_uv_assets().backbone
    wave = b.wavelength_nm
    flux = b.solar_photon_irradiance_per_element
    o2 = flux * b.sigma_O2_cm2
    o3 = flux * b.sigma_O3_cm2
    assert np.sum(o3[(wave > 210.0) & (wave < 310.0)]) == pytest.approx(
        7.951381890000001e-3, rel=2e-15
    )
    assert np.sum(o2[(wave >= 130.0) & (wave <= 175.0)]) == pytest.approx(
        3.6227120000000004e-6, rel=2e-15
    )
    assert o2[27] == pytest.approx(3.82e-9, rel=2e-15)
    assert np.sum(o2) == pytest.approx(4.5171738408e-6, rel=2e-15)
    assert np.sum(o3) == pytest.approx(8.07364762308e-3, rel=2e-15)
    duplicated_contribution = np.sum(o2[[20, 21]])
    assert duplicated_contribution > 0.0


@pytest.mark.parametrize(
    ("wavelength", "sigma_1e20"),
    [
        (121.567, 1480.0),
        (130.0, 718.0),
        (145.0, 58.0),
        (165.0, 499.0),
        (184.0, 12.1),
        (198.0, 0.09),
    ],
)
def test_h2o_jpl18_table_4b3_spot_rows(wavelength, sigma_1e20) -> None:
    table = load_historical_uv_assets().h2o
    index = int(np.flatnonzero(table.wavelength_nm == wavelength)[0])
    assert table.sigma_cm2[index] == sigma_1e20 * 1e-20
    assert uv_asset_hashes()["jpl18_h2o_cross_sections_298k.csv"] == H2O_SHA256


def test_documented_jpl18_199_to_189_nm_typographical_correction() -> None:
    """Freeze the corrected asset row independently of its metadata record."""

    root = files("tfm_photochem").joinpath("assets", "historical_2020")
    with root.joinpath("jpl18_h2o_cross_sections_298k.csv").open(
        "r", encoding="utf-8", newline=""
    ) as stream:
        rows = list(csv.DictReader(stream))
    wavelengths = [float(row["wavelength_nm"]) for row in rows]
    corrected = [row for row in rows if float(row["wavelength_nm"]) == 189.0]
    assert len(corrected) == 1
    assert float(corrected[0]["sigma_cm2"]) == 1.08e-20
    assert 199.0 not in wavelengths

    with root.joinpath("jpl18_uv_cross_sections_metadata.json").open(
        "r", encoding="utf-8"
    ) as stream:
        metadata = json.load(stream)
    correction = metadata["h2o"]["source_corrections"][0]
    assert correction["classification"] == "typographical correction"
    assert correction["printed_entry"] == {
        "wavelength_nm": 199.0,
        "sigma_cm2": 1.08e-20,
    }
    assert correction["implemented_entry"] == {
        "wavelength_nm": 189.0,
        "sigma_cm2": 1.08e-20,
    }
    assert correction["numerical_source_configuration"]["configuration"] == (
        "historical_2020"
    )
    assert "Evaluation 18" in correction["source"]["title"]
    assert correction["corroborating_source"]["role"] == (
        "corroboration only; not a numerical source"
    )


def test_h2o_interpolation_domain_yields_and_anchors() -> None:
    wavelength = np.array([120.9, 121.0, 121.25, 146.999, 147.0, 198.0, 198.1])
    sigma = h2o_cross_section(wavelength)
    assert sigma[0] == sigma[-1] == 0.0
    assert sigma[2] == pytest.approx(0.5 * (624.0 + 1276.0) * 1e-20)
    yield_a, yield_b = h2o_channel_yields(wavelength)
    assert np.array_equal(yield_a, [0.0, 0.89, 0.89, 0.89, 1.0, 1.0, 0.0])
    assert np.array_equal(yield_b, [0.0, 0.11, 0.11, 0.11, 0.0, 0.0, 0.0])
    b = load_historical_uv_assets().backbone
    sigma = h2o_cross_section(b.wavelength_nm)
    yield_a, yield_b = h2o_channel_yields(b.wavelength_nm)
    element = b.solar_photon_irradiance_per_element * sigma
    assert np.sum(element * yield_a) == pytest.approx(1.1454298921361168e-5)
    assert np.sum(element * yield_b) == pytest.approx(6.647332715993185e-7)
    assert np.sum(element) == pytest.approx(1.2119032192960486e-5)
    assert np.sum(element * (yield_a + yield_b)) == pytest.approx(np.sum(element))


@pytest.mark.parametrize(
    ("wavelength", "sigma_1e20"),
    [(190.0, 67.2), (230.0, 18.2), (260.0, 5.3), (300.0, 0.68), (350.0, 0.036)],
)
def test_h2o2_jpl18_table_4b5_spot_rows(wavelength, sigma_1e20) -> None:
    table = load_historical_uv_assets().h2o2
    index = int(np.flatnonzero(table.wavelength_nm == wavelength)[0])
    assert table.sigma_cm2[index] == sigma_1e20 * 1e-20
    assert uv_asset_hashes()["jpl18_h2o2_cross_sections_298k.csv"] == H2O2_SHA256


@pytest.mark.parametrize(
    "wavelength,temperature", [(260.0, 200.0), (287.3, 298.0), (350.0, 400.0)]
)
def test_h2o2_polynomial_against_independent_direct_sum(
    wavelength, temperature
) -> None:
    coefficients_a = [
        6.4761e4,
        -9.2170972e2,
        4.535649,
        -4.4589016e-3,
        -4.035101e-5,
        1.6878206e-7,
        -2.652014e-10,
        1.5534675e-13,
    ]
    coefficients_b = [6.8123e3, -5.1351e1, 1.1522e-1, -3.0493e-5, -1.0924e-7]
    chi = 1.0 / (1.0 + np.exp(-1265.0 / temperature))
    pa = sum(
        coefficient * wavelength**power
        for power, coefficient in enumerate(coefficients_a)
    )
    pb = sum(
        coefficient * wavelength**power
        for power, coefficient in enumerate(coefficients_b)
    )
    expected = 1e-21 * (chi * pa + (1.0 - chi) * pb)
    actual, used, clamped = h2o2_cross_section(wavelength, temperature)
    assert float(actual) == pytest.approx(expected, rel=3e-12)
    assert float(used) == temperature
    assert not bool(clamped)


def test_h2o2_temperature_policy_domain_and_unattenuated_anchors() -> None:
    wavelength = np.array([121.567, 189.9, 260.0, 350.0, 350.1])
    sigma_199, used_199, clamped = h2o2_cross_section(wavelength, 199.0)
    sigma_200, used_200, _ = h2o2_cross_section(wavelength, 200.0)
    assert np.array_equal(sigma_199, sigma_200)
    assert np.all(used_199 == 200.0) and np.all(used_200 == 200.0)
    assert np.all(clamped)
    assert sigma_199[0] == sigma_199[1] == sigma_199[-1] == 0.0
    with pytest.raises(ValueError, match="above 400"):
        h2o2_cross_section(300.0, 400.0001)
    b = load_historical_uv_assets().backbone
    for temperature, expected in (
        (298.0, 9.483272946290916e-5),
        (200.0, 9.062306562957585e-5),
    ):
        sigma, _, _ = h2o2_cross_section(b.wavelength_nm, temperature)
        assert np.sum(b.solar_photon_irradiance_per_element * sigma) == pytest.approx(
            expected, rel=2e-12
        )
