"""Fail-closed historical source verification and semantic transition parsing."""

from __future__ import annotations

import ast
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

SOURCE_IDENTITIES = {
    "guest1593878592.txt": (
        2268239,
        "6b4acbc01cb649891f2d8597875c9cd8e4805cfdd4d3b7841c2d18cbf718de12",
    ),
    "PMC5103325.xml": (
        310708,
        "935fd09d5f619f7eb3f7fac5347e80fa81bc23d3158dc9c519874bb161c364fe",
    ),
    "1-s2.0-S0022407316301108-mmc1.pdf": (
        89406,
        "12e621d3b5d17e7648d140ea16134e3c04096bd7e47e2c1bb0e2084adeccbb51",
    ),
    "07_A-band_SDF.dat": (
        6229,
        "7cfefb8040a89cb0e4948c2811a6766b793181646d8188ebfa4d646e063dbd26",
    ),
    "07_hit12_0.76mic_Galatry.par": (
        47231,
        "69c9fd181b5aba8aa818dc906bdc216aaa8cf038eb5687dd4da8f2bb9bf42dab",
    ),
    "O2-O2_2011.cia": (
        1938473,
        "8cc3ecc87bf7a02492b385ecc71abf279b058da853aea768825deb81237d5ee3",
    ),
    "hapi.py": (
        1204196,
        "81d9d2f4fc6dd80021d329280810008e0385109d8c5295f41615f51d405b0964",
    ),
    "wehrli85.txt": (
        28555,
        "daad62d53f188d8c48bfb60e4b78afd22c74ffc49180e2ac249c6d95b8f96d43",
    ),
}
BAND_IDENTITIES = {
    "A": (430, "176a6c21ee37b1244bd11ef7047f6e31f7cada7edff2c3498f31f8d1f2e92eea"),
    "B": (320, "bb5f8b26a2ad3c9dc31870506c3c05bcdb115b7c5b06d7141c9660c952d83c2d"),
    "IRA": (835, "8d06f322aa4058ab03150a705bf9765fe356a2c7ecd06df98379c46062d295ad"),
}


class SourceError(ValueError):
    """A historical source or transition identity failed verification."""


def verified_bytes(path: str | Path, identity: str) -> bytes:
    data = Path(path).read_bytes()
    size, digest = SOURCE_IDENTITIES[identity]
    if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
        raise SourceError(f"SOURCE MATERIALIZATION BLOCKER: {identity} byte identity")
    return data


def normalize_quantum(text: str) -> str:
    return " ".join(text.split())


@dataclass(frozen=True)
class Line:
    isotope: int
    nu: float
    sw: float
    gamma_air: float
    gamma_self: float
    elower: float
    n_air: float
    delta_air: float
    upper: str
    lower: str
    local_upper: str
    local_lower: str
    record: str

    @property
    def key(self) -> tuple:
        return (
            7,
            self.isotope,
            self.upper,
            self.lower,
            self.local_upper,
            self.local_lower,
        )

    @property
    def flag(self) -> str:
        return self.record[126]

    @property
    def dipole_label(self) -> str:
        # Both branch identifiers and both N/J numbers, including the d flag.
        match = re.fullmatch(r"([PR])\s*(\d+)([PQR])\s*(\d+)\s*d", self.local_lower)
        if not match:
            raise SourceError(f"invalid magnetic-dipole quantum identifier: {self.key}")
        return "".join(match.groups())


def parse_line(record: str) -> Line:
    if len(record) != 160 or record[:2].strip() != "7":
        raise SourceError("not an O2 160-character HITRAN record")
    line = Line(
        int(record[2]),
        float(record[3:15]),
        float(record[15:25]),
        float(record[35:40]),
        float(record[40:45]),
        float(record[45:55]),
        float(record[55:59]),
        float(record[59:67]),
        *(
            normalize_quantum(record[a:b])
            for a, b in ((67, 82), (82, 97), (97, 112), (112, 127))
        ),
        record,
    )
    if line.isotope not in (1, 2, 3):
        raise SourceError("unexpected O2 isotope")
    values = [
        line.nu,
        line.sw,
        line.gamma_air,
        line.gamma_self,
        line.elower,
        line.n_air,
        line.delta_air,
    ]
    if not np.all(np.isfinite(values)) or min(values[:6]) < 0:
        raise SourceError("invalid numerical line fields")
    return line


def load_bands(path: str | Path) -> dict[str, tuple[Line, ...]]:
    text = verified_bytes(path, "guest1593878592.txt").decode("ascii")
    # The source has exactly thirteen header lines. Do not skip malformed rows.
    records = text.splitlines()[13:]
    if len(records) != 14085:
        raise SourceError("unexpected SpectralCalc record count")
    lines = tuple(parse_line(record) for record in records)
    selectors = {"A": "b 0", "B": "b 1", "IRA": "a 0"}
    out = {}
    for band, upper in selectors.items():
        subset = tuple(
            line for line in lines if line.upper == upper and line.lower == "X 0"
        )
        count, digest = BAND_IDENTITIES[band]
        canonical = "".join(line.record + "\n" for line in subset).encode("ascii")
        if len(subset) != count or hashlib.sha256(canonical).hexdigest() != digest:
            raise SourceError(f"{band} canonical subset mismatch")
        if len({line.key for line in subset}) != count:
            raise SourceError(f"{band} duplicate quantum identity")
        # Canonical hashes use source order; arithmetic uses a stable identity sort.
        out[band] = tuple(sorted(subset, key=lambda line: line.key))
    return out


def load_tips(path: str | Path) -> tuple[np.ndarray, dict[int, np.ndarray]]:
    """Extract only literal lists from pinned code; never execute downloaded HAPI."""
    text = verified_bytes(path, "hapi.py").decode("utf-8")
    grid = re.search(r"TIPS_2017_ISOT\[5\] = float64\((\[.*?\])\)", text, re.S)
    if grid is None:
        raise SourceError("TIPS temperature grid missing")
    temperatures = np.array(ast.literal_eval(grid[1]), dtype=float)
    tables = {}
    for isotope in (1, 2, 3):
        match = re.search(
            rf"#\s*-+ M = 7, I = {isotope} -+.*?"
            r"TIPS_2017_ISOQ_HASH\[\(M,I\)\] = float64\((\[.*?\])\)",
            text,
            re.S,
        )
        if match is None:
            raise SourceError(f"TIPS isotope {isotope} missing")
        tables[isotope] = np.array(ast.literal_eval(match[1]), dtype=float)
        if len(tables[isotope]) != len(temperatures):
            raise SourceError("TIPS table/grid lengths disagree")
    return temperatures, tables


def load_solar(path: str | Path) -> np.ndarray:
    from io import BytesIO

    table = np.loadtxt(BytesIO(verified_bytes(path, "wehrli85.txt")))
    if np.any(np.diff(table[:, 0]) <= 0) or np.any(table[:, 1] < 0):
        raise SourceError("invalid Wehrli table")
    return table[:, :2]
