# M5 temporal reference report

## Current decision

**NO-GO M5A / PERIODIC INITIALIZATION BLOCKER: persistent alternating-day dynamics.**

Dynamic H2O2 passes the physics preflights and resolves the previous dark QSSA obstruction. The prescribed three seed families nevertheless do not obtain a common certified 24-hour cycle. Ordinary continuations show large alternating-day excursions, reproduced by tighter BDF and Radau. The reference dawn remains unaccepted because its initialization policy has not passed.

This is an observed failure of the tested daily spin-up, **not a proof that no mathematical 24-hour orbit exists**. A possible 48-hour attractor is a hypothesis from the alternating snapshots, not a newly accepted initialization policy. No chemistry, kinetic constant or forcing is changed to suppress the behavior.

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

## Periodic reference and new obstruction

ReferenceEquinoxSolarCycle: 45 N, declination 0, 86400 s; frozen M4A; dynamically attenuated M4C UV; M4D A0/B/IRA, including O2-Air CIA attenuation only; no transport. Three original numerical seed families (1, 0.1, 10 factors) reach recorded map indices **55 / 54 / 56** without a daily periodic PASS. These indices include candidate-map acceleration and are not physical elapsed days. The later continuations are ordinary unchanged-ODE days; the following snapshots are from one continuous ordinary stretch.

All states remain finite/nonnegative. O1D/B0/B1 keep physical positive denominators; their largest scaled full-day residual is 4.44e-16. The full-day OH+HO2 budget residual is <=1.63e-16 relative to the event-flux sum. No additional QSSA promotion is indicated.

At the same midnight solar phase, 85 km, family 0:

| Recorded map index | O3 (cm^-3) | H2O2 (cm^-3) |
| --- | ---: | ---: |
| 36 | 1.5041516e7 | 2465.957 |
| 37 | 5.2171279e6 | 4676.117 |
| 38 | 1.6244815e7 | 2326.355 |
| 39 | 5.5511466e6 | 4271.437 |
| 40 | 1.5329591e7 | 2430.490 |
| 41 | 5.2930228e6 | 4578.007 |

The alternation persists in the later samples, including the final recorded continuations. The witness 36->37 changes O3 by **65.315%** (the larger-density denominator); all seven species participate in the phase response. This difference is far above numerical uncertainty and is not a near-zero normalization artifact. The apparent two-day recurrence still has drift and is not certified here as an exact 48-hour orbit.

### Independent full-day verification

The same full 51x7 witness initial state is integrated over 0..86400 s with BDF base, tighter BDF, and Radau. Every actual dynamic UV call and the prescribed NIR table are retained. Comparison uses a per-species relevance floor max(1 cm^-3, 1e-6 of the full time-height species peak); below it, the absolute bound is 0.005 times that declared floor.

| Check | Maximum relevant relative difference | Outcome |
| --- | ---: | --- |
| BDF base vs tighter BDF | 0.075816% | PASS |
| Tighter BDF vs Radau | 0.002983% | PASS |
| One-day O3 change at 85 km, all three solvers | ~65.315% | Daily periodicity FAIL |
| Physical states / exact shadow forcing / three QSSA / family budget | finite, nonnegative; shadow exactly zero | PASS |

The corresponding near-zero absolute differences pass the declared bounds; their per-species values are in the single evidence JSON. The same witness and independent trajectories are replayable with the existing validator's `periodicity-regression` mode. Matching source-fingerprinted local caches are audited again; an empty cache recomputes the three integrations.

NIR forcing uses the existing audited 276-node interpolation: maximum midpoint relative error 0.497655%, near-zero absolute error 9.837e-16 s^-1, exact geometrical shadow. This interpolation is unchanged from the accepted M5 radiation setup.

The current blocker is the required **common 24-hour initialization**, not the historical OH/HO2/H2O2 QSSA failures. No dawn from these states is labeled an accepted reference. A multi-day initialization, an arbitrary chosen phase, or any change of chemistry/forcing would require a new scientific decision; none is implemented.

## Numerical implementation and QA

The current column kernel reuses accepted scalar O1D/B0/B1 and event evaluator bytecode with frozen coefficients. Joint evaluation matches the scalar temporal kernel bit-for-bit for independent random columns; scalar full traces remain the golden audit. Benchmark chemistry cost decreased ~7.8 times; this changes evaluation overhead only.

Full pytest: **864 tests + 13 subtests PASS**. Ruff PASS; five historical validators PASS; old OH and peroxide validator regressions PASS; the new alternating-day witness regression PASS. M4C-R2 SHA256 remains `2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe`. main and accepted M3/M4 code remain unchanged. M4D remains NOT FROZEN.

Local implementation commits: `9a461ae` dynamic peroxide; `c888fdc` identical joint column evaluation. Current evidence is consolidated in `evidence/m5_temporal_evidence.json`; generated numerical caches stay outside Git.

## Reproduction

Use the authorized local HITRAN export and frozen source directory; the raw export is not in Git. The existing `scripts/validate_m5_temporal.py` supports:

- `--mode domain-regression`: original OH root failure.
- `--mode positivity-regression`: original six-state dark peroxide obstruction.
- `--mode periodicity-regression`: current seven-state one-day obstruction, checked with base/tighter BDF and Radau.
- `--mode periodic`: attempt the full daily seed spin-up; finite-horizon lack of convergence returns a structured NO-GO, not a claim of global orbit nonexistence.

For example, with `PYTHONPATH=src;.` on Windows:

```text
python scripts/validate_m5_temporal.py --sources <frozen-m4d-sources> --hitran <authorized-guest1593878592.txt> --cache <local-derived-cache> --mode periodicity-regression
```

The dark continuum remains a regression test; the analytic dark HO2/H2O2 limit also passes BDF and Radau at 50/75/100 km with no clipping.
