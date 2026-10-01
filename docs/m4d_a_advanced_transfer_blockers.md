# A advanced transfer scientific blockers

2026-10-01. Status: **PARTIAL ISOLATED IMPLEMENTATION / SCIENTIFIC BLOCKERS /
M4D NOT FROZEN**. M4C-R2 remains accepted and M5 has not started. The IRA CIA
post-stop scope resolution remains in force.

## LM coefficient normalization

Drouin's verified PMC5103325 XML identifies F-prime as the imaginary component
and Eq. 11 adds Y times that component. This supports the sign of the earlier
candidate algebra. It does not reconcile the absolute coefficient units.
The publisher supplement Table 22, page 11, labels Y in cm^-1 atm^-1, including
a MHz/Pa conversion. Its rendered page confirms this is not a text-extraction
artifact. With the normalized complex SDV returned by historical HAPI,
Re(F) and Im(F) both have units cm, requiring a dimensionless mixing multiplier.
The previously added `p*Y_table` combination has no demonstrated reconciliation
of that label. The frozen HAPI contains y_air/y_self metadata, not an executable
LM profile combination. No modern HAPI formula is substituted.

Additionally, the frozen XML Eq. 10 writes the logarithm as
`ln[1+(x+v)/(y*(1+S*(v^2-3/2))+H)]`, without a square. As written it need not
be real over the integration domain. The author prose suffices to identify
dispersion, but silently repairing this expression would exceed the request.
The branch's earlier algebra tests verify an implementation identity, not this
historical normalization. Neither a positive cross section nor area/parity
limits distinguish all possible normalization factors.

**SOURCE CONVENTION BLOCKER.** Nominal LM-enabled rate transfer raises before
spectral integration. The earlier low-level algebra remains explicitly a
candidate diagnostic. Retrieve a historical executable LBL convention or an
unambiguous author/publisher equation and establish how Table-22 numerical Y
combines with normalized F/F-prime. Then verify source-node numerical cases
and total-band conservation/physical opacity without empirical fitting.

## Table-22 high-temperature domain

The selected policy deliberately fails above 340 K. At 0.125-km spacing, the
accepted 0--150-km atmosphere has 248 shells above that limit, starting at the
119.0-km lower edge; maximum shell temperature is 741.757396697998 K.
All 248 are active on the illuminated 50-km vertical ray, so this cannot be
excused as a target-temperature issue or unused geometry.

**DESIGN BLOCKER.** Resolve an historically supported high-T prescription or
establish and explicitly approve a converged materiality bound. No clamp to
340 K, opacity deletion or nominal LM-off fallback is introduced. The code can
evaluate LM-off principal transfer as a labelled diagnostic; it is not gA.

## Rare-isotopologue Galatry convention

The byte-verified historical auxiliary and existing validator map 140 iso-2
and 140 iso-3 lines, with air/self Dicke fields, to accepted HITRAN2016 quantum
identities. This is a data coverage PASS, not a profile-semantics PASS.
HAPI 1.1.0.8.2 at the frozen SHA provides Galatry parameter metadata and lists,
but AST inspection finds zero Galatry evaluator functions. Its pCqSDHC/HTP
velocity-changing term is hard collision and cannot serve as Galatry.

**SOURCE CONVENTION BLOCKER.** The frozen evidence does not establish the full
exact beta-to-profile frequency convention and temperature law. Do not borrow
the ordinary n_air exponent, assume no beta temperature dependence, infer a
2*pi conversion, or combine the air/self coefficients by analogy. Recover the
historical Long/Galatry executable definition, reference-temperature units,
beta(T,p) rule and air/self convention before coding the rare evaluator.
Ordinary target-edition fields retain precedence; auxiliary redundant widths,
shifts, positions and intensities are never substituted.

## Verified scope and intentionally unexecuted work

The new isolated module validates principal 91/70/21/59 population identities,
evaluates SDV and classic q contributions, and provides exact all-selected-line
shell and target transfer as an explicit LM-off principal diagnostic. Low-T Y
policies and no-Y/q omission populations are separable; omission bounds a
population contribution rather than inventing a nonzero high-J Y.

Tests cover independent Gaussian/Voigt/Maxwell limits, SDV area, candidate mixed
pair area, Table-22 interpolation, negative summed opacity rejection, order
invariance, zero column, shadow, spectral refinement and scientific gate errors.
The source audit compares all 91 SDV lines at 12 T/p states against the actual
default CPF in pinned HAPI using math-only AST extraction. Single-node calls
avoid the historical routine's mixed PART2/PART4 vector-mask indexing bug;
its equations and CPF are unchanged. Only the reviewed math functions execute,
not HAPI module initialization, downloads or database code.

The 430-line gA, full-domain A convergence and retained low-T/no-Y/q sensitivities
are NOT RUN. Galatry normalization, area, zero-beta and strong-narrowing limits
are NOT RUN because no authorized Galatry evaluator exists. These blockers
prevent proceeding to B corrected qSDV or M5 in this task. A code/test PASS does
not close any of these scientific gates.

See `evidence/m4d_a_advanced_transfer.json` for reproducible numeric scope, code
fingerprints and blocker exceptions, and `m4d_a_advanced_transfer_execution.md`
for the implementation contract. Historical restricted source records remain
outside Git and unchanged.
