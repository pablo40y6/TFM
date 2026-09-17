# M4D pressure-broadening and line-shape provenance follow-up

Status: **A-BAND SOURCE MATERIALIZATION BLOCKER / B+IRA BASELINE CANDIDATES SELECTED / DESIGN NOT FROZEN**

Branch: `milestone/m4d-design`

This note follows `docs/m4d_final_design_review.md`. It does not implement M4D, change the accepted M4C-R2 baseline, or authorize M5. It narrows the remaining pressure-broadening / line-shape gate using the historical HITRAN2016-era evidence.

## 1. Accepted starting point

The previous numerical review remains accepted:

- Doppler-only is not adequate over the full required altitude/SZA domain because illuminated twilight rays can traverse substantially denser atmosphere below the 50 km chemistry boundary.
- The accepted M4C spherical geometry remains valid.
- Shell-local temperature scaling is mandatory.
- Deterministic atmospheric/path sub-stratification at `0.125 km`, checked against `0.0625 km`, is the current converged M4D path rule.
- The mixed Doppler-target/Voigt-attenuation experiment was sufficient to reject Doppler-only, but it was not a final pressure-broadened calculation.
- Plain Voigt attenuation windows `+/-10 -> +/-20 cm^-1` did not close the declared `0.1%` gate for weak A/B twilight rates.

## 2. A band: exact historical source identified, executable materialization still blocked

Gordon et al. (2017), HITRAN2016, Section 2.7.2 identifies Drouin et al. (2017), *Multispectrum analysis of the oxygen A-band*, JQSRT 186, 118-138, DOI `10.1016/j.jqsrt.2016.03.037`, as the principal-isotopologue A-band source.

The historical representation is not plain isolated Voigt. HITRAN2016 describes:

- speed-dependent Voigt broadening;
- collisional line mixing;
- a full W-matrix treatment in the Drouin source model;
- conversion of Drouin foreign-broadening quantities to air using the `N2:O2 = 0.79:0.21` atmospheric mixture;
- evaluation of scaled foreign/self W matrices at four standard temperatures and transformation to first-order line-by-line Rosenkranz parameters for HITRAN;
- pressure shifts and temperature dependences associated with the advanced parameterization;
- CIA as a separate spectroscopic component rather than a resonant-line wing surrogate.

Drouin et al. explicitly state that high-accuracy A-band absorption across atmospheric pressures requires a sophisticated line shape together with line mixing. Their public PMC record, `PMC5103325`, identifies the exact supplementary file

```text
NIHMS804415-supplement-supplement_1.pdf
reported size: 94.8 kB
```

and states that the supplement contains the modified line-mixing matrices and temperature-dependent `Y` values. The article describes four retained sub-matrices: `PP` and `RR` of size `18 x 18`, and `PQ` and `RQ` of size `17 x 17`.

Therefore A is no longer a source-*discovery* blocker: the authoritative source family and exact supplement identity are known.

It remains a **SOURCE MATERIALIZATION / PARAMETER-MAPPING BLOCKER** because the project still lacks:

1. frozen bytes and SHA-256 for the historical supplement;
2. a deterministic transcription/extraction of the required W-matrix / `Y(T)` material;
3. the exact executable mapping from the Drouin native model to the HITRAN2016 Rosenkranz representation used for the project;
4. a frozen policy for the rare A-band isotopologues, whose summed 296-K intensity is small but non-zero and for which the same principal-isotopologue parameterization cannot simply be assumed.

The current 160-character SpectralCalc records remain valid transition/intensity provenance, but do not contain the complete advanced A-band relation set.

**A-band decision:** do not replace the historical advanced representation by an arbitrary isolated Voigt model merely to obtain convergence.

## 3. B band: classic HITRAN2016 Voigt selected as baseline candidate

The B band must be separated from A.

