# M5 temporal reference report

## Current decision

**NO-GO M5A / LONG TRANSIENT AND SLOW DRIFT: period-2 not certified.**

Thirty additional consecutive ordinary physical days were completed for each of the three existing seven-state seed lineages: **90 new full-column days**, 31 midnight endpoint states per lineage. No secant, day-map acceleration, clipping, algebraic species reset or chemistry/forcing change was used. Starting candidates retain their original seed provenance; the new day count is physical and excludes all prior accelerated candidate indices.

The strict 24-hour-orbit requirement is historical. The current test accepts either parity of a common asymptotic two-day orbit under unchanged 24-hour forcing. D2/D4 and same-phase drift fail across the full 357-variable state. This finite-horizon result does not prove that an asymptotic 48-hour orbit is absent.

## Current model

M5-only state: O, O3, H, OH, HO2, H2O2, Delta; 51 frozen reference levels, 357 ODEs. R_H=OH+HO2 is diagnostic. O1D/B0/B1 alone remain algebraic. Original M3/M4 modules, reactions, kinetics, photolysis and forcing are unchanged. Original close_local_chemistry and the historical five/six-species formulations remain available for regression.

The temporal equations retain the original O/O3/H/Delta tendencies. OH is the accepted OH production-minus-loss expression. HO2 tendency is exactly accepted dR_H-dOH. H2O2 tendency is exactly HO2_HO2-H2O2_PHOTOLYSIS-OH_H2O2, without a self-reaction factor 1/2. OH+H2O2 loses one OH and produces one HO2, with zero net R_H change. No dynamic species is reset to QSSA or clipped.

Golden comparison: all fluxes and algebraic O1D/B0/B1 reproduce the original closure at old-QSSA-valid states. O/O3/H/Delta tendencies match exactly. The old OH root imposes dOH=0, not dR_H=0: hence new dHO2=old dR_H in general. All three HOx derivatives vanish at stationary family states, including the exact dark continuum. Requiring zero dHO2 for every old OH-QSSA root would contradict the accepted evolving family budget.

## Physics preflight

All seven boundary tests pass at every height, with dark and nonnegative illuminated forcing and widely separated physical states. Negative event stoichiometry requires its consumed dynamic reactant; the full finite-peroxide mass-action network is quasipositive. Cancellation in dR_H-dOH is assessed against machine precision times the event-flux sum, not hidden by clipping.

Remaining QSSA losses have strictly positive radiative terms: O1D >=0.00681 s^-1, B0 >=0.0834 s^-1, B1 >=0.072 s^-1 for every physical state. Frozen backgrounds and nonnegative states add nonnegative collision losses. Sampled 51-level minima: 508.198636, 0.108614855, 38.9332194 s^-1 respectively. Frozen O2>0 also keeps the accepted Barth transfer denominator positive.

## Historical blockers and regressions

1. Dark SZA99 equilibrium continuum remains exact: [O=0,O3=c,H=0,OH=0,HO2=0,H2O2=0,Delta=0] is stationary; it does not define a unique initial profile.
2. Original OH/HO2 QSSA root failure at 100 km / ~19223.76 s remains reproducible with its original scalar guard. The seven-state trajectory crosses the retained full-column anchor at 19222.72317 s through 19300 s. Golden algebraic difference=0; BDF base/tight maximum=0.00780354%; BDF/Radau=0.000671537%; retained QSSA scaled residual=2.094e-16.
3. Historical six-state H2O2 QSSA singularity remains reproducible: dark OH->0+, HO2>0 yields a finite outward OH loss, and OH=0 gives positive peroxide production with zero QSSA loss. This no longer stops the dynamic-peroxide model.

The 100-km natural-night witness begins with OH=0.0155041789, HO2=1000, H2O2=1.2815680973e8 cm^-3. The new equations remain finite/nonnegative to 10000 s. At 4289.881963 s: OH=0.00575855734, HO2=999.979044, H2O2=1.28156809733e8. At 10000 s: OH=0.00154090328, HO2=999.942414, H2O2=1.28156809750e8. All eleven actual reference forcings are exactly zero throughout this interval. BDF base/tight maximum difference=0.00002009%; BDF/Radau=0.000010865% (relative for values >1e-8 cm^-3, absolute below). Peroxide is evolved freely.

## Ordinary period-2 experiment

ReferenceEquinoxSolarCycle: 45 N, declination 0, 86400 s; frozen M4A; dynamic M4C UV self-shielding; M4D A0/B/IRA with historical CIA attenuation; no transport. The model/NIR/background fingerprint is identical across the three continuations. Every day starts directly from the previous physical endpoint. Initial candidate indices were 55/54/56; the new 0..30 counter denotes actual consecutive days. Starting and final full states are in the existing evidence JSON. Full endpoint histories and sampled trajectories remain in the local derived cache.

For every species, lag differences are calculated at all 51 heights. Relevant concentrations use abs(a-b)/max(a,b). The near-zero floor is max(1 cm^-3, 1e-6 times the reference species column peak); below it the absolute bound is 0.005 times that declared floor. Certification requires six consecutive D2/D4 passes at <=0.5%, material D1/D3, and both same-phase ten-day comparisons <=0.5%, after at least 20 ordinary days.

| Seed family | New ordinary days | Final D1 | Final D2 | Final D3 | Final D4 | Period-2 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 30 | 65.65450% | 1.68905% | 65.66204% | 3.37454% | FAIL |
| 1 | 30 | 65.65391% | 1.84701% | 65.66591% | 3.70459% | FAIL |
| 2 | 30 | 65.63662% | 1.34859% | 65.65809% | 2.71125% | FAIL |

