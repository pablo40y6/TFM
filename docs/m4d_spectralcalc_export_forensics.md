# M4D SpectralCalc HITRAN2016 O2 export forensics

Status: **TARGET-BAND LINE-SOURCE GATE PASSED / FULL-RANGE EXPORT INCOMPLETE / OVERALL DESIGN NOT FROZEN**

Branch: `milestone/m4d-design`

This note records forensic inspection of the untouched text export produced manually from SpectralCalc's Line List Browser on 2026-09-17 with the browser UI visibly set to `HITRAN2016`, molecule `O2`, intensity threshold `0`, spectral range `0-57028 cm^-1`, and output format `HITRAN`.

The raw downloaded file is intentionally not committed to the repository because redistribution permission for the underlying historical line-list data has not been established. The source bytes were supplied separately for audit.

## Raw file identity

- byte size: `2,268,239`
- SHA-256: `6b4acbc01cb649891f2d8597875c9cd8e4805cfdd4d3b7841c2d18cbf718de12`
- text records reported by SpectralCalc: `14,085`
- parsed transition records: `14,085`
- every parsed transition record is exactly 160 characters long, consistent with the classic HITRAN fixed-width record layout.

The text export header itself says:

```text
---------- SpectralCalc.com -------------

 query:
    database: unknown
    molecules: O2 (7)
    lower waveband limit: 0 cm-1
    upper waveband limit: 57028 cm-1
    intensity threshold: none

 number of lines found: 14085
```

The `database: unknown` string is therefore a property of the downloaded text export. It does **not** erase the browser-side evidence that the UI was explicitly set to `HITRAN2016`, but it means the edition identity is not self-describing in the raw text bytes and must be preserved through the accompanying acquisition evidence.

SpectralCalc's own version history independently records that the HITRAN2016 line list was added on 2018-08-20, while HITRAN2020 was only added on 2023-02-02 and then made the default for subscribers. The explicit UI selection of `HITRAN2016` is therefore meaningful edition-selection evidence rather than a generic label.

Source: https://www.spectralcalc.com/info/news.php

## Parsed molecule/isotopologue summary

All 14,085 fixed-width records identify HITRAN molecule `7` (O2).

| local iso | records in SpectralCalc export | min nu (cm^-1) | max nu (cm^-1) |
| --- | ---: | ---: | ---: |
| 1 | 1,897 | 0.000001 | 17,272.060042 |
| 2 | 875 | 1.691663 | 15,852.677413 |
| 3 | 11,313 | 0.000001 | 14,537.832827 |

The official HITRAN2016 publication fingerprints for complete O2 coverage are larger for local isotopologues 1 and 2:

| local iso | HITRAN2012 count/range | HITRAN2016 count/range |
| --- | --- | --- |
| 1 / 16O2 | 1,787 / 0-15,928 cm^-1 | 15,263 / 0-57,028 cm^-1 |
| 2 / 16O18O | 875 / 1-15,853 cm^-1 | 2,965 / 1-56,670 cm^-1 |
| 3 / 16O17O | 11,313 / 0-14,538 cm^-1 | 11,313 / 0-14,537 cm^-1 |

Primary source: Gordon et al. (2017), HITRAN2016, Table 3, DOI `10.1016/j.jqsrt.2017.06.038`.

Therefore the SpectralCalc export is **not a complete full-range reproduction** of the published HITRAN2016 O2 inventory. That fact remains documented and must not be hidden.

## Why the full-range mismatch does not invalidate the M4D target bands

The later band-level investigation substantially narrows the discrepancy.

### 1. The low-frequency main-isotopologue inventory closes exactly against the documented HITRAN2016 additions

The SpectralCalc export contains `1,897` iso-1 records. The HITRAN2012 count reported in the HITRAN2016 paper is `1,787`, so the low-frequency SpectralCalc inventory contains exactly `110` more main-isotopologue records than HITRAN2012.

Direct quantum-label counting in the acquired raw export gives:

- `b(v'=3) <- X(v''=0)`: `59` iso-1 records;
- `b(v'=2) <- X(v''=1)`: `51` iso-1 records;
- total: `110` records.

Section 2.7.3 of the HITRAN2016 paper explicitly identifies these **same two bands** as new additions to HITRAN2016 and then separately states that the O2 UV bands were merged into the ordinary HITRAN retrieval system.

Thus the numerical identity

```text
1787 + 59 + 51 = 1897
```

is strong evidence that SpectralCalc preserves the complete non-UV/low-frequency HITRAN2016 O2 inventory relevant to this project while omitting the large merged high-energy/UV extension that drives the published full-range counts upward.

This is a forensic inference, not a claim that SpectralCalc reproduces the complete official database outside its exposed range.

### 2. All three M4D target systems lie wholly inside the retained visible/NIR inventory

The semantic subsets extracted below occupy only `7571.882333-14557.976587 cm^-1`.

