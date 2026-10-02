"""Reproduce downstream A0/A1 and M5B UTC geometry without reopening M5A."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from scripts.validate_m5_temporal import (
    prepare_nir,
    retained_closure_audit,
    trajectory_difference,
)
from tfm_photochem.m5_simulation import ReferenceElapsedGeometry, simulate
from tfm_photochem.m5_temporal import (
    DynamicPeroxideColumnRHS,
    integrate_reference_noon_to_dawn,
    reference_noon_initialization,
)
from tfm_photochem.solar_geometry import DatetimeSolarGeometry


class A1OnlyNIR:
    """Change gA alone, preserving B/IRA interpolation bit for bit."""
    def __init__(self, baseline, advanced):
        self.baseline = baseline
        self.advanced = advanced

    def __call__(self, angle):
        rates = self.baseline(angle)
        rates[:,0] = self.advanced(angle)[:,0]
        return rates


def downstream_stats(reference, trial, times):
    """Symmetric relevant relative difference; absolute difference for all values."""
    dawn = (times>=86400)&(np.asarray(ReferenceElapsedGeometry().sza(times-43200))<=99.+1e-9)
    result={}
    for index,name in ((1,"O3"),(6,"Delta")):
        a,b=reference[dawn,:,index],trial[dawn,:,index]
        floor=max(1.,1e-6*float(np.max(reference[:,:,index])))
        def summary(a,b):
            relevant=np.maximum(a,b)>floor
            difference=abs(a-b)
            relative=np.divide(difference,np.maximum(a,b),out=np.zeros_like(a),where=relevant)
            values=relative[relevant]
            maximum=np.unravel_index(np.argmax(relative),relative.shape)
            return dict(max_relative=float(values.max()) if values.size else 0.,
                p90_relative=float(np.percentile(values,90)) if values.size else 0.,
                p99_relative=float(np.percentile(values,99)) if values.size else 0.,
                maximum_absolute_difference_cm3=float(difference.max()),
                near_zero_absolute_max_cm3=float(np.max(np.where(relevant,0.,difference))),
                relevance_floor_cm3=floor,maximum_index=list(map(int,maximum)))
        global_stats=summary(a,b)
        i,j=global_stats.pop("maximum_index")
        global_stats["maximum_case"]={"time_s":float(times[dawn][i]),"z_km":j+50,
                                     "SZA_deg":float(ReferenceElapsedGeometry().sza(times[dawn][i]-43200))}
        result[name]=dict(all_heights=global_stats,selected_heights={str(z):summary(a[:,z-50],b[:,z-50])
                                                                   for z in (60,70,80,90,100)})
    return result


def assess(args):
    cache=args.cache
    golden_sha=hashlib.sha256(Path("evidence/m5_reference_cycle.npz").read_bytes()).hexdigest()
    assert golden_sha=="96ba8d5cde0775dbe20b4d0b22a3e5f82ac64a050ead443f7248b1db23553689"
    with np.load("evidence/m5_reference_cycle.npz") as golden:
        golden_state=golden["state_cm3"].copy()
        golden_times=golden["time_s"].copy()
    runs={}
    audits={}
    for model in ("A0","A1"):
        with np.load(cache/f"downstream-{model}-run.npz") as data:
            np.testing.assert_array_equal(data["time"],golden_times)
            runs[model]=data["state"].copy()
            if not np.all(np.isfinite(runs[model])) or np.any(runs[model]<0):
                raise ValueError(f"nonphysical {model} trajectory")
            audits[model]=json.loads(str(data["audit"]))
            if model=="A1":
                assert bool(data["B_IRA_identical_A0"])
                initialization=json.loads(str(data["initialization"]))
                for level in initialization["levels"]:
                    assert sum(seed["passed"] for seed in level["seeds"])>=3
                    assert level["root_relative_spread"]<=1e-4
    sensitivity=downstream_stats(runs["A0"],runs["A1"],golden_times)
    a0_regression=trajectory_difference(golden_state,runs["A0"])
    assert a0_regression["pass_"]
    trajectories={}
    geometry_audits={}
    for geometry,method in (("golden","tight"),("real","base"),("real","tight"),("real","Radau")):
        with np.load(cache/f"m5b-{geometry}-{method}.npz") as data:
            np.testing.assert_array_equal(data["time_s"],golden_times-43200)
            trajectories[geometry,method]=data["state_cm3"].copy()
            assert np.all(np.isfinite(data["state_cm3"])) and np.all(data["state_cm3"]>=0)
        geometry_audits[f"{geometry}-{method}"]=json.loads(
            (cache/f"m5b-{geometry}-{method}-audit.json").read_text())
    reference=trajectory_difference(golden_state,trajectories["golden","tight"])
    convergence={"base_tight":trajectory_difference(trajectories["real","tight"],trajectories["real","base"]),
                 "tight_Radau":trajectory_difference(trajectories["real","tight"],trajectories["real","Radau"])}
    assert reference["pass_"] and all(item["pass_"] for item in convergence.values())
    for audit in (*audits.values(),*geometry_audits.values()):
        for metric in ("retained_QSSA_scaled_max","family_budget_scaled_max","dynamic_H2O2_budget_scaled_max"):
            assert audit[metric]<=1e-12
    small=all(sensitivity[name]["all_heights"]["max_relative"]<=.01 for name in ("O3","Delta"))
    return dict(decision="GO M5B",M4D_decision="CLOSED / ACCEPTED for temporal model" if small else
                "Downstream difference over 1%; quantify materiality before closure",
                downstream=sensitivity,A0_golden_regression=a0_regression,
                M5B_golden_regression=reference,real_geometry_solver_comparison=convergence,
                downstream_audits=audits,geometry_audits=geometry_audits,
                A1_initialization=initialization,
                golden_npz_sha256=hashlib.sha256(Path("evidence/m5_reference_cycle.npz").read_bytes()).hexdigest())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode",choices=("downstream","geometry","nir","assess"),required=True)
    parser.add_argument("--sources",type=Path)
    parser.add_argument("--hitran",type=Path)
    parser.add_argument("--cache",type=Path,default=Path(".m5-derived-cache"))
    parser.add_argument("--a-model",choices=("A0","A1"),default="A0")
    parser.add_argument("--geometry",choices=("golden","real"),default="real")
    parser.add_argument("--solver",choices=("base","tight","Radau"),default="tight")
    args=parser.parse_args()
    if args.mode=="assess":
        print(json.dumps(assess(args),indent=2))
        return 0
    if args.sources is None or args.hitran is None:
        parser.error("reproduction requires --sources and the authorized --hitran export")
    args.cache.mkdir(parents=True,exist_ok=True)
    args.minimum_sza=0. if args.mode=="nir" else 45.
    table,nir=prepare_nir(args)
    if args.mode=="nir":
        np.savez_compressed(args.cache/"m5b-universal-nir.npz",sza=table.sza_deg,
                             rates=table.rates_s1,audit=json.dumps(nir))
        print(json.dumps(dict(decision="PASS full-SZA frozen NIR",audit=nir)))
        return 0
    controls=dict(method="Radau" if args.solver=="Radau" else "BDF",
                  rtol=2e-6 if args.solver=="base" else 2e-8,
                  atol=1e-8 if args.solver=="base" else 1e-10,
                  max_step_s=120. if args.solver=="base" else 60.)
    with np.load("evidence/m5_reference_cycle.npz") as g:
        initial=g["state_cm3"][0].copy()
        times=g["time_s"].copy()
    if args.mode=="downstream":
        if args.solver!="tight":
            parser.error("downstream comparison uses identical tighter BDF controls")
        advanced_table = table
        if args.a_model=="A1":
            baseline_args=argparse.Namespace(**vars(args))
            baseline_args.a_model="A0"
            baseline,_=prepare_nir(baseline_args)
            table=A1OnlyNIR(baseline,advanced_table)
        rhs=DynamicPeroxideColumnRHS(table)
        initial,record=reference_noon_initialization(rhs)
        controls["atol_log"]=controls.pop("atol")
        time,state,stats=integrate_reference_noon_to_dawn(rhs,initial,**controls)
        audit=retained_closure_audit(rhs,time,state)
        np.savez_compressed(args.cache/f"downstream-{args.a_model}-nir.npz",
            sza=advanced_table.sza_deg,rates=advanced_table.rates_s1,audit=json.dumps(nir))
        np.savez_compressed(args.cache/f"downstream-{args.a_model}-run.npz",time=time,state=state,
            initial=initial,initialization=json.dumps(record),audit=json.dumps(audit),stats=json.dumps(stats),
            B_IRA_identical_A0=True)
    else:
        if args.a_model!="A0":
            parser.error("M5B reference geometry validation uses accepted A0/B/IRA")
        start=datetime(2020,3,20,12,tzinfo=timezone.utc)
        clock=ReferenceElapsedGeometry() if args.geometry=="golden" else None
        result=simulate(start,start+timedelta(hours=21),45,0,initial,nir_provider=table,
                        geometry=clock,output_times_s=times-43200,**controls,
                        initialization_metadata={"policy":"explicit M5A golden noon state"})
        result.save(args.cache/f"m5b-{args.geometry}-{args.solver}.npz")
        rhs=DynamicPeroxideColumnRHS(table,cycle=clock if clock else DatetimeSolarGeometry(start,45,0))
        audit=retained_closure_audit(rhs,result.time_s,result.state_cm3)
        audit.update(solver=result.metadata["solver"],NIR=nir)
        (args.cache/f"m5b-{args.geometry}-{args.solver}-audit.json").write_text(json.dumps(audit,indent=2))
    print(json.dumps(dict(decision="PASS individual trajectory; run assess for combined decision",audit=audit)))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
