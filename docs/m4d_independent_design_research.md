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

## 4. HITRAN edition requirement

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

Current status: **UNRESOLVED PROVENANCE RISK**, not yet a final SOURCE BLOCKER.

## 5. O2 1.27-micron spectroscopy and CIA

The HITRAN2016 paper specifically reports revised collision-induced absorption (CIA) data for the O2 1.27-micron band and states that, under atmospheric conditions, CIA is relatively important in this region because the monomer magnetic-dipole lines are weaker than in the A band.

This creates a design question rather than an automatic implementation requirement:

- Li Table A1 represents `gIRA` as a first-order `O2 + photon -> O2(a1Delta)` excitation coefficient.
- HITRAN2016 documents both discrete monomer lines and CIA in the same spectral region.

The baseline must therefore decide explicitly whether `gIRA` is intended to represent only monomer resonant excitation or a broader effective absorption process. No choice is frozen yet. The decision must be justified against Li's model semantics and the mesospheric direct-beam problem, with CIA retained at minimum as a sensitivity/limitation if excluded from the baseline.

## 6. Partition sums / temperature scaling

Gamache et al. (2017), *Total internal partition sums for 166 isotopologues of 51 molecules important in planetary atmospheres: Application to HITRAN2016 and beyond*, JQSRT 203, 70-87, DOI 10.1016/j.jqsrt.2017.03.045, provides the TIPS generation associated with HITRAN2016.

The publication states that the partition sums cover the HITRAN2016 molecules/isotopologues and that the data and TIPS code were provided with HITRAN2016.

This supports using the historical 2017 partition-sum generation for temperature scaling if line intensities need to be converted away from the HITRAN reference temperature. It does **not** yet solve reproducibility: an exact historical machine-readable TIPS source still has to be acquired and hashed before implementation.

## 7. Solar spectrum

Li et al. (2020) does not provide a complete source/provenance recipe for the solar spectrum used to derive `gA`, `gB`, and `gIRA`.

Thuillier et al. (2003), *The Solar Spectral Irradiance from 200 to 2400 nm as Measured by the SOLSPEC Spectrometer from the ATLAS and EURECA Missions*, Solar Physics 214, 1-22, DOI 10.1023/A:1024048429145, provides a measured extraterrestrial spectrum covering all three required regions in one historically plausible product.

Thuillier 2003 is therefore a **candidate historical reconstruction source**, not an established Li-2020 source. It must not be frozen as the M4D baseline until the project has checked whether Li's thesis, code, or another cited source specifies the actual solar spectrum used for the g-factor profiles.

## 8. Current design questions

The following are still open and must be resolved before M4D implementation:

1. Exact HITRAN2016 O2 machine-readable line source and hash.
2. Exact historical partition-sum source and hash.
3. Exact band-selection rules from HITRAN quantum labels for A, B, and IRA.
4. Which O2 isotopologues contribute to each target band.
5. Whether HITRAN natural-abundance weighting already embedded in line intensities requires any further isotopic factor (expected answer must be verified from the historical HITRAN documentation, not assumed).
6. Line-intensity temperature-scaling formula and constants.
7. Baseline line shape at 50-100 km and whether Doppler-only is adequate for the accepted historical model.
8. Whether pressure broadening, line mixing, CIA, or other O2 continua are baseline physics or deferred sensitivities.
9. Exact solar-spectrum provenance used by Li/Anqi, if recoverable.
10. If not recoverable, which historical reconstruction spectrum is defensible and how that choice is labelled.
11. Direct-beam attenuation/self-shielding geometry and whether the accepted M4C spherical ray geometry can be reused without changing its scientific semantics.
12. Numerical integration grid / line-wing truncation and convergence criteria.
13. Independent validation anchors for unattenuated and altitude/SZA-dependent `gA`, `gB`, and `gIRA`.
14. Whether the accepted Li topology's omission of gamma-band pumping is quantitatively safe for this TFM baseline or simply an inherited scope limitation to document.

## 9. Provisional evidence-based conclusions

The following points are sufficiently supported to carry forward into the next research step, but the M4D design as a whole is **not frozen**:

- `gA`, `gB`, and `gIRA` are solar-excitation rate coefficients into O2(b1Sigma_g+, v=0), O2(b1Sigma_g+, v=1), and O2(a1Delta_g), respectively.
- Li 2020 assigns all three as altitude-dependent profiles sourced to HITRAN/Gordon 2017.
- HITRAN2016 is the historically coherent edition implied by that citation.
- The current HITRANonline line list is not an acceptable substitute for a frozen HITRAN2016 line source because the live service now corresponds to HITRAN2024.
- TIPS2017 is bibliographically coupled to HITRAN2016, but exact machine-readable historical TIPS data still need to be frozen.
- A single measured solar spectrum spanning A/B/IRA is scientifically desirable; Thuillier 2003 is a viable reconstruction candidate, not yet the chosen baseline.
- CIA at 1.27 microns is physically documented by HITRAN2016 and cannot simply be declared nonexistent; whether it belongs in the reduced `gIRA` baseline remains a design decision.

## 10. Next research gate

Before freezing the design, inspect the Anqi Li 2017 thesis and any available historical implementation for the exact g-factor calculation, especially:

- wavelengths/band definitions;
- solar spectral source or constants;
- line-shape assumption;
- attenuation/self-shielding method;
- any hard-coded or benchmark unattenuated g values;
- any direct statement about HITRAN edition or partition sums.

In parallel, search for a verifiably archived HITRAN2016 O2 line dataset and the matching 2017 partition-sum source. If those historical numerical inputs cannot be obtained with adequate provenance after this investigation, M4D must stop with **SOURCE BLOCKER** rather than substitute current HITRAN data silently.
