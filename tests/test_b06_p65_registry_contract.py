import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry"
PACK = ROOT / "docs" / "source_packs" / "B06_P65_EMITTER_TEMPERATURE_AUTHORITY.md"


def rows(name):
    with (REGISTRY / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def by(rows_, key, value):
    return next(row for row in rows_ if row[key] == value)


def test_q_b06_008_is_resolved_without_claiming_national_coverage():
    question = by(rows("open_questions.csv"), "question_id", "Q-B06-008")
    assert question["status"] == "RESOLVED"
    notes = question["notes"].lower()
    assert "national household emitter coverage is not claimed" in notes
    assert "missing record-level evidence remains q" in notes


def test_p65_external_sources_are_registered_in_both_source_registries():
    canonical = {row["source_id"]: row for row in rows("sources.csv")}
    retrofit = {row["source_id"]: row for row in rows("retrofit_sources.csv")}
    required = {
        "SRC-B06-MCS-021-2-1-2015",
        "SRC-B06-HU-ULLOI411-MEP-2024",
    }
    assert required <= canonical.keys()
    assert required <= retrofit.keys()

    hu = canonical["SRC-B06-HU-ULLOI411-MEP-2024"]
    assert hu["evidence_status"] == "DER"
    assert hu["source_tier"] == "P2"
    assert "not retrofit evidence" in hu["notes"].lower()
    assert "not an engine default" in hu["notes"].lower()


def test_readiness_does_not_inflate_when_only_authority_blocker_is_closed():
    readiness = {row["component_id"]: row for row in rows("retrofit_readiness.csv")}
    supply = readiness["SUPPLY_TEMPERATURE_EFFECT"]
    handoff = readiness["B05_HANDOFF"]
    assert supply["status"] == "PARTIAL"
    assert supply["readiness_percent"] == "70"
    assert handoff["status"] == "PARTIAL"
    assert handoff["readiness_percent"] == "65"
    assert "national household emitter inventory coverage is still partial" in supply["notes"].lower()
    assert "population coverage remains partial" in handoff["notes"].lower()


def test_source_pack_preserves_non_equivalence_and_fail_closed_boundary():
    text = PACK.read_text(encoding="utf-8")
    assert "BUILDING-AVERAGE EMITTER CAPACITY" in text
    assert "!= ALL-ROOM ADEQUACY" in text
    assert "Q-B06-008 -> RESOLVED" in text
    assert "national household emitter coverage -> NOT CLAIMED" in text
    assert "individual record with missing evidence -> Q" in text

def test_b02_s2_bridge_uses_p65_as_record_transition_gate_not_national_precondition():
    bridge = {row["bridge_id"]: row for row in rows("b02_readiness_bridge.csv")}
    emitter = bridge["BR-B02-S2-HEAT-EMITTER"]
    temperature = bridge["BR-B02-S2-WATER-TEMPERATURE"]
    for row in (emitter, temperature):
        assert row["status"] == "CONTRACTED"
        assert row["evidence_status"] == "OBS/DER_PER_RECORD"
        assert row["required_for_gate"] == "yes"
        assert row["allow_inference"] == "no"
        assert "P65" in row["notes"]
        assert "missing" in row["notes"].lower()
        assert "q" in row["notes"].lower()


def test_national_stock_gaps_remain_visible_but_no_longer_block_gate_execution():
    gap_matrix = {row["gap_id"]: row for row in rows("b02_s0_s2_evidence_gap_matrix.csv")}
    assert gap_matrix["GAP-B02-S2-HEAT-EMITTER"]["evidence_status"] == "Q"
    assert gap_matrix["GAP-B02-S2-DESIGN-TEMPERATURE"]["evidence_status"] == "Q"

    technical = by(rows("b02_technical_eligibility_gate.csv"), "contract_id", "B02-P2-TECHNICAL-ELIGIBILITY")
    assert technical["blocking_gap_ids"] == ""
    assert technical["technical_eligible_dwellings"] == ""
    assert technical["technical_eligibility_status"] == "Q"
    assert "P65 retires current-stock emitter and design-temperature coverage as aggregate prerequisites" in technical["notes"]

