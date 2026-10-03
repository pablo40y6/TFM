# M4D historical solar forcing freeze

Status: **SOURCE AND NUMERICAL CONVENTION SELECTED / DERIVED-ASSET HASH PENDING**

Branch: `milestone/m4d-design`

This note freezes the solar spectral forcing convention for the independent M4D reconstruction. It does not authorize implementation by itself.

## 1. Selected source

The M4D historical reconstruction will use the **Wehrli (1985) WMO/WRC extraterrestrial solar irradiance spectrum** as the solar source for `gA`, `gB`, and `gIRA`.

Authoritative institutional source:

- National Laboratory of the Rockies (NLR; historical NREL solar-resource archive)
- dataset title: `1985 Wehrli Standard Extraterrestrial Solar Irradiance Spectrum`
- tabulated quantity: wavelength in nm and extraterrestrial irradiance in W m^-2 nm^-1
- historical reference: C. Wehrli, *Extraterrestrial Solar Spectrum*, Publication No. 615, Physikalisch-Meteorologisches Observatorium + World Radiation Center, Davos, 1985
- dataset page: https://www.nlr.gov/grid/solar-resource/spectra-wehrli
- text product: https://www.nlr.gov/media/docs/libraries/grid/wehrli85.txt

The institutional description identifies the spectrum with the World Meteorological Organization / World Radiation Center standard extraterrestrial distribution.

## 2. Stable public byte witness

For reproducibility independent of mutable institutional URLs, an immutable public Git witness is pinned:

- repository: `mkelley/mskpy`
- commit: `4deb59f47b3fb72991958cbc95a393c8e4c68660`
- path: `mskpy/data/wehrli85.txt`
- Git blob SHA-1: `42abbff356d8b6528ede3ca7def30778dea2a3f9`
- repository-reported size: `28,555` bytes

This mirror carries the same three-column Wehrli table (`nm`, `W/m2/nm`, cumulative/integrated column). During implementation the exact bytes used to generate the M4D solar asset must be materialized and assigned a project SHA-256.

## 3. Why Wehrli is selected

Anqi Li's 2017 thesis explicitly states that the A-band solar irradiance used in the historical `gA` calculation is taken from WMO. Its recovered legacy code uses the numerical photon-flux factor `2.742e13 photons cm^-2 s^-1 (cm^-1)^-1` near 762 nm.

The Wehrli/WMO tabulation gives, around the A band:

- 761 nm: 1.238 W m^-2 nm^-1
- 763 nm: 1.242 W m^-2 nm^-1
- linear value at 762 nm: 1.240 W m^-2 nm^-1

Converted to photons per unit wavenumber, this is about `2.762e13 photons cm^-2 s^-1 (cm^-1)^-1`, only ~0.73% above the recovered legacy value. This is a strong numerical consistency check linking the legacy WMO statement to the Wehrli standard.

Li et al. (2020) does not publish a separate resolved solar-spectrum recipe for all three g-factor profiles. Therefore extension of the same Wehrli/WMO source to B and IRA is explicitly classified as a **historical reconstruction choice**, not as a claim that Li et al. documented this exact file.

## 4. Frozen interpolation and unit convention

The baseline will evaluate the tabulated Wehrli irradiance at each HITRAN line center.

For a line center `nu_cm1`:

```text
lambda_nm = 1.0e7 / nu_cm1
```

Use ordinary linear interpolation in wavelength on the Wehrli `W m^-2 nm^-1` column. No extrapolation is permitted for the three target systems; all required wavelengths lie inside the table domain.

Convert interpolated spectral irradiance `I_lambda` to photon spectral flux per unit wavenumber using:

```text
E_photon_J = h * c / lambda_m
phi_lambda = I_lambda / E_photon_J / 1.0e4
            # photons cm^-2 s^-1 nm^-1

dlambda_nm_dnu_cm1 = lambda_nm**2 / 1.0e7

phi_nu = phi_lambda * dlambda_nm_dnu_cm1
       # photons cm^-2 s^-1 (cm^-1)^-1
```

Use exact SI values of `h` and `c` from the implementation's pinned physical constants. The derived `phi_nu` multiplies HITRAN line cross sections expressed per wavenumber.

This convention is chosen instead of introducing an undocumented modern high-resolution solar spectrum. It retains the historical WMO lineage while allowing B and IRA to be reconstructed consistently.

## 5. Band-center regression anchors

The following Wehrli values are useful independent diagnostics; they are not substitutes for per-line interpolation:

| nominal band | wavelength | Wehrli irradiance | derived photon flux per cm^-1 |
| --- | ---: | ---: | ---: |
| B | 688 nm | ~1.466 W m^-2 nm^-1 | ~2.4034e13 photons cm^-2 s^-1 (cm^-1)^-1 |
| A | 762 nm | ~1.240 W m^-2 nm^-1 | ~2.7619e13 photons cm^-2 s^-1 (cm^-1)^-1 |
| IRA | 1270 nm | ~0.4385 W m^-2 nm^-1 | ~4.5217e13 photons cm^-2 s^-1 (cm^-1)^-1 |

The 688-nm value is the linear interpolation of the 687/689-nm tabulation and the 762-nm value is the interpolation of 761/763 nm. Near 1270 nm the table gives 1267.5/1272.5-nm values around 0.438/0.439 W m^-2 nm^-1.

## 6. Optically thin diagnostic against historical g-factor anchors

As a deliberately simple diagnostic only, multiplying the 296-K summed HITRAN2016 line strengths by the nominal band-center Wehrli photon flux gives approximately:

- A: `~6.23e-9 s^-1`
- B: `~3.60e-10 s^-1`
- IRA: `~1.46e-10 s^-1`

These are **not final M4D values** because line-strength temperature scaling, per-line irradiance, and attenuation have not yet been applied. Their purpose is only to catch gross normalization/unit errors.

The IRA estimate is close to the independent Zhu et al. (2007) direct-excitation scale of `1.54e-10 s^-1`; the A value has the expected few-e-9 s^-1 scale. Final validation will be performed after the full temperature-scaled calculation is implemented.

## 7. Solar variability scope

The historical baseline uses the fixed Wehrli standard spectrum and does not introduce solar-cycle/time-dependent NIR variability into M4D. Such variability may be a later sensitivity if scientifically needed, but it must not be mixed into the frozen `historical_2020` baseline.

## 8. Implementation materialization requirement

Before M4D closure:

1. preserve the exact source bytes used, or a deterministic project-derived table if redistribution policy requires it;
2. record source commit/blob and source/project SHA-256;
3. freeze the interpolation implementation;
4. test the 688-, 762-, and 1270-nm anchors above;
5. test the legacy 762-nm photon-flux comparison;
6. ensure that wavelength/wavenumber Jacobian conversion is explicitly unit-tested.

## 9. Gate decision

**PASS — the M4D historical solar source and numerical conversion/interpolation convention are selected.**

The remaining work is deterministic asset materialization and implementation testing, not solar-source discovery.