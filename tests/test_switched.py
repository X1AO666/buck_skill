"""Independent coupled-circuit checks, requiring requirements-validation.txt."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
reference=load('switched',ROOT/'scripts/compare_switched.py')
design=load('design',ROOT/'scripts/design_buck.py')
BASE=dict(Vin=24,R=3,Vo_min=6,Vo_max=12,fsw=100000,rL=.3,rv=.01)

class SwitchedTests(unittest.TestCase):
    def solution(self,data,vo=None,rtol=1e-10):
        bounds=design.validate(data); r=design.design(data,*bounds)
        return reference.switched_solution(data['Vin'],data['R'],data['fsw'],r['L_H'],r['C_F'],vo or bounds[0],rtol=rtol)[0]

    def test_periodic_state_and_dc_balance(self):
        for data in (BASE,{**BASE,'rv':.2},{**BASE,'Vo_min':23.9,'Vo_max':23.9}):
            for vo in set(design.validate(data)):
                r=self.solution(data,vo)
                self.assertLess(r['periodic_residual_scaled'],1e-8)
                self.assertLess(abs(r['mean_v_V']/vo-1),1e-8)
                self.assertLess(abs(r['mean_i_A']/(vo/data['R'])-1),1e-8)

    def test_tighter_tolerance_consistency(self):
        for data in (BASE,{**BASE,'rv':.5},{**BASE,'Vo_min':23.9,'Vo_max':23.9}):
            a=self.solution(data); b=self.solution(data,rtol=1e-12)
            for key in ('dIL_A','dVo_V'):
                self.assertLess(abs(a[key]/b[key]-1),1e-6)

    def test_small_ripple_limit(self):
        # Reference is a coupled ODE, not the sizing formula under test.
        errors=[]
        for rv in (.01,.001):
            data={**BASE,'rv':rv}; r=self.solution(data)
            errors.append(abs(r['dVo_V']/(rv*6)-1))
        self.assertLess(errors[1],errors[0])
        self.assertLess(errors[1],.001)

    def test_large_ripple_can_disagree_materially(self):
        r=self.solution({**BASE,'rv':.2})
        self.assertGreater(abs(r['dVo_V']/(.2*6)-1),.1)

    def test_near_dropout_error_is_not_guaranteed_by_small_rv(self):
        data={**BASE,'Vo_min':23.9,'Vo_max':23.9}
        r=self.solution(data)
        self.assertGreater(abs(r['dVo_V']/(.01*23.9)-1),.5)

    def test_nonpositive_valley_invalidates_diode_CCM(self):
        r=self.solution({**BASE,'rL':1.999})
        self.assertFalse(r['positive_valley'])

if __name__=='__main__': unittest.main(verbosity=2)
