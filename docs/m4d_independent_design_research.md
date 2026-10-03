# Milestone 4D independent design research

Status: **DRAFT / DESIGN NOT FROZEN**

Branch: `milestone/m4d-design`

This document records the independent M4D source investigation before any implementation. It is intentionally not an implementation handoff and does not authorize coding. The previous M4D design proposal is not used as an authority here; comparison with it is deferred until the new design has been independently frozen.

## 1. Accepted boundary

M4D must supply the three physical forcing fields still missing from the accepted eleven-field `LocalForcing` contract:

- `gA`
- `gB`
- `gIRA`

M1 through M4C-R2 remain closed and accepted. M4D does not integrate the chemistry in time and must not begin M5.

## 2. What Li et al. (2020) establishes directly

Primary project source: Li et al. (2020), *Retrieval of daytime mesospheric ozone using OSIRIS observations of O2(a1Delta_g) emission*, Atmos. Meas. Tech. 13, 6215-6236, DOI 10.5194/amt-13-6215-2020.

Table A1 explicitly defines the three excitation processes as vertical-profile rate coefficients referenced to HITRAN:

- `gA`: ground-state O2 + photon -> O2(b1Sigma_g+, v=0)
- `gB`: ground-state O2 + photon -> O2(b1Sigma_g+, v=1)
- `gIRA`: ground-state O2 + photon -> O2(a1Delta_g)

The same table cites Gordon et al. (2017) for HITRAN. This establishes the physical target states and the intended spectroscopic source family, but it does **not** publish a complete numerical recipe for reconstructing the three vertical profiles from line parameters and a solar spectrum.

Li et al. also uses HITRAN line strengths and absorption coefficients in its 1.27-micron radiative-transfer retrieval. The paper notes that O2 self-absorption becomes important for the limb-emission problem at sufficiently low tangent altitude. That retrieval calculation is not automatically the same problem as the direct solar-excitation `g` factors, but it confirms that narrow-band O2 spectroscopy and self-absorption are physically relevant.

## 3. Independent historical support for the process topology

Mlynczak et al. (2007), DOI 10.1029/2006JD008355, describes the daytime O2(a1Delta) airglow model and states that the updated model includes:

- solar excitation of the O2 A band near 762 nm;
- solar excitation of the O2 B band near 688 nm;
- solar excitation of the O2 gamma band near 629 nm;
- direct solar excitation of O2(a1Delta) itself.

It further notes rapid quenching of the higher O2(b1Sigma) vibrational levels toward lower levels under mesospheric conditions. This independently supports the physical importance of A/B pumping and direct a1Delta pumping.

However, the accepted Li-2020 topology used by this project contains only `gA`, `gB`, and `gIRA`. No gamma-band forcing exists in the accepted `LocalForcing` contract. M4D therefore must not silently add a new gamma-band state or forcing; any such extension would require a separate scientific change to the accepted topology.

Mlynczak and Marshall (1996), *A reexamination of the role of solar heating in the O2 atmospheric and infrared atmospheric bands*, GRL 23, 657-660, DOI 10.1029/96GL00145, is an additional historical anchor for direct O2 near-IR solar absorption. Later radiation-budget work writes the corresponding absorption rate, or g factor, as a spectrally integrated product of absorption cross section and solar specific intensity. This supports treating the `g` fields as first-order photon-absorption rates rather than empirical chemical rate coefficients.

## 4. Anqi Li 2017 thesis: executable historical A-band recipe

The 2017 Chalmers thesis is particularly important because it gives an explicit A-band calculation rather than only listing `gA` as a profile.

### 4.1 Line shape

Section 3.5 states that both Lorentz and Doppler broadening exist physically, but **Lorentz broadening is neglected for the upper-mesosphere application**. The adopted line profile is Doppler-only.

The cross section is built as a sum over HITRAN lines:

```text
sigma_O2(nu,T) = sum_i S_i(T) * g_D(nu - nu_i,T)
```

with a Gaussian Doppler profile and a temperature-dependent Doppler width.

This is direct historical evidence that a Doppler-only mesospheric baseline is defensible for the legacy A-band calculation. It does not yet prove that the same approximation is adequate for B and IRA at all SZA values in the new 50-100 km model; that still requires an explicit M4D decision and later sensitivity check.

### 4.2 Temperature dependence of line strength

The thesis uses HITRAN reference line strength and lower-state energy to scale the line strength away from the reference temperature. Its printed Eq. 3.45 is a simplified historical expression and does not show an explicit partition-sum ratio.

This creates an important branch decision:

- reproducing the thesis literally would preserve its simplified historical scaling;
- reconstructing from HITRAN2016 consistently would normally use the HITRAN temperature-scaling convention, including partition sums.

M4D must resolve this explicitly; it must not combine the two conventions silently.

### 4.3 Optical depth and direct excitation

The thesis computes O2 A-band optical depth from the same spectroscopic cross section and the slant O2 column:

