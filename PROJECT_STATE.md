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
| M4C-R2 | CLOSED / ACCEPTED; current implemented baseline | `tfm-photochem-milestone4c-r2.zip` | `2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe` | 0.5.1 |

The immutable current artifact is stored at `artifacts/accepted/m4c-r2/tfm-photochem-milestone4c-r2.zip`. Accepted baseline details live in that artifact and in `docs/handoffs/TFM2_ProjectReset_PreM4D_Context.md`.

## Current next milestone

M4D is **NOT IMPLEMENTED**. Its independent design has advanced from open source investigation to a substantially frozen implementation specification, but it remains **PENDING FINAL INDEPENDENT DESIGN REVIEW** before coding is authorized.

M4D must supply the remaining physical forcing arrays `gA`, `gB`, and `gIRA` without starting M5.

### M4D spectroscopy/source gates

The previous historical spectroscopy provenance risk has been resolved for the target systems rather than bypassed with modern data:

- **HITRAN2016 target-line source: PASS.** The manually acquired SpectralCalc export was produced with the browser UI explicitly set to HITRAN2016/O2 and was hashed as `6b4acbc01cb649891f2d8597875c9cd8e4805cfdd4d3b7841c2d18cbf718de12`. Although the export is not a complete full-range HITRAN2016 O2 database, forensic comparison supports its target A/B/IRA systems as the historical HITRAN2016 source. Frozen semantic subsets are `a(0)-X(0)` = 835 lines, `b(0)-X(0)` = 430 lines, and `b(1)-X(0)` = 320 lines, each with deterministic subset hashes documented in `docs/m4d_spectralcalc_export_forensics.md`.
- **TIPS-2017: PASS.** The selected historical numerical source is official `hitranonline/hapi@f41d9911f2631eed51b96d6c617b4f27786ad477`, `hapi/hapi.py`, Git blob `caeab1bfaa278b5420adef7efe7ab566991ba763`, HAPI `1.1.0.8.2`. O2 partition-sum table anchors are frozen; project-local derived-asset SHA-256 remains an implementation materialization step.
- **Solar source: PASS.** Wehrli (1985) WMO/WRC extraterrestrial irradiance is selected, with deterministic wavelength interpolation and conversion to photon flux per wavenumber documented in `docs/m4d_solar_forcing_freeze.md`.
- **Line shape: PASS.** Doppler-only is the historical baseline. At the densest chemistry level (50 km), the maximum Lorentz/Doppler HWHM ratios across every target line are only 0.6088% (IRA), 0.3854% (A), and 0.3342% (B); they decrease upward. A Voigt sensitivity remains required as validation evidence.
- **Geometry: PASS.** M4D reuses the accepted M4C exact spherical-shell solar path matrix, Earth shadow, 0-150 km radiative column, and endpoint-mean shell-density convention. O2 optical depth is temperature resolved by shell.
- **IRA CIA scope: PASS for baseline definition.** Historical `gIRA` is monomer `a(0)-X(0)` resonance absorption. O2 CIA is physically real but is not injected into the first historical implementation; near-twilight CIA attenuation is explicitly deferred as a documented sensitivity/limitation.
- **Numerical spectroscopy specification: FROZEN FOR REVIEW.** Standard HITRAN temperature scaling, historical TIPS 3/4-point Lagrange interpolation, Doppler normalization, line-local converged spectral quadrature, validation anchors and tolerances are specified in `docs/m4d_numerical_specification.md`.

Current live HITRAN/HAPI data are not used as a silent historical substitute. The earlier SOURCE BLOCKER risk has therefore been overcome for the M4D target spectroscopy, but implementation remains gated on final independent review of the frozen design.

### M4D primary design documents

- `docs/m4d_spectralcalc_export_forensics.md`
- `docs/m4d_tips2017_provenance_recovery.md`
- `docs/m4d_solar_forcing_freeze.md`
- `docs/m4d_broadening_and_geometry_freeze.md`
- `docs/m4d_ira_cia_scope_freeze.md`
- `docs/m4d_numerical_specification.md`

Earlier research/forensics notes remain supporting evidence and are not superseded as provenance records.

### Immediate next gate

Perform an **independent design audit** against the primary/historical sources and the accepted M4C-R2 contracts. The audit must check equations, units, source identities, line-selection semantics, temperature scaling, geometry, numerical convergence criteria and milestone boundaries.

Only if that audit passes should an implementation handoff be frozen and Codex be authorized to implement M4D on a separate implementation branch/PR.

## Known bootstrap reproducibility finding

During repository bootstrap, the optional M4A background regeneration was attempted with `pymsis==0.12.0` on Windows / Python 3.14. The three regenerated background outputs were not byte-identical to the accepted frozen M4A assets.

The accepted frozen assets themselves were **not** modified: their accepted hashes and repository validators pass. This is currently classified as an environment/reproducibility finding, not as evidence of a scientific defect in M4A. M4A remains **CLOSED / ACCEPTED**. Future work must not replace the accepted frozen backgrounds based solely on this cross-environment regeneration result; reproducing the original generation environment may be investigated separately.

## Documented source-identity discrepancy

The external file `references/scientific/JPL_Publication_15-10_compressed.pdf` has SHA-256 `a5c57b2a8435760bc4dd43da328a9dd34768865c022e965326f3eccaaf0cd3c8`. The accepted package documents other hashes for JPL Evaluation 18 source copies, including `149a4bab985402c67419e02ff8ca80202d1ba55f5383fbf69692e2184b68da08` in the M4C asset generator and `ddf6e0b4454d5076ec128dafce498c2070c63b4ad166edbca84d22b12cd51796` for a later official repository download. Bibliographic similarity is not treated as file identity.

## Provisional roadmap after M4D

1. M5A: performance-ready 51-level chemistry kernel.
2. M5B: 255-state RHS with BDF/Radau integration.
3. M6: diurnal cycle and periodic convergence.
4. M7: scientific validation and sensitivity work, including deferred CIA/twilight and accepted shell-discretization sensitivities.
5. M8: Odin/retrieval/application work, if still in scope.

At M4D closure, reconsider explicitly whether M5A and M5B should remain separate. Before any M5 optimization, preserve the M3 scalar closure as the golden scientific reference.