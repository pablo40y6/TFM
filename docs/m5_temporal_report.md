# M5 temporal reference report

## Current decision

**M5A ACCEPTED / CLOSED - validated finite-horizon reference temporal simulation. M5B GO - real solar geometry with explicit initial state.**

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

## M5A historical diagnostics and acceptance QA

The dark SZA99 continuum, old OH/HO2 QSSA root failure and old H2O2 dark singularity remain reproducible regressions. Dynamic OH/HO2/H2O2 resolved the temporal QSSA assumptions without changing reactions. The 90 additional ordinary spin-up days remain historical evidence of slow multi-day drift and no certified attractor in that horizon. This reduced frozen-atmosphere/no-transport drift is not asserted as atmospheric behavior and is no longer an M5A gate. Further spin-up modes are disabled in the public validator.

Full pytest: **870 tests + 13 subtests PASS**. Ruff and five historical validators PASS. M4C-R2 SHA256 remains 2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe. M3/M4 accepted code and main are unchanged; M4D remains NOT FROZEN. The raw HITRAN export and intermediate caches remain outside Git.

## M5A reproduction and original handoff scope (historical)

The existing validator defaults to noon. Run nominal with --noon-solver base, tight and Radau; low, high and missing_bound variants with --noon-variant. Mode noon-assessment rechecks the six complete cached trajectories, initial fast roots, physical budgets and convergence before exporting the nominal artifact and returning GO. Use PYTHONPATH=src;. on Windows.

    python scripts/validate_m5_temporal.py --sources <frozen-m4d-sources> --hitran <authorized-HITRAN2016-export> --cache <derived-cache> --mode noon --noon-variant nominal --noon-solver base
    python scripts/validate_m5_temporal.py --sources <frozen-m4d-sources> --hitran <authorized-HITRAN2016-export> --cache <derived-cache> --mode noon-assessment

The original M5A handoff scope was real date/latitude/longitude solar geometry while retaining this reference-noon case as regression. Atmospheric dynamics are not implemented here. The final API should permit explicit initial_state injection in addition to any future automatic initialization policy.


## M4D final downstream A0/A1 validation

**M4D CLOSED / ACCEPTED for temporal model.** A0 remains the baseline; A1 changes exactly 91 principal d lines to Drouin SDV, with 339 Voigt lines and no LM/Galatry. The continuous 21-hour reference run is repeated with identical atmosphere, dynamic UV, native O/O3/H initial policy, chemistry and tighter BDF controls. A1 re-solves the four noon fast equations; its initializer has at least five physical seed convergences per height, maximum residual 2.53e-14, and no distinct roots. B/IRA use exactly the A0 provider, including interpolation.

Statistics below use symmetric relative difference for concentrations above max(1 cm^-3, 1e-6 of the full nominal time-height species peak), with absolute reporting below that floor. Max/p90/p99 apply to relevant dawn samples, SZA 99 -> 60, over 51 heights. Near-zero concentrations are not assigned relative errors.

| Species | max (%) | p90 (%) | p99 (%) | max absolute (cm^-3) | max relevant case z / SZA |
| --- | ---: | ---: | ---: | ---: | --- |
| O3 | 0.000122437 | 7.28844e-06 | 3.5645e-05 | 334.47203 | 81 km / 94.415 deg |
| Delta | 0.233878 | 0.0244668 | 0.218352 | 120329.66 | 77 km / 97.3656 deg |

| z (km) | O3 max / p90 / p99 (%) | O3 max abs (cm^-3) | Delta max / p90 / p99 (%) | Delta max abs (cm^-3) |
| ---: | --- | ---: | --- | ---: |
| 60 | 2.33909e-06 / 6.852e-07 / 1.55153e-06 | 23.57984 | 0.155388 / 0.0238025 / 0.122829 | 49612.936 |
| 70 | 3.63983e-05 / 3.5645e-05 / 3.5811e-05 | 62.702043 | 0.195432 / 0.103141 / 0.182882 | 7150.6138 |
| 80 | 8.4457e-05 / 8.107e-06 / 7.46966e-05 | 1.4264135 | 0.223441 / 0.196352 / 0.222038 | 677.78837 |
| 90 | 2.80043e-05 / 1.01797e-07 / 1.20228e-05 | 36.30762 | 0.000604216 / 0.000383798 / 0.000565569 | 95.874046 |
| 100 | 5.31764e-05 / 9.27117e-08 / 1.70422e-05 | 22.134077 | 0.000148709 / 0.000138053 / 0.000148613 | 29.58157 |

