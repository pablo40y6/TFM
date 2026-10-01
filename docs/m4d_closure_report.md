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

## Results

Full-domain results and final decision will be inserted after computation and QA.
