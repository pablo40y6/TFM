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

M4D is **NOT IMPLEMENTED / DESIGN NOT FROZEN**. The full-domain numerical review rejected Doppler-only. Historical follow-up has now selected classic HITRAN2016 Voigt as the B-band baseline candidate and the IRA monomer baseline candidate. The principal-isotopologue A band remains blocked on materialization/mapping of the historical Drouin/HITRAN2016 advanced speed-dependent + line-mixing representation. Coding is not authorized.

M4D must supply the remaining physical forcing arrays `gA`, `gB`, and `gIRA` without starting M5.

### M4D spectroscopy/source gates

- **HITRAN2016 target-line source: PASS for transition/intensity provenance.** The manually acquired SpectralCalc export was produced with the browser UI explicitly set to HITRAN2016/O2 and was hashed as `6b4acbc01cb649891f2d8597875c9cd8e4805cfdd4d3b7841c2d18cbf718de12`. Although the export is not a complete full-range HITRAN2016 O2 database, forensic comparison supports the target A/B/IRA systems as historical HITRAN2016 transition sources. Frozen semantic subsets are `a(0)-X(0)` = 835 lines, `b(0)-X(0)` = 430 lines, and `b(1)-X(0)` = 320 lines, each with deterministic subset hashes documented in `docs/m4d_spectralcalc_export_forensics.md`. This PASS does **not** imply that classic 160-character records contain the complete advanced A-band relation set.
- **TIPS-2017: PASS.** The selected historical numerical source is official `hitranonline/hapi@f41d9911f2631eed51b96d6c617b4f27786ad477`, `hapi/hapi.py`, Git blob `caeab1bfaa278b5420adef7efe7ab566991ba763`, HAPI `1.1.0.8.2`.
- **Solar source: PASS.** Wehrli (1985) WMO/WRC extraterrestrial irradiance is selected with deterministic wavelength interpolation and photon-flux conversion.
- **Doppler-only: REJECTED FOR FULL DOMAIN.** Local chemistry-level width ratios do not bound illuminated twilight rays through denser air below 50 km. The previous full-band pressure-broadening sensitivity exceeded the `0.1%` adequacy criterion for A even for rates above `1e-10 s^-1` and produced much larger differences in selected post-90-degree cases.
- **A-band principal isotopologue: SOURCE MATERIALIZATION / PARAMETER-MAPPING BLOCKER.** HITRAN2016 points to Drouin et al. for an advanced SDV + collisional-line-mixing treatment and transforms scaled W-matrix information to first-order Rosenkranz parameters. The source family and exact supplement identity (`NIHMS804415-supplement-supplement_1.pdf`, reported 94.8 kB) are known, but the project has not frozen its bytes/SHA-256 or executable parameter mapping.
- **A-band rare isotopologues: OPEN.** The accepted A subset includes iso-2 and iso-3 lines. Recover the historically appropriate profile or demonstrate that a documented classic-profile fallback changes final `gA` by no more than `0.1%` throughout the validation domain.
- **B-band line shape: BASELINE CANDIDATE SELECTED.** Use the complete classic isolated-Voigt HITRAN2016 fields from the accepted B subset. Do not reproduce the known defective/partial advanced B qSDV values silently. A source-corrected qSDV sensitivity on the historically covered principal-isotopologue lines is required; if any validated B rate changes by more than `0.1%`, reopen the baseline before freeze.
- **IRA monomer line shape: BASELINE CANDIDATE SELECTED.** Use classic isolated Voigt with the accepted HITRAN2016 `gamma_air`, `gamma_self`, `n_air`, and `delta_air` fields, pending the final consistent target+attenuation convergence run.
- **Classic B/IRA pressure-broadening convention: SELECTED.** Use `gamma_L=(296/T)^n_air * [gamma_air*(p-p_O2)+gamma_self*p_O2]` with pressures in atm. `gamma_air` is already the HITRAN air-broadening coefficient and must not be multiplied by another N2/O2 mixture factor.
- **Classic B/IRA pressure-shift convention: SELECTED CANDIDATE.** Use `nu_shifted=nu0+delta_air*p` with shell-local total pressure and no invented temperature dependence. A full-path sensitivity remains required. A uses its recovered advanced shift convention instead.
- **Geometry: PASS.** Retain the M4C spherical-ray equations, Earth radius, radiative top and physical shadow semantics. M4D NIR path integration uses deterministic `0.125 km` atmospheric sub-stratification derived from the accepted one-kilometre profiles and checks it against `0.0625 km`; M4C-R2 production behavior is untouched.
- **Shellwise transfer: PASS as a design requirement.** O2 optical depth is evaluated shell by shell with local temperature and, for pressure-broadened profiles, local pressure. A target-temperature cross section multiplied by total O2 column is rejected.
- **B/IRA attenuation-wing strategy: CANDIDATE SELECTED.** At each target quadrature node evaluate attenuation from all accepted absorber lines in the band rather than imposing a `+/-10` or `+/-20 cm^-1` absorber cutoff. Target support/order are converged separately. This must still pass the full numerical gate.
- **IRA CIA scope: PASS for baseline definition / HISTORICAL SENSITIVITY REQUIRED.** Historical `gIRA` remains monomer `a(0)-X(0)` excitation. HITRAN2016 identifies Maté et al. (1999), DOI `10.1029/1999JD900824`, for the revised 1.27-micron CIA data, with pure-O2 and 21:79 O2:N2 mixture products represented separately. Freeze the exact historical HITRAN2016 CIA file identity/hash and execute the twilight sensitivity without double counting O2-O2 and without substituting current HITRAN CIA data.
- **Numerical spectroscopy specification: PARTIAL / NOT FROZEN.** Standard HITRAN scaling, historical TIPS interpolation, Wehrli forcing, unattenuated `g0(T)` anchors, shellwise transfer, M4D path sub-stratification, and B/IRA classic-profile candidates are selected. Final A spectroscopy plus the full profile/convergence/sensitivity runs remain open.

