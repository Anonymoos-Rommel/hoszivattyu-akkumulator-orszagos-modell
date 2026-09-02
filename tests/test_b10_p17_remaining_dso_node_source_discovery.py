import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "registry" / "dso_node_inventory_sources.csv"
SOURCE_PACK = ROOT / "docs" / "source_packs" / "P17_B10_REMAINING_DSO_NODE_SOURCE_DISCOVERY.md"


def _rows():
    with SOURCES.open(encoding="utf-8", newline="") as handle:
        return {row["operator_id"]: row for row in csv.DictReader(handle)}


def test_p17_keeps_exact_six_operator_manifest():
    assert set(_rows()) == {
        "ELMU", "EON_DDASZ", "EON_EDASZ", "MVM_DEMASZ", "MVM_EMASZ", "OPUS_TITASZ"
    }


def test_elmu_generation_publication_does_not_promote_consumption_authority():
    row = _rows()["ELMU"]
    assert row["node_source_status"] == "Q_CONSUMPTION_NODE_SOURCE_UNRESOLVED"
    assert row["source_semantics"] == "OFFICIAL_GENERATION_SIDE_SUBSTATION_PUBLICATION_FAMILY_ONLY"
    assert row["inventory_completeness_status"] == "Q_INVENTORY_COMPLETENESS_UNPROVEN"


def test_eon_ddasz_and_edasz_remain_fail_closed():
    rows = _rows()
    for operator in ("EON_DDASZ", "EON_EDASZ"):
        assert rows[operator]["node_source_status"] == "Q_NODE_SOURCE_DISCOVERY_REQUIRED"
        assert rows[operator]["source_url"] == ""
        assert rows[operator]["inventory_completeness_status"] == "Q_INVENTORY_COMPLETENESS_UNPROVEN"


def test_mvm_emasz_named_node_evidence_is_not_operator_inventory():
    row = _rows()["MVM_EMASZ"]
    assert row["node_source_status"] == "Q_OPERATOR_NODE_TABLE_UNRESOLVED"
    assert row["source_semantics"] == "OFFICIAL_NAMED_SUBSTATION_PROJECT_EVIDENCE_ONLY"
    assert row["inventory_completeness_status"] == "Q_INVENTORY_COMPLETENESS_UNPROVEN"


def test_existing_consumption_node_sources_remain_bounded_not_complete():
    rows = _rows()
    for operator in ("MVM_DEMASZ", "OPUS_TITASZ"):
        assert rows[operator]["node_source_status"] == "NODE_BEARING_SOURCE_BOUNDED"
        assert rows[operator]["inventory_completeness_status"] == "Q_INVENTORY_COMPLETENESS_UNPROVEN"


def test_no_operator_is_promoted_to_complete_inventory():
    assert all(
        row["inventory_completeness_status"] != "COMPLETE_NODE_INVENTORY_PROVEN"
        for row in _rows().values()
    )


def test_source_pack_records_refined_blockers_and_no_readiness_uplift():
    text = SOURCE_PACK.read_text(encoding="utf-8")
    for blocker in (
        "ELMU_CONSUMPTION_NODE_SOURCE_UNRESOLVED",
        "EON_DDASZ_NODE_SOURCE_UNRESOLVED",
        "EON_EDASZ_NODE_SOURCE_UNRESOLVED",
        "MVM_EMASZ_OPERATOR_NODE_TABLE_UNRESOLVED",
        "NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY",
        "HEADROOM_NODE_SET_NOT_INVENTORY_COMPLETENESS",
    ):
        assert blocker in text
    assert "No operator receives `COMPLETE_NODE_INVENTORY_PROVEN`" in text
    assert "readiness uplift" in text
