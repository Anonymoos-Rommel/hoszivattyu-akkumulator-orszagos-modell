from pathlib import Path
import unittest

from modules.B10.managed_flex_survivability_contract import (
    MANAGED_NODE_LOAD_PROVEN,
    ManagedNodeLoadResult,
)
from modules.B10.managed_peak_study_input_contract import (
    ManagedPeakStudyInputDecision,
    ManagedPeakStudyNode,
    REAL_MANAGED_PEAK_STUDY_INPUT_PROVEN,
)
from modules.B10.programme_node_demand_contract import (
    NODE_DEMAND_PROVEN,
    ProgrammeNodeDemandResult,
)
from modules.B10.survivability_study_result_contract import (
    NETWORK_SURVIVABILITY_STUDY_RESULT,
    Q_REAL_SURVIVABILITY_STUDY_RESULT_UNRESOLVED,
    REAL_SURVIVABILITY_STUDY_RESULT_PROVEN,
    B10SurvivabilityStudyResultError,
    SurvivabilityStudyResultEvidence,
    SurvivabilityStudyResultRecord,
    certify_real_survivability_study_result,
    require_real_survivability_study_result,
    require_survivability_node_result,
)


ROOT = Path(__file__).resolve().parents[1]
NODE1 = "MVM_DEMASZ:CSON:132KV"
NODE2 = "MVM_DEMASZ:SZEN:132KV"
OPERATOR = "MVM_DEMASZ"
STUDY = "NS-REAL-1"
CASE = "CASE-REAL-1"
INPUT = "INPUT-REAL-1"
HORIZON = "CURRENT"


def p28_input(nodes=((NODE1, 0.006), (NODE2, 0.004))):
    unmanaged = ProgrammeNodeDemandResult(
        status=NODE_DEMAND_PROVEN,
        scope="BOUNDED_EXPLICIT_PANEL",
        scope_id="PROGRAMME:REAL:2026:PILOT-A",
        truth_context="REAL",
        rows=(),
        peaks=(),
        unresolved_entity_ids=(),
        source_refs=("programme",),
        reason="fixture",
    )
    managed = ManagedNodeLoadResult(
        status=MANAGED_NODE_LOAD_PROVEN,
        scope_id="PROGRAMME:REAL:2026:PILOT-A",
        truth_context="REAL",
        unmanaged=unmanaged,
        rows=(),
        peak_managed_import_mw_by_node=tuple(nodes),
        source_refs=("programme", "flex"),
        reason="fixture",
    )
    study_nodes = tuple(ManagedPeakStudyNode(node, peak, "OBS") for node, peak in nodes)
    return ManagedPeakStudyInputDecision(
        study_input_id=INPUT,
        network_operator=OPERATOR,
        network_study_id=STUDY,
        study_case_id=CASE,
        panel_id="PANEL-1",
        programme_id="PROGRAMME-1",
        cohort_id="COHORT-1",
        scope_id="PROGRAMME:REAL:2026:PILOT-A",
        horizon=HORIZON,
        truth_context="REAL",
        status=REAL_MANAGED_PEAK_STUDY_INPUT_PROVEN,
        evidence_status="OBS",
        nodes=study_nodes,
        managed_load_result=managed,
        source_refs=("study-input",),
        reason="fixture proven P28 input",
    )


def result_record(node, peak, *, case=CASE, horizon=HORIZON, study=STUDY, input_id=INPUT, authoritative=True):
    source_id = f"result:{node}"
    supports = [
        NETWORK_SURVIVABILITY_STUDY_RESULT,
        "NETWORK_SURVIVABILITY",
        f"SURVIVABILITY_RESULT_ID:RESULT:{node}",
        f"STUDY_INPUT_ID:{input_id}",
        f"NETWORK_OPERATOR:{OPERATOR}",
        f"NETWORK_STUDY_ID:{study}",
        f"STUDY_CASE_ID:{case}",
        f"HORIZON:{horizon}",
        "TRUTH_CONTEXT:REAL",
        f"NODE_REGION_ID:{node}",
        "NODE_REGION_GRAIN:DSO_SUBSTATION",
        f"ASSESSED_MANAGED_PEAK_MW:{peak}",
    ]
    if not authoritative:
        supports.remove(NETWORK_SURVIVABILITY_STUDY_RESULT)
    evidence = SurvivabilityStudyResultEvidence(
        source_id=source_id,
        authority_level=1,
        truth_status="OBS",
        supports=tuple(supports),
    )
    return SurvivabilityStudyResultRecord(
        survivability_result_id=f"RESULT:{node}",
        study_input_id=input_id,
        network_operator=OPERATOR,
        network_study_id=study,
        study_case_id=case,
        horizon=horizon,
        node_region_id=node,
        assessed_managed_peak_mw=peak,
        source_refs=(source_id,),
        evidence=(evidence,),
    )


class B10P29SurvivabilityStudyResultAdmissionTests(unittest.TestCase):
    def test_complete_exact_p28_node_set_can_be_proven(self):
        decision = certify_real_survivability_study_result(
            p28_input(),
            (result_record(NODE1, 0.006), result_record(NODE2, 0.004)),
        )
        self.assertEqual(REAL_SURVIVABILITY_STUDY_RESULT_PROVEN, decision.status)
        self.assertEqual("OBS", decision.evidence_status)
        self.assertEqual(2, decision.expected_node_count)
        self.assertEqual(2, decision.actual_node_count)
        self.assertFalse(decision.missing_node_ids)
        self.assertFalse(decision.extra_node_ids)
        self.assertEqual({NODE1, NODE2}, {item.node_region_id for item in decision.node_results})

    def test_missing_result_node_is_q_not_survivability(self):
        decision = certify_real_survivability_study_result(
            p28_input(),
            (result_record(NODE1, 0.006),),
        )
        self.assertEqual(Q_REAL_SURVIVABILITY_STUDY_RESULT_UNRESOLVED, decision.status)
        self.assertEqual((NODE2,), decision.missing_node_ids)
        self.assertEqual((), decision.node_results)

    def test_extra_result_node_is_rejected(self):
        decision = certify_real_survivability_study_result(
            p28_input(((NODE1, 0.006),)),
            (result_record(NODE1, 0.006), result_record(NODE2, 0.004)),
        )
        self.assertEqual(Q_REAL_SURVIVABILITY_STUDY_RESULT_UNRESOLVED, decision.status)
        self.assertEqual((NODE2,), decision.extra_node_ids)

    def test_duplicate_result_node_is_rejected(self):
        decision = certify_real_survivability_study_result(
            p28_input(((NODE1, 0.006),)),
            (result_record(NODE1, 0.006), result_record(NODE1, 0.006)),
        )
        self.assertEqual(Q_REAL_SURVIVABILITY_STUDY_RESULT_UNRESOLVED, decision.status)
        self.assertIn("duplicate", decision.reason)

    def test_case_mismatch_is_q(self):
        decision = certify_real_survivability_study_result(
            p28_input(((NODE1, 0.006),)),
            (result_record(NODE1, 0.006, case="OTHER-CASE"),),
        )
        self.assertEqual(Q_REAL_SURVIVABILITY_STUDY_RESULT_UNRESOLVED, decision.status)
        self.assertIn("study_case_id", decision.reason)

    def test_horizon_mismatch_is_q(self):
        decision = certify_real_survivability_study_result(
            p28_input(((NODE1, 0.006),)),
            (result_record(NODE1, 0.006, horizon="FIVE_YEAR"),),
        )
        self.assertEqual(Q_REAL_SURVIVABILITY_STUDY_RESULT_UNRESOLVED, decision.status)
        self.assertIn("horizon", decision.reason)

    def test_numeric_peak_match_alone_does_not_prove_result_lineage(self):
        decision = certify_real_survivability_study_result(
            p28_input(((NODE1, 0.006),)),
            (result_record(NODE1, 0.006, authoritative=False),),
        )
        self.assertEqual(Q_REAL_SURVIVABILITY_STUDY_RESULT_UNRESOLVED, decision.status)
        self.assertEqual((), decision.node_results)

    def test_peak_mismatch_is_q(self):
        decision = certify_real_survivability_study_result(
            p28_input(((NODE1, 0.006),)),
            (result_record(NODE1, 0.007),),
        )
        self.assertEqual(Q_REAL_SURVIVABILITY_STUDY_RESULT_UNRESOLVED, decision.status)
        self.assertIn("managed peak", decision.reason)

    def test_require_helpers_fail_closed_and_return_p10_decision_when_proven(self):
        q = certify_real_survivability_study_result(p28_input(), ())
        with self.assertRaisesRegex(B10SurvivabilityStudyResultError, "proven REAL survivability"):
            require_real_survivability_study_result(q)
        proven = certify_real_survivability_study_result(
            p28_input(((NODE1, 0.006),)),
            (result_record(NODE1, 0.006),),
        )
        legacy = require_survivability_node_result(proven, NODE1)
        self.assertEqual(NODE1, legacy.node_region_id)
        self.assertEqual(0.006, legacy.assessed_managed_peak_mw)

    def test_registry_remains_header_only(self):
        lines = (ROOT / "registry/survivability_study_results.csv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))
        self.assertTrue(lines[0].startswith("survivability_result_id,study_input_id,network_operator,"))

    def test_source_pack_preserves_boundary_blockers_and_readiness(self):
        text = (ROOT / "docs/source_packs/P29_B10_SURVIVABILITY_STUDY_RESULT_ADMISSION.md").read_text(encoding="utf-8")
        self.assertIn("REAL MANAGED-PEAK STUDY INPUT != SURVIVABILITY STUDY RESULT", text)
        self.assertIn("MISSING RESULT NODE != SURVIVABILITY", text)
        self.assertIn("NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY", text)
        self.assertIn("readiness remains 15%", text)


if __name__ == "__main__":
    unittest.main()
