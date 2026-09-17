# M4D manual acquisition gate — SpectralCalc HITRAN2016 O2

Status: **USER-ACTION GATE / NO SCIENTIFIC CODE CHANGE**

Branch: `milestone/m4d-design`

This document defines the one browser-mediated acquisition step that is currently required before the M4D spectroscopy design can be frozen. It does not authorize implementation and does not advance M5.

## 1. Why this step is manual

The historical-source investigation has identified SpectralCalc as the strongest practical route for obtaining a transition-level HITRAN2016 O2 line list. Its public documentation confirms that:

- HITRAN2016 was added to SpectralCalc on 20 August 2018;
- the Line List Browser can download complete line-list datasets or selected molecules/wavebands;
- the Extract Data interface accepts spectral ranges within `0-60,000 cm^-1`;
- HITRAN-format data use the standard fixed-width transition record fields needed by M4D.

The current research environment can inspect the public documentation but cannot reliably operate the interactive line-list selection/export form with the user's browser/session. The decisive next evidence must therefore be an export produced through the normal browser UI.

Do **not** automate high-volume requests or attempt to bypass account/interface limits. SpectralCalc's Terms of Use explicitly prohibit automated high-volume simulation requests.

Sources:

- https://spectralcalc.com/info/news.php
- https://www.spectralcalc.com/info/help.php
- https://www.spectralcalc.com/spectral_browser/db_data.php
- https://www.spectralcalc.com/info/glossary.php
- https://www.spectralcalc.com/info/terms.html

## 2. Exact browser procedure

### A. Open the Line List Browser

Open SpectralCalc's **Line List Browser** and make the historical edition explicit before exporting.

Required selections:

```text
Line List / database edition : HITRAN2016
Species / molecule           : O2 (HITRAN molecule 7)
Isotopologues                : all available O2 line-list isotopologues
Intensity representation     : raw line intensity, not an extra atmospheric-concentration scaling
```

If `HITRAN2016` is **not** explicitly selectable, stop. Do not accept a default HITRAN2020/current list as a substitute.

### B. Go to Extract Data

Use the **Extract Data** tab for the selected historical line list and O2 molecule.

Preferred settings:

```text
Line List         : HITRAN2016
Intensity cutoff  : 0, or the least restrictive exact value allowed
Units             : cm^-1
Lower limit       : 0
Upper limit       : 57028
Summary table     : enabled if available
Data file format  : HITRAN fixed-width / original HITRAN style if available
```

The `0-57028 cm^-1` interval is the preferred complete O2 extraction because it spans the published HITRAN2016 coverage of the principal O2 isotopologue and enables a complete Table-3 fingerprint test.

If the interface rejects `0-57028` because of a line-count/waveband/account limit, do not narrow the dataset silently. Use the chunked fallback below.

## 3. Full-range chunked fallback

If one complete O2 export is not permitted, export these non-overlapping chunks with **identical settings**:

```text
00000-10000 cm^-1
10000-20000 cm^-1
20000-30000 cm^-1
30000-40000 cm^-1
40000-50000 cm^-1
50000-57028 cm^-1
```

Boundary handling must be checked after download because some interfaces may treat both interval endpoints as inclusive. Preserve every original chunk unchanged. Any duplicate boundary records should be removed only in a later documented processing step, never by editing the raw downloads.

If full-range chunking is unavailable but narrower exports are possible, the minimum M4D-specific acquisition fallback is:

```text
IRA source interval : 7000-9000 cm^-1
A+B source interval : 12000-16000 cm^-1
```

These are deliberately broad **acquisition intervals**, not physical band definitions. The frozen `gIRA`, `gA` and `gB` subsets must later be selected from the HITRAN electronic/vibrational quantum labels.

## 4. File format requirements

Prefer the standard HITRAN fixed-width transition format. SpectralCalc documents the following fields:

- molecule number;
- isotopologue number;
- transition frequency / wavenumber;
- line intensity;
- Einstein A coefficient;
- air- and self-broadened widths;
- lower-state energy;
- temperature-dependence exponent;
- pressure shift;
- upper/lower global vibrational/electronic quanta;
- upper/lower local quanta;
- error codes;
- reference codes;
- line-mixing flag;
- upper/lower statistical weights.

If only CSV is offered, export it only if the columns preserve the same information. Do not manually delete columns before validation.

## 5. Preserve the raw evidence before touching it

Immediately after download:

1. **Do not edit, re-save, convert or rename the original file yet.**
2. Keep the browser-generated filename exactly as downloaded.
3. Record the download date/time.
4. Save a screenshot showing, if possible, `HITRAN2016`, `O2`, spectral range, threshold and output format.
5. Upload the untouched file(s) for validation before publishing them in the GitHub repository.

The raw line-list file should initially stay outside the public repository until redistribution terms have been reviewed. SpectralCalc's Terms of Use permit users, except where expressly prohibited, to view/copy/print information and products generated by the site, but that language is not a clean standalone redistribution licence for the underlying historical HITRAN dataset.

Therefore the conservative project policy is:

- use the downloaded data for the thesis/reproducibility audit;
- hash and document it;
- do not commit the raw line list publicly until redistribution permission is clear.

## 6. What the project will do immediately after the file is supplied

No manual scientific interpretation is expected from the user. Once the untouched export is available, the M4D validation pass will:

1. compute SHA-256 and byte size for every raw download;
2. identify the exact file encoding/record structure;
3. parse molecule/isotopologue IDs and all provenance-rich fields;
4. if full O2 was acquired, verify HITRAN2016 fingerprints:
   - local iso 1 / `16O2`: 15,263 lines, coverage 0-57,028 cm^-1;
   - local iso 2 / `16O18O`: 2,965 lines, coverage 1-56,670 cm^-1;
   - local iso 3 / `16O17O`: 11,313 lines, coverage 0-14,537 cm^-1;
5. detect and resolve chunk-boundary duplication if chunking was required, while leaving raw files untouched;
6. select A/B/IRA from quantum-state labels, not from the download windows;
7. calculate line counts, contributing isotopologues, min/max wavenumber and summed reference-temperature `sw` for each target system;
8. compare representative A-band records against the independent MATS witness;
9. link the accepted line-list asset to the already identified historical TIPS-2017 freeze candidate;
10. create a spectroscopy provenance manifest containing source identity, hashes, retrieval settings and validation results;
11. only then decide whether the M4D numerical spectroscopy specification can be marked `FROZEN`.

## 7. Expected raw size

The published HITRAN2016 O2 counts sum to `29,541` transitions across the three O2 line-list isotopologues. A standard 160-character HITRAN record file for O2 alone should therefore be only a few megabytes, so the scientifically preferred full O2 export is not intrinsically a large dataset once the molecule has been restricted to O2.

## 8. Pass / fail outcome

### PASS to forensic validation

Proceed when an untouched export exists and the UI/source evidence shows that it was generated from **HITRAN2016 O2**.

### STOP / do not substitute

Stop and report the UI state if any of the following occurs:

- only HITRAN2020/current data can be selected;
- O2 cannot be isolated;
- the interface only returns simulated cross sections rather than transition records;
- quantum-state/reference fields cannot be preserved;
- historical-edition access requires a subscription or permission not currently available.

A failed manual acquisition is evidence about the source gate. It is **not** permission to replace HITRAN2016 with current HITRAN data.

## 9. Current milestone state

Until an export passes forensic validation:

- M4D remains **DESIGN NOT FROZEN / NOT IMPLEMENTED**;
- the accepted M4C-R2 baseline remains untouched;
- M5 remains gated.
