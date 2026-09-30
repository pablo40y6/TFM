"""Exact historical Mate blocks with explicit HITRAN2016 O2-Air correction."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .sources import SourceError, verified_bytes

BLOCK_IDENTITIES = {
    253: (4194, "58366c46162ca55c84aecd8b81bdadc1f5a68a27db0fbbd615a401dcc21f0bfc"),
    273: (4029, "09a1e93c23004c0b12acf3e9b97fcb44f4bd32872e7ad1c6441225f0ab56b545"),
    296: (4237, "19bd3c333c56dc9dd90019b57d014a69db420cae139a33a1c470557b1ad78e08"),
}


@dataclass(frozen=True)
class HistoricalCIA:
    spectra: dict[int, np.ndarray]

    def at_nodes(self, nodes, clip_source_nodes: bool = True) -> np.ndarray:
        out = []
        for temperature in (253, 273, 296):
            table = self.spectra[temperature]
            if np.any(nodes < table[0, 0]) or np.any(nodes > table[-1, 0]):
                raise ValueError(
                    "CIA spectral support exceeded; no silent extrapolation"
                )
            values = np.maximum(table[:, 1], 0) if clip_source_nodes else table[:, 1]
            out.append(np.interp(nodes, table[:, 0], values))
        return np.array(out)


def temperature_weights(temperatures: np.ndarray) -> np.ndarray:
    temperatures = np.asarray(temperatures)
    t = np.clip(temperatures, 253, 296)
    out = np.zeros((len(t), 3))
    low = t <= 273
    f = (t[low] - 253) / 20
    out[low, 0], out[low, 1] = 1 - f, f
    f = (t[~low] - 273) / 23
    out[~low, 1], out[~low, 2] = 1 - f, f
    return out


def load_cia(path: str | Path) -> HistoricalCIA:
    raw = verified_bytes(path, "O2-O2_2011.cia")
    lines = raw.splitlines(keepends=True)
    result = {}
    i = 0
    while i < len(lines):
        fields = lines[i].decode("ascii").split()
        if len(fields) < 5:
            raise SourceError("malformed CIA block header")
        count, t = int(fields[3]), float(fields[4])
        if 7400 < float(fields[1]) < 7600 and t in BLOCK_IDENTITIES:
            expected_count, digest = BLOCK_IDENTITIES[int(t)]
            block = b"".join(lines[i : i + count + 1])
            if count != expected_count or hashlib.sha256(block).hexdigest() != digest:
                raise SourceError("historical Mate block mismatch")
            if t in result:
                raise SourceError("duplicate historical Mate block")
            array = np.array(
                [
                    [float(x) for x in row.split()]
                    for row in lines[i + 1 : i + count + 1]
                ]
            )
            if np.any(np.diff(array[:, 0]) <= 0) or not np.all(np.isfinite(array)):
                raise SourceError("invalid historical CIA spectral grid")
            result[int(t)] = array
        i += count + 1
    if set(result) != set(BLOCK_IDENTITIES):
        raise SourceError("historical Mate temperature coverage incomplete")
    return HistoricalCIA(result)
