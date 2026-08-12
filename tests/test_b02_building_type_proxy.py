from __future__ import annotations

import csv
import hashlib
import json
import unittest
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "b02"


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B02BuildingTypeProxyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_rows = read_csv("ksh_building_type_source_2015.csv")
        cls.proxy_rows = read_csv("ksh_building_type_proxy_2022.csv")
        cls.manifest = json.loads(
            (DATA / "ksh_building_type_proxy_manifest.json").read_text(encoding="utf-8")
        )

    def test_source_table_controls_and_rounding_residual(self) -> None:
        self.assertEqual(40, len(self.source_rows))
        totals = defaultdict(int)
        for row in self.source_rows:
            totals[row["occupancy_scope"]] += int(row["dwelling_count"])
            self.assertEqual("OBS", row["evidence_status"])
        self.assertEqual(4_420_700, totals["ALL_DWELLINGS"])
        self.assertEqual(3_860_700, totals["OCCUPIED_DWELLINGS"])
        controls = self.manifest["controls"]
        self.assertEqual(3_860_600, controls["ksh_2015_published_occupied_national_total"])
        self.assertEqual(-100, controls["ksh_2015_rounding_residual"])

    def test_proxy_is_assumption_and_reconciles_by_settlement(self) -> None:
        self.assertEqual(8, len(self.proxy_rows))
        by_settlement: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in self.proxy_rows:
            self.assertEqual("ASS", row["evidence_status"])
            by_settlement[row["wbl_settlement_code"]].append(row)

        self.assertEqual({"FV", "MJV", "EV", "K"}, set(by_settlement))
        for code, rows in by_settlement.items():
            self.assertEqual({"FAMILY_HOUSE", "MULTI_DWELLING"}, {row["canonical_building_type"] for row in rows})
            self.assertAlmostEqual(1.0, sum(float(row["source_2015_share"]) for row in rows), places=12)
            self.assertEqual(
                int(rows[0]["wbl_2022_occupied_dwellings"]),
                sum(int(row["proxy_2022_dwelling_count"]) for row in rows),
                code,
            )

    def test_national_proxy_controls(self) -> None:
        by_type = defaultdict(int)
        for row in self.proxy_rows:
            by_type[row["canonical_building_type"]] += int(row["proxy_2022_dwelling_count"])
        self.assertEqual(2_423_136, by_type["FAMILY_HOUSE"])
        self.assertEqual(1_585_405, by_type["MULTI_DWELLING"])
        self.assertEqual(4_008_541, sum(by_type.values()))
        self.assertEqual(0, self.manifest["controls"]["proxy_reconciliation_residual"])

    def test_category_alignment_is_not_overstated(self) -> None:
        alignment = {
            row["wbl_settlement_code"]: row["category_alignment"]
            for row in self.proxy_rows
        }
        self.assertEqual("EXACT", alignment["FV"])
        self.assertEqual("EXACT", alignment["K"])
        self.assertEqual("APPROXIMATE", alignment["MJV"])
        self.assertEqual("APPROXIMATE", alignment["EV"])

    def test_manifest_output_hashes(self) -> None:
        for name, metadata in self.manifest["outputs"].items():
            digest = hashlib.sha256((DATA / name).read_bytes()).hexdigest()
            self.assertEqual(metadata["sha256"], digest, name)

    def test_source_pack_does_not_claim_heat_emitter_or_eligibility(self) -> None:
        text = (ROOT / "docs" / "source_packs" / "P1D_B02_BUILDING_TYPE_PROXY.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("országos hőleadó-adat nem azonosítható", text)
        self.assertIn("nincs új technikailag alkalmas lakásszám", text)
        self.assertIn("nem imputálhatók `OBS` vagy `DER`", text)


if __name__ == "__main__":
    unittest.main()
