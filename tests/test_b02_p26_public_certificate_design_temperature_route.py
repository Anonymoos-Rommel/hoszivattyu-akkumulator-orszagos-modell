from __future__ import annotations

import csv
import unittest
from pathlib import Path

from modules.B02.archetype_admission_gate import (
    DesignTemperatureAuthorityCandidate,
    assess_direct_design_temperature_authority,
)


ROOT = Path(__file__).resolve().parents[1]
CONTROLS = ROOT / "registry" / "b02_current_design_temperature_controls.csv"
GATE = ROOT / "registry" / "b02_archetype_admission_gate.csv"
PACK = ROOT / "docs" / "source_packs" / "B02_P26_PUBLIC_CERTIFICATE_DESIGN_TEMPERATURE_ROUTE.md"


class B02P26PublicCertificateDesignTemperatureRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with CONTROLS.open(encoding="utf-8", newline="") as handle:
            cls.controls = list(csv.DictReader(handle))
        with GATE.open(encoding="utf-8", newline="") as handle:
            cls.gate = {row["claim_id"]: row for row in csv.DictReader(handle)}
        cls.pack = PACK.read_text(encoding="utf-8")

    def test_exact_current_record_control_is_frozen(self) -> None:
        self.assertEqual(len(self.controls), 1)
        row = self.controls[0]
        self.assertEqual(row["record_identifier"], "HET-1008-3097")
        self.assertEqual(row["state_scope"], "CURRENT_STATE")
        self.assertEqual(row["emitter_type"], "RADIATOR")
        self.assertEqual(row["temperature_basis"], "CALCULATION_INPUT")
        self.assertEqual(float(row["supply_temperature_c"]), 70.0)
        self.assertEqual(float(row["return_temperature_c"]), 55.0)
        self.assertEqual(row["evidence_status"], "DER")
        self.assertEqual(row["status"], "QUALIFIED_RECORD_ROUTE_ONLY")

    def test_record_route_is_not_stock_authority(self) -> None:
        row = self.controls[0]
        self.assertEqual(row["wbl_direct_join"], "NO")
        self.assertEqual(row["current_stock_complete"], "NO")
        for blocker in (
            "PUBLIC_MIRROR_NOT_BULK_OENY_DATASET",
            "NO_WBL_BINDING",
            "NO_NATIONAL_COMPLETENESS",
        ):
            self.assertIn(blocker, row["blockers"])

    def test_p18_accepts_pair_semantics_but_rejects_single_record_as_stock_authority(self) -> None:
        decision = assess_direct_design_temperature_authority(
            DesignTemperatureAuthorityCandidate(
                source_id="SRC-B02-HET-1008-3097-PUBLIC-CERTIFICATE-2024",
                reference_year=2024,
                source_universe="INDIVIDUAL_CERTIFICATE_RECORD",
                source_grain="DWELLING_RECORD",
                evidence_status="DER",
                current_state_explicit=True,
                temperature_basis="CALCULATION_INPUT",
                supply_temperature_c=70.0,
                return_temperature_c=55.0,
                evidence_locator_present=True,
                publishes_complete_assignment=False,
                wbl_compatible_join_key=False,
                reproducible_repository_binding=False,
            )
        )
        self.assertEqual(decision.status, "Q")
        self.assertNotIn("TEMPERATURE_BASIS_NOT_DESIGN_AUTHORITY", decision.reasons)
        self.assertNotIn("DESIGN_TEMPERATURE_PAIR_INCOMPLETE", decision.reasons)
        self.assertNotIn("DESIGN_TEMPERATURE_PAIR_INVALID", decision.reasons)
        self.assertIn("NOT_OCCUPIED_DWELLING_STOCK", decision.reasons)
        self.assertIn("NO_COMPLETE_DESIGN_TEMPERATURE_ASSIGNMENT", decision.reasons)
        self.assertIn("NO_WBL_COMPATIBLE_JOIN_KEY", decision.reasons)
        self.assertIn("NO_REPRODUCIBLE_REPOSITORY_BINDING", decision.reasons)

    def test_current_and_proposed_temperature_pairs_are_not_conflated(self) -> None:
        self.assertIn(
            "CURRENT-SYSTEM CALCULATION 70/55 C != PROPOSED RETROFIT CALCULATION 55/45 C",
            self.pack,
        )
        self.assertIn("CALCULATION_INPUT != GENERIC REFERENCE ASSUMPTION", self.pack)
        self.assertIn("ONE HET RECORD != COMPLETE OCCUPIED-STOCK DESIGN-TEMPERATURE ASSIGNMENT", self.pack)

    def test_technical_readiness_stays_on_exact_two_blockers(self) -> None:
        row = self.gate["TECHNICAL_READINESS_ARCHETYPE"]
        self.assertEqual(row["current_status"], "Q")
        self.assertEqual(
            row["current_blockers"],
            "NO_CURRENT_HEAT_EMITTER_EVIDENCE;NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE",
        )
        self.assertIn("P26", row["notes"])
        self.assertIn("70/55 C", row["notes"])
        self.assertIn("QUALIFIED_RECORD_ROUTE_ONLY", row["notes"])

    def test_registry_omits_unnecessary_personal_data(self) -> None:
        text = CONTROLS.read_text(encoding="utf-8")
        self.assertNotIn("@", text)
        self.assertNotIn("+36", text)
        self.assertNotIn("Szentendre", text)


if __name__ == "__main__":
    unittest.main()
