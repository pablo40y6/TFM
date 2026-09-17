# M4D pressure-broadening and line-shape provenance follow-up

Status: **A-BAND BYTE/MAPPING BLOCKER / B+IRA BASELINE CANDIDATES SELECTED / DESIGN NOT FROZEN**

Branch: `milestone/m4d-design`

This note follows `docs/m4d_final_design_review.md`. It does not implement M4D, change the accepted M4C-R2 baseline, or authorize M5. It narrows the remaining pressure-broadening / line-shape gate using the historical HITRAN2016-era evidence. Detailed A auxiliary provenance is in `docs/m4d_a_band_auxiliary_source_recovery.md`; detailed IRA CIA provenance is in `docs/m4d_ira_cia_historical_source_recovery.md`.

## 1. Accepted starting point

The previous numerical review remains accepted:

- Doppler-only is not adequate over the full required altitude/SZA domain because illuminated twilight rays can traverse substantially denser atmosphere below the 50 km chemistry boundary.
- The accepted M4C spherical geometry remains valid.
- Shell-local temperature scaling is mandatory.
- Deterministic atmospheric/path sub-stratification at `0.125 km`, checked against `0.0625 km`, is the current converged M4D path rule.
- The mixed Doppler-target/Voigt-attenuation experiment was sufficient to reject Doppler-only, but it was not a final pressure-broadened calculation.
- Plain Voigt attenuation windows `+/-10 -> +/-20 cm^-1` did not close the declared `0.1%` gate for weak A/B twilight rates.

## 2. A band principal isotopologue: historical representation identified

Gordon et al. (2017), HITRAN2016 Section 2.7.2, identifies Drouin et al. (2017), DOI `10.1016/j.jqsrt.2016.03.037`, as the update source for principal-isotopologue A-band magnetic-dipole transitions.

The intended representation is not plain isolated Voigt. HITRAN2016/Drouin establish:

- speed-dependent Voigt broadening;
- collisional line mixing;
- a full W-matrix treatment in the native Drouin model;
- conversion of foreign-broadening quantities to air with the atmospheric N2/O2 mixture;
- HITRAN-facing first-order Rosenkranz line-mixing parameters derived from scaled W matrices at standard temperatures;
- pressure-shift and temperature-dependent line-shape information;
- CIA represented separately rather than as an arbitrary resonant far wing.

The public Drouin manuscript is `PMC5103325`; its exact identified supplement is:

```text
NIHMS804415-supplement-supplement_1.pdf
reported size: 94.8 kB
```

The source states that the supplement contains modified line-mixing matrices and temperature-dependent `Y` values, with retained `PP`/`RR` `18 x 18` and `PQ`/`RQ` `17 x 17` submatrices.

Therefore the source family is known. The principal-isotopologue blocker is now **byte materialization + exact executable Drouin-to-HITRAN/Rosenkranz mapping**, not source discovery.

## 3. A band rare isotopologues: historical Galatry lineage recovered

The rare A-band isotopologues are no longer an unspecified-profile problem.

HITRAN2012 Section 2.7.3 and Long et al. (2011), DOI `10.1016/j.jqsrt.2011.07.002`, document A-band fits for `16O2`, `16O18O`, and `16O17O` with **Galatry profiles**, including Doppler broadening, pressure broadening and Dicke narrowing. The auxiliary files carry the required collisional-narrowing information.

The surviving Harvard/CfA HITRAN2012 archive identifies:

```text
07_A-band_SDF.dat
last modified 20-May-2013 10:51
index size 6.1K

07_hit12_0.76mic_Galatry.par
last modified 20-May-2013 10:51
index size 46K
```

HITRAN2016 describes its Drouin replacement specifically for the principal isotopologue; no equivalent replacement of the rare-isotopologue Long/Galatry source is documented in the accepted evidence.

The accepted A-band 296-K summed strengths are:

```text
iso 1 = 2.24412333089e-22
iso 2 = 8.7675965e-25
iso 3 = 1.77109027e-25
total = 2.25466201766e-22
```

so iso-2 + iso-3 contribute approximately `0.4674176%` of total A integrated strength. This exceeds the project `0.1%` design tolerance and rules out simply omitting the rare isotopologues.

**A rare-isotopologue baseline candidate: historical Long/HITRAN2012 Galatry + Dicke-narrowing parameters, pending exact auxiliary-file bytes/hash, line mapping, and a continuity check that HITRAN2016 did not supersede those relations.**

## 4. B band: classic HITRAN2016 Voigt selected as baseline candidate

The B-band advanced qSDV history is partial, principally self-broadened, and version-sensitive; HITRAN2020 later documents a FWHM/HWHM interpretation defect in the HITRAN2016-era advanced values.

The `historical_2020` baseline candidate is therefore the complete classic isolated Voigt representation carried by the accepted HITRAN2016 160-character B records.

For every B line:

```text
gamma_L(p,T)
  = (296/T)^n_air
    * [gamma_air * (p - p_O2) + gamma_self * p_O2]

nu_shifted = nu0 + delta_air * p
```

with pressures in atm and Lorentz HWHM coefficients in `cm^-1 atm^-1`.

`gamma_air` is already the HITRAN air-broadening coefficient. Do not convert it again with another `0.79/0.21` mixture.

A source-corrected qSDV sensitivity on the historically covered principal-isotopologue lines is mandatory. If it changes any accepted B-band M4D rate by more than `0.1%`, reopen the classic-Voigt candidate before freeze.