Near-zero maximum absolute differences: O3 0, Delta 116.802 cm^-3. The very small O3 difference is below the established solver error bound and should not be interpreted as a resolved physical effect. Delta remains below 1%; optional LM/Galatry spectroscopy does not delay the temporal model. No PR #4 merge or new advanced-spectroscopy assumptions are made.

## M5B real solar geometry and explicit initial-value API

**GO M5B. M5A is ACCEPTED / CLOSED.** The reference-noon run and m5_reference_cycle.npz are unchanged golden regressions. Spin-up, previous QSSA relaxations and the accepted noon initialization policy are not reopened.

The implemented algorithm is the documented [NOAA fractional-year solar equations](https://gml.noaa.gov/grad/solcalc/solareqns.PDF). It computes declination and equation of time from the UTC fractional year (366-day denominator in leap years), then true solar time/hour angle and geometric SZA from latitude. All datetimes must be timezone-aware and are normalized to UTC; longitude is east-positive [-180,180], latitude [-90,90], and SZA is in degrees. No civil timezone, refraction or solar-disk correction enters the SZA. This is the published Fourier approximation, not a precision ephemeris; no global sub-degree accuracy claim is made.

Polar day/night follow directly from the geometric SZA. The accepted spherical M4C/M4D shell geometry alone determines shadow by height. The temporal engine brackets the 51 tangent crossings, including narrow grazing twilight by independently finding extrema, and retains the accepted segment solver and positivity rejection. Exact zero initial values also work in polar darkness; no clipping, reset or extra prognostic species is introduced.

```python
from tfm_photochem.m5_simulation import simulate

result = simulate(start_datetime, end_datetime, latitude, longitude,
                  initial_state, atmosphere="frozen_reference")
result.save("trajectory.npz")
```

initial_state is mandatory and explicit, shape (51,7), in cm^-3 and species order O/O3/H/OH/HO2/H2O2/Delta. Geometry never determines the chemical initial state. reference_noon_initialization remains exclusively a reference regression mode. The default radiation provider is a SHA-verified derived A0/B/IRA table spanning SZA=0 through the highest shell tangent, with direct midpoint interpolation audit <=0.5%; it contains no raw HITRAN. An explicitly supplied verified NIR provider can override it. The frozen M4A atmosphere remains the 2020-03-20 45N/0E reference even for other geometry locations, recorded by atmosphere_tracks_location=False. No dynamic atmosphere or climatological initializer is implemented.

SimulationResult/save retain elapsed time from the metadata UTC origin, altitude, SZA, all seven dynamic fields, exact R_H, O1D/B0/B1, eleven forcings and geometry/atmosphere/initialization/solver metadata. The completed real-geometry 21-hour example is saved in [m5b_reference_real_geometry.npz](../evidence/m5b_reference_real_geometry.npz); it explicitly injects the M5A golden noon state and does not assert equilibrium at actual astronomical noon.

### Validation and numerical regression

| Check over 21 hours / full seven-species time-height state | Maximum relevant difference | Outcome |
| --- | ---: | --- |
| A0 repeat vs M5A golden | 0% | PASS |
| General API + explicit golden geometry vs M5A NPZ | 0.000965912% | PASS |
| Real geometry BDF base vs tighter BDF | 0.247077% | PASS |
| Real geometry tighter BDF vs tighter Radau | 0.0117191% | PASS |

Absolute near-zero bounds also pass. All completed trajectories are finite/nonnegative with remaining QSSA and family/peroxide budget residuals below 1e-12, plus exact shadow. Radau rejects 72 invalid Newton trial states using the existing M5A step-retry strategy; all accepted states remain physical, and there is no concentration projection or physical reset.

Geometry tests cover equinox 45N approximate agreement with the old trajectory, noon/midnight, geometric sunrise/sunset, longitude shifts, UTC equivalent instants, hemisphere reversal, solstices, polar day/night, grazing twilight, leap-date continuity and invalid inputs. At 2020-03-20 12:00Z /45N/0E, SZA=45.18534 degrees and equation of time=-7.92441 minutes; geometric ground horizon crossings are about 06:08:59 and 18:07:39 UTC.

Real geometry is not expected to reproduce the artificial trajectory at identical UTC timestamps: equation of time and declination shift the onset. The very large relative differences possible near that onset are phase/forcing changes, not solver nonconvergence. Solver agreement is evaluated using the same real geometry; the original toy trajectory is retained by an explicit ReferenceElapsedGeometry adapter without changing ReferenceEquinoxSolarCycle.

Final QA: **887 tests + 13 subtests PASS**, ruff PASS, five historical validators PASS, M4D mapping PASS (91/70/21/59/280, no unmatched/duplicate/ambiguous lines). M4C-R2 retains SHA256 2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe. M3/M4 accepted code, M5A source and golden NPZ, reaction/constant/forcing definitions and main are unchanged.

Reproduce with scripts/validate_m5b_temporal.py --mode downstream --a-model A0/A1; --mode geometry --geometry golden/real --solver base/tight/Radau; --mode nir for the full-SZA frozen provider; then --mode assess. Supply the verified historical --sources, authorized --hitran and local --cache for trajectory reproduction. Assessment reads the derived cache and returns the combined downstream/geometry decision. No periodic-search mode is invoked.

## M5C execution specification (authorized)

Numerical refinement amendment: the initial coupled 2-hour/1-hour linear grids fail the O3/Delta output criterion (3.94% / 1.49%). An independent 1-minute MSIS sampling audit does not establish a useful PCHIP improvement; linear interpolation is retained. Temperature/native-density and expensive NIR-rate grids will therefore be independently refinable: default background 300 s, NIR 3600 s, with NIR snapshots an exact subset of the same precomputed MSIS data. Certification compares background 600/300 s at fixed NIR cadence and NIR 7200/3600 s at fixed fine background, refining further if needed. No RHS MSIS calls, extrapolation, negative-value clipping or chemical changes are permitted. Both errors must pass approximately 0.5% in O3/Delta before closure.

M5A/M5B are ACCEPTED; their NPZ files and reference atmosphere/solar trajectory remain golden. M4D A0/B/IRA is CLOSED / ACCEPTED for temporal use. M5C changes prescribed background fields only, without changing chemistry, constants or accepted radiation equations. Seven concentrations remain dynamic in cm^-3; no transport, dilution term or new QSSA is added.

Separate runtime MSIS-00 provider: pymsis==0.12.0, version=0, all accepted M4A option switches equal to 1. Every MSIS call supplies explicit previous-day F107, 81-day F107a and daily Ap; no automatic space-weather access. QuietReferenceActivity defaults to 150/150/4. M equals the sum of the seven ordinary native neutral densities, excluding anomalous O; unavailable native trace contributions are explicitly zero in this sum, retaining their NaN availability mask. Convert m^-3 to cm^-3 by 1e-6. T/M must be strictly positive and finite. O2=0.21M, N2=0.78M, CO2=405e-6M. H2O/H2/SOCRATES O3 VMR profiles stay prescribed; the O3 VMR is not a date-dependent climatology. Outside 50..100 km, native MSIS O is used with unavailable values zero; within the domain O/O3 come from the ODE state.

Atmosphere is precomputed on an explicit UTC time grid and linearly interpolated in T/densities. The API defaults to 300-s background nodes and 3600-s NIR snapshots, an exact subset of the same native MSIS array. M4D transfer equations are unchanged; rates interpolate between snapshots at the actual SZA. Each table covers its reachable angular interval and undergoes direct midpoint auditing. Certify native-background 600/300 s and NIR 7200/3600 s independently; refine if either exceeds about 0.5% in O3/Delta. No pymsis calls occur in the RHS. BDF/tighter Radau agreement <=0.5%, finite/nonnegative output, positive remaining QSSA denominators and exact shadow remain required. Large temporary exact-opacity buffers are explicitly released between atmosphere snapshots.

Automatic reference_noon finds the preceding local apparent solar noon, builds that background, seeds SOCRATES O3/native O/H (unavailable atoms exactly zero), solves the accepted four fast stationary equations with multistart positivity, and integrates to the requested start. This is an approximate reference bootstrap, never a validated climatology. An explicit initial_state skips it completely. Exactly one initialization route must be selected. Additional cases cover season, hemisphere, longitude and high latitude. Stop only for the authorized physical/numerical/initializer failures; do not reopen historical spin-up/QSSA decisions.

Runtime NIR numerical optimization, verified before adoption: retain accepted moment/Voigt equations, use far_order=8 / near_cm1=0.25 for fresh rates, and reuse verified direct far_order=4 / near_cm1=2 cache values with per-row provenance. All five complete noon rate profiles agree to rounding; frozen twilight SZA95/97/99 differs by at most 5.872e-10 relative. Exact-Voigt audits sample every historical transition core, both sides of the 0.25-cm^-1 boundary and inter-line midpoints at eleven shells, across five backgrounds; maximum relative cross-section difference is 6.765e-6. The runtime computes nominal outputs only by removing unused CIA envelope/raw diagnostic evaluations from a privately compiled copy of the accepted function; tests require bit-identical retained outputs. Frozen M4D source and frozen M5B provider remain unchanged.

## M5C closure: dynamic prescribed atmosphere and automatic reference bootstrap

**GO M5C.** The accepted 357-ODE chemistry, remaining O1D/B0/B1 QSSA, M5A/M5B goldens, frozen M4A assets and M3/M4/M4D source are unchanged. This is a finite-horizon model with prescribed MSIS variability and no transport. It does not establish a climatological initial state or periodic attractor. No further large block is started.

DynamicMSISAtmosphere precomputes MSIS-00 (pymsis 0.12.0, accepted all-one option vector) over 0..150 km. The API uses 300-s native-background nodes and exact-subset 3600-s NIR snapshots, with linear interpolation and no RHS MSIS/source-file calls. Every runtime kinetic coefficient is evaluated at the current interpolated T/M. QuietReferenceActivity defaults to F107=150, F107a=150, Ap=4; ActivityDrivers accepts explicit UTC series with declared previous-day/81-day-mean/daily-Ap semantics and rejects missing coverage. No space-weather lookup/download occurs.

The accepted O2/N2/CO2 and prescribed H2O/H2 VMR conventions are retained. Ordinary M excludes anomalous oxygen; unavailable native trace values contribute exact zero while their availability remains recorded. M4C uses dynamic chemical O/O3 inside 50..100 km and the dynamic native-O/SOCRATES-VMR exterior. The exterior O3 profile is explicitly a reference VMR, not a date-dependent climatology. Dynamic NIR remains A0/B/IRA with historical CIA attenuation and unchanged nominal CIA temperature policy.

reference_noon finds the previous apparent solar noon, takes current native O/H and reference O3, solves the accepted four fast equations with seven positive multistart seeds, then integrates continuously to the requested start. Every tested height has at least five physical convergences to the same root. The initializer is applied only at noon; all seven species evolve freely afterwards. The API requires exactly one initialization route; supplying initial_state skips noon/root/bootstrap completely.

```python
from tfm_photochem.dynamic_atmosphere import QuietReferenceActivity
from tfm_photochem.dynamic_radiation import HistoricalNIRInputs
from tfm_photochem.m5_simulation import simulate

inputs = HistoricalNIRInputs(sources_dir, authorized_hitran_file)
result = simulate(start_datetime, end_datetime, latitude, longitude,
                  atmosphere="dynamic_msis", initialization="reference_noon",
                  activity=QuietReferenceActivity(), radiation_inputs=inputs,
                  cache=local_cache, background_step_s=300, radiation_step_s=3600)
result.save("trajectory.npz")
```

Alternatively supply initial_state (51x7, cm^-3), omitting initialization. atmosphere="frozen_reference" preserves the golden path. Dynamic radiation needs the authorized historical local sources or an explicitly precomputed DynamicNIRForcing; raw HITRAN is never packaged. Install the existing background-gen optional dependency for pinned pymsis. Datetimes are aware UTC, longitude east-positive; initialization is labelled approximate reference bootstrap in output metadata.

### Numerical certification

The continuous 21-hour equinox run uses the same explicit M5B golden noon state for all interpolation/solver comparisons. Relative differences use max(1 cm^-3, 1e-6 of the species peak) as the relevance floor and a symmetric denominator; below that floor the absolute difference is assessed. The original coupled 2-hour/1-hour grids fail (O3 3.94%, Delta 1.49%). Refining native atmosphere separately fixes that numerical error; a direct 1-minute MSIS audit did not support replacing linear interpolation by PCHIP.

| Comparison, full 21-hour trajectory | O3 max (%) | Delta max (%) | Outcome |
| --- | ---: | ---: | --- |
| Native background 600 / 300 s, NIR fixed 3600 s | 0.183255 | 0.0120341 | PASS |
| NIR snapshots 7200 / 3600 s, background fixed 300 s | 0.000614071 | 0.0554322 | PASS |
| BDF base / tighter BDF | 0.0378396 | 0.0236265 | PASS |
| Tighter BDF / tighter Radau | 0.00269619 | 0.000624184 | PASS |

Maximum over all seven relevant species: BDF base/tight 0.423641%; BDF tight/Radau 0.00946013%. All near-zero absolute bounds pass. Controls: base BDF rtol=2e-6/atol=1e-8/max_step=120 s; tighter BDF/Radau 2e-8/1e-10/60 s. Direct NIR angular midpoint audits remain below 0.5%. Radau rejects 72 invalid Newton trial states using the existing step-retry mechanism; accepted states stay nonnegative without projection/reset.

All completed reference trajectories retain finite/nonnegative state, strictly positive remaining QSSA denominators, exact solar shadow and exact R_H=OH+HO2. Normalized remaining-QSSA/family/peroxide residuals are below 5.2e-16. Exact-Voigt, original numerical-control and frozen twilight checks certify the NIR performance optimization; no spectral line, reaction, physical constant or forcing definition was changed.

### Automatic-route cases

Each location below runs an actual noon multistart solve, a 60-s bootstrap and a 120-s requested integration. These smoke cases complement the full reference day; they are not global climatological validation.

| Case | Latitude / east longitude | UTC apparent noon | max root spread | Outcome |
| --- | --- | --- | ---: | --- |
| equinox | 45 / 0 | 2020-03-20T12:07:55.363681+00:00 | 1.98e-13 | PASS |
| summer | 45 / 0 | 2020-06-21T12:01:26.679355+00:00 | 2.1e-13 | PASS |
| south | -45 / 0 | 2020-12-21T11:57:50.565321+00:00 | 2.26e-13 | PASS |
| longitude | 45 / -75 | 2020-03-20T17:07:51.534311+00:00 | 3.29e-13 | PASS |
| high_latitude | 70 / 0 | 2020-06-21T12:01:26.679355+00:00 | 2.14e-13 | PASS |

The full automatic example starts 2020-03-20 20:00 UTC and ends 2020-03-21 09:00 UTC at 45N/0E. Its preceding noon is 12:07:55.363681 UTC: bootstrap 28324.636319 s, followed by 46800 s of requested simulation through the next dawn. All states remain physical; maximum normalized QSSA/family/peroxide residual is 3.56e-16. This exercises the full automatic route rather than only the root solver.

### Frozen versus dynamic background sensitivity

Both runs begin with the identical explicit golden state, separating the evolving-background effect from initialization. Dawn statistics select SZA in [60,99] over all 51 heights; the accepted 21-hour real-geometry reference stops at 09:00 UTC, approximately SZA 61.2 degrees. The large differences below are resolved model sensitivity, not an interpolation/solver failure.

| Species | max (%) | p90 (%) | p99 (%) | max absolute (cm^-3) | max relevant z / SZA |
| --- | ---: | ---: | ---: | ---: | --- |
| O3 | 69.2122 | 20.4115 | 40.5306 | 1.666889e+08 | 83 km / 81.551 deg |
| Delta | 24.6128 | 16.6901 | 20.844 | 3.580542e+08 | 99 km / 95.673 deg |

Near-zero maximum absolute differences: O3 0, Delta 5528.81 cm^-3; relative percentages are not assigned there. Detailed 60/70/80/90/100-km sensitivity statistics, convergence distributions/cases, per-height root convergence and budgets are retained in the existing evidence JSON.

The derived [m5c_reference_dynamic_msis.npz](../evidence/m5c_reference_dynamic_msis.npz) saves time, height, SZA, seven dynamic species, exact R_H, O1D/B0/B1, eleven forcings, all requested chemical background fields, exterior radiative fields and geometry/atmosphere/activity/initialization/solver metadata. Native unavailable O/H remain NaN-labelled availability data; chemical states and prescribed physical backgrounds are finite. Artifact SHA256: 0c8efafdaaedabab819ecabc027370b054c39f1b44badbc1897501d75467cb57.

Final QA: **908 tests + 13 subtests PASS**, ruff PASS, five historical validators PASS, historical M4D mapping PASS. All previous dark/OH/H2O2/periodicity diagnostic regressions remain passing and historical. The full frozen API regression is bit-identical to M5B (all seven species maximum difference zero). M5A/M5B golden NPZ, frozen NIR and M4C-R2 hashes are unchanged; M4C-R2 remains 2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe. main is unchanged.

Reproduce using scripts/validate_m5c_temporal.py: prepare with --step 3600 and 7200 plus authorized --sources/--hitran; run --step 300 --nir-step 3600 --solver base/tight/Radau, then 600/3600/tight and 300/7200/tight; assess --step 300 --nir-step 3600 --comparison-step 600 --comparison-nir-step 7200. Run cases with the local sources; bootstrap --step 300 --nir-step 3600 --start 2020-03-20T20:00:00+00:00 --solver tight. Supply the same --cache directory. numerics independently reproduces exact-profile/control audits using the five initializer cases. No periodic-search or automatic space-weather mode is called.
