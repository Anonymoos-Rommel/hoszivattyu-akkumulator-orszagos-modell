"""Write a pinned historical B11 source/control receipt in fresh private storage."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.B11 import gas_quality_reference as quality
from tools.materialize_b13_fiscal_reference import guard_private_output

# The existing hardened guard protects receipt.json and an unused fiscal name.
# Reuse it unchanged; no mutable global changes or guard substitutes.
OUTPUT_NAME = 'receipt.json'


def materialize(source_paths, *, historical_scope, output_dir):
    output = guard_private_output(output_dir)
    quality._require(not output.exists(), 'fresh private output directory required')
    reference = quality.read_gas_quality_reference(source_paths, historical_scope=historical_scope)
    payload = (json.dumps(reference, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    _write_receipt(payload, output)
    return {'reference_id': quality.REFERENCE_ID, 'historical_scope': historical_scope,
            'panels': [{'observation_year': p['provenance']['observation_year'], **p['summary']} for p in reference['panels']],
            'validated_source_artifacts': len(reference['source_validation']),
            'receipt_sha256': hashlib.sha256(payload).hexdigest(),
            'storage_policy': reference['storage_policy']}


def _write_receipt(payload, output):
    # Validation and serialization complete before any output directory exists.
    guard_private_output(output)
    quality._require(not output.exists(), 'fresh private output directory required')
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    guard_private_output(output)
    directory = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        fd = os.open(OUTPUT_NAME, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(payload)
    finally:
        os.close(directory)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-map', required=True, type=Path)
    parser.add_argument('--historical-scope', required=True, choices=(quality.HISTORICAL_SCOPE,))
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = materialize(quality.source_map(args.source_map), historical_scope=args.historical_scope,
                             output_dir=args.output_dir)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
