from dataclasses import replace
import unittest

from modules.B10.network_layer_authority_contract import (
    B10NetworkLayerAuthorityError,
    COORDINATED_TSO_DSO,
    DISTRIBUTION,
    DISTRIBUTION_LAYER,
    NetworkLayerEvidence,
    NetworkLayerRecord,
    Q_UNRESOLVED_NETWORK_LAYER,
    TRANSMISSION,
    TRANSMISSION_LAYER,
    TSO_DSO_INTERFACE,
    classify_network_layer,
)


class B10P7NetworkLayerAuthorityTests(unittest.TestCase):
    def evidence(self, source_id, *claims, truth_status="OBS", authority_level=2):
        return NetworkLayerEvidence(
            source_id=source_id,
            authority_level=authority_level,
            truth_status=truth_status,
            supports=claims,
        )

    def record(self, operator="MAVIR", voltage=132, evidence=(), refs=None, claimed_layer=None):
        project_id = "PROJECT-1"
        return NetworkLayerRecord(
            project_id=project_id,
            network_operator=operator,
            voltage_kv=voltage,
            source_refs=tuple(refs or [item.source_id for item in evidence]),
            evidence=tuple(evidence),
            claimed_layer=claimed_layer,
        )

    def bound_claims(self, operator, claim):
        return (claim, "PROJECT_ID:PROJECT-1", f"NETWORK_OPERATOR:{operator}")

    def test_voltage_alone_cannot_classify_network_layer(self):
        evidence = self.evidence("SRC", "VOLTAGE_KV:132")
        decision = classify_network_layer(self.record(evidence=(evidence,)))
        self.assertEqual(Q_UNRESOLVED_NETWORK_LAYER, decision.network_layer)
        self.assertEqual("Q", decision.evidence_status)

    def test_operator_name_alone_cannot_classify_network_layer(self):
        evidence = self.evidence("SRC", "OPERATOR_IDENTITY")
        decision = classify_network_layer(self.record(operator="MAVIR", evidence=(evidence,)))
        self.assertEqual(Q_UNRESOLVED_NETWORK_LAYER, decision.network_layer)

    def test_claim_specific_transmission_authority_classifies_transmission(self):
        evidence = self.evidence("SRC", *self.bound_claims("MAVIR", TRANSMISSION_LAYER))
        decision = classify_network_layer(self.record(operator="MAVIR", voltage=400, evidence=(evidence,)))
        self.assertEqual(TRANSMISSION, decision.network_layer)
        self.assertEqual("OBS", decision.evidence_status)

    def test_claim_specific_distribution_authority_classifies_distribution(self):
        evidence = self.evidence("SRC", *self.bound_claims("MVM DEMASZ", DISTRIBUTION_LAYER))
        decision = classify_network_layer(self.record(operator="MVM DEMASZ", voltage=132, evidence=(evidence,)))
        self.assertEqual(DISTRIBUTION, decision.network_layer)

    def test_same_voltage_can_exist_on_different_network_layers(self):
        tx = self.evidence("TX", *self.bound_claims("MAVIR", TRANSMISSION_LAYER))
        dx = self.evidence("DX", *self.bound_claims("MVM DEMASZ", DISTRIBUTION_LAYER))
        self.assertEqual(
            TRANSMISSION,
            classify_network_layer(self.record(operator="MAVIR", voltage=132, evidence=(tx,))).network_layer,
        )
        self.assertEqual(
            DISTRIBUTION,
            classify_network_layer(self.record(operator="MVM DEMASZ", voltage=132, evidence=(dx,))).network_layer,
        )

    def test_both_layers_require_explicit_interface_authority(self):
        tx = self.evidence("TX", *self.bound_claims("COORDINATED", TRANSMISSION_LAYER))
        dx = self.evidence("DX", *self.bound_claims("COORDINATED", DISTRIBUTION_LAYER))
        unresolved = classify_network_layer(self.record(operator="COORDINATED", evidence=(tx, dx)))
        self.assertEqual(Q_UNRESOLVED_NETWORK_LAYER, unresolved.network_layer)

        interface = self.evidence("IF", *self.bound_claims("COORDINATED", TSO_DSO_INTERFACE))
        coordinated = classify_network_layer(self.record(operator="COORDINATED", evidence=(tx, dx, interface)))
        self.assertEqual(COORDINATED_TSO_DSO, coordinated.network_layer)

    def test_interface_claim_cannot_supply_missing_other_layer(self):
        tx = self.evidence("TX", *self.bound_claims("MAVIR", TRANSMISSION_LAYER))
        interface = self.evidence("IF", *self.bound_claims("MAVIR", TSO_DSO_INTERFACE))
        decision = classify_network_layer(self.record(operator="MAVIR", evidence=(tx, interface)))
        self.assertEqual(Q_UNRESOLVED_NETWORK_LAYER, decision.network_layer)

    def test_wrong_project_or_operator_binding_fails_closed(self):
        wrong_project = self.evidence(
            "SRC1", TRANSMISSION_LAYER, "PROJECT_ID:OTHER", "NETWORK_OPERATOR:MAVIR"
        )
        wrong_operator = self.evidence(
            "SRC2", TRANSMISSION_LAYER, "PROJECT_ID:PROJECT-1", "NETWORK_OPERATOR:OTHER"
        )
        self.assertEqual(
            Q_UNRESOLVED_NETWORK_LAYER,
            classify_network_layer(self.record(evidence=(wrong_project,))).network_layer,
        )
        self.assertEqual(
            Q_UNRESOLVED_NETWORK_LAYER,
            classify_network_layer(self.record(evidence=(wrong_operator,))).network_layer,
        )

    def test_unreferenced_layer_evidence_cannot_authorize_classification(self):
        layer = self.evidence("LAYER", *self.bound_claims("MAVIR", TRANSMISSION_LAYER))
        generic = self.evidence("GENERIC", "PROJECT_ID:PROJECT-1", "NETWORK_OPERATOR:MAVIR")
        decision = classify_network_layer(
            self.record(operator="MAVIR", evidence=(layer, generic), refs=("GENERIC",))
        )
        self.assertEqual(Q_UNRESOLVED_NETWORK_LAYER, decision.network_layer)

    def test_q_evidence_cannot_promote_layer(self):
        evidence = self.evidence(
            "SRC", *self.bound_claims("MAVIR", TRANSMISSION_LAYER), truth_status="Q"
        )
        decision = classify_network_layer(self.record(evidence=(evidence,)))
        self.assertEqual(Q_UNRESOLVED_NETWORK_LAYER, decision.network_layer)

    def test_claimed_layer_must_match_evidence_decision(self):
        evidence = self.evidence("SRC", *self.bound_claims("MAVIR", TRANSMISSION_LAYER))
        record = self.record(operator="MAVIR", evidence=(evidence,), claimed_layer=DISTRIBUTION)
        with self.assertRaises(B10NetworkLayerAuthorityError):
            classify_network_layer(record)

    def test_network_layer_does_not_mint_project_attribution_or_capex(self):
        evidence = self.evidence("SRC", *self.bound_claims("MAVIR", TRANSMISSION_LAYER))
        decision = classify_network_layer(self.record(evidence=(evidence,)))
        self.assertFalse(hasattr(decision, "incremental_cost_huf"))
        self.assertFalse(hasattr(decision, "programme_causality_status"))
        self.assertFalse(hasattr(decision, "reinforcement_required"))


if __name__ == "__main__":
    unittest.main()
