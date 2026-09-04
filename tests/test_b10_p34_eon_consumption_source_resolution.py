import csv
from pathlib import Path

from modules.B10.integration_closure_contract import (
    OUTPUT_LIMITING_NODES,
    Q_UNRESOLVED,
    current_b10_closure_assessment,
)


ROOT = Path(__file__).resolve().parents[1]
AUTHORITIES = ROOT / "registry" / "dso_consumption_publication_authorities.csv"
SOURCES = ROOT / "registry" / "dso_node_inventory_sources.csv"
CANONICAL_INVENTORY = ROOT / "registry" / "dso_node_inventory.csv"
DOC = ROOT / "docs" / "source_packs" / "P34_B10_EON_CONSUMPTION_SOURCE_RESOLUTION.md"

CAPACITYPEDIA_EON = "https://www.tsodsoplatform.eu/capacitypedia/hungary/eon-hungary"
EON_PUBLICATION_URL = (
    "https://www.eon.hu/hu/lakossagi/ugyintezes/kiemelt-informaciok/szabad-kapacitas.html"
)
EON_OPERATORS = ("ELMU", "EON_DDASZ", "EON_EDASZ")
P23_URL_BLOCKERS = {
    "Q-B10-P23-ELMU-2026-CONSUMPTION-PUBLICATION-URL",
    "Q-B10-P23-EON-DDASZ-2026-CONSUMPTION-PUBLICATION-URL",
    "Q-B10-P23-EON-EDASZ-2026-CONSUMPTION-PUBLICATION-URL",
}


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_p34_pins_exact_current_eon_publication_for_all_three_dsos():
    by_operator = {
        row["operator_id"]: row
        for row in rows(AUTHORITIES)
        if row["operator_id"] in EON_OPERATORS
    }
    assert set(by_operator) == set(EON_OPERATORS)
    for operator in EON_OPERATORS:
        row = by_operator[operator]
        assert row["source_url"] == CAPACITYPEDIA_EON
        assert row["source_kind"] == "ENTSOE_DSO_ENTITY_CAPACITYPEDIA_DSO_SUBMISSION"
        assert row["currentness_status"] == "CURRENT_2026"
        assert row["authorizes"] == "EXACT_CURRENT_CONSUMPTION_PUBLICATION_URL"
        assert row["publication_url_status"] == "PINNED_CURRENT_2026"
        assert row["publication_url"] == EON_PUBLICATION_URL


def test_all_six_dso_rows_now_have_bounded_consumption_node_sources():
    source_rows = rows(SOURCES)
    assert len(source_rows) == 6
    assert {
        row["operator_id"] for row in source_rows
    } == {"ELMU", "EON_DDASZ", "EON_EDASZ", "MVM_DEMASZ", "MVM_EMASZ", "OPUS_TITASZ"}
    assert all(row["node_source_status"] == "NODE_BEARING_SOURCE_BOUNDED" for row in source_rows)
    assert all(
        row["source_semantics"] == "PUBLISHED_CONSUMPTION_HEADROOM_NODE_SET"
        for row in source_rows
    )


def test_eon_source_resolution_does_not_mint_inventory_completeness():
    by_operator = {row["operator_id"]: row for row in rows(SOURCES)}
    for operator in EON_OPERATORS:
        assert by_operator[operator]["inventory_completeness_status"] == (
            "Q_INVENTORY_COMPLETENESS_UNPROVEN"
        )
    inventory_lines = CANONICAL_INVENTORY.read_text(encoding="utf-8").splitlines()
    assert len(inventory_lines) == 1


def test_p34_does_not_materialize_eon_node_rows():
    p34_fact_files = list((ROOT / "registry").glob("*p34*node*facts*.csv"))
    assert p34_fact_files == []


def test_closure_audit_removes_only_the_eon_url_discovery_blockers():
    assessment = current_b10_closure_assessment()
    blockers = set(assessment.blocking_refs)
    assert P23_URL_BLOCKERS.isdisjoint(blockers)
    for blocker in (
        "NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY",
        "PUBLISHED_NODE_SET_REPOSITORY_MATERIALIZATION_BLOCKED",
        "HEADROOM_NODE_SET_NOT_INVENTORY_COMPLETENESS",
        "NO_REAL_PROGRAMME_NODE_PANEL",
        "NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY",
        "NO_REAL_TIMED_PROGRAMME_CAPEX",
    ):
        assert blocker in blockers
    assert assessment.readiness_percent == 15
    assert assessment.module_status == "IN_PROGRESS"


def test_limiting_node_output_remains_q_after_source_resolution():
    assessment = current_b10_closure_assessment()
    gate = next(item for item in assessment.output_gates if item.gate_id == OUTPUT_LIMITING_NODES)
    assert gate.status == Q_UNRESOLVED
    assert "B10-P34" in gate.canonical_refs
    assert P23_URL_BLOCKERS.isdisjoint(gate.blocking_refs)
    assert "NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY" in gate.blocking_refs
    assert "NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY" in gate.blocking_refs


def test_p34_source_pack_is_explicitly_evidence_only_and_fail_closed():
    text = DOC.read_text(encoding="utf-8")
    assert "P34 is an evidence-only slice" in text
    assert "It introduces no new authority contract or semantic gate" in text
    assert CAPACITYPEDIA_EON in text
    assert EON_PUBLICATION_URL in text
    for blocker in P23_URL_BLOCKERS:
        assert blocker in text
    assert "NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY" in text
    assert "OFFICIAL CURRENT PAGE PINNED != SOURCE-NATIVE ROWS EXTRACTED" in text
    assert "readiness remains **15%**" in text
