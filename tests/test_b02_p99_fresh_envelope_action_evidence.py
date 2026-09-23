import csv
import unittest
from pathlib import Path

from modules.B02.fresh_envelope_action_evidence import (
    CARES_SOURCE_ID,
    EKR_SOURCE_ID,
    FRESHNESS_FLOOR_YEAR,
    MEHI_MONITORING_SOURCE_ID,
    NEXT_RESIDUAL,
    P99_STATUS,
    RECENT_EKR_ATTIC_INSULATION_PROPERTIES,
    REKK_2022_STOCK_STATE_SHARES,
    REKK_LAST_12M_ACTION_SHARES,
    REKK_OBSERVATION_YEAR,
    REKK_SOURCE_ID,
    current_p99_evidence_state,
    national_2022_recent_envelope_action_rate,
    p99_state,
    semantic_boundaries,
    union_bounds_without_overlap_information,
)


ROOT = Path(__file__).resolve().parents[1]
DATA = (
    ROOT / "data" / "processed" / "b02"
    / "p99_fresh_envelope_action_evidence.csv"
)
REG = ROOT / "registry" / "b02_p99_fresh_envelope_action_evidence.csv"
SOURCES = ROOT / "registry" / "sources.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
DOC = (
    ROOT / "docs" / "source_packs"
    / "B02_P99_FRESH_ENVELOPE_ACTION_EVIDENCE.md"
)


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


