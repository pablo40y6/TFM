# M4D principal-isotopologue A-band Drouin materialization audit

Status: **SOURCE BYTES MATERIALIZED / 91/91 MAGNETIC-DIPOLE LBL MAPPING PASS / 70-LINE LM COVERAGE IDENTIFIED / EXECUTABLE PROFILE NOT YET FROZEN**

Branch: `milestone/m4d-design`

This audit records the source materialization and deterministic transition mapping needed for the HITRAN2016 principal-isotopologue A-band update. It does not implement production M4D or authorize M5.

## 1. Official publisher supplementary asset

The Drouin et al. paper is:

```text
Multispectrum analysis of the oxygen A-band
JQSRT 186 (2017) 118-138
DOI 10.1016/j.jqsrt.2016.03.037
PII S0022407316301108
```

The official Elsevier supplementary PDF was acquired reproducibly from:

```text
https://ars.els-cdn.com/content/image/1-s2.0-S0022407316301108-mmc1.pdf
```

Frozen acquisition identity:

```text
bytes:   89406
SHA-256: 12e621d3b5d17e7648d140ea16134e3c04096bd7e47e2c1bb0e2084adeccbb51
format:  PDF 1.6
pages:   12
```

This is the publisher copy corresponding to the PMC supplementary item historically exposed as `NIHMS804415-supplement-supplement_1.pdf`.

The raw publisher PDF is acquisition evidence and is not committed to the repository.

## 2. Structured manuscript source

The NCBI PMC structured manuscript was acquired through E-utilities:

```text
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=5103325
bytes:   310708
SHA-256: 935fd09d5f619f7eb3f7fac5347e80fa81bc23d3158dc9c519874bb161c364fe
format:  XML / UTF-8
```

The XML contains five article tables. Tables 4 and 5 are the line-by-line P- and R-branch parameters used below. This structured source avoids OCR transcription for the principal line parameters.

## 3. Drouin magnetic-dipole LBL table content

Tables 4 and 5 contain, per transition:

```text
quanta
sigma0
I(296 K)
E''
gamma_f, n_f
gamma_s, n_s
delta_f, delta_f'
delta_s, delta_s'
S
```

where `f` and `s` are the Drouin foreign- and self-collision components, and `S` is the speed-dependence parameter. The paper states that speed dependence is applied to the total shifted frequency and Lorentz width after combining the foreign and self components.

The structured tables contain:

```text
Table 4 P branch: 45 transitions
Table 5 R branch: 46 transitions
total:            91 transitions
unique labels:    91
```

A deterministic normalized serialization of the 91 extracted numerical rows has:

```text
UTF-8 bytes: 9015
SHA-256: c4a8040edba2cc824a3fe9de439e855ec360e99ba02b8018368cd622dc8338e2
```

This derived hash is a transcription guard, not a substitute for the publisher/PMC source hashes.

## 4. Exact historical transition mapping

The historical HITRAN2012 O2 A-band principal-isotopologue target set contains:

```text
150 total b(0)-X(0) lines
91 magnetic-dipole lines, local flag d
59 electric-quadrupole lines, local flag q
```

The 91 Drouin Table-4/5 quantum labels map one-to-one to the 91 historical magnetic-dipole labels:

```text
Drouin labels:                 91
unique HITRAN2012 d matches:   91
unmatched Drouin labels:        0
unmatched HITRAN d labels:      0
ambiguous labels:               0
```

Thus Tables 4/5 are not a partial sampling of the magnetic-dipole line list: they cover the complete 91-line principal-isotopologue magnetic-dipole A-band set carried by the historical line list.

The same quantum-identity audit was then executed against the accepted user-provided HITRAN2016 SpectralCalc export. Its A subset contains exactly `150` principal-isotopologue lines split as `91 d + 59 q`. The 91 accepted 2016 `d` labels match the Drouin Tables 4/5 set `91/91`, with zero missing, extra, or duplicate labels. This closes the principal-isotopologue target-edition continuity gate without redistributing the raw export.

The 59 `q` transitions are not part of this Drouin magnetic-dipole update and must not be assigned the Drouin advanced parameters by extrapolation.

## 5. Strength magnitude of the non-Drouin quadrupole lines

Using the historical HITRAN2012 target list as a classification witness:

```text
sum strength, 91 d lines = 2.2313470544e-22
sum strength, 59 q lines = 1.770649e-27
q fraction of iso-1 A    = 0.00079353 %
```

The quadrupole contribution is extremely small in unattenuated integrated strength, but it is not deleted by design. The candidate historical rule is to retain those accepted target-edition lines with their classic profile and verify their actual contribution in the full twilight calculation.

## 6. Line-mixing source materialization

The official supplement contains the abridged self/foreign relaxation-matrix material and its temperature dependence in Tables 6-21, split into four subbands:

```text
PP: 18 x 18
PQ: 17 x 17
RR: 18 x 18
RQ: 17 x 17
```

The supplement states that air line-mixing matrices can be constructed for specific temperature and pressure and diagonalized into first-order line-by-line `Y` factors.

Table 22 supplies those post-diagonalization air `Y` factors explicitly at:

```text
200 K
250 K
296 K
340 K
```

with units `cm^-1 atm^-1`.

Table 22 contains exactly 70 line entries. After translating the supplement's branch-label convention to the HITRAN local-label convention, all 70 map uniquely to Drouin magnetic-dipole transitions.

A normalized serialization of the 70 mapped `(label,Y200,Y250,Y296,Y340)` rows has:

```text
UTF-8 bytes: 2934
SHA-256: e68cdd3ac212453e26860a03502a3f36442eaaaaf4cdeb8c70ce6848290b3973
```

## 7. Line-mixing coverage

The 70 Table-22 entries cover the lower-J magnetic-dipole subset. The 21 magnetic-dipole lines without a Table-22 Y value are:

```text
P37P37, P37Q36,
P39P39, P39Q38,
P41P41, P41Q40,
P43P43, P43Q42,
P45P45, P45Q44,
R35Q36,
R37R37, R37Q38,
R39R39, R39Q40,
R41R41, R41Q42,
R43R43, R43Q44,
R45R45, R45Q46
```

Their historical integrated strength is small:

```text
21 no-Y d-line strength fraction of all d lines:   0.0131465 %
21 no-Y d-line strength fraction of iso-1 A:       0.0131464 %
```

This is below the project's `0.1%` integrated-strength scale but is not sufficient, by itself, to omit their line-shape contribution in strongly attenuated twilight cases.

## 8. Candidate principal-isotopologue profile split

The source evidence now supports this per-transition candidate:

```text
91 magnetic-dipole d lines:
    Drouin SDV parameters from Tables 4/5

70 of those 91 lines:
    + first-order Rosenkranz line mixing using the historical Table-22 Y(T) relation

21 high-J magnetic-dipole lines without Table-22 Y:
    SDV retained; line-mixing coefficient must not be invented
    (candidate Y=0 only after source-semantic and numerical sensitivity confirmation)

59 electric-quadrupole q lines:
    accepted target-edition classic parameters/profile;
    no Drouin advanced parameters copied onto them
```

This split is a source-supported candidate, not yet a final numerical freeze.

## 9. Air/foreign/self semantics must not be conflated

Drouin Tables 4/5 report separate foreign and self components. HITRAN2016 states that for the database's Earth-atmosphere representation the Drouin foreign-broadening parameters were converted to **air-broadening** parameters with the binary ratio `[N2]:[O2] = 0.79:0.21`, and the full foreign/self W matrices were likewise evaluated for one atmosphere of air before conversion to first-order Rosenkranz parameters.

Therefore the resulting HITRAN `air` coefficient is an effective air-diluent coefficient. It must not be treated as if it were an N2-only coefficient and then mixed with 21% `gamma_self` a second time for ordinary atmospheric air.

This finding triggers a correction to the provisional B/IRA pressure-broadening formula elsewhere in the design documents: for the atmospheric baseline, an HITRAN `air` coefficient is applied to the shell's air pressure/composition as the air diluent; `self` is a separate diluent choice for non-air/self-rich mixtures, not a second 21% term to be added on top of an already air-averaged coefficient.

## 10. Remaining A1 design gates

A1 is no longer a byte/source-discovery blocker. Remaining issues are now executable semantics and numerical validation:

1. freeze the exact SDV mathematical evaluator corresponding to Drouin/HITRAN2016, including the mapping of `S` to the adopted SDV width parameterization;
2. freeze the temperature evaluation/interpolation rule for the four Table-22 Rosenkranz `Y` values rather than inventing an interpolation silently;
3. confirm the candidate `Y=0` treatment for the 21 magnetic-dipole lines outside Table 22 from the source semantics and quantify its twilight impact;
4. accepted local HITRAN2016 `91/91` d-line continuity: **PASS** by quantum identity, zero missing/extra/duplicates;
5. retain/test the 59 q lines with target-edition classic parameters;
6. apply identical per-line physical profile semantics in target excitation and shell attenuation;
7. pass the full M4D convergence domain.

## 11. Gate result

```text
Drouin publisher PDF bytes/hash:          PASS
structured PMC XML bytes/hash:            PASS
Tables 4/5 extraction:                    PASS
magnetic-dipole mapping:                  91/91 PASS
Table-22 Y source:                        70 lines PASS
high-J no-Y set:                          21 lines IDENTIFIED
quadrupole non-Drouin set:                59 lines IDENTIFIED
final SDV/Y evaluator semantics:          OPEN
accepted HITRAN2016 local continuity map: 91/91 PASS
full numerical convergence:               OPEN
```

The principal-isotopologue A-band blocker has moved from **source materialization** to **executable parameter semantics + local edition continuity + numerical convergence**.
