import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "registry" / "dso_node_inventory_sources.csv"
SOURCE_PACK = ROOT / "docs" / "source_packs" / "P17_B10_REMAINING_DSO_NODE_SOURCE_DISCOVERY.md"


def _rows():
    with SOURCES.open(encoding="utf-8", newline="") as handle:
        return {row["operator_id"]: row for row in csv.DictReader(handle)}


def _consumption_authorities():
    path = ROOT / "registry" / "dso_consumption_publication_authorities.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _assert_p34_consumption_authority(row, authorities):
    # A common URL, legal duty or generation publication is insufficient.
    expected_sources = {
        "ELMU": "SRC-B10-P34-ELMU-CONSUMPTION-PUBLICATION-2026",
        "EON_DDASZ": "SRC-B10-P34-EON-DDASZ-CONSUMPTION-PUBLICATION-2026",
        "EON_EDASZ": "SRC-B10-P34-EON-EDASZ-CONSUMPTION-PUBLICATION-2026",
    }
    assert row["source_id"] == expected_sources[row["operator_id"]]
    matches = [r for r in authorities if r["authority_id"] == row["source_id"]
               and r["operator_id"] == row["operator_id"]]
    assert len(matches) == 1
    authority = matches[0]
    assert authority["source_kind"] == "ENTSOE_DSO_ENTITY_CAPACITYPEDIA_DSO_SUBMISSION"
    assert authority["source_url"] == "https://www.tsodsoplatform.eu/capacitypedia/hungary/eon-hungary"
    assert authority["currentness_status"] == "CURRENT_2026"
    assert authority["authorizes"] == "EXACT_CURRENT_CONSUMPTION_PUBLICATION_URL"
    assert authority["publication_url_status"] == "PINNED_CURRENT_2026"
    assert authority["publication_url"] == row["source_url"] == (
        "https://www.eon.hu/hu/lakossagi/ugyintezes/kiemelt-informaciok/szabad-kapacitas.html"
    )
    assert row["node_source_status"] == "NODE_BEARING_SOURCE_BOUNDED"
    assert row["source_semantics"] == "PUBLISHED_CONSUMPTION_HEADROOM_NODE_SET"


def test_p17_keeps_exact_six_operator_manifest():
    assert set(_rows()) == {
        "ELMU", "EON_DDASZ", "EON_EDASZ", "MVM_DEMASZ", "MVM_EMASZ", "OPUS_TITASZ"
    }


def test_elmu_generation_publication_does_not_promote_consumption_authority_without_later_evidence():
    row = _rows()["ELMU"]
    _assert_p34_consumption_authority(row, _consumption_authorities())
    assert row["inventory_completeness_status"] == "Q_INVENTORY_COMPLETENESS_UNPROVEN"


def test_eon_ddasz_and_edasz_remain_fail_closed_until_exact_consumption_source_is_pinned():
    rows = _rows()
    for operator in ("EON_DDASZ", "EON_EDASZ"):
        _assert_p34_consumption_authority(rows[operator], _consumption_authorities())
        assert rows[operator]["inventory_completeness_status"] == "Q_INVENTORY_COMPLETENESS_UNPROVEN"


def test_mvm_emasz_p17_q_may_be_refined_by_later_current_source_evidence():
    row = _rows()["MVM_EMASZ"]
    assert row["node_source_status"] in {"Q_OPERATOR_NODE_TABLE_UNRESOLVED", "NODE_BEARING_SOURCE_BOUNDED"}
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


def test_source_pack_preserves_historical_p17_blockers_and_no_readiness_uplift():
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


def load_tests(loader, tests, pattern):
    """Admit the explicit legacy cases to the configured unittest runner."""
    import unittest

    tests.addTests(
        unittest.FunctionTestCase(test, description=f"{__name__}.{test.__name__}")
        for test in (
            test_elmu_generation_publication_does_not_promote_consumption_authority_without_later_evidence,
            test_eon_ddasz_and_edasz_remain_fail_closed_until_exact_consumption_source_is_pinned,
            test_existing_consumption_node_sources_remain_bounded_not_complete,
            test_mvm_emasz_p17_q_may_be_refined_by_later_current_source_evidence,
            test_no_operator_is_promoted_to_complete_inventory,
            test_p17_keeps_exact_six_operator_manifest,
            test_source_pack_preserves_historical_p17_blockers_and_no_readiness_uplift,
        )
    )
    return tests
