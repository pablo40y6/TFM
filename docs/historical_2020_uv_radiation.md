# Historical-2020 UV/VUV direct-beam radiation

## Scope and data flow

M4C maps a supplied solar zenith angle and 51-level dynamic O/O3 profiles to
eight first-order photolysis frequencies on 50--100 km. It does not calculate
`gA`, `gB`, `gIRA`, astronomical SZA, time evolution, or a retrieval. Results
are immutable arrays with the geometry, columns, optical depth, photon field,
temperature-clamp mask, and source provenance retained as diagnostics.

## Spectral backbone and provenance limit

`uv_spectral_backbone_2017.csv` is generated from the accepted 2017
`sigma.mat` and is exactly equal, element for element, to its `wave`, `irrad`,
`sO`, `sO2`, `sO3`, and `sN2` arrays. It preserves 125 entries, the duplicate
117.30308 nm rows, and source MATLAB element 28 = 121.567 nm. Its irradiance is
used as photons cm-2 s-1 per spectral element; no delta-lambda multiplier is
introduced.

This is explicitly a historical reconstruction decision: it is the validated
project-local 2017 backbone and is not claimed to be the exact spectrum used by
Li et al. (2020) or a JPL18 spectrum. `legacy_2017` remains a separate branch;
M4C neither imports its path algorithm nor its `Jfactors` implementation.

## Geometry, shells, and shadow

The Earth radius is 6370 km. The radiative support has 151 nodes at 0--150 km
and 150 one-kilometre shells. For target radius `r0`, SZA `theta`, ray distance
`s`, ray coordinate `u = r0 cos(theta) + s`, and impact parameter
`b = r0 sin(theta)`, the top intersection is

```text
u_top = sqrt((R + 150 km)^2 - b^2)
s_top = u_top - r0 cos(theta).
```

For sphere radius `q`, the ray interval inside it is
`[-sqrt(q^2-b^2), +sqrt(q^2-b^2)]`. Intersecting that interval with
`[u0,u_top]` gives cumulative in-sphere length; adjacent cumulative differences
give every exact shell length. This naturally represents the two legs of an
illuminated twilight ray. There is no legacy fallback.

For SZA > 90 degrees the target is shadowed only if `b < R`, subject solely to
a 16-ULP radius-scale equality tolerance. A tangent ray remains illuminated.
The altitude-specific threshold is
`180 deg - asin(R/(R+z))`; therefore one SZA can shadow lower targets while
higher targets remain illuminated. Shadowed path and photon-flux rows are
exactly zero.

Node densities become shell densities through the frozen arithmetic mean
`n_shell[i] = 0.5*(n[i]+n[i+1])`. Slant columns are
`N = sum(n_shell * path_km * 1e5)` in molecule cm-2.

## Absorber profiles and optical depth

Dynamic O and O3 replace nodes 50--100 km exactly. External O3 is the accepted
M4A prescribed profile. External atomic O is native MSIS O where finite and
nonnegative, and zero where that diagnostic is unavailable; the latter is an
explicit radiative-boundary approximation, not a demonstrated negligible
effect. Fixed O2 and N2 are the M4A `0.21 M` and `0.78 M` profiles.

Only O, O2, O3, and N2 absorb. For spectral element `k`,

```text
tau[k] = sigma_O[k] N_O + sigma_O2[k] N_O2
       + sigma_O3[k] N_O3 + sigma_N2[k] N_N2
F[k] = irrad[k] exp(-tau[k]).
```

All products are `cm2 * molecule cm-3 * cm`, hence dimensionless optical
depth. Zero optical depth gives the unattenuated source, unlike the historical
legacy zero-tau special case. Huge optical depth underflows safely to zero.

## Eight photolysis definitions

All sums are over source elements, not wavelength integrals:

| Output | Definition |
| --- | --- |
| `JH` | sum `F sigma_O3` where `210 < lambda < 310 nm` |
| `J_SRC` | sum `F sigma_O2` where `130 <= lambda <= 175 nm` |
| `J_LYA` | exact `F sigma_O2` at source MATLAB element 28 |
| `J_O2_TOTAL` | sum `F sigma_O2` over all 125 elements |
| `J_O3_TOTAL` | sum `F sigma_O3` over all 125 elements |
| `J_H2O2` | sum `F sigma_H2O2(lambda,T)` over its represented production range |
| `J_H2O_A` | sum `F sigma_H2O phi_A` |
| `J_H2O_B` | sum `F sigma_H2O phi_B` |

The M4C SRC lower bound follows Li-2020 and intentionally differs from the
legacy `122 < lambda < 175 nm` mask. `J_LYA` has no nearest-bin lookup and no
0.44 factor: 0.44 is a later M4B product yield.

## H2O data, documented source correction, and reduced branching

The 98-row 298 K H2O asset is a corrected transcription of JPL18 Table 4B-3
(121--198 nm). The printed table places `199 nm -> 1.08e-20 cm2 molecule-1`
between its 188 and 190 nm rows. Because 199 nm is outside the stated table
range, the surrounding rows are sequential, and the notes assign 183--191 nm
to one source, `historical_2020` implements
`189 nm -> 1.08e-20 cm2 molecule-1` as a typographical correction. JPL20 Table
4B-2-2 independently prints 189 nm for the same value; it is recorded only as
corroboration and is not the numerical source. The complete structured record
is in `jpl18_uv_cross_sections_metadata.json`, and the generator comments the
corrected row directly.

The corrected table is linearly interpolated onto the inherited backbone and
set to zero outside its range. The historical_2020 reduced two-channel H2O
yields, based on the frozen Brasseur/JPL-informed model approximation, use
`phi_A=0.89, phi_B=0.11` for `121 <= lambda < 147 nm`, and
`phi_A=1, phi_B=0` for `147 <= lambda <= 198 nm`. It is a reduction compatible
with the already accepted chemistry, not exact JPL18 quantum yields and not a
complete account of all VUV H2O products. No product channel is added.
Numerically, `J_H2O_A + J_H2O_B` closes to the represented total.

## H2O2 data, temperature rule, and Lyman-alpha limit

All 33 JPL18 Table 4B-5 rows are retained. For `190 <= lambda < 260 nm`, the
298 K table is linearly interpolated. For `260 <= lambda <= 350 nm`, Table
4B-6 is evaluated as

```text
1e21 sigma = chi sum(A_n lambda^n) + (1-chi) sum(B_n lambda^n)
chi = (1 + exp(-1265/T))^-1.
```

The exact A/B coefficients are stored in source and metadata. The JPL validity
range is 200--400 K: levels below 200 K use exactly 200 K and are marked in a
diagnostic mask; temperatures above 400 K raise. The frozen baseline contains
13 clamped levels (88--100 km).

The reduced chemistry has only `H2O2 + hv -> 2OH`. JPL18 gives an H2O2
Lyman-alpha absorption cross section but no complete matching 2OH branching
prescription, so it is excluded from production and reported separately as
`J_H2O2_LYA_ABS_UPPER = 9.8e-18 * F_LYA`. Across the specified M4C baseline
cases its largest ratio to represented production above the 1e-12 s-1 rate
floor is 4.0651%, at 100 km and SZA 0; this does not trigger the specified 10%
follow-up flag.

## Upper-O3-tail sensitivity

The accepted M4A external O3 tail was compared with an alternative that sets
only prescribed nodes `z >= 109 km` to zero, at SZA 0, 60, 85, 89.9, 95, and
99 degrees. The largest relative changes above the 1e-12 s-1 rate floor are:

| J | Maximum relative change |
| --- | ---: |
| `JH` | 0.00937% |
| `J_SRC` | 0.000654% |
| `J_LYA` | 0.03056% |
| `J_O2_TOTAL` | 0.02512% |
| `J_O3_TOTAL` | 0.00925% |
| `J_H2O2` | 0.00570% |
| `J_H2O_A` | 0.01997% |
| `J_H2O_B` | 0.03056% |

No principal O2/O3 J changes by more than 1%; the tail is therefore not
material under the specified M4C criterion. Full absolute differences and
locations are emitted by `validate_historical_2020_uv.py`.

## Deferred shell-discretization sensitivity

The frozen 1 km shell implementation uses arithmetic endpoint-mean densities,
equivalent to one constant density per shell. An independent audit found that
replacing this with piecewise-linear density integration can change selected
twilight values by roughly 1--2% (for example near 50 km/SZA 89.9 degrees,
about 1.5% for `JH` and 2.2% for `J_O2_TOTAL`). This is a nonblocking future
convergence/shell-discretization sensitivity for scientific validation,
provisionally M7 or earlier if sunrise/twilight results make it material. M4C-R2
does not change the accepted shell calculation.

## Validation and remaining boundary

Tests independently verify the corrected source transcription, including the
hard-coded 189 nm row and absence of the printed 199 nm typo, exact masks, unattenuated
anchors, analytic paths, a high-resolution numerical ray trace, shell units,
synthetic optical depths, physical shadow, controlled self-shielding, all M4B
gross-subset invariants, and an actual local-closure smoke evaluation using
explicit synthetic g-factors.

M4D may later determine `gA`, `gB`, and `gIRA`; M4C does not implement or infer
them. HITRAN line-by-line excitation, astronomy, the 255-ODE RHS, BDF/Radau,
periodic cycling, and retrieval remain outside this milestone.
