# Project state

## Purpose

This repository develops a reproducible time-dependent mesospheric ozone and O2(a1Delta) photochemical model. The accepted implementation currently ends at the SZA-resolved direct-beam UV/VUV radiation baseline, M4C-R2.

## Accepted M3/M4 reference architecture

- Dynamic state at each chemistry level: O, O3, H, `R_H = OH + HO2`, and Delta = O2(a1Delta_g).
- Chemistry grid: 50-100 km at 1 km spacing, 51 levels.
- Golden M3/M4 basis: 255 dynamic coordinates across 51 levels.
- Algebraic/QSSA species: O(1D), OH, HO2, H2O2, B0 = O2(b1Sigma_g+, v=0), and B1 = O2(b1Sigma_g+, v=1).
- Prescribed fields: T, M, O2, N2, CO2, H2O, and H2.
- First temporal version: no vertical transport; BDF main solver; Radau independent verification; finite-horizon reference noon-to-dawn simulation. Periodic spin-up is a closed historical diagnostic.
- Delta remains dynamic: `dDelta/dt = P_Delta - L_Delta*Delta`.

M5 alone uses O/O3/H/OH/HO2/H2O2/Delta (357 ODEs), with R_H=OH+HO2
as an exact diagnostic. Only O1D/B0/B1 remain algebraic. Accepted M3/M4
and original close_local_chemistry are unchanged; only timescale assumptions
for OH/HO2/H2O2 have been relaxed.

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

M4D is **PROVISIONALLY CLOSED / INTEGRATION READY / NOT FROZEN** under the authorized pragmatic closure in `docs/m4d_closure_report.md`: A0 430 Voigt, B 320 Voigt, IRA 835 monomer Voigt plus historical O2-Air CIA attenuation; A1 is sensitivity only. Historical Y/Galatry/high-T/B-qSDV gates do not block integration; PR #4 is not merged.

M5A is **GO / VALIDATED FINITE-HORIZON REFERENCE DAWN** on milestone/m5-temporal.
The 357-ODE baseline is unchanged; O1D/B0/B1 remain QSSA. Reference noon uses
frozen M4A O3/native O/H, declared missing-atom zeros at 50..72 km, and a
multistart stationary OH/HO2/H2O2/Delta subsystem only at t0. All six trajectories
complete the 21-hour noon -> next-dawn -> SZA60 interval without resets/clipping.
BDF base/tight differ by 0.045420%; tighter BDF/Radau by 0.001248%.
O3/Delta initialization sensitivities are quantified and material; they are a
climatological-initialization limitation, not a chemistry-change gate. Periodic
spin-up is closed as a historical diagnostic and no longer required. Full
reference time-height fields and dawn tables are saved. Pytest **870 + 13
subtests**, ruff and five historical validators pass. M3/M4/main and M4C-R2 SHA
are unchanged; M4D remains NOT FROZEN. Next scope: real solar geometry with
explicit initial_state support; atmospheric dynamics remain outside this change.
See the single temporal report and existing evidence JSON.

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
- **Monomer path sub-stratification: SELECTED.** M4D NIR monomer transfer uses `0.125 km`, checked against `0.0625 km`.
- **CIA path sub-stratification: SELECTED.** Historical O2-Air CIA uses `0.0625 km`, checked against `0.03125 km`; `0.125 -> 0.0625 km` narrowly fails the 0.1% CIA attenuation-factor gate in near-ground SZA=99 deg tangents.
- **Shellwise spectroscopy: REQUIRED.** Target-temperature cross section times total column is rejected.
- **No arbitrary Voigt attenuation wing:** for classic B/IRA candidates, evaluate all accepted absorber lines at each target quadrature node and converge target support/order separately.

## Classic B/IRA pressure-width convention for the isolated experiment

For the 2026-09-30 isolated experiment, the user's explicit requested formula supersedes this branch's earlier air-only candidate:

The experiment uses shell-local total and O2 partial pressures:

```text
gamma_L = (296/T)^n_air * [gamma_air*(p-p_O2) + gamma_self*p_O2]
nu_shifted = nu0 + delta_air * p
```

Pressures are in atm. Do not multiply the air term by an additional 0.79. The earlier `gamma_air*p*(296/T)^n_air` candidate remains available as the explicitly named `branch_air_only` comparison; it is not the default in this experiment. Earlier design documents retain the previous candidate as provenance, not current execution instructions. The requested partial-pressure expression also appears in HITRAN's primary definitions: https://hitran.org/docs/definitions-and-units/.

Native Drouin A parameters retain their separately sourced foreign/self mixture. HITRAN2016 converted the Drouin foreign fields to air before creating its HITRAN-facing representation; the implementation does not confuse those native foreign fields with the main-record air coefficient.

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
- exact physical normalization of Table-22 Y against F/F-prime; the earlier
  `p*Y*Im(F)` algebra is blocked for nominal rate transfer pending historical proof;
- supported treatment or approved materiality bound for active shells above 340 K;
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

Local accepted-HITRAN2016 continuity is **PASS**: `280/280` rare lines with zero ambiguities, reproducible through `scripts/validate_m4d_mapping.py` and `evidence/m4d_mapping.json`.

### Still open

- exact historical Galatry beta/profile conversion and temperature law;
- Galatry target+attenuation numerical convergence.

See `docs/m4d_a_band_auxiliary_mapping_audit.md`.

## B band

**ISOLATED BASELINE CANDIDATE IMPLEMENTED.** Use classic HITRAN2016 Voigt with the explicitly requested partial-pressure expression above. Full-domain acceptance remains open.

The known partial/defective historical qSDV data are not silently reproduced. A source-corrected qSDV sensitivity on covered principal-isotopologue lines is required; if any scientifically retained B rate changes by more than `0.1%`, reopen the baseline candidate.

## IRA monomer

**ISOLATED MONOMER CANDIDATE IMPLEMENTED.** Use classic HITRAN2016 Voigt with the explicitly requested partial-pressure expression above. For the selected M4D IRA radiative-transfer baseline, this monomer opacity is combined with the resolved historical O2-Air CIA attenuation; full-domain convergence remains open.

## IRA CIA attenuation scope

The historical monomer source term remains the first-order 835-line a(0)-X(0) excitation. CIA is a separate binary-density opacity and never becomes a production source.

The historical Mate numerical source is materialized and the HITRAN2016 O2-Air semantic correction is frozen. A full-domain geometry diagnostic now shows that CIA is **not uniformly negligible** over the required twilight domain. At 0.0625-km CIA sub-stratification, a line-strength-weighted diagnostic gives about 0.382% reduction at 50 km / SZA 95 deg and about 2.05% at 100 km / SZA 99 deg, with much larger effects for near-ground SZA 99 deg tangents. The measured-temperature source envelope does not change that materiality conclusion.

A profile-independent lower-bound test also finds four illuminated SZA 99 deg cases (80--83 km) where the minimum CIA attenuation across the entire accepted IRA spectral support already exceeds 0.1%.

The previous **monomer-only attenuation baseline candidate failed the retained-rate gate**. At 50 km / SZA 95 degrees the refined monomer-only rate is `6.7194715555556325e-12 s^-1`, and the historical CIA rate is `6.699880907505247e-12 s^-1`. Both exceed the floor. Counterexample refinement maxima are 0.03885055038% spatial, 0.000214008794% quadrature order and 0.007189447952% target support, all below 0.1%.

The mandatory stop was then independently reviewed. The resolved M4D baseline keeps the 835-line monomer system as the **only excitation source** but includes historical MatÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©/HITRAN2016 O2-Air CIA as a separate opacity in IRA direct-beam attenuation. Do not add a separate O2-O2 term on top of O2-Air. The nominal historical temperature clamp/interpolation, measured-source envelope and raw/noise sensitivity remain required. This resolves the CIA scope decision without freezing M4D or changing M4C-R2. See `docs/m4d_ira_cia_post_stop_resolution.md`.

Numerical CIA rules now selected:

~~~text
historical source: Mate 253/273/296-K O2-Air blocks
temperature: source-node interpolation + frozen endpoint/envelope policy
physical opacity: nonnegative
CIA sub-stratification: 0.0625 km
CIA convergence reference: 0.03125 km
~~~

The 0.0625 -> 0.03125 comparison passes with maximum relative differences of about 0.0388% in the diagnostic attenuation factor and 0.0416% in the maximum line-centre optical depth.

See docs/m4d_ira_cia_materialization_audit.md and docs/m4d_ira_cia_numerical_diagnostic.md.

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
- monomer `0.125 -> 0.0625 km` path refinement;
- CIA `0.0625 -> 0.03125 km` path refinement;
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

1. CIA post-stop review is complete: include historical MatÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©/HITRAN2016 O2-Air CIA in the IRA attenuation baseline; keep excitation monomer-only and retain nominal/envelope/raw CIA sensitivities.
2. Resolve the documented A LM normalization, high-temperature and historical
   Galatry convention blockers before completing nominal SDV+LM/Galatry transfer
   and its low-temperature/no-Y/quadrupole retained-rate sensitivities.
3. Materialize and test corrected source-based B qSDV and quantify pressure-shift sensitivity.
4. Pass the full altitude/SZA/tangent spectral and spatial rate gate, including the selected IRA CIA baseline and its source-envelope sensitivity. Geometry coverage alone is not rate convergence.

Only then may independent audit accept a final M4D design/freeze. The current isolated implementation experiment is explicitly authorized by the user's request; it is not production acceptance.

## Known bootstrap reproducibility finding

During repository bootstrap, optional M4A background regeneration with `pymsis==0.12.0` on Windows/Python 3.14 was not byte-identical to the accepted frozen M4A assets. The accepted assets and validators were not modified, so M4A remains CLOSED / ACCEPTED. Do not replace accepted backgrounds solely from that cross-environment result.

## Documented source-identity discrepancy

`references/scientific/JPL_Publication_15-10_compressed.pdf` has SHA-256 `a5c57b2a8435760bc4dd43da328a9dd34768865c022e965326f3eccaaf0cd3c8`. Other accepted documentation records different byte identities for other JPL Evaluation-18 source copies. Bibliographic equivalence is not treated as byte identity.

## Provisional roadmap after M4D

1. M5A: performance-ready 51-level chemistry kernel.
2. M5B: 357-state RHS with BDF/Radau integration.
3. M6: diurnal cycle and periodic convergence.
4. M7: scientific validation and sensitivities not already required for M4D closure.
5. M8: Odin/retrieval/application work, if still in scope.

Before any M5 optimization, preserve the M3 scalar closure as the golden scientific reference.
