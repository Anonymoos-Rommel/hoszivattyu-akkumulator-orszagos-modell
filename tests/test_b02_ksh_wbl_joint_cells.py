from __future__ import annotations

import csv
import hashlib
import json
import unittest
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "b02"
P14_REGISTRY = ROOT / "registry" / "b02_wbl011_source_native_full_joint.csv"

def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))

class B02KshWblJointCellsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = read_csv("ksh_wbl_joint_cells_2022.csv")
        cls.coverage = read_csv("ksh_wbl_joint_cell_coverage_2022.csv")
        cls.joinability = read_csv("b02_archetype_joinability_2022.csv")
        cls.manifest = json.loads((DATA / "ksh_wbl_joint_manifest.json").read_text(encoding="utf-8"))

    def test_projection_record_controls(self) -> None:
        counts = Counter(row["projection_id"] for row in self.rows)
        self.assertEqual({
            "WBL011_ENVELOPE": 32_655,
            "WBL011_HEATING_FUEL": 7_682,
            "WBL011_FULL_STOCK_JOINT": 116_452,
            "WBL017_HEAT_PUMP_BASELINE": 7_623,
        }, dict(counts))
        self.assertEqual(164_412, len(self.rows))
        self.assertEqual(164_412, len({row["cell_id"] for row in self.rows}))

    def test_wbl011_projections_reconcile_independently(self) -> None:
        totals = defaultdict(int)
        for row in self.rows:
            totals[row["projection_id"]] += int(row["dwelling_count"])
        for projection in ("WBL011_ENVELOPE", "WBL011_HEATING_FUEL", "WBL011_FULL_STOCK_JOINT"):
            self.assertEqual(4_008_541, totals[projection])
        self.assertEqual(3_919_564, totals["WBL017_HEAT_PUMP_BASELINE"])

    def test_full_joint_reconciles_to_both_wbl011_margins_at_shared_grain(self) -> None:
        ids = ("WBL011_ENVELOPE", "WBL011_HEATING_FUEL", "WBL011_FULL_STOCK_JOINT")
        shared = {projection: defaultdict(int) for projection in ids}
        for row in self.rows:
            if row["projection_id"] not in shared:
                continue
            key = (row["county_code"], row["settlement_type_code"], row["construction_period_code"])
            shared[row["projection_id"]][key] += int(row["dwelling_count"])
        self.assertEqual(406, len(shared["WBL011_FULL_STOCK_JOINT"]))
        self.assertEqual(shared["WBL011_ENVELOPE"], shared["WBL011_FULL_STOCK_JOINT"])
        self.assertEqual(shared["WBL011_HEATING_FUEL"], shared["WBL011_FULL_STOCK_JOINT"])

    def test_direct_full_joint_has_all_wbl011_dimensions_non_total(self) -> None:
        rows = [row for row in self.rows if row["projection_id"] == "WBL011_FULL_STOCK_JOINT"]
        self.assertEqual(116_452, len(rows))
        for row in rows:
            for field in ("construction_period_code","wall_material_code","floor_area_code","comfort_code","heating_mode_code","heating_fuel_code"):
                self.assertNotEqual("TOTAL", row[field])
            self.assertEqual("", row["heat_pump_code"])

    def test_heat_pump_baseline_is_not_eligibility(self) -> None:
        heat_pump = defaultdict(int)
        for row in self.rows:
            if row["projection_id"] == "WBL017_HEAT_PUMP_BASELINE":
                heat_pump[row["heat_pump_code"]] += int(row["dwelling_count"])
        self.assertEqual({"0": 3_855_849, "1": 61_559, "9": 2_156}, dict(heat_pump))
        self.assertEqual("Q", self.manifest["controls"]["technical_eligibility_status"])

    def test_only_returned_observations_are_materialized(self) -> None:
        self.assertEqual({"OBS"}, {row["evidence_status"] for row in self.rows})
        self.assertEqual({"RETURNED_POSITIVE"}, {row["availability_status"] for row in self.rows})
        self.assertTrue(all(int(row["dwelling_count"]) >= 1 for row in self.rows))
        by_projection = {row["projection_id"]: row for row in self.coverage}
        self.assertEqual(3_467_548, int(by_projection["WBL011_FULL_STOCK_JOINT"]["unreturned_candidate_combinations"]))
        self.assertIn("not proven zero", by_projection["WBL011_FULL_STOCK_JOINT"]["unreturned_interpretation"])

    def test_manifest_lineage_and_output_hashes(self) -> None:
        queries = self.manifest["queries"]
        self.assertEqual(80, len(queries))
        self.assertEqual(80, len({query["query_id"] for query in queries}))
        self.assertEqual(80, len({query["url"] for query in queries}))
        self.assertEqual("MATERIALIZED", self.manifest["controls"]["wbl011_full_stock_joint_materialization_status"])
        self.assertEqual(116_452, self.manifest["controls"]["projections"]["WBL011_FULL_STOCK_JOINT"]["returned_records"])
        for name, metadata in self.manifest["outputs"].items():
            self.assertEqual(metadata["sha256"], hashlib.sha256((DATA / name).read_bytes()).hexdigest())

    def test_p14_p15_response_shape_is_stable_but_raw_hash_is_retrieval_lineage(self) -> None:
        with P14_REGISTRY.open(encoding="utf-8", newline="") as handle:
            p14 = {row["county_code"]: row for row in csv.DictReader(handle) if row["scope_id"] != "NATIONAL"}
        p15 = {q["county_code"]: q for q in self.manifest["queries"] if q["projection_id"] == "WBL011_FULL_STOCK_JOINT"}
        self.assertEqual(set(p14), set(p15))
        hash_matches = 0
        for county in p14:
            self.assertEqual(int(p14[county]["joint_record_count"]), int(p15[county]["returned_records"]))
            self.assertEqual(int(p14[county]["joint_response_bytes"]), int(p15[county]["response_bytes"]))
            hash_matches += p14[county]["joint_response_sha256"] == p15[county]["response_sha256"]
        self.assertLess(hash_matches, 20)

    def test_joinability_exposes_materialized_direct_wbl011_joint(self) -> None:
        by_id = {row["join_id"]: row for row in self.joinability}
        core = by_id["JOIN-B02-WBL011-CORE"]
        self.assertEqual("OBS", core["evidence_status"])
        self.assertEqual("MATERIALIZED", core["materialization_status"])
        self.assertEqual("116452", core["record_count"])
        self.assertEqual("4008541", core["population_count"])
        self.assertEqual("Q", by_id["JOIN-B02-FULL-ARCHETYPE"]["evidence_status"])

if __name__ == "__main__":
    unittest.main()
