# Isolated A advanced transfer: execution contract

Date: 2026-10-01. M4D remains NOT FROZEN; M4C-R2 and M5 are unchanged.

The supplied starting SHA was `3cc036efc0d77e5f62f5b4fbe01d372d9ba9c5de`.
The remote design branch was already at `25caaf9285545338a6b2cfc259b3348db7857ce3`.
Its six subsequent commits add principal SDV/LM algebra, dispatch tests and CI.
This experiment preserves them and works on `codex/m4d-advanced-transfer`.

## Equations and provenance before implementation

Use the existing frozen SDV contract (Drouin Eqs. 5--7 and pinned HAPI
1.1.0.8.2): `Gam2=S*Gam0`, `Shift2=anuVC=eta=0`, native 0.79 foreign / 0.21
self width and shift. Sigma denotes Gaussian standard deviation in cm^-1.
Line centres, intensities, lower energies and isotopic abundance stay in the
accepted HITRAN2016 records. Drouin intensity/centre copies are not substituted.

The verified PMC XML prose preceding Eq. 10 explicitly says that Y multiplies
the imaginary portion of the line shape; Eq. 11 adds this term. With positive
detuning `nu-nu0-shift` in Eq. 6, the dispersion sign agrees with pinned
`pcqsdhc`. However, this identifies the sign, not the complete Table-22 numeric
normalization. The pre-existing `Re(F) + p*Y(T)*Im(F)` reduction remains candidate
algebra only. Table 22 explicitly labels Y in cm^-1 atm^-1 (confirmed in the
rendered historical supplement), whereas Re(F) and Im(F) from normalized SDV
have the same units. Hence the multiplier requires a dimensionless convention
that is not established by this annotation. Do not silently call the annotation
a typo, insert a Doppler/frequency factor, or infer units from numerical size.
The XML's logarithm in Eq. 10 is also malformed as written; do not repair it
into a new integral or reconstruct W matrices. Nominal LM-enabled rate transfer
now fails closed with a SOURCE CONVENTION BLOCKER. Low-level candidate algebra
and its numerical tests do not resolve this scientific gate.

Enforce exactly 91 d lines, 70 source-supported Y entries, 21 nominal Y=0 lines,
and 59 classic q lines. At shell and target temperatures evaluate the same
profile model; absorber sums include every selected line at every node without
a physical wing cutoff. Separate diagnostics disable LM, choose the frozen
clamp/linear/zero low-T policy, omit the 21 unsupported-Y lines, or omit q lines
in both target and attenuation. Omission bounds the contribution of the no-Y
population; it does not prove robustness against every unknown nonzero Y.
No high-J coefficient is manufactured.

Use the existing spherical geometry and target quadrature for the explicitly
named principal LM-off diagnostic. At every quadrature node, validate total
opacity at both shell and target states; never clip negative candidate mixed
wings or renormalize target support. Principal-only diagnostic rates identify
their selected population and cannot be presented as full 430-line gA.

## Fail-closed scientific gates

1. LM normalization: stop nominal transfer until the historical Table-22
   convention against normalized F/F-prime is demonstrated. The pinned HAPI
   code has Y metadata but no executable LM combination. Source-node recovery,
   parity, positive opacity probes and symmetric principal-value area tests
   cannot establish the coefficient's absolute physical normalization.
2. Table-22 above 340 K: preserve the frozen fail-closed policy. The actual
   accepted column contains hot active shells; no upper-T extrapolation,
   omitted opacity, pressure threshold or Y=0 nominal fallback is authorized.
   LM-off evaluation is explicitly a diagnostic, not the nominal calculation.
3. Rare Galatry: verified auxiliary bytes and 280/280 mapping establish the
   available air/self Dicke fields, but not a complete executable convention.
   Pinned HAPI has metadata/parameter lists for Galatry and no Galatry evaluator.
   The frozen materials do not establish the exact beta-to-profile conversion
   together with shell-temperature dependence. Do not equate beta to hard
   collisions in HTP, reuse n_air as a narrowing exponent, assume beta is
   temperature independent, or invent a self/air mixing rule. Full A transfer
   raises a SOURCE CONVENTION BLOCKER until this evidence is recovered.

## Validation scope

Independently check SDV Maxwell-speed integrals, unit area, Gaussian/Voigt
limits, dispersion parity/sign, Table-22 nodes and interpolation continuity,
sum opacity positivity without clipping, exact mapping and source-order
invariance. Exercise principal transfer on supported synthetic atmospheres:
zero column, shadow/tangent geometry, target/absorber policy consistency, and
spectral refinement. Reproduce historical-source mapping, actual hot-shell
coverage, source-driven principal opacity probes, and the nominal blocker.

Galatry area and zero-beta/strong-narrowing limits are NOT RUN, because there is
no authorized Galatry implementation. Full-domain rates/convergence are NOT RUN.
Run pytest, ruff and all existing validators. The legacy CIA stop validator may
still exit 2 for the historical stop; record that event without reopening the
resolved CIA scope or claiming full M4D acceptance.
