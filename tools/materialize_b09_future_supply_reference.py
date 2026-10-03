"""Materialize one explicitly selected external B09 future source reference.

No download, central baseline, future runtime or source-use permission is created.
Normalized source data remain outside Git or in the repository's ignored interim
storage. Existing outputs are never overwritten.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.B09.future_supply_reference import (
    FutureSupplyReferenceError, ReferenceSelection, read_future_supply_reference,
    reference_summary,
)

OUTPUT_NAMES = ('future_supply_source_reference.csv', 'receipt.json')


def guard_private_output(output_dir, *, root=ROOT):
    root = Path(root).resolve()
    output = Path(output_dir).absolute()
    for path in (output, *output.parents):
        if path.is_symlink():
            raise FutureSupplyReferenceError('symlinked output path forbidden')
    resolved = output.resolve()
    in_repo = resolved.is_relative_to(root)
    if in_repo and not resolved.is_relative_to(root / 'data/interim'):
        raise FutureSupplyReferenceError('repository output must be in ignored data/interim')
    for path in (resolved, *resolved.parents):
        if path == root:
            break
        marker = path / '.git'
        if marker.exists() or marker.is_symlink():
            raise FutureSupplyReferenceError('output must not belong to another Git checkout')
    output = resolved
    for name in OUTPUT_NAMES:
        target = output / name
        if target.exists() or target.is_symlink():
            raise FutureSupplyReferenceError('output already exists; use a fresh private directory')
        if in_repo:
            relative = target.relative_to(root)
            tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', '--', str(relative)],
                                     cwd=root, capture_output=True, check=False)
            ignored = subprocess.run(['git', 'check-ignore', '--quiet', '--no-index', '--', str(relative)],
                                     cwd=root, capture_output=True, check=False)
            if tracked.returncode != 1 or ignored.returncode != 0:
                raise FutureSupplyReferenceError('numeric output must be untracked and ignored')
    return resolved


def write_reference(reference, output_dir):
    output = guard_private_output(output_dir)
    summary = reference_summary(reference)
    output.mkdir(parents=True, exist_ok=True)
    target = output / OUTPUT_NAMES[0]
    fields = [
        'source_id', 'source_revision', 'source_sha256', 'source_member',
        'source_member_sha256', 'source_row', 'source_value_cell', 'scenario_id',
        'model_stage', 'target_year', 'capacity_date_convention', 'market_node',
        'technology', 'resource_role', 'market_treatment_status', 'change_type',
        'value_mw', 'value_basis', 'unit', 'evidence_status', 'lifecycle_status',
        'financing_status', 'source_fields_json',
    ]
    with target.open('x', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(fields)
        for record in reference.records:
            values = [getattr(record, f) for f in fields[:-1]]
            values.append(json.dumps(dict(record.source_fields), ensure_ascii=False,
                                     separators=(',', ':')))
            writer.writerow(values)
    summary['normalized_csv_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    summary['normalized_storage_policy'] = 'EXTERNAL_ONLY_NOT_FOR_PUBLIC_COMMIT'
    with (output / OUTPUT_NAMES[1]).open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-file', required=True, type=Path)
    for name in ('source-id', 'source-revision', 'scenario-id', 'model-stage', 'capacity-date-convention'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--target-years', required=True, nargs='+', type=int)
    parser.add_argument('--resource-roles', required=True, nargs='+')
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        guard_private_output(args.output_dir)
        selection = ReferenceSelection(
            args.source_id, args.source_revision, args.scenario_id, args.model_stage,
            tuple(args.target_years), args.capacity_date_convention, tuple(args.resource_roles))
        reference = read_future_supply_reference(args.source_file, selection)
        summary = write_reference(reference, args.output_dir)
    except (FutureSupplyReferenceError, OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
