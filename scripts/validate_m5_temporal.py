"""Reproduce the SZA=99 initialization blocker with direct accepted forcing.

Exit 2 means the scientific initialization gate failed, not a regression failure.
Only shadowed cases are needed: two exact roots disprove full-domain uniqueness.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

from tfm_photochem.historical_2020.background import load_baseline_background
from tfm_photochem.historical_2020.local_closure import close_local_chemistry
from tfm_photochem.historical_2020.uv_radiation import (
    compute_uv_photolysis,
    local_forcing_from_uv,
)
from tfm_photochem.m4d_reconstruction.cia import load_cia
from tfm_photochem.m4d_reconstruction.sources import load_bands, load_solar, load_tips
from tfm_photochem.m4d_reconstruction.spectroscopy import SpectralSources
from tfm_photochem.m4d_reconstruction.transfer import compute_classic_rates
from tfm_photochem.m5_temporal import (
    InitializationBlocker,
    local_rhs,
    reject_nonunique_dark_equilibrium,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--hitran", type=Path, required=True)
    args = parser.parse_args()
    background = load_baseline_background()
    oxygen = background.radiative.msis_O_native_cm3[50:101]
    # This is exactly the accepted unavailable-O boundary convention, a seed
    # for UV opacity only. It does not select an initial dynamic concentration.
    oxygen_seed = np.where(np.isfinite(oxygen), oxygen, 0.0)
    ozone_seed = background.radiative.O3_socrates_reference_cm3[50:101]
    uv = compute_uv_photolysis(oxygen_seed, ozone_seed, 99, background=background)
    indices = np.flatnonzero(~uv.illuminated)
    cases = [(float(background.z_chem_km[i]), 99.0) for i in indices]
    bands = load_bands(args.hitran)
    sources = SpectralSources(
        *load_tips(args.sources / "hapi.py"), load_solar(args.sources / "wehrli85.txt")
    )
    cia = load_cia(args.sources / "O2-O2_2011.cia")
    rates = {
        "gA": compute_classic_rates(bands["A"], sources, cases)["monomer"],
        "gB": compute_classic_rates(bands["B"], sources, cases)["monomer"],
        "gIRA": compute_classic_rates(bands["IRA"], sources, cases, cia=cia)["cia_nominal"],
    }
    evidence = []
    for row, i in enumerate(indices):
        altitude = float(background.z_chem_km[i])
        local_background = background.local_background_at(altitude)
        forcing = local_forcing_from_uv(
            uv, int(i), **{name: float(value[row]) for name, value in rates.items()}
        )
        assert all(value == 0 for value in asdict(forcing).values())
        try:
            reject_nonunique_dark_equilibrium(local_background, forcing, ozone_seed[i])
        except InitializationBlocker as error:
            records = []
            for witness in error.witnesses:
                initial = np.array(list(asdict(witness).values()))
                closure = close_local_chemistry(witness, local_background, forcing)
                solution = solve_ivp(
                    lambda t, y: local_rhs(t, y, background=local_background, forcing=forcing),
                    (0, 86400), initial, method="BDF", rtol=1e-9, atol=1e-8,
                    max_step=3600, jac=np.zeros((5, 5)),
                )
                # Iteration Jacobian only, for exact constant boundary roots.
                # Finite-difference QSSA trials need not be physically admissible;
                # neither this check nor its Jacobian establishes attraction.
                if not solution.success:
                    raise RuntimeError(solution.message)
                departure = float(np.max(np.abs(solution.y - initial[:, None])))
                assert departure == 0.0
                assert np.all(np.isfinite(solution.y)) and np.all(solution.y >= 0)
                records.append({
                    "state_cm3": asdict(witness),
                    "five_tendencies_cm3_s1": asdict(closure.tendencies),
                    "six_QSSA_residuals": asdict(closure.residuals),
                    "BDF_86400s_max_absolute_departure_cm3": departure,
                })
            evidence.append({"altitude_km": altitude, "forcing_s1": asdict(forcing), "roots": records})
        else:
            raise AssertionError("expected nonunique dark equilibrium")
    print(json.dumps({
        "decision": "INITIALIZATION BLOCKER / NO-GO M5A",
        "policy": "reference_twilight_equilibrium",
        "SZA_deg": 99,
        "direct_forcing": "accepted M4C plus M4D A0/B/IRA with CIA attenuation",
        "nonunique_heights_km": [case[0] for case in cases],
        "equilibrium_family": "[0,c,0,0,0], c>=0",
        "seed_O3_factors": [0.1, 10.0],
        "BDF_persistence_interval_s": 86400,
        "unique_attractor": False,
        "attraction_verification": "fails: distinct O3 perturbations remain at distinct exact roots",
        "witnesses": evidence,
    }, indent=2, allow_nan=False))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
