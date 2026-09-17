# `historical_2020` single-level local closure

## Scope and inputs

Milestone 3 evaluates one altitude and one instant. Concentrations are in
molecule cm^-3, first-order forcing in s^-1, event fluxes and tendencies in
molecule cm^-3 s^-1, and temperature in K.

| Object | Fields | Meaning |
| --- | --- | --- |
| `LocalState` | `O`, `O3`, `H`, `R_H`, `Delta` | future dynamic state; `Delta` is supplied, never replaced by equilibrium |
| `LocalBackground` | `T`, `M`, `O2`, `N2`, `CO2`, `H2O`, `H2` | prescribed scalar background |
| `LocalForcing` | `JH`, `J_SRC`, `J_LYA`, `J_O2_TOTAL`, `J_O3_TOTAL`, `J_H2O2`, `J_H2O_A`, `J_H2O_B`, `gA`, `gB`, `gIRA` | M4C calculates the first eight; the three g-factors remain externally injected |

All inputs must be finite scalars. `T > 0`; every concentration and forcing
value is nonnegative. Invalid values raise explicitly and are not clipped.

The forcing contract also validates gross spectral-subset consistency before
the reduced odd-oxygen partition:

```text
J_O3_TOTAL >= JH
J_O2_TOTAL >= J_SRC + J_LYA
```

This gross-event check is separate from the excited-product check. The 0.9
Hartley and 0.44 Lyman-alpha factors are product yields, not reductions of the
parent photodissociation counts. Both comparisons use a relative tolerance of
`64*machine_epsilon`; accepted one-ULP gross equality noise does not zero the
positive product-yield ground complement.

`close_local_chemistry(state, background, forcing)` returns the algebraic
state, flux map, six residuals, production/loss diagnostics, per-event dynamic
contributions, and five total tendencies.

## Six algebraic relations

The implementation uses the M2-R2 rate laws without modifying them.

### O1D

```text
P_O1D = 0.9 JH O3 + J_SRC O2 + 0.44 J_LYA O2 + J_H2O_B H2O
L_O1D = A_O1D + k_O1D_N2 N2 + k_O1D_O2 O2
        + k_O1D_H2O H2O + k_O1D_H2 H2
O1D = P_O1D / L_O1D
```

The total O1D+O2 loss appears once. Its 0.8 and 0.2 product branches are
calculated after the total event flux.

### OH, HO2, and H2O2

```text
HO2 = R_H - OH
r_HO2_HO2 = k_HO2_HO2(T,M) HO2^2
L_H2O2 = J_H2O2 + k_OH_H2O2 OH
H2O2 = r_HO2_HO2 / L_H2O2
```

No factor 1/2 is applied to the self-reaction event flux. The single OH
equation is the exact production-minus-loss expression frozen in the handoff.
It is solved with Brent's method for `x = OH/R_H` on `[0,1]`. A 257-point scan
first rejects absent or multiple sign-changing physical roots; no root is
selected silently and no result is clipped.

If `R_H == 0`, the dynamic boundary convention is
`OH = HO2 = H2O2 = 0`. A nonzero `res_OH` is then allowed because the next
dynamic tendency may grow the family. If H2O2 production and loss are both
zero, `H2O2=0`; positive production with exactly zero loss is singular and
raises `SingularQSSAError`.

### B1

```text
r_O1D_O2_total = k_O1D_O2 O1D O2
P_B1 = gB O2 + 0.8 r_O1D_O2_total
L_B1 = A_B1 + k_B1_O2 O2 + k_B1_N2 N2 + k_B1_O O + k_B1_O3 O3
B1 = P_B1 / L_B1
```

### B0

```text
P_B0 = gA O2 + 0.2 r_O1D_O2_total + r_B1_O2 + r_B1_N2
       + P_Barth_B0
L_B0 = A_B0 + k_B0_N2 N2 + k_B0_O2 O2 + k_B0_O O
       + k_B0_O3 O3 + k_B0_CO2 CO2
B0 = P_B0 / L_B0
```

