"""Reproduce the eight fixed coupled-circuit comparisons (optional SciPy)."""
from pathlib import Path
import argparse
import importlib.util
import json

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    spec=importlib.util.spec_from_file_location('reference',root/'scripts/compare_switched.py')
    reference=importlib.util.module_from_spec(spec); spec.loader.exec_module(reference)
    base=dict(Vin=24,R=3,Vo_min=6,Vo_max=12,fsw=100000,rL=.3,rv=.01)
    cases={'T1':base,
       'changed':dict(Vin=48,R=6,Vo_min=12,Vo_max=24,fsw=200000,rL=.2,rv=.005),
       'rv_5pct':{**base,'rv':.05},'rv_20pct':{**base,'rv':.2},'rv_50pct':{**base,'rv':.5},
       'near_dropout':{**base,'Vo_min':23.9,'Vo_max':23.9},
       'near_CCM':{**base,'rL':1.999},'small_rv':{**base,'rv':.001}}
    output=Path(args.output_dir); output.mkdir(parents=True,exist_ok=True)
    summaries=[]
    for name,data in cases.items():
        folder=output/name; folder.mkdir(exist_ok=True)
        (folder/'input.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
        report=reference.compare_case(data,folder)
        summaries.append({'case':name,**report})
        print(name,'complete')
    (output/'summary.json').write_text(json.dumps(summaries,indent=2),encoding='utf-8')
if __name__=='__main__': main()
