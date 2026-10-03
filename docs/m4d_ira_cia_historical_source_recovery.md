# M4D 1.27-micron CIA historical source recovery

Status: **HISTORICAL SOURCE FAMILY + TRANSFER SEMANTICS + COLD-SHELL POLICY RECOVERED / EXACT FILE BYTES PENDING**

Branch: `milestone/m4d-design`

This note records the historical source and usage semantics required for the Option-B 1.27-micron CIA twilight sensitivity. It does not add CIA to the historical monomer `gIRA` baseline, implement M4D, alter M4C-R2, or start M5.

## 1. Scope

The accepted `gIRA` baseline remains the first-order monomer excitation

```text
O2(X, v''=0) + h nu -> O2(a1Delta_g, v'=0)
```

represented by the accepted HITRAN2016 `a(0)-X(0)` line subset.

Collision-induced absorption is a separate binary-density opacity. In M4D it remains outside the monomer source coefficient and outside baseline attenuation, but the previously selected Option B requires a documented historical twilight sensitivity before milestone closure.

## 2. HITRAN2016 source identity

Gordon et al. (2017), HITRAN2016 Section 4.1, explicitly states that the 1.27-micron CIA data were revised in HITRAN2016 and that **all data included for this transition are taken from Maté et al. (1999)**:

```text
B. Maté, C. Lugez, G. T. Fraser, W. J. Lafferty,
Absolute intensities for the O2 1.27 um continuum absorption,
J. Geophys. Res. Atmos. 104 (1999) 30585-30590,
DOI 10.1029/1999JD900824
```

This supersedes using Smith & Newnham as the numerical source for the historical HITRAN2016 sensitivity. Smith/Newnham remains useful independent physical evidence for the existence and scale of the continuum.

The NIST record for Maté et al. independently confirms measurements for pure O2 and O2/N2 mixtures at `253`, `273`, and `296 K`, after removal of the overlapping sharp monomer lines, and states that the binary collision coefficients are available as a function of frequency for atmospheric modelling.

Later independent CRDS work explicitly compares against the Maté data as represented in HITRAN2016, providing an additional witness to the source identity.

## 3. O2-O2 versus O2-Air semantics

HITRAN2016 made an important correction and relabelling relative to HITRAN2012:

- spectra recorded for **pure O2** are placed in the `O2-O2` CIA product;
- spectra recorded for **21:79 O2:N2 mixtures** are placed in the `O2-Air` CIA product;
- the older HITRAN2012 `O2-N2` placement of air-mixture spectra was changed because those spectra already contain both O2-O2 and O2-N2 collisional contributions;
- HITRAN2016 explicitly warns that an atmospheric calculation must **not** add an `O2-O2` contribution on top of `O2-Air` for the same mixture, because that would double-count O2-O2 CIA.

For the M4D atmospheric twilight sensitivity, use the historical `O2-Air` product directly:

```text
tau_CIA(nu)
  = sum_shell k_O2-Air(nu,T_shell)
              * n_O2,shell
              * n_air,shell
              * ds_shell
```

where `k` is in `cm^5 molecule^-2`, number densities are in `molecule cm^-3`, and `ds` is in cm.

This obeys the HITRAN2016 absorber/air convention and avoids reconstructing the 21:79 mixture by separately adding O2-O2 and O2-N2.

It is a sensitivity calculation only; it does not redefine `gIRA` as a binary-density production coefficient.

## 4. Historical spectral/temperature coverage

The Maté experiment measured the 1.27-micron continuum at:

```text
253 K
273 K
296 K
```

The historical HITRAN CIA documentation and the later 2018 CIA inventory preserve the corresponding `O2-Air` product as three sets over approximately:

```text
7450-8480 cm^-1
250-296 K listed range
3 sets
source: Maté et al. (1999)
```

The accepted IRA monomer line subset lies inside this spectral region.

### 4.1 Frozen cold-shell sensitivity policy

The accepted M4D radiative/background profile can be colder than the lowest Maté measurement. The project will **not** invent a physical extrapolation below the historical source range and will **not** import the post-2016 Karman temperature extension into `historical_2020`.

For the required Option-B CIA sensitivity, use this deterministic policy:

```text
253 K <= T <= 296 K:
    linear interpolation in temperature at each CIA spectral grid point

T < 253 K:
    nominal historical sensitivity = 253 K endpoint spectrum

T > 296 K, if encountered:
    nominal historical sensitivity = 296 K endpoint spectrum
```

