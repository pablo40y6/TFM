# Project state

## Accepted milestones

M1-R2, M2-R2, M3, M4A, M4B-R2 and M4C-R2 are CLOSED / ACCEPTED.
M4D is CLOSED / ACCEPTED **for the temporal model**; M5A is CLOSED / ACCEPTED,
and M5B/M5C are GO / accepted.

Scientific recovery tags: `m5a-accepted` (a0a9c6f), `m5b-accepted` (faebd30),
`m5c-accepted` (dbb5878), and `m4d-temporal-accepted` (faebd30, downstream acceptance).
The consolidated main baseline is identified by `tfm-temporal-model-v1`.
The M4C-R2 immutable artifact remains
`artifacts/accepted/m4c-r2/tfm-photochem-milestone4c-r2.zip`, SHA-256
`2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe`.
Earlier accepted artifacts and provenance remain in `artifacts/accepted/`.

## Current model

- 51 chemistry heights, 50-100 km at 1 km spacing; 357 ODEs.
- Dynamic O, O3, H, OH, HO2, H2O2, Delta; concentrations in cm^-3.
- Exact diagnostic R_H = OH + HO2; QSSA only O1D, B0, B1.
- Accepted event kinetics and budgets; M3 scalar closure remains a golden reference.
- Dynamic O/O3 in M4C UV; M4D A0/B/IRA excitation with historical O2-Air CIA attenuation.
- UTC date/latitude/east-positive longitude solar geometry and exact shell shadow.
- BDF main solver; Radau validation; no transport.
- `frozen_reference` or prescribed `dynamic_msis` atmosphere (MSIS-00).
- Default dynamic background cadence 300 s, NIR cadence 3600 s.

## Inputs

Aware start/end datetimes, latitude, longitude, atmosphere choice, and exactly
one initialization route: explicit `(51, 7)` nonnegative `initial_state`, or
approximate `initialization="reference_noon"` bootstrap from preceding apparent
solar noon. Geometry does not establish a chemical initial condition.

Dynamic MSIS uses pinned `pymsis==0.12.0`, quiet activity 150/150/4 or explicit
UTC drivers (previous-day F107, 81-day-mean F107a, daily Ap), with no automatic
space-weather download. Dynamic NIR requires authorized local historical
sources/HITRAN2016 or an explicit precomputed provider. The frozen route has
a packaged, SHA-verified derived NIR table. Restricted source data and temporary
MSIS/NIR caches are excluded from Git.

## Outputs and validation

`SimulationResult` and saved NPZ contain time, height, SZA, seven species,
R_H, three QSSA fields, eleven forcings and geometry/atmosphere/initialization/
solver metadata. Dynamic outputs also retain prescribed physical backgrounds
and native-field availability. Native availability NaNs are distinct from
finite chemical state/background requirements.

Preserved accepted evidence:

- M5A: `evidence/m5_reference_cycle.npz`.
- M5B: `evidence/m5b_reference_real_geometry.npz`.
- M5C: `evidence/m5c_reference_dynamic_msis.npz`.
- Certification/provenance: `evidence/m5_temporal_evidence.json` and M4D evidence.

M5C closure recorded 908 tests + 13 subtests, ruff, five historical validators
and M4D mapping PASS. Background/NIR output convergence is below approximately
0.5%; all-species BDF base/tight maximum is 0.423641%, tight/Radau 0.00946013%.
The detailed evidence and reproduction commands remain in the single
[technical report](docs/m5_temporal_report.md).

## Limitations

Reference-noon is an approximate bootstrap, not validated climatology.
Finite-horizon acceptance does not certify a periodic attractor. H2O/H2 and
exterior O3 VMRs remain prescribed; dynamic MSIS does not add transport or
chemical dilution. Frozen atmosphere retains the M4A reference independently
of geometry location. Source/temperature envelopes and numerical scopes remain
those in the report.

M4D A1/A0 downstream maximum differences are approximately 0.000122% for O3
and 0.233878% for Delta. Advanced LM/Galatry sensitivities are optional;
PR #4 is historical and is not merged separately. Earlier blockers and
proposals remain evidence rather than current operational gates.

## Next phase

Final scientific results, figures and thesis writing. No new scientific
milestone or experiments belong to this repository-consolidation task.

Current authority: [README](README.md), this file, and
[docs/m5_temporal_report.md](docs/m5_temporal_report.md).
Historical material is indexed in [docs/archive/README.md](docs/archive/README.md).
