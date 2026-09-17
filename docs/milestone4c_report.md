# Milestone 4C-R2 provenance correction and evidence report

Date: 2026-09-11  
Package: `tfm-photochem` 0.5.1  
Starting artifact: mathematically and numerically accepted
`tfm-photochem-milestone4c.zip`  
Starting SHA256: `27ec4168ca38bd193f88dd05dbaf8e702eb2be0ce77eb679e2d7f311f32fb101`  
Earlier M4B-R2 lineage SHA256:
`87fe1d585efa6f42231fc6d9898ca37c5afa51d1b4baa6325015caaee03530c8`

## R2 correction boundary

M4C-R2 changes provenance, documentation, tests, and deterministic evidence
only. It keeps every accepted cross-section value, yield, spectral mask,
geometry rule, shell rule, optical-depth expression, photolysis definition,
and numerical anchor unchanged. It does not implement `gA`, `gB`, `gIRA`,
M4D, or M5.

JPL18 Table 4B-3 prints `199 nm -> 1.08e-20 cm2 molecule-1` between its 188
and 190 nm rows. The frozen asset continues to use
`189 nm -> 1.08e-20 cm2 molecule-1`, now explicitly classified as a
typographical correction. The evidence is the sequential position, the table's
121--198 nm range, its 183--191 nm source interval, and JPL20 Table 4B-2-2's
corroborating 189 nm row. JPL20 is corroboration only; the numerical source
configuration remains `historical_2020` / JPL18 Table 4B-3.

The generator comments the corrected row and emits the same correction as a
structured `source_corrections` metadata record. A hard-coded test reads the
CSV directly and requires one 189 nm row at `1.08e-20`, no 199 nm row, and the
documented classification. The validator repeats those independent asset
checks and emits the full correction record.

The unchanged H2O branching values are described accurately as
historical_2020 reduced two-channel H2O yields based on the frozen
Brasseur/JPL-informed model approximation, not exact JPL18 quantum yields.

The exact 16-file modification list and single new evidence file, together
with hashes of the untouched numerical assets and radiation modules, are in
`evidence/delta_from_m4c.json`.

## Scope delivered

M4C implements only the spherical, direct-beam historical UV/VUV calculation
and its eight authorized J outputs. It does not implement `gA`, `gB`, `gIRA`,
HITRAN excitation, astronomical SZA, M4D, any time/ODE solver, or M5.

Added production modules are `uv_assets.py`, `uv_cross_sections.py`,
`uv_geometry.py`, and `uv_radiation.py`. The only pre-existing production
contract extended is `background_types.py`, which now exposes the specified
atomic-O composition from dynamic values and the already frozen native-MSIS
diagnostic. Chemistry kinetics, QSSA, fluxes, stoichiometry, M4B partitioning,
and every `legacy_2017` production file are unchanged.

## Historical source assets

The generated backbone contains 125 rows and is exactly equal to the six
`sigma.mat` arrays. Independent tests and the validator use `scipy.io.loadmat`
directly and report `array_equal=true` for `wave`, `irrad`, `sO`, `sO2`,
`sO3`, and `sN2`. The duplicate 117.30308 nm source rows and exact MATLAB row
28 at 121.567 nm are retained.

| Asset | Rows | SHA256 |
| --- | ---: | --- |
| `uv_spectral_backbone_2017.csv` | 125 | `a398b97e7b2ae68efa9c72353444317e8a73f836870f0bd2cd6f21a5b1c7b135` |
| `uv_spectral_backbone_2017_metadata.json` | n/a | `1dc9c033449805ed432bffe3fd9bc80b9b2f76d7261cc6e2e6f5dec44b201df2` |
| `jpl18_h2o_cross_sections_298k.csv` | 98 | `d70d7d79405cb4b86de2186d1fd1212c332eb1eb362279f117b99daa00ce2e2c` |
| `jpl18_h2o2_cross_sections_298k.csv` | 33 | `bec01ae613d088455bdb64657b46f33bfe3cdb3b6e294c6f41fd21cbd611f4a1` |
| `jpl18_uv_cross_sections_metadata.json` | n/a | `d5459c8ca854d41e2ed7754f8550a08c9d8e015a8ee41ae4b87233ba4b7df55e` |

The generator verifies `sigma.mat` SHA256
`a98567c4f971721cec4197ad7ea17182e95df78c3a0eea880acb08fc6d560424`
and the exact JPL Publication 15-10 reference PDF SHA256
`149a4bab985402c67419e02ff8ca80202d1ba55f5383fbf69692e2184b68da08`.
Table 4B-3 is a corrected 98-row transcription and Table 4B-5 is a complete
33-row transcription; both were checked against rendered printed pages 4-43
and 4-47. Tests hard-code the required H2O/H2O2 spot rows and the documented
JPL18 199-to-189 nm correction.
The Table 4B-6 A/B coefficients are independently direct-summed at multiple
wavelength/temperature pairs. No Evaluation-20/2025 value is used
numerically; JPL20 is cited only as provenance corroboration for 189 nm.

## Geometry and optical evidence

The production geometry uses `R=6370 km`, `z_top=150 km`, the ray coordinate
`u=r0 cos(theta)+s`, impact parameter `b=r0 sin(theta)`, and exact intersections
of `[-sqrt(q^2-b^2),+sqrt(q^2-b^2)]` with the sunward ray segment. Adjacent
in-sphere lengths form the 150 shell paths. Earth shadow is altitude-specific:
for SZA greater than 90 degrees only `b<R` is shadowed; equality is illuminated
within a 16-ULP radius tolerance.

Path-sum anchors in km are: z50/SZA0 = 100;
z80/SZA60 = 137.81504100359234; z80/SZA90 = 952.8378665859158;
z80/SZA95 = 1668.4626929362385; and z100/SZA99 = 2305.927394165518.
Analytic threshold tests at 50, 80, and 100 km evaluate immediately below,
at, and above the tangent SZA. A separate 400,000-midpoint ray tracer, which
does not import production intersections, checks four near-tangent/twilight
rays to a maximum per-shell error below 0.012 km.

Shell density is the exact arithmetic endpoint mean and path length is
converted using `1 km=1e5 cm`. Synthetic tests cover zero, one, and four
absorbers, the explicit sum in optical depth, zero tau, huge tau, physical
shadow, and dimensional cancellation. Dynamic O/O3 composition tests verify
exact 50--100 km replacement, external invariance, invalid input rejection,
direct-beam monotonicity, and controlled O3 self-shielding.

## J definitions and anchors

`JH` uses strict `210<lambda<310 nm`; `J_SRC` uses Li-2020
`130<=lambda<=175 nm`; `J_LYA` is source row 28; O2/O3 totals use all 125
elements. H2O uses linear Table-4B-3 interpolation and the frozen two-channel
yields. H2O2 uses the 298 K table below 260 nm and Table-4B-6 from 260 through
350 nm. Thirteen frozen chemical temperatures below 200 K use exactly 200 K
and are marked; temperatures above 400 K raise.

Unattenuated anchors in s-1:

| Quantity | Value |
| --- | ---: |
| `JH` | 7.951381890000001e-3 |
| `J_SRC` | 3.6227120000000004e-6 |
| `J_LYA` | 3.82e-9 |
| `J_O2_TOTAL` | 4.5171738408e-6 |
| `J_O3_TOTAL` | 8.07364762308e-3 |
| `J_H2O_A` | 1.1454298921361168e-5 |
| `J_H2O_B` | 6.647332715993185e-7 |
| represented H2O total | 1.2119032192960486e-5 |
| `J_H2O2` at 298 K | 9.48327294630001e-5 |
| `J_H2O2` at 200 K | 9.062306562966788e-5 |
| H2O2 Lyman-alpha absorption upper bound | 3.7436e-6 |

The final two production anchors agree with the handoff values within
1.1e-12 relative; the difference is floating evaluation order in the degree-7
polynomial.

