# M4D spectroscopy numerical specification

Status: **DESIGN SPECIFICATION FROZEN FOR IMPLEMENTATION REVIEW / NO CODE YET**

Branch: `milestone/m4d-design`

This document consolidates the numerical rules for the three M4D O2 solar-excitation coefficients after the independent source investigation. It is an implementation specification, not an implementation commit.

## 1. Required outputs

For any supplied solar zenith angle, M4D must produce 51-element arrays on the accepted chemistry grid `50..100 km`:

```text
gA(z)    [s^-1]
gB(z)    [s^-1]
gIRA(z)  [s^-1]
```

with the accepted target-state semantics:

```text
gA   : O2 X(v''=0) -> b(v'=0)
gB   : O2 X(v''=0) -> b(v'=1)
gIRA : O2 X(v''=0) -> a(v'=0)
```

No M5 time integration is part of this milestone.

## 2. Frozen source chain

### HITRAN2016 target transitions

Use only the already accepted/fingerprinted target subsets derived from the untouched SpectralCalc HITRAN2016 export.

Canonical all-isotopologue subset hashes:

```text
gIRA  835 lines  SHA256 8d06f322aa4058ab03150a705bf9765fe356a2c7ecd06df98379c46062d295ad
gA    430 lines  SHA256 176a6c21ee37b1244bd11ef7047f6e31f7cada7edff2c3498f31f8d1f2e92eea
gB    320 lines  SHA256 bb5f8b26a2ad3c9dc31870506c3c05bcdb115b7c5b06d7141c9660c952d83c2d
```

The raw source itself is not redistributed automatically; deterministic extraction/provenance must reproduce these fingerprints.

### TIPS-2017

Use the historical official HAPI source pinned at:

```text
hitranonline/hapi
commit f41d9911f2631eed51b96d6c617b4f27786ad477
hapi/hapi.py
Git blob ca... = caeab1bfaa278b5420adef7efe7ab566991ba763
HAPI version 1.1.0.8.2
```

for O2 local isotopologues 1-3.

### Solar source

Use the Wehrli 1985 WMO/WRC extraterrestrial spectrum and the convention frozen in `docs/m4d_solar_forcing_freeze.md`.

## 3. HITRAN line-strength temperature scaling

For every source line, use the standard HITRAN expression at target/shell temperature `T`:

```text
S(T) = S(296)
       * Q(296)/Q(T)
       * exp[-c2*E''*(1/T - 1/296)]
       * [1 - exp(-c2*nu0/T)]
         / [1 - exp(-c2*nu0/296)]
```

where

```text
c2 = h*c/k_B expressed in cm K
   = 1.4387768775039336 cm K using exact SI h, c and k_B
```

and `nu0`, `E''` are in `cm^-1`.

Do not add another terrestrial-isotopic-abundance factor: standard HITRAN `sw` already contains it.

### TIPS interpolation

To preserve the historical TIPS implementation semantics, use the interpolation convention of the pinned HAPI source rather than inventing a new one. Its `AtoB` routine is explicitly a **3-/4-point Lagrange interpolation** over the historical TIPS-2017 temperature/Q arrays.

The project implementation may reimplement this narrow interpolation locally, but it must reproduce the pinned HAPI values to numerical roundoff at test temperatures. It must not import a mutable current HAPI installation at runtime.

## 4. Frozen line shape

Use the normalized Doppler-only Gaussian frozen in `docs/m4d_broadening_and_geometry_freeze.md`.

For each line/isotopologue:

```text
gamma_D = nu0 * sqrt(2*k_B*T*ln(2) / (m*c^2))

g_D(nu) = sqrt(ln(2)/pi) / gamma_D
          * exp[-ln(2)*((nu-nu0)/gamma_D)^2]
```

so that

```text
integral g_D(nu) dnu = 1
sigma_line(nu,T) = S(T) * g_D(nu)
integral sigma_line dnu = S(T)
```

Use isotopologue-specific molecular masses from a pinned source/constants table. Pressure broadening is excluded from baseline and checked separately as a sensitivity.

## 5. Solar spectral photon flux

For each spectral point, evaluate the Wehrli irradiance through linear interpolation in wavelength:

```text
lambda_nm = 1e7 / nu_cm1
```

and convert `I_lambda [W m^-2 nm^-1]` to

```text
Phi_sun(nu) [photons cm^-2 s^-1 (cm^-1)^-1]
```

with the wavelength-to-wavenumber Jacobian exactly as frozen in `docs/m4d_solar_forcing_freeze.md`.

No arbitrary bandwidth factor is applied to a HITRAN line strength; integration is explicitly over wavenumber.

## 6. Solar-path optical depth

Reuse the accepted M4C exact spherical path matrix and shadow mask.

For each target altitude, SZA and spectral point:

```text
tau(nu,z,SZA)
  = sum_shell n_O2_shell * dl_shell_cm * sigma_band(nu,T_shell)
```

with:

- M4C one-km shells from 0 to 150 km;
- endpoint-mean O2 shell density convention inherited unchanged from M4C;
- accepted radiative-background shell temperatures;
- shell-local temperature-scaled line strengths and Doppler widths;
- exactly zero direct beam for shadowed target/SZA pairs.

