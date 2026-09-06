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
        # B10-P4 replaces the temporary header-only baseline template with the
        # two bounded observed RRF project applications.
        for name in template_names - {"priority_components.csv", "baseline_infrastructure.csv"}:
            headers, rows = read_csv(REGISTRY / name)
            self.assertEqual(EXPECTED_HEADERS[name], headers)
            self.assertEqual([], rows, name)

        headers, rows = read_csv(REGISTRY / "baseline_infrastructure.csv")
        self.assertEqual(EXPECTED_HEADERS["baseline_infrastructure.csv"], headers)
        self.assertEqual(
            {
                "RRF-6.1.1-21-2022-00006",
                "RRF-6.1.1-21-2022-00001",
            },
            {row["project_id"] for row in rows},
        )

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
        self.assertIn("READY_FOR_HUMAN_REVIEW", package)
        self.assertIn("NOT SENT", package)
        self.assertIn("NEM KÜLDÖTT", letter)
        self.assertIn("legfeljebb 500 rekordos", letter)
        self.assertNotIn("calculation_software", letter)
        self.assertNotIn("software_version", letter)
        self.assertIn("nem mind OÉNY-forrásmező", package)
        self.assertIn("source-native", package)
        self.assertNotIn("a teljes P1K-mezőkészletet kéri", package)

    def test_p1m_public_mapping_covers_all_p1k_fields_and_is_fail_closed(self) -> None:
        schema = json.loads((ROOT / "schemas" / "oeny_readiness_pilot.schema.json").read_text(encoding="utf-8"))
        headers, rows = read_csv(REGISTRY / "oeny_public_field_mapping.csv")
        self.assertEqual(EXPECTED_HEADERS["oeny_public_field_mapping.csv"], headers)
        self.assertEqual(set(schema["properties"]), {row["field_name"] for row in rows})
        self.assertEqual(len(rows), 22)
        self.assertIn("PUBLIC_PARTIAL", {row["availability_status"] for row in rows})
        self.assertIn("UNCERTAIN", {row["availability_status"] for row in rows})
        self.assertEqual(0, sum(row["availability_status"] == "PUBLIC_OBS_AVAILABLE" for row in rows))

    def test_p1m_release_state_and_endpoint_registry_are_explicit(self) -> None:
        endpoint_headers, endpoints = read_csv(REGISTRY / "oeny_public_endpoints.csv")
        self.assertEqual(EXPECTED_HEADERS["oeny_public_endpoints.csv"], endpoint_headers)
        self.assertTrue(any("cert-list/search" in row["endpoint_url_or_pattern"] for row in endpoints))
        audit = (ROOT / "docs" / "source_packs" / "P1M_OENY_PUBLIC_MACHINE_ACCESS_AUDIT.md").read_text(encoding="utf-8")
        release = (ROOT / "docs" / "data_requests" / "P1L_OENY_DATA_REQUEST_RELEASE_PACKAGE.md").read_text(encoding="utf-8")
        self.assertIn("PATH_B_HYBRID", audit)
        self.assertIn("P1L=HOLD_PUBLIC_ACCESS_AUDIT", audit)
        self.assertIn("READY_FOR_HUMAN_REVIEW", release)

    def test_p1l_final_attachment_separates_source_native_and_derived_fields(self) -> None:
        schema = json.loads((ROOT / "schemas" / "oeny_readiness_pilot.schema.json").read_text(encoding="utf-8"))
        attachment = (ROOT / "docs" / "data_requests" / "P1L_FINAL_ATTACHMENT_1_REQUESTED_FIELDS.md").read_text(encoding="utf-8")
        self.assertEqual(22, len(schema["properties"]))
        self.assertIn("## 1. SOURCE-NATIVE REQUEST FIELDS", attachment)
        self.assertIn("## 2. INTERNAL P1K DERIVED FIELDS", attachment)
        self.assertIn("P1K célmezők:** 22", attachment)
        source_section = attachment.split("## 2. INTERNAL P1K DERIVED FIELDS", 1)[0]
        for field_name in ("schema_version", "pilot_record_id", "emitter_status", "temperature_status", "demand_reduction_status", "hydraulic_readiness_status", "electrical_readiness_status", "permit_readiness_status", "pii_check"):
            self.assertNotIn(f"| `{field_name}` |", source_section)
        for field_name in schema["properties"]:
            self.assertIn(f"`{field_name}`", attachment)
        self.assertIn("Nem kérünk új kategorizálást", attachment)
        self.assertIn("BAD/POOR/... saját enumot", attachment)

    def test_p1l_final_package_has_recorded_dispatch_state(self) -> None:
        letter = (ROOT / "docs" / "data_requests" / "P1L_FINAL_OENY_REQUEST_LETTER.md").read_text(encoding="utf-8")
        email = (ROOT / "docs" / "data_requests" / "P1L_FINAL_EMAIL_COVER.md").read_text(encoding="utf-8")
        approval = (ROOT / "docs" / "data_requests" / "P1L_FINAL_JOSEPH_APPROVAL_SHEET.md").read_text(encoding="utf-8")
        dispatch = (ROOT / "docs" / "source_packs" / "B02_P19_OENY_DISPATCH_EVIDENCE.md").read_text(encoding="utf-8")
        self.assertIn("P1L_FINAL_R1 = READY_FOR_HUMAN_REVIEW", letter)
        self.assertIn("NEM KÜLDÖTT", letter)
        self.assertIn("READY_FOR_HUMAN_REVIEW", email)
        for expected in ("Címzett", "Csatorna", "Tárgy", "Kért rekordszám", "P1K célmezők száma", "Lechnertől kért source-native kutatási fogalmak száma", "Személyes adat", "SENT_2026-08-22 / AWAITING_RESPONSE"):
            self.assertIn(expected, approval)
        self.assertIn("22 (canonical contract; változatlan)", approval)
        self.assertIn("| Lechnertől kért source-native kutatási fogalmak száma | 9 |", approval)
        self.assertIn("NEM", approval)
        self.assertIn("REQUEST_SENT / AWAITING_RESPONSE", dispatch)
        self.assertIn("f8ae92f94ae37b7760a1770377eec08c2ec6bb2f14376cec8484a9d9454a3742", dispatch)
        self.assertIn("PRIVATE_EXTERNAL_EVIDENCE", dispatch)
        self.assertIn("public-repository storage: `NO`", dispatch)


if __name__ == "__main__":
    unittest.main()
