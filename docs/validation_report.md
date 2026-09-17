# Validation report through Milestone 4C-R2

Date: 2026-09-11

## Milestone 4C outcome

The historical-2020 branch now calculates the eight authorized UV/VUV
photolysis frequencies from supplied SZA and dynamic 51-level O/O3 profiles.
The 125-element spectrum and four absorber cross sections are exactly inherited
from the accepted 2017 MATLAB asset; H2O uses a corrected transcription of the
scoped JPL18 table, H2O2 uses its complete scoped JPL18 transcription, and the
H2O2 temperature polynomial is unchanged. The H2O asset contains
`189 nm -> 1.08e-20 cm2 molecule-1` and no 199 nm row. Structured metadata
classifies JPL18's printed 199 nm entry as a typographical error and records
JPL20 as corroboration only, never as the numerical source.

The suite passes 487 tests plus 13 unittest subtests. Independent tests cover
all six source-array identities, source hashes and table spot rows, spectral
masks, unattenuated anchors, exact analytic spherical-shell paths,
altitude-specific shadow, a 400,000-point numerical ray tracer, endpoint shell
quadrature and units, one/multiple/huge optical depths, immutable results,
dynamic composition and controlled O3 self-shielding. Actual computed profiles
obey both M4B gross-subset invariants, and one actual M4B local closure succeeds
with deliberately synthetic external g-factors.

The M4A upper-O3-tail sensitivity is below the specified 1% materiality
threshold for every principal rate at the 1e-12 s-1 rate floor. The separate
H2O2 Lyman-alpha absorption upper bound reaches 4.0651% of represented H2O2
production in the tested baseline cases, below the specified 10% follow-up
threshold. These are reconstruction/regression tests, not atmospheric
validation. Exact evidence is in `docs/milestone4c_report.md` and the JSON UV
validator output.

The frozen reduced two-channel H2O yields are documented as a
historical_2020 Brasseur/JPL-informed model approximation, not exact JPL18
quantum yields. A future scientific-validation item will compare the accepted
1 km endpoint-mean shells with piecewise-linear or refined-shell integration;
selected twilight rates can differ by about 1--2%. No radiation formula or
numerical result changes in M4C-R2.

`gA`, `gB`, `gIRA`, HITRAN excitation, astronomical SZA, time integration, and
retrieval are not implemented.

## Milestone 4B-R2 outcome

The chemistry-facing forcing contract now contains eleven injected rates,
including total O2/O3 photodissociation. Independent synthetic tests verify
the Hartley-only, Lyman-only, SRC-only, and mixed partitions; the exact
two-oxygen-atom source from total O2 photolysis; and reduced odd-oxygen
redistribution by O3 photolysis. Invalid totals below represented excited
channels raise rather than clip. R2 additionally rejects totals below the
known gross spectral subsets: `J_O3_TOTAL < JH` and
`J_O2_TOTAL < J_SRC + J_LYA`.

The suite passes 431 tests plus 13 unittest subtests. New independent tests
cover all three audited rejection examples, exact physical subset equality,
one-ULP-low equality for O2 and O3, preservation of the positive yield
complements, and separation from the excited-channel comparison. The M3 O1D QSSA source
code is byte-identical to M4A and its formula is unchanged. The direct Delta
Hartley event remains `0.9 JH O3`. Legacy/background validator output and all
five frozen M1/M4A asset hashes remain unchanged. Exact build and validator
evidence is in `docs/milestone4b_report.md`.

This validates injected-rate bookkeeping only. No spectrum, cross section,
SZA, spherical ray, optical depth, Beer--Lambert transfer, or HITRAN/radiation
calculation was implemented.

## Milestone 4A outcome

The frozen `midlatitude_equinox_quiet` case provides 151 profile-support nodes
and 51 exactly aligned chemical levels. Tests independently cover the source
knots, geometric-height log interpolation, unbounded last-two-knot O3 upper
extension, ordinary-neutral definition of M, unit conversion, Li fixed VMRs,
exact dynamic/external O3 composition, immutable arrays, static runtime loading,
explicit MSIS generation arguments, packaged hashes, and M3 interface/closure
compatibility.

The full suite passes 373 tests plus 13 unittest subtests. All three validators,
Ruff, bytecode compilation, offline lock verification, full pinned pymsis
byte-for-byte regeneration, wheel install, and extracted-sdist tests pass.
Exact artifacts and command evidence are recorded in
`docs/milestone4a_report.md`.

This validates provenance, transformations, packaging, and interfaces; it does
not validate atmospheric truth, radiation, photolysis, or temporal chemistry.

## Milestone 3 outcome

The scalar `historical_2020` closure connects validated state/background/
forcing inputs to six algebraic species, 54 fluxes and diagnostics, 49
per-event contribution rows, and five local chemical tendencies. The full
suite passes 342 tests plus 13 unittest subtests.

Independent tests cover every required QSSA relation, OH/HO2 physical-root
handling, H2O2 singular limits, O1D branch conservation, Hartley and
Lyman-alpha yield semantics, identical-reactant event conventions, exact R_H
family coefficients, the effective Barth assumption, dynamic Delta, both
frozen O3 topologies, forcing-off behaviour, input validation, and independent
reconstruction of all five aggregate tendencies.

