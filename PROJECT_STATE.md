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

M4D is **NOT IMPLEMENTED / DESIGN NOT FROZEN**. Doppler-only is rejected over the required spherical twilight domain. The per-band historical profile families are now substantially identified: A iso-1 uses the HITRAN2016/Drouin advanced SDV + line-mixing lineage, A iso-2/3 use the Long/HITRAN2012 Galatry + Dicke-narrowing lineage unless a HITRAN2016 supersession is found, B uses classic HITRAN2016 Voigt as baseline candidate with corrected qSDV sensitivity, and IRA uses classic HITRAN2016 Voigt as monomer baseline candidate with a required historical CIA twilight sensitivity. Coding is not authorized.

M4D must supply the remaining physical forcing arrays `gA`, `gB`, and `gIRA` without starting M5.

### M4D spectroscopy/source gates

- **HITRAN2016 target-line source: PASS for transition/intensity provenance.** The manually acquired SpectralCalc export was produced with the browser UI explicitly set to HITRAN2016/O2 and was hashed as `6b4acbc01cb649891f2d8597875c9cd8e4805cfdd4d3b7841c2d18cbf718de12`. Although the export is not a complete full-range HITRAN2016 O2 database, forensic comparison supports the target A/B/IRA systems as historical HITRAN2016 transition sources. Frozen semantic subsets are `a(0)-X(0)` = 835 lines, `b(0)-X(0)` = 430 lines, and `b(1)-X(0)` = 320 lines, each with deterministic subset hashes documented in `docs/m4d_spectralcalc_export_forensics.md`. This PASS does **not** imply that classic 160-character records contain complete advanced/auxiliary A-band profile parameters.
- **TIPS-2017: PASS.** Use official historical `hitranonline/hapi@f41d9911f2631eed51b96d6c617b4f27786ad477`, `hapi/hapi.py`, Git blob `caeab1bfaa278b5420adef7efe7ab566991ba763`, HAPI `1.1.0.8.2`.
- **Solar source: PASS.** Wehrli (1985) WMO/WRC extraterrestrial irradiance is selected with deterministic wavelength interpolation and photon-flux conversion.
- **Doppler-only: REJECTED FOR FULL DOMAIN.** Local chemistry-level width ratios do not bound illuminated twilight rays through denser air below 50 km. The pressure-broadening sensitivity exceeded the `0.1%` adequacy criterion for A even for rates above `1e-10 s^-1` and produced much larger differences in selected post-90-degree cases.
- **A iso-1 line shape: SOURCE MATERIALIZATION / PARAMETER-MAPPING BLOCKER.** HITRAN2016 points to Drouin et al. for an advanced speed-dependent + collisional-line-mixing treatment, transformed to HITRAN-facing Rosenkranz parameters. The exact public supplement identity is known (`NIHMS804415-supplement-supplement_1.pdf`, reported 94.8 kB), but its bytes/SHA-256 and executable mapping are not frozen.
- **A iso-2/iso-3 line shape: HISTORICAL PROFILE FAMILY IDENTIFIED / BYTE+MAPPING BLOCKER.** HITRAN2012 and Long et al. document Galatry profiles with Dicke narrowing for the rare A-band isotopologues. The surviving Harvard/CfA archive identifies `07_A-band_SDF.dat` and `07_hit12_0.76mic_Galatry.par`. The rare lines contribute approximately `0.4674%` of total accepted A integrated strength at 296 K, so they cannot simply be omitted against the `0.1%` gate. Exact bytes/hash, deterministic line mapping, and a HITRAN2016 continuity check remain required.
- **B-band line shape: BASELINE CANDIDATE SELECTED.** Use complete classic isolated Voigt from the accepted HITRAN2016 records. Do not reproduce the known defective/partial advanced B qSDV values silently. A source-corrected qSDV sensitivity on covered principal-isotopologue lines is required; if any validated B rate changes by more than `0.1%`, reopen the baseline before freeze.
- **IRA monomer line shape: BASELINE CANDIDATE SELECTED.** Use classic isolated Voigt with accepted HITRAN2016 `gamma_air`, `gamma_self`, `n_air`, and `delta_air`, pending final consistent target+attenuation convergence.
- **Classic B/IRA pressure broadening: SELECTED.** Use `gamma_L=(296/T)^n_air * [gamma_air*(p-p_O2)+gamma_self*p_O2]` with pressures in atm. `gamma_air` is already the HITRAN air-broadening coefficient; do not multiply by another N2/O2 mixture factor.
- **Classic B/IRA pressure shift: SELECTED CANDIDATE.** Use `nu_shifted=nu0+delta_air*p` with shell-local total pressure and no invented temperature dependence. A full-path shift sensitivity remains required. A follows its recovered historical profile conventions.
- **Geometry: PASS.** Retain M4C spherical-ray equations, Earth radius, radiative top and physical shadow semantics. M4D NIR path integration uses deterministic `0.125 km` atmospheric sub-stratification derived from accepted one-kilometre profiles and checks against `0.0625 km`; M4C-R2 production behavior remains untouched.
- **Shellwise transfer: PASS as a design requirement.** O2 optical depth is evaluated shell by shell with local temperature and pressure/profile parameters. Target-temperature cross section times total column is rejected.
- **B/IRA attenuation-wing strategy: CANDIDATE SELECTED.** At each target quadrature node evaluate attenuation from all accepted absorber lines in the band rather than imposing a `+/-10` or `+/-20 cm^-1` absorber cutoff. Target support/order are converged separately.
- **IRA CIA baseline scope: PASS / CLOSURE SENSITIVITY REQUIRED.** Historical `gIRA` remains monomer first-order excitation. HITRAN2016 identifies Maté et al. (1999), DOI `10.1029/1999JD900824`, as the revised 1.27-micron CIA source; pure O2 maps to `O2-O2`, 21:79 O2:N2 to `O2-Air`, and the two must not be double counted. Exact historical CIA bytes/hash and a cold-shell policy below the Maté measurement temperatures (`253`, `273`, `296 K`) remain open before the required twilight sensitivity can run.
- **Numerical spectroscopy specification: PARTIAL / NOT FROZEN.** Standard HITRAN scaling, historical TIPS interpolation, Wehrli forcing, unattenuated `g0(T)` anchors, shellwise transfer, M4D path sub-stratification, and B/IRA classic-profile candidates are selected. Final A auxiliary materialization plus the full profile/convergence/sensitivity runs remain open.

