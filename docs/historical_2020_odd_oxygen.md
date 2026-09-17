# Milestone 4B odd-oxygen photolysis contract

## Scope and historical correction

M3 correctly implemented its then-frozen single-level specification. During
M4 radiation design, comparison with total `JO2`/`JO3` in Anqi Li (2017) and
the odd-oxygen continuity equations in Brasseur and Solomon (2005) exposed a
specification-level omission for future dynamic O/O3 integration. M4B
supersedes only M3 photolysis bookkeeping. It does not change QSSA mathematics,
thermal chemistry, airglow losses, background profiles, or legacy code.

M4B itself calculates no radiation. M4C now supplies its five O2/O3 J inputs
from the historical UV kernel; the partition equations below remain unchanged.
HITRAN and the three O2 excitation g-factors remain outside M4C.

## Eleven-field forcing contract

In exact dataclass order:

```text
JH, J_SRC, J_LYA, J_O2_TOTAL, J_O3_TOTAL,
J_H2O2, J_H2O_A, J_H2O_B, gA, gB, gIRA
```

All values must be finite and nonnegative. Because `JH`, `J_SRC`, and `J_LYA`
are gross parent-photodissociation rates in known, non-overlapping spectral
subsets, the forcing contract first requires

```text
J_O3_TOTAL >= JH
J_O2_TOTAL >= J_SRC + J_LYA
```

These are **gross photolysis subset constraints**. The factors 0.9 and 0.44
are product quantum yields; they do not reduce the number of parent molecules
photodissociated in those subsets. After validating the gross subsets, the
unchanged reduced-product partition is

```text
J2_star   = J_SRC + 0.44 J_LYA
J2_ground = J_O2_TOTAL - J2_star
J3_star   = 0.9 JH
J3_ground = J_O3_TOTAL - J3_star
```

The gross-subset and represented-excited-channel comparisons are distinct and
both raise `ValueError` when violated. Each uses a documented relative
tolerance of `64*machine_epsilon`, scaled by the larger compared magnitude
(and the minimum positive normal float as a zero floor). This accepts only
floating-point equality noise. A one-ULP-low gross total is accepted, but the
effective ground complement is still calculated from the formulas above and
is not normalized to zero. Only a tiny negative *excited-channel complement*
within its own comparison tolerance is normalized to zero; this is not broad
concentration or rate clipping.

## Reduced event semantics

| Flux | Rate | Dynamic contribution | Algebraic source |
| --- | --- | --- | --- |
| `O3_HARTLEY_GROSS` | `JH O3` | none; diagnostic only | none |
| `O3_HARTLEY_PRODUCTS` | `J3_star O3` | `-O3`, `+Delta` | `+O1D` |
| `O3_PHOTOLYSIS_GROUND_EFFECTIVE` | `J3_ground O3` | `-O3`, `+O` | none |
| `O2_SRC` | `J_SRC O2` | `+O` | `+O1D` |
| `O2_LYMAN_ALPHA` | `0.44 J_LYA O2` | `+O` | `+O1D` |
| `O2_PHOTOLYSIS_GROUND_EFFECTIVE` | `J2_ground O2` | `+2O` | none |

`O3_HARTLEY_UNTRACKED` and `O2_LYMAN_ALPHA_UNTRACKED` remain useful
diagnostic subsets. They are no longer missing products: their reduced atom
budget is contained in the effective ground channels. The model does not claim
that detailed VUV products consist microscopically of only two channels.

The corrected photolysis tendency rows are therefore:

| Flux | O | O3 | H | R_H | Delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| `O3_HARTLEY_PRODUCTS` | 0 | -1 | 0 | 0 | +1 |
| `O3_PHOTOLYSIS_GROUND_EFFECTIVE` | +1 | -1 | 0 | 0 | 0 |
| `O2_SRC` | +1 | 0 | 0 | 0 | 0 |
| `O2_LYMAN_ALPHA` | +1 | 0 | 0 | 0 | 0 |
| `O2_PHOTOLYSIS_GROUND_EFFECTIVE` | +2 | 0 | 0 | 0 | 0 |

The gross Hartley diagnostic has no tendency row, preventing a second O3
parent loss.

## Acceptance identities

For O2 photolysis, independent direct and algebraic terms give

```text
direct O = (J2_star + 2 J2_ground) O2
O1D      = J2_star O2
sum      = 2 J_O2_TOTAL O2
```

For O3 photolysis and `Ox_reduced = O + O1D + O3`, excluding Delta because it
is an excited O2 molecule,

```text
-J_O3_TOTAL O3 + J3_ground O3 + J3_star O3 = 0.
```

The O1D QSSA source remains exactly the accepted expression:

```text
P_O1D = 0.9 JH O3 + J_SRC O2 + 0.44 J_LYA O2 + J_H2O_B H2O.
```

The direct Delta Hartley source remains `0.9 JH O3`; the ground complement
adds no Delta.

## Provenance boundary

The total channels follow Anqi Li (2017), Sect. 3.2, Eqs. 3.4 and 3.7, plus
the separate total `J2`/`J3` output of Appendix A.11 `Jfactors.m`. Brasseur and
Solomon (2005), Sect. 5.2.1, distinguishes ground and excited channels and
gives the two-atom O2 family source. JPL Evaluation 18 (2015) supplies the
historical 0.90 O3 and 0.44 Lyman-alpha O(1D) yields.

Anqi Li (2017), Sect. 3.4 Eq. 3.40 and Appendix A.11, defines `JH`, `J_SRC`,
and `J_LYA` as gross band/subset dissociation rates and `J3`/`J2` as the
corresponding totals. The accepted legacy convention separates SRC
(`122 < wavelength < 175 nm`) from the single Lyman-alpha element at
121.567 nm, so their gross O2 subset bound is their sum.

The two effective-ground registry rows are corrective reduced-network rows;
they are explicitly not attributed to Li et al. (2020) Table A1, which is an
airglow kinetic scheme rather than a complete dynamic Chapman budget.
