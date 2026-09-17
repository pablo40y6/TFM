# M4D 1.27-micron Maté CIA materialization audit

Status: **HISTORICAL NUMERICAL BLOCKS MATERIALIZED / HITRAN2016 PAIR-SEMANTIC CORRECTION APPLIED / SOURCE GATE PASS**

Branch: `milestone/m4d-design`

This audit records the recovery of the historical Maté et al. (1999) 1.27-micron CIA numerical spectra required for the M4D Option-B twilight sensitivity. It does not add CIA to the monomer `gIRA` production term, alter M4C-R2, or authorize M5.

## 1. Why HITRAN2012 is a valid recovery witness

HITRAN2016 Section 4.1 explicitly states that:

- all 1.27-micron CIA data included in HITRAN2016 for this transition are from Maté et al. (1999), DOI `10.1029/1999JD900824`;
- pure-O2 spectra belong in `O2-O2`;
- 21:79 O2:N2 air-mixture spectra belong in `O2-Air`;
- HITRAN2012 contained an error in this region: its `O2-O2` file accidentally contained `O2-Air` spectra;
- the 2016 release corrected the pair semantics and introduced/used `O2-Air` explicitly for atmospheric air mixtures;
- atmospheric modelling must not add a separate O2-O2 term on top of the O2-Air product for the same mixture.

Therefore the mislabelled HITRAN2012 numerical blocks are a direct historical byte witness for the Maté air-mixture spectra, provided the pair label is interpreted using the explicit HITRAN2016 correction rather than the erroneous 2012 header label.

This is not a silent modern substitution: both the numerical file and the correction are historical HITRAN-era sources.

## 2. Historical archive acquisition

The surviving Harvard/CfA HITRAN2012 archive was queried directly.

Directory:

```text
https://lweb.cfa.harvard.edu/HITRAN/HITRAN2012/CIA/Main-Folder/O2-O2/
```

It exposes one main file:

```text
O2-O2_2011.cia
```

Reproducibly acquired identity:

```text
bytes:   1938473
SHA-256: 8cc3ecc87bf7a02492b385ecc71abf279b058da853aea768825deb81237d5ee3
format:  ASCII text
access:  2026-09-17 UTC via GitHub-hosted runner
```

The raw file is historical acquisition evidence and is not committed to the repository.

For comparison, the contemporaneous HITRAN2012 `O2-N2_2011.cia` file was also recovered:

```text
bytes:   1734297
SHA-256: ea72413f7276dd6114fb65547445bfedd8de8e88df7d77c3e93d0735666ce9dd
```

Its 1.27-micron blocks are primarily older 198/229/295-K mixture datasets and are **not** used as the Maté/HITRAN2016 Option-B source. This negative control prevents a false 2012-O2-N2 -> 2016-O2-Air rename.

## 3. Maté blocks found in the historically mislabelled O2-O2 file

`O2-O2_2011.cia` contains exactly three contiguous 1.27-micron blocks with the Maté temperature triplet and reference id `10`:

| T (K) | Header spectral range (cm^-1) | Points | Header line | Raw block bytes | Raw block SHA-256 |
| ---: | ---: | ---: | ---: | ---: | --- |
| 253 | 7450.380 - 8477.180 | 4194 | 60046 | 92369 | `58366c46162ca55c84aecd8b81bdadc1f5a68a27db0fbbd615a401dcc21f0bfc` |
| 273 | 7500.089 - 8486.485 | 4029 | 64241 | 88739 | `09a1e93c23004c0b12acf3e9b97fcb44f4bd32872e7ad1c6441225f0ab56b545` |
| 296 | 7450.132 - 8487.465 | 4237 | 68271 | 93315 | `19bd3c333c56dc9dd90019b57d014a69db420cae139a33a1c470557b1ad78e08` |

Each block hash covers its original historical header plus exactly the declared number of following spectral records, preserving the source byte representation including line endings.

The source headers are:

```text
O2-O2 7450.380 8477.180 4194 253.0 ... ref 10
O2-O2 7500.089 8486.485 4029 273.0 ... ref 10
O2-O2 7450.132 8487.465 4237 296.0 ... ref 10
```

The **`O2-O2` label is known erroneous pair metadata for these air-mixture spectra** under the explicit HITRAN2016 correction. The spectral numbers themselves are retained byte-for-byte.

## 4. Frozen pair-semantic interpretation

For M4D historical CIA sensitivity, interpret the recovered three blocks as:

```text
historical numerical values:
    unchanged Maté block values from O2-O2_2011.cia

historical pair semantics:
    O2-Air, according to the explicit HITRAN2016 correction

perturber density:
    n_air = n_O2 + n_N2 under the HITRAN air convention

optical depth:
    tau_CIA(nu) = sum k_O2-Air(nu,T) * n_O2 * n_air * ds
```

Do not numerically modify the blocks merely to make their header label look modern. The implementation/source-materialization layer should carry the original block hashes plus a separate semantic override `pair = O2-Air (HITRAN2016 correction)`.

Do not add a second O2-O2 term for the same atmospheric mixture.

## 5. Temperature policy

The previously frozen source-limited temperature rule is retained:

```text
253 <= T <= 296 K:
    interpolate linearly in T between the measured Maté spectra

T < 253 K:
    nominal sensitivity = 253-K endpoint spectrum

T > 296 K:
    nominal sensitivity = 296-K endpoint spectrum

outside measured source range:
    additionally propagate a min/max envelope from the three measured spectra
```

Because the three historical spectra have slightly different spectral grids/ranges, a deterministic common spectral evaluation rule is required before temperature interpolation. Preferred rule:

1. evaluate each historical spectrum by deterministic linear interpolation in wavenumber only within its own tabulated support;
2. for a requested wavenumber inside the accepted IRA calculation domain, use only temperature spectra that cover that point;
3. do not extrapolate a CIA spectrum beyond its historical wavenumber support;
4. define the usable CIA support as the union needed by the accepted IRA monomer quadrature, while reporting any target nodes not covered by all temperature sets;
5. convergence/sensitivity evidence must show that edge-support handling does not affect retained `gIRA` cases beyond the project tolerance.

Do not use the post-2016 theoretical temperature extension to fill cold shells silently.

## 6. Negative values in the experimental spectra

The raw experimental blocks contain small negative coefficients at some wing/grid points:

```text
253 K: 360 negative samples
273 K:  19 negative samples
296 K: 822 negative samples
```

These are experimental baseline/noise behaviour, not physically negative CIA opacity.

Observed raw coefficient maxima are approximately:

```text
253 K: 1.191e-45 cm^5 molecule^-2
273 K: 1.120e-45 cm^5 molecule^-2
296 K: 1.091e-45 cm^5 molecule^-2
```

A numerical rule for negative experimental samples is still required before execution. It must be declared and sensitivity-tested; do not silently clip, take absolute values, or spline through them.

The preferred candidate is:

```text
nominal physical opacity: max(k_raw, 0)
noise sensitivity: compare against unmodified linear interpolation before the final nonnegative optical-depth evaluation
```

but this is not frozen until its effect on `gIRA` is quantified.

## 7. Current HITRAN data are a negative control only

The present HITRAN `O2-air_2024.cia` was also acquired for source forensics:

```text
bytes:   528988
SHA-256: 737e91ea6e340df19cc19398ff22f310fbd59dcf675a669f9eb6282a7cbc77b3
```

Its 1.27-micron products use later 2019/2021 experimental and 2023 theoretical sources. They are **not** substituted for the historical Maté blocks.

Likewise:

```text
O2-Air_altern_2016.cia
SHA-256 6da6da146f126fac08378763318bd78855f091de1e881acbebf2ed9694e36849
```

is an A-band CIA alternate dataset around 13,000 cm^-1, not the required 1.27-micron product.

## 8. CIA source gate result

```text
historical Maté source family:       PASS
historical source file bytes:        PASS
three Maté temperature blocks:       PASS
per-block byte hashes:               PASS
HITRAN2016 O2-Air semantic mapping:  PASS
no-double-counting rule:             PASS
cold-shell policy:                   PASS
spectral-grid evaluation details:    PARTIAL / numerical validation pending
negative-sample policy:              OPEN / sensitivity pending
final twilight CIA sensitivity:      OPEN
```

The exact historical numerical source is no longer an external acquisition blocker. M4D still cannot freeze until the CIA spectral/noise handling and full twilight sensitivity pass the numerical gate.
