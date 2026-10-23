"""Behavioral regression checks; run from any working directory with Python."""
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('buck_design', ROOT/'scripts/design_buck.py')
buck = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(buck)
BASE = dict(Vin=24, R=3, Vo_min=6, Vo_max=12, fsw=100000, rL=.3, rv=.01)

class DesignTests(unittest.TestCase):
    def result(self, data):
        return buck.design(data, *buck.validate(data))

    def test_public_result(self):
        r = self.result(BASE)
        self.assertAlmostEqual(r['L_H'],75e-6)
        self.assertAlmostEqual(r['C_F'],12.5e-6)
        self.assertEqual(r['worst_L_Vo'],6)
        self.assertEqual(r['worst_C_Vo'],6)
        for p,di,dv in zip(r['points'],[.6,.8],[.06,.08]):
            self.assertAlmostEqual(p['dIL'],di)
            self.assertAlmostEqual(p['dVo'],dv)

    def test_power_only_and_consistent_ranges(self):
        both={**BASE,'P_min':12,'P_max':48}
        power={k:v for k,v in both.items() if k not in ('Vo_min','Vo_max')}
        for d in (both,power):
            self.assertAlmostEqual(self.result(d)['L_H'],75e-6)
            self.assertAlmostEqual(self.result(d)['C_F'],12.5e-6)

    def test_single_point(self):
        r=self.result({**BASE,'Vo_min':12})
        self.assertAlmostEqual(r['L_H'],50e-6)
        self.assertAlmostEqual(r['C_F'],12.5e-6)

    def test_changed_parameters(self):
        r=self.result(dict(Vin=48,R=6,Vo_min=12,Vo_max=24,fsw=200000,rL=.2,rv=.005))
        self.assertAlmostEqual(r['L_H'],112.5e-6)
        self.assertAlmostEqual(r['C_F'],1/240000)

    def test_model_screening_is_not_input_rejection(self):
        normal=buck.model_assessment(BASE,self.result(BASE))
        self.assertEqual(normal['warnings'],[])
        self.assertEqual(normal['status'],'screening_passed_not_validated')
        for data in ({**BASE,'rv':.2},{**BASE,'rL':1.999},
                     {**BASE,'Vo_min':23.9,'Vo_max':23.9}):
            assessment=buck.model_assessment(data,self.result(data))
            self.assertTrue(assessment['warnings'])
            self.assertEqual(assessment['status'],'needs_independent_validation')

    def test_missing_multiple(self):
        with self.assertRaises(ValueError) as ctx:
            buck.validate({k:v for k,v in BASE.items() if k not in ('fsw','rv')})
        self.assertIn('fsw',str(ctx.exception)); self.assertIn('rv',str(ctx.exception))

    def test_invalid_inputs(self):
        variants=[('Vo_max',24),('Vo_max',30),('Vo_min',13),('rL',2),('rL',0),('rv',0),('Vin',-24),('R',True),('fsw','100kHz'),('R',float('nan')),('R',float('inf'))]
        for key,value in variants:
            with self.subTest(key=key,value=value), self.assertRaises(ValueError):
                buck.validate({**BASE,key:value})
        for d in ([],None,42):
            with self.subTest(data=d), self.assertRaises(ValueError): buck.validate(d)

    def test_null_or_partial_additional_range(self):
        power={k:v for k,v in {**BASE,'P_min':12,'P_max':48}.items() if k not in ('Vo_min','Vo_max')}
        for d in ({**BASE,'P_min':None,'P_max':50}, {**BASE,'P_min':12},
                  {**power,'Vo_min':None,'Vo_max':30}, {**power,'Vo_max':30},
                  {**BASE,'P_min':None,'P_max':None}):
            with self.subTest(data=d), self.assertRaises(ValueError): buck.validate(d)

    def test_inconsistent_or_reversed_power(self):
        for d in ({**BASE,'P_min':12,'P_max':50},{**BASE,'P_min':48,'P_max':12}):
            with self.subTest(data=d), self.assertRaises(ValueError): buck.validate(d)

    def test_entire_ranges_and_minimality(self):
        # Deterministic varied designs, checked at 101 points (not just endpoints).
        rng=random.Random(20261023)
        for _ in range(100):
            vin=rng.uniform(5,100); lo=rng.uniform(.001,.8)*vin
            hi=rng.uniform(lo/vin,.999)*vin
            d=dict(Vin=vin,R=10**rng.uniform(-1,2),Vo_min=lo,Vo_max=hi,
                   fsw=10**rng.uniform(3,6),rL=rng.uniform(.05,1.95),rv=10**rng.uniform(-4,-1))
            result=self.result(d); L=result['L_H']; C=result['C_F']
            for j in range(101):
                vo=lo+(hi-lo)*j/100; io=vo/d['R']
                ripple=vo*(1-vo/vin)/(L*d['fsw'])
                self.assertLessEqual(ripple/io,d['rL']*(1+1e-12))
                self.assertLessEqual(ripple/(8*d['fsw']*C*vo),d['rv']*(1+1e-12))
                self.assertGreater(io-ripple/2,0)
            # Reducing either selected value 1% must violate its limiting constraint.
            di=lo*(1-lo/vin)/(L*.99*d['fsw'])
            self.assertGreater(di/(lo/d['R']),d['rL'])
            di=lo*(1-lo/vin)/(L*d['fsw'])
            self.assertGreater(di/(8*d['fsw']*C*.99*lo),d['rv'])

    def test_plot_equations_extremes_and_periodicity(self):
        # Capture plotted arrays, then check physical amplitude and period endpoints.
        import numpy as np
        import matplotlib
        matplotlib.use('Agg')
        from matplotlib.axes import Axes
        from unittest.mock import patch
        original=Axes.plot
        for lo,hi in ((6,12),(.000024,23.999976)):
            d={**BASE,'Vo_min':lo,'Vo_max':hi}; r=self.result(d); traces=[]
            def capture(ax,x,y,*args,**kwargs):
                traces.append((np.asarray(x),np.asarray(y)))
                return original(ax,x,y,*args,**kwargs)
            with tempfile.TemporaryDirectory() as tmp, patch.object(Axes,'plot',capture):
                self.assertTrue(Path(buck.make_plot(d,r,lo,hi,tmp)).is_file())
            for p,(t,il),(_,vr) in zip(r['points'],traces[::2],traces[1::2]):
                self.assertAlmostEqual(float(np.ptp(il))/p['dIL'],1,places=7)
                self.assertAlmostEqual(float(np.ptp(vr))/(p['dVo']*1000),1,places=7)
                self.assertAlmostEqual(float(vr[-1]-vr[0]),0,places=7)
                self.assertAlmostEqual(float(t[-1]),3e6/d['fsw'])
                # Integration must represent voltage minus its continuous-time mean.
                integrate=getattr(np,'trapezoid',None) or np.trapz
                self.assertLess(abs(float(integrate(vr,t)/(t[-1]-t[0]))),p['dVo']*1000*1e-4)

    def test_cli_from_unrelated_directory(self):
        with tempfile.TemporaryDirectory(prefix='buck test ') as tmp:
            folder=Path(tmp); inp=folder/'input with spaces.json'
            inp.write_text(json.dumps(BASE),encoding='utf-8')
            run=subprocess.run([sys.executable,str(ROOT/'scripts/design_buck.py'),'--input',str(inp),'--output-dir',str(folder/'out with spaces')],cwd=tmp,capture_output=True,text=True,encoding='utf-8')
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertTrue(Path(json.loads(run.stdout)['plot']).is_file())
            inp.write_text('[]',encoding='utf-8')
            run=subprocess.run([sys.executable,str(ROOT/'scripts/design_buck.py'),'--input',str(inp)],cwd=tmp,capture_output=True,text=True,encoding='utf-8')
            self.assertEqual(run.returncode,2)
            self.assertNotIn('Traceback',run.stderr)

if __name__=='__main__': unittest.main(verbosity=2)
