# Milestone 2 R2 delivery evidence

Date: 2026-09-09

## Audit ledger

| Artifact | SHA256 | Status |
| --- | --- | --- |
| `tfm-photochem-milestone1-r2.zip` | `46c88ec344de1569d06dff76c36c991edb19777497146ff5183756b54cba6f3d` | accepted / closed |
| `tfm-photochem-milestone2(1).zip` | `531900f689a219ed3618b0c0eb4a4e5164ea00b388f0a79ca659410515aeb4dc` | provisional / retained |
| `tfm-photochem-milestone2-r2.zip` | reported with the external artifact | pending independent audit |

The provisional M2 archive was not overwritten.

## R2 correction scope

Only the independently requested M2 corrections were made. The registry still
contains 50 processes, 38 distinct executable rate laws, 39 processes linked
to a coefficient, 11 `PENDING INPUT` processes, and six scalar parameters.

### Scientific coefficient diff

| Rate law | Provisional M2 | M2-R2 | Source/unit | Temperature direction |
| --- | --- | --- | --- | --- |
| `k_b0_n2` | `2.1e-15` | `1.8e-15*exp(+45/T)` | JPL18 A86; cm3 molecule-1 s-1 | decreases as T increases |
| `k_b0_o3` | `2.2e-11` | `3.5e-11*exp(-135/T)` | JPL18 A82 total loss; cm3 molecule-1 s-1 | increases as T increases |

`B0 + O3 -> Delta + O3` remains Li's simplified routing. The JPL18 A82
coefficient is total B0 loss; applying it to that routing is explicitly a Li
model assumption and not a claim of 100-percent JPL branching. No 70/30 or
other branching was introduced.

### Li/JPL discrepancy decisions

| Item | Li 2020 printing | Historical evidence | M2-R2 decision |
| --- | --- | --- | --- |
| O1D + N2 | `exp(-110/T)` | JPL18 A7: `exp(+110/T)` | retain JPL18 sign |
| O1D + O2 | `exp(-55/T)` | JPL18 A3: `exp(+55/T)` | retain JPL18 sign and Li 0.8/0.2 routing |
| Delta + O3 | `Delta + O3 -> O2 + O3`; `5.2e-11*exp(+2840/T)` | JPL18 A75: `Delta + O3 -> O + 2 O2`; `5.2e-11*exp(-2840/T)` | JPL18 topology and law; future tendency is `-O3`, `+O` |
| B0 + N2 | constant `2.1e-15` | JPL18 A86: `1.8e-15*exp(+45/T)` | full JPL18 law; Li product routing |
| B0 + O3 | constant `2.2e-11`; simplified Delta routing | JPL18 A82: total `3.5e-11*exp(-135/T)` with branching | full JPL18 total coefficient plus explicit Li routing assumption; no new branching |
| Barth | `4.7e-33*exp(300/T)` | Brasseur and Solomon Table 4.5 and Anqi 2017 executable listing: `(300/T)^2` | retain historical power law |

The `DELTA_O3` registry test freezes reactants `Delta + O3`, products
`O + 2 O2`, and modified species `Delta`, `O3`, and `O`.

## Frozen reduced topology and yield semantics

`docs/historical_2020_topology.md` is the exhaustive inclusion/exclusion
manifest. It explicitly excludes `O + H2`, `O + H2O2`, `OH + OH + M`, and the
H2O enhancement of `HO2 + HO2`; none was added. It records each included HOx
process with source, decision reason, and future dynamic/QSSA role.

The registered 0.9 Hartley and 0.44 Lyman-alpha factors are now documented and
tested as product-channel yields. They must not scale total reactant
photolysis loss in a future assembly.

## Exact file delta from provisional M2

Modified:

- `README.md`
- `docs/architecture.md`
- `docs/historical_2020_reactions.md`
- `docs/milestone2_report.md`
- `docs/validation_report.md`
- `src/tfm_photochem/historical_2020/kinetics.py`
- `src/tfm_photochem/historical_2020/reactions.py`
- `tests/test_historical_2020_kinetics.py`
- `tests/test_historical_2020_registry.py`

Added:

- `docs/historical_2020_topology.md`

No other project file differs from provisional M2. No M1 production, test,
script, or asset file changed.

## Test and quality evidence

| Check | Exact result |
| --- | --- |
| Tests | `uv run --extra dev pytest -q` -> `242 passed, 13 subtests passed in 0.34s` |
| Ruff | Ruff 0.16.6, `ruff check src tests scripts` -> `All checks passed!` |
| Bytecode | `python -m compileall -q src tests scripts` -> exit 0, no output |
| Lock | `uv lock --check --offline` -> exit 0 |
| Build | `uv build --clear` -> wheel and sdist 0.2.0 built |
| Clean wheel | fresh Python 3.12 environment outside source tree; import/version, 38 laws, 50 reactions, both corrected B0 values, and packaged sigma hash verified |
| Extracted sdist | fresh Python 3.12 environment; `242 passed, 13 subtests passed` |

The final ZIP is additionally extracted into a clean directory and subjected
to pytest, Ruff, lock, bytecode, and legacy validation before delivery.

## Exact legacy validator output

`PYTHONPATH=src python scripts/validate_legacy.py` exited 0:

```json
{
  "configuration": "legacy_2017",
  "sigma_sha256": "a98567c4f971721cec4197ad7ea17182e95df78c3a0eea880acb08fc6d560424",
  "sza_deg": 60.0,
  "altitude_km": [50.0, 80.0, 100.0, 150.0],
  "j_hart_s-1": [0.007901060075276741, 0.007943298912613521, 0.007950799890467177, 0.007951370570121479],
  "j_src_s-1": [1.4729438260421979e-307, 9.562150252425894e-15, 2.6712220862792933e-08, 3.636571535539284e-06],
  "j_lya_s-1": [3.83873300714473e-36, 1.6186877815710608e-09, 3.6361272783339067e-09, 3.819962471375554e-09],
  "j_o3_total_s-1": [0.008011935688633766, 0.008058062381488302, 0.008070366753215189, 0.008073629856095872],
  "j_o2_total_s-1": [5.10968259712899e-10, 2.1429561639980833e-09, 3.099237774818972e-08, 4.460643082713598e-06],
  "mkozone_cm-3": [575602196091.73, 8325166168.343959, 52693522.02762813, 0.003597832916437647]
}
```

Every regular file below `src/tfm_photochem/legacy_2017/` and
`src/tfm_photochem/assets/legacy_2017/` is byte-identical to M1-R2. The frozen
`sigma.mat` SHA256 is
`a98567c4f971721cec4197ad7ea17182e95df78c3a0eea880acb08fc6d560424`.

## Sources and exclusions

All corrected coefficients use JPL Publication 15-10 / Evaluation 18 (2015).
JPL Evaluation 20 / 2025 was not used to select or change any numerical value.
The remaining historical H2O/H2O2, HITRAN, profile, and MSIS inputs stay
explicitly pending; no values were invented or substituted.

## Stop-condition confirmation

No QSSA, RHS, 255-ODE system, stoichiometric tendency assembly, BDF/Radau,
dynamic Delta integration, final radiation/HITRAN, MSIS, H2O/H2 profiles,
diurnal cycle, periodic convergence, spin-up, retrieval, transport,
`li2020_table_literal`, or `updated_2025` implementation was added. Milestone 3
has not started.
