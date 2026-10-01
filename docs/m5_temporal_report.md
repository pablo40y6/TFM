# M5 temporal reconstruction and initial-condition blocker

## Decision and authorized integration base

**NO-GO M5A: accepted initial conditions are missing.** This is the stop required
by sections 8 and 17 of the authorized M5 handoff, not an M4D spectroscopy gate.
No temporal solver, arbitrary chemical initialization or dawn result is claimed.

Branch: `milestone/m5-temporal`, created from local integration-ready M4D closure
`f1841de891145323ddabaea50b7e2038e6ddaf5c`. Local `milestone/m4d-design` still points
to `25caaf9285545338a6b2cfc259b3348db7857ce3`, which lacks the pragmatic closure.
Using the closure head preserves its implementation/evidence without merging PR #4,
rewriting an earlier branch or changing main. This M5 change is documentation only.

M4D is PROVISIONALLY CLOSED / INTEGRATION READY, without a definitive scientific
freeze. The handoff authorizes A0 (430 Voigt), B (320 Voigt), IRA (835 monomer
Voigt plus historical O2-Air CIA attenuation only); A1 is sensitivity only.
Historical Y/Galatry/high-T/B-qSDV questions do not block M5.

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

## Evidence for the initial-condition blocker

M4A's chemical asset contains only z,T,M,O2,N2,CO2,H2O,H2 (and their listed VMRs).
The radiative asset adds reference SOCRATES O3 and partly unavailable native-MSIS O.
These are background/boundary reference fields, not an accepted five-component
initial chemical state consistent with SZA=99 degrees. Neither asset supplies H,
R_H or Delta initialization.

`LocalState` requires all five dynamic concentrations from its caller. The
algebraic closure accepts these values, reconstructs six fast species, and
returns generally nonzero dynamic tendencies. It does not solve for H, R_H or
Delta, nor provide a dark/twilight equilibrium initialization routine.

`scripts/validate_local_closure.py` explicitly supplies the synthetic scalar
`O=2e11, O3=2e8, H=2e7, R_H=5e7, Delta=1e8` at synthetic T=200 K/background and
injected forcing. M4A/M4C smoke tests reuse synthetic H/R_H/Delta. These are
software regressions, not accepted 51-level dawn initial profiles. The legacy
three-pass ozone equilibrium does not initialize this reduced-HOx network.

Search of the relevant code, docs, tests, scripts and packaged assets found no
initial-state asset, accepted initialization rule, dark/twilight equilibrium or
spin-up procedure. QSSA consistency alone underdetermines the dynamic state;
choosing zeros, extrapolating smoke-test concentrations, or imposing full steady
state would introduce a new scientific initialization assumption.

To resume, provide an accepted five-species initial profile with provenance, or
explicitly authorize a new initialization policy derived from the accepted
chemistry and specify its intended physical reference. Such a policy must then
be investigated for existence/uniqueness, QSSA consistency and sensitivity.
This report does not infer that authorization from the instruction to stop when
no accepted initial conditions exist.

## Architecture identified for continuation (not implemented)

Use a pure RHS wrapping accepted local tendencies; BDF with Radau verification,
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
implemented because the required initialization is missing. No calendar
astronomy, atmosphere regeneration, vertical transport, temporal curves, solver
convergence or downstream A0/A1 chemical sensitivity has been claimed.

## QA and boundary preservation

Executed after this reconstruction:

- Full pytest: **569 passed + 13 subtests passed**.
- Ruff (`src tests scripts`): all checks passed.
- Legacy, local closure, odd-oxygen budget, historical background, historical UV:
  all five validators exit 0.
- M4C-R2 artifact SHA256:
  `2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe`.
- Compared all 37 packaged source/asset files in that artifact with the current
  checkout: 11 byte-identical, 26 differ only by pre-existing checkout line
  endings; no source/asset content differences. No EOL conversion was made here.
- No M1-M4D code, tests, assets, artifact or numerical evidence is changed by M5.

No new temporal validator was fabricated: without an accepted initial state,
there is no scientifically authorized reference trajectory to validate. Only
this report and a short PROJECT_STATE update are added. The next minimum step
is resolving initialization, then implementing/testing M5A; M5B astronomy and
M5C date/location atmosphere remain later work.
