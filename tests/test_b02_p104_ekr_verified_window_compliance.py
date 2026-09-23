import csv
import unittest
from pathlib import Path

from modules.B02.ekr_verified_window_compliance import (
    AFFECTED_OPENING_REFERENCE_DEFICIT,
    AFFECTED_OPENING_REFERENCE_SATISFIED,
    AFFECTED_OPENING_UNRESOLVED,
    COVERAGE_RESIDUAL,
    EKR_COHORT_RESIDUAL,
    EKR_WINDOW_ACTION_TYPE,
    EKR_WINDOW_MEASURE_CODES,
    NON_EKR_RESIDUAL,
    P104_STATUS,
    PRIMARY_NEXT_RESIDUAL,
    WHOLE_DWELLING_WINDOW_REFERENCE_SATISFIED,
    WHOLE_DWELLING_WINDOW_UNRESOLVED,
    assess_ekr_window_action,
    p104_state,
    public_hem_surface,
    semantic_boundaries,
)


ROOT = Path(__file__).resolve().parents[1]
ROUTES = ROOT / "data" / "processed" / "b02" / "p104_window_compliance_evidence_routes.csv"
PUBLIC = ROOT / "data" / "processed" / "b02" / "p104_ekr_window_publication_boundary.csv"
REG = ROOT / "registry" / "b02_p104_ekr_verified_window_compliance.csv"
SOURCES = ROOT / "registry" / "sources.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P104_EKR_VERIFIED_WINDOW_COMPLIANCE.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


class B02P104EkrVerifiedWindowComplianceTests(unittest.TestCase):
    def test_current_ekr_window_measure_family_is_exact(self):
        self.assertEqual(EKR_WINDOW_MEASURE_CODES, ("1.2", "1.4", "1.6"))
        self.assertEqual(EKR_WINDOW_ACTION_TYPE, "1103")

        routes = rows(ROUTES, "route_id")
        self.assertEqual(
            routes["B02-P104-R02"]["status"],
            "QUALIFIED_ADMINISTRATIVE_ROUTE",
        )
        self.assertIn(
            "SRC-B06-HU-EKR-18-2025",
            routes["B02-P104-R02"]["authority"],
        )

    def test_verified_technical_u_can_classify_affected_opening(self):
        sat = assess_ekr_window_action(
            measure_code="1.2",
            hem_verified=True,
            technical_record_available=True,
            new_window_u_w_m2k=1.10,
            full_dwelling_window_coverage=False,
        )
        self.assertEqual(
            sat.affected_opening_state,
            AFFECTED_OPENING_REFERENCE_SATISFIED,
        )
        self.assertEqual(
            sat.dwelling_window_state,
            WHOLE_DWELLING_WINDOW_UNRESOLVED,
        )
        self.assertIn(COVERAGE_RESIDUAL, sat.blockers)

        deficit = assess_ekr_window_action(
            measure_code="1.6",
            hem_verified=True,
            technical_record_available=True,
            new_window_u_w_m2k=1.20,
        )
        self.assertEqual(
            deficit.affected_opening_state,
            AFFECTED_OPENING_REFERENCE_DEFICIT,
        )

        whole = assess_ekr_window_action(
            measure_code="1.4",
            hem_verified=True,
            technical_record_available=True,
            new_window_u_w_m2k=0.90,
            full_dwelling_window_coverage=True,
        )
        self.assertEqual(
            whole.dwelling_window_state,
            WHOLE_DWELLING_WINDOW_REFERENCE_SATISFIED,
        )
        self.assertNotIn(COVERAGE_RESIDUAL, whole.blockers)

    def test_ekr_label_without_verification_or_technical_u_remains_unresolved(self):
        x = assess_ekr_window_action(
            measure_code="1.2",
            hem_verified=False,
            technical_record_available=False,
            new_window_u_w_m2k=None,
        )
        self.assertEqual(x.affected_opening_state, AFFECTED_OPENING_UNRESOLVED)
        self.assertEqual(
            x.dwelling_window_state,
            WHOLE_DWELLING_WINDOW_UNRESOLVED,
        )
        self.assertIn("HEM_VERIFICATION_REQUIRED", x.blockers)
        self.assertIn("EKR_TECHNICAL_RECORD_REQUIRED", x.blockers)
        self.assertIn(
            "NEW_WINDOW_U_VALUE_REQUIRED_FROM_TECHNICAL_RECORD",
            x.blockers,
        )

        with self.assertRaises(ValueError):
            assess_ekr_window_action(
                measure_code="9.9",
                hem_verified=True,
                technical_record_available=True,
                new_window_u_w_m2k=1.0,
            )

    def test_public_hem_surface_preserves_admin_public_boundary(self):
        x = public_hem_surface()
        self.assertTrue(x.public_generic_lookup_available)
        self.assertTrue(x.public_total_count_available)
        self.assertFalse(x.public_measure_type_available)
        self.assertFalse(x.public_technical_u_available)
        self.assertTrue(x.administrative_measure_type_available)
        self.assertTrue(x.administrative_technical_u_route_available)
        self.assertFalse(x.national_1103_count_identified)
        self.assertEqual(x.residual, EKR_COHORT_RESIDUAL)

        materialized = rows(PUBLIC, "surface_id")
        self.assertEqual(
            materialized["B02-P104-P04"]["status"],
            "PUBLIC_GENERIC_AGGREGATE",
        )
        self.assertEqual(
            materialized["B02-P104-P06"]["status"],
            "QUALIFIED_TECHNICAL_RECORD",
        )
        self.assertEqual(
            materialized["B02-P104-P06"]["public_without_login"],
            "NO",
        )

    def test_p104_supersedes_direct_u_only_blocker_without_numeric_tightening(self):
        state = p104_state()
        self.assertEqual(state["status"], P104_STATUS)
        self.assertEqual(
            state["superseded_primary_residual"],
            "CURRENT_REPLACED_WINDOW_REALIZED_UW_DISTRIBUTION_REQUIRED",
        )
        self.assertEqual(state["primary_residual"], PRIMARY_NEXT_RESIDUAL)
        self.assertIn(
            "DIRECT_REPRESENTATIVE_OR_CALIBRATED_REPLACED_WINDOW_UW",
            state["admissible_closure_routes"],
        )
        self.assertIn(
            "EKR_1103_VERIFIED_TECHNICAL_RECORD_COHORT",
            state["admissible_closure_routes"],
        )
        self.assertFalse(
            state["public_national_ekr_1103_technical_cohort_identified"]
        )
        self.assertFalse(
            state["national_replaced_window_compliance_share_identified"]
        )
        self.assertFalse(state["p104_numeric_national_action_tightening"])
        self.assertAlmostEqual(
            state["p102_structural_calibrated_retrofit_floor_lower_share"],
            0.8278610299446981,
        )
        self.assertEqual(state["hp_only_share_lower"], 0.0)
        self.assertAlmostEqual(
            state["hp_only_share_upper"],
            0.17213897005530188,
        )
        self.assertIn(EKR_COHORT_RESIDUAL, state["sub_residuals"])
        self.assertIn(NON_EKR_RESIDUAL, state["sub_residuals"])
        self.assertIn(COVERAGE_RESIDUAL, state["sub_residuals"])

    def test_registry_sources_and_project_state_are_exact(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P104-U08"]["status"],
            "SUPERSEDED_BY_MULTI_ROUTE_COMPLIANCE_CONTRACT",
        )
        self.assertEqual(
            reg["B02-P104-U05"]["residual_gap"],
            EKR_COHORT_RESIDUAL,
        )
        self.assertAlmostEqual(
            float(reg["B02-P104-U09"]["lower_bound"]),
            0.8278610299446981,
        )

        sources = rows(SOURCES, "source_id")
        for source_id in (
            "SRC-B06-HU-EKR-18-2025",
            "SRC-B02-MEKH-HEM-MODULE-HANDBOOK",
            "SRC-B02-MEKH-17-2020-HEM-DATA-CONTENT",
            "SRC-B02-EHAT-15A-PUBLIC-HEM-REGISTRY",
            "SRC-B02-HU-MEHI-RENOVATION-DATA-GAPS-2025",
        ):
            self.assertIn(source_id, sources)

        self.assertIn(
            "P104 current window-compliance authority",
            sources["SRC-B06-HU-EKR-18-2025"]["notes"],
        )
        self.assertIn(
            "P104 public/private field boundary",
            sources["SRC-B02-MEKH-HEM-MODULE-HANDBOOK"]["notes"],
        )

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P104", q["notes"])
        self.assertIn(PRIMARY_NEXT_RESIDUAL, q["notes"])

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P104", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P104", peak["notes"])

    def test_semantic_boundaries_and_document_are_frozen(self):
        boundaries = semantic_boundaries()
        for item in (
            "GENERIC_LEGAL_REQUIREMENT_IS_NOT_VERIFIED_EKR_ACTION",
            "VERIFIED_EKR_AFFECTED_OPENING_IS_NOT_WHOLE_DWELLING_WINDOW_COMPLIANCE",
            "PUBLIC_TOTAL_HEM_COUNT_IS_NOT_EKR_1103_WINDOW_COUNT",
            "ADMINISTRATIVE_TECHNICAL_FIELD_IS_NOT_PUBLIC_POPULATION_SURFACE",
            "EKR_WINDOW_ACTION_IS_NOT_ALL_REPLACED_WINDOWS",
            "EKR_COHORT_IS_NOT_NON_EKR_REPLACED_WINDOW_STOCK",
        ):
            self.assertIn(item, boundaries)

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "1.2 — Nyílászáró korszerűsítés és csere",
            "1103",
            "new opening U",
            "CURRENT_REPLACED_WINDOW_COMPLIANCE_POPULATION_SURFACE_REQUIRED",
            "EKR_1103_TECHNICAL_COHORT_AGGREGATE_REQUIRED",
            "82.7861029945%",
            "17.2138970055%",
            "**B02 remains 55%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
