"""Independent principal transfer limits and fail-closed scientific boundaries."""

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.special import voigt_profile

from tfm_photochem.m4d_reconstruction import a_band
from tfm_photochem.m4d_reconstruction.a_band import (
    APolicy,
    PrincipalA,
    PrincipalAColumn,
    compute_a_rates,
    compute_principal_a_rates,
)
from tfm_photochem.m4d_reconstruction.sources import Line, SourceError
from tfm_photochem.m4d_reconstruction.spectroscopy import (
    K_B,
    SpectralSources,
    complex_sdv,
    drouin_mixed_profile,
    mixing_y,
)
from tfm_photochem.m4d_reconstruction.transfer import Atmosphere


def model(policy=APolicy()):
    """Explicitly synthetic 91/70/21/59 identities, never historical line data."""
    lines, drouin, mixing = [], {}, {}
    for i in range(150):
        flag = "d" if i < 91 else "q"
        record = " " * 126 + flag + " " * 33
        quantum = f"P{i + 1}P{i + 1} d" if flag == "d" else f"Q {i} q"
        line = Line(
            1,
            13000 + i,
            1e-25,
            0.05,
            0.08,
            0,
            0.7,
            0,
            "b 0",
            "X 0",
            "",
            quantum,
            record,
        )
        lines.append(line)
        if flag == "d":
            drouin[line.dipole_label] = (0, 0, 0, 0.05, 0.7, 0.08, 0.7, 0, 0, 0, 0, 0.1)
            if i < 70:
                mixing[line.dipole_label] = (0.0, 0.0, 0.0, 0.0)
    t = np.arange(160.0, 801.0, 20.0)
    sources = SpectralSources(
        t, {iso: t * iso for iso in (1, 2, 3)}, np.array([[700.0, 1.0], [900.0, 1.0]])
    )
    return PrincipalA(tuple(lines), sources, drouin, mixing, policy)


@pytest.mark.parametrize("fraction", [1e-3, 1e-6, 1e-9])
def test_sdv_continuous_voigt_limit_against_scipy(fraction):
    nodes = np.linspace(-0.2, 0.2, 151)
    actual = complex_sdv(nodes, 0.01, 0.06, fraction * 0.06)
    expected = voigt_profile(nodes, 0.01, 0.06)
    assert np.max(np.abs(actual.real - expected)) / expected.max() < 2 * fraction


def test_zero_pressure_is_gaussian_for_every_population():
    m = model()
    lines = m.selected_lines
    nodes = np.array([line.nu for line in lines])
    actual = m.contributions(nodes, 296.0, 0.0, 0.0, owners=np.arange(150))
    sigma = (
        nodes / 299792458 * np.sqrt(1.380649e-23 * 296 / (31.98983 * 1.66053906660e-27))
    )
    expected = 1e-25 / (np.sqrt(2 * np.pi) * sigma)
    assert np.allclose(actual, expected, rtol=2e-15)


def test_balanced_mixed_pair_preserves_total_integrable_area():
    # Equal strengths/opposite Y cancel the 1/detuning dispersion tail.
    # This tests the physically summed area, not an individual divergent wing.
    def pair(nu):
        return drouin_mixed_profile(
            nu + 0.5, 0.01, 0.06, 0.006, -0.03, 1.0
        ) + drouin_mixed_profile(nu - 0.5, 0.01, 0.06, 0.006, 0.03, 1.0)

    area, _ = quad(pair, -np.inf, np.inf, epsabs=1e-9)
    assert area == pytest.approx(2.0, abs=2e-9)


def test_lm_low_temperature_envelope_and_off_diagnostic_are_explicit():
    m = model()
    m = replace(m, mixing={label: (0.2, -0.1, 0.07, -0.03) for label in m.mixing})
    y_clamp = m.parameters(180.0, 0.1, 0.021)[-1]
    y_linear = replace(m, policy=APolicy(low_temperature="linear")).parameters(
        180.0, 0.1, 0.021
    )[-1]
    y_zero = replace(m, policy=APolicy(low_temperature="zero")).parameters(
        180.0, 0.1, 0.021
    )[-1]
    y_off = replace(m, policy=APolicy(line_mixing=False)).parameters(400.0, 0.1, 0.021)[
        -1
    ]
    assert np.count_nonzero(y_clamp) == 70
    assert np.all(y_clamp[y_clamp != 0] == 0.2)
    assert np.all(y_linear[y_linear != 0] == pytest.approx(0.32))
    assert not np.any(y_zero) and not np.any(y_off)


@pytest.mark.parametrize("boundary", [200.0, 250.0, 296.0, 340.0])
def test_y_interpolation_continuity_and_exact_nodes(boundary):
    values = (0.2, -0.1, 0.07, -0.03)
    assert mixing_y(values, boundary) == values[[200, 250, 296, 340].index(boundary)]
    if boundary < 340:
        assert mixing_y(values, boundary + 1e-7) == pytest.approx(
            mixing_y(values, boundary), abs=1e-8
        )
    assert mixing_y(values, boundary - 1e-7) == pytest.approx(
        mixing_y(values, boundary), abs=1e-8
    )


def test_no_y_and_q_sensitivities_are_separate_population_bounds():
    base = model()
    assert len(base.selected_lines) == 150
    assert len(replace(base, policy=APolicy(include_no_y=False)).selected_lines) == 129
    assert (
        len(replace(base, policy=APolicy(include_quadrupoles=False)).selected_lines)
        == 91
    )
    assert (
        len(
            replace(
                base, policy=APolicy(include_no_y=False, include_quadrupoles=False)
            ).selected_lines
        )
        == 70
    )


