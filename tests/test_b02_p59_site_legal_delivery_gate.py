import unittest

from modules.B02.site_legal_delivery_gate import (
    APPROVED,
    BLOCKED,
    NOT_REQUIRED,
    PENDING,
    Q,
    QUALIFIED,
    REFUSED,
    SiteLegalDeliveryCandidate,
    assess_site_legal_delivery,
)


def base_candidate():
    return SiteLegalDeliveryCandidate(
        record_id="REC-P59-001",
        national_building_rule_checked=True,
        local_townscape_rule_checked=True,
        local_clearance_status=NOT_REQUIRED,
        heritage_or_protected_status_checked=True,
        property_or_condominium_consent_status=NOT_REQUIRED,
        outdoor_unit_siting_documented=True,
        noise_compliance_basis_documented=True,
        condensate_or_water_disposal_documented=True,
        alternative_compliant_design_available=False,
        evidence_refs_present=True,
        reproducible_repository_binding=True,
    )


class B02P59SiteLegalDeliveryGateTests(unittest.TestCase):
    def test_not_required_clearances_can_qualify(self):
        decision = assess_site_legal_delivery(base_candidate())
        self.assertEqual(QUALIFIED, decision.status)
        self.assertEqual((), decision.reasons)

    def test_approved_clearances_can_qualify(self):
        c = base_candidate()
        candidate = SiteLegalDeliveryCandidate(
            **{
                **c.__dict__,
                "local_clearance_status": APPROVED,
                "property_or_condominium_consent_status": APPROVED,
            }
        )
        self.assertEqual(QUALIFIED, assess_site_legal_delivery(candidate).status)

    def test_pending_local_clearance_is_q(self):
        c = base_candidate()
        candidate = SiteLegalDeliveryCandidate(
            **{**c.__dict__, "local_clearance_status": PENDING}
        )
        decision = assess_site_legal_delivery(candidate)
        self.assertEqual(Q, decision.status)
        self.assertIn("LOCAL_CLEARANCE_PENDING", decision.reasons)

    def test_final_local_refusal_without_alternative_blocks(self):
        c = base_candidate()
        candidate = SiteLegalDeliveryCandidate(
            **{**c.__dict__, "local_clearance_status": REFUSED}
        )
        decision = assess_site_legal_delivery(candidate)
        self.assertEqual(BLOCKED, decision.status)
        self.assertEqual(("LOCAL_CLEARANCE_REFUSED_NO_ALTERNATIVE",), decision.reasons)

    def test_refusal_with_alternative_returns_q_for_redesign(self):
        c = base_candidate()
        candidate = SiteLegalDeliveryCandidate(
            **{
                **c.__dict__,
                "local_clearance_status": REFUSED,
                "alternative_compliant_design_available": True,
            }
        )
        decision = assess_site_legal_delivery(candidate)
        self.assertEqual(Q, decision.status)
        self.assertIn("ALTERNATIVE_DESIGN_REQUIRES_NEW_CLEARANCE", decision.reasons)

    def test_missing_noise_or_siting_basis_fails_closed(self):
        c = base_candidate()
        candidate = SiteLegalDeliveryCandidate(
            **{
                **c.__dict__,
                "outdoor_unit_siting_documented": False,
                "noise_compliance_basis_documented": False,
            }
        )
        decision = assess_site_legal_delivery(candidate)
        self.assertEqual(Q, decision.status)
        self.assertIn("OUTDOOR_UNIT_SITING_MISSING", decision.reasons)
        self.assertIn("NOISE_COMPLIANCE_BASIS_MISSING", decision.reasons)


if __name__ == "__main__":
    unittest.main()
