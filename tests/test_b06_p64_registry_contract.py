import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "registry" / "open_questions.csv"
BRIDGE = ROOT / "registry" / "b02_readiness_bridge.csv"
AUTHORITY = ROOT / "registry" / "b06_p64_realized_completion_authority.csv"
REQUIREMENTS = ROOT / "registry" / "b06_p64_completion_requirements.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"


def by(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


def test_q_b06_009_is_resolved_as_completion_plus_outcome_contract():
    row = by(QUESTIONS, "question_id")["Q-B06-009"]
    assert row["status"] == "RESOLVED"
    assert "final invoice + performance confirmation" in row["notes"]
    assert "P60 separately proves" in row["notes"]


def test_s1_has_separate_realized_completion_and_outcome_bridges():
    rows = by(BRIDGE, "bridge_id")
    completion = rows["BR-B02-S1-REALIZED-COMPLETION"]
    outcome = rows["BR-B02-S1-DEMAND-OUTCOME"]
    assert completion["status"] == "CONTRACTED"
    assert completion["evidence_status"] == "OBS_PER_RECORD"
    assert completion["required_for_gate"] == "yes"
    assert outcome["status"] == "CONTRACTED"
    assert outcome["evidence_status"] == "OBS/DER_PER_RECORD"


def test_p57_p58_p59_stale_bridge_rows_are_repaired():
    rows = by(BRIDGE, "bridge_id")

    hydraulic = rows["BR-B02-S2-HYDRAULIC"]
    assert hydraulic["status"] == "CONTRACTED"
    assert "hydraulic_transition_gate.py" in hydraulic["current_source_or_registry"]
    assert hydraulic["block_reason"] == ""

    electrical = rows["BR-B02-S2-ELECTRICAL"]
    assert electrical["status"] == "CONTRACTED"
    assert "electrical_transition_gate.py" in electrical["current_source_or_registry"]
    assert electrical["block_reason"] == ""

    permit = rows["BR-B02-S2-PERMIT"]
    assert permit["status"] == "CONTRACTED"
    assert permit["required_for_gate"] == "no"
    assert "site_legal_delivery_gate.py" in permit["current_source_or_registry"]
    assert permit["state_id"] == "S2"
    assert permit["allow_inference"] == "no"
    assert "registry/b02_p59_site_legal_delivery_authority.csv" in permit["current_source_or_registry"]
    assert "mandatory separate site legal/delivery gate in programme orchestration" in permit["notes"]
    authority = by(ROOT / "registry" / "b02_p59_site_legal_delivery_authority.csv", "claim_id")["SITE_LEGAL_DELIVERY_AUTHORITY"]
    assert authority["current_status"] == "CONTRACTED"
    assert authority["authority_type"] == "LEGAL_DELIVERY_GATE"
    assert "local clearance status" in authority["required_inputs"]
    assert "reproducible binding" in authority["required_inputs"]
    # The discovered B02 P59 tests exercise PENDING=Q and final-refusal=BLOCKED.
    assert "PENDING=Q;" in authority["notes"]
    assert "final refusal without admitted alternative=BLOCKED" in authority["notes"]


def test_completion_authority_requires_both_document_layers():
    row = by(AUTHORITY, "claim_id")["REALIZED_S1_COMPLETION"]
    assert row["current_status"] == "CONTRACTED"
    assert "final invoice refs" in row["required_completion_artifacts"]
    assert "performance confirmation refs" in row["required_completion_artifacts"]
    assert "final HET refs" in row["required_completion_artifacts"]
    assert "P60 linked before/after outcome" in row["required_outcome_artifacts"]
    assert row["s1_rule"] == "REALIZED_COMPLETION_QUALIFIED AND S1_OUTCOME_READY"
    assert row["national_completed_stock_claim"] == "NO"


def test_completion_artifacts_do_not_collapse_roles():
    rows = by(REQUIREMENTS, "artifact_id")
    assert rows["P64-FINAL-INVOICE"]["evidence_status"] == "OBS"
    assert rows["P64-PERFORMANCE-CONFIRMATION"]["evidence_status"] == "OBS"
    assert rows["P64-FINAL-HET"]["evidence_status"] == "DER"
    assert rows["P64-FINAL-ENERGY-CALC"]["evidence_status"] == "DER"
    assert rows["P64-P60-OUTCOME"]["evidence_status"] == "OBS_OR_DER"


def test_readiness_percentage_is_not_uplifted_by_contract_only():
    row = by(READINESS, "component_id")["RETROFIT_CONTRACT"]
    assert row["readiness_percent"] == "70"
    assert "intentionally unchanged" in row["notes"]
    assert "SRC-B06-HU-KEHOP-417-COMPLETION-2025" in row["source_ids"]


def load_tests(loader, tests, pattern):
    """Admit the explicit legacy cases to the configured unittest runner."""
    import unittest

    tests.addTests(
        unittest.FunctionTestCase(test, description=f"{__name__}.{test.__name__}")
        for test in (
            test_completion_artifacts_do_not_collapse_roles,
            test_completion_authority_requires_both_document_layers,
            test_p57_p58_p59_stale_bridge_rows_are_repaired,
            test_q_b06_009_is_resolved_as_completion_plus_outcome_contract,
            test_readiness_percentage_is_not_uplifted_by_contract_only,
            test_s1_has_separate_realized_completion_and_outcome_bridges,
        )
    )
    return tests
