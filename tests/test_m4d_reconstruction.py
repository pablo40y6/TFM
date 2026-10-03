"""M4D identity failures, physics limits and independent profile/geometry checks."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.special import roots_genlaguerre

from tfm_photochem.historical_2020 import spherical_shell_paths
from tfm_photochem.m4d_reconstruction.cia import HistoricalCIA, temperature_weights
from tfm_photochem.m4d_reconstruction.mapping import (
    source_number,
    supplement_label,
    unique_rows,
)
from tfm_photochem.m4d_reconstruction.sources import (
    Line,
    SourceError,
    parse_line,
    verified_bytes,
)
from tfm_photochem.m4d_reconstruction.spectroscopy import (
    SpectralSources,
    classic_parameters,
    complex_sdv,
    complex_voigt,
    doppler_sigma,
    drouin_mixed_profile,
    drouin_parameters,
    mixing_y,
    principal_a_cross_section,
)
from tfm_photochem.m4d_reconstruction.transfer import (
    Atmosphere,
    VoigtColumn,
    cia_path_coefficients,
    compute_classic_rates,
    path_lengths,
    target_quadrature,
)


def synthetic_lines():
    lines = []
    for index in range(6):
        lines.append(
            Line(
                1 + index % 3,
                7800 + index * 5,
                1e-25 * (1 + index),
                0.05,
                0.08,
                20 * index,
                0.7,
                -0.005,
                "a 0",
                "X 0",
                "",
                f"Q {index}",
                " " * 160,
            )
        )
    return tuple(lines)


def synthetic_sources():
    temperatures = np.arange(160.0, 341.0, 20.0)
    return SpectralSources(
        temperatures,
        {iso: temperatures * iso for iso in (1, 2, 3)},
        np.array([[600.0, 1.2], [800.0, 1.2], [1500.0, 0.4]]),
    )


def test_wrong_raw_source_fails_before_parsing(monkeypatch):
    path = Path("guest1593878592.txt")
    monkeypatch.setattr(Path, "read_bytes", lambda self: b"unverified historical data")
    with pytest.raises(SourceError, match="SOURCE MATERIALIZATION BLOCKER"):
        verified_bytes(path, path.name)


@pytest.mark.parametrize("record", [" " * 159, " " * 161, " 81" + " " * 157])
def test_malformed_records_are_never_skipped(record):
    with pytest.raises(SourceError):
        parse_line(record)


def test_duplicate_identity_fails_even_with_equal_values():
    with pytest.raises(SourceError, match="duplicate/ambiguous"):
        unique_rows([("P1P1", (1,)), ("P1P1", (1,))], "source")


@pytest.mark.parametrize(
    "first,second,expected",
    [
        ("P34", "Q34", "P35Q34"),
        ("R2", "Q2", "R1Q2"),
        ("R35", "R35", "R35R35"),
        ("P1", "P1", "P1P1"),
    ],
)
def test_spectroscopic_supplement_conversion(first, second, expected):
    assert supplement_label(first, second) == expected


def test_invalid_supplement_identity_rejected():
    with pytest.raises(SourceError):
        supplement_label("R3", "Q2")


def test_uncertainty_text_preserves_published_mean():
    assert source_number("−3.9E-06(1)") == -3.9e-6
    assert source_number("0.05977(11)") == 0.05977
    with pytest.raises(SourceError):
        source_number("0.05 missing")


def test_requested_broadening_formula_has_no_extra_air_fraction():
    line = synthetic_lines()[0]
    gamma, shift = classic_parameters((line,), 296, 1, 0.21)
    assert gamma[0] == pytest.approx(0.05 * 0.79 + 0.08 * 0.21)
    assert shift[0] == -0.005
    assert classic_parameters((line,), 296, 1, 0.21, False)[1][0] == 0
    assert (
        classic_parameters((line,), 296, 1, 0.21, diluent="branch_air_only")[0][0]
        == 0.05
    )


@pytest.mark.parametrize(
    "t,p,po2", [(0, 1, 0.2), (296, -0.1, 0), (296, 1, 1.1), (np.nan, 1, 0.2)]
)
def test_invalid_shells_fail(t, p, po2):
    with pytest.raises(ValueError):
        classic_parameters(synthetic_lines(), t, p, po2)


def test_partition_scaling_and_no_second_abundance():
    sources = synthetic_sources()
    lines = synthetic_lines()
    assert np.array_equal(
        sources.strengths(lines, 296), np.array([line.sw for line in lines])
    )
    for isotope in (1, 2, 3):
        assert sources.partition(296, isotope) == pytest.approx(296 * isotope)


def test_solar_photon_jacobian_matches_independent_si_conversion():
    source = synthetic_sources()
    wavelength = 762.0
    nu = 1e7 / wavelength
    expected = (
        1.2 * wavelength * 1e-9 / (6.62607015e-34 * 299792458) / 1e4 * 1e7 / nu**2
    )
    assert source.photons(np.array([nu]))[0] == pytest.approx(expected, rel=1e-14)
    with pytest.raises(ValueError):
        source.photons(np.array([1.0]))


@pytest.mark.parametrize("gamma", [0.0, 0.001, 0.05])
def test_sdv_voigt_limit(gamma):
    nodes = np.linspace(-0.1, 0.1, 121)
    assert np.array_equal(
        complex_sdv(nodes, 0.01, gamma, 0), complex_voigt(nodes, 0.01, gamma)
    )


@pytest.mark.parametrize("speed", [0.05, 0.1, 0.2])
def test_sdv_against_independent_maxwell_speed_integral(speed):
    sigma, gamma = 0.01, 0.06
    detuning = np.array([-0.07, -0.01, 0, 0.01, 0.07])
    x, weights = roots_genlaguerre(80, 0.5)
    width = sigma * np.sqrt(2)
    a = gamma + speed * gamma * (x[:, None] - 1.5) - 1j * detuning
    b = 1j * width * np.sqrt(x[:, None])
    directional_mean = np.log((a + b) / (a - b)) / (2 * b)
    independent = 2 / (np.pi**1.5) * (weights @ directional_mean)
    assert np.allclose(
        complex_sdv(detuning, sigma, gamma, speed * gamma),
        independent,
        rtol=2e-12,
        atol=1e-12,
    )


def test_drouin_mixing_zero_limits_and_pressure_scaling():
    nodes = np.linspace(-0.15, 0.15, 401)
    sigma, gamma, gamma2 = 0.01, 0.06, 0.006
    base = complex_sdv(nodes, sigma, gamma, gamma2)
    assert np.array_equal(
        drouin_mixed_profile(nodes, sigma, gamma, gamma2, 0.0, 0.8),
        base.real,
    )
    assert np.array_equal(
        drouin_mixed_profile(nodes, sigma, gamma, gamma2, 0.35, 0.0),
        base.real,
    )
    mixed = drouin_mixed_profile(nodes, sigma, gamma, gamma2, -0.2, 0.7)
    assert np.allclose(mixed, base.real - 0.14 * base.imag, rtol=2e-15, atol=1e-15)


def test_drouin_first_order_mixing_is_dispersion_odd_about_line_centre():
    nodes = np.linspace(-0.2, 0.2, 1001)
    base = complex_sdv(nodes, 0.01, 0.06, 0.006)
    mixed = drouin_mixed_profile(nodes, 0.01, 0.06, 0.006, 0.3, 0.8)
    correction = mixed - base.real
    assert np.allclose(correction, -correction[::-1], rtol=2e-12, atol=2e-15)
    # First-order mixing redistributes an isolated line; its symmetric
    # principal-value area correction is zero.
    assert abs(np.sum(correction)) < 1e-12


@pytest.mark.parametrize("pressure,y", [(-1e-3, 0.1), (np.nan, 0.1), (1.0, np.nan)])
def test_invalid_drouin_line_mixing_controls_fail(pressure, y):
    with pytest.raises(ValueError):
        drouin_mixed_profile(np.array([0.0]), 0.01, 0.06, 0.006, y, pressure)


def _record_with_flag(flag):
    chars = list(" " * 160)
    chars[126] = flag
    return "".join(chars)


def test_principal_a_cross_section_dispatches_d_and_q_profiles():
    base = synthetic_lines()[0]
    dline = replace(
        base,
        isotope=1,
        nu=13100.0,
        sw=2e-25,
        elower=10.0,
        upper="b 0",
        lower="X 0",
        local_lower="P1P1 d",
        record=_record_with_flag("d"),
    )
    qline = replace(
        base,
        isotope=1,
        nu=13101.0,
        sw=3e-25,
        elower=20.0,
        upper="b 0",
        lower="X 0",
        local_lower="Q1",
        record=_record_with_flag("q"),
    )
    lines = (dline, qline)
    row = (13100.0, 1.0, 10.0, 0.05, 0.7, 0.08, 0.6, 0.0, 0.0, 0.0, 0.0, 0.1)
    drouin = {"P1P1": row}
    mixing = {"P1P1": (0.01, 0.02, 0.03, 0.04)}
    nodes = np.linspace(13099.8, 13101.2, 301)
    sources = synthetic_sources()
    p, po2 = 0.7, 0.14

    actual = principal_a_cross_section(
        nodes, lines, sources, drouin, mixing, 296.0, p, po2
    )
    sigma = doppler_sigma(lines, 296.0)
    gd, gd2, sd = drouin_parameters(row, 296.0, p)
    expected = dline.sw * drouin_mixed_profile(
        nodes - dline.nu - sd, sigma[0], gd, gd2, 0.03, p
    )
    gq, sq = classic_parameters((qline,), 296.0, p, po2)
    expected += qline.sw * complex_voigt(
        nodes - qline.nu - sq[0], sigma[1], gq[0]
    ).real
    assert np.allclose(actual, expected, rtol=2e-15, atol=0)


def test_principal_a_cross_section_uses_zero_y_when_table22_is_absent():
    line = replace(
        synthetic_lines()[0],
        isotope=1,
        nu=13100.0,
        upper="b 0",
        lower="X 0",
        local_lower="R45R45 d",
        record=_record_with_flag("d"),
    )
    row = (13100.0, 1.0, 0.0, 0.05, 0.7, 0.08, 0.6, 0.0, 0.0, 0.0, 0.0, 0.1)
    nodes = np.linspace(13099.9, 13100.1, 101)
    actual = principal_a_cross_section(
        nodes, (line,), synthetic_sources(), {"R45R45": row}, {}, 296.0, 0.5, 0.1
    )
    sigma = doppler_sigma((line,), 296.0)[0]
    gamma, gamma2, shift = drouin_parameters(row, 296.0, 0.5)
    expected = line.sw * complex_sdv(
        nodes - line.nu - shift, sigma, gamma, gamma2
    ).real
    assert np.allclose(actual, expected, rtol=2e-15, atol=0)


def test_principal_a_cross_section_fails_closed_on_missing_drouin_mapping():
    line = replace(
        synthetic_lines()[0],
        isotope=1,
        upper="b 0",
        lower="X 0",
        local_lower="P1P1 d",
        record=_record_with_flag("d"),
    )
    with pytest.raises(SourceError, match="Drouin row missing"):
        principal_a_cross_section(
            np.array([line.nu]),
            (line,),
            synthetic_sources(),
            {},
            {},
            296.0,
            0.5,
            0.1,
        )


def test_profiles_recover_unit_area():
    for function in (
        lambda nu: complex_voigt(nu, 0.01, 0.06).real,
        lambda nu: complex_sdv(nu, 0.01, 0.06, 0.006).real,
    ):
        area, _ = quad(function, -np.inf, np.inf, epsabs=1e-9)
        assert area == pytest.approx(1, abs=2e-9)


@pytest.mark.parametrize("temperature", [200.0, 250.0, 296.0, 340.0])
def test_y_source_nodes_exact(temperature):
    values = (0.1, 0.2, 0.3, 0.4)
    assert (
        mixing_y(values, temperature) == values[[200, 250, 296, 340].index(temperature)]
    )


def test_y_source_envelope_and_fail_closed_temperature():
    assert mixing_y((0.1, 0.2, 0.3, 0.4), 180) == 0.1
    assert mixing_y((0.1, 0.2, 0.3, 0.4), 180, "linear") == pytest.approx(0.06)
    assert mixing_y((0.1, 0.2, 0.3, 0.4), 180, "zero") == 0
    with pytest.raises(ValueError, match="DESIGN BLOCKER"):
        mixing_y((0.1, 0.2, 0.3, 0.4), 341)


@pytest.mark.parametrize("sza", [0.0, 60.0, 85.0, 89.0, 89.9, 95.0, 99.0])
def test_refined_geometry_aggregates_to_accepted_m4c(sza):
    edges = np.arange(0, 150.0625, 0.125)
    accepted = spherical_shell_paths(sza)
    for i, height in enumerate(range(50, 101)):
        illuminated, path = path_lengths(height, sza, edges)
        assert illuminated == accepted.illuminated[i]
        assert np.allclose(
            path.reshape(150, 8).sum(axis=1),
            accepted.path_length_km[i],
            rtol=1e-10,
            atol=1e-9,
        )


def test_illuminated_tangent_and_immediately_shadowed():
    sza = 180 - np.rad2deg(np.arcsin(6370 / (6370 + 100)))
    edges = np.arange(0, 150.125, 0.125)
    assert path_lengths(100, sza, edges)[0]
    illuminated, path = path_lengths(100, sza + 1e-7, edges)
    assert not illuminated
    assert np.array_equal(path, np.zeros_like(path))


def test_cia_historical_nodes_clamp_and_raw_noise_policy():
    grid = np.array([7500.0, 8000.0, 8500.0])
    cia = HistoricalCIA(
        {t: np.column_stack([grid, [1e-45, -1e-48, 2e-45]]) for t in (253, 273, 296)}
    )
    assert np.all(cia.at_nodes(np.array([8000.0])) == 0)
    assert np.all(cia.at_nodes(np.array([8000.0]), False) < 0)
    with pytest.raises(ValueError, match="support exceeded"):
        cia.at_nodes(np.array([7499.0]))
    weights = temperature_weights(
        np.array([180.0, 253.0, 263.0, 273.0, 284.5, 296.0, 400.0])
    )
    assert np.array_equal(weights[[0, 1]], [[1, 0, 0], [1, 0, 0]])
    assert np.array_equal(weights[[5, 6]], [[0, 0, 1], [0, 0, 1]])
    assert np.all(weights.sum(axis=1) == 1)


def test_all_absorbers_retained_and_moment_evaluator_matches_exact():
    lines = synthetic_lines()
    shells = Atmosphere(
        np.arange(4.0),
        np.array([190.0, 253.0, 296.0]),
        np.array([1e-5, 0.1, 1.0]),
        np.array([0.21e-5, 0.021, 0.21]),
        np.ones(3),
        np.ones(3),
    )
    column = VoigtColumn(lines, synthetic_sources(), shells)
    # Far beyond the entire band: a cutoff would incorrectly return zero.
    nodes = np.array([7700.0, 7798.0, 7800.0, 7805.1, 7825.0, 7900.0])
    exact = column.cross_section(nodes, exact=True)
    fast = column.cross_section(nodes, order=10)
    assert np.all(exact > 0)
    assert np.allclose(fast, exact, rtol=2e-11, atol=0)
    reversed_column = VoigtColumn(tuple(reversed(lines)), synthetic_sources(), shells)
    assert np.allclose(
        reversed_column.cross_section(nodes, exact=True), exact, rtol=3e-15
    )


def test_target_quadrature_not_empirically_renormalized():
    line = replace(synthetic_lines()[0], nu=7800.0)
    nodes, weights, owners = target_quadrature((line,), 128, 32, 3.84)
    area = np.sum(complex_voigt(nodes - line.nu, 0.01, 0.001).real * weights)
    assert owners.shape == weights.shape
    assert 0.999 < area < 1
    assert abs(area - 1) > 1e-5


def test_entirely_shadowed_rate_request_is_exactly_zero():
    result = compute_classic_rates(
        synthetic_lines(), synthetic_sources(), [(50.0, 180.0), (100.0, 180.0)]
    )
    assert not np.any(result["illuminated"])
    for key in ("monomer", "unattenuated"):
        assert np.array_equal(result[key], np.zeros(2))


@pytest.mark.parametrize("with_cia", [False, True])
def test_zero_absorber_column_recovers_same_quadrature_unattenuated_rate(
    monkeypatch, with_cia
):
    from tfm_photochem.m4d_reconstruction import transfer

    empty_column = Atmosphere(
        np.array([0.0, 150.0]),
        np.array([264.0]),
        np.zeros(1),
        np.zeros(1),
        np.zeros(1),
        np.zeros(1),
    )
    monkeypatch.setattr(transfer, "atmosphere", lambda step: empty_column)
    cia = (
        HistoricalCIA(
            {t: np.array([[7500.0, 1e-45], [8500.0, 1e-45]]) for t in (253, 273, 296)}
        )
        if with_cia
        else None
    )
    result = compute_classic_rates(
        synthetic_lines(), synthetic_sources(), [(50.0, 0.0), (50.0, 95.0)], cia=cia
    )
    assert np.all(result["unattenuated"] > 0)
    assert np.array_equal(result["monomer"], result["unattenuated"])
    for key in result:
        if key.startswith("cia_"):
            assert np.array_equal(result[key], result["unattenuated"])


def test_cia_uses_oxygen_times_total_diluent_not_oxygen_squared():
    shells = Atmosphere(
        np.array([0.0, 150.0]),
        np.array([273.0]),
        np.ones(1),
        np.ones(1),
        np.array([2.0]),
        np.array([8.0]),
    )
    nominal, measured, outside = cia_path_coefficients(shells, [(50.0, 0.0)])
    # Vertical path is 100 km; density product is 2*(2+8), not 2*2.
    assert np.array_equal(nominal, [[0, 100 * 1e5 * 20, 0]])
    assert np.array_equal(measured, nominal)
    assert np.array_equal(outside, np.zeros(1))
