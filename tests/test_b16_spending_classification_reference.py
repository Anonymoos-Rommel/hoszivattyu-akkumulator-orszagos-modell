"""Hermetic contract tests; source-native replay is a separate private check."""
import copy
import hashlib
import json
import tempfile
import unittest
from decimal import Inexact, Rounded, localcontext
from pathlib import Path
from unittest.mock import patch

from modules.B16 import industry_structure_reference as industry
from modules.B16 import spending_classification_reference as ref
from test_b16_industry_structure_reference import fixture, parse, LEAVES


class B16SpendingClassificationTests(unittest.TestCase):
    def setUp(self):
        self.catalogue = ref.load_spending_classification_reference(claim=ref.CLASSIFICATION_CLAIM)

    def route(self, route_id, **extra):
        return self.catalogue.read_route(route_id=route_id, product_classification="CPA2.1",
                                        activity_classification="NACE Rev.2", **extra)

    def test_original_handoff_preserves_every_declared_package(self):
        groups = set(self.catalogue.package_groups)
        self.assertEqual(groups, {"heat_pump_equipment", "heat_pump_installation", "battery_equipment",
            "electrical_and_grid_works", "envelope_materials", "envelope_works", "window_door_goods",
            "combined_installed_works", "professional_services", "vocational_training", "price_conversion"})
        self.assertEqual(len(self.catalogue.route_ids), len(set(self.catalogue.route_ids)))
        for group in groups:
            result = self.catalogue.read_package(package_group=group, product_classification="CPA2.1",
                                                 activity_classification="NACE Rev.2")
            self.assertTrue(result["conditional_routes"])
            self.assertIsNone(result["selected_route"])
            self.assertIsNone(result["monetary_allocation"])
            self.assertFalse(result["classification_proves_actual_purchase"])

    def test_product_class_is_not_actual_supplier(self):
        r = self.route("hp_refrigerating_equipment")
        self.assertEqual((r["cpa_2_1_code"], r["characteristic_nace_rev2"]), ("28.25.13", "28.25"))
        self.assertEqual((r["figaro_2026_circabc_product_code"], r["figaro_2026_circabc_industry_code"]), ("CPA_C28", "C28"))
        self.assertIsNone(r["actual_supplier_industry"])
        self.assertIsNone(r["monetary_allocation"])
        self.assertEqual(r["actual_supplier_status"], "Q")

    def test_heat_pump_version_split_stays_relation(self):
        r = self.route("hp_refrigerating_equipment")
        self.assertEqual(r["cpa_2_2_correspondence_targets"], ("28.21.14", "28.25.13"))
        self.assertEqual(r["source_witnesses"]["cpa_correspondence"]["rows"], (3139, 3140))
        self.assertIn("NOT_WHOLE_CLASS_EQUIVALENCE", r["correspondence_semantics"])

    def test_lithium_code_version_collision_is_preserved(self):
        r = self.route("battery_lithium_or_other")
        self.assertEqual(r["cpa_2_1_code"], "27.20.23")
        self.assertEqual(r["cpa_2_2_correspondence_targets"], ("27.20.23", "27.20.24"))
        self.assertNotIn("27.20.24", [x["cpa_2_1_code"] for x in self.catalogue.metadata["routes"]])

    def test_inverter_is_separate_from_accumulator(self):
        r = self.route("battery_inverter")
        self.assertEqual((r["cpa_2_1_code"], r["characteristic_nace_rev2"]), ("27.90.41", "27.90"))
        self.assertEqual(len(r["cpa_2_2_correspondence_targets"]), 5)

    def test_installation_and_goods_do_not_share_product_class(self):
        r = self.route("hp_installation")
        self.assertEqual((r["cpa_2_1_code"], r["figaro_2026_circabc_product_code"], r["national_io_characteristic_industry_code"]),
                         ("43.22.12", "CPA_F", "F43"))
        self.assertIn("embedded", r["exclusions"])
        self.assertIsNone(r["monetary_allocation"])

    def test_education_alias_is_explicit(self):
        r = self.route("vocational_secondary")
        self.assertEqual((r["national_io_characteristic_industry_code"], r["employment_a64_characteristic_code"],
                          r["figaro_2026_circabc_industry_code"], r["figaro_2026_circabc_product_code"]),
                         ("P", "P", "P85", "CPA_P85"))
        self.assertEqual(r["cpa_level"], 4)

    def test_conditional_material_routes_remain_distinct(self):
        self.assertEqual({self.route(x)["figaro_2026_circabc_product_code"] for x in
            ("wood_openings", "plastic_openings", "metal_openings")}, {"CPA_C16", "CPA_C22", "CPA_C25"})
        self.assertEqual(self.route("joinery_installation")["cpa_2_2_correspondence_targets"],
                         ("43.32.01", "43.32.02", "43.32.09"))
        self.assertNotEqual(self.route("glass_wool_material")["cpa_2_1_code"],
                            self.route("other_mineral_insulation")["cpa_2_1_code"])

    def test_mixed_work_and_margins_are_not_default_spend_vectors(self):
        self.assertEqual(self.route("combined_residential_works")["cpa_level"], 5)
        self.assertIn("unallocated", self.route("combined_residential_works")["exclusions"])
        for key in ("wholesale_margin", "retail_margin"):
            self.assertIn("Never assign the full", self.route(key)["exclusions"])
            self.assertIsNone(self.route(key)["monetary_allocation"])

    def test_source_versions_and_private_originals_preserved(self):
        for source in self.catalogue.metadata["source_artifacts"]:
            self.assertEqual(source["reuse_status"], "EXTERNAL_ONLY")
            self.assertIsNone(source["repo_snapshot_path"])
            self.assertEqual(len(source["sha256"]), 64)
        self.assertFalse(self.catalogue.metadata["classification_basis"]["figaro_numeric_data_loaded"])
        self.assertFalse(self.catalogue.report()["programme_calculation_performed"])

    def test_unsupported_inputs_fail_closed(self):
        for claim in (None, "PROGRAMME_GDP", "CURRENT_ELIGIBILITY"):
            with self.subTest(claim=claim), self.assertRaises(ref.SpendingClassificationError):
                ref.load_spending_classification_reference(claim=claim)
        for key in ("WM50", "whole_house", ""):
            with self.subTest(key=key), self.assertRaises(ref.SpendingClassificationError):
                self.catalogue.read_package(package_group=key, product_classification="CPA2.1", activity_classification="NACE Rev.2")
        with self.assertRaises(ref.SpendingClassificationError): self.route("named_invoice")

    def test_unqualified_version_never_silently_relabels(self):
        for product, activity in (("CPA2.2", "NACE Rev.2"), ("CPA2008", "NACE Rev.2"), ("CPA2.1", "NACE Rev.2.1")):
            with self.subTest(product=product), self.assertRaises(ref.SpendingClassificationError):
                self.catalogue.read_route(route_id="battery_lithium_or_other", product_classification=product,
                                         activity_classification=activity)

    def test_returned_records_are_immutable(self):
        r = self.route("hp_installation")
        with self.assertRaises(TypeError): r["actual_supplier_industry"] = "F43"
        with self.assertRaises(TypeError): r["source_witnesses"]["figaro_codes"]["row"] = 1

    def test_changed_manifest_is_not_admitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_bytes(ref.MANIFEST_PATH.read_bytes() + b" ")
            with patch.object(ref, "MANIFEST_PATH", path), self.assertRaises(ref.SpendingClassificationError):
                ref.load_spending_classification_reference(claim=ref.CLASSIFICATION_CLAIM)


class B16HistoricalImportRatioTests(unittest.TestCase):
    def setUp(self):
        data, contract = fixture()
        self.cube = parse(data, contract)
        metadata = {"industry_partition": {"leaf_codes": LEAVES}, "price_basis": "SYNTHETIC basic prices",
                    "import_valuation": "SYNTHETIC CIF"}
        self.reference = ref.HistoricalImportReference(industry.IndustryStructureReference(self.cube, metadata, ()),
            {"origin_ratio_contract": "SYNTHETIC TEST ONLY"})

    def test_exact_nonnegative_share(self):
        result = ref._origin_ratio(total=3, imported=1, domestic=2)
        self.assertEqual(result["exact_ratio"], {"numerator": 1, "denominator": 3})
        self.assertEqual(result["status"], "NONNEGATIVE_ORIGIN_SHARE")
        self.assertIsNone(result["programme_import_propensity"])

    def test_boundaries_zero_and_one_are_valid(self):
        for total, imp, dom, expected in ((3, 0, 3, 0), (3, 3, 0, 1)):
            r = ref._origin_ratio(total=total, imported=imp, domestic=dom)
            self.assertEqual(r["exact_ratio"], {"numerator": expected, "denominator": 1})
            self.assertEqual(r["status"], "NONNEGATIVE_ORIGIN_SHARE")

    def test_signed_cases_are_not_bounded_propensities(self):
        for amounts, fraction in (((2, 3, -1), (3, 2)), ((2, -1, 3), (-1, 2)), ((-3, -1, -2), (1, 3))):
            r = ref._origin_ratio(total=amounts[0], imported=amounts[1], domestic=amounts[2])
            self.assertEqual(r["status"], "SIGNED_ACCOUNTING_RATIO")
            self.assertEqual(r["exact_ratio"], dict(zip(("numerator", "denominator"), fraction)))
            self.assertFalse(r["clamped"])

    def test_zero_denominator_preserves_cancellation(self):
        for imp, dom in ((0, 0), (7, -7)):
            r = ref._origin_ratio(total=0, imported=imp, domestic=dom)
            self.assertEqual(r["status"], "UNDEFINED_ZERO_DENOMINATOR")
            self.assertEqual(r["imported_million_HUF"], imp)
            self.assertIsNone(r["exact_ratio"])
            self.assertEqual(r["truth_status"], "Q")

    def test_missing_is_not_zero(self):
        r = ref._origin_ratio(total=None, imported=None, domestic=None)
        self.assertEqual(r["status"], "MISSING")
        self.assertIsNone(r["exact_ratio"])
        self.assertNotEqual(r, ref._origin_ratio(total=0, imported=0, domestic=0))

    def test_invalid_origin_identity_and_type_rejected(self):
        for values in ((4, 1, 2), (None, 0, None), (3.0, 1, 2), (True, 0, 1), ("3", 1, 2)):
            with self.subTest(values=values), self.assertRaises(ref.SpendingClassificationError):
                ref._origin_ratio(total=values[0], imported=values[1], domestic=values[2])

    def test_decimal_context_cannot_change_classification(self):
        with localcontext() as context:
            context.prec = 1
            context.traps[Inexact] = True
            context.traps[Rounded] = True
            result = ref._origin_ratio(total=10**100 + 1, imported=10**100, domestic=1)
        self.assertEqual(result["exact_ratio"]["numerator"], 10**100)
        self.assertEqual(result["exact_ratio"]["denominator"], 10**100 + 1)

    def test_named_historical_grain_and_denominator(self):
        r = self.reference.read_import_ratio(row="A01", column="A01")
        self.assertEqual((r["total_million_HUF"], r["imported_million_HUF"], r["domestic_million_HUF"]), (10, 2, 8))
        self.assertEqual(r["exact_ratio"], {"numerator": 1, "denominator": 5})
        self.assertEqual((r["row"], r["column"], r["reference_year"]), ("A01", "A01", 2023))
        self.assertIn("same named origin-use cell", r["denominator"])

    def test_account_rows_and_overlapping_parents_rejected(self):
        for row, col in (("B1G", "A01"), ("P1", "A01"), ("IMP", "A01"), ("A", "A01"), ("A01", "A")):
            with self.subTest(row=row, col=col), self.assertRaises(ref.SpendingClassificationError):
                self.reference.read_import_ratio(row=row, column=col)

    def test_structurally_absent_final_use_retains_missing(self):
        r = self.reference.read_import_ratio(row="A01", column="P6_U2")
        self.assertEqual(r["status"], "MISSING")
        self.assertIsNone(r["imported_million_HUF"])

    def test_total_and_final_use_are_distinct_explicit_denominators(self):
        first = self.reference.read_import_ratio(row="A01", column="TOTAL")
        second = self.reference.read_import_ratio(row="A01", column="TU")
        self.assertNotEqual(first["total_million_HUF"], second["total_million_HUF"])
        self.assertNotEqual(first["exact_ratio"], second["exact_ratio"])

    def test_report_keeps_every_cell_and_status(self):
        r = self.reference.report()
        self.assertEqual(sum(r["ratio_status_counts"].values()), r["row_count"] * r["column_count"])
        self.assertGreater(r["ratio_status_counts"]["MISSING"], 0)
        self.assertGreater(r["ratio_status_counts"]["SIGNED_ACCOUNTING_RATIO"], 0)
        self.assertFalse(r["programme_calculation_performed"])

    def test_exact_source_loader_rejects_wrong_claim_and_source(self):
        args = dict(source_id=industry.SOURCE_ID, reference_year=2023, unit="MIO_NAC")
        with self.assertRaises(ref.SpendingClassificationError):
            ref.load_historical_import_reference("unused", claim="PROGRAMME_IMPORT_LEAKAGE", **args)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.json"
            path.write_text('{}')
            with self.assertRaises(industry.IndustryStructureReferenceError):
                ref.load_historical_import_reference(path, claim=ref.IMPORT_CLAIM, **args)


if __name__ == "__main__":
    unittest.main()
