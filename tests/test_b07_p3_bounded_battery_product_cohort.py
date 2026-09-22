import csv
import unittest
from pathlib import Path

from modules.B07.product_cohort_envelope import (
    bounded_product_cohort,
    efficiency_boundary,
    origin_boundary,
    warranty_lifecycle_boundary,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "b07_battery_product_cohort_envelope.csv"
REG = ROOT / "registry" / "b07_p3_battery_product_cohort_envelope.csv"
DOC = ROOT / "docs" / "source_packs" / "B07_P3_BOUNDED_BATTERY_PRODUCT_COHORT.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B07P3BoundedBatteryProductCohortTests(unittest.TestCase):
    def test_cohort_materializes_only_complete_comparable_fields(self):
        x = bounded_product_cohort()
        self.assertEqual(x.product_count, 2)
        self.assertEqual(x.manufacturer_count, 2)
        self.assertEqual(x.chemistry_count, 2)
        self.assertEqual(x.nominal_capacity_min_kwh, 6.5)
        self.assertEqual(x.nominal_capacity_max_kwh, 11.0)
        self.assertEqual(x.max_charge_power_min_kw, 2.5)
        self.assertEqual(x.max_charge_power_max_kw, 7.0)
        self.assertEqual(x.max_discharge_power_min_kw, 2.3)
        self.assertEqual(x.max_discharge_power_max_kw, 7.0)
        self.assertEqual(x.status, "QUALIFIED_BOUNDED_PRODUCT_COHORT")

    def test_common_warranty_boundary_is_explicit(self):
        x = bounded_product_cohort()
        self.assertEqual(x.common_warranty_years, 10)
        self.assertEqual(x.common_warranty_retention_pct, 80.0)
        self.assertEqual(x.warranty_cycles_min, 4000)
        self.assertEqual(x.warranty_cycles_max, 10000)

    def test_efficiency_is_not_imputed(self):
        boundary = efficiency_boundary()
        self.assertIn("NO_SQUARE_ROOT_SPLIT_TO_ONE_WAY_EFFICIENCIES", boundary)
        self.assertIn(
            "PRODUCT_SPECIFIC_RUNTIME_EFFICIENCY_REMAINS_FAIL_CLOSED",
            boundary,
        )

    def test_warranty_is_not_degradation_curve(self):
        boundary = warranty_lifecycle_boundary()
        self.assertIn(
            "WARRANTY_RETENTION_CANNOT_BE_INTERPOLATED_AS_DEGRADATION_CURVE",
            boundary,
        )

    def test_origin_gap_is_not_soc_physics(self):
        boundary = origin_boundary()
        self.assertIn(
            "SUPPLY_CHAIN_ORIGIN_IS_PROCUREMENT_POLICY_EVIDENCE_NOT_SOC_PHYSICS",
            boundary,
        )

    def test_materialized_csv_matches_module(self):
        with DATA.open(encoding="utf-8", newline="") as handle:
            data = list(csv.DictReader(handle))
        self.assertEqual(len(data), 1)
        row = data[0]
        self.assertEqual(row["product_count"], "2")
        self.assertEqual(row["nominal_capacity_min_kwh"], "6.5")
        self.assertEqual(row["nominal_capacity_max_kwh"], "11")
        self.assertEqual(row["common_warranty_years"], "10")
        self.assertEqual(row["common_warranty_retention_pct"], "80")

    def test_registry_preserves_runtime_gaps(self):
        reg = rows(REG, "item_id")
        self.assertEqual(reg["B07-P3-C08"]["status"], "Q")
        self.assertEqual(reg["B07-P3-C09"]["status"], "PROCUREMENT_POLICY_GAP")
        self.assertEqual(reg["B07-P3-C10"]["status"], "OPEN_NARROWED_TO_RUNTIME_AGING")

    def test_document_freezes_readiness_and_nonpromotion(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "PRODUCT COHORT != PRODUCT-SPECIFIC RUNTIME",
            "WARRANTY RETENTION != DEGRADATION LAW",
            "BATTERY-ONLY EFFICIENCY != WHOLE-SYSTEM EFFICIENCY",
            "Module readiness remains **58%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
