# M4D HITRAN2016 O2 line-source recovery

Status: **DRAFT EVIDENCE / ACQUISITION CANDIDATE IDENTIFIED / BYTES NOT FROZEN**

Branch: `milestone/m4d-design`

This note records the current acquisition state for the exact historical O2 line-list input required by M4D. It does not authorize implementation, does not reopen M1-M4C-R2, and does not permit substitution of current HITRAN data for the historical HITRAN2016 baseline.

## 1. Current conclusion

A practical historical acquisition route has now been identified: **SpectralCalc's Line List Browser**, which explicitly added the HITRAN2016 line list in 2018 and is independently documented in a 2024 peer-reviewed study as the source used for HITRAN2016 calculations.

The line-list gate is **not yet closed**. We still need to retrieve the actual O2 transition records, preserve the original bytes or an auditable permitted equivalent, compute SHA-256, and validate the records against HITRAN2016 fingerprints and the required A/B/IRA quantum-state selections.

Working status:

**HITRAN2016 O2 ACQUISITION CANDIDATE IDENTIFIED — ACTUAL O2 BYTES / HASH / BAND COUNTS PENDING.**

## 2. Important correction to the HITRAN2016 O2 coverage fingerprints

HITRAN2016 Table 3 gives both **HITRAN2012** and **HITRAN2016** spectral coverage columns. An earlier draft of the M4D research notes accidentally copied the old HITRAN2012 coverage values for the first two O2 isotopologues while pairing them with the HITRAN2016 transition counts.

The correct HITRAN2016 fingerprints are:

| local iso | HITRAN isotopologue code | isotopologue | HITRAN2016 line count | HITRAN2016 spectral coverage (cm^-1) |
| --- | --- | --- | ---: | ---: |
| 1 | 66 | 16O2 | 15,263 | 0-57,028 |
| 2 | 68 | 16O18O | 2,965 | 1-56,670 |
| 3 | 67 | 16O17O | 11,313 | 0-14,537 |

For comparison, the corresponding HITRAN2012 coverage values printed in the preceding column are `0-15,928`, `1-15,853`, and `0-14,538 cm^-1`. Those older ranges must **not** be used as HITRAN2016 full-range fingerprints.

Primary source:

- Gordon et al. (2017), *The HITRAN2016 molecular spectroscopic database*, JQSRT 203, 3-69, Table 3, DOI `10.1016/j.jqsrt.2017.06.038`.
- https://hitran.org/media/refs/HITRAN-2016.pdf

This correction does **not** change the M4D target bands, which are all below about 15,000 cm^-1. It does change the preferred full-O2 acquisition range and the full-dataset validation fingerprint.

## 3. Why current live HITRANonline is not the historical source

As of September 2026, HITRANonline states that the data on its website correspond to the HITRAN2024 edition. HITRAN2024 went live in January 2026, and the site records subsequent 2026 updates including changes to O2 A-band parameters.

For the `historical_2020` reconstruction, a new download from the current HITRANonline line-by-line interface therefore cannot simply be labelled HITRAN2016.

Current official evidence:

- https://hitran.org/
- https://hitran.org/lbl/
- https://hitran.org/docs/hitran-papers/

Current HITRAN data may later be useful as an explicit updated-physics comparison branch. It is rejected as a silent numerical replacement for the historical M4D baseline.

## 4. SpectralCalc has an explicit HITRAN2016 lineage

SpectralCalc's own release history states:

- **20 August 2018:** `Added HITRAN 2016 linelist`; the 2016 HITRAN line data became available for gases 1-42.
- **2 February 2023:** `Added HITRAN 2020 linelist`; HITRAN2020 became the **default** line list for subscribers.

The second statement describes HITRAN2020 as the default, not as a replacement that erased earlier line-list editions. SpectralCalc's older release history also explicitly states, when HITRAN2008 was introduced, that HITRAN2004 would remain available indefinitely, demonstrating an archival-edition practice.

Source:

- https://spectralcalc.com/info/news.php

SpectralCalc's current help page states that its Line List Browser displays HITRAN and other line-list databases and that users can download complete line-list datasets or selected molecules and wavebands:

- https://www.spectralcalc.com/info/help.php

The current Extract Data page still exposes controls for line list, intensity threshold, spectral range, summary table and data-file format:

- https://www.spectralcalc.com/spectral_browser/db_data.php

