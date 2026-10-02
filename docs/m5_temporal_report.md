# M5 temporal reference report

## Current decision

**GO M5A - validated finite-horizon temporal initial-value simulation of the reference dawn.**

The accepted scope is the reference noon -> afternoon -> night -> next dawn -> SZA=60 trajectory, lasting **75600 s (21 hours)**. Asymptotic periodicity is not required. The former 90-day experiment is closed as a historical diagnosis of alternating response plus slow multi-day drift; no additional spin-up days are executed.

This GO concerns the frozen-reference reduced model and its temporal solver. It is not a validated atmosphere-wide climatology or the final date/latitude/longitude API.

## Model and reference inputs

M5 state: O, O3, H, OH, HO2, H2O2, Delta, at 51 levels (50..100 km): **357 ODEs**. R_H=OH+HO2 is diagnostic. O1D/B0/B1 alone remain QSSA. All seven species evolve freely after t0; no equilibrium enforcement, nighttime reset or clipping is used.

M3/M4, original close_local_chemistry, reaction topology, kinetic constants and forcing are unchanged. H2O2 tendency remains HO2_HO2-H2O2_PHOTOLYSIS-OH_H2O2, without a factor 1/2 on the self-reaction event. OH/HO2 preserve the accepted family budget.

Reference initialization: 2020-03-20, 45 N, longitude 0, LST=12, SZA=45 in ReferenceEquinoxSolarCycle, frozen M4A. The reference cycle is explicit equinox geometry, not a calendar astronomy implementation. Radiation is dynamic M4C UV with evolving O/O3 opacity and M4D A0/B/IRA, including historical CIA attenuation only; no transport.

O3 at t0 uses M4A O3_socrates_reference_cm3. O and H use their finite native MSIS columns from the verified frozen M4A CSV. H exists in that asset although the original runtime background class does not expose it; M5 reads the asset without altering M4A. Both native atomic columns are unavailable at **50..72 km**. The nominal initial value is exactly zero there, as an explicit reference convention; no MSIS extrapolation or small-positive substitution is introduced. Photo/chemical tendencies subsequently create the atoms dynamically.

## Noon stationary fast subsystem and numerical uniqueness

With O/O3/H and the corresponding noon forcing fixed, OH/HO2/H2O2/Delta are solved simultaneously from the accepted seven-species temporal RHS. Positive log coordinates enforce positivity. Seven widely separated seeds per height are attempted, with fixed-rate basin localization followed by relative-rate polishing. Peroxide and Delta production/loss ratios provide numerical seeds only at t0. No time-dependent closure is introduced.

At least five independent physical convergences are obtained at every height in each variant. All physical roots agree far within the 1e-4 relative distinct-root threshold. Failed numerical attempts remain recorded and are not counted as physical roots. This establishes numerical multistart seed independence, not a mathematical global uniqueness theorem.

| Variant | Minimum converged physical seeds / height | Maximum normalized fast residual | Maximum root relative spread |
| --- | ---: | ---: | ---: |
| nominal | 5 | 2.531e-14 | 1.986e-13 |
| low | 5 | 3.276e-14 | 9.281e-14 |
| high | 5 | 4.953e-14 | 3.171e-13 |
| missing_bound | 6 | 2.531e-14 | 1.986e-13 |

O1D/B0/B1 retain their accepted strictly positive loss denominators. The initializer is separate from the integrator; an explicitly supplied initial state can be passed directly to the reference temporal engine.

## Completion and solver verification

Nominal BDF base, tighter BDF and tighter Radau all complete noon -> next-dawn -> SZA60. Low/high native-atom and missing-atom-bound variants complete with base BDF. The stored nominal fields use **tighter BDF**, with Radau as independent verification.

| Comparison over the full time-height state | Maximum relevant relative difference | Outcome |
| --- | ---: | --- |
| BDF base vs tighter BDF | 0.045420% | PASS |
| Tighter BDF vs Radau | 0.001248% | PASS |

The near-zero floor is max(1 cm^-3, 1e-6 of the full species time-height peak). Below it, convergence is checked against an absolute bound of 0.005 times that declared floor. All seven species pass both relative and absolute checks. NIR interpolation retains its prior 276-node audit: 0.497655% maximum midpoint relative error; exact shadow.

Every run has finite/nonnegative concentrations, exact shadow in all eleven forcings, physical O1D/B0/B1 and accepted OH+HO2 / dynamic H2O2 budgets. Largest scaled residuals: QSSA **3.848e-16**, family **2.722e-16**, peroxide **4.093e-16**. The accepted solver trajectories require zero invalid-trial rejections in these runs.

Software fix: adding the day offset collapsed two nearly identical floating final timestamps. Output sampling now retains the last identical physical endpoint and has strictly increasing time. This correction does not change ODEs, forcing or the integrated physical state. Initial O/H zeros are carried exactly by illuminated linear coordinates, not clipped into a log-positive seed.

