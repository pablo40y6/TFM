# Thesis source map and completed pre-writing inventory

Authority: consolidated main `e6ecef1f76dc3730484969d94a9a9f2f3743d0d8`, tagged
`tfm-final-results-v1`; scientific predecessor `tfm-temporal-model-v1`
(`6637b20eb4dafa35d68c766ff4370241c750def2`). PR #6 was squash-merged by explicit
user authorization; its accepted tree is identical to the consolidated tree.

## Inventory and editorial decisions

- Original specification: `docs/project/Thesis idea for Pablo.pdf`, three pages,
  English; proposed title **Photochemical modelling of Ozone and O2(1a_delta)**.
  Use this title with typeset species notation. The brief motivates a temporal
  replacement of sunrise equilibrium retrieval assumptions. Its proposed
  periodic relaxation and satellite comparison are objectives not achieved here.
- No editable thesis, LaTeX template, university formatting instructions or
  authoritative submission information is present. `anqisthesis.pdf` is Anqi
  Li's 2017 Chalmers thesis: literature and historical model source, not this
  student's institutional template. `TAF_Supercomputacion.pdf` is unrelated
  computational teaching material, not a thesis template.
- Authoritative implementation: `README.md`, `PROJECT_STATE.md`, final closure
  sections of `docs/m5_temporal_report.md`, accepted scientific Python modules.
- Historical design/validation: inventoried `docs/`, interpreted using
  `docs/archive/README.md`. Earlier QSSA, incomplete-radiation and periodicity
  claims are superseded; never transfer their acceptance wording into the draft.
  `references/README.md` and `docs/source_inventory.md` also contain old M4D
  pending-language; use their source identities, not that obsolete roadmap.
- Evidence: immutable M4C-R2 ZIP; three accepted temporal NPZ files;
  `evidence/m5_temporal_evidence.json`; M4D closure/mapping evidence.
- Results: `results/README.md`, six configs, ten manifests, four CSV/Markdown
  summaries, seven compact NPZ datasets, eleven PNG/PDF figure pairs. Retain
  their hashes. Reference PDFs directly from `../results/figures`; no copies.
- Literature: all thirteen files in `references/scientific/` inventoried.
  Li 2020, Li 2017, JPL18, Brasseur/Solomon, Mlynczak 1993/2007, Allen 1984,
  Zhu 2007 and Thomas 1983 are potentially relevant. Frederick 1979 and the two
  Schumann--Runge papers are context, not sources of a new numerical scheme.
  JPL20 is only corroboration of the documented 189-nm correction.
- Body language: English; English Abstract and Spanish Resumen. Placeholders:
  full author name, university, programme, supervisor, submission date, optional
  acknowledgements. No institutional affiliation is inferred from cited theses.

## Chapter-to-evidence mapping

| Chapter | Accepted implementation/evidence | Scientific literature and role |
|---|---|---|
| 1 Introduction | Original project brief; final scope in PROJECT_STATE | Li 2020, Mlynczak 1993/2007: airglow/ozone connection; Brasseur/Solomon: context |
| 2 Background | Species definitions and reduced topology | Brasseur/Solomon; Li 2020; JPL18; Allen 1984: odd oxygen/HOx; Mlynczak 1993: excited oxygen |
| 3 Chemistry | reactions.py, kinetics.py, fluxes.py, stoichiometry.py; dynamic-peroxide closure in m5_temporal.py | Li 2020 Table A1; JPL18; Li 2017; clearly label model routing assumptions |
| 4 Forcing | dynamic_atmosphere.py; uv_geometry/uv_radiation; m4d_reconstruction; solar_geometry.py | Picone 2002; NOAA equations; HITRAN2016; TIPS2017; Wehrli 1985; Mate 1999; Drouin 2017 |
| 5 Temporal methods | m5_temporal.py, m5_dynamic.py, m5_simulation.py; final noon initialization/report | Original reduction sources above; SciPy solver documentation; QSSA failures are thesis results |
| 6 Validation | m5_temporal_evidence.json; final M5C report; results/manifests/campaign_qa.json | Solver documentation for methods; precision/convergence values are internal direct evidence |
| 7 Results | Four accepted summaries and eleven accepted figures, configs/manifests/NPZ | Numerical findings of this thesis; no literature substituted for computed outputs |
| 8 Discussion | Identical-y0 atmosphere comparison, initialization sensitivity, common-SZA comparisons | Brasseur/Solomon and Zhu 2007 for transport context; causal interpretations explicitly limited |
| 9 Conclusions | Supported objectives and measured results above | No new empirical claim |
| 10 Future work | Scope limitations and original retrieval motivation | Li 2020/Mlynczak 2007: observational targets; Zhu 2007: transport coupling |
| Appendix A Network | Registry equations, rates and scalar parameters, automatically audited | Per-row frozen historical source; pending elementary Barth steps identified as effective only |
| Appendix B Mathematics | Seven tendencies, QSSA, photolysis partition and accepted event coefficients | Model definitions; analytic family/positivity checks |
| Appendix C Provenance | Asset metadata, external SHA values, six scenario manifests | Primary database/model publications and source identities |
| Appendix D Reproduction | Accepted tags, solver controls, script names, checksums | Tool documentation; no private paths or raw licensed data |

