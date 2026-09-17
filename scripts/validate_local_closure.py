"""Emit a deterministic Milestone-4B single-level closure regression."""

from __future__ import annotations

import json
from dataclasses import asdict

from tfm_photochem.historical_2020 import (
    LocalBackground,
    LocalForcing,
    LocalState,
    close_local_chemistry,
)


def main() -> None:
    state = LocalState(O=2e11, O3=2e8, H=2e7, R_H=5e7, Delta=1e8)
    background = LocalBackground(
        T=200.0,
        M=2e13,
        O2=4e12,
        N2=1.5e13,
        CO2=8e9,
        H2O=2e7,
        H2=1e8,
    )
    forcing = LocalForcing(
        JH=8e-3,
        J_SRC=2e-8,
        J_LYA=3e-9,
        J_O2_TOTAL=2.3e-8,
        J_O3_TOTAL=8e-3,
        J_H2O2=2e-5,
        J_H2O_A=2e-8,
        J_H2O_B=1e-9,
        gA=1e-9,
        gB=2e-10,
        gIRA=3e-9,
    )
    result = close_local_chemistry(state, background, forcing)
    payload = {
        "configuration": "historical_2020",
        "scope": "single-level local closure; no time integration",
        "state": asdict(state),
        "background": asdict(background),
        "forcing": asdict(forcing),
        "algebraic": asdict(result.algebraic),
        "residuals": asdict(result.residuals),
        "tendencies": asdict(result.tendencies),
        "diagnostics": asdict(result.diagnostics),
        "flux_count": len(result.fluxes),
        "contribution_row_count": len(result.contributions),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
