# M4D pressure-broadening and line-shape provenance follow-up

Status: **A SOURCES MATERIALIZED / AIR-DILUENT SEMANTICS CORRECTED / DESIGN NOT FROZEN**

Branch: `milestone/m4d-design`

This note records the current pressure-broadening and profile decisions after direct historical-source acquisition. It does not implement M4D, alter M4C-R2, or authorize M5.

## 1. Accepted starting point

The previous numerical conclusions remain:

- Doppler-only is rejected over the complete spherical twilight domain.
- M4C spherical geometry is retained.
- Shell-local temperature/profile evaluation is mandatory.
- M4D NIR path integration uses `0.125 km` atmospheric sub-stratification and checks against `0.0625 km`.
- Target-temperature cross section multiplied by total slant column is rejected.
- The previous mixed Doppler-target/Voigt-attenuation calculation was a diagnostic, not a final model.
- No arbitrary `+/-10` or `+/-20 cm^-1` absorber truncation is frozen.

## 2. A-band source status

### Principal isotopologue

The official Drouin publisher supplement is now materialized:

```text
publisher URL:
https://ars.els-cdn.com/content/image/1-s2.0-S0022407316301108-mmc1.pdf

bytes:   89406
SHA-256: 12e621d3b5d17e7648d140ea16134e3c04096bd7e47e2c1bb0e2084adeccbb51
pages:   12
```

The NCBI structured manuscript is also frozen as an acquisition witness:

```text
PMC5103325 XML
bytes:   310708
SHA-256: 935fd09d5f619f7eb3f7fac5347e80fa81bc23d3158dc9c519874bb161c364fe
```

Tables 4/5 contain all `91` principal-isotopologue magnetic-dipole line-by-line Drouin parameters. They map `91/91`, with zero unmatched or ambiguous labels, to the historical A-band magnetic-dipole set. Table 22 supplies first-order air Rosenkranz `Y` factors for `70` of those lines at `200, 250, 296, 340 K`.

The remaining principal-isotopologue classification is:

```text
91 magnetic-dipole d lines:
    Drouin SDV source available

70/91 d lines:
    Table-22 first-order line mixing available

21/91 d lines:
    no Table-22 Y value; high-J set explicitly identified

59 electric-quadrupole q lines:
    not part of the Drouin magnetic-dipole update
```

The 21 no-Y d lines contribute about `0.0131464%` of historical iso-1 integrated A strength and the 59 q lines about `0.00079353%`. Neither class is silently deleted; their treatment must be numerically tested.

See `docs/m4d_a_band_drouin_materialization_audit.md`.

### Rare isotopologues

The historical Long/HITRAN2012 Galatry sources are now byte-materialized:

```text
07_A-band_SDF.dat
bytes 6229
SHA-256 7cfefb8040a89cb0e4948c2811a6766b793181646d8188ebfa4d646e063dbd26

07_hit12_0.76mic_Galatry.par
bytes 47231
SHA-256 69c9fd181b5aba8aa818dc906bdc216aaa8cf038eb5687dd4da8f2bb9bf42dab
```

The Galatry auxiliary maps `430/430` to the historical HITRAN2012 A system, including complete Dicke coefficients for all `140 + 140` rare-isotopologue lines. The accepted HITRAN2016 target record remains authoritative for the ordinary line fields; the historical auxiliary supplies the Dicke coefficients.

See `docs/m4d_a_band_auxiliary_mapping_audit.md`.

## 3. Important correction: HITRAN `air` is a diluent coefficient

An earlier candidate formula in this project wrote, for atmospheric O2,

```text
gamma_air * (p - p_O2) + gamma_self * p_O2
```

while simultaneously treating `gamma_air` as an already air-averaged O2 coefficient. Those two interpretations cannot both be used.

HITRAN defines `air` and `self` as separate broadening/diluent choices. HAPI likewise represents the diluent as a composition dictionary and defaults atmospheric calculations to `{'air': 1.0}`. For the O2 A-band specifically, HITRAN2016 states that Drouin foreign-broadening parameters were converted to **air-broadening** parameters using the binary air ratio `[N2]:[O2] = 0.79:0.21`.

Therefore, for the historical terrestrial atmospheric baseline:

```text
an HITRAN air-broadened parameter is applied to the shell air pressure
```

and must **not** then be combined with another 21% self term as though `gamma_air` meant N2-only broadening.

`gamma_self` remains relevant for an explicitly self/O2 diluent condition, not as an additional atmospheric 21% correction on top of an already air-defined parameter.

This correction applies to the B/IRA classic candidates and to any HITRAN-facing A parameterization expressed as `air`.

## 4. Corrected classic B/IRA atmospheric candidate

For the M4D atmospheric baseline, classic B/IRA lines use the historical HITRAN2016 **air** coefficient at shell total pressure:

```text
gamma_L(p,T)
  = gamma_air(296) * p * (296/T)^n_air

nu_shifted(p)
  = nu0 + delta_air * p
```

where `p` is the shell atmospheric pressure in atm.

Do not add a second `gamma_self * p_O2` term to this atmospheric-air calculation.

If a sensitivity deliberately models a different diluent composition, that calculation must state the diluent explicitly and use the corresponding historical coefficients; it must not be conflated with the terrestrial baseline.

### B

Classic HITRAN2016 Voigt remains the baseline candidate. The historically partial/defective qSDV B data are not reproduced silently. A source-corrected qSDV sensitivity on the covered principal-isotopologue lines remains required; a `>0.1%` effect on retained B rates reopens the candidate.

### IRA

Classic HITRAN2016 Voigt remains the monomer baseline candidate, pending final full-domain target+attenuation convergence.

## 5. A principal-isotopologue foreign/self versus HITRAN-air semantics

Drouin Tables 4/5 give native foreign/self quantities. The paper combines the total Lorentz width and shifted frequency from those components before applying the speed-dependent profile.

HITRAN2016 then makes an Earth-atmosphere-facing transformation:

- foreign-broadening line-shape quantities are converted to air-broadening quantities using `0.79:0.21` N2:O2;
- full foreign/self line-mixing matrices are evaluated for one atmosphere of air at four standard temperatures;
- the resulting relation is tabulated as first-order Rosenkranz parameters.

M4D must pick **one coherent representation** for A and use it identically for target and attenuation. It must not mix a native N2 coefficient with a HITRAN air coefficient or apply the 0.79/0.21 combination twice.

The preferred historical target is the HITRAN2016-facing air representation because M4D is reconstructing the HITRAN2016 forcing source. The exact SDV/Y evaluator and temperature rule remain to be frozen.

## 6. A rare-isotopologue precedence

For iso-2/iso-3:

```text
nu, S, E'', gamma_air, gamma_self, n_air, delta_air:
    accepted target-edition HITRAN line record

Galatry/Dicke beta_air, beta_self:
    quantum-identity-matched historical auxiliary record
```

The historical auxiliary contains a small number of stale/swapped redundant classic fields; therefore those repeated fields are not used to override the target-edition line record.

For the atmospheric baseline, use the target-edition **air** Galatry/Dicke coefficients under the same air-diluent semantics. Do not re-mix an air coefficient with 21% self unless explicitly modelling a non-air diluent.

## 7. Pressure shifts

For classic B/IRA and classic fallback components:

```text
nu_shifted = nu0 + delta_air * p
```

with shell-local atmospheric pressure and no invented temperature dependence.

For Drouin A magnetic-dipole lines, Tables 4/5 include foreign/self shifts and linear temperature-shift coefficients. The final HITRAN-facing advanced evaluator must reproduce the historically selected air representation rather than force the classic shift rule onto it.

A full-path pressure-shift sensitivity remains required.

## 8. Line mixing and profile invariants

For A line mixing, physical tests apply to the total absorption, not blindly to each algebraic mixing term. Required checks include:

- finite total absorption;
- physically nonnegative total band absorption over the validation grid;
- zero-column unattenuated limit;
- finite/nonnegative final excitation rates;
- source-order invariance;
- normalization/conservation consistent with the selected Rosenkranz/Drouin formalism;
- same per-transition profile semantics in target excitation and shell attenuation.

For classic Voigt/Galatry components, integrated normalized profile strength must recover `S(T)` within the declared numerical tolerance.

## 9. Far-wing / support strategy

No universal physical `+/-N cm^-1` cutoff is frozen.

For B/IRA classic profiles, the selected numerical candidate is to evaluate attenuation from **all accepted absorber lines in the band** at each target quadrature node, while converging target integration support/order independently.

For A, support and quadrature must be validated for the final SDV+Rosenkranz and Galatry components rather than borrowing an isolated-Voigt wing rule.

## 10. IRA CIA

The monomer baseline still excludes CIA. The required Option-B twilight sensitivity uses historical Maté `O2-Air` semantics without separately adding O2-O2.

The cold-shell policy is now frozen in `docs/m4d_ira_cia_historical_source_recovery.md`:

- linear interpolation at `253..296 K`;
- endpoint-clamped nominal sensitivity outside the measured range;
- measured-three-spectrum min/max envelope as historical-source uncertainty;
- no post-2016 temperature extension silently substituted.

The exact historical machine-readable Maté `O2-Air` asset is still pending.

## 11. Current gate

**M4D DESIGN REMAINS NOT FROZEN.**

Closed since the previous follow-up:

```text
A1 Drouin publisher source bytes:        PASS
A Tables 4/5 91-line mapping:            PASS
A Table-22 70-line LM source:            PASS
A2/A3 historical auxiliary bytes:        PASS
A rare historical mapping:              430/430 PASS
A rare Dicke coverage:                  280/280 PASS
B/IRA atmospheric air semantics:        CORRECTED
CIA cold-shell sensitivity policy:       FROZEN
```

Still open:

1. final executable SDV/Rosenkranz temperature semantics for A iso-1;
2. source-supported/numerically validated treatment of the 21 no-Y d lines and 59 q lines;
3. accepted local HITRAN2016 continuity maps (`91/91` Drouin d and `280/280` rare Galatry);
4. exact historical Maté `O2-Air` CIA machine-readable bytes;
5. corrected B qSDV sensitivity;
6. pressure-shift sensitivity;
7. complete target+attenuation numerical convergence across the required altitude/SZA/tangent domain.

Do not create `docs/m4d_final_design_specification.md` and do not authorize production M4D implementation until these gates close.
