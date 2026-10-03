# M4D MATS A-band forensics

Status: **DRAFT EVIDENCE / DESIGN NOT FROZEN**

Branch: `milestone/m4d-design`

This note records executable A-band behaviour recovered independently from the public `innosat-mats/MATS-analysis` repository. It is supporting/validation evidence only. It does not establish the HITRAN2016 numerical baseline and does not authorize M4D implementation.

## 1. Repository history narrows the date of the public notebook

The historical path `Bjorn/retrieval/Abandabscorr_edit.ipynb` appears in repository history at least as early as commit:

- `2e4575dadb273dca0c211b5083c768f09a8fab27`
- date: 2024-02-20 UTC
- message: `Initial. Small tweaks before changes.xy`

It was subsequently updated during February-May 2024 and moved/restructured in commit `ff3a523b97c5835aa24a7020c9f9799e3b33d57c` on 2024-05-06.

The saved notebook output already contains a completed HAPI fetch. Thus this public artifact proves a MATS-team A-band workflow by 2024, but does not establish that its downloaded line records are HITRAN2016. No edition identifier is embedded in the inspected fetch cell.

## 2. Exact HAPI fetch performed by the notebook

The notebook executes:

```python
db_begin('Abanddata')
fetch_by_ids('oxygen', [36], 1/776e-7, 1/749e-7)
```

and its saved output states:

```text
Data is fetched from http://hitran.org
BEGIN DOWNLOAD: oxygen
  65536 bytes written to Abanddata/oxygen.data
Header written to Abanddata/oxygen.header
END DOWNLOAD
Lines parsed: 199
```

Global isotopologue ID `36` is the principal `16O2` isotopologue. Therefore this specific MATS A-band calculation intentionally fetched only the principal isotopologue over approximately 749-776 nm, rather than all O2 isotopologues.

That is useful historical/model-practice evidence, but it is not automatically the correct policy for the new `historical_2020` reconstruction. Li 2020 points to HITRAN2016 generally, so M4D should first quantify the contribution of all O2 isotopologues actually present in HITRAN2016 before deciding whether minor-isotopologue omission is negligible.

## 3. State-level A-band selection is explicit

After downloading the 199-line interval, the notebook applies a HAPI query:

```python
select(
    'oxygen',
    ParameterNames=('nu', 'sw', 'local_iso_id', 'a', 'elower', 'gp', 'gpp'),
    Conditions=('==', 'global_upper_quanta', ('STR', ('       b      0'))),
    DestinationTableName='tmp',
)
```

The selected set reports:

```text
min(nu) = 12892.859666 cm^-1
max(nu) = 13339.201391 cm^-1
```

This independently supports the M4D design choice to select the A band using HITRAN global electronic/vibrational quantum labels rather than reproducing Anqi's narrower hard-coded `12900:0.01:13170 cm^-1` grid as the definition of the band.

The notebook only constrains the upper global state in this cell. For M4D, the semantic definition should remain explicitly `b(v'=0) <- X(v''=0)` and both upper/lower global labels should be checked against the acquired HITRAN2016 records.

## 4. A significant abundance-handling quirk is visible

The downloaded HITRAN/HAPI header describes `sw` as:

> Line intensity, multiplied by isotopologue abundance, at T = 296 K.

Nevertheless, after reading the selected lines the notebook executes:

```python
for i in range(a.shape[0]):
    a[i] *= abundance(7, iso[i])
    sw[i] *= abundance(7, iso[i])
```

For standard HITRAN `sw`, the second multiplication applies isotopologue abundance a second time. The multiplication of the Einstein-A coefficient by terrestrial abundance is also not part of the standard definition of a molecular Einstein-A coefficient.

These operations must therefore be treated as **MATS notebook implementation quirks / choices**, not inherited silently into M4D.

Because this notebook fetched only principal `16O2`, the numerical impact of the extra abundance multiplier is relatively small compared with the conceptual issue, but M4D must validate the standard HITRAN convention directly and use one internally consistent density/intensity convention.

## 5. Why this is useful despite not being the historical line source

This notebook supplies several independent checks relevant to M4D:

1. the MATS analysis lineage uses HAPI/HITRAN fixed-column line data for A-band absorption;
2. the global upper quantum label for the A system is represented in HAPI as a `b`, `v=0` state;
3. an interval wider than Anqi's legacy grid contains A-band records selected by state label;
4. the public workflow selected only global isotope ID 36 (`16O2`), giving us an explicit approximation to test rather than assume;
5. the abundance multiplication in the notebook demonstrates why M4D needs a formally frozen isotopic/intensity convention instead of copying downstream code.

## 6. Consequence for the M4D specification

The following should be carried into the design review:

- Use quantum-state semantics as the primary A/B/IRA selector.
- Do not use the Anqi 12900-13170 cm^-1 interval as the physical definition of the entire A band.
- Do not automatically restrict the new baseline to `16O2`; quantify minor-isotopologue contributions from the actual HITRAN2016 source first.
- Do not apply an additional terrestrial-abundance multiplier to standard HITRAN `sw` values.
- Do not multiply Einstein-A by isotopic abundance unless a separately defined effective-mixture quantity explicitly requires it.
- Preserve the MATS notebook as an independent validation/forensics source, not as numerical provenance for the historical line list.

## 7. Provenance status

The MATS evidence improves the reconstruction of intended A-band processing but does not close the numerical spectroscopy gate. The exact HITRAN2016 O2 line asset remains to be acquired and frozen with edition evidence and hashes.

Status remains:

**UNRESOLVED PROVENANCE RISK — not yet SOURCE BLOCKER.**

Sources inspected:

- https://github.com/innosat-mats/MATS-analysis/blob/43b541904996461fcf3209efd1a613143deaf02e/Bjorn/retrieval/Abandabscorr_edit.ipynb
- https://github.com/innosat-mats/MATS-analysis/blob/1b16746bf030af9b13d1e568033fcd0dfc7ece46/Bjorn/retrieval/1D_full/Abandabs/Abanddata/oxygen.header
