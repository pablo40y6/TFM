"""Independent checks of complete-band diagnostic transfer additions."""

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from tfm_photochem.m4d_reconstruction import transfer
from tfm_photochem.m4d_reconstruction.cia import HistoricalCIA
from tfm_photochem.m4d_reconstruction.sources import Line
from tfm_photochem.m4d_reconstruction.spectroscopy import (
    K_B,
    SpectralSources,
    complex_sdv,
    complex_voigt,
)


def fixture(monkeypatch, pressure=0.001):
    lines = tuple(
        Line(
            iso,
            13000 + i * 0.5,
            1e-25,
            0.05,
            0.08,
            0,
            0.7,
            0,
            "b 0",
            "X 0",
            "",
            f"P{i + 1}P{i + 1} d",
            " " * 126 + "d" + " " * 33,
        )
        for i, iso in enumerate((1, 1, 2, 3))
    )
    grid = np.arange(160.0, 801.0, 20.0)
    sources = SpectralSources(
        grid,
        {iso: grid * iso for iso in (1, 2, 3)},
        np.array([[700.0, 1.0], [1500.0, 1.0]]),
    )
    factor = 1e6 * K_B * 296 / 101325
    o2 = pressure * 0.21 / factor
    shells = transfer.Atmosphere(
        np.array([0.0, 150.0]),
        np.array([296.0]),
        np.array([pressure]),
        np.array([pressure * 0.21]),
        np.array([o2]),
        np.array([o2 * 0.79 / 0.21]),
    )
    bg = SimpleNamespace(
        z_km=np.array([0.0, 150.0]),
        T_K=np.array([296.0] * 2),
        M_cm3=np.array([pressure / factor] * 2),
        O2_model_cm3=np.array([o2] * 2),
    )
    monkeypatch.setattr(transfer, "atmosphere", lambda step: shells)
    monkeypatch.setattr(
        transfer, "load_baseline_background", lambda: SimpleNamespace(radiative=bg)
    )
    drouin = {
        x.dipole_label: (0, 0, 0, 0.05, 0.7, 0.08, 0.7, 0, 0, 0, 0, 0.1)
        for x in lines
        if x.isotope == 1
    }
    return lines, sources, shells, drouin


def test_broadcast_sdv_matches_scalar_evaluations():
    delta = np.linspace(-0.1, 0.1, 45)[:, None]
    sigma = np.array([0.01, 0.02, 0.03])
    gamma = np.array([0.06, 0.03, 0.01])
    gamma2 = 0.1 * gamma
    actual = complex_sdv(delta, sigma, gamma, gamma2)
    expected = np.column_stack(
        [complex_sdv(delta[:, 0], s, g, g2) for s, g, g2 in zip(sigma, gamma, gamma2)]
    )
    assert np.array_equal(actual, expected)


def test_a1_full_population_and_rare_profiles_remain_classic(monkeypatch):
    lines, sources, shells, drouin = fixture(monkeypatch)
    advanced = transfer.VoigtColumn(lines, sources, shells, drouin=drouin)
    classic = transfer.VoigtColumn(lines, sources, shells)
    assert np.count_nonzero(advanced.gamma2) == 2
    assert np.array_equal(advanced.gamma[:, 2:], classic.gamma[:, 2:])
    assert np.array_equal(advanced.shift[:, 2:], classic.shift[:, 2:])
    nodes = np.array([lines[0].nu, lines[-1].nu, lines[0].nu + 3])
    exact = advanced.cross_section(nodes, exact=True)
    expected = np.zeros_like(exact)
    for i, x in enumerate(lines):
        detuning = nodes - x.nu - advanced.shift[0, i]
        profile = (
            complex_sdv(
                detuning,
                advanced.sigma[0, i],
                advanced.gamma[0, i],
                advanced.gamma2[0, i],
            )
            if x.isotope == 1
            else complex_voigt(detuning, advanced.sigma[0, i], advanced.gamma[0, i])
        )
        expected[:, 0] += sources.strengths((x,), 296)[0] * profile.real
    assert np.allclose(exact, expected, rtol=2e-15, atol=0)


def test_complete_a_transfer_zero_pressure_limit_shadow_and_order(monkeypatch):
    lines, sources, _, drouin = fixture(monkeypatch, pressure=0)
    cases = [(50.0, 0.0), (100.0, 180.0)]
    a0 = transfer.compute_classic_rates(lines, sources, cases)
    a1 = transfer.compute_classic_rates(lines, sources, cases, drouin=drouin)
    reverse = transfer.compute_classic_rates(
        tuple(reversed(lines)), sources, cases, drouin=drouin, exact=True
    )
    assert np.array_equal(a0["monomer"], a1["monomer"])
    assert np.allclose(a1["monomer"], reverse["monomer"], rtol=2e-15, atol=0)
    assert a1["monomer"][0] > 0 and a1["monomer"][1] == 0
    assert np.array_equal(a1["monomer"], a1["unattenuated"])


def test_cia_is_only_attenuation_and_cannot_create_excitation(monkeypatch):
    lines, sources, _, _ = fixture(monkeypatch)
    cia = HistoricalCIA(
        {t: np.array([[12000.0, 1e-46], [14000.0, 1e-46]]) for t in (253, 273, 296)}
    )
    cases = [(50.0, 0.0), (100.0, 180.0)]
    result = transfer.compute_classic_rates(lines, sources, cases, cia=cia)
    assert 0 < result["cia_nominal"][0] < result["monomer"][0]
    assert result["cia_nominal"][1] == 0
    zero = tuple(replace(x, sw=0) for x in lines)
    dark = transfer.compute_classic_rates(zero, sources, cases, cia=cia)
    assert all(
        np.all(value == 0) for key, value in dark.items() if key != "illuminated"
    )


def test_incomplete_drouin_mapping_fails(monkeypatch):
    lines, sources, shells, _ = fixture(monkeypatch)
    with pytest.raises(ValueError, match="missing principal"):
        transfer.VoigtColumn(lines, sources, shells, drouin={})
