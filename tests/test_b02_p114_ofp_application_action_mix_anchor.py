import csv
import unittest
from pathlib import Path

from modules.B02.ofp_application_action_mix_anchor import (
    CURRENT_COMPLETION_RESIDUAL,
    INSULATION_APPLICATION_SHARE,
    INSULATION_PLUS_WINDOW_REPLACEMENT_REPORTED_SHARE,
    canonical_observation,
    assess_application_action_mix,
    p114_state,
    semantic_boundaries,
)

ROOT = Path(__file__).resolve().parents[1]
SURFACE = ROOT / "data" / "processed" / "b02" / "p114_ofp_application_action_mix_surface.csv"
CONTRACT = ROOT / "data" / "processed" / "b02" / "p114_ofp_application_action_mix_contract.csv"
REG = ROOT / "registry" / "b02_p114_ofp_application_action_mix.csv"
SOURCES = ROOT / "registry" / "sources.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P114_OFP_APPLICATION_ACTION_MIX.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as h:
        data = list(csv.DictReader(h))
    return {r[key]: r for r in data} if key else data


class P114Tests(unittest.TestCase):
    def test_canonical_empirical_observation_admitted(self):
        c = canonical_observation()
        d = assess_application_action_mix(c)
        self.assertTrue(d.admitted)
        self.assertEqual(d.blockers, ())
        self.assertEqual(c.snapshot_date, "2025-10-17")
        self.assertEqual(c.application_volume_huf_bn, 50.4)
        self.assertEqual(c.approval_volume_huf_bn, 40.3)
        self.assertEqual(c.disbursement_volume_huf_bn, 18.8)
        self.assertEqual(c.disbursement_case_count, 4457)
        self.assertEqual(c.average_application_huf_m, 5.5)
        self.assertEqual(c.insulation_application_share, 0.90)
        self.assertAlmostEqual(
            c.insulation_plus_window_replacement_share,
            2.0 / 3.0,
        )
        self.assertTrue(c.combined_share_is_approximate)

    def test_empirical_data_are_not_promoted_to_completed_1103(self):
        d = assess_application_action_mix(canonical_observation())
        for warning in (
            "APPLICATION_ACTION_MIX_IS_NOT_COMPLETED_ACTION_COHORT",
            "RRF_PLUS_KEHOP_CUMULATIVE_SERIES_IS_NOT_KEHOP_417_418_ONLY",
            "WINDOW_REPLACEMENT_LABEL_IS_NOT_VERIFIED_ADMIN_CODE_1103",
            "DISBURSEMENT_CASE_IS_NOT_PHYSICALLY_COMPLETED_PROJECT",
            "APPROXIMATE_TWO_THIRDS_IS_NOT_EXACT_HARD_SHARE_BOUND",
        ):
            self.assertIn(warning, d.warnings)

    def test_state_preserves_completion_residual_and_numeric_bounds(self):
        s = p114_state()
        self.assertTrue(s["empirical_action_mix_admitted"])
        self.assertFalse(s["kehop_417_418_only_action_mix_identified"])
        self.assertFalse(s["completion_1103_cohort_identified"])
        self.assertEqual(s["current_completion_residual"], CURRENT_COMPLETION_RESIDUAL)
        self.assertEqual(s["insulation_application_share"], INSULATION_APPLICATION_SHARE)
        self.assertAlmostEqual(
            s["insulation_plus_window_replacement_reported_share"],
            INSULATION_PLUS_WINDOW_REPLACEMENT_REPORTED_SHARE,
        )
        self.assertFalse(s["p114_numeric_national_compliance_tightening"])
        self.assertAlmostEqual(s["hp_only_share_upper"], 0.17213897005530188)

    def test_surface_contract_registry_and_sources(self):
        surface = rows(SURFACE, "surface_id")
        self.assertEqual(
            surface["B02-P114-S01"]["status"],
            "ADMITTED_EMPIRICAL_PROGRAMME_OBSERVATION",
        )
        self.assertEqual(
            surface["B02-P114-S04"]["status"],
            "NOT_COMPLETION_1103",
        )

        contract = rows(CONTRACT, "field_id")
        self.assertEqual(
            contract["B02-P114-C01"]["status"],
            "SOURCE_OBSERVED",
        )
        self.assertEqual(
            contract["B02-P114-C09"]["status"],
            "EXPLICIT_SCOPE_BOUNDARY",
        )

        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P114-U01"]["status"],
            "ADMITTED_EMPIRICAL_APPLICATION_ACTION_MIX",
        )
        self.assertEqual(
            reg["B02-P114-U07"]["residual_gap"],
            CURRENT_COMPLETION_RESIDUAL,
        )

        sources = rows(SOURCES, "source_id")
        self.assertIn("SRC-B02-MFB-OFP-ACTION-MIX-2025", sources)
        self.assertIn("SRC-B02-MEHI-OFP-ACTION-MIX-CROSSCHECK-2025", sources)

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertIn("B02-P114", q["notes"])
        self.assertIn("90%", q["notes"])
        self.assertIn(CURRENT_COMPLETION_RESIDUAL, q["notes"])

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P114", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P114", peak["notes"])

    def test_semantic_boundaries_and_doc(self):
        for boundary in (
            "APPLICATION_ACTION_MIX_IS_NOT_COMPLETED_ACTION_COHORT",
            "RRF_PLUS_KEHOP_CUMULATIVE_SERIES_IS_NOT_KEHOP_417_418_ONLY",
            "WINDOW_REPLACEMENT_LABEL_IS_NOT_VERIFIED_ADMIN_CODE_1103",
            "DISBURSEMENT_CASE_IS_NOT_PHYSICALLY_COMPLETED_PROJECT",
            "APPROXIMATELY_TWO_THIRDS_IS_NOT_EXACT_HARD_SHARE_BOUND",
        ):
            self.assertIn(boundary, semantic_boundaries())

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "50.4",
            "40.3",
            "18.8",
            "4,457",
            "90%",
            "two thirds",
            "application-stage",
            CURRENT_COMPLETION_RESIDUAL,
            "82.7861029945%",
            "17.2138970055%",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
