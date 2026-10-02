"""Reproduce the existing B09 P5/P6/P7 UTC-2025 reference in ignored storage.

The source directory must contain the six already-admitted exact workbooks.
No download, new source admission, OBS/reuse promotion or programme run occurs.
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
from modules.B09.gui_generation_reference import (
    GENERATION_ID, STEP, GuiGenerationReferenceError, _column_name,
    read_pinned_gui_generation_reference, reference_summary, source_artifacts,
)

OUTPUT_NAMES = ('hu_generation_utc_2025_pt15m.csv', 'recovery_cell_lineage.csv', 'receipt.json')


def guard_private_output(output_dir, *, root=ROOT):
    """Reject public, tracked, symlinked or existing outputs before reading sources."""
    root = Path(root).resolve()
    allowed = root / 'data/interim'
    output = Path(output_dir).absolute()
    if not output.resolve().is_relative_to(allowed) or allowed.resolve() != allowed:
        raise GuiGenerationReferenceError('complete numeric panel must remain in ignored data/interim')
    for path in (output, *output.parents):
        if path == root:
            break
        if path.is_symlink():
            raise GuiGenerationReferenceError('symlinked output paths are forbidden')
    output = output.resolve()
    for path in (output, *output.parents):
        if path == root:
            break
        marker = path / '.git'
        if marker.exists() or marker.is_symlink():
            raise GuiGenerationReferenceError('output must not belong to a nested Git checkout')
    for name in OUTPUT_NAMES:
        target = output / name
        if target.exists() or target.is_symlink():
            raise GuiGenerationReferenceError('output already exists; use a fresh ignored output directory')
        relative = target.relative_to(root)
        tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', '--', str(relative)],
                                 cwd=root, capture_output=True, check=False)
        ignored = subprocess.run(['git', 'check-ignore', '--quiet', '--no-index', '--', str(relative)],
                                 cwd=root, capture_output=True, check=False)
        if tracked.returncode != 1 or ignored.returncode != 0:
            raise GuiGenerationReferenceError('outputs must be untracked and covered by the repository ignore policy')
    return output.resolve()


def _digest(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def write_reference(panel, output_dir):
    output = guard_private_output(output_dir)
    summary = reference_summary(panel)
    artifacts = {a.acquisition_record_id: a for a in panel.artifacts}
    a75 = artifacts[GENERATION_ID]
    columns = dict(panel.a75_columns)
    recoveries = {(r.production_type_code, r.timestamp_utc): r for r in panel.recovery_lineage}
    output.mkdir(parents=True, exist_ok=True)
    target = output / OUTPUT_NAMES[0]
    with target.open('x', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow([
            'start_utc', 'end_utc', 'timestep_hours', 'production_type_code',
            'delivered_generation_kw', 'source_withdrawal_kw', 'net_generation_contribution_kw',
            'boundary_id', 'region_id', 'region_scheme', 'truth_context', 'evidence_status',
            'evidence_tier', 'model_use_status', 'source_refs', 'a75_acquisition_record_id',
            'a75_sha256', 'a75_cell', 'selected_operational_acquisition_record_id',
            'selected_operational_sha256', 'selected_operational_cell',
        ])
        for row in panel.records:
            code = row.source_component_id.removeprefix('ENTSOE_PSR_')
            recovery = recoveries.get((code, row.timestamp))
            source_row = int((row.timestamp - panel.request_start_utc) / STEP) + 7
            writer.writerow([
                row.timestamp.isoformat(), (row.timestamp + STEP).isoformat(), row.timestep_hours,
                code, row.delivered_generation_kw, row.source_withdrawal_kw,
                row.net_generation_contribution_kw, row.boundary_id, row.region_id,
                row.region_scheme, row.truth_context, row.evidence_status, panel.evidence_tier,
                panel.model_use_status, ';'.join(row.source_refs), a75.acquisition_record_id,
                a75.sha256, _column_name(columns[code]) + str(source_row),
                recovery.operational_cells[0][0] if recovery else '',
                recovery.selected_source_sha256 if recovery else '',
                recovery.operational_cells[0][1] if recovery else '',
            ])
    lineage_target = output / OUTPUT_NAMES[1]
    with lineage_target.open('x', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow([
            'start_utc', 'production_type_code', 'a75_acquisition_record_id', 'a75_sha256',
            'a75_cell', 'source_signed_power_mw', 'operational_acquisition_record_id',
            'operational_sha256', 'operational_cell', 'selected_for_recovery',
        ])
        for recovery in panel.recovery_lineage:
            for i, (record_id, cell) in enumerate(recovery.operational_cells):
                writer.writerow([
                    recovery.timestamp_utc.isoformat(), recovery.production_type_code,
                    a75.acquisition_record_id, a75.sha256, recovery.a75_cell,
                    str(recovery.signed_power_mw), record_id, artifacts[record_id].sha256,
                    cell, i == 0,
                ])
    summary['csv_sha256'] = _digest(target)
    summary['recovery_lineage_csv_sha256'] = _digest(lineage_target)
    summary['csv_storage_policy'] = 'EXTERNAL_ONLY_IGNORED_NOT_FOR_PUBLIC_COMMIT'
    summary['lineage_rule'] = 'Every recovered cell retains all identical MAVIR source-cell copies; first acquisition ID wins'
    with (output / OUTPUT_NAMES[2]).open('x', encoding='utf-8') as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
        handle.write('\n')
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'data/interim/b09_gui_reference')
    args = parser.parse_args(argv)
    try:
        guard_private_output(args.output_dir)
        paths = {a.acquisition_record_id: args.source_dir / a.external_filename for a in source_artifacts()}
        panel = read_pinned_gui_generation_reference(paths)
        summary = write_reference(panel, args.output_dir)
    except (GuiGenerationReferenceError, OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
