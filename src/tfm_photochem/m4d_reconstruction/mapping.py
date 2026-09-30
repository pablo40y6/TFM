"""Quantum-identity mapping; source parameter tables remain local/uncommitted."""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from .sources import Line, SourceError, normalize_quantum, verified_bytes


def unique_rows(rows, label: str) -> dict:
    out = {}
    for key, value in rows:
        if key in out:
            raise SourceError(f"{label}: duplicate/ambiguous key {key}")
        out[key] = value
    return out


def source_number(text: str) -> float:
    # Parentheses contain published uncertainties, never part of the mean.
    value = text.replace("\u2212", "-").split("(")[0].strip()
    if not re.fullmatch(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[Ee][+-]?\d+)?", value):
        raise SourceError(f"unrecognized source number {text!r}")
    return float(value)


def parse_drouin(path: str | Path) -> dict[str, tuple[float, ...]]:
    root = ET.fromstring(verified_bytes(path, "PMC5103325.xml"))
    result = []
    counts = []
    for table in root.iter("table-wrap"):
        label = "".join(table.find("label").itertext())
        if label not in ("Table 4", "Table 5"):
            continue
        rows = list(table.iter("tr"))[1:]
        counts.append((label, len(rows)))
        for row in rows:
            cells = ["".join(cell.itertext()).strip() for cell in row]
            if len(cells) != 14 or not all(
                re.fullmatch(r"[PQR]\d+", x) for x in cells[:2]
            ):
                raise SourceError(f"invalid {label} quantum row")
            result.append(
                ("".join(cells[:2]), tuple(source_number(x) for x in cells[2:]))
            )
    if sorted(counts) != [("Table 4", 45), ("Table 5", 46)]:
        raise SourceError(f"Drouin table count mismatch: {counts}")
    return unique_rows(result, "Drouin Tables 4/5")


def supplement_label(first: str, second: str) -> str:
    """Translate supplement N'/J'' convention using spectroscopic branch rules."""
    n = int(first[1:])
    if second[0] == "Q":
        j = int(second[1:])
        if n != j or n % 2 != 0:
            raise SourceError("invalid supplement Q-branch quantum identity")
        n = j + 1 if first[0] == "P" else j - 1
    return f"{first[0]}{n}{second}"


def parse_supplement(path: str | Path) -> tuple[dict, dict]:
    # PyMuPDF is only needed in source materialization, not transfer at runtime.
    import pymupdf

    data = verified_bytes(path, "1-s2.0-S0022407316301108-mmc1.pdf")
    document = pymupdf.open(stream=data, filetype="pdf")
    if len(document) != 12:
        raise SourceError("Drouin supplement page count")
    texts = [page.get_text() for page in document]
    all_text = "\n".join(texts)
    table22 = [
        page.get_text(sort=True) for page in document if "Table 22:" in page.get_text()
    ]
    if len(table22) != 1:
        raise SourceError("missing or ambiguous Table 22")
    rows = []
    for row in table22[0].splitlines():
        cells = row.split()
        if cells and re.fullmatch(r"[PR]\d+", cells[0]):
            if len(cells) != 6 or not re.fullmatch(r"[PQR]\d+", cells[1]):
                raise SourceError(f"malformed Table-22 row {row!r}")
            rows.append(
                (
                    supplement_label(*cells[:2]),
                    tuple(source_number(x) for x in cells[2:]),
                )
            )
    if len(rows) != 70:
        raise SourceError("Table 22 does not contain exactly 70 rows")
    mixing = unique_rows(rows, "Table 22")
    # Matrix material is parsed as individually delimited source tables for
    # auditing; it is never reverse-engineered into replacement Y coefficients.
    matrix_tables = {}
    for number in range(6, 22):
        match = re.search(rf"Table {number}:.*?(?=Table \d+:|\Z)", all_text, re.S)
        if match is None:
            raise SourceError(f"missing supplement matrix table {number}")
        section = match[0].replace("\u2212", "-")
        labels = list(dict.fromkeys(re.findall(r"[PR]\d+[PQR]\d+", section)))
        branch = re.search(r"for the ([PR][PQR]) sub-band", section)
        if branch is None:
            raise SourceError(f"matrix {number}: missing sub-band")
        dimension = 17 if branch[1] in ("PQ", "RQ") else 18
        if len(labels) != dimension:
            raise SourceError(f"matrix {number}: dimension/quantum coverage mismatch")
        row_matches = list(
            re.finditer(r"([PR]\d+[PQR]\d+)[ \t]+(\d{5}\.\d)\s+", section)
        )
        if len(row_matches) != dimension - 1:
            raise SourceError(f"matrix {number}: triangular row count")
        values = []
        for index, row_match in enumerate(row_matches):
            end = (
                row_matches[index + 1].start()
                if index + 1 < len(row_matches)
                else len(section)
            )
            tokens = section[row_match.end() : end].split()
            # Last row is followed by page numbers and source explanatory prose.
            # Its value count follows the explicitly verified triangular layout.
            if index == len(row_matches) - 1:
                trailing = tokens[index + 1 :]
                if trailing and not (trailing[0].isdigit() or trailing[0] == "Air"):
                    raise SourceError(f"matrix {number}: unrecognized table footer")
                tokens = tokens[: index + 1]
            row_values = tuple(source_number(token) for token in tokens)
            if row_match[1] != labels[index + 1] or len(row_values) != index + 1:
                raise SourceError(f"matrix {number}: label/triangular value count")
            values.extend(row_values)
        matrix_tables[str(number)] = {
            "dimension": dimension,
            "branch": branch[1],
            "quantum_labels": labels,
            "offdiagonal_values": len(values),
            "extracted_text_sha256": hashlib.sha256(match[0].encode()).hexdigest(),
        }
    return mixing, {
        "pages": 12,
        "table22_rows": 70,
        "matrix_tables": matrix_tables,
        "matrix_dimensions_by_branch": {"PP": 18, "PQ": 17, "RR": 18, "RQ": 17},
    }


def parse_galatry(path: str | Path) -> dict[tuple, tuple[float, float] | None]:
    text = verified_bytes(path, "07_hit12_0.76mic_Galatry.par").decode("ascii")
    records = text.splitlines()
    if len(records) != 489:
        raise SourceError("Galatry record count")
    population = Counter(int(row[2]) for row in records)
    if population != {1: 209, 2: 140, 3: 140}:
        raise SourceError("Galatry isotope population")
    rows = []
    for row in records:
        if len(row) not in (87, 97) or row[:2].strip() != "7":
            raise SourceError(f"Galatry auxiliary layout: {len(row)}")
        key = (
            7,
            int(row[2]),
            *(
                normalize_quantum(row[a:b])
                for a, b in ((26, 41), (41, 56), (56, 71), (71, 86))
            ),
        )
        if key[2:4] != ("b 0", "X 0"):
            continue
        beta = (float(row[86:92]), float(row[92:97])) if len(row) == 97 else None
        if key[1] in (2, 3) and (beta is None or min(beta) <= 0):
            raise SourceError("rare Dicke coefficients missing or invalid")
        rows.append((key, beta))
    if len(rows) != 430:
        raise SourceError("Galatry A-band subset count")
    return unique_rows(rows, "Galatry A-band")


def audit_mapping(
    lines: tuple[Line, ...], drouin: dict, mixing: dict, galatry: dict, supplement: dict
) -> dict:
    dipoles = unique_rows(
        (
            (line.dipole_label, line)
            for line in lines
            if line.isotope == 1 and line.flag == "d"
        ),
        "HITRAN2016 dipoles",
    )
    quadrupoles = [line for line in lines if line.isotope == 1 and line.flag == "q"]
    other = [
        line.key for line in lines if line.isotope == 1 and line.flag not in ("d", "q")
    ]
    missing = sorted(set(dipoles) - set(drouin))
    extra = sorted(set(drouin) - set(dipoles))
    lm_extra = sorted(set(mixing) - set(dipoles))
    missing_aux = sorted(set(line.key for line in lines) - set(galatry))
    extra_aux = sorted(set(galatry) - set(line.key for line in lines))
    if (len(dipoles), len(mixing), len(quadrupoles)) != (91, 70, 59) or any(
        (missing, extra, lm_extra, missing_aux, extra_aux, other)
    ):
        raise SourceError(
            f"MAPPING BLOCKER: {(missing, extra, lm_extra, missing_aux, extra_aux, other)}"
        )
    no_y = sorted(set(dipoles) - set(mixing))
    classes = {
        "drouin_sdv_rosenkranz": sorted(mixing),
        "drouin_sdv_no_published_y": no_y,
        "classic_quadrupole_count": len(quadrupoles),
        "other": other,
    }
    return {
        "status": "PASS",
        "principal_total": 150,
        "drouin_sdv": 91,
        "published_lm": 70,
        "dipoles_outside_lm": len(no_y),
        "quadrupoles": 59,
        "rare_galatry": sum(line.isotope in (2, 3) for line in lines),
        "auxiliary_matches": 430,
        "unmatched": [],
        "duplicates": [],
        "ambiguities": [],
        "source_extra": [],
        "classes": classes,
        "supplement": supplement,
        "precedence": "HITRAN2016 ordinary fields; auxiliary Dicke fields only",
    }