```text
tau(nu,z) = sigma_O2(nu,T) * sum_z' [ n_O2(z') * dl(z,z') ]
```

and then defines the solar excitation rate schematically as:

```text
gA(z) = sum_nu sigma_O2(nu,T) * J_762 * exp[-tau(nu,T)]
```

where the solar irradiance at 762 nm is stated to come from WMO.

This is strong independent evidence for the core M4D structure:

1. line-by-line O2 absorption;
2. temperature-dependent line strengths and Doppler widths;
3. O2 self-shielding along the solar slant path;
4. an excitation coefficient in s^-1 formed from cross section times attenuated photon flux.

### 4.4 Historical spectroscopy edition is not the new baseline

The thesis cites Rothman et al. (2009), i.e. an older HITRAN generation, for its A-band data. Therefore its line list must be treated as a **legacy methodological specification**, not as the numerical source for the `historical_2020` branch, because Li et al. (2020) later cites Gordon et al. (2017)/HITRAN2016 for the g profiles.

### 4.5 Scope limitation of the thesis

The thesis develops the detailed line-by-line calculation for the **A band**. It does not, in the material inspected so far, publish corresponding complete executable recipes for the B and IRA bands. Consequently, extension of the A-band method to `gB` and `gIRA` must be justified from spectroscopy/airglow sources rather than assumed to be verbatim thesis behavior.

## 5. HITRAN edition requirement

Li et al. (2020) cites Gordon et al. (2017), *The HITRAN2016 Molecular Spectroscopic Database*, JQSRT 203, 3-69, DOI 10.1016/j.jqsrt.2017.06.038.

The HITRAN publication page identifies this as the 2016 edition, replacing HITRAN2012. The current HITRANonline site explicitly states that its live line-by-line data correspond to the current HITRAN2024 edition.

Therefore a line list downloaded today from the ordinary live HITRANonline line-by-line interface or current HAPI cannot, by itself, establish `edition = HITRAN2016`.

### Source gate still open

Before implementation, M4D needs an exact machine-readable O2 line source whose provenance establishes that the records are HITRAN2016. The source must be frozen with at least:

- provider/archive;
- exact filename;
- edition/version evidence;
- retrieval/access date;
- SHA-256;
- format;
- record count;
- O2 isotopologues present;
- documented selection rules used to extract the A, B, and IRA bands.

An archived 2017 IDEALS record titled *HITRAN2016: Part I. Line lists for H2O, CO2, O3, N2O, CO, CH4, and O2* confirms contemporaneously that the HITRAN2016 database was officially released and that O2 was part of the updated line-list set. It is useful provenance evidence, but the record located so far exposes presentation material rather than an immediately verifiable full O2 `.par` asset.

Current status: **UNRESOLVED PROVENANCE RISK**, not yet a final SOURCE BLOCKER.

## 6. O2 1.27-micron spectroscopy and CIA

The HITRAN2016 paper specifically reports revised collision-induced absorption (CIA) data for the O2 1.27-micron band and states that, under atmospheric conditions, CIA is relatively important in this region because the monomer magnetic-dipole lines are weaker than in the A band.

This creates a design question rather than an automatic implementation requirement:

- Li Table A1 represents `gIRA` as a first-order `O2 + photon -> O2(a1Delta)` excitation coefficient.
- HITRAN2016 documents both discrete monomer lines and CIA in the same spectral region.

The baseline must therefore decide explicitly whether `gIRA` is intended to represent only monomer resonant excitation or a broader effective absorption process. No choice is frozen yet. The decision must be justified against Li's model semantics and the mesospheric direct-beam problem, with CIA retained at minimum as a sensitivity/limitation if excluded from the baseline.

## 7. Partition sums / temperature scaling

Gamache et al. (2017), *Total internal partition sums for 166 isotopologues of 51 molecules important in planetary atmospheres: Application to HITRAN2016 and beyond*, JQSRT 203, 70-87, DOI 10.1016/j.jqsrt.2017.03.045, provides the TIPS generation associated with HITRAN2016.

The publication states that the partition sums cover the HITRAN2016 molecules/isotopologues and that the data and TIPS code were provided with HITRAN2016.

This supports using the historical 2017 partition-sum generation for temperature scaling if line intensities need to be converted away from the HITRAN reference temperature. It does **not** yet solve reproducibility: an exact historical machine-readable TIPS source still has to be acquired and hashed before implementation.

Current HITRAN supplementary pages now expose newer TIPS generations, so a present-day generic TIPS download cannot simply be relabelled TIPS2017.

## 8. Solar spectrum

The new thesis inspection materially narrows this question for A-band: Anqi Li 2017 explicitly states that `J762`, the 762-nm solar irradiance used for `gA`, is taken from the World Meteorological Organization (WMO). The thesis uses a single value at the band rather than documenting a high-resolution solar spectrum across each resolved O2 line.

