"""Produce thesis figures/tables from accepted outputs, without a chemistry solve.

Relative sensitivity is |a-b|/max(a,b); samples below the explicitly recorded
species relevance floor are reported absolutely, never as an unmasked percent.
SZA comparisons use linear interpolation of saved concentrations, not forcing.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from scripts.run_final_results import (
    BASELINE,
    CASES,
    ROOT,
    TAG,
    load_result,
    sha,
    write_json,
)
from scripts.validate_m5_temporal import trajectory_difference
from tfm_photochem.m5_temporal import ReferenceEquinoxSolarCycle

HEIGHTS = (60, 70, 80, 90, 100)
SPECIES = ("O", "O3", "H", "OH", "HO2", "H2O2", "Delta")
PRESENTATION = {"O3": r"O$_3$", "Delta": r"O$_2$(a$^1\Delta$)"}
SEED_NAMES = ("nominal", "low", "high", "missing_bound")
SEED_LABELS = ("Nominal", "Native O/H ×0.5", "Native O/H ×2", "Missing-atom bound")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf8"))


def write_table(name, rows, markdown_columns=None):
    path = ROOT / f"results/tables/{name}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    columns = markdown_columns or list(rows[0])

    def display(value):
        if value is None:
            return "unavailable"
        if isinstance(value, float):
            return f"{value:.5g}"
        return str(value)

    lines = ["Concentrations: molecule cm^-3. Angles: degrees. Relative metrics: percent. Times: explicit UTC or the named reference phase clock.",
             "", "| " + " | ".join(columns) + " |", "| " + " | ".join(["---"]*len(columns)) + " |"]
    lines.extend("| " + " | ".join(display(row[c]) for c in columns) + " |" for row in rows)
    path.with_suffix(".md").write_text("\n".join(lines)+"\n", encoding="utf8")


def at_sza(sza, values, target):
    """Interpolate a strictly decreasing dawn; refuse unavailable coverage."""
    if np.any(np.diff(sza) >= 0):
        raise ValueError("dawn SZA must decrease strictly")
    if target < sza[-1]-1e-6 or target > sza[0]+1e-6:
        return None
    target = min(max(float(target), float(sza[-1])), float(sza[0]))
    a = np.asarray(values)
    return np.array([np.interp(target, sza[::-1], v[::-1])
                    for v in a.reshape(len(a), -1).T]).reshape(a.shape[1:])


def sensitivity(a, b, sza, time, floor):
    difference = abs(a-b)
    relevant = np.maximum(a, b) > floor
    relative = np.divide(difference, np.maximum(a, b), out=np.zeros_like(a), where=relevant)
    values = relative[relevant]
    row, level = np.unravel_index(relative.argmax(), relative.shape)
    return dict(max_percent=float(values.max()*100) if values.size else 0.,
        p90_percent=float(np.percentile(values,90)*100) if values.size else 0.,
        p99_percent=float(np.percentile(values,99)*100) if values.size else 0.,
        maximum_absolute_cm3=float(difference.max()),
        near_zero_absolute_max_cm3=float(np.max(np.where(relevant, 0., difference))),
        relevance_floor_cm3=float(floor), maximum_z_km=int(50+level),
        maximum_SZA_deg=float(sza[row]), maximum_time_s=float(time[row])), relative, relevant


def reuse(accepted_cache):
    """Publish compact accepted sensitivities with immutable input fingerprints."""
    evidence = read_json(ROOT/"evidence/m5_temporal_evidence.json")
    frozen = load_result(ROOT/"evidence/m5b_reference_real_geometry.npz")
    dynamic = load_result(ROOT/"evidence/m5c_reference_dynamic_msis.npz")
    for result, key in ((frozen,"M5B"), (dynamic,"M5C")):
        record = evidence[key]
        artifact = record.get("artifact", record.get("time_height_artifact", {}))
        if artifact and artifact.get("sha256") and sha(ROOT/Path(artifact["path"].replace("\\","/"))) != artifact["sha256"]:
            raise ValueError("accepted artifact fingerprint mismatch")
        np.testing.assert_array_equal(result.R_H_cm3, result.state_cm3[:,:,3]+result.state_cm3[:,:,4])
    np.testing.assert_array_equal(frozen.state_cm3[0], dynamic.state_cm3[0])
    np.testing.assert_array_equal(frozen.time_s, dynamic.time_s)
    mask = (dynamic.time_s > 43200)&(dynamic.sza_deg <= 99)&(dynamic.sza_deg >= 60)
    rows = []
    for index, name in ((1,"O3"), (6,"Delta")):
        floor = max(1., 1e-6*float(frozen.state_cm3[:,:,index].max()))
        stats, _, _ = sensitivity(frozen.state_cm3[mask,:,index], dynamic.state_cm3[mask,:,index],
                                 dynamic.sza_deg[mask], dynamic.time_s[mask], floor)
        rows.append(dict(experiment="frozen_vs_dynamic", variant="same explicit initial state",
                         species=name, **stats))
    temporal_path = ROOT/"src/tfm_photochem/m5_temporal.py"
    current_ast = hashlib.sha256(ast.dump(ast.parse(temporal_path.read_text(encoding="utf8")),
                               include_attributes=False).encode()).hexdigest()
    seed_states, audits, inputs = [], [], []
    time = None
    for name in SEED_NAMES:
        path = accepted_cache/f"noon-run-{name}-base.npz"
        with np.load(path, allow_pickle=False) as data:
            if str(data["source_ast_sha256"]) != current_ast:
                raise ValueError("accepted initialization source AST mismatch")
            states = data["state"].copy()
            if time is None:
                time = data["time"].copy()
            else:
                np.testing.assert_array_equal(time, data["time"])
            if not np.all(np.isfinite(states)) or np.any(states < 0):
                raise ValueError("invalid accepted initialization state")
            audits.append(json.loads(str(data["audit"])))
            seed_states.append(states)
            inputs.append(dict(variant=name, local_cache_basename=path.name, sha256=sha(path),
                               accepted_source_AST_sha256=current_ast,
                               original_source_sha256=str(data["source_sha256"])))
    with np.load(ROOT/"evidence/m5_reference_cycle.npz") as golden:
        np.testing.assert_array_equal(golden["state_cm3"][0], seed_states[0][0])
        golden_comparison = trajectory_difference(golden["state_cm3"], seed_states[0])
        if not golden_comparison["pass_"]:
            raise ValueError("accepted base initialization run does not reproduce tight golden")
    angles = ReferenceEquinoxSolarCycle().sza(time)
    mask = (time > 86400)&(angles <= 99)&(angles >= 60)
    seed_states = np.array(seed_states)
    path = ROOT/"results/tables/initialization_dawn.npz"
    np.savez_compressed(path, state_cm3=seed_states[:,mask], time_phase_s=time[mask],
        sza_deg=angles[mask], altitude_km=np.arange(50,101), state_names=SPECIES,
        variants=SEED_NAMES, metadata=json.dumps(dict(geometry="accepted artificial equinox cycle",
            time="phase seconds; no UTC interpretation", atmosphere="frozen_reference M4A",
            scope="accepted M5A initialization sensitivity, separate from dynamic campaign")))
    for variant in range(1,4):
        for index, name in ((1,"O3"), (6,"Delta")):
            # Same dawn-only relevance floor as accepted M5A initialization evidence.
            floor = max(1., 1e-6*float(seed_states[0,mask,:,index].max()))
            stats, _, _ = sensitivity(seed_states[0,mask,:,index], seed_states[variant,mask,:,index],
                                     angles[mask], time[mask], floor)
            rows.append(dict(experiment="initialization", variant=SEED_NAMES[variant],
                             species=name, **stats))
    write_table("sensitivity_summary", rows, ["experiment","variant","species",
        "max_percent","p90_percent","p99_percent","maximum_absolute_cm3",
        "maximum_z_km","maximum_SZA_deg"])
    write_json(ROOT/"results/manifests/reused_sensitivities.json", dict(
        baseline_git_sha=BASELINE, baseline_tag=TAG, evidence="evidence/m5_temporal_evidence.json",
        evidence_sha256=sha(ROOT/"evidence/m5_temporal_evidence.json"),
        atmosphere_inputs=[dict(path=p,sha256=sha(ROOT/p)) for p in
            ("evidence/m5b_reference_real_geometry.npz","evidence/m5c_reference_dynamic_msis.npz")],
        exact_same_initial_state=True, initialization_inputs=inputs, accepted_audits=audits,
        initialization_base_vs_tight_golden=golden_comparison,
        initialization_output=dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),
                                   bytes=path.stat().st_size),
        comparison="symmetric relative difference; floor=max(1,1e-6 nominal peak); full-run peak for atmosphere, dawn peak for initialization, as in accepted evidence",
        initialization_window="saved native dawn samples, SZA99 to60; same accepted artificial geometry"))
    return rows


def summaries(cases):
    reference = cases["reference"]
    rows = []
    for angle in (99.,85.,60.):
        column = at_sza(reference.sza_deg, reference.state_cm3, angle)
        t = float(at_sza(reference.sza_deg, reference.time_s, angle))
        for z in HEIGHTS:
            state = column[z-50]
            origin = datetime.fromisoformat(reference.metadata["absolute_time_origin_utc"])
            rows.append(dict(z_km=z,SZA_deg=angle,UTC=(origin+timedelta(seconds=t)).isoformat(),
                             **dict(zip(SPECIES,map(float,state),strict=True)),
                             R_H=float(state[3]+state[4])))
    write_table("reference_dawn_summary",rows)
    all_metrics = {}
    for group, names in (("seasonal",("reference","summer","autumn","winter")),
                         ("latitude",("equatorial","reference","high_latitude"))):
        rows = []
        for name in names:
            result = cases[name]
            for z in HEIGHTS:
                for index, species in ((1,"O3"),(6,"Delta")):
                    values = result.state_cm3[:,z-50,index]
                    sza = result.sza_deg
                    at99 = float(at_sza(sza,values,99.))
                    at70 = float(at_sza(sza,values,70.))
                    at60 = at_sza(sza,values,60.)
                    common = np.r_[at99,values[(sza<99)&(sza>70)],at70]
                    floor = max(1.,1e-6*result.state_cm3[:,:,index].max())
                    rows.append(dict(case=name, latitude_deg=result.metadata["campaign"]["latitude_deg"],
                        z_km=z,species=species,at_SZA99_cm3=at99,
                        at_SZA85_cm3=float(at_sza(sza,values,85.)),
                        at_SZA70_cm3=at70,at_SZA60_cm3=None if at60 is None else float(at60),
                        dawn_min_cm3=float(values.min()),dawn_max_cm3=float(values.max()),
                        common_99_70_min_cm3=float(common.min()),common_99_70_max_cm3=float(common.max()),
                        common_99_70_change_percent=100*(at70-at99)/at99 if at99>floor else None,
                        common_99_70_change_absolute_cm3=at70-at99,
                        final_SZA_deg=float(sza[-1])))
        write_table(group+"_summary",rows,["case","z_km","species","at_SZA99_cm3",
            "at_SZA85_cm3","at_SZA70_cm3","at_SZA60_cm3","common_99_70_change_percent"])
        all_metrics[group] = rows
    return all_metrics


def plotting():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False,
        "savefig.dpi":300,"pdf.fonttype":42,"figure.constrained_layout.use":True})
    return plt


def save_figure(fig, name, caption, registry):
    path = ROOT/f"results/figures/{name}"
    path.parent.mkdir(parents=True,exist_ok=True)
    files = []
    for suffix in (".png",".pdf"):
        target = path.with_suffix(suffix)
        fig.savefig(target)
        files.append(dict(path=target.relative_to(ROOT).as_posix(),sha256=sha(target),bytes=target.stat().st_size))
    registry.append(dict(figure=name,caption=caption,files=files))
    plotting().close(fig)


def figures(cases):
    plt = plotting()
    registry = []
    ref = cases["reference"]
    hours = ref.time_s/3600.+20.
    origin = datetime.fromisoformat(ref.metadata["absolute_time_origin_utc"])
    hours -= 24.
    angle_ticks = (99.,90.,85.,75.,60.)
    hour_ticks = [float(at_sza(ref.sza_deg,hours,a)) for a in angle_ticks]
    for index,name,number in ((1,"O3",1),(6,"Delta",2)):
        fig,ax = plt.subplots(figsize=(7.1,4.3))
        values = ref.state_cm3[:,:,index]
        from matplotlib.colors import LogNorm
        positive = values[values>0]
        mesh = ax.pcolormesh(hours,ref.altitude_km,np.ma.masked_less_equal(values.T,1.),
            shading="auto",norm=LogNorm(vmin=max(1.,positive.min()),vmax=values.max()),cmap="viridis")
        fig.colorbar(mesh,ax=ax,label=PRESENTATION[name]+r" [molecule cm$^{-3}$]")
        ax.set(xlabel=f"UTC hour, {(origin+timedelta(days=1)):%Y-%m-%d}",ylabel="Altitude [km]")
        top = ax.secondary_xaxis("top")
        top.set_xticks(hour_ticks,[f"{a:g}" for a in angle_ticks])
        top.set_xlabel("Solar zenith angle [°]")
        save_figure(fig,f"{number:02d}_reference_{name.lower()}_heatmap",
            "Reference dynamic-MSIS dawn; approximate reference-noon bootstrap; logarithmic concentration colour scale. Values≤1 molecule cm^-3 are masked for display only; all numerical data are retained.",registry)
    for index,name,number in ((1,"O3",3),(6,"Delta",4)):
        fig,ax = plt.subplots(figsize=(7.1,4.3))
        for z in HEIGHTS:
            ax.plot(ref.sza_deg,np.ma.masked_less_equal(ref.state_cm3[:,z-50,index],1.),label=f"{z} km")
        ax.set(yscale="log",xlim=(99,60),xlabel="Solar zenith angle [°] (dawn →)",
               ylabel=PRESENTATION[name]+r" [molecule cm$^{-3}$]")
        ax.legend(ncol=3,frameon=False)
        save_figure(fig,f"{number:02d}_reference_{name.lower()}_levels",
                    "Reference dawn at five selected heights; concentrations evolve freely after the approximate initialization. Values≤1 molecule cm^-3 are omitted on logarithmic axes for display only.",registry)
    fig,axes = plt.subplots(1,2,figsize=(8.1,4.8),sharey=True)
    for ax,index,name in zip(axes,(1,6),("O3","Delta"),strict=True):
        for angle in (99.,85.,60.):
            ax.plot(np.ma.masked_less_equal(at_sza(ref.sza_deg,ref.state_cm3[:,:,index],angle),1.),ref.altitude_km,
                    label=f"SZA {angle:g}°")
        ax.set(xscale="log",xlabel=PRESENTATION[name]+r" [molecule cm$^{-3}$]")
    axes[0].set_ylabel("Altitude [km]")
    axes[1].legend(frameon=False)
    save_figure(fig,"05_reference_profiles","Vertical profiles at SZA99/85/60 from saved reference concentrations; intermediate SZA values use linear output interpolation. Values≤1 molecule cm^-3 are omitted on logarithmic axes for display only.",registry)
    for group,names,numbers in (("seasonal",("reference","summer","autumn","winter"),(6,7)),
                                ("latitude",("equatorial","reference","high_latitude"),(8,9))):
        if not all(name in cases for name in names):
            continue  # Allow a local reference preview while new cases are running.
        for index,species,number in zip((1,6),("O3","Delta"),numbers,strict=True):
            fig,axes = plt.subplots(1,2,figsize=(8.2,4.8),sharey=True)
            for name in names:
                result = cases[name]
                label = result.metadata["campaign"]["date"] if group=="seasonal" else f"{result.metadata['campaign']['latitude_deg']:g}°N"
                for ax,angle in zip(axes,(85.,70.),strict=True):
                    ax.plot(at_sza(result.sza_deg,result.state_cm3[:,:,index],angle),
                            result.altitude_km,label=label)
                    ax.set(xscale="log",title=f"SZA {angle:g}°",xlabel=PRESENTATION[species]+r" [molecule cm$^{-3}$]")
            axes[0].set_ylabel("Altitude [km]")
            axes[1].legend(frameon=False)
            save_figure(fig,f"{number:02d}_{group}_{species.lower()}",
                f"Complete {group} model response at common SZA85/70: solar geometry, dynamic background and approximate initialization all change. Common dawn interval99→70; no extrapolation to unreachable60°.",registry)
    frozen = load_result(ROOT/"evidence/m5b_reference_real_geometry.npz")
    dynamic = load_result(ROOT/"evidence/m5c_reference_dynamic_msis.npz")
    mask = (dynamic.time_s>43200)&(dynamic.sza_deg<=99)&(dynamic.sza_deg>=60)
    fig,axes = plt.subplots(1,2,figsize=(9.2,4.8),sharey=True)
    for ax,index,name in zip(axes,(1,6),("O3","Delta"),strict=True):
        floor = max(1.,1e-6*frozen.state_cm3[:,:,index].max())
        _,relative,relevant = sensitivity(frozen.state_cm3[mask,:,index],dynamic.state_cm3[mask,:,index],
                                           dynamic.sza_deg[mask],dynamic.time_s[mask],floor)
        mesh = ax.pcolormesh(dynamic.sza_deg[mask],dynamic.altitude_km,
            np.ma.array(100*relative.T,mask=~relevant.T),shading="auto",vmin=0,vmax=100*relative.max(),cmap="magma")
        ax.set(xlim=(99,60),xlabel="Solar zenith angle [°] (dawn →)",title=PRESENTATION[name])
        fig.colorbar(mesh,ax=ax,label=r"$|dynamic-frozen|/\max(dynamic,frozen)$ [%]")
    axes[0].set_ylabel("Altitude [km]")
    save_figure(fig,"10_frozen_dynamic_sensitivity",
        "Accepted frozen/dynamic sensitivity with identical explicit initial concentrations. Near-zero concentrations are masked using the recorded relevance floors; accepted output stops at SZA60.961°, leaving60° uncovered.",registry)
    with np.load(ROOT/"results/tables/initialization_dawn.npz") as data:
        states,time,sza = data["state_cm3"],data["time_phase_s"],data["sza_deg"]
    fig,axes = plt.subplots(1,2,figsize=(8.2,4.8),sharey=True)
    for ax,index,name in zip(axes,(1,6),("O3","Delta"),strict=True):
        rows = list(csv.DictReader((ROOT/"results/tables/sensitivity_summary.csv").open(encoding="utf8")))
        floor = float(next(r for r in rows if r["experiment"]=="initialization" and r["species"]==name)["relevance_floor_cm3"])
        for variant in range(1,4):
            _,rel,relevant = sensitivity(states[0,:,:,index],states[variant,:,:,index],sza,time,floor)
            # Ignore near-zero samples; no relevant samples means no relative metric.
            curve = np.array([np.max(rel[relevant[:,z],z]) if np.any(relevant[:,z]) else np.nan for z in range(51)])
            ax.plot(100*curve,np.arange(50,101),label=SEED_LABELS[variant])
        ax.set(xlabel="Maximum relevant dawn difference [%]",title=PRESENTATION[name],xlim=(0,100))
    axes[0].set_ylabel("Altitude [km]")
    axes[1].legend(frameon=False,fontsize=9)
    save_figure(fig,"11_initialization_sensitivity",
        "Reused accepted M5A frozen-atmosphere/artificial-equinox experiment; maximum relative dawn sensitivity per altitude. Reference-noon bootstrap is approximate, not climatology; small-concentration samples use absolute metrics in the table.",registry)
    write_json(ROOT/"results/manifests/figures.json",dict(figures=registry,
        plotting_script_sha256=sha(Path(__file__)),
        matplotlib_version=__import__("matplotlib").__version__,numpy_version=np.__version__,
        numeric_inputs_sha256={p.relative_to(ROOT).as_posix():sha(p) for pattern in ("*.npz","*.csv")
                              for p in (ROOT/"results/tables").glob(pattern)}))
    return registry


def checks():
    """Artifact and table consistency, including boundary/interpolation conventions."""
    unchanged = subprocess.run(["git","diff","--quiet",BASELINE,"--","src",
                                "artifacts/accepted","evidence"],cwd=ROOT,check=False)
    if unchanged.returncode:
        raise ValueError("accepted model/assets/evidence were modified")
    for name in CASES:
        manifest = read_json(ROOT/f"results/manifests/{name}.json")
        path = ROOT/manifest["output"]["path"]
        if sha(path) != manifest["output"]["sha256"]:
            raise ValueError("output checksum mismatch")
        result = load_result(path)
        assert np.all(np.isfinite(result.state_cm3)) and np.all(result.state_cm3>=0)
        np.testing.assert_array_equal(result.R_H_cm3,result.state_cm3[:,:,3]+result.state_cm3[:,:,4])
        assert abs(result.sza_deg[0]-99)<1e-6 and np.all(np.diff(result.sza_deg)<0)
        assert manifest["QA"]["exact_shadow"] and manifest["QA"]["exact_R_H"]
        tangent = 180-np.rad2deg(np.arcsin(6370/(6370+result.altitude_km)))
        assert np.all(result.forcing_s1[result.sza_deg[:,None]>tangent[None,:]]==0)
        assert np.all(np.isfinite(result.algebraic_cm3)) and np.all(result.algebraic_cm3>=0)
        if manifest["config"]["reaches_sza60"]:
            assert abs(result.sza_deg[-1]-60)<1e-6
        else:
            assert at_sza(result.sza_deg,result.state_cm3,60.) is None
    figure_manifest = read_json(ROOT/"results/manifests/figures.json")
    assert len(figure_manifest["figures"])==11
    for path, digest in figure_manifest["numeric_inputs_sha256"].items():
        assert sha(ROOT/path)==digest
    for figure in figure_manifest["figures"]:
        for file in figure["files"]:
            assert sha(ROOT/file["path"])==file["sha256"]
    reused = read_json(ROOT/"results/manifests/reused_sensitivities.json")
    seed_output = reused["initialization_output"]
    assert sha(ROOT/seed_output["path"])==seed_output["sha256"]
    for item in reused["atmosphere_inputs"]:
        assert sha(ROOT/item["path"])==item["sha256"]
    ref = load_result(ROOT/"results/tables/reference_dawn.npz")
    rows = list(csv.DictReader((ROOT/"results/tables/reference_dawn_summary.csv").open(encoding="utf8")))
    assert len(rows)==15
    for row in rows:
        z,angle = int(row["z_km"]),float(row["SZA_deg"])
        state = at_sza(ref.sza_deg,ref.state_cm3,angle)[z-50]
        np.testing.assert_allclose([float(row[name]) for name in SPECIES],state,rtol=1e-14)
        assert float(row["R_H"])==float(row["OH"])+float(row["HO2"])
    immutable = ROOT/"artifacts/accepted/m4c-r2/tfm-photochem-milestone4c-r2.zip"
    assert sha(immutable)=="2944c8a8e0899b320c69c45192ee6f03b9001114c4120a9db8c67a3f1bb8f1fe"
    return dict(status="PASS",scenarios=6,figures=11,reference_rows=15,
                output_checksums=True,table_consistency=True,M4C_R2_intact=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode",choices=("reuse","all","check"),default="all")
    parser.add_argument("--accepted-initialization-cache",type=Path)
    args = parser.parse_args()
    if args.mode=="check":
        record = checks()
        write_json(ROOT/"results/manifests/results_consistency.json",record)
        print(json.dumps(record))
        return
    if args.accepted_initialization_cache is not None:
        reuse(args.accepted_initialization_cache)
    elif args.mode=="reuse" or not (ROOT/"results/tables/initialization_dawn.npz").exists():
        parser.error("initial preparation needs verified local --accepted-initialization-cache")
    if args.mode=="reuse":
        return
    cases = {name:load_result(ROOT/f"results/tables/{name}_dawn.npz") for name in CASES}
    summaries(cases)
    figures(cases)
    print(json.dumps(checks()))


if __name__=="__main__":
    main()
