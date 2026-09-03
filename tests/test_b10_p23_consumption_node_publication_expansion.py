import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "registry/dso_node_inventory_sources.csv"
FACTS = ROOT / "registry/dso_published_node_facts_p23.csv"
CANONICAL = ROOT / "registry/dso_node_inventory.csv"
DOC = ROOT / "docs/source_packs/P23_B10_CONSUMPTION_NODE_PUBLICATION_EXPANSION.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_mvm_emasz_consumption_node_source_is_now_bounded():
    by_operator = {row["operator_id"]: row for row in rows(SOURCES)}
    emasz = by_operator["MVM_EMASZ"]
    assert emasz["node_source_status"] == "NODE_BEARING_SOURCE_BOUNDED"
    assert emasz["source_id"] == "SRC-B10-MVM-EMASZ-CONSUMPTION-HEADROOM-2026"
    assert emasz["source_semantics"] == "PUBLISHED_CONSUMPTION_HEADROOM_NODE_SET"
    assert emasz["inventory_completeness_status"] == "Q_INVENTORY_COMPLETENESS_UNPROVEN"


def test_exact_45_emasz_public_node_identity_facts_are_materialized():
    facts = rows(FACTS)
    assert len(facts) == 45
    assert {row["operator_id"] for row in facts} == {"MVM_EMASZ"}
    assert all(row["evidence_status"] == "OBS" for row in facts)
    assert all(row["status"] == "NODE_IDENTITY_PROVEN" for row in facts)
    assert all(row["node_kind"] == "DSO_SUBSTATION" for row in facts)
    assert len({row["node_id"] for row in facts}) == 45
    by_id = {row["node_id"]: row for row in facts}
    for node_id in (
        "MVM_EMASZ:BABR",
        "MVM_EMASZ:BGYA",
        "MVM_EMASZ:EGER22",
        "MVM_EMASZ:JBER",
        "MVM_EMASZ:MDEL",
        "MVM_EMASZ:MAKL",
        "MVM_EMASZ:MBOG",
        "MVM_EMASZ:EGKE",
    ):
        assert node_id in by_id


def test_eon_trio_blocker_is_narrowed_to_exact_2026_consumption_publication_url():
    by_operator = {row["operator_id"]: row for row in rows(SOURCES)}
    for operator in ("ELMU", "EON_DDASZ", "EON_EDASZ"):
        assert by_operator[operator]["node_source_status"] == "Q_2026_MANDATORY_CONSUMPTION_PUBLICATION_URL_UNRESOLVED"
        assert by_operator[operator]["inventory_completeness_status"] == "Q_INVENTORY_COMPLETENESS_UNPROVEN"


def test_existing_demasz_and_opus_bounded_sources_are_unchanged():
    by_operator = {row["operator_id"]: row for row in rows(SOURCES)}
    for operator in ("MVM_DEMASZ", "OPUS_TITASZ"):
        assert by_operator[operator]["node_source_status"] == "NODE_BEARING_SOURCE_BOUNDED"
        assert by_operator[operator]["source_semantics"] == "PUBLISHED_CONSUMPTION_HEADROOM_NODE_SET"
        assert by_operator[operator]["inventory_completeness_status"] == "Q_INVENTORY_COMPLETENESS_UNPROVEN"


def test_no_complete_inventory_is_minted():
    assert all(row["inventory_completeness_status"] != "COMPLETE_NODE_INVENTORY_PROVEN" for row in rows(SOURCES))
    lines = CANONICAL.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1


def test_p23_document_preserves_mandatory_publication_and_completeness_boundaries():
    text = DOC.read_text(encoding="utf-8")
    assert "MANDATORY PUBLICATION DUTY != PINNED PUBLICATION URL != NODE-BEARING SOURCE != COMPLETE OPERATOR NODE INVENTORY" in text
    assert "ATTRIBUTED PUBLIC NODE FACT != COMPLETE NETWORK TOPOLOGY" in text
    assert "MVM_EMASZ_OPERATOR_NODE_TABLE_UNRESOLVED" in text
    assert "Q_2026_MANDATORY_CONSUMPTION_PUBLICATION_URL_UNRESOLVED" in text
    assert "45 MVM Émász" in text
    assert "readiness remains **15**" in text
