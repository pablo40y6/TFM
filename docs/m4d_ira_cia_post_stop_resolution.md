# M4D IRA CIA post-stop baseline resolution

Status: **CIA ATTENUATION SCOPE RESOLVED / M4D STILL NOT FROZEN**

Date: 2026-10-01  
Branch: `milestone/m4d-design`

This note resolves the scientific decision required after the source-verified
retained-rate CIA stop probe triggered the mandatory `0.1%` gate. It does not
modify M1--M4C-R2, does not start M5, and does not reinterpret CIA as a chemical
production channel.

## 1. Triggering evidence

The converged retained counterexample at 50 km / SZA 95 deg gives:

```text
monomer-only IRA rate:       6.7194715555556325e-12 s^-1
historical CIA nominal rate: 6.6998809075052470e-12 s^-1
relative CIA reduction:      0.2915504276 %
project gate:                0.1 %
```

The measured-source temperature envelope gives approximately
`0.2722675--0.2924815%` reduction. The spatial, quadrature-order and spectral
support refinements for this counterexample are all below the project gate. The
raw-vs-nonnegative experimental CIA treatment does not change the retained
nominal result at the reported precision.

The original execution specification therefore behaved correctly by stopping
scientific closure with `DESIGN BLOCKER`.

## 2. Independent physical/source review

HITRAN2016 defines collision-induced absorption as a contribution to
transmittance proportional to absorber and perturber number densities. For the
1.27-micron O2 band it states that CIA is significant under atmospheric
conditions because the CIA is comparatively strong while the magnetic-dipole
lines are weak.

For atmospheric air, HITRAN2016 places the Maté 21:79 O2:N2 measurements in the
O2-Air product and explicitly warns not to add a separate O2-O2 contribution on
top of O2-Air for the same calculation.

Primary sources:

- Gordon et al. (2017), *The HITRAN2016 Molecular Spectroscopic Database*,
  Section 4 and 4.1:
  https://hitran.org/media/refs/HITRAN-2016.pdf
- Maté, Lugez, Fraser & Lafferty (1999), *Absolute intensities for the O2
  1.27 um continuum absorption*, DOI 10.1029/1999JD900824:
  https://doi.org/10.1029/1999JD900824
- Li et al. (2020), historical photochemical context:
  https://doi.org/10.5194/amt-13-6215-2020

This review preserves the distinction between the first-order excitation source
and the radiative-transfer opacity. Adding CIA to attenuation does not create a
binary-density O2(a1Delta) production term.

## 3. Resolved M4D baseline semantics

The M4D IRA baseline is now:

```text
target excitation:
    accepted HITRAN2016 835-line a(0)-X(0) monomer system only

monomer attenuation:
    accepted HITRAN2016 835-line shell-local monomer opacity

CIA attenuation:
    INCLUDE historical Maté/HITRAN2016 O2-Air opacity

CIA production:
    NONE

CIA pair density:
    n_O2 * (n_O2 + n_N2)

double counting:
    do not add a second O2-O2 term on top of O2-Air
```

Nominal historical temperature treatment remains:

```text
253..296 K:
    interpolate between measured 253/273/296-K spectra

below 253 K:
    clamp to 253-K endpoint

above 296 K:
    clamp to 296-K endpoint
```

The measured-temperature min/max envelope outside source range remains a
mandatory sensitivity. Physical opacity remains nonnegative; the raw
experimental interpolation remains a noise-handling sensitivity.

## 4. Why inclusion is selected

The prior monomer-only attenuation candidate was acceptable only while CIA was a
required sensitivity whose effect was not yet known. The coupled target-edition
calculation now demonstrates a converged retained-rate effect larger than the
project's own numerical/design tolerance.

Retaining monomer-only attenuation after that result would knowingly preserve a
radiative-transfer omission larger than the M4D acceptance gate. Including the
historical CIA opacity is the smaller and better-defined change because:

1. the historical source family and exact numerical bytes are already frozen;
2. HITRAN2016 defines the pair semantics and no-double-counting rule explicitly;
3. the effect is on transmission, not on the chemical source definition;
4. the source-temperature envelope does not reverse the decision;
5. the required counterexample is numerically converged below the gate.

No empirical normalization and no modern CIA replacement are introduced.

## 5. Gate consequence

The CIA **scope decision is resolved**. The historical stop remains an important
audit event and is not retroactively converted into a PASS.

M4D remains **NOT FROZEN** because the following still require closure:

- A-band Drouin SDV + Table-22 first-order line mixing;
- rare-isotopologue Galatry target and attenuation evaluation;
- A low-temperature Y / no-Y high-J / quadrupole sensitivities;
- source-corrected B qSDV sensitivity;
- pressure-shift sensitivity;
- full 51-altitude / SZA / tangent spectral and spatial rate convergence;
- full-domain IRA CIA nominal/envelope sensitivity with CIA included in the
  selected attenuation baseline.

M5 remains untouched.
