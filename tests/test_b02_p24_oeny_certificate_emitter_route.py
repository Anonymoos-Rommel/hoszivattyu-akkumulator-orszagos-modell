from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "registry" / "b02_public_emitter_evidence_audit.csv"
GATE = ROOT / "registry" / "b02_archetype_admission_gate.csv"
PACK = ROOT / "docs" / "source_packs" / "B02_P24_OENY_CERTIFICATE_EMITTER_ROUTE.md"


class B02P24OenyCertificateEmitterRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with AUDIT.open(encoding="utf-8", newline="") as handle:
            cls.rows = list(csv.DictReader(handle))
        with GATE.open(encoding="utf-8", newline="") as handle:
            cls.gate = {row["claim_id"]: row for row in csv.DictReader(handle)}
        cls.pack = PACK.read_text(encoding="utf-8")

    def test_oeny_certificate_route_is_record_level_only(self) -> None:
        row = next(row for row in self.rows if row["audit_id"] == "B02-P24-A06")
        self.assertEqual(row["emitter_taxonomy_explicit"], "YES")
        self.assertEqual(row["published_numeric_emitter_assignment"], "NO")
        self.assertEqual(row["wbl_direct_join"], "NO")
        self.assertEqual(row["current_stock_complete"], "NO")
        self.assertEqual(row["admission_effect"], "RECORD_LEVEL_ROUTE_ONLY")
        self.assertEqual(row["status"], "QUALIFIED_RECORD_ROUTE_ONLY")

    def test_certificate_route_does_not_mint_bulk_stock_authority(self) -> None:
        row = next(row for row in self.rows if row["audit_id"] == "B02-P24-A06")
        for blocker in (
            "NO_DOCUMENTED_BULK_STOCK_ASSIGNMENT",
            "NO_WBL_BINDING",
            "NO_NATIONAL_COMPLETENESS",
        ):
            self.assertIn(blocker, row["blockers"])
        self.assertIn(
            "CERTIFICATE-LEVEL EMITTER EVIDENCE != COMPLETE OCCUPIED-STOCK EMITTER ASSIGNMENT",
            self.pack,
        )

    def test_synthetic_preview_is_template_evidence_only(self) -> None:
        self.assertIn("JELLEMZŐ HŐLEADÓ ÉS ANNAK SZABÁLYOZÁSA", self.pack)
        self.assertIn("non-authentic synthetic example", self.pack)
        self.assertIn("template/content surface", self.pack)

    def test_ambient_design_temperature_is_not_hydronic_pair(self) -> None:
        self.assertIn(
            "INDOOR/OUTDOOR DESIGN CONDITION != HYDRONIC SUPPLY/RETURN DESIGN TEMPERATURE",
            self.pack,
        )
        self.assertIn("20 °C indoors and -15 °C outdoors", self.pack)
        self.assertIn("REFERENCE 55/45 C != CURRENT BUILDING DESIGN TEMPERATURE", self.pack)

    def test_p18_boundary_is_reused_not_reimplemented(self) -> None:
        self.assertIn("No new runtime gate is required", self.pack)
        self.assertIn("existing P18 direct-authority contract", self.pack)

    def test_technical_readiness_blockers_remain_exact(self) -> None:
        row = self.gate["TECHNICAL_READINESS_ARCHETYPE"]
        self.assertEqual(row["current_status"], "Q")
        self.assertEqual(
            row["current_blockers"],
            "NO_CURRENT_HEAT_EMITTER_EVIDENCE;NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE",
        )
        self.assertIn("P24", row["notes"])
        self.assertIn("individual-certificate", row["notes"])
        self.assertIn("current-emitter evidence route", row["notes"])
        self.assertIn("COMPLETE CURRENT-STOCK EMITTER AUTHORITY = Q", self.pack)
        self.assertIn("COMPLETE CURRENT DESIGN-TEMPERATURE AUTHORITY = Q", self.pack)


if __name__ == "__main__":
    unittest.main()
