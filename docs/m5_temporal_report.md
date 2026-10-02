# M5 temporal reference report

## Decision

**NO-GO M5A / POSITIVITY BLOCKER: retained H2O2 QSSA in darkness.**

The authorized OH/HO2 temporal relaxation is implemented and crosses the old
OH root failure. Its required *global OH positivity preflight* fails: the
remaining peroxide QSSA has no finite root at OH=0, HO2>0 and J_H2O2=0, and its
one-sided OH tendency points out of the nonnegative domain. This is a reduced
closure obstruction, not an error in the accepted reaction network/constants.
The user's explicit positivity STOP condition applies. No further species is
promoted, no chemistry/forcing is changed and no final reference dawn is certified.

This counterexample is a dark-boundary validation case, **not a claim that the
nominal spin-up trajectory reached that boundary**. The attempted seed runs
remained finite/nonnegative but had not attained certified periodic convergence.

## Implemented model

| Role | Definition |
| --- | --- |
| Dynamic state | O, O3, H, OH, HO2, Delta; 51 levels 50..100 km, 306 ODEs |
| Family | R_H=OH+HO2, diagnostic only |
| Remaining QSSA | Original O1D, H2O2, B0, B1 formulas and denominator checks |
| Atmosphere | Frozen M4A T/M/O2/N2/CO2/H2O/H2 |
| Solar reference | Equinox 45N, declination 0, 86400 s, prescribed SZA |
| Radiation | Dynamic M4C O/O3 UV opacity; M4D A0/B/IRA with historical CIA attenuation |
| Dynamics | No transport; Delta remains prognostic throughout |

O/O3/H/Delta use the exact accepted event fluxes and stoichiometry. dOH/dt is
accepted OH production minus loss; dHO2/dt=accepted dR_H/dt-dOH/dt. Independent
registry coefficients prove this reaction by reaction. Random-state tests
verify the family budget to machine flux precision and unchanged four-species
tendencies. The supplied-HOx closure executes the original closure body in a
private namespace, without mutating M3/M4. At valid old roots it reproduces all
algebraic species, fluxes and tendencies exactly. The lean RHS omits diagnostic
trace construction only and is bitwise equal to the fully audited RHS.

## Why the required dark OH boundary fails

The accepted peroxide formula is

`P_H2O2 = K(T,M)*HO2^2`

`H2O2 = P_H2O2 / (J_H2O2 + k_OH_H2O2*OH)`.

In darkness, for OH>0, substitution into the accepted OH loss gives

`F_OH_H2O2 = k_OH_H2O2*OH*H2O2 = K(T,M)*HO2^2`.

For the allowed boundary O=O3=H=Delta=0, HO2=c>0 and all forcing zero, OH
production is zero and other OH losses vanish as OH tends to zero. Therefore

`lim(OH -> 0+) dOH/dt = -K(T,M)*c^2 < 0`.

At OH=0, peroxide production stays positive and its loss frequency is zero;
no finite H2O2 can satisfy its stationary equation. The original solver raises
`SingularQSSAError: H2O2 QSSA has positive production and zero loss`.
With any *finite supplied peroxide*, the unchanged mass-action OH equation
instead has zero OH loss at OH=0. Thus the problem is the peroxide elimination,
not the reaction itself. Tests cover the dark limit at 50/60/70/80/90/100 km.
The OH=HO2=0 dark continuum remains exact, including 24 h BDF persistence.

The earlier OH boundary tests used the finite photolysis domain. Adding the
mandatory dark one-sided limit invalidates their operational positivity PASS;
the default periodic validator now performs this preflight and stops before
starting any spin-up. No singular denominator is regularized or clipped.

## Independent natural-night witness

Frozen M4A at 100 km: T=185.6060638428 K, M=1.281568097278e13 cm^-3.
Initial six-state witness:

`[0, 0, 0, 0.0155041788815, 1000, 0] cm^-3`.

Its accepted initial H2O2 is 1.281568097278e8 cm^-3 (1e-5 of M). Initial
dOH/dt=-3.579513318516e-6 cm^-3 s^-1; the dark outward limit is
-3.576538985232e-6 cm^-3 s^-1. These are model-derived validation numbers,
not external profiles or accepted initial conditions.

All eleven forcing frequencies are exactly zero in the actual reference solar
cycle over this interval (SZA 135 -> 132.297 degrees); their equality to the
accepted column forcing is checked at both ends. No forcing is modified.
Integrations stop at positive OH=1% of its initial value, before the singularity:

| Solver | rtol | Time to positive threshold (s) |
| --- | --- | --- |
| BDF | 2e-06 | 4289.881963452972 |
| BDF | 2e-09 | 4289.881963453012 |
| Radau | 2e-09 | 4289.881963452897 |