Its current glossary documents the standard HITRAN fixed-width fields and states that HITRAN data can be downloaded from the Line List Browser / Extract Data tab:

- https://www.spectralcalc.com/info/glossary.php

Its abundance page still contains a separate HITRAN2016 abundance section and identifies O2 as molecule 7 with three isotopologues:

- local iso 1: 16O2;
- local iso 2: 16O18O;
- local iso 3: 16O17O.

- https://spectralcalc.com/calc/abundances.php

This makes SpectralCalc a concrete candidate for recovering historical HITRAN2016 transition-level data rather than a simulated cross section.

## 5. Independent 2024 peer-reviewed use of SpectralCalc as HITRAN2016 source

Gava, Costa and Sena (2024) explicitly state that their HITRAN2020 spectroscopic parameters were obtained from HITRANonline whereas their **HITRAN2016 spectroscopic parameters were obtained from SpectralCalc**, with last access on 11 March 2024.

References:

- M. L. L. M. Gava, S. M. S. Costa, C. A. P. Sena, *The effects of changes in HITRAN and the water vapor continuum model on infrared radiative transfer calculations and remote sensing applications*, JQSRT 322 (2024) 109025, DOI `10.1016/j.jqsrt.2024.109025`.
- M. L. L. M. Gava, S. M. S. Costa, C. A. P. Sena, *Infrared radiative transfer dataset: Comparisons of HITRAN2020, HITRAN2016, and MT_CKD versions 3.2 & 4.1.1 across five model atmospheres*, Data in Brief 57 (2024) 110867, DOI `10.1016/j.dib.2024.110867`.
- https://pmc.ncbi.nlm.nih.gov/articles/PMC11403244/

Their public reproduction script is even more explicit: it loops over `2016` and `2020` and points RFM to `../hit/hitran${version}-spectralcalc.bin`, implying local inputs named `hitran2016-spectralcalc.bin` and `hitran2020-spectralcalc.bin`.

Stable witness:

- https://github.com/livialmg/HITRAN_MT_CKD_IR_calculations/blob/main/driver_tables/loop_over_profiles.sh

The spectroscopy binaries themselves are not in the public repository, so this is provenance evidence rather than a recoverable numerical asset.

## 6. Independent Prometheus witness

The public `CrossTM/Prometheus` repository at tag `v1.1` preserves an O2 file explicitly named:

```text
O2/O2_SPEC_HITRAN2016.csv
```

Repository metadata:

- Git blob SHA-1: `6723e3c85d48c0f883d4f2c415075184dd8b7301`;
- size: `51,381` bytes.

The file contains transition-level HITRAN-style O2 data beginning near `1405 cm^-1` and extending through the O2 fundamental-region extraction. It is therefore **not** the A/B/IRA M4D dataset and cannot close the source gate.

Its value is provenance/format evidence: the associated Prometheus project documentation states that its HITRAN2016 data were obtained from SpectralCalc as CSV.

Stable witness:

- https://github.com/CrossTM/Prometheus/blob/v1.1/O2/O2_SPEC_HITRAN2016.csv

## 7. Required SpectralCalc extraction

The preferred acquisition is one **complete O2 HITRAN2016 line-list extraction**, not a simulated absorption/cross-section spectrum.

Target configuration:

```text
Line list        : HITRAN2016
Molecule         : O2 / HITRAN molecule 7
Isotopologues    : all O2 isotopologues represented in the HITRAN2016 line list
Intensity cutoff : 0, or the least restrictive exact option available
Spectral range   : complete O2 coverage if permitted, 0-57028 cm^-1
Output            : transition-level line-list data
Preferred format : standard HITRAN fixed-width record format
```

The current SpectralCalc extract interface advertises a permissible spectral-range domain of `0-60,000 cm^-1`, so the published complete HITRAN2016 O2 coverage fits within that domain in principle. Whether the complete interval is allowed in one public extraction still has to be tested in the actual interactive interface.

A full-range extraction is preferred because it permits direct validation against Table 3 counts and coverage. If the service cannot export the entire molecule in one operation, obtain a set of **lossless, non-overlapping chunks** spanning 0-57,028 cm^-1 and concatenate only after preserving each original chunk and its hash.

