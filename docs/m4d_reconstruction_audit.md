# M4D isolated reconstruction audit, completed 2026-10-01

The accepted scientific baseline remains M4C-R2, version 0.5.1. This audit covers
an isolated implementation experiment on `milestone/m4d-design`, started from
`08a818c`. M4D is not frozen and M5 is untouched. The user explicitly requires a
scientific stop if a retained CIA or corrected B qSDV sensitivity exceeds 0.1%.

## Implementation and source mapping

The new `tfm_photochem.m4d_reconstruction` namespace is not imported by the
accepted `historical_2020` API. Exact size/SHA-256 checks precede source parsing.
The accepted HITRAN2016 export supplies line centres, strengths, lower energies,
isotopes and ordinary fields; the historical auxiliary supplies Dicke fields only.

`evidence/m4d_mapping.json` records PASS: 150 principal A lines split into 91
Drouin SDV dipoles and 59 quadrupoles. Exactly 70 dipoles have published matrix
and Table-22 coverage; 21 have no published Y. All 280 rare lines have matched
air/self Dicke coefficients. All 430 target-to-auxiliary identities match, with
zero unmatched entries, duplicate keys, extra target-source entries or ambiguities.

Tables 4–5 are parsed from structured PMC XML. Table 22 and all sixteen
triangular Tables 6–21 are parsed from publisher PDF text without OCR. The matrix
quantum-label union must equal Table-22 coverage. The P/Q and R/Q convention is
translated through branch quantum rules; no join uses row order or nearest
wavenumber. Only classifications, counts, quantum labels and transcription hashes
are committed; numerical source parameter tables remain external.

Implemented numerical components include TIPS-2017 interpolation, line-strength
temperature scaling, the Wehrli photon Jacobian, stable complex Voigt and isolated
Drouin SDV primitives, shell-local widths/shifts, exact spherical sub-shell paths,
all-line B/IRA Voigt transfer, and historical CIA opacity with source-node clipping
and measured-temperature envelope diagnostics. All absorber lines contribute at
every node. A distant-profile moment series accelerates contributions outside
2 cm^-1; it is compared with direct all-line `scipy.special.wofz`, never used as
an absorber cutoff. Target support is separately refined, without renormalization.

The default B/IRA width follows the user's explicit partial-pressure expression.
The branch's previous air-only candidate remains a named comparison. No accepted
M4C calculation or asset changes. A full coupled A SDV+LM/Galatry evaluator and
corrected B qSDV are outstanding; the available SDV primitives and mapped Dicke
parameters must not be mistaken for complete A transfer.

## Numerical evidence and stop decision

`scripts/validate_m4d_reconstruction.py` verifies the retained IRA counterexample
at 50 km / SZA 95 degrees using all 835 accepted IRA lines. Its machine-readable
report is `evidence/m4d_cia_stop_gate.json`. A spatial comparison jointly refines
monomer paths 0.125→0.0625 km and CIA paths 0.0625→0.03125 km. Independent spectral
comparisons on the selected 0.125/0.0625-km monomer/CIA paths refine quadrature
order 64/8→128/16 and target support 3.84→7.68 cm^-1. Each comparison uses the same
monomer-only and CIA nominal/envelope/raw calculations; relative differences are
normalized by the refined rate and gated at 1e-3 above 1e-15 s^-1.

The report also checks all 21 unattenuated source regression anchors, all 357
height/SZA geometry cases, the illuminated Earth tangent and the immediately
shadowed path/rate. These preliminary checks do not establish full-domain rate
closure. The opacity evaluator is checked on source-driven core, wing and
between-line nodes in every active reference shell against direct all-line Voigt.

**DESIGN BLOCKER.** At the refined target support, monomer-only
`gIRA = 6.7194715555556325e-12 s^-1`; historical-CIA
`gIRA = 6.699880907505247e-12 s^-1`. The 0.2915504276% reduction exceeds the
0.1% gate; both rates remain above 1e-15 s^-1. The measured-temperature envelope
gives reductions 0.2722675384--0.2924815347%; every value triggers the same stop.
The raw-negative-sample diagnostic matches nominal at the reported precision.

| Counterexample comparison | Maximum relative difference | Percent | Decision |
| --- | ---: | ---: | --- |
| Spatial, joint monomer/CIA path halving | 3.8850550379429836e-4 | 0.03885055038% | PASS |
| Target core/wing order 64/8 to 128/16 | 2.140087936324544e-6 | 0.000214008794% | PASS |
| Target support 3.84 to 7.68 cm^-1 | 7.189447951514405e-5 | 0.007189447952% | PASS |

These maxima cover the six retained rates in the one counterexample, not all
altitudes/SZAs. The existing 357-case geometry check gives 327 illuminated
targets and a maximum aggregated accepted-shell path difference
`2.842170943040401e-14 km`. The Earth tangent is illuminated at
`100.08663838402701 deg`; immediately shadowed IRA rates are exactly zero.
The 21 source regression anchors have maximum relative error
`3.1011216756082296e-11`. On 728 profile probes in 1991 active reference shells,
distant-profile orders 4/6/8 have respective maximum relative errors
`1.4054744698291315e-8`, `3.3782455643144574e-12` and
`1.4259996743236795e-14` against direct all-line Voigt.

Scientific closure stops at the CIA gate as requested. No unexecuted gate is
reported as PASS, and no final M4D design/freeze or M5 work is authorized by this
result. `evidence/m4d_audit_checks.json` provides the compact audit receipt.

## Exact validation commands

Run from the repository root with Python >=3.10. Install the existing dev extras
and the new source-audit extra; PyMuPDF is needed only for the mapping validator:

```powershell
python -m pip install -e '.[dev,m4d-audit]'
$env:PYTHONPATH='src'
$env:PYTHONIOENCODING='utf-8'
$env:OPENBLAS_NUM_THREADS='1'
python -m pytest -q -p no:cacheprovider
python -m ruff check .
python scripts/validate_legacy.py
python scripts/validate_local_closure.py
python scripts/validate_odd_oxygen_photolysis_budget.py
python scripts/validate_historical_2020_background.py
python scripts/validate_historical_2020_uv.py
python scripts/validate_m4d_legacy_cia_diagnostic.py --sources ../m4d-workflow-check/acquisition --work ../m4d-legacy-rerun --output evidence/m4d_legacy_cia_diagnostic.json
python scripts/validate_m4d_mapping.py --sources ../m4d-sources --hitran 'C:/Users/Pablo/Downloads/guest1593878592.txt' --output evidence/m4d_mapping.json
python scripts/validate_m4d_reconstruction.py --sources ../m4d-sources --hitran 'C:/Users/Pablo/Downloads/guest1593878592.txt' --checkpoints ../m4d-run-cache --output evidence/m4d_cia_stop_gate.json
Get-FileHash artifacts/accepted/m4c-r2/tfm-photochem-milestone4c-r2.zip -Algorithm SHA256
```

The actual interpreter for this audit is `../m4d-env/Scripts/python.exe`.
Checkpoints are optional derived rates external to Git. Reusing them requires
identical configuration, numerical module fingerprints and fixed controls; all
input sources are reverified. The per-variant producer CLI hash records which
orchestration version produced each completed quadrature. Changing the spectral
refinement plan does not change a completed spatial quadrature's numerical module
or inputs.
Delete/omit the checkpoint option to force numerical recomputation. Exit 2 from
the stop validator denotes the explicitly required DESIGN BLOCKER, not a passing
closure validator. Exit 1 denotes source/numerical verification failure; exit 0
only means this probe did not trigger. It never denotes complete M4D closure.
When wrapping the command in PowerShell, use `exit $LASTEXITCODE` in a separate
validation shell to propagate Python's exit 2; otherwise PowerShell may report
its generic native-command failure code 1. The written scientific decision is
DESIGN BLOCKER in both cases.

The complete suite passes 532 tests plus 13 subtests. The five existing validators,
the mapping validator and the unmodified inline CIA geometry diagnostic pass.
The new legacy wrapper checks exact witnesses and the extracted workflow-code
hash before running it outside Git. `evidence/m4d_legacy_cia_diagnostic.json`
records its 357 cases per spacing: the selected CIA 0.0625→0.03125-km refinement
has maxima 0.03883374097% in diagnostic attenuation and 0.04156931421% in maximum
line-centre optical depth. Its HITRAN2012 strength weights remain a diagnostic
witness, never the target-edition monomer-transfer input. Final lint and source/frozen-file checks are
recorded with the completed numerical report in the audit evidence.

## Source identities and acquisition

The full identities are in `sources.SOURCE_IDENTITIES` and the two JSON reports.
Restricted/raw source files and PDFs reside outside Git in `../m4d-sources` or
the user's pre-existing Downloads directory. No source bytes are redistributed.

- HITRAN2016: pre-existing `guest1593878592.txt`, 2268239 bytes, 14085 records;
  SHA-256 `6b4acbc01cb649891f2d8597875c9cd8e4805cfdd4d3b7841c2d18cbf718de12`.
- PMC XML: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=5103325
- Primary HITRAN2016 article: https://hitran.org/media/refs/HITRAN-2016.pdf,
  11019503 bytes,
  SHA-256 `59cfae42b11a0f67372804555583095d768dfdf4d65b5cc1fae2513c03bb5b86`;
  corroborates the documented historical CIA semantic correction and B source scope.
- Publisher supplement: https://ars.els-cdn.com/content/image/1-s2.0-S0022407316301108-mmc1.pdf
- Rare historical auxiliaries: `07_A-band_SDF.dat` and
  `07_hit12_0.76mic_Galatry.par` under
  https://lweb.cfa.harvard.edu/HITRAN/HITRAN2012/HITRAN2012/By-Molecule/Uncompressed-files/
- Historical Maté witness: https://lweb.cfa.harvard.edu/HITRAN/HITRAN2012/CIA/Main-Folder/O2-O2/O2-O2_2011.cia
  Its full hash and 253/273/296-K block hashes are checked. The documented
  HITRAN2016 O2-Air semantic correction is used; the old basename is not treated
  as evidence of pure O2-O2 semantics. See the existing CIA materialization audit.
- Existing workflow witness only: `07_hit12.par` under the same historical
  By-Molecule URL, 2263950 bytes,
  SHA-256 `ad2cadf91cb985bec4074ce0bf47cdcfa7aab627ea15de2ac85de731873417a4`.
  Keep it and a copy of `O2-O2_2011.cia` in the external
  `../m4d-workflow-check/acquisition` directory for the legacy-wrapper command.
- TIPS: https://raw.githubusercontent.com/hitranonline/hapi/f41d9911f2631eed51b96d6c617b4f27786ad477/hapi/hapi.py
  Only literal historical tables are parsed; external Python is not executed.
- Solar: https://raw.githubusercontent.com/mkelley/mskpy/4deb59f47b3fb72991958cbc95a393c8e4c68660/mskpy/data/wehrli85.txt

## Remaining independent audit and scientific work

Do not freeze M4D or start M5. Resolve the retained CIA baseline stop decision
before proceeding. Full-domain A/B/IRA rate maxima, A LM/Galatry transfer and
sensitivities, corrected source-based B qSDV, pressure-shift sensitivity and
illuminated tangent rate closure remain explicitly NOT RUN / outstanding.
Geometry coverage, profile tests and a converged counterexample establish only
their stated scopes. No corrected B parameters were inferred from modern HITRAN.
The accepted upper column exceeds Table-22's 340-K source range; the current
Y primitive fails closed there. A supported upper-temperature policy or a
validated materiality bound remains necessary before complete A transfer.
