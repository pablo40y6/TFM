# M4D historical solar-forcing reconstruction

Status: **SOLAR SOURCE CANDIDATE SELECTED / NORMALIZATION FORENSICS PASSED / DESIGN NOT YET FROZEN**

Branch: `milestone/m4d-design`

This note records the independent reconstruction of the extraterrestrial solar forcing needed by `gA`, `gB`, and `gIRA`. It does not authorize M4D implementation and does not change the accepted M4C-R2 baseline.

## 1. Historical source selected for evaluation

The strongest historically coherent source identified so far is the **1985 Wehrli Standard Extraterrestrial Solar Irradiance Spectrum**.

The current U.S. National Laboratory of the Rockies (NLR; formerly NREL solar-resource archive) describes this file as the World Meteorological Organization / World Radiation Data Centre Wehrli air-mass-zero extraterrestrial solar spectral irradiance distribution. It cites:

- C. Wehrli, *Extraterrestrial Solar Spectrum*, Publication no. 615, PMO/WRC, Davos, July 1985;
- H. Neckel and D. Labs (1981), *Improved Data of Solar Spectral Irradiance from 0.33 to 1.25 micron*.

Archive page:

- https://www.nlr.gov/grid/solar-resource/spectra-wehrli

Archived text data:

- https://www.nlr.gov/media/docs/libraries/grid/wehrli85.txt

This provenance is especially relevant because Anqi Li (2017) explicitly states that the 762-nm solar irradiance used in the legacy A-band `gA` calculation comes from **WMO**.

For A-band, Wehrli is therefore not an arbitrary modern solar spectrum: it is a direct historical candidate for the source family named by the legacy thesis. For B and IRA, using the same spectrum would be a transparent reconstruction choice because Li et al. (2020) does not specify the exact solar-spectrum product behind all three `g` profiles.

## 2. Official tabulated values around the three systems

The NLR text file gives irradiance in `W m^-2 nm^-1`.

### B band, near 688 nm

Relevant entries are:

| wavelength (nm) | irradiance (W m^-2 nm^-1) |
| ---: | ---: |
| 685 | 1.457 |
| 687 | 1.469 |
| 689 | 1.463 |
| 691 | 1.450 |
| 693 | 1.450 |
| 695 | 1.438 |
| 697 | 1.418 |
| 699 | 1.427 |
| 701 | 1.388 |

Linear interpolation at 688 nm gives `1.466 W m^-2 nm^-1`.

### A band, near 762 nm

Relevant entries include:

| wavelength (nm) | irradiance (W m^-2 nm^-1) |
| ---: | ---: |
| 749 | 1.271 |
| 751 | 1.263 |
| 753 | 1.260 |
| 755 | 1.256 |
| 757 | 1.249 |
| 759 | 1.241 |
| 761 | 1.238 |
| 763 | 1.242 |
| 765 | 1.222 |
| 767 | 1.186 |
| 769 | 1.204 |
| 771 | 1.205 |
| 773 | 1.209 |
| 775 | 1.189 |
| 777 | 1.197 |
| 779 | 1.188 |

Linear interpolation at 762 nm gives `1.240 W m^-2 nm^-1`.

### IRA, near 1.27 micron

Relevant entries include:

| wavelength (nm) | irradiance (W m^-2 nm^-1) |
| ---: | ---: |
| 1222.5 | 0.481 |
| 1227.5 | 0.481 |
| 1232.5 | 0.484 |
| 1237.5 | 0.477 |
| 1242.5 | 0.477 |
| 1247.5 | 0.466 |
| 1252.5 | 0.474 |
| 1257.5 | 0.463 |
| 1262.5 | 0.444 |
| 1267.5 | 0.438 |
| 1272.5 | 0.439 |
| 1277.5 | 0.453 |
| 1282.5 | 0.435 |
| 1287.5 | 0.437 |
| 1292.5 | 0.442 |
| 1297.5 | 0.438 |
| 1302.5 | 0.438 |
| 1307.5 | 0.429 |
| 1312.5 | 0.419 |
| 1317.5 | 0.416 |
| 1322.5 | 0.416 |

Linear interpolation at 1270 nm gives approximately `0.4385 W m^-2 nm^-1`.

## 3. Conversion to photon spectral flux per wavenumber

For line strength `S` in the standard HITRAN units compatible with integration over wavenumber, the relevant solar quantity is photon flux per wavenumber.

For wavelength `lambda_nm` and spectral irradiance `E_lambda` in `W m^-2 nm^-1`:

```text
E_photon = h c / lambda
Phi_lambda = E_lambda / E_photon
Phi_nu_tilde = (Phi_lambda / 1e4) * lambda_nm^2 / 1e7
```

where the `/1e4` converts `m^-2` to `cm^-2`, and `lambda_nm^2 / 1e7` is the absolute Jacobian `|d lambda_nm / d nu_tilde|` in `nm per cm^-1`.

Using exact SI `h` and `c`, the interpolated Wehrli values give approximately:

| reference wavelength | E_lambda | photon flux per cm^-1 |
| ---: | ---: | ---: |
| 688 nm | 1.466 W m^-2 nm^-1 | `2.40338e13 photons cm^-2 s^-1 (cm^-1)^-1` |
| 762 nm | 1.240 W m^-2 nm^-1 | `2.76191e13 photons cm^-2 s^-1 (cm^-1)^-1` |
| 1270 nm | 0.4385 W m^-2 nm^-1 | `4.52172e13 photons cm^-2 s^-1 (cm^-1)^-1` |

## 4. Legacy A-band normalization closes closely

The recovered Anqi `gfactor.m` hard-codes:

```text
2.742e13 photons cm^-2 s^-1 (cm^-1)^-1
```

at 762 nm.

The Wehrli interpolation gives `2.76191e13` in the same units. The difference is about `0.73%`.

Conversely, the legacy constant corresponds to about `1.231 W m^-2 nm^-1` at 762 nm, while the simple Wehrli 761/763 interpolation is `1.240 W m^-2 nm^-1`.

This is strong numerical evidence that Anqi's hard-coded A-band solar normalization is consistent with the historical WMO/Wehrli spectrum, allowing for interpolation/rounding/product details that are not recoverable from the thesis listing alone.

The project therefore does not need to preserve `2.742e13` as an unexplained magic constant. It can preserve it as a legacy regression anchor while using an explicitly documented historical solar spectrum in the reconstructed M4D physics.

## 5. Preliminary unattenuated line-sum check

Before any line-profile or twilight transfer is implemented, an optically thin/exo-atmospheric sanity test can be performed from the accepted target-band line subsets.

Because a normalized line profile integrates to unity, if the extraterrestrial solar photon flux varies negligibly across an individual Doppler line,

```text
g0(T) ~= sum_i S_i(T) * Phi_sun(nu_i)
```

where `Phi_sun(nu_i)` is obtained by linearly interpolating the Wehrli irradiance to each HITRAN line wavelength and converting it to photon flux per wavenumber.

Using the acquired target subsets and their HITRAN reference strengths at approximately 296 K gives the preliminary results:

| system | lines | preliminary g0 at ~296 K |
| --- | ---: | ---: |
| `gA`, b(0)-X(0) | 430 | `6.2053e-9 s^-1` |
| `gB`, b(1)-X(0) | 320 | `3.5989e-10 s^-1` |
| `gIRA`, a(0)-X(0) | 835 | `1.4645e-10 s^-1` |

A provisional TIPS-2017 temperature scaling check over 200-280 K changes these integrated values only weakly; for example near 220 K the corresponding estimates are approximately `6.2000e-9`, `3.5853e-10`, and `1.4594e-10 s^-1`.

These numbers are **diagnostic calculations, not yet frozen regression values**. The final values must be regenerated by repository code from the frozen HITRAN/TIPS/Wehrli assets and tested independently.

## 6. Comparison with independent literature anchors

The recovered literature anchors are:

- Zhu, Yee & Talaat (2007): A-band excitation `5.35e-9 s^-1`;
- Zhu, Yee & Talaat (2007): direct 1.27-micron excitation `1.54e-10 s^-1`;
- Marsh et al. (2002): combined atmospheric-band A+B result near `5.56e-9 s^-1`.

