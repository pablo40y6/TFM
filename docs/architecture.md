# Frozen implementation architecture

## Configuration boundary

Each scientific branch owns its numerical assumptions. Shared code is limited
to neutral metadata types. `historical_2020` does not import numerical content
from `legacy_2017`, so M3 cannot change accepted legacy outputs.

## Implemented through Milestone 4C-R2

```text
tfm_photochem
├── legacy_2017               accepted M1 production code
│   ├── geometry.py
│   ├── photolysis.py
│   ├── ozone.py
│   └── parameters.py
└── historical_2020
    ├── config.py             units, species labels, frozen boundaries
    ├── kinetics.py           scalar/vector coefficient evaluators
    ├── reactions.py          immutable declarative registry
    ├── local_types.py        validated scalar contracts and diagnostics
    ├── qssa.py               O1D, HOx/H2O2, B1, and B0 closure
    ├── fluxes.py             reaction/event flux map
    ├── stoichiometry.py      dynamic coefficient table and assembly
    ├── local_closure.py      one-level orchestration
    ├── photolysis_budget.py  injected-total odd-oxygen partition
    ├── background_types.py   immutable M4A profile values
    ├── prescribed_profiles.py SOCRATES pure profile transforms
    ├── background_generation.py optional pinned MSIS generation
    ├── background.py         frozen-asset validation and runtime API
    ├── uv_assets.py          immutable UV tables and hash validation
    ├── uv_cross_sections.py  corrected JPL18 H2O/H2O2 tables and rules
    ├── uv_geometry.py        exact spherical ray/shell intersections
    └── uv_radiation.py       columns, optical depth, flux, and eight J
```

The registry points from each process to a `RateLaw` identifier or explicitly
uses `PENDING INPUT`. A `RateLaw` contains its callable, literal expression,
unit, molecular order, reference, year, configuration, arguments, and note.
Quantum efficiencies and the two empirical Barth constants are separately
represented as provenance-bearing `Parameter` records.

The exhaustive frozen inclusion/exclusion manifest is
`docs/historical_2020_topology.md`. In particular, it prevents a later assembly
step from silently importing extra reactions from a broader mechanism and
distinguishes product-channel photolysis yields from total reactant losses.

M3 evaluates one scalar level. `qssa.py` closes the six fast species;
`fluxes.py` evaluates registered events plus explicit yield/effective-mechanism
diagnostics; `stoichiometry.py` derives coefficients from the M2 registry and
assembles per-event contributions. `local_closure.py` exposes that complete
chain without constructing a temporal or vertical RHS.

M4A supplies that scalar closure with a static `LocalBackground` at each exact
integer-kilometre chemistry level. The 51-node chemical grid is an exact slice
of a 151-node profile-support grid. Runtime reads packaged deterministic assets;
only the optional generator imports `pymsis`. The larger grid defines sampling
nodes only: it has no shell interfaces, paths, quadrature, SZA, or optical
depth.

M4B extends the scalar forcing contract from nine to eleven injected rates by
adding total O2 and O3 photodissociation coefficients. It partitions those
totals into the already represented O(1D) channels and effective ground-state
complements. This changes only O/O3 photolysis tendency bookkeeping; the O1D
QSSA expression and direct Delta Hartley source are unchanged.

M4B-R2 adds only the missing physical input invariant: the totals must contain
the known gross spectral subsets (`J_O3_TOTAL >= JH` and
`J_O2_TOTAL >= J_SRC + J_LYA`). Product yields remain separate from this
validation, and all partition formulas are unchanged.

M4C composes 151-node atomic-O and ozone columns around the dynamic 50--100 km
state, constructs 150 arithmetic-mean density shells, and integrates exact
sunward spherical ray lengths from each of the 51 targets. Only O, O2, O3, and
N2 absorb the inherited direct-beam spectrum. Beer--Lambert attenuation supplies
the eight UV/VUV J rates required by M4B. Spectral assets load once into
read-only arrays; no scalar OH/QSSA solve occurs in radiation code.

M4C-R2 changes provenance only. Its machine-readable JPL18 metadata records
that Table 4B-3 prints `199 nm` between `188` and `190 nm`; the frozen asset
uses the documented correction `189 nm -> 1.08e-20 cm2 molecule-1`. JPL20 is
corroboration only, not the numerical source. Geometry, shell averaging,
cross-section values, yields, and all eight J-rate formulas remain unchanged.

## Frozen future temporal state (ODE column not implemented)

- Chemistry grid: 50-100 km at 1 km spacing (51 levels).
- Dynamic species per level: O, O3, H, R_H, Delta (255 future ODEs).
- Locally implemented algebraic/QSSA species: O1D, OH, HO2, H2O2, B0, B1.
- Prescribed fields: T, M, O2, N2, CO2, H2O, H2.
- No transport in the first temporal version.
- Future primary solver BDF; verification solver Radau.
- Delta must remain dynamic; it must not be replaced by P/L equilibrium.

## Explicit M4C stop boundary

There is no `rhs.py`, `column.py`, `integrator.py`, or `periodic.py` in
`historical_2020`. M4C accepts SZA directly and makes no claim about calendar
astronomy, `gA/gB/gIRA`, HITRAN excitation, time integration, sunrise
simulation, observations, a converged diurnal cycle, or ozone retrieval.
