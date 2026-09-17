# M4D HITRAN2016 acquisition and band-selection gate

Status: **DRAFT EVIDENCE / DESIGN NOT FROZEN**

Branch: `milestone/m4d-design`

This note records what can now be specified independently about the O2 spectroscopy inputs required for M4D, and what is still missing before implementation is allowed. It does not authorize M4D coding and does not reopen M1-M4C-R2.

## 1. Current outcome

The semantic definition of the three required O2 bands and the HITRAN abundance convention can now be narrowed substantially, but an exact machine-readable O2 line file whose provenance establishes **HITRAN2016** has still not been frozen in this repository.

Current status of the numerical line source therefore remains:

**UNRESOLVED PROVENANCE RISK — not yet SOURCE BLOCKER.**

A present-day live HITRANonline download must not be used as a silent replacement for the required historical edition.

## 2. Canonical O2 identity in HITRAN2016

HITRAN assigns molecular oxygen molecule number `7`.

The HITRAN2016 paper reports three O2 isotopologues in the line-by-line database:

| local iso | AFGL | isotopologue | HITRAN2016 full-range line count | reported range (cm^-1) |
| --- | --- | --- | ---: | ---: |
| 1 | 66 | 16O2 | 15,263 | 0-15,928 |
| 2 | 68 | 16O18O | 2,965 | 1-15,853 |
| 3 | 67 | 16O17O | 11,313 | 0-14,538 |

These counts/ranges are useful fingerprints for a future full O2 extraction. They are not by themselves sufficient to authenticate a candidate file, but a complete claimed HITRAN2016 O2 file should be checked against them.

Primary reference:

- Gordon et al. (2017), *The HITRAN2016 Molecular Spectroscopic Database*, JQSRT 203, 3-69, DOI 10.1016/j.jqsrt.2017.06.038.
- https://hitran.org/media/refs/HITRAN-2016.pdf

## 3. Natural-abundance convention: do not double-weight isotopologues

HITRAN line intensity `sw` is defined using terrestrial natural isotopic abundance. The official HITRAN definitions explicitly include isotopic abundance in the line-intensity convention.

An independent MATS/HAPI header preserved in `innosat-mats/MATS-analysis` states the same point directly for its downloaded HITRAN data:

> `sw`: "Line intensity, multiplied by isotopologue abundance, at T = 296 K"

Therefore the M4D implementation, if it consumes standard HITRAN line strengths and a bulk O2 number density under the HITRAN natural-terrestrial isotopic convention, must **not multiply each line by isotopologue abundance a second time**.

This rule should be frozen only for standard HITRAN `sw` values. If any transformed/third-party line source is eventually used, its intensity convention must first be demonstrated to be equivalent.

Official definitions:

- https://hitran.org/docs/definitions-and-units/
- https://hitran.org/docs/iso-meta/

MATS witness:

- https://github.com/innosat-mats/MATS-analysis/blob/1b16746bf030af9b13d1e568033fcd0dfc7ece46/Bjorn/retrieval/1D_full/Abandabs/Abanddata/oxygen.header

## 4. Semantic band selection should use quantum labels, not wavelength windows

The required physical target states are already established independently from Li et al. (2020):

- `gA`: O2(X, v''=0) -> O2(b, v'=0), atmospheric A band, near 762 nm;
- `gB`: O2(X, v''=0) -> O2(b, v'=1), atmospheric B band, near 688 nm;
- `gIRA`: O2(X, v''=0) -> O2(a, v'=0), infrared atmospheric system, near 1.27 micron.

The standard HITRAN record format contains global upper/lower quantum fields representing electronic and vibrational labels. Therefore the robust M4D selection rule should be based on those state labels, not on broad hard-coded wavelength windows.

Provisional semantic filters to validate against the actual HITRAN2016 file are:

```text
gA   : upper electronic/vibrational state b(v'=0), lower X(v''=0)
gB   : upper electronic/vibrational state b(v'=1), lower X(v''=0)
gIRA : upper electronic/vibrational state a(v'=0), lower X(v''=0)
```

The exact fixed-width string formatting and accepted variants must be derived from the acquired HITRAN2016 records before implementation.

All relevant transition types carried by HITRAN inside those state-to-state systems should remain eligible unless a source-supported reason exists to exclude them. In particular, M4D must not assume that selecting only a specific rotational branch is equivalent to selecting the complete physical band.

## 5. Historical wavenumber windows are diagnostics only

Older HITRAN documentation gives approximate system ranges useful as sanity checks, for example:

- a(0) <- X(0): roughly the 1.27-micron region (~7,700-8,100 cm^-1);
- b(0) <- X(0), A band: roughly 12,900-13,170 cm^-1;
- b(1) <- X(0), B band: roughly 14,300-14,560 cm^-1.

These historical windows are **not** the M4D selection criterion. Once the actual HITRAN2016 O2 records are acquired, min/max wavenumbers and line counts must be derived from the quantum-label filter itself and recorded as evidence.

This avoids silently excluding updated or weak transitions merely because an older band window was too narrow.

## 6. Isotopologue policy

The future extraction should begin from all O2 isotopologues actually present in HITRAN2016 line-by-line data (local IDs 1-3 above) and then apply the semantic band filter.

For each target band, record:

- isotopologues contributing at least one line;
- line count by isotopologue;
- min/max wavenumber by isotopologue;
- summed reference-temperature line strength by isotopologue as a diagnostic;
- reference identifiers (`iref`) retained from the source where available.

Do not invent transitions for additional O2 isotopologues simply because TIPS-2017 contains partition sums for more isotopic species. TIPS coverage and line-list coverage are not the same thing.

## 7. TIPS-2017 is now much less ambiguous

Gamache et al. (2017) provides the partition-sum generation associated with HITRAN2016 and describes six O2 isotopologues in TIPS-2017. It also documents the standalone/subroutine data-code products `TIPS_2017_v1p0` and `BD_TIPS_2017_v1p0`.

Primary reference:

- Gamache et al. (2017), JQSRT 203, 70-87, DOI 10.1016/j.jqsrt.2017.03.045.

The official `hitranonline/hapi` Git history gives an exact source-control path:

- `2a12552364f0ac93e3f3bdfa7b3a9701a45d446b` — `Added partition sums from TIPS-2017`;
- `f41d9911f2631eed51b96d6c617b4f27786ad477` — follow-up `fixed I=(2,0) in TIPS-2017`.

HITRAN molecule 2 is CO2, whereas O2 is molecule 7. Consequently the explicitly named `(2,0)` correction is not an O2 key. This reduces concern that this particular follow-up correction changed O2 partition sums, although the complete diff still must be treated carefully when selecting the exact historical snapshot.

For a reproducible baseline, prefer a post-fix historical snapshot unless a stronger versioned archive is recovered. Before implementation, freeze the exact O2 TIPS numerical source/data used and record its SHA-256.

Official HAPI commits:

- https://github.com/hitranonline/hapi/commit/2a12552364f0ac93e3f3bdfa7b3a9701a45d446b
- https://github.com/hitranonline/hapi/commit/f41d9911f2631eed51b96d6c617b4f27786ad477

An additional institutional archive, `KSPECTRUM_Htr16`, explicitly states that it uses HITRAN2016 and includes `BD_TIPS_2017_v1p0`, providing a second recovery/check path:

- DOI 10.14279/depositonce-10054
- https://depositonce.tu-berlin.de/items/0dc3d4b8-c913-49b2-b4c1-14646a2f5c3e

## 8. Evidence that a canonical historical `HITRAN2016.par` existed

Several independent scientific-software projects refer to an all-molecule file explicitly named `HITRAN2016.par` or `hitran2016.par`:

- Oxford RFM/HITBIN documentation shows direct conversion of `HITRAN2016.par` and records HITRAN2016-specific parser changes made in September 2017;
- VPL modeling scripts point to `HITRAN_Data/HITRAN2016.par` and explicitly request the HITRAN 2016 `.par` format;
- NOAA-GFDL GRTCODE workflows refer to `HITRAN_files/hitran2016.par`.

Oxford also reports 5,507,557 records for a full `HITRAN2016.par` example. These are valuable historical witnesses of file identity/workflow, but none of the inspected repositories exposes the full licensed line file as a source we can currently freeze.

Oxford reference:

- https://eodg.atm.ox.ac.uk/RFM/hitbin.html

These witnesses therefore strengthen provenance expectations but do **not** satisfy the acquisition gate themselves.

## 9. MATS A-band data are a useful witness, not yet an edition-proof source

The public `innosat-mats/MATS-analysis` repository contains an A-band HITRAN download:

- `oxygen.data`;
- `oxygen.header`;
- notebook output stating `Data is fetched from http://hitran.org` and `Lines parsed: 199`.

The header preserves standard HITRAN fixed-column semantics and independently confirms that `sw` is abundance-weighted.

However, the path history currently visible in that repository shows the present file entering its current location during a 2024 restructuring commit. That does **not** establish when the HITRAN download itself occurred or which database edition served it.

Therefore this 199-line A-band file is currently only an independent formatting/content witness. It must not be relabelled HITRAN2016 without stronger provenance.

Relevant repository paths:

- https://github.com/innosat-mats/MATS-analysis/blob/1b16746bf030af9b13d1e568033fcd0dfc7ece46/Bjorn/retrieval/1D_full/Abandabs/Abanddata/oxygen.data
- https://github.com/innosat-mats/MATS-analysis/blob/1b16746bf030af9b13d1e568033fcd0dfc7ece46/Bjorn/retrieval/1D_full/Abandabs/Abanddata/oxygen.header

## 10. Other public O2 line fragments are not sufficient provenance

Public GitHub repositories contain O2 line files with recognisable HITRAN records, including A-band lines around 13,000 cm^-1 and files spanning the IRA/A regions. These are useful for cross-checking parsing and individual line identities.

Unless their exact database edition, retrieval process and file identity can be established, they must not be promoted to the `historical_2020` numerical baseline.

In other words, numerical agreement of a few lines is useful validation evidence but is not a substitute for edition provenance.

## 11. Acceptance gate for the HITRAN2016 O2 asset

Before M4D implementation starts, the selected spectroscopy source must satisfy all of the following:

1. provider/archive documented;
2. exact original filename documented;
3. evidence that the bytes/records correspond to HITRAN2016;
4. access/retrieval date recorded;
5. original file SHA-256 recorded where licensing permits local preservation;
6. format documented (prefer standard HITRAN fixed-width records or a transparent lossless extraction);
7. complete O2 record count and isotopologue counts checked against HITRAN2016 publication fingerprints if a full O2 file is used;
8. target-band extraction performed by documented quantum-state rules;
9. extracted band files/subsets receive their own SHA-256 hashes;
10. line counts, isotopologue counts, min/max wavenumber and diagnostic summed strengths are recorded for A, B and IRA;
11. line-reference identifiers and necessary quantum labels are retained;
12. no current HITRAN2024/live-data substitution is hidden inside the source chain.

If licensing prevents committing the original line database, preserve a reproducible source-derived subset when permitted plus source identity/hash/provenance metadata sufficient to audit the extraction. Do not redistribute data contrary to the source licence.

## 12. Decisions that are now close to freeze

Subject to final review against the acquired HITRAN2016 records, the following design choices are now strongly supported:

- select A/B/IRA by electronic/vibrational state labels, not arbitrary wavelength windows;
- start from the three O2 isotopologues represented in the HITRAN2016 O2 line list and retain those that contribute lines to each selected system;
- use standard HITRAN `sw` without an extra isotopic-abundance multiplier;
- use a historical TIPS-2017 numerical source for HITRAN temperature scaling if the full HITRAN convention is adopted;
- preserve Anqi's Doppler-only implementation as a historical methodological anchor, but do not inherit its nonstandard spectral normalization as physics.

The exact numerical spectroscopy asset itself is **not frozen**.

## 13. Next acquisition actions

The next research step should be narrow and practical:

1. inspect the institutional `KSPECTRUM_Htr16` archive for recoverable/pinnable `BD_TIPS_2017_v1p0` material and its licence/provenance;
2. continue searching official/institutional historical HITRAN access routes for a verifiably HITRAN2016 O2 line source;
3. investigate older MATS-analysis history/related repositories for the original creation/fetch of the 199-line A-band file;
4. if no archival raw file is recoverable, identify the appropriate official HITRAN route for obtaining the historical 2016 edition rather than substituting the live edition;
5. only after the line asset is acquired, compute the exact A/B/IRA extraction statistics and freeze the M4D spectroscopy specification.

If these reasonable recovery routes fail, then and only then reassess whether the spectroscopy gate has become a true **SOURCE BLOCKER**.
