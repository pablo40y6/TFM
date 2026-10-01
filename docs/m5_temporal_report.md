# M5 temporal reconstruction and initial-condition blocker

## Decision and authorized integration base

**INITIALIZATION BLOCKER / NO-GO M5A: reference_twilight_equilibrium is nonunique.**
The initial-condition policy is now explicitly authorized; the earlier missing-
policy blocker is superseded. The new blocker is an exact physical consequence
of the accepted model at SZA=99, not missing external profiles or spectroscopy.

Branch: `milestone/m5-temporal`, continuing from `8230587`, whose integration base
is local M4D closure `f1841de891145323ddabaea50b7e2038e6ddaf5c`.
Local `milestone/m4d-design` still points to `25caaf9285545338a6b2cfc259b3348db7857ce3`.
No branch was merged or rewritten and main remains unchanged.

M4D is PROVISIONALLY CLOSED / INTEGRATION READY, without a definitive scientific
freeze. M5 uses A0 (430 Voigt), B (320 Voigt), IRA (835 monomer Voigt plus historical
O2-Air CIA attenuation only); A1 remains sensitivity only. PR #4 is not merged;
Y/Galatry/high-T/B-qSDV questions do not block M5.

Implemented `tfm_photochem.m5_temporal.local_rhs`: a pure five-species temporal RHS
that calls the accepted scalar closure without modifying kinetics or tendencies.
It rejects invalid concentrations explicitly, contains no clipping and keeps
Delta dynamic. A separate initialization preflight rejects exact nonunique dark
equilibria before numerical optimization; no equilibrium is selected arbitrarily.
The general root solver and 255-state dawn integration are intentionally stopped
because the user's explicit multiple-root stop condition has already occurred.

## Exact accepted chemistry

Reviewed PROJECT_STATE, architecture, historical topology/reactions/local closure,
odd oxygen, background, UV radiation and milestone 3/4A/4B/4C reports, together
with their source modules and tests. The scientific reference is the current
accepted M4B-corrected `close_local_chemistry`; M3's QSSA mathematics is unchanged.

| Role | Variables | Definition / source |
| --- | --- | --- |
| Prognostic | O, O3, H, R_H, Delta | `LocalState`, `config.DYNAMIC_SPECIES` |
| Reduced family | R_H | OH + HO2; H remains separate and dynamic |
| QSSA/algebraic | O1D, OH, HO2, H2O2, B0, B1 | `qssa.py`, `local_closure.py` |
| Prescribed | T, M, O2, N2, CO2, H2O, H2 | frozen M4A `LocalBackground` |
| Forcing | eight UV J plus gA, gB, gIRA | M4C and authorized M4D |

The grid is 51 integer levels, 50..100 km: 255 dynamic variables, no transport.
Concentrations are molecule cm^-3; tendencies/event fluxes molecule cm^-3 s^-1;
J/g frequencies s^-1; T kelvin. Second/third-order coefficients use accepted
cm3 molecule^-1 s^-1 / cm6 molecule^-2 s^-1 units.

Let `r_ID` denote exactly the event flux from accepted `fluxes.evaluate_fluxes`.
The following aggregate equations were reconstructed directly from the current
registry-derived `stoichiometry.TENDENCY_COEFFICIENTS` (no new reactions):

```text
dO/dt =
    -r_O_ASSOCIATION
    -r_O_O3
    -2*r_BARTH_RECOMBINATION
    -r_O_OH
    -r_O_HO2
    +r_H_HO2_H2O_O
    +r_OH_OH
    +r_O3_PHOTOLYSIS_GROUND_EFFECTIVE
    +r_O2_SRC
    +r_O2_LYMAN_ALPHA
    +2*r_O2_PHOTOLYSIS_GROUND_EFFECTIVE
    +r_O1D_RADIATIVE
    +r_O1D_N2
    +r_O1D_O2_B1
    +r_O1D_O2_B0
    +r_B1_O3
    +r_DELTA_O3
```

```text
dO3/dt =
    +r_O_ASSOCIATION
    -r_O_O3
    -r_H_O3
    -r_OH_O3
    -r_HO2_O3
    -r_O3_PHOTOLYSIS_GROUND_EFFECTIVE
    -r_B1_O3
    -r_DELTA_O3
    -r_O3_HARTLEY_PRODUCTS
```

```text
dH/dt =
    -r_H_O2_ASSOCIATION
    -r_H_O3
    +r_O_OH
    +r_OH_H2
    -r_H_HO2_2OH
    -r_H_HO2_H2O_O
    -r_H_HO2_H2_O2
    +r_H2O_PHOTOLYSIS_A
    +r_O1D_H2
```

```text
dR_H/dt =
    +r_H_O2_ASSOCIATION
    +r_H_O3
    -r_O_OH
    -r_OH_H2
    +r_H_HO2_2OH
    -r_H_HO2_H2O_O
    -r_H_HO2_H2_O2
    -2*r_OH_OH
    -2*r_OH_HO2
    -2*r_HO2_HO2
    +2*r_H2O2_PHOTOLYSIS
    +r_H2O_PHOTOLYSIS_A
    +2*r_O1D_H2O
    +r_O1D_H2
```

```text
dDelta/dt =
    +r_O2_IRA_BAND
    -r_DELTA_RADIATIVE
    +r_B0_N2
    +r_B0_O2
    +r_B0_O
    +r_B0_O3
    +r_B0_CO2
    -r_DELTA_O2
    -r_DELTA_N2
    -r_DELTA_O
    -r_DELTA_O3
    +r_O3_HARTLEY_PRODUCTS
```

For ordinary events use the unchanged accepted coefficients and reactant
products. A self-reaction event is k*X^2, without 1/2; stoichiometry supplies the
factor two. Barth consumes two O via its gross recombination event, while its
separate effective B0 source is not a second dynamic event. Gross/complement
Hartley/Lyman diagnostics and O1D_O2_TOTAL are not assembled again.

The six closures are exactly:

```text
P_O1D = 0.9*JH*O3 + J_SRC*O2 + 0.44*J_LYA*O2 + J_H2O_B*H2O
L_O1D = A_O1D + k_O1D_N2*N2 + k_O1D_O2*O2
        + k_O1D_H2O*H2O + k_O1D_H2*H2
O1D = P_O1D/L_O1D
HO2 = R_H - OH
H2O2 = k_HO2_HO2(T,M)*HO2^2/(J_H2O2 + k_OH_H2O2*OH)
OH: unique physical root of accepted OH production-minus-loss = 0
0 = r_H_O3 + r_O_HO2 + r_HO2_O3 + 2*r_H_HO2_2OH
    + 2*r_H2O2_PHOTOLYSIS + r_H2O_PHOTOLYSIS_A
    + 2*r_O1D_H2O + r_O1D_H2
    - r_O_OH - r_OH_O3 - r_OH_H2 - 2*r_OH_OH
    - r_OH_HO2 - r_OH_H2O2
P_B1 = gB*O2 + 0.8*k_O1D_O2*O1D*O2
L_B1 = A_B1 + k_B1_O2*O2 + k_B1_N2*N2 + k_B1_O*O + k_B1_O3*O3
B1 = P_B1/L_B1
P_B0 = gA*O2 + 0.2*k_O1D_O2*O1D*O2
       + k_B1_O2*B1*O2 + k_B1_N2*B1*N2 + P_Barth_B0
P_Barth_B0 = k_Barth*O^2*M*O2/(6.6*O2 + 19*O)
L_B0 = A_B0 + k_B0_N2*N2 + k_B0_O2*O2
       + k_B0_O*O + k_B0_O3*O3 + k_B0_CO2*CO2
B0 = P_B0/L_B0
P_Delta = 0.9*JH*O3 + gIRA*O2 + sum(B0 quenching fluxes)
L_Delta = A_Delta + k_Delta_O2*O2 + k_Delta_N2*N2
          + k_Delta_O*O + k_Delta_O3*O3
dDelta/dt = P_Delta - L_Delta*Delta
```

Existing zero/singular limits and the 257-point OH root ambiguity guard are
retained; Delta remains prognostic. There is a unique OH/HO2 reconstruction only
when that existing closure accepts the supplied state and forcing. No assumption
that it will remain nonsingular throughout dawn has been verified yet.

M4B partitions `J2_star=J_SRC+0.44*J_LYA`, `J2_ground=J_O2_TOTAL-J2_star`,
`J3_star=0.9*JH`, `J3_ground=J_O3_TOTAL-J3_star`. Gross subset checks remain
`J_O2_TOTAL>=J_SRC+J_LYA`, `J_O3_TOTAL>=JH`. Eight UV inputs also include
J_H2O2, J_H2O_A, J_H2O_B. The accepted 0.89/0.11 H2O short-wavelength reduction
and H2O2 source/temperature policy remain unchanged. No legacy optional HOx
reaction is imported; the four explicit topology exclusions remain excluded.

## Authorized initialization and exact nonuniqueness

The user authorized `reference_twilight_equilibrium`: five stationary tendencies
at fixed SZA=99, nonnegative states, unique physical roots across seeds, passing
QSSA and independent constant-forcing relaxation. Existing profiles are numerical
seeds only, never an automatic accepted initial condition. This supersedes the
previous lack of an accepted initialization policy.

At SZA=99 the accepted solid-Earth shadow covers every integer height 50..79 km.
M4C returns exactly zero for all eight UV inputs there regardless of dynamic
column opacity. Direct M4D calls with the verified complete A/B/IRA line subsets
and historical CIA also return exactly zero for all three g-factors. The validator
loads the frozen historical sources and authorized HITRAN export; this is direct
model forcing, not an assumed negligible twilight flux or an interpolated table.

For any c>=0 the following is then an exact stationary solution:

```text
y = [O=0, O3=c, H=0, R_H=0, Delta=0]
OH=HO2=H2O2=O1D=B0=B1=0
five tendencies = 0
six QSSA residuals = 0
```

