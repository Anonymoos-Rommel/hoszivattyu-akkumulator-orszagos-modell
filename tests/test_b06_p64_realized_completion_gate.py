import unittest

from modules.B06.realized_completion_gate import (
    BLOCKED,
    OBS,
    Q,
    QUALIFIED,
    RealizedCompletionEvidence,
    assess_realized_completion,
)


def completed(**changes):
    values = dict(
        record_id="HU-REC-001",
        intervention_id="RETROFIT-001",
        project_id="KEHOP-417-TEST-001",
        site_link_id="SITE-HRSZ-001",
        completion_evidence_status=OBS,
        physical_completion_date="2026-06-30",
        final_het_date="2026-07-05",
        contract_scope_ids=("WALL", "ROOF", "WINDOW"),
        realized_scope_ids=("WALL", "ROOF", "WINDOW"),
        final_invoice_refs=("FINAL-INVOICE-001",),
        performance_confirmation_refs=("PERFORMANCE-CONFIRMATION-001",),
        final_het_refs=("HET-FINAL-001",),
        final_energy_calculation_refs=("HET-CALC-FINAL-001",),
        verifier_id="TE-VERIFIER-001",
        final_het_record_link="HU-REC-001",
        final_het_site_link="SITE-HRSZ-001",
        physical_completion_declared=True,
        reproducible_repository_binding=True,
    )
    values.update(changes)
    return RealizedCompletionEvidence(**values)


class B06P64RealizedCompletionGateTests(unittest.TestCase):
    def test_complete_document_chain_qualifies(self):
        decision = assess_realized_completion(completed())
        self.assertEqual(QUALIFIED, decision.status)
        self.assertEqual(OBS, decision.evidence_status)
        self.assertEqual((), decision.reasons)

    def test_final_invoice_without_final_het_is_not_completion_authority(self):
        decision = assess_realized_completion(completed(final_het_refs=()))
        self.assertEqual(Q, decision.status)
        self.assertIn("FINAL_HET_REFS_MISSING", decision.reasons)

    def test_final_het_without_delivery_proof_is_not_completion_authority(self):
        decision = assess_realized_completion(
            completed(
                final_invoice_refs=(),
                performance_confirmation_refs=(),
            )
        )
        self.assertEqual(Q, decision.status)
        self.assertIn("FINAL_INVOICE_REFS_MISSING", decision.reasons)
        self.assertIn("PERFORMANCE_CONFIRMATION_REFS_MISSING", decision.reasons)

    def test_final_het_must_follow_physical_completion(self):
        decision = assess_realized_completion(
            completed(final_het_date="2026-06-20")
        )
        self.assertEqual(Q, decision.status)
        self.assertIn("FINAL_HET_PRECEDES_PHYSICAL_COMPLETION", decision.reasons)

    def test_unapproved_scope_deviation_is_blocked(self):
        decision = assess_realized_completion(
            completed(realized_scope_ids=("WALL", "ROOF"))
        )
        self.assertEqual(BLOCKED, decision.status)
        self.assertIn("UNAPPROVED_SCOPE_DEVIATION", decision.reasons)

    def test_approved_scope_change_requires_reference(self):
        decision = assess_realized_completion(
            completed(
                realized_scope_ids=("WALL", "ROOF"),
                scope_amendment_approved=True,
                scope_amendment_refs=(),
            )
        )
        self.assertEqual(Q, decision.status)
        self.assertIn("SCOPE_AMENDMENT_REFS_MISSING", decision.reasons)

    def test_final_het_must_link_same_record_and_site(self):
        decision = assess_realized_completion(
            completed(
                final_het_record_link="OTHER",
                final_het_site_link="OTHER-SITE",
            )
        )
        self.assertEqual(Q, decision.status)
        self.assertIn("FINAL_HET_RECORD_LINK_MISMATCH", decision.reasons)
        self.assertIn("FINAL_HET_SITE_LINK_MISMATCH", decision.reasons)


if __name__ == "__main__":
    unittest.main()
