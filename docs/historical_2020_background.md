# Historical-2020 static background (Milestone 4A)

## Frozen case

`midlatitude_equinox_quiet` is a reproducible noon snapshot, not a particular
Odin observation. It uses NRLMSISE-00 (Picone, Hedin, Drob & Aikin, 2002)
through generation-only `pymsis==0.12.0`, explicitly selecting `version=0`.
The date is 2020-03-20 12:00 UTC, latitude +45 degrees, longitude 0 degrees,
F10.7(previous day)=150, F10.7A(81 day)=150, and daily Ap=4 with the explicit
row `[4,4,4,4,4,4,4]`. Derived local solar time is 12 h.

All 14 named standard options are 1, producing the explicit 25-element vector
of ones. Daily-Ap mode is used. Every driver is supplied, so automatic
space-weather acquisition is unreachable on this path.

## Native atmosphere, M, and Li model composition

`pymsis` returns temperature, mass density, and native species. Number density
is converted by `1 m^-3 = 1e-6 molecule cm^-3`. The model air density is

`M = N2 + O2 + O + He + H + Ar + N`.

Anomalous O is excluded; mass density and an assumed molecular weight are not
used. MSIS-00 marks unavailable low-altitude trace-species outputs with a
sentinel that `pymsis` exposes as `NaN`; these unavailable terms contribute
zero to M, while the diagnostic native columns preserve `NaN` transparently.

The chemistry does not use native diffusive O2/N2 fractions. Following Li 2020:

- `O2_model = 0.21 M`
- `N2_model = 0.78 M`
- `CO2_model = 405e-6 M`

Those fields populate M3 `LocalBackground`.

## Prescribed H2O and H2

Brasseur & Solomon (2005), Appendix 6 Tables A.6.1 and A.6.2.a supply printed
geometric height and H2O/H2 VMR. M4A uses the VMR columns, interpolating
linearly in `log10(VMR)` against geometric height and multiplying by the local
MSIS-derived M. No H2O/H2 extrapolation occurs over 50--100 km.

The book describes these SOCRATES profiles as approximate zonal, latitudinal,
and annual averages suitable for crude estimates. They are **prescribed
baseline climatological profiles**, not observations or validation truth.

## External O3 approximation

Appendix 6 Tables A.6.1/A.6.2.c supply the O3 VMR. Interpolation is linear in
`log10(O3 VMR)` versus geometric height. Above 108.4 km the last two positive
knots only, `(104.0 km, 3.0e-6)` and `(108.4 km, 1.1e-6)`, define the log-linear
extension to 150 km. There is no floor, clipping, or forced zero.

This is explicitly an **M4A baseline external-O3 approximation**. Li used CMAM
ozone in parts of its work; no versioned CMAM asset is present. M4B must compare
this upper tail with a zero-above-last-knot alternative.

For a supplied 51-value dynamic O3 vector, 0--49 and 101--150 km retain the
reference, while 50--100 km are replaced exactly. Dynamic values win at both
50 and 100 km. There is no blending or smoothing.

## Grids and time assumption

The chemical grid is exactly `arange(50,101,1)` (51 levels). The profile-support
grid is exactly `arange(0,151,1)` (151 nodes); M4A defines nodes only. It does
not define layers, interfaces, paths, quadrature, SZA, or optical depth.

The noon temperature, M, O2, N2, CO2, H2O, and H2 profiles are held fixed in a
future baseline 24 h chemical integration. This intentionally excludes tides
and diurnal atmospheric variability to isolate photochemical time dependence.

## Runtime API

```python
from tfm_photochem.historical_2020 import load_baseline_background

profile = load_baseline_background()
local = profile.local_background_at(80.0)
o3_column = profile.compose_radiative_ozone(dynamic_o3_cm3)
```

Runtime loading verifies asset hashes, performs no interpolation of T/M, has no
time dimension, does not import `pymsis`, and uses no network.

## M4B boundary

M4A calculates none of JH, J_SRC, J_LYA, J_H2O2, J_H2O_A, J_H2O_B, gA, gB,
or gIRA. Solar geometry, ray paths, attenuation, spectral data, cross sections,
and HITRAN remain entirely for a separately authorized M4B.