## Chemistry consistency and sensitivities

Across baseline profiles at SZA 0, 60, 85, 89.9, 95, and 99 degrees, every
illuminated target satisfies `J_O3_TOTAL >= JH` and
`J_O2_TOTAL >= J_SRC + J_LYA`; every shadowed J is exactly zero. An actual
80-km/SZA-60 M4B closure evaluation produces finite tendencies when the three
still-external g-factors are supplied as explicit synthetic values.

The upper-O3-tail experiment changes no frozen asset. Compared with setting
external O3 nodes at and above 109 km to zero, the maximum relative differences
above the 1e-12 s-1 floor are 9.3656e-5 (`JH`), 6.5426e-6 (`J_SRC`),
3.0558e-4 (`J_LYA`), 2.5117e-4 (`J_O2_TOTAL`), 9.2501e-5
(`J_O3_TOTAL`), 5.7039e-5 (`J_H2O2`), 1.9975e-4 (`J_H2O_A`), and
3.0558e-4 (`J_H2O_B`). No principal rate exceeds the 1% materiality threshold.
The JSON validator records every maximum absolute difference and location.

H2O2 Lyman-alpha absorption remains outside the represented 2OH production
rate. Its maximum upper-bound/production ratio above the same floor is
0.04065058478608969 at 100 km/SZA 0, below the specified 10% follow-up trigger.

## Software verification

- Full source-tree suite: 487 passed plus 13 unittest subtests.
- Five deterministic validators: all exit zero.
- Ruff: `All checks passed!`.
- `compileall`: passed.
- `uv lock --check`: passed; lock identifies package 0.5.1.
- `uv lock --check --offline`: passed.
- `uv build --clear --no-build-isolation --offline`: wheel and sdist both
  built successfully using the installed build backend. The isolated offline
  attempt could not resolve `setuptools>=68` from the runner cache and is
  recorded as an environment limitation, not hidden.
- Clean external wheel installation (`--no-deps`, system-site scientific
  dependencies): version, frozen background, five UV assets, and an actual
  SZA-60 profile passed.
- Extracted-sdist suite: 487 passed plus 13 subtests.

Machine-readable validator payloads and final artifact hashes are included in
the outer delivery under `evidence/`.

## Unchanged accepted assets

The four M4A hashes remain:

| Asset | SHA256 |
| --- | --- |
| `socrates_prescribed_vmr.csv` | `8985b4774b6e1aa91e3522758c7a33b652501601cdd167871afdc215474b4e01` |
| radiative background | `217fe7187c42a4ca8f590e1fa382ef815adffae6f5f1429816cea739f27c604f` |
| chemical background | `c1c115d840fa1b3115d7bcb7a1feca769b9dbbddd0faee5a2df0edadc4b5c291` |
| background metadata | `5b4c53276b587141201b74116faf3210e3ce0ffa0de025e767fb944b25daa75a` |

`sigma.mat` remains byte-identical at the SHA256 stated above.

## Blockers, ambiguities, and roadmap

No scientific blocker was found within M4C. The original irradiance provenance
remains weaker than the JPL18 H2O/H2O2 provenance and is explicitly labelled a
historical reconstruction. Native atomic O unavailable outside the dynamic
region is set to zero exactly as instructed and remains a documented boundary
approximation. No reproducibility blocker was encountered in R2.

The accepted arithmetic endpoint-mean density in each 1 km shell is also
retained. A future convergence/shell-discretization sensitivity should compare
it with piecewise-linear or refined-shell integration: an independent audit
found selected twilight changes of about 1--2% (near 50 km/SZA 89.9 degrees,
approximately 1.5% for `JH` and 2.2% for `J_O2_TOTAL`). This is nonblocking and
is provisionally assigned to M7, or earlier if sunrise/twilight analysis shows
material impact.

Stop here. Before authorizing more work, review the roadmap and the M4C audit.
The provisional next block would be M4D for `gA/gB/gIRA`, but neither M4D nor
M5 is implemented or authorized by this artifact.
