import csv
from pathlib import Path
import unittest

from modules.B10.dso_node_inventory_contract import (
    B10NodeInventoryError,
    COMPLETE_OPERATOR_NODE_POPULATION,
    CURRENT_OPERATOR_IDS,
    DSO_SUBSTATION,
    DsoNodeIdentityRecord,
    EXACT_NODE_IDENTITY,
    NATIONAL_NODE_INVENTORY_COMPLETE,
    NODE_BEARING_SOURCE,
    NODE_BEARING_SOURCE_BOUNDED,
    NODE_IDENTITY_PROVEN,
    NodeInventoryEvidence,
    OPERATOR_NODE_INVENTORY_COMPLETE,
    OperatorNodeSourceDecision,
    OperatorNodeSourceRecord,
    Q_INVENTORY_COMPLETENESS_UNPROVEN,
    Q_NATIONAL_NODE_INVENTORY_INCOMPLETE,
    Q_NODE_IDENTITY_UNRESOLVED,
    Q_NODE_SOURCE_UNRESOLVED,
    assess_national_node_inventory,
    classify_node_identity,
    classify_operator_node_source,
    require_node_identity,
)


ROOT = Path(__file__).resolve().parents[1]


class B10P16DsoNodeInventoryTests(unittest.TestCase):
    def evidence(self, *supports, source_id="SRC", level=2, truth="DER"):
        return NodeInventoryEvidence(source_id, level, truth, tuple(supports))

    def node_record(self, *, operator_id="MVM_DEMASZ", node_id="MVM_DEMASZ:BAJA:132KV", key="BAJA|132KV", evidence=None):
        service_area_id = f"{operator_id}:SERVICE_AREA"
        ev = evidence or self.evidence(
            EXACT_NODE_IDENTITY,
            f"OPERATOR_ID:{operator_id}",
            f"SERVICE_AREA_ID:{service_area_id}",
            f"NODE_ID:{node_id}",
            f"SOURCE_NATIVE_KEY:{key}",
        )
        return DsoNodeIdentityRecord(
            operator_id=operator_id,
            network_operator="MVM Démász Áramhálózati Kft." if operator_id == "MVM_DEMASZ" else "OPUS TITÁSZ Áramhálózati Zrt.",
            service_area_id=service_area_id,
            node_id=node_id,
            node_label="Baja" if operator_id == "MVM_DEMASZ" else "Example",
            source_native_key=key,
            source_refs=(ev.source_id,),
            evidence=(ev,),
        )

    def source_record(self, operator_id, *, source=True, complete=False):
        supports = []
        if source:
            supports.extend((
                NODE_BEARING_SOURCE,
                f"OPERATOR_ID:{operator_id}",
                f"SERVICE_AREA_ID:{operator_id}:SERVICE_AREA",
            ))
        evidence = []
        refs = []
        if supports:
            evidence.append(self.evidence(*supports, source_id=f"SRC-{operator_id}"))
            refs.append(f"SRC-{operator_id}")
        if complete:
            evidence.append(self.evidence(
                COMPLETE_OPERATOR_NODE_POPULATION,
                f"OPERATOR_ID:{operator_id}",
                f"SERVICE_AREA_ID:{operator_id}:SERVICE_AREA",
                source_id=f"COMPLETE-{operator_id}",
                level=2,
                truth="OBS",
            ))
            refs.append(f"COMPLETE-{operator_id}")
        return OperatorNodeSourceRecord(
            operator_id=operator_id,
            network_operator=operator_id,
            service_area_id=f"{operator_id}:SERVICE_AREA",
            source_refs=tuple(refs),
            evidence=tuple(evidence),
        )

    def test_exact_source_native_node_identity_can_be_proven_without_completeness(self):
        decision = classify_node_identity(self.node_record())
        self.assertEqual(NODE_IDENTITY_PROVEN, decision.status)
        self.assertEqual("MVM_DEMASZ:BAJA:132KV", require_node_identity(decision))
        self.assertEqual(DSO_SUBSTATION, decision.node_kind)
        self.assertFalse(hasattr(decision, "inventory_complete"))
        self.assertFalse(hasattr(decision, "limiting_node"))

    def test_q_node_evidence_cannot_promote_identity(self):
        record = self.node_record(evidence=self.evidence("UNRESOLVED", truth="Q"))
        decision = classify_node_identity(record)
        self.assertEqual(Q_NODE_IDENTITY_UNRESOLVED, decision.status)
        self.assertIsNone(decision.node_id)
        with self.assertRaises(B10NodeInventoryError):
            require_node_identity(decision)

    def test_wrong_operator_scoped_node_identity_is_rejected(self):
        with self.assertRaisesRegex(B10NodeInventoryError, "operator-scoped"):
            self.node_record(operator_id="MVM_DEMASZ", node_id="OPUS_TITASZ:ABCD:Example")

    def test_service_area_is_not_a_node_identity(self):
        with self.assertRaisesRegex(B10NodeInventoryError, "operator-scoped"):
            self.node_record(node_id="MVM_DEMASZ_SERVICE_AREA")

    def test_node_bearing_source_is_not_inventory_completeness(self):
        decision = classify_operator_node_source(self.source_record("MVM_DEMASZ", source=True, complete=False))
        self.assertEqual(NODE_BEARING_SOURCE_BOUNDED, decision.source_status)
        self.assertEqual(Q_INVENTORY_COMPLETENESS_UNPROVEN, decision.inventory_status)

    def test_complete_operator_inventory_requires_separate_claim(self):
        decision = classify_operator_node_source(self.source_record("MVM_DEMASZ", source=True, complete=True))
        self.assertEqual(NODE_BEARING_SOURCE_BOUNDED, decision.source_status)
        self.assertEqual(OPERATOR_NODE_INVENTORY_COMPLETE, decision.inventory_status)

    def test_completeness_claim_without_node_source_does_not_promote(self):
        record = self.source_record("MVM_DEMASZ", source=False, complete=True)
        decision = classify_operator_node_source(record)
        self.assertEqual(Q_NODE_SOURCE_UNRESOLVED, decision.source_status)
        self.assertEqual(Q_INVENTORY_COMPLETENESS_UNPROVEN, decision.inventory_status)

    def test_national_inventory_remains_q_when_all_sources_exist_but_completeness_does_not(self):
        decisions = tuple(classify_operator_node_source(self.source_record(operator_id, source=True)) for operator_id in CURRENT_OPERATOR_IDS)
        result = assess_national_node_inventory(decisions)
        self.assertEqual(Q_NATIONAL_NODE_INVENTORY_INCOMPLETE, result.status)
        self.assertEqual(set(CURRENT_OPERATOR_IDS), set(result.source_covered_operator_ids))
        self.assertEqual((), result.complete_operator_ids)

    def test_future_national_completion_requires_all_six_complete_operator_populations(self):
        decisions = tuple(classify_operator_node_source(self.source_record(operator_id, source=True, complete=True)) for operator_id in CURRENT_OPERATOR_IDS)
        result = assess_national_node_inventory(decisions)
        self.assertEqual(NATIONAL_NODE_INVENTORY_COMPLETE, result.status)
        self.assertEqual(set(CURRENT_OPERATOR_IDS), set(result.complete_operator_ids))
        self.assertFalse(result.unresolved_source_operator_ids)
        self.assertFalse(result.incomplete_operator_ids)

    def test_missing_operator_and_duplicate_operator_fail_closed(self):
        five = tuple(
            OperatorNodeSourceDecision(operator_id, NODE_BEARING_SOURCE_BOUNDED, Q_INVENTORY_COMPLETENESS_UNPROVEN, "bounded")
            for operator_id in CURRENT_OPERATOR_IDS[:-1]
        )
        result = assess_national_node_inventory(five)
        self.assertEqual(Q_NATIONAL_NODE_INVENTORY_INCOMPLETE, result.status)
        self.assertIn(CURRENT_OPERATOR_IDS[-1], result.unresolved_source_operator_ids)
        with self.assertRaisesRegex(B10NodeInventoryError, "duplicate"):
            assess_national_node_inventory((five[0], five[0]))

    def test_source_manifest_covers_exact_six_operators_and_preserves_p17_refinements(self):
        with (ROOT / "registry/dso_node_inventory_sources.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(6, len(rows))
        self.assertEqual(set(CURRENT_OPERATOR_IDS), {row["operator_id"] for row in rows})
        by_operator = {row["operator_id"]: row for row in rows}
        bounded = {row["operator_id"] for row in rows if row["node_source_status"] == "NODE_BEARING_SOURCE_BOUNDED"}
        self.assertEqual({"MVM_DEMASZ", "OPUS_TITASZ"}, bounded)
        unresolved_discovery = {row["operator_id"] for row in rows if row["node_source_status"] == "Q_NODE_SOURCE_DISCOVERY_REQUIRED"}
        self.assertEqual({"EON_DDASZ", "EON_EDASZ"}, unresolved_discovery)
        self.assertEqual("Q_CONSUMPTION_NODE_SOURCE_UNRESOLVED", by_operator["ELMU"]["node_source_status"])
        self.assertEqual("Q_OPERATOR_NODE_TABLE_UNRESOLVED", by_operator["MVM_EMASZ"]["node_source_status"])
        self.assertTrue(all(row["inventory_completeness_status"] == Q_INVENTORY_COMPLETENESS_UNPROVEN for row in rows))

    def test_p1_p2_source_rows_are_not_labelled_complete_inventory(self):
        with (ROOT / "registry/dso_node_inventory_sources.csv").open(encoding="utf-8", newline="") as handle:
            rows = {row["operator_id"]: row for row in csv.DictReader(handle)}
        for operator_id in ("MVM_DEMASZ", "OPUS_TITASZ"):
            self.assertEqual("PUBLISHED_CONSUMPTION_HEADROOM_NODE_SET", rows[operator_id]["source_semantics"])
            self.assertEqual(Q_INVENTORY_COMPLETENESS_UNPROVEN, rows[operator_id]["inventory_completeness_status"])

    def test_national_node_inventory_registry_is_header_only(self):
        lines = (ROOT / "registry/dso_node_inventory.csv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))
        self.assertTrue(lines[0].startswith("operator_id,network_operator,service_area_id,node_id,"))


if __name__ == "__main__":
    unittest.main()
