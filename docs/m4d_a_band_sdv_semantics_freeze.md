# M4D A-band principal-isotopologue SDV executable semantics freeze

Status: **EQUATIONS / PARAMETER CONVENTION SELECTED / NUMERICAL CLOSURE PENDING**

Branch: `milestone/m4d-design`

This note freezes the executable line-shape semantics for the 91 principal-isotopologue magnetic-dipole O2 A-band transitions recovered from Drouin et al. (2017). It does not implement production M4D, does not freeze the remaining line-mixing temperature rule, and does not authorize M5.

## 1. Primary source equations

The structured Drouin manuscript, PMC5103325, gives for the resonant main-isotopologue lines the real speed-dependent profile

```text
F(x,y,S,H)
```

with dimensionless detuning and Lorentz width defined by its Eqs. 6-7:

```text
x = [sigma - sigma0
     - p { Xf [delta_f + (T-Tref) delta_f']
           + Xs [delta_s + (T-Tref) delta_s'] }]
    / gamma_D

y = p { Xf gamma_f (Tref/T)^n_f
        + Xs gamma_s (Tref/T)^n_s }
    / gamma_D
```

and the speed-dependent width factor in Eq. 5 is

```text
y * [1 + S (v^2 - 3/2)]
```

where `Tref = 296 K`.

For terrestrial air, Drouin's foreign/self mixture is the atmospheric binary ratio

```text
Xf = X_N2 = 0.79
Xs = X_O2 = 0.21
```

for the source-model reconstruction. This is the source-level mixture used before the HITRAN-facing air representation is formed.

## 2. Final Drouin narrowing decision

The paper explicitly reports tests of speed dependence versus Dicke narrowing. Fitting both was unstable; fitting Dicke narrowing alone produced poorer FTS residuals; subsequent tests with fixed speed dependence plus fitted narrowing were also poorer than speed dependence alone.

Therefore for the accepted historical Drouin candidate:

```text
Dicke / hard-collision narrowing frequency = 0
```

No non-zero velocity-changing collision frequency may be invented for the 91 Drouin magnetic-dipole lines.

## 3. Historical HAPI convention cross-check

The already frozen historical HAPI source is:

```text
hitranonline/hapi
commit f41d9911f2631eed51b96d6c617b4f27786ad477
HAPI 1.1.0.8.2
hapi/hapi.py blob caeab1bfaa278b5420adef7efe7ab566991ba763
```

In that version, `PROFILE_SDVOIGT` calls `pcqsdhc` with

```text
anuVC = 0
eta   = 0
```

and `pcqsdhc` parameterizes the complex collisional term with

```text
c0 = Gam0 + i Shift0
c2 = Gam2 + i Shift2
c0t = c0 - 1.5 c2
c2t = c2
```

which is the quadratic speed dependence

```text
Gam(v) = Gam0 + Gam2 (v^2 - 3/2)
```

in the same Maxwell-speed convention used by Drouin.

Comparing directly with Drouin Eq. 5 therefore fixes the mapping:

```text
Gam2   = S * Gam0
Shift2 = 0
anuVC  = 0
eta    = 0
```

This is not a fitted inference; it follows algebraically from the two published parameterizations.

## 4. Shell-local atmospheric parameters

For each Drouin magnetic-dipole line and each shell:

```text
Gam0(T,p) =
    p * [0.79 gamma_f (296/T)^n_f
         + 0.21 gamma_s (296/T)^n_s]

Shift0(T,p) =
    p * [0.79 {delta_f + (T-296) delta_f'}
         + 0.21 {delta_s + (T-296) delta_s'}]

Gam2(T,p) = S * Gam0(T,p)

Shift2(T,p) = 0
anuVC(T,p)  = 0
eta         = 0
```

Pressure `p` must use the same atmosphere unit convention as the Drouin tabulated coefficients.

The Doppler HWHM is evaluated shell-locally from the line center, absorber mass and shell temperature using the project's already frozen spectroscopy convention.

## 5. Why this is SDVoigt, not a non-zero-narrowing Rautian profile

Drouin presents Eq. 5 in a speed-dependent Rautian family with an optional `H` narrowing term. For the final A-band fit, however, the retained narrowing term is zero.

Consequently the historical executable reduction is:

```text
speed-dependent Voigt
```

or equivalently the HTP/pCqSDHC reduction with `anuVC=eta=Shift2=0`.

Calling this profile "SDRautian" in implementation while assigning a non-zero hard-collision frequency would be scientifically wrong for the selected Drouin fit.

## 6. Line-mixing combination

Drouin Eq. 11 applies first-order line mixing as

```text
kappa_i = rho_O2 * sum_k [ F_k + Y_k(p,T) F'_k ] I_k(T)
```

for the mixed subset.

This note freezes only the isolated-line `F_k` semantics above. The exact shell-temperature evaluation of `Y_k(p,T)` remains a separate gate because Table 22 tabulates air Y factors only at 200, 250, 296 and 340 K, while the mesospheric model may reach lower temperatures.

No arbitrary interpolation/extrapolation of Table-22 Y values is authorized by this note.

## 7. Required numerical verification before final freeze

The analysis implementation must verify at minimum:

1. unit-area normalization of the real SDVoigt profile over a converged spectral support;
2. Voigt limit as `S -> 0`;
3. finite/non-negative total physical absorption after the permitted first-order LM correction;
4. agreement between an independent implementation of the equations above and the frozen historical HAPI `PROFILE_SDVOIGT` reduction at representative line/shell cases;
5. full-path convergence under the M4D spectral and spatial gates.

## 8. Gate result

```text
Drouin Eq. 5/6/7 source semantics:       PASS
historical HAPI convention cross-check: PASS
S -> Gam2 mapping:                       FROZEN (Gam2 = S*Gam0)
speed-dependent shift:                  FROZEN (Shift2 = 0)
Dicke / hard-collision narrowing:       FROZEN OFF (anuVC = 0)
correlation parameter:                  FROZEN (eta = 0)
shell-local gamma/shift equations:      FROZEN
Table-22 Y(T) continuous rule:           OPEN
accepted HITRAN2016 continuity mapping: OPEN
full numerical convergence:             OPEN
```

The principal-isotopologue isolated-line profile is now an executable historical specification. The remaining A-band design work is line-mixing temperature evaluation, local target-edition continuity, and numerical closure.
