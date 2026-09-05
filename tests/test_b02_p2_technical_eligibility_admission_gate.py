from pathlib import Path
import csv
import unittest

from modules.B02.technical_eligibility_contract import (
    BLOCKED,
    ELECTRICAL,
    ELIGIBLE,
    HYDRAULIC,
    OUT_OF_SCOPE,
    PERMIT,
    Q,
    S2_BLOCKED,
    S2_Q,
    S2_READY,
    THERMAL_DISTRIBUTION,
    B02EligibilityError,
    PhysicalScopeEvidence,
    PredecessorGateEvidence,
    TechnicalComponentEvidence,
    TechnicalEligibilityRecord,
    assess_current_repository_gate,
    assess_s2_transition_readiness,
    assess_technical_eligibility,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/b02_technical_eligibility_gate.csv"
VARIABLES = ROOT / "registry/variables.csv"
DOC = ROOT / "docs/source_packs/B02_P2_TECHNICAL_ELIGIBILITY_ADMISSION_GATE.md"


class B02P2TechnicalEligibilityAdmissionGateTests(unittest.TestCase):
    def scope(self, decision="IN_SCOPE", evidence_status="OBS"):
        refs = ("SRC-SCOPE",) if decision != Q else ()
        return PhysicalScopeEvidence(
            decision=decision,
            evidence_status=evidence_status,
            evidence_refs=refs,
            criterion_ref="CRIT-PHYSICAL-SCOPE",
        )

    def component(self, component_id, decision="PASS", evidence_status="OBS"):
        refs = (f"SRC-{component_id}",) if decision != Q else ()
        return TechnicalComponentEvidence(
            component_id=component_id,
            decision=decision,
            evidence_status=evidence_status,
            evidence_refs=refs,
            criterion_ref=f"CRIT-{component_id}",
        )

    def record(self, **changes):
        values = {
            "record_id": "REC-B02-P2-001",
            "as_of": "2026-09-05",
            "physical_scope": self.scope(),
            "components": (
                self.component(THERMAL_DISTRIBUTION),
                self.component(HYDRAULIC),
                self.component(ELECTRICAL),
                self.component(PERMIT),
            ),
        }
        values.update(changes)
        return TechnicalEligibilityRecord(**values)

    def test_all_required_real_components_pass_to_eligible(self):
        decision = assess_technical_eligibility(self.record())
        self.assertEqual(ELIGIBLE, decision.status)
        self.assertEqual("OBS", decision.evidence_status)
        self.assertEqual((), decision.blocked_components)
        self.assertEqual((), decision.unresolved_components)

    def test_any_q_component_keeps_record_q_not_failed(self):
        components = (
            self.component(THERMAL_DISTRIBUTION),
            self.component(HYDRAULIC, decision=Q, evidence_status=Q),
            self.component(ELECTRICAL),
            self.component(PERMIT),
        )
        decision = assess_technical_eligibility(self.record(components=components))
        self.assertEqual(Q, decision.status)
        self.assertEqual(Q, decision.evidence_status)
        self.assertEqual((HYDRAULIC,), decision.unresolved_components)
        self.assertEqual((), decision.blocked_components)

    def test_explicit_fail_requires_real_evidence_and_blocks(self):
        components = (
            self.component(THERMAL_DISTRIBUTION),
            self.component(HYDRAULIC, decision="FAIL", evidence_status="DER"),
            self.component(ELECTRICAL, decision=Q, evidence_status=Q),
            self.component(PERMIT, decision=Q, evidence_status=Q),
        )
        decision = assess_technical_eligibility(self.record(components=components))
        self.assertEqual(BLOCKED, decision.status)
        self.assertEqual("DER", decision.evidence_status)
        self.assertEqual((HYDRAULIC,), decision.blocked_components)
        self.assertEqual((), decision.unresolved_components)

    def test_assumption_or_scenario_cannot_prove_real_pass_or_fail(self):
        for evidence_status in ("ASS", "SCN", "POL"):
            with self.assertRaises(B02EligibilityError):
                self.component(HYDRAULIC, decision="PASS", evidence_status=evidence_status).validate()
            with self.assertRaises(B02EligibilityError):
                self.component(HYDRAULIC, decision="FAIL", evidence_status=evidence_status).validate()

    def test_out_of_scope_is_not_relabelled_as_technical_fail(self):
        components = tuple(
            self.component(component_id, decision=Q, evidence_status=Q)
            for component_id in (THERMAL_DISTRIBUTION, HYDRAULIC, ELECTRICAL, PERMIT)
        )
        decision = assess_technical_eligibility(
            self.record(physical_scope=self.scope(decision=OUT_OF_SCOPE), components=components)
        )
        self.assertEqual(OUT_OF_SCOPE, decision.status)
        self.assertEqual("OBS", decision.evidence_status)
        self.assertEqual((), decision.blocked_components)

    def test_exact_component_set_is_required(self):
        with self.assertRaises(B02EligibilityError):
            assess_technical_eligibility(
                self.record(
                    components=(
                        self.component(THERMAL_DISTRIBUTION),
                        self.component(HYDRAULIC),
                        self.component(ELECTRICAL),
                    )
                )
            )

    def test_s2_requires_both_technical_eligibility_and_s1_predecessor(self):
        eligible = assess_technical_eligibility(self.record())
        self.assertEqual(
            S2_Q,
            assess_s2_transition_readiness(
                eligible,
                PredecessorGateEvidence(decision=Q, evidence_status=Q, evidence_refs=()),
            ).status,
        )
        self.assertEqual(
            S2_READY,
            assess_s2_transition_readiness(
                eligible,
                PredecessorGateEvidence(
                    decision="PASS", evidence_status="DER", evidence_refs=("SRC-S1",)
                ),
            ).status,
        )
        blocked = assess_technical_eligibility(
            self.record(
                components=(
                    self.component(THERMAL_DISTRIBUTION),
                    self.component(HYDRAULIC, decision="FAIL", evidence_status="OBS"),
                    self.component(ELECTRICAL),
                    self.component(PERMIT),
                )
            )
        )
        self.assertEqual(
            S2_BLOCKED,
            assess_s2_transition_readiness(
                blocked,
                PredecessorGateEvidence(
                    decision="PASS", evidence_status="OBS", evidence_refs=("SRC-S1",)
                ),
            ).status,
        )

    def test_current_repository_gate_is_q_with_exact_physical_reference(self):
        gate = assess_current_repository_gate()
        self.assertEqual(Q, gate.status)
        self.assertIsNone(gate.eligible_dwellings)
        self.assertEqual(3_389_817, gate.physical_screening_reference_households)
        self.assertEqual("DER_FROM_OBS_WBL011_CELLS", gate.physical_screening_reference_status)
        self.assertEqual(
            (
                "GAP-B02-S2-HEAT-EMITTER",
                "GAP-B02-S2-DESIGN-TEMPERATURE",
                "GAP-B02-S2-HYDRAULIC",
                "GAP-B02-S2-ELECTRICAL",
                "GAP-B02-S2-PERMIT",
            ),
            gate.blocking_gap_ids,
        )

    def test_registry_and_variable_stay_fail_closed(self):
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("3389817", row["physical_screening_reference_households"])
        self.assertEqual("", row["technical_eligible_dwellings"])
        self.assertEqual("Q", row["technical_eligibility_status"])
        self.assertEqual("S2_Q", row["s2_transition_status"])

        with VARIABLES.open(encoding="utf-8", newline="") as handle:
            variables = {item["variable_id"]: item for item in csv.DictReader(handle)}
        eligible = variables["VAR-B02-ELIGIBLE-DWELLINGS"]
        self.assertEqual("", eligible["default_value"])
        self.assertEqual("Q", eligible["status"])
        self.assertIn("műszaki", eligible["definition"].lower())
        self.assertIn("jogi/gazdasági", eligible["notes"].lower())

    def test_document_freezes_core_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "PHYSICAL SCREENING SCOPE != TECHNICAL ELIGIBILITY != S2 TRANSITION READINESS != LEGAL/ECONOMIC PROGRAMME ELIGIBILITY",
            "3,389,817",
            "TECHNICALLY_ELIGIBLE != S2_TRANSITION_READY",
            "Q-B02-001",
            "Q-B02-004",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
