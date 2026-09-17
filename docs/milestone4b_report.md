# Milestone 4B-R2 delivery report

Date: 2026-09-10

## Baseline and scope

- Accepted input: `tfm-photochem-milestone4a.zip`
- Verified input SHA256:
  `d1a68e6344710cd8ae6543f12081cde55355f23849ea73b9724d9e49156fbc12`
- First M4B audit artifact: `tfm-photochem-milestone4b.zip`
- Verified first-M4B SHA256:
  `c79273d9938108209d07a3786429afbc06127b0c6c5260e4dac062633b966d37`
- Output package version: `0.4.2`
- Scope: corrective odd-oxygen photolysis bookkeeping and eleven-field
  injected-forcing contract only. R2 adds the missing gross spectral-subset
  consistency invariant; it does not redesign the accepted partition.

No radiation was implemented. There is no new solar spectrum, cross-section
asset, SZA, ray geometry, optical depth, Beer--Lambert calculation, HITRAN
handling, column RHS, time integration, or M4C/M4D work.

## Exact delta from first M4B

No file was added or removed. Exactly these 14 files changed:

- `README.md`
- `pyproject.toml`
- `uv.lock`
- `src/tfm_photochem/__init__.py`
- `src/tfm_photochem/historical_2020/__init__.py`
- `src/tfm_photochem/historical_2020/photolysis_budget.py`
- `tests/test_odd_oxygen_photolysis_budget.py`
- `scripts/validate_odd_oxygen_photolysis_budget.py`
- `docs/architecture.md`
- `docs/historical_2020_local_closure.md`
- `docs/historical_2020_odd_oxygen.md`
- `docs/historical_2020_reactions.md`
- `docs/validation_report.md`
- `docs/milestone4b_report.md`

The other 50 package files are byte-identical to the first M4B artifact.

## Exact delta from accepted M4A

Added:

- `src/tfm_photochem/historical_2020/photolysis_budget.py`
- `tests/test_odd_oxygen_photolysis_budget.py`
- `scripts/validate_odd_oxygen_photolysis_budget.py`
- `docs/historical_2020_odd_oxygen.md`
- `docs/milestone4b_report.md`

Changed:

- `README.md`
- `pyproject.toml`
- `uv.lock`
- `src/tfm_photochem/__init__.py`
- `src/tfm_photochem/historical_2020/__init__.py`
- `src/tfm_photochem/historical_2020/fluxes.py`
- `src/tfm_photochem/historical_2020/local_closure.py`
- `src/tfm_photochem/historical_2020/local_types.py`
- `src/tfm_photochem/historical_2020/reactions.py`
- `src/tfm_photochem/historical_2020/stoichiometry.py`
- `tests/test_historical_2020_background.py`
- `tests/test_historical_2020_local_closure.py`
- `tests/test_historical_2020_qssa.py`
- `scripts/validate_local_closure.py`
- `docs/architecture.md`
- `docs/historical_2020_local_closure.md`
- `docs/historical_2020_reactions.md`
- `docs/historical_2020_topology.md`
- `docs/source_inventory.md`
- `docs/validation_report.md`

No file was removed. The M3 QSSA and kinetics implementation files are
byte-identical to M4A:

| File | M4A SHA256 | M4B SHA256 |
| --- | --- | --- |
| `qssa.py` | `0587b1a0d06a219e0cb308b652223b5e8b4e374d58455420b6e1bac46ae895f2` | same |
| `kinetics.py` | `946cde786e641e7cda713dd7a3e26673f2aa138b77cf3c6de4af1208caa6523a` | same |

## Corrective chemistry contract

Exact `LocalForcing` order, all in `s^-1`:

```text
JH, J_SRC, J_LYA, J_O2_TOTAL, J_O3_TOTAL,
J_H2O2, J_H2O_A, J_H2O_B, gA, gB, gIRA
```

Partition formulas:

```text
J2_star   = J_SRC + 0.44*J_LYA
J2_ground = J_O2_TOTAL - J2_star
J3_star   = 0.9*JH
J3_ground = J_O3_TOTAL - J3_star
```

The consistency tolerance is `64*sys.float_info.epsilon` relative to the
larger compared rate, with `sys.float_info.min` as the zero scale floor. R2
validates the gross parent-photodissociation subsets first:

