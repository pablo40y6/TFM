# M4D final design review and numerical forensics

Status: **FINAL DESIGN REVIEW FAILED — DESIGN NOT FROZEN / NO IMPLEMENTATION AUTHORIZED**

Branch: `milestone/m4d-design`

This review completes the requested pre-implementation numerical forensics as far as the available historical inputs permit. It does not implement M4D, alter the accepted M4C-R2 baseline, authorize M5, or redistribute the supplied SpectralCalc line records.

## 1. Review outcome

Most M4D inputs and numerical conventions now close reproducibly:

- the supplied SpectralCalc export reproduces every established source and target-subset fingerprint;
- the standard HITRAN/TIPS-2017 temperature scaling is fully specified and numerically checked;
- the Wehrli-1985 unattenuated `g0(T)` reconstruction passes the declared historical-anchor tolerance without empirical scaling;
- a deterministic line-centred Doppler quadrature converges below `0.1%`;
- shell-local temperature scaling is necessary;
- the accepted spherical M4C geometry can be reused, but its atmospheric integration must be sub-stratified more finely than one kilometre to meet the M4D `0.1%` numerical tolerance;
- the historical baseline CIA decision remains monomer-only, with CIA retained as a later twilight sensitivity.

The review does **not** support freezing M4D because the previously proposed Doppler-only baseline is not uniformly adequate over the required altitude/SZA domain. A Voigt attenuation sensitivity changes selected post-90-degree rates by tens of percent, and even the lower-bound A-band result at `50 km, SZA=89.9 deg` changes by about `0.47%`. Moreover, simple Voigt far-wing truncation is not converged to `0.1%` for A and B at the declared `1e-15 s^-1` diagnostic floor. The minimum pressure-broadening/line-wing treatment therefore remains a numerical and scientific-design blocker.

## 2. Raw SpectralCalc export verification

The attached file was read locally only. It is not committed, copied into this repository, or reproduced below.

Raw identity and structure independently reproduced:

```text
byte size       2,268,239
SHA-256         6b4acbc01cb649891f2d8597875c9cd8e4805cfdd4d3b7841c2d18cbf718de12
parsed records  14,085
record width    160 ASCII characters for every transition
molecule        7 for all 14,085 records
```

Whole-export isotopologue inventory:

| local iso | records | range (cm^-1) |
| ---: | ---: | ---: |
| 1 | 1,897 | 0.000001–17,272.060042 |
| 2 | 875 | 1.691663–15,852.677413 |
| 3 | 11,313 | 0.000001–14,537.832827 |

Semantic target subsets reproduce the established fingerprints exactly:

| field | transition | lines by iso 1/2/3 | range (cm^-1) | sum `sw` at 296 K | canonical SHA-256 |
| --- | --- | --- | --- | ---: | --- |
| `gA` | `b(0) <- X(0)` | 150 / 140 / 140 | 12,849.566990–13,339.201391 | `2.254662017660e-22` | `176a6c21ee37b1244bd11ef7047f6e31f7cada7edff2c3498f31f8d1f2e92eea` |
| `gB` | `b(1) <- X(0)` | 87 / 128 / 105 | 14,284.825910–14,557.976587 | `1.496427012400e-23` | `bb5f8b26a2ad3c9dc31870506c3c05bcdb115b7c5b06d7141c9660c952d83c2d` |
| `gIRA` | `a(0) <- X(0)` | 230 / 322 / 283 | 7,571.882333–8,170.942339 | `3.227316866330e-24` | `8d06f322aa4058ab03150a705bf9765fe356a2c7ecd06df98379c46062d295ad` |

The established target-band HITRAN2016 source gate therefore remains passed. The known full-range incompleteness for isotopologues 1 and 2 remains outside the selected A/B/IRA systems and is not hidden.

## 3. Historical TIPS-2017 scaling

The numerical source used for this review is only the pinned historical implementation:

```text
repository  hitranonline/hapi
commit      f41d9911f2631eed51b96d6c617b4f27786ad477
path        hapi/hapi.py
Git blob    caeab1bfaa278b5420adef7efe7ab566991ba763
version     HAPI 1.1.0.8.2
```

No current HAPI installation or current HITRAN data was used as a numerical source.

For a standard HITRAN line intensity `S(296)` in `cm^-1/(molecule cm^-2)`, line centre `nu0` and lower-state energy `E''` in `cm^-1`, the required scaling is

```text
S(T) = S(296)
       * Q(296)/Q(T)
       * exp[-c2 E'' (1/T - 1/296)]
       * [1 - exp(-c2 nu0/T)] / [1 - exp(-c2 nu0/296)]

c2 = h c / k_B = 1.4387768775039336 cm K
Tref = 296 K
```

`Q(T)` is selected by local isotopologue `1`, `2`, or `3` and evaluated with the pinned HAPI `AtoB` three-/four-point Lagrange interpolation. Standard HITRAN `sw` is already terrestrial-abundance weighted; no additional abundance factor is applied. The scaled strength retains the HITRAN integrated-intensity units and multiplying it by a normalized profile in `(cm^-1)^-1` produces cross section in `cm^2 molecule^-1`.

Historical partition-sum anchors reproduced:

| T (K) | Q iso 1 | Q iso 2 | Q iso 3 |
| ---: | ---: | ---: | ---: |
| 180 | 131.3804 | 276.5444 | 1,614.965 |
| 200 | 145.9015 | 307.2954 | 1,794.512 |
| 220 | 160.4275 | 338.0581 | 1,974.123 |
| 240 | 174.9609 | 368.8395 | 2,153.834 |
| 260 | 189.5058 | 399.6500 | 2,333.703 |
| 280 | 204.0679 | 430.5039 | 2,513.805 |
| 296 | 215.7344616 | 455.2299560 | 2,658.1201680 |

The 296-K values are interpolated, not tabulated; exact tabulated 300-K anchors remain `218.6540`, `461.4188`, and `2694.239`.

Band-summed scaled strengths are:

| T (K) | A | B | IRA |
| ---: | ---: | ---: | ---: |
| 180 | `2.2460823801e-22` | `1.4868147499e-23` | `3.2157537130e-24` |
| 200 | `2.2485052467e-22` | `1.4889952178e-23` | `3.2191118194e-24` |
| 220 | `2.2504654055e-22` | `1.4909330161e-23` | `3.2218108857e-24` |
| 240 | `2.2520445936e-22` | `1.4926633156e-23` | `3.2239622450e-24` |
| 260 | `2.2532806310e-22` | `1.4941953186e-23` | `3.2256126539e-24` |
| 280 | `2.2541828902e-22` | `1.4955221393e-23` | `3.2267653696e-24` |
| 296 | `2.2546620177e-22` | `1.4964270124e-23` | `3.2273168663e-24` |

## 4. Unattenuated Wehrli-1985 validation

The frozen candidate convention was evaluated directly:

1. `lambda_nm = 1e7 / nu_cm1`;
2. linear interpolation of the Wehrli `W m^-2 nm^-1` table in wavelength at every line centre;
3. photon-energy conversion followed by the absolute wavelength/wavenumber Jacobian;
4. `g0(T) = sum_i S_i(T) Phi_sun(nu_i)`.

This is the normalized-line-profile unattenuated limit; no bandwidth factor or empirical normalization is introduced.

| T (K) | `gA0` (s^-1) | `gB0` (s^-1) | `gIRA0` (s^-1) |
| ---: | ---: | ---: | ---: |
| 180 | `6.1914394520e-9` | `3.5752856768e-10` | `1.4549983481e-10` |
| 200 | `6.1963256585e-9` | `3.5805572358e-10` | `1.4573674701e-10` |
| 220 | `6.1999597393e-9` | `3.5852735538e-10` | `1.4593873602e-10` |
| 240 | `6.2025842093e-9` | `3.5895153697e-10` | `1.4611114500e-10` |
| 260 | `6.2043175651e-9` | `3.5933010076e-10` | `1.4625641629e-10` |
| 280 | `6.2051968875e-9` | `3.5966103384e-10` | `1.4637502395e-10` |
| 296 | `6.2052846913e-9` | `3.5988913888e-10` | `1.4645036484e-10` |

At 296 K:

- A is `+15.99%` relative to the Zhu et al. `5.35e-9 s^-1` anchor;
- IRA is `-4.90%` relative to the Zhu et al. `1.54e-10 s^-1` anchor;
- A+B is `6.56517e-9 s^-1`, `+18.08%` relative to the Marsh et al. combined `5.56e-9 s^-1` anchor;
- B is `+22.41%` relative to the independent `2.94e-10 s^-1` scale recorded in the prior design evidence.

All are within the predeclared `30%` investigate threshold. They are validation results, not calibration targets, and no empirical scaling is justified.

## 5. Line-shape sensitivity

### 5.1 Local widths and normalized profile checks

For the strongest 296-K source line in each target system, the local Lorentz/Doppler HWHM ratio and centre-profile change are:

| band / line centre | at 50 km: `gammaL/gammaD` | centre Voigt vs Doppler | at 100 km: `gammaL/gammaD` | centre Voigt vs Doppler |
| --- | ---: | ---: | ---: | ---: |
| A / 13,142.583253 cm^-1 | `0.2993%` | `-0.2806%` | `0.000197%` | `-0.000185%` |
| B / 14,546.003143 cm^-1 | `0.2748%` | `-0.2576%` | `0.000179%` | `-0.000168%` |
| IRA / 7,880.637233 cm^-1 | `0.5132%` | `-0.4803%` | `0.000350%` | `-0.000329%` |

The ratios decrease monotonically at the inspected 60, 70, 80 and 90-km levels. Doppler profiles integrated over `+/-8` Doppler HWHM close to unity at printed precision. Voigt profiles integrated over `+/-20` Doppler HWHM close to `0.9999046` (A), `0.9999124` (B), and `0.9998364` (IRA) at 50 km; the omitted target-profile area is below `0.02%` in these checks.

### 5.2 Representative strong-line transfer

Using shell-local temperature, pressure and O2 along the accepted spherical paths, and comparing the strongest line's own Doppler and Voigt source/attenuation contribution:

- at `50 km, SZA=0`, the changes are `+0.265%` (A), `+0.0055%` (B), and `-0.0077%` (IRA);
- at `50 km, SZA=89.9`, they are `+9.50%` (A), `+0.567%` (B), and `+0.320%` (IRA);
- at `50 km, SZA=95`, they are `-72.4%` (A), `-63.3%` (B), and `-57.4%` (IRA).

The post-90-degree values are illuminated but their rays reach much denser layers below the 50-km chemistry boundary. This is the concrete failure in the earlier width-ratio argument: checking only local pressure at chemistry levels does not bound broadening along a twilight ray.

### 5.3 Full-band Voigt-attenuation sensitivity

An all-line sensitivity used the exact Doppler source decomposition and changed the shell attenuation profiles from Doppler to Voigt. This isolates the path-broadening effect; the target-profile effect above is separate.

With a `+/-20 cm^-1` Voigt attenuation window, the maximum full-band changes relative to Doppler are:

- considering rates above `1e-10 s^-1`: A `0.4725%`, B `0.0630%`, IRA `0.0515%`, all at or bounded by the lower-bound/near-twilight cases;
- considering rates above `1e-12 s^-1`: A `33.6%`, B `19.5%`, IRA `23.4%` in selected post-90-degree cases;
- at the declared `1e-15 s^-1` floor: A reaches `73.8%` and IRA `25.1%` in selected `SZA=99 deg` cases.

The A-band result alone violates a `0.1%` adequacy criterion even before the large post-90-degree differences are considered. Doppler-only is therefore **not accepted as the full-domain M4D baseline by this review**.

### 5.4 Unresolved Voigt wing convergence

Changing the Voigt attenuation window from `+/-10` to `+/-20 cm^-1` changes the weakest retained cases by:

| band | maximum relative change above `1e-15 s^-1` | above `1e-12 s^-1` | above `1e-10 s^-1` |
| --- | ---: | ---: | ---: |
| A | `1.734%` | `0.228%` | `0.000016%` |
| B | `0.270%` | `0.0117%` | `0.0000012%` |
| IRA | `0.0727%` | `0.0031%` | `0.00000028%` |

Thus a plain truncated Voigt sensitivity is converged for ordinary/high-rate cases and for IRA at the declared floor, but it is not converged for weak A/B twilight rates. Extending an isolated-line Voigt profile to arbitrarily distant wings is also not automatically a physically valid substitute for the HITRAN2016 A-band line-shape/line-mixing treatment.

Required resolution before freeze:

1. define the intended pressure-broadened validation/baseline profile, including whether line mixing or a physically sourced far-wing cutoff is required;
2. evaluate both target excitation and shell attenuation consistently with that profile;
3. demonstrate `<=0.1%` numerical convergence above the declared absolute floor;
4. state explicitly whether extremely attenuated post-90-degree rates remain inside the baseline acceptance domain or are zeroed only by the physical Earth-shadow mask, never by a numerical convenience threshold.

## 6. Spectral quadrature

For the Doppler calculation, an exact integrand decomposition by target line was used:

```text
g = sum_i integral S_i(T_target) g_i(nu,T_target)
                   Phi_sun(nu) exp[-tau_total(nu)] dnu
```

This remains valid when neighbouring line supports overlap because the target cross-section sum is decomposed, while `tau_total` includes every overlapping absorber line. Each line is integrated on deterministic Gauss-Legendre nodes centred on its source wavenumber.

Against a `+/-10 HWHM`, 128-point reference over representative altitudes and `SZA = 0, 60, 85, 89, 89.9, 95, 99 deg`, `+/-8 HWHM` with 64 points gives maximum relative differences:

| band | maximum relative difference | location |
| --- | ---: | --- |
| A | `0.07584%` | 50 km, 95 deg |
| B | `0.04164%` | 50 km, 95 deg |
| IRA | `0.00120%` | 100 km, 99 deg |

At 128 points, expanding support from 8 to 10 HWHM changes A by at most `0.00127%`, B by `0.000188%`, and IRA by `0.000047%` in the tested domain.

Therefore `+/-8 Doppler HWHM`, 64-point line-centred Gauss-Legendre quadrature is an acceptable Doppler algorithm under the `0.1%` gate. It is not, by itself, the final algorithm for a pressure-broadened design because the Voigt wing rule remains unresolved.

Indicative single-process runtimes for four altitudes and seven SZAs were below three seconds per band for the strictest Doppler reference on the audit machine. The line-decomposition approach scales approximately with target-line count, quadrature order, number of shell temperatures, and number of altitude/SZA path cases; correctness and deterministic ordering remain the acceptance priorities.

## 7. Shellwise temperature and path convergence

The required optical depth is

```text
tau(nu,z,SZA) = sum_shell sigma(nu,T_shell) n_O2,shell ds_shell
```

Replacing it by one target-temperature cross section multiplied by total O2 column is not adequate. Relative differences reach:

- A: `45.1%` above `1e-12 s^-1` and `16.7%` above `1e-10 s^-1`;
- B: `34.3%` above `1e-12 s^-1` and `2.19%` above `1e-10 s^-1`;
- IRA: `39.2%` above `1e-12 s^-1` and `2.11%` above `1e-10 s^-1`.

Shell-local temperature scaling is therefore mandatory.

The accepted M4C spherical intersections, Earth radius, 150-km top, shadow mask and endpoint-mean density convention are retained. For M4D accuracy, however, evaluating the atmosphere only in one-kilometre shells misses the `0.1%` target in twilight cases. Relative to a `0.125 km` sub-stratification, the largest one-kilometre differences are:

```text
A     0.846%
B     0.537%
IRA   0.600%
```

Using piecewise-linear interpolation of the accepted one-kilometre node profiles and exact spherical intersections on `0.125 km` sub-shells gives, relative to `0.0625 km`:

```text
A     0.0335%
B     0.0211%
IRA   0.0274%
```

The geometry itself is not replaced. The resolved M4D rule is to sub-stratify the accepted profile/path calculation to `0.125 km`, with `0.0625 km` retained as the convergence check. Any implementation should generate these sub-shells deterministically from the accepted node profiles and must not alter the M4C-R2 implementation used by existing UV results.

Representative refined Doppler rates (`0.125 km`) include:

| case | `gA` | `gB` | `gIRA` | units |
| --- | ---: | ---: | ---: | --- |
| 50 km, 0 deg | `3.720712e-9` | `3.475611e-10` | `1.451101e-10` | s^-1 |
| 50 km, 89.9 deg | `1.793589e-10` | `1.403230e-10` | `1.132164e-10` | s^-1 |
| 50 km, 95 deg | `1.360579e-11` | `5.497490e-12` | `7.574985e-12` | s^-1 |
| 90 km, 99 deg | `4.967248e-13` | `5.636151e-13` | `7.018363e-13` | s^-1 |
| 100 km, 0 deg | `6.190972e-9` | `3.576759e-10` | `1.455695e-10` | s^-1 |
| 100 km, 95 deg | `1.817083e-9` | `3.268598e-10` | `1.423722e-10` | s^-1 |
| 100 km, 99 deg | `2.559137e-12` | `1.467075e-12` | `1.511254e-12` | s^-1 |

These are design-forensics outputs, not accepted production assets.

## 8. IRA CIA/continuum decision

The existing evidence supports option **B**:

**Exclude CIA/continuum from the historical M4D baseline, but require it as a documented later twilight sensitivity.**

The baseline `gIRA` source is the first-order monomer `a(0)-X(0)` excitation represented by the accepted 835-line subset. Monomer line absorption supplies baseline solar attenuation. O2-O2/O2-N2 CIA is not silently folded into the first-order coefficient and is not added merely because modern HITRAN exposes CIA products.

This does not declare CIA negligible. Smith & Newnham, Zhu et al. and HITRAN2016 establish its physical relevance around 1.27 microns, especially for long low-tangent rays. A later sensitivity needs an exact historical CIA source, pair-density and temperature conventions, and a decision on attenuation versus excitation yield. It does not block the monomer baseline design, but the eventual sunrise/near-shadow application must disclose the omission.

## 9. Validation and implementation acceptance criteria retained for the eventual freeze

Any revised final design and later implementation must require:

1. exact verification of the raw export identity and all three canonical subset hashes before derivation;
2. exact TIPS table anchors and interpolation regression checks for isotopologues 1-3;
3. `S(296) == sw` to numerical roundoff and no second abundance factor;
4. exact Wehrli interpolation/unit-conversion anchor tests;
5. the `g0(T)` table above reproduced deterministically, with no empirical scaling;
6. normalized line-profile strength closure and finite, nonnegative cross sections/rates;
7. a pressure-broadened profile/wing rule that converges to `<=0.1%` above `1e-15 s^-1` or an independently justified revised absolute floor approved before implementation;
8. shellwise temperature scaling and `0.125` versus `0.0625 km` path convergence `<=0.1%` over all 51 targets and the final SZA validation set;
9. exact zero only for physical shadow, with the unattenuated limit recovered at zero column;
10. monotonic non-increase of direct-beam excitation when absorber column is increased at fixed target state;
11. source-line-order invariance;
12. retained M1–M4C-R2 tests and validators passing unchanged;
13. implementation evidence for all 51 altitudes at `SZA = 0, 60, 85, 89, 89.9, 95, 99 deg`, plus tangent/just-shadowed boundary cases.

## 10. Exact remaining blockers

### Numerical convergence blocker

- A/B Voigt far-wing attenuation does not meet the declared `0.1%` gate at the `1e-15 s^-1` floor with the tested `+/-20 cm^-1` window.

### Scientific design blocker

- The minimum acceptable pressure-broadened treatment is unresolved: ordinary isolated-line Voigt, a finite physically justified cutoff, and/or HITRAN2016 A-band line mixing must be selected from historical evidence.
- The pressure-broadened target excitation profile and shell attenuation must then be evaluated consistently across the full 50–100 km/SZA domain.

### Source/provenance blocker

- If line mixing or a non-Voigt far-wing model is required, the exact historical HITRAN2016 parameters and references needed for that treatment must be shown to be present in, or recoverable consistently with, the accepted source chain. The supplied 160-character records alone do not establish a complete executable line-mixing model.

### Environment/tool limitation

- None blocks the conclusions above. The raw source remained local and uncommitted as required. Numerical analysis used temporary uncommitted tooling.

## 11. Gate decision

**M4D DESIGN IS NOT FROZEN.**

Do not create `docs/m4d_final_design_specification.md`, do not mark M4D ready for implementation, and do not implement production code. The next design-only task should resolve the historical pressure-broadening/line-mixing and far-wing rule, rerun the full profile and path convergence tests, and only then decide whether the final specification can be frozen.

