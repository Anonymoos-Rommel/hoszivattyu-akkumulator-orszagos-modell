"""Materialize explicit B18 source observations into private, untracked storage.

No download, unit counts, domestic-availability/import-share or rollout estimate.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, fields
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.B18.supply_source_reference import (
    SupplyReferenceRecord, SupplySelection, SupplySourceReferenceError,
    read_supply_reference, reference_summary,
)

OUTPUT_NAMES = ('supply_source_reference.csv', 'receipt.json')


def guard_private_output(output_dir, *, root=ROOT):
    root = Path(root).resolve()
    output = Path(output_dir).absolute()
    if any(p.is_symlink() for p in (output, *output.parents)):
        raise SupplySourceReferenceError('symlinked output forbidden')
    resolved = output.resolve()
    output = resolved
    in_repo = resolved.is_relative_to(root)
    if in_repo and not resolved.is_relative_to(root / 'data/interim'):
        raise SupplySourceReferenceError('repository output must be in ignored data/interim')
    for path in (resolved, *resolved.parents):
        if path == root:
            break
        marker = path / '.git'
        if marker.exists() or marker.is_symlink():
            raise SupplySourceReferenceError('output must not belong to another Git checkout')
    for name in OUTPUT_NAMES:
        target = output / name
        if target.exists() or target.is_symlink():
            raise SupplySourceReferenceError('output exists; use a fresh private directory')
        if in_repo:
            relative = str(target.relative_to(root))
            tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', '--', relative],
                                     cwd=root, capture_output=True, check=False)
            ignored = subprocess.run(['git', 'check-ignore', '--quiet', '--no-index', '--', relative],
                                     cwd=root, capture_output=True, check=False)
            if tracked.returncode != 1 or ignored.returncode != 0:
                raise SupplySourceReferenceError('numeric output must be untracked and ignored')
    return resolved


def write_reference(reference, output_dir):
    output = guard_private_output(output_dir)
    summary = reference_summary(reference)
    output.mkdir(parents=True, exist_ok=True)
    target = output / OUTPUT_NAMES[0]
    names = [f.name for f in fields(SupplyReferenceRecord)]
    with target.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=names, lineterminator='\n')
        writer.writeheader()
        for record in reference.records:
            writer.writerow(asdict(record))
    summary['selection'] = asdict(reference.selection)
    summary['normalized_csv_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    summary['normalized_storage_policy'] = 'EXTERNAL_ONLY_NOT_FOR_PUBLIC_COMMIT'
    with (output / OUTPUT_NAMES[1]).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-file', required=True, type=Path)
    for name in ('source-id', 'dataset-id', 'product-code', 'classification', 'source-updated-at', 'reporter'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--reference-year', required=True, type=int)
    parser.add_argument('--partner', required=True, help='Native aggregate or NONE for production')
    parser.add_argument('--flow', required=True, help='1 import / 2 export or NONE for production')
    parser.add_argument('--metrics', required=True, nargs='+')
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        guard_private_output(args.output_dir)
        selected = SupplySelection(args.source_id, args.dataset_id, args.product_code, args.classification,
            args.reference_year, args.source_updated_at, args.reporter,
            None if args.partner == 'NONE' else args.partner,
            None if args.flow == 'NONE' else args.flow, tuple(args.metrics))
        result = write_reference(read_supply_reference(args.source_file, selected), args.output_dir)
    except (SupplySourceReferenceError, OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
