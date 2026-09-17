# TFM photochemistry model

Reproducible Python implementation of mesospheric O3 and O2(a1Delta)
photochemistry, developed in independently auditable milestones.

## Current milestone: 4C-R2

Milestone 4C adds a reproducible spherical, direct-beam UV/VUV kernel on the
frozen 0--150 km atmosphere. Given 51 dynamic O and O3 concentrations and a
supplied SZA, it calculates exactly eight photolysis coefficients: `JH`,
`J_SRC`, `J_LYA`, `J_O2_TOTAL`, `J_O3_TOTAL`, `J_H2O2`, `J_H2O_A`, and
`J_H2O_B`. The spectral backbone is numerically identical to all six arrays in
the accepted 2017 `sigma.mat`; H2O and H2O2 cross sections are corrected
transcriptions from JPL Evaluation 18 (2015). The H2O row implemented at
189 nm documents and corrects the table's printed 199 nm typo without changing
its `1.08e-20 cm2 molecule-1` value. Exact spherical shell intersections,
altitude-specific Earth shadow, endpoint-mean shell densities, and
Beer--Lambert attenuation are implemented independently of `legacy_2017`.

The M4A background provides:

- NRLMSISE-00 temperature and ordinary-neutral density from a pinned,
  explicitly driven `pymsis==0.12.0`, `version=0` generation;
- fixed Li-2020 model VMRs for O2, N2, and CO2;
- prescribed SOCRATES H2O/H2 climatological profiles on 50--100 km;
- a qualified SOCRATES external-O3 approximation on 0--150 km;
- exact dynamic O/O3 replacement on 50--100 km for the radiative column;
- packaged CSV/JSON assets loaded at runtime without pymsis or network.

M3 thermal/QSSA semantics, M2 kinetics, M4B odd-oxygen bookkeeping, the
accepted `legacy_2017` code, and frozen `sigma.mat` remain unchanged.

Not implemented in M4C: `gA/gB/gIRA`, HITRAN O2 excitation, calendar/local-time
astronomy, a column/vector RHS, time integration, BDF/Radau, diurnal spin-up,
retrieval, transport, or `updated_2025`.

## Layout

```text
src/tfm_photochem/
  metadata.py
  assets/legacy_2017/         frozen sigma.mat and metadata
  assets/historical_2020/     frozen M4A profiles and M4C UV source tables
  legacy_2017/                accepted literal MATLAB reproduction
  historical_2020/
    config.py                 neutral names and unit conventions
    kinetics.py               38 historical rate laws + provenance
    reactions.py              declarative 52-process registry
    local_types.py            scalar input/output contracts
    qssa.py                   six-species algebraic closure
    fluxes.py                 event-flux evaluation
    stoichiometry.py          registry-derived tendency coefficients
    local_closure.py          single-level orchestration
    photolysis_budget.py      injected-total odd-oxygen partition
    background_types.py       immutable profile contracts
    prescribed_profiles.py    SOCRATES interpolation/extrapolation
    background_generation.py  optional pinned MSIS generator
    background.py             network-free runtime loader/API
    uv_assets.py              immutable spectral assets and hashes
    uv_cross_sections.py      JPL18 H2O/H2O2 rules
    uv_geometry.py            exact spherical shell paths and Earth shadow
    uv_radiation.py           columns, optical depth, photon field, eight J
tests/                        inherited tests plus independent M4C tests
scripts/                      five validators and deterministic generators
docs/                          architecture, sources, provenance, evidence
```

## Run

From the repository root:

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check src tests scripts
python -m compileall -q src tests scripts
python scripts/validate_legacy.py
python scripts/validate_local_closure.py
python scripts/validate_historical_2020_background.py
python scripts/validate_odd_oxygen_photolysis_budget.py
python scripts/validate_historical_2020_uv.py
```

To independently regenerate the frozen background (optional generation extra):

```bash
python -m pip install -e ".[background-gen]"
python scripts/generate_historical_2020_background.py --check-against-frozen
```

The meaning and limits of validation are documented in
`docs/validation_report.md`; the full M2 provenance table is in
`docs/historical_2020_reactions.md`; the exhaustive reduced-network inclusion
and exclusion decisions are in `docs/historical_2020_topology.md`.
The M3 equations, flux map, coefficient table, and limitations are in
`docs/historical_2020_local_closure.md`.
The superseding M4B partition, event semantics, and conservation identities are
in `docs/historical_2020_odd_oxygen.md`.
M4A sources, transformations, limitations, and anchors are in
`docs/historical_2020_background.md` and `docs/milestone4a_report.md`.
M4C equations, reconstruction choices, source limits, and sensitivity results
are in `docs/historical_2020_uv_radiation.md` and `docs/milestone4c_report.md`.
