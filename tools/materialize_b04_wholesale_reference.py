"""Materialize qualified HU wholesale reference rows and optional explicit cost.

All originals are caller-local and pinned. No download or public numeric output.
The single receipt.json contains source evidence, normalized rows and, if an
imports JSON is explicitly supplied, exact caller-declared reference valuation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.B04 import wholesale_reference as wholesale
from tools.materialize_b13_fiscal_reference import guard_private_output

# Reuse the existing hardened policy unchanged. It guards receipt.json and an
# additional unused fiscal_reference.json name. We write only the former, so
# every actual output is covered, with no mutable guard-global customization.
OUTPUT_NAME = 'receipt.json'


def imports_contract(path):
    contract = wholesale._json(Path(path).read_bytes())
    required = {'profile_id', 'convention', 'within_hour_profile', 'energy_unit', 'intervals'}
    wholesale._require(type(contract) is dict and set(contract) == required
                       and type(contract['intervals']) is list, 'exact explicit imports contract required')
    records = []
    for row in contract['intervals']:
        wholesale._require(type(row) is dict and set(row) == {'start_utc', 'end_utc', 'imported_mwh'},
                           'exact imported-energy row fields required')
        records.append(wholesale.ImportedEnergy(wholesale._endpoint(row['start_utc']),
                       wholesale._endpoint(row['end_utc']), wholesale._number(row['imported_mwh'], nonnegative=True)))
    return {k: v for k, v in contract.items() if k != 'intervals'}, tuple(records)


def materialize(source_paths, *, window, output_dir, imports_json=None):
    output = guard_private_output(output_dir)
    reference = wholesale.read_wholesale_reference(source_paths, window=window)
    valuation = None
    if imports_json is not None:
        contract, energy = imports_contract(imports_json)
        valuation = wholesale._value(reference, energy, **contract)
    receipt = {'evidence': reference.evidence, 'reconciliation': reference.reconciliation,
               'normalized_rows': [wholesale.normalized_record(r) for r in reference.records],
               'valuation': valuation, 'storage_policy': 'PRIVATE_NUMERIC_OUTPUT_NOT_FOR_PUBLIC_COMMIT'}
    # Serialization and UTF-8 validation must finish before any numeric file exists.
    payload = (json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    # Validate again immediately before creation; O_EXCL forbids overwrite.
    guard_private_output(output)
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = output / OUTPUT_NAME
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(payload)
    return {'reference_id': wholesale.REFERENCE_ID, 'window': window,
            'hours': len(reference.records), 'has_caller_declared_valuation': valuation is not None,
            'receipt_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
            'storage_policy': receipt['storage_policy']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-map', required=True, type=Path)
    parser.add_argument('--window', required=True, choices=('utc2025', 'civil2025'))
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--imports-json', type=Path, help='Caller-declared energy/convention contract; no default profile')
    args = parser.parse_args(argv)
    try:
        guard_private_output(args.output_dir)
        result = materialize(wholesale.source_map(args.source_map), window=args.window,
                             output_dir=args.output_dir, imports_json=args.imports_json)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