The O2 atmospheric visible/NIR systems are conventionally in the approximately `5000-18000 cm^-1` region, whereas the Schumann-Runge/Herzberg UV systems responsible for very high-energy coverage lie above roughly `33000 cm^-1`. The target states `a(0)-X(0)`, `b(0)-X(0)` and `b(1)-X(0)` therefore lie far below the high-wavenumber material absent from the SpectralCalc export.

The band definition is nevertheless by quantum labels, **not** by these numerical windows.

### 3. HITRAN2016 describes the target-band updates themselves

The HITRAN2016 O2 section states that:

- the A-band line list already existed in HITRAN2012, with the 2016 principal-isotopologue update adding the Drouin multispectrum line-shape/line-mixing/CIA parameterization and replacing line centers with the more precise Yu et al. positions;
- the rare-isotopologue A-band data originate from the Long et al. studies already underlying the earlier compilation;
- the B band already existed, with 2016 discussion focused on improved line-shape information for the main isotopologue;
- the `a-X` system already existed and received updated energy/position information plus correction of a quantum-number assignment error for 17 lines in the principal-isotopologue `a-X(0,0)` band.

A later independent 2019 spectroscopy analysis also states that the discrete 1.27-micron HITRAN2016 parameters are very similar to HITRAN2012 except for improved line positions from Yu et al.

Sources:

- Gordon et al. (2017), HITRAN2016, Sections 2.7.1-2.7.4.
- Toon et al./TCCON O2 1.27-micron spectroscopy discussion: https://amt.copernicus.org/articles/12/35/2019/

These statements are consistent with an edition update of the target-band parameters without requiring the merged UV inventory for M4D.

## Independent pre-HITRAN2020 record witness

A separate public repository, `ka-til/physhack2020`, preserves `O2.txt.txt`. Its README states that the O2 file was downloaded from `https://hitran.org/`. The commit introducing the file is dated 2020-10-30, before HITRAN2020 was publicly released; a contemporaneous 2020 HITRAN presentation described the online database as pertaining to HITRAN2016, with updates toward HITRAN2020.

Immutable witness:

- repository commit: `d21119b8907235b685bc3bdca1b8dfa4c423c96c`
- Git blob SHA-1: `e50fc990f4528a517ab7106aa72040827328eca5`
- byte size: `136,584`
- row width including CRLF: `72` bytes
- inferred exact row count: `136584 / 72 = 1897`
- last wavenumber: `17272.060042 cm^-1`

The row count and endpoint therefore independently reproduce the SpectralCalc iso-1 low-frequency inventory.

Representative shared fields also agree exactly between that historical direct-HITRAN witness and the 2026 SpectralCalc HITRAN2016 export:

| system | nu (cm^-1) | sw | delta_air | gamma_air | gamma_self | n_air | elower |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| IRA | 7877.648499 | 6.420e-26 | -0.004201 | 0.0443 | 0.045 | 0.83 | 345.8495 |
| A | 13128.268756 | 3.587e-24 | -0.005100 | 0.0564 | 0.055 | 0.71 | 2.0843 |
| A | 13339.201391 | 3.180e-31 | -0.009300 | 0.0312 | 0.034 | 0.63 | 1245.9718 |
| B | 14522.507802 | 9.370e-30 | -0.012200 | 0.0220 | 0.027 | 0.71 | 2701.4912 |

This witness is intentionally treated as corroboration, not as the primary numerical source, because the repository itself labels the files only as downloaded from HITRAN and does not embed a formal edition string.

## Target-band semantic extraction from the supplied records

The fixed-width global quantum labels were parsed directly. The M4D target filters are:

- `gA`: upper `b, v'=0`, lower `X, v''=0`;
- `gB`: upper `b, v'=1`, lower `X, v''=0`;
- `gIRA`: upper `a, v'=0`, lower `X, v''=0`.

### gA / b(0) <- X(0)

- total lines: `430`
- iso 1: `150`, 12849.566990-13339.201391 cm^-1, sum(sw) = `2.24412333089e-22`
- iso 2: `140`, 12975.869001-13165.053952 cm^-1, sum(sw) = `8.7675965e-25`
- iso 3: `140`, 12970.809823-13165.143773 cm^-1, sum(sw) = `1.77109027e-25`
- total sum(sw): `2.25466201766e-22`

### gB / b(1) <- X(0)

- total lines: `320`
- iso 1: `87`, 14284.825910-14557.976587 cm^-1, sum(sw) = `1.4890159683e-23`
- iso 2: `128`, 14341.883025-14519.742461 cm^-1, sum(sw) = `6.1123132e-26`
- iso 3: `105`, 14393.151700-14537.832827 cm^-1, sum(sw) = `1.2987309e-26`
- total sum(sw): `1.4964270124e-23`

### gIRA / a(0) <- X(0)

- total lines: `835`
- iso 1: `230`, 7571.882333-8170.942339 cm^-1, sum(sw) = `3.21142816575e-24`
- iso 2: `322`, 7671.566304-8059.607962 cm^-1, sum(sw) = `1.347918328e-26`
- iso 3: `283`, 7698.734210-8047.714899 cm^-1, sum(sw) = `2.4095173e-27`
- total sum(sw): `3.22731686633e-24`

