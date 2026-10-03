# TFM photochemistry model

A reproducible temporal model of mesospheric ozone (O3) and excited molecular
oxygen O2(a1Delta), developed for the master's thesis (TFM).

## Accepted temporal model

The chemistry grid has 51 heights from **50 to 100 km**, at 1 km spacing.
Seven species evolve dynamically: **O, O3, H, OH, HO2, H2O2 and Delta**
(357 ODEs). `R_H = OH + HO2` is diagnostic; only O1D, B0 and B1 use QSSA.
M4C UV responds to chemical O/O3, and accepted M4D A0/B/IRA excitation
includes historical O2-Air CIA attenuation. UTC date, latitude and
east-positive longitude determine solar geometry and height-dependent shadow.
BDF is the main solver; Radau provides independent numerical validation.

M1-R2, M2-R2, M3, M4A, M4B-R2, M4C-R2, M4D for temporal use, and M5A/M5B/M5C
are accepted. The current references are [PROJECT_STATE.md](PROJECT_STATE.md)
and the single [technical report](docs/m5_temporal_report.md).
Earlier investigations are indexed in [docs/archive](docs/archive/README.md).

## Install and run

Use Python 3.10 or later from the repository root:

```bash
python -m pip install -e ".[dev,background-gen]"
```

A dynamic atmosphere uses pinned `pymsis==0.12.0` (MSIS-00), prescribed reference
VMRs, and quiet activity `F107/F107a/Ap = 150/150/4` or explicit activity drivers.
It never downloads space weather. Dynamic NIR requires the authorized local
historical source bundle and HITRAN2016 export, or an explicitly precomputed
`DynamicNIRForcing`. Raw HITRAN is not distributed in this repository.

```python
from datetime import datetime, timezone
from pathlib import Path
from tfm_photochem.dynamic_radiation import HistoricalNIRInputs
from tfm_photochem.m5_simulation import simulate

start_datetime = datetime(2020, 3, 20, 20, tzinfo=timezone.utc)
end_datetime = datetime(2020, 3, 21, 9, tzinfo=timezone.utc)
latitude, longitude = 45.0, 0.0
inputs = HistoricalNIRInputs(
    Path("/path/to/verified/historical-sources"),
    Path("/path/to/authorized-hitran2016.txt"),
)
result = simulate(
    start_datetime, end_datetime, latitude, longitude,
    atmosphere="dynamic_msis", initialization="reference_noon",
    radiation_inputs=inputs, cache=Path(".m5-derived-cache"),
)
result.save("trajectory.npz")
```

`reference_noon` is an approximate bootstrap from the preceding apparent solar
noon. To bypass it, omit `initialization` and supply `initial_state=state`, a
finite, nonnegative `(51, 7)` array in cm^-3, in the species order above:

```python
result = simulate(
    start_datetime, end_datetime, latitude, longitude,
    initial_state=state, atmosphere="dynamic_msis",
    radiation_inputs=inputs, cache=Path(".m5-derived-cache"),
)
```

For a self-contained frozen-atmosphere example using the accepted golden noon
state and packaged NIR table (no external spectroscopy files required):

```python
import numpy as np

with np.load("evidence/m5b_reference_real_geometry.npz", allow_pickle=False) as data:
    state = data["state_cm3"][0].copy()
result = simulate(
    datetime(2020, 3, 20, 12, tzinfo=timezone.utc), end_datetime, 45.0, 0.0,
    initial_state=state, atmosphere="frozen_reference",
)
result.save("trajectory.npz")
```

This last example explicitly injects a reference state; it does not establish
chemical equilibrium at actual astronomical noon. `frozen_reference` retains
the M4A reference atmosphere even if the geometry date/location changes.
Saved NPZ outputs include time, height, SZA, species, QSSA fields, forcings and
solver/atmosphere/initialization metadata; dynamic runs also retain backgrounds.

## Validate

```bash
python -m pytest
python -m ruff check src tests scripts
python scripts/validate_legacy.py
python scripts/validate_local_closure.py
python scripts/validate_odd_oxygen_photolysis_budget.py
python scripts/validate_historical_2020_background.py
python scripts/validate_historical_2020_uv.py
```

Run M5 validators as modules from the repository root (for example,
`python -m scripts.validate_m5b_temporal --mode assess --cache /local/cache`).
M4D mapping and M5A/M5B/M5C certification commands, verified source identities,
and cache requirements are documented in the [technical report](docs/m5_temporal_report.md).
Accepted reference trajectories are `evidence/m5_reference_cycle.npz`,
`evidence/m5b_reference_real_geometry.npz` and
`evidence/m5c_reference_dynamic_msis.npz`. Numerical certification uses 300-s
background and 3600-s NIR grids, with output convergence below approximately
0.5%. These goldens are evidence, not universal initial conditions.

## Scientific limits and next phase

There is no transport or validated climatological initialization. This is a
finite-horizon model; a periodic attractor is not certified. Exterior O3 and
H2O/H2 VMR profiles are prescribed references. Large frozen/dynamic differences
are atmospheric sensitivities, not solver error. Advanced LM/Galatry remains
optional historical spectroscopy work and is not required by the accepted
A0/B/IRA temporal baseline. The M4C-R2 immutable ZIP and earlier accepted
scientific assets remain preserved.

The next phase is final scientific results, figures and thesis writing.
Repository consolidation introduces no new scientific model or milestone.
