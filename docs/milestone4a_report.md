# Milestone 4A delivery report

Date: 2026-09-10

## Scope and baseline

- Accepted input: `tfm-photochem-milestone3.zip`
- Accepted input SHA256: `d5dac9f3d160b0d53a1fdc16b23b4c72b918c271466dfbe58d99c5a54a9d89ef`
- Package version: `0.4.0`
- Scope: static atmospheric background and prescribed profile infrastructure
- M4B status: **not started**

## Exact file delta from accepted M3

Modified (10):

- `README.md`
- `docs/architecture.md`
- `docs/historical_2020_local_closure.md`
- `docs/source_inventory.md`
- `docs/validation_report.md`
- `pyproject.toml`
- `src/tfm_photochem/historical_2020/__init__.py`
- `src/tfm_photochem/__init__.py`
- `tests/test_historical_2020_registry.py` (stop-boundary expectation only)
- `uv.lock`

Added (13):

- `docs/historical_2020_background.md`
- `docs/milestone4a_report.md`
- `scripts/generate_historical_2020_background.py`
- `scripts/validate_historical_2020_background.py`
- `src/tfm_photochem/assets/historical_2020/midlatitude_equinox_quiet_chemical_background.csv`
- `src/tfm_photochem/assets/historical_2020/midlatitude_equinox_quiet_metadata.json`
- `src/tfm_photochem/assets/historical_2020/midlatitude_equinox_quiet_radiative_background.csv`
- `src/tfm_photochem/assets/historical_2020/socrates_prescribed_vmr.csv`
- `src/tfm_photochem/historical_2020/background.py`
- `src/tfm_photochem/historical_2020/background_generation.py`
- `src/tfm_photochem/historical_2020/background_types.py`
- `src/tfm_photochem/historical_2020/prescribed_profiles.py`
- `tests/test_historical_2020_background.py`

Removed: none.

All six legacy production modules, both legacy assets, the M2 kinetics and
reaction registries, and all five M3 implementation modules (`local_types`,
`qssa`, `fluxes`, `stoichiometry`, `local_closure`) are byte-identical to the
accepted M3 ZIP. Only the public `historical_2020/__init__.py` export surface
was extended.

## Frozen assets

| Asset | Rows | SHA256 |
| --- | ---: | --- |
| `socrates_prescribed_vmr.csv` | 23 | `8985b4774b6e1aa91e3522758c7a33b652501601cdd167871afdc215474b4e01` |
| `midlatitude_equinox_quiet_radiative_background.csv` | 151 | `217fe7187c42a4ca8f590e1fa382ef815adffae6f5f1429816cea739f27c604f` |
| `midlatitude_equinox_quiet_chemical_background.csv` | 51 | `c1c115d840fa1b3115d7bcb7a1feca769b9dbbddd0faee5a2df0edadc4b5c291` |
| `midlatitude_equinox_quiet_metadata.json` | - | `5b4c53276b587141201b74116faf3210e3ce0ffa0de025e767fb944b25daa75a` |

Source PDF hashes:

- Li et al. 2020: `3bf92a0c36147e9c4f3d200ec3e37c2cbdf61143470cbd6c61f6075d98824df5`
- Brasseur & Solomon 2005: `e43cd39b21d4f3d4c401ceddbe72da8801443db3bffdcb600374304dda61ca22`
- Legacy sigma: `a98567c4f971721cec4197ad7ea17182e95df78c3a0eea880acb08fc6d560424`

## Exact generation contract

NRLMSISE-00 is called through `pymsis==0.12.0` with `version=0`, UTC
`2020-03-20T12:00:00Z`, latitude 45, longitude 0, F10.7=150, F10.7A=150,
daily Ap=4, `aps=[[4,4,4,4,4,4,4]]`, and an explicit 25-element option vector
of ones. Local solar time is 12 h. No driver is omitted, so no automatic
space-weather download occurs.

The generator converts native number density by 1e-6, sums exactly N2, O2, O,
He, H, Ar, and N for M, excludes anomalous O, and never reconstructs M from
mass density. `pymsis` NaN sentinels for unavailable low-altitude trace species
are transparent diagnostics and contribute zero to this sum.

## Numerical anchors

| z (km) | T (K) | M (molecule cm-3) | O3 reference VMR |
| ---: | ---: | ---: | ---: |
| 0 | 283.8648376464844 | 2.5719328316280975e19 | 3.8e-8 |
| 50 | 264.9381103515625 | 2.1204504413317356e16 | 2.971960976381563e-6 |
| 80 | 207.4347381591797 | 3.334677084390829e14 | 2.889707485137857e-7 |
| 100 | 185.60606384277344 | 1.281568097278211e13 | 3.1901806551266033e-6 |
| 150 | 742.3129272460938 | 5.0237509715755005e10 | 8.351742935579349e-11 |

| z (km) | H2O VMR | H2 VMR |
| ---: | ---: | ---: |
| 50 | 5.332492923133265e-6 | 3.3663344224407917e-7 |
| 80 | 2.891858967466243e-6 | 2.3983967056790553e-6 |
| 100 | 1.636061481548315e-7 | 3.2901899827150895e-6 |

At 150 km the independently evaluated last-two-knot O3 formula gives
`8.351742935579349e-11`, positive and without a floor. Tests also hard-code
the four handoff source rows and a synthetic geometric-mean interpolation that
a linear-in-VMR implementation cannot pass.

## Composition and M3 evidence

A synthetic dynamic vector `[1,...,51]` is reproduced exactly at 50--100 km:
the endpoints are 1 at 50 km and 51 at 100 km. The 49 and 101 km reference
values remain bitwise unchanged. Independent error tests cover wrong length,
negative values, NaN, and infinity.

M3 `LocalBackground` construction is checked at 50, 80, and 100 km. A full M3
closure smoke evaluation at 80 km returns finite tendencies. The accepted M3
validator retains the exact algebraic values, residuals, 54 fluxes, 49
contribution rows, and tendencies recorded at M3 closure.

## Verification results

- Full suite: `373 passed, 13 subtests passed`
- `validate_legacy.py`: PASS; accepted arrays and sigma hash unchanged
- `validate_local_closure.py`: PASS; accepted M3 regression unchanged
- `validate_historical_2020_background.py`: PASS; 151/51 nodes and all checks true
- Ruff 0.16.6: `All checks passed!`
- Bytecode compile: PASS
- `uv lock --check --offline`: PASS (18 packages resolved offline)
- Pinned full regeneration: radiative, chemical, and metadata byte-identical
- Wheel build: PASS; four M4A assets present and loadable without pymsis
- Clean wheel install outside source tree: PASS; version 0.4.0, 151/51 nodes,
  exact documented asset hashes, and `pymsis_imported=false`
- Sdist build: PASS; assets, tests, scripts, lockfile, and documentation present
- Extracted-sdist suite: `373 passed, 13 subtests passed`

The final ZIP, wheel, and sdist SHA256 values are reported alongside the
delivered artifact, avoiding self-referential hashes inside the sdist report.

## Limitations

1. The noon NRLMSISE-00 snapshot is static; no tides or diurnal atmospheric
   variation are represented.
2. SOCRATES H2O/H2/O3 are approximate annual/zonal/latitudinal climatologies,
   not observations or validation truth.
3. SOCRATES external O3 substitutes for unavailable versioned CMAM ozone and
   is not exact Li-2020 ozone provenance.
4. The O3 tail above 108.4 km is a closure convention requiring an M4B
   zero-tail sensitivity test.
5. The accepted M3 scalar closure performance debt (about 20.8--21.5 ms per
   altitude, roughly 1.06--1.10 s for a naive 51-level call) remains an M5A
   design requirement and was not refactored here.

## Ambiguity handled transparently

The handoff did not specify how to sum MSIS-00 fields that the wrapper exposes
as NaN sentinels below their valid species range. M4A treats only those
unavailable trace-species contributions as zero in M and preserves the native
NaN diagnostic fields. This is recorded in metadata and tested; no alternative
MSIS wrapper or generation was substituted.

## Roadmap review proposal (not implemented)

After M4A audit/closure, design M4B in a fresh handoff around historical
spectral inputs, spherical solar geometry, attenuation, the nine forcing
quantities, and the mandated upper-O3-tail sensitivity. Keep 51-level closure,
time integration, and performance work outside M4B unless separately approved.
