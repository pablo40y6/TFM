# M4D pragmatic closure

## Authorized policy and reproducible definitions

This report supersedes the old universal 0.1% gate for the operational closure
path. Accepted M1–M4C-R2 remain frozen. M4D is not frozen; M5 is not implemented.
PR #4 is preserved independently and is not merged by this work.

A0 uses all 430 HITRAN2016 lines with classic Voigt, frozen TIPS-2017 strengths,
Wehrli 1985 photon flux and existing spherical shell transfer. A1 changes only
the 91 principal d-line widths/shifts/profiles to sourced Drouin SDV. Its 59
principal q and 280 rare lines remain Voigt. Both have no LM or Galatry.
This is an explicitly pragmatic complete baseline, not a claim of exact advanced
historical spectroscopy. SDV is already validated against pinned historical HAPI.

Rates integrate target monomer cross section times transmitted photon flux, in
s^-1 per molecule. All selected lines attenuate every spectral node. Omission
sensitivities remove the specified population from both excitation and opacity.
B has all 320 lines; IRA all 835. IRA CIA affects attenuation only and uses the
verified Maté/HITRAN2016 O2-Air spectra with nO2*(nO2+nN2). No additional O2-O2.
Nominal CIA interpolates 253/273/296 K, clamping outside; its envelope uses the
minimum/maximum historical spectra at outside-range shells.

The executable rate equation is
`g = sum_i integral S_i(T_target)*phi_i(nu,T_target)*F_nu*exp(-tau_nu) dnu`,
with `tau_nu = sum_shell nO2*sigma_nu*L_cm + tau_CIA`. Profiles have unit
area on infinite support, strengths are HITRAN2016 cm/molecule (isotopic abundance
already included), flux is photons/cm²/s per cm^-1, and rates are s^-1.
Classic widths use `(296/T)^n * [gamma_air*(p-pO2)+gamma_self*pO2]`, in cm^-1
with pressures in atm. A1 uses the previously validated Drouin SDV reduction:
`gamma0=p*[0.79*gamma_foreign*(296/T)^n_foreign + 0.21*gamma_self*(296/T)^n_self]`,
`gamma2=speed*gamma0`, zero speed-dependent shift/narrowing/correlation, and
published temperature-dependent mean shifts. Centers, strengths and energies
stay HITRAN2016. The fixed 79/21 mixture is part of this sensitivity's sourced
parameter convention. No CIA spectrum or line profile is added as a production
term, and no isotopic abundance is applied twice.

Domain: every integer altitude 50–100 km and SZA 0/60/85/89/89.9/95/99 degrees,
plus illuminated surface-tangent and immediately shadowed rays at 100 km.
Relative convergence target is 0.5% for rates above max(1e-15 s^-1, 0.01% of
the reference band maximum). This practical near-zero definition is declared
before inspecting convergence differences; absolute differences and case counts
are reported below the floor. Spatial grids are 0.125/0.0625 km. Spectral
orders are 64/12 versus 128/24 and supports 3.84/7.68 cm^-1. Finite support is
not renormalized. Every line contributes to opacity: distant classic moments
are audited against exact Voigt; A1 mean-width distant approximation is audited
against exact SDV. Numerical errors are fixed; plausible material effects are
investigated; small reasonable approximation differences are documented.

Historical Y normalization and Galatry beta(T,p) are unresolved conventions for
future optional advanced models, not blockers for the authorized A0/A1 path.
No Y extrapolation above 340 K is used because LM is off. B qSDV is optional.
The previously reproduced 0.29155% CIA effect is physical attenuation.

The nominal programmatic entry point is `compute_classic_rates`: A0 and B use
its `monomer` result; IRA uses `cia_nominal`; A1 supplies `drouin=parse_drouin(...)`
and uses `monomer`. The older `a_band.compute_a_rates` remains the explicitly
blocked *advanced LM/Galatry* experiment and is not the A0/A1 entry point.

## Results and provisional decision

**GO provisional M4D → M5 under the authorized A0/B/IRA baseline.** M4D remains NOT FROZEN pending acceptance; M5 is unchanged. All 359 cases were computed: 328 illuminated, 31 shadowed. Every rate output is finite/nonnegative and every shadow output is exactly zero.

Rates below use the 128/24 quadrature and 7.68 cm^-1 support on the 0.125-km grid. The 0.0625-km comparison independently checks spatial error.

| Model | Lines and profile | g(50 km,0°), s^-1 | g(50 km,95°), s^-1 | g(tangent at 100 km), s^-1 |
| --- | --- | ---: | ---: | ---: |
| A0 | 430 Voigt | 3.7269785262e-09 | 1.1322958871e-11 | 8.4167628946e-15 |
| A1 | 91 SDV + 339 Voigt | 3.7268964439e-09 | 1.1299100539e-11 | 8.4196390057e-15 |
| B | 320 Voigt | 3.4759249757e-10 | 4.6371727198e-12 | 1.1092344546e-13 |
| IRA | 835 Voigt + CIA attenuation | 1.4511573614e-10 | 6.6998755443e-12 | 9.9639630216e-15 |

Maximum relative convergence differences in percent for relevant rates:

| Model | Spatial | Quadrature | Support | Reversed source order |
| --- | ---: | ---: | ---: | ---: |
| A0 | 0.073612 | 0.00360674 | 0.146848 | 1.67004e-13 |
| A1 | 0.073804 | 0.00367752 | 0.149764 | 1.93014e-13 |
| B | 0.0363783 | 0.000290603 | 0.0245222 | 1.83637e-13 |
| IRA | 0.0404607 | 0.000226375 | 0.00711255 | 2.66326e-13 |

The monomer-only IRA reference, both CIA envelopes and raw-source diagnostic also pass: their largest auxiliary convergence difference is 0.104596%. Source-order checks reverse all lines over the full domain, not only a probe.

Near-zero spatial differences (s^-1) are A0 3.408378e-16, A1 3.374468e-16, B 0, IRA 5.114147e-18. Full absolute percentiles and cases are in the single evidence JSON.

| Exact-profile audit | Nodes × active shells | Sampled transmission bound, % (relevant cases) |
| --- | ---: | ---: |
| A0 | 408 × 1200 | 1.09476e-07 |
| A1 | 408 × 1200 | 0.0001042 |
| B | 342 × 1200 | 7.76207e-06 |
| IRA | 651 × 1200 | 2.74501e-06 |

These are sampled-node bounds against direct Voigt/SDV. They are not a rigorous continuum supremum. Existing independent profile limits, area checks and the sourced SDV/HAPI audit remain applicable.

### A sensitivities

Percentiles include relevant cases only; differences are absolute magnitudes. Near-zero rates use absolute differences. Populations are removed from both excitation and opacity; the atmosphere and all other controls are fixed.

| Experiment | Max, % | p50, % | p90, % | p99, % | Max case z/SZA | Near-zero max abs, s^-1 |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| A1_vs_A0 | 1.18987 | 5.40402e-05 | 0.0274314 | 0.899403 | 97 / 99 | 6.899225e-15 |
| A0_omit_21_no_Y | 1.58539 | 0.000772227 | 0.0594957 | 0.839772 | 50 / 95 | 2.344654e-15 |
| A1_omit_21_no_Y | 1.58883 | 0.000772222 | 0.059466 | 0.841218 | 50 / 95 | 2.334250e-15 |
| A0_omit_59_q | 1.19919 | 0.0010165 | 0.0635053 | 0.63214 | 97 / 99 | 8.409093e-15 |
| A1_omit_59_q | 1.20592 | 0.0010165 | 0.0634916 | 0.632321 | 97 / 99 | 8.361234e-15 |
| A0_omit_280_rare | 96.4397 | 0.620059 | 41.5243 | 93.5671 | 100 / 99 | 5.415924e-13 |
| A1_omit_280_rare | 96.3805 | 0.620061 | 41.5189 | 93.4741 | 100 / 99 | 5.343625e-13 |

The no-Y and q omission maxima are approximately 1.6% and 1.2%; they remain included in A0 and A1. Rare lines are essential: the largest omission effect is 96.4397% at 100 km / 99°, changing gA from 1.699266e-12 to 6.049924e-14 s^-1. Their largest absolute effect is 2.897631e-11 s^-1 (0.468041% of the A0 peak). This demonstrates population importance, not an error of Voigt or a measured Galatry-minus-Voigt difference. All 280 are retained. If advanced rare-profile work is pursued later, focus on 95–99° twilight first; exact Galatry convention archaeology is not a prerequisite for the authorized complete Voigt baseline.

A1/A0 remains a small reasonable profile/parameter sensitivity: 1.18987% maximum, with its largest absolute difference only 0.00325148% of the A0 peak. No tested difference establishes a conceptual/software error requiring a fix.

### CIA and high-temperature scope

The retained 50 km / 95° reduction is 0.29155%; the temperature envelope is 0.272267–0.292481%. This reproduces the historical stop as physical attenuation, not an operational blocker.

Over the full domain, nominal CIA can remove approximately 95% near the surface-tangent ray, where the resulting rate is near-zero. The largest envelope departure from nominal is 6.73471% at 85 km / 99°. Its largest absolute departure is 1.027127e-14 s^-1, or 0.00704253% of the nominal band peak. This is a documented localized uncertainty, not an automatic 2% blocker or a new production term. The envelope samples the available measured spectra; it is not a guaranteed bound on unmeasured CIA.

The 248 >340 K shells start at 119 km and have maximum pressure 2.598743e-08 atm. Sampled exact SDV-versus-Voigt changes in these shells bound transmission differences at 1.036699e-12. Deleting the entire hot A0 opacity has a much more conservative rigorous Voigt upper bound of 0.74419%; this is not an observed model uncertainty. No unsupported Y(T>340 K) or beta(T,p) law is introduced.

### QA, provenance and remaining work

HITRAN verified: 2,268,239 bytes, 14,085 records; A/B/IRA = 430/320/835. SHA-256 `6b4acbc01cb649891f2d8597875c9cd8e4805cfdd4d3b7841c2d18cbf718de12`. The authorized identical-byte export was read locally; raw HITRAN is not committed.

Final pytest: **569 tests + 13 subtests passed**. Ruff passes. Legacy, local closure, odd-oxygen budget, historical background and historical UV validators all exit 0. Mapping passes: 430 matches, including 280 rare, with zero unmatched/duplicates/ambiguities. M4C-R2 SHA-256 remains `2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe`.

No unequivocal physical/software error was found in the tested authorized models; no accepted baseline was rewritten. Added isolated SDV array dispatch and reproducible complete-domain numerical/sensitivity checks. The universal 0.1% gate, exact Y normalization, high-temperature Y and historical Galatry conventions remain historical/optional; B qSDV is optional. Their exact scientific conventions remain unresolved, rather than being assigned guesses.

This GO adopts a conventional complete Voigt baseline, not a proof that every remaining advanced correction is uniformly negligible. The measured SDV sensitivity is small, CIA envelope impact is small in absolute terms, all line populations are present, and numerical QA passes. The defined pragmatic model provides sufficient evidence to proceed to the temporal TFM phase provisionally. Main, M1–M4C-R2 and M5 were not modified; PR #4 was not merged by this work. Milestone acceptance/freeze and temporal validation are not claimed.

Reproduce using the source folder and authorized HITRAN export:

```text
python scripts/validate_m4d_closure.py --sources <frozen-source-folder> --hitran <authorized-export> --cache <local-derived-cache> --output evidence/m4d_closure.json
python -m pytest -q -p no:cacheprovider
python -m ruff check src tests scripts
```

Only `evidence/m4d_closure.json` is the new public numerical evidence. Local checkpoints contain derived rates and are not committed.
