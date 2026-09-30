# M4D isolated reconstruction execution specification

Status: implementation experiment authorized by the 2026-09-30 user request;
scientific acceptance and final M4D freeze remain pending independent audit.

This specification governs only the new, separable reconstruction layer. M1--M4C-R2
and M5 are untouched. Earlier design-only restrictions do not override the user's
explicit implementation request. No final design specification is created.

## Source and identity rules

Verify exact source bytes before parsing. Select bands by global state labels.
Join auxiliary records on molecule, isotope and all four quantum fields; never
join on row order or nearest frequency. Drouin rows join on both branch/quantum
identifiers with the dipole flag; Table 22's even Q labels denote lower J and
translate to the adjacent odd lower N in HITRAN. Require 91 dipole, 70 mixed,
21 unmixed high-J, 59 quadrupole and 280 rare transitions, with no duplicates,
unmatched or ambiguous entries. Commit code and statistics, never restricted
source records, PDFs or parameter tables with unestablished redistribution rights.

## Equations and units

Use the line-strength equation and exact c2 in m4d_numerical_specification.md,
pinned HAPI TIPS-2017 Lagrange interpolation, and Wehrli wavelength interpolation
with the stated photon-energy and wavenumber Jacobian. Natural abundance is
already in sw. Cross sections are cm2/molecule; rates are s^-1; pressure is atm.

The user specifically requires classic B/IRA widths
`(296/T)^n_air * [gamma_air*(p-p_O2)+gamma_self*p_O2]` and shift `delta_air*p`.
This overrides the branch's air-only candidate for this experiment. Retain
`gamma_air*p*(296/T)^n_air` as a named comparison. No extra 0.79 factor is applied
to gamma_air. A native Drouin foreign/self semantics remain as separately sourced.

Use shell-local T,p and exact accepted spherical intersections on 0.125-km
monomer shells; check 0.0625 km. CIA uses 0.0625 km, checked at 0.03125 km.
The Maté byte witness and the documented HITRAN2016 O2-Air semantic correction
are valid historical recovery; do not substitute a current CIA product. CIA is
opacity only, with n_O2*(n_O2+n_N2), never a production coefficient.

## Numerics and acceptance

Decompose excitation into target-line integrals. At every node include all
accepted absorber lines, with no physical absorber wing cutoff. Integrate target
core and wings separately with Gauss-Legendre rules and expand support/increase
order independently. Do not empirically renormalize finite target support.
Nonnegative finite rates, zero in physical shadow, zero-column normalization,
source-order invariance and profile-area closure are mandatory.

The classic Voigt evaluator may accelerate distant contributions with Gaussian
moments: `M0=1`, `M1=shift-i*gamma`,
`M_(m+1)=(shift-i*gamma)*M_m+m*sigma^2*M_(m-1)`, and
`phi=-sum_m Im(M_m)/(pi*(nu-nu0)^(m+1))`, with sigma the Gaussian standard
deviation. Inside 2 cm^-1 evaluate the exact complex Voigt; outside it every
line still contributes. Check expansion orders 4/6/8 against direct all-line
Voigt on source-driven core/wing/between-line nodes in all active reference
shells. Use order 4 only after its relative opacity error is <=1e-6 in this
stop probe; the general transfer default remains order 8. This is numerical
evaluation of the Voigt tail, not a physical absorber cutoff or a modified
profile. Record order and radius with each experiment.

Required grid: all 51 heights, SZA 0/60/85/89/89.9/95/99 degrees plus illuminated
Earth-tangent and immediately shadowed cases. Numerical differences must be
<=1e-3 relative above 1e-15 s^-1; report absolute differences below the floor.

If corrected B qSDV or historical CIA changes any retained rate by >1e-3,
stop scientific closure with DESIGN BLOCKER. If the historical CIA source cannot
be identified, report SOURCE MATERIALIZATION BLOCKER. Missing numerical evidence
must remain explicitly NOT RUN, never PASS. A triggered stop condition may leave
later profile/sensitivity work outstanding; tests and an honest audit handoff
are still required. Do not declare M4D frozen or start M5.
