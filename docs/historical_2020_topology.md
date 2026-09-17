# Frozen `historical_2020` topology

## Purpose and boundary

This document retains the accepted Milestone-2 reduced-HOx manifest. M4B adds
only the effective ground O2/O3 photolysis channels required to close the
future dynamic odd-oxygen budget. It is not a temporal or vertical RHS.

The frozen TFM specification is decisive for the reduction. JPL Evaluation 18
(2015) supplies the historical coefficients for included elementary reactions.
Li et al. (2020) supplies the airglow topology. More complete mechanisms in
Brasseur and Solomon (2005) are context, not authorization to add reactions.

Future roles use the frozen state partition: dynamic `O`, `O3`, `H`, `R_H`, and
`Delta`; algebraic/QSSA `O1D`, `OH`, `HO2`, `H2O2`, `B0`, and `B1`; prescribed
`T`, `M`, `O2`, `N2`, `CO2`, `H2O`, and `H2`.

## Included reduced HOx processes

| Reaction/process | Decision | Source | Reason | Future role |
| --- | --- | --- | --- | --- |
| `H + O2 + M -> HO2 + M` | Included | Frozen TFM; JPL18 HOx B1 | Forms HO2 from dynamic H | H tendency and `R_H`; algebraic HO2 |
| `H + O3 -> OH + O2` | Included | Frozen TFM; JPL18 HOx B4 | Couples odd hydrogen and ozone | H/O3 tendencies and `R_H`; algebraic OH |
| `O + OH -> O2 + H` | Included | Frozen TFM; JPL18 HOx B1 | Recycles OH to H | O/H tendencies and `R_H`; algebraic OH |
| `O + HO2 -> OH + O2` | Included | Frozen TFM; JPL18 HOx B2 | Interconverts the OH/HO2 partition | O tendency and algebraic OH/HO2; conserves `R_H` |
| `OH + O3 -> HO2 + O2` | Included | Frozen TFM; JPL18 HOx B6 | Couples the OH/HO2 partition to ozone | O3 tendency and algebraic OH/HO2; conserves `R_H` |
| `HO2 + O3 -> OH + 2 O2` | Included | Frozen TFM; JPL18 HOx B12 | Couples the OH/HO2 partition to ozone | O3 tendency and algebraic OH/HO2; conserves `R_H` |
| `OH + H2 -> H2O + H` | Included | Frozen TFM; JPL18 HOx B7 | H2-mediated odd-hydrogen recycling | H and `R_H`; prescribed H2, algebraic OH |
| `H + HO2 -> 2 OH` | Included | Frozen TFM; JPL18 HOx B5 | Approved first H+HO2 branch | H and `R_H`; algebraic OH/HO2 |
| `H + HO2 -> H2O + O` | Included | Frozen TFM; JPL18 HOx B5 | Approved second H+HO2 branch | H/O and `R_H`; algebraic HO2 |
| `H + HO2 -> H2 + O2` | Included | Frozen TFM; JPL18 HOx B5 | Approved third H+HO2 branch | H and `R_H`; algebraic HO2, prescribed H2 |
| `2 OH -> H2O + O` | Included | Frozen TFM; JPL18 HOx B9 | Frozen bimolecular OH self-reaction | O and `R_H`; algebraic OH |
| `OH + HO2 -> H2O + O2` | Included | Frozen TFM; JPL18 HOx B10 | Odd-hydrogen termination | `R_H`; algebraic OH/HO2 |
| `2 HO2 -> H2O2 + O2` | Included | Frozen TFM; JPL18 HOx B13 | Defines the approved H2O2 algebraic source | `R_H`; algebraic HO2/H2O2; effective coefficient includes M |
| `OH + H2O2 -> H2O + HO2` | Included | Frozen TFM; JPL18 Note B11 | Approved H2O2 recycling loss | `R_H`; algebraic OH/HO2/H2O2 |
| `H2O2 + photon -> 2 OH` | Included, numerical input pending | Frozen TFM; historical JPL18-era photolysis data pending | Required H2O2 photochemical loss/source of OH | `R_H`; algebraic H2O2/OH |
| `H2O + photon -> H + OH` | Included, numerical input pending | Frozen TFM; historical JPL18-era photolysis data pending | Approved H2O photolysis channel A | H and `R_H`; prescribed H2O, algebraic OH |
| `H2O + photon -> H2 + O1D` | Included, numerical input pending | Frozen TFM; historical JPL18-era photolysis data pending | Approved H2O photolysis channel B | O1D QSSA source; prescribed H2O/H2 |
| `O1D + H2O -> 2 OH` | Included | Frozen TFM; JPL18 O(1D) A6 | Approved collisional source of odd hydrogen | O1D QSSA loss and `R_H` source; prescribed H2O, algebraic OH |
| `O1D + H2 -> H + OH` | Included | Frozen TFM; JPL18 O(1D) A5 | Approved collisional source of H and OH | O1D QSSA loss; H and `R_H`; prescribed H2, algebraic OH |

## Explicit exclusions

| Reaction/process | Decision | Source/context | Reason | Future role |
| --- | --- | --- | --- | --- |
| `O + H2 -> OH + H` | Excluded | Present in broader mechanisms; original frozen TFM brief calls it legacy optional | Baseline explicitly says not to include it | None in `historical_2020`; may only enter a separately approved legacy/diagnostic configuration |
| `O + H2O2 -> OH + HO2` | Excluded | Broader chemistry context | Frozen network includes `OH + H2O2`, not this reaction | None in the future baseline RHS/QSSA |
| `OH + OH + M -> H2O2 + M` | Excluded | Broader chemistry context | Frozen network specifies bimolecular `2 OH -> H2O + O` and no termolecular association | None in the future baseline RHS/QSSA |
| H2O enhancement of `HO2 + HO2` | Excluded | JPL18 discusses a separate water-complex enhancement | Frozen coefficient is exactly `3.0e-13 exp(+460/T) + 2.1e-33 M exp(+920/T)` | No enhancement factor in the future H2O2 QSSA or `R_H` tendency |

These exclusions are deliberate model-reduction decisions, not claims that the
processes are physically impossible. M3 does not restore them, and they must
not be restored silently in a later column RHS.

## Airglow decisions that constrain future assembly

- `B0 + O3 -> Delta + O3` retains Li's simplified product routing but uses the
  JPL18 A82 total loss coefficient. This is a model assumption, not a statement
  of 100-percent JPL branching; M3 adds no branching.
- `Delta + O3 -> O + 2 O2` uses both the JPL18 A75 topology and its
  `5.2e-11*exp(-2840/T)` law, resolving both discrepancies in the Li row. The
  M3 tendency assembly therefore contributes `-O3` and `+O`.
- The 0.9 Hartley and 0.44 Lyman-alpha values are product-channel yields. They
  scale the relevant product source only; they must not scale total O3 or O2
  photolysis loss.

## M4B corrective odd-oxygen channels

| Effective process | Source | Reduced role |
| --- | --- | --- |
| `O2 + photon -> 2 O` | Anqi (2017) Sect. 3.2 Eq. 3.4; Brasseur and Solomon (2005) Sect. 5.2.1 | Complements explicit SRC/Lyman O(1D) channels up to injected `J_O2_TOTAL`; contributes `+2O` |
| `O3 + photon -> O2 + O` | Anqi (2017) Sect. 3.2 Eq. 3.7; Brasseur and Solomon (2005) Sect. 5.2.1 | Complements the 0.9 Hartley O(1D)+Delta event up to injected `J_O3_TOTAL`; contributes `-O3,+O` |

JPL Evaluation 18 supplies the historical excited-state yields. These are
reduced corrective rows, not claims about every microscopic VUV product and
not reactions copied from Li (2020) Table A1. The previous M3 Hartley/Lyman
complement diagnostics remain visible but no longer represent a missing atom
budget.

## Stop condition

This manifest closes the documentary ambiguity identified by the M2 audit and
records the M4B odd-oxygen correction.
The four named extra HOx processes remain excluded. M3 implements only the
single-level closure described in `docs/historical_2020_local_closure.md`;
M4C radiation supplies the eight UV/VUV photolysis forcings without changing
this accepted reaction topology.