Only B1+O2 and B1+N2 feed B0. B1+O and B1+O3 do not.

## Effective Barth assumption

Machine-readable metadata records:

```text
M3 baseline model assumption: effective Barth source -> B0
```

This is a model-reduction choice, not an experimental branching claim:

```text
r_Barth_total = 4.7e-33 (300/T)^2 O^2 M
P_Barth_B0 = r_Barth_total O2 / (6.6 O2 + 19 O)
```

`r_Barth_total` consumes `2*r_Barth_total` of O. When it is exactly zero,
`P_Barth_B0=0` even if the denominator is zero. No epsilon is used. The pending
elementary `BARTH_TRANSFER` and `BARTH_O2STAR_QUENCH` coefficients remain
unevaluated and are not invented.

## Flux semantics and complete flux map

Ordinary bimolecular and termolecular IDs use `k[A][B]` and `k[A][B][M]`.
For `2X`, the event flux is `k[X]^2`; stoichiometry supplies the factor two in
the tendency. The following compact notation uses the concentration name as
its symbol.

| Flux ID(s) | Event-flux definition |
| --- | --- |
| `O_ASSOCIATION` | `k_o_o2_m O O2 M` |
| `O_O3` | `k_o_o3 O O3` |
| `BARTH_RECOMBINATION` | `k_barth O^2 M` |
| `H_O2_ASSOCIATION` | `k_h_o2_m H O2 M` |
| `H_O3`, `O_OH`, `O_HO2` | corresponding `k` times the two reactants |
| `OH_O3`, `HO2_O3`, `OH_H2` | corresponding `k` times the two reactants |
| `H_HO2_2OH`, `H_HO2_H2O_O`, `H_HO2_H2_O2` | branch-specific `k H HO2` |
| `OH_OH`, `OH_HO2`, `HO2_HO2`, `OH_H2O2` | `k OH^2`, `k OH HO2`, `k(T,M) HO2^2`, `k OH H2O2` |
| `H2O2_PHOTOLYSIS`, `H2O_PHOTOLYSIS_A/B` | injected `J` times parent concentration |
| `O3_HARTLEY_GROSS` | gross `JH O3` diagnostic; no tendency row |
| `O3_HARTLEY_PRODUCTS` | `0.9 JH O3` actual reduced excited event |
| `O3_HARTLEY_UNTRACKED` | `0.1 JH O3` diagnostic subset represented by the effective complement |
| `O3_PHOTOLYSIS_GROUND_EFFECTIVE` | `(J_O3_TOTAL - 0.9 JH) O3` |
| `O2_SRC` | `J_SRC O2` |
| `O2_LYMAN_ALPHA_GROSS` | `J_LYA O2` diagnostic |
| `O2_LYMAN_ALPHA` | `0.44 J_LYA O2` represented product event |
| `O2_LYMAN_ALPHA_UNTRACKED` | `0.56 J_LYA O2` diagnostic subset |
| `O2_PHOTOLYSIS_GROUND_EFFECTIVE` | `(J_O2_TOTAL - J_SRC - 0.44 J_LYA) O2` |
| `O2_A_BAND`, `O2_B_BAND`, `O2_IRA_BAND` | `gA O2`, `gB O2`, `gIRA O2` |
| `O1D_RADIATIVE`, `B0_RADIATIVE`, `B1_RADIATIVE`, `DELTA_RADIATIVE` | registered `A` times excited-state concentration |
| `O1D_N2`, `O1D_H2O`, `O1D_H2` | corresponding `k` times O1D and collider |
| `O1D_O2_TOTAL` | `k_o1d_o2 O1D O2` diagnostic, counted once in O1D loss |
| `O1D_O2_B1`, `O1D_O2_B0` | `0.8` and `0.2` times total event flux |
| `B1_O2`, `B1_N2`, `B1_O`, `B1_O3` | corresponding `k` times B1 and collider/reactant |
| `B0_N2`, `B0_O2`, `B0_O`, `B0_O3`, `B0_CO2` | corresponding `k` times B0 and collider/reactant |
| `DELTA_O2`, `DELTA_N2`, `DELTA_O`, `DELTA_O3` | corresponding `k` times Delta and collider/reactant |
| `BARTH_B0_EFFECTIVE` | effective `P_Barth_B0`; algebraic-source diagnostic |

