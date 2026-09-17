# M4D HITRAN2016 acquisition and band-selection gate

Status: **DRAFT EVIDENCE / DESIGN NOT FROZEN**

Branch: `milestone/m4d-design`

This note records the current evidence-backed spectroscopy design for M4D. It does not authorize M4D coding and does not reopen M1-M4C-R2.

## 1. Current outcome

The physical definition of the three required O2 bands, the isotopologue convention and the historical TIPS-2017 route are now substantially constrained. A concrete historical line-list acquisition route has also been identified through SpectralCalc.

The exact numerical O2 HITRAN2016 transition asset has **not yet been retrieved and frozen**, so M4D remains:

**DESIGN NOT FROZEN / NOT IMPLEMENTED.**

A present-day live HITRANonline download must not be used as a silent replacement for the required historical edition.

## 2. Canonical O2 identity and corrected HITRAN2016 fingerprints

HITRAN assigns molecular oxygen molecule number `7`.

HITRAN2016 Table 3 reports three O2 isotopologues in the line-by-line database. The correct HITRAN2016 fingerprints are:

| local iso | HITRAN isotopologue code | isotopologue | HITRAN2016 line count | HITRAN2016 spectral coverage (cm^-1) |
| --- | --- | --- | ---: | ---: |
| 1 | 66 | 16O2 | 15,263 | 0-57,028 |
| 2 | 68 | 16O18O | 2,965 | 1-56,670 |
| 3 | 67 | 16O17O | 11,313 | 0-14,537 |

### Correction record

An earlier draft of this note incorrectly paired the **HITRAN2012** coverage values `0-15,928`, `1-15,853`, `0-14,538 cm^-1` with the HITRAN2016 counts. Table 3 contains adjacent columns for HITRAN2012 and HITRAN2016, which caused the transcription error.

The counts `15,263 / 2,965 / 11,313` were already correct; the full-range HITRAN2016 coverage for isotopologues 1 and 2 extends to about `57,000 cm^-1`.

This correction affects the preferred full-dataset acquisition/fingerprint test, but does not change the M4D target A/B/IRA systems, all of which lie below about `15,000 cm^-1`.

Primary source:

- Gordon et al. (2017), *The HITRAN2016 Molecular Spectroscopic Database*, JQSRT 203, 3-69, Table 3, DOI `10.1016/j.jqsrt.2017.06.038`.
- https://hitran.org/media/refs/HITRAN-2016.pdf

SpectralCalc's HITRAN2016 abundance table independently identifies O2 molecule 7 local isotopologues 1-3 as `16O2`, `16O18O` and `16O17O`:

- https://spectralcalc.com/calc/abundances.php

## 3. Natural-abundance convention: do not double-weight isotopologues

HITRAN line intensity `sw` uses the terrestrial natural isotopic abundance convention. The official HITRAN documentation describes line intensities as abundance-scaled, and SpectralCalc explicitly explains the same convention.

An independent MATS/HAPI header preserved in `innosat-mats/MATS-analysis` states:

> `sw`: "Line intensity, multiplied by isotopologue abundance, at T = 296 K"

Therefore, if M4D consumes standard HITRAN line strengths and a bulk O2 number density under the terrestrial isotopic convention, it must **not multiply `sw` by isotopologue abundance a second time**.

Sources:

- https://hitran.org/docs/definitions-and-units/
- https://www.spectralcalc.com/info/help.php
- https://github.com/innosat-mats/MATS-analysis/blob/1b16746bf030af9b13d1e568033fcd0dfc7ece46/Bjorn/retrieval/1D_full/Abandabs/Abanddata/oxygen.header

This rule must be rechecked if a transformed line source is used instead of a standard HITRAN-style export.

## 4. Semantic band selection: quantum labels, not acquisition windows

The required physical target systems are:

- `gA`: O2(X, v''=0) -> O2(b, v'=0), atmospheric A band near 762 nm;
- `gB`: O2(X, v''=0) -> O2(b, v'=1), atmospheric B band near 688 nm;
- `gIRA`: O2(X, v''=0) -> O2(a, v'=0), infrared atmospheric system near 1.27 micron.

The robust selection rule should use the HITRAN global electronic/vibrational labels:

```text
gA   : upper b(v'=0), lower X(v''=0)
gB   : upper b(v'=1), lower X(v''=0)
gIRA : upper a(v'=0), lower X(v''=0)
```

The exact fixed-width strings must be derived from the acquired HITRAN2016 records before implementation.

Do not define the physical systems using only hard-coded wavelength or wavenumber windows. Windows may be used for acquisition convenience and diagnostics, but the final frozen subsets must be generated from the state labels.

## 5. Diagnostic spectral regions

Historical/independent implementations suggest approximate diagnostic regions:

- `a(0) <- X(0)` / IRA: around 1.27 micron, roughly `7,700-8,100 cm^-1`;
- `b(0) <- X(0)` / A: around `12,900-13,300 cm^-1` depending on how completely weak/hot neighboring transitions are represented;
- `b(1) <- X(0)` / B: roughly `14,300-14,600 cm^-1`.

These ranges are deliberately broader than some legacy model grids. They are not frozen selectors.

The public MATS A-band notebook provides a useful independent example: after fetching approximately 749-776 nm for principal `16O2`, it selects upper global state `b, v=0` and obtains records spanning `12892.859666-13339.201391 cm^-1`.

This independently demonstrates why Anqi's narrower `12900-13170 cm^-1` grid should not be promoted to the definition of the complete A system.

## 6. Isotopologue policy

Begin from all three O2 isotopologues represented in the HITRAN2016 line-by-line database and then apply the semantic band filters.

For each target system record:

- contributing isotopologues;
- line count by isotopologue;
- min/max wavenumber by isotopologue;
- summed reference-temperature `sw` by isotopologue as a diagnostic;
- retained HITRAN reference identifiers (`iref`) and relevant uncertainty codes.

Do not invent line transitions for additional O2 isotopic species merely because TIPS-2017 provides partition sums for more isotopologues. TIPS coverage and line-list coverage are separate concepts.

## 7. TIPS-2017 historical route

The TIPS part of the provenance gate is now much stronger than it was in the first draft of this note.

A strong freeze candidate has been identified:

- repository: `sergio66/UMBC_LBL`;
- commit: `2cde4f679a1398403d6bd5ced4b130be7055d33f`;
- path: `Global_Data_HITRAN2016/ORIG/BD_TIPS_2017_v1p0.for`;
- Git blob SHA-1: `525350fef5305a02c6708b9111c8b6b63e4b97de`;
- repository-reported size: `9,603,971` bytes.

Independent witnesses include the official `hitranonline/hapi` historical TIPS-2017 commit and a preserved `BD_TIPS_2017_v1p0.zip` in `HUyoshis/Radmodel`, plus the TU Berlin `KSPECTRUM_Htr16` archive.

Full evidence and the pending local SHA-256 / numerical cross-check procedure are recorded in:

- `docs/m4d_tips2017_provenance_recovery.md`

TIPS-2017 should therefore be treated as **provenance recovered, freeze candidate identified**, not as the main remaining M4D blocker.

## 8. Canonical historical line-list identity witnesses

Several independent scientific software projects refer to a historical file explicitly named `HITRAN2016.par` or `hitran2016.par`:

- Oxford RFM/HITBIN documentation demonstrates conversion of `HITRAN2016.par` and records a September 2017 parser change specifically required for HITRAN2016;
- VPL modeling scripts point to `HITRAN_Data/HITRAN2016.par` and request HITRAN2016 `.par` format;
- NOAA-GFDL workflows refer to `HITRAN_files/hitran2016.par`.

Oxford reference:

- https://eodg.atm.ox.ac.uk/RFM/hitbin.html

These sources prove the historical workflow/file identity but do not expose the complete historical line bytes for us to freeze.

## 9. SpectralCalc is now the primary acquisition candidate

SpectralCalc explicitly announced adding the HITRAN2016 line list on 20 August 2018. Its current Line List Browser documentation states that users can download complete line-list datasets or selected molecules/wavebands, and its Extract Data page supports spectral ranges up to `60,000 cm^-1`.

Sources:

- https://spectralcalc.com/info/news.php
- https://www.spectralcalc.com/info/help.php
- https://www.spectralcalc.com/spectral_browser/db_data.php
- https://www.spectralcalc.com/info/glossary.php

A 2024 peer-reviewed JQSRT study by Gava, Costa and Sena explicitly reports obtaining its HITRAN2016 parameters from SpectralCalc on 11 March 2024. Its public RFM reproduction script points to a local file named `hitran2016-spectralcalc.bin`.

Evidence is recorded in:

- `docs/m4d_hitran2016_line_source_recovery.md`
- `docs/m4d_spectralcalc_2024_reproduction_witness.md`

This makes SpectralCalc the current primary acquisition route, but not yet the accepted source: the actual bytes still have to be retrieved, hashed and checked.

## 10. MATS and other public O2 fragments are validation witnesses only

The public MATS repository contains a 199-line principal-isotopologue A-band download fetched from hitran.org. It is useful for:

- fixed-column semantics;
- A-band quantum-label behavior;
- independent record spot-checks;
- exposing an abundance-handling quirk that M4D must not copy.

Its public history does not prove which HITRAN edition generated the file, so it is not the historical numerical source.

Likewise, miscellaneous public O2 line files may be used for record-level comparisons but must not be relabeled HITRAN2016 without edition provenance.

## 11. Required full-O2 acquisition and acceptance gate

Preferred SpectralCalc extraction:

```text
Line list        : HITRAN2016
Molecule         : O2 / molecule 7
Isotopologues    : all line-list isotopologues
Intensity cutoff : 0 / least restrictive exact option
Spectral range   : 0-57028 cm^-1 for a complete O2 fingerprint if service limits permit
Output            : transition-level line data
Preferred format : standard HITRAN fixed-width format
```

If one full export is not possible, use lossless non-overlapping chunks covering the same interval. Preserve/hash every original chunk before concatenation.

Before M4D implementation starts, the accepted source must have:

1. provider/archive documented;
2. exact selected edition documented as HITRAN2016;
3. original filename(s) and retrieval date recorded;
4. SHA-256 and byte size for every original source file;
5. format/field mapping documented;
6. full O2 line counts checked as `15263 / 2965 / 11313` if complete coverage is acquired;
7. HITRAN2016 spectral coverage checked as `0-57028 / 1-56670 / 0-14537 cm^-1` for local isotopologues 1/2/3;
8. A/B/IRA extraction generated by quantum-state rules;
9. hashes for each frozen source-derived band subset;
10. line counts, isotopologue counts, min/max wavenumber and diagnostic summed strengths recorded for A/B/IRA;
11. quantum labels, `iref` and other provenance-rich fields retained;
12. no current HITRAN2024/live-data substitution hidden in the source chain.

If licensing prevents committing the raw line data, keep the exact bytes locally and commit the source identity, retrieval procedure and cryptographic hashes. Do not redistribute contrary to provider terms.

## 12. Decisions close to freeze

Subject to final review against the acquired HITRAN2016 records, the following choices are strongly supported:

- select A/B/IRA by electronic/vibrational state labels;
- consider all three O2 isotopologues present in the HITRAN2016 line list before quantifying whether minor isotopologues can be neglected;
- use standard HITRAN `sw` without an extra isotopic-abundance multiplier;
- use a frozen historical TIPS-2017 source for line-strength temperature scaling;
- preserve Anqi's Doppler-only treatment as a historical methodological anchor, while independently validating normalization and source conventions;
- preserve the original spectroscopy export separately from any later RFM/HITBIN or project-specific conversion.

The exact numerical line asset itself is **not frozen**.

## 13. Next action

The research phase has reached a practical acquisition boundary.

The next decisive step is to retrieve a SpectralCalc **HITRAN2016 O2 transition-level export** using the configuration above. Once the bytes are available, immediately run the forensic acceptance checks, derive the A/B/IRA subsets and record their hashes/statistics.

Until that happens:

- do not implement M4D;
- do not use current HITRAN2024 as historical data;
- do not advance to M5.
