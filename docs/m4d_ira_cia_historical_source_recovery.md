# M4D 1.27-micron CIA historical source recovery

Status: **HISTORICAL SOURCE FAMILY AND TRANSFER SEMANTICS RECOVERED / EXACT FILE BYTES PENDING**

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

Later independent CRDS work by Mondelain et al. (2019) explicitly compares against the Maté data *as reproduced in HITRAN2016*, providing an independent witness to this source identity.

## 3. O2-O2 versus O2-Air semantics

HITRAN2016 made an important correction and relabelling relative to HITRAN2012:

- spectra recorded for **pure O2** are placed in the `O2-O2` CIA product;
- spectra recorded for **21:79 O2:N2 mixtures** are placed in the `O2-Air` CIA product;
- the older HITRAN2012 `O2-N2` placement of air-mixture spectra was changed because those spectra already contain both O2-O2 and O2-N2 collisional contributions;
- HITRAN2016 explicitly warns that an atmospheric calculation must **not** add an `O2-O2` contribution on top of `O2-Air` for the same mixture, because that would double-count O2-O2 CIA.

For an atmospheric M4D twilight sensitivity, the simplest historically faithful candidate is therefore to use the historical `O2-Air` product directly:

```text
tau_CIA(nu)
  = sum_shell k_O2-Air(nu,T_shell)
              * n_O2,shell
              * n_air,shell
              * ds_shell
```

where `k` is in `cm^5 molecule^-2`, number densities are in `molecule cm^-3`, and `ds` is in cm.

This candidate avoids reconstructing the 21:79 mixture by separately adding O2-O2 and O2-N2 and obeys the HITRAN2016 no-double-counting instruction.

It is a sensitivity calculation only; it does not redefine `gIRA` as a binary-density production coefficient.

## 4. Historical spectral/temperature coverage

The Maté experiment used high-density FT spectra at three temperatures:

```text
253 K
273 K
296 K
```

Later HITRAN CIA documentation preserves the corresponding historical O2-Air 1.27-micron product as three sets over approximately:

```text
7450-8480 cm^-1
250-296 K listed range
3 sets
```

and attributes that product to the Maté source.

The accepted IRA monomer line subset lies inside this spectral region.

### Temperature-domain consequence

The accepted M4D radiative/background profile can be colder than the lowest Maté measurement. Therefore the historical CIA sensitivity must **not silently extrapolate a Maté interpolation below the source temperature range**.

Before executing the sensitivity, select and document one of the following historical-scope policies:

1. restrict interpolation to shells whose temperatures lie inside the Maté source range and perform an explicit lower-bound/upper-bound sensitivity for colder shells;
2. use a clearly documented constant-endpoint extrapolation as a sensitivity bound, not as a claimed Maté measurement;
3. locate an additional pre-/HITRAN2016 source that legitimately supplies the colder-temperature dependence and justify combining it with Maté.

Do not use the post-2016 Karman theoretical temperature extension merely because modern HITRAN contains it. That would change the historical source generation.

## 5. Exact byte provenance still missing

The historical source family, spectral region, number of temperature sets, density convention and no-double-counting semantics are now identified.

The project has **not yet frozen the exact machine-readable HITRAN2016 CIA bytes** used for the Maté O2-Air product. Current HITRAN CIA files have undergone later updates and cannot be silently relabelled as the 2016 asset.

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

If a historical O2-O2 file is also retained for provenance, freeze it separately, but do not combine it with O2-Air in the atmospheric sensitivity unless a different pair-decomposition calculation is explicitly designed.

## 6. Required interpolation and unit tests once bytes are recovered

The sensitivity implementation/evidence must verify:

1. source temperatures and spectral domain reproduce the frozen historical file headers;
2. `k >= 0` over the usable historical data domain, allowing only explicitly documented measurement noise/format behavior if present;
3. units close exactly:

```text
[cm^5 molecule^-2]
* [molecule cm^-3]
* [molecule cm^-3]
* [cm]
= dimensionless tau
```

4. zero O2 density gives zero CIA optical depth;
5. zero air density gives zero CIA optical depth;
6. scaling either density at fixed conditions scales the local CIA extinction linearly, and scaling both together at fixed mixing ratio gives the expected quadratic-density behavior;
7. `O2-Air` is not combined with a separate O2-O2 term for the same atmospheric mixture;
8. interpolation/extrapolation policy at shell temperatures below the historical Maté range is explicit and sensitivity-labelled.

## 7. Required M4D twilight sensitivity

Once the historical O2-Air bytes are recovered, evaluate at least the already required illuminated twilight/tangent cases using the same `0.125 km` shellwise spherical transfer convention as the monomer calculation.

Compare:

```text
monomer attenuation only
vs
monomer attenuation + historical O2-Air CIA attenuation
```

for `gIRA`.

Report absolute and relative changes across the accepted rate floors (`1e-10`, `1e-12`, `1e-15 s^-1`) and identify the maximum change above each floor.

If CIA changes any scientifically retained `gIRA` baseline case by more than the M4D `0.1%` design tolerance, that does **not** automatically mean CIA becomes a first-order production source. It means the baseline attenuation scope must be reopened explicitly before M4D can be frozen.

## 8. Gate decision

**CIA source discovery is closed; byte materialization and the required twilight sensitivity remain open.**

The historical numerical source for the HITRAN2016 1.27-micron CIA is Maté et al. (1999), and the atmospheric `O2-Air` semantics are sufficiently defined to design the sensitivity without double counting.

The remaining blocker is the exact historical machine-readable HITRAN2016 CIA asset plus a justified treatment of shells below the lowest Maté temperature and the final twilight sensitivity calculation.
