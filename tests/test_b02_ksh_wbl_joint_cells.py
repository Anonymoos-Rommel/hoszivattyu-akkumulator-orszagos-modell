from __future__ import annotations

import csv
import hashlib
import json
import unittest
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "b02"


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B02KshWblJointCellsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = read_csv("ksh_wbl_joint_cells_2022.csv")
        cls.coverage = read_csv("ksh_wbl_joint_cell_coverage_2022.csv")
        cls.joinability = read_csv("b02_archetype_joinability_2022.csv")
        cls.manifest = json.loads(
            (DATA / "ksh_wbl_joint_manifest.json").read_text(encoding="utf-8")
        )

    def test_projection_record_controls(self) -> None:
        counts = Counter(row["projection_id"] for row in self.rows)
        self.assertEqual(
            {
                "WBL011_ENVELOPE": 32_655,
                "WBL011_HEATING_FUEL": 7_682,
                "WBL017_HEAT_PUMP_BASELINE": 7_623,
            },
            dict(counts),
        )
        self.assertEqual(47_960, len(self.rows))
        self.assertEqual(47_960, len({row["cell_id"] for row in self.rows}))

    def test_wbl011_projections_reconcile_independently(self) -> None:
        totals = defaultdict(int)
        for row in self.rows:
            totals[row["projection_id"]] += int(row["dwelling_count"])
        self.assertEqual(4_008_541, totals["WBL011_ENVELOPE"])
        self.assertEqual(4_008_541, totals["WBL011_HEATING_FUEL"])
        self.assertEqual(3_919_564, totals["WBL017_HEAT_PUMP_BASELINE"])

    def test_wbl011_projections_reconcile_at_shared_grain(self) -> None:
        shared = {
            "WBL011_ENVELOPE": defaultdict(int),
            "WBL011_HEATING_FUEL": defaultdict(int),
        }
        for row in self.rows:
            if row["projection_id"] not in shared:
                continue
            key = (
                row["county_code"],
                row["settlement_type_code"],
                row["construction_period_code"],
            )
            shared[row["projection_id"]][key] += int(row["dwelling_count"])
        self.assertEqual(406, len(shared["WBL011_ENVELOPE"]))
        self.assertEqual(shared["WBL011_ENVELOPE"], shared["WBL011_HEATING_FUEL"])

    def test_heat_pump_baseline_is_not_eligibility(self) -> None:
        heat_pump = defaultdict(int)
        for row in self.rows:
            if row["projection_id"] == "WBL017_HEAT_PUMP_BASELINE":
                heat_pump[row["heat_pump_code"]] += int(row["dwelling_count"])
        self.assertEqual({"0": 3_855_849, "1": 61_559, "9": 2_156}, dict(heat_pump))
        self.assertEqual("Q", self.manifest["controls"]["technical_eligibility_status"])

    def test_only_returned_observations_are_materialized(self) -> None:
        self.assertEqual({"OBS"}, {row["evidence_status"] for row in self.rows})
        self.assertEqual(
            {"RETURNED_POSITIVE"}, {row["availability_status"] for row in self.rows}
        )
        self.assertTrue(all(int(row["dwelling_count"]) >= 1 for row in self.rows))
        by_projection = {row["projection_id"]: row for row in self.coverage}
        self.assertEqual(0, sum(int(row["returned_zero_records"]) for row in self.coverage))
        self.assertEqual(
            79_345,
            int(by_projection["WBL011_ENVELOPE"]["unreturned_candidate_combinations"]),
        )
        self.assertIn(
            "not proven zero",
            by_projection["WBL017_HEAT_PUMP_BASELINE"]["unreturned_interpretation"],
        )

    def test_projection_fields_do_not_create_a_synthetic_joint(self) -> None:
        for row in self.rows:
            if row["projection_id"] == "WBL011_ENVELOPE":
                self.assertEqual("TOTAL", row["heating_mode_code"])
                self.assertEqual("TOTAL", row["heating_fuel_code"])
                self.assertEqual("", row["heat_pump_code"])
            elif row["projection_id"] == "WBL011_HEATING_FUEL":
                self.assertEqual("TOTAL", row["wall_material_code"])
                self.assertEqual("TOTAL", row["floor_area_code"])
                self.assertEqual("TOTAL", row["comfort_code"])
                self.assertIn(
                    row["heating_mode_code"],
                    {"HEAT111", "HEAT112", "HEAT12", "NHEAT"},
                )
            else:
                self.assertEqual("TOTAL", row["wall_material_code"])
                self.assertEqual("TOTAL", row["floor_area_code"])
                self.assertEqual("TOTAL", row["comfort_code"])
                self.assertEqual("", row["heating_mode_code"])
        self.assertEqual("Q", self.manifest["controls"]["full_cross_projection_joint_status"])

    def test_manifest_lineage_and_output_hashes(self) -> None:
        queries = self.manifest["queries"]
        self.assertEqual(60, len(queries))
        self.assertEqual(60, len({query["query_id"] for query in queries}))
        self.assertEqual(60, len({query["url"] for query in queries}))
        self.assertTrue(all(len(query["response_sha256"]) == 64 for query in queries))
        for name, metadata in self.manifest["outputs"].items():
            self.assertEqual(
                metadata["sha256"], hashlib.sha256((DATA / name).read_bytes()).hexdigest()
            )

    def test_joinability_exposes_only_materialized_projection_grains(self) -> None:
        by_id = {row["join_id"]: row for row in self.joinability}
        self.assertEqual(
            "PARTIALLY_MATERIALIZED",
            by_id["JOIN-B02-WBL011-CORE"]["materialization_status"],
        )
        for join_id in (
            "JOIN-B02-WBL011-ENVELOPE",
            "JOIN-B02-WBL011-HEATING-FUEL",
            "JOIN-B02-WBL017-HEAT-PUMP",
        ):
            self.assertEqual("OBS", by_id[join_id]["evidence_status"])
            self.assertEqual("MATERIALIZED", by_id[join_id]["materialization_status"])
        self.assertEqual("Q", by_id["JOIN-B02-FULL-ARCHETYPE"]["evidence_status"])

    def test_source_pack_preserves_fail_closed_boundaries(self) -> None:
        text = (
            ROOT / "docs" / "source_packs" / "P1H_B02_KSH_WBL_JOINT_CELLS.md"
        ).read_text(encoding="utf-8")
        self.assertIn("nem bizonyított nulla", text)
        self.assertIn("nem műszaki alkalmasság", text)
        self.assertIn("nem kapcsolható össze cellaszinten", text)


if __name__ == "__main__":
    unittest.main()
