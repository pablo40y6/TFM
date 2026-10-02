# M5 temporal reference cycle

## Authorized minimal temporal relaxation (current work)

The previous OH/HO2 domain exit is accepted as a scientific diagnosis and is
superseded operationally by the authorized M5-only timescale relaxation.
Current status: six-species implementation and onset preflight PASS;
periodic spin-up and seed independence are still being evaluated.

State: O, O3, H, OH, HO2, Delta (306 ODEs); R_H=OH+HO2 is diagnostic.
The four O/O3/H/Delta tendencies retain accepted event fluxes and stoichiometry.
dOH/dt is the exact accepted OH production-minus-loss expression;
dHO2/dt=accepted dR_H/dt-dOH/dt. Units remain molecule cm^-3 and seconds.
O1D, H2O2, B0 and B1 retain their exact accepted QSSA, including all singular
denominator checks. M3/M4 and original close_local_chemistry remain untouched.
No reaction, coefficient, photolysis frequency or forcing changes are authorized.

Validation gates: per-event/random-state family budget, original-root golden
agreement, analytic and tested physical boundary directions, dark continuum,
crossing the recorded dawn onset, then periodic convergence with three seeds,
base/stricter BDF and Radau (practical 0.5%). No clipping or further promotion
is permitted; a physical failure of a remaining QSSA stops this work.

### Six-species preflight evidence

- 108 specific tests pass: per-reaction OH/HO2 coefficients independently
  reconstructed from the reaction registry; 100 random positive states;
  preserved O/O3/H/Delta tendencies; exact family identity to machine flux
  precision; 100 boundary states for each HOx species; 153 golden night roots
  (three seeds at all 51 heights); exact dark continuum at all 51 heights.
- The lean ODE evaluation uses the original scalar QSSA and flux evaluators
  and accepted stoichiometric coefficients, omitting diagnostic trace objects
  only. Its six derivatives are bitwise equal to the fully audited closure
  in random-state tests. Original M3 functions/modules are never mutated.
- OH=0 in the finite closure domain: every accepted OH loss contains OH,
  hence dOH/dt=P_OH>=0. HO2=0: H2O2=0 and the independent registry gives
  dHO2/dt=F(H+O2+M)+F(OH+O3)>=0. In complete darkness, OH=0 with HO2>0
  has positive peroxide production and zero loss; the original H2O2 singular
  check is retained and tested, with no artificial extension of that domain.
- The new exact dark root [0,c,0,0,0,0] persists for 86400 s under BDF;
  a constant Newton preconditioner avoids inadmissible off-manifold numerical
  perturbations and does not alter the zero physical RHS.
- Starting from the original full-column anchor at 19222.723172994694 s,
  all 51 supplied-HOx closures reproduce the original algebraic species
  exactly. Integration reaches 19300 s through the former 19223.755728 s
  failure: BDF base/tight max relevant difference 0.00515135%; tight BDF/Radau
  0.000550887%. All concentrations stay positive (minimum 5.6058809e-5 cm^-3).
  Four retained QSSA scaled max 2.13427e-16; family identity scaled max
  2.21207e-20. At 100 km OH/HO2 change from 0.297371757/5.60588091e-5 to
  0.389827535/1.02653705e-4 cm^-3. This directly relaxes a timescale assumption,
  without changing a chemical event or forcing.
- Illuminated OH/HO2 use concentration-specific error scales (minimum 1 cm^-3)
  rather than a universal 1e5 cm^-3 scale. Dense segment endpoints use the
  exact accepted initial/final solver values, avoiding polynomial cancellation
  in tiny populations. No concentration clipping is used.
- Full QA after the numerical initializer work: **732 tests + 13 subtests**;
  ruff and the five legacy/local/odd-oxygen/M4A/M4C validators pass. The old
  scalar OH domain-exit regression still passes as historical evidence.

### Periodic initializer numerics

The full-day map always integrates the unchanged 306 ODEs, dynamic UV and
prescribed A0/B/IRA. Initial transient days are retained. To resolve slow upper
column relaxation, optional block Anderson/secant acceleration works only on
log-positive numerical guesses between day-map evaluations (memory six,
rank tolerance 1e-8, damped log corrections <=2). Candidate guesses remain
finite and below the prescribed total density; no concentrations are clipped.
Each actual day still couples all heights through the unchanged radiation.
These numerical iterations are **not elapsed atmospheric days**.

Acceptance requires three consecutive ordinary cycles with acceleration
disabled once the endpoint criterion is met, matching full cycles from all
three original seed families, and ordinary base/tighter BDF plus Radau under
the current RHS. Current endpoint target is 0.1% where relevant and 1 cm^-3
near zero; final trajectory comparisons target 0.5% with reported absolute
near-zero errors. Local cached spin-ups are source-hash and seed-fingerprint
checked; their closures and periodicity are re-audited, and the independent
final integrations must themselves remain periodic. Geometry memoization uses
exact SZA keys and immutable original ray arrays, with no interpolation.

The sections below are **historical five-coordinate diagnosis**, retained for
provenance. Their NO-GO and 255-ODE statements are not the current M5 formulation.

## Decision

**NO-GO provisional M5A / PERIODIC INITIALIZATION BLOCKER: accepted OH/HO2 QSSA
leaves its physical domain during the nominal bootstrap dawn.**

This is not the old dark-equilibrium uniqueness blocker. The authorized policy
is `reference_periodic_diurnal_spinup`; the SZA=99 dark continuum remains an
accepted regression and is non-blocking. No accepted chemistry was changed to
continue through the new failure. No complete periodic day, seed independence
or final reference dawn is certified.

Branch: `milestone/m5-temporal`, integration base
`f1841de891145323ddabaea50b7e2038e6ddaf5c`. M4D stays INTEGRATION READY / NOT
FROZEN. Main and accepted M1-M4C chemistry/assets/artifacts are unchanged;
PR #4 remains unmerged. The single machine-readable evidence file is
`evidence/m5_temporal_evidence.json`.

## Exact model and implemented architecture

| Role | Definition |
| --- | --- |
| Dynamic state | O, O3, H, R_H=OH+HO2, Delta; 51 levels 50..100 km, 255 ODEs |
| Algebraic species | O1D, OH, HO2, H2O2, B0, B1; accepted six QSSA |
| Frozen atmosphere | M4A T, M, O2, N2, CO2, H2O, H2 |
| UV | Eight accepted M4C J, recomputed with dynamic O/O3 on every RHS |
| NIR | M4D A0 430 Voigt; B 320 Voigt; IRA 835 monomer Voigt with historical O2-Air CIA attenuation only |
| Transport | None |

`local_rhs` uses accepted `close_local_chemistry` and stoichiometry. There are no
new reactions, rates or Delta=P/L closure; all five species remain dynamic.
Concentrations are molecule cm^-3, tendencies molecule cm^-3 s^-1, time seconds.

`ReferenceEquinoxSolarCycle`: latitude 45 degrees, declination zero, period
86400 s; cos(SZA)=cos(45)*cos(2*pi*(t/86400-1/2)). Midnight=135, noon=45,
sunrise/sunset=90. This is an explicit reference, not a calendar ephemeris.
The extraction window is morning SZA=99..60.

Three numerical seed families are defined, with factors 1, 0.1 and 10 in
reference O/O3 and broad positive H/R_H/Delta. Missing MSIS O uses 1e-10*M as a
numerical seed only. **Only nominal seed factor 1 was integrated; zero full days
completed.** Physical failure stops the task before the other families. It does
not prove that every possible seed or periodic orbit is impossible.

Consecutive-day endpoint convergence is configured at 0.1% for relevant
concentrations and 1 molecule cm^-3 near zero, followed by full-cycle agreement
across seeds, stricter BDF and Radau within 0.5%. Those periodic gates have not
been reached. The implemented final export would contain five dynamic species,
six algebraic species, all eleven forcing frequencies, time, height, SZA and
explicit dawn window. **No accepted dawn series at 60/70/80/90/100 km is exported.**

## Numerical work and corrections

The solver uses log concentrations in dark levels and scaled physical
concentrations in illuminated levels, with exact coordinate transformations.
The switches occur at all 51 physical tangent events on dawn and dusk. One-sided
forcing at a split endpoint avoids fitting an incoming discontinuity on the
outgoing dark interval. No concentration clipping or arbitrary equilibrium
reset is used. Negative/nonfinite trials are rejected and retried from the last
accepted state at reduced step.

The chemical block Jacobian is a Newton iteration approximation: radiation
partial derivatives are omitted from that preconditioner, while the full RHS
always recomputes dynamic UV. One-sided finite differences adapt to the physical
QSSA domain. Synthetic analytic derivative/recovery tests cover this strategy,
BDF and Radau; independent method comparison is required for acceptance.

Two numerical implementation problems were corrected:

- Missing altitude-specific tangent nodes smeared finite illuminated NIR rates
  toward shadow zero. The table now includes all 51 tangent angles and applies
  exact current shadow geometry.
- The accepted geometry's grazing tolerance sometimes admitted impact just
  below Earth, producing a tiny Earth chord and failed shell-length closure.
  A private M5 wrapper repairs only that roundoff interval to the tangent radius.
  Ordinary rays remain byte-identical; all tangent neighborhoods pass independent
  length/nonnegativity tests. Accepted M4C source files remain unchanged.

Log coordinates alone also caused enormous dy/y Newton predictors when solar
sources appeared in nearly empty populations. Switching coordinates removes
that artificial stiffness without changing an ODE. Invalid Jacobian perturbations
are handled numerically instead of being classified as physical trajectory stops.

For performance, private copies of original closure bytecode cache frozen scalar
coefficients and batch the original 257-point OH ambiguity scan. Original modules
are never mutated. Endpoint/small residual samples and Brent root tolerances remain
accepted originals. Golden comparisons cover all 51 heights, all three seeds,
dark/illuminated forcing and QSSA error propagation. The scientific blocker below
is reproduced using the **original scalar closure**, independent of these caches.

## NIR baseline preparation

Authorized HITRAN export: 2268239 bytes, 14085 records, SHA256
6b4acbc01cb649891f2d8597875c9cd8e4805cfdd4d3b7841c2d18cbf718de12;
A/B/IRA = 430/320/835. Raw data are not committed or uploaded. Derived opacity
caches remain outside Git and carry spectral/control/code fingerprints.

Adaptive piecewise linear interpolation/direct midpoint auditing gives
**276 nodes**, maximum relevant error **0.4976554195%**, near-zero maximum absolute
error **9.836573759e-16 s^-1**. Worst relative case: IRA, z=94 km,
SZA=99.7186393503, direct=1.7821954387e-14 s^-1,
interpolated=1.7910646309e-14 s^-1. This is a midpoint audit, not a uniform bound.
NIR HITRAN transfer is never evaluated inside the temporal RHS.

## Physical QSSA domain exit

The full nominal run from t=0 fails at **t=19223.755728 s (LST 05:20:23.756),
SZA=96.98356356, z=100 km**. Its positive state is approximately
[O=5.653112466e11, O3=3.897608539e8, H=1492.249917,
R_H=0.299405517, Delta=1.381497227e7] molecule cm^-3.

The original OH production-minus-loss residual is positive at every one of its
257 guard samples, including OH=R_H. A stationary OH partition would need to
leave 0<=OH<=R_H, implying negative HO2. The original `close_local_chemistry`
rejects the state with `NoPhysicalRootError`. Further step reduction reaches the
same domain boundary; no root or parameter was substituted to cross it.

Independent probes start from the same accepted full-column state at
19222.723173 s. They use the complete dynamic UV/RHS:

| Solver | rtol / transformed atol | max step, s | Domain exit, s | Height, km |
| --- | --- | ---: | ---: | ---: |
| BDF base | 2e-6 / 1e-8 | 120 | 19223.755514 | 100 |
| BDF stricter | 2e-8 / 1e-10 | 60 | 19223.756557 | 100 |
| Radau stricter | 2e-8 / 1e-10 | 60 | 19223.581121 | 99 |

Each exit is independently rejected by the original scalar closure. All 257
residuals are positive; minima are 1.0101e-10, 1.1532e-10 and 6.5317e-11
molecule cm^-3 s^-1, respectively. Small values locate the boundary; they are
not the sole evidence for a physical exit. A separately labelled one-second
forward-Euler diagnostic using the accepted RHS at the common anchor gives
positive minimum residuals 0.01454 and 0.009813 at 99 and 100 km. This diagnostic
is neither an accepted integration trajectory nor a repair.

A stronger local check starts at an accepted boundary state at 19223.756557 s:
all 51 original scalar closures still pass and the endpoint residual is
-5.522e-8. Directional steps of 1e-5, 1e-4 and 1e-3 s using the accepted full
RHS and recomputed UV give dG/dt=0.1021..0.1068 molecule cm^-3 s^-2. The minimum
OH residual becomes positive by 9.656e-7..1.067e-4. Thus the vector field points
out of the admissible domain, beyond a floating-point sign ambiguity. These are
directional diagnostics, not a continued physical trajectory.

On the common **0.8-second pre-boundary interval**, relevant maximum differences
are **0.015595%** (BDF base versus stricter) and **0.001981%** (stricter BDF versus
Radau). Near-zero R_H absolute differences are 1.478e-4 and 7.504e-5 molecule
cm^-3. This is local numerical agreement only; no full-day convergence or
periodic seed independence is claimed. The stop is physical admissibility of
this reduced QSSA trajectory, not CIA, a spectroscopy approximation or the old
universal 0.1% gate. No error in accepted reaction rates/budgets is inferred.

## Dark continuum regression and QA

At fixed SZA=99, every 50..79 km level is in solid-Earth shadow. Direct accepted
M4C/M4D forcing is exactly zero. For any c>=0, [0,c,0,0,0] has five zero
tendencies and all six zero QSSA residuals. Two witnesses per level, a factor
100 apart in O3, remain unchanged for 24 h BDF. The `dark-regression` validator
returns PASS; this result is historical and non-blocking for periodic forcing.

- Full pytest: **622 passed + 13 subtests passed**.
- Ruff: PASS.
- Legacy, local closure, odd-oxygen budget, M4A background and M4C UV validators:
  all five PASS.
- Dark continuum regression and recorded OH/HO2 domain-exit regression: PASS.
- Full periodic validator: intentional NO-GO at the physical QSSA domain boundary.
- M4C-R2 artifact SHA256 remains
  2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe.

```text
PYTHONPATH=src python scripts/validate_m5_temporal.py --sources <frozen-source-folder> --hitran <authorized-export> --cache <outside-git-cache>
PYTHONPATH=src python scripts/validate_m5_temporal.py --mode dark-regression --sources <frozen-source-folder> --hitran <authorized-export>
PYTHONPATH=src python scripts/validate_m5_temporal.py --mode domain-regression --sources <frozen-source-folder> --hitran <authorized-export>
PYTHONPATH=src python -m pytest -q -p no:cacheprovider
python -m ruff check src tests scripts
```

Continuing needs a scientific decision about temporal OH/HO2 QSSA admissibility;
this task does not alter the accepted reduction or invent a partition outside
its physical domain. Calendar ephemerides and dynamic atmosphere are not started.
