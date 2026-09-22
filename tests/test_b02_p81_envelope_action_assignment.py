import csv
import unittest
from pathlib import Path

from modules.B02.programme_envelope_action_assignment import (
    AIR_TO_WATER_HP_ONLY,
    REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
    SCN_EXPLICIT_PROGRAMME_ASSIGNMENT,
    PopulationActionEvidence,
    ProgrammeActionAssignment,
    assess_bounded_population_action_inference,
    assess_explicit_programme_scenario_override,
    current_kehop_policy_calibration,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b02_p81_envelope_action_assignment.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P81_ENVELOPE_ACTION_ASSIGNMENT.md"

METRIC = "ENVELOPE_RETROFIT_PLUS_AWHP_SHARE"
SCOPE = "HUNGARY_PROGRAMME_ELIGIBLE_RESIDENTIAL_STOCK"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


def evidence(
    source_id,
    family,
    year,
    lower,
    upper,
    central=None,
    weight=None,
    *,
    metric=METRIC,
    scope=SCOPE,
):
    return PopulationActionEvidence(
        source_id=source_id,
        independent_source_family=family,
        metric_key=metric,
        population_scope_key=scope,
        observation_year=year,
        lower_share=lower,
        upper_share=upper,
        central_share=central,
        aggregation_weight=weight,
    )


class B02P81EnvelopeActionAssignmentTests(unittest.TestCase):
    def test_current_kehop_policy_is_scope_limited(self):
        out = current_kehop_policy_calibration()
        self.assertEqual(
            out.status,
            "QUALIFIED_SCOPE_LIMITED_POLICY_CALIBRATION",
        )
        self.assertEqual(out.construction_cutoff, "BUILT_AND_PERMITTED_BEFORE_2007")
        self.assertAlmostEqual(out.minimum_primary_energy_saving_share, 0.30)
        self.assertIn("AIR_TO_WATER_HEAT_PUMP", out.eligible_measure_families)
        self.assertIn("NATIONAL_ENVELOPE_ACTION_SHARE", out.forbidden_uses)

    def test_no_fresh_comparable_evidence_fails_closed(self):
        out = assess_bounded_population_action_inference(
            (),
            metric_key=METRIC,
            population_scope_key=SCOPE,
            reference_year=2026,
            freshness_floor_year=2021,
        )
        self.assertEqual(out.status, "Q")
        self.assertIn(
            "FRESH_COMPARABLE_POPULATION_EVIDENCE_REQUIRED",
            out.blockers,
        )

    def test_three_fresh_independent_sources_produce_bounded_inference(self):
        out = assess_bounded_population_action_inference(
            (
                evidence("SRC-A", "FAMILY-A", 2024, 0.28, 0.40, 0.34, 2.0),
                evidence("SRC-B", "FAMILY-B", 2025, 0.31, 0.43, 0.37, 3.0),
                evidence("SRC-C", "FAMILY-C", 2026, 0.30, 0.46, 0.39, 5.0),
            ),
            metric_key=METRIC,
            population_scope_key=SCOPE,
            reference_year=2026,
            freshness_floor_year=2021,
        )
        self.assertEqual(
            out.status,
            "QUALIFIED_MULTI_SOURCE_BOUNDED_INFERENCE",
        )
        self.assertEqual(out.independent_fresh_source_count, 3)
        self.assertAlmostEqual(out.lower_share, 0.28)
        self.assertAlmostEqual(out.upper_share, 0.46)
        self.assertAlmostEqual(out.weighted_central_share, 0.375)
        self.assertEqual(out.blockers, ())

    def test_two_fresh_sources_remain_partial_not_blocked(self):
        out = assess_bounded_population_action_inference(
            (
                evidence("SRC-A", "FAMILY-A", 2025, 0.28, 0.40),
                evidence("SRC-B", "FAMILY-B", 2026, 0.31, 0.43),
            ),
            metric_key=METRIC,
            population_scope_key=SCOPE,
            reference_year=2026,
            freshness_floor_year=2021,
        )
        self.assertEqual(
            out.status,
            "PARTIAL_MULTI_SOURCE_BOUNDED_INFERENCE",
        )
        self.assertEqual(out.blockers, ())
        self.assertIn(
            "FEWER_THAN_PREFERRED_INDEPENDENT_FRESH_SOURCES",
            out.warnings,
        )

    def test_old_compatible_source_is_historical_not_pooled(self):
        out = assess_bounded_population_action_inference(
            (
                evidence("SRC-OLD", "FAMILY-OLD", 2015, 0.10, 0.20),
                evidence("SRC-A", "FAMILY-A", 2024, 0.30, 0.40),
                evidence("SRC-B", "FAMILY-B", 2025, 0.32, 0.42),
                evidence("SRC-C", "FAMILY-C", 2026, 0.34, 0.44),
            ),
            metric_key=METRIC,
            population_scope_key=SCOPE,
            reference_year=2026,
            freshness_floor_year=2021,
        )
        self.assertEqual(out.historical_compatible_source_count, 1)
        self.assertEqual(out.fresh_source_count, 3)
        self.assertAlmostEqual(out.lower_share, 0.30)
        self.assertAlmostEqual(out.upper_share, 0.44)
        self.assertNotIn("SRC-OLD", out.source_ids)

    def test_semantically_incompatible_source_is_not_averaged(self):
        out = assess_bounded_population_action_inference(
            (
                evidence("SRC-A", "FAMILY-A", 2024, 0.30, 0.40),
                evidence("SRC-B", "FAMILY-B", 2025, 0.32, 0.42),
                evidence("SRC-C", "FAMILY-C", 2026, 0.34, 0.44),
                evidence(
                    "SRC-X",
                    "FAMILY-X",
                    2026,
                    0.80,
                    0.90,
                    metric="ANY_ENVELOPE_MEASURE_SHARE",
                ),
            ),
            metric_key=METRIC,
            population_scope_key=SCOPE,
            reference_year=2026,
            freshness_floor_year=2021,
        )
        self.assertAlmostEqual(out.upper_share, 0.44)
        self.assertIn(
            "EXCLUDED_SEMANTICALLY_INCOMPATIBLE_SOURCE:SRC-X",
            out.warnings,
        )

    def test_weighted_central_requires_explicit_weights(self):
        out = assess_bounded_population_action_inference(
            (
                evidence("SRC-A", "FAMILY-A", 2024, 0.30, 0.40, 0.35),
                evidence("SRC-B", "FAMILY-B", 2025, 0.32, 0.42, 0.37),
                evidence("SRC-C", "FAMILY-C", 2026, 0.34, 0.44, 0.39),
            ),
            metric_key=METRIC,
            population_scope_key=SCOPE,
            reference_year=2026,
            freshness_floor_year=2021,
        )
        self.assertIsNone(out.weighted_central_share)
        self.assertIn(
            "EXPLICIT_WEIGHTED_CENTRAL_ESTIMATE_NOT_AVAILABLE",
            out.warnings,
        )

    def test_exact_split_is_optional_scenario_override_only(self):
        out = assess_explicit_programme_scenario_override(
            (
                ProgrammeActionAssignment(
                    population_key="GROUP-A",
                    assigned_dwelling_equivalents=1_250_000,
                    action=AIR_TO_WATER_HP_ONLY,
                    assignment_class=SCN_EXPLICIT_PROGRAMME_ASSIGNMENT,
                    authority="OWNER_APPROVED_SCENARIO",
                ),
                ProgrammeActionAssignment(
                    population_key="GROUP-B",
                    assigned_dwelling_equivalents=750_000,
                    action=REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
                    assignment_class=SCN_EXPLICIT_PROGRAMME_ASSIGNMENT,
                    authority="OWNER_APPROVED_SCENARIO",
                ),
            ),
            declared_programme_population=2_000_000,
        )
        self.assertEqual(
            out.status,
            "QUALIFIED_EXPLICIT_PROGRAMME_SCENARIO_OVERRIDE",
        )
        self.assertAlmostEqual(out.coverage_share, 1.0)
        self.assertEqual(out.blockers, ())

    def test_partial_scenario_override_fails_only_override_path(self):
        out = assess_explicit_programme_scenario_override(
            (
                ProgrammeActionAssignment(
                    population_key="GROUP-A",
                    assigned_dwelling_equivalents=1_200_000,
                    action=AIR_TO_WATER_HP_ONLY,
                    assignment_class=SCN_EXPLICIT_PROGRAMME_ASSIGNMENT,
                    authority="OWNER_APPROVED_SCENARIO",
                ),
            ),
            declared_programme_population=2_000_000,
        )
        self.assertEqual(out.status, "Q")
        self.assertIn(
            "SCENARIO_OVERRIDE_MUST_CLOSE_TO_DECLARED_POPULATION",
            out.blockers,
        )

    def test_registry_uses_bounded_inference_as_primary_path(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P81-A04"]["status"],
            "CONTRACTED_MULTI_SOURCE_BOUNDED_INFERENCE",
        )
        self.assertEqual(
            reg["B02-P81-A06"]["residual_gap"],
            "FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED",
        )
        self.assertEqual(reg["B02-P81-A08"]["status"], "OPEN_NARROWED")

    def test_source_pack_preserves_core_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "FULL HOUSEHOLD ACTION IDENTIFICATION != REQUIRED",
            "REPRESENTATIVE MULTI-SOURCE POPULATION INFERENCE = ADMISSIBLE",
            "EVIDENCE-DERIVED ACTION MIX != EXACT POINT ASSIGNMENT",
            "EXACT PROGRAMME ACTION MIX = SCENARIO / POLICY INPUT ONLY",
            "OLD SOURCE != CURRENT STOCK WITHOUT TEMPORAL BRIDGE",
            "THREE SOURCES != SIMPLE AVERAGE WITHOUT SEMANTIC COMPATIBILITY",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