## Branching and yield rules

- Hartley gross `JH O3` is diagnostic. Actual excited and effective-ground
  events sum to the injected total `J_O3_TOTAL O3`, so O3 is lost once.
- Lyman-alpha represented O and O1D sources are `0.44 J_LYA O2`; its 0.56
  diagnostic subset enters the effective ground channel when total equals
  `J_SRC + J_LYA`. O2 is prescribed, so no O2 tendency exists.
- O1D+O2 total loss is evaluated once; its 0.8 B1 and 0.2 B0 event fluxes sum
  to the total exactly.
- `B0 + O3 -> Delta + O3` remains the Li routing assumption applied to the
  JPL18 total B0-loss coefficient; its net O3 coefficient is zero.
- `Delta + O3 -> O + 2 O2` retains the JPL18 topology and therefore produces O
  and consumes O3.

## Reaction-to-tendency coefficient table

Each entry is multiplied by its event flux. `R_H` is derived mechanically as
`nu_OH + nu_HO2`. Zero rows are retained to make algebraic-only events explicit.

| Flux ID | O | O3 | H | R_H | Delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| `O_ASSOCIATION` | -1 | 1 | 0 | 0 | 0 |
| `O_O3` | -1 | -1 | 0 | 0 | 0 |
| `BARTH_RECOMBINATION` | -2 | 0 | 0 | 0 | 0 |
| `H_O2_ASSOCIATION` | 0 | 0 | -1 | 1 | 0 |
| `H_O3` | 0 | -1 | -1 | 1 | 0 |
| `O_OH` | -1 | 0 | 1 | -1 | 0 |
| `O_HO2` | -1 | 0 | 0 | 0 | 0 |
| `OH_O3` | 0 | -1 | 0 | 0 | 0 |
| `HO2_O3` | 0 | -1 | 0 | 0 | 0 |
| `OH_H2` | 0 | 0 | 1 | -1 | 0 |
| `H_HO2_2OH` | 0 | 0 | -1 | 1 | 0 |
| `H_HO2_H2O_O` | 1 | 0 | -1 | -1 | 0 |
| `H_HO2_H2_O2` | 0 | 0 | -1 | -1 | 0 |
| `OH_OH` | 1 | 0 | 0 | -2 | 0 |
| `OH_HO2` | 0 | 0 | 0 | -2 | 0 |
| `HO2_HO2` | 0 | 0 | 0 | -2 | 0 |
| `OH_H2O2` | 0 | 0 | 0 | 0 | 0 |
| `H2O2_PHOTOLYSIS` | 0 | 0 | 0 | 2 | 0 |
| `H2O_PHOTOLYSIS_A` | 0 | 0 | 1 | 1 | 0 |
| `H2O_PHOTOLYSIS_B` | 0 | 0 | 0 | 0 | 0 |
| `O3_HARTLEY_PRODUCTS` | 0 | -1 | 0 | 0 | 1 |
| `O3_PHOTOLYSIS_GROUND_EFFECTIVE` | 1 | -1 | 0 | 0 | 0 |
| `O2_SRC` | 1 | 0 | 0 | 0 | 0 |
| `O2_LYMAN_ALPHA` | 1 | 0 | 0 | 0 | 0 |
| `O2_PHOTOLYSIS_GROUND_EFFECTIVE` | 2 | 0 | 0 | 0 | 0 |
| `O2_A_BAND` | 0 | 0 | 0 | 0 | 0 |
| `O2_B_BAND` | 0 | 0 | 0 | 0 | 0 |
| `O2_IRA_BAND` | 0 | 0 | 0 | 0 | 1 |
| `O1D_RADIATIVE` | 1 | 0 | 0 | 0 | 0 |
| `B0_RADIATIVE` | 0 | 0 | 0 | 0 | 0 |
| `B1_RADIATIVE` | 0 | 0 | 0 | 0 | 0 |
| `DELTA_RADIATIVE` | 0 | 0 | 0 | 0 | -1 |
| `O1D_N2` | 1 | 0 | 0 | 0 | 0 |
| `O1D_O2_B1` | 1 | 0 | 0 | 0 | 0 |
| `O1D_O2_B0` | 1 | 0 | 0 | 0 | 0 |
| `O1D_H2O` | 0 | 0 | 0 | 2 | 0 |
| `O1D_H2` | 0 | 0 | 1 | 1 | 0 |
| `B1_O2` | 0 | 0 | 0 | 0 | 0 |
| `B1_N2` | 0 | 0 | 0 | 0 | 0 |
| `B1_O` | 0 | 0 | 0 | 0 | 0 |
| `B1_O3` | 1 | -1 | 0 | 0 | 0 |
| `B0_N2` | 0 | 0 | 0 | 0 | 1 |
| `B0_O2` | 0 | 0 | 0 | 0 | 1 |
| `B0_O` | 0 | 0 | 0 | 0 | 1 |
| `B0_O3` | 0 | 0 | 0 | 0 | 1 |
| `B0_CO2` | 0 | 0 | 0 | 0 | 1 |
| `DELTA_O2` | 0 | 0 | 0 | 0 | -1 |
| `DELTA_N2` | 0 | 0 | 0 | 0 | -1 |
| `DELTA_O` | 0 | 0 | 0 | 0 | -1 |
| `DELTA_O3` | 1 | -1 | 0 | 0 | -1 |

