from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.validate_registry import EXPECTED_HEADERS, read_csv


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry"


class V12PortfolioContractTests(unittest.TestCase):
    def test_state_model_has_monotone_s0_to_s5_contract(self) -> None:
        model = json.loads((REGISTRY / "household_state_model.json").read_text(encoding="utf-8"))
        self.assertEqual("CONTRACTED_SKELETON", model["status"])
        self.assertEqual(["S0", "S1", "S2", "S3", "S4", "S5"], [s["state_id"] for s in model["states"]])
        self.assertEqual(
            [
                "BASELINE_AUDITED",
                "DEMAND_REDUCED",
                "TECHNICALLY_READY",
                "HEAT_PUMP_ACTIVE",
                "FLEX_READY",
                "TARGET_STATE",
            ],
            [s["name"] for s in model["states"]],
        )
        self.assertTrue(model["transition_invariants"])

    def test_v12_registry_templates_are_header_only(self) -> None:
        template_names = {
            "intervention_catalog.csv",
            "priority_components.csv",
            "portfolio_schedule.csv",
            "regional_readiness.csv",
            "baseline_infrastructure.csv",
            "incremental_capex_attribution.csv",
            "fiscal_headroom.csv",
        }
        for name in template_names - {"priority_components.csv"}:
            headers, rows = read_csv(REGISTRY / name)
            self.assertEqual(EXPECTED_HEADERS[name], headers)
            self.assertEqual([], rows, name)

        headers, rows = read_csv(REGISTRY / "priority_components.csv")
        self.assertEqual(EXPECTED_HEADERS["priority_components.csv"], headers)
        self.assertEqual(
            {
                "SOCIAL_NEED",
                "ENERGY_WASTE",
                "HOUSEHOLD_GAIN",
                "PUBLIC_EFFICIENCY",
                "FISCAL_EFFECT",
                "SYSTEM_VALUE",
                "ENV_HEALTH",
                "READINESS",
                "REGIONAL_EQUITY",
            },
            {row["component_id"] for row in rows},
        )
        self.assertTrue(all(row["weight_status"] == "Q" for row in rows))

    def test_v12_questions_are_registered(self) -> None:
        _, rows = read_csv(REGISTRY / "open_questions.csv")
        ids = {row["question_id"] for row in rows}
        self.assertTrue(
            {
                "Q-B01-003",
                "Q-B01-004",
                "Q-B01-005",
                "Q-B10-001",
                "Q-B01-006",
                "Q-B12-001",
                "Q-B10-002",
                "Q-B06-001",
                "Q-B13-001",
                "Q-B01-007",
            }.issubset(ids)
        )

    def test_support_formula_is_explicit_assumption(self) -> None:
        _, rows = read_csv(REGISTRY / "formulas.csv")
        row = next(item for item in rows if item["formula_id"] == "FORM-B15-REQUIRED-PUBLIC-SUPPORT")
        self.assertEqual("ASS", row["status"])
        self.assertIn("max(0;", row["expression"])

    def test_b02_readiness_bridge_fails_closed_at_s1_and_s2(self) -> None:
        headers, rows = read_csv(REGISTRY / "b02_readiness_bridge.csv")
        self.assertEqual(EXPECTED_HEADERS["b02_readiness_bridge.csv"], headers)
        self.assertEqual({"S0", "S1", "S2"}, {row["state_id"] for row in rows})
        for row in rows:
            self.assertEqual("no", row["allow_inference"])
        blocked = [row for row in rows if row["state_id"] in {"S1", "S2"}]
        self.assertTrue(blocked)
        self.assertTrue(all(row["evidence_status"] == "Q" for row in blocked))

    def test_b02_evidence_gap_matrix_is_field_level_and_no_new_eligibility(self) -> None:
        headers, rows = read_csv(REGISTRY / "b02_s0_s2_evidence_gap_matrix.csv")
        self.assertEqual(EXPECTED_HEADERS["b02_s0_s2_evidence_gap_matrix.csv"], headers)
        self.assertEqual({"S0", "S1", "S2"}, {row["state_id"] for row in rows})
        self.assertTrue(any(row["readiness_field"] == "program_eligibility" for row in rows))
        self.assertTrue(
            all(row["allow_for_gate"] in {"yes", "partial", "no"} for row in rows)
        )
        self.assertTrue(
            all(row["status"] == "GAP" for row in rows if row["state_id"] == "S2" and row["evidence_status"] == "Q")
        )

    def test_oeny_readiness_pilot_schema_is_strict_and_parseable(self) -> None:
        schema = json.loads((ROOT / "schemas" / "oeny_readiness_pilot.schema.json").read_text(encoding="utf-8"))
        self.assertTrue(schema["additionalProperties"] is False)
        self.assertIn("pii_check", schema["required"])
        self.assertIn("pilot_record_id", schema["required"])

    def test_oeny_pilot_acceptance_covers_every_schema_property(self) -> None:
        schema = json.loads((ROOT / "schemas" / "oeny_readiness_pilot.schema.json").read_text(encoding="utf-8"))
        headers, rows = read_csv(REGISTRY / "oeny_pilot_acceptance_contract.csv")
        self.assertEqual(EXPECTED_HEADERS["oeny_pilot_acceptance_contract.csv"], headers)
        self.assertEqual(set(schema["properties"]), {row["field_name"] for row in rows})
        self.assertEqual(len(schema["properties"]), len(rows))
        self.assertEqual(len(rows), len({row["field_id"] for row in rows}))
        for row in rows:
            for column in EXPECTED_HEADERS["oeny_pilot_acceptance_contract.csv"]:
                self.assertTrue(row[column].strip(), f"empty {column} for {row['field_name']}")
            self.assertEqual("CONTRACTED", row["status"])

    def test_p1k_is_fail_closed_and_does_not_authorize_external_send(self) -> None:
        contract = (ROOT / "docs" / "source_packs" / "P1K_OENY_PILOT_ACCEPTANCE_CONTRACT.md").read_text(encoding="utf-8")
        self.assertIn("GO_FOR_REQUEST", contract)
        self.assertIn("REVISE_REQUEST", contract)
        self.assertIn("NO_GO", contract)
        self.assertIn("külső adatbekérés nem történt", contract)
        self.assertIn("Joseph végső engedélyére", contract)

    def test_p1l_manifest_covers_only_p1k_schema_properties(self) -> None:
        schema = json.loads((ROOT / "schemas" / "oeny_readiness_pilot.schema.json").read_text(encoding="utf-8"))
        headers, rows = read_csv(REGISTRY / "oeny_requested_field_manifest.csv")
        self.assertEqual(EXPECTED_HEADERS["oeny_requested_field_manifest.csv"], headers)
        field_rows = [row for row in rows if row["field_name"] in schema["properties"]]
        self.assertEqual(set(schema["properties"]), {row["field_name"] for row in field_rows})
        self.assertTrue(all(row["status"] == "IN_SCOPE" for row in rows))
        self.assertTrue(all(row["acceptance_link"] for row in rows))
        self.assertEqual(len(rows), len({row["manifest_id"] for row in rows}))

    def test_p1l_release_package_is_not_sent_and_has_explicit_decision(self) -> None:
        package = (ROOT / "docs" / "data_requests" / "P1L_OENY_DATA_REQUEST_RELEASE_PACKAGE.md").read_text(encoding="utf-8")
        letter = (ROOT / "docs" / "data_requests" / "P1L_OENY_FINAL_REQUEST_LETTER.md").read_text(encoding="utf-8")
        self.assertIn("READY_FOR_JOSEPH_APPROVAL", package)
        self.assertIn("NOT SENT", package)
        self.assertIn("NEM KÜLDÖTT", letter)
        self.assertIn("legfeljebb 500 rekordos", letter)
        self.assertNotIn("calculation_software", letter)
        self.assertNotIn("software_version", letter)


if __name__ == "__main__":
    unittest.main()
