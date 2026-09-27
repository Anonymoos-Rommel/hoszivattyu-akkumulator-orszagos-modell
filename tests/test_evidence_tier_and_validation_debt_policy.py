import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "docs" / "methodology" / "evidence_tier_and_validation_debt_policy.md"
AUDIT = ROOT / "registry" / "project_blocker_evidence_audit.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
README = ROOT / "README.md"
AGENTS = ROOT / "AGENTS.md"
CHARTER = ROOT / "PROJECT_CHARTER.md"
EVIDENCE_PROTOCOL = ROOT / "docs" / "methodology" / "evidence_protocol.md"
POP_POLICY = ROOT / "docs" / "methodology" / "population_inference_policy.md"

READINESS_FILES = (
    ROOT / "registry" / "b08_readiness.csv",
    ROOT / "registry" / "b09_readiness.csv",
    ROOT / "registry" / "battery_readiness.csv",
    ROOT / "registry" / "electricity_readiness.csv",
    ROOT / "registry" / "heat_pump_readiness.csv",
    ROOT / "registry" / "regional_readiness.csv",
    ROOT / "registry" / "retrofit_readiness.csv",
)

ALLOWED_TIERS = {"E1", "E2", "E3"}
ALLOWED_CLASSES = {
    "MODEL_BLOCKER",
    "VALIDATION_BLOCKER",
    "LEGAL_AUTHORITY_BLOCKER",
    "POLICY_DECISION",
    "EXECUTION_DEPENDENCY",
    "OPTIONAL_EXTENSION",
    "CONTRACT_BOUNDARY",
}


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class EvidenceTierAndValidationDebtPolicyTests(unittest.TestCase):
    def test_policy_freezes_three_tiers_and_single_base_rule(self):
        text = POLICY.read_text(encoding="utf-8")
        for token in (
            "E1 — VERIFIED / AUTHORITATIVE",
            "E2 — PROVISIONAL_BASE / VALIDATION_DEBT",
            "E3 — ASSUMPTION_ONLY / INSUFFICIENT_EVIDENCE",
            "ONE CANONICAL VALUE PER MODEL VARIABLE",
            "NO AUTOMATIC LOW/BASE/HIGH CARTESIAN PRODUCT FOR SOURCE GAPS",
            "MODEL CONTINUATION != FINAL VALIDATION",
        ):
            self.assertIn(token, text)

    def test_every_current_open_question_is_audited_exactly_once(self):
        current = {r["question_id"] for r in rows(QUESTIONS) if r["status"] == "OPEN"}
        audit_rows = [r for r in rows(AUDIT) if r["source_registry"] == "open_questions.csv"]
        audited = [r["blocker_id"] for r in audit_rows]
        self.assertEqual(current, set(audited))
        self.assertEqual(len(audited), len(set(audited)))

    def test_every_readiness_q_component_is_audited(self):
        expected = set()
        for path in READINESS_FILES:
            for row in rows(path):
                if row.get("status") == "Q":
                    expected.add(f'READINESS:{row["module_id"]}:{row["component_id"]}')
        audited = {
            r["blocker_id"]
            for r in rows(AUDIT)
            if r["blocker_id"].startswith("READINESS:")
        }
        self.assertEqual(expected, audited)

    def test_audit_uses_only_contract_tiers_and_classes(self):
        for row in rows(AUDIT):
            self.assertIn(row["evidence_tier"], ALLOWED_TIERS)
            self.assertIn(row["blocker_class"], ALLOWED_CLASSES)
            self.assertIn(row["model_blocker"], {"yes", "no"})
            self.assertIn(row["finalization_blocker"], {"yes", "no", "claim_specific"})

    def test_e2_rows_have_single_base_and_validation_debt(self):
        for row in rows(AUDIT):
            if row["evidence_tier"] == "E2":
                self.assertTrue(row["validation_debt"].strip())
                if "LOW_BASE_HIGH" in row["canonical_base_rule"]:
                    self.assertIn("NO_LOW_BASE_HIGH", row["canonical_base_rule"])
                self.assertNotIn("X_low", row["canonical_base_rule"])
                self.assertTrue(
                    "SINGLE" in row["canonical_base_rule"]
                    or row["canonical_use"] == "DOWNSTREAM_ONLY"
                )

    def test_e3_legal_authority_is_fail_closed(self):
        legal = [
            r for r in rows(AUDIT)
            if r["blocker_class"] == "LEGAL_AUTHORITY_BLOCKER"
        ]
        self.assertTrue(legal)
        for row in legal:
            self.assertEqual("E3", row["evidence_tier"])
            self.assertEqual("FAIL_CLOSED", row["canonical_use"])
            self.assertEqual("yes", row["model_blocker"])

    def test_b05_runtime_and_b10_expected_network_are_validation_debt_not_model_stop(self):
        audit = {r["blocker_id"]: r for r in rows(AUDIT)}
        for blocker in ("Q-B05-003", "Q-B05-004", "Q-B05-005", "Q-B10-001"):
            row = audit[blocker]
            self.assertEqual("E2", row["evidence_tier"])
            self.assertEqual("VALIDATION_BLOCKER", row["blocker_class"])
            self.assertEqual("no", row["model_blocker"])
            self.assertEqual("yes", row["finalization_blocker"])

    def test_product_scaling_is_a_contract_boundary_not_a_missing_coefficient(self):
        audit = {r["blocker_id"]: r for r in rows(AUDIT)}
        row = audit["READINESS:B05:PRODUCT_SCALING"]
        self.assertEqual("E1", row["evidence_tier"])
        self.assertEqual("CONTRACT_BOUNDARY", row["blocker_class"])
        self.assertIn("FORBIDDEN_OPERATION", row["canonical_base_rule"])

    def test_core_docs_bind_to_new_policy(self):
        for path in (README, AGENTS, CHARTER, EVIDENCE_PROTOCOL, POP_POLICY):
            text = path.read_text(encoding="utf-8")
            self.assertIn("evidence_tier_and_validation_debt_policy.md", text)


if __name__ == "__main__":
    unittest.main()
