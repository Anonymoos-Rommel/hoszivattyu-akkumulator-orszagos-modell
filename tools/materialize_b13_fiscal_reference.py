"""Materialize the exact B13 external baseline into fresh private storage.

No download, fiscal programme calculation, allocation or public numeric panel.
The source map is an explicit source-ID/path object or an external acquisition
manifest list containing source_id and local_snapshot_path. Only selected pins
are used; paths have no semantic authority.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.B13.fiscal_reference import (
    FiscalReferenceError, read_fiscal_reference, reference_summary, source_manifest,
)

OUTPUT_NAMES = ('fiscal_reference.json', 'receipt.json')


def guard_private_output(output_dir, *, root=ROOT):
    root = Path(root).resolve()
    output = Path(output_dir).absolute()
    if any(p.is_symlink() for p in (output, *output.parents)):
        raise FiscalReferenceError('symlinked output forbidden')
    output = output.resolve()
    in_repo = output.is_relative_to(root)
    if in_repo and not output.is_relative_to(root / 'data/interim'):
        raise FiscalReferenceError('repository output must be in ignored data/interim')
    # Outer ignore rules do not protect files in an embedded repository or
    # linked worktree. Inspect the whole ancestry, including nonexistent tails,
    # and stop only at this checkout's own root/metadata when inside it.
    for parent in (output, *output.parents):
        if in_repo and parent == root:
            break
        marker = parent / '.git'
        if marker.exists() or marker.is_symlink():
            raise FiscalReferenceError('output must not belong to another or nested Git checkout')
    existing = next(p for p in (output, *output.parents) if p.exists())
    if not existing.is_dir():
        raise FiscalReferenceError('output ancestry must consist of directories')
    checkout = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                              cwd=existing, capture_output=True, text=True, check=False)
    if in_repo:
        if checkout.returncode != 0 or Path(checkout.stdout.strip()).resolve() != root:
            raise FiscalReferenceError('output must belong to the intended Git checkout')
    elif checkout.returncode != 128:
        # Git returns 128 when discovery reaches an ancestor outside a checkout.
        # A found checkout or an unexpected discovery result fails closed.
        raise FiscalReferenceError('external output Git isolation could not be established')
    for name in OUTPUT_NAMES:
        target = output / name
        if target.exists() or target.is_symlink():
            raise FiscalReferenceError('output exists; use a fresh private directory')
        if in_repo:
            relative = str(target.relative_to(root))
            tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', '--', relative],
                                     cwd=root, capture_output=True, check=False)
            ignored = subprocess.run(['git', 'check-ignore', '--quiet', '--no-index', '--', relative],
                                     cwd=root, capture_output=True, check=False)
            if tracked.returncode == 0 or ignored.returncode != 0:
                raise FiscalReferenceError('numeric output must be untracked and ignored')
    return output


def source_map(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise FiscalReferenceError('duplicate source-map key')
            result[key] = value
        return result

    entries = json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique)
    if isinstance(entries, list):
        selected = {s['source_id'] for s in source_manifest()['source_artifacts']}
        result = {}
        for entry in entries:
            sid = entry['source_id']
            if sid in selected:
                if sid in result:
                    raise FiscalReferenceError('duplicate selected source ID')
                result[sid] = entry['local_snapshot_path']
        entries = result
    if not isinstance(entries, dict) or any(not isinstance(v, str) or not v for v in entries.values()):
        raise FiscalReferenceError('explicit local source paths required')
    return {sid: Path(value) for sid, value in entries.items()}


def _json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f'unsupported output type: {type(value).__name__}')


def materialize(panel_path, source_files, output_dir):
    output = guard_private_output(output_dir)
    reference = read_fiscal_reference(panel_path, source_files)
    summary = reference_summary(reference)
    output.mkdir(parents=True, exist_ok=True)
    target = output / OUTPUT_NAMES[0]
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump([asdict(r) for r in reference.records], stream,
                  ensure_ascii=False, indent=2, default=_json_default)
        stream.write('\n')
    receipt = {**summary,
               'normalized_storage_policy': 'EXTERNAL_ONLY_NOT_FOR_PUBLIC_COMMIT',
               'materialized_panel_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
               'reconciliations': [asdict(c) for c in reference.reconciliations]}
    with (output / OUTPUT_NAMES[1]).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2, default=_json_default)
        stream.write('\n')
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--panel', required=True, type=Path)
    parser.add_argument('--source-map', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = materialize(args.panel, source_map(args.source_map), args.output_dir)
    except (FiscalReferenceError, OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