These are maxima over all seven species and heights. Full per-species D1..D4 histories, near-zero absolute differences, floors and final spatial witnesses are in evidence/m5_temporal_evidence.json under period2_certification.

| Physical day | D2 seed 0 | D4 seed 0 | D2 seed 1 | D4 seed 1 | D2 seed 2 | D4 seed 2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 2.0707% | 4.1357% | 2.4660% | 4.9246% | 1.8746% | 3.3823% |
| 10 | 1.9815% | 3.9578% | 2.3329% | 4.6628% | 1.6463% | 3.2877% |
| 15 | 1.8995% | 3.7944% | 2.2047% | 4.4104% | 1.5816% | 3.1648% |
| 20 | 1.8239% | 3.6436% | 2.0812% | 4.1669% | 1.5083% | 3.0235% |
| 25 | 1.7540% | 3.5040% | 1.9620% | 3.9318% | 1.4298% | 2.8706% |
| 30 | 1.6890% | 3.3745% | 1.8470% | 3.7046% | 1.3486% | 2.7112% |

## Phase convergence, seed dependence and drift

Each provisional parity is compared to the same parity ten physical days earlier. Neither phase passes the full-state threshold:

| Seed family | Ten-day drift, latest phase | Ten-day drift, other phase | H at 100 km: initial -> final (cm^-3) | Days with increasing midnight H |
| --- | ---: | ---: | ---: | ---: |
| 0 | 8.4090% | 8.4714% | 1.419825e+08 -> 1.84985e+08 | 30/30 |
| 1 | 9.3280% | 9.4358% | 4.5856246e+08 -> 5.0080527e+08 | 30/30 |
| 2 | 6.8698% | 6.9455% | 7.0297465e+08 -> 7.4435904e+08 | 30/30 |

O3 at 85 km approaches two alternating values, roughly 1.57e7 and 5.41e6 cm^-3, but that local pattern does not certify the whole column. Material lag-2 changes remain elsewhere, including O3 near 94 km. H and the tracked hydrogen inventory retain slow growth at the same solar phase. The absence-of-drift requirement fails even though concentrations remain physical.

Diagnostic phase pairing permits only one common A/B swap for the whole column. A/B are provisional endpoint labels, not accepted reference phases:

| Pair | Parity swapped | Maximum phase A difference | Maximum phase B difference | Seed independence |
| --- | --- | ---: | ---: | --- |
| 0 vs 1 | False | 70.1858% | 70.0003% | not certified |
| 0 vs 2 | True | 76.9084% | 76.6792% | not certified |

These finite-time separations do **not** establish multiple asymptotic attractors: the individual lineages have not converged. No MULTIPLE ATTRACTOR diagnosis is claimed.

## Interpretation and stopping point

D1 and D3 remain large. D2 decreases slowly; D4 is approximately twice D2 in the dominant drifting variables. Neither period-3 nor period-4 recurrence passes the measured tolerance. Quasiperiodicity is not demonstrated. The supported diagnosis is an alternating component with a long transient / slow finite-window secular drift. The tested horizon cannot distinguish eventual relaxation from permanently persistent drift.

This is behavior of the **frozen-reference reduced model**, not a demonstrated atmospheric property. There is no transport and the prescribed reservoirs/atmosphere remain fixed.

No certified two-day candidate is available for the downstream 48-hour BDF/tighter-BDF/Radau and perturbation-recovery tests. Those stages and dawn_A/dawn_B remain **not executed / not accepted**. The previous full-day witness comparison (base/tight 0.075816%, tight/Radau 0.002983%) is historical evidence only; it is not presented as a new 48-hour verification. No arbitrary day is selected as reference and no chemistry is adjusted to obtain periodicity.

## Physics and QA

All 90 new days have finite/nonnegative sampled states, exact shadow in all eleven forcings, physical O1D/B0/B1 closures and the accepted OH+HO2 budget. The largest scaled QSSA residual is 5.959e-16 and the family-budget residual is 1.622e-16. The retained denominators keep their strictly positive radiative lower bounds. Positivity/QSSA/budget tests pass; asymptotic initialization and absence of drift fail.

The seven-state chemistry kernel is unchanged from c888fdc; no accepted M3/M4 module, reaction, rate, forcing or additional QSSA species is modified. Dynamic H2O2 remains the M5 baseline.

Full pytest: **868 tests + 13 subtests PASS**. Ruff and five historical validators PASS. All three historical blocker regressions pass: dark continuum, old OH root failure, old H2O2 dark singularity. M4C-R2 SHA256 remains 2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe. main is unchanged; M4D stays NOT FROZEN. Generated trajectories/caches and the licensed raw HITRAN export remain outside Git.

## Reproduction

The existing validator defaults to period2-certification, rejects acceleration in this mode, retains every physical day and resumes checkpoints with the same model/input fingerprint. The existing evidence JSON supplies starting candidates if prior local seed checkpoints are absent. Run separately for --family 0, 1 and 2 with --ordinary-days 30. Mode period2-assessment reports all lags and aligned provisional phase comparisons. A seed-local candidate PASS alone still requires independence, 48-hour solver agreement and perturbation recovery before GO M5A.

Use PYTHONPATH=src;. on Windows. Example commands:

    python scripts/validate_m5_temporal.py --sources <frozen-m4d-sources> --hitran <authorized-HITRAN2016-export> --cache <derived-cache> --mode period2-certification --family 0 --ordinary-days 30
    python scripts/validate_m5_temporal.py --sources <frozen-m4d-sources> --hitran <authorized-HITRAN2016-export> --cache <derived-cache> --mode period2-assessment

Modes dark-regression, domain-regression, positivity-regression and the former one-day periodicity-regression remain historical regressions. The old periodic/acceleration mode is a historical daily-orbit diagnostic, not the current initialization requirement.
