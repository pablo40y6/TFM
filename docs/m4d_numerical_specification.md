# M4D spectroscopy numerical specification — partial / not frozen

Status: **PARTIAL SPECIFICATION / A SOURCE MATERIALIZATION PASS / EXECUTABLE+NUMERICAL GATES OPEN**

Branch: `milestone/m4d-design`

> This is not the final M4D implementation specification. It records only currently accepted/selected rules. Production implementation remains unauthorized until the open gates in Section 17 close.

## 1. Required outputs

For any supplied solar zenith angle, M4D must eventually produce 51-element arrays on the accepted `50..100 km` chemistry grid:

```text
gA(z)    [s^-1]
gB(z)    [s^-1]
gIRA(z)  [s^-1]
```

with:

```text
gA   : O2 X(v''=0) -> b(v'=0)
gB   : O2 X(v''=0) -> b(v'=1)
gIRA : O2 X(v''=0) -> a(v'=0)
```

No M5 time integration belongs to M4D.

## 2. Frozen transition/source chain

Use only the accepted/fingerprinted target subsets derived from the untouched SpectralCalc HITRAN2016 export:

```text
gIRA  835 lines  SHA256 8d06f322aa4058ab03150a705bf9765fe356a2c7ecd06df98379c46062d295ad
gA    430 lines  SHA256 176a6c21ee37b1244bd11ef7047f6e31f7cada7edff2c3498f31f8d1f2e92eea
gB    320 lines  SHA256 bb5f8b26a2ad3c9dc31870506c3c05bcdb115b7c5b06d7141c9660c952d83c2d
```

This freezes transition identity/intensity provenance. It does not mean the classic 160-character records contain every advanced A-band parameter.

### TIPS-2017

Use the historical source:

```text
hitranonline/hapi
commit f41d9911f2631eed51b96d6c617b4f27786ad477
path hapi/hapi.py
Git blob caeab1bfaa278b5420adef7efe7ab566991ba763
HAPI version 1.1.0.8.2
```

for O2 local isotopologues 1-3.

### Solar source

Use the frozen Wehrli 1985 WMO/WRC extraterrestrial spectrum convention from `docs/m4d_solar_forcing_freeze.md`.

## 3. HITRAN line-strength temperature scaling

For every accepted line:

```text
S(T) = S(296)
       * Q(296)/Q(T)
       * exp[-c2*E''*(1/T - 1/296)]
       * [1 - exp(-c2*nu0/T)]
         / [1 - exp(-c2*nu0/296)]

c2 = 1.4387768775039336 cm K
```

`nu0` and `E''` are in `cm^-1`.

Do not apply terrestrial abundance a second time. Standard HITRAN `sw` already includes it.

TIPS interpolation follows the pinned historical HAPI implementation. A project-local implementation must reproduce that source and must not depend on a mutable current HAPI installation at runtime.

## 4. HITRAN diluent semantics — corrected

For this project, `air` and `self` are **diluent choices**, not quantities that may be mixed arbitrarily after a coefficient has already been defined as air-broadened.

For O2 in the terrestrial atmospheric baseline, use the historical HITRAN **air** coefficient with shell atmospheric pressure:

```text
gamma_L_air(p,T)
  = gamma_air(296) * p * (296/T)^n_air

nu_shifted_air(p)
  = nu0 + delta_air * p
```

Do **not** use

```text
gamma_air*(p-p_O2) + gamma_self*p_O2
```

when `gamma_air` is itself the HITRAN air-diluent coefficient. For the O2 A band HITRAN2016 explicitly constructed air parameters from the Drouin foreign/self information using the atmospheric N2:O2 mixture.

`gamma_self` is retained for an explicitly self/O2 diluent calculation, not as an additional atmospheric 21% term on top of an already air-defined coefficient.

Any non-air sensitivity must declare its diluent composition explicitly.

## 5. Per-band / per-isotopologue profile selection

There is no single common M4D line profile.

### 5.1 A iso 1: 91 magnetic-dipole lines

The Drouin sources are now materialized.

Official supplement:

```text
Elsevier PII S0022407316301108, mmc1.pdf
bytes 89406
SHA-256 12e621d3b5d17e7648d140ea16134e3c04096bd7e47e2c1bb0e2084adeccbb51
```

Structured manuscript:

```text
PMC5103325 XML
bytes 310708
SHA-256 935fd09d5f619f7eb3f7fac5347e80fa81bc23d3158dc9c519874bb161c364fe
```

Tables 4/5 provide `91` line-by-line magnetic-dipole parameters and map `91/91` to the historical principal-isotopologue `d` transitions.

For each of these lines the selected profile family is **speed-dependent Voigt**, using Drouin/HITRAN2016 parameters. The paper supplies, per line, foreign/self widths and temperature exponents, foreign/self pressure shifts and linear shift-temperature coefficients, and speed-dependence parameter `S`.

The executable isolated-line convention is frozen in `docs/m4d_a_band_sdv_semantics_freeze.md`: `Gam2 = S*Gam0`, `Shift2 = 0`, `anuVC = 0`, `eta = 0`, with shell-local Drouin foreign/self width and shift equations. Do not substitute classic Voigt on these 91 lines merely for convenience.

### 5.2 A iso 1: line mixing on 70/91 magnetic-dipole lines

Drouin supplement Table 22 provides first-order air Rosenkranz `Y` coefficients at:

```text
200 K, 250 K, 296 K, 340 K
```

for `70` of the `91` magnetic-dipole lines. After branch-label normalization the mapping is unique.

The `21` magnetic-dipole lines without a Table-22 Y value are explicitly identified in `docs/m4d_a_band_drouin_materialization_audit.md`. Their historical integrated strength is about `0.0131464%` of iso-1 A.

Selected historical_2020 rule:

```text
70 lines: SDV + first-order Rosenkranz Y(T)
          exact Table-22 nodes at 200/250/296/340 K
          piecewise-linear interpolation inside 200..340 K
          T<200 K nominal 200-K clamp + required extrapolation/Y=0 envelope
21 lines: SDV with Y=0 nominal; no invented LM term
```

This operational rule is selected in `docs/m4d_a_band_table22_temperature_policy.md`; the low-temperature and no-Y sensitivities remain numerical closure gates.

### 5.3 A iso 1: 59 electric-quadrupole lines

The remaining `59` principal-isotopologue A lines are local-flag `q` electric-quadrupole transitions, not part of the Drouin magnetic-dipole update.

Candidate historical treatment:

```text
accepted target-edition classic HITRAN parameters/profile
```

Do not copy Drouin SDV/LM parameters onto them.

Their historical integrated-strength fraction is about `0.00079353%` of iso-1 A, but the final twilight calculation must still verify that their actual contribution is negligible at the project tolerance.

### 5.4 A iso 2/3: historical Galatry

The historical Long/HITRAN2012 Galatry sources are materialized:

```text
07_A-band_SDF.dat
bytes 6229
SHA-256 7cfefb8040a89cb0e4948c2811a6766b793181646d8188ebfa4d646e063dbd26

07_hit12_0.76mic_Galatry.par
bytes 47231
SHA-256 69c9fd181b5aba8aa818dc906bdc216aaa8cf038eb5687dd4da8f2bb9bf42dab
```

The historical auxiliary maps `430/430` to the HITRAN2012 A system and supplies complete air/self Dicke coefficients for the `140 + 140` rare lines.

Frozen precedence:

```text
nu, S, E'', gamma_air, gamma_self, n_air, delta_air:
    accepted target-edition HITRAN line record

Galatry/Dicke narrowing coefficient:
    quantum-identity-matched historical auxiliary field
```

For terrestrial baseline shells use the **air** Galatry/Dicke parameters under the same air-diluent semantics in Section 4. Do not combine the already air-defined coefficient with another atmospheric self fraction.

The accepted HITRAN2016 raw source must still pass a local `280/280`, zero-ambiguity continuity map to the historical auxiliary before implementation freeze.

### 5.5 B band: classic Voigt baseline candidate

Use the accepted HITRAN2016 classic air fields:

```text
gamma_L = gamma_air * p * (296/T)^n_air
nu_shifted = nu0 + delta_air * p
```

with shell atmospheric pressure in atm.

A source-corrected qSDV sensitivity on the historically covered principal-isotopologue lines is mandatory. If it changes any scientifically retained B rate by more than `0.1%`, reopen this baseline candidate.

### 5.6 IRA: classic Voigt monomer baseline candidate

Use the same classic HITRAN2016 air-diluent Voigt equations for the accepted `a(0)-X(0)` monomer lines.

IRA CIA is a separate Option-B attenuation sensitivity; it is not folded into the monomer line profile or monomer production coefficient.

## 6. Solar photon flux

At each spectral point:

```text
lambda_nm = 1e7 / nu_cm1
```

Interpolate Wehrli irradiance linearly in wavelength and convert to

```text
Phi_sun(nu) [photons cm^-2 s^-1 (cm^-1)^-1]
```

using the frozen wavelength/wavenumber Jacobian. No arbitrary line bandwidth factor is applied.

## 7. Geometry and path discretization

Retain accepted M4C geometry:

- Earth radius `6370 km`;
- radiative top `150 km`;
- exact spherical intersections;
- solid-Earth shadow mask;
- accepted illuminated tangent convention.

For M4D NIR transfer use:

- piecewise-linear interpolation of accepted one-kilometre atmospheric nodes;
- exact intersections on deterministic `0.125 km` sub-shells;
- `0.0625 km` as refinement reference.

Do not modify M4C-R2 UV behavior.

## 8. Shellwise optical depth

Required structure:

```text
tau(nu,z,SZA)
  = sum_shell sigma_band(nu,T_shell,p_shell,...)
              * n_O2,shell * dl_shell_cm
```

The target-temperature-cross-section-times-total-column approximation is rejected.

Each shell uses the same per-transition profile family as the target calculation:

- A d: selected Drouin SDV / Rosenkranz semantics;
- A q: classic target-edition profile candidate;
- A rare: historical Galatry;
- B: classic Voigt candidate;
- IRA: classic Voigt candidate.

## 9. Excitation integral

For every band:

```text
g_band(z,SZA)
  = integral sigma_band(nu,T_target,p_target,...)
             * Phi_sun(nu)
             * exp[-tau(nu,z,SZA)] dnu
```

Units must close to `s^-1`.

At zero absorber column recover the unattenuated integral. Target excitation and shell attenuation must use identical physical profile semantics for each line class.

## 10. B/IRA spectral quadrature candidate

For classic B/IRA profiles:

1. decompose the target cross section by source line;
2. integrate each target-line contribution on deterministic line-centred quadrature;
3. at every target node evaluate attenuation from **all accepted absorber lines in the band**;
4. do not impose an arbitrary absorber `+/-10` or `+/-20 cm^-1` cutoff;
5. converge target support/order against a stricter reference.

Final support/order remains open until the full-domain gate passes.

## 11. A-band quadrature

A requires independent controls by component:

- SDV target/source quadrature for 91 d lines;
- Rosenkranz LM evaluation for the 70 covered d lines;
- classic-profile integration for 59 q lines;
- Galatry integration for 280 rare lines.

All accepted components must be summed consistently before the final `gA` convergence test.

No isolated-Voigt wing rule is automatically transferred to the advanced A components.

## 12. Pressure-shift sensitivity

The final calculation must compare shifts on/off over the full path domain.

Classic components use:

```text
nu_shifted = nu0 + delta_air * p
```

with no invented temperature dependence.

Drouin d lines use the selected advanced historical pressure/temperature shift relation from Tables 4/5 / HITRAN2016 semantics.

## 13. Unattenuated validation anchors

Accepted design-forensics values:

| T (K) | `gA0` (s^-1) | `gB0` (s^-1) | `gIRA0` (s^-1) |
| ---: | ---: | ---: | ---: |
| 180 | `6.1914394520e-9` | `3.5752856768e-10` | `1.4549983481e-10` |
| 200 | `6.1963256585e-9` | `3.5805572358e-10` | `1.4573674701e-10` |
| 220 | `6.1999597393e-9` | `3.5852735538e-10` | `1.4593873602e-10` |
| 240 | `6.2025842093e-9` | `3.5895153697e-10` | `1.4611114500e-10` |
| 260 | `6.2043175651e-9` | `3.5933010076e-10` | `1.4625641629e-10` |
| 280 | `6.2051968875e-9` | `3.5966103384e-10` | `1.4637502395e-10` |
| 296 | `6.2052846913e-9` | `3.5988913888e-10` | `1.4645036484e-10` |

These are regression anchors for line strengths/solar integration, not forced answers for the final pressure-broadened transfer.

No empirical normalization may be used to force agreement.

## 14. IRA CIA Option B

The monomer baseline excludes CIA from production and baseline attenuation.

The required closure sensitivity uses historical Maté `O2-Air` data and must not separately add O2-O2 for the same atmospheric mixture:

```text
tau_CIA(nu)
  = sum_shell k_O2-Air(nu,T_shell)
              * n_O2,shell
              * n_air,shell
              * ds_shell
```

with `k` in `cm^5 molecule^-2`.

Frozen temperature policy:

```text
253 <= T <= 296 K:
    linear interpolation among measured Maté temperature sets

T < 253 K:
    nominal = 253-K endpoint

T > 296 K:
    nominal = 296-K endpoint

outside measured range:
    also propagate min/max envelope of the three measured spectra
```

Endpoint clamping is a sensitivity convention, not a claim of measured extrapolation. Do not silently use the post-2016 theoretical temperature extension.

The historical Maté numerical source is now materialized through the surviving `O2-O2_2011.cia` byte witness plus the explicit HITRAN2016 pair-semantic correction. The source gate is PASS; remaining CIA gates are common-grid/support handling, negative experimental-sample sensitivity, and the full twilight rate sensitivity.

## 15. Numerical convergence gate

Test all 51 chemistry altitudes for at least:

```text
SZA = 0, 60, 85, 89, 89.9, 95, 99 deg
```

plus an illuminated tangent case and an immediately shadowed case.

Current gate:

```text
max relative difference <= 1e-3    # 0.1%
```

for rates above `1e-15 s^-1`. Below the floor report absolute differences and require finite/nonnegative results.

Required refinements/sensitivities include:

- target spectral support/order;
- `0.125 -> 0.0625 km` path refinement;
- pressure shifts on/off;
- B corrected qSDV sensitivity;
- A 21 no-Y d-line treatment;
- A q-line contribution;
- A component-specific quadrature refinements;
- IRA historical CIA nominal/envelope sensitivity.

Do not silently change the tolerance or floor.

## 16. Physical/numerical invariants

The final implementation must enforce at least:

- final rates finite and nonnegative;
- shadowed direct beam exactly zero;
- zero absorber column recovers unattenuated excitation;
- increasing absorber column cannot increase direct-beam excitation at fixed target state;
- `S(296) == sw` to numerical roundoff;
- correct TIPS isotopologue selection;
- no second natural-abundance factor;
- deterministic source-order invariance;
- accepted subset hashes verified before generation.

For Voigt/Galatry components, integrated normalized profile strength must recover `S(T)` within tolerance.

For A line mixing, non-negativity/conservation checks apply to the total physical band absorption according to the selected Rosenkranz/Drouin formalism; individual algebraic mixing contributions need not be positive.

## 17. Evidence still required before final design freeze

Before `docs/m4d_final_design_specification.md` may be created:

- retain/regression-test the frozen SDV evaluator for the 91 Drouin d lines;
- retain/regression-test the selected Table-22 `Y(T)` evaluation semantics;
- quantify the required low-temperature Y envelope, 21 no-Y d-line sensitivity, and 59 q-line contribution;
- complete the local accepted-HITRAN2016 rare continuity map (`91/91` Drouin is PASS; `280/280` Galatry remains open);
- run full A target+attenuation convergence;
- run full B classic-Voigt convergence and corrected qSDV sensitivity;
- run full IRA classic-Voigt convergence;
- quantify pressure-shift sensitivity;
- use the frozen historical Maté byte witness and close CIA grid/negative-sample handling plus twilight sensitivity;
- retain TIPS/solar/g0 regression checks.

## 18. Implementation boundary

**M4D DESIGN IS NOT FROZEN / PRODUCTION IMPLEMENTATION IS NOT AUTHORIZED.**

The source-discovery/byte blockers for A and historical Maté CIA are closed. The remaining work is rare-line edition continuity and the declared numerical/sensitivity/convergence gates. Do not advance to M5.
