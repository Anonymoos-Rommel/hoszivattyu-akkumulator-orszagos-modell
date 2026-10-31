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

    def test_sonnen_exact_variant_and_usable_capacity_are_source_bound(self):
        products = rows(ROOT / "registry/battery_products.csv", "product_id")
        evidence = rows(ROOT / "data/processed/battery_product_evidence.csv", "product_id")
        product_id = "SONNEN-BATTERY-10-PERFORMANCE"
        for row in (products[product_id], evidence[product_id]):
            self.assertIn("10p/11", row["model"])
            self.assertIn("May 2024", row["model"])
            self.assertIn("3000364", row["model"])
            self.assertEqual(row["nominal_capacity_kwh"], "11")
            self.assertEqual(row["usable_capacity_kwh"], "10")
            self.assertEqual(row["usable_capacity_status"], "OBS")
            self.assertEqual(row["capacity_boundary"], "NOMINAL")
            self.assertEqual(row["max_charge_power_kw"], "7")
            self.assertEqual(row["max_discharge_power_kw"], "7")
            self.assertEqual(row["power_boundary"], "AC")
            self.assertEqual(row["status"], "PARTIAL")
            self.assertIn("SRC-B07-SONNEN-10P11-DATASHEET-2024", row["source_ids"].split(";"))

    def test_temperature_operating_is_not_optimal_or_guaranteed_power(self):
        product = rows(ROOT / "registry/battery_products.csv", "product_id")["SONNEN-BATTERY-10-PERFORMANCE"]
        evidence = rows(ROOT / "data/processed/battery_product_evidence.csv", "product_id")["SONNEN-BATTERY-10-PERFORMANCE"]
        for row, note in ((product, "notes"), (evidence, "limitations")):
            self.assertEqual(row["operating_temp_min_c"], "-5")
            self.assertEqual(row["operating_temp_max_c"], "45")
            self.assertIn("optimal 5..35 C is not the operating range", row[note])
            self.assertIn("possible but unquantified", row[note])
            self.assertIn("no full-power guarantee", row[note])
        residual = "VALIDATED_TEMPERATURE_DERATING_RESPONSE_REQUIRED_FOR_COHORT_RUNTIME"
        self.assertIn(residual, bounded_product_cohort().residuals)
        surface = rows(DATA, "cohort_id")
        self.assertIn(residual, next(iter(surface.values()))["residuals"])
        self.assertNotIn("SECOND_PRODUCT_TEMPERATURE_ENVELOPE_REQUIRED_FOR_COHORT_DERATING", bounded_product_cohort().residuals)

    def test_datasheet_provenance_is_exact_and_not_republished(self):
        sid = "SRC-B07-SONNEN-10P11-DATASHEET-2024"
        sources = rows(ROOT / "registry/sources.csv", "source_id")
        battery_sources = rows(ROOT / "registry/battery_sources.csv", "source_id")
        expected_hash = "39016d76a5b8f7e301deee3e45ab3e1f5a006afc4a4ee27dbd79f35e179c268c"
        self.assertEqual(sources[sid]["local_snapshot_sha256"], expected_hash)
        for row in (sources[sid], battery_sources[sid]):
            self.assertEqual(row["published_at"], "undated")
            self.assertEqual(row["retrieved_at"], "2026-10-31")
            self.assertEqual(row["evidence_status"], "OBS")
            self.assertIn("EXTERNAL_ONLY", row["license"])
            self.assertIn("3000364", row["title"])
            self.assertEqual(row["url"], sources[sid]["url"])

    def test_catalog_update_does_not_promote_efficiency_or_readiness(self):
        product = rows(ROOT / "registry/battery_products.csv", "product_id")["SONNEN-BATTERY-10-PERFORMANCE"]
        for prefix in ("charge_efficiency", "discharge_efficiency", "round_trip_efficiency"):
            self.assertEqual(product[prefix + "_value"], "")
            self.assertEqual(product[prefix + "_status"], "Q")
        self.assertEqual(product["efficiency_value"], "")
        self.assertEqual(product["efficiency_status"], "Q")
        self.assertEqual(product["efficiency_boundary"], "UNSPECIFIED")
        self.assertEqual((product["warranty_years"], product["warranty_cycles"], product["warranty_retention_pct"]), ("10", "10000", "80"))
        readiness = rows(ROOT / "registry/battery_readiness.csv", "component_id")
        for key, status, percent in (("TEMPERATURE_ENVELOPE", "PARTIAL", "45"), ("PRODUCT_EVIDENCE", "PARTIAL", "65"), ("DEGRADATION_MODEL", "Q", "20")):
            self.assertEqual((readiness[key]["status"], readiness[key]["readiness_percent"]), (status, percent))

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
