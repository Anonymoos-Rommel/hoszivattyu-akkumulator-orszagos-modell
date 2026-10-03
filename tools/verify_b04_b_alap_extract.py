"""Verify curated B Alap and outside-H rate facts against a pinned public PDF.

The source bytes remain external-only. The legal mapping is independently
reviewed in the checkpoint; this tool verifies only the numerical rate inputs.
"""
import argparse
import csv
import hashlib
import json
import re
import subprocess
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = 'SRC-B04-MVM-RESIDENTIAL-TARIFF-2026'
AREAS = ('MVM Démász', 'E.ON Dél/E.ON Észak/OPUS', 'ELMŰ', 'MVM Émász')


def parse_source_tables(text):
    """The pinned PDF has five four-column numeric vectors per A1/B table."""
    vectors = []
    for line in text.splitlines():
        values = re.findall(r'(?<!\d)\d+,\d{3}(?!\d)', line)
        if len(values) == 4:
            vectors.append([Decimal(v.replace(',', '.')) for v in values])
    if len(vectors) != 20:
        raise ValueError('four complete five-vector A1/B distributor tables required')
    return [dict(distributor_area=area, energy=vectors[5*i],
                 base_net=vectors[5*i+1], network=vectors[5*i+2],
                 base_gross=vectors[5*i+3], final_gross=vectors[5*i+4])
            for i, area in enumerate(AREAS)]


def unique(rows, **criteria):
    matches = [r for r in rows if all(r.get(k) == v for k, v in criteria.items())]
    if len(matches) != 1:
        raise ValueError('exactly one curated tariff row required: ' + str(criteria))
    return matches[0]


def verify_rates(tables, residential, h_rows):
    b_high = unique(residential, tariff_id='B-ALAP-ALL-MARKET')
    a_high = unique(residential, tariff_id='A1-ALL-MARKET')
    controls = []
    for t in tables:
        area = t['distributor_area']
        b = unique(residential, distributor_area=area, tariff_band='B Alap discounted')
        a = unique(residential, distributor_area=area, tariff_band='A1 discounted')
        h = unique(h_rows, distributor_area=area, period_type='outside season discounted energy')
        pairs = [
            (b['energy_price_net_huf_per_kwh'], t['energy'][2]),
            (b['energy_price_gross_huf_per_kwh'], (t['energy'][2]*Decimal('1.27')).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)),
            (b['network_charge_huf_per_kwh'], t['network'][2]),
            (b['final_gross_huf_per_kwh'], t['final_gross'][2]),
            (b['fixed_charge_huf_per_year'], 12*t['base_gross'][2]),
            (b_high['energy_price_net_huf_per_kwh'], t['energy'][3]),
            (b_high['network_charge_huf_per_kwh'], t['network'][3]),
            (b_high['final_gross_huf_per_kwh'], t['final_gross'][3]),
            (a['final_gross_huf_per_kwh'], t['final_gross'][0]),
            (a['fixed_charge_huf_per_year'], 12*t['base_gross'][0]),
            (a_high['final_gross_huf_per_kwh'], t['final_gross'][1]),
            (h['net_huf_per_kwh'], t['energy'][0]),
            (h['final_gross_huf_per_kwh'], t['final_gross'][0]),
            (h['fixed_gross_huf_per_month'], t['base_gross'][0]),
        ]
        if any(Decimal(curated) != source for curated, source in pairs):
            raise ValueError('curated tariff differs from source table: ' + area)
        if t['base_gross'][2] != t['base_gross'][3] or t['base_gross'][0] != t['base_gross'][1]:
            raise ValueError('connection fixed rate must be identical across consumption tiers')
        controls.append(dict(distributor_area=area,
                             b_discounted_gross_huf_kwh=str(t['final_gross'][2]),
                             b_excess_gross_huf_kwh=str(t['final_gross'][3]),
                             b_fixed_gross_huf_month=str(t['base_gross'][2]),
                             outside_h_derived_gross_huf_kwh=str(t['final_gross'][0]),
                             outside_h_derived_fixed_gross_huf_month=str(t['base_gross'][0])))
    return controls


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((ROOT/'registry/b04_tariff_source_verification.json').read_text())
    source = unique(manifest['sources'], source_id=SOURCE_ID)
    expected = source['sha256']
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != expected:
        parser.error('source revision mismatch')
    text = subprocess.run(['pdftotext', '-layout', str(args.pdf), '-'],
                          capture_output=True, text=True, check=True, timeout=30).stdout
    def rows(name):
        with (ROOT/'data/processed'/name).open(encoding='utf-8', newline='') as f:
            return list(csv.DictReader(f))
    controls = verify_rates(parse_source_tables(text), rows('residential_electricity_tariff_schedule.csv'),
                            rows('h_tariff_schedule.csv'))
    print(json.dumps({'source_id': SOURCE_ID, 'source_sha256': expected,
                      'controls': controls, 'numeric_comparisons': 56,
                      'legal_mapping': 'REQUIRES_SEPARATE_SOURCE_REVIEW', 'result': 'PASS'},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
