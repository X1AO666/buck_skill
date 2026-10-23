#!/usr/bin/env python3
"""Independent ideal switched-circuit comparison; requires optional SciPy.

Uses coupled state equations, not assumed triangular capacitor current.
The two-state CCM candidate is rejected as a diode-buck solution if iL <= 0.
No automatic L/C correction, DCM integration, controller or real parasitics.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import expm
from scipy.optimize import brentq


def switched_solution(Vin, R, fs, L, C, Vo, rtol=1e-10):
    """Periodic state via affine matrix maps, then independent IVP integration.

    Equations: di/dt=(u*Vin-v)/L; dv/dt=(i-v/R)/C.
    A normalized time coordinate s=t/T avoids tiny time intervals.
    Integrating i and v also verifies their DC averages without ripple formulas.
    """
    T=1/fs; duty=Vo/Vin
    A=np.array([[0.,-1/L],[1/C,-1/(R*C)]])*T
    b=np.array([Vin/L,0.])*T
    def affine(duration, u):
        M=np.zeros((3,3)); M[:2,:2]=A; M[:2,2]=u*b
        E=expm(M*duration)
        return E[:2,:2],E[:2,2]
    on,gon=affine(duty,1); off,goff=affine(1-duty,0)
    F=off@on; g=off@gon+goff
    start=np.linalg.solve(np.eye(2)-F,g)
    def rhs(u):
        def fun(s,x):
            dx=A@x[:2]+u*b
            return [dx[0],dx[1],x[0],x[1]]
        return fun
    x=np.r_[start,0.,0.]
    segments=[]
    for left,right,u in ((0,duty,1),(duty,1,0)):
        fun=rhs(u)
        sol=solve_ivp(fun,(left,right),x,method='DOP853',rtol=rtol,
                      atol=rtol*1e-3,max_step=(right-left)/100,dense_output=True)
        if not sol.success: raise RuntimeError(sol.message)
        segments.append((left,right,u,sol)); x=sol.y[:,-1]
    ts=[]; ys=[]; critical=[[],[]]
    for left,right,u,sol in segments:
        mesh=np.linspace(left,right,1001)
        values=sol.sol(mesh)
        ts.append(mesh); ys.append(values[:2])
        deriv=A@values[:2]+(u*b)[:,None]
        for component in (0,1):
            critical[component].extend([float(values[component,0]),float(values[component,-1])])
            for j in np.flatnonzero(deriv[component,:-1]*deriv[component,1:]<0):
                zero=brentq(lambda s: float((A@sol.sol(s)[:2]+u*b)[component]),mesh[j],mesh[j+1],xtol=1e-14)
                critical[component].append(float(sol.sol(zero)[component]))
    t=np.concatenate(ts); y=np.concatenate(ys,axis=1)
    minimum_i=min(critical[0]); maximum_i=max(critical[0])
    dvo=max(critical[1])-min(critical[1]); dil=maximum_i-minimum_i
    mean_i=float(x[2]); mean_v=float(x[3])
    scale=np.array([max(abs(Vo/R),1e-12),max(abs(Vo),1e-12)])
    residual=float(np.max(np.abs(x[:2]-start)/scale))
    metrics={'mean_i_A':mean_i,'mean_v_V':mean_v,'dIL_A':dil,'dVo_V':dvo,
             'min_i_A':minimum_i,'rL':dil/mean_i,'rv':dvo/mean_v,
             'positive_valley':minimum_i>0,'periodic_residual_scaled':residual,
             'mean_v_relative_error':abs(mean_v-Vo)/Vo}
    return metrics,(t*T,y)


def compare_case(data, output_dir):
    # Import is confined to obtaining the assignment's selected L/C and predictions.
    # The reference state solver above never calls the sizing or ripple formulas.
    spec=importlib.util.spec_from_file_location('sizing',Path(__file__).with_name('design_buck.py'))
    model=importlib.util.module_from_spec(spec); spec.loader.exec_module(model)
    vmin,vmax=model.validate(data); result=model.design(data,vmin,vmax)
    folder=Path(output_dir); folder.mkdir(parents=True,exist_ok=True)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,1,sharex=True,figsize=(10,7),layout='constrained')
    rows=[]
    for color,vo in zip(['tab:blue','tab:orange'],dict.fromkeys((vmin,vmax))):
        reference,trace=switched_solution(data['Vin'],data['R'],data['fsw'],result['L_H'],result['C_F'],vo)
        tighter,_=switched_solution(data['Vin'],data['R'],data['fsw'],result['L_H'],result['C_F'],vo,rtol=1e-12)
        expected=next(p for p in result['points'] if p['Vo']==vo)
        errs={k:(reference[k]-expected[pred])/expected[pred] for k,pred in [('dIL_A','dIL'),('dVo_V','dVo')]}
        stable=max(abs(reference[k]-tighter[k])/max(abs(tighter[k]),1e-15) for k in ('dIL_A','dVo_V'))
        valid=reference['positive_valley'] and reference['periodic_residual_scaled']<1e-7
        rows.append({'Vo_V':vo,'formula':expected,'coupled_CCM_candidate':reference,
                     'reference_valid_for_diode_buck':valid,
                     'signed_relative_difference_reference_minus_formula':errs,
                     'tight_tolerance_relative_change_max':stable,
                     'exceeds_requested_rL':reference['rL']>data['rL']*(1+1e-9) if valid else None,
                     'exceeds_requested_rv':reference['rv']>data['rv']*(1+1e-9) if valid else None})
        t,y=trace; phase=t*data['fsw']; d=vo/data['Vin']; dil=expected['dIL']
        approx_i=vo/data['R']+np.where(phase<d,-dil/2+dil*phase/d,dil/2-dil*(phase-d)/(1-d))
        charge=np.where(phase<d,-dil*phase/2+dil*phase**2/(2*d),dil*(phase-d)/2-dil*(phase-d)**2/(2*(1-d)))
        approx_v=(charge-dil*(1-2*d)/12)/(data['fsw']*result['C_F'])
        label=f'{vo:g} V coupled CCM'+(' candidate INVALID for diode buck' if not valid else '')
        axes[0].plot(t*1e6,y[0],color=color,label=label)
        axes[0].plot(t*1e6,approx_i,color=color,ls='--',label=f'{vo:g} V triangle approx.')
        axes[1].plot(t*1e6,(y[1]-vo)*1000,color=color,label=label)
        axes[1].plot(t*1e6,approx_v*1000,color=color,ls='--',label=f'{vo:g} V approximate integral')
    axes[0].set_title('Independent switched-state ODE vs small-ripple approximation (one period)')
    axes[0].set_ylabel('Inductor current (A)'); axes[1].set_ylabel('Output minus target (mV)')
    axes[1].set_xlabel('Time (us)')
    for ax in axes: ax.grid(alpha=.3); ax.legend(fontsize=7)
    fig.savefig(folder/'comparison.png',dpi=160); plt.close(fig)
    report={'inputs':data,'L_H':result['L_H'],'C_F':result['C_F'],
            'method':'periodic affine matrix exponential + coupled switched ODE DOP853 + derivative-root extrema',
            'limits':'ideal fixed-duty CCM candidate only; no DCM, control loop, parasitics or hardware validation',
            'model_assessment':model.model_assessment(data,result),'points':rows}
    (folder/'comparison.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True); parser.add_argument('--output-dir',required=True)
    args=parser.parse_args()
    data=json.loads(Path(args.input).read_text(encoding='utf-8'))
    print(json.dumps(compare_case(data,args.output_dir),indent=2))

if __name__=='__main__':
    try: main()
    except (ValueError,ArithmeticError,OSError,RuntimeError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr); sys.exit(2)