The deterministic single-level result is a closure/assembly regression, not an
atmospheric validation. No time solver, column, physical radiation, or
background generator is implemented. Full evidence is in
`docs/milestone3_report.md` and equations/tables are in
`docs/historical_2020_local_closure.md`.

## Milestone 2 outcome

The `historical_2020` reaction registry and coefficient catalogue are
implemented within the exact M2-R2 boundary. The full suite passes 242 tests
plus 13 unittest subtests. Of 50 registered processes, 39 point to one of 38
implemented rate laws and 11 are explicitly `PENDING INPUT`.

M2 tests independently recompute every coefficient from its published
expression; check units and molecular order; exercise mesospheric temperatures,
scalar and vector inputs, broadcasting, NaN, nonpositive temperature, negative
density, and incompatible shapes; and enforce registry/provenance completeness.

R2 replaces the provisional room-temperature constants for B0+N2 and B0+O3
with the full JPL18 A86 and A82 temperature laws. Tests additionally freeze the
JPL18 `Delta + O3 -> O + 2 O2` topology, Li's simplified B0+O3 product routing,
and the product-yield semantics of the 0.9 and 0.44 photolysis efficiencies.
The exhaustive reduced-network decision table is
`docs/historical_2020_topology.md`.

The accepted M1 production files under `legacy_2017` and the legacy asset files
are byte-identical to `tfm-photochem-milestone1-r2.zip`. The legacy validator
still returns the accepted sigma hash and exact regression arrays.

M2 validates only the traceable registry and individual rate laws. It does not
validate an atmospheric state, QSSA closure, temporal tendency, sunrise,
diurnal convergence, retrieval, or observations.

Detailed commands, artifact checksums, package tests, and the file delta are in
`docs/milestone2_report.md`.

## Milestone 1 accepted outcome

The `legacy_2017` geometry, `Jfactors.m`, and `mkozone.m` numerical core is
implemented and passes all 22 automated tests plus 13 parameterized subtests.

## Checks passed

- Exact SHA256 and MATLAB variable structure for `sigma.mat`.
- Read-only in-memory spectral vectors with finite, nonnegative values.
- Exact wavelength endpoints, duplicate-bin preservation, strict band masks,
  and MATLAB element 28 for Lyman-alpha.
- Overhead 1 km shell paths and independent ray-sphere intersections.
- Tangent geometry at 90 degrees and increasing slant column toward the
  terminator.
- Required SZA coverage at 0, 60, 89.999, 90, 90.001, 95, and 100 degrees with
  finite, nonnegative outputs and preserved shapes.
- Independent analytic ray-sphere comparisons on the day side and at
  twilight where the represented grid and the legacy semantics coincide.
- Exact illuminated-to-Earth-shadow boundary at tangent altitude zero.
- Explicit reproduction of the `isempty(I)` fallback and an independent
  demonstration that it can include below-grid path in the lowest layer.
- Altitude-dependent Earth shadow for SZA greater than 90 degrees.
- Direct equality with a separately written MATLAB-matrix translation of
  `Jfactors.m`.
- Correct zero-optical-depth convention, including the artificial illuminated
  zero-absorber case where `Jfactors.m` forces all J values to zero.
- Preserved inconsistency whereby `mkozone.m` instead evaluates
  `exp(-tau) = 1` when `tau == 0`.
- Direct equality with a separately written three-pass translation of
  `mkozone.m`.
- Fixed numerical regression values at 50, 80, 100, and 150 km.
- Finite, nonnegative photolysis frequencies and positive ozone for the
  deterministic physical test profile.
- Explicit rejection of zero or negative temperature; no concentration
  clipping is performed.

## Packaging checks

- Source distribution and wheel build successfully with `uv build --clear`.
- The wheel contains both `sigma.mat` and its metadata file.
- A clean wheel installation loads the packaged asset and verifies its SHA256.
- `MANIFEST.in` includes all test helpers, documentation, scripts, and lockfile
  in the source distribution.
- The extracted sdist contains `tests/sample_profiles.py`; installation into a
  fresh environment and pytest execution from the extracted tree pass all 22
  tests plus 13 subtests.
- Ruff 0.16.6 is declared in the `dev` extra, configured in `pyproject.toml`,
  locked in `uv.lock`, and reports `All checks passed!`.
- Python bytecode compilation passes.

Detailed commands and outputs are recorded in `docs/audit_r2_evidence.md`.

## Scope boundary

The test profile is deterministic and physically scaled, but it is not an
observational atmosphere and is not presented as scientific validation against
Anqi's figures. That comparison requires her exact background profiles, which
were not supplied. Fixed profile outputs are software regression evidence.
Independent ray-sphere tests are mathematical geometry evidence. Neither is an
atmospheric validation dataset.

No production numerical file under `src/tfm_photochem/legacy_2017/` changed in
audit revision 2 or Milestone 2. At M1 closure,
`historical_2020/__init__.py` was still an empty marker; M2 replaces only that
marker and adds the registry/kinetics modules. No temporal model or 2025
numerical data has been implemented.
