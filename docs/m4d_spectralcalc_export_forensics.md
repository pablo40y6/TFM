# M4D SpectralCalc HITRAN2016 O2 export forensics

Status: **DRAFT EVIDENCE / RAW EXPORT ACQUIRED / DESIGN NOT FROZEN**

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

## Parsed molecule/isotopologue summary

All 14,085 fixed-width records identify HITRAN molecule `7` (O2).

| local iso | records in SpectralCalc export | min nu (cm^-1) | max nu (cm^-1) |
| --- | ---: | ---: | ---: |
| 1 | 1,897 | 0.000001 | 17,272.060042 |
| 2 | 875 | 1.691663 | 15,852.677413 |
| 3 | 11,313 | 0.000001 | 14,537.832827 |

The official HITRAN2016 publication fingerprints for full O2 coverage are larger for local isotopologues 1 and 2:

- iso 1 / 16O2: 15,263 transitions over 0-57,028 cm^-1;
- iso 2 / 16O18O: 2,965 transitions over 1-56,670 cm^-1;
- iso 3 / 16O17O: 11,313 transitions over 0-14,537 cm^-1.

Therefore this SpectralCalc export is **not a complete full-range reproduction of the published HITRAN2016 O2 line-list counts**, despite the requested 0-57028 cm^-1 interval and zero intensity threshold. The exact reason is not yet established. This discrepancy must not be ignored.

Notably, iso 3 matches the published count exactly, whereas iso 1 and iso 2 are substantially reduced and terminate below 17,300 cm^-1. This strongly suggests incomplete high-wavenumber coverage for iso 1/2 rather than a generic parser failure.

## Target-band semantic extraction from the supplied records

The fixed-width global quantum labels were parsed directly. Using the provisional semantic filters already established for M4D:

- `gA`: upper `b, v'=0`, lower `X, v''=0`;
- `gB`: upper `b, v'=1`, lower `X, v''=0`;
- `gIRA`: upper `a, v'=0`, lower `X, v''=0`;

produces the following subsets.

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

These target systems are present in the export and their ranges are physically plausible. However, presence is not yet proof that the target-band subsets are complete relative to the exact HITRAN2016 source.

## Independent record-level witnesses

Representative A-band records, including the terminal iso-1 line at `13339.201391 cm^-1`, appear identically in several independent public scientific-code witnesses, including the MATS-analysis A-band material and other HITRAN-derived O2 files. This supports correct parsing and record identity for at least part of the A-band content.

Such agreement is validation evidence only; it does not by itself prove completeness or edition identity of the entire SpectralCalc export.

## Current interpretation

The manual acquisition succeeded in the operational sense: a transition-level O2 file was produced from a browser session visibly configured for HITRAN2016, with all provenance-rich fixed-width fields preserved.

However, the full-range fingerprint gate fails because the exported counts for isotopologues 1 and 2 do not reproduce the HITRAN2016 publication totals. Therefore the spectroscopy asset is **not yet FROZEN**.

The most important next question is narrower than before:

**Are the A, B and IRA subsets themselves complete and faithful to HITRAN2016 even though SpectralCalc does not expose the complete higher-wavenumber O2 inventory for iso 1/2?**

That must be answered by independent band-level comparison or by obtaining a second historical HITRAN2016 source covering the same target systems.

## Gate state

- raw SpectralCalc export acquired: **YES**
- raw bytes hashed: **YES**
- 160-character HITRAN structure verified: **YES**
- molecule/isotopologue parsing verified: **YES**
- A/B/IRA semantic subsets extracted: **YES**
- full HITRAN2016 O2 fingerprint test: **FAIL for iso 1 and 2; PASS for iso 3**
- exact reason for SpectralCalc truncation: **OPEN**
- target-band completeness: **OPEN**
- M4D spectroscopy frozen: **NO**
- M4D implementation authorized: **NO**