The target-level cross section in the excitation integral is evaluated at the target temperature.

## 7. Excitation integral

For each band:

```text
g_band(z,SZA)
 = integral sigma_band(nu,T_target)
            * Phi_sun(nu)
            * exp[-tau(nu,z,SZA)] dnu
```

Units must close to `s^-1`.

`tau=0` must recover the unattenuated integral. Do not inherit the legacy `tau==0 -> g=0` behavior.

## 8. Deterministic spectral quadrature

The Doppler-only spectrum permits a compact line-local mesh rather than an enormous full-band uniform mesh.

For each band:

1. For every target line, determine the maximum Doppler HWHM over all accepted radiative/target temperatures used by the calculation.
2. Define that line's support as `nu0 +/- 8*gamma_D,max`.
3. Merge overlapping support intervals; regions outside the merged intervals contribute zero under the numerical Doppler truncation.
4. Let `gamma_D,min` be the minimum Doppler HWHM over all target lines and accepted temperatures.
5. Start with a deterministic maximum mesh step
   `h0 = gamma_D,min / 4` inside every merged interval.
6. Include interval boundaries and exact line centers in the mesh.
7. Evaluate the integral with deterministic trapezoidal quadrature on the sorted unique mesh.
8. Refine by halving the maximum step until the convergence gate below passes.

The `+/-8 HWHM` Gaussian support makes the omitted single-line tail far below the required numerical tolerance; nevertheless a `+/-10 HWHM` support comparison is mandatory as a separate convergence check.

The chosen/final resolved mesh and its hash/metadata must be recorded in the generated M4D asset/evidence rather than hidden in code.

## 9. Numerical convergence gate

Convergence is checked across all 51 chemistry altitudes for at least the SZA set already used in accepted M4C scientific validation:

```text
0, 60, 85, 89.9, 95, 99 degrees
```

plus any altitude-specific near-shadow cases needed to exercise an illuminated tangent ray and an immediately shadowed ray.

For each of `gA`, `gB`, `gIRA`, compare successive step refinement and `8 -> 10 HWHM` support expansion.

Required criterion for values above an absolute diagnostic floor of `1e-15 s^-1`:

```text
max relative difference <= 1e-3   # 0.1%
```

Below that floor use absolute differences and require no artificial negative/nonfinite rates.

If the criterion is not met, continue refinement; do not loosen the tolerance silently.

## 10. Historical unattenuated validation anchors

Yankovsky & Manuilova (2006), Table 1, reports top-of-atmosphere direct photoexcitation rates:

```text
A / 762 nm   5.35e-9  s^-1
B / 689 nm   2.94e-10 s^-1
IRA / 1.27um 1.54e-10 s^-1
```

The M4D reconstruction uses newer HITRAN2016 spectroscopy and the frozen Wehrli/WMO spectrum, so these are independent **scale/regression anchors**, not numbers to force by renormalization.

At 296 K, an unattenuated all-isotopologue calculation must be reported for direct comparison. A discrepancy larger than 30% for any band is a STOP/INVESTIGATE condition before milestone closure. No empirical scale factor may be introduced merely to hit the historical values.

The pre-implementation summed-strength/band-center estimates already give the correct order of magnitude (`~6.23e-9`, `~3.60e-10`, `~1.46e-10 s^-1`).

## 11. Physical invariants

Tests must enforce at least:

- all `g` values finite and nonnegative;
- shadowed direct-beam values exactly zero;
- at zero O2 slant column, attenuated = unattenuated;
- adding O2 column cannot increase a direct-beam g-factor at fixed target state;
- `S(T)` equals source `sw` at exactly 296 K;
- Doppler profiles integrate to the temperature-scaled line strengths within numerical tolerance;
- TIPS local isotope selection is correct for every line;
- natural abundance is not applied twice;
- spectral integration result is invariant to source-line ordering;
- target-subset hashes are verified before generation.

## 12. Baseline CIA scope

Follow `docs/m4d_ira_cia_scope_freeze.md`: `gIRA` baseline uses monomer `a(0)-X(0)` lines only. CIA is not added to production or baseline attenuation; it is a documented later twilight sensitivity.

## 13. Required evidence before M4D closure

The implementation task must produce:

- frozen compact HITRAN target-line assets or a licence-compatible deterministic derivative plus provenance manifest;
- frozen O2 TIPS-2017 asset + extraction script + SHA-256;
- frozen Wehrli-derived solar asset + provenance + SHA-256;
- spectral mesh/convergence evidence;
- 296-K unattenuated validation table against historical A/B/IRA anchors;
- altitude/SZA diagnostic tables including twilight/shadow cases;
- Doppler-vs-Voigt sensitivity at representative 50-km/high-pressure conditions;
- all inherited M1-M4C-R2 tests still passing;
- new M4D tests/validator passing.

## 14. Implementation boundary

The scientific/numerical design above is sufficiently specified for an implementation task **after a final independent design review**.

M4D implementation must not alter M1-M4C-R2 accepted scientific behavior, must not start the 255-ODE solver, and must not advance to M5.