import csv
import unittest
from pathlib import Path

from modules.B02.technical_component_authority import (
    B02ComponentAuthorityError,
    assess_authoritative_technical_eligibility,
    load_component_authority,
    validate_component_authority,
)
from modules.B02.technical_eligibility_contract import (
    ELECTRICAL,
    ELIGIBLE,
    HYDRAULIC,
    Q,
    THERMAL_DISTRIBUTION,
    PhysicalScopeEvidence,
    TechnicalComponentEvidence,
    TechnicalEligibilityRecord,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/b02_technical_component_authority.csv"
DOC = ROOT / "docs/source_packs/B02_P4_COMPONENT_AUTHORITY_HANDOFF.md"


class B02P4ComponentAuthorityHandoffTests(unittest.TestCase):
    def component(self, component_id, decision="PASS"):
        return TechnicalComponentEvidence(
            component_id=component_id,
            decision=decision,
            evidence_status="OBS" if decision != Q else Q,
            evidence_refs=(f"SRC-{component_id}",) if decision != Q else (),
            criterion_ref=f"CRIT-{component_id}",
        )

    def record(self, components=None):
        return TechnicalEligibilityRecord(
            record_id="REC-B02-P4-001",
            as_of="2026-09-05",
            physical_scope=PhysicalScopeEvidence(
                decision="IN_SCOPE",
                evidence_status="OBS",
                evidence_refs=("SRC-SCOPE",),
                criterion_ref="CRIT-SCOPE",
            ),
            components=components or (
                self.component(THERMAL_DISTRIBUTION),
                self.component(HYDRAULIC),
                self.component(ELECTRICAL),
            ),
        )

    def valid_producers(self):
        return {
            THERMAL_DISTRIBUTION: "B02",
            HYDRAULIC: "B06",
            ELECTRICAL: "B10",
        }

    def test_registry_exact_authority_partition(self):
        authority = load_component_authority()
        self.assertEqual({"B02"}, set(authority[THERMAL_DISTRIBUTION]))
        self.assertEqual({"B02", "B06"}, set(authority[HYDRAULIC]))
        self.assertEqual({"B08", "B10"}, set(authority[ELECTRICAL]))
        self.assertNotIn("PERMIT", authority)

        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = {row["component_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(4, len(rows))
        self.assertEqual(
            {"THERMAL_DISTRIBUTION", "HYDRAULIC", "ELECTRICAL", "PERMIT"},
            set(rows),
        )
        for component_id in ("THERMAL_DISTRIBUTION", "HYDRAULIC", "ELECTRICAL"):
            self.assertEqual("Q", rows[component_id]["current_authority_status"])
            self.assertEqual("B02", rows[component_id]["consumer_module"])
        self.assertEqual("CONTRACTED", rows["PERMIT"]["current_authority_status"])
        self.assertEqual("B01;B18", rows["PERMIT"]["consumer_module"])
        self.assertEqual("B18;B10", rows["PERMIT"]["permitted_producer_modules"])

    def test_b02_cannot_self_authorize_electrical(self):
        producers = self.valid_producers()
        producers[ELECTRICAL] = "B02"
        with self.assertRaises(B02ComponentAuthorityError):
            validate_component_authority(self.record(), producers)

    def test_permit_is_not_a_technical_producer_key_after_p59(self):
        producers = self.valid_producers()
        producers["PERMIT"] = "B18"
        with self.assertRaises(B02ComponentAuthorityError):
            validate_component_authority(self.record(), producers)

    def test_permitted_cross_module_producers_are_accepted(self):
        decision = assess_authoritative_technical_eligibility(
            self.record(), self.valid_producers()
        )
        self.assertEqual(ELIGIBLE, decision.status)

    def test_q_component_must_not_claim_a_producer(self):
        record = self.record(
            components=(
                self.component(THERMAL_DISTRIBUTION),
                self.component(HYDRAULIC),
                self.component(ELECTRICAL, decision=Q),
            )
        )
        producers = self.valid_producers()
        with self.assertRaises(B02ComponentAuthorityError):
            validate_component_authority(record, producers)
        producers.pop(ELECTRICAL)
        validate_component_authority(record, producers)

    def test_real_pass_or_fail_requires_explicit_producer(self):
        producers = self.valid_producers()
        producers.pop(ELECTRICAL)
        with self.assertRaises(B02ComponentAuthorityError):
            validate_component_authority(self.record(), producers)

    def test_unknown_producer_key_fails_closed(self):
        producers = self.valid_producers()
        producers["UNKNOWN"] = "B99"
        with self.assertRaises(B02ComponentAuthorityError):
            validate_component_authority(self.record(), producers)

    def test_document_freezes_cross_module_boundary(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "B02 != ELECTRICAL AUTHORITY",
            "B02 != PERMIT AUTHORITY",
            "Q != SELF-AUTHORIZATION",
            "Q-B02-001",
            "Q-B02-004",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
