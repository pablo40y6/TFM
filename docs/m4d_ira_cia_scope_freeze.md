# M4D IRA collision-induced absorption scope freeze

Status: **BASELINE SCOPE SELECTED / HISTORICAL TWILIGHT SENSITIVITY REQUIRED BEFORE M4D CLOSURE**

Branch: `milestone/m4d-design`

This note resolves whether O2 collision-induced absorption (CIA) is part of the `historical_2020` M4D `gIRA` baseline and clarifies the closure obligation after the historical-source recovery in `docs/m4d_ira_cia_historical_source_recovery.md`.

## 1. Baseline decision

The M4D historical baseline defines `gIRA` from the first-order monomer resonance system

```text
O2(X, v''=0) + h nu -> O2(a1Delta_g, v'=0)
```

using the accepted HITRAN2016 `a(0)-X(0)` line subset.

O2-O2 / O2-N2 CIA is:

- **not** added as a binary-density production term to `gIRA`;
- **not** included in the monomer baseline attenuation;
- **required** as a separate historical twilight attenuation sensitivity before M4D milestone closure.

This is Option B from the design review. It must not be silently converted into Option C (an unspecified later milestone).

## 2. Why the monomer baseline matches the reduced historical model

Li et al. (2020) writes `gIRA` as the first-order process

```text
O2 + h nu -> O2(a1Delta_g)
```

and sources the profile to HITRAN. Yankovsky and Manuilova (2006) use the same first-order direct photoexcitation process and report the independent top-of-atmosphere scale near `1.54e-10 s^-1`.

A density-squared collision-pair source is therefore not silently folded into the accepted reduced `gIRA` coefficient.

Sources:

- Li et al. (2020), AMT 13, 6215-6236, DOI `10.5194/amt-13-6215-2020`.
- Yankovsky & Manuilova (2006), Ann. Geophys. 24, 2823-2839.

## 3. Historical CIA source now identified

HITRAN2016 Section 4.1 states that the revised 1.27-micron CIA data in that edition are taken from:

```text
B. Maté, C. Lugez, G. T. Fraser, W. J. Lafferty,
Absolute intensities for the O2 1.27 um continuum absorption,
J. Geophys. Res. Atmos. 104 (1999) 30585-30590,
DOI 10.1029/1999JD900824
```

The HITRAN2016 semantics are:

- pure-O2 spectra -> `O2-O2`;
- 21:79 O2:N2 mixture spectra -> `O2-Air`;
- the `O2-Air` product already contains the atmospheric O2-O2 and O2-N2 collision contributions represented by that mixture;
- do **not** add a separate O2-O2 term on top of `O2-Air` for the same atmospheric calculation.

This replaces the earlier open question about which historical CIA source family should be used.

## 4. Candidate atmospheric sensitivity equation

For the required atmospheric twilight sensitivity, the historically simplest candidate is the HITRAN2016 `O2-Air` product:

```text
tau_CIA(nu,z,SZA)
  = sum_shell k_O2-Air(nu,T_shell)
              * n_O2,shell
              * n_air,shell
              * ds_shell
```

with:

```text
k           [cm^5 molecule^-2]
n_O2,n_air  [molecule cm^-3]
ds          [cm]
tau_CIA     dimensionless
```

Use the same M4D spherical path semantics and `0.125 km` atmospheric sub-stratification as the monomer calculation.

This equation defines an attenuation sensitivity only. It does not assign a CIA absorption event unit yield into O2(a1Delta) and does not change the first-order `gIRA` source definition.

## 5. Historical temperature-domain limitation

Maté et al. measured the 1.27-micron continuum at three temperatures:

```text
253 K
273 K
296 K
```

HITRAN documentation preserves three O2-Air sets over the 1.27-micron region (approximately `7450-8480 cm^-1`).

The accepted M4D radiative profile includes shells colder than the lowest Maté temperature. Therefore the sensitivity must not silently extrapolate a Maté interpolation below its historical measurement range.

Before executing the sensitivity, freeze one explicit policy:

- a documented endpoint-bound sensitivity below 253 K; or
- another pre-/HITRAN2016 source that genuinely supplies the required colder-temperature behavior and whose combination with Maté is scientifically justified.

Post-2016 theoretical/experimental extensions are useful comparison evidence but are not automatic historical replacements.

## 6. Why CIA still matters even though it is outside baseline

CIA scales with the product of two number densities. It therefore falls rapidly with altitude locally, but illuminated twilight rays to mesospheric targets can have much lower tangent altitudes and traverse substantially denser air.

HITRAN2016 explicitly notes that CIA is relatively important around 1.27 microns because the monomer magnetic-dipole lines are weak. Later direct measurements independently confirm that the Maté/HITRAN2016 continuum has the correct broad scale.

Consequently the baseline may remain monomer-only only if the required twilight sensitivity is quantified and disclosed.

## 7. Exact byte provenance still required

The source family and transfer semantics are now resolved, but the exact historical HITRAN2016 machine-readable CIA bytes are not frozen in the project.

Before executing the sensitivity, record:

- historical provider/archive;
- exact filename;
- edition/version evidence;
- access date;
- byte size;
- SHA-256;
- file header/reference identity;
- spectral coverage;
- all three temperature sets and their row structure.

Do not substitute current HITRAN CIA files silently.

## 8. Required sensitivity acceptance evidence

Compare, for the accepted M4D validation domain:

```text
monomer attenuation only
vs
monomer attenuation + historical O2-Air CIA attenuation
```

Report maximum absolute and relative changes in `gIRA`, including the established rate floors `1e-10`, `1e-12`, and `1e-15 s^-1` and the near-tangent illuminated cases.

If the CIA attenuation changes a scientifically retained baseline case by more than the `0.1%` design tolerance, the attenuation scope must be reopened explicitly before M4D is frozen. That result does not by itself redefine CIA as a first-order excitation source.

## 9. Gate decision

**PASS for baseline semantics; OPEN for required closure sensitivity.**

The `historical_2020` baseline remains monomer resonance excitation/attenuation only. The historical CIA source is now identified as the Maté/HITRAN2016 1.27-micron product, and the atmospheric no-double-counting convention is defined.

M4D must not close until the exact historical CIA asset is frozen and the twilight attenuation sensitivity has been executed with an explicit treatment of temperatures below the Maté measurement range.
