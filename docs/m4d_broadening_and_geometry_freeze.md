# M4D broadening and solar-path geometry review

Status: **GEOMETRY RETAINED / B+IRA PROFILE CANDIDATES SELECTED / A-BAND AUXILIARY BYTES+MAPPING BLOCKER**

Branch: `milestone/m4d-design`

> The earlier Doppler-only freeze is superseded by `docs/m4d_final_design_review.md`, `docs/m4d_pressure_broadening_provenance_followup.md`, and `docs/m4d_a_band_auxiliary_source_recovery.md`. The local-width calculation remains useful evidence, but it is not a valid full-domain line-shape decision.

This note separates the retained spherical geometry from the per-band/per-isotopologue spectroscopy decision.

## 1. Doppler-only decision is superseded

The earlier design proposed normalized Gaussian Doppler profiles for all three O2 systems and treated pressure broadening as a later sensitivity. That proposal was motivated by the recovered Anqi Li A-band method and by the small Lorentz/Doppler ratio at the lowest chemistry level.

The independent full-path review showed that illuminated twilight rays to 50-100 km targets can pass through much denser atmosphere below the chemistry boundary. Therefore pressure broadening cannot be bounded by the pressure at the target altitude.

Doppler-only remains useful as a legacy-method comparison, optically thin/profile-normalization check, and converged numerical reference calculation. It is not an authorized final M4D profile.

## 2. Local-width evidence retained

At the accepted M4A 50-km chemistry level:

```text
z = 50 km
T = 264.9381103515625 K
M = 2.1204504413317356e16 cm^-3
O2 = 4.4529459267966445e15 cm^-3
O2/M = 0.210000...
p approximately 77.563 Pa = 7.6549e-4 atm
```

The earlier local diagnostic gave maximum `gamma_L/gamma_D` values of approximately:

| system | maximum local ratio at 50 km |
| --- | ---: |
| IRA `a(0)-X(0)` | `0.6088%` |
| A `b(0)-X(0)` | `0.3854%` |
| B `b(1)-X(0)` | `0.3342%` |

These values describe the local 50-km state only. They do not bound a spherical twilight path.

## 3. Full-path counterexample retained

`docs/m4d_final_design_review.md` found that, with a `+/-20 cm^-1` Voigt attenuation sensitivity, A-band differed from Doppler by approximately `0.4725%` even when restricting to rates above `1e-10 s^-1`, exceeding the declared `0.1%` adequacy criterion.

At weaker illuminated post-90-degree cases, differences reached tens of percent. The `+/-10 -> +/-20 cm^-1` isolated-Voigt attenuation comparison also failed the `0.1%` gate for weak A/B twilight rates.

Therefore:

**Doppler-only is rejected over the complete M4D altitude/SZA domain.**

## 4. Per-band / per-isotopologue line-shape status

### 4.1 A band, iso 1 / 16O2

HITRAN2016 Section 2.7.2 points to Drouin et al. (2017) and an advanced principal-isotopologue representation containing speed-dependent line shape and collisional line mixing. HITRAN transformed scaled W-matrix information to first-order Rosenkranz line-mixing parameters at standard temperatures.

The exact source family and public supplement identity are known:

```text
PMC5103325
NIHMS804415-supplement-supplement_1.pdf
reported size 94.8 kB
```

but the bytes/hash and executable Drouin-to-HITRAN/Rosenkranz mapping are not yet frozen.

Current status:

**A iso 1: advanced SDV + line mixing selected in principle / source materialization and parameter mapping still block freeze.**

### 4.2 A band, iso 2/3 / rare isotopologues

Historical evidence now identifies the rare-isotopologue profile family rather than leaving it unspecified.

HITRAN2012 and Long et al. document `16O18O` and `16O17O` A-band analyses using **Galatry profiles** with Doppler broadening, pressure broadening and Dicke narrowing. The surviving HITRAN2012 archive identifies the auxiliary files:

```text
07_A-band_SDF.dat
07_hit12_0.76mic_Galatry.par
```

HITRAN2016 documents the Drouin replacement specifically for the principal isotopologue and does not document an equivalent replacement of the rare-isotopologue Long/Galatry treatment.

The rare isotopologues contribute approximately `0.4674%` of total accepted A-band integrated strength at 296 K, above the `0.1%` project tolerance, so they cannot simply be omitted.

Current status:

**A iso 2/3: historical Long/HITRAN2012 Galatry + Dicke-narrowing baseline candidate selected / auxiliary bytes+hash, transition mapping and HITRAN2016 continuity check pending.**

See `docs/m4d_a_band_auxiliary_source_recovery.md`.

### 4.3 B band

The advanced B-band qSDV history is partial, principally self-broadened, and affected by a later-documented FWHM/HWHM interpretation defect in the HITRAN2016-era advanced values.

The selected `historical_2020` baseline candidate is therefore the complete classic HITRAN2016 isolated Voigt representation carried by the accepted 160-character B records.

For each line:

```text
gamma_L(p,T)
  = (296/T)^n_air
    * [gamma_air * (p - p_O2) + gamma_self * p_O2]
```

with pressures in atm and HITRAN HWHM coefficients in `cm^-1 atm^-1`.

The classic shifted center is

```text
nu_shifted = nu0 + delta_air * p.
```

`gamma_air` is already the HITRAN air-broadening coefficient. Do not multiply it by an additional `0.79` or reconstruct it from N2/O2 fractions. The standard partial-pressure expression above already combines the air and absorber-self terms.

A source-corrected qSDV calculation on the historical lines for which it is available is retained as a mandatory sensitivity. If it changes any accepted B-band M4D rate by more than `0.1%`, the classic-Voigt candidate must be reopened before design freeze.

Current status:

**B classic Voigt: BASELINE CANDIDATE SELECTED / NUMERICAL VALIDATION PENDING.**

### 4.4 IRA / 1.27 micron

HITRAN2016 discrete 1.27-micron monomer lines are historically close to the HITRAN2012 compilation apart from important line-position updates; the earlier discrete parameters were based on Voigt analyses. Later spectroscopy demonstrates beyond-Voigt effects for high-accuracy terrestrial retrievals, but does not establish a complete historical HITRAN2016 advanced monomer parameterization analogous to the A band.

The selected monomer baseline candidate is therefore the complete classic HITRAN2016 isolated Voigt representation in the accepted IRA records, with the same Lorentz-width and pressure-shift equations used for B.

Current status:

**IRA classic Voigt: BASELINE CANDIDATE SELECTED / NUMERICAL VALIDATION PENDING.**

CIA remains outside the monomer baseline and is a required M4D closure sensitivity, documented in `docs/m4d_ira_cia_historical_source_recovery.md`.

## 5. Pressure shifts and narrowing

For classic B/IRA profiles the candidate rule is:

```text
nu_shifted = nu0 + delta_air * p
```

with shell-local total pressure and no invented temperature dependence of the classic `delta_air` field.

For A iso 1, the recovered advanced historical representation must supply the applicable shift convention. For A iso 2/3, the historical Galatry/Dicke auxiliary representation must be followed rather than inventing principal-isotopologue SDV parameters.

A full-path pressure-shift sensitivity remains required before freeze because twilight rays sample much denser shells than the chemistry target.

## 6. Solar geometry remains accepted

M4D retains the accepted M4C direct-beam spherical geometry semantics:

- Earth radius `6370 km`;
- radiative top `150 km`;
- chemistry targets `50..100 km`;
- exact spherical ray/shell intersections;
- exact solid-Earth shadowing for `SZA > 90 deg`;
- tangent-ray illumination at the solid-Earth boundary within numerical tolerance.

M4D must not introduce a plane-parallel approximation or a second Earth radius. The accepted M4C-R2 production implementation remains untouched.

## 7. M4D atmospheric/path discretization refinement

The M4C geometry equations and shadow semantics are reused, but NIR optical-depth integration needs finer atmospheric sub-stratification than the accepted M4C one-kilometre UV calculation.

The design-forensics rule remains:

- piecewise-linear interpolation from the accepted one-kilometre atmospheric nodes;
- exact spherical intersections on `0.125 km` sub-shells for M4D;
- `0.0625 km` as convergence reference.

The previous review found maximum `0.125 -> 0.0625 km` differences below approximately `0.034%` across A/B/IRA in the tested domain.

This is an M4D integration refinement only; it does not change M4C-R2 behavior.

## 8. Shellwise optical depth remains mandatory

The required structure is

```text
tau(nu,z,SZA)
  = sum_shell sigma_band(nu,T_shell,p_shell,...)
              * n_O2,shell * dl_shell.
```

A target-temperature cross section multiplied by total O2 slant column is rejected.

For shadowed targets the direct beam is exactly zero from the physical Earth-shadow mask.

## 9. Excitation form and profile consistency

For an illuminated target:

```text
g_band(z,SZA)
  = integral sigma_band(nu,T_target,p_target,...)
             * Phi_sun(nu)
             * exp[-tau(nu,z,SZA)] dnu.
```

Within each isotopologue/profile family, the same selected physical profile semantics must be used for target excitation and shell attenuation. The earlier mixed Doppler-source/Voigt-attenuation calculation was a diagnostic only.

## 10. Far-wing/convergence direction

No fixed physical `+/-N cm^-1` wing cutoff is frozen.

For classic B/IRA candidates, the preferred numerical route is:

1. deterministic line-centred target/source quadrature;
2. evaluate attenuation at each target quadrature node from all accepted absorber lines in that band;
3. converge target support/order independently against a stricter reference;
4. validate all 51 target altitudes and the final SZA set.

For A iso 1, support/convergence must be defined from the recovered SDV + line-mixing representation. For A iso 2/3, it must be appropriate to the recovered Galatry representation.

## 11. Gate decision

**PARTIAL PASS / M4D DESIGN NOT FROZEN.**

Retained/resolved:

- M4C spherical geometry semantics;
- shell-local transfer;
- `0.125 km` M4D sub-stratification with `0.0625 km` convergence reference;
- rejection of Doppler-only;
- A iso-1 historical advanced profile family identified;
- A iso-2/3 historical Galatry/Dicke profile family identified;
- B classic HITRAN2016 Voigt baseline candidate;
- IRA classic HITRAN2016 Voigt monomer baseline candidate;
- standard classic B/IRA broadening/shift equations.

Still blocking:

- A iso-1 supplement byte identity and executable Drouin/HITRAN2016 parameter mapping;
- A iso-2/3 auxiliary file bytes/hash, mapping and HITRAN2016 continuity verification;
- final target+attenuation convergence for all selected profiles;
- pressure-shift sensitivity;
- corrected qSDV B sensitivity;
- historical IRA CIA byte materialization and twilight sensitivity.

No M4D implementation is authorized.
