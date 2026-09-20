import csv
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "registry" / "open_questions.csv"
IMPACT = ROOT / "registry" / "b02_p61_emitter_population_impact.csv"
AUDIT = ROOT / "registry" / "b02_public_emitter_evidence_audit.csv"
SOURCES = ROOT / "registry" / "sources.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
SOURCE_PACK = ROOT / "docs" / "source_packs" / "B02_P61_EMITTER_POPULATION_IMPACT_REPAIR.md"
TECHNICAL_CONTRACT = ROOT / "modules" / "B02" / "technical_eligibility_contract.py"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("b02_p61_technical_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class B02P61EmitterPopulationImpactRepairTests(unittest.TestCase):
    def test_q_b02_004_stays_open_but_is_not_eligibility_precondition(self):
        with QUESTIONS.open(encoding="utf-8", newline="") as handle:
            rows = {row["question_id"]: row for row in csv.DictReader(handle)}
        q4 = rows["Q-B02-004"]
        self.assertEqual(q4["status"], "OPEN")
        self.assertIn("CAPEX", q4["decision_impact"])
        self.assertIn("COP", q4["decision_impact"])
        self.assertIn("Nem aggregate technical-eligibility előfeltétel", q4["decision_impact"])
        self.assertIn("CURRENT_REQUIRED_GAP_IDS=()", q4["notes"])
        self.assertIn("2026-08-22", q4["notes"])
        self.assertIn("record-level evidence", q4["notes"])

    def test_q_b02_001_no_longer_waits_for_emitter_mix(self):
        with QUESTIONS.open(encoding="utf-8", newline="") as handle:
            rows = {row["question_id"]: row for row in csv.DictReader(handle)}
        q1 = rows["Q-B02-001"]
        self.assertEqual(q1["status"], "OPEN")
        self.assertIn("reprezentatív", q1["evidence_needed"])
        self.assertIn("kalibrált", q1["evidence_needed"])
        self.assertIn("terminal PASS/FAIL", q1["evidence_needed"])
        self.assertIn("NEM előfeltétele", q1["notes"])
        self.assertIn("önmagában nem blocker", q1["notes"])

    def test_current_aggregate_gap_list_is_empty(self):
        module = load_module(TECHNICAL_CONTRACT)
        self.assertEqual(module.CURRENT_REQUIRED_GAP_IDS, ())

    def test_impact_registry_forbids_eligibility_promotion(self):
        with IMPACT.open(encoding="utf-8", newline="") as handle:
            rows = {row["surface_id"]: row for row in csv.DictReader(handle)}
        aggregate = rows["B02-P61-S09"]
        self.assertEqual(aggregate["current_status"], "OPEN")
        self.assertEqual(aggregate["eligibility_precondition"], "NO")
        self.assertIn("CAPEX", aggregate["allowed_uses"])
        self.assertIn("seasonal COP", aggregate["allowed_uses"])
        self.assertIn("TECHNICAL_INELIGIBILITY", aggregate["forbidden_promotion"])
        self.assertIn("NON_DISTRICT_HYDRONIC_EMITTER_MIX", aggregate["residual_gap"])
        self.assertIn("DESIGN_TEMPERATURE_DISTRIBUTION", aggregate["residual_gap"])

    def test_new_public_sources_are_boundary_only_not_numeric_prevalence(self):
        with AUDIT.open(encoding="utf-8", newline="") as handle:
            rows = {row["audit_id"]: row for row in csv.DictReader(handle)}
        for audit_id in ("B02-P61-A10", "B02-P61-A11", "B02-P61-A12"):
            self.assertEqual(rows[audit_id]["published_numeric_emitter_assignment"], "NO")
            self.assertEqual(rows[audit_id]["current_stock_complete"], "NO")
        self.assertIn("NO_PUBLISHED_EMITTER_CLASS", rows["B02-P61-A10"]["blockers"])
        self.assertIn("NO_NUMERIC_POPULATION_SHARE", rows["B02-P61-A11"]["blockers"])
        self.assertIn("NO_INSTALLED_STOCK_PREVALENCE", rows["B02-P61-A12"]["blockers"])

    def test_registered_source_authorities_exist(self):
        with SOURCES.open(encoding="utf-8", newline="") as handle:
            rows = {row["source_id"]: row for row in csv.DictReader(handle)}
        for source_id in (
            "SRC-B02-BME-RBSM-2026",
            "SRC-B02-ENERGIAKLUB-LAKCIMKE-2010",
            "SRC-B02-KSH-OSAP-1831-2026",
        ):
            self.assertIn(source_id, rows)
        self.assertEqual(rows["SRC-B02-KSH-OSAP-1831-2026"]["reliability"], "HIGH")

    def test_qualitative_prior_cannot_become_numeric_share(self):
        with IMPACT.open(encoding="utf-8", newline="") as handle:
            rows = {row["surface_id"]: row for row in csv.DictReader(handle)}
        prior = rows["B02-P61-S06"]
        self.assertEqual(prior["current_status"], "QUALIFIED_BOUNDARY_ONLY")
        self.assertEqual(prior["population_output_use"], "YES_AS_DIRECTIONAL_SENSITIVITY_ONLY")
        self.assertEqual(prior["forbidden_promotion"], "NUMERIC_POPULATION_SHARE")
        self.assertNotRegex(prior["notes"], r"\b\d{1,2}(?:\.\d+)?%\b")

    def test_module_status_keeps_readiness_and_correct_layer(self):
        with MODULE_STATUS.open(encoding="utf-8", newline="") as handle:
            rows = {row["module_id"]: row for row in csv.DictReader(handle)}
        b02 = rows["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("nem aggregate eligibility-precondition", b02["gate_note"])
        self.assertIn("CAPEX", b02["gate_note"])
        self.assertIn("CURRENT_REQUIRED_GAP_IDS=()", b02["gate_note"])

    def test_source_pack_freezes_core_non_equivalences(self):
        text = SOURCE_PACK.read_text(encoding="utf-8")
        for boundary in (
            "CURRENT EMITTER MIX != TECHNICAL ELIGIBILITY PRECONDITION",
            "CURRENT EMITTER NOT LOW-TEMP-READY != TECHNICALLY INELIGIBLE",
            "PREDOMINANT != NUMERIC SHARE",
            "CURRENT OFFICIAL TAXONOMY != INSTALLED STOCK DISTRIBUTION",
            "POPULATION EMITTER MIX -> PROGRAMME QUANTITY/COST/COP DISTRIBUTION",
            "RECORD TRANSITION DESIGN -> TECHNICAL PASS/Q/FAIL",
        ):
            self.assertIn(boundary, text)


if __name__ == "__main__":
    unittest.main()
