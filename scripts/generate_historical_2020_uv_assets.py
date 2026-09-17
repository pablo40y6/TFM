"""Generate the deterministic Milestone-4C historical UV source assets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat

SIGMA_SHA256 = "a98567c4f971721cec4197ad7ea17182e95df78c3a0eea880acb08fc6d560424"
JPL18_PDF_SHA256 = "149a4bab985402c67419e02ff8ca80202d1ba55f5383fbf69692e2184b68da08"
JPL20_PDF_SHA256 = "835496c8fd180b29ff9fc456e038dc8fd34e829e5f6e00346b0837ad71b4169c"
BACKBONE_FILENAME = "uv_spectral_backbone_2017.csv"
BACKBONE_METADATA_FILENAME = "uv_spectral_backbone_2017_metadata.json"
H2O_FILENAME = "jpl18_h2o_cross_sections_298k.csv"
H2O2_FILENAME = "jpl18_h2o2_cross_sections_298k.csv"
JPL_METADATA_FILENAME = "jpl18_uv_cross_sections_metadata.json"

H2O_TABLE_4B3 = (
    (121.0, 624.0),
    (121.5, 1276.0),
    (121.567, 1480.0),
    (122.0, 1689.0),
    (122.5, 826.0),
    (123.0, 283.0),
    (123.5, 589.0),
    (124.0, 1332.0),
    (124.5, 663.0),
    (125.0, 619.0),
    (125.5, 693.0),
    (126.0, 706.0),
    (126.5, 768.0),
    (127.0, 800.0),
    (127.5, 780.0),
    (128.0, 854.0),
    (128.5, 820.0),
    (129.0, 777.0),
    (129.5, 819.0),
    (130.0, 718.0),
    (130.5, 733.0),
    (131.0, 699.0),
    (131.5, 601.0),
    (132.0, 667.0),
    (132.5, 538.0),
    (133.0, 494.0),
    (133.5, 513.0),
    (134.0, 424.0),
    (134.5, 382.0),
    (135.0, 367.0),
    (135.5, 310.0),
    (136.0, 251.0),
    (136.5, 257.0),
    (137.0, 204.0),
    (137.5, 195.0),
    (138.0, 177.0),
    (138.5, 129.0),
    (139.0, 126.0),
    (139.5, 125.0),
    (140.0, 100.0),
    (141.0, 82.3),
    (142.0, 64.1),
    (143.0, 57.1),
    (144.0, 56.4),
    (145.0, 58.0),
    (146.0, 65.8),
    (147.0, 75.2),
    (148.0, 84.9),
    (149.0, 101.0),
    (150.0, 120.0),
    (151.0, 141.0),
    (152.0, 165.0),
    (153.0, 197.0),
    (154.0, 211.0),
    (155.0, 236.0),
    (156.0, 266.0),
    (157.0, 295.0),
    (158.0, 327.0),
    (159.0, 354.0),
    (160.0, 385.0),
    (161.0, 413.0),
    (162.0, 434.0),
    (163.0, 456.0),
    (164.0, 480.0),
    (165.0, 499.0),
    (166.0, 509.0),
    (167.0, 510.0),
    (168.0, 508.0),
    (169.0, 502.0),
    (170.0, 492.0),
    (171.0, 470.0),
    (172.0, 435.0),
    (173.0, 394.0),
    (174.0, 353.0),
    (175.0, 319.0),
    (176.0, 284.0),
    (177.0, 240.0),
    (178.0, 193.0),
    (179.0, 140.0),
    (180.0, 90.0),
    (181.0, 54.6),
    (182.0, 32.9),
    (183.0, 16.9),
    (184.0, 12.1),
    (185.0, 6.78),
    (186.0, 4.39),
    (187.0, 2.71),
    (188.0, 1.77),
    # JPL18 Table 4B-3 prints "199" here between 188 and 190. Historical_2020
    # implements 189 nm as a documented typographical correction; JPL20 is
    # corroboration only and is not the numerical source for this table.
    (189.0, 1.08),
    (190.0, 0.672),
    (191.0, 0.464),
    (192.0, 0.30),
    (193.0, 0.21),
    (194.0, 0.16),
    (195.0, 0.13),
    (196.0, 0.11),
    (197.0, 0.10),
    (198.0, 0.09),
)

H2O2_TABLE_4B5 = tuple(
    zip(
        range(190, 351, 5),
        (
            67.2,
            56.4,
            47.5,
            40.8,
            35.7,
            30.7,
            25.8,
            21.7,
            18.2,
            15.0,
            12.4,
            10.2,
            8.3,
            6.7,
            5.3,
            4.2,
            3.3,
            2.6,
            2.0,
            1.5,
            1.2,
            0.90,
            0.68,
            0.51,
            0.38,
            0.28,
            0.20,
            0.15,
            0.11,
            0.084,
            0.064,
            0.049,
            0.036,
        ),
        strict=True,
    )
)

H2O2_A = (
    6.4761e4,
    -9.2170972e2,
    4.535649,
    -4.4589016e-3,
    -4.035101e-5,
    1.6878206e-7,
    -2.652014e-10,
    1.5534675e-13,
)
H2O2_B = (6.8123e3, -5.1351e1, 1.1522e-1, -3.0493e-5, -1.0924e-7)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _numeric_csv(headers: tuple[str, ...], rows: list[tuple[object, ...]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(headers)
    for row in rows:
        writer.writerow(
            format(value, ".17g") if isinstance(value, float) else value
            for value in row
        )
    return stream.getvalue().encode("utf-8")


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build_assets(sigma_path: Path) -> dict[str, bytes]:
    sigma_bytes = sigma_path.read_bytes()
    if _sha256(sigma_bytes) != SIGMA_SHA256:
        raise ValueError("source sigma.mat SHA256 mismatch")
    raw = loadmat(sigma_path, squeeze_me=True)
    arrays = {
        name: np.asarray(raw[name], dtype=np.float64).reshape(-1)
        for name in ("wave", "irrad", "sO", "sO2", "sO3", "sN2")
    }
    if any(values.shape != (125,) for values in arrays.values()):
        raise ValueError("source sigma.mat arrays must each contain 125 values")
    if arrays["wave"][27] != 121.567:
        raise ValueError("source MATLAB element 28 must be exactly 121.567 nm")
    if not (arrays["wave"][20] == arrays["wave"][21] == 117.30308):
        raise ValueError("source duplicated 117.30308-nm rows were not preserved")

    backbone_rows = [
        (
            index + 1,
            arrays["wave"][index],
            arrays["irrad"][index],
            arrays["sO"][index],
            arrays["sO2"][index],
            arrays["sO3"][index],
            arrays["sN2"][index],
        )
        for index in range(125)
    ]
    backbone = _numeric_csv(
        (
            "source_matlab_index",
            "wavelength_nm",
            "solar_photon_irradiance_per_element",
            "sigma_O_cm2",
            "sigma_O2_cm2",
            "sigma_O3_cm2",
            "sigma_N2_cm2",
        ),
        backbone_rows,
    )
    h2o = _numeric_csv(
        ("wavelength_nm", "sigma_1e20_cm2", "sigma_cm2"),
        [
            (wavelength, scaled, scaled * 1.0e-20)
            for wavelength, scaled in H2O_TABLE_4B3
        ],
    )
    h2o2 = _numeric_csv(
        ("wavelength_nm", "sigma_1e20_cm2", "sigma_cm2"),
        [
            (float(wavelength), scaled, scaled * 1.0e-20)
            for wavelength, scaled in H2O2_TABLE_4B5
        ],
    )
    backbone_metadata = _json_bytes(
        {
            "configuration": "historical_2020",
            "description": (
                "baseline UV spectral backbone inherited from the validated "
                "2017 Chalmers asset"
            ),
            "derived_asset": BACKBONE_FILENAME,
            "derived_asset_sha256": _sha256(backbone),
            "duplicate_source_indices": [21, 22],
            "irradiance_operational_unit": (
                "photon cm^-2 s^-1 per tabulated spectral element"
            ),
            "lyman_alpha_source_matlab_index": 28,
            "row_count": 125,
            "source_asset": "assets/legacy_2017/sigma.mat",
            "source_asset_sha256": SIGMA_SHA256,
            "source_arrays": ["wave", "irrad", "sO", "sO2", "sO3", "sN2"],
            "wavelength_range_nm": [7.5, 360.0],
            "provenance_limitation": (
                "exact project-local 2017 arrays; not claimed as an exact "
                "Li-2020 or JPL18 spectrum"
            ),
        }
    )
    jpl_metadata = _json_bytes(
        {
            "configuration": "historical_2020",
            "source": {
                "title": "JPL Publication 15-10 / Evaluation 18",
                "year": 2015,
                "pdf_sha256": JPL18_PDF_SHA256,
                "transcription": (
                    "corrected machine-readable transcription plus rendered-page check"
                ),
            },
            "h2o": {
                "asset": H2O_FILENAME,
                "asset_sha256": _sha256(h2o),
                "printed_page": "4-43",
                "row_count": len(H2O_TABLE_4B3),
                "table": "4B-3",
                "temperature_K": 298.0,
                "wavelength_range_nm": [121.0, 198.0],
                "reduced_yields": {
                    "121<=lambda<147_nm": {"phi_A": 0.89, "phi_B": 0.11},
                    "147<=lambda<=198_nm": {"phi_A": 1.0, "phi_B": 0.0},
                },
                "reduced_yields_provenance": (
                    "historical_2020 reduced two-channel H2O yields, based on "
                    "the frozen Brasseur/JPL-informed model approximation; "
                    "not exact JPL18 quantum yields"
                ),
                "source_corrections": [
                    {
                        "id": "jpl18_h2o_table_4b3_199_to_189_nm",
                        "classification": "typographical correction",
                        "source": {
                            "title": "JPL Publication 15-10 / Evaluation 18",
                            "table": "4B-3",
                            "printed_page": "4-43",
                            "year": 2015,
                        },
                        "printed_entry": {
                            "wavelength_nm": 199.0,
                            "sigma_cm2": 1.08e-20,
                        },
                        "implemented_entry": {
                            "wavelength_nm": 189.0,
                            "sigma_cm2": 1.08e-20,
                        },
                        "evidence": [
                            "the printed row occurs between the 188 and 190 nm rows",
                            "Table 4B-3 states a nominal wavelength range of 121-198 nm",
                            "the table notes assign the surrounding 183-191 nm interval to one source",
                            "JPL Evaluation 20 prints 189 nm for the same cross section and is corroboration only",
                        ],
                        "numerical_source_configuration": {
                            "configuration": "historical_2020",
                            "numerical_source": (
                                "JPL Publication 15-10 / Evaluation 18 / Table 4B-3"
                            ),
                        },
                        "corroborating_source": {
                            "title": "JPL Publication 25-1 / Evaluation 20",
                            "table": "4B-2-2",
                            "printed_page": "4-40",
                            "pdf_sha256": JPL20_PDF_SHA256,
                            "entry_wavelength_nm": 189.0,
                            "entry_sigma_cm2": 1.08e-20,
                            "role": "corroboration only; not a numerical source",
                        },
                    }
                ],
            },
            "h2o2": {
                "asset": H2O2_FILENAME,
                "asset_sha256": _sha256(h2o2),
                "printed_page": "4-47",
                "row_count": len(H2O2_TABLE_4B5),
                "table_4B5_temperature_K": 298.0,
                "wavelength_range_nm": [190.0, 350.0],
                "table_4B6": {
                    "A": H2O2_A,
                    "B": H2O2_B,
                    "chi": "(1 + exp(-1265/T))^-1",
                    "expression": (
                        "sigma=1e-21*(chi*sum(A_n*lambda^n) + "
                        "(1-chi)*sum(B_n*lambda^n))"
                    ),
                    "temperature_range_K": [200.0, 400.0],
                    "wavelength_range_nm": [260.0, 350.0],
                },
                "temperature_policy": "T<200 K uses 200 K; T>400 K raises",
                "lyman_alpha_absorption_upper_bound": {
                    "production_channel": False,
                    "sigma_cm2": 9.8e-18,
                    "wavelength_nm": 121.567,
                },
            },
            "units": "cm^2 molecule^-1",
        }
    )
    return {
        BACKBONE_FILENAME: backbone,
        BACKBONE_METADATA_FILENAME: backbone_metadata,
        H2O_FILENAME: h2o,
        H2O2_FILENAME: h2o2,
        JPL_METADATA_FILENAME: jpl_metadata,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--sigma",
        type=Path,
        default=Path("src/tfm_photochem/assets/legacy_2017/sigma.mat"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("src/tfm_photochem/assets/historical_2020"),
    )
    parser.add_argument("--jpl18-pdf", type=Path)
    args = parser.parse_args()
    if args.jpl18_pdf is not None:
        if _sha256(args.jpl18_pdf.read_bytes()) != JPL18_PDF_SHA256:
            raise ValueError("JPL18 source PDF SHA256 mismatch")
    assets = build_assets(args.sigma)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in assets.items():
        target = args.output_dir / name
        if args.check:
            if not target.exists() or target.read_bytes() != data:
                raise SystemExit(f"asset mismatch: {target}")
        else:
            target.write_bytes(data)
        print(f"{name} {_sha256(data)}")


if __name__ == "__main__":
    main()