If even that is impractical, the minimum M4D-specific fallback is a lossless set of broad source intervals containing the complete `a(0)<-X(0)`, `b(0)<-X(0)` and `b(1)<-X(0)` systems. In that fallback, full-dataset Table 3 counts cannot be used as a direct byte-set acceptance test, so provenance evidence and independent record spot-checks become more important.

The physical band subsets must always be selected afterwards from quantum labels, not from acquisition-window boundaries.

## 8. Fields that must survive the extraction

At minimum preserve:

- molecule and local isotopologue identifiers;
- line-center wavenumber `nu`;
- reference-temperature line intensity `sw`;
- Einstein-A coefficient;
- air/self widths;
- lower-state energy;
- temperature exponent and pressure shift;
- global upper and lower quantum labels;
- local upper and lower quantum labels;
- uncertainty and reference identifiers (`ierr`, `iref`);
- line-mixing flag;
- upper/lower statistical weights.

The standard 160-character HITRAN record is preferred because SpectralCalc documents exactly this field structure. A CSV export can be accepted only if its mapping to the HITRAN records is transparent and no required source fields have been discarded.

## 9. Acceptance procedure after download

The retrieved source must pass this gate before M4D implementation begins:

1. Record provider (`SpectralCalc`), exact historical line-list selection (`HITRAN2016`), retrieval date and retrieval URL.
2. Preserve the original downloaded filename and bytes unchanged where terms permit.
3. Compute and record SHA-256 and byte size.
4. Document output format and every exported field.
5. If full O2 is obtained, reproduce the HITRAN2016 counts `15263 / 2965 / 11313` for local isotopologues `1 / 2 / 3` and verify coverage `0-57028 / 1-56670 / 0-14537 cm^-1` within the exact precision of the source records.
6. Confirm that the records belong to HITRAN molecule 7 and only expected O2 line-list isotopologues are present.
7. Select `gIRA`, `gA` and `gB` semantically from global electronic/vibrational state labels:
   - `a(v'=0) <- X(v''=0)`;
   - `b(v'=0) <- X(v''=0)`;
   - `b(v'=1) <- X(v''=0)`.
8. For each selected system record total line count, line count by isotopologue, min/max wavenumber and diagnostic summed `sw` at the HITRAN reference temperature.
9. Preserve hashes for source-derived frozen band subsets.
10. Spot-check representative records against independent historical witnesses where possible.
11. Confirm that standard HITRAN `sw` is used under its terrestrial natural-abundance convention; do not multiply isotopic abundance a second time.
12. Link the line source and the historical TIPS-2017 freeze candidate in one spectroscopy provenance manifest.

Only after these checks pass should the numerical spectroscopy specification be marked `FROZEN` and implementation begin.

## 10. Licensing and repository policy

Do not assume that a publicly accessible extraction can automatically be redistributed.

If provider terms permit preservation of the downloaded data in the project repository, store the untouched source as an immutable raw asset with its manifest.

If redistribution is restricted, do not commit the raw database. Preserve locally the exact bytes and commit only the auditable provenance information, hashes, extraction settings and permitted source-derived subsets.

If a later RFM/HITBIN binary is created, preserve and hash the **original SpectralCalc export first**, then document and hash the conversion product separately.

## 11. Rejected or supporting alternatives

The following remain validation/provenance witnesses rather than the frozen historical numerical source:

- current HITRANonline/HAPI downloads: current site corresponds to HITRAN2024;
- MATS `oxygen.data`: exact historical edition not demonstrated;
- Prometheus `O2_SPEC_HITRAN2016.csv`: explicit edition, but wrong spectral region for M4D;
- miscellaneous public O2 HITRAN-format files without edition provenance;
- AER or other modified line databases derived from HITRAN unless exact equivalence is independently established.

## 12. Current M4D gate

TIPS-2017 now has a strong historical freeze candidate documented separately in `docs/m4d_tips2017_provenance_recovery.md`.

For the O2 transition data, the search has advanced from an open-ended provenance problem to a concrete acquisition route:

**SpectralCalc / HITRAN2016 is the primary acquisition candidate.**

The gate remains open until the actual O2 line bytes are retrieved and validated.

Therefore:

- M4D remains **DESIGN NOT FROZEN / NOT IMPLEMENTED**;
- do not substitute HITRAN2024/current live data;
- do not advance to M5;
- next action is acquisition and forensic validation of the SpectralCalc HITRAN2016 O2 line-list export.