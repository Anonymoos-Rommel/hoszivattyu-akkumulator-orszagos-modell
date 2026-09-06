import csv
import unittest
from pathlib import Path

from modules.B02.emitter_marginal_reconciliation import (
    HISTORICAL_MULTI_PRIOR_SCENARIOS,
    build_calibrated_emitter_linkage,
)

ROOT = Path(__file__).resolve().parents[1]
WBL = ROOT / "data" / "processed" / "b02" / "ksh_wbl_joint_cells_2022.csv"


class B02P38DiagnosticTests(unittest.TestCase):
    def test_probe_national_and_budapest_outputs(self):
        with WBL.open(encoding="utf-8", newline="") as handle:
            source_rows = {
                row["cell_id"]: row
                for row in csv.DictReader(handle)
                if row.get("projection_id") == "WBL011_FULL_STOCK_JOINT"
            }
        model_rows, _ = build_calibrated_emitter_linkage(WBL)
        self.assertEqual(len(source_rows), 116452)
        self.assertEqual(len(model_rows), 116452)

        national_dwellings = sum(int(row["dwelling_count"]) for row in source_rows.values())
        budapest_cells = {
            cell_id for cell_id, row in source_rows.items() if row["county_code"] == "HU110"
        }
        budapest_dwellings = sum(
            int(source_rows[cell_id]["dwelling_count"]) for cell_id in budapest_cells
        )
        print("P38_TOTALS", national_dwellings, budapest_dwellings)

        for scenario_id in HISTORICAL_MULTI_PRIOR_SCENARIOS:
            probability_key = f"probability__{scenario_id}"
            national_expected = sum(
                row["dwelling_count"] * row[probability_key] for row in model_rows
            )
            budapest_expected = sum(
                row["dwelling_count"] * row[probability_key]
                for row in model_rows
                if row["cell_id"] in budapest_cells
            )
            print(
                "P38_METRIC",
                scenario_id,
                f"national_expected={national_expected:.6f}",
                f"national_share={national_expected / national_dwellings:.9f}",
                f"budapest_expected={budapest_expected:.6f}",
                f"budapest_share={budapest_expected / budapest_dwellings:.9f}",
            )


if __name__ == "__main__":
    unittest.main()
