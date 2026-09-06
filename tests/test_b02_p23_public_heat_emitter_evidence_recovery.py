from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "registry" / "b02_public_emitter_evidence_audit.csv"
GATE = ROOT / "registry" / "b02_archetype_admission_gate.csv"
PACK = ROOT / "docs" / "source_packs" / "B02_P23_PUBLIC_HEAT_EMITTER_EVIDENCE_RECOVERY.md"


class B02P23PublicHeatEmitterEvidenceRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with AUDIT.open(encoding="utf-8", newline="") as handle:
            cls.rows = list(csv.DictReader(handle))
        with GATE.open(encoding="utf-8", newline="") as handle:
            cls.gate = {row["claim_id"]: row for row in csv.DictReader(handle)}
        cls.pack = PACK.read_text(encoding="utf-8")

    def test_audit_has_exact_five_bounded_public_surfaces(self) -> None:
        self.assertEqual(len(self.rows), 5)
        self.assertEqual(
            {row["audit_id"] for row in self.rows},
            {f"B02-P23-A0{i}" for i in range(1, 6)},
        )

    def test_ksh_questionnaire_is_taxonomy_only_not_stock_assignment(self) -> None:
        row = next(row for row in self.rows if row["audit_id"] == "B02-P23-A02")
        self.assertEqual(row["emitter_taxonomy_explicit"], "YES")
        self.assertEqual(row["published_numeric_emitter_assignment"], "NO")
        self.assertEqual(row["wbl_direct_join"], "NO")
        self.assertEqual(row["current_stock_complete"], "NO")
        self.assertEqual(row["status"], "QUALIFIED_TAXONOMY_ONLY")
        for token in (
            "gas convector",
            "stove/fireplace",
            "electric storage heater",
            "air conditioner",
            "electric floor/wall heating",
        ):
            self.assertIn(token, row["notes"])

    def test_yearbook_broad_shares_are_not_emitter_subtypes(self) -> None:
        row = next(row for row in self.rows if row["audit_id"] == "B02-P23-A03")
        self.assertEqual(row["status"], "QUALIFIED_CONTROL_ONLY")
        self.assertIn("EMITTER_SUBTYPES_COLLAPSED", row["blockers"])
        self.assertIn("48.4% one-dwelling central", row["notes"])
        self.assertIn("28.9% individual fixed", row["notes"])
        self.assertIn("48.4% ONE-DWELLING CENTRAL != 48.4% RADIATOR", self.pack)
        self.assertIn("28.9% INDIVIDUAL FIXED != 28.9% GAS CONVECTOR", self.pack)

    def test_bso_topic_coverage_does_not_mint_hungary_emitter_authority(self) -> None:
        row = next(row for row in self.rows if row["audit_id"] == "B02-P23-A01")
        self.assertEqual(row["status"], "Q")
        self.assertEqual(row["admission_effect"], "NONE")
        self.assertIn("NO_VERIFIED_HUNGARY_EMITTER_INDICATOR", row["blockers"])
        self.assertIn("BSO TECHNICAL-SYSTEM COVERAGE != VERIFIED HUNGARY EMITTER DISTRIBUTION", self.pack)

    def test_mehi_equipment_count_is_not_dwelling_count(self) -> None:
        row = next(row for row in self.rows if row["audit_id"] == "B02-P23-A05")
        self.assertEqual(row["status"], "CONTEXT_ONLY")
        self.assertIn("DEVICE_COUNT_NOT_DWELLING_COUNT", row["blockers"])
        self.assertIn("3,000,000 CONVECTOR DEVICES != 3,000,000 CONVECTOR-HEATED DWELLINGS", self.pack)

    def test_p22_system_authority_survives_without_emitter_promotion(self) -> None:
        row = next(row for row in self.rows if row["audit_id"] == "B02-P23-A04")
        self.assertEqual(row["status"], "QUALIFIED_SYSTEM_ONLY")
        self.assertEqual(row["wbl_direct_join"], "YES")
        self.assertEqual(row["current_stock_complete"], "YES")
        self.assertEqual(row["published_numeric_emitter_assignment"], "NO")
        self.assertIn("EMITTER_NOT_OBSERVED", row["blockers"])

    def test_technical_readiness_remains_exactly_fail_closed(self) -> None:
        row = self.gate["TECHNICAL_READINESS_ARCHETYPE"]
        self.assertEqual(row["current_status"], "Q")
        self.assertEqual(
            row["current_blockers"],
            "NO_CURRENT_HEAT_EMITTER_EVIDENCE;NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE",
        )
        self.assertIn("P23", row["notes"])
        self.assertIn("no complete current-emitter WBL binding is promoted", row["notes"])
        self.assertIn("CURRENT_HEAT_EMITTER_EVIDENCE = Q", self.pack)
        self.assertIn("NO_CURRENT_HEAT_EMITTER_EVIDENCE = OPEN", self.pack)


if __name__ == "__main__":
    unittest.main()
