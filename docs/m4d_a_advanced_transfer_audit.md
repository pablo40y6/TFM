# Isolated A transfer audit

2026-10-01. M4D is PARTIAL / SCIENTIFIC BLOCKERS / NOT FROZEN. M5 is untouched.

Work starts at remote design HEAD `25caaf9`, preserving the six commits already
added after the user-supplied `3cc036e`. The local review branch is
`codex/m4d-advanced-transfer`. Its implementation commit is `92f7472`; `4582c67`
preserves exact scientific asset bytes during Windows checkout. Publication was
rejected by automatic approval review because implementation/commit authorization
did not explicitly authorize publishing this branch to external GitHub. No push
or pull request was completed; the commits remain local pending user approval.

## Scope verified

- Full pytest: **564 passed, 13 subtests passed**; ruff: **PASS**.
- The same 564 tests and 13 subtests pass in a clean indexed checkout with
  `core.autocrlf=true`, without manual asset conversion.
- All five accepted baseline validators: exit 0.
- Existing M4D mapping validator: exit 0, 430/430 matches, zero ambiguities.
- Existing historical CIA geometry wrapper: exit 0, 357 cases per spacing.
- New A audit: exit 2, explicitly SCIENTIFIC BLOCKER, not failed test execution.
- All 91 SDV lines at 12 T/p states: 1,092 comparisons against math-only
  historical HAPI with its actual default CPF, maximum complex profile-scaled
  error `2.1635279370293397e-5` (0.00216353%), below 0.1%.
- Source-driven SDV area: 24 checks, maximum error `8.038014698286133e-14`.
- All 280 Table-22 temperature nodes are recovered exactly.
- Candidate principal algebra: 3,868 spectral probes at 16 supported T/p states
  are finite/nonnegative and invariant under source reversal. This does not
  establish the unresolved LM coefficient normalization.

`evidence/m4d_a_advanced_transfer.json` contains the A gates and current code
fingerprints. `m4d_a_mapping_recheck.json` and `m4d_a_legacy_cia_recheck.json`
contain the independent existing-validator rechecks. No restricted numerical
source tables, raw line exports, or reference PDFs are added to Git.

## Scientific blockers

1. Absolute normalization of Table-22 Y against normalized complex SDV is not
   established by its cm^-1 atm^-1 source annotation. Nominal LM rates fail
   closed; previous candidate algebra is not a source-semantics PASS.
2. The accepted atmosphere has 248 active 0.125-km shells above 340 K, starting
   at 119.0 km, with maximum shell T `741.757396697998 K`. Preserve the selected
   fail-closed Y policy instead of extending it without evidence.
3. Historical rare-line Galatry beta/profile conversion and the temperature law
   are unestablished in the frozen sources. The pinned HAPI has metadata but
   zero Galatry evaluators. The 280/280 mapping does not close this gate.

Full-band rates, retained low-T/no-Y/q sensitivities, full-domain A convergence,
and Galatry area/limits are NOT RUN. The implemented principal LM-off transfer
and candidate LM algebra tests do not provide a nominal gA. Details and recovery
criteria are in `m4d_a_advanced_transfer_blockers.md`.

## CIA regression recheck

The existing retained-rate validator completed a fresh run with no inherited
cached results and exit 2: the historical CIA stop is reproduced. Nominal CIA
reduces the retained 50-km / SZA 95-degree rate by 0.2915504276%. The
spatial, quadrature-order and spectral-support refinements all pass the 0.1%
gate. This is audit reproduction of the resolved historical stop, not a new
rejection of including CIA attenuation. The post-stop scope remains resolved.

The producer fingerprints in the CIA report reflect the local snapshot at run
start, while A-only code was being finalized. The executed classic spectroscopy
and CIA/source/transfer definitions are unchanged; line-ending normalization
changes only text byte fingerprints. `evidence/m4d_a_validation_receipt.json`
records that integrity check, the final A fingerprints, and each validator exit.

## Baseline integrity and checkout finding

M4C-R2 package SHA-256 remains
`2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe`.
All accepted assets and the artifact are byte-identical to the requested Git
baseline. The accepted historical_2020 source is unchanged apart from checkout
line endings; none of it is part of this diff. The five classic spectroscopy
definitions used by B/IRA are AST-identical to the requested starting commit.
Only SDV/Drouin/Y input validation changes in the shared isolated module.

The initial Windows clone converted hashed asset LF bytes into CRLF, causing
baseline hash checks to fail. Restoring their canonical Git bytes fixed all
baseline tests without changing the frozen data. `.gitattributes` now disables
newline conversion for accepted assets/artifacts and selects LF for isolated
M4D modules/validators. Accepted CSVs and metadata are not changed in Git.

## Reproduction

Install the existing `dev,m4d-audit` extras. Supply the external source directory
and original HITRAN2016 export using task-specific variables:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONIOENCODING='utf-8'
$env:OPENBLAS_NUM_THREADS='1'
python -m pytest -q -p no:cacheprovider
python -m ruff check .
python scripts/validate_legacy.py
python scripts/validate_local_closure.py
python scripts/validate_odd_oxygen_photolysis_budget.py
python scripts/validate_historical_2020_background.py
python scripts/validate_historical_2020_uv.py
python scripts/validate_m4d_mapping.py --sources $M4D_SOURCE_DIR --hitran $M4D_HITRAN --output evidence/m4d_a_mapping_recheck.json
python scripts/validate_m4d_a_transfer.py --sources $M4D_SOURCE_DIR --hitran $M4D_HITRAN --output evidence/m4d_a_advanced_transfer.json
python scripts/validate_m4d_legacy_cia_diagnostic.py --sources $M4D_LEGACY_SOURCE_DIR --work ../m4d-a-legacy-rerun --output evidence/m4d_a_legacy_cia_recheck.json
python scripts/validate_m4d_reconstruction.py --sources $M4D_SOURCE_DIR --hitran $M4D_HITRAN --checkpoints ../m4d-a-run-cache --output evidence/m4d_a_cia_stop_recheck.json
```

For the two scientific-blocker validators, propagate the Python process's exit
code explicitly from a dedicated PowerShell wrapper (`exit $LASTEXITCODE`).
Exit 2 records a blocker; it never certifies complete M4D closure.