class B02P99FreshEnvelopeActionEvidenceTests(unittest.TestCase):
    def test_source_native_recent_action_rates_are_exact(self):
        self.assertEqual(REKK_OBSERVATION_YEAR, 2022)
        self.assertEqual(FRESHNESS_FLOOR_YEAR, 2021)
        self.assertEqual(
            REKK_LAST_12M_ACTION_SHARES,
            {
                "FACADE_INSULATION": 0.037,
                "ROOF_INSULATION": 0.024,
                "ATTIC_FLOOR_INSULATION": 0.041,
                "WINDOW_REPLACEMENT": 0.082,
            },
        )
        self.assertEqual(
            REKK_2022_STOCK_STATE_SHARES,
            {
                "INSULATED_FACADE": 0.350,
                "INSULATED_ATTIC_OR_CEILING": 0.297,
                "WINDOW_REPLACED": 0.527,
            },
        )

    def test_unknown_overlap_produces_union_bounds_not_summed_point(self):
        out = national_2022_recent_envelope_action_rate()
        self.assertEqual(out.source_id, REKK_SOURCE_ID)
        self.assertEqual(
            out.status,
            "QUALIFIED_REPRESENTATIVE_NATIONAL_BOUNDED_ACTION_RATE",
        )
        self.assertAlmostEqual(out.lower_share, 0.082)
        self.assertAlmostEqual(out.upper_share, 0.184)
        self.assertIn(
            "COMPONENT_ACTION_OVERLAP_NOT_PUBLISHED",
            out.warnings,
        )

        self.assertEqual(
            union_bounds_without_overlap_information((0.2, 0.3)),
            (0.3, 0.5),
        )
        self.assertEqual(
            union_bounds_without_overlap_information((0.7, 0.8)),
            (0.8, 1.0),
        )
        with self.assertRaises(ValueError):
            union_bounds_without_overlap_information(())
        with self.assertRaises(ValueError):
            union_bounds_without_overlap_information((1.1,))

    def test_p99_is_partial_resolution_and_exposes_next_semantic_residual(self):
        state = current_p99_evidence_state()
        self.assertEqual(state.status, P99_STATUS)
        self.assertEqual(state.binding_national_source_id, REKK_SOURCE_ID)
        self.assertEqual(
            state.independent_validation_source_ids,
            (CARES_SOURCE_ID, EKR_SOURCE_ID),
        )
        self.assertEqual(
            state.current_monitoring_boundary_source_id,
            MEHI_MONITORING_SOURCE_ID,
        )
        self.assertFalse(state.national_point_rate_for_2026_available)
        self.assertFalse(state.reference_programme_action_share_identified)
        self.assertEqual(state.residual, NEXT_RESIDUAL)
        self.assertAlmostEqual(state.any_major_envelope_action_lower_share, 0.082)
        self.assertAlmostEqual(state.any_major_envelope_action_upper_share, 0.184)

    def test_recent_ekr_volume_is_not_promoted_to_rate(self):
        self.assertEqual(RECENT_EKR_ATTIC_INSULATION_PROPERTIES, 50_000)
        state = p99_state()
        self.assertEqual(
            state["recent_ekr_attic_insulation_properties"],
            50_000,
        )
        self.assertFalse(state["national_2026_point_rate_available"])
        self.assertFalse(state["reference_programme_action_share_identified"])
        self.assertIsNone(state["fresh_multi_source_evidence_blocker"])
        self.assertEqual(
            state["reference_programme_selection_residual"],
            NEXT_RESIDUAL,
        )

    def test_processed_surface_matches_runtime(self):
        data = rows(DATA, "metric_id")
        self.assertEqual(float(data["B02-P99-A01"]["lower_share"]), 0.037)
        self.assertEqual(float(data["B02-P99-A02"]["lower_share"]), 0.024)
        self.assertEqual(float(data["B02-P99-A03"]["lower_share"]), 0.041)
        self.assertEqual(float(data["B02-P99-A04"]["lower_share"]), 0.082)
        self.assertEqual(float(data["B02-P99-A05"]["lower_share"]), 0.082)
        self.assertEqual(float(data["B02-P99-A05"]["upper_share"]), 0.184)
        self.assertEqual(
            data["B02-P99-A05"]["status"],
            "QUALIFIED_REPRESENTATIVE_NATIONAL_BOUNDED_ACTION_RATE",
        )

    def test_registry_preserves_evidence_roles_and_forbidden_promotions(self):
        reg = rows(REG, "evidence_id")
        self.assertEqual(
            reg["B02-P99-E05"]["role"],
            "BOUNDED_NATIONAL_ACTION_RATE",
        )
        self.assertIn(
            "POINT_RATE_FROM_SUM",
            reg["B02-P99-E05"]["forbidden_use"],
        )
        self.assertEqual(
            reg["B02-P99-E09"]["role"],
            "INDEPENDENT_REGIONAL_VALIDATION",
        )
        self.assertEqual(
            reg["B02-P99-E10"]["role"],
            "RECENT_REALIZED_IMPLEMENTATION_VALIDATION",
        )
        self.assertEqual(
            reg["B02-P99-E11"]["role"],
            "NEGATIVE_CURRENT_DATA_BOUNDARY",
        )
        self.assertEqual(
            reg["B02-P99-E12"]["status"],
            "PARTIAL_RESOLVED_FRESH_MULTI_SOURCE_ACTION_EVIDENCE",
        )
        self.assertEqual(
            reg["B02-P99-E12"]["residual_gap"],
            NEXT_RESIDUAL,
        )

    def test_canonical_sources_are_registered_for_future_study(self):
        sources = rows(SOURCES, "source_id")
        for source_id in (
            REKK_SOURCE_ID,
            CARES_SOURCE_ID,
            EKR_SOURCE_ID,
            MEHI_MONITORING_SOURCE_ID,
        ):
            self.assertIn(source_id, sources)

        self.assertIn(
            "Table 40 reports previous-12-month actions",
            sources[REKK_SOURCE_ID]["notes"],
        )
        self.assertIn(
            "regional/structural validation",
            sources[CARES_SOURCE_ID]["notes"],
        )
        self.assertIn(
            "50,000 properties",
            sources[EKR_SOURCE_ID]["notes"],
        )
        self.assertIn(
            "Monitoring System has not been implemented",
            sources[MEHI_MONITORING_SOURCE_ID]["notes"],
        )
        self.assertEqual(sources[CARES_SOURCE_ID]["published_at"], "undated")

    def test_current_q_is_narrowed_not_closed(self):
        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P99", q["notes"])
        self.assertIn(
            "PARTIAL_RESOLVED_FRESH_MULTI_SOURCE_ACTION_EVIDENCE",
            q["notes"],
        )
        self.assertIn(NEXT_RESIDUAL, q["notes"])

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P99", module["gate_note"])
        self.assertIn(NEXT_RESIDUAL, module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P99", peak["notes"])

    def test_source_pack_freezes_semantic_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "OBSERVED RECENT ENVELOPE ACTION RATE != REFERENCE PROGRAMME ACTION SHARE",
            "SUM OF COMPONENT ACTION RATES != ANY-ACTION POINT RATE",
            "BUDAPEST REPRESENTATIVE != HUNGARY REPRESENTATIVE",
            "REALIZED EKR ACTION VOLUME != NATIONAL ANNUAL RATE",
            "PUBLICATION YEAR != OBSERVATION YEAR",
            "FRESH ACTION EVIDENCE != REFERENCE U COMPLIANCE",
            "ANY_MAJOR_ENVELOPE_ACTION_LAST_12_MONTHS in [8.2%, 18.4%]",
            NEXT_RESIDUAL,
        ):
            self.assertIn(phrase, text)

        boundaries = semantic_boundaries()
        self.assertIn(
            "OBSERVED_RECENT_ENVELOPE_ACTION_RATE_IS_NOT_REFERENCE_PROGRAMME_ACTION_SHARE",
            boundaries,
        )
        self.assertIn(
            "FRESH_ACTION_EVIDENCE_IS_NOT_REFERENCE_U_COMPLIANCE",
            boundaries,
        )


if __name__ == "__main__":
    unittest.main()
