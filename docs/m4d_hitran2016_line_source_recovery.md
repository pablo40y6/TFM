# M4D HITRAN2016 O2 line-source recovery

Status: **DRAFT EVIDENCE / ACQUISITION CANDIDATE IDENTIFIED / BYTES NOT FROZEN**

Branch: `milestone/m4d-design`

This note records the current acquisition state for the exact historical O2 line-list input required by M4D. It does not authorize implementation, does not reopen M1-M4C-R2, and does not permit substitution of current HITRAN data for the historical HITRAN2016 baseline.

## 1. Current conclusion

A practical historical acquisition route has now been identified: **SpectralCalc's Line List Browser**, which explicitly added the HITRAN2016 line list in 2018 and is independently documented in a 2024 peer-reviewed data article as the source used for HITRAN2016 calculations.

This materially improves the M4D source situation, but the line-list gate is **not yet closed**. We still need to retrieve the actual O2 transition records, preserve the original bytes or an auditable permitted equivalent, compute SHA-256, and validate the records against HITRAN2016 fingerprints and the required A/B/IRA quantum-state selections.

Working status:

**HITRAN2016 O2 ACQUISITION CANDIDATE IDENTIFIED — ACTUAL O2 BYTES / HASH / BAND COUNTS PENDING.**

## 2. Why current live HITRANonline is not the historical source

As of September 2026, HITRANonline states that the data on its website correspond to the HITRAN2024 edition. HITRAN2024 went live in January 2026, and the site also records subsequent 2026 updates, including changes to O2 A-band parameters.

For the `historical_2020` reconstruction, a new download from the current HITRANonline line-by-line interface therefore cannot simply be labelled HITRAN2016.

Current official evidence:

- https://hitran.org/
- https://hitran.org/lbl/
- Gordon et al., *The HITRAN2024 molecular spectroscopic database*, JQSRT 353 (2026) 109807.

Current HITRAN data may later be useful as an explicit updated-physics comparison branch. It is rejected as a silent numerical replacement for the historical M4D baseline.

## 3. SpectralCalc has an explicit HITRAN2016 lineage

SpectralCalc's own release history states:

- **20 August 2018:** `Added HITRAN 2016 linelist`; the 2016 HITRAN line data became available for gases 1-42.
- **2 February 2023:** `Added HITRAN 2020 linelist`; HITRAN2020 became the **default** line list for subscribers.

The second statement is important: it describes HITRAN2020 as the default, not as a replacement that erased the earlier line-list infrastructure.

Source:

- https://spectralcalc.com/info/news.php

SpectralCalc's current help page states that its Line List Browser displays HITRAN and other line-list databases and that users can download complete line-list datasets or selected molecules and wavebands.

- https://www.spectralcalc.com/info/help.php

The current Extract Data page still exposes controls for:

- `Line List`;
- intensity threshold;
- spectral range;
- summary table;
- data-file format.

- https://www.spectralcalc.com/spectral_browser/db_data.php

This makes SpectralCalc a concrete candidate for recovering historical HITRAN2016 transition-level data rather than a simulated cross section.

## 4. Independent 2024 peer-reviewed use of SpectralCalc as HITRAN2016 source

A 2024 open-access Data in Brief article comparing radiative-transfer calculations made with HITRAN2020 and HITRAN2016 explicitly states in its data-collection table:

- HITRAN2020 was obtained from HITRANonline;
- **HITRAN2016 was obtained from SpectralCalc**.

Reference:

M. L. L. M. Gava, S. M. S. Costa, C. A. P. Sena, *Infrared radiative transfer dataset: Comparisons of HITRAN2020, HITRAN2016, and MT_CKD versions 3.2 & 4.1.1 across five model atmospheres*, Data in Brief 57 (2024) 110867. DOI `10.1016/j.dib.2024.110867`.

Open-access copy:

- https://pmc.ncbi.nlm.nih.gov/articles/PMC11403244/

This does not prove the bytes we will retrieve before we actually retrieve and inspect them, but it is strong independent evidence that SpectralCalc has been used as a practical historical HITRAN2016 provider even after HITRAN2020 became current.

## 5. Independent Prometheus witness

The public `CrossTM/Prometheus` repository at tag `v1.1` preserves an O2 file explicitly named:

```text
O2/O2_SPEC_HITRAN2016.csv
```

Repository metadata:

- Git blob SHA-1: `6723e3c85d48c0f883d4f2c415075184dd8b7301`;
- size: `51,381` bytes.

The file contains transition-level HITRAN-style O2 data beginning near `1405 cm^-1` and extending through the O2 fundamental-region extraction. It is therefore **not** the A/B/IRA M4D dataset and cannot close the M4D source gate.

Its value is provenance/format evidence: the associated Prometheus project documentation states that its HITRAN2016 data were obtained from SpectralCalc as CSV. This independently corroborates the SpectralCalc recovery route.

Stable repository witness:

- https://github.com/CrossTM/Prometheus/blob/v1.1/O2/O2_SPEC_HITRAN2016.csv

The Prometheus file must not be repurposed as the M4D numerical source because it does not cover the required spectral systems.

## 6. Required SpectralCalc extraction

The preferred acquisition is one **complete O2 HITRAN2016 line-list extraction**, not precomputed absorption/cross-section spectra.

Target configuration:

```text
Line list        : HITRAN2016
Molecule         : O2 / HITRAN molecule 7
Isotopologues    : all O2 isotopologues represented in the HITRAN2016 line list
Intensity cutoff : 0, or the least restrictive exact option available
Spectral range   : full O2 range if permitted, ideally 0-15928 cm^-1
Output            : transition-level line-list data
Preferred format : standard HITRAN fixed-width record format
```

The full-range extraction is preferred because it permits direct checking of the HITRAN2016 O2 publication fingerprints:

| local iso | isotopologue | expected HITRAN2016 full-range count | published range (cm^-1) |
| --- | --- | ---: | ---: |
| 1 | 16O2 | 15,263 | 0-15,928 |
| 2 | 16O18O | 2,965 | 1-15,853 |
| 3 | 16O17O | 11,313 | 0-14,538 |

If the service cannot export the complete O2 molecule in one operation, a second-best acquisition is a lossless set of sufficiently broad source intervals that contains the complete `a(0)<-X(0)`, `b(0)<-X(0)` and `b(1)<-X(0)` systems. The band subsets must still be selected afterwards from quantum labels, not from the extraction-window boundaries.

## 7. Fields that must survive the extraction

For M4D, a candidate export is useful only if it preserves enough information to reproduce the standard HITRAN line-strength temperature scaling and identify the physical transitions unambiguously.

At minimum preserve:

- molecule and local isotopologue identifiers;
- line-center wavenumber `nu`;
- reference-temperature line intensity `sw`;
- Einstein-A coefficient;
- lower-state energy;
- global upper and lower quantum labels;
- local upper and lower quantum labels where present;
- upper/lower statistical weights where present;
- uncertainty/reference identifiers (`ierr`, `iref`) where present;
- pressure-broadening/shift fields even if the frozen historical baseline later uses Doppler-only absorption.

The standard 160-character HITRAN record is preferred because it preserves this provenance-rich structure without inventing a new schema. A CSV export can be accepted only if its field mapping to the HITRAN records is transparent and no required source fields have been discarded.

## 8. Acceptance procedure after download

The retrieved source must pass this gate before M4D implementation begins:

1. Record provider (`SpectralCalc`), exact historical line-list selection (`HITRAN2016`), retrieval date and retrieval URL.
2. Preserve the original downloaded filename and bytes unchanged where terms permit.
3. Compute and record SHA-256 and byte size.
4. Document the output format and every exported field.
5. If full O2 is obtained, reproduce the HITRAN2016 line counts by local isotopologue and check spectral min/max against the publication fingerprints above.
6. Confirm that the records belong to HITRAN molecule 7 and only expected O2 isotopologues are present.
7. Select `gIRA`, `gA` and `gB` semantically from global electronic/vibrational state labels:
   - `a(v'=0) <- X(v''=0)`;
   - `b(v'=0) <- X(v''=0)`;
   - `b(v'=1) <- X(v''=0)`.
8. For each selected system record total line count, line count by isotopologue, min/max wavenumber and diagnostic summed `sw` at the HITRAN reference temperature.
9. Preserve hashes for the source-derived frozen band subsets.
10. Spot-check representative records against independent historical witnesses where possible (MATS A-band data, published HITRAN2016 values, other scientific repositories).
11. Confirm that standard HITRAN `sw` is used directly under its terrestrial natural-abundance convention; do not multiply isotopic abundance a second time.
12. Link the line source and the already identified TIPS-2017 historical freeze candidate in a single spectroscopy provenance manifest.

Only after these checks pass should the numerical spectroscopy specification be marked `FROZEN` and implementation begin.

## 9. Licensing and repository policy

Do not assume that a third-party/publicly accessible extraction can automatically be redistributed in this repository.

If the provider's terms permit preservation of the downloaded data in the private/project repository, store the untouched source as an immutable raw asset with its manifest.

If redistribution is restricted, do not commit the raw database. Instead preserve locally:

- the exact downloaded bytes;
- SHA-256;
- acquisition metadata;
- extraction settings;
- an auditable manifest in Git;
- source-derived subsets only if their redistribution is permitted.

Provenance must remain reproducible even if the raw source itself cannot be published with the thesis repository.

## 10. Rejected or supporting alternatives

The following remain useful only as validation/provenance witnesses, not as the frozen historical numerical source:

- current HITRANonline/HAPI downloads: current site corresponds to HITRAN2024;
- MATS `oxygen.data`: exact historical edition not demonstrated;
- Prometheus `O2_SPEC_HITRAN2016.csv`: explicit edition, but wrong spectral region for M4D;
- miscellaneous public O2 HITRAN-format files without edition provenance;
- AER or other modified line databases derived from HITRAN: not byte/record-equivalent to the required baseline unless independently demonstrated.

## 11. Current M4D gate

TIPS-2017 now has a strong historical freeze candidate documented separately in `docs/m4d_tips2017_provenance_recovery.md`.

For the O2 transition data, the situation has advanced from an open-ended source search to a concrete acquisition route:

**SpectralCalc / HITRAN2016 is the primary acquisition candidate.**

The gate remains open until the actual O2 line bytes are downloaded and validated.

Therefore:

- M4D remains **DESIGN NOT FROZEN / NOT IMPLEMENTED**;
- do not substitute HITRAN2024/current live data;
- do not advance to M5;
- next action is acquisition and forensic validation of the SpectralCalc HITRAN2016 O2 line-list export.