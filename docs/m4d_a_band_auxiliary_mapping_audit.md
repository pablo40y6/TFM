# M4D A-band Galatry auxiliary byte and mapping audit

Status: **A2/A3 MATERIALIZED / 430/430 A-BAND MAPPING PASS / DICKE-FIELD SEMANTICS FROZEN**

Branch: `milestone/m4d-design`

This audit records the direct acquisition and deterministic mapping of the historical HITRAN2012 O2 A-band auxiliary files needed for the rare-isotopologue Galatry treatment. It does not implement M4D, alter M4C-R2, or authorize M5.

## 1. Reproducible acquisition

The files were downloaded on a GitHub-hosted Ubuntu runner from the surviving Harvard/CfA HITRAN2012 archive at approximately `2026-09-17T21:06:45Z` UTC.

### A2

```text
filename: 07_A-band_SDF.dat
source: https://lweb.cfa.harvard.edu/HITRAN/HITRAN2012/HITRAN2012/By-Molecule/Uncompressed-files/07_A-band_SDF.dat
bytes: 6229
SHA-256: 7cfefb8040a89cb0e4948c2811a6766b793181646d8188ebfa4d646e063dbd26
format: ASCII text with CRLF line terminators
parsed records: 70
```

The archive directory index reports the same historical file identity and an approximate displayed size of `6.1K`.

### A3

```text
filename: 07_hit12_0.76mic_Galatry.par
source: https://lweb.cfa.harvard.edu/HITRAN/HITRAN2012/HITRAN2012/By-Molecule/Uncompressed-files/07_hit12_0.76mic_Galatry.par
bytes: 47231
SHA-256: 69c9fd181b5aba8aa818dc906bdc216aaa8cf038eb5687dd4da8f2bb9bf42dab
format: ASCII text with CRLF line terminators
records: 489
```

The archive directory index reports the same historical file identity and an approximate displayed size of `46K`.

### Historical full O2 HITRAN2012 line file used for the mapping audit

```text
filename: 07_hit12.par
source: https://lweb.cfa.harvard.edu/HITRAN/HITRAN2012/HITRAN2012/By-Molecule/Uncompressed-files/07_hit12.par
bytes: 2263950
SHA-256: ad2cadf91cb985bec4074ce0bf47cdcfa7aab627ea15de2ac85de731873417a4
format: ASCII text with CRLF line terminators
records: 13975
```

These raw historical files are acquisition evidence. They are not committed to the repository.

## 2. Structure of the Galatry auxiliary file

`07_hit12_0.76mic_Galatry.par` contains:

```text
isotopologue 1 (16O2):    209 records
isotopologue 2 (16O18O):  140 records
isotopologue 3 (16O17O):  140 records
```

Of the 489 total records, exactly 430 belong to the target A-band system `b(v'=0) <- X(v''=0)`:

```text
iso 1: 150
iso 2: 140
iso 3: 140
total: 430
```

This exactly matches the accepted M4D A-subset cardinality.

All `140 + 140` rare-isotopologue records have the two appended Dicke-narrowing fields. HITRAN2012 identifies these last two columns as the air- and self-broadened collisional/Dicke narrowing parameters, respectively, in `cm^-1 atm^-1` at 296 K.

The principal-isotopologue subset makes an additional profile-family distinction explicit in the file layout:

```text
91 local-flag d rows: appended Dicke fields present
59 local-flag q rows: appended Dicke fields absent
```

Thus the historical auxiliary itself does not supply Galatry/Dicke narrowing parameters for the 59 principal-isotopologue electric-quadrupole `q` transitions. Those lines must not be assigned either rare-isotopologue Galatry coefficients or Drouin magnetic-dipole advanced parameters by extrapolation; the source-supported candidate is the accepted target-edition classic profile.

## 3. Deterministic mapping rule

The auxiliary file intentionally omits line position, intensity and lower-state energy. It repeats the molecule/isotopologue identifier, classic broadening/shift fields, global/local quantum identifications and a transition flag, then appends the two Dicke parameters when available.

The mapping audit therefore used the stable spectroscopic identity:

```text
molecule/isotopologue
+ global upper quantum label
+ global lower quantum label
+ local upper quantum label
+ local lower quantum label
```

The repeated numerical broadening fields were **not** required as part of the identity key.

Result for target `b(0)-X(0)`:

