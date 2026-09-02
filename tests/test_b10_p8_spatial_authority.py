import unittest

from modules.B10.spatial_authority_contract import (
    ADMINISTRATIVE_ONLY,
    AMBIGUOUS_OR_MULTI_SUPPLY,
    B10SpatialAuthorityError,
    CONTROL_AREA_ONLY,
    DSO_SERVICE_AREA_MEMBERSHIP,
    EXACT_DSO_SUBSTATION_MAPPING,
    EXACT_NODE_PROVEN,
    PROXIMITY_ONLY,
    Q_EXACT_NODE_UNRESOLVED,
    Q_SERVICE_AREA_UNRESOLVED,
    SERVICE_AREA_PROVEN,
    SpatialAuthorityEvidence,
    SpatialAuthorityRecord,
    classify_spatial_authority,
    require_exact_dso_substation_mapping,
)


class B10P8SpatialAuthorityTests(unittest.TestCase):
    def evidence(self, source_id, *claims, truth_status="OBS", authority_level=2):
        return SpatialAuthorityEvidence(
            source_id=source_id,
            authority_level=authority_level,
            truth_status=truth_status,
            supports=claims,
        )

    def record(
        self,
        *,
        evidence,
        refs=None,
        service_area_id="MVM_DEMASZ_SERVICE_AREA",
        node_id="MVM_DEMASZ:ABCD:132KV",
        confidence_score=None,
        admin="HU-CS",
        household="HH-1",
        b08=("10YHU-MAVIR----U", "ENTSOE_CONTROL_AREA"),
    ):
        return SpatialAuthorityRecord(
            entity_id="HH-1",
            network_operator="MVM DEMASZ",
            service_area_id=service_area_id,
            target_node_region_id=node_id,
            source_refs=tuple(refs or [item.source_id for item in evidence]),
            evidence=tuple(evidence),
            administrative_region_id=admin,
            household_location_id=household,
            b08_region_id=b08[0] if b08 else None,
            b08_region_scheme=b08[1] if b08 else None,
            confidence_score=confidence_score,
        )

    def service_claims(self):
        return (
            DSO_SERVICE_AREA_MEMBERSHIP,
            "ENTITY_ID:HH-1",
            "NETWORK_OPERATOR:MVM DEMASZ",
            "SERVICE_AREA_ID:MVM_DEMASZ_SERVICE_AREA",
        )

    def node_claims(self):
        return (
            EXACT_DSO_SUBSTATION_MAPPING,
            "ENTITY_ID:HH-1",
            "NETWORK_OPERATOR:MVM DEMASZ",
            "NODE_REGION_ID:MVM_DEMASZ:ABCD:132KV",
            "NODE_REGION_GRAIN:DSO_SUBSTATION",
        )

    def test_administrative_location_does_not_prove_service_area_or_node(self):
        evidence = self.evidence("ADMIN", ADMINISTRATIVE_ONLY, "ENTITY_ID:HH-1")
        decision = classify_spatial_authority(self.record(evidence=(evidence,)))
        self.assertEqual(Q_SERVICE_AREA_UNRESOLVED, decision.service_area_status)
        self.assertEqual(Q_EXACT_NODE_UNRESOLVED, decision.exact_node_status)

    def test_control_area_is_not_dso_service_area_or_substation(self):
        evidence = self.evidence("B08", CONTROL_AREA_ONLY, "ENTITY_ID:HH-1")
        decision = classify_spatial_authority(self.record(evidence=(evidence,)))
        self.assertEqual(Q_SERVICE_AREA_UNRESOLVED, decision.service_area_status)
        self.assertEqual(Q_EXACT_NODE_UNRESOLVED, decision.exact_node_status)

    def test_service_area_membership_does_not_mint_exact_substation(self):
        evidence = self.evidence("SERVICE", *self.service_claims())
        decision = classify_spatial_authority(self.record(evidence=(evidence,)))
        self.assertEqual(SERVICE_AREA_PROVEN, decision.service_area_status)
        self.assertEqual(Q_EXACT_NODE_UNRESOLVED, decision.exact_node_status)
        self.assertIsNone(decision.target_node_region_id)

    def test_nearest_node_and_confidence_cannot_mint_authority(self):
        evidence = self.evidence("GIS", PROXIMITY_ONLY, "ENTITY_ID:HH-1")
        decision = classify_spatial_authority(
            self.record(evidence=(evidence,), confidence_score=0.999999)
        )
        self.assertEqual(Q_EXACT_NODE_UNRESOLVED, decision.exact_node_status)

    def test_exact_node_requires_claim_specific_entity_operator_node_binding(self):
        service = self.evidence("SERVICE", *self.service_claims())
        node = self.evidence("NODE", *self.node_claims())
        decision = classify_spatial_authority(self.record(evidence=(service, node)))
        self.assertEqual(SERVICE_AREA_PROVEN, decision.service_area_status)
        self.assertEqual(EXACT_NODE_PROVEN, decision.exact_node_status)
        self.assertEqual("MVM_DEMASZ:ABCD:132KV", require_exact_dso_substation_mapping(decision))

    def test_wrong_node_binding_fails_closed(self):
        wrong = self.evidence(
            "NODE",
            EXACT_DSO_SUBSTATION_MAPPING,
            "ENTITY_ID:HH-1",
            "NETWORK_OPERATOR:MVM DEMASZ",
            "NODE_REGION_ID:MVM_DEMASZ:OTHER:132KV",
            "NODE_REGION_GRAIN:DSO_SUBSTATION",
        )
        decision = classify_spatial_authority(self.record(evidence=(wrong,)))
        self.assertEqual(Q_EXACT_NODE_UNRESOLVED, decision.exact_node_status)

    def test_unreferenced_exact_mapping_cannot_authorize_node(self):
        node = self.evidence("NODE", *self.node_claims())
        generic = self.evidence("GENERIC", "ENTITY_ID:HH-1")
        decision = classify_spatial_authority(
            self.record(evidence=(node, generic), refs=("GENERIC",))
        )
        self.assertEqual(Q_EXACT_NODE_UNRESOLVED, decision.exact_node_status)

    def test_q_evidence_cannot_promote_exact_node(self):
        node = self.evidence("NODE", *self.node_claims(), truth_status="Q")
        decision = classify_spatial_authority(self.record(evidence=(node,)))
        self.assertEqual(Q_EXACT_NODE_UNRESOLVED, decision.exact_node_status)

    def test_weak_authority_cannot_promote_exact_node(self):
        node = self.evidence("NODE", *self.node_claims(), authority_level=4)
        decision = classify_spatial_authority(self.record(evidence=(node,)))
        self.assertEqual(Q_EXACT_NODE_UNRESOLVED, decision.exact_node_status)

    def test_ambiguous_or_multi_supply_forces_exact_node_to_q(self):
        node = self.evidence("NODE", *self.node_claims())
        ambiguity = self.evidence("AMB", AMBIGUOUS_OR_MULTI_SUPPLY, "ENTITY_ID:HH-1")
        decision = classify_spatial_authority(self.record(evidence=(node, ambiguity)))
        self.assertEqual(Q_EXACT_NODE_UNRESOLVED, decision.exact_node_status)
        self.assertIn("ambiguous", decision.reason)

    def test_headroom_handoff_fails_without_exact_node(self):
        service = self.evidence("SERVICE", *self.service_claims())
        decision = classify_spatial_authority(self.record(evidence=(service,)))
        with self.assertRaisesRegex(B10SpatialAuthorityError, "exact DSO_SUBSTATION"):
            require_exact_dso_substation_mapping(decision)

    def test_spatial_decision_does_not_mint_other_b10_authorities(self):
        node = self.evidence("NODE", *self.node_claims())
        decision = classify_spatial_authority(self.record(evidence=(node,)))
        self.assertFalse(hasattr(decision, "grid_headroom_mw"))
        self.assertFalse(hasattr(decision, "reinforcement_required"))
        self.assertFalse(hasattr(decision, "program_incremental_capex_huf"))
        self.assertFalse(hasattr(decision, "network_layer"))
        self.assertFalse(hasattr(decision, "readiness_percent"))

    def test_b08_region_pair_is_fail_closed(self):
        evidence = self.evidence("GENERIC", "ENTITY_ID:HH-1")
        with self.assertRaisesRegex(B10SpatialAuthorityError, "supplied together"):
            SpatialAuthorityRecord(
                entity_id="HH-1",
                network_operator="MVM DEMASZ",
                service_area_id=None,
                target_node_region_id=None,
                source_refs=("GENERIC",),
                evidence=(evidence,),
                b08_region_id="10YHU-MAVIR----U",
                b08_region_scheme=None,
            )


if __name__ == "__main__":
    unittest.main()
