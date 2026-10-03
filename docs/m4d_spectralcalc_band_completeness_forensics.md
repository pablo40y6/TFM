# M4D SpectralCalc HITRAN2016 band-completeness forensics

Status: **DRAFT EVIDENCE / TARGET BANDS STRONGLY SUPPORTED / DESIGN NOT YET FROZEN**

Branch: `milestone/m4d-design`

This note evaluates the untouched SpectralCalc export obtained manually through the browser with `Line List = HITRAN2016`, `Species = O2`, intensity threshold `0`, wavenumber range `0-57028 cm^-1`, and HITRAN fixed-width output. It does not authorize M4D implementation.

## 1. Raw export identity

User-supplied untouched browser export:

- byte size: `2,268,239` bytes;
- SHA-256: `6b4acbc01cb649891f2d8597875c9cd8e4805cfdd4d3b7841c2d18cbf718de12`;
- SpectralCalc text header reports O2 molecule 7, `0-57028 cm^-1`, no intensity threshold, and `14,085` lines;
- every transition record is exactly 160 characters and parses as the standard HITRAN fixed-width record layout;
- the text header itself says `database: unknown`, so the browser screenshot showing `HITRAN2016` remains essential provenance evidence for the selected edition.

No raw HITRAN/SpectralCalc line-list bytes are committed to this public repository pending redistribution/licensing review.

## 2. Whole-export isotopologue inventory

Parsed line counts and actual returned coverage:

| local iso | isotopologue | SpectralCalc lines | SpectralCalc range (cm^-1) | HITRAN2016 Table-3 lines | HITRAN2016 Table-3 range (cm^-1) |
| --- | --- | ---: | ---: | ---: | ---: |
| 1 | 16O2 | 1,897 | 0.000001-17,272.060042 | 15,263 | 0-57,028 |
| 2 | 16O18O | 875 | 1.691663-15,852.677413 | 2,965 | 1-56,670 |
| 3 | 16O17O | 11,313 | 0.000001-14,537.832827 | 11,313 | 0-14,537 |

Total returned records: `14,085`.

Therefore this SpectralCalc export is **not a complete full-range byte-equivalent extraction of the entire HITRAN2016 O2 line list**.

## 3. Interpretation of the full-range discrepancy

The discrepancy is highly structured rather than random:

- local iso 3 (`16O17O`) matches the HITRAN2016 publication count exactly (`11,313`) and reaches the publication upper limit (~14,537 cm^-1);
- local iso 2 stops at ~15,853 cm^-1, exactly the legacy visible/near-IR coverage scale, while HITRAN2016 Table 3 extends that isotopologue to 56,670 cm^-1;
- local iso 1 reaches ~17,272 cm^-1 but not the HITRAN2016 UV extension to 57,028 cm^-1.

Gordon et al. (2017) explains that HITRAN2016 merged UV O2 bands into the ordinary line-by-line database and also added visible b-state bands. That publication change provides a physically coherent explanation for why the SpectralCalc export can contain updated visible/NIR HITRAN2016 content while still lacking the large UV-line additions that drive the Table-3 full-range count increase.

This means the full-range mismatch does **not by itself demonstrate that the A/B/IRA subsets are incomplete**. The M4D target systems all lie below ~14,600 cm^-1, where the SpectralCalc export has dense, provenance-rich fixed-width records.

However, target-band completeness must be demonstrated independently before the asset can be frozen.

## 4. Semantic A/B/IRA extraction

Using the HITRAN global upper/lower state fields, the raw export yields:

| M4D field | semantic transition | total lines | iso 1 | iso 2 | iso 3 | min nu (cm^-1) | max nu (cm^-1) | sum sw @ HITRAN reference T |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| gIRA | `a(v'=0) <- X(v''=0)` | 835 | 230 | 322 | 283 | 7,571.882333 | 8,170.942339 | 3.22731686633e-24 |
| gA | `b(v'=0) <- X(v''=0)` | 430 | 150 | 140 | 140 | 12,849.566990 | 13,339.201391 | 2.25466201766e-22 |
| gB | `b(v'=1) <- X(v''=0)` | 320 | 87 | 128 | 105 | 14,284.825910 | 14,557.976587 | 1.49642701240e-23 |

These are semantic state selections, not acquisition-window selections.

## 5. Independent line-level witnesses

Several representative records agree with independent public HITRAN-derived witnesses at the line-center and line-strength level.

### A band

The SpectralCalc export contains the `16O2` A-band line:

```text
nu = 13339.201391 cm^-1
sw = 3.180e-31
upper = b, v=0
lower = X, v=0
```

The same line center and line strength are preserved in the public MATS-analysis `oxygen.data` witness and in other public HITRAN-derived line files.

### B band

The SpectralCalc export contains the `16O2` B-band line:

```text
nu = 14557.976587 cm^-1
sw = 9.700e-26
upper = b, v=1
lower = X, v=0
```

The same center/intensity pair appears independently in public HITRAN-derived files including RAGNAR and GALAH-related O2 data.

### IRA band

The SpectralCalc export contains the `16O2` IRA line:

```text
nu = 8170.942339 cm^-1
sw = 9.000e-32
upper = a, v=0
lower = X, v=0
```

The same center/intensity pair appears in an independent public O2 HITRAN-derived file.

These spot checks establish consistency of representative target-band records, but they are not yet a proof that every target-band line is complete or edition-identical.

## 6. What can now be concluded

The source situation is materially better than before the browser acquisition:

1. We have an untouched, hashed, standard-format SpectralCalc export generated while the browser UI explicitly selected `HITRAN2016` and O2.
2. The export is not the complete HITRAN2016 O2 database because SpectralCalc omits large UV portions for isotopologues 1 and 2.
3. The omitted material is at high wavenumber and is structurally consistent with HITRAN2016's UV line-list expansion; the three M4D target systems lie well below that missing UV region.
4. The target A/B/IRA systems are all present with semantic quantum labels, all three HITRAN2016 O2 isotopologues contribute, and representative line parameters agree with independent public HITRAN-derived witnesses.

Therefore the current status is:

**SPECTRALCALC EXPORT IS A STRONG CANDIDATE FOR THE HISTORICAL M4D A/B/IRA NUMERICAL SOURCE, BUT TARGET-BAND COMPLETENESS / EDITION IDENTITY STILL REQUIRES ONE FINAL FORENSIC GATE.**

## 7. Final spectroscopy gate before freezing

Before marking the line source `FROZEN`, complete the following:

1. compare full A/B/IRA line-center sets, where possible, against independent historical or edition-pinned witnesses rather than only spot checks;
2. verify that no HITRAN2016 publication change inside A/B/IRA is absent from the SpectralCalc export;
3. inspect reference-code (`iref`) patterns and confirm they are compatible with the HITRAN2016 O2 update described by Gordon et al. (2017);
4. preserve the browser screenshot and raw export hash together in the provenance manifest;
5. freeze source-derived A/B/IRA subsets with their own SHA-256 hashes if redistribution terms permit, or preserve hashes/derivation metadata without publishing restricted raw bytes;
6. join those subsets to the selected historical TIPS-2017 numerical source and validate `Q(T)` / line-strength scaling;
7. only then freeze the full M4D spectroscopy specification.

Until this final gate passes, M4D remains **DESIGN NOT FROZEN / NOT IMPLEMENTED** and M5 remains gated.
