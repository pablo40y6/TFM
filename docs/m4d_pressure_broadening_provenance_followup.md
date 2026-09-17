# M4D pressure-broadening and line-shape provenance follow-up

Status: **SOURCE/PROVENANCE BLOCKER CONFIRMED / DESIGN NOT FROZEN**

Branch: `milestone/m4d-design`

This note follows `docs/m4d_final_design_review.md`. It does not implement M4D, change the accepted M4C-R2 baseline, or authorize M5. Its purpose is to determine whether the pressure-broadened treatment exposed by the numerical review can be frozen from the historical HITRAN2016-era evidence already available to the project.

## 1. Accepted starting point

The previous numerical review is retained:

- Doppler-only is not adequate over the full required altitude/SZA domain because illuminated twilight rays can traverse substantially denser atmosphere below the 50 km chemistry boundary.
- The accepted M4C spherical geometry remains valid.
- Shell-local temperature scaling is mandatory.
- Deterministic atmospheric/path sub-stratification at `0.125 km`, checked against `0.0625 km`, is the current converged M4D path rule.
- Plain truncated Voigt sensitivities did not close the A/B far-wing gate at the declared `1e-15 s^-1` diagnostic floor.

This follow-up does not reopen those numerical findings.

## 2. What HITRAN2016 establishes for the A band

Gordon et al. (2017), HITRAN2016, Section 2.7.2 states that the principal-isotopologue A-band update was based on Drouin et al. (2017), *Multispectrum analysis of the oxygen A-band*, JQSRT 186, 118-138, DOI `10.1016/j.jqsrt.2016.03.037`.

The HITRAN2016 paper is explicit that this was not a plain isolated-Voigt parameterization. For the principal isotopologue it incorporated:

- a speed-dependent Voigt line shape;
- collisional line mixing;
- a full W-matrix treatment in the underlying Drouin analysis;
- a HITRAN-facing transformation to first-order line-by-line Rosenkranz parameters evaluated from the scaled W matrices at four standard temperatures;
- pressure shifts and temperature dependences associated with the advanced line-shape representation;
- CIA represented separately from the resonant line list.

Primary sources:

- Gordon et al. (2017), *The HITRAN2016 molecular spectroscopic database*, JQSRT 203, 3-69, DOI `10.1016/j.jqsrt.2017.06.038`, Section 2.7.2 and Table 2.
- Drouin et al. (2017), *Multispectrum analysis of the oxygen A-band*, JQSRT 186, 118-138, DOI `10.1016/j.jqsrt.2016.03.037`.
- Stable public manuscript witness: PubMed Central `PMC5103325`, which also exposes the associated supplemental material and states that the modified W matrices and temperature-dependent Y values are provided there.

The Drouin paper also states that accurate A-band absorption over atmospheric pressures requires a beyond-Voigt line shape together with line mixing; this is consistent with the HITRAN2016 representation.

### Consequence for the project

The accepted SpectralCalc export contains classic 160-character HITRAN records. Those records are sufficient for the already accepted transition identities, intensities, lower-state energies, classic `gamma_air`, `gamma_self`, `n_air`, and `delta_air` fields, but they do **not** by themselves carry the full HITRAN2016 advanced A-band SDV/Rosenkranz parameter set described in HITRAN2016 Table 2.

Therefore the project cannot claim that an executable HITRAN2016 A-band SDV + line-mixing model has been recovered from the current raw export.

The public Drouin supplemental material is strong provenance evidence and may become a valid recovery source, but it has not yet been frozen in this repository with the exact byte identity, parameter mapping, temperature convention, and deterministic conversion required to reproduce the HITRAN2016 representation used by the project.

**A-band result: SOURCE/PROVENANCE BLOCKER.**

An isolated Voigt profile with an arbitrary cutoff must not be promoted to the historical HITRAN2016 A-band baseline merely because it can be made numerically convergent.

## 3. What HITRAN2016 establishes for the B band

The B-band requires separate treatment; the A-band model must not be copied automatically.