## Initialization sensitivity

- Nominal: finite native O/H, exact zero for missing native atoms.
- Low: finite native O/H multiplied by 0.5; missing values remain zero.
- High: finite native O/H multiplied by 2; missing values remain zero.
- Missing bound: native finite values unchanged; unavailable O/H initialized to **1e-8 times M**. This 10-ppb fraction is a declared numerical sensitivity bound, not a physical profile or the nominal baseline.

Every variant re-solves the four-variable fast subsystem at noon. Sensitivities compare variant base-BDF fields with the nominal tighter-BDF fields during the dawn window. Relevant differences use abs(a-b)/max(a,b); near-zero differences are absolute. The solver discrepancy is much smaller than the material sensitivities. No sensitivity percentage is an automatic acceptance gate.

| Variant | Dawn maximum O3 difference | Dawn maximum Delta difference | Near-zero Delta max absolute difference (cm^-3) |
| --- | ---: | ---: | ---: |
| low | 72.4953% | 71.3846% | 864.8 |
| high | 51.0824% | 70.5681% | 1371 |
| missing_bound | 21.6170% | 14.0773% | 11.13 |

Per-height maxima over the dawn window:

| Variant | z (km) | O3 relevant difference | Delta relevant difference |
| --- | ---: | ---: | ---: |
| low | 60 | 0.1041% | 0.0637% |
| low | 70 | 0.1569% | 0.0930% |
| low | 80 | 2.4678% | 4.7947% |
| low | 90 | 46.4385% | 71.0954% |
| low | 100 | 48.4777% | 69.2379% |
| high | 60 | 0.1753% | 0.1065% |
| high | 70 | 0.2639% | 0.1529% |
| high | 80 | 12.5958% | 8.2461% |
| high | 90 | 43.8697% | 68.6888% |
| high | 100 | 47.9118% | 62.7476% |
| missing_bound | 60 | 11.1919% | 6.0975% |
| missing_bound | 70 | 7.8111% | 4.6002% |
| missing_bound | 80 | 8.2200% | 2.6558% |
| missing_bound | 90 | 5.0494% | 9.8630% |
| missing_bound | 100 | 5.7936% | 5.8518% |

These differences are material and limit the scientific interpretation of this reference initialization. A later climatological initialization must address them. They do not justify changing the accepted chemistry. Secondary O/H/HOx sensitivities and per-species absolute values are in the existing evidence JSON.

## Dawn tables and time-height artifact

The nominal next-dawn window is SZA99 -> 60. The following samples use SZA99, 85 and 60 at 60/70/80/90/100 km. Concentrations are cm^-3; forcing frequencies are s^-1.

The complete continuous nominal time-height fields, dawn mask, reference date/location, time since noon, SZA, seven dynamic species, diagnostic R_H, O1D/B0/B1 and all eleven forcings are saved in [m5_reference_cycle.npz](../evidence/m5_reference_cycle.npz). The existing evidence JSON records the artifact SHA256, input policy, all initial multistart outcomes, convergence and sensitivities. This is a finite-horizon reference trajectory, not a periodic cycle.

### Scientific outputs

| SZA | z (km) | O3 | Delta |
| ---: | ---: | ---: | ---: |
| 99 | 60 | 1.15858e+09 | 1.43219e-13 |
| 99 | 70 | 1.74182e+08 | 0.0101903 |
| 99 | 80 | 7.47384e+06 | 5948.35 |
| 99 | 90 | 4.18316e+08 | 1.48179e+07 |
| 99 | 100 | 1.3142e+08 | 6.49209e+06 |
| 85 | 60 | 6.96724e+08 | 3.93285e+09 |
| 85 | 70 | 2.74379e+07 | 1.68881e+09 |
| 85 | 80 | 829186 | 6.12761e+08 |
| 85 | 90 | 4.36899e+07 | 1.06312e+09 |
| 85 | 100 | 4.44408e+06 | 1.30448e+08 |
| 60 | 60 | 7.28019e+08 | 6.07574e+09 |
| 60 | 70 | 2.94639e+07 | 3.29093e+09 |
| 60 | 80 | 4.64041e+06 | 1.36129e+09 |
| 60 | 90 | 4.31893e+07 | 1.43538e+09 |
| 60 | 100 | 4.44188e+06 | 1.65929e+08 |

### Other dynamic concentrations and family diagnostic

