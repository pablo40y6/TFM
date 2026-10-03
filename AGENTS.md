# Repository instructions

## Accepted scientific baseline

- M1-R2, M2-R2, M3, M4A, M4B-R2, M4C-R2, M4D for temporal use, M5A, M5B and M5C are accepted.
- The current temporal model has 51 heights (50-100 km), seven dynamic species O/O3/H/OH/HO2/H2O2/Delta and 357 ODEs. R_H is diagnostic; only O1D/B0/B1 use QSSA.
- M4D A0/B/IRA is accepted for this model. Advanced LM/Galatry diagnostics remain optional historical work, not an acceptance blocker.
- Current authority is README.md, PROJECT_STATE.md and docs/m5_temporal_report.md. Earlier proposals and blockers indexed in docs/archive/README.md are historical.
- Preserve accepted scientific behavior, equations, constants, event budgets and frozen assets. Never silently change scientific behavior or reopen a baseline without a demonstrable error.
- Preserve the M3 scalar closure as a golden scientific reference.
- The immutable M4C-R2 artifact is artifacts/accepted/m4c-r2/tfm-photochem-milestone4c-r2.zip, SHA-256 2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe.
- Package version 0.5.1 is retained; milestone acceptance is recorded separately by recovery tags and reports.

## Scientific-change discipline

- Freeze equations, units, assumptions, provenance, numerical strategy and validation criteria before a scientific change; freeze the specification before a milestone implementation.
- Run required tests and validators and produce auditable evidence before closure. Do not advance a milestone without explicit acceptance.
- Use branches and pull requests for substantive work; do not silently push scientific work directly to main.
- Do not invent scientific rules or substitute a modern spectroscopy edition for accepted historical sources without explicit scientific approval. Prefer a documented source blocker to an unverifiable substitution.
- NASA/JPL Evaluation 20 is corroborative for historical_2020, not an automatic numerical replacement.
- External reference PDFs are immutable source material; preserve their basenames unless explicitly authorized otherwise.
- Do not commit raw HITRAN, large derived caches, temporary MSIS/NIR caches or scratch certification scripts.

## Current scope

The next phase is final scientific results, figures and thesis writing. Repository consolidation must not introduce new science, models or milestones. Historical periodic-spinup and advanced-spectroscopy blockers are not current next gates.
