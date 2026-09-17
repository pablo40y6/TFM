"""Optional deterministic generator for the frozen NRLMSISE-00 background."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .prescribed_profiles import (
    external_o3_vmr,
    prescribed_h2o_h2_vmr,
    source_asset_path,
)

CASE_NAME = "midlatitude_equinox_quiet"
RAD_FILENAME = f"{CASE_NAME}_radiative_background.csv"
CHEM_FILENAME = f"{CASE_NAME}_chemical_background.csv"
METADATA_FILENAME = f"{CASE_NAME}_metadata.json"
Z_RAD_KM = np.arange(0.0, 151.0, 1.0)
Z_CHEM_KM = np.arange(50.0, 101.0, 1.0)
MSIS_OPTION_NAMES = (
    "f107",
    "time_independent",
    "symmetrical_annual",
    "symmetrical_semiannual",
    "asymmetrical_annual",
    "asymmetrical_semiannual",
    "diurnal",
    "semidiurnal",
    "geomagnetic_activity",
    "all_ut_effects",
    "longitudinal",
    "mixed_ut_long",
    "mixed_ap_ut_long",
    "terdiurnal",
)
MSIS_OPTIONS = {name: 1 for name in MSIS_OPTION_NAMES}
MSIS_OPTION_VECTOR = [1] * 25


@dataclass(frozen=True)
class GenerationCase:
    datetime_utc: str = "2020-03-20T12:00:00Z"
    latitude_deg: float = 45.0
    longitude_deg: float = 0.0
    f107_previous_day: float = 150.0
    f107a_81day: float = 150.0
    daily_Ap: float = 4.0
    aps_vector: tuple[float, ...] = (4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0)
    model_version_argument: int = 0


def m3_to_cm3(native_m3: ArrayLike) -> NDArray[np.float64]:
    """Convert number density from m^-3 to molecule cm^-3."""

    return np.asarray(native_m3, dtype=np.float64) * 1.0e-6


def ordinary_neutral_total_cm3(
    n2: ArrayLike,
    o2: ArrayLike,
    o: ArrayLike,
    he: ArrayLike,
    h: ArrayLike,
    ar: ArrayLike,
    n: ArrayLike,
) -> NDArray[np.float64]:
    """Sum the seven ordinary neutral species; anomalous O is not an input."""

    arrays = np.broadcast_arrays(
        *[np.asarray(value, dtype=np.float64) for value in (n2, o2, o, he, h, ar, n)]
    )
    if any(np.any(~np.isfinite(value)) or np.any(value < 0.0) for value in arrays):
        raise ValueError("ordinary neutral number densities must be finite and non-negative")
    return np.add.reduce(arrays)


def build_msis_call(case: GenerationCase = GenerationCase()) -> dict[str, Any]:
    """Build the complete no-download model call, including every driver."""

    date = np.array([case.datetime_utc.removesuffix("Z")], dtype="datetime64[s]")
    return {
        "dates": date,
        "lons": np.array([case.longitude_deg], dtype=np.float64),
        "lats": np.array([case.latitude_deg], dtype=np.float64),
        "alts": Z_RAD_KM.copy(),
        "f107s": np.array([case.f107_previous_day], dtype=np.float64),
        "f107as": np.array([case.f107a_81day], dtype=np.float64),
        "aps": np.array([case.aps_vector], dtype=np.float64),
        "options": list(MSIS_OPTION_VECTOR),
        "version": case.model_version_argument,
    }


def run_pymsis(case: GenerationCase = GenerationCase()) -> NDArray[np.float64]:
    """Run only pymsis 0.12.0 and never request automatic space weather."""

    import pymsis
    from pymsis import msis

    if pymsis.__version__ != "0.12.0":
        raise RuntimeError(
            f"background generation requires pymsis==0.12.0, got {pymsis.__version__}"
        )
    output = msis.run(**build_msis_call(case))
    expected = (1, 1, 1, 151, 11)
    if output.shape != expected:
        raise RuntimeError(f"unexpected pymsis output shape {output.shape}, expected {expected}")
    return np.asarray(output[0, 0, 0, :, :], dtype=np.float64)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _format(value: object) -> str:
    if isinstance(value, (float, np.floating)):
        return format(float(value), ".17g")
    return str(value)


def _write_csv(path: Path, columns: list[str], rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(columns)
        writer.writerows([[_format(value) for value in row] for row in rows])


def generate_background_assets(output_dir: Path) -> dict[str, Path]:
    """Generate the two profile CSVs and deterministic metadata JSON."""

    output_dir.mkdir(parents=True, exist_ok=True)
    case = GenerationCase()
    raw = run_pymsis(case)
    native = raw[:, 1:9] * 1.0e-6
    # pymsis maps the MSIS-00 not-available sentinel to NaN. Such unavailable
    # trace-species contributions are zero for the ordinary-neutral sum while
    # the native diagnostic columns retain NaN verbatim for auditability.
    ordinary = np.nan_to_num(native[:, :7], nan=0.0)
    M = ordinary_neutral_total_cm3(*(ordinary[:, i] for i in range(7)))
    temperature = raw[:, 10]
    o2_model = 0.21 * M
    n2_model = 0.78 * M
    co2_model = 405.0e-6 * M
    o3_vmr = external_o3_vmr(Z_RAD_KM)
    o3_cm3 = o3_vmr * M

    rad_columns = [
        "z_km",
        "T_K",
        "M_cm3",
        "O2_model_cm3",
        "N2_model_cm3",
        "CO2_model_cm3",
        "O3_socrates_reference_vmr",
        "O3_socrates_reference_cm3",
        "msis_mass_density_kg_m3",
        "msis_N2_native_cm3",
        "msis_O2_native_cm3",
        "msis_O_native_cm3",
        "msis_He_native_cm3",
        "msis_H_native_cm3",
        "msis_Ar_native_cm3",
        "msis_N_native_cm3",
        "msis_anomalous_O_native_cm3",
    ]
    rad_rows = [
        [
            Z_RAD_KM[i],
            temperature[i],
            M[i],
            o2_model[i],
            n2_model[i],
            co2_model[i],
            o3_vmr[i],
            o3_cm3[i],
            raw[i, 0],
            *native[i, :],
        ]
        for i in range(151)
    ]
    rad_path = output_dir / RAD_FILENAME
    _write_csv(rad_path, rad_columns, rad_rows)

    index = np.arange(50, 101)
    h2o_vmr, h2_vmr = prescribed_h2o_h2_vmr(Z_CHEM_KM)
    chem_columns = [
        "z_km",
        "T_K",
        "M_cm3",
        "O2_cm3",
        "N2_cm3",
        "CO2_cm3",
        "H2O_vmr",
        "H2O_cm3",
        "H2_vmr",
        "H2_cm3",
    ]
    chem_rows = [
        [
            Z_CHEM_KM[j],
            temperature[i],
            M[i],
            o2_model[i],
            n2_model[i],
            co2_model[i],
            h2o_vmr[j],
            h2o_vmr[j] * M[i],
            h2_vmr[j],
            h2_vmr[j] * M[i],
        ]
        for j, i in enumerate(index)
    ]
    chem_path = output_dir / CHEM_FILENAME
    _write_csv(chem_path, chem_columns, chem_rows)

    source_path = Path(str(source_asset_path()))
    metadata = {
        "configuration": "historical_2020",
        "case_name": CASE_NAME,
        "source_model": "NRLMSISE-00 / MSISE-00",
        "source_model_reference": "Picone, Hedin, Drob & Aikin (2002)",
        "generator_package": "pymsis",
        "generator_package_version": "0.12.0",
        "model_version_argument": 0,
        "datetime_utc": case.datetime_utc,
        "latitude_deg": case.latitude_deg,
        "longitude_deg": case.longitude_deg,
        "derived_local_solar_time_hours": 12.0,
        "f107_previous_day": case.f107_previous_day,
        "f107a_81day": case.f107a_81day,
        "daily_Ap": case.daily_Ap,
        "aps_vector": list(case.aps_vector),
        "ap_mode": "daily Ap",
        "msis_options": MSIS_OPTIONS,
        "msis_option_vector": MSIS_OPTION_VECTOR,
        "z_rad_definition": "numpy.arange(0.0, 151.0, 1.0); 151 profile nodes",
        "z_chem_definition": "numpy.arange(50.0, 101.0, 1.0); 51 levels",
        "number_density_conversion": "1 m^-3 = 1e-6 molecule cm^-3",
        "M_definition": "N2 + O2 + O + He + H + Ar + N; anomalous O excluded",
        "msis_unavailable_species_handling": (
            "pymsis MSIS-00 NaN sentinels contribute zero to M; diagnostic columns retain NaN"
        ),
        "fixed_vmr_O2": 0.21,
        "fixed_vmr_N2": 0.78,
        "fixed_vmr_CO2": 405.0e-6,
        "H2O_H2_source": (
            "Brasseur & Solomon (2005), Appendix 6 Tables A.6.1 and A.6.2.a; "
            "prescribed baseline climatological profiles"
        ),
        "O3_external_source": (
            "Brasseur & Solomon (2005), Appendix 6 Tables A.6.1 and A.6.2.c; "
            "M4A baseline external-O3 approximation"
        ),
        "O3_external_limitation": (
            "SOCRATES substitutes for unavailable versioned CMAM shielding ozone; "
            "it is not exact Li-2020 ozone provenance"
        ),
        "interpolation_method": "linear interpolation of log10(VMR) versus geometric z",
        "O3_upper_extrapolation_method": (
            "last two positive knots: (104.0 km, 3.0e-6), "
            "(108.4 km, 1.1e-6); no floor or clipping"
        ),
        "static_background_assumption": (
            "single noon snapshot held fixed during future 24 h chemistry integrations"
        ),
        "source_pdf_hashes": {
            "anqi2020.pdf": "3bf92a0c36147e9c4f3d200ec3e37c2cbdf61143470cbd6c61f6075d98824df5",
            "Aeronomy of the Middle Atmosphere_ Chemistry and Physics of the Stratosphere and Mesosphere.pdf": "e43cd39b21d4f3d4c401ceddbe72da8801443db3bffdcb600374304dda61ca22",
        },
        "generated_asset_sha256": {
            SOURCE_ASSET_NAME: _sha256(source_path),
            RAD_FILENAME: _sha256(rad_path),
            CHEM_FILENAME: _sha256(chem_path),
        },
    }
    metadata_path = output_dir / METADATA_FILENAME
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return {"radiative": rad_path, "chemical": chem_path, "metadata": metadata_path}


SOURCE_ASSET_NAME = "socrates_prescribed_vmr.csv"


def generation_environment() -> dict[str, object]:
    """Report the optional generation software without importing it at runtime."""

    try:
        import pymsis
    except ImportError:
        return {"available": False, "required_version": "0.12.0"}
    return {
        "available": True,
        "required_version": "0.12.0",
        "installed_version": pymsis.__version__,
    }
