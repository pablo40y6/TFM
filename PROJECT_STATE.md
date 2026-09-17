# Project state

## Purpose

This repository develops a reproducible time-dependent mesospheric ozone and O2(a1Delta) photochemical model. The accepted implementation currently ends at the SZA-resolved direct-beam UV/VUV radiation baseline, M4C-R2.

## Accepted architecture

- Dynamic state at each chemistry level: O, O3, H, `R_H = OH + HO2`, and Delta = O2(a1Delta_g).
- Chemistry grid: 50-100 km at 1 km spacing, 51 levels.
- Future full system: 255 ODEs.
- Algebraic/QSSA species: O(1D), OH, HO2, H2O2, B0 = O2(b1Sigma_g+, v=0), and B1 = O2(b1Sigma_g+, v=1).
- Prescribed fields: T, M, O2, N2, CO2, H2O, and H2.
- First temporal version: no vertical transport; BDF as the main solver; Radau as an independent verification; repeated diurnal cycles to periodic convergence.
- Delta remains dynamic: `dDelta/dt = P_Delta - L_Delta*Delta`.

These statements describe the accepted architecture and provisional continuation. They do not mean M4D or the later temporal solver has been implemented.

## Accepted milestone ledger

| Milestone | Status | Artifact | SHA-256 | Package version |
| --- | --- | --- | --- | --- |
| M1-R2 | CLOSED / ACCEPTED | `tfm-photochem-milestone1-r2.zip` | `46c88ec344de1569d06dff76c36c991edb19777497146ff5183756b54cba6f3d` | 0.1.0, documented in inherited audit/build evidence |
| M2-R2 | CLOSED / ACCEPTED | `tfm-photochem-milestone2-r2.zip` | `ffb179c9f2c7fdb71ad5af8990490ae0040cf729f7209e1ae90a25fa0021f47f` | 0.2.0, documented in the inherited M2 report |
| M3 | CLOSED / ACCEPTED | `tfm-photochem-milestone3.zip` | `d5dac9f3d160b0d53a1fdc16b23b4c72b918c271466dfbe58d99c5a54a9d89ef` | 0.3.0 |
| M4A | CLOSED / ACCEPTED | `tfm-photochem-milestone4a.zip` | `d1a68e6344710cd8ae6543f12081cde55355f23849ea73b9724d9e49156fbc12` | 0.4.0 |
| M4B-R2 | CLOSED / ACCEPTED | `tfm-photochem-milestone4b-r2.zip` | `87fe1d585efa6f42231fc6d9898ca37c5afa51d1b4baa6325015caaee03530c8` | 0.4.2 |
| M4C-R2 | CLOSED / ACCEPTED; current baseline | `tfm-photochem-milestone4c-r2.zip` | `2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe` | 0.5.1 |

The immutable current artifact is stored at `artifacts/accepted/m4c-r2/tfm-photochem-milestone4c-r2.zip`. Accepted baseline details live in that artifact and in `docs/handoffs/TFM2_ProjectReset_PreM4D_Context.md`.

## Current next milestone

M4D is **NOT IMPLEMENTED / DESIGN NOT FROZEN**. Its intended outputs are the remaining `gA`, `gB`, and `gIRA` physical forcings. The design must be reconstructed independently from primary and historical sources before implementation.

There is a known unresolved provenance risk concerning historical O2 spectroscopy, including the exact historical HITRAN2016 line dataset and TIPS2017 partition-function provenance. Modern HITRAN, HAPI, or HITRANonline data must not be substituted silently. NASA/JPL Evaluation 20 is corroborative material only. If the required historical inputs cannot be verified during the independent M4D source investigation, the project must stop with **SOURCE BLOCKER** rather than silently substitute modern data.

## Known bootstrap reproducibility finding

During repository bootstrap, the optional M4A background regeneration was attempted with `pymsis==0.12.0` on Windows / Python 3.14. The three regenerated background outputs were not byte-identical to the accepted frozen M4A assets.

The accepted frozen assets themselves were **not** modified: their accepted hashes and repository validators pass. This is currently classified as an environment/reproducibility finding, not as evidence of a scientific defect in M4A. M4A remains **CLOSED / ACCEPTED**. Future work must not replace the accepted frozen backgrounds based solely on this cross-environment regeneration result; reproducing the original generation environment may be investigated separately.

## Documented source-identity discrepancy

The external file `references/scientific/JPL_Publication_15-10_compressed.pdf` has SHA-256 `a5c57b2a8435760bc4dd43da328a9dd34768865c022e965326f3eccaaf0cd3c8`. The accepted package documents other hashes for JPL Evaluation 18 source copies, including `149a4bab985402c67419e02ff8ca80202d1ba55f5383fbf69692e2184b68da08` in the M4C asset generator and `ddf6e0b4454d5076ec128dafce498c2070c63b4ad166edbca84d22b12cd51796` for a later official repository download. Bibliographic similarity is not treated as file identity.

## Provisional roadmap after M4D

1. M5A: performance-ready 51-level chemistry kernel.
2. M5B: 255-state RHS with BDF/Radau integration.
3. M6: diurnal cycle and periodic convergence.
4. M7: scientific validation and sensitivity work.
5. M8: Odin/retrieval/application work, if still in scope.

At M4D closure, reconsider explicitly whether M5A and M5B should remain separate. Before any M5 optimization, preserve the M3 scalar closure as the golden scientific reference.
