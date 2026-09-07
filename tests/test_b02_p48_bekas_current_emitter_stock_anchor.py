import csv
import unittest
from pathlib import Path

from modules.B02.current_emitter_stock_anchor import (
    P42_CLAIMS,
    CurrentEmitterStockCandidate,
    assess_current_emitter_stock_anchor,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_p48_current_emitter_stock_anchor.csv"
P42 = ROOT / "registry" / "b02_p42_radiator_stock_requirement.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P48_BEKAS_CURRENT_EMITTER_STOCK_ANCHOR.md"


def bekas_candidate(**overrides):
    values = dict(
        anchor_id="BEKAS3_6BUILDING_CURRENT_EMITTER_STOCK",
        country="HU",
        segment="DISTRICT_HEATED_HOUSING_COOPERATIVE",
        dwelling_count=1215,
        building_count=6,
        installed_cost_allocator_count=4809,
        bathroom_radiator_place_count=1215,
        cost_allocator_is_per_emitter=True,
        bathroom_places_are_additional=True,
        same_cohort_binding=True,
        device_population_includes_non_dwelling_premises=True,
        residential_only_device_denominator_proven=False,
        current_tkm_all_buildings_awarded=True,
        tkm_award_amount_huf=47_098_673,
        tkm_execution_started=False,
        tkm_execution_completed=False,
        current_stock_source_url="https://bekas3.hu/futesi-tudnivalok/",
        tkm_execution_source_url="https://bekas3.hu/2026/09/01/fontos-tajekoztatas-futesi-koltsegosztok-cserejenek-halasztasa/",
        reproducible_binding=True,
    )
    values.update(overrides)
    return CurrentEmitterStockCandidate(**values)


class B02P48BekasCurrentEmitterStockAnchorTests(unittest.TestCase):
    def test_exact_bounded_stock_computes_6024_positions_but_withholds_dwelling_ratio(self):
        decision = assess_current_emitter_stock_anchor(bekas_candidate())
        self.assertEqual(decision.status, "QUALIFIED_BOUNDED_CURRENT_STOCK_ANCHOR")
        self.assertEqual(decision.emitter_position_count, 6024)
        self.assertIsNone(decision.cost_allocators_per_dwelling)
        self.assertIsNone(decision.emitter_positions_per_dwelling)
        self.assertEqual(decision.ratio_status, "Q_NON_DWELLING_NUMERATOR_CONTAMINATION")
        self.assertFalse(decision.p42_national_authority)

    def test_residential_ratio_requires_clean_numerator_or_separate_binding(self):
        clean = assess_current_emitter_stock_anchor(
            bekas_candidate(device_population_includes_non_dwelling_premises=False)
        )
        rebound = assess_current_emitter_stock_anchor(
            bekas_candidate(residential_only_device_denominator_proven=True)
        )
        for decision in (clean, rebound):
            self.assertEqual(decision.ratio_status, "QUALIFIED_RESIDENTIAL_RATIO")
            self.assertAlmostEqual(decision.cost_allocators_per_dwelling, 4809 / 1215)
            self.assertAlmostEqual(decision.emitter_positions_per_dwelling, 6024 / 1215)

    def test_bathroom_places_must_be_explicitly_additional(self):
        decision = assess_current_emitter_stock_anchor(
            bekas_candidate(bathroom_places_are_additional=False)
        )
        self.assertEqual(decision.status, "Q")
        self.assertIsNone(decision.emitter_position_count)
        self.assertIn("BATHROOM_PLACE_OVERLAP_UNRESOLVED", decision.reasons)

    def test_cost_allocator_semantics_must_be_per_emitter(self):
        decision = assess_current_emitter_stock_anchor(
            bekas_candidate(cost_allocator_is_per_emitter=False)
        )
        self.assertEqual(decision.status, "Q")
        self.assertIn("COST_ALLOCATOR_NOT_BOUND_PER_EMITTER", decision.reasons)

    def test_counts_must_belong_to_same_cohort(self):
        decision = assess_current_emitter_stock_anchor(
            bekas_candidate(same_cohort_binding=False)
        )
        self.assertEqual(decision.status, "Q")
        self.assertIn("STOCK_COUNTS_NOT_SAME_COHORT", decision.reasons)

    def test_award_is_not_relabelled_as_completed_execution(self):
        decision = assess_current_emitter_stock_anchor(bekas_candidate())
        self.assertEqual(decision.tkm_execution_status, "AWARDED_NOT_COMPLETED")

    def test_execution_states_are_separate(self):
        started = assess_current_emitter_stock_anchor(
            bekas_candidate(tkm_execution_started=True)
        )
        completed = assess_current_emitter_stock_anchor(
            bekas_candidate(tkm_execution_started=True, tkm_execution_completed=True)
        )
        self.assertEqual(started.tkm_execution_status, "STARTED_NOT_COMPLETED")
        self.assertEqual(completed.tkm_execution_status, "COMPLETED")

    def test_registry_freezes_exact_counts_and_withheld_ratios(self):
        with REGISTRY.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["building_count"], "6")
        self.assertEqual(row["dwelling_count"], "1215")
        self.assertEqual(row["installed_cost_allocator_count"], "4809")
        self.assertEqual(row["bathroom_radiator_place_count"], "1215")
        self.assertEqual(row["emitter_position_count"], "6024")
        self.assertEqual(row["device_population_includes_non_dwelling_premises"], "YES")
        self.assertEqual(row["residential_only_device_denominator_proven"], "NO")
        self.assertEqual(row["cost_allocators_per_dwelling"], "")
        self.assertEqual(row["emitter_positions_per_dwelling"], "")
        self.assertEqual(row["ratio_status"], "Q_NON_DWELLING_NUMERATOR_CONTAMINATION")
        self.assertEqual(row["tkm_award_amount_huf"], "47098673")
        self.assertEqual(row["tkm_execution_status"], "AWARDED_NOT_COMPLETED")
        self.assertEqual(row["p42_national_authority"], "NO")

    def test_p42_five_national_claims_remain_q_and_disabled(self):
        with P42.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(tuple(row["claim_id"] for row in rows), P42_CLAIMS)
        self.assertTrue(all(row["current_status"] == "Q" for row in rows))
        self.assertTrue(all(row["programme_use_allowed"] == "NO" for row in rows))

    def test_document_freezes_quantity_denominator_and_execution_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for boundary in (
            "EXACT BOUNDED STOCK != NATIONAL STOCK",
            "EMITTER POSITION != RADIATOR TYPE/SIZE",
            "CURRENT STOCK COUNT != POST-ENVELOPE KEEP/UPSIZE/CHANGE",
            "AWARDED TKM PROJECT != COMPLETED REPLACEMENT",
            "TKM AWARD AMOUNT != DEVICE COUNT",
            "6024 EMITTER POSITIONS != 6024 PROVEN RADIATOR PRODUCT UNITS OF KNOWN TYPE/SIZE",
            "DEVICE NUMERATOR INCLUDES RENTAL PREMISES != RESIDENTIAL-ONLY PER-DWELLING RATIO",
            "OLDER AWARD SNAPSHOT ABSENCE != NO LATER AWARD",
        ):
            self.assertIn(boundary, text)
        self.assertIn("No external request, email or purchase is performed in P48.", text)

    def test_invalid_numeric_inputs_fail_closed(self):
        cases = (
            dict(dwelling_count=0),
            dict(building_count=0),
            dict(installed_cost_allocator_count=-1),
            dict(bathroom_radiator_place_count=-1),
            dict(tkm_award_amount_huf=-1),
        )
        for override in cases:
            with self.subTest(override=override):
                decision = assess_current_emitter_stock_anchor(
                    bekas_candidate(**override)
                )
                self.assertEqual(decision.status, "Q")
                self.assertIsNone(decision.emitter_position_count)


if __name__ == "__main__":
    unittest.main()