```text
J_O3_TOTAL >= JH
J_O2_TOTAL >= J_SRC + J_LYA
```

This is separate from the existing represented-excited-channel comparison.
The code is in
`src/tfm_photochem/historical_2020/photolysis_budget.py`, in
`_validate_gross_subset()` and its two calls in
`partition_odd_oxygen_photolysis()`. Totals smaller beyond the floating-noise
allowance raise a clear `ValueError`; no invalid partition is clipped.

| Event/diagnostic | Event rate | O | O3 | Delta | O1D source |
| --- | --- | ---: | ---: | ---: | ---: |
| `O3_HARTLEY_GROSS` | `JH O3` | -- | -- | -- | -- |
| `O3_HARTLEY_PRODUCTS` | `J3_star O3` | 0 | -1 | +1 | +1 |
| `O3_PHOTOLYSIS_GROUND_EFFECTIVE` | `J3_ground O3` | +1 | -1 | 0 | 0 |
| `O2_SRC` | `J_SRC O2` | +1 | 0 | 0 | +1 |
| `O2_LYMAN_ALPHA` | `0.44 J_LYA O2` | +1 | 0 | 0 | +1 |
| `O2_PHOTOLYSIS_GROUND_EFFECTIVE` | `J2_ground O2` | +2 | 0 | 0 | 0 |

The Hartley gross value is excluded from tendency assembly. The two actual O3
events sum to exactly one total parent loss. Registry size is now 52 processes:
39 implemented coefficient rows and 13 explicitly pending injected inputs.

## Conservation and special-case evidence

The deterministic validator uses `O2=4e12` and `O3=2e8` molecule cm^-3.

| Case | Direct O | Algebraic O1D | Expected atom total | Conservation residual |
| --- | ---: | ---: | ---: | ---: |
| Hartley only, O3 redistribution | 160000 | 1440000.0000000002 | zero net after `-1600000` O3 | 0 |
| Lyman only | 18720 | 5280 | 24000 | 0 |
| SRC only | 80000 | 80000 | 160000 | 0 |
| Mixed O2 | 138719.99999999997 | 85280 | 224000 | `-2.9103830456733704e-11` |
| Mixed O3 redistribution | 360000 | 1440000.0000000002 | zero net after `-1800000` O3 | 0 |

The mixed-O2 residual is one floating-point summation ulp relative to
`2.24e5`; the independent pytest identity uses `2e-15` relative tolerance.
Tests do not call the production partition helper to form the expected
conservation totals.

New gross-subset rejection evidence:

```text
JH=1.0, J_O3_TOTAL=0.95
  -> J_O3_TOTAL must be >= its known gross spectral subset
J_LYA=1.0, J_SRC=0.0, J_O2_TOTAL=0.5
  -> J_O2_TOTAL must be >= its known gross spectral subset
J_SRC=1.0, J_LYA=1.0, J_O2_TOTAL=1.5
  -> J_O2_TOTAL must be >= its known gross spectral subset
```

The validator separately emits an artificial custom-yield failure labelled
`represented excited-channel rate`, proving the two constraints are distinct.
At exact gross equality it reports `J3_ground=0.09999999999999998` and
`J2_ground=0.56`; one ULP below equality it reports positive complements
`0.09999999999999987` and `0.5599999999999996`. The accepted gross-comparison
noise therefore does not zero the yield complements.

The test module contains three parametrized rejection cases plus independent
exact-equality, O2/O3 one-ULP, tolerance-constant, and conservation tests.

## O1D and Delta preservation

The O1D QSSA source remains:

```text
0.9*JH*O3 + J_SRC*O2 + 0.44*J_LYA*O2 + J_H2O_B*H2O
```

`qssa.py` is byte-identical to M4A, and a test varies only the two new totals
while holding the specific rates fixed: all six algebraic values, including
O1D, remain exactly equal. The direct Delta Hartley tendency row is still
exactly `+0.9*JH*O3`; the new ground O3 channel has zero Delta coefficient.

All non-photolysis fluxes are compared exactly under two distinct total-rate
partitions and remain unchanged. The inherited all-J-zero/night test also
passes.

## Old versus new local validator

The accepted M3/M4A validator inputs are retained and the two total fields are
set to `J_O2_TOTAL=2.3e-8`, `J_O3_TOTAL=0.008`.

| Field | M3/M4A | M4B | Reason |
| --- | ---: | ---: | --- |
| forcing field count | 9 | 11 | required total coefficients added |
| flux count | 54 | 56 | gross Hartley renamed plus two effective fluxes |
| contribution rows | 49 | 50 | gross row removed, two actual ground rows added |
| O tendency | `-572329026.0011083` | `-572155586.0011083` | +160000 O3-ground O and +13440 O2-ground O |
| O3 tendency | `-1639155.1637750806` | `-1639155.1637750808` | mathematically unchanged because total O3 rate equals JH; last-bit summation order |
| Delta tendency | `1572007.5893378519` | `1572007.589337852` | same formula; last-bit summation order |
| `P_O1D` | `1525280.02` | `1525280.0200000003` | unchanged formula; last-bit event summation order |
| `P_Delta` | `1599102.631728437` | `1599102.6317284373` | unchanged direct source; last-bit event summation order |
| `res_O1D` | `-2.3283064365386963e-10` | `0.0` | algebraically identical closure with changed floating summation order |

All six algebraic concentrations are bit-for-bit unchanged. Other residuals,
diagnostics, H tendency, and R_H tendency are unchanged. `hartley_products`
changes only in its last floating bit from `1440000.0` to
`1440000.0000000002`.

## Reproducibility evidence

- Full suite: `431 passed, 13 subtests passed`.
- `validate_legacy.py`: PASS; output byte-identical to accepted M4A run.
- `validate_historical_2020_background.py`: PASS; output byte-identical to
  accepted M4A run.
- `validate_local_closure.py`: PASS; deliberate delta documented above.
- `validate_odd_oxygen_photolysis_budget.py`: PASS; all four cases emitted,
  conservation residuals within floating precision, all three new physical
  invalid cases raised, exact/one-ULP boundaries emitted, and the independent
  excited-channel failure remained distinct.
- Ruff: `All checks passed!`.
- Bytecode compilation: PASS.
- `uv lock --check --offline`: PASS; 18 packages resolved offline.
- Wheel build: PASS.
- Clean wheel installation outside the source tree: PASS; version `0.4.2`,
  import and frozen asset loading verified in a fresh venv using the runtime's
  already installed NumPy/SciPy.
- Sdist build: PASS.
- Extracted-sdist suite: `431 passed, 13 subtests passed`.

## Frozen asset integrity

| Asset | SHA256 |
| --- | --- |
| `socrates_prescribed_vmr.csv` | `8985b4774b6e1aa91e3522758c7a33b652501601cdd167871afdc215474b4e01` |
| `midlatitude_equinox_quiet_radiative_background.csv` | `217fe7187c42a4ca8f590e1fa382ef815adffae6f5f1429816cea739f27c604f` |
| `midlatitude_equinox_quiet_chemical_background.csv` | `c1c115d840fa1b3115d7bcb7a1feca769b9dbbddd0faee5a2df0edadc4b5c291` |
| `midlatitude_equinox_quiet_metadata.json` | `5b4c53276b587141201b74116faf3210e3ce0ffa0de025e767fb944b25daa75a` |
| `sigma.mat` | `a98567c4f971721cec4197ad7ea17182e95df78c3a0eea880acb08fc6d560424` |

## Blockers, ambiguities, and roadmap review

No project blocker remains. The R2 handoff requested a tiny tolerance
comparable to M4B; R2 reuses and tests the exact
`64*machine_epsilon` relative convention.

`ENVIRONMENT LIMITATION`, not project failure: a fully isolated offline
dependency resolution cannot fetch the locked SciPy wheel because it is absent
from the global uv cache and registry access is disabled. The wheel itself was
installed offline with `--no-deps` into a fresh external venv using the
runtime's system-site NumPy/SciPy; import, version, 151/51-node background
loading, and frozen assets passed. The extracted sdist imported its own `src/`
tree and passed all 431 tests using the available locked test environment.

Proposed next milestone, not started in M4B: M4C historical UV/VUV direct-beam
radiation supplying the eight UV/VUV J values, including both new totals, with
spherical geometry and optical depth. M4D would remain the separately audited
O2 resonant-excitation stage. This report authorizes neither.
