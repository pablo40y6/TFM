# M4D TIPS-2017 provenance recovery

Status: **DRAFT EVIDENCE / TIPS-2017 FREEZE CANDIDATE**

Branch: `milestone/m4d-design`

This note narrows the TIPS-2017 part of the M4D spectroscopy provenance gate. It does not authorize M4D implementation and does not resolve the still-open HITRAN2016 O2 line-list acquisition gate.

## 1. Current conclusion

TIPS-2017 is no longer the main historical-source blocker for M4D.

A near-contemporaneous scientific repository preserves an `ORIG` copy of `BD_TIPS_2017_v1p0.for` explicitly inside a `Global_Data_HITRAN2016` tree, with accompanying documentation tracing the working copy to an institutional `/asl/data/hitran/H2016/QTIPS` directory. Independent official and institutional witnesses are also available.

The strongest current freeze candidate is:

- repository: `sergio66/UMBC_LBL`
- repository commit: `2cde4f679a1398403d6bd5ced4b130be7055d33f`
- commit date: 2018-07-07 UTC
- path: `Global_Data_HITRAN2016/ORIG/BD_TIPS_2017_v1p0.for`
- Git blob SHA-1: `525350fef5305a02c6708b9111c8b6b63e4b97de`
- repository-reported size: `9,603,971` bytes

This is a **freeze candidate**, not yet the final locally frozen M4D asset. A local byte copy and SHA-256 are still required before the numerical input is accepted.

## 2. Why the UMBC copy is strong provenance evidence

The UMBC repository contains a dedicated `Global_Data_HITRAN2016` directory and an `ORIG` subdirectory with preserved TIPS files, including:

- `BD_TIPS_2017_v1p0.for`;
- `TIPS_2017_v1p0.for`;
- `BD_ISO_2016.for`;
- `BD_MOL_2016.FOR`.

The repository's H2016 setup documentation states that the local TIPS material was taken from:

```text
/asl/data/hitran/H2016/QTIPS
```

and separately documents unpacking:

```text
QTpy.zip
TIPS_2017_v1p0.zip
BD_TIPS_2017_v1p0.zip
```

The same documentation describes the surrounding workflow as getting `H2016` running and refers to HITRAN2016 by-gas line directories and HITRAN molecular/isotopic metadata.

The `ORIG` path is important because the same repository also documents later local adaptations of the TIPS code for UMBC interfaces. For M4D provenance, the `ORIG/BD_TIPS_2017_v1p0.for` bytes are therefore preferable to the adapted working copy.

Stable witnesses:

- https://github.com/sergio66/UMBC_LBL/tree/2cde4f679a1398403d6bd5ced4b130be7055d33f/Global_Data_HITRAN2016/ORIG
- https://github.com/sergio66/UMBC_LBL/blob/2cde4f679a1398403d6bd5ced4b130be7055d33f/Readme_make_new_qtipsH16
- https://github.com/sergio66/UMBC_LBL/blob/2cde4f679a1398403d6bd5ced4b130be7055d33f/Global_Data_HITRAN2016/Readme

## 3. Independent official HAPI witness

The official `hitranonline/hapi` Git history independently records:

- commit `2a12552364f0ac93e3f3bdfa7b3a9701a45d446b`;
- date: 2018-05-08 UTC;
- message: `Added partition sums from TIPS-2017`.

This gives an official HITRAN-controlled, date-pinned implementation witness only months after the TIPS-2017/HITRAN2016 publications.

The immediately following historical commit:

- `f41d9911f2631eed51b96d6c617b4f27786ad477`;
- message: `Added custom extension support for datafiles and fixed I=(2,0) in TIPS-2017`.

The explicitly named `(2,0)` correction concerns molecule number 2, whereas O2 is HITRAN molecule 7. This makes that named correction non-O2-specific. Nevertheless, the full file changed substantially between those commits, so M4D must not infer byte identity from the commit message alone. The O2 partition sums should be cross-checked numerically between the selected historical source and the official HAPI history.

Stable witnesses:

- https://github.com/hitranonline/hapi/commit/2a12552364f0ac93e3f3bdfa7b3a9701a45d446b
- https://github.com/hitranonline/hapi/commit/f41d9911f2631eed51b96d6c617b4f27786ad477

## 4. Independent recovery of the original HITRAN supplemental ZIP

A second scientific repository, `HUyoshis/Radmodel`, preserves both the acquisition instructions and a binary copy of the historical supplemental archive.

Its README records the original retrieval command:

```text
wget http://hitran.org/suppl/TIPS/BD_TIPS_2017_v1p0.zip
```

and an alternative author-hosted TIPS-2017 route at Robert Gamache's UML page.

The repository currently preserves:

- path: `lbl_k-dist/src_common/TIPS_2017.org/downloaded/BD_TIPS_2017_v1p0.zip`;
- Git blob SHA-1: `306f0ad21a2b931607f58c78ffcf97f865850e9d`;
- repository-reported size: `1,367,428` bytes.

The ZIP itself entered that Git repository in 2024, so the Git commit date is not primary evidence of the archive's original publication date. Its value is instead that the exact filename and historical HITRAN supplemental download URL are preserved alongside the binary archive.

The repository also contains a transformed `BD_TIPS_2017.f`. Its transformation script only adjusts include-file capitalization/name compatibility and splits long Fortran lines before compilation. Therefore this transformed source is useful as an independent numerical cross-check, but it should not replace an original preserved source when one is available.

Stable witnesses:

- https://github.com/HUyoshis/Radmodel/blob/5e501894a336b5304936fd8473b630a6286249fa/lbl_k-dist/src_common/TIPS_2017.org/README
- https://github.com/HUyoshis/Radmodel/blob/5e501894a336b5304936fd8473b630a6286249fa/lbl_k-dist/src_common/TIPS_2017.org/downloaded/BD_TIPS_2017_v1p0.zip
- https://github.com/HUyoshis/Radmodel/blob/5e501894a336b5304936fd8473b630a6286249fa/lbl_k-dist/src_common/TIPS_2017.org/modify_programs.sh

## 5. Independent institutional archive

TU Berlin's DepositOnce archive `KSPECTRUM_Htr16` provides another institutional witness. Its metadata explicitly states that the package uses the HITRAN 2016 line list and includes the updated total internal partition sums `BD_TIPS_2017_v1p0` from R. Gamache.

- DOI: `10.14279/depositonce-10054`
- issued: 2020-05-19
- institutional repository: Technische Universitaet Berlin / DepositOnce

This is not required to become the numerical TIPS source, but it independently supports the pairing of HITRAN2016 spectroscopy with `BD_TIPS_2017_v1p0`.

## 6. Relation to the TIPS-2017 publication

Gamache et al. (2017), JQSRT 203, 70-87, documents the TIPS generation associated with the HITRAN2016 era and the corresponding standalone/program products. The recovered Fortran source header identifies R. R. Gamache and records a last-change date of 27 June 2017.

The recovered program supports six O2 isotopologues in its TIPS tables. This must not be confused with the HITRAN2016 O2 line-list coverage, which contains three O2 isotopologues in the line-by-line database. Partition-sum coverage and transition-list coverage are separate concepts.

Primary publication:

- Gamache et al. (2017), DOI `10.1016/j.jqsrt.2017.03.045`.

## 7. Proposed TIPS-2017 freeze procedure

Before M4D coding, perform the following narrow acceptance procedure:

1. Obtain the exact bytes of the UMBC `ORIG/BD_TIPS_2017_v1p0.for` freeze candidate at commit `2cde4f...`.
2. Record its local filename, source URL, access date, byte size and SHA-256.
3. Preserve either the original file locally when licensing permits or an auditable provenance manifest plus an exact retrieval procedure.
4. Extract/evaluate the O2 partition sums required by the O2 line isotopologues actually selected from HITRAN2016.
5. Compare representative O2 `Q(T)` values over the mesospheric temperature range against the historical official HAPI TIPS-2017 implementation from commit `2a125...` and, where practical, the independently recovered Radmodel copy.
6. Verify the 296 K values against the HITRAN2016-era molecular/isotopic metadata used by the historical source.
7. Record the numerical comparison and hashes in the M4D provenance manifest.
8. Freeze the exact interpolation convention used by M4D rather than depending on a mutable external HAPI installation at runtime.

No present-day TIPS table or current HAPI default should silently replace this frozen historical source.

## 8. What this resolves and what it does not

This evidence is sufficient to change the working assessment from "TIPS-2017 historical source uncertain" to:

**TIPS-2017 PROVENANCE RECOVERED — FREEZE CANDIDATE IDENTIFIED; LOCAL SHA-256/NUMERICAL CROSS-CHECK PENDING.**

It does **not** close the M4D spectroscopy gate as a whole.

The remaining critical acquisition problem is the exact HITRAN2016 O2 transition line list. We still need a machine-readable O2 line source whose edition is demonstrably HITRAN2016, after which the A/B/IRA subsets can be selected by quantum labels and frozen with line counts, ranges and hashes.

Therefore:

- do not implement M4D yet;
- do not use a live/current HITRANonline download as a historical substitute;
- do not advance to M5;
- focus the next acquisition effort on the HITRAN2016 O2 line bytes.