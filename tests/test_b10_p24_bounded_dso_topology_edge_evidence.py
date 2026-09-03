import csv
import unittest
from pathlib import Path

from modules.B10.dso_topology_edge_contract import (
    B10TopologyEdgeError,
    DsoTopologyEdgeRecord,
    NAMED_LINE_SEGMENT,
    Q_TOPOLOGY_EDGE_UNRESOLVED,
    SUBSTATION_INSERTION_INTO_NAMED_LINE,
    SUBSTATION_TO_SUBSTATION_LINE,
    TOPOLOGY_EDGE,
    TOPOLOGY_EDGE_PROVEN,
    TopologyEdgeEvidence,
    classify_topology_edge,
    require_topology_edge,
)


ROOT = Path(__file__).resolve().parents[1]
FACTS = ROOT / "registry/dso_topology_edge_facts.csv"
DOC = ROOT / "docs/source_packs/P24_B10_BOUNDED_DSO_TOPOLOGY_EDGE_EVIDENCE.md"
CANONICAL_NODE_INVENTORY = ROOT / "registry/dso_node_inventory.csv"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def evidence_for(record, truth_status="OBS", authority_level=2):
    return TopologyEdgeEvidence(
        source_id="SRC-TEST",
        authority_level=authority_level,
        truth_status=truth_status,
        supports=(
            TOPOLOGY_EDGE,
            f"OPERATOR_ID:{record.operator_id}",
            f"SERVICE_AREA_ID:{record.service_area_id}",
            f"EDGE_ID:{record.edge_id}",
            f"ENDPOINT_A:{record.endpoint_a}",
            f"ENDPOINT_B:{record.endpoint_b}",
            f"EDGE_KIND:{record.edge_kind}",
            f"VOLTAGE_KV:{record.voltage_kv}",
        ),
    )


def make_record(edge_kind=SUBSTATION_TO_SUBSTATION_LINE):
    provisional = DsoTopologyEdgeRecord(
        operator_id="MVM_DEMASZ",
        service_area_id="MVM_DEMASZ:SERVICE_AREA",
        edge_id="MVM_DEMASZ:TEST:132KV",
        endpoint_a="MVM_DEMASZ:A:132KV",
        endpoint_b="MVM_DEMASZ:B:132KV",
        edge_kind=edge_kind,
        voltage_kv=132,
        source_refs=("SRC-TEST",),
        evidence=(TopologyEdgeEvidence("SRC-TEST", 2, "Q", ()),),
    )
    return DsoTopologyEdgeRecord(
        operator_id=provisional.operator_id,
        service_area_id=provisional.service_area_id,
        edge_id=provisional.edge_id,
        endpoint_a=provisional.endpoint_a,
        endpoint_b=provisional.endpoint_b,
        edge_kind=provisional.edge_kind,
        voltage_kv=provisional.voltage_kv,
        source_refs=provisional.source_refs,
        evidence=(evidence_for(provisional),),
    )


class B10P24TopologyEdgeTests(unittest.TestCase):
    def test_exact_three_first_tranche_topology_facts_are_materialized(self):
        facts = rows(FACTS)
        self.assertEqual(len(facts), 3)
        self.assertEqual(
            {row["operator_id"] for row in facts},
            {"MVM_DEMASZ", "MVM_EMASZ", "OPUS_TITASZ"},
        )
        self.assertTrue(all(row["evidence_status"] == "OBS" for row in facts))
        self.assertTrue(all(row["status"] == "TOPOLOGY_EDGE_PROVEN" for row in facts))
        self.assertTrue(all(row["voltage_kv"] == "132" for row in facts))

    def test_demasz_edge_is_exact_csongrad_szentes_substation_connection(self):
        edge = {row["edge_id"]: row for row in rows(FACTS)}[
            "MVM_DEMASZ:CSONGRAD-SZENTES:132KV"
        ]
        self.assertEqual(edge["endpoint_a"], "MVM_DEMASZ:CSON:132KV")
        self.assertEqual(edge["endpoint_b"], "MVM_DEMASZ:SZEN:132KV")
        self.assertEqual(edge["edge_kind"], SUBSTATION_TO_SUBSTATION_LINE)

    def test_emasz_preserves_named_line_instead_of_inventing_endpoint_substations(self):
        edge = {row["edge_id"]: row for row in rows(FACTS)}[
            "MVM_EMASZ:MAKLAR-FUZESABONY-EGER-INSERTION:132KV"
        ]
        self.assertEqual(edge["endpoint_a"], "MVM_EMASZ:MAKL")
        self.assertEqual(edge["endpoint_b"], "MVM_EMASZ:FUZESABONY-EGER-LINE:132KV")
        self.assertEqual(edge["edge_kind"], SUBSTATION_INSERTION_INTO_NAMED_LINE)
        self.assertNotIn("FUZESABONY:132KV", edge["endpoint_b"])
        self.assertNotIn("EGER:132KV", edge["endpoint_b"])

    def test_opus_preserves_cross_operator_mavir_buj_endpoint(self):
        edge = {row["edge_id"]: row for row in rows(FACTS)}[
            "OPUS_TITASZ:BUJ-NYIRJES:132KV"
        ]
        self.assertEqual(edge["endpoint_a"], "MAVIR:BUJ:400/132KV")
        self.assertEqual(edge["endpoint_b"], "OPUS_TITASZ:NYIREGYHAZA-NYIRJES:132/22KV")
        self.assertEqual(edge["edge_kind"], SUBSTATION_TO_SUBSTATION_LINE)

    def test_exact_authority_can_prove_one_bounded_edge(self):
        decision = classify_topology_edge(make_record())
        self.assertEqual(decision.status, TOPOLOGY_EDGE_PROVEN)
        self.assertEqual(decision.evidence_status, "OBS")
        self.assertEqual(decision.voltage_kv, 132)
        self.assertEqual(
            require_topology_edge(decision),
            ("MVM_DEMASZ:A:132KV", "MVM_DEMASZ:B:132KV"),
        )

    def test_missing_exact_support_fails_closed_and_withholds_endpoints(self):
        record = make_record()
        weak = TopologyEdgeEvidence(
            source_id="SRC-TEST",
            authority_level=2,
            truth_status="OBS",
            supports=(
                TOPOLOGY_EDGE,
                f"OPERATOR_ID:{record.operator_id}",
                f"SERVICE_AREA_ID:{record.service_area_id}",
                f"EDGE_ID:{record.edge_id}",
                f"ENDPOINT_A:{record.endpoint_a}",
                f"EDGE_KIND:{record.edge_kind}",
                f"VOLTAGE_KV:{record.voltage_kv}",
            ),
        )
        unresolved = DsoTopologyEdgeRecord(
            operator_id=record.operator_id,
            service_area_id=record.service_area_id,
            edge_id=record.edge_id,
            endpoint_a=record.endpoint_a,
            endpoint_b=record.endpoint_b,
            edge_kind=record.edge_kind,
            voltage_kv=record.voltage_kv,
            source_refs=("SRC-TEST",),
            evidence=(weak,),
        )
        decision = classify_topology_edge(unresolved)
        self.assertEqual(decision.status, Q_TOPOLOGY_EDGE_UNRESOLVED)
        self.assertIsNone(decision.endpoint_a)
        self.assertIsNone(decision.endpoint_b)
        self.assertIsNone(decision.voltage_kv)
        with self.assertRaises(B10TopologyEdgeError):
            require_topology_edge(decision)

    def test_q_or_low_authority_evidence_cannot_mint_topology(self):
        record = make_record()
        for truth_status, authority_level in (("Q", 2), ("OBS", 4)):
            with self.subTest(truth_status=truth_status, authority_level=authority_level):
                candidate = DsoTopologyEdgeRecord(
                    operator_id=record.operator_id,
                    service_area_id=record.service_area_id,
                    edge_id=record.edge_id,
                    endpoint_a=record.endpoint_a,
                    endpoint_b=record.endpoint_b,
                    edge_kind=record.edge_kind,
                    voltage_kv=record.voltage_kv,
                    source_refs=("SRC-TEST",),
                    evidence=(
                        evidence_for(
                            record,
                            truth_status=truth_status,
                            authority_level=authority_level,
                        ),
                    ),
                )
                self.assertEqual(
                    classify_topology_edge(candidate).status,
                    Q_TOPOLOGY_EDGE_UNRESOLVED,
                )

    def test_contract_rejects_self_edge_and_invalid_voltage(self):
        with self.assertRaises(B10TopologyEdgeError):
            DsoTopologyEdgeRecord(
                operator_id="MVM_DEMASZ",
                service_area_id="MVM_DEMASZ:SERVICE_AREA",
                edge_id="MVM_DEMASZ:SELF:132KV",
                endpoint_a="MVM_DEMASZ:A:132KV",
                endpoint_b="MVM_DEMASZ:A:132KV",
                edge_kind=NAMED_LINE_SEGMENT,
                voltage_kv=132,
                source_refs=("SRC-TEST",),
                evidence=(TopologyEdgeEvidence("SRC-TEST", 2, "Q", ()),),
            )
        with self.assertRaises(B10TopologyEdgeError):
            DsoTopologyEdgeRecord(
                operator_id="MVM_DEMASZ",
                service_area_id="MVM_DEMASZ:SERVICE_AREA",
                edge_id="MVM_DEMASZ:BAD:0KV",
                endpoint_a="MVM_DEMASZ:A",
                endpoint_b="MVM_DEMASZ:B",
                edge_kind=NAMED_LINE_SEGMENT,
                voltage_kv=0,
                source_refs=("SRC-TEST",),
                evidence=(TopologyEdgeEvidence("SRC-TEST", 2, "Q", ()),),
            )

    def test_p24_does_not_promote_node_inventory_or_readiness(self):
        self.assertEqual(
            len(CANONICAL_NODE_INVENTORY.read_text(encoding="utf-8").splitlines()),
            1,
        )
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("BOUNDED TOPOLOGY EDGES != COMPLETE DSO TOPOLOGY", text)
        self.assertIn(
            "TOPOLOGY EDGE != POWER FLOW DIRECTION != THERMAL CAPACITY != HEADROOM != LIMITING NODE != PROGRAMME REINFORCEMENT REQUIREMENT != PROGRAMME-INCREMENTAL CAPEX",
            text,
        )
        self.assertIn("integration_closure_contract.py` is intentionally unchanged", text)
        self.assertIn("readiness remains **15**", text)


if __name__ == "__main__":
    unittest.main()