## Canonical target-subset fingerprints

The raw database itself is not redistributed in Git. For reproducibility, target-subset hashes are defined over the exact 160-character source records in their original source order, encoded as ASCII, with a single LF byte appended after every record including the final record.

| subset | records | canonical bytes | SHA-256 |
| --- | ---: | ---: | --- |
| `gIRA` all isotopologues | 835 | 134,435 | `8d06f322aa4058ab03150a705bf9765fe356a2c7ecd06df98379c46062d295ad` |
| `gA` all isotopologues | 430 | 69,230 | `176a6c21ee37b1244bd11ef7047f6e31f7cada7edff2c3498f31f8d1f2e92eea` |
| `gB` all isotopologues | 320 | 51,520 | `bb5f8b26a2ad3c9dc31870506c3c05bcdb115b7c5b06d7141c9660c952d83c2d` |

Per-isotopologue canonical hashes:

| subset | iso 1 | iso 2 | iso 3 |
| --- | --- | --- | --- |
| `gIRA` | `f4aeed4e555cbd8a0d21700ed03c7401d2ccce97c4332a1ce4f50710c352fe3f` | `66ae63b6ff0815837cf56de19985e9b354a1947dbdeab95c6190ab8c0c084fa8` | `1c245a1034dd9c2ce9440f589e2365b91995c2db768e23da1052c2d32744f9bb` |
| `gA` | `c6ce638220471fa6d278435e856a9ba97d3d3c26576933360b47f36cdffa1b83` | `d48fd3ab51fb22a10a05d708a6faddba8729fa7d3a5cac79a0ed7ff8d2c6319f` | `68985b2077aa6b4c1e2f5cfaa91593ff408f31cc082bdb17abe3a9427bec750f` |
| `gB` | `31a15ed1bc6531cbb8d088ae6f6dbb264ec0423b97d0bdac02c96261c27eefd9` | `0a66c6603829686567131e6588746a28e487e670d680834e51a1856cd23da2bc` | `8189c64409c747e99ea1e340b3141f0ada8155531ad0989c4b45f22825da8587` |

These hashes can later be regenerated from the untouched locally preserved raw export without committing the licensed database bytes.

## Decision on the historical line-list source gate

The evidence now supports the following scoped decision:

**PASS — the acquired SpectralCalc export is accepted as the historical HITRAN2016 transition-level source for the three M4D target systems `a(0)-X(0)`, `b(0)-X(0)`, and `b(1)-X(0)`.**

This PASS is deliberately narrower than claiming that the file is a complete HITRAN2016 O2 database. The full-range fingerprint still fails for isotopologues 1 and 2 because the export omits high-wavenumber material outside the M4D target scope.

The acceptance rests on the combined evidence chain:

1. explicit `HITRAN2016` selection in the acquisition UI;
2. SpectralCalc's documented, versioned HITRAN2016 support;
3. exact classic HITRAN fixed-width structure and molecule/isotopologue semantics;
4. numerical closure of the retained main-isotopologue inventory against the two documented HITRAN2016 low-frequency band additions (`59 + 51 = 110`);
5. separation of the M4D target atmospheric bands from the omitted UV/high-energy inventory;
6. direct HITRAN-era 2020 witness with exactly `1897` main-isotopologue rows and matching target-band parameters;
7. target systems selected semantically from source quantum labels and assigned deterministic hashes.

This closes the previous **HITRAN2016 line-list SOURCE risk for the A/B/IRA target bands**. It does not close the overall M4D design.

## Remaining spectroscopy/design gates

Before implementation is authorized, M4D still requires:

- exact numerical freeze/cross-check of the historical TIPS-2017 O2 partition sums used for temperature scaling;
- a frozen solar irradiance/photon-flux source and exact unit conversion/interpolation rule for all three bands;
- a frozen Doppler/broadening baseline and at least one quantitative sensitivity argument for 50-100 km;
- the direct-beam O2 self-shielding geometry and numerical quadrature/integration strategy;
- an explicit baseline decision on 1.27-micron CIA/continuum treatment;
- numerical convergence criteria and validation tolerances against independent `g`-factor anchors.

## Gate state

- raw SpectralCalc export acquired: **YES**
- raw bytes hashed: **YES**
- 160-character HITRAN structure verified: **YES**
- molecule/isotopologue parsing verified: **YES**
- full HITRAN2016 O2 fingerprint test: **INCOMPLETE for iso 1/2; complete for iso 3**
- reason for count mismatch: **strongly attributable to omitted merged high-energy/UV inventory outside the M4D target range; low-frequency main-isotopologue inventory closes numerically against documented 2016 additions**
- A/B/IRA semantic subsets extracted: **YES**
- target-subset hashes frozen: **YES**
- target-band HITRAN2016 line-source gate: **PASS**
- overall M4D spectroscopy frozen: **NO**
- M4D implementation authorized: **NO**
