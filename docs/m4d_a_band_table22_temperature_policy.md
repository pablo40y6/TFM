# M4D O2 A-band Table-22 line-mixing temperature policy

Status: **SELECTED FOR HISTORICAL_2020 / NUMERICAL SENSITIVITY REQUIRED**

Branch: `milestone/m4d-design`

This note freezes how the historical branch evaluates the published Drouin et al. (2017) first-order line-mixing coefficients for the 70 principal-isotopologue A-band transitions for which Table 22 supplies an effective `Y` factor.

It deliberately does **not** replace the published effective coefficients with a newly reconstructed relaxation matrix.

## 1. Authoritative effective data

The accepted source is the frozen Drouin publisher supplement:

```text
1-s2.0-S0022407316301108-mmc1.pdf
bytes:   89406
SHA-256: 12e621d3b5d17e7648d140ea16134e3c04096bd7e47e2c1bb0e2084adeccbb51
pages:   12
```

Table 22 gives air line-mixing `Y` factors for 70 lines at exactly:

```text
200 K
250 K
296 K
340 K
```

The table states that these values were determined from the best-fit LBL parameters and augmented line mixing. The main article describes them as the condensed line-by-line dependent dispersion coefficients intended for tabulation and use in LBL codes.

The supplemental relaxation matrices and their temperature exponents remain provenance and reproducibility witnesses, but they are not substituted for the published effective Table-22 values unless an independent reconstruction reproduces Table 22 to source-rounding accuracy.

## 2. Why direct Table-22 use is selected

Independent forensics established that a naive first-order Rosenkranz evaluation of the tabulated lower-triangle matrices does not reproduce Table 22.

This is consistent with the article's stated processing chain: the multispectrum implementation includes detailed balance, a sign-convention reconciliation, empirical scaling, sub-band truncation, and an eigenvector-based transformation to effective `Y` values.

Therefore:

```text
published Table-22 Y(T)  >  an undocumented reimplementation of W -> Y
```

for the `historical_2020` production candidate.

No inferred Niro renormalization rule or modern line-mixing library may silently replace these published coefficients.

## 3. In-range temperature evaluation

For shell temperatures in the closed interval `[200, 340] K`, evaluate each line independently by piecewise-linear interpolation in temperature between the adjacent published Table-22 nodes.

Thus, for adjacent source nodes `(T0,Y0)` and `(T1,Y1)`:

```text
Y(T) = Y0 + (Y1-Y0) * (T-T0)/(T1-T0)
```

with exact recovery of every published node.

Intervals are:

```text
200..250 K
250..296 K
296..340 K
```

This interpolation is an explicit numerical convention, not a claim that Drouin prescribed linear temperature physics between nodes.

## 4. Temperatures below 200 K

Drouin Table 22 does not provide an effective Y factor below 200 K. The historical branch must not manufacture a low-temperature matrix extension.

Nominal rule:

```text
T < 200 K:
    Y_nominal(T) = Y(200 K)
```

Required low-temperature envelope:

```text
case A: clamp to Y(200 K)
case B: linear continuation of the 200..250 K segment down to the actual shell T
case C: Y = 0  (line mixing disabled only as a diagnostic bound)
```

The envelope is a numerical/source-limitation sensitivity. Cases B and C are not alternative historical baselines.

If this envelope changes any scientifically retained `gA` rate by more than `0.1%`, or changes a convergence/pass-fail conclusion, the A-band design reopens and M4D cannot be frozen.

## 5. Temperatures above 340 K

The currently frozen M4D atmospheric domain is not expected to require an A-band shell temperature above 340 K.

Fail closed if such a shell is encountered in the accepted atmosphere:

```text
T > 340 K -> NUMERICAL/DESIGN BLOCKER
```

Do not extrapolate silently.

## 6. Pressure dependence

Table-22 values are pressure-normalized coefficients. The shell-local line-mixing contribution uses the shell pressure consistently with the Drouin LBL formulation.

No empirical refit or altitude-dependent scaling is permitted.

The previously frozen isolated-line SDV semantics remain:

```text
Gam2   = S * Gam0
Shift2 = 0
anuVC  = 0
eta    = 0
```

and line mixing augments only the 70 source-supported lines through the published `Y` coefficient.

## 7. Lines without Table-22 Y

For the 21 high-J magnetic-dipole lines absent from Table 22:

```text
Y = 0
```

in the nominal candidate; no coefficient is invented.

Their integrated-strength contribution is already known to be about `0.0131464%` of historical principal-isotopologue A-band strength. Their impact must nevertheless be checked numerically over the full spherical twilight domain.

For the 59 electric-quadrupole lines:

```text
no Drouin LM coefficient is applied
```

and their contribution is separately bounded.

## 8. Validation gates

Before M4D design freeze, verify:

1. exact reproduction of all 70 x 4 Table-22 source nodes;
2. continuity at 250 K and 296 K interpolation boundaries;
3. the low-temperature clamp / linear-continuation / Y=0 envelope;
4. Y on/off sensitivity for the 21 unsupported high-J d lines;
5. q-line contribution;
6. spectral and spatial convergence at all required target altitudes/SZAs;
7. finite and non-negative total physical absorption.

The global M4D acceptance threshold remains:

```text
max relative retained-rate effect <= 0.1%
for rates above 1e-15 s^-1
```

unless the quantity under test is an intentionally retained physical effect rather than a numerical/source uncertainty.

## 9. Gate result

```text
Table-22 source bytes:                 PASS
70 x 4 effective Y values:             PASS / frozen source data
200..340 K interpolation policy:       SELECTED
T < 200 K nominal policy:              SELECTED (200-K clamp)
T < 200 K source envelope:             REQUIRED
T > 340 K:                             FAIL CLOSED
21 no-Y d lines:                       Y=0 nominal / sensitivity required
59 q lines:                            no LM
W-matrix reverse reconstruction:       NOT REQUIRED FOR BASELINE
full numerical A-band closure:         OPEN
```

This closes the previously ambiguous continuous-temperature operational rule without claiming unsupported low-temperature spectroscopy.