`O3_HARTLEY_PRODUCTS` is the sole special tendency key; machine-readable
metadata links it to `O3_HARTLEY`. `O3_HARTLEY_GROSS`,
`O3_HARTLEY_UNTRACKED`, the Lyman-alpha
gross/complement diagnostics, `O1D_O2_TOTAL`, and `BARTH_B0_EFFECTIVE` are not
independent dynamic events and are excluded from the tendency sum.

## Residual and production/loss diagnostics

The result exposes:

```text
res_O1D = P_O1D - L_O1D O1D
res_OH = P_OH - L_OH
res_family = OH + HO2 - R_H
res_H2O2 = P_H2O2 - L_H2O2 H2O2
res_B1 = P_B1 - L_B1 B1
res_B0 = P_B0 - L_B0 B0
```

It also exposes `P/L` pairs for O1D, OH, H2O2, B1, B0, and Delta, plus the
Hartley, Lyman-alpha, and Barth gross/product/complement diagnostics. Tests use
relative residual tolerances of `2e-13` for regular synthetic cases and an
absolute `1e-8 molecule cm^-3` family-constraint tolerance.

## Delta remains dynamic

```text
P_Delta = 0.9 JH O3 + gIRA O2 + sum(B0 quenching fluxes)
L_Delta = A_Delta + k_Delta_O2 O2 + k_Delta_N2 N2
          + k_Delta_O O + k_Delta_O3 O3
dDelta/dt = P_Delta - L_Delta Delta
```

There is no `Delta=P/L` closure or `Delta_eq` API. A test changes only supplied
Delta, verifies unchanged `P_Delta`/`L_Delta`, and verifies the exact tendency
change `-L_Delta*change(Delta)`.

## Limitations and stop condition

The deterministic validation case is software/scientific-structure evidence,
not atmospheric validation. M4B does not calculate forcing, integrate time,
assemble a vertical column, or claim sunrise/retrieval performance. M4A now
supplies a static MSIS-derived background, but there is still no spectral
radiative g-factors, HITRAN, 255-vector, column RHS, `solve_ivp`, BDF, Radau, spin-up,
periodic cycle, transport, retrieval, or `updated_2025`.

## M4A background interface note

M4A now constructs the accepted `LocalBackground` interface at each exact
50--100 km grid level from frozen static profile assets. M4B changes only the
photolysis tendency semantics documented in `historical_2020_odd_oxygen.md`.
The eleven `LocalForcing` values remain injected inputs: M4B calculates none
of them.
