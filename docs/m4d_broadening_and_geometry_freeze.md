# M4D broadening and solar-path geometry freeze

Status: **INDEPENDENT REVIEW FOUND FULL-DOMAIN BROADENING BLOCKER / GEOMETRY RETAINED**

Branch: `milestone/m4d-design`

> **Independent-review update:** the local 50-km width-ratio argument below is valid for chemistry-level pressures but does not bound post-90-degree spherical rays that traverse denser air below 50 km. Full-domain numerical tests in `docs/m4d_final_design_review.md` find material Voigt sensitivity. The geometry decision remains valid; the Doppler-only line-shape decision is reopened by this concrete counterexample.

This note freezes two M4D design choices: the baseline line shape and the direct-beam solar geometry. It does not yet authorize implementation because the spectral integration/convergence specification and the IRA CIA decision remain separate gates.

## 1. Baseline line shape: Doppler-only

The historical M4D baseline will use normalized Gaussian Doppler profiles for the monomer O2 lines in `gIRA`, `gA`, and `gB`.

Pressure/Lorentz broadening is not included in the baseline line profile. It is retained as a quantitative sensitivity/diagnostic and the source HITRAN broadening parameters remain preserved in provenance.

This choice is supported independently by:

1. Anqi Li's 2017 thesis and recovered `doppler.m`/`gfactor.m`, which explicitly neglect Lorentz broadening for the upper-mesosphere A-band calculation;
2. the accepted M4A atmospheric background, which allows the pressure/Doppler ratio to be evaluated directly at the densest chemistry level;
3. the complete acquired M4D target-line subsets, including all three HITRAN2016 O2 line-list isotopologues.

## 2. Conservative quantitative check at 50 km

The accepted M4A background at the lowest chemistry level gives:

```text
z = 50 km
T = 264.9381103515625 K
M = 2.1204504413317356e16 cm^-3
O2 = 4.4529459267966445e15 cm^-3
O2/M = 0.210000...
```

Using the ideal-gas law, this corresponds to approximately:

```text
p = 77.563 Pa = 7.6549e-4 atm
```

This is the largest pressure in the 50-100 km chemistry domain, so it is the conservative endpoint for collisional broadening.

For each acquired target line, the diagnostic Lorentz HWHM was calculated from the HITRAN air/self broadening coefficients as

```text
gamma_L(T,p) = p_atm * [ (1-xO2)*gamma_air + xO2*gamma_self ]
               * (296 K / T)**n_air
```

and compared with the thermal Doppler HWHM

```text
gamma_D = nu0 * sqrt( 2*k*T*ln(2) / (m*c**2) )
```

using the corresponding O2 isotopologue mass.

Results over **every line in each target subset**:

| system | lines | median gamma_L/gamma_D | maximum gamma_L/gamma_D |
| --- | ---: | ---: | ---: |
| IRA `a(0)-X(0)` | 835 | 0.4241% | 0.6088% |
| A `b(0)-X(0)` | 430 | 0.2650% | 0.3854% |
| B `b(1)-X(0)` | 320 | 0.2391% | 0.3342% |

Worst-case lines at 50 km:

- IRA: iso 2, 7875.477741 cm^-1; `gamma_D = 7.87357e-3 cm^-1`, `gamma_L = 4.79351e-5 cm^-1`;
- A: iso 2, 13120.268403 cm^-1; `gamma_D = 1.31171e-2 cm^-1`, `gamma_L = 5.05542e-5 cm^-1`;
- B: iso 2, 14486.101611 cm^-1; `gamma_D = 1.44826e-2 cm^-1`, `gamma_L = 4.84045e-5 cm^-1`.

Since atmospheric number density falls rapidly above 50 km, the Lorentz/Doppler ratios decrease further over the rest of the chemistry domain.

Therefore pressure broadening is safely sub-percent relative to Doppler HWHM throughout the baseline 50-100 km domain. Doppler-only is a quantitatively justified historical baseline rather than merely an inherited assumption.

## 3. Doppler profile convention

For line center `nu0` and Doppler HWHM `gamma_D`, use a normalized Gaussian in wavenumber whose integral is unity:

```text
integral g_D(nu-nu0,T) dnu = 1
```

The temperature-scaled HITRAN line strength then satisfies

```text
integral sigma_line(nu,T) dnu = S(T)
```

This normalization is an explicit invariant and prevents inheritance of the legacy `size(freq,1)` normalization quirk.

No empirical extra abundance factor is applied to `S(T)`.

## 4. Pressure-broadening sensitivity requirement

Although excluded from the baseline, one implementation-level sensitivity check must compare the Doppler-only result with a Voigt result at representative conditions including 50 km. The purpose is not to reopen the baseline but to confirm that the sub-percent width ratio does not create a material g-factor difference under the chosen spectral quadrature/self-shielding scheme.

The sensitivity must use the preserved HITRAN `gamma_air`, `gamma_self`, and `n_air` fields and must be reported separately from the frozen baseline.

## 5. Solar geometry: reuse accepted M4C spherical-shell paths

M4D will reuse the already accepted M4C spherical direct-beam geometry without changing its semantics.

The accepted implementation is `src/tfm_photochem/historical_2020/uv_geometry.py` and defines:

- Earth radius: 6370 km;
- top of radiative column: 150 km;
- chemistry targets: 50-100 km at 1 km spacing;
- radiative shells: 0-150 km with 1 km shell edges;
- exact spherical ray/shell intersection lengths;
- exact solid-Earth shadowing for SZA > 90 degrees;
- tangent rays remain illuminated at the solid-Earth boundary within numerical tolerance.

This geometry is already independently validated in M4C-R2 and is the appropriate common geometry for UV/VUV and O2 NIR direct solar radiation in the historical model.

M4D must not introduce a plane-parallel approximation or a separate Earth radius.

## 6. O2 optical-depth integration along the accepted geometry

M4C already integrates endpoint-mean shell densities along the exact path matrix. For M4D, however, the NIR O2 line cross section depends on local shell temperature.

Therefore the line-resolved optical depth cannot generally be collapsed to

```text
tau(nu) = sigma(nu,T_target) * total_O2_slant_column
```

because `T` varies along the solar ray.

The M4D baseline optical depth must instead have the shell-resolved form

```text
tau(nu, z_target, SZA)
    = sum_shell [ n_O2_shell * dl_shell
                  * sigma_O2(nu, T_shell) ]
```

where:

- `dl_shell` comes directly from the accepted M4C spherical path matrix;
- `n_O2_shell` uses the accepted radiative O2 background and the same endpoint-mean shell convention as M4C;
- `T_shell` comes from the accepted radiative/background temperature field;
- `sigma_O2` is built from the frozen target-line HITRAN2016 subsets, TIPS-2017 temperature scaling, and the Doppler-only line shape.

For shadowed targets, direct solar excitation is exactly zero, consistent with the M4C illumination mask.

## 7. Source-function/excitation form

For an illuminated target level, each target-system excitation coefficient has the physical structure

```text
g_band(z,SZA)
    = integral dnu [ sigma_band(nu,T_target)
                     * Phi_sun(nu)
                     * exp(-tau(nu,z,SZA)) ]
```

with units `s^-1`.

The target cross section is evaluated at the local target temperature, while attenuation along the ray uses shell-local temperatures as stated above.

The exact discrete quadrature/grid used to evaluate this integral remains to be frozen by convergence tests; no legacy fixed `0.01 cm^-1` grid is accepted automatically.

## 8. Gate decision

**PARTIAL PASS / LINE-SHAPE GATE REOPENED.** The accepted M4C exact spherical-shell geometry remains the M4D geometry. Doppler-only is not accepted over the full altitude/SZA domain after the independent numerical review: selected near/post-twilight cases show material Voigt sensitivity, and A/B Voigt far-wing convergence remains unresolved at the declared numerical floor.

See `docs/m4d_final_design_review.md` for the quantitative counterexample and exact remaining blockers. No M4D implementation is authorized.