The HITRAN2016 O2 discussion describes a Domyslawska/Wojtewicz/Lisak quadratic speed-dependent Voigt dataset for self-broadened principal-isotopologue B-band transitions, but also states that incorporation into HITRAN was planned. HITRAN2020 later states retrospectively that B-band SDV parameters adopted in HITRAN2016 contained a concrete width-convention defect: values reported as full widths in the source work had been treated as half-widths and were subsequently corrected.

This leaves the advanced B-band history both partial and version-sensitive. It is also primarily a self-broadened dataset rather than a complete all-isotopologue atmospheric profile model.

For `historical_2020`, the design policy is therefore:

**Baseline candidate: classic isolated Voigt using the complete historical HITRAN2016 160-character fields already present in the accepted B subset.**

For every B line, the classic Lorentz HWHM is

```text
gamma_L(p,T)
  = (296/T)^n_air
    * [gamma_air * (p - p_O2) + gamma_self * p_O2]
```

with pressures in atm and HITRAN HWHM coefficients in `cm^-1 atm^-1`.

The classic shifted center is

```text
nu_shifted = nu0 + delta_air * p
```

under the historical classic HITRAN convention unless a more specific historical relation is explicitly recovered for that line.

`gamma_air` is already the HITRAN air-broadening coefficient. Do **not** convert it again with another `0.79/0.21` mixture. The partial pressure term above already combines air and O2 self broadening in the standard HITRAN formula.

The known defective/partial advanced B-band SDV values are **not** reproduced silently in the baseline. Instead, a corrected source-based qSDV calculation on the covered principal-isotopologue lines is a required sensitivity. If that sensitivity changes any accepted M4D B-band rate by more than the `0.1%` design tolerance, the classic-Voigt baseline candidate must be reopened before freeze.

This closes the previous B-band scientific-policy ambiguity without claiming that numerical validation is complete.

## 4. IRA / 1.27 micron: classic HITRAN2016 Voigt selected as monomer baseline candidate

Mendonca et al. (2019) records that the discrete HITRAN2016 1.27-micron line parameters are very similar to HITRAN2012 except for improved line positions, and that the HITRAN2012-era parameters were derived from Voigt-profile analyses. Later beyond-Voigt studies improve high-accuracy terrestrial retrievals, but do not establish a complete historical HITRAN2016 advanced profile analogous to the A-band update.

Therefore the selected historical monomer baseline candidate for `gIRA` is:

**classic isolated Voigt using the accepted HITRAN2016 `gamma_air`, `gamma_self`, `n_air`, and `delta_air` fields with the same standard pressure/temperature equations stated for B.**

This is now a design selection, not merely an open possibility. It remains conditional on the final consistent target+attenuation convergence run.

## 5. Pressure-shift rule and remaining sensitivity

For classic B/IRA profiles, the baseline candidate uses the historical HITRAN shift convention

```text
nu_shifted = nu0 + delta_air * p
```

with shell-local total pressure. No separate temperature dependence of classic `delta_air` is invented.

For A, the advanced historical source contains richer shift information, including temperature-dependent shift behavior, so the final A treatment must follow the recovered A parameterization rather than force the classic rule onto it.

A full-path pressure-shift sensitivity remains required because twilight rays sample denser shells far below the chemistry target.

## 6. A-band rare isotopologues

The accepted A subset contains:

```text
iso 1: 150 lines
iso 2: 140 lines
iso 3: 140 lines
```

and the rare-isotopologue summed strengths are small compared with iso 1 but not identically zero. The principal-isotopologue Drouin parameterization must not be copied automatically to iso 2/3.

Before A can be frozen, either:

- recover the historically appropriate line-shape treatment for the rare isotopologues; or
- demonstrate quantitatively that a documented classic-profile fallback for iso 2/3 changes final `gA` by `<=0.1%` throughout the validation domain.

## 7. Far-wing / quadrature policy

No universal fixed `+/-N cm^-1` physical cutoff is frozen.

For the classic Voigt B/IRA candidates, the preferred convergence strategy is to separate source integration support from attenuation evaluation:

