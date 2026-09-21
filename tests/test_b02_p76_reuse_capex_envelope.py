import csv
import unittest
from pathlib import Path

from modules.B02.reuse_capex_envelope import (
    ASS_CONSERVATIVE_SUPERSET_UPPER_BOUND,
    QUALIFIED_SCOPE_LIMITED_TECHNICAL_ACTION_AUTHORITY,
    assess_family_house_reuse_action_authority,
    assess_legal_eligibility_relevance,
    assess_reuse_cost_use,
    build_reuse_capex_envelope,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b02_p76_reuse_capex_envelope.csv"
P75 = ROOT / "registry" / "b02_p75_kehop_scope_crosswalk.csv"
OPEN_Q = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P76_REUSE_CAPEX_SUPERSET_ENVELOPE.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B02P76ReuseCapexSupersetEnvelopeTests(unittest.TestCase):
    def test_exact_reuse_structural_upper_bounds(self):
        x = build_reuse_capex_envelope()
        self.assertEqual(x.path, "REUSE_EXISTING_DISTRIBUTION")
        self.assertEqual(x.per_set_lower_huf, 0.0)
        self.assertEqual(x.per_set_upper_huf, 3_556_000.0)
        self.assertAlmostEqual(
            x.definite_pre2007_reuse_candidate_upper,
            1_124_830.2828892032,
            delta=1e-6,
        )
        self.assertAlmostEqual(
            x.possible_pre2007_reuse_candidate_upper,
            1_298_476.1553200493,
            delta=1e-6,
        )
        self.assertEqual(
            x.evidence_status,
            ASS_CONSERVATIVE_SUPERSET_UPPER_BOUND,
        )

    def test_exact_aggregate_upper_sensitivities(self):
        x = build_reuse_capex_envelope()
        self.assertAlmostEqual(
            x.definite_pre2007_aggregate_upper_huf,
            3_999_896_485_954.0063,
            delta=1.0,
        )
        self.assertAlmostEqual(
            x.possible_pre2007_aggregate_upper_huf,
            4_617_381_208_318.095,
            delta=1.0,
        )

    def test_reuse_capex_transfer_requires_both_guards(self):
        ok = assess_reuse_cost_use(
            requested_use="TECHNICAL_REUSE_CAPEX_UPPER_BOUND",
            structural_scope_compatible=True,
            reuse_work_scope_is_subset=True,
        )
        self.assertEqual(ok.status, ASS_CONSERVATIVE_SUPERSET_UPPER_BOUND)

        outside = assess_reuse_cost_use(
            requested_use="TECHNICAL_REUSE_CAPEX_UPPER_BOUND",
            structural_scope_compatible=False,
            reuse_work_scope_is_subset=True,
        )
        self.assertEqual(outside.status, "Q")
        self.assertIn(
            "OUTSIDE_KEHOP_STRUCTURAL_SCOPE_CAPEX_AUTHORITY",
            outside.blockers,
        )

        extra_work = assess_reuse_cost_use(
            requested_use="TECHNICAL_REUSE_CAPEX_UPPER_BOUND",
            structural_scope_compatible=True,
            reuse_work_scope_is_subset=False,
        )
        self.assertEqual(extra_work.status, "Q")
        self.assertIn(
            "REUSE_WORK_SCOPE_NOT_PROVEN_SUBSET_OF_REPLACEMENT_PACKAGE",
            extra_work.blockers,
        )

    def test_source_ceiling_is_not_promoted_to_official_reuse_price(self):
        official = assess_reuse_cost_use(
            requested_use="OFFICIAL_REUSE_PRICE",
            structural_scope_compatible=True,
            reuse_work_scope_is_subset=True,
        )
        self.assertEqual(official.status, "Q")
        self.assertIn("NO_SOURCE_NATIVE_REUSE_ONLY_PRICE_LINE", official.blockers)

        market = assess_reuse_cost_use(
            requested_use="EXPECTED_REALIZED_COST",
            structural_scope_compatible=True,
            reuse_work_scope_is_subset=True,
        )
        self.assertEqual(market.status, "Q")
        self.assertIn("SUPERSET_CEILING_IS_NOT_MARKET_DISTRIBUTION", market.blockers)

    def test_family_house_reuse_action_authority_is_scope_limited(self):
        ok = assess_family_house_reuse_action_authority(
            structural_scope_compatible=True,
            requested_use="TECHNICAL_ACTION_FAMILY",
        )
        self.assertEqual(
            ok.status,
            QUALIFIED_SCOPE_LIMITED_TECHNICAL_ACTION_AUTHORITY,
        )

        outside = assess_family_house_reuse_action_authority(
            structural_scope_compatible=False,
            requested_use="TECHNICAL_ACTION_FAMILY",
        )
        self.assertEqual(outside.status, "Q")
        self.assertIn(
            "REUSE_ACTION_AUTHORITY_OUTSIDE_KEHOP_STRUCTURAL_SCOPE_REQUIRED",
            outside.blockers,
        )

    def test_legal_eligibility_is_not_technical_cost_blocker(self):
        technical = assess_legal_eligibility_relevance(
            requested_use="TECHNICAL_CAPEX_REFERENCE"
        )
        self.assertEqual(
            technical.status,
            "NOT_REQUIRED_FOR_TECHNICAL_REFERENCE_COST",
        )

        funding = assess_legal_eligibility_relevance(
            requested_use="CURRENT_KEHOP_FUNDING_ELIGIBILITY"
        )
        self.assertEqual(funding.status, "Q")
        self.assertIn("PROJECT_SPECIFIC_LEGAL_ELIGIBILITY_REQUIRED", funding.blockers)

    def test_registry_narrows_reuse_capex_and_action_gaps(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P76-C09"]["status"],
            "PARTIAL_RESOLVED_WITHIN_KEHOP_STRUCTURAL_SCOPE",
        )
        self.assertEqual(
            reg["B02-P76-C10"]["status"],
            "PARTIAL_RESOLVED_KEHOP_FAMILY_HOUSE_SCOPE",
        )
        self.assertEqual(
            reg["B02-P76-C11"]["status"],
            "RETIRED_AS_TECHNICAL_MODEL_BLOCKER",
        )
        self.assertIn(
            "REUSE_OUTSIDE_KEHOP_STRUCTURAL_SCOPE_CAPEX_BOUND_REQUIRED",
            reg["B02-P76-C13"]["residual_gap"],
        )

    def test_p75_current_state_is_superseded_not_deleted(self):
        p75 = rows(P75, "item_id")
        self.assertEqual(
            p75["B02-P75-K13"]["status"],
            "SUPERSEDED_BY_P76_CURRENT_STATE",
        )
        self.assertEqual(
            p75["B02-P75-K12"]["status"],
            "UNRESOLVED_AFTER_STRUCTURAL_CROSSWALK",
        )

    def test_q_b02_004_and_readiness(self):
        q = rows(OPEN_Q, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P76", q["notes"])
        self.assertIn(
            "REUSE_OUTSIDE_KEHOP_STRUCTURAL_SCOPE_CAPEX_BOUND_REQUIRED",
            q["notes"],
        )
        self.assertNotIn(
            "Current residual: REUSE_PATH_CAPEX_BOUND_REQUIRED",
            q["notes"],
        )
        b02 = rows(MODULE_STATUS, "module_id")["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("B02-P76", b02["gate_note"])

    def test_source_pack_preserves_transfer_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "OFFICIAL REPLACEMENT PACKAGE CEILING != OFFICIAL REUSE PRICE",
            "CONSERVATIVE SUPERSET CAP != MARKET-TYPICAL OR EXPECTED COST",
            "CURRENT KEHOP FUNDING ELIGIBILITY != TECHNICAL REFERENCE COST AUTHORITY",
            "REUSE SECONDARY WORK ⊆ COMPLETE REPLACEMENT PACKAGE WORK",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