HITRAN-era spectroscopy introduced speed-dependent Voigt information for self-broadened B-band transitions from the Domyslawska/Wojtewicz/Lisak measurement series. However, the later HITRAN2020 database paper documents a concrete defect in the HITRAN2016 B-band advanced line-shape data:

> the speed-dependent Voigt broadening parameters adopted in HITRAN2016 were treated as half-widths although the original publications reported full widths.

HITRAN2020 Section 2.7.3 states that this discrepancy was subsequently corrected.

Primary source:

- Gordon et al. (2022), *The HITRAN2020 molecular spectroscopic database*, JQSRT 277, 107949, DOI `10.1016/j.jqsrt.2021.107949`, Section 2.7.3.

Supporting historical spectroscopy:

- Domyslawska et al. (2017), *Speed-dependent Voigt profile parameters for oxygen B-band measured by cavity ring-down spectrometer referenced to the optical frequency comb*, J. Phys.: Conf. Ser. 810, 012030, DOI `10.1088/1742-6596/810/1/012030`.

A later B-band study also records that the ordinary air-broadening values in HITRAN2016 inherited older/scaled information and that self-shift parameters were not generally present for the B-band line list. This reinforces the need to distinguish classic Voigt fields from the advanced self-broadened SDV dataset rather than treating them as one homogeneous parameterization.

### Consequence for the project

The historical_2020 branch has two scientifically different choices that must not be conflated:

1. reproduce the released HITRAN2016 advanced B-band values literally, including a now-documented width interpretation error; or
2. apply the later documented correction while still using the HITRAN2016-era spectroscopic source family.

The project has not approved either policy. Because the TFM has consistently avoided silently reproducing known source mistakes or silently substituting newer editions, this choice requires an explicit scientific decision and a frozen parameter source.

The current 160-character SpectralCalc records are not enough to recover the full historical B-band SDV representation or to document a corrected historical advanced parameter set.

**B-band result: SOURCE/PROVENANCE + SCIENTIFIC-DESIGN BLOCKER.**

The previous isolated-Voigt sensitivity remains useful numerical evidence, but it is not a frozen final B-band profile.

## 4. What the historical evidence establishes for the 1.27 micron IRA band

For the `a(0) <- X(0)` discrete monomer lines, HITRAN2016 is much closer to the HITRAN2012 discrete-line compilation, with improved line positions among the important changes. The HITRAN2012-era 1.27-micron line parameters were obtained using Voigt-profile analyses.

A later dedicated study of the 1.27-micron band reports that non-Voigt effects can matter for high-accuracy terrestrial column retrievals, but that does not establish that HITRAN2016 supplied an executable advanced line-shape parameterization for the complete IRA line set analogous to the 2016 A-band update.

Relevant source:

- Mendonca et al. (2019), *Using a speed-dependent Voigt line shape to retrieve O2 from Total Carbon Column Observing Network solar spectra to improve measurements of XCO2*, Atmos. Meas. Tech. 12, 35-50, DOI `10.5194/amt-12-35-2019`.

That paper explicitly notes that HITRAN2016 discrete 1.27-micron parameters are very similar to HITRAN2012 apart from improved line positions, while discussing subsequent evidence for beyond-Voigt effects.

### Consequence for the project

For a strictly HITRAN2016 historical reconstruction, isolated Voigt remains a defensible *candidate* monomer profile for IRA, unlike the principal-isotopologue A band where HITRAN2016 itself documents an advanced representation.

However, the previous M4D numerical review changed shell attenuation to Voigt while retaining a Doppler target/source decomposition as a sensitivity experiment. That was sufficient to reject Doppler-only, but it did not perform the final required calculation with the same Voigt profile applied consistently to both target excitation and shell attenuation over the full validation domain.

**IRA result: no new historical-source blocker for an isolated-Voigt candidate, but the final consistent full-profile numerical convergence test is still required before freeze.**

## 5. Pressure shifts cannot be silently discarded

The accepted classic HITRAN records include `delta_air`. The low-target twilight counterexample demonstrates why a shift assessment must use the pressure along the complete illuminated ray rather than only the pressure at the 50-100 km target.

For any band that ultimately uses a classic or advanced pressure-broadened profile, the implementation design must state explicitly:

- which pressure-shift parameter is used for air and, where available, self broadening;
- its temperature dependence when the selected historical representation defines one;
- how the line center is evaluated shell by shell;
- what is done when a historical self-shift or advanced shift parameter is unavailable.

No assumption that `delta_air` is negligible is frozen by this follow-up. A quantitative full-path sensitivity is still required once the final historical profile source is recovered.

## 6. Line mixing and numerical invariants

If A-band line mixing is recovered, implementation tests must apply invariants to the **total physical band absorption**, not blindly to every algebraic per-line mixing contribution.

Required invariants include:

- total absorption/cross section finite and physically nonnegative over the validated domain;
- correct unattenuated limit at zero absorber column;
- finite and nonnegative excitation rates;
- deterministic source-order invariance;
- conservation/normalization consistent with the recovered historical line-mixing formalism;
- identical selected physical profile semantics in target excitation and shell attenuation.

The exact conservation rule cannot be frozen until the historical A-band parameterization and its executable formula have been recovered.

## 7. Far-wing rule

No universal `+/-N cm^-1` cutoff is frozen here.

The previous review showed that `+/-10 -> +/-20 cm^-1` isolated-Voigt changes still exceed the declared `0.1%` gate for weak A/B twilight cases. More importantly, an arbitrarily extended isolated Voigt is not necessarily the correct physical model for a band whose historical representation includes line mixing and separate CIA.

The required order of operations is therefore:

1. recover/freeze the historical profile parameterization for the relevant band;
2. define its physical support/cutoff or computational evaluation rule from the source model;
3. only then demonstrate numerical convergence of target excitation and shell attenuation to `<=0.1%` over the accepted validation domain.

## 8. IRA CIA scope clarification

The existing Option-B decision is retained:

- CIA is excluded from the historical monomer `gIRA` baseline source term and baseline attenuation;
- CIA remains a required documented twilight sensitivity/limitation.

For design-freeze purposes, this does not require injecting CIA into the baseline profile. The future final M4D specification must state the historical CIA sensitivity as required milestone-closure evidence, with its own exact historical source/provenance, rather than silently converting Option B into Option C or silently adding modern CIA data.

If an exact historical CIA source cannot be obtained when that sensitivity is executed, that limitation must be reported explicitly; it must not be solved by substituting current HITRAN CIA products.

## 9. Current gate decision

**M4D DESIGN REMAINS NOT FROZEN.**

The pressure-broadening blocker is now more specific than in `docs/m4d_final_design_review.md`:

### Source/provenance blocker

- Recover and freeze the executable HITRAN2016-era principal-isotopologue A-band advanced parameterization needed for SDV + line mixing, including the exact historical parameter source, parameter mapping, temperature dependence, pressure shifts and line-mixing representation.
- Resolve the historical B-band advanced-parameter provenance together with the documented HITRAN2016 FWHM/HWHM defect; explicitly approve whether the historical_2020 branch reproduces the released 2016 values or applies the later source-documented correction.

### Scientific-design blocker

- Decide the approved historical policy for the known B-band HITRAN2016 width defect.
- Define per-band/per-isotopologue profile semantics once the source parameters are available; do not require A, B and IRA to share one profile if the historical evidence does not support that.

### Numerical-convergence blocker

After source recovery:

- apply the selected profile consistently to target excitation and shell attenuation;
- include shell-local pressure shifts where required by the selected representation;
- repeat the full 51-altitude validation at `SZA = 0, 60, 85, 89, 89.9, 95, 99 deg` plus tangent/just-shadowed cases;
- demonstrate `<=0.1%` convergence above the currently declared `1e-15 s^-1` floor or separately justify any revised floor before implementation authorization.

### Environment/tool limitation

None. The blocker is historical spectroscopic provenance, not computational capability.

Do not create `docs/m4d_final_design_specification.md` and do not authorize implementation until these items close.
