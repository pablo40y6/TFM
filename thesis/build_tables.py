"""Produce thesis tables directly from accepted data and frozen registries.

Run from the repository root with src on PYTHONPATH. Never changes model files.
"""
from pathlib import Path
import ast
import csv
import hashlib
import json
import math

from tfm_photochem.historical_2020.kinetics import RATE_LAWS
from tfm_photochem.historical_2020.reactions import REACTIONS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "thesis/tables"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number(value):
    value = float(value)
    if value == 0:
        return "0"
    exponent = int(math.floor(math.log10(abs(value))))
    return rf"{value / 10**exponent:.4f}\times10^{{{exponent}}}"


def expression(node):
    if isinstance(node, ast.Constant):
        if abs(node.value) < 0.01:
            return number(node.value)
        return str(node.value)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.UnaryOp):
        return ("-" if isinstance(node.op, ast.USub) else "+") + expression(node.operand)
    if isinstance(node, ast.Call) and node.func.id == "exp":
        return rf"\exp\left({expression(node.args[0])}\right)"
    if isinstance(node, ast.BinOp):
        a, b = expression(node.left), expression(node.right)
        if isinstance(node.op, ast.Div):
            return rf"\frac{{{a}}}{{{b}}}"
        if isinstance(node.op, ast.Pow):
            return rf"\left({a}\right)^{{{b}}}"
        if isinstance(node.op, ast.Mult):
            return a + r"\," + b
        if isinstance(node.op, ast.Add):
            return a + "+" + b
    raise ValueError(ast.dump(node))


SPECIES = {"O1D": r"\mathrm{O}(^1D)", "Delta": r"\mathrm{O}_2(a^1\Delta_g)",
           "B0": r"B_0", "B1": r"B_1", "O2star": r"\mathrm{O}_2^*",
           "hv": r"h\nu", "photon": r"h\nu"}


def species(name):
    if name in SPECIES:
        return SPECIES[name]
    return r"\mathrm{" + "".join("_{" + c + "}" if c.isdigit() else c for c in name) + "}"


def side(terms):
    return "+".join((str(int(n)) if n != 1 else "") + species(s) for s, n in terms)


def write(name, text):
    (OUT / name).write_text(text + "\n", encoding="utf8", newline="\n")


def rows(name):
    with (ROOT / "results/tables" / (name + ".csv")).open(newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))


def generate():
    OUT.mkdir(parents=True, exist_ok=True)
    ids = {key: f"K{i}" for i, key in enumerate(RATE_LAWS, 1)}
    header = r"\begin{longtable}{rp{0.54\textwidth}p{0.25\textwidth}}\caption{Complete accepted process registry. K labels refer to Table~\ref{tab:rates}; forcing and effective entries are explained below.}\label{tab:network}\\\toprule No. & Process & Coefficient/source\\\midrule\endfirsthead\toprule No. & Process & Coefficient/source\\\midrule\endhead\bottomrule\endfoot"
    data = []
    forcing = {"O3_HARTLEY":r"$0.9J_H$", "O3_PHOTOLYSIS_GROUND_EFFECTIVE":r"$J_3^g$",
               "O2_SRC":r"$J_{\mathrm{SRC}}$", "O2_LYMAN_ALPHA":r"$0.44J_{\mathrm{Ly\alpha}}$",
               "O2_PHOTOLYSIS_GROUND_EFFECTIVE":r"$J_2^g$", "O2_A_BAND":r"$g_A$",
               "O2_B_BAND":r"$g_B$", "O2_IRA_BAND":r"$g_{\mathrm{IRA}}$",
               "H2O2_PHOTOLYSIS":r"$J_{\mathrm{H_2O_2}}$", "H2O_PHOTOLYSIS_A":r"$J_{\mathrm{H_2O,A}}$",
               "H2O_PHOTOLYSIS_B":r"$J_{\mathrm{H_2O,B}}$",
               "BARTH_TRANSFER":"Absorbed into effective source", "BARTH_O2STAR_QUENCH":"Absorbed into effective source"}
    for i, r in enumerate(REACTIONS, 1):
        coefficient = ids[r.coefficient_id] if r.coefficient_id else forcing[r.identifier]
        if r.identifier == "O1D_O2_B1":
            coefficient = "0.8 " + coefficient
        elif r.identifier == "O1D_O2_B0":
            coefficient = "0.2 " + coefficient
        equation = side(r.reactants) + r"\longrightarrow" + side(r.products)
        data.append(f"{i} & ${equation}$ & {coefficient}" + r"\\")
    write("network.tex", header + "\n" + "\n".join(data) + "\n" + r"\end{longtable}")
    rate_rows = []
    for key, law in RATE_LAWS.items():
        formula = expression(ast.parse(law.expression.replace("^", "**"), mode="eval").body)
        unit = {1:r"s^{-1}", 2:r"cm^3\,molecule^{-1}\,s^{-1}",
                3:r"cm^6\,molecule^{-2}\,s^{-1}"}[law.molecular_order]
        source = "JPL18" if "JPL" in law.reference else "Historical model"
        rate_rows.append(f"{ids[key]} & ${formula}$ & ${unit}$ & {source}" + r"\\")
    write("rates.tex", r"\begin{longtable}{rp{0.40\textwidth}p{0.25\textwidth}l}\caption{Accepted coefficient laws; $T$ is kelvin and $M$ is molecule cm$^{-3}$.}\label{tab:rates}\\\toprule Label & Law & Unit & Provenance\\\midrule\endfirsthead\toprule Label & Law & Unit & Provenance\\\midrule\endhead\bottomrule\endfoot" + "\n" + "\n".join(rate_rows) + "\n" + r"\end{longtable}")
    reference = rows("reference_dawn_summary")
    data = []
    for r in reference:
        # Field names are validated against the canonical table, never inferred.
        data.append(f"{float(r['z_km']):g} & {float(r['SZA_deg']):g} & ${number(r['O3'])}$ & ${number(r['Delta'])}$" + r"\\")
    write("reference.tex", r"\begin{table}[htbp]\centering\small\caption{Reference dawn concentrations at selected heights and SZA. Units: molecule cm$^{-3}$. Intermediate SZA values are interpolated saved outputs.}\label{tab:reference}\begin{tabular}{rrrr}\toprule Height (km) & SZA ($^\circ$) & O$_3$ & $\Delta$\\\midrule" + "\n" + "\n".join(data) + r"\bottomrule\end{tabular}\end{table}")
    audit = {"inputs":{p.relative_to(ROOT).as_posix():sha(p) for p in
             [ROOT/"results/tables/reference_dawn_summary.csv",ROOT/"src/tfm_photochem/historical_2020/reactions.py",ROOT/"src/tfm_photochem/historical_2020/kinetics.py"]},
             "registry_processes":len(REACTIONS),"rate_laws":len(RATE_LAWS),"reference_rows":len(reference)}
    write("provenance.json", json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    generate()
