import csv
import unittest
from pathlib import Path

from modules.B02.radiator_quantity_calibration import (
    P42_CLAIMS,
    RadiatorQuantityCalibrationCandidate,
    assess_radiator_quantity_calibration,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_p49_radiator_quantity_calibration.csv"
P42 = ROOT / "registry" / "b02_p42_radiator_stock_requirement.csv"
P44 = ROOT / "registry" / "b02_p44_panel_radiator_quantity_anchor.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P49_IMPLEMENTED_RADIATOR_PORTFOLIO_ANCHOR.md"


def lehel_candidate(**overrides):
    values = dict(
        anchor_id="LEHEL_ZFR_2019_2020_IMPLEMENTED_PORTFOLIO",
        country="HU",
        role="IMPLEMENTED_RETROFIT_PORTFOLIO",
        dwelling_count=3621,
        building_count_primary=36,
        building_count_crosscheck=38,
        radiator_unit_count=None,
        cost_allocator_count=12500,
        reported_replacement_radiator_count=6000,
        replacement_count_precision="APPROXIMATE",
        radiator_type="LEHEL_VIKING",
        per_emitter_binding=True,
        same_cohort_binding=True,
        residential_only_numerator_proven=False,
        current_stock_observation=False,
        implemented_works=True,
        primary_source_url="https://lehelradiator.hu/_user/file/lehel_muszaki_katalogus_2023.pdf",
        crosscheck_source_url="https://letesz.hu/lehel-2025.pdf",
        reproducible_binding=True,
    )
    values.update(overrides)
    return RadiatorQuantityCalibrationCandidate(**values)


def dunakeszi_candidate(**overrides):
    values = dict(
        anchor_id="DUNAKESZI_PANEL_PUBLIC_DWELLING_4_RAD",
        country="HU",
        role="CURRENT_DWELLING_STOCK",
        dwelling_count=1,
        building_count_primary=None,
        building_count_crosscheck=None,
        radiator_unit_count=4,
        cost_allocator_count=4,
        reported_replacement_radiator_count=None,
        replacement_count_precision="NONE",
        radiator_type="",
        per_emitter_binding=True,
        same_cohort_binding=True,
        residential_only_numerator_proven=True,
        current_stock_observation=True,
        implemented_works=False,
        primary_source_url="https://www.ingatlantajolo.hu/ingatlan/kiado%2Bpanellakas%2Bdunakeszi/8097040",
        crosscheck_source_url="",
        reproducible_binding=True,
    )
    values.update(overrides)
    return RadiatorQuantityCalibrationCandidate(**values)


class B02P49ImplementedRadiatorPortfolioAnchorTests(unittest.TestCase):
    def test_lehel_portfolio_qualifies_exact_12500_emitter_positions(self):
        decision = assess_radiator_quantity_calibration(lehel_candidate())
        self.assertEqual(decision.status, "QUALIFIED_BOUNDED_QUANTITY_CALIBRATION")
        self.assertEqual(decision.emitter_position_count, 12500)
        self.assertFalse(decision.p42_national_authority)
        self.assertEqual(decision.unresolved_p42_claims, P42_CLAIMS)

    def test_nearly_6000_is_never_promoted_to_exact_replacement_count(self):
        decision = assess_radiator_quantity_calibration(lehel_candidate())
        self.assertIsNone(decision.exact_replacement_radiator_count)
        self.assertEqual(decision.replacement_count_status, "APPROXIMATE_REFERENCE_ONLY")

    def test_building_count_drift_is_fail_closed(self):
        decision = assess_radiator_quantity_calibration(lehel_candidate())
        self.assertEqual(decision.building_count_status, "Q_SOURCE_VERSION_CONFLICT")
        consistent = assess_radiator_quantity_calibration(
            lehel_candidate(building_count_crosscheck=36)
        )
        self.assertEqual(consistent.building_count_status, "CONSISTENT")

    def test_portfolio_does_not_manufacture_per_dwelling_stock_ratio(self):
        decision = assess_radiator_quantity_calibration(lehel_candidate())
        self.assertIsNone(decision.radiators_per_dwelling)
        self.assertEqual(
            decision.ratio_status,
            "Q_PORTFOLIO_NOT_CURRENT_RESIDENTIAL_STOCK_RATIO",
        )

    def test_dunakeszi_exact_household_count_can_be_bounded_ratio(self):
        decision = assess_radiator_quantity_calibration(dunakeszi_candidate())
        self.assertEqual(decision.status, "QUALIFIED_BOUNDED_QUANTITY_CALIBRATION")
        self.assertEqual(decision.emitter_position_count, 4)
        self.assertEqual(decision.radiators_per_dwelling, 4.0)
        self.assertEqual(decision.ratio_status, "QUALIFIED_CURRENT_DWELLING_RATIO")
        self.assertFalse(decision.p42_national_authority)

    def test_known_radiator_and_allocator_counts_must_match(self):
        decision = assess_radiator_quantity_calibration(
            dunakeszi_candidate(cost_allocator_count=5)
        )
        self.assertEqual(decision.status, "Q")
        self.assertIsNone(decision.emitter_position_count)
        self.assertIn("RADIATOR_ALLOCATOR_COUNT_MISMATCH", decision.reasons)

    def test_cost_allocator_without_per_emitter_binding_fails_closed(self):
        decision = assess_radiator_quantity_calibration(
            lehel_candidate(per_emitter_binding=False)
        )
        self.assertEqual(decision.status, "Q")
        self.assertIsNone(decision.emitter_position_count)
        self.assertIn("COST_ALLOCATOR_NOT_BOUND_PER_EMITTER", decision.reasons)

    def test_role_semantics_cannot_self_authorize(self):
        current_without_current = assess_radiator_quantity_calibration(
            dunakeszi_candidate(current_stock_observation=False)
        )
        implemented_without_works = assess_radiator_quantity_calibration(
            lehel_candidate(implemented_works=False)
        )
        self.assertEqual(current_without_current.status, "Q")
        self.assertEqual(implemented_without_works.status, "Q")

    def test_registry_freezes_two_distinct_bounded_roles(self):
        with REGISTRY.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 2)
        by_id = {row["anchor_id"]: row for row in rows}
        lehel = by_id["LEHEL_ZFR_2019_2020_IMPLEMENTED_PORTFOLIO"]
        dunakeszi = by_id["DUNAKESZI_PANEL_PUBLIC_DWELLING_4_RAD"]
        self.assertEqual(lehel["dwelling_count"], "3621")
        self.assertEqual(lehel["cost_allocator_count"], "12500")
        self.assertEqual(lehel["emitter_position_count"], "12500")
        self.assertEqual(lehel["building_count_status"], "Q_SOURCE_VERSION_CONFLICT")
        self.assertEqual(lehel["replacement_count_precision"], "APPROXIMATE")
        self.assertEqual(lehel["exact_replacement_radiator_count"], "")
        self.assertEqual(lehel["p42_national_authority"], "NO")
        self.assertEqual(dunakeszi["radiator_unit_count"], "4")
        self.assertEqual(dunakeszi["radiators_per_dwelling"], "4.000000")
        self.assertEqual(dunakeszi["p42_national_authority"], "NO")

    def test_p44_quantities_are_not_rewritten_or_added_to_p49(self):
        with P44.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        by_id = {row["anchor_id"]: row for row in rows}
        self.assertEqual(
            by_id["ARPADHIDFO_ALL_DWELLINGS_2015"]["radiator_unit_count"],
            "1680",
        )
        self.assertEqual(
            by_id["LEHEL_2021_PANEL_RETROFIT"]["replacement_radiator_count"],
            "3307",
        )
        text = DOC.read_text(encoding="utf-8")
        self.assertIn(
            "P44 LEHEL PROJECT + P49 LEHEL PORTFOLIO != ADDITIVE WITHOUT DISJOINTNESS PROOF",
            text,
        )

    def test_p42_five_national_claims_remain_q_and_disabled(self):
        with P42.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(tuple(row["claim_id"] for row in rows), P42_CLAIMS)
        self.assertTrue(all(row["current_status"] == "Q" for row in rows))
        self.assertTrue(all(row["programme_use_allowed"] == "NO" for row in rows))

    def test_document_freezes_quantity_precision_and_size_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for boundary in (
            "IMPLEMENTED PORTFOLIO != CURRENT NATIONAL STOCK",
            "APARTMENT HEAT METER != PER-RADIATOR COST ALLOCATOR",
            "EXACT COST-ALLOCATOR COUNT != EXACT REPLACEMENT-RADIATOR COUNT",
            "NEARLY 6000 != EXACT 6000",
            "BUILDING-COUNT SOURCE CONFLICT != SILENTLY RESOLVED METADATA",
            "PORTFOLIO DEVICE TOTAL != RESIDENTIAL-ONLY PER-DWELLING RATIO",
            "ONE CURRENT PUBLIC LISTING != REPRESENTATIVE STOCK",
            "PRODUCT FAMILY != INSTALLED SIZE DISTRIBUTION",
            "COUNT CONSISTENCY != REPRESENTATIVENESS",
            "P44/P48/P49 BOUNDED ANCHORS != P42 NATIONAL AUTHORITY",
        ):
            self.assertIn(boundary, text)
        self.assertIn("No external request, email or purchase is performed in P49.", text)

    def test_invalid_numeric_and_precision_inputs_fail_closed(self):
        cases = (
            dict(dwelling_count=0),
            dict(dwelling_count=True),
            dict(cost_allocator_count=-1),
            dict(reported_replacement_radiator_count=-1),
            dict(replacement_count_precision="BAD"),
            dict(same_cohort_binding=False),
            dict(reproducible_binding=False),
        )
        for override in cases:
            with self.subTest(override=override):
                decision = assess_radiator_quantity_calibration(
                    lehel_candidate(**override)
                )
                self.assertEqual(decision.status, "Q")
                self.assertIsNone(decision.emitter_position_count)


if __name__ == "__main__":
    unittest.main()
