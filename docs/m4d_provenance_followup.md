# M4D provenance follow-up

Status: **DRAFT EVIDENCE / DESIGN NOT FROZEN**

This note records additional provenance evidence gathered after `docs/m4d_independent_design_research.md`. It does not authorize M4D implementation and does not change the accepted M4C-R2 baseline.

## 1. Historical TIPS-2017 source narrowed to an exact official HAPI commit

The official `hitranonline/hapi` GitHub history contains an exact commit introducing TIPS-2017:

- repository: `hitranonline/hapi`
- commit: `2a12552364f0ac93e3f3bdfa7b3a9701a45d446b`
- commit date: 2018-05-08 UTC
- commit message: `Added partition sums from TIPS-2017`
- modified file: `hapi/hapi.py`
- Git blob SHA for that file at the commit: `44d04fe469119bc6dc72a834706866b13b932b1c`
- commit URL: https://github.com/hitranonline/hapi/commit/2a12552364f0ac93e3f3bdfa7b3a9701a45d446b

The official HAPI README version history identifies TIPS-2017 as introduced in HAPI version `1.1.0.8`.

A follow-up commit two days later is also relevant:

- commit: `f41d9911f2631eed51b96d6c617b4f27786ad477`
- date: 2018-05-09 UTC
- message: `Added custom extension support for datafiles and fixed I=(2,0) in TIPS-2017`
- URL: https://github.com/hitranonline/hapi/commit/f41d9911f2631eed51b96d6c617b4f27786ad477

The stated `(2,0)` fix does not on its face concern molecular oxygen (HITRAN molecule 7), but this must be verified from the historical code before freezing an exact TIPS snapshot. The important result is that TIPS-2017 is no longer only a bibliographic citation: there is an exact official source-control provenance path that can be pinned and inspected.

### Current assessment

This materially reduces the TIPS provenance risk. Before implementation, the project still needs to decide exactly which historical HAPI commit/version is frozen and to extract/verify the O2 isotopologue partition-sum behaviour actually required by M4D. The selected source should then be stored or otherwise pinned with SHA-256 evidence in the repository.

## 2. WMO solar source is strongly consistent with Wehrli 1985, but exact Anqi `J762` is not yet proven

The U.S. National Laboratory of the Rockies (formerly NREL solar-resource archive) describes the **1985 Wehrli Standard Extraterrestrial Solar Irradiance Spectrum** as the World Meteorological Organization / World Radiation Data Centre air-mass-zero extraterrestrial solar spectral irradiance distribution.

Primary archive page:
https://www.nlr.gov/grid/solar-resource/spectra-wehrli

The archive identifies the source as:

- C. Wehrli, *Extraterrestrial Solar Spectrum*, Publication no. 615, PMO/WRC, Davos, July 1985;
- spectrum range approximately 199.5 nm to 10075 nm;
- WMO/WRC extraterrestrial distribution.

The archived text dataset is:
https://www.nlr.gov/media/docs/libraries/grid/wehrli85.txt

Near the O2 A band, the archived tabulation gives:

- 761.0 nm: `1.238 W m^-2 nm^-1`
- 763.0 nm: `1.242 W m^-2 nm^-1`

A simple linear interpolation to 762.0 nm would therefore give `1.240 W m^-2 nm^-1`, but **this interpolated value is not yet asserted to be Anqi Li's exact `J762`**. The thesis must be checked for its units, any photon-flux conversion, and whether it used interpolation, a band average, or another WMO table/product.

### Current assessment

Wehrli 1985 is now a strong provenance candidate for the thesis phrase "WMO". This narrows the solar-source problem substantially, but the exact numerical `J762` and unit convention remain open.

## 3. ExoMol provides independent evidence of a HITRAN2016-derived O2 product, but not yet the required raw line source

The ExoMol page for `16O2` includes a dataset explicitly labelled `HITRAN` and states that its line-list products were constructed using data from HITRAN.org, citing Gordon et al. (2017), *The HITRAN2016 Molecular Spectroscopic Database*.

Dataset page:
https://www.exomol.com/data/molecules/O2/16O2/HITRAN/

However, the files exposed on the page inspected are precomputed opacity products (k-tables / cross sections), not the raw HITRAN2016 O2 line records needed to reconstruct `gA`, `gB`, and `gIRA` with transparent band selection and temperature scaling.

### Current assessment

This is useful independent provenance evidence that a HITRAN2016-derived O2 product exists outside the current HITRANonline live edition, but it does **not** satisfy the M4D raw-line-data gate by itself.

## 4. HITRAN2016 raw O2 line-list gate remains open

The official HITRAN2016 publication and the archived 2017 IDEALS record establish that O2 was part of the released HITRAN2016 line-list compilation. The current live HITRANonline service now corresponds to a newer edition, so a fresh live download cannot be silently treated as HITRAN2016.

A third-party historical source, SpectralCalc, publicly records that it added the HITRAN2016 line list in August 2018 and still distinguishes it from later editions. This is a potentially useful recovery path, but the project should prefer an official or independently archived machine-readable source with clear file identity, and must record licensing/access conditions if a third-party copy is used.

Current status remains:

**UNRESOLVED PROVENANCE RISK — not yet SOURCE BLOCKER.**

## 5. Immediate next checks

Before freezing M4D design:

1. inspect the historical HAPI TIPS-2017 implementation at the pinned commit and verify O2 isotopologue mappings/partition values;
2. continue searching for a verifiably archived raw HITRAN2016 O2 line file or official historical access route;
3. inspect the Anqi thesis/code trail for the exact `J762` numerical value and units;
4. determine whether the WMO/Wehrli candidate is sufficient for A-band reconstruction and what independent solar treatment is defensible for B and IRA;
5. do not implement M4D until these provenance choices are explicitly frozen.
