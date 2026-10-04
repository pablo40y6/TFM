"""Independent thesis event-equation, citation and immutable-input audit.

Run from the repository root with PYTHONPATH=src;. Does not rerun simulations.
"""

import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

from tfm_photochem.historical_2020.stoichiometry import TENDENCY_COEFFICIENTS
from tfm_photochem.m5_temporal import OH_EVENT_COEFFICIENTS

ROOT = Path(__file__).resolve().parents[1]
THESIS = ROOT / "thesis"
BASE = "e6ecef1f76dc3730484969d94a9a9f2f3743d0d8"
ALIASES = {
    "O,O_2,M": "O_ASSOCIATION",
    "O,O_3": "O_O3",
    "Barth": "BARTH_RECOMBINATION",
    "H,O_2,M": "H_O2_ASSOCIATION",
    "H,O_3": "H_O3",
    "O,OH": "O_OH",
    "O,HO_2": "O_HO2",
    "OH,O_3": "OH_O3",
    "HO_2,O_3": "HO2_O3",
    "OH,H_2": "OH_H2",
    r"H,HO_2\to2OH": "H_HO2_2OH",
    r"H,HO_2\toH_2O+O": "H_HO2_H2O_O",
    r"H,HO_2\toH_2+O_2": "H_HO2_H2_O2",
    "OH,OH": "OH_OH",
    "OH,HO_2": "OH_HO2",
    "HO_2,HO_2": "HO2_HO2",
    "OH,H_2O_2": "OH_H2O2",
    r"H_2O_2,h\nu": "H2O2_PHOTOLYSIS",
    "H_2O,A": "H2O_PHOTOLYSIS_A",
    "O_3,ground": "O3_PHOTOLYSIS_GROUND_EFFECTIVE",
    "O_3,exc": "O3_HARTLEY_PRODUCTS",
    "O_2,SRC": "O2_SRC",
    r"O_2,Ly\alpha": "O2_LYMAN_ALPHA",
    "O_2,ground": "O2_PHOTOLYSIS_GROUND_EFFECTIVE",
    "O_2,IRA": "O2_IRA_BAND",
    r"x,\gamma": "O1D_RADIATIVE",
    r"\Delta,\gamma": "DELTA_RADIATIVE",
    "x,N_2": "O1D_N2",
    r"x,O_2\toB_1": "O1D_O2_B1",
    r"x,O_2\toB_0": "O1D_O2_B0",
    "x,H_2O": "O1D_H2O",
    "x,H_2": "O1D_H2",
    "B_1,O_3": "B1_O3",
    "B_0,N_2": "B0_N2",
    "B_0,O_2": "B0_O2",
    "B_0,O": "B0_O",
    "B_0,O_3": "B0_O3",
    "B_0,CO_2": "B0_CO2",
    r"\Delta,O_2": "DELTA_O2",
    r"\Delta,N_2": "DELTA_N2",
    r"\Delta,O": "DELTA_O",
    r"\Delta,O_3": "DELTA_O3",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def events(equation):
    """Read signed fluxes using balanced braces rather than flat TeX matching."""
    result = Counter()
    for match in re.finditer(r"r_\{", equation):
        start = match.end()
        end, depth = start, 1
        while depth:
            depth += (equation[end] == "{") - (equation[end] == "}")
            end += 1
        name = (
            equation[start : end - 1]
            .replace(r"\mathrm", "")
            .replace("{", "")
            .replace("}", "")
        )
        name = re.sub(r"\s+", "", name)
        prefix = equation[: match.start()]
        signs = list(re.finditer(r"[+-]", prefix))
        previous = signs[-1] if signs else None
        coefficient = 1 if previous is None or previous.group() == "+" else -1
        tail = prefix[previous.end() :] if previous else prefix
        numeric = re.search(r"(\d+)\s*$", tail)
        if numeric:
            coefficient *= int(numeric.group(1))
        result[ALIASES[name]] += coefficient
    return {key: value for key, value in result.items() if value}


def prose_words(source):
    source = re.sub(
        r"\\begin\{(align|equation)\}.*?\\end\{\1\}", "", source, flags=re.S
    )
    source = re.sub(r"\$.*?\$", "", source, flags=re.S)
    source = re.sub(r"\\(?:cite\w*|ref|eqref|label|input)\{[^}]*\}", "", source)
    source = re.sub(r"\\[A-Za-z]+", "", source)
    return len(re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", source))


def main():
    chemistry = (THESIS / "chapters/03_chemistry.tex").read_text()
    appendix = (THESIS / "chapters/appendices.tex").read_text()
    expected = {
        species: {
            event: row[species]
            for event, row in TENDENCY_COEFFICIENTS.items()
            if row[species]
        }
        for species in ("O", "O3", "H", "Delta", "R_H")
    }
    expected["OH"] = dict(OH_EVENT_COEFFICIENTS)
    expected["HO2"] = {
        event: row["R_H"] - OH_EVENT_COEFFICIENTS.get(event, 0)
        for event, row in TENDENCY_COEFFICIENTS.items()
        if row["R_H"] - OH_EVENT_COEFFICIENTS.get(event, 0)
    }
    expected["H2O2"] = {"HO2_HO2": 1, "H2O2_PHOTOLYSIS": -1, "OH_H2O2": -1}
    for species in expected:
        label = "Rbudget" if species == "R_H" else species
        source = appendix if species == "R_H" else chemistry
        stop = source.index(r"\label{eq:" + label + "}")
        start = source.rfind(r"\begin", 0, stop)
        found = events(source[start:stop].split("=", 1)[1])
        assert found == expected[species], (species, found, expected[species])
    chapters = sorted((THESIS / "chapters").glob("[0-9]*.tex"))
    # The independently reviewed draft is the editorial revision reference.
    reviewed = "37d8a04682b96a390ae166ed64169fcdaab95666"
    display_math = r"\\begin\{(align|equation)\}.*?\\end\{\1\}"
    for path in chapters + [THESIS / "chapters/appendices.tex"]:
        relative = path.relative_to(ROOT).as_posix()
        old = subprocess.check_output(
            ["git", "show", f"{reviewed}:{relative}"], cwd=ROOT, text=True
        )
        original_math = [m.group() for m in re.finditer(display_math, old, re.S)]
        revised_math = [
            m.group() for m in re.finditer(display_math, path.read_text(), re.S)
        ]
        assert original_math == revised_math, relative
    for path in (THESIS / "tables").glob("*.tex"):
        relative = path.relative_to(ROOT).as_posix()
        old = subprocess.check_output(
            ["git", "show", f"{reviewed}:{relative}"], cwd=ROOT, text=True
        )
        original_rows = [
            line
            for line in old.splitlines()
            if " & " in line and not line.startswith(r"\begin")
        ]
        revised_rows = [
            line
            for line in path.read_text().splitlines()
            if " & " in line and not line.startswith(r"\begin")
        ]
        assert original_rows == revised_rows, relative
    results_old = subprocess.check_output(
        ["git", "show", f"{reviewed}:thesis/chapters/07_results.tex"],
        cwd=ROOT,
        text=True,
    )
    def numerical_math(source):
        return Counter(
            item for item in re.findall(r"\$([^$]+)\$", source) if re.search(r"\d", item)
        )
    assert not numerical_math(results_old) - numerical_math(
        (THESIS / "chapters/07_results.tex").read_text()
    )
    all_tex = "\n".join(
        path.read_text() for path in (THESIS / "chapters").glob("*.tex")
    )
    keys = set(re.findall(r"@\w+\{([^,]+),", (THESIS / "references.bib").read_text()))
    citations = {
        key
        for group in re.findall(r"\\cite\w*\{([^}]+)\}", all_tex)
        for key in group.split(",")
    }
    assert citations <= keys, citations - keys
    figures = re.findall(r"\\resultfigure(?:\[[^\]]*\])?\{([^}]+)\}", all_tex)
    assert len(figures) == len(set(figures)) == 11
    figure_hashes = {
        name: digest(ROOT / "results/figures" / (name + ".pdf")) for name in figures
    }
    provenance = json.loads((THESIS / "tables/provenance.json").read_text())
    for name, value in provenance["inputs"].items():
        assert digest(ROOT / name) == value, name
    assert digest(
        ROOT / "artifacts/accepted/m4c-r2/tfm-photochem-milestone4c-r2.zip"
    ) == ("2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe")
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", BASE, "--", ".", ":(exclude)thesis"],
        cwd=ROOT,
        text=True,
    )
    assert not changed.strip(), changed
    log = (THESIS / "build/main.log").read_text(errors="replace")
    for failure in (
        "Overfull",
        "undefined references",
        "Citation",
        "! Undefined",
        "LaTeX Error",
    ):
        assert failure not in log, failure
    blg = (THESIS / "build/main.blg").read_text(errors="replace")
    assert "Warning" not in blg and "error" not in blg.lower()
    pages = int(re.search(r"Output written on .*?\((\d+) pages", log).group(1))
    aux = (THESIS / "build/main.aux").read_text()
    main_pages = (
        int(re.search(r"\\newlabel\{app:network\}\{\{A\}\{(\d+)\}", aux).group(1)) - 1
    )
    report = {
        "accepted_base": BASE,
        "status": "PASS",
        "seven_tendencies_and_family_transcription": "exact accepted event coefficients",
        "figures": figure_hashes,
        "bibliography_entries": len(keys),
        "cited_entries": len(citations),
        "main_chapters": len(chapters),
        "appendices": 4,
        "pdf_pages": pages,
        "main_scientific_body_pages": main_pages,
        "main_prose_word_estimate": sum(
            prose_words(path.read_text()) for path in chapters
        ),
        "word_count_method": "source prose/captions excluding math, references and included tables; TeX macros removed",
        "accepted_code_evidence_results_unchanged": True,
        "reviewed_draft_equations_and_table_rows_unchanged": True,
        "results_chapter_numerical_math_retained": True,
        "m4c_r2_sha256": "PASS",
        "compiler": "Tectonic 0.17.0",
        "undefined_citations_references_overfull": 0,
        "pdf_sha256": digest(THESIS / "build/main.pdf"),
        "administrative_placeholders": [
            "university",
            "programme",
            "author",
            "supervisor",
            "submission date",
            "optional acknowledgements",
            "institutional title/template",
        ],
        "human_review": [
            "registered title and institutional layout",
            "initialization and prescribed reservoirs",
            "reduced excited-state routing",
            "finite-horizon and observational claim scope",
        ],
    }
    (THESIS / "consistency_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "figures"}, indent=2
        )
    )


if __name__ == "__main__":
    main()