def test_mapping_fails_on_missing_extra_or_duplicate_lines():
    m = model()
    for lines in (m.lines[:-1], m.lines[:-1] + (m.lines[0],)):
        with pytest.raises(SourceError):
            replace(m, lines=lines)
    with pytest.raises(SourceError, match="MAPPING BLOCKER"):
        replace(m, mixing={**m.mixing, "invented": (0, 0, 0, 0)})


def test_order_invariance_and_owner_decomposition():
    m = model()
    nodes = np.array([13000.0, 13000.1, 13040.0, 13149.0, 13250.0])
    expected = m.cross_section(nodes, 296.0, 0.4, 0.084)
    reverse = replace(m, lines=tuple(reversed(m.lines)))
    assert np.array_equal(expected, reverse.cross_section(nodes, 296.0, 0.4, 0.084))
    all_nodes = np.repeat(nodes, 150)
    owners = np.tile(np.arange(150), len(nodes))
    parts = m.contributions(all_nodes, 296.0, 0.4, 0.084, owners=owners).reshape(
        -1, 150
    )
    assert np.array_equal(expected, parts.sum(axis=1))
    assert np.all(expected > 0)  # includes a node 100 cm^-1 beyond the last line


def test_negative_summed_opacity_is_blocked_never_clipped():
    m = model()
    m = replace(m, mixing={label: (1e4,) * 4 for label in m.mixing})
    with pytest.raises(FloatingPointError, match="negative summed"):
        m.cross_section(np.array([12000.0]), 296.0, 1.0, 0.21)


def test_hot_active_shell_fails_but_unused_shell_has_zero_geometry_weight():
    shells = Atmosphere(
        np.array([0.0, 100.0, 150.0]),
        np.array([296.0, 400.0]),
        np.array([0.1, 0.01]),
        np.array([0.021, 0.0021]),
        np.ones(2),
        np.ones(2),
    )
    with pytest.raises(ValueError, match="shell 1.*DESIGN BLOCKER"):
        PrincipalAColumn(model(), shells)
    column = PrincipalAColumn(model(), shells, used_shells=np.array([True, False]))
    assert np.all(column.cross_section(np.array([13000.0])) > 0)
    diagnostic = PrincipalAColumn(model(APolicy(line_mixing=False)), shells)
    assert diagnostic.cross_section(np.array([13000.0])).shape == (1, 2)


def set_atmosphere(monkeypatch, oxygen=0.0):
    p = 1e-4 if oxygen else 0.0
    shells = Atmosphere(
        np.array([0.0, 150.0]),
        np.array([296.0]),
        np.array([p]),
        np.array([p * 0.21]),
        np.array([oxygen]),
        np.array([oxygen * 4]),
    )
    monkeypatch.setattr(a_band, "atmosphere", lambda step: shells)
    factor = 1e6 * K_B * 296 / 101325
    bg = SimpleNamespace(
        z_km=np.array([0.0, 150.0]),
        T_K=np.array([296.0, 296.0]),
        M_cm3=np.array([p / factor] * 2),
        O2_model_cm3=np.array([p * 0.21 / factor] * 2),
    )
    monkeypatch.setattr(
        a_band, "load_baseline_background", lambda: SimpleNamespace(radiative=bg)
    )


def test_principal_transfer_zero_column_and_shadow(monkeypatch):
    set_atmosphere(monkeypatch)
    result = compute_principal_a_rates(
        model(APolicy(line_mixing=False)),
        [(50.0, 0.0), (50.0, 180.0)],
        core_order=32,
        wing_order=4,
    )
    assert result["principal"][0] > 0
    assert np.array_equal(result["principal"], result["unattenuated"])
    assert result["principal"][1] == 0
    assert result["scope"].startswith("principal-only")
    assert not result["M4D_frozen"]


def test_principal_transfer_absorption_refinement_and_policy_consistency(monkeypatch):
    set_atmosphere(monkeypatch, oxygen=1e12)
    m = model(APolicy(line_mixing=False))
    result = compute_principal_a_rates(m, [(50.0, 0.0)], core_order=64, wing_order=8)
    refined = compute_principal_a_rates(
        m, [(50.0, 0.0)], core_order=128, wing_order=16, support=7.68
    )
    assert 0 < result["principal"][0] < result["unattenuated"][0]
    assert result["principal"][0] == pytest.approx(refined["principal"][0], rel=1e-3)
    # At exactly zero pressure every line has equal strength and temperature;
    # an omission must change excitation as well as attenuation.
    set_atmosphere(monkeypatch)
    base = compute_principal_a_rates(m, [(50.0, 0.0)], core_order=32, wing_order=4)
    no_q = compute_principal_a_rates(
        replace(m, policy=APolicy(line_mixing=False, include_quadrupoles=False)),
        [(50.0, 0.0)],
        core_order=32,
        wing_order=4,
    )
    assert 0 < no_q["principal"][0] < base["principal"][0]
    assert no_q["selected_lines"] == 91


def test_full_a_has_no_unsourced_galatry_or_voigt_fallback():
    with pytest.raises(SourceError, match="SOURCE CONVENTION BLOCKER.*Galatry"):
        compute_a_rates()


def test_nominal_lm_transfer_has_no_inferred_normalization(monkeypatch):
    set_atmosphere(monkeypatch)
    with pytest.raises(SourceError, match="Table-22 Y unit annotation"):
        compute_principal_a_rates(model(), [(50.0, 0.0)])


@pytest.mark.parametrize(
    "sigma,gamma,gamma2",
    [(np.nan, 0.1, 0), (0.01, np.inf, 0), (0.01, 0.1, np.nan), (0.01, 0.1, 0.1)],
)
def test_nonfinite_and_nonphysical_sdv_parameters_rejected(sigma, gamma, gamma2):
    with pytest.raises(ValueError):
        complex_sdv(np.array([0.0]), sigma, gamma, gamma2)
