from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.audit_oeny_heat_emitter_schema import (  # noqa: E402
    PROHIBITED_DEDICATED_KEYS,
    collect_json_keys_and_strings,
)


class OenySchemaAuditTests(unittest.TestCase):
    def test_nested_keys_and_values_are_collected(self) -> None:
        keys, strings = collect_json_keys_and_strings(
            {"photos": [{"category": "characteristicHeatExchanger"}]}
        )
        self.assertEqual({"photos", "category"}, keys)
        self.assertEqual({"characteristicHeatExchanger"}, strings)

    def test_prohibited_keys_represent_dedicated_current_fields(self) -> None:
        self.assertIn("heatEmitterType", PROHIBITED_DEDICATED_KEYS)
        self.assertIn("supplyTemperature", PROHIBITED_DEDICATED_KEYS)
        self.assertIn("returnTemperature", PROHIBITED_DEDICATED_KEYS)
