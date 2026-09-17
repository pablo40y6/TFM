# TFM 2.0 — CLEAN PROJECT RESET HANDOFF
## Authoritative state through M4C-R2; M4D must be redesigned from scratch

## Purpose

This handoff is for starting a new ChatGPT project with a clean context.

The new project must preserve every milestone already CLOSED / ACCEPTED, but it must rethink M4D from first principles using the scientific sources rather than inheriting the previous M4D design proposal.

Rules:
- Treat this file as authoritative for the accepted state through M4C-R2.
- Do not reopen M1–M4C unless a demonstrable error is found.
- Do not upload the old `TFM2_Work_Milestone4D_handoff.md` initially.
- The old M4D handoff may be consulted later only as a comparison after an independent M4D design is frozen.
- Preserve the audit ledger: milestone -> artifact -> hash -> tests -> findings -> corrections -> status.
- Before coding a milestone, freeze equations, units, assumptions, provenance, and numerical strategy.
- Review the roadmap explicitly at every milestone closure.

## Accepted architecture

Dynamic state per chemistry level:
O, O3, H, R_H=OH+HO2, Delta=O2(a1Delta_g)

Chemistry grid:
50–100 km, 1 km, 51 levels.

Future system:
255 ODE.

QSSA/algebraic:
O(1D), OH, HO2, H2O2, B0=O2(b1Sigma_g+,v=0), B1=O2(b1Sigma_g+,v=1).

Prescribed:
T, M, O2, N2, CO2, H2O, H2.

First temporal version:
no vertical transport; BDF main solver; Radau independent verification; repeated diurnal cycles to periodic convergence.

Delta remains dynamic:
dDelta/dt = P_Delta - L_Delta*Delta.

## Milestone ledger

### M1-R2 — CLOSED / ACCEPTED
Artifact: `tfm-photochem-milestone1-r2.zip`
SHA256: `46c88ec344de1569d06dff76c36c991edb19777497146ff5183756b54cba6f3d`

Legacy 2017 reproduction: pathleng.m, Jfactors.m, mkozone.m, sigma.mat.
Accepted sigma.mat SHA256:
`a98567c4f971721cec4197ad7ea17182e95df78c3a0eea880acb08fc6d560424`

### M2-R2 — CLOSED / ACCEPTED
Artifact: `tfm-photochem-milestone2-r2.zip`
SHA256: `ffb179c9f2c7fdb71ad5af8990490ae0040cf729f7209e1ae90a25fa0021f47f`

historical_2020 reaction registry/topology/kinetics.
Historical kinetic baseline: JPL Evaluation 18 / 2015.
Important accepted rates:
B0+N2 = 1.8e-15 exp(+45/T)
B0+O3 = 3.5e-11 exp(-135/T)
Delta+O3 -> O+2O2, k=5.2e-11 exp(-2840/T)
0.9 and 0.44 are product yields, not parent-loss multipliers.

### M3 — CLOSED / ACCEPTED
Artifact: `tfm-photochem-milestone3.zip`
SHA256: `d5dac9f3d160b0d53a1fdc16b23b4c72b918c271466dfbe58d99c5a54a9d89ef`
Package: 0.3.0

Single-level local closure with QSSA O1D/OH/HO2/H2O2/B0/B1 and tendencies dO,dO3,dH,dR_H,dDelta.
Independent audit: 342 tests + 13 subtests PASS; raw-formula audit ~1e-13 or better.
Effective Barth source -> B0 is a documented model-reduction assumption.
Performance debt: ~20.8–21.5 ms per scalar closure; naive 51-level RHS ~1.06–1.10 s. Defer optimization until M5.

### M4A — CLOSED / ACCEPTED
Artifact: `tfm-photochem-milestone4a.zip`
SHA256: `d1a68e6344710cd8ae6543f12081cde55355f23849ea73b9724d9e49156fbc12`
Package: 0.4.0

NRLMSISE-00 background:
pymsis==0.12.0, version=0
case midlatitude_equinox_quiet
2020-03-20T12:00:00Z, 45 N, 0 E
F10.7=150, F10.7A=150, Ap=4
Static background during future daily integration.

M = N2+O2+O+He+H+Ar+N
O2=0.21M, N2=0.78M, CO2=405e-6M

H2O/H2: Brasseur & Solomon Appendix 6 / SOCRATES VMR, log10(VMR) interpolation vs geometric height.

z_chem=50..100 km
z_rad=0..150 km

External O3:
0–49 prescribed SOCRATES
50–100 dynamic
101–150 prescribed SOCRATES

Accepted M4A assets:
socrates_prescribed_vmr.csv
`8985b4774b6e1aa91e3522758c7a33b652501601cdd167871afdc215474b4e01`

midlatitude_equinox_quiet_radiative_background.csv
`217fe7187c42a4ca8f590e1fa382ef815adffae6f5f1429816cea739f27c604f`

midlatitude_equinox_quiet_chemical_background.csv
`c1c115d840fa1b3115d7bcb7a1feca769b9dbbddd0faee5a2df0edadc4b5c291`

midlatitude_equinox_quiet_metadata.json
`5b4c53276b587141201b74116faf3210e3ce0ffa0de025e767fb944b25daa75a`

### M4B-R2 — CLOSED / ACCEPTED
Artifact: `tfm-photochem-milestone4b-r2.zip`
SHA256: `87fe1d585efa6f42231fc6d9898ca37c5afa51d1b4baa6325015caaee03530c8`
Package: 0.4.2

LocalForcing has 11 fields:
JH, J_SRC, J_LYA, J_H2O2, J_H2O_A, J_H2O_B, J_O2_TOTAL, J_O3_TOTAL, gA, gB, gIRA.

Partitions:
J2_star = J_SRC + 0.44*J_LYA
J2_ground = J_O2_TOTAL - J2_star
J3_star = 0.9*JH
J3_ground = J_O3_TOTAL - J3_star

Gross-subset invariants:
J_O3_TOTAL >= JH
J_O2_TOTAL >= J_SRC + J_LYA

Conservation:
O2: direct O + algebraic O1D = 2*J_O2_TOTAL*O2
O3: -O3 + direct O + algebraic O1D = 0
Direct Hartley Delta source = 0.9*JH*O3.

### M4C-R2 — CLOSED / ACCEPTED
Artifact: `tfm-photochem-milestone4c-r2.zip`
SHA256: `2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe`
Package: 0.5.1

THIS IS THE CURRENT ACCEPTED CODE BASELINE.

Purpose: SZA-resolved spherical direct-beam UV/VUV radiation and eight J forcings:
JH, J_SRC, J_LYA, J_O2_TOTAL, J_O3_TOTAL, J_H2O2, J_H2O_A, J_H2O_B.

Independent audit:
487 tests + 13 subtests PASS
all five validators PASS
wheel/sdist/clean-install PASS
UV/JPL assets regenerated byte-identical.

Geometry:
Earth radius=6370 km
top atmosphere=150 km
150 spherical shells
SZA supplied directly
exact ray/sphere Earth shadow
No legacy twilight fallback.
Illuminated + tau=0 => unattenuated sunlight.

Accepted M4C assets:
uv_spectral_backbone_2017.csv
`a398b97e7b2ae68efa9c72353444317e8a73f836870f0bd2cd6f21a5b1c7b135`

uv_spectral_backbone_2017_metadata.json
`1dc9c033449805ed432bffe3fd9bc80b9b2f76d7261cc6e2e6f5dec44b201df2`

jpl18_h2o_cross_sections_298k.csv
`d70d7d79405cb4b86de2186d1fd1212c332eb1eb362279f117b99daa00ce2e2c`

jpl18_h2o2_cross_sections_298k.csv
`bec01ae613d088455bdb64657b46f33bfe3cdb3b6e294c6f41fd21cbd611f4a1`

jpl18_uv_cross_sections_metadata.json
`20dae1b58fa5dce498b7b3bb28dfcfbd0e644196f1190a19863853e0686b818d`

Masks:
JH: 210<lambda<310 nm
J_SRC: 130<=lambda<=175 nm
J_LYA: exact historical row at 121.567 nm

JPL18 H2O source correction:
printed 199 nm -> 1.08e-20 cm2
accepted corrected interpretation 189 nm -> 1.08e-20 cm2
documented as typographical correction; JPL20 is corroboration only.

Reduced H2O branching:
121<=lambda<147: phi_A=0.89, phi_B=0.11
147<=lambda<=198: phi_A=1, phi_B=0

