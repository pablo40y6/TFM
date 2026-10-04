# Complete scientific thesis draft

This draft is written exclusively from consolidated main:
`e6ecef1f76dc3730484969d94a9a9f2f3743d0d8`, tag `tfm-final-results-v1`.
The accepted scientific precursor is `tfm-temporal-model-v1`:
`6637b20eb4dafa35d68c766ff4370241c750def2`.
The original project title is retained, with properly typeset oxygen notation.
Body: English. Front matter includes English Abstract and Spanish Resumen.

## Build

From the `thesis/` directory with portable Tectonic 0.17.0:

```text
tectonic --keep-logs --keep-intermediates --outdir build main.tex
```

Alternatively use a standard TeX installation with latexmk/BibTeX:

```text
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

Required packages are declared in main.tex (standard report class, geometry,
lmodern, AMS maths, graphicx, booktabs/longtable, setspace, microtype, natbib,
hyperref). No institutional template was supplied. Tectonic's first build may
download its standard typesetting bundle; it never downloads scientific inputs.
Compiler auxiliaries and the local draft PDF remain ignored under build/.

From the repository root, using the existing scientific environment and `src`
on PYTHONPATH, rebuild registry/CSV tables with:

```text
python thesis/build_tables.py
python thesis/check_thesis.py
```

The table generator reads accepted reaction/rate metadata and the reference CSV;
it never changes model code. Mathematical laws are typeset from parsed symbolic
metadata, and table provenance records input SHA values. Main-text equations
are independently written in event notation and audited against stoichiometry.

## Figures, tables and literature

The eleven accepted PDF figures are referenced directly from
`../results/figures/`; `thesis/figures/` contains only the mapping README.
No figure is regenerated, copied or modified. Source numbers come from the
four CSV summaries, canonical NPZ fields and accepted numerical report/evidence.
SOURCE_MAP.md records the completed inventory and chapter-to-source links.
Literature entries distinguish historical scientific sources from internal
implementation reports. Undated documentation uses an explicit `n.d.` rather
than an invented year. NOAA and SciPy documentation include access dates.

## Unresolved administrative fields and scientific review

Placeholders: university, official programme, author's full name, supervisor,
submission date, optional acknowledgements and institutional title/template.
The original brief's title is
retained pending confirmation of the official registered title.

If no institutional title is already registered, the recommended descriptive
title for human consideration is **Time-dependent photochemical modelling of
mesospheric ozone and O2(a1Delta_g) during dawn** (with the oxygen state typeset
as O2(a¹Δg)). This is a recommendation only; the displayed title is unchanged.

Scientific review should assess the sufficiency of approximate noon states,
prescribed reservoir/exterior ozone fields, absent transport and reduced
excited-state routing for the intended application. The draft claims numerical
finite-horizon validation; it does not claim observational agreement, a global
climatology, a periodic attractor or clean mechanism isolation in season/latitude
experiments. Original retrieval/spin-up ambitions are distinguished from the
accepted delivered forward-model scope.

## Draft verification

The compiled draft contains 10 chapters, 4 appendices, English Abstract and
Spanish Resumen: 69 PDF pages including front matter, 46 main-body pages,
approximately 11,169 main-body prose/caption words, 11 original accepted figures
and 18 verified and cited bibliography entries. The word estimate excludes
mathematics and included registry/data tables; it is not a PDF token count.

Tectonic 0.17.0 compilation passes with no undefined citations/references,
BibTeX warnings or overfull boxes. Benign underfull-line warnings remain in
narrow source-table columns and long bibliographic URLs. Every page was rendered
and visually reviewed, with enlarged checks of equations and dense tables.
The independent transcription audit checks all seven manual event equations
and the radical-family equation exactly against accepted coefficients. The
accepted chemistry, evidence, canonical results, figure PDFs and M4C-R2 SHA
remain unchanged. `consistency_report.json` records the audit and PDF fingerprint.

Final software QA was repeated with the existing scientific environment and
pymsis 0.12.0: 913 tests plus 13 subtests pass, and full-repository ruff passes.
Initial local attempts encountered missing MSIS on the search path and Windows
temporary-directory permissions; the complete run used the existing MSIS
dependency and an authorized workspace temporary directory. No model changes
were needed. This draft adds document audits rather than new physical runs.

## Academic revision before institutional formatting

The reviewed scientific core is preserved. The targeted pass removes repeated
project-internal acceptance wording from the main body, moves endpoint-defect
and detailed regression material from Chapter 6 to Appendix D, and retains all
convergence, positivity, QSSA/budget and shadow evidence. Chapters 1/2/8 gain
three locally verified literature sources (Thomas et al. 1983, Allen et al. 1984,
Koppers and Murtagh 1996), mapped to their specific claims in SOURCE_MAP.md.
Results/Discussion explicitly distinguish geometry/MSIS/initialization changes
from fixed activity, reservoir profiles and incident spectra, with no Earth–Sun
distance irradiance rescaling. The Spanish Resumen and Abstract/Conclusions
are edited without changing numerical claims or adding observational validation.

The document audit additionally compares every displayed equation and every
generated table data row with independently reviewed draft `37d8a04`, and checks
that numerical math in the Results chapter is retained. The prior complete
913-test/13-subtest QA remains applicable because no scientific files change;
this revision repeats document compilation, consistency, visual review and lint.
PR #7 remains draft and must not be marked ready or merged at this stage.
