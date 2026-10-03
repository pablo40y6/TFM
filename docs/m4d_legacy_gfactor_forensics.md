# M4D legacy g-factor forensics and validation anchors

Status: **DRAFT EVIDENCE / DESIGN NOT FROZEN**

Branch: `milestone/m4d-design`

This note records independently recovered legacy executable behaviour and external validation anchors for M4D. It does **not** authorize implementation, does not reopen M1-M4C-R2, and does not treat the previous M4D handoff as an authority.

## 1. Primary legacy evidence recovered from Anqi Li (2017)

The Appendix of Anqi Li's 2017 Chalmers thesis contains the actual MATLAB listings for `gfactor.m` and `doppler.m`. This is stronger evidence than reconstructing their behaviour only from the prose equations.

The legacy A-band routine has the following relevant numerical behaviour:

- input line file: `alines.dat`;
- columns loaded: line centre, line strength, Einstein-A field and lower-state energy;
- the Einstein-A column is loaded but is not used by the routine;
- fixed spectral grid: `12900:0.01:13170 cm^-1`;
- line shape: Gaussian/Doppler only;
- reference temperature: 298 K;
- O2 molecular mass represented as 32 amu;
- temperature-dependent Doppler width scales as `sqrt(T/298)`;
- line strength is scaled with the simplified historical expression described in the thesis, equivalent to a `298/T` prefactor times the lower-state Boltzmann exponential;
- no explicit TIPS partition-function ratio appears in this implementation;
- optical depth is computed from O2 density, the line-by-line cross section and the geometrical path lengths;
- the hard-coded solar spectral photon-flux factor is `2.742e13`;
- the final spectral sum is divided by the **number of HITRAN lines** (`size(freq,1)`), rather than explicitly multiplied by the spectral grid interval or evaluated with a standard quadrature rule;
- values are forced to zero where the first optical-depth row equals zero.

The accompanying `doppler.m` is a normalized Gaussian in wavenumber with the thesis Doppler half-width convention.

### Interpretation

These behaviours are historical evidence, not automatic requirements for `historical_2020`.

In particular, two behaviours require explicit treatment in the new M4D design rather than silent reproduction:

1. division of the spectral sample sum by the number of spectral lines is not the standard numerical approximation to the continuous line-by-line integral;
2. forcing `gA=0` when the optical depth is zero conflicts with the physical optically-thin/unattenuated limit, in which direct solar excitation remains non-zero for an illuminated target.

The simplified `298/T` intensity scaling is also not automatically equivalent to a full HITRAN2016 temperature scaling with TIPS2017. The new design must choose one convention explicitly and justify it.

## 2. Reverse unit check on the legacy solar constant

Treating the hard-coded Anqi value

`2.742e13 photons cm^-2 s^-1 (cm^-1)^-1`

as spectral photon flux at 762 nm gives, using `E_photon = hc/lambda` and the Jacobian between wavelength and wavenumber, approximately

`1.231 W m^-2 nm^-1` at 762 nm.

This is very close to the historical WMO/WRC Wehrli 1985 extraterrestrial spectrum around the A band (the archived tabulation brackets 762 nm with about 1.238 W m^-2 nm^-1 at 761 nm and 1.242 W m^-2 nm^-1 at 763 nm).

Therefore the legacy numerical constant is **strongly consistent** with a WMO/Wehrli-type 762-nm solar spectrum after conversion to photon flux per wavenumber. This is not yet proof of the exact table/interpolation or rounding path used by Anqi, so the exact `J762` provenance remains open.

## 3. Independent unattenuated g-factor anchors

Zhu, Yee & Talaat (2007), JGR 112, D20304, DOI `10.1029/2007JD008447`, provides two particularly useful exo-atmospheric rate coefficients in its Table 1:

- O2 + photon (762 nm) -> O2(b1Sigma): `5.35e-9 s^-1`;
- O2 + photon (1.27 micron) -> O2(a1Delta): `1.54e-10 s^-1`.

These are directly useful as **independent order-and-normalization validation anchors** for reconstructed `gA` and `gIRA` in an unattenuated/zero-column illuminated limit. They are not substitutes for the required HITRAN2016 reconstruction.

Marsh et al. (2002), *High Resolution Doppler Imager observations of ozone in the mesosphere and lower thermosphere*, DOI `10.1029/2001JD001505`, reports an exo-atmospheric O2 atmospheric-band g factor of `5.56e-9 s^-1`, calculated with k-distribution theory. The paper states that this is approximately 4% above the Mlynczak-era value because the calculation also includes the small B-band contribution.

The difference `5.56e-9 - 5.35e-9 = 2.1e-10 s^-1` is therefore useful only as a **rough diagnostic scale** for the B-band contribution. It must not be frozen as an exact `gB` target because the cited 4% comparison and the underlying methods are not exact component separation.