| SZA | z (km) | O | H | OH | HO2 | H2O2 | R_H |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 99 | 60 | 6.02373 | 1.30586 | 167096 | 318441 | 2.48246e+06 | 485537 |
| 99 | 70 | 1162.48 | 17.6006 | 636844 | 48694.3 | 792300 | 685538 |
| 99 | 80 | 182689 | 2575.84 | 533011 | 80415.8 | 292879 | 613427 |
| 99 | 90 | 2.44088e+11 | 6.98526e+07 | 34459 | 256.439 | 0.00835804 | 34715.4 |
| 99 | 100 | 5.66351e+11 | 1.91892e+07 | 1045.71 | 1.08922 | 2.0336e-07 | 1046.8 |
| 85 | 60 | 6.5172e+08 | 1.38157e+06 | 2.53474e+07 | 1.35325e+07 | 2.54501e+06 | 3.888e+07 |
| 85 | 70 | 3.54081e+08 | 5.30134e+06 | 1.1532e+07 | 6.04389e+06 | 747953 | 1.75759e+07 |
| 85 | 80 | 2.05022e+08 | 7.61593e+06 | 1.60481e+06 | 740637 | 216334 | 2.34545e+06 |
| 85 | 90 | 2.42872e+11 | 7.05723e+07 | 4099.05 | 260.366 | 0.00680168 | 4359.42 |
| 85 | 100 | 5.65963e+11 | 1.92521e+07 | 37.9296 | 1.09352 | 1.58741e-07 | 39.0231 |
| 60 | 60 | 6.91255e+08 | 1.46075e+06 | 2.54009e+07 | 1.35441e+07 | 2.72899e+06 | 3.8945e+07 |
| 60 | 70 | 3.82264e+08 | 5.84484e+06 | 1.18324e+07 | 6.19023e+06 | 792803 | 1.80227e+07 |
| 60 | 80 | 1.20888e+09 | 4.74449e+07 | 1.68549e+06 | 793745 | 102543 | 2.47924e+06 |
| 60 | 90 | 2.42078e+11 | 7.46323e+07 | 4313.16 | 276.243 | 0.0043841 | 4589.4 |
| 60 | 100 | 5.66557e+11 | 1.95213e+07 | 38.5581 | 1.10764 | 9.6505e-08 | 39.6657 |

### Remaining QSSA concentrations

| SZA | z (km) | O1D | B0 | B1 |
| ---: | ---: | ---: | ---: | ---: |
| 99 | 60 | 0 | 2.18522e-17 | 0 |
| 99 | 70 | 0 | 9.21354e-13 | 0 |
| 99 | 80 | 2.48071e-16 | 14.47 | 0.00878644 |
| 99 | 90 | 3.37974e-14 | 26541.2 | 0.0349912 |
| 99 | 100 | 1.47373e-20 | 30550.9 | 0.0860524 |
| 85 | 60 | 22.2567 | 336626 | 66.0341 |
| 85 | 70 | 3.48235 | 503935 | 29.9649 |
| 85 | 80 | 0.570252 | 584099 | 24.6688 |
| 85 | 90 | 122.408 | 739671 | 310.366 |
| 85 | 100 | 73.3 | 198633 | 192.054 |
| 60 | 60 | 23.6674 | 654184 | 70.6041 |
| 60 | 70 | 3.89654 | 670361 | 31.3179 |
| 60 | 80 | 6.58134 | 650449 | 38.3479 |
| 60 | 90 | 127.864 | 759856 | 323.162 |
| 60 | 100 | 388.727 | 431169 | 918.612 |

### Eight M4C photolysis frequencies