Current live HITRAN/HAPI data are not used as a silent historical substitute. The target-transition gate is closed; the remaining source blocker is specifically the historical A-band advanced parameterization plus historical CIA byte materialization for the required IRA sensitivity.

### M4D primary design documents

- `docs/m4d_spectralcalc_export_forensics.md`
- `docs/m4d_tips2017_provenance_recovery.md`
- `docs/m4d_solar_forcing_freeze.md`
- `docs/m4d_broadening_and_geometry_freeze.md`
- `docs/m4d_ira_cia_scope_freeze.md`
- `docs/m4d_numerical_specification.md`
- `docs/m4d_final_design_review.md`
- `docs/m4d_pressure_broadening_provenance_followup.md`

Earlier research/forensics notes remain supporting evidence and are not superseded as provenance records.

### Immediate next gate

1. Freeze the exact Drouin A-band supplement bytes/hash and executable Drouin/HITRAN2016 SDV + line-mixing mapping.
2. Resolve or quantitatively bound the A-band rare-isotopologue profile treatment.
3. Freeze the exact historical HITRAN2016 1.27-micron CIA file required for the Option-B sensitivity.
4. Run the selected B and IRA classic-Voigt profiles consistently in target excitation and shell attenuation using all accepted absorber lines at each target quadrature node; quantify pressure-shift sensitivity and the corrected B qSDV sensitivity.
5. Run the final A representation consistently once materialized.
6. Validate all 51 altitudes at `SZA = 0, 60, 85, 89, 89.9, 95, 99 deg` plus illuminated-tangent/immediately-shadowed boundary cases and demonstrate `<=0.1%` convergence above the declared `1e-15 s^-1` floor.
7. Execute the historical IRA CIA twilight sensitivity.

Only after these gates pass may `docs/m4d_final_design_specification.md` be created and implementation authorized.

## Known bootstrap reproducibility finding

During repository bootstrap, the optional M4A background regeneration was attempted with `pymsis==0.12.0` on Windows / Python 3.14. The three regenerated background outputs were not byte-identical to the accepted frozen M4A assets.

The accepted frozen assets themselves were **not** modified: their accepted hashes and repository validators pass. This is currently classified as an environment/reproducibility finding, not as evidence of a scientific defect in M4A. M4A remains **CLOSED / ACCEPTED**. Future work must not replace the accepted frozen backgrounds based solely on this cross-environment regeneration result; reproducing the original generation environment may be investigated separately.

## Documented source-identity discrepancy

The external file `references/scientific/JPL_Publication_15-10_compressed.pdf` has SHA-256 `a5c57b2a8435760bc4dd43da328a9dd34768865c022e965326f3eccaaf0cd3c8`. The accepted package documents other hashes for JPL Evaluation 18 source copies, including `149a4bab985402c67419e02ff8ca80202d1ba55f5383fbf69692e2184b68da08` in the M4C asset generator and `ddf6e0b4454d5076ec128dafce498c2070c63b4ad166edbca84d22b12cd51796` for a later official repository download. Bibliographic similarity is not treated as file identity.

## Provisional roadmap after M4D

1. M5A: performance-ready 51-level chemistry kernel.
2. M5B: 255-state RHS with BDF/Radau integration.
3. M6: diurnal cycle and periodic convergence.
4. M7: scientific validation and sensitivity work not already required for M4D closure.
5. M8: Odin/retrieval/application work, if still in scope.

At M4D closure, reconsider explicitly whether M5A and M5B should remain separate. Before any M5 optimization, preserve the M3 scalar closure as the golden scientific reference.
