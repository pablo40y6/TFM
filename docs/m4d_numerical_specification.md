# M4D spectroscopy numerical specification — partial / not frozen

Status: **PARTIAL SPECIFICATION / A AUXILIARY BYTE+MAPPING BLOCKER / B+IRA BASELINE CANDIDATES SELECTED**

Branch: `milestone/m4d-design`

> This is not the final M4D implementation specification. `docs/m4d_final_design_review.md`, `docs/m4d_pressure_broadening_provenance_followup.md`, `docs/m4d_a_band_auxiliary_source_recovery.md`, and `docs/m4d_ira_cia_historical_source_recovery.md` supersede the old Doppler-only prescription. Only the rules explicitly marked retained or selected below may be carried forward.

## 1. Required outputs — retained

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

## 2. Frozen transition/source chain — retained

Use only the accepted/fingerprinted target subsets derived from the untouched SpectralCalc HITRAN2016 export:

```text
gIRA  835 lines  SHA256 8d06f322aa4058ab03150a705bf9765fe356a2c7ecd06df98379c46062d295ad
gA    430 lines  SHA256 176a6c21ee37b1244bd11ef7047f6e31f7cada7edff2c3498f31f8d1f2e92eea
gB    320 lines  SHA256 bb5f8b26a2ad3c9dc31870506c3c05bcdb115b7c5b06d7141c9660c952d83c2d
```

This freezes transition identity/intensity provenance. It does not imply that classic 160-character records contain every advanced/auxiliary A-band parameter required by the historical design.

### TIPS-2017

Use:

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

## 3. HITRAN line-strength temperature scaling — retained

For every line:

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

TIPS interpolation follows the pinned historical HAPI implementation. A project-local implementation must reproduce that source to numerical roundoff and must not depend on current mutable HAPI at runtime.

## 4. Per-band / per-isotopologue profile selection

There is no single common M4D line profile.

### 4.1 A iso 1 / principal isotopologue — not executable yet

The final historical representation must reproduce the HITRAN2016/Drouin speed-dependent + line-mixing treatment. The public Drouin source and exact supplement identity are known:

```text
PMC5103325
NIHMS804415-supplement-supplement_1.pdf
reported size 94.8 kB
```

but the project has not yet frozen the supplement bytes or the executable Drouin-to-HITRAN/Rosenkranz mapping.

Do not substitute isolated Voigt merely for implementation convenience.

### 4.2 A iso 2/3 / rare isotopologues — Galatry historical candidate selected

HITRAN2012/Long et al. document the rare A-band isotopologues with **Galatry** profiles including pressure broadening and Dicke narrowing. HITRAN2016 documents the Drouin replacement specifically for the principal isotopologue rather than an equivalent rare-isotopologue update.

The historical auxiliary identities are:

```text
07_A-band_SDF.dat
07_hit12_0.76mic_Galatry.par
```

The accepted rare-isotopologue integrated strength is approximately `0.4674%` of total A at 296 K, so omitting those lines cannot be justified against a `0.1%` tolerance without calculation.

Selected candidate:

```text
A iso 2/3 -> Long/HITRAN2012 Galatry + historical Dicke-narrowing parameters
```

This remains conditional on exact auxiliary bytes/hash, deterministic line mapping and a HITRAN2016 continuity check.

### 4.3 B band — classic Voigt baseline candidate selected

Use the complete accepted HITRAN2016 classic fields:

```text
gamma_L(p,T)
  = (296/T)^n_air
    * [gamma_air * (p - p_O2) + gamma_self * p_O2]

nu_shifted = nu0 + delta_air * p
```

with pressures in atm and Lorentz HWHM coefficients in `cm^-1 atm^-1`.

`gamma_air` is already an air-broadening coefficient. Do not apply another N2/O2 mixture factor to it.

A source-corrected qSDV sensitivity on the historically covered principal-isotopologue lines is mandatory. The classic-Voigt baseline candidate remains accepted only if that sensitivity changes all validated B rates by `<=0.1%`.

### 4.4 IRA — classic Voigt monomer baseline candidate selected

Use the same classic HITRAN2016 Voigt equations and accepted line fields as B for the discrete `a(0)-X(0)` monomer lines.

This remains conditional on final consistent target+attenuation convergence.

IRA CIA is not folded into this monomer line profile; it is the separate Option-B closure sensitivity in Section 14.

## 5. Solar spectral photon flux — retained

At each spectral point:

```text
lambda_nm = 1e7 / nu_cm1
```

Interpolate Wehrli irradiance linearly in wavelength and convert to:

```text
Phi_sun(nu) [photons cm^-2 s^-1 (cm^-1)^-1]
```

using the frozen wavelength/wavenumber Jacobian. No arbitrary line bandwidth factor is applied.

## 6. Solar geometry and path discretization — retained

Retain the M4C geometry semantics:

- Earth radius `6370 km`;
- radiative top `150 km`;
- exact spherical intersections;
- solid-Earth shadow mask;
- illuminated tangent-ray convention.

For M4D transfer use:

- piecewise-linear interpolation of accepted one-kilometre atmospheric nodes;
- exact intersections on deterministic `0.125 km` sub-shells;
- `0.0625 km` reference for convergence.

Do not modify the accepted M4C-R2 UV implementation.

## 7. Shellwise optical depth — retained

The required structure is:

```text
tau(nu,z,SZA)
  = sum_shell sigma_band(nu,T_shell,p_shell,...)
              * n_O2,shell * dl_shell_cm.
```

The target-temperature-cross-section-times-total-column approximation is rejected.

For classic B/IRA profiles each shell uses shell-local pressure, O2 partial pressure and temperature in the selected width expression, plus shell-local pressure shift.

For A iso 1, shell-local advanced parameters must follow the recovered historical Drouin/HITRAN representation. For A iso 2/3, shell-local broadening/narrowing must follow the recovered Galatry auxiliary parameters.

## 8. Excitation integral — retained

For every band:

```text
g_band(z,SZA)
  = integral sigma_band(nu,T_target,p_target,...)
             * Phi_sun(nu)
             * exp[-tau(nu,z,SZA)] dnu.
```

Units must close to `s^-1`.

At zero absorber column recover the unattenuated integral. Target excitation and shell attenuation must use the same selected physical profile semantics for each isotopologue/profile family.

## 9. Doppler quadrature evidence — diagnostic only

The independent review established a converged Doppler reference with line-centred Gauss-Legendre quadrature:

```text
+/-8 Doppler HWHM / 64 points
```

versus `+/-10 HWHM / 128`, with maximum tested differences approximately:

```text
A     0.07584%
B     0.04164%
IRA   0.00120%
```

At 128 points, `8 -> 10 HWHM` changed results by at most:

```text
A     0.00127%
B     0.000188%
IRA   0.000047%
```

This remains a diagnostic/reference result, not the final pressure-broadened algorithm.

## 10. B/IRA classic-Voigt quadrature candidate

The previous numerical failure arose partly from imposing an arbitrary finite Voigt attenuation window. For B/IRA the preferred candidate strategy is:

1. decompose the target cross section by source line;
2. integrate each target-line contribution on deterministic line-centred quadrature;
3. at every target quadrature node, evaluate `tau_total` from **all accepted absorber lines in that band**;
4. do not impose an arbitrary absorber `+/-10` or `+/-20 cm^-1` cutoff;
5. converge target quadrature support and order against a stricter reference.

Because every accepted target subset is finite, evaluating all absorber lines at a given node is deterministic and avoids confusing numerical wing truncation with physical line-shape selection.

The final support/order is not frozen until the full-domain calculation passes the gate below.

## 11. A-band quadrature — open by profile family

A iso-1 spectral support and convergence must be defined from the recovered Drouin/HITRAN2016 SDV + line-mixing representation and must not be inferred from isolated-Voigt wings.

A iso-2/3 spectral support/convergence must be appropriate to the recovered Galatry representation, including Dicke narrowing. The final A calculation must sum all accepted isotopologues consistently before applying the M4D convergence gate.

## 12. Final numerical convergence gate

For the final selected profile of every band, test all 51 chemistry altitudes for at least:

```text
SZA = 0, 60, 85, 89, 89.9, 95, 99 deg
```

plus an illuminated tangent case and an immediately shadowed case.

Current target:

```text
max relative difference <= 1e-3    # 0.1%
```

for rates above `1e-15 s^-1`. Below that floor use absolute differences and require no negative/nonfinite rates.

Do not silently change the tolerance or floor.

The B/IRA convergence study must test at least:

- target quadrature order refinement;
- target support expansion;
- `0.125 -> 0.0625 km` atmospheric sub-stratification;
- pressure-shift on/off sensitivity;
- all-absorber-lines attenuation evaluation.

The A convergence study must separately validate the numerical controls appropriate to the Drouin/Rosenkranz and Galatry components, then validate their summed `gA`.

## 13. Unattenuated validation — retained

The accepted design-forensics values are:

| T (K) | `gA0` (s^-1) | `gB0` (s^-1) | `gIRA0` (s^-1) |
| ---: | ---: | ---: | ---: |
| 180 | `6.1914394520e-9` | `3.5752856768e-10` | `1.4549983481e-10` |
| 200 | `6.1963256585e-9` | `3.5805572358e-10` | `1.4573674701e-10` |
| 220 | `6.1999597393e-9` | `3.5852735538e-10` | `1.4593873602e-10` |
| 240 | `6.2025842093e-9` | `3.5895153697e-10` | `1.4611114500e-10` |
| 260 | `6.2043175651e-9` | `3.5933010076e-10` | `1.4625641629e-10` |
| 280 | `6.2051968875e-9` | `3.5966103384e-10` | `1.4637502395e-10` |
| 296 | `6.2052846913e-9` | `3.5988913888e-10` | `1.4645036484e-10` |

Historical scales remain comparison anchors only:

```text
A      ~5.35e-9 s^-1
B      ~2.94e-10 s^-1
IRA    ~1.54e-10 s^-1
A+B    ~5.56e-9 s^-1
```

No empirical normalization may be used to force agreement.

## 14. IRA CIA Option B — historical source recovered, exact asset/run open

The monomer baseline excludes CIA from both `gIRA` source and baseline attenuation.

The historical CIA sensitivity is nevertheless required. HITRAN2016 identifies Maté et al. (1999), DOI `10.1029/1999JD900824`, as the revised 1.27-micron CIA source and distinguishes:

- pure-O2 data in `O2-O2`;
- 21:79 O2:N2 mixture data in `O2-Air`.

Do not double count O2-O2 by combining atmospheric O2-Air with a second O2-O2 contribution for the same mixture.

The candidate atmospheric sensitivity is:

```text
tau_CIA(nu)
  = sum_shell k_O2-Air(nu,T_shell)
              * n_O2,shell * n_air,shell * ds_shell.
```

Maté measurements were made at `253`, `273`, and `296 K`; colder M4D shells require an explicitly bounded or separately sourced policy. No post-2016 temperature extension is an automatic historical replacement.

Before milestone closure, freeze the exact historical HITRAN2016 CIA file bytes/hash and run the required twilight sensitivity. See `docs/m4d_ira_cia_historical_source_recovery.md`.

## 15. Physical/numerical invariants

The final implementation must enforce at least:

- all final rates finite and nonnegative;
- shadowed direct beam exactly zero;
- zero absorber column recovers unattenuated excitation;
- increasing absorber column cannot increase direct-beam excitation at fixed target state;
- `S(296) == sw` to numerical roundoff;
- correct TIPS isotopologue selection;
- no second natural-abundance factor;
- deterministic source-order invariance;
- accepted subset hashes verified before generation.

For normalized isolated/Galatry profiles, integrated profile strength must recover `S(T)` according to the recovered historical formalism and numerical tolerance.

For A line mixing, apply non-negativity and conservation tests to the total physical band absorption according to the recovered historical formalism; do not assume every algebraic line-mixing contribution must be individually positive.

## 16. Evidence still required before final design freeze

Before `docs/m4d_final_design_specification.md` may be created, provide:

- frozen Drouin A iso-1 supplement bytes/hash and executable parameter mapping;
- frozen historical A iso-2/3 Galatry auxiliary bytes/hash, deterministic mapping, and HITRAN2016 continuity check;
- final A target+attenuation convergence over all isotopologues;
- final B classic-Voigt target+attenuation convergence;
- corrected B qSDV sensitivity on covered lines;
- final IRA classic-Voigt target+attenuation convergence;
- pressure-shift sensitivity;
- historical IRA CIA file identity/hash, cold-shell policy and twilight sensitivity;
- retained source/TIPS/solar/g0 regression checks.

## 17. Implementation boundary

**M4D DESIGN IS NOT FROZEN / M4D IS NOT IMPLEMENTED.**

No production implementation, implementation PR, M5 work, or modification of accepted M1-M4C-R2 behavior is authorized until the remaining source-materialization and final numerical gates close.
