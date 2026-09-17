"""Historical-2020 spherical-column UV attenuation and eight photolysis rates."""

from __future__ import annotations

from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import Mapping

import numpy as np
from numpy.typing import NDArray

from .background import load_baseline_background
from .background_types import BackgroundCase
from .local_types import LocalForcing
from .uv_assets import UVSpectralBackbone, load_historical_uv_assets
from .uv_cross_sections import (
    H2O2_LYMAN_ALPHA_SIGMA_CM2,
    h2o2_cross_section,
    h2o_channel_yields,
    h2o_cross_section,
)
from .uv_geometry import (
    CHEMISTRY_ALTITUDES_KM,
    SphericalPathGeometry,
    spherical_shell_paths,
)

FloatArray = NDArray[np.float64]
J_NAMES = (
    "JH",
    "J_SRC",
    "J_LYA",
    "J_O2_TOTAL",
    "J_O3_TOTAL",
    "J_H2O2",
    "J_H2O_A",
    "J_H2O_B",
)


def _freeze_array(value: object, shape: tuple[int, ...], name: str) -> FloatArray:
    array = np.array(value, dtype=np.float64, copy=True)
    if array.shape != shape or not np.all(np.isfinite(array)):
        raise ValueError(f"invalid {name}")
    if np.any(array < 0.0):
        raise ValueError(f"{name} must be non-negative")
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class SlantColumns:
    """Absorber columns from each chemistry target toward the Sun, cm^-2."""

    O: FloatArray  # noqa: E741 - scientific species name
    O2: FloatArray
    O3: FloatArray
    N2: FloatArray

    def __post_init__(self) -> None:
        for field in fields(self):
            object.__setattr__(
                self,
                field.name,
                _freeze_array(getattr(self, field.name), (51,), field.name),
            )


@dataclass(frozen=True)
class UVRadiationDiagnostics:
    geometry: SphericalPathGeometry
    columns_cm2: SlantColumns
    optical_depth: FloatArray
    attenuated_photon_flux: FloatArray
    J_H2O_REPRESENTED_TOTAL: FloatArray
    h2o2_temperature_K_used: FloatArray
    h2o2_T_clamped_to_200K: NDArray[np.bool_]
    J_H2O2_LYA_ABS_UPPER: FloatArray
    external_o3_mode: str
    provenance: Mapping[str, str]

    def __post_init__(self) -> None:
        for name in ("optical_depth", "attenuated_photon_flux"):
            object.__setattr__(
                self, name, _freeze_array(getattr(self, name), (51, 125), name)
            )
        for name in (
            "J_H2O_REPRESENTED_TOTAL",
            "h2o2_temperature_K_used",
            "J_H2O2_LYA_ABS_UPPER",
        ):
            object.__setattr__(
                self, name, _freeze_array(getattr(self, name), (51,), name)
            )
        clamped = np.array(self.h2o2_T_clamped_to_200K, dtype=np.bool_, copy=True)
        if clamped.shape != (51,):
            raise ValueError("h2o2_T_clamped_to_200K must contain 51 values")
        clamped.setflags(write=False)
        object.__setattr__(self, "h2o2_T_clamped_to_200K", clamped)
        if self.external_o3_mode not in ("baseline", "zero_above_109_km"):
            raise ValueError("invalid external_o3_mode")
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class UVPhotolysisProfile:
    """The eight M4C UV/VUV rates on the 50--100 km chemistry grid."""

    z_km: FloatArray
    JH: FloatArray
    J_SRC: FloatArray
    J_LYA: FloatArray
    J_O2_TOTAL: FloatArray
    J_O3_TOTAL: FloatArray
    J_H2O2: FloatArray
    J_H2O_A: FloatArray
    J_H2O_B: FloatArray
    illuminated: NDArray[np.bool_]
    diagnostics: UVRadiationDiagnostics

    def __post_init__(self) -> None:
        for name in ("z_km", *J_NAMES):
            object.__setattr__(
                self, name, _freeze_array(getattr(self, name), (51,), name)
            )
        illuminated = np.array(self.illuminated, dtype=np.bool_, copy=True)
        if illuminated.shape != (51,):
            raise ValueError("illuminated must contain 51 values")
        illuminated.setflags(write=False)
        object.__setattr__(self, "illuminated", illuminated)


def _shell_mean(node_density: object, name: str) -> FloatArray:
    nodes = np.asarray(node_density, dtype=np.float64)
    if nodes.shape != (151,) or not np.all(np.isfinite(nodes)) or np.any(nodes < 0.0):
        raise ValueError(f"invalid {name} node density")
    return 0.5 * (nodes[:-1] + nodes[1:])


def slant_columns(
    geometry: SphericalPathGeometry,
    *,
    O_cm3: object,  # noqa: E741 - scientific species name
    O2_cm3: object,
    O3_cm3: object,
    N2_cm3: object,
) -> SlantColumns:
    """Integrate arithmetic endpoint-mean shell densities along exact paths."""

    path_cm = geometry.path_length_km * 1.0e5

    def integrate(values: object, name: str) -> FloatArray:
        return path_cm @ _shell_mean(values, name)

    return SlantColumns(
        integrate(O_cm3, "O"),
        integrate(O2_cm3, "O2"),
        integrate(O3_cm3, "O3"),
        integrate(N2_cm3, "N2"),
    )


def optical_depth(columns: SlantColumns, backbone: UVSpectralBackbone) -> FloatArray:
    """Compute absorber-resolved Beer--Lambert optical depth."""

    tau = (
        columns.O[:, None] * backbone.sigma_O_cm2[None, :]
        + columns.O2[:, None] * backbone.sigma_O2_cm2[None, :]
        + columns.O3[:, None] * backbone.sigma_O3_cm2[None, :]
        + columns.N2[:, None] * backbone.sigma_N2_cm2[None, :]
    )
    if not np.all(np.isfinite(tau)) or np.any(tau < 0.0):
        raise FloatingPointError("invalid optical depth")
    return tau


def attenuated_photon_flux(
    backbone: UVSpectralBackbone,
    tau: object,
    illuminated: object,
) -> FloatArray:
    """Apply Beer--Lambert attenuation and exact solid-Earth shadowing."""

    optical = np.asarray(tau, dtype=np.float64)
    light = np.asarray(illuminated, dtype=np.bool_)
    if optical.shape != (51, 125) or light.shape != (51,):
        raise ValueError("invalid optical-depth or illumination shape")
    flux = backbone.solar_photon_irradiance_per_element[None, :] * np.exp(-optical)
    flux[~light] = 0.0
    return flux


def _compose_absorbers(
    case: BackgroundCase,
    dynamic_O_cm3: object,
    dynamic_O3_cm3: object,
    external_o3_mode: str,
) -> tuple[FloatArray, FloatArray]:
    oxygen = case.compose_radiative_atomic_oxygen(dynamic_O_cm3)
    ozone = np.array(case.compose_radiative_ozone(dynamic_O3_cm3), copy=True)
    if external_o3_mode == "zero_above_109_km":
        ozone[109:] = 0.0
    elif external_o3_mode != "baseline":
        raise ValueError("external_o3_mode must be baseline or zero_above_109_km")
    ozone.setflags(write=False)
    return oxygen, ozone


def compute_uv_photolysis(
    dynamic_O_cm3: object,
    dynamic_O3_cm3: object,
    sza_deg: float,
    *,
    background: BackgroundCase | None = None,
    external_o3_mode: str = "baseline",
) -> UVPhotolysisProfile:
    """Calculate the eight historical-2020 UV/VUV photolysis frequencies."""

    case = load_baseline_background() if background is None else background
    oxygen, ozone = _compose_absorbers(
        case, dynamic_O_cm3, dynamic_O3_cm3, external_o3_mode
    )
    geometry = spherical_shell_paths(sza_deg)
    columns = slant_columns(
        geometry,
        O_cm3=oxygen,
        O2_cm3=case.radiative.O2_model_cm3,
        O3_cm3=ozone,
        N2_cm3=case.radiative.N2_model_cm3,
    )
    assets = load_historical_uv_assets()
    backbone = assets.backbone
    tau = optical_depth(columns, backbone)
    flux = attenuated_photon_flux(backbone, tau, geometry.illuminated)
    wave = backbone.wavelength_nm

    j_o2_element = flux * backbone.sigma_O2_cm2[None, :]
    j_o3_element = flux * backbone.sigma_O3_cm2[None, :]
    mask_hartley = (wave > 210.0) & (wave < 310.0)
    mask_src = (wave >= 130.0) & (wave <= 175.0)
    jh = np.sum(j_o3_element[:, mask_hartley], axis=1)
    j_src = np.sum(j_o2_element[:, mask_src], axis=1)
    j_lya = j_o2_element[:, 27]
    j_o2_total = np.sum(j_o2_element, axis=1)
    j_o3_total = np.sum(j_o3_element, axis=1)

    sigma_h2o = h2o_cross_section(wave)
    yield_a, yield_b = h2o_channel_yields(wave)
    h2o_element = flux * sigma_h2o[None, :]
    j_h2o_a = np.sum(h2o_element * yield_a[None, :], axis=1)
    j_h2o_b = np.sum(h2o_element * yield_b[None, :], axis=1)
    j_h2o_total = np.sum(h2o_element, axis=1)

    temperature = case.chemical.T_K[:, None]
    sigma_h2o2, temperature_used, clamped = h2o2_cross_section(
        wave[None, :], temperature
    )
    j_h2o2 = np.sum(flux * sigma_h2o2, axis=1)
    j_h2o2_lya_upper = flux[:, 27] * H2O2_LYMAN_ALPHA_SIGMA_CM2

    diagnostics = UVRadiationDiagnostics(
        geometry=geometry,
        columns_cm2=columns,
        optical_depth=tau,
        attenuated_photon_flux=flux,
        J_H2O_REPRESENTED_TOTAL=j_h2o_total,
        h2o2_temperature_K_used=temperature_used[:, 0],
        h2o2_T_clamped_to_200K=clamped[:, 0],
        J_H2O2_LYA_ABS_UPPER=j_h2o2_lya_upper,
        external_o3_mode=external_o3_mode,
        provenance={
            "configuration": "historical_2020",
            "spectral_backbone": "Anqi sigma.mat (2017), exact 125 elements",
            "H2O_H2O2": "JPL Evaluation 18 / Publication 15-10 (2015)",
            "irradiance_convention": "photon irradiance per spectral element; no delta-lambda",
        },
    )
    return UVPhotolysisProfile(
        z_km=CHEMISTRY_ALTITUDES_KM,
        JH=jh,
        J_SRC=j_src,
        J_LYA=j_lya,
        J_O2_TOTAL=j_o2_total,
        J_O3_TOTAL=j_o3_total,
        J_H2O2=j_h2o2,
        J_H2O_A=j_h2o_a,
        J_H2O_B=j_h2o_b,
        illuminated=geometry.illuminated,
        diagnostics=diagnostics,
    )


def local_forcing_from_uv(
    profile: UVPhotolysisProfile,
    level_index: int,
    *,
    gA: float,
    gB: float,
    gIRA: float,
) -> LocalForcing:
    """Combine one M4C UV row with explicitly supplied, external g-factors."""

    if isinstance(level_index, bool) or not isinstance(level_index, (int, np.integer)):
        raise ValueError("level_index must be an integer")
    index = int(level_index)
    if not 0 <= index < 51:
        raise ValueError("level_index must be in [0, 50]")
    return LocalForcing(
        **{name: float(getattr(profile, name)[index]) for name in J_NAMES},
        gA=gA,
        gB=gB,
        gIRA=gIRA,
    )