Event-time spread is 1.15e-10 s. HO2 remains 999.984651108 cm^-3 and dOH/dt
remains -3.576458902368e-6 cm^-3 s^-1. Concentrations stay finite/nonnegative
through that checkpoint; H2O2 has grown to 1.28152875628e10 cm^-3. At the same
boundary with OH=0, the original peroxide root fails. The mathematical
log-OH continuation approaches the limiting time near 4333.23 s; its divergent
peroxide values are explicitly **not** accepted atmospheric concentrations.
No negative state or continuation through a singularity is accepted.

## Old dawn failure crossed by six-state dynamics

The original full-column anchor is t=19222.723172994694 s. All 51 new closures
match the old algebraic state exactly there. Six-state BDF and Radau advance
to 19300 s across the former 19223.755728 s / SZA 96.98356 root failure.

| Check | Result |
| --- | --- |
| BDF base vs tight max relevant difference | 0.00515135% |
| Tight BDF vs Radau | 0.000550887% |
| Four retained QSSA scaled residual max | 2.13427e-16 |
| OH+HO2 budget scaled residual max | 2.21207e-20 |
| Minimum concentration during crossing | 5.60588e-5 cm^-3 |
| 100 km OH start -> end | 0.297371757 -> 0.389827535 cm^-3 |
| 100 km HO2 start -> end | 5.60588e-5 -> 1.02654e-4 cm^-3 |

This establishes that relaxing OH/HO2 timescales crosses the old blocker with
unchanged chemistry. It does not waive the newly demonstrated dark OH test.

## Periodic attempts and numerical work

Three seed factors 1, 0.1 and 10 completed [31, 28, 29] full ODE day-map evaluations
(including positive numerical secant guesses); initial consecutive ordinary
spin-up days were [10, 7, 8]. No periodic root, seed independence or final
reference dawn was certified before the mandatory positivity stop.

The six-state integrator uses log coordinates in darkness and scaled physical
coordinates when illuminated. Negative Newton trials are rejected and retried,
never clipped. Small OH/HO2 use concentration-specific error scales. Dense
segment endpoints use accepted solver values to avoid cancellation. Geometry
memoization uses exact SZA keys and immutable original ray arrays. Dynamic UV
is recomputed for the actual evolving O/O3 at every RHS call.

Optional positive block secant acceleration changes numerical guesses between
day-map evaluations only; every evaluated day uses the unchanged ODE/forcing.
These iterations are not elapsed atmospheric days. Its acceptance design
requires three subsequent consecutive ordinary cycles and current-RHS
base/tight BDF plus Radau, with source-fingerprinted cached trajectories and
0.5% full-cycle comparisons. Those final gates remain **unreached**. The
positivity preflight prevents this option from becoming an operational bypass.

## QA and immutable reference

- Full pytest: **739 passed + 13 subtests passed**.
- Ruff: PASS.
- Legacy, local closure, odd-oxygen budget, M4A and M4C UV validators: PASS.
- Old dark continuum and OH-domain exit regressions: retained/PASS.
- New positivity regression: PASS as a blocker diagnosis; periodic mode exits 2.
- NIR table: 276 nodes, max relevant interpolation error 0.497655%; all 51
  tangencies and exact shadow retained. No NIR approximation or source change
  was introduced for the new boundary case.
- Accepted M3/M4 code/assets and main are unchanged. M4D is INTEGRATION READY /
  NOT FROZEN; PR #4 remains unmerged.
- M4C-R2 artifact SHA256:
  `2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe`.

The single machine-readable evidence file is `evidence/m5_temporal_evidence.json`;
its flat probe_anchor/independent_probes/boundary_directional_diagnostic fields
retain historical-test compatibility. The rest of the old five-state diagnosis
is explicitly nested as history. The dark equilibrium continuum and old OH
root blocker remain valid historical diagnoses; the current stop is H2O2.

Reproduce with the existing validator (`PYTHONPATH=src`):

```text
python scripts/validate_m5_temporal.py --sources <frozen-source-folder> --hitran <authorized-export>
# Expected exit 2: mandatory dark OH/peroxide positivity blocker.
python scripts/validate_m5_temporal.py --mode positivity-regression --sources <frozen-source-folder> --hitran <authorized-export>
# Expected exit 0: the diagnosed blocker regression is reproduced.
python scripts/validate_m5_temporal.py --mode onset --sources <frozen-source-folder> --hitran <authorized-export> --cache <derived-cache>
# Crossing regression only; does not certify a periodic initial condition.
python -m pytest -q -p no:cacheprovider
python -m ruff check src tests scripts
```