The Wehrli/HITRAN2016 preliminary result for `gIRA` is within roughly 5% of the Zhu direct-IRA anchor, which is a strong normalization sanity check given the different spectroscopy/solar inputs and historical methods.

The reconstructed `gA` is about 16% above Zhu's A-band number, while `gA + gB` is also above the Marsh combined value. This discrepancy is **not treated as a failure of the source reconstruction** because the comparison calculations do not yet share the same spectroscopy edition, solar spectrum, exact band definition, isotopologue treatment, or reference-temperature convention. It is instead a required validation item for the final M4D design.

No empirical rescaling may be introduced merely to force agreement with these literature values.

## 7. Solar interpolation rule proposed for the frozen design

The evidence favours using the original Wehrli tabulation as a single historical extraterrestrial solar source for all three target systems, with deterministic **linear interpolation in wavelength** to each HITRAN line centre.

This is preferred over one constant per band because:

- the historical source already spans all A/B/IRA wavelengths;
- it preserves the observed spectral slope/structure across each band at the resolution actually provided by Wehrli;
- it removes arbitrary choices of a single representative wavelength;
- it reproduces the legacy A-band WMO normalization closely without copying its unexplained constant;
- line-centre interpolation is sufficient for the extraterrestrial irradiance because the solar spectrum is effectively constant across the width of an individual mesospheric Doppler line at Wehrli resolution.

For A-band, this is a reconstruction tightly linked to the legacy WMO statement. For B and IRA, it must be described explicitly as a **historical reconstruction choice**, not as a demonstrated statement about the unpublished Li-2020 solar input.

No extrapolation outside the frozen Wehrli wavelength domain will be allowed. The three accepted target subsets all lie inside it.

## 8. Direct-beam geometry should reuse the accepted M4C ray geometry

M4C-R2 already freezes a spherical direct-beam geometry with:

- Earth radius 6370 km;
- radiative support from 0 to 150 km in 1-km shells;
- exact shell path lengths through a spherical atmosphere;
- physical target-dependent twilight shadow;
- shell densities from arithmetic endpoint means;
- optical-depth units `cm2 * molecule cm^-3 * cm`;
- the physically correct unattenuated limit when optical depth is zero.

M4D should reuse this accepted geometry rather than introduce a second solar-ray implementation. The spectroscopy-specific change is that O2 line cross sections depend on shell temperature, so line optical depth should be accumulated shell by shell rather than approximated as one target-temperature cross section times a total O2 column:

```text
tau_i(z,SZA) = sum_shell sigma_i[T_shell] * n_O2_shell * ds_shell
```

This shellwise treatment is the scientifically preferred reconstruction. It remains subject to numerical-convergence testing before the design is frozen.

## 9. Remaining solar/radiative decisions before design freeze

The historical solar-source discovery itself is now sufficiently narrow that no further open-ended solar-spectrum search is justified. Remaining work is methodological:

1. freeze the exact NLR Wehrli text asset identity and project-local provenance/hash;
2. freeze deterministic wavelength interpolation and SI-to-photon-flux conversion tests;
3. determine the line-profile quadrature / wing truncation required for attenuated line-by-line transfer;
4. test Doppler-only against pressure broadening over 50-100 km, with special attention to 50 km and extreme twilight;
5. decide whether 1.27-micron CIA/continuum contributes only to a documented sensitivity/attenuation extension or to the baseline;
6. regenerate the unattenuated `g0(T)` anchors in the final implementation and explain, rather than tune away, differences from Zhu/Marsh;
7. specify convergence tolerances for spectral quadrature and shell/ray calculations.

## 10. Current decision

The solar-source part of M4D is now assessed as:

**PASS TO DESIGN FREEZE — use Wehrli 1985 WMO/WRC AM0 as the historical extraterrestrial solar-spectrum source, with linear interpolation to HITRAN line centres, unless the remaining numerical sensitivity work demonstrates a material problem.**

This does not yet make M4D `DESIGN FROZEN`. The remaining gates are line-profile/broadening, twilight optical-depth numerics, CIA scope, deterministic asset materialization, and final validation criteria.