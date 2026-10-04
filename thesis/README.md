# Final Master Thesis

**Time-dependent photochemical modelling of mesospheric ozone and O₂(a¹Δg) during dawn**

Pablo Martínez · Department of Physics · University of Gothenburg · 2026.
Physics, Master's Programme; Master of Science (120 credits) with a major in Physics.
Master's Thesis, 30 ECTS; FIM930 — Physics: Master Thesis, 30 credits. Supervisor: Anqi Li.

The scientific content is closed. No administrative placeholders or Acknowledgements section remain.
English body and Abstract; Spanish Resumen; contents, figure/table lists and four appendices.

## Reproducible build

From `thesis/`, use portable Tectonic 0.17.0:

Set `SOURCE_DATE_EPOCH=1791102838` (the immutable scientific-results baseline
timestamp) before compiling. In PowerShell use
`$env:SOURCE_DATE_EPOCH='1791102838'`; in a POSIX shell use
`export SOURCE_DATE_EPOCH=1791102838`. This fixes PDF metadata timestamps so
the checked branch and merged main produce byte-identical PDFs.

```text
tectonic --keep-logs --keep-intermediates --outdir build main.tex
```

Alternatively, use a standard LaTeX installation with BibTeX:

```text
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

Copy `build/main.pdf` to `build/Pablo_Martinez_Master_Thesis_2026.pdf` for submission.
Build outputs and compiler auxiliaries remain ignored. Standard packages are declared in `main.tex`.
Tectonic may download its typesetting bundle on first use; scientific inputs remain local.
The cover uses the author's confirmed institutional fields and clean academic layout;
it does not claim to be an official university template.

From the repository root, with the scientific environment and `src` on PYTHONPATH:

```text
python thesis/build_tables.py
python thesis/check_thesis.py
```

The table generator reads frozen registry metadata and canonical CSVs. The consistency
check verifies equations, table data, citations, eleven original figure PDFs, input
hashes and the immutable M4C-R2 artifact. It checks confirmed cover fields and absence
of editorial placeholders. The audit receipt is `consistency_report.json`.

## Provenance and verification

Scientific results are consolidated at `tfm-final-results-v1`
(`e6ecef1f76dc3730484969d94a9a9f2f3743d0d8`), with the temporal model at
`tfm-temporal-model-v1` (`6637b20eb4dafa35d68c766ff4370241c750def2`).
Final thesis source is identified by `tfm-thesis-final-v1` on main.
`SOURCE_MAP.md` preserves inventory and revision provenance. Figures are referenced
directly from `../results/figures/`. No model, evidence, scientific results or source
PDFs are modified by this thesis work.

The final document has ten chapters, four appendices, 46 main-body pages,
approximately 11,169 prose/caption words, eleven figures and eighteen cited references.
The word estimate excludes mathematics and included registry/data tables.
Compilation, document consistency, full-repository ruff and 913 tests plus 13 subtests
pass. Every final PDF page is rendered and checked for layout, numbering and references.
Remaining underfull warnings in narrow table columns and long bibliographic URLs
produce no clipped or out-of-margin content. The accepted finite-horizon scope and
atmospheric limitations remain unchanged, without new experiments.
