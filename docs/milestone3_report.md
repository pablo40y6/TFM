# Milestone 3 delivery evidence

Date: 2026-09-10

Baseline: `tfm-photochem-milestone2-r2.zip`, SHA256
`ffb179c9f2c7fdb71ad5af8990490ae0040cf729f7209e1ae90a25fa0021f47f`.
The baseline was extracted into a separate M3 project and was not overwritten.

## Delivered scope and version

Package version: `0.3.0`.

`historical_2020` now implements one scalar local closure:

```text
LocalState + LocalBackground + LocalForcing
    -> six QSSA species
    -> 54 reaction/event fluxes and diagnostics
    -> 49 coefficient/contribution rows
    -> tendencies for O, O3, H, R_H, and dynamic Delta
```

The public result also exposes six residuals and production/loss diagnostics.
The complete equations, flux map, branching rules, and coefficient table are
in `docs/historical_2020_local_closure.md`.

## Exact file delta from M2-R2

Modified:

- `README.md`
- `docs/architecture.md`
- `docs/historical_2020_reactions.md`
- `docs/historical_2020_topology.md`
- `docs/validation_report.md`
- `pyproject.toml`
- `src/tfm_photochem/__init__.py`
- `src/tfm_photochem/historical_2020/__init__.py`
- `src/tfm_photochem/historical_2020/config.py`
- `tests/test_historical_2020_registry.py`
- `uv.lock`

Added:

- `docs/historical_2020_local_closure.md`
- `docs/milestone3_report.md`
- `scripts/validate_local_closure.py`
- `src/tfm_photochem/historical_2020/fluxes.py`
- `src/tfm_photochem/historical_2020/local_closure.py`
- `src/tfm_photochem/historical_2020/local_types.py`
- `src/tfm_photochem/historical_2020/qssa.py`
- `src/tfm_photochem/historical_2020/stoichiometry.py`
- `tests/test_historical_2020_local_closure.py`
- `tests/test_historical_2020_qssa.py`

Removed: none.

The accepted M2-R2 `kinetics.py`, `reactions.py`, and coefficient tests remain
byte-identical. The M2 registry boundary test is changed only to permit the
now-authorized scalar QSSA modules while continuing to forbid M4+ modules.

## Scientific implementation

The six relations are:

1. `O1D = P_O1D/L_O1D`, with the O1D+O2 total loss counted once.
2. `HO2 = R_H-OH`.
3. `H2O2 = k_HO2_HO2 HO2^2/(J_H2O2+k_OH_H2O2 OH)`.
4. One `dOH/dt=0` equation solved for `OH/R_H` on `[0,1]` with a
   257-point ambiguity scan and Brent's method.
5. `B1 = P_B1/L_B1`, including gB and the 0.8 O1D+O2 branch.
6. `B0 = P_B0/L_B0`, including gA, the 0.2 branch, B1 O2/N2 cascade,
   and effective Barth source.

H2O2 zero-production/zero-loss uses its explicit zero limit. Positive
production with zero loss raises. `R_H=0` uses the documented dynamic boundary
condition, and no clipping is applied.

The Barth metadata states exactly:

```text
M3 baseline model assumption: effective Barth source -> B0
```

It uses `r=k O^2 M` and
`P_B0=r O2/(6.6 O2+19 O)`. The O tendency receives `-2r`. No elementary
coefficient is invented for the two pending effective steps.

Hartley gross parent loss remains `JH O3`; only O1D/Delta production is scaled
by 0.9. Lyman-alpha represented O/O1D production is `0.44 J_LYA O2`. Both
untracked complements are diagnostic only. O1D+O2 branches sum to the single
total event flux.

`R_H` coefficients are derived as `nu_OH+nu_HO2` from the registry. The five
totals are sums of returned per-event contributions, and an independent test
reconstructs all five frozen aggregate equations.

Delta is not a QSSA species:

```text
dDelta/dt = P_Delta - L_Delta * supplied_Delta
```

Changing only supplied Delta leaves `P_Delta` and `L_Delta` unchanged and
changes its tendency by exactly `-L_Delta*change(Delta)`.

## Tests and reproducibility

| Check | Result |
| --- | --- |
| pytest | `342 passed, 13 subtests passed` |
| Ruff 0.16.6 | `All checks passed!` |
| bytecode | `python -m compileall -q src tests scripts`, exit 0, no output |
| lock | `uv lock --check --offline` -> `Resolved 17 packages`, exit 0 |
| build | wheel and sdist 0.3.0 built successfully |
| clean wheel | fresh Python 3.12 environment outside source; version/API/counts/sigma verified |
| extracted sdist | fresh Python 3.12 environment; `342 passed, 13 subtests passed` |

Test coverage includes direct independent formula calculations, forcing-off,
branch closure, product-yield semantics, self-reaction event conventions,
OH/HO2 physical bounds, zero and singular H2O2 limits, absent/multiple root
errors, B1/B0 cascade rules, Barth, exact R_H stoichiometry, Delta dynamics,
both O3 topology decisions, input validation, traceability, single-reaction
switches, and independent reconstruction of all five total tendencies.

## Deterministic local closure regression

`PYTHONPATH=src python scripts/validate_local_closure.py` exits 0. Key output:

```json
{
  "algebraic": {
    "B0": 2585610.3112498927,
    "B1": 4753.180874470538,
    "H2O2": 11823828.223648872,
    "HO2": 17593365.263392903,
    "O1D": 2081.4997087301526,
    "OH": 32406634.736607097
  },
  "flux_count": 54,
  "contribution_row_count": 49,
  "residuals": {
    "res_B0": 0.0,
    "res_B1": 0.0,
    "res_H2O2": 0.0,
    "res_O1D": -2.3283064365386963e-10,
    "res_OH": -5.960464477539063e-08,
    "res_family": 0.0
  },
  "tendencies": {
    "Delta": 1572007.5893378519,
    "H": 286865029.8228769,
    "O": -572329026.0011083,
    "O3": -1639155.1637750806,
    "R_H": -287067141.6564752
  }
}
```

For this case, `P_Delta=1599102.631728437` and
`L_Delta=0.0002709504239058501 s^-1`. The nonzero raw OH/O1D residuals are
roundoff at relative levels below the documented `2e-13` acceptance threshold.

## Accepted legacy regression

`PYTHONPATH=src python scripts/validate_legacy.py` exits 0 and returns:

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

All six `legacy_2017` production files and both legacy assets are byte-identical
to M2-R2/M1-R2. The frozen `sigma.mat` SHA256 remains
`a98567c4f971721cec4197ad7ea17182e95df78c3a0eea880acb08fc6d560424`.

## Blockers, sources, and stop condition

No scientific ambiguity blocks M3. Inputs deliberately injected here remain
real M4 work: historical H2O/H2O2 photolysis data, historical HITRAN inputs,
prescribed H2O/H2 profiles, and a reproducible MSIS-compatible background.
JPL Evaluation 20 / 2025 supplies no numerical value.

No radiation calculation, background builder, altitude array, 51-level/255
state assembly, column RHS, temporal solver, `solve_ivp`, BDF, Radau, diurnal
cycle, spin-up, periodic convergence, transport, retrieval, or
`updated_2025` was added. Milestone 4 has not started.

## Roadmap review proposal after M3

The M4-M8 order remains scientifically coherent. Before authorizing M4, review
whether its broad scope should be split into M4A (background/profile datasets
and provenance) and M4B (historical radiation/photolysis and solar geometry).
Then retain M5 integration, M6 periodic cycle, M7 scientific validation, and
M8 retrieval/application. This is a proposal only; no M4 work is included.
