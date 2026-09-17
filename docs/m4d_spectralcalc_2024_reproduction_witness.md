# M4D SpectralCalc HITRAN2016 reproduction witness

Status: **DRAFT EVIDENCE / SUPPORTING PROVENANCE WITNESS**

Branch: `milestone/m4d-design`

This note records a particularly strong independent reconstruction witness for the proposed SpectralCalc acquisition route. It does not itself supply the M4D O2 A/B/IRA line bytes and therefore does not close the spectroscopy gate.

## 1. Peer-reviewed 2024 provenance statement

Gava, Costa and Sena (2024) explicitly compared HITRAN2016 with HITRAN2020 using the Oxford Reference Forward Model (RFM).

Their JQSRT paper records in its data-availability statement:

- HITRAN2020 spectroscopic parameters: obtained from HITRANonline;
- HITRAN2016 spectroscopic parameters: obtained from SpectralCalc;
- last access for the HITRAN2016 source: **11 March 2024**.

Reference:

M. L. L. M. Gava, S. M. S. Costa, C. A. P. Sena, *The effects of changes in HITRAN and the water vapor continuum model on infrared radiative transfer calculations and remote sensing applications*, JQSRT 322 (2024) 109025. DOI `10.1016/j.jqsrt.2024.109025`.

Their companion open-access Data in Brief article repeats that HITRAN2016 came from SpectralCalc:

M. L. L. M. Gava, S. M. S. Costa, C. A. P. Sena, *Infrared radiative transfer dataset: Comparisons of HITRAN2020, HITRAN2016, and MT_CKD versions 3.2 & 4.1.1 across five model atmospheres*, Data in Brief 57 (2024) 110867. DOI `10.1016/j.dib.2024.110867`.

The Data in Brief acknowledgements additionally thank Dr. I. Gordon for assistance in accessing HITRAN2016. This gives the study a direct HITRAN-community connection, but it does not by itself establish that every future SpectralCalc export is byte-identical to the file used by the authors.

Sources:

- https://www.sciencedirect.com/science/article/pii/S0022407324001328
- https://pmc.ncbi.nlm.nih.gov/articles/PMC11403244/

## 2. Public reproduction scripts preserve the exact local filename

The authors' public repository is:

- `livialmg/HITRAN_MT_CKD_IR_calculations`
- https://github.com/livialmg/HITRAN_MT_CKD_IR_calculations

Its driver-generation script loops over two explicit versions:

```bash
versions=("2016" "2020")
```

and supplies RFM with:

```text
*HIT
../hit/hitran${version}-spectralcalc.bin
```

Thus the actual local inputs used by the workflow were named:

```text
hitran2016-spectralcalc.bin
hitran2020-spectralcalc.bin
```

The script also declares a 10-3000 cm^-1 calculation range and includes O2 among the absorbers.

Stable witness:

- https://github.com/livialmg/HITRAN_MT_CKD_IR_calculations/blob/main/driver_tables/loop_over_profiles.sh

This is a stronger provenance chain than a generic citation to SpectralCalc because the executable reproduction workflow itself associates the historical version label `2016` with a file explicitly named `hitran2016-spectralcalc.bin`.

## 3. Important limitation: the spectroscopy binary is intentionally absent from the public repository

The current public repository contains:

- RFM source archive;
- driver scripts;
- atmospheric profiles;
- documentation.

It does **not** contain the referenced `hit/` directory or the files `hitran2016-spectralcalc.bin` / `hitran2020-spectralcalc.bin`.

The corresponding Zenodo data record contains the RFM output products, not the historical spectroscopy binary itself.

Therefore we cannot hash, inspect or reuse the 2024 study's exact line-list input from the public materials currently available.

Public records:

- https://github.com/livialmg/HITRAN_MT_CKD_IR_calculations
- https://zenodo.org/records/11122536

This absence is consistent with treating spectroscopy data as a separately acquired input rather than redistributing it with model/output files, although the public sources do not state the licensing reason explicitly.

## 4. Consequence for our acquisition strategy

This witness strengthens the case for retrieving a fresh **historical HITRAN2016 selection from SpectralCalc**, provided the edition can still be explicitly selected and the resulting transition-level file is validated.

After retrieval, compare our acquisition manifest against this 2024 workflow:

```text
Provider      : SpectralCalc
Edition       : HITRAN2016
Historical witness access date : 2024-03-11
Historical local filename       : hitran2016-spectralcalc.bin
Our source type                 : transition-level export, not simulated spectrum
Our target molecule             : O2 / molecule 7
Our target spectral coverage    : full O2 preferred; at minimum complete IRA/A/B systems
```

The `.bin` used by RFM is not necessarily the direct format downloaded from SpectralCalc; it may be an RFM/HITBIN conversion product. Therefore our provenance chain must preserve the **original SpectralCalc export before any conversion**, then document any conversion separately and hash both stages.

## 5. Current interpretation

The evidence now supports all of the following simultaneously:

- SpectralCalc explicitly ingested HITRAN2016 in 2018;
- SpectralCalc continued to support historical-version use after HITRAN2020 became available;
- a peer-reviewed 2024 study explicitly obtained HITRAN2016 from SpectralCalc on 2024-03-11;
- that study's executable RFM workflow names its local historical input `hitran2016-spectralcalc.bin`;
- the raw/binary spectroscopy file is not publicly preserved in the reproduction repository.

Therefore SpectralCalc remains the strongest practical acquisition route identified so far, but the decisive next evidence must be the actual retrieved O2 records and their hashes.

M4D remains **DESIGN NOT FROZEN / NOT IMPLEMENTED**.