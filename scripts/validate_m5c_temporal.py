"""Reproduce M5C without network data lookup or changes to accepted chemistry."""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from scripts.validate_m5_temporal import retained_closure_audit, trajectory_difference
from tfm_photochem.dynamic_atmosphere import DynamicMSISAtmosphere, background_from_msis
from tfm_photochem.dynamic_radiation import (
    DynamicNIRForcing,
    HistoricalNIRInputs,
    snapshot_transfer,
)
from tfm_photochem.m4d_reconstruction.transfer import VoigtColumn
from tfm_photochem.m5_dynamic import (
    DynamicAtmosphereColumnRHS,
    dynamic_reference_noon_initialization,
    previous_solar_noon,
)
from tfm_photochem.m5_simulation import frozen_reference_nir, simulate
from tfm_photochem.solar_geometry import DatetimeSolarGeometry

START=datetime(2020,3,20,12,tzinfo=timezone.utc)
END=START+timedelta(hours=21)


def numerical_audit(inputs,cache):
    """Independent exact Voigt cross sections and complete retained rate witnesses."""
    from tfm_photochem.historical_2020.background import load_baseline_background
    profiles=[]
    noon=[]
    for path in sorted(cache.glob('initializer-*.npz')):
        with np.load(path,allow_pickle=False) as data:
            bg=background_from_msis(data['raw'][0],{})
            reference=data['nir_rates_s1'].copy()
            record=json.loads(str(data['record']))
        original=snapshot_transfer(bg)
        nominal=snapshot_transfer(bg,nominal_only=True)
        shell=original.__globals__['atmosphere'](.125)
        mask=np.zeros(1200,dtype=bool)
        mask[[0,1,7,63,119,239,399,599,799,959,1199]]=True
        for band in ('A','B','IRA'):
            lines=inputs.bands[band]
            centres=np.array([line.nu for line in lines])
            nodes=np.unique(np.r_[centres,centres-.249999,centres+.249999,
                centres-.250001,centres+.250001,(centres[:-1]+centres[1:])/2])
            column=VoigtColumn(lines,inputs.spectral,shell,used_shells=mask)
            exact=column.cross_section(nodes,exact=True)
            approximate=column.cross_section(nodes,order=8,near_cm1=.25)
            relative=abs(exact-approximate)/np.maximum(exact,1e-8*exact.max(axis=0))
            profiles.append(dict(case=path.stem,band=band,nodes=len(nodes),shells=int(mask.sum()),
                relative_max=float(relative.max()),approx_min=float(approximate.min())))
            assert relative.max()<=.0005 and approximate.min()>=0
        cases=[(float(z),record['SZA_deg']) for z in range(50,101)]
        def rate(band):
            result=nominal(inputs.bands[band],inputs.spectral,cases,far_order=8,near_cm1=.25,
                           cia=inputs.cia if band=='IRA' else None)
            return result['cia_nominal' if band=='IRA' else 'monomer']
        with ThreadPoolExecutor(max_workers=3) as pool:
            trial=np.column_stack(list(pool.map(rate,('A','B','IRA'))))
        floor=np.maximum(1e-15,1e-4*reference.max(axis=0))
        relative=abs(reference-trial)/np.maximum(reference,floor)
        noon.append(dict(case=path.stem,relative_max_by_band=relative.max(axis=0).tolist()))
        assert relative.max()<=.0005
    if len(noon)<5:
        raise ValueError('numerical certification needs all five initializer background cases')
    frozen=frozen_reference_nir()
    angles=[float(frozen.sza_deg[np.argmin(abs(frozen.sza_deg-s))]) for s in (95.,97.,99.)]
    cases=[(float(z),angle) for angle in angles for z in range(50,101)]
    transfer=snapshot_transfer(load_baseline_background(),nominal_only=True)
    def rate(band):
        result=transfer(inputs.bands[band],inputs.spectral,cases,far_order=8,near_cm1=.25,
                        cia=inputs.cia if band=='IRA' else None)
        return result['cia_nominal' if band=='IRA' else 'monomer']
    with ThreadPoolExecutor(max_workers=3) as pool:
        trial=np.column_stack(list(pool.map(rate,('A','B','IRA')))).reshape(3,51,3)
    reference=np.array([frozen(angle) for angle in angles])
    floor=np.maximum(1e-15,1e-4*reference.max(axis=(0,1)))
    relative=abs(reference-trial)/np.maximum(reference,floor)
    assert relative.max()<=.0005
    return dict(exact_profiles=profiles,complete_noon_profiles=noon,
        twilight=dict(SZA_deg=angles,relative_max_by_band=relative.max(axis=(0,1)).tolist()),
        internal_tolerance=.0005,decision='PASS numerical optimization; physical model unchanged')


def load_background(cache,step):
    path=cache/f'atmosphere-{step:g}.npz'
    raw=None
    if path.exists():
        with np.load(path,allow_pickle=False) as data:
            raw=data['raw'].copy()
    provider=DynamicMSISAtmosphere(START,END,45,0,step_s=step,raw=raw)
    if raw is None:
        np.savez_compressed(path,raw=provider.raw,times_s=provider.times)
    return provider


def compare_outputs(a,b,times,sza):
    """Relevant relative and near-zero absolute differences, including dawn."""
    results={}
    for index,name in ((1,'O3'),(6,'Delta')):
        floor=max(1.,1e-6*float(np.max(a[:,:,index])))
        cases={}
        for selection,label in ((np.ones(len(times),dtype=bool),'full'),
                                ((times>43200)&(sza<=99)&(sza>=60),'dawn')):
            x,y=a[selection,:,index],b[selection,:,index]
            absolute=abs(x-y)
            relevant=np.maximum(x,y)>floor
            relative=np.divide(absolute,np.maximum(x,y),out=np.zeros_like(x),where=relevant)
            values=relative[relevant]
            maximum=np.unravel_index(np.argmax(relative),relative.shape)
            rows=np.flatnonzero(selection)
            cases[label]=dict(max_relative=float(values.max()) if values.size else 0.,
                p90_relative=float(np.percentile(values,90)) if values.size else 0.,
                p99_relative=float(np.percentile(values,99)) if values.size else 0.,
                maximum_absolute_cm3=float(absolute.max()),
                near_zero_absolute_max_cm3=float(np.max(np.where(relevant,0.,absolute))),
                floor_cm3=floor,maximum_case=dict(time_s=float(times[rows[maximum[0]]]),
                z_km=int(50+maximum[1]),SZA_deg=float(sza[rows[maximum[0]]])))
        results[name]=cases
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=('prepare','run','bootstrap','initializer','numerics','assess','cases'),required=True)
    parser.add_argument('--sources',type=Path)
    parser.add_argument('--hitran',type=Path)
    parser.add_argument('--cache',type=Path,required=True)
    parser.add_argument('--step',type=float,default=3600.)
    parser.add_argument('--nir-step',type=float,default=None)
    parser.add_argument('--solver',choices=('base','tight','Radau'),default='tight')
    parser.add_argument('--comparison-step',type=float,default=7200.)
    parser.add_argument('--comparison-nir-step',type=float,default=7200.)
    parser.add_argument('--start',type=datetime.fromisoformat,default=START+timedelta(hours=2))
    parser.add_argument('--latitude',type=float,default=45.)
    parser.add_argument('--longitude',type=float,default=0.)
    args=parser.parse_args()
    args.cache.mkdir(parents=True,exist_ok=True)
    if args.mode=='cases':
        if args.sources is None or args.hitran is None:
            parser.error('cases needs authorized local --sources and --hitran')
        run_validation_cases(HistoricalNIRInputs(args.sources,args.hitran),args.cache)
        return
    if args.mode=='numerics':
        if args.sources is None or args.hitran is None:
            parser.error('numerics needs authorized local --sources and --hitran')
        inputs=HistoricalNIRInputs(args.sources,args.hitran)
        report=numerical_audit(inputs,args.cache)
        (args.cache/'numerical-audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
        print(json.dumps(report,indent=2))
        return
    if args.mode=='initializer':
        if args.sources is None or args.hitran is None:
            parser.error('initializer needs authorized local --sources and --hitran')
        noon=previous_solar_noon(args.start,args.longitude)
        provider=DynamicMSISAtmosphere(noon,noon+timedelta(seconds=300),args.latitude,args.longitude)
        clock=DatetimeSolarGeometry(noon,args.latitude,args.longitude)
        angle=float(clock.sza(0.))
        inputs=HistoricalNIRInputs(args.sources,args.hitran)
        transfer=snapshot_transfer(provider.at(0.))
        cases=[(float(z),angle) for z in range(50,101)]
        def rate(band):
            result=transfer(inputs.bands[band],inputs.spectral,cases,far_order=4,
                            cia=inputs.cia if band=='IRA' else None)
            return result['cia_nominal' if band=='IRA' else 'monomer']
        with ThreadPoolExecutor(max_workers=3) as pool:
            rates=np.column_stack(list(pool.map(rate,('A','B','IRA'))))
        # Fixed noon forcing only for the stationary t0 preflight, never evolution.
        rhs=DynamicAtmosphereColumnRHS(provider,lambda t,s:rates,clock)
        state,record=dynamic_reference_noon_initialization(rhs)
        name=f'initializer-{noon:%Y%m%d}-{args.latitude:g}-{args.longitude:g}.npz'
        np.savez_compressed(args.cache/name,state_cm3=state,nir_rates_s1=rates,
                            record=json.dumps(record),raw=provider.raw)
        print(json.dumps(record))
        return
    if args.mode=='assess':
        if args.nir_step is not None:
            certify_independent_grids(args)
            return
        runs={}
        for step,solver in ((3600.,'base'),(3600.,'tight'),(3600.,'Radau'),(args.comparison_step,'tight')):
            with np.load(args.cache/f'run-{step:g}-{solver}.npz',allow_pickle=False) as data:
                runs[step,solver]=data['state_cm3'].copy()
                times=data['time_s'].copy()
                sza=data['sza_deg'].copy()
        temporal=compare_outputs(runs[3600.,'tight'],runs[args.comparison_step,'tight'],times,sza)
        solver={key:trajectory_difference(runs[3600.,'tight'],runs[3600.,method])
                for key,method in (('BDF_base_tight','base'),('BDF_Radau','Radau'))}
        temporal_pass=all(v['full']['max_relative']<=.005 and
            v['full']['near_zero_absolute_max_cm3']<=.005*v['full']['floor_cm3']
            for v in temporal.values())
        with np.load('evidence/m5b_reference_real_geometry.npz',allow_pickle=False) as golden:
            np.testing.assert_array_equal(times,golden['time_s'])
            sensitivity=compare_outputs(golden['state_cm3'],runs[3600.,'tight'],times,sza)
        report=dict(decision='GO candidate; bootstrap/case/regression QA also required'
                    if temporal_pass and all(v['pass_'] for v in solver.values()) else
                    'NUMERICAL CONVERGENCE BLOCKER; refine before scientific diagnosis',
                    background_convergence=temporal,solver_comparison=solver,
                    frozen_vs_dynamic=sensitivity)
        (args.cache/'assessment.json').write_text(json.dumps(report,indent=2),encoding='utf8')
        print(json.dumps(report,indent=2))
        return
    provider=load_background(args.cache,args.step)
    clock=DatetimeSolarGeometry(START,45,0)
    nir_step=args.step if args.nir_step is None else args.nir_step
    snapshots=provider if nir_step==args.step else provider.sampled(nir_step)
    path=args.cache/f'nir-{nir_step:g}.npz'
    if args.mode=='prepare':
        if args.sources is None or args.hitran is None:
            parser.error('prepare needs authorized local --sources and --hitran')
        inputs=HistoricalNIRInputs(args.sources,args.hitran)
        nir=DynamicNIRForcing(snapshots,clock,inputs,cache=args.cache/'nir',
            progress=lambda i,n,a:print(json.dumps(dict(snapshot=i,total=n,audit=a)),flush=True))
        nir.save(path)
        return
    nir=DynamicNIRForcing.load(path,snapshots,clock)
    controls=dict(method='Radau' if args.solver=='Radau' else 'BDF',
        rtol=2e-6 if args.solver=='base' else 2e-8,
        atol=1e-8 if args.solver=='base' else 1e-10,
        max_step_s=120. if args.solver=='base' else 60.)
    if args.mode=='bootstrap':
        # Previous apparent noon lies inside the precomputed reference coverage.
        a=args.start
        b=END
        if not START<a<b:
            parser.error('reference bootstrap start must lie inside precomputed coverage')
        result=simulate(a,b,45,0,initialization='reference_noon',atmosphere='dynamic_msis',
            atmosphere_provider=provider,dynamic_nir=nir,output_step_s=300.,**controls,
            progress=lambda t,n,s:print(json.dumps(dict(time_s=t,nfev=n,SZA=s)),flush=True))
        result.save(args.cache/'bootstrap-reference.npz')
        record=result.metadata['initialization']
        print(json.dumps({key:value for key,value in record.items() if key!='levels'}))
        return
    with np.load('evidence/m5b_reference_real_geometry.npz',allow_pickle=False) as golden:
        state=golden['state_cm3'][0].copy()
        times=golden['time_s'].copy()
    result=simulate(START,END,45,0,state,atmosphere='dynamic_msis',
        atmosphere_provider=provider,dynamic_nir=nir,output_times_s=times,**controls,
        initialization_metadata={'policy':'explicit identical M5B golden noon state; atmosphere sensitivity only',
                                 'source':'evidence/m5b_reference_real_geometry.npz'},
        progress=lambda t,n,s:print(json.dumps(dict(time_s=t,nfev=n,SZA=s)),flush=True))
    rhs=DynamicAtmosphereColumnRHS(provider,nir,clock)
    audit=retained_closure_audit(rhs,result.time_s,result.state_cm3)
    audit.update(msis_calls=provider.msis_calls,solver=result.metadata['solver'],
                 finite_nonnegative=bool(np.all(np.isfinite(result.state_cm3)) and np.all(result.state_cm3>=0)),
                 no_clipping=True)
    suffix=f'{args.step:g}-{args.solver}' if args.nir_step is None else f'{args.step:g}-nir{nir_step:g}-{args.solver}'
    result.save(args.cache/f'run-{suffix}.npz')
    (args.cache/f'audit-{suffix}.json').write_text(json.dumps(audit,indent=2),encoding='utf8')
    print(json.dumps(audit))


def certify_independent_grids(args):
    """Separate native atmosphere and NIR rate interpolation errors."""
    def load(step,nir,solver):
        with np.load(args.cache/f'run-{step:g}-nir{nir:g}-{solver}.npz',allow_pickle=False) as data:
            return data['state_cm3'].copy(),data['time_s'].copy(),data['sza_deg'].copy()
    reference,times,sza=load(args.step,args.nir_step,'tight')
    comparisons={}
    for name,step,nir in (('native_atmosphere',args.comparison_step,args.nir_step),
                          ('NIR_rates',args.step,args.comparison_nir_step)):
        trial,t,s=load(step,nir,'tight')
        np.testing.assert_array_equal(t,times)
        np.testing.assert_array_equal(s,sza)
        comparisons[name]=compare_outputs(reference,trial,times,sza)
    solvers={}
    for method in ('base','Radau'):
        trial,t,s=load(args.step,args.nir_step,method)
        np.testing.assert_array_equal(t,times)
        np.testing.assert_array_equal(s,sza)
        solvers[method]=trajectory_difference(reference,trial)
    numerical_pass=all(v['full']['max_relative']<=.005 and
        v['full']['near_zero_absolute_max_cm3']<=.005*v['full']['floor_cm3']
        for comparison in comparisons.values() for v in comparison.values())
    with np.load('evidence/m5b_reference_real_geometry.npz',allow_pickle=False) as golden:
        np.testing.assert_array_equal(times,golden['time_s'])
        sensitivity=compare_outputs(golden['state_cm3'],reference,times,sza)
    report=dict(decision='PASS numerical convergence; case/regression QA also required'
        if numerical_pass and all(s['pass_'] for s in solvers.values()) else
        'REFINE numerical grids before closure',background_step_s=args.step,
        NIR_step_s=args.nir_step,background_convergence=comparisons,
        solver_comparison=solvers,frozen_vs_dynamic=sensitivity)
    (args.cache/'refined-assessment.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2))


def run_validation_cases(inputs,cache):
    """Five actual MSIS/noon-root/bootstrap/integration smoke cases (not climatology)."""
    cases=[('equinox',START+timedelta(hours=1),45,0),
           ('summer',START.replace(month=6,day=21,hour=13),45,0),
           ('south',START.replace(month=12,day=21,hour=13),-45,0),
           ('longitude',START.replace(hour=18),45,-75),
           ('high_latitude',START.replace(month=6,day=21,hour=13),70,0)]
    records=[]
    for name,date,lat,lon in cases:
        noon=previous_solar_noon(date,lon)
        start,end=noon+timedelta(seconds=60),noon+timedelta(seconds=180)
        provider=DynamicMSISAtmosphere(noon,end,lat,lon,step_s=300.)
        clock=DatetimeSolarGeometry(noon,lat,lon)
        nir=DynamicNIRForcing(provider,clock,inputs,cache=cache/'nir')
        result=simulate(start,end,lat,lon,initialization='reference_noon',
            atmosphere='dynamic_msis',atmosphere_provider=provider,dynamic_nir=nir,
            method='BDF',rtol=2e-8,atol=1e-10,max_step_s=30.,output_step_s=20.)
        result.save(cache/f'case-{name}.npz')
        rhs=DynamicAtmosphereColumnRHS(provider,nir,DatetimeSolarGeometry(start,lat,lon),offset_s=60.)
        audit=retained_closure_audit(rhs,result.time_s,result.state_cm3)
        record=dict(case=name,latitude_deg=lat,longitude_deg=lon,noon_utc=noon.isoformat(),
            minimum_state_cm3=float(result.state_cm3.min()),
            finite_nonnegative=bool(np.all(np.isfinite(result.state_cm3)) and np.all(result.state_cm3>=0)),
            initializer=result.metadata['initialization'],audit=audit,msis_calls=provider.msis_calls)
        records.append(record)
        (cache/'case-simulations.json').write_text(json.dumps(records,indent=2),encoding='utf8')
        print(json.dumps(dict(case=name,finite_nonnegative=record['finite_nonnegative'],audit=audit)),flush=True)


if __name__=='__main__':
    main()
