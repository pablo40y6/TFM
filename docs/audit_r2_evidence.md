# Milestone 1 audit revision 2 evidence

Date: 2026-09-09

Audited input artifact:
`tfm-photochem-milestone1(1).zip`

Audited input SHA256:
`f3e3fdad179f84f518c1dac115913c744553245488ba0220161f64ac7235a204`

## Modified files relative to the audited ZIP

- `MANIFEST.in` (new)
- `README.md`
- `pyproject.toml`
- `uv.lock`
- `docs/architecture.md`
- `docs/audit_r2_evidence.md` (new)
- `docs/legacy_2017_notes.md`
- `docs/source_inventory.md`
- `docs/validation_report.md`
- `tests/test_geometry.py`
- `tests/test_ozone.py`
- `tests/test_photolysis.py`

No numerical production module was modified. In particular,
`src/tfm_photochem/historical_2020/__init__.py` remains byte-identical to the
audited artifact with SHA256
`80bf4464c3cce298845ae3d74ff6c5c193e7e2a89cf92b1c2344061e14453e73`.
The frozen `sigma.mat` remains byte-identical with SHA256
`a98567c4f971721cec4197ad7ea17182e95df78c3a0eea880acb08fc6d560424`.

## Audit finding -> correction -> evidence

| Audit finding | Correction | Evidence |
| --- | --- | --- |
| The sdist omitted `tests/sample_profiles.py` | Added `MANIFEST.in` with recursive test inclusion | Tar listing contains the helper; pytest passes from the extracted sdist |
| Static lint claim was not reproducible | Declared Ruff in the `dev` extra, configured it in `pyproject.toml`, and updated `uv.lock` | Ruff 0.16.6: `All checks passed!` |
| Thesis eq. 3.40 says 112 nm while A.11 uses 122 nm | Documented the internal discrepancy and selected executable A.11 for legacy compatibility | `legacy_2017_notes.md` and `source_inventory.md` explicitly distinguish both values |
| Twilight fallback can assign below-grid path | Documented it as a literal legacy limitation and not exact geometry over the full twilight range | Independent test verifies the literal value and proves it exceeds the represented-shell-only path |
| Twilight/Earth-shadow coverage was incomplete | Added required SZA shape checks, independent day/twilight ray-sphere checks, and exact shadow transition | Tests cover 0, 60, 89.999, 90, 90.001, 95, and 100 degrees plus tangent altitude zero |
| `tau == 0` was described only as shadow behavior | Documented its broader semantics and added illuminated zero-absorber coverage | `test_zero_tau_in_daylight_forces_all_legacy_j_values_to_zero` passes |
| `Jfactors.m` and `mkozone.m` differ at `tau == 0` | Documented and tested the inherited inconsistency without harmonizing the routines | `test_zero_tau_semantics_differ_from_jfactors_as_in_matlab` passes |

## Required command evidence

### 1. Tests from repository

Command:

```bash
uv run --extra dev pytest -q
```

Result:

```text
......................                                      [100%]
22 passed, 13 subtests passed in 0.23s
```

### 2. Legacy validator

Command:

```bash
uv run --extra dev python scripts/validate_legacy.py
```

Result: exit 0. The output retained the frozen asset hash and regression
values:

```json
{
  "configuration": "legacy_2017",
  "sigma_sha256": "a98567c4f971721cec4197ad7ea17182e95df78c3a0eea880acb08fc6d560424",
  "sza_deg": 60.0,
  "altitude_km": [50.0, 80.0, 100.0, 150.0],
  "j_hart_s-1": [
    0.007901060075276741,
    0.007943298912613521,
    0.007950799890467177,
    0.007951370570121479
  ],
  "j_src_s-1": [
    1.4729438260421979e-307,
    9.562150252425894e-15,
    2.6712220862792933e-08,
    3.636571535539284e-06
  ],
  "j_lya_s-1": [
    3.83873300714473e-36,
    1.6186877815710608e-09,
    3.6361272783339067e-09,
    3.819962471375554e-09
  ],
  "j_o3_total_s-1": [
    0.008011935688633766,
    0.008058062381488302,
    0.008070366753215189,
    0.008073629856095872
  ],
  "j_o2_total_s-1": [
    5.10968259712899e-10,
    2.1429561639980833e-09,
    3.099237774818972e-08,
    4.460643082713598e-06
  ],
  "mkozone_cm-3": [
    575602196091.73,
    8325166168.343959,
    52693522.02762813,
    0.003597832916437647
  ]
}
```

### 3. Bytecode compilation

Command:

```bash
PYTHONPYCACHEPREFIX=/workspace/scratch/889c958cd82e/tmp/m1-r2-pycache \
  uv run --extra dev python -m compileall -q src tests scripts
```

Result: exit 0, `bytecode compilation: PASS`.

### 4. Lint

Commands:

```bash
uv run --extra dev ruff --version
uv run --extra dev ruff check src tests scripts
```

Result:

```text
ruff 0.16.6
All checks passed!
```

### 5-6. Wheel and sdist build

Command:

```bash
uv build --clear
```

Result:

```text
Successfully built dist/tfm_photochem-0.1.0.tar.gz
Successfully built dist/tfm_photochem-0.1.0-py3-none-any.whl
```

### 7. Wheel installation in a clean environment

The wheel was installed into a newly created Python 3.12 virtual environment,
from a working directory outside the source tree. NumPy 2.5.3, SciPy 1.18.1,
and `tfm-photochem` 0.1.0 were installed.

Result:

```text
wheel clean install: PASS
packaged sigma SHA256: a98567c4f971721cec4197ad7ea17182e95df78c3a0eea880acb08fc6d560424
```

### 8-9. Extracted sdist and tests from that tree

The tar listing explicitly contained:

```text
tfm_photochem-0.1.0/MANIFEST.in
tfm_photochem-0.1.0/docs/validation_report.md
tfm_photochem-0.1.0/tests/sample_profiles.py
```

The sdist was extracted, installed with its `dev` extra into a second fresh
Python 3.12 environment, and pytest was run from the extracted source tree.

Result:

```text
......................                                      [100%]
22 passed, 13 subtests passed in 0.62s
```

## Failure classification

- `PROJECT FAILURE`: none.
- `ENVIRONMENT LIMITATION`: an initial attempt to delete a previous temporary
  validation directory was blocked before any project command ran. The required
  clean-wheel test was rerun successfully in a new `mktemp` directory without
  deletion.

## Scope confirmation

This revision does not implement Milestone 2. `historical_2020` still contains
only its original namespace marker. No kinetics, ODE, QSSA, transport, spin-up,
BDF/Radau integration, or updated-2025 numerical input was added.