## 4. Important split for the 1.27-micron problem: excitation versus attenuation

Zhu et al. (2007) explicitly states that near-infrared O2 absorption at 1.27 micron was added because the time-dependent model encounters long absorber slant paths near twilight; the absorption cross section was taken from Smith & Newnham (2000).

Smith & Newnham (2000), DOI `10.1029/1999JD901171`, reports laboratory measurements covering the O2 1.27-micron region and distinguishes:

- monomer absorption;
- binary O2-O2 and O2-N2 absorption;
- underlying continuum absorption centred near 7850 cm^-1.

This shows that two M4D questions must be kept separate:

1. **excitation source semantics**: what absorption process is represented by Li-2020 `gIRA` as a first-order O2 excitation coefficient;
2. **direct-beam attenuation**: which O2 absorbers should contribute to optical depth along the long twilight path.

It is therefore scientifically possible that the baseline source term remains a monomer line excitation while a CIA/continuum contribution is considered separately for attenuation or sensitivity. No such choice is frozen yet.

## 5. HITRAN2016 O2 integrity fingerprints

The HITRAN2016 paper provides useful whole-database fingerprints for O2 that can be checked if a candidate raw historical line file is recovered. For molecule 7, the main listed isotopologue entries include:

- isotopologue code 66 (`16O2`): HITRAN2016 coverage to 57028 cm^-1 and **15263 transitions**;
- code 68 (`16O18O`): coverage to 56670 cm^-1 and **2965 transitions**;
- code 67 (`16O17O`): coverage to 14537 cm^-1 and **11313 transitions**.

These counts do not by themselves authenticate a recovered file, but they provide strong consistency checks in addition to edition metadata, record format, hashes and band-selection diagnostics.

## 6. TIPS2017 recovery status

The official `hitranonline/hapi` history already supplies an exact source-control provenance path:

- commit `2a12552364f0ac93e3f3bdfa7b3a9701a45d446b` (2018-05-08): `Added partition sums from TIPS-2017`;
- follow-up `f41d9911f2631eed51b96d6c617b4f27786ad477` (2018-05-09): includes a specific TIPS-2017 fix.

The HITRAN2016/TIPS literature identifies the distributed historical code family as `TIPS_2017` / `BD_TIPS_2017`, with the Gamache 2017 implementation naming the v1p0 files explicitly. This means TIPS provenance is now substantially narrower than the raw line-list problem, although an exact frozen artifact/checksum for the implementation used by this project still has to be selected before coding.

A further archival lead is the TU Berlin DepositOnce software package `KSPECTRUM_Htr16`, DOI `10.14279/depositonce-10054` (issued 2020-05-19). Its repository description explicitly states that it uses the HITRAN2016 line list and includes updated `BD_TIPS_2017_v1p0` partition sums. The deposited archive (`KSPECTRUM_Htr16.zip`) is therefore worth inspecting as an independent historical source for TIPS implementation/provenance and possibly line-list interface expectations. It must **not** be assumed to contain redistributable HITRAN line data until the archive is inspected.

## 7. What is now supported versus what remains open

Supported strongly enough to carry into the design phase:

- the exact executable quirks of Anqi's legacy A-band routine are now recovered from the thesis appendix;
- Anqi's solar constant is dimensionally and numerically consistent with a historical WMO/Wehrli-like 762-nm spectrum;
- independent literature gives useful unattenuated validation anchors near `5.35e-9 s^-1` for A-band excitation and `1.54e-10 s^-1` for direct 1.27-micron excitation;
- an A+B atmospheric-band calculation near `5.56e-9 s^-1` supplies an additional combined-band check and rough B-band scale;
- 1.27-micron CIA/continuum physics is historically relevant to twilight attenuation and must be separated conceptually from the semantics of the first-order `gIRA` excitation source;
- HITRAN2016 provides whole-O2 transition-count fingerprints useful for authenticating a recovered historical dataset;
- TIPS2017 has an official historical HAPI commit trail and an additional archived 2020 software lead.

Still open before implementation:

1. recover/freeze a machine-readable O2 line dataset whose identity is verifiably HITRAN2016;
2. freeze the exact TIPS2017 artifact/commit and SHA-256 used for M4D;
3. freeze band-selection rules and participating isotopologues for A, B and IRA;
4. freeze the exact solar forcing for B and IRA and the exact provenance/rounding convention for A;
5. decide the monomer/CIA split for 1.27-micron excitation and attenuation;
6. define the line-by-line quadrature, line-wing/padding and convergence criteria independently of the legacy normalization quirk;
7. validate the resulting unattenuated rates against the historical anchors before any altitude/SZA validation;
8. only then compare the independently derived specification against the previous M4D proposal.

Current gate remains **UNRESOLVED PROVENANCE RISK — NOT YET SOURCE BLOCKER** and **DESIGN NOT FROZEN**.
