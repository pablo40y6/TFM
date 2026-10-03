# M4D TIPS-2017 provenance recovery

Status: **HISTORICAL SOURCE SELECTED / NUMERICAL BASELINE PINNED / LOCAL DERIVED-ASSET HASH PENDING**

Branch: `milestone/m4d-design`

This note closes the source-selection part of the TIPS-2017 gate for M4D. It does not authorize M4D implementation by itself and does not advance M5.

## 1. Selected historical TIPS-2017 baseline

The primary numerical source for M4D temperature scaling is now the official historical HITRAN/HAPI implementation at the post-fix commit:

- repository: `hitranonline/hapi`
- commit: `f41d9911f2631eed51b96d6c617b4f27786ad477`
- path: `hapi/hapi.py`
- Git blob SHA-1: `caeab1bfaa278b5420adef7efe7ab566991ba763`
- blob size: `1,204,196` bytes
- embedded HAPI version: `1.1.0.8.2`

The source's own changelog states:

```text
ADDED TIPS-2017 (ver. 1.1.0.8)
FIXED LINK TO (2,0) ISOTOPOLOGUE IN TIPS-2017 (ver. 1.1.0.8.2)
```

The same source cites Gamache et al. (2017), JQSRT 203, 70-87, DOI `10.1016/j.jqsrt.2017.03.045`, as the TIPS-2017 reference.

This is preferred as the primary M4D source because it is official HITRAN-controlled code, source-control pinned, contemporaneous with HITRAN2016/TIPS-2017, and contains the numerical partition-sum tables directly.

Stable source:

- https://github.com/hitranonline/hapi/blob/f41d9911f2631eed51b96d6c617b4f27786ad477/hapi/hapi.py

## 2. Why the post-fix commit is selected

The preceding official commit

`2a12552364f0ac93e3f3bdfa7b3a9701a45d446b`

was committed on 2018-05-08 with message `Added partition sums from TIPS-2017`.

The selected follow-up commit `f41d9911...` fixes the `(2,0)` TIPS-2017 link and adds data-file extension support. HITRAN molecule 2 is CO2, whereas molecular oxygen is molecule 7. The named correction is therefore not an O2 key, but using the post-fix snapshot avoids deliberately pinning a known-bug revision.

No current/default HAPI installation is used at runtime as a mutable TIPS source.

## 3. Exact O2 TIPS-2017 temperature grid

For the three O2 line-list isotopologues needed by M4D, the selected HAPI source assigns the same TIPS-2017 temperature grid `TIPS_2017_ISOT[5]`.

The grid begins at 1 K, then 20 K, and proceeds in 20 K increments through the documented table range. This fully covers the accepted mesospheric temperature profile used by the project (~185-265 K on the 50-100 km chemistry grid).

M4D will use the historical table through an explicit frozen interpolation rule rather than calling a mutable external HAPI install.

## 4. Numerical O2 anchors from the selected historical source

The following exact table values are transcribed from the pinned HAPI source and serve as regression anchors.

### HITRAN molecule 7, local isotopologue 1: 16O2

| T (K) | Q(T) |
| ---: | ---: |
| 200 | 145.9015 |
| 220 | 160.4275 |
| 240 | 174.9609 |
| 260 | 189.5058 |
| 280 | 204.0679 |
| 300 | 218.6540 |
| 320 | 233.2724 |

The beginning of the table is `Q(1 K)=1.259272`, `Q(20 K)=15.41160`, `Q(40 K)=29.84283`.

### HITRAN molecule 7, local isotopologue 2: 16O18O

| T (K) | Q(T) |
| ---: | ---: |
| 200 | 307.2954 |
| 220 | 338.0581 |
| 240 | 368.8395 |
| 260 | 399.6500 |
| 280 | 430.5039 |
| 300 | 461.4188 |

The beginning of the table is `Q(1 K)=3.562445`, `Q(20 K)=30.92123`, `Q(40 K)=61.51168`.

### HITRAN molecule 7, local isotopologue 3: 16O17O

| T (K) | Q(T) |
| ---: | ---: |
| 200 | 1794.512 |
| 220 | 1974.123 |
| 240 | 2153.834 |
| 260 | 2333.703 |
| 280 | 2513.805 |
| 300 | 2694.239 |

The beginning of the table is `Q(1 K)=20.92314`, `Q(20 K)=180.8102`, `Q(40 K)=359.4239`.

These values must be reproduced by any derived M4D TIPS asset.

## 5. Secondary archival cross-checks

### UMBC historical HITRAN2016 tree

A near-contemporaneous scientific repository independently preserves the original Fortran product:

- repository: `sergio66/UMBC_LBL`
- commit: `2cde4f679a1398403d6bd5ced4b130be7055d33f`
- date: 2018-07-07 UTC
- path: `Global_Data_HITRAN2016/ORIG/BD_TIPS_2017_v1p0.for`
- Git blob SHA-1: `525350fef5305a02c6708b9111c8b6b63e4b97de`
- repository-reported size: `9,603,971` bytes

The surrounding repository documentation traces its H2016 TIPS material to `/asl/data/hitran/H2016/QTIPS`.

This copy is retained as an independent archival witness and future numerical cross-check rather than the primary runtime/frozen source.

### Recovered original supplemental ZIP

`HUyoshis/Radmodel` preserves the original retrieval URL and a copy of `BD_TIPS_2017_v1p0.zip`:

- blob SHA-1: `306f0ad21a2b931607f58c78ffcf97f865850e9d`
- size: `1,367,428` bytes

Its README records the historical URL `http://hitran.org/suppl/TIPS/BD_TIPS_2017_v1p0.zip`.

### Institutional archive

TU Berlin DepositOnce `KSPECTRUM_Htr16`, DOI `10.14279/depositonce-10054`, independently documents pairing HITRAN2016 with `BD_TIPS_2017_v1p0`.

## 6. Frozen M4D usage convention

For each HITRAN line at temperature `T`, M4D will use the standard HITRAN line-intensity temperature scaling with the partition-sum ratio from this historical TIPS-2017 baseline. The exact mathematical formula, constants, stimulated-emission factor and interpolation implementation will be written into the final M4D design specification before coding.

The partition function for each line is selected by its HITRAN local isotopologue ID. Standard HITRAN `sw` values are already terrestrial-natural-abundance weighted; no additional isotope-abundance multiplier is introduced.

The interpolation must be deterministic and covered by tests at exact tabulated temperatures and intermediate mesospheric temperatures.

## 7. Materialization requirement before closure

During M4D implementation, derive a compact project asset containing only the TIPS-2017 O2 data required for local isotopologues 1-3, together with:

- source repository/commit/path/blob identity;
- exact source table points used;
- deterministic extraction script;
- project asset SHA-256;
- tests against the numerical anchors above;
- an independent check against the archived Fortran copy where practical.

The project need not depend on HAPI at runtime.

## 8. Gate decision

The TIPS-2017 source/provenance question is now:

**PASS — historical source selected and numerical O2 baseline pinned.**

The remaining work is reproducible materialization and implementation testing, not source discovery.

This closes the historical TIPS-2017 source risk for M4D. It does not by itself freeze the overall M4D design; solar forcing, line shape/broadening, geometry, CIA handling, numerical convergence and final validation criteria remain separate gates.