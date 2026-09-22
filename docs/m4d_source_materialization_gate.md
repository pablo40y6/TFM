# M4D historical source materialization gate

Status: **OPERATIONAL SOURCE GATE / DESIGN NOT FROZEN / NO IMPLEMENTATION AUTHORIZED**

Branch: `milestone/m4d-design`

This document began as the M4D provenance acquisition checklist. A1/A2/A3 and the historical Maté 1.27-micron CIA numerical source have now passed byte materialization. The remaining work is accepted-HITRAN2016 continuity for the rare A lines plus executable/numerical closure for A/B/IRA; there is no longer an external historical-source byte blocker.

No current HITRAN/HAPI/CIA product may be substituted for a missing historical asset merely to pass this gate.

## 1. Asset A1 — Drouin principal-isotopologue A-band supplement

Authoritative source family:

```text
Drouin et al. (2017)
Multispectrum analysis of the oxygen A-band
JQSRT 186, 118-138
DOI 10.1016/j.jqsrt.2016.03.037
PMC5103325 / NIHMS804415
```

Exact public supplement identity recovered from the article:

```text
NIHMS804415-supplement-supplement_1.pdf
reported size: 94.8 kB
```

Expected scientific content:

- modified line-mixing matrices;
- temperature-dependent Y values;
- PP/RR 18 x 18 and PQ/RQ 17 x 17 matrix families described by the article.

Required local evidence:

```text
retrieval URL/provider
retrieval date
byte size
SHA-256
PDF page count
successful parse/read check
```

Then derive a deterministic machine-readable transcription without modifying the source PDF. Record the transcription algorithm/version and a hash of the derived parameter table. The source PDF itself need not be committed to the repository.

Gate A1: **PASS.** The official Elsevier supplement was materialized as `1-s2.0-S0022407316301108-mmc1.pdf`, 89406 bytes, SHA-256 `12e621d3b5d17e7648d140ea16134e3c04096bd7e47e2c1bb0e2084adeccbb51`, 12 pages. The structured PMC manuscript was also frozen from NCBI E-utilities for deterministic Tables 4/5 extraction.

## 2. Assets A2/A3 — historical rare-isotopologue A-band auxiliaries

Authoritative Harvard/CfA HITRAN2012 archive index:

```text
HITRAN/HITRAN2012/HITRAN2012/By-Molecule/Uncompressed-files/
```

Exact archive identities:

```text
07_A-band_SDF.dat
archive index date: 20-May-2013 10:51
archive index size: 6.1K

07_hit12_0.76mic_Galatry.par
archive index date: 20-May-2013 10:51
archive index size: 46K
```

Scientific lineage:

- Long et al. rare A-band isotopologues;
- HITRAN2012 Galatry profiles;
- air/self Dicke-narrowing parameters in auxiliary fields;
- carried forward as the candidate historical treatment for accepted HITRAN2016 A iso-2/iso-3 lines unless a concrete HITRAN2016 supersession is demonstrated.

Required local evidence for each file:

```text
exact source URL/provider
retrieval date
byte size
SHA-256
line count
encoding/line-ending convention
field-layout summary
```

Required mapping evidence:

- map each accepted A iso-2/iso-3 transition to its auxiliary Galatry/Dicke parameters by deterministic spectroscopic identifiers, not row order alone;
- report unmatched, duplicate, or ambiguous transitions explicitly;
- verify that the accepted HITRAN2016 rare-isotopologue line identities remain consistent with this historical auxiliary representation.

Gate A2/A3: **PASS.** `07_A-band_SDF.dat` and `07_hit12_0.76mic_Galatry.par` were materialized and hashed; the A-band historical mapping is 430/430 with zero unmatched/ambiguous transitions, and all 280 rare target lines carry the auxiliary Dicke fields.

## 3. Asset C1 — historical HITRAN2016 O2-Air 1.27-micron CIA product

Authoritative scientific identity:

```text
HITRAN2016 CIA section
O2-Air
X3Sigma_g-(v=0) -> a1Delta_g(v=0)
source: Mate et al. (1999)
DOI 10.1029/1999JD900824
```

HITRAN2016 explicitly documents the 2012 pair-label error: the Maté air-mixture spectra were accidentally present under the 2012 `O2-O2` label, and the 2016 release corrected their semantics to `O2-Air`. The historical numerical blocks can therefore be recovered byte-for-byte from the surviving HITRAN2012 archive while applying the explicit HITRAN2016 pair-semantic correction. This is a historical recovery witness, not a modern substitution.

Frozen historical source witness:

```text
archive file: O2-O2_2011.cia
bytes:        1938473
SHA-256:      8cc3ecc87bf7a02492b385ecc71abf279b058da853aea768825deb81237d5ee3
```

Recovered Maté 1.27-micron blocks:

```text
253 K: 7450.380..8477.180 cm^-1, 4194 points
       block SHA-256 58366c46162ca55c84aecd8b81bdadc1f5a68a27db0fbbd615a401dcc21f0bfc
273 K: 7500.089..8486.485 cm^-1, 4029 points
       block SHA-256 09a1e93c23004c0b12acf3e9b97fcb44f4bd32872e7ad1c6441225f0ab56b545
296 K: 7450.132..8487.465 cm^-1, 4237 points
       block SHA-256 19bd3c333c56dc9dd90019b57d014a69db420cae139a33a1c470557b1ad78e08
```

Frozen semantics:

- interpret these numerical blocks as `O2-Air` under the explicit HITRAN2016 correction;
- use `n_O2 * n_air` in the CIA optical depth;
- do not add a separate O2-O2 term for the same atmospheric mixture;
- retain the frozen 253/273/296-K interpolation/clamp/envelope policy;
- do not use the post-2016 theoretical low-temperature extension as a historical replacement.

Gate C1: **PASS FOR HISTORICAL SOURCE MATERIALIZATION.** Remaining CIA work is numerical: common-grid/support handling, the declared treatment/sensitivity for small negative experimental samples, and the full twilight `gIRA` sensitivity. See `docs/m4d_ira_cia_materialization_audit.md`.

## 4. Raw HITRAN2016 SpectralCalc export — already available, never redistribute

The user-provided raw export is:

```text
guest1593878592.txt
expected byte size: 2268239
expected SHA-256: 6b4acbc01cb649891f2d8597875c9cd8e4805cfdd4d3b7841c2d18cbf718de12
expected parsed records: 14085
molecule: O2 (7)
```

Accepted semantic subsets:

```text
A   430 lines
B   320 lines
IRA 835 lines
```

This file may be used locally for analysis but must not be committed, copied into documentation, or redistributed.

Before the final numerical closure run, the execution environment must independently recompute its byte size and SHA-256 and fail closed on any mismatch.

## 5. Minimum local acquisition script behavior

A local/Codex source-materialization task may download the public/authorized historical auxiliary assets, but it must not silently alter them. For each asset it must record:

```text
source URL
HTTP/fetch metadata when available
access UTC timestamp
raw byte count
SHA-256
```

It should then place the raw source outside the committed repository or in an explicitly ignored local source cache.

Derived non-redistributive parameter summaries may be committed only if they do not violate the source license and if their provenance is independently reconstructible. When in doubt, commit hashes/mapping statistics/documentation, not source bytes.

## 6. Exact numerical work unlocked by these assets

With A1/A2/A3 and the historical Maté CIA source materialized, execute numerical work in this order:

1. **A iso-1:** reconstruct the Drouin/HITRAN2016 advanced profile and line mixing; validate source normalization and total nonnegative physical absorption.
2. **A iso-2/3:** execute historical Galatry/Dicke treatment and map all accepted rare lines.
3. **B:** execute classic HITRAN2016 Voigt baseline and corrected source-based qSDV sensitivity for covered lines.
4. **IRA:** execute classic HITRAN2016 Voigt baseline.
5. **Pressure shift:** quantify shell-local `delta_air` effect for B/IRA and the recovered advanced A shift convention.
6. **CIA:** execute the historical O2-Air twilight sensitivity with the frozen Maté temperature policy.
7. **Spectral convergence:** target/source quadrature plus all-accepted-lines attenuation for B/IRA; source-appropriate convergence for A.
8. **Spatial convergence:** `0.125 km` baseline versus `0.0625 km` reference.
9. **Full domain:** all 51 target altitudes at SZA `0, 60, 85, 89, 89.9, 95, 99 deg`, plus illuminated tangent and immediately shadowed boundary cases.

Final numerical gate remains:

```text
max relative numerical difference <= 0.1%
for rates above the declared 1e-15 s^-1 diagnostic floor
```

The floor/tolerance may not be loosened silently.

## 7. Stop conditions

Stop and report **SOURCE MATERIALIZATION BLOCKER** rather than changing the science if any of the following occurs:

- a required historical asset cannot be obtained with edition/source identity;
- bytes cannot be hashed reproducibly;
- a mapping has unresolved duplicates/unmatched records;
- the only available asset is a later HITRAN/HAPI/CIA edition;
- the Drouin supplement cannot be converted into an executable representation without an undocumented assumption.

Stop and report **NUMERICAL/DESIGN BLOCKER** if:

- the historically supported candidate profile fails the 0.1% convergence gate;
- corrected B qSDV changes retained B rates by more than 0.1%;
- CIA changes retained IRA rates by more than 0.1% or its historical temperature envelope changes the pass/fail conclusion;
- pressure-shift treatment materially changes results and the historical convention cannot be fixed unambiguously.

## 8. Current gate state

```text
Transition/intensity source          PASS
TIPS-2017 source                     PASS
Wehrli solar source                  PASS
M4C spherical geometry               PASS
Shellwise transfer                    PASS
B baseline profile policy             SELECTED, numerical closure pending
IRA baseline profile policy           SELECTED, numerical closure pending
IRA CIA cold-shell policy             SELECTED, numerical closure pending
A profile families                    IDENTIFIED
A1 exact source bytes                 PASS
A2/A3 exact source bytes              PASS
A historical deterministic mapping    PASS
A isolated-line SDV semantics          SELECTED / frozen equations
A Table-22 Y(T) operational policy     SELECTED / low-T sensitivity pending
C1 historical CIA source/material     PASS via Maté byte witness + HITRAN2016 semantic correction
CIA grid/negative-sample sensitivity   OPEN / numerical closure pending
Full final numerical convergence      OPEN
M4D design                             NOT FROZEN
M4D implementation                    NOT AUTHORIZED
M5                                    NOT AUTHORIZED
```

The source-materialization phase is now substantially closed. The next productive actions are **accepted-HITRAN2016 rare-line continuity plus numerical closure**, including the CIA grid/noise sensitivity. A-band and CIA source acquisition are no longer external blockers.
