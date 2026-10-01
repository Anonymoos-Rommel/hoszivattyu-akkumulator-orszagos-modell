"""Materialize the existing qualified P5 source pair to ignored data/interim.

No download, source re-acquisition, raw public-reuse promotion or programme
simulation occurs. The output remains an external-only historical baseline.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.B08.gui_load_reference import read_pinned_gui_workbook, local_2025_reference, reference_summary
from modules.B08.seasonal_reporting_contract import canonical_reporting_window, ReportingWindowKind, seasonal_peak


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-2025', type=Path, required=True)
    parser.add_argument('--source-2024', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, default=ROOT/'data/interim/b08_gui_reference')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if not output.is_relative_to((ROOT/'data/interim').resolve()):
        parser.error('complete numeric panel must remain in ignored data/interim')
    panels = [read_pinned_gui_workbook(args.source_2025, 'B08B09-P5-R01'),
              read_pinned_gui_workbook(args.source_2024, 'B08B09-P5-R02')]
    panel = local_2025_reference(panels)
    summary = reference_summary(panel)
    output.mkdir(parents=True, exist_ok=True)
    target = output/'hu_actual_load_local_2025_pt15m.csv'
    with target.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['start_utc', 'end_utc', 'actual_load_mw', 'timestep_hours',
                         'source_id', 'source_revision', 'evidence_status', 'evidence_tier'])
        for r in panel.records:
            writer.writerow([r.timestamp_utc.isoformat(), r.interval_end_utc.isoformat(),
                             r.power_mw, r.timestep_hours, r.source_refs[0], r.source_revision,
                             r.evidence_status, panel.evidence_tier])
    window = canonical_reporting_window(ReportingWindowKind.METEOROLOGICAL_WINTER, 2025)
    winter = tuple(r for p in panels for r in p.records if window.utc_start <= r.timestamp_utc < window.utc_end)
    peak = seasonal_peak(winter, window)
    summary['winter_2025'] = {'intervals': len(winter), 'start_utc': window.utc_start.isoformat(),
                              'end_utc_exclusive': window.utc_end.isoformat(), 'peak_mw': peak.peak_mw,
                              'peak_timestamps_utc': [t.isoformat() for t in peak.tied_timestamps_utc],
                              'evidence_status': peak.evidence_status}
    summary['source_acquisition_record_ids'] = list(panel.acquisition_record_ids)
    summary['source_sha256'] = list(panel.source_sha256)
    summary['csv_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    summary['csv_storage_policy'] = 'EXTERNAL_ONLY_IGNORED_NOT_FOR_PUBLIC_COMMIT'
    (output/'receipt.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