Every accepted event is zero: there is no O for association/Barth, no radicals
for ozone destruction, no excited species and no photolysis. The accepted
R_H=0 boundary convention has zero OH production here and is fully consistent.
Consequently there is a continuum of nonnegative physical equilibria: changing
O3 alone is a neutral mode. Root tolerances, scaling, positive seeds or a longer
integration cannot establish a unique attracting root that these equations lack.

At each of the 30 shadowed heights, the preflight verifies two distinct roots
with c equal to 0.1 and 10 times the existing reference O3 seed, a factor 100
apart. Those reference values are used only to construct counterexamples.
For example, at 60 km:

| Witness | O3, molecule cm^-3 | Other four dynamic species | Five tendencies / six QSSA residuals |
| --- | ---: | --- | --- |
| lower O3 seed | 9.078617676877669e8 | exactly zero | exactly zero |
| higher O3 seed | 9.078617676877668e10 | exactly zero | exactly zero |

The normalized residual is exactly zero for any positive scale; no arbitrary
residual floor determines this conclusion. All witness states are finite and
nonnegative. The independently tested RHS retains Hartley and B1 ozone budgets
and the exact dynamic Delta response `delta(dDelta/dt)=-L_Delta*delta(Delta)`.

## BDF persistence and attraction failure

All 60 distinct stationary witnesses were integrated with the accepted RHS for
86400 seconds at fixed direct SZA=99 forcing using BDF, rtol=1e-9, atol=1e-8
molecule cm^-3 and max_step=3600 seconds. Their maximum absolute departure is
exactly zero; every integration succeeds with finite/nonnegative states.
Starting from the different O3 values preserves their difference instead of
relaxing to a common root. This disproves a unique attractor, not just seed
independence of an optimizer. The analytic continuum establishes nonuniqueness
for arbitrary persistence intervals, including intervals longer than one day.

For these exact constant boundary trajectories BDF receives a zero iteration
Jacobian to avoid finite-difference trial states outside the physical QSSA domain.
This is a numerical iteration choice only, not a physical Jacobian or a linear
stability calculation. No general stability of the dark equilibria or relaxation
from arbitrary five-species interior perturbations is claimed. Neither is needed
to disprove uniqueness: valid O3-only perturbations stay on distinct exact roots.

`scripts/validate_m5_temporal.py` reproduces direct forcing, exact stationary/QSSA
witnesses and BDF persistence at all 30 heights. It deliberately exits **2** for
INITIALIZATION BLOCKER. This is the requested scientific stop, not a software
regression. Remaining illuminated-height root searches cannot repair the failed
full-domain uniqueness criterion and have not been pursued.

## Architecture identified for continuation (not implemented)

The pure local RHS is implemented; the eventual full-column solver uses BDF with Radau verification,
configurable tolerances/max_step, and separate diagnostics. Never clip state in
the RHS. Independent chemical levels have no transport, but M4C UV radiation
couples their O/O3 opacity: reevaluate that inexpensive kernel with the dynamic
column, or demonstrate an explicitly declared fixed-opacity approximation.
A single J table in SZA/height cannot preserve evolving O/O3 self-shielding.

NIR forcing depends on prescribed atmosphere/O2 and may be precomputed in
SZA/height, with node reproduction and interpolation-error checks and A0/A1
selection. Precomputed ray geometry can also avoid repeated geometric work for
UV. No HITRAN transfer inside each chemical RHS evaluation is required.

A prescribed 99->60-degree reference dawn is authorized in principle; its
interval, interpolation resolution and output times have not been selected or
implemented because the authorized initialization is nonunique. No calendar
astronomy, atmosphere regeneration, vertical transport, temporal curves, solver
convergence or downstream A0/A1 chemical sensitivity has been claimed.

## QA and boundary preservation

Executed after this reconstruction:

- Full pytest: **604 passed + 13 subtests passed**.
- Ruff (`src tests scripts`): all checks passed.
- Legacy, local closure, odd-oxygen budget, historical background, historical UV:
  all five validators exit 0.
- M4C-R2 artifact SHA256:
  `2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe`.
- Compared all 37 packaged source/asset files in that artifact with the current
  checkout: 11 byte-identical, 26 differ only by pre-existing checkout line
  endings; no source/asset content differences. No EOL conversion was made here.
- No M1-M4D code, tests, assets, artifact or numerical evidence is changed by M5.

The new M5 validator returns the intentional initialization stop described above.
No dawn trajectories, BDF-versus-Radau dawn convergence or temporal 60/70/80/90/100
km output is claimed; those depend on a passing initial condition. No new public
JSON is committed; the validator emits its machine-readable witnesses to stdout.

Reproduce with `PYTHONPATH=src`:

```text
python scripts/validate_m5_temporal.py --sources <frozen-source-folder> --hitran <authorized-export>
python -m pytest -q -p no:cacheprovider
python -m ruff check src tests scripts
```

The next scientific decision must change the uniqueness requirement/initialization
policy, not the accepted dark chemistry silently. A possible future policy is a
specified illuminated initialization followed by an explicit presunset trajectory,
or the already planned repeated diurnal cycle to periodic convergence. Neither
policy nor an arbitrary selection from the dark equilibrium continuum is adopted
here. SZA=99 full-domain unique stationary initialization fails the authorized gate.