1. integrate the target/source contribution on deterministic line-centred quadrature;
2. at every target quadrature node, evaluate attenuation from **all accepted absorber lines in the band**, rather than discarding absorber contributions outside an arbitrary `+/-10` or `+/-20 cm^-1` window;
3. converge target quadrature/support independently against a stricter reference;
4. verify the resulting rates over the complete altitude/SZA validation set.

This is a candidate numerical strategy, not yet a frozen final algorithm. Its purpose is to remove the artificial attenuation-wing truncation that caused the previous Voigt convergence failure.

For A, the computational support/convergence rule must follow the recovered SDV + line-mixing representation and cannot be inferred from an isolated Voigt tail.

## 8. IRA CIA Option-B source chain narrowed

The existing Option-B decision is retained:

- CIA is excluded from the historical monomer `gIRA` baseline source term and baseline attenuation;
- CIA remains a required documented twilight sensitivity/limitation.

HITRAN2016 narrows the historical CIA provenance substantially. For the 1.27-micron transition it states that the revised data are from Maté et al. (1999), *Absolute intensities for the O2 1.27 um continuum absorption*, JGR Atmospheres 104(D23), 30585-30590, DOI `10.1029/1999JD900824`.

HITRAN2016 places:

- pure-O2 measurements in the `O2-O2` CIA file;
- `21:79 O2:N2` air-mixture measurements in the `O2-Air` file;
- and explicitly warns not to double count O2-O2 by adding both atmospheric `O2-Air` and a separate O2-O2 contribution for the same mixture.

Thus the CIA sensitivity no longer lacks a historical source family. What remains is to freeze the exact historical machine-readable HITRAN2016 CIA file bytes/hash and execute the twilight sensitivity. Current HITRAN2024 CIA products must not be substituted silently.

## 9. Line-mixing numerical invariants

When A line mixing is materialized, tests must apply invariants to the **total physical band absorption**, not blindly to every algebraic per-line mixing contribution.

Required invariants include:

- total absorption finite and physically nonnegative over the validated domain;
- zero absorber column recovers the unattenuated limit;
- final excitation rates finite and nonnegative;
- deterministic source-order invariance;
- normalization/conservation consistent with the recovered historical line-mixing formalism;
- identical selected profile semantics in target excitation and shell attenuation.

## 10. Current gate decision

**M4D DESIGN REMAINS NOT FROZEN.**

The blocker is now narrower.

### Source/materialization blocker

- Freeze the exact Drouin A-band supplement bytes/hash and executable parameter mapping needed to reproduce the HITRAN2016 principal-isotopologue SDV + line-mixing representation.
- Resolve or numerically bound the A-band rare-isotopologue line-shape treatment.
- Freeze the exact historical HITRAN2016 1.27-micron CIA file required for the Option-B sensitivity.

### Scientific-design status

- A principal isotopologue: advanced historical SDV + line mixing required; not yet executable.
- B: classic HITRAN2016 Voigt selected as baseline candidate; corrected qSDV on covered principal-isotopologue lines is a required sensitivity.
- IRA: classic HITRAN2016 Voigt selected as monomer baseline candidate.
- No unresolved B-band policy choice remains.

### Numerical-convergence blocker

Once the required source bytes are locally available:

- apply each selected profile consistently to target excitation and shell attenuation;
- quantify pressure-shift impact;
- test the all-absorber-lines attenuation strategy for B/IRA;
- repeat all 51 target altitudes at `SZA = 0, 60, 85, 89, 89.9, 95, 99 deg` plus illuminated-tangent and immediately-shadowed boundary cases;
- demonstrate `<=0.1%` numerical convergence above the current `1e-15 s^-1` diagnostic floor, or separately justify any revised floor before implementation authorization;
- execute the required historical IRA CIA twilight sensitivity.

### Environment/tool limitation

The remaining numerical closure cannot be reproduced from repository bytes alone because the licensed raw HITRAN2016 line export is intentionally not committed. The source document identities are known, but the A supplement and historical CIA bytes are not yet frozen locally.

Do not create `docs/m4d_final_design_specification.md` and do not authorize production M4D implementation until these items close.
