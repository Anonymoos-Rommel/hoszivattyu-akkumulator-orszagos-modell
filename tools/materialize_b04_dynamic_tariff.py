"""Materialize a hash-pinned public MVM PDF locally; never fetch or publish it."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.B04.dynamic_tariff import parse_mvm_table


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', required=True, type=Path)
    parser.add_argument('--output-dir', type=Path, default=ROOT/'data/interim/b04_dynamic')
    args=parser.parse_args()
    output=args.output_dir.resolve()
    if not output.is_relative_to((ROOT/'data/interim').resolve()):
        parser.error('complete numeric panel must remain in ignored data/interim')
    manifest=json.loads((ROOT/'registry/b04_dynamic_tariff_panel_manifest.json').read_text())
    digest=hashlib.sha256(args.pdf.read_bytes()).hexdigest()
    if digest != manifest['sha256']:
        parser.error('source revision hash mismatch; review new document before admission')
    result=subprocess.run(['pdftotext','-layout',str(args.pdf),'-'], check=True, capture_output=True, text=True)
    rows=parse_mvm_table(result.stdout,date.fromisoformat(manifest['start_date_local']),date.fromisoformat(manifest['end_date_local_exclusive']),manifest['source_id'])
    negative=sum(r.net_energy_huf_per_kwh<0 for r in rows)
    if len(rows)!=manifest['expected_intervals'] or negative!=manifest['expected_negative_net_prices']:
        parser.error('pinned-panel reconciliation failed')
    output.mkdir(parents=True,exist_ok=True)
    target=output/'mvm_d_backcast_202509_202608.csv'
    with target.open('w',newline='') as handle:
        writer=csv.writer(handle,lineterminator='\n')
        writer.writerow(['start_utc','end_utc','net_energy_huf_per_kwh','source_id','evidence_status'])
        for row in rows:
            writer.writerow([row.start_utc.isoformat(),row.end_utc.isoformat(),str(row.net_energy_huf_per_kwh),row.source_id,row.evidence_status])
    receipt={'source_id':manifest['source_id'],'source_sha256':digest,'csv_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'intervals':len(rows),'negative_net_prices':negative,'first_utc':rows[0].start_utc.isoformat(),'end_utc_exclusive':rows[-1].end_utc.isoformat(),'status':'SCN_EXTERNAL_ONLY_MATERIALIZED_NOT_NATIONAL_INPUT_CLOSURE'}
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
