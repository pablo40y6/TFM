"""M5C NIR snapshots using unchanged accepted M4D A0/B/IRA equations."""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
from concurrent.futures import ThreadPoolExecutor
from functools import cache
from pathlib import Path
from types import FunctionType
from uuid import uuid4

import numpy as np
from scipy.optimize import minimize_scalar

from .dynamic_atmosphere import _time_within_coverage
from .m4d_reconstruction.cia import load_cia
from .m4d_reconstruction.sources import load_bands, load_solar, load_tips
from .m4d_reconstruction.spectroscopy import K_B, SpectralSources
from .m4d_reconstruction.transfer import Atmosphere, VoigtColumn, compute_classic_rates
from .m5_simulation import frozen_reference_nir
from .m5_temporal import NIRForcingTable, _reference_shell_paths


@cache
def _nominal_code():
    """Scope the frozen evaluator to its nominal outputs, without equation edits.

    M5 does not consume historical CIA envelope/raw diagnostics. Compile the
    accepted function after removing only those unused evaluations. Tests compare
    every retained array bit for bit with the complete original evaluator.
    """
    tree=ast.parse(inspect.getsource(compute_classic_rates))
    counts=[0,0,0]
    class NominalOnly(ast.NodeTransformer):
        def visit_AugAssign(self,node):
            if isinstance(node.target,ast.Name) and node.target.id=='names':
                node.value.elts=[v for v in node.value.elts if v.value=='cia_nominal']
                counts[0]+=1
            return self.generic_visit(node)

        def visit_Assign(self,node):
            if len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
                name=node.targets[0].id
                if name=='raw':
                    counts[1]+=1
                    return None
                if name=='tau_cia':
                    pairs=[(k,v) for k,v in zip(node.value.keys,node.value.values,strict=True)
                           if k.value=='cia_nominal']
                    node.value.keys=[k for k,v in pairs]
                    node.value.values=[v for k,v in pairs]
                    counts[2]+=1
            return self.generic_visit(node)
    NominalOnly().visit(tree)
    if counts!=[1,1,1]:
        raise RuntimeError('accepted transfer structure changed; nominal specialization not verified')
    namespace=dict(compute_classic_rates.__globals__)
    exec(compile(ast.fix_missing_locations(tree),inspect.getfile(compute_classic_rates),'exec'),namespace)
    return namespace['compute_classic_rates'].__code__


def snapshot_transfer(background,*,nominal_only=False):
    """Private namespace injection; accepted transfer code/parameters unchanged."""
    def shells(step):
        source=background.radiative
        edges=np.linspace(0,150,round(150/step)+1)
        mids=(edges[1:]+edges[:-1])/2
        T=np.interp(mids,source.z_km,source.T_K)
        M=np.interp(mids,source.z_km,source.M_cm3)
        O2=np.interp(mids,source.z_km,source.O2_model_cm3)
        N2=np.interp(mids,source.z_km,source.N2_model_cm3)
        return Atmosphere(edges,T,M*1e6*K_B*T/101325,O2*1e6*K_B*T/101325,O2,N2)
    namespace=dict(compute_classic_rates.__globals__)
    namespace.update(atmosphere=shells,load_baseline_background=lambda:background)
    code=_nominal_code() if nominal_only else compute_classic_rates.__code__
    return FunctionType(code,namespace,
                         compute_classic_rates.__name__,compute_classic_rates.__defaults__)


class HistoricalNIRInputs:
    """Explicit authorized local source locations, never downloaded by runtime."""
    def __init__(self,sources,hitran):
        self.sources=Path(sources)
        self.hitran=Path(hitran)
        self.bands=load_bands(self.hitran)
        self.spectral=SpectralSources(*load_tips(self.sources/'hapi.py'),
                                     load_solar(self.sources/'wehrli85.txt'))
        self.cia=load_cia(self.sources/'O2-O2_2011.cia')


class DynamicNIRForcing:
    """Time-interpolated snapshot angular tables; exact height shadow at queries.

    Atmosphere snapshots are precomputed; no transfer calculation or source I/O
    occurs in the chemistry RHS. Every table uses direct M4D rates and a direct
    midpoint angular audit. Temporal refinement is assessed on chemical output.
    """
    def __init__(self,atmosphere,geometry,inputs,*,cache=None,progress=None):
        self.atmosphere,self.geometry,self.inputs=atmosphere,geometry,inputs
        self.cache=None if cache is None else Path(cache)
        if self.cache is not None:
            self.cache.mkdir(parents=True,exist_ok=True)
        self.tables=[]
        self.audits=[]
        standard=frozen_reference_nir().sza_deg
        for i,t in enumerate(atmosphere.times):
            a=atmosphere.times[max(0,i-1)]
            b=atmosphere.times[min(i+1,len(atmosphere.times)-1)]
            grid=np.linspace(a,b,25)
            angles=geometry.sza(grid)
            minimum=min(float(angles.min()),float(minimize_scalar(geometry.sza,bounds=(a,b),method='bounded').fun))
            maximum=max(float(angles.max()),float(-minimize_scalar(lambda x:-geometry.sza(x),bounds=(a,b),method='bounded').fun))
            maximum=min(maximum,float(standard[-1]))
            if minimum>standard[-1]:
                table=NIRForcingTable([standard[-1],180.],np.zeros((2,51,3)))
                audit=dict(nodes=2,relative_max=0.,near_zero_absolute_max_s1=0.,dark=True)
            else:
                lo=max(0,int(np.searchsorted(standard,minimum))-1)
                hi=min(len(standard),int(np.searchsorted(standard,maximum,side='right'))+1)
                nodes=standard[lo:max(hi,lo+2)].tolist()
                table,audit=self._build(atmosphere.at(float(t)),nodes)
            self.tables.append(table)
            self.audits.append(audit)
            if progress:
                progress(i+1,len(atmosphere.times),audit)

    def _build(self,background,nodes):
        transfer=snapshot_transfer(background,nominal_only=True)
        # Exact per-snapshot reuse across midpoint refinements; no interpolated
        # spectral profile, dropped line, or changed quadrature. Bound memory.
        opacity={}
        templates={}
        memory=[0]
        class ReusedColumn(VoigtColumn):
            def __post_init__(self):
                self.identity=(len(self.lines),self.lines[0].nu,
                               None if self.used_shells is None else self.used_shells.tobytes())
                if self.identity in templates:
                    self.__dict__.update(templates[self.identity].__dict__)
                else:
                    super().__post_init__()
                    templates[self.identity]=self

            def cross_section(self,nodes,order=8,near_cm1=2.,exact=False):
                key=(self.identity,order,near_cm1,exact,nodes.tobytes())
                if key not in opacity:
                    result=super().cross_section(nodes,order,near_cm1,exact)
                    if memory[0]+result.nbytes<=1_500_000_000:
                        result.setflags(write=False)
                        opacity[key]=result
                        memory[0]+=result.nbytes
                    return result
                return opacity[key]
        transfer.__globals__['VoigtColumn']=ReusedColumn
        known={}
        modes={}
        digest=hashlib.sha256(b'M5C accepted A0/B/IRA snapshot; .125/64/12/3.84/far4/CIA.0625')
        for name in ('T_K','M_cm3','O2_model_cm3','N2_model_cm3'):
            digest.update(np.ascontiguousarray(getattr(background.radiative,name)).tobytes())
        for p in Path(__file__).parent.joinpath('m4d_reconstruction').glob('*.py'):
            digest.update(p.read_bytes())
        path=None if self.cache is None else self.cache/(digest.hexdigest()+'.optimized.npz')
        reference_path=None if self.cache is None else self.cache/(digest.hexdigest()+'.npz')
        load_path=path if path is not None and path.exists() else reference_path
        if load_path is not None and load_path.exists():
            with np.load(load_path) as f:
                known.update(zip(map(float,f['sza']),f['rates'],strict=True))
                mode=f['mode'] if 'mode' in f else np.zeros(len(f['sza']),dtype=int)
                modes.update(zip(map(float,f['sza']),map(int,mode),strict=True))
        def evaluate(angles):
            missing=[float(a) for a in angles if float(a) not in known]
            if missing:
                cases=[(float(z),sza) for sza in missing for z in range(50,101)]
                def rate(band):
                    result=transfer(self.inputs.bands[band],self.inputs.spectral,cases,
                                    far_order=8,near_cm1=.25,
                                    cia=self.inputs.cia if band=='IRA' else None)
                    return result['cia_nominal' if band=='IRA' else 'monomer']
                with ThreadPoolExecutor(max_workers=3) as pool:
                    columns=list(pool.map(rate,('A','B','IRA')))
                values=np.column_stack(columns).reshape(len(missing),51,3)
                known.update(zip(missing,values,strict=True))
                modes.update((angle,1) for angle in missing)
                if path is not None:
                    ordered=sorted(known)
                    temporary=path.with_suffix('.'+uuid4().hex+'.tmp')
                    with temporary.open('wb') as stream:
                        np.savez_compressed(stream,sza=ordered,rates=np.array([known[a] for a in ordered]),
                                            mode=np.array([modes[a] for a in ordered]))
                    temporary.replace(path)
            return np.array([known[float(a)] for a in angles])
        for _ in range(10):
            mid=(np.array(nodes[1:])+nodes[:-1])/2
            evaluate(np.r_[nodes,mid])
            rates=evaluate(nodes)
            table=NIRForcingTable(nodes,rates)
            actual=evaluate(mid)
            approximate=np.array([table(a) for a in mid])
            delta=abs(actual-approximate)
            floor=np.maximum(1e-15,1e-4*np.max(rates,axis=(0,1)))
            relevant=np.maximum(actual,approximate)>floor
            relative=np.divide(delta,np.maximum(actual,floor),out=np.zeros_like(delta),where=relevant)
            bad=np.any((relevant&(relative>.005))|(~relevant&(delta>1e-15)),axis=(1,2))
            audit=dict(nodes=len(nodes),relative_max=float(relative.max()),
                near_zero_absolute_max_s1=float(np.max(np.where(relevant,0.,delta))),dark=False,
                cached_reference_nodes=sum(modes[float(a)]==0 for a in nodes),
                optimized_nodes=sum(modes[float(a)]==1 for a in nodes))
            if not np.any(bad):
                # The private subclass/parameter templates form a reference cycle.
                # Free large exact-opacity buffers before the next atmosphere.
                opacity.clear()
                templates.clear()
                return table,audit
            nodes=sorted(set(nodes+mid[bad].tolist()))
        opacity.clear()
        templates.clear()
        raise RuntimeError('dynamic NIR angular interpolation does not converge to 0.5%')

    def __call__(self,time_s,sza_deg):
        times=self.atmosphere.times
        time_s = _time_within_coverage(time_s, times[0], times[-1])
        if time_s<times[0] or time_s>times[-1]:
            raise ValueError('dynamic NIR time outside precomputed coverage')
        i=min(int(np.searchsorted(times,time_s,side='right'))-1,len(times)-2)
        w=(time_s-times[i])/(times[i+1]-times[i])
        value=(1-w)*self.tables[i](sza_deg)+w*self.tables[i+1](sza_deg)
        value[~_reference_shell_paths(sza_deg).illuminated]=0.
        return value

    def metadata(self):
        return dict(policy='dynamic background A0/B/IRA snapshot tables; no frozen-NIR substitution',
            atmosphere_step_s=self.atmosphere.step_s,angular_audits=self.audits,
            temporal_interpolation='linear rates between adjacent atmospheres at actual SZA',
            numerics=dict(fresh_far_order=8,fresh_near_cm1=.25,
                cached_reference='validated far_order=4 / near_cm1=2 direct rates; row provenance retained',
                outputs='nominal only; unused CIA envelope/raw evaluations omitted without equation changes'),
            raw_hitran_distributed=False,CIA='historical O2-Air attenuation only')

    def save(self,path):
        """Persist derived rates only, using numeric arrays and no pickle."""
        values=dict(times_s=self.atmosphere.times,
                    atmosphere_sha256=np.array(hashlib.sha256(self.atmosphere.raw.tobytes()).hexdigest()),
                    audits_json=np.array(json.dumps(self.audits)),
                    geometry_json=np.array(json.dumps(self.geometry.metadata())))
        for i,table in enumerate(self.tables):
            values[f'sza_{i}']=table.sza_deg
            values[f'rates_{i}']=table.rates_s1
        np.savez_compressed(path,**values)

    @classmethod
    def load(cls,path,atmosphere,geometry):
        """Explicit precomputed provider; reject a different atmosphere/geometry."""
        instance=cls.__new__(cls)
        instance.atmosphere,instance.geometry=atmosphere,geometry
        instance.inputs=None
        instance.cache=None
        with np.load(path,allow_pickle=False) as values:
            np.testing.assert_array_equal(values['times_s'],atmosphere.times)
            digest=hashlib.sha256(atmosphere.raw.tobytes()).hexdigest()
            if str(values['atmosphere_sha256'])!=digest:
                raise ValueError('precomputed NIR atmosphere identity mismatch')
            if json.loads(str(values['geometry_json']))!=geometry.metadata():
                raise ValueError('precomputed NIR geometry identity mismatch')
            instance.audits=json.loads(str(values['audits_json']))
            instance.tables=[NIRForcingTable(values[f'sza_{i}'],values[f'rates_{i}'])
                             for i in range(len(atmosphere.times))]
        if len(instance.audits)!=len(instance.tables) or any(
                a['relative_max']>.005 or a['near_zero_absolute_max_s1']>1e-15
                for a in instance.audits):
            raise ValueError('precomputed NIR angular audit failed')
        return instance
