import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "registry/dso_node_inventory_sources.csv"
FACTS = ROOT / "registry/dso_published_node_facts_p23.csv"
AUTHORITIES = ROOT / "registry/dso_consumption_publication_authorities.csv"
CANONICAL = ROOT / "registry/dso_node_inventory.csv"
DOC = ROOT / "docs/source_packs/P23_B10_CONSUMPTION_NODE_PUBLICATION_EXPANSION.md"

EON_PUBLICATION_URL = (
    "https://www.eon.hu/hu/lakossagi/ugyintezes/kiemelt-informaciok/szabad-kapacitas.html"
)
CAPACITYPEDIA_EON = "https://www.tsodsoplatform.eu/capacitypedia/hungary/eon-hungary"


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


def test_current_law_remains_separate_from_p34_operator_url_authority():
    by_id = {row["authority_id"]: row for row in rows(AUTHORITIES)}
    duty = by_id["SRC-B10-HU-VHR-8-7-CAPACITY-PUBLICATION-2026"]
    assert duty["source_kind"] == "OFFICIAL_CURRENT_LEGAL_TEXT"
    assert duty["authorizes"] == "MV_HV_SUBSTATION_CAPACITY_PUBLICATION_DUTY"
    effective = by_id["SRC-B10-HU-VHR-126A6-EFFECTIVE-DATE-2026"]
    assert effective["authorizes"] == "MV_HV_PUBLICATION_DUTY_EFFECTIVE_FROM_2026-01-01"

    current_ids = {
        "ELMU": "SRC-B10-P34-ELMU-CONSUMPTION-PUBLICATION-2026",
        "EON_DDASZ": "SRC-B10-P34-EON-DDASZ-CONSUMPTION-PUBLICATION-2026",
        "EON_EDASZ": "SRC-B10-P34-EON-EDASZ-CONSUMPTION-PUBLICATION-2026",
    }
    for operator, authority_id in current_ids.items():
        row = by_id[authority_id]
        assert row["operator_id"] == operator
        assert row["source_url"] == CAPACITYPEDIA_EON
        assert row["source_kind"] == "ENTSOE_DSO_ENTITY_CAPACITYPEDIA_DSO_SUBMISSION"
        assert row["publication_url_status"] == "PINNED_CURRENT_2026"
        assert row["publication_url"] == EON_PUBLICATION_URL

    historical_q_ids = {
        "Q-B10-P23-ELMU-2026-CONSUMPTION-PUBLICATION-URL",
        "Q-B10-P23-EON-DDASZ-2026-CONSUMPTION-PUBLICATION-URL",
        "Q-B10-P23-EON-EDASZ-2026-CONSUMPTION-PUBLICATION-URL",
    }
    assert historical_q_ids.isdisjoint(by_id)


def test_eon_trio_is_now_bounded_but_inventory_completeness_remains_q():
    by_operator = {row["operator_id"]: row for row in rows(SOURCES)}
    for operator in ("ELMU", "EON_DDASZ", "EON_EDASZ"):
        row = by_operator[operator]
        assert row["node_source_status"] == "NODE_BEARING_SOURCE_BOUNDED"
        assert row["source_url"] == EON_PUBLICATION_URL
        assert row["source_semantics"] == "PUBLISHED_CONSUMPTION_HEADROOM_NODE_SET"
        assert row["inventory_completeness_status"] == "Q_INVENTORY_COMPLETENESS_UNPROVEN"


def test_existing_demasz_and_opus_bounded_sources_are_unchanged():
    by_operator = {row["operator_id"]: row for row in rows(SOURCES)}
    for operator in ("MVM_DEMASZ", "OPUS_TITASZ"):
        assert by_operator[operator]["node_source_status"] == "NODE_BEARING_SOURCE_BOUNDED"
        assert by_operator[operator]["source_semantics"] == "PUBLISHED_CONSUMPTION_HEADROOM_NODE_SET"
        assert by_operator[operator]["inventory_completeness_status"] == "Q_INVENTORY_COMPLETENESS_UNPROVEN"


def test_no_complete_inventory_is_minted():
    assert all(
        row["inventory_completeness_status"] != "COMPLETE_NODE_INVENTORY_PROVEN"
        for row in rows(SOURCES)
    )
    lines = CANONICAL.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1


def test_p23_document_remains_historical_and_preserves_original_boundaries():
    text = DOC.read_text(encoding="utf-8")
    assert "MANDATORY PUBLICATION DUTY != PINNED PUBLICATION URL != NODE-BEARING SOURCE != COMPLETE OPERATOR NODE INVENTORY" in text
    assert "ATTRIBUTED PUBLIC NODE FACT != COMPLETE NETWORK TOPOLOGY" in text
    assert "SEARCH ABSENCE != PUBLICATION ABSENCE != NON-COMPLIANCE" in text
    assert "126/A. § (6)" in text
    assert "Q_2026_MANDATORY_CONSUMPTION_PUBLICATION_URL_UNRESOLVED" in text
    assert "45 MVM Émász" in text
    assert "readiness remains **15**" in text
