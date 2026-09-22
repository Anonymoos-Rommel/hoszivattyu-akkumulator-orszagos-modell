import csv
import unittest
from pathlib import Path

from modules.B05.product_cohort_envelope import (
    envelope_at,
    materializable_coordinates,
    national_envelope_boundary,
    qualified_cross_manufacturer_coordinates,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "b05_product_cohort_performance_envelope.csv"
REG = ROOT / "registry" / "b05_p7_product_cohort_envelope.csv"
DOC = ROOT / "docs" / "source_packs" / "B05_P7_PRODUCT_COHORT_ENVELOPE.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B05P7ProductCohortEnvelopeTests(unittest.TestCase):
    def test_eight_common_observed_coordinates_are_materializable(self):
        self.assertEqual(
            materializable_coordinates(),
            (
                (-15.0, 35.0),
                (-7.0, 35.0),
                (-7.0, 45.0),
                (2.0, 35.0),
                (2.0, 45.0),
                (7.0, 35.0),
                (7.0, 45.0),
                (7.0, 55.0),
            ),
        )

    def test_five_coordinates_are_cross_manufacturer(self):
        self.assertEqual(
            qualified_cross_manufacturer_coordinates(),
            (
                (-7.0, 35.0),
                (2.0, 35.0),
                (7.0, 35.0),
                (7.0, 45.0),
                (7.0, 55.0),
            ),
        )

    def test_a_minus7_w35_envelope_is_bounded_without_averaging(self):
        x = envelope_at(-7.0, 35.0)
        self.assertEqual(x.status, "QUALIFIED_CROSS_MANUFACTURER_COHORT_ENVELOPE")
        self.assertEqual(x.equipment_count, 6)
        self.assertEqual(x.manufacturer_count, 2)
        self.assertAlmostEqual(x.capacity_min_kw, 3.60)
        self.assertAlmostEqual(x.capacity_max_kw, 11.90)
        self.assertAlmostEqual(x.cop_min, 2.50)
        self.assertAlmostEqual(x.cop_max, 3.20)

    def test_a_minus15_w35_remains_single_manufacturer_calibration(self):
        x = envelope_at(-15.0, 35.0)
        self.assertEqual(x.manufacturer_count, 1)
        self.assertEqual(x.equipment_count, 2)
        self.assertEqual(x.status, "CALIBRATION_ONLY_SINGLE_MANUFACTURER_COHORT")
        self.assertAlmostEqual(x.cop_min, 2.41)
        self.assertAlmostEqual(x.cop_max, 2.49)

    def test_cold_w45_is_not_promoted(self):
        for outdoor in (-7.0, 2.0):
            x = envelope_at(outdoor, 45.0)
            self.assertEqual(x.status, "CALIBRATION_ONLY_SINGLE_MANUFACTURER_COHORT")
        x = envelope_at(7.0, 45.0)
        self.assertEqual(x.status, "QUALIFIED_CROSS_MANUFACTURER_COHORT_ENVELOPE")

    def test_materialized_csv_matches_core_coordinates(self):
        with DATA.open(encoding="utf-8", newline="") as handle:
            data = list(csv.DictReader(handle))
        self.assertEqual(len(data), 8)
        qualified = [r for r in data if r["status"] == "QUALIFIED_CROSS_MANUFACTURER_COHORT_ENVELOPE"]
        self.assertEqual(len(qualified), 5)
        calibration = [r for r in data if r["status"] == "CALIBRATION_ONLY_SINGLE_MANUFACTURER_COHORT"]
        self.assertEqual(len(calibration), 3)

    def test_registry_preserves_real_residuals(self):
        reg = rows(REG, "item_id")
        self.assertEqual(reg["B05-P7-E03"]["status"], "QUALIFIED_BOUNDED_ENVELOPE")
        self.assertEqual(reg["B05-P7-E06"]["status"], "PARTIAL")
        self.assertIn(
            "B05_COLD_W45_CROSS_MANUFACTURER_ENVELOPE_REQUIRED",
            reg["B05-P7-E09"]["residual_gap"],
        )
        self.assertEqual(reg["B05-P7-E09"]["status"], "OPEN_NARROWED")

    def test_product_specific_boundary_is_explicit(self):
        boundary = national_envelope_boundary()
        self.assertIn("COHORT_ENVELOPE_CANNOT_AUTHORIZE_A_SPECIFIC_PRODUCT", boundary)
        self.assertIn("NO_OUT_OF_COORDINATE_EXTRAPOLATION", boundary)

    def test_document_preserves_nonpromotion_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "PRODUCT-COHORT ENVELOPE != PRODUCT-SPECIFIC PERFORMANCE MAP",
            "CROSS-MANUFACTURER COMMON POINT != NATIONAL MARKET SHARE",
            "MISSING COMMON POINT != LICENSE TO EXTRAPOLATE",
            "B05 module readiness remains 64%",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