```text
auxiliary target rows: 430
unique matches in 07_hit12.par: 430
unmatched: 0
ambiguous: 0
```

By isotopologue:

```text
iso 1: 150 / 150
iso 2: 140 / 140
iso 3: 140 / 140
```

This closes the historical HITRAN2012 line-to-Galatry-auxiliary mapping itself.

## 4. Redundant-field discrepancies discovered

When the auxiliary's repeated classic fields were compared against the matched `07_hit12.par` records, the following were found:

```text
n_air differences:       0
gamma_air differences:   4
gamma_self differences:  2
delta_air differences:   2
```

The affected cases are localized and have the pattern of swapped/older redundant values rather than identity failures. Examples include neighboring `16O17O` R-branch transitions whose `gamma_air`/`gamma_self` values are exchanged between the auxiliary representation and the final 160-character HITRAN2012 line file, plus two `16O2` R-branch pressure shifts exchanged between neighboring quantum assignments.

These differences demonstrate why the redundant numerical fields must not be used as the mapping key.

## 5. Frozen parameter-precedence rule

HITRAN2012 states that the purpose of the final two columns in the auxiliary A-band input file is to provide the Galatry/Dicke narrowing parameters, while the standard HITRAN line list carries the normal line position/intensity/broadening/shift fields.

Therefore the M4D historical rare-isotopologue rule is:

```text
line position, intensity, lower-state energy,
gamma_air, gamma_self, n_air, delta_air:
    use the accepted historical HITRAN line record for the target edition

Dicke narrowing air/self coefficients:
    use the final two columns of the quantum-identity-matched
    07_hit12_0.76mic_Galatry.par record
```

Do **not** overwrite a final HITRAN line's classic broadening/shift fields with the auxiliary's redundant copies.

For the actual M4D `historical_2020` run, the accepted HITRAN2016 SpectralCalc target record remains authoritative for the classic line fields; the 2012 auxiliary supplies only the historically documented Dicke coefficients for iso-2/iso-3. This is consistent with HITRAN2016 documenting the Drouin replacement for the principal isotopologue while retaining the Long-lineage rare-isotopologue target systems.

## 6. Rare-isotopologue parameter coverage

The mapped historical rare-line auxiliary provides complete Dicke coverage:

```text
16O18O: 140/140 lines with air+self Dicke coefficients
16O17O: 140/140 lines with air+self Dicke coefficients
```

Observed coefficient ranges in the historical auxiliary are approximately:

```text
16O18O:
  Dicke-air  0.0067 .. 0.0203 cm^-1 atm^-1
  Dicke-self 0.0062 .. 0.0168 cm^-1 atm^-1

16O17O:
  Dicke-air  0.0069 .. 0.0209 cm^-1 atm^-1
  Dicke-self 0.0064 .. 0.0173 cm^-1 atm^-1
```

These ranges are evidence/validation anchors, not replacements for the per-line values.

## 7. Remaining HITRAN2016 continuity check

The historical auxiliary mapping to HITRAN2012 is closed. Before production M4D implementation, the local execution environment must still map the accepted HITRAN2016 SpectralCalc iso-2/iso-3 A lines to these auxiliary rows using the same quantum-identity key and report:

```text
expected: 280 mappings
unmatched: 0
ambiguous: 0
```

Because the accepted raw SpectralCalc source is intentionally not committed, this final edition-continuity check belongs in the local source-materialization/implementation evidence rather than in the repository source tree.

No profile-family ambiguity remains: failure of the 280-line continuity check is a SOURCE/MAPPING BLOCKER, not permission to copy Drouin iso-1 parameters to the rare isotopologues.

## 8. Gate result

```text
A2 exact bytes/hash:                       PASS
A3 exact bytes/hash:                       PASS
07_hit12.par audit witness:                PASS
HITRAN2012 target A mapping:               430/430 PASS
Rare Dicke coverage:                       280/280 PASS
Principal q Dicke coverage:                 0/59 by source design; classic-profile candidate
Auxiliary parameter-precedence semantics:  FROZEN
Accepted HITRAN2016 principal d continuity: 91/91 PASS
Accepted HITRAN2016 rare continuity map:    pending local raw-source check
```

A2/A3 are no longer source-materialization blockers. The remaining A-band external blocker is principally A1: the Drouin principal-isotopologue advanced parameterization, plus the final local HITRAN2016 continuity check and numerical convergence.
