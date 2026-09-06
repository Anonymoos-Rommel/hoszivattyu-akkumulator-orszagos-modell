import csv
import unittest
from pathlib import Path

from modules.B02.emitter_marginal_reconciliation import build_calibrated_emitter_linkage

ROOT = Path(__file__).resolve().parents[1]
WBL = ROOT / "data" / "processed" / "b02" / "ksh_wbl_joint_cells_2022.csv"


class B02P38DiagnosticTests(unittest.TestCase):
    def test_probe_wbl_dimensions_and_budapest_candidates(self):
        with WBL.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            self.assertIsNotNone(reader.fieldnames)
            rows = [row for row in reader if row.get("projection_id") == "WBL011_FULL_STOCK_JOINT"]
        print("P38_FIELDS", reader.fieldnames)
        print("P38_FIRST", rows[0] if rows else None)
        for key in reader.fieldnames or []:
            values = sorted({row[key] for row in rows})
            if len(values) <= 30:
                print("P38_VALUES", key, values)
        model_rows, _ = build_calibrated_emitter_linkage(WBL)
        print("P38_MODEL_FIRST", model_rows[0])
        self.assertEqual(len(rows), 116452)
        self.assertEqual(len(model_rows), 116452)


if __name__ == "__main__":
    unittest.main()
