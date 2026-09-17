# Legacy 2017 compatibility notes

The implementation is based on the visually checked MATLAB listings in Anqi
Li's 2017 MSc thesis:

- PDF page 71: `mkozone.m` (Appendix A.4).
- PDF pages 76-78: `pathleng.m` and `Jfactors.m` (Appendices A.10-A.11).
- Thesis equations 3.37-3.41 describe the surrounding optical-depth and
  photolysis formulation, but they are not identical to the executable listing
  in every detail.

### Internal SRC discrepancy in the thesis

Equation 3.40 gives an SRC lower limit of approximately 112 nm, whereas the
executable `Jfactors.m` listing in Appendix A.11 uses
`wave > 122 & wave < 175`. The `legacy_2017` compatibility authority is the
MATLAB listing, so it deliberately preserves `122 < wavelength < 175 nm`.
This resolves reproduction of the old program only; it is not a modern
scientific recommendation.

## Deliberately preserved behavior

1. `pathleng.m` uses Earth radius 6370 km and appends one top layer whose width
   equals the last grid spacing.
2. The `SZA == 90` tangent branch is an exact equality test.
3. For `SZA > 90`, rows whose tangent altitude is at or below zero are set to
   zero before the two-leg path is assembled.
4. `Jfactors.m` sets spectral rates to zero wherever optical depth is exactly
   zero. This is broader than an Earth-shadow mask: with exactly zero
   absorbers at an illuminated point, `tau == 0` and the MATLAB still forces
   the photolysis contributions to zero.
5. `mkozone.m` does not apply that zero-optical-depth mask. For the same
   zero-path or zero-absorber condition it evaluates `exp(-tau) = 1` instead.
   The two legacy routines therefore have intentionally different semantics.
6. `mkozone.m` uses `6e-34 * exp(300/T)^2.3`, not a modern JPL power law.
7. `M` in `mkozone.m` is exactly `O2 + N2`.
8. Ozone self-shielding is updated by exactly three fixed-point passes.
9. Hartley and SRC bounds are strict inequalities; Lyman-alpha is MATLAB
   element 28 rather than a nearest-wavelength search.

## Twilight fallback limitation

For `SZA > 90`, Appendix A.10 contains the literal fallback
`I=max(1,j-1)` when no lower grid point lies between the tangent point and the
target level. If the tangent point is below the lower boundary of the supplied
atmospheric grid while the ray still clears Earth, the fallback can attribute
to the lowest represented layer path length that actually lies partly in the
unrepresented atmosphere below the grid. The Python port reproduces this
behavior exactly.

Consequently, `pathleng.m` compatibility must not be described as physically
exact ray-sphere geometry across the entire twilight range. The independent
tests verify exact ray-sphere segments where legacy grid semantics coincide
with them and separately prove the fallback discrepancy. It is not corrected
inside `legacy_2017`; any improved geometry belongs to a later configuration.

These choices are compatibility behavior, not recommendations for
`historical_2020`.

