# M4D broadening and solar-path geometry review

Status: **GEOMETRY RETAINED / LINE SHAPE NOT FROZEN / HISTORICAL ADVANCED-PARAMETER SOURCE BLOCKER**

Branch: `milestone/m4d-design`

> The earlier Doppler-only freeze recorded in this file is superseded by `docs/m4d_final_design_review.md` and `docs/m4d_pressure_broadening_provenance_followup.md`. The local-width calculation remains useful historical evidence, but it is not a valid full-domain line-shape decision.

This note now separates the part that remains accepted (solar-ray geometry) from the line-shape decision that failed independent review.

## 1. Superseded Doppler-only decision

The earlier design proposed normalized Gaussian Doppler profiles for all three monomer O2 systems and treated pressure broadening as a later sensitivity. That proposal was motivated by the recovered Anqi Li A-band method and by the small Lorentz/Doppler width ratio at the lowest chemistry level.

That decision is **not frozen anymore**.

The independent full-path review demonstrated that an illuminated twilight ray to a 50-100 km target can pass through much denser atmosphere below the chemistry boundary. Therefore pressure broadening cannot be bounded by evaluating only the pressure at the target altitude.

Doppler-only remains acceptable as:

- a historical legacy reference;
- an optically thin/profile-normalization check;
- a numerical comparison case.

It is not the authorized final M4D line-shape model.

## 2. Historical local-width calculation retained as evidence

At the accepted M4A 50-km chemistry level:

```text
z = 50 km
T = 264.9381103515625 K
M = 2.1204504413317356e16 cm^-3
O2 = 4.4529459267966445e15 cm^-3
O2/M = 0.210000...
p approximately 77.563 Pa = 7.6549e-4 atm
```

The earlier diagnostic Lorentz HWHM was

```text
gamma_L(T,p) = p_atm * [(1-xO2)*gamma_air + xO2*gamma_self]
               * (296/T)**n_air
```

and the Doppler HWHM was

```text
gamma_D = nu0 * sqrt(2*k*T*ln(2)/(m*c**2)).
```

Across the accepted target subsets, the maximum local 50-km `gamma_L/gamma_D` values were approximately:

| system | maximum local ratio at 50 km |
| --- | ---: |
| IRA `a(0)-X(0)` | `0.6088%` |
| A `b(0)-X(0)` | `0.3854%` |
| B `b(1)-X(0)` | `0.3342%` |

These numbers remain valid for the local 50-km state. The error was interpreting them as a bound on the complete spherical solar path.

## 3. Full-path counterexample that reopened the gate

`docs/m4d_final_design_review.md` compared Doppler attenuation with a pressure-broadened Voigt sensitivity using the accepted spherical geometry and shell-local state.

With a `+/-20 cm^-1` Voigt attenuation window, the maximum A-band full-band difference relative to Doppler remained approximately `0.4725%` even when considering only rates above `1e-10 s^-1`, already exceeding the declared `0.1%` adequacy criterion.

At weaker illuminated post-90-degree cases, differences reached tens of percent. The `+/-10 -> +/-20 cm^-1` isolated-Voigt comparison also failed the `0.1%` gate for weak A/B twilight cases.

Therefore:

**Doppler-only is rejected as the full-domain M4D baseline.**

## 4. Historical line-shape evidence after provenance follow-up

The three systems must now be treated separately unless historical evidence supports a common model.

### A band

HITRAN2016 Section 2.7.2 documents an advanced principal-isotopologue A-band representation derived from Drouin et al. (2017): speed-dependent Voigt behavior together with collisional line mixing, with a HITRAN-facing first-order Rosenkranz representation derived from scaled W matrices. CIA is a separate spectroscopic component.

The accepted 160-character SpectralCalc line records do not contain the complete advanced parameterization required to execute that historical representation.

Therefore an arbitrary isolated Voigt model must not be promoted to the historical HITRAN2016 A-band baseline solely to obtain numerical convergence.

Current status: **SOURCE/PROVENANCE BLOCKER** pending recovery and freezing of the exact historical executable advanced parameters and formula mapping.

### B band

HITRAN2016 incorporated advanced B-band line-shape information from the Domyslawska measurement series. HITRAN2020 later documented that the speed-dependent Voigt broadening values adopted in HITRAN2016 had been interpreted as half-widths although the source papers reported full widths.

The project must explicitly decide whether `historical_2020` reproduces the released HITRAN2016 advanced values literally or applies the later source-documented correction. Neither choice may be made silently.

Current status: **SOURCE/PROVENANCE + SCIENTIFIC-DESIGN BLOCKER**.

### IRA / 1.27 micron

The discrete HITRAN2016 `a(0)-X(0)` line set is historically close to the HITRAN2012 monomer compilation, whose relevant line parameters were based on Voigt analyses; HITRAN2016 notably improved line positions. Later work demonstrates measurable beyond-Voigt effects at high terrestrial-spectroscopy accuracy, but the current evidence does not establish an HITRAN2016 advanced parameterization analogous to the principal-isotopologue A-band update.

An isolated Voigt treatment therefore remains a defensible **candidate** historical monomer profile for IRA, but it is not yet frozen. The final candidate must still be evaluated consistently in both target excitation and shell attenuation and must pass the full numerical convergence gate.

See `docs/m4d_pressure_broadening_provenance_followup.md` for the detailed source assessment.

## 5. Pressure shifts are part of the remaining gate

The accepted classic HITRAN records include `delta_air`. Because the problematic twilight rays traverse lower, denser shells, pressure shifts must be assessed along the full ray rather than only at the target altitude.

The final per-band specification must state:

- air and self broadening conventions;
- pressure-shift parameters used;
- temperature dependence where defined historically;
- shell-local line-center evaluation;
- explicit behavior when a self-shift or advanced shift parameter is not historically available.

No blanket `delta_air = 0` rule is frozen.

## 6. Solar geometry remains accepted

M4D retains the accepted M4C spherical direct-beam geometry semantics:

- Earth radius `6370 km`;
- radiative top `150 km`;
- chemistry targets `50..100 km`;
- exact spherical ray/shell intersections;
- exact solid-Earth shadowing for `SZA > 90 deg`;
- illuminated tangent rays at the solid-Earth boundary within numerical tolerance.

M4D must not introduce a plane-parallel approximation or a second Earth radius.

The M4C production implementation remains untouched.

## 7. M4D atmospheric/path discretization refinement

The M4C one-kilometre geometry equations and shadow semantics are reused, but the M4D NIR attenuation calculation requires finer deterministic atmospheric sub-stratification to satisfy the proposed numerical tolerance.

The accepted design-forensics rule is:

- derive piecewise-linear atmospheric profiles from the accepted one-kilometre nodes;
- evaluate exact spherical intersections on `0.125 km` sub-shells for the M4D calculation;
- retain `0.0625 km` as the convergence reference.

The previous review found maximum `0.125 -> 0.0625 km` differences below approximately `0.034%` for A/B/IRA in the tested domain.

This is an M4D integration refinement, not a modification of the accepted M4C-R2 UV geometry implementation.

## 8. Shellwise optical depth remains mandatory

The required structure is

```text
tau(nu,z,SZA)
  = sum_shell sigma_band(nu,T_shell,p_shell,...) * n_O2,shell * dl_shell.
```

Using one target-temperature cross section multiplied by a total O2 slant column is rejected because the previous review found multi-percent to tens-of-percent errors in relevant twilight cases.

For shadowed targets the direct beam remains exactly zero from the physical Earth-shadow mask.

## 9. Excitation form retained

For an illuminated target level:

```text
g_band(z,SZA)
  = integral sigma_band(nu,T_target,p_target,...)
             * Phi_sun(nu)
             * exp[-tau(nu,z,SZA)] dnu.
```

The **same selected physical line-shape semantics for a band** must be used consistently for target excitation and shell attenuation. The earlier mixed Doppler-source/Voigt-attenuation experiment was a diagnostic sufficient to reject Doppler-only; it is not a final production prescription.

## 10. Gate decision

**PARTIAL PASS / DESIGN NOT FROZEN.**

Frozen/retained:

- accepted M4C spherical geometry semantics;
- shell-local transfer requirement;
- `0.125 km` M4D sub-stratification with `0.0625 km` convergence reference;
- rejection of Doppler-only over the complete required domain.

Still blocking:

- recover/freeze the historical HITRAN2016 A-band advanced line-shape/line-mixing parameterization;
- resolve the B-band HITRAN2016 width-interpretation defect and freeze the approved historical policy;
- evaluate pressure shifts consistently;
- apply the selected final profile to both target excitation and attenuation;
- demonstrate final line-wing/profile convergence to the declared tolerance.

No M4D implementation is authorized.