| SZA | z (km) | JH | J_SRC | J_LYA | J_O2_TOTAL | J_O3_TOTAL | J_H2O2 | J_H2O_A | J_H2O_B |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 99 | 60 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 99 | 70 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 99 | 80 | 4.61607e-19 | 0 | 0 | 0 | 5.17913e-06 | 1.38642e-06 | 3.41381e-41 | 0 |
| 99 | 90 | 2.35767e-19 | 0 | 0 | 6.57494e-284 | 5.07649e-06 | 1.3549e-06 | 7.66665e-42 | 0 |
| 99 | 100 | 6.3321e-26 | 0 | 0 | 1.51517e-115 | 3.49564e-06 | 1.10481e-06 | 1.89684e-56 | 0 |
| 85 | 60 | 0.00777837 | 0 | 2.36779e-50 | 5.01597e-10 | 0.00788916 | 8.93599e-05 | 1.49367e-06 | 3.85477e-48 |
| 85 | 70 | 0.00791607 | 4.86009e-268 | 1.22133e-18 | 5.18878e-10 | 0.00802703 | 9.05689e-05 | 1.49634e-06 | 1.98832e-16 |
| 85 | 80 | 0.0079203 | 3.0307e-62 | 3.96159e-11 | 5.61871e-10 | 0.00803139 | 9.05085e-05 | 1.54855e-06 | 6.44947e-09 |
| 85 | 90 | 0.00792962 | 9.13073e-19 | 1.53552e-09 | 2.05931e-09 | 0.00804419 | 9.04612e-05 | 3.51913e-06 | 2.49982e-07 |
| 85 | 100 | 0.00794271 | 6.14186e-10 | 3.23318e-09 | 4.42754e-09 | 0.00806123 | 9.05609e-05 | 5.76532e-06 | 5.26675e-07 |
| 60 | 60 | 0.00791581 | 2.11772e-226 | 4.03987e-17 | 5.19528e-10 | 0.00802677 | 9.11871e-05 | 1.49632e-06 | 6.57691e-15 |
| 60 | 70 | 0.00794298 | 4.37581e-58 | 5.67166e-11 | 5.79675e-10 | 0.00805411 | 9.09612e-05 | 1.57155e-06 | 9.23347e-09 |
| 60 | 80 | 0.00794472 | 1.95238e-18 | 1.58851e-09 | 2.11278e-09 | 0.00805941 | 9.07213e-05 | 3.58925e-06 | 2.58609e-07 |
| 60 | 90 | 0.00794714 | 4.66618e-10 | 3.20806e-09 | 4.24598e-09 | 0.0080656 | 9.05916e-05 | 5.73022e-06 | 5.22538e-07 |
| 60 | 100 | 0.00794977 | 5.99666e-08 | 3.69924e-09 | 6.62261e-08 | 0.00806959 | 9.06115e-05 | 6.95118e-06 | 6.09948e-07 |

### M4D baseline frequencies

| SZA | z (km) | gA | gB | gIRA |
| ---: | ---: | ---: | ---: | ---: |
| 99 | 60 | 0 | 0 | 0 |
| 99 | 70 | 0 | 0 | 0 |
| 99 | 80 | 1.58447e-14 | 1.33891e-13 | 1.83149e-14 |
| 99 | 90 | 1.28437e-13 | 5.22712e-13 | 3.58037e-13 |
| 99 | 100 | 1.69926e-12 | 1.32762e-12 | 1.13833e-12 |
| 85 | 60 | 1.78053e-09 | 3.25179e-10 | 1.42612e-10 |
| 85 | 70 | 4.19933e-09 | 3.49718e-10 | 1.4505e-10 |
| 85 | 80 | 5.66219e-09 | 3.56285e-10 | 1.45621e-10 |
| 85 | 90 | 6.07868e-09 | 3.57557e-10 | 1.45656e-10 |
| 85 | 100 | 6.1722e-09 | 3.57611e-10 | 1.45563e-10 |
| 60 | 60 | 4.55549e-09 | 3.52001e-10 | 1.45404e-10 |
| 60 | 70 | 5.7259e-09 | 3.5679e-10 | 1.4576e-10 |
| 60 | 80 | 6.08987e-09 | 3.57861e-10 | 1.45778e-10 |
| 60 | 90 | 6.173e-09 | 3.57886e-10 | 1.45689e-10 |
| 60 | 100 | 6.189e-09 | 3.57669e-10 | 1.45569e-10 |

## Historical diagnostics and QA

The dark SZA99 continuum, old OH/HO2 QSSA root failure and old H2O2 dark singularity remain reproducible regressions. Dynamic OH/HO2/H2O2 resolved the temporal QSSA assumptions without changing reactions. The 90 additional ordinary spin-up days remain historical evidence of slow multi-day drift and no certified attractor in that horizon. This reduced frozen-atmosphere/no-transport drift is not asserted as atmospheric behavior and is no longer an M5A gate. Further spin-up modes are disabled in the public validator.

Full pytest: **870 tests + 13 subtests PASS**. Ruff and five historical validators PASS. M4C-R2 SHA256 remains 2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe. M3/M4 accepted code and main are unchanged; M4D remains NOT FROZEN. The raw HITRAN export and intermediate caches remain outside Git.

## Reproduction and next scope

The existing validator defaults to noon. Run nominal with --noon-solver base, tight and Radau; low, high and missing_bound variants with --noon-variant. Mode noon-assessment rechecks the six complete cached trajectories, initial fast roots, physical budgets and convergence before exporting the nominal artifact and returning GO. Use PYTHONPATH=src;. on Windows.

    python scripts/validate_m5_temporal.py --sources <frozen-m4d-sources> --hitran <authorized-HITRAN2016-export> --cache <derived-cache> --mode noon --noon-variant nominal --noon-solver base
    python scripts/validate_m5_temporal.py --sources <frozen-m4d-sources> --hitran <authorized-HITRAN2016-export> --cache <derived-cache> --mode noon-assessment

The next scientific scope is real date/latitude/longitude solar geometry while retaining this reference-noon case as regression. Atmospheric dynamics are not implemented here. The final API should permit explicit initial_state injection in addition to any future automatic initialization policy.