Li et al. (2020), however, does not publish a complete source/provenance recipe for the solar spectrum behind all three profiles `gA`, `gB`, and `gIRA`.

Thuillier et al. (2003), *The Solar Spectral Irradiance from 200 to 2400 nm as Measured by the SOLSPEC Spectrometer from the ATLAS and EURECA Missions*, Solar Physics 214, 1-22, DOI 10.1023/A:1024048429145, provides a measured extraterrestrial spectrum covering all three required regions in one historically plausible product.

Therefore there are currently two historically motivated options to evaluate, not yet choose:

1. a band-local WMO-style solar irradiance treatment analogous to Anqi 2017;
2. a single resolved historical solar spectrum such as Thuillier 2003 for all three bands.

The latter is a **candidate reconstruction choice**, not an established Li-2020 source. The final baseline must make the reconstruction status explicit.

## 9. Current design questions

The following are still open and must be resolved before M4D implementation:

1. Exact HITRAN2016 O2 machine-readable line source and hash.
2. Exact historical partition-sum source and hash, if full HITRAN2016 temperature scaling is adopted.
3. Exact band-selection rules from HITRAN quantum labels for A, B, and IRA.
4. Which O2 isotopologues contribute to each target band.
5. Whether HITRAN natural-abundance weighting already embedded in line intensities requires any further isotopic factor; verify from historical HITRAN documentation.
6. Whether to reproduce Anqi's simplified Eq. 3.45 temperature scaling or use the complete HITRAN2016/TIPS convention for the historical_2020 reconstruction.
7. Whether Doppler-only remains adequate for B and IRA over 50-100 km and the SZA range needed for sunrise, especially near extreme twilight.
8. Whether pressure broadening, line mixing, CIA, or other O2 continua are baseline physics or deferred sensitivities.
9. Exact numerical WMO source/value/units used by Anqi for `J762`.
10. Solar treatment for `gB` and `gIRA`; Li 2020 does not specify it explicitly in the material inspected.
11. If a unified historical solar spectrum is used, which product is defensible and how the reconstruction choice is labelled.
12. Direct-beam attenuation/self-shielding geometry and whether the accepted M4C spherical ray geometry can be reused without changing its scientific semantics.
13. Numerical integration grid / line-wing truncation and convergence criteria.
14. Independent validation anchors for unattenuated and altitude/SZA-dependent `gA`, `gB`, and `gIRA`.
15. Whether the accepted Li topology's omission of gamma-band pumping is quantitatively safe for this TFM baseline or simply an inherited scope limitation to document.
16. Whether the legacy source-code implementation contains discretization or normalization quirks that should be treated as legacy-only rather than reproduced in `historical_2020`.

## 10. Provisional evidence-based conclusions

The following points are sufficiently supported to carry forward into the next research step, but the M4D design as a whole is **not frozen**:

- `gA`, `gB`, and `gIRA` are solar-excitation rate coefficients into O2(b1Sigma_g+, v=0), O2(b1Sigma_g+, v=1), and O2(a1Delta_g), respectively.
- Li 2020 assigns all three as altitude-dependent profiles sourced to HITRAN/Gordon 2017.
- HITRAN2016 is the historically coherent edition implied by that citation.
- Anqi 2017 independently establishes the legacy A-band computational pattern: Doppler-only lines in the upper mesosphere, O2 slant self-absorption, and `gA` from cross section times attenuated 762-nm solar flux.
- Anqi 2017 used an older HITRAN generation and a WMO 762-nm irradiance; these are methodological/historical anchors, not automatically the numerical sources for historical_2020.
- The current HITRANonline line list is not an acceptable substitute for a frozen HITRAN2016 line source because the live service now corresponds to HITRAN2024.
- TIPS2017 is bibliographically coupled to HITRAN2016, but exact machine-readable historical TIPS data still need to be frozen if used.
- A single measured solar spectrum spanning A/B/IRA is scientifically attractive; Thuillier 2003 remains a viable reconstruction candidate, not yet the chosen baseline.
- CIA at 1.27 microns is physically documented by HITRAN2016 and cannot simply be declared nonexistent; whether it belongs in the reduced `gIRA` baseline remains a design decision.

## 11. Next research gate

Continue the independent investigation before freezing any implementation specification:

1. recover as much as possible of the actual `gfactor.m` / `doppler.m` legacy code and identify any discretization/normalization behavior;
2. identify the exact WMO source/value and units behind Anqi's `J762` if recoverable;
3. inspect primary spectroscopy/airglow sources for B- and IRA-band calculation conventions;
4. locate a verifiably archived HITRAN2016 O2 machine-readable line dataset;
5. locate the matching historical partition-sum numerical source if the full HITRAN scaling is selected;
6. only after the above, compare this independently derived design against the old M4D proposal for discrepancies.

If the historical numerical inputs cannot be obtained with adequate provenance after this investigation, M4D must stop with **SOURCE BLOCKER** rather than substitute current HITRAN data silently.