Current live HITRAN/HAPI data are not used as a silent historical substitute. The remaining source problem is now byte materialization and deterministic mapping of identified historical auxiliary sources, not an undefined choice of spectroscopy.

### M4D primary design documents

- `docs/m4d_spectralcalc_export_forensics.md`
- `docs/m4d_tips2017_provenance_recovery.md`
- `docs/m4d_solar_forcing_freeze.md`
- `docs/m4d_broadening_and_geometry_freeze.md`
- `docs/m4d_ira_cia_scope_freeze.md`
- `docs/m4d_numerical_specification.md`
- `docs/m4d_final_design_review.md`
- `docs/m4d_pressure_broadening_provenance_followup.md`
- `docs/m4d_a_band_auxiliary_source_recovery.md`
- `docs/m4d_ira_cia_historical_source_recovery.md`

Earlier research/forensics notes remain supporting evidence and are not superseded as provenance records.

### Immediate next gate

1. Freeze `NIHMS804415-supplement-supplement_1.pdf` bytes/hash and executable Drouin/HITRAN2016 mapping for A iso-1.
2. Freeze `07_A-band_SDF.dat` and `07_hit12_0.76mic_Galatry.par` bytes/hash, map accepted A iso-2/iso-3 transitions, and verify HITRAN2016 continuity.
3. Freeze the exact historical HITRAN2016 Maté `O2-Air` CIA asset and select an explicit cold-shell policy below 253 K.
4. Run B and IRA classic-Voigt target excitation and shell attenuation consistently using all accepted absorber lines at target quadrature nodes; quantify pressure-shift sensitivity and corrected B qSDV sensitivity.
5. Run A iso-1 advanced and A iso-2/3 Galatry representations consistently once materialized.
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
