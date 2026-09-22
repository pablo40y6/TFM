# Project state

## Purpose

This repository develops a reproducible time-dependent mesospheric ozone and O2(a1Delta) photochemical model. The accepted implementation currently ends at the SZA-resolved direct-beam UV/VUV radiation baseline, M4C-R2.

## Accepted architecture

- Dynamic state at each chemistry level: O, O3, H, `R_H = OH + HO2`, and Delta = O2(a1Delta_g).
- Chemistry grid: 50-100 km at 1 km spacing, 51 levels.
- Future full system: 255 ODEs.
- Algebraic/QSSA species: O(1D), OH, HO2, H2O2, B0 = O2(b1Sigma_g+, v=0), and B1 = O2(b1Sigma_g+, v=1).
- Prescribed fields: T, M, O2, N2, CO2, H2O, and H2.
- First temporal version: no vertical transport; BDF main solver; Radau independent verification; repeated diurnal cycles to periodic convergence.
- Delta remains dynamic: `dDelta/dt = P_Delta - L_Delta*Delta`.

These statements describe the accepted architecture and provisional continuation. They do not mean M4D or the later temporal solver has been implemented.

## Accepted milestone ledger

| Milestone | Status | Artifact | SHA-256 | Package version |
| --- | --- | --- | --- | --- |
| M1-R2 | CLOSED / ACCEPTED | `tfm-photochem-milestone1-r2.zip` | `46c88ec344de1569d06dff76c36c991edb19777497146ff5183756b54cba6f3d` | 0.1.0 |
| M2-R2 | CLOSED / ACCEPTED | `tfm-photochem-milestone2-r2.zip` | `ffb179c9f2c7fdb71ad5af8990490ae0040cf729f7209e1ae90a25fa0021f47f` | 0.2.0 |
| M3 | CLOSED / ACCEPTED | `tfm-photochem-milestone3.zip` | `d5dac9f3d160b0d53a1fdc16b23b4c72b918c271466dfbe58d99c5a54a9d89ef` | 0.3.0 |
| M4A | CLOSED / ACCEPTED | `tfm-photochem-milestone4a.zip` | `d1a68e6344710cd8ae6543f12081cde55355f23849ea73b9724d9e49156fbc12` | 0.4.0 |
| M4B-R2 | CLOSED / ACCEPTED | `tfm-photochem-milestone4b-r2.zip` | `87fe1d585efa6f42231fc6d9898ca37c5afa51d1b4baa6325015caaee03530c8` | 0.4.2 |
| M4C-R2 | CLOSED / ACCEPTED; current implemented baseline | `tfm-photochem-milestone4c-r2.zip` | `2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe` | 0.5.1 |

The immutable current artifact is `artifacts/accepted/m4c-r2/tfm-photochem-milestone4c-r2.zip`. Accepted M4C behavior is not modified by M4D design work.

## Current next milestone

M4D is **NOT IMPLEMENTED / DESIGN NOT FROZEN**. It must provide `gA`, `gB`, and `gIRA` without starting M5.

The historical A-band and Maté CIA source-discovery/byte-materialization blockers have now been closed through reproducible public-source acquisition. The remaining gates are local HITRAN2016 rare-line continuity and numerical closure/sensitivity for the selected A/B/IRA treatments.

## Frozen source / transition gates

### Accepted HITRAN2016 target-line export

The manually acquired SpectralCalc O2 export remains the transition/intensity source:

```text
raw export SHA-256: 6b4acbc01cb649891f2d8597875c9cd8e4805cfdd4d3b7841c2d18cbf718de12
records:               14085
```

Frozen target subsets:

```text
gA    b(0)-X(0): 430 lines
gB    b(1)-X(0): 320 lines
gIRA  a(0)-X(0): 835 lines
```

The raw export is intentionally not committed. Classic 160-character records freeze transition/intensity provenance but do not contain all advanced A-band relation parameters.

### TIPS-2017

**PASS.** Historical numerical source:

```text
hitranonline/hapi@f41d9911f2631eed51b96d6c617b4f27786ad477
hapi/hapi.py
Git blob caeab1bfaa278b5420adef7efe7ab566991ba763
HAPI 1.1.0.8.2
```

### Solar source

**PASS.** Wehrli (1985) WMO/WRC extraterrestrial irradiance with the frozen interpolation/Jacobian convention.

