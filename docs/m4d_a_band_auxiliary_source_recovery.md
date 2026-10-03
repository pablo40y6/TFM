# M4D A-band auxiliary line-shape source recovery

Status: **SOURCE FAMILY AND HISTORICAL FILE IDENTITIES RECOVERED / BYTE HASHES PENDING**

Branch: `milestone/m4d-design`

This note narrows the remaining A-band provenance gate. It does not implement M4D, redistribute HITRAN line data, modify accepted M4C-R2 behavior, or authorize M5.

## 1. Why a separate A-band source note is necessary

The accepted SpectralCalc HITRAN2016 export provides the classic 160-character transition records required to identify the three M4D systems and reproduce their line strengths. It does not contain the complete auxiliary/relational information needed for the historically intended A-band line shape.

The historical sources show that the principal and rare A-band isotopologues must not be treated identically.

## 2. Principal isotopologue in HITRAN2016

Gordon et al. (2017), HITRAN2016 Section 2.7.2, states that the HITRAN2012 A-band line list originated from Long et al. and that HITRAN2016 introduced an update specifically for the **principal isotopologue magnetic-dipole allowed transitions** based on Drouin et al. (2017), DOI `10.1016/j.jqsrt.2016.03.037`.

The Drouin/HITRAN2016 principal-isotopologue representation includes:

- speed-dependent Voigt line shape;
- collisional line mixing;
- a full W-matrix in the native Drouin model;
- HITRAN-facing first-order Rosenkranz line-mixing parameters derived from scaled W matrices;
- pressure-shift and temperature-dependent line-shape information;
- CIA represented as a separate component rather than an arbitrary resonant-line far wing.

The public manuscript record is:

```text
PubMed Central: PMC5103325
NIHMSID:        NIHMS804415
article:        Multispectrum analysis of the oxygen A-band
DOI:            10.1016/j.jqsrt.2016.03.037
```

Its supplemental material is identified as:

```text
NIHMS804415-supplement-supplement_1.pdf
reported size: 94.8 kB
```

The article states that the supplement contains the modified line-mixing matrices and temperature-dependent `Y` values. The retained submatrices are described as:

```text
PP  18 x 18
RR  18 x 18
PQ  17 x 17
RQ  17 x 17
```

The source is therefore identified, but its bytes and SHA-256 have not yet been materialized in the project environment. The exact Drouin-native to HITRAN2016 Rosenkranz conversion must also be frozen before implementation.

## 3. Rare isotopologues: HITRAN2012 Galatry lineage retained into HITRAN2016 target lines

The HITRAN2016 wording is important: it says the HITRAN2012 A-band line list originated from Long et al. and then describes a new Drouin update of the **principal isotopologue**. It does not describe an equivalent Drouin replacement for the accepted `16O18O` and `16O17O` A-band systems.

HITRAN2012 Section 2.7.3 documents the earlier A-band treatment for `16O2`, `16O18O`, and `16O17O` explicitly:

- the spectra were fitted with **Galatry line profiles**;
- Galatry accounts for Doppler broadening, pressure broadening and Dicke narrowing;
- air- and self-broadened Dicke narrowing parameters for each included isotopologue were supplied in the final two columns of the auxiliary A-band input file;
- the rare-isotopologue source is Long et al. (2011), *O2 A-band line parameters to support atmospheric remote sensing. Part II: The rare isotopologues*, JQSRT 112, 2527-2541, DOI `10.1016/j.jqsrt.2011.07.002`.

Long et al. explicitly reports positions, intensities, pressure-broadening and collisional-narrowing parameters for `16O18O` and `16O17O` and describes recommended Galatry line lists.

### Historical archive identities

The surviving Harvard/CfA HITRAN2012 archive exposes the following O2 auxiliary files in the molecule-7 uncompressed directory:

```text
07_A-band_SDF.dat
last modified: 20-May-2013 10:51
index size:    6.1K

07_hit12_0.76mic_Galatry.par
last modified: 20-May-2013 10:51
index size:    46K
```

Archive directory:

```text
https://lweb.cfa.harvard.edu/HITRAN/HITRAN2012/HITRAN2012/By-Molecule/Uncompressed-files/
```

These names and archive metadata are authoritative file-identity evidence, but the current project environment has not successfully retrieved the file bytes. Therefore SHA-256, row layout verification and exact line-to-auxiliary mapping remain pending.

## 4. Rare-isotopologue magnitude is above the M4D tolerance

The accepted HITRAN2016 A subset at 296 K contains:

```text
iso 1 sum(sw) = 2.24412333089e-22
iso 2 sum(sw) = 8.7675965e-25
iso 3 sum(sw) = 1.77109027e-25
A total       = 2.25466201766e-22
```

Thus:

```text
iso 2 + iso 3 = 1.053868677e-24
fraction of A = 0.4674176%
```

The rare-isotopologue integrated strength fraction is therefore approximately `0.467%`, which is already larger than the declared `0.1%` M4D numerical/design tolerance.

Consequences:

- iso-2/iso-3 cannot simply be omitted;
- the project cannot assume their profile choice is irrelevant without calculation;
- the historically supported Galatry treatment is preferable to inventing the principal-isotopologue Drouin parameters for them.

## 5. Candidate per-isotopologue A-band design

The evidence now supports the following **candidate** split:

```text
A iso 1 (16O2):
    HITRAN2016 / Drouin advanced speed-dependent profile
    + historical line mixing / Rosenkranz representation

A iso 2 (16O18O):
    Long/HITRAN2012 Galatry profile with historical Dicke parameters

A iso 3 (16O17O):
    Long/HITRAN2012 Galatry profile with historical Dicke parameters
```

This is not yet frozen because the exact auxiliary bytes and executable mapping have not been verified.

The final design must also check that no HITRAN2016 relational update superseded the rare-isotopologue auxiliary parameters without being visible in the classic 160-character export.

## 6. Required materialization before A can close

### Principal isotopologue

Recover and freeze:

1. `NIHMS804415-supplement-supplement_1.pdf` exact bytes and SHA-256;
2. deterministic extraction/transcription of the required Drouin W-matrix / `Y(T)` information;
3. the exact equations and mapping used to reproduce the HITRAN2016 principal-isotopologue representation;
4. pressure/temperature/shift conventions and numerical normalization checks.

### Rare isotopologues

Recover and freeze:

1. `07_A-band_SDF.dat` bytes and SHA-256;
2. `07_hit12_0.76mic_Galatry.par` bytes and SHA-256;
3. deterministic mapping of the accepted HITRAN2016 iso-2/iso-3 transitions to their historical Galatry/Dicke parameters;
4. an explicit check that the rare-isotopologue HITRAN2016 records remain scientifically consistent with the Long/HITRAN2012 auxiliary representation;
5. target+attenuation sensitivity demonstrating the resulting treatment within the global M4D convergence gate.

## 7. Gate decision

**A-band source discovery is substantially closed, but A-band executable provenance is not.**

The remaining A-band blocker is no longer “which line shape should rare isotopologues use?”. Historical evidence identifies Galatry/Dicke narrowing for the rare lines and Drouin advanced SDV + line mixing for the principal isotopologue.

The blocker is now **byte materialization + parameter mapping + final numerical convergence**.

Do not freeze M4D or implement production A-band code until those assets and mappings are independently verified.
