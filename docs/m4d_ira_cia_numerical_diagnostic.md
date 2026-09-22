# M4D IRA historical CIA numerical diagnostic

Status: **SOURCE PASS / CIA PATH NUMERICS PASS / FULL COUPLED gIRA DECISION STILL OPEN**

Branch: milestone/m4d-design

This note records the numerical follow-up to docs/m4d_ira_cia_materialization_audit.md. It is a design diagnostic only: it does not implement M4D and it does not silently replace the accepted HITRAN2016 monomer line source.

## 1. Reproducible run identity

GitHub Actions diagnostic:

~~~
run:      35769308744
head:     196664b6997b787b8356d391601a386ca1133e69
artifact: m4d-cia-numerical-diagnostic
artifact id: 10713531629
artifact digest:
sha256:7c65147f32f3cf3ef8e0a823170c106e0840aa454edb4e311c2ba7d46c776a2b
~~~

Historical source bytes re-acquired inside the runner:

~~~
O2-O2_2011.cia
bytes: 1938473
SHA-256: 8cc3ecc87bf7a02492b385ecc71abf279b058da853aea768825deb81237d5ee3

07_hit12.par
bytes: 2263950
SHA-256: ad2cadf91cb985bec4074ce0bf47cdcfa7aab627ea15de2ac85de731873417a4
~~~

The first file is the surviving HITRAN2012 byte witness containing the Mate air-mixture blocks whose pair semantics HITRAN2016 explicitly corrected from the erroneous 2012 O2-O2 label to O2-Air.

The second file is used only as a historical IRA line-centre/strength witness for a line-strength-weighted diagnostic. It is not substituted for the accepted HITRAN2016 monomer source.

## 2. Inputs and numerical semantics

The diagnostic uses:

- the accepted M4C radiative background midlatitude_equinox_quiet_radiative_background.csv;
- exact spherical ray/shell intersections with Earth radius 6370 km and top of column 150 km;
- n_air = n_O2 + n_N2 for the historical O2-Air CIA pair;
- the recovered Mate spectra at 253, 273 and 296 K;
- linear temperature interpolation between measured temperatures and endpoint clamp outside 253--296 K;
- the frozen outside-range source envelope: per-frequency min/max of the three measured spectra;
- the accepted HITRAN2016 IRA support 7571.882333--8170.942339 cm^-1;
- all native Mate knots inside that support for the full-support optical-depth diagnostic.

For the separate line-strength-weighted diagnostic only, the historical HITRAN2012 a(0)-X(0) witness contains:

~~~
835 lines
7571.882912--8170.942711 cm^-1
sum(S296) = 3.22731686633e-24
~~~

The count and total strength match the accepted HITRAN2016 target subset, but the raw-record fingerprints do not match because HITRAN2016 includes line-position/assignment updates. Therefore this weighting remains diagnostic rather than final target-edition closure.

## 3. Negative experimental samples

Clipping all negative Mate samples to zero is not globally negligible if one integrates the complete experimental spectra without regard to the IRA line locations. The raw-vs-clipped integrated-area changes are approximately:

~~~
253 K: 0.0844 %
273 K: 0.00133 %
296 K: 0.4456 %
~~~

However, inside the accepted IRA support:

- 253 K: zero negative samples;
- 273 K: zero negative samples;
- 296 K: only two negative source knots, around 7574.53--7574.78 cm^-1;
- those two knots are more than 2.65 cm^-1 from the nearest historical IRA line centre;
- that nearest historical line is extremely weak, S/Smax about 5.3e-7.

At all 835 historical IRA line centres, the interpolated 253/273/296-K CIA coefficients are non-negative. Consequently the full 51-altitude / seven-SZA line-centre diagnostic gives:

~~~
max |tau_nodeclip - tau_raw| at IRA line centres = 0
~~~

Across the complete continuous IRA support, the largest raw-vs-source-node-clipped optical-depth difference is 4.7934e-4 in the most extreme tangent cases. This occurs away from the line-centre diagnostic and must still be respected by the final finite-wing quadrature.

Operational consequence:

- physical nonnegative opacity remains the nominal rule;
- negative-sample handling is not a line-centre blocker;
- the final coupled line-profile quadrature must retain one explicit raw-vs-nonnegative sensitivity before M4D freeze.

## 4. CIA materiality over the required geometry

The line-strength-weighted calculation is intentionally not the final monomer-self-shielded gIRA. It asks a narrower question: is CIA obviously negligible over the required spherical domain?

It is not.

Representative 0.0625-km results:

| case | nominal CIA-only weighted rate reduction | historical source-envelope range |
| --- | ---: | ---: |
| 50 km, 95 deg | 0.3818 % | 0.3545--0.3821 % |
| 54 km, 95 deg | 0.1073 % | 0.0997--0.1074 % |
| 55 km, 95 deg | 0.0784 % | 0.0729--0.0785 % |
| 80 km, 99 deg | 97.4001 % | 97.3523--97.4113 % |
| 83 km, 99 deg | 90.0691 % | 89.5571--90.1000 % |
| 90 km, 99 deg | 36.5294 % | 34.4878--36.5579 % |
| 100 km, 99 deg | 2.0460 % | 1.9002--2.0475 % |

The source-temperature envelope therefore does not change the qualitative materiality conclusion.

A stronger profile-independent test uses the minimum CIA optical depth over the complete accepted IRA spectral support. At SZA 99 deg the following cases have a minimum attenuation greater than 0.1% at every frequency in the support:

~~~
80 km: min tau ~ 1.887e-2  -> at least ~1.87 % attenuation
81 km: min tau ~ 1.56e-2   -> at least ~1.55 % attenuation
82 km: min tau ~ 9.6e-3    -> at least ~0.95 % attenuation
83 km: min tau ~ 3.8e-3    -> at least ~0.38 % attenuation
~~~

Thus CIA cannot be classified as uniformly negligible over the declared altitude/SZA geometry.

This still does not by itself decide the production baseline. The final gate is the CIA-coupled, target-edition, monomer-self-shielded gIRA above the declared 1e-15 s^-1 retained-rate floor.

The earlier monomer diagnostics show that representative twilight rates such as 50 km / 95 deg, 90 km / 99 deg and 100 km / 99 deg are above that floor, so a full coupled calculation is scientifically required rather than optional bookkeeping.

## 5. CIA spatial convergence

The earlier M4D line-transfer geometry used 0.125-km sub-stratification with 0.0625 km as the convergence reference. CIA is proportional to a density product and is more demanding for near-ground tangent paths.

For the CIA diagnostic:

~~~
0.125 -> 0.0625 km:
max relative CIA attenuation-factor difference = 0.1234 %
max relative tau(line-centre max) difference   = 0.1243 %
~~~

This narrowly fails the 0.1% numerical gate.

A further refinement gives:

~~~
0.0625 -> 0.03125 km:
max relative CIA attenuation-factor difference = 0.03883 %
max relative tau(line-centre max) difference   = 0.04157 %
~~~

This passes comfortably.

Therefore the selected CIA-specific spatial rule is:

~~~
CIA baseline sub-stratification: 0.0625 km
CIA convergence reference:       0.03125 km
~~~

This CIA-specific refinement does not require changing the accepted M4C UV geometry or the already selected M4D monomer 0.125-km rule. The final IRA transfer may evaluate monomer and CIA optical depths on their independently converged sub-grids before summing optical depth at target quadrature nodes, or use the finer common grid if simpler; either approach must reproduce the same result within the gate.

## 6. Gate decision

Closed by this diagnostic:

~~~
historical CIA bytes/source semantics       PASS
CIA 253/273/296 temperature convention      PASS
CIA full-domain materiality search          PASS: NOT uniformly negligible
CIA negative samples at line centres        PASS / no effect in diagnostic
CIA spatial step 0.0625 vs 0.03125 km       PASS
~~~

Still open:

~~~
target-edition IRA monomer continuity/execution
full Voigt target + shell attenuation
CIA evaluated at the final target quadrature nodes
raw-vs-nonnegative CIA finite-wing sensitivity
final CIA-coupled gIRA change above 1e-15 s^-1
baseline decision: monomer-only vs CIA-included attenuation
~~~

**Decision:** the previous monomer-only CIA baseline candidate is now **REOPENED FOR NUMERICAL CLOSURE**. Historical CIA is demonstrably capable of exceeding the 0.1% relevance threshold over the required domain, so M4D may not be frozen until the fully coupled retained-rate test is executed. This is not yet an instruction to include CIA in production unconditionally.