## M4D geometry / transfer gates

- **Doppler-only: REJECTED FOR FULL DOMAIN.** Illuminated twilight rays can sample dense atmosphere well below the 50-km chemistry target.
- **Geometry: PASS.** Retain the accepted M4C spherical geometry, Earth radius `6370 km`, radiative top `150 km`, physical Earth shadow and tangent semantics.
- **Path sub-stratification: SELECTED.** M4D NIR transfer uses `0.125 km`, checked against `0.0625 km`.
- **Shellwise spectroscopy: REQUIRED.** Target-temperature cross section times total column is rejected.
- **No arbitrary Voigt attenuation wing:** for classic B/IRA candidates, evaluate all accepted absorber lines at each target quadrature node and converge target support/order separately.

## Corrected HITRAN air-diluent semantics

A previous candidate expression mixed an already air-defined coefficient with an extra O2 self fraction. That is superseded.

For the terrestrial atmospheric baseline an HITRAN `air` coefficient is a **diluent coefficient** applied to shell atmospheric pressure:

```text
gamma_L = gamma_air * p * (296/T)^n_air
nu_shifted = nu0 + delta_air * p
```

Do not apply `gamma_air*(p-p_O2)+gamma_self*p_O2` when `gamma_air` is already the HITRAN air-diluent coefficient. `self` is a separate diluent choice for explicitly self/O2-rich conditions.

For the O2 A band this interpretation is independently reinforced by HITRAN2016: Drouin foreign parameters were converted to air using the N2:O2 `0.79:0.21` mixture before the HITRAN-facing representation was produced.

## A-band principal isotopologue

### Source materialization: PASS

Official Drouin publisher supplement:

```text
https://ars.els-cdn.com/content/image/1-s2.0-S0022407316301108-mmc1.pdf
bytes:   89406
SHA-256: 12e621d3b5d17e7648d140ea16134e3c04096bd7e47e2c1bb0e2084adeccbb51
pages:   12
```

Structured PMC manuscript:

```text
PMC5103325 XML via NCBI E-utilities
bytes:   310708
SHA-256: 935fd09d5f619f7eb3f7fac5347e80fa81bc23d3158dc9c519874bb161c364fe
```

### Transition classification / mapping: PASS

The principal-isotopologue target set contains:

```text
91 magnetic-dipole d lines
59 electric-quadrupole q lines
```

Drouin Tables 4/5 contain exactly `91` magnetic-dipole rows and map `91/91`, with zero unmatched/ambiguous labels, to the historical d-line set. The accepted HITRAN2016 SpectralCalc A subset was independently checked by fixed-record quantum identity: it contains exactly `91` principal-isotopologue `d` lines and the label set matches Drouin `91/91`, with zero missing, extra, or duplicate labels.

Drouin supplement Table 22 supplies first-order air Rosenkranz `Y` values at `200, 250, 296, 340 K` for `70/91` d lines. The remaining 21 high-J d lines are explicitly identified and account for about `0.0131464%` of historical iso-1 integrated A strength. The 59 q lines account for about `0.00079353%`.

### Selected candidate profile split

```text
91 d lines:
    Drouin/HITRAN2016 SDV

70/91 d lines:
    + first-order Rosenkranz line mixing Y(T)

21/91 d lines without Table-22 Y:
    SDV retained; no LM coefficient invented
    final Y=0/source interpretation + numerical sensitivity OPEN

59 q lines:
    accepted target-edition classic profile candidate
    no Drouin advanced parameters copied onto them
```

### Still open

- Drouin isolated-line SDV evaluator is now frozen: `Gam2 = S*Gam0`, `Shift2 = 0`, `anuVC = 0`, `eta = 0`, with shell-local Drouin Eqs. 6-7 for width/shift;
- Table-22 temperature policy is now selected: exact source nodes at 200/250/296/340 K, piecewise-linear interpolation within 200..340 K, nominal 200-K clamp below range with mandatory linear-extrapolation/Y=0 sensitivity;
- 21 no-Y d-line sensitivity;
- 59 q-line sensitivity;
- accepted-HITRAN2016 principal `91/91` continuity: **PASS**;
- final A spectral/path convergence.

See `docs/m4d_a_band_drouin_materialization_audit.md`, `docs/m4d_a_band_sdv_semantics_freeze.md`, and `docs/m4d_a_band_table22_temperature_policy.md`.

## A-band rare isotopologues

### Historical source bytes: PASS

```text
07_A-band_SDF.dat
bytes 6229
SHA-256 7cfefb8040a89cb0e4948c2811a6766b793181646d8188ebfa4d646e063dbd26

07_hit12_0.76mic_Galatry.par
bytes 47231
SHA-256 69c9fd181b5aba8aa818dc906bdc216aaa8cf038eb5687dd4da8f2bb9bf42dab

07_hit12.par audit witness
bytes 2263950
SHA-256 ad2cadf91cb985bec4074ce0bf47cdcfa7aab627ea15de2ac85de731873417a4
```

### Historical mapping: PASS

`07_hit12_0.76mic_Galatry.par` contains `489` records, with target A-band composition `150 + 140 + 140 = 430`. The mapping to historical `07_hit12.par` is `430/430`, zero unmatched and zero ambiguous. All `280` rare target lines have historical air/self Dicke coefficients.

The rare isotopologues contribute about `0.4674%` of accepted A integrated strength and cannot simply be dropped against the `0.1%` gate.

### Frozen precedence

```text
ordinary line fields:
    accepted target-edition HITRAN record

Dicke/Galatry narrowing fields:
    quantum-identity-matched historical auxiliary record
```

Do not overwrite target-edition broadening/shift fields with redundant auxiliary copies.

### Still open

- local accepted-HITRAN2016 `280/280`, zero-ambiguity continuity mapping;
- Galatry target+attenuation numerical convergence.

See `docs/m4d_a_band_auxiliary_mapping_audit.md`.

## B band

**BASELINE CANDIDATE SELECTED.** Use classic HITRAN2016 Voigt with atmospheric `air` coefficients under the corrected diluent semantics above.

The known partial/defective historical qSDV data are not silently reproduced. A source-corrected qSDV sensitivity on covered principal-isotopologue lines is required; if any scientifically retained B rate changes by more than `0.1%`, reopen the baseline candidate.

## IRA monomer

**BASELINE CANDIDATE SELECTED.** Use classic HITRAN2016 Voigt with atmospheric `air` coefficients under the corrected diluent semantics above, pending final full-domain convergence.

## IRA CIA Option B

The historical monomer baseline excludes CIA as a production process and baseline opacity, but M4D closure requires a twilight attenuation sensitivity.

HITRAN2016 identifies Maté et al. (1999), DOI `10.1029/1999JD900824`, as the revised 1.27-micron CIA source and explicitly corrects the 2012 pair-label error. The three historical Maté air-mixture numerical blocks have therefore been recovered byte-for-byte from the surviving HITRAN2012 `O2-O2_2011.cia` witness and are interpreted as `O2-Air` under the HITRAN2016 correction. Do not separately add O2-O2 for the same mixture.

Historical witness:

```text
O2-O2_2011.cia
bytes 1938473
SHA-256 8cc3ecc87bf7a02492b385ecc71abf279b058da853aea768825deb81237d5ee3

Maté blocks:
253 K  block SHA-256 58366c46162ca55c84aecd8b81bdadc1f5a68a27db0fbbd615a401dcc21f0bfc
273 K  block SHA-256 09a1e93c23004c0b12acf3e9b97fcb44f4bd32872e7ad1c6441225f0ab56b545
296 K  block SHA-256 19bd3c333c56dc9dd90019b57d014a69db420cae139a33a1c470557b1ad78e08
```

Frozen cold-shell sensitivity policy:

```text
253..296 K: linear interpolation among measured Maté spectra
T < 253 K:  nominal clamp to 253-K endpoint
T > 296 K: nominal clamp to 296-K endpoint
outside source range: also propagate min/max envelope of the three measured spectra
```

Do not silently substitute the post-2016 theoretical temperature extension.

**Source materialization: PASS.** Still open: deterministic common-grid/support handling, the negative experimental-sample sensitivity, and the resulting full twilight CIA sensitivity. See `docs/m4d_ira_cia_materialization_audit.md`.

## Numerical closure gate

For final selected profiles, validate all 51 target altitudes for at least:

```text
SZA = 0, 60, 85, 89, 89.9, 95, 99 deg
```

plus an illuminated tangent and immediately-shadowed boundary case.

Current gate:

```text
max relative difference <= 0.1%
```

for rates above `1e-15 s^-1`. Below that floor report absolute differences and require finite/nonnegative results.

Required sensitivities/refinements include:

- spectral support/order;
- `0.125 -> 0.0625 km` path refinement;
- pressure shifts on/off;
- A LM/no-LM high-J treatment;
- A q-line contribution;
- B corrected qSDV;
- IRA historical CIA nominal/envelope.

No empirical normalization is allowed.

## Unattenuated regression anchors

| T (K) | `gA0` (s^-1) | `gB0` (s^-1) | `gIRA0` (s^-1) |
| ---: | ---: | ---: | ---: |
| 180 | `6.1914394520e-9` | `3.5752856768e-10` | `1.4549983481e-10` |
| 200 | `6.1963256585e-9` | `3.5805572358e-10` | `1.4573674701e-10` |
| 220 | `6.1999597393e-9` | `3.5852735538e-10` | `1.4593873602e-10` |
| 240 | `6.2025842093e-9` | `3.5895153697e-10` | `1.4611114500e-10` |
| 260 | `6.2043175651e-9` | `3.5933010076e-10` | `1.4625641629e-10` |
| 280 | `6.2051968875e-9` | `3.5966103384e-10` | `1.4637502395e-10` |
| 296 | `6.2052846913e-9` | `3.5988913888e-10` | `1.4645036484e-10` |

These are regression anchors, not forced final answers.

## Primary M4D design documents

- `docs/m4d_spectralcalc_export_forensics.md`
- `docs/m4d_tips2017_provenance_recovery.md`
- `docs/m4d_solar_forcing_freeze.md`
- `docs/m4d_broadening_and_geometry_freeze.md`
- `docs/m4d_numerical_specification.md`
- `docs/m4d_pressure_broadening_provenance_followup.md`
- `docs/m4d_a_band_auxiliary_source_recovery.md`
- `docs/m4d_a_band_auxiliary_mapping_audit.md`
- `docs/m4d_a_band_drouin_materialization_audit.md`
- `docs/m4d_a_band_sdv_semantics_freeze.md`
- `docs/m4d_a_band_table22_temperature_policy.md`
- `docs/m4d_ira_cia_scope_freeze.md`
- `docs/m4d_ira_cia_historical_source_recovery.md`
- `docs/m4d_source_materialization_gate.md`
- `docs/m4d_final_design_review.md`

Earlier forensics/research notes remain provenance evidence even where their old candidate conclusions are superseded.

## Immediate next gate

1. Execute the A iso-1 Table-22 low-temperature envelope numerically; SDV and operational Y(T) semantics are selected.
2. Complete the remaining accepted-HITRAN2016 continuity map: `280/280` rare Galatry (`91/91` Drouin d is now PASS).
3. Close the CIA common-grid/negative-sample sensitivity using the frozen Maté blocks.
4. Execute consistent A/B/IRA target+attenuation calculations and declared sensitivities.
5. Pass the full altitude/SZA/tangent convergence gate.

Only then may `docs/m4d_final_design_specification.md` be created and production implementation authorized.

## Known bootstrap reproducibility finding

During repository bootstrap, optional M4A background regeneration with `pymsis==0.12.0` on Windows/Python 3.14 was not byte-identical to the accepted frozen M4A assets. The accepted assets and validators were not modified, so M4A remains CLOSED / ACCEPTED. Do not replace accepted backgrounds solely from that cross-environment result.

## Documented source-identity discrepancy

`references/scientific/JPL_Publication_15-10_compressed.pdf` has SHA-256 `a5c57b2a8435760bc4dd43da328a9dd34768865c022e965326f3eccaaf0cd3c8`. Other accepted documentation records different byte identities for other JPL Evaluation-18 source copies. Bibliographic equivalence is not treated as byte identity.

## Provisional roadmap after M4D

1. M5A: performance-ready 51-level chemistry kernel.
2. M5B: 255-state RHS with BDF/Radau integration.
3. M6: diurnal cycle and periodic convergence.
4. M7: scientific validation and sensitivities not already required for M4D closure.
5. M8: Odin/retrieval/application work, if still in scope.

Before any M5 optimization, preserve the M3 scalar closure as the golden scientific reference.
