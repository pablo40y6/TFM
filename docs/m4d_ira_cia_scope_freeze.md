# M4D IRA collision-induced absorption scope freeze

Status: **BASELINE SCOPE SELECTED / CIA DEFERRED AS SENSITIVITY**

Branch: `milestone/m4d-design`

This note resolves whether O2 collision-induced absorption (CIA) is part of the frozen `historical_2020` M4D `gIRA` baseline.

## 1. Decision

The M4D historical baseline defines `gIRA` from the **monomer resonance system**

```text
O2(X, v''=0) + h nu -> O2(a1Delta_g, v'=0)
```

using the frozen HITRAN2016 `a(0)-X(0)` line subset.

O2-O2 / O2-N2 collision-induced absorption around 1.27 microns is **not added to the `gIRA` production coefficient in the baseline** and is **not included as an extra continuum attenuation term in the first historical implementation**.

CIA is retained as an explicit later sensitivity/limitation, especially for extreme twilight rays with low tangent altitudes.

## 2. Why this matches the reduced historical model semantics

Li et al. (2020) describes `gA`, `gB`, and `gIRA` as resonance absorption of ground-state O2 at 762, 688, and 1270 nm, respectively. Table A1 writes `gIRA` as a first-order process:

```text
O2 + h nu -> O2(a1Delta_g)
```

with a vertical-profile coefficient sourced to HITRAN.

Yankovsky and Manuilova (2006), a direct predecessor in the oxygen-airglow modelling lineage, writes the same first-order process explicitly:

```text
O2 + h nu (1.27 micron) -> O2(a1Delta_g, v=0)
```

and reports the top-of-atmosphere photoexcitation rate `1.54e-10 s^-1`. Their table also reports `5.35e-9 s^-1` for A and `2.94e-10 s^-1` for B. These are first-order per-molecule solar excitation rates, not density-squared collision-pair source terms.

This makes the monomer line system the coherent baseline interpretation of the accepted reduced `gIRA` forcing.

Sources:

- Li et al. (2020), AMT 13, 6215-6236, DOI `10.5194/amt-13-6215-2020`.
- Yankovsky & Manuilova (2006), Ann. Geophys. 24, 2823-2839.

## 3. CIA is physically real and is not being declared nonexistent

Laboratory and atmospheric studies establish a broad collision-induced continuum beneath the 1.27-micron O2 `a-X(0,0)` system.

Smith & Newnham (2000) separately measured monomer and binary O2/O2-N2 absorption. Smith, Newnham & Williams (2001) validated continuum absorption near 1.27 microns against direct solar observations. HITRAN2016 includes revised O2 CIA products in this spectral region and treats monomer line absorption and CIA as separate spectroscopic components.

Modern spectroscopy describes the scaling distinction explicitly:

- monomer line absorption is proportional to O2 number density;
- O2-O2 CIA is proportional approximately to `[O2]^2`;
- foreign-pair CIA includes products such as `[O2][N2]`.

Therefore CIA cannot be silently represented by simply modifying the first-order monomer HITRAN line strengths.

## 4. Why CIA is deferred from the historical baseline

The project is reconstructing the documented Li-2020 reduced topology before adding updated physics. The current evidence does not establish that Li's `gIRA` vertical profile folded a particular HITRAN2016 CIA file into the direct excitation coefficient, nor does it define how collision-pair absorption would be mapped into the single first-order forcing field.

Adding CIA now would require several new, independently sourced choices:

- exact historical HITRAN2016 CIA file/version;
- O2-O2 and O2-N2 density-pair convention;
- temperature interpolation;
- whether CIA absorption creates O2(a1Delta) with unit/effective yield or only attenuates the direct beam in the reduced model;
- treatment along spherical twilight rays that may pass below the 50-km chemistry domain.

Those additions would enlarge M4D beyond the independently reconstructed historical baseline.

## 5. Expected domain behavior and limitation

Within the 50-100 km chemistry domain, local CIA falls much faster with decreasing density than monomer absorption because of its binary-density scaling. This supports its exclusion from the local baseline source term.

However, near sunrise/sunset, an illuminated ray to a high-altitude target can have a tangent altitude below the target level and may traverse much denser air. CIA may then add continuum attenuation around 1.27 microns. The baseline explicitly does not claim this effect is zero.

The practical consequence is:

- baseline M4D: monomer lines only;
- later sensitivity: historical CIA attenuation on selected near-twilight rays;
- if that sensitivity materially changes `gIRA` over the time/SZA range important to the final sunrise integration, elevate CIA into an explicit model extension rather than silently editing the frozen baseline.

## 6. Validation implication

The monomer baseline must recover the historical top-of-atmosphere scales before attenuation:

```text
gA   ~ 5.35e-9 s^-1
gB   ~ 2.94e-10 s^-1
gIRA ~ 1.54e-10 s^-1
```

These values are historical validation anchors, not exact forced answers for HITRAN2016 + Wehrli1985 because both spectroscopy and solar-source choices differ slightly from older compilations.

A material discrepancy outside a predeclared validation tolerance must be investigated rather than corrected by adding CIA ad hoc.

## 7. Gate decision

**PASS — M4D `historical_2020` uses monomer resonance absorption only for `gIRA`; CIA is deferred to a documented sensitivity/limitation.**

This decision avoids both extremes: it does not erase known CIA physics, and it does not inject a new density-pair process into a first-order forcing field without source-supported semantics.