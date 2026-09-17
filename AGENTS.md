# Repository instructions

## Accepted scientific baseline

- Milestones M1 through M4C-R2 are accepted and frozen scientific baselines.
- M4C-R2, package version 0.5.1, is the current accepted code baseline.
- The immutable accepted artifact is `artifacts/accepted/m4c-r2/tfm-photochem-milestone4c-r2.zip` with SHA-256 `2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe`.
- Do not reopen an accepted baseline without a demonstrable error.
- Never silently change scientific behaviour.
- Frozen scientific assets must not be altered casually.
- External reference PDFs are immutable source material. Preserve their basenames unless explicitly authorized otherwise.

## Scientific-change discipline

- Before coding a scientific change, explicitly freeze its equations, units, assumptions, provenance, numerical strategy, and validation criteria.
- Before implementing every milestone, freeze its specification.
- Before milestone closure, run the required tests and validators and produce auditable evidence.
- Do not advance to the next milestone until the current milestone is explicitly accepted.
- Do not invent scientific rules beyond the authoritative handoff and accepted package documentation.
- Use branches and pull requests for substantive work; do not silently push scientific work directly to `main`.

## M4D and later work

- M4D is **NOT IMPLEMENTED / DESIGN NOT FROZEN**.
- Reconstruct M4D independently from primary and historical sources before implementation.
- Do not use any old M4D proposal as an accepted design.
- Do not substitute modern HITRAN, HAPI, or HITRANonline data for an exact historical edition without explicit scientific approval.
- NASA/JPL Evaluation 20 is corroborative for the `historical_2020` baseline, not an automatic numerical replacement.
- Prefer a **SOURCE BLOCKER** to an unverifiable scientific substitution.
- Preserve the M3 scalar closure as the golden scientific reference before any future M5 optimization.