The endpoint use outside the measured range is explicitly an **endpoint-clamped sensitivity convention**, not a claim that Maté measured those temperatures and not a physical extrapolation law.

For every shell outside `[253,296] K`, also execute a source-envelope uncertainty case using the minimum and maximum CIA coefficient available among the three measured Maté temperature sets at each spectral point. Propagate both envelope bounds through the same spherical transfer calculation.

This closes the cold-shell *design choice* while retaining the uncertainty caused by the historical source limit. The closure criterion is:

- if the nominal CIA sensitivity itself changes a scientifically retained `gIRA` case by more than `0.1%`, reopen the baseline attenuation scope;
- if the measured-temperature envelope changes the conclusion about whether the `0.1%` threshold is crossed, classify CIA as an unresolved historical-source limitation and do not freeze M4D until that ambiguity is addressed.

This convention deliberately avoids using later spectroscopy to manufacture information that the historical source did not contain.

## 5. Exact byte provenance still missing

The historical source family, spectral region, number of temperature sets, density convention, no-double-counting semantics, and out-of-range temperature policy are now identified.

The project has **not yet frozen the exact machine-readable HITRAN2016 CIA bytes** used for the Maté `O2-Air` product. Current HITRAN CIA files have undergone later updates and cannot be silently relabelled as the 2016 asset.

Historical archive evidence establishes that HITRAN CIA was distributed as static ASCII, and HITRAN2016 explicitly states that the Maté 21:79 mixture spectra were moved into the newly introduced `O2-Air` product. However, a byte-identical 2016 file has not yet been materialized in the current environment.

Before numerical closure, record at minimum:

- exact historical provider/archive;
- exact filename;
- edition/version evidence;
- retrieval/access date;
- byte size;
- SHA-256;
- header/reference identity;
- spectral coverage;
- the three source temperatures and row/set structure.

If a historical `O2-O2` file is also retained for provenance, freeze it separately, but do not combine it with `O2-Air` in the atmospheric sensitivity unless a different pair-decomposition calculation is explicitly designed.

## 6. Required interpolation and unit tests once bytes are recovered

The sensitivity implementation/evidence must verify:

1. source temperatures and spectral domain reproduce the frozen historical file headers;
2. spectral grids of the three Maté temperature sets are either identical or are mapped by a deterministic documented interpolation before temperature interpolation;
3. `k >= 0` over the usable historical data domain, allowing only explicitly documented measurement-noise/format behavior if present;
4. units close exactly:

```text
[cm^5 molecule^-2]
* [molecule cm^-3]
* [molecule cm^-3]
* [cm]
= dimensionless tau
```

5. zero O2 density gives zero CIA optical depth;
6. zero air density gives zero CIA optical depth;
7. scaling either density at fixed conditions scales the local CIA extinction linearly, and scaling both together at fixed mixing ratio gives the expected quadratic-density behavior;
8. `O2-Air` is not combined with a separate O2-O2 term for the same atmospheric mixture;
9. temperatures inside `[253,296] K` use deterministic linear interpolation;
10. temperatures outside the measured range use the frozen endpoint-clamp convention plus the three-spectrum measured-source envelope, with both explicitly labelled as sensitivities rather than source measurements.

## 7. Required M4D twilight sensitivity

Once the historical `O2-Air` bytes are recovered, evaluate at least the already required illuminated twilight/tangent cases using the same `0.125 km` shellwise spherical transfer convention as the monomer calculation.

Compare:

```text
monomer attenuation only
vs
monomer attenuation + historical O2-Air CIA attenuation
```

for `gIRA`, for both the nominal endpoint-clamped temperature treatment and the measured-source envelope bounds.

Report absolute and relative changes across the accepted rate floors (`1e-10`, `1e-12`, `1e-15 s^-1`) and identify the maximum change above each floor.

If CIA changes any scientifically retained `gIRA` baseline case by more than the M4D `0.1%` design tolerance, that does **not** automatically mean CIA becomes a first-order production source. It means the baseline attenuation scope must be reopened explicitly before M4D can be frozen.

## 8. Gate decision

**CIA source discovery, transfer semantics and cold-shell policy are closed; byte materialization and the required twilight sensitivity remain open.**

The historical numerical source for the HITRAN2016 1.27-micron CIA is Maté et al. (1999), the atmospheric `O2-Air` semantics are defined without double counting, and the project now has a deterministic historical-source-limited rule for shells outside the Maté temperature range.

The remaining CIA blocker is the exact historical machine-readable HITRAN2016 `O2-Air` asset plus the final twilight sensitivity calculation.
