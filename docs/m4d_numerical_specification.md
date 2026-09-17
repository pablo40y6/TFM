# M4D spectroscopy numerical specification — partial / not frozen

Status: **PARTIAL SPECIFICATION ONLY / LINE-SHAPE SOURCE BLOCKER / NOT READY FOR IMPLEMENTATION**

Branch: `milestone/m4d-design`

> This document is not the final M4D implementation specification. The earlier Doppler-only prescription is superseded by `docs/m4d_final_design_review.md` and `docs/m4d_pressure_broadening_provenance_followup.md`. Only the source, scaling, solar-forcing, geometry and convergence conventions explicitly marked retained below may be carried forward.

## 1. Required outputs — retained

For any supplied solar zenith angle, M4D must eventually produce 51-element arrays on the accepted chemistry grid `50..100 km`:

```text
gA(z)    [s^-1]
gB(z)    [s^-1]
gIRA(z)  [s^-1]
```

with target-state semantics:

```text
gA   : O2 X(v''=0) -> b(v'=0)
gB   : O2 X(v''=0) -> b(v'=1)
gIRA : O2 X(v''=0) -> a(v'=0)
```

No M5 time integration belongs to M4D.

## 2. Frozen source chain — retained

### HITRAN2016 target transitions

Use only the accepted/fingerprinted target subsets derived from the untouched SpectralCalc HITRAN2016 export:

```text
gIRA  835 lines  SHA256 8d06f322aa4058ab03150a705bf9765fe356a2c7ecd06df98379c46062d295ad
gA    430 lines  SHA256 176a6c21ee37b1244bd11ef7047f6e31f7cada7edff2c3498f31f8d1f2e92eea
gB    320 lines  SHA256 bb5f8b26a2ad3c9dc31870506c3c05bcdb115b7c5b06d7141c9660c952d83c2d
```

This freezes transition identity/intensity provenance only. It does **not** establish that the classic 160-character records contain every advanced HITRAN2016 line-shape/line-mixing parameter needed by the final M4D calculation.

### TIPS-2017

Use the pinned historical source:

```text
hitranonline/hapi
commit f41d9911f2631eed51b96d6c617b4f27786ad477
path hapi/hapi.py
Git blob caeab1bfaa278b5420adef7efe7ab566991ba763
HAPI version 1.1.0.8.2
```

for O2 local isotopologues 1-3.

### Solar source

Use the Wehrli 1985 WMO/WRC extraterrestrial spectrum and the convention frozen in `docs/m4d_solar_forcing_freeze.md`.

## 3. HITRAN line-strength temperature scaling — retained

For every source line:

```text
S(T) = S(296)
       * Q(296)/Q(T)
       * exp[-c2*E''*(1/T - 1/296)]
       * [1 - exp(-c2*nu0/T)]
         / [1 - exp(-c2*nu0/296)]
```

with

```text
c2 = h*c/k_B = 1.4387768775039336 cm K
```

and `nu0`, `E''` in `cm^-1`.

Do not apply terrestrial isotopic abundance a second time: standard HITRAN `sw` already includes it.

The partition sum for each line is selected by local isotopologue and evaluated with the interpolation semantics of the pinned historical HAPI/TIPS-2017 implementation.

Any project-local reimplementation must reproduce the pinned source to numerical roundoff at regression temperatures and must not depend on current mutable HAPI at runtime.

## 4. Line shape — NOT FROZEN

There is no single authorized M4D line-shape formula yet.

The previous normalized Doppler prescription is retained only as a diagnostic/reference calculation. It failed the full-path adequacy gate because post-90-degree rays can traverse substantially denser air below the chemistry boundary.

Current per-band status:

- **A band:** historical HITRAN2016 principal-isotopologue representation requires recovery of the advanced Drouin-era speed-dependent/line-mixing parameterization before a final profile can be frozen. Classic isolated Voigt is not automatically an acceptable historical substitute.
- **B band:** advanced historical parameters require source recovery and an explicit policy for the later-documented HITRAN2016 FWHM/HWHM interpretation defect.
- **IRA:** isolated Voigt remains a defensible historical candidate for the monomer discrete lines, but it still requires a consistent target+attenuation full-domain convergence run before freeze.

See `docs/m4d_pressure_broadening_provenance_followup.md`.

## 5. Solar spectral photon flux — retained

For each spectral point evaluate Wehrli irradiance by linear interpolation in wavelength:

```text
lambda_nm = 1e7 / nu_cm1
```

and convert `I_lambda [W m^-2 nm^-1]` to

```text
Phi_sun(nu) [photons cm^-2 s^-1 (cm^-1)^-1]
```

using the frozen wavelength-to-wavenumber Jacobian in `docs/m4d_solar_forcing_freeze.md`.

No arbitrary bandwidth factor is applied to HITRAN line strength.

## 6. Solar-path geometry and atmospheric discretization — retained with M4D refinement

Retain the accepted M4C spherical geometry semantics:

- Earth radius `6370 km`;
- radiative top `150 km`;
- exact spherical ray intersections;
- physical solid-Earth shadow mask;
- tangent-ray illumination convention.

Do **not** use a separate plane-parallel geometry.

For M4D NIR transfer, the one-kilometre atmospheric representation was not sufficiently converged in twilight cases. The current design-forensics rule is:

- piecewise-linear interpolation of accepted one-kilometre atmospheric node profiles;
- exact spherical intersections evaluated on deterministic `0.125 km` sub-shells;
- `0.0625 km` retained as convergence reference.

This refines the M4D path integral only; it does not modify the accepted M4C-R2 UV implementation.

## 7. Shellwise optical depth — retained

The required physical structure is

```text
tau(nu,z,SZA)
  = sum_shell sigma_band(nu,T_shell,p_shell,...) 
              * n_O2,shell * dl_shell_cm.
```

A target-temperature cross section multiplied by total O2 slant column is rejected.

The final selected profile must be evaluated shellwise with its required temperature, pressure, broadening, shift and line-mixing state.

For shadowed targets the direct beam is exactly zero only because of the physical Earth-shadow mask.

## 8. Excitation integral — retained in structure

For each band:

```text
g_band(z,SZA)
  = integral sigma_band(nu,T_target,p_target,...)
             * Phi_sun(nu)
             * exp[-tau(nu,z,SZA)] dnu.
```

Units must close to `s^-1`.

At zero absorber column the result must recover the unattenuated integral. Do not reproduce the legacy `tau == 0 -> g = 0` behavior.

The target and attenuation calculations must use the **same selected physical profile semantics for that band**. The mixed Doppler-source/Voigt-attenuation experiment from the independent review was diagnostic only.

## 9. Doppler quadrature evidence — retained as a diagnostic, not final production algorithm

The independent review tested line-centred Gauss-Legendre integration for the Doppler diagnostic.

Against a `+/-10 HWHM`, 128-point reference over representative altitude/SZA cases, `+/-8 HWHM` with 64 points produced maximum relative differences of approximately:

```text
A     0.07584%
B     0.04164%
IRA   0.00120%
```

At 128 points, `8 -> 10 HWHM` changed the tested results by at most approximately:

```text
A     0.00127%
B     0.000188%
IRA   0.000047%
```

This closes the numerical Doppler reference calculation. It does **not** define the final quadrature/support rule for an SDV, line-mixed, or Voigt production model.

The older fixed-trapezoid Doppler mesh prescription in the pre-review draft is superseded and must not be implemented as a frozen requirement.

## 10. Final profile/wing convergence gate — NOT YET CLOSED

For the eventual selected historical profile, convergence must be demonstrated over all 51 target altitudes for at least:

```text
SZA = 0, 60, 85, 89, 89.9, 95, 99 deg
```

plus illuminated tangent and immediately shadowed boundary cases.

The current numerical target remains:

```text
max relative difference <= 1e-3    # 0.1%
```

for values above the declared diagnostic floor `1e-15 s^-1`.

The previous isolated-Voigt `+/-10 -> +/-20 cm^-1` sensitivity did not satisfy this criterion for weak A/B twilight cases. No universal `+/-N cm^-1` cutoff is frozen.

The physical historical profile must be selected first; its appropriate computational support/convergence variables are then to be tested.

Do not loosen the floor or tolerance silently.

## 11. Pressure-shift gate — OPEN

The accepted classic records include `delta_air`, and the problematic twilight rays traverse lower-pressure-altitude shells than the chemistry target.

The final specification must state, per selected band/profile:

- pressure-shift parameter source;
- air/self convention;
- temperature dependence where historically defined;
- shell-local shifted center evaluation;
- behavior when a required historical self-shift or advanced shift is unavailable.

A full-path sensitivity is required once the final profile source is recovered.

## 12. Historical unattenuated validation anchors — retained

The deterministic Wehrli + HITRAN2016 + TIPS calculation from the final design review gave:

| T (K) | `gA0` (s^-1) | `gB0` (s^-1) | `gIRA0` (s^-1) |
| ---: | ---: | ---: | ---: |
| 180 | `6.1914394520e-9` | `3.5752856768e-10` | `1.4549983481e-10` |
| 200 | `6.1963256585e-9` | `3.5805572358e-10` | `1.4573674701e-10` |
| 220 | `6.1999597393e-9` | `3.5852735538e-10` | `1.4593873602e-10` |
| 240 | `6.2025842093e-9` | `3.5895153697e-10` | `1.4611114500e-10` |
| 260 | `6.2043175651e-9` | `3.5933010076e-10` | `1.4625641629e-10` |
| 280 | `6.2051968875e-9` | `3.5966103384e-10` | `1.4637502395e-10` |
| 296 | `6.2052846913e-9` | `3.5988913888e-10` | `1.4645036484e-10` |

Historical comparison anchors remain approximate scale/regression checks, not calibration targets:

```text
A      ~5.35e-9 s^-1
B      ~2.94e-10 s^-1
IRA    ~1.54e-10 s^-1
A+B    ~5.56e-9 s^-1  (independent combined historical scale)
```

No empirical factor may be introduced merely to force agreement.

## 13. Physical/numerical invariants — retained and generalized

The eventual implementation must enforce at least:

- all final `g` values finite and nonnegative;
- shadowed direct beam exactly zero;
- zero absorber column recovers the unattenuated value;
- increasing absorber column cannot increase direct-beam excitation at fixed target state;
- `S(296)` equals source `sw` to numerical roundoff;
- correct TIPS isotopologue selection;
- no second natural-abundance multiplier;
- deterministic source-order invariance;
- accepted target-subset hashes verified before generation.

For isolated non-mixing profiles, integrated line-profile strength closure must reproduce the temperature-scaled line strength.

If line mixing is selected, do not require every algebraic per-line mixing contribution to be individually nonnegative. Instead test the total physical band absorption for finiteness/non-negativity and enforce the normalization/conservation rule of the recovered historical formalism.

## 14. IRA CIA scope — retained as Option B

The historical baseline `gIRA` source is monomer `a(0)-X(0)` excitation. CIA is not silently added to the baseline monomer source or baseline attenuation.

The prior design selected **Option B**, not Option C: CIA remains a required documented twilight sensitivity/limitation. The eventual final M4D specification must state the exact closure evidence expected for that sensitivity and its historical source/provenance; it must not silently substitute current HITRAN CIA data.

## 15. Required evidence before design freeze

Before `docs/m4d_final_design_specification.md` may be created, the design phase must supply:

- frozen executable historical A-band advanced line-shape/line-mixing source and parameter mapping;
- an explicit, approved B-band policy for the documented HITRAN2016 width interpretation defect, with frozen parameter provenance;
- a final per-band/per-isotopologue profile table;
- pressure-shift treatment;
- consistent target+attenuation calculation with the selected profile;
- final profile/wing convergence evidence over the complete validation domain;
- IRA isolated-Voigt full-profile convergence if that remains the chosen historical monomer treatment;
- explicit closure rule for the Option-B CIA twilight sensitivity;
- retained unattenuated `g0(T)` regression table and source-chain checks.

## 16. Implementation boundary

**M4D DESIGN IS NOT FROZEN / M4D IS NOT IMPLEMENTED.**

The blocker is now specifically historical advanced line-shape provenance and the associated per-band scientific decision, followed by final numerical convergence.

No production M4D implementation, implementation PR, M5 work, or modification of accepted M1-M4C-R2 behavior is authorized.
