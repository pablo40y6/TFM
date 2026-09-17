# `historical_2020` reaction and coefficient provenance

## Scope and conventions

This is the accepted Milestone-2 traceability table, extended in M4B only with
two effective odd-oxygen photolysis rows. Li et al. (2020), Sect. 2.3 and
Table A1, define the airglow topology; the frozen TFM specification adds the
approved O/O3/HOx reactions. JPL Evaluation 18 (2015) supplies historical
kinetics where applicable. JPL Evaluation 20 (2025) supplies no value here.

Units use molecule-cm-s conventions:

- `k2`: cm3 molecule-1 s-1;
- `k3`: cm6 molecule-2 s-1;
- `k1`: s-1.

For JPL Table 1, `A exp(-E/R/T)` is used literally. A negative tabulated
`E/R` therefore produces a positive exponent in code. The HO2 self-reaction
returns the published effective second-order coefficient, including its
explicit `M` term.

## Implemented coefficient table

| Rate-law ID | Reaction ID(s) | Implemented expression | Unit | Source/year | Status/note |
| --- | --- | --- | --- | --- | --- |
| `k_o_o2_m` | `O_ASSOCIATION` | `6.0e-34*(300/T)^2.4` | k3 | JPL18 Table 2-1, 2015 | implemented |
| `k_o_o3` | `O_O3` | `8.0e-12*exp(-2060/T)` | k2 | JPL18 Ox A1, 2015 | implemented |
| `k_o_o_m_barth` | `BARTH_RECOMBINATION` | `4.7e-33*(300/T)^2` | k3 | Brasseur & Solomon Table 4.5, 2005 | implemented; resolves Li misprint |
| `k_h_o2_m` | `H_O2_ASSOCIATION` | `4.4e-32*(300/T)^1.3` | k3 | JPL18 Table 2-1 HOx B1, 2015 | implemented low-pressure limit |
| `k_h_o3` | `H_O3` | `1.4e-10*exp(-470/T)` | k2 | JPL18 HOx B4, 2015 | implemented |
| `k_o_oh` | `O_OH` | `1.8e-11*exp(+180/T)` | k2 | JPL18 HOx B1, 2015 | implemented |
| `k_o_ho2` | `O_HO2` | `3.0e-11*exp(+200/T)` | k2 | JPL18 HOx B2, 2015 | implemented |
| `k_oh_o3` | `OH_O3` | `1.7e-12*exp(-940/T)` | k2 | JPL18 HOx B6, 2015 | implemented |
| `k_ho2_o3` | `HO2_O3` | `1.0e-14*exp(-490/T)` | k2 | JPL18 HOx B12, 2015 | implemented |
| `k_oh_h2` | `OH_H2` | `2.8e-12*exp(-1800/T)` | k2 | JPL18 HOx B7, 2015 | implemented |
| `k_h_ho2_2oh` | `H_HO2_2OH` | `7.2e-11` | k2 | JPL18 HOx B5, 2015 | implemented channel 1 |
| `k_h_ho2_h2o_o` | `H_HO2_H2O_O` | `1.6e-12` | k2 | JPL18 HOx B5, 2015 | implemented channel 2 |
| `k_h_ho2_h2_o2` | `H_HO2_H2_O2` | `6.9e-12` | k2 | JPL18 HOx B5, 2015 | implemented channel 3 |
| `k_oh_oh` | `OH_OH` | `1.8e-12` | k2 | JPL18 HOx B9, 2015 | implemented |
| `k_oh_ho2` | `OH_HO2` | `4.8e-11*exp(+250/T)` | k2 | JPL18 HOx B10, 2015 | implemented |
| `k_ho2_ho2` | `HO2_HO2` | `3.0e-13*exp(+460/T) + 2.1e-33*M*exp(+920/T)` | effective k2 | JPL18 HOx B13, 2015 | implemented; no separate H2O enhancement |
| `k_oh_h2o2` | `OH_H2O2` | `1.8e-12` | k2 | JPL18 Note B11, 2015 | implemented 200-300 K recommendation |
| `a_o1d` | `O1D_RADIATIVE` | `6.81e-3` | k1 | Li Table A1, 2020 | implemented |
| `a_b0` | `B0_RADIATIVE` | `8.34e-2` | k1 | Li Table A1, 2020 | implemented |
| `a_b1` | `B1_RADIATIVE` | `7.2e-2` | k1 | Li Table A1, 2020 | implemented |
| `a_delta` | `DELTA_RADIATIVE` | `2.26e-4` | k1 | Li Table A1, 2020 | implemented; project band is 1.27 micrometres |
| `k_o1d_n2` | `O1D_N2` | `2.15e-11*exp(+110/T)` | k2 | JPL18 O(1D) A7, 2015 | implemented; Li sign corrected |
| `k_o1d_o2` | `O1D_O2_B1`, `O1D_O2_B0` | `3.3e-11*exp(+55/T)` | k2 | JPL18 O(1D) A3, 2015 | implemented; Li sign corrected; 0.8/0.2 routing |
| `k_o1d_h2o` | `O1D_H2O` | `1.63e-10*exp(+60/T)` | k2 | JPL18 O(1D) A6, 2015 | implemented |
| `k_o1d_h2` | `O1D_H2` | `1.2e-10` | k2 | JPL18 O(1D) A5, 2015 | implemented |
| `k_b1_o2` | `B1_O2` | `2.2e-11*exp(-115/T)` | k2 | Li Table A1, 2020 | adopted through Yankovsky et al. (2016) reference compilation |
| `k_b1_n2` | `B1_N2` | `7.0e-13` | k2 | Li Table A1, 2020 | adopted through Yankovsky et al. (2016) reference compilation |
| `k_b1_o` | `B1_O` | `4.5e-12` | k2 | Li Table A1, 2020 | adopted through Yankovsky et al. (2016) reference compilation |
| `k_b1_o3` | `B1_O3` | `3.0e-10` | k2 | Li Table A1, 2020 | adopted through Yankovsky et al. (2016) reference compilation |
| `k_b0_n2` | `B0_N2` | `1.8e-15*exp(+45/T)` | k2 | JPL18 A86, 2015 | implemented full temperature law; Li routing retained |
| `k_b0_o2` | `B0_O2` | `3.9e-17` | k2 | JPL18 A81, 2015 | implemented |
| `k_b0_o` | `B0_O` | `8.0e-14` | k2 | JPL18 A80, 2015 | implemented with Li Delta-product topology |
| `k_b0_o3` | `B0_O3` | `3.5e-11*exp(-135/T)` | k2 | JPL18 A82, 2015 | total loss coefficient; Li routing assumption retained |
| `k_b0_co2` | `B0_CO2` | `4.2e-13` | k2 | JPL18 A88, 2015 | implemented |
| `k_delta_o2` | `DELTA_O2` | `3.6e-18*exp(-220/T)` | k2 | JPL18 A74, 2015 | implemented |
| `k_delta_n2` | `DELTA_N2` | `1.0e-20` | k2 | JPL18 A78, 2015 | Li uses JPL upper-limit boundary |
| `k_delta_o` | `DELTA_O` | `2.0e-16` | k2 | JPL18 A73, 2015 | Li uses JPL upper-limit boundary |
| `k_delta_o3` | `DELTA_O3` | `5.2e-11*exp(-2840/T)` | k2 | JPL18 A75, 2015 | implemented; Li sign corrected |

Each table row has its full reference, year, configuration, argument list, and
provenance note in `kinetics.RATE_LAWS`; the compact source column above is not
a replacement for those machine-readable records.

## Registered scalar parameters

| ID | Value | Unit | Source/year | Use |
| --- | ---: | --- | --- | --- |
| `yield_o3_hartley_delta_o1d` | 0.9 | 1 | Li Table A1, 2020 | product-channel yield for JH direct Delta/O1D production; not a multiplier on total O3 loss |
| `yield_o2_lya_o1d` | 0.44 | 1 | Li Table A1, 2020 | product-channel yield for Lyman-alpha O1D production; not a multiplier on total O2 loss |
| `branch_o1d_o2_b1` | 0.8 | 1 | Li Q1a, 2020 | B1 branch |
| `branch_o1d_o2_b0` | 0.2 | 1 | Li Q1b, 2020 | B0 branch |
| `barth_c_o2` | 6.6 | 1 | McDade et al., 1986; Li adoption | M3 effective Barth algebra |
| `barth_c_o` | 19 | 1 | McDade et al., 1986; Li adoption | M3 effective Barth algebra |

## Gross photolysis subset contract

`JH`, `J_SRC`, and `J_LYA` are gross parent-photodissociation coefficients,
whereas 0.9 and 0.44 are product-state yields. Following Anqi Li (2017),
Sect. 3.4 Eq. 3.40 and Appendix A.11, the known subsets must be contained in
their totals:

```text
J_O3_TOTAL >= JH
J_O2_TOTAL >= J_SRC + J_LYA
```

The accepted legacy wavelength convention makes SRC and Lyman-alpha
non-overlapping. These input invariants do not alter the effective reduced
partition: `J3_ground = J_O3_TOTAL - 0.9*JH` and
`J2_ground = J_O2_TOTAL - J_SRC - 0.44*J_LYA`.

## `PENDING INPUT` processes

| Reaction ID | Required numerical input | M3 handling |
| --- | --- | --- |
| `H2O2_PHOTOLYSIS` | historical H2O2 cross sections/yields and spectrum | `J_H2O2` injected; physical calculation remains pending |
| `H2O_PHOTOLYSIS_A` | historical H2O cross sections and channel yield | `J_H2O_A` injected; physical calculation remains pending |
| `H2O_PHOTOLYSIS_B` | historical H2O cross sections and channel yield | `J_H2O_B` injected; physical calculation remains pending |
| `O3_HARTLEY` | final JH radiative calculation | `JH` injected; actual reduced 0.9 excited event |
| `O3_PHOTOLYSIS_GROUND_EFFECTIVE` | total historical O3 photolysis calculation | `J_O3_TOTAL` injected; effective complement calculated without radiation |
| `O2_SRC` | final Schumann-Runge continuum calculation | `J_SRC` injected |
| `O2_LYMAN_ALPHA` | final Lyman-alpha calculation | `J_LYA` injected; 0.44 product yield applied separately |
| `O2_PHOTOLYSIS_GROUND_EFFECTIVE` | total historical O2 photolysis calculation | `J_O2_TOTAL` injected; effective complement calculated without radiation |
| `O2_A_BAND` | reproducible historical HITRAN data and transfer | `gA` injected |
| `O2_B_BAND` | reproducible historical HITRAN data and transfer | `gB` injected |
| `O2_IRA_BAND` | reproducible historical HITRAN data and transfer | `gIRA` injected |
| `BARTH_TRANSFER` | elementary O2star transfer coefficient | absorbed by M3 effective formula using empirical C values; none invented |
| `BARTH_O2STAR_QUENCH` | elementary O2star loss coefficients | remains absorbed inside the M3 effective parameterization |

## Complete 52-process registry

- O/O3 and Barth: `O_ASSOCIATION`, `O_O3`, `BARTH_RECOMBINATION`,
  `BARTH_TRANSFER`, `BARTH_O2STAR_QUENCH`.
- HOx: `H_O2_ASSOCIATION`, `H_O3`, `O_OH`, `O_HO2`, `OH_O3`, `HO2_O3`,
  `OH_H2`, `H_HO2_2OH`, `H_HO2_H2O_O`, `H_HO2_H2_O2`, `OH_OH`,
  `OH_HO2`, `HO2_HO2`, `OH_H2O2`, `H2O2_PHOTOLYSIS`,
  `H2O_PHOTOLYSIS_A`, `H2O_PHOTOLYSIS_B`.
- Photolysis/excitation: `O3_HARTLEY`, `O3_PHOTOLYSIS_GROUND_EFFECTIVE`,
  `O2_SRC`, `O2_LYMAN_ALPHA`, `O2_PHOTOLYSIS_GROUND_EFFECTIVE`, `O2_A_BAND`,
  `O2_B_BAND`, `O2_IRA_BAND`.
- O1D/radiative: `O1D_RADIATIVE`, `B0_RADIATIVE`, `B1_RADIATIVE`,
  `DELTA_RADIATIVE`, `O1D_N2`, `O1D_O2_B1`, `O1D_O2_B0`, `O1D_H2O`,
  `O1D_H2`.
- B1/B0/Delta quenching: `B1_O2`, `B1_N2`, `B1_O`, `B1_O3`, `B0_N2`,
  `B0_O2`, `B0_O`, `B0_O3`, `B0_CO2`, `DELTA_O2`, `DELTA_N2`,
  `DELTA_O`, `DELTA_O3`.

The exhaustive inclusion/exclusion manifest for the reduced HOx network is in
`docs/historical_2020_topology.md`. M4B evaluates the two new effective rows
locally under injected totals; it does not calculate radiation or implement a
temporal RHS. These rows cite Anqi (2017) and Brasseur and Solomon (2005), and
are explicitly not presented as Li (2020) Table A1 reactions.

## B0 + O3 routing decision

`k_b0_o3` is the total B0-loss coefficient from JPL18 A82. The registered
products, `B0 + O3 -> Delta + O3`, are the simplified Li 2020 model-routing
assumption. This combination does **not** assert that JPL18 assigns 100 percent
of its total coefficient to that channel. No 70/30 or other unapproved
branching is introduced in M2-R2.

## Li 2020 discrepancies and resolutions

| Item | Li 2020 printing | Historical evidence | M2 implementation |
| --- | --- | --- | --- |
| O1D + N2 | `exp(-110/T)` | JPL18 A7 has E/R = -110 in `A exp(-E/R/T)` | `exp(+110/T)` |
| O1D + O2 | `exp(-55/T)` | JPL18 A3 has E/R = -55 | `exp(+55/T)` |
| Delta + O3 | `Delta + O3 -> O2 + O3`; `5.2e-11*exp(+2840/T)` | JPL18 A75 gives `Delta + O3 -> O + 2 O2`; `5.2e-11*exp(-2840/T)` | JPL18 topology and law. M3 tendency consequence: `-O3`, `+O` |
| B0 + N2 | Li uses the 298 K value `2.1e-15` with Delta routing | JPL18 A86 gives `1.8e-15*exp(+45/T)` | full JPL18 law; Li product routing retained |
| B0 + O3 | Li uses the 298 K value `2.2e-11` and `B0 + O3 -> Delta + O3` | JPL18 A82 gives total loss `3.5e-11*exp(-135/T)` and discusses branching | full JPL18 total coefficient with explicitly labelled Li routing assumption; no new branching |
| Barth recombination | `exp(300/T)` | Brasseur & Solomon Table 4.5 and Anqi's executable listing use a power law | `(300/T)^2` |
| JPL citation label | footnote says Publication `10-10` with Burkholder 2015 | official work is Publication 15-10 / Evaluation 18 | reference corrected, value source unchanged |
| A3 topology | printed B1 on both sides of radiative transition | Sect. 2.3 defines inverse lifetime returning to ground state | B1 is consumed |
| A4 wavelength | table prints 1.24 micrometres | paper text defines IRA at 1270 nm and TFM observable is 1.27 micrometres | 1.27 micrometres |

The B0+N2 and B0+O3 298 K constants used in provisional M2 are replaced by the
full historical JPL18 laws as required by the coefficient-provenance rule. The
Delta+N2/O upper-limit boundaries remain the frozen Li choices. No value comes
from JPL Evaluation 20 / 2025.
