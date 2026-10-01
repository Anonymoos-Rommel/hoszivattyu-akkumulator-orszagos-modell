"""Reproduce the narrow REKK Table1 numeric extract from the pinned public PDF.

Requires existing pdftotext; never downloads or republishes the PDF. KSH's
integer area comparator, income and significance marks are not service inputs.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
GROUPS = ('ALL', 'GAS_PRIMARY', 'GAS_SECONDARY_ONLY', 'NO_GAS_HEATING')
ANCHORS = ('Mintában súlyozott', 'Átlagos belső hőmérsék-',
           'Átlagos alapterület', 'Átlagos fűtött alapterü-')
FIELDS = ('weighted_household_share_pct', 'mean_reported_indoor_temperature_c',
          'mean_dwelling_area_m2', 'mean_reported_heated_area_share_pct')


def parse_page(text):
    if 'N=1013' not in text or '1. TÁBLÁZAT' not in text:
        raise ValueError('expected source table and overall sample size')
    lines = text.splitlines()
    vectors = []
    for anchor in ANCHORS:
        matches = [i for i, line in enumerate(lines) if anchor in line]
        if len(matches) != 1:
            raise ValueError('unique metric row anchor required')
        i = matches[0]
        line = lines[i] if anchor == ANCHORS[2] else lines[i+1]
        values = re.findall(r'(?<!\d)\d+,\d{2}(?!\d)', line)
        if len(values) != 4:
            raise ValueError('four printed decimal service values required')
        vectors.append([v.replace(',', '.') for v in values])
    return [dict(group_id=g, **{k:vectors[j][i] for j,k in enumerate(FIELDS)},
                 reference_year=2022, source_table=1, printed_page=17, pdf_page_1based=41,
                 source_id='SRC-B02-HU-REKK-TARKI-ENVELOPE-2022', evidence_status='DER',
                 allowed_use='SURVEY_GROUP_MEAN_CONTROL_ONLY') for i,g in enumerate(GROUPS)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((ROOT/'registry/b02_reported_service_manifest.json').read_text())
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != manifest['source_sha256']:
        parser.error('source PDF revision mismatch')
    result = subprocess.run(['pdftotext','-f','41','-l','41','-layout',str(args.pdf),'-'],
                            capture_output=True, text=True, check=True, timeout=30)
    rows = parse_page(result.stdout)
    with args.output.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
    print(json.dumps({'rows':len(rows),'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == '__main__': main()