H2O2:
JPL18 190–350 nm; 260–350 temperature-dependent parameterization.
If T<200 K, evaluate at 200 K.
13 baseline chemistry levels use this boundary.
Ly-alpha H2O2 is diagnostic upper bound only; max ratio ~4.1%.

Deferred M4C sensitivity:
1-km endpoint-mean shell-density convention can differ from piecewise-linear radial integration by ~1–2% in selected twilight cases.
Example z~50 km, SZA~89.9: JH ~1.5%, J_O2_TOTAL ~2.2%.
Not an M4C bug; retain for later validation.

## M4D must be redesigned independently

The new project begins before any M4D design is frozen.

Known required outputs:
gA, gB, gIRA

These are the remaining three physical forcings needed to complete LocalForcing.

The new project must independently determine from primary/historical sources:
- exact physical transitions represented by gA/gB/gIRA;
- equations and units;
- required O2 spectroscopy;
- historical line-data edition/source;
- partition-function treatment;
- solar spectrum/provenance;
- line shapes;
- attenuation/self-absorption;
- isotopologue treatment;
- numerical spectral integration;
- validation benchmarks;
- baseline vs future sensitivity choices.

Independently verify from Li 2020 and other sources:
- which HITRAN edition is actually cited/used;
- whether an exact historical line dataset can be frozen;
- whether historical partition functions are required;
- what solar spectrum is provenance-wise defensible;
- whether line-by-line or parameterized g factors are appropriate;
- what literature gives independent benchmark values.

If exact historical data cannot be obtained, prefer SOURCE BLOCKER over silently substituting modern data.

## Old M4D proposal

A previous chat created:
`TFM2_Work_Milestone4D_handoff.md`

Do NOT upload it initially.

Clean workflow:
1. independently design M4D;
2. freeze the new project's equations/provenance/validation plan;
3. only then optionally compare with the old M4D handoff;
4. resolve differences by evidence.

## Recommended scientific sources for the new project

Highest priority:
- Thesis idea for Pablo.pdf
- anqi2020.pdf
- anqisthesis.pdf
- 1993.pdf
- 2006JD008355.pdf
- murtaghSR.pdf
- koppers&murtagh.pdf
- Aeronomy of the Middle Atmosphere_ Chemistry and Physics of the Stratosphere and Mesosphere.pdf
- JPL_Publication_15-10.pdf

Useful comparison/context:
- NASA_Data_Evaluation_20.pdf
- Journal of Geophysical Research Atmospheres - 2007 - Zhu - Effect of dynamical-photochemical coupling on oxygen airglow.pdf

Do not overload the new project initially with unrelated/low-priority historical ozone papers unless they become necessary.

## Potential missing source files for M4D

The new project should determine whether it needs:
- exact historical O2 HITRAN line data;
- historical partition-function data;
- a frozen solar-spectrum source file.

Any new source must be frozen with:
filename, provider/archive, edition/version, access date, SHA256, format, record count, selection rules.

Do not rely on a live current database without edition guarantees.

## Roadmap after M4D

Provisional:
M4D: remaining 3 g forcings
M5A: performance-ready 51-level chemistry kernel
M5B: 255-state RHS + BDF/Radau
M6: diurnal cycle + periodic convergence
M7: scientific validation/sensitivity
M8: Odin/retrieval/application if still in scope

At M4D closure, explicitly reconsider whether M5A/M5B should remain separate.

## M5 constraints already known

Before BDF:
- preserve M3 scalar closure as golden scientific reference;
- optimize/cache/vectorize without changing chemistry;
- address OH-root performance bottleneck;
- compare optimized kernel against accepted M3;
- only then assemble the 255-state RHS.

Deferred sensitivities:
- M4C shell discretization near twilight;
- static atmospheric background through the day;
- M4D line-shape/pressure/CIA uncertainties if relevant;
- solar-spectrum resolution if relevant.

## Required behavior of the new project

It should begin by accepting M1–M4C-R2 as frozen baselines, then read this clean handoff and the primary M4D sources, reconstruct the physical meaning/provenance of gA/gB/gIRA independently, and only then propose the M4D architecture.

Do not jump directly to implementation.

## Current accepted starting artifact

Upload and use:
`tfm-photochem-milestone4c-r2.zip`

SHA256:
`2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe`

Everything prior is represented cumulatively in that ZIP plus this handoff.
Old milestone ZIPs are not required for ordinary continuation unless later binary comparison is needed.
