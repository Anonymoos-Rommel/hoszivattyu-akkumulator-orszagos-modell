"""Write the fully validated joint market reference only to fresh private storage."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from modules.B04 import wholesale_reference as hu
from modules.B19 import historical_joint_market as joint
from tools.materialize_b13_fiscal_reference import guard_private_output

OUTPUT_NAME = 'receipt.json'  # Protected by the unchanged shared guard.


def paths_contract(path):
    paths = hu._json(Path(path).read_bytes())
    hu._require(type(paths) is dict and set(paths) == {'source_paths','handoff_paths','weather_path','hu_source_paths','at_source_paths'},
                'exact caller-owned original/handoff/weather/two-zone path mapping required')
    hu._require(type(paths['weather_path']) is str and paths['weather_path'], 'explicit weather path required')
    for name in ('source_paths','handoff_paths','hu_source_paths','at_source_paths'):
        value = paths[name]
        hu._require(type(value) is dict and all(type(k) is str and type(v) is str and v for k,v in value.items()),
                    'explicit source-ID/local-path mappings required')
    return paths


def materialize(paths, *, window, window_hours, output_dir):
    output = guard_private_output(output_dir)
    result = joint.calculate_reference(**paths,window=window,window_hours=window_hours)
    result['storage_policy'] = 'PRIVATE_NUMERIC_OUTPUT_NOT_FOR_PUBLIC_COMMIT'
    payload = (json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
    guard_private_output(output)
    output.mkdir(parents=True,exist_ok=True,mode=0o700)
    target = output/OUTPUT_NAME
    fd = os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:
        stream.write(payload)
    return {'reference_id':result['reference_id'], 'window':window, 'window_hours':window_hours,
            'hours':result['result']['hours'], 'windows_evaluated':result['result']['windows_evaluated'],
            'receipt_sha256':hashlib.sha256(target.read_bytes()).hexdigest(), 'storage_policy':result['storage_policy']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paths-json',required=True,type=Path)
    parser.add_argument('--window',required=True,choices=('utc2025',))
    parser.add_argument('--window-hours',required=True,type=int)
    parser.add_argument('--output-dir',required=True,type=Path)
    args = parser.parse_args(argv)
    try:
        guard_private_output(args.output_dir)
        result = materialize(paths_contract(args.paths_json),window=args.window,window_hours=args.window_hours,output_dir=args.output_dir)
    except (ValueError,OSError,KeyError,TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__ == '__main__':
    main()