## Detailed drafting outline and order

1. Background: domain, odd oxygen, HOx, excited oxygen, radiation, twilight.
2. Chemistry: notation, event convention, full seven-species flux equations,
   family identity, reduced product routing, prescribed reservoirs.
3. Forcing: frozen/dynamic distinction, UV spectral sum and columns, monomer
   A/B/IRA transfer and CIA, solar geometry, shadow.
4. Temporal methods: state, retained QSSA, rejected OH/peroxide elimination,
   initialization, mixed positive coordinates, stiff solvers and interpolation.
5. Validation: convergence scopes, residuals, positivity/shadow, source integrity.
6. Results: reference five figures; seasonal two; latitude two; sensitivities two.
7. Discussion: synthesis, non-isolated mechanisms, initialization/transport limits.
8. Introduction; conclusions/future work; Abstract/Resumen; appendices.
9. Full numbers/equations/citations/figure/format consistency pass and PDF build.

## Claim discipline

Literature citations support background, not the accuracy of this model.
Repository files are implementation evidence, not substitute literature.
Convergence is scoped to tested finite-horizon trajectories; no observational,
global initial-condition or periodic-attractor certification is claimed.
Season/latitude vary geometry, background and initialization simultaneously.
Missing SZA60 for winter45N/equinox70N is a geometry limitation, not missing data
to be interpolated. Initialization sensitivities use the accepted frozen,
artificial-equinox experiment; do not describe them as fresh dynamic-MSIS runs.

## Targeted academic revision: added literature

Bibliography expanded from 15 to 18 sources. Metadata (full authors, title,
journal, year, volume/issue and page range) was checked against the existing
documents, not inferred from filenames. No scientific source PDF was edited.

| Entry | Document and metadata check | Supported claim and scope |
|---|---|---|
| Thomas et al. (1983), GRL 10(4), 245–248 | `1983-Ozone_density_distribution_in_the_mesosphere_(50-90_km)_measured_by_the_SME_limb_scanning_near_infrared_spectromete.pdf`, pp. 245–248; complete nine-author list on p. 245; DOI corroborated in Li et al. (2020)'s bibliography | Chapters 1/2/8: historical 1.27 μm SME ozone inference, secondary vertical maximum and height-dependent variability; afternoon measurements are not a dawn matchup. |
| Allen, Lunine and Yung (1984), JGR 89(D3), 4841–4872 | `1984-The_Vertical_Distribution_of_Ozone_in_the_Mesosphere_and_Lower_Thermosphere (1).pdf`, title/abstract p. 4841; DOI corroborated by the publisher | Chapters 2/8: mesospheric/mesopause ozone structure, diurnal behaviour and coupled oxygen–hydrogen chemistry with sensitivity to illumination, water and thermal structure; no transferred validation statistics. |
| Koppers and Murtagh (1996), Ann. Geophys. 14(1), 68–79 | `koppers&murtagh.pdf`, scanned title/abstract p. 68; full metadata and DOI corroborated by the journal | Chapters 2/8: Schumann–Runge parameterization depends on slant column, temperature and SZA and can affect ozone-related chemistry; no coefficient substitution or borrowed error bound. |

Primary corroborating records: [Allen et al.](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/JD089iD03p04841),
[Koppers and Murtagh](https://angeo.copernicus.org/articles/14/68/1996/),
[Li et al. bibliography](https://amt.copernicus.org/articles/13/6215/2020/amt-13-6215-2020-relations.html).
`murtaghSR.pdf` was also inspected visually (1989 ESA SP-291 proceedings,
pp. 49–53 plus a blank scanned page); it adds overlapping parameterization
context and was not added solely to increase the reference count.

This revision preserves all displayed equations and generated table data rows,
all numerical results, the eleven figure PDFs and the consolidated scientific
tree. Software endpoint and detailed regression coverage moved to Appendix D;
the main validation chapter retains numerical convergence and physical checks.