## 5. IRA / 1.27 micron: classic HITRAN2016 Voigt selected as monomer baseline candidate

The HITRAN2016 discrete 1.27-micron monomer parameters remain historically close to HITRAN2012 apart from important position updates, and the earlier discrete-line analysis used Voigt profiles. Later beyond-Voigt studies are valuable sensitivity evidence but are not a complete historical HITRAN2016 replacement.

The selected monomer baseline candidate is therefore classic isolated Voigt using the accepted HITRAN2016 `gamma_air`, `gamma_self`, `n_air`, and `delta_air` fields with the same standard width/shift equations used for B.

This remains conditional on the final consistent target+attenuation convergence run.

## 6. Pressure shifts

For classic B/IRA profiles, use the historical classic candidate rule

```text
nu_shifted = nu0 + delta_air * p
```

with shell-local total pressure and no invented temperature dependence.

For A iso-1, follow the recovered advanced historical shift parameterization. For rare A isotopologues, follow the recovered Galatry auxiliary representation and do not invent missing shift/narrowing behavior.

A full-path pressure-shift sensitivity remains required because the critical twilight rays sample dense shells well below the chemistry target.

## 7. Far-wing / quadrature policy

No universal fixed `+/-N cm^-1` physical cutoff is frozen.

For classic Voigt B/IRA candidates, the preferred numerical strategy is:

1. integrate target/source contributions on deterministic line-centred quadrature;
2. at every target quadrature node, evaluate attenuation from **all accepted absorber lines in that band** rather than discarding absorbers outside an arbitrary `+/-10` or `+/-20 cm^-1` window;
3. converge target support and quadrature order independently against stricter references;
4. verify the complete altitude/SZA domain.

For A, the support/convergence strategy must follow the recovered SDV+line-mixing and Galatry representations rather than isolated-Voigt tails.

## 8. IRA CIA Option B: source identity recovered, exact asset still pending

The baseline remains monomer-only, but the historical CIA twilight attenuation sensitivity is mandatory before M4D closure.

HITRAN2016 identifies Maté et al. (1999), DOI `10.1029/1999JD900824`, as the revised 1.27-micron CIA source.

The historical semantics are:

- pure O2 -> `O2-O2`;
- 21:79 O2:N2 mixture -> `O2-Air`;
- do not add O2-O2 on top of O2-Air for the same atmospheric mixture.

For the atmospheric sensitivity the candidate optical depth is:

```text
tau_CIA(nu)
  = sum_shell k_O2-Air(nu,T_shell)
              * n_O2,shell * n_air,shell * ds_shell
```

with `k` in `cm^5 molecule^-2`.

Maté measurements were made at `253`, `273`, and `296 K`; the M4D column contains colder shells. No below-range extrapolation policy is frozen yet. The exact historical HITRAN2016 CIA bytes/hash also remain pending. See `docs/m4d_ira_cia_historical_source_recovery.md`.

## 9. Line-mixing / profile invariants

For A line mixing, apply physical invariants to the **total band absorption**, not blindly to every algebraic mixing contribution.

Required final invariants include:

- total physical absorption finite and nonnegative;
- zero absorber column recovers unattenuated excitation;
- final excitation rates finite and nonnegative;
- deterministic source-order invariance;
- normalization/conservation consistent with the recovered historical formalism;
- identical selected profile semantics in target excitation and shell attenuation.

For isolated Voigt/Galatry components, integrated normalized profile strength must recover `S(T)` to the declared numerical tolerance.

## 10. Current gate decision

**M4D DESIGN REMAINS NOT FROZEN.**

### Source/materialization blockers

- Freeze `NIHMS804415-supplement-supplement_1.pdf` exact bytes/SHA-256 and executable Drouin/HITRAN2016 mapping for A iso-1.
- Freeze `07_A-band_SDF.dat` and `07_hit12_0.76mic_Galatry.par` bytes/SHA-256, verify their mapping to the accepted A iso-2/iso-3 lines, and confirm HITRAN2016 continuity.
- Freeze the exact historical HITRAN2016 Maté `O2-Air` CIA asset used for the required IRA sensitivity.

### Scientific-design status

- A iso-1: Drouin/HITRAN2016 advanced SDV + line mixing selected in principle; executable materialization pending.
- A iso-2/iso-3: Long/HITRAN2012 Galatry + Dicke narrowing selected as historical candidate; byte/mapping continuity check pending.
- B: classic HITRAN2016 Voigt baseline candidate selected; corrected qSDV sensitivity required.
- IRA: classic HITRAN2016 Voigt monomer baseline candidate selected; historical CIA attenuation remains a separate closure sensitivity.

### Numerical-convergence blockers

After the required source bytes are locally available:

- apply each selected profile consistently to target excitation and shell attenuation;
- quantify pressure-shift impact;
- test all-absorber-lines attenuation for B/IRA;
- converge A advanced/Galatry evaluations with physically appropriate support rules;
- repeat all 51 target altitudes at `SZA = 0, 60, 85, 89, 89.9, 95, 99 deg` plus illuminated-tangent and immediately-shadowed boundary cases;
- demonstrate `<=0.1%` numerical convergence above the current `1e-15 s^-1` floor or independently justify a revised floor before implementation authorization;
- execute the historical IRA CIA twilight sensitivity with an explicit cold-shell policy.

Do not create `docs/m4d_final_design_specification.md` and do not authorize production M4D implementation until these items close.
