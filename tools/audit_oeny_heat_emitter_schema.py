"""Audit the pinned public OÉNY upload examples for B02 heat-emitter fields."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any


TAG = "v3.0.14801"
BASE_URL = f"https://git.lechnerkozpont.hu/entan/dokumentacio/-/raw/{TAG}"
FILES = {
    "dictionary.md": {
        "path": "docs/dictionary.md",
        "sha256": "b95fa656b13eaac4228a2d5d7388fcfc6d7f1e483bf656a85551fb9a7b326457",
    },
    "validationRules.md": {
        "path": "docs/validationRules.md",
        "sha256": "c729c53a8c223f9460d3f379669e566c9560a4ce14fc6cfd68959db7ccc0f374",
    },
    "functional_unit_full_data.json": {
        "path": "test/system/data/json/functional_unit_full_data.json",
        "sha256": "f717b7b502abb79fa9827f38e3916e67c8b27e6c4391f3bdb22c94fc5ec159f5",
    },
}

REQUIRED_KEYS = {
    "buildingServicesSystemEnergeticQuality",
    "heatingSystem",
    "modernisationProposalsOfBuildingServicesSystems",
    "recommendedModernisations",
    "systemElements",
    "photos",
    "calculationsPdfFileContent",
}

PROHIBITED_DEDICATED_KEYS = {
    "radiator",
    "emitterType",
    "heatEmitterType",
    "supplyTemperature",
    "returnTemperature",
    "flowTemperature",
}

REQUIRED_PROPOSAL_VALUES = {"HeatExchangers", "FanCoilUnits"}
REQUIRED_PHOTO_VALUE = "characteristicHeatExchanger"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collect_json_keys_and_strings(value: Any) -> tuple[set[str], set[str]]:
    keys: set[str] = set()
    strings: set[str] = set()

    def walk(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                keys.add(key)
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)
        elif isinstance(item, str):
            strings.add(item)

    walk(value)
    return keys, strings


def load_bytes(filename: str, snapshot_dir: Path | None) -> bytes:
    if snapshot_dir is not None:
        return (snapshot_dir / filename).read_bytes()
    path = FILES[filename]["path"]
    with urllib.request.urlopen(f"{BASE_URL}/{path}", timeout=30) as response:
        return response.read()


def audit(snapshot_dir: Path | None = None) -> dict[str, Any]:
    blobs = {name: load_bytes(name, snapshot_dir) for name in FILES}
    actual_hashes = {name: sha256(data) for name, data in blobs.items()}
    hash_matches = {
        name: actual_hashes[name] == metadata["sha256"]
        for name, metadata in FILES.items()
    }

    sample = json.loads(blobs["functional_unit_full_data.json"].decode("utf-8-sig"))
    keys, strings = collect_json_keys_and_strings(sample)

    required_keys_present = sorted(REQUIRED_KEYS & keys)
    prohibited_keys_present = sorted(PROHIBITED_DEDICATED_KEYS & keys)
    proposal_values_present = sorted(REQUIRED_PROPOSAL_VALUES & strings)
    photo_value_present = REQUIRED_PHOTO_VALUE in strings

    passed = (
        all(hash_matches.values())
        and set(required_keys_present) == REQUIRED_KEYS
        and not prohibited_keys_present
        and set(proposal_values_present) == REQUIRED_PROPOSAL_VALUES
        and photo_value_present
    )

    return {
        "schema_tag": TAG,
        "passed": passed,
        "hashes": actual_hashes,
        "hash_matches": hash_matches,
        "required_keys_present": required_keys_present,
        "prohibited_dedicated_keys_present": prohibited_keys_present,
        "proposal_values_present": proposal_values_present,
        "characteristic_heat_emitter_photo_value_present": photo_value_present,
        "interpretation": (
            "The pinned upload example has coarse heating-system quality, proposal elements, "
            "photos, and a calculations PDF, but no dedicated current heat-emitter or "
            "supply/return-temperature key."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        help="Directory containing the three pinned files; downloads them if omitted.",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON report path.")
    args = parser.parse_args()

    report = audit(args.snapshot_dir)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
