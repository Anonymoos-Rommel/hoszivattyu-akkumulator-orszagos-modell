import csv
import unittest
from pathlib import Path

from modules.B10.topology_endpoint_contract import (
    B10TopologyEndpointError,
    CANONICAL_DSO_NODE_LINK,
    CANONICAL_DSO_NODE_LINK_NOT_APPLICABLE,
    CANONICAL_DSO_NODE_LINK_PROVEN,
    DSO_SUBSTATION,
    NAMED_LINE,
    Q_CANONICAL_DSO_NODE_LINK_UNRESOLVED,
    Q_TOPOLOGY_ENDPOINT_UNRESOLVED,
    TOPOLOGY_ENDPOINT,
    TOPOLOGY_ENDPOINT_PROVEN,
    TSO_SUBSTATION,
    TopologyEndpointEvidence,
    TopologyEndpointRecord,
    classify_topology_endpoint,
    require_canonical_dso_node_link,
    require_topology_endpoint,
)


ROOT = Path(__file__).resolve().parents[1]
ENDPOINTS = ROOT / "registry/dso_topology_endpoint_facts.csv"
EDGES = ROOT / "registry/dso_topology_edge_facts.csv"
P19_FACTS = ROOT / "registry/dso_published_node_facts.csv"
P23_FACTS = ROOT / "registry/dso_published_node_facts_p23.csv"
CANONICAL_NODE_INVENTORY = ROOT / "registry/dso_node_inventory.csv"
DOC = ROOT / "docs/source_packs/P25_B10_TOPOLOGY_ENDPOINT_TYPING.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class TestB10P25TopologyEndpointTyping(unittest.TestCase):
    def test_exact_six_unique_p24_endpoints_are_typed(self):
        endpoints = rows(ENDPOINTS)
        self.assertEqual(len(endpoints), 6)
        self.assertEqual(len({row["endpoint_id"] for row in endpoints}), 6)
        self.assertTrue(all(row["status"] == TOPOLOGY_ENDPOINT_PROVEN for row in endpoints))
        self.assertTrue(all(row["evidence_status"] == "OBS" for row in endpoints))

        edge_endpoints = set()
        for edge in rows(EDGES):
            edge_endpoints.add(edge["endpoint_a"])
            edge_endpoints.add(edge["endpoint_b"])
        self.assertEqual(edge_endpoints, {row["endpoint_id"] for row in endpoints})

    def test_endpoint_kinds_preserve_dso_tso_and_named_line_semantics(self):
        by_id = {row["endpoint_id"]: row for row in rows(ENDPOINTS)}
        self.assertEqual(by_id["MVM_DEMASZ:CSON:132KV"]["endpoint_kind"], DSO_SUBSTATION)
        self.assertEqual(by_id["MVM_DEMASZ:SZEN:132KV"]["endpoint_kind"], DSO_SUBSTATION)
        self.assertEqual(by_id["MVM_EMASZ:MAKL"]["endpoint_kind"], DSO_SUBSTATION)
        self.assertEqual(
            by_id["OPUS_TITASZ:NYIREGYHAZA-NYIRJES:132/22KV"]["endpoint_kind"],
            DSO_SUBSTATION,
        )
        self.assertEqual(by_id["MAVIR:BUJ:400/132KV"]["endpoint_kind"], TSO_SUBSTATION)
        self.assertEqual(
            by_id["MVM_EMASZ:FUZESABONY-EGER-LINE:132KV"]["endpoint_kind"],
            NAMED_LINE,
        )

    def test_only_exact_existing_dso_node_facts_are_linked(self):
        p19_ids = {row["node_id"] for row in rows(P19_FACTS)}
        p23_ids = {row["node_id"] for row in rows(P23_FACTS)}
        known = p19_ids | p23_ids
        by_id = {row["endpoint_id"]: row for row in rows(ENDPOINTS)}

        for endpoint_id in (
            "MVM_DEMASZ:CSON:132KV",
            "MVM_DEMASZ:SZEN:132KV",
            "MVM_EMASZ:MAKL",
        ):
            row = by_id[endpoint_id]
            self.assertEqual(row["node_link_status"], CANONICAL_DSO_NODE_LINK_PROVEN)
            self.assertEqual(row["canonical_dso_node_ref"], endpoint_id)
            self.assertIn(endpoint_id, known)

        nyirjes = by_id["OPUS_TITASZ:NYIREGYHAZA-NYIRJES:132/22KV"]
        self.assertEqual(
            nyirjes["node_link_status"], Q_CANONICAL_DSO_NODE_LINK_UNRESOLVED
        )
        self.assertEqual(nyirjes["canonical_dso_node_ref"], "")
        self.assertNotIn(nyirjes["endpoint_id"], known)

    def test_non_dso_endpoints_cannot_be_promoted_to_dso_nodes(self):
        by_id = {row["endpoint_id"]: row for row in rows(ENDPOINTS)}
        for endpoint_id in (
            "MAVIR:BUJ:400/132KV",
            "MVM_EMASZ:FUZESABONY-EGER-LINE:132KV",
        ):
            row = by_id[endpoint_id]
            self.assertEqual(
                row["node_link_status"], CANONICAL_DSO_NODE_LINK_NOT_APPLICABLE
            )
            self.assertEqual(row["canonical_dso_node_ref"], "")

    def test_contract_proves_endpoint_and_separate_dso_node_link(self):
        supports = (
            TOPOLOGY_ENDPOINT,
            "ENDPOINT_ID:MVM_DEMASZ:CSON:132KV",
            f"ENDPOINT_KIND:{DSO_SUBSTATION}",
            "OPERATOR_CONTEXT_ID:MVM_DEMASZ",
            "SCOPE_ID:MVM_DEMASZ:SERVICE_AREA",
            "EDGE_REF:MVM_DEMASZ:CSONGRAD-SZENTES:132KV",
            CANONICAL_DSO_NODE_LINK,
            "CANONICAL_DSO_NODE_REF:MVM_DEMASZ:CSON:132KV",
        )
        evidence = TopologyEndpointEvidence("SRC-TEST", 2, "OBS", supports)
        record = TopologyEndpointRecord(
            endpoint_id="MVM_DEMASZ:CSON:132KV",
            endpoint_kind=DSO_SUBSTATION,
            operator_context_id="MVM_DEMASZ",
            scope_id="MVM_DEMASZ:SERVICE_AREA",
            edge_refs=("MVM_DEMASZ:CSONGRAD-SZENTES:132KV",),
            source_refs=("SRC-TEST",),
            evidence=(evidence,),
            canonical_dso_node_ref="MVM_DEMASZ:CSON:132KV",
        )
        decision = classify_topology_endpoint(record)
        self.assertEqual(decision.status, TOPOLOGY_ENDPOINT_PROVEN)
        self.assertEqual(decision.node_link_status, CANONICAL_DSO_NODE_LINK_PROVEN)
        self.assertEqual(require_topology_endpoint(decision), record.endpoint_id)
        self.assertEqual(
            require_canonical_dso_node_link(decision), record.canonical_dso_node_ref
        )

    def test_proven_dso_endpoint_can_keep_node_link_q(self):
        supports = (
            TOPOLOGY_ENDPOINT,
            "ENDPOINT_ID:OPUS_TITASZ:NYIREGYHAZA-NYIRJES:132/22KV",
            f"ENDPOINT_KIND:{DSO_SUBSTATION}",
            "OPERATOR_CONTEXT_ID:OPUS_TITASZ",
            "SCOPE_ID:OPUS_TITASZ:SERVICE_AREA",
            "EDGE_REF:OPUS_TITASZ:BUJ-NYIRJES:132KV",
        )
        record = TopologyEndpointRecord(
            endpoint_id="OPUS_TITASZ:NYIREGYHAZA-NYIRJES:132/22KV",
            endpoint_kind=DSO_SUBSTATION,
            operator_context_id="OPUS_TITASZ",
            scope_id="OPUS_TITASZ:SERVICE_AREA",
            edge_refs=("OPUS_TITASZ:BUJ-NYIRJES:132KV",),
            source_refs=("SRC-TEST",),
            evidence=(TopologyEndpointEvidence("SRC-TEST", 2, "OBS", supports),),
        )
        decision = classify_topology_endpoint(record)
        self.assertEqual(decision.status, TOPOLOGY_ENDPOINT_PROVEN)
        self.assertEqual(
            decision.node_link_status, Q_CANONICAL_DSO_NODE_LINK_UNRESOLVED
        )
        with self.assertRaises(B10TopologyEndpointError):
            require_canonical_dso_node_link(decision)

    def test_named_line_and_tso_endpoint_are_dso_node_link_not_applicable(self):
        for endpoint_id, endpoint_kind, operator, scope, edge_ref in (
            (
                "MVM_EMASZ:FUZESABONY-EGER-LINE:132KV",
                NAMED_LINE,
                "MVM_EMASZ",
                "MVM_EMASZ:SERVICE_AREA",
                "MVM_EMASZ:MAKLAR-FUZESABONY-EGER-INSERTION:132KV",
            ),
            (
                "MAVIR:BUJ:400/132KV",
                TSO_SUBSTATION,
                "MAVIR",
                "HU_TRANSMISSION_SYSTEM",
                "OPUS_TITASZ:BUJ-NYIRJES:132KV",
            ),
        ):
            supports = (
                TOPOLOGY_ENDPOINT,
                f"ENDPOINT_ID:{endpoint_id}",
                f"ENDPOINT_KIND:{endpoint_kind}",
                f"OPERATOR_CONTEXT_ID:{operator}",
                f"SCOPE_ID:{scope}",
                f"EDGE_REF:{edge_ref}",
            )
            record = TopologyEndpointRecord(
                endpoint_id=endpoint_id,
                endpoint_kind=endpoint_kind,
                operator_context_id=operator,
                scope_id=scope,
                edge_refs=(edge_ref,),
                source_refs=("SRC-TEST",),
                evidence=(TopologyEndpointEvidence("SRC-TEST", 2, "OBS", supports),),
            )
            decision = classify_topology_endpoint(record)
            self.assertEqual(decision.status, TOPOLOGY_ENDPOINT_PROVEN)
            self.assertEqual(
                decision.node_link_status, CANONICAL_DSO_NODE_LINK_NOT_APPLICABLE
            )
            self.assertIsNone(decision.canonical_dso_node_ref)

    def test_missing_endpoint_type_support_fails_closed(self):
        record = TopologyEndpointRecord(
            endpoint_id="MVM_DEMASZ:CSON:132KV",
            endpoint_kind=DSO_SUBSTATION,
            operator_context_id="MVM_DEMASZ",
            scope_id="MVM_DEMASZ:SERVICE_AREA",
            edge_refs=("MVM_DEMASZ:CSONGRAD-SZENTES:132KV",),
            source_refs=("SRC-TEST",),
            evidence=(
                TopologyEndpointEvidence(
                    "SRC-TEST",
                    2,
                    "OBS",
                    (
                        TOPOLOGY_ENDPOINT,
                        "ENDPOINT_ID:MVM_DEMASZ:CSON:132KV",
                        "OPERATOR_CONTEXT_ID:MVM_DEMASZ",
                        "SCOPE_ID:MVM_DEMASZ:SERVICE_AREA",
                        "EDGE_REF:MVM_DEMASZ:CSONGRAD-SZENTES:132KV",
                    ),
                ),
            ),
        )
        decision = classify_topology_endpoint(record)
        self.assertEqual(decision.status, Q_TOPOLOGY_ENDPOINT_UNRESOLVED)
        with self.assertRaises(B10TopologyEndpointError):
            require_topology_endpoint(decision)

    def test_contract_rejects_dso_node_ref_on_non_dso_endpoint(self):
        with self.assertRaises(B10TopologyEndpointError):
            TopologyEndpointRecord(
                endpoint_id="MAVIR:BUJ:400/132KV",
                endpoint_kind=TSO_SUBSTATION,
                operator_context_id="MAVIR",
                scope_id="HU_TRANSMISSION_SYSTEM",
                edge_refs=("OPUS_TITASZ:BUJ-NYIRJES:132KV",),
                source_refs=("SRC-TEST",),
                evidence=(TopologyEndpointEvidence("SRC-TEST", 2, "Q", ()),),
                canonical_dso_node_ref="MAVIR:BUJ:400/132KV",
            )

    def test_p25_does_not_mint_complete_topology_or_readiness(self):
        self.assertEqual(len(CANONICAL_NODE_INVENTORY.read_text(encoding="utf-8").splitlines()), 1)
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("TYPED ENDPOINTS != COMPLETE TOPOLOGY != CONNECTED COMPONENT", text)
        self.assertIn("does **not** compute", text)
        self.assertIn("integration_closure_contract.py` therefore remains unchanged", text)
        self.assertIn("readiness remains **15**", text)


if __name__ == "__main__":
    unittest.main()
