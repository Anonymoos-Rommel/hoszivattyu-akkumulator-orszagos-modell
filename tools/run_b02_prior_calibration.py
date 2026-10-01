"""Run the explicit experimental age/prior bridge on the existing WBL joint."""
import argparse
import json
from pathlib import Path
from modules.B02.keop_prior_calibration import run_calibration_experiment

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=run_calibration_experiment();a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'cases':4,'rows':len(result),'status':'SCN_EXPERIMENT_NOT_E2_TYPE_WEIGHTS','output':str(a.output)}))
