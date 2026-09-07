import csv
import unittest
from dataclasses import replace
from pathlib import Path

from modules.B02.legacy_radal_replacement_gate import (
    HistoricalInstalledSurfaceReference,
    LegacyRadiatorReference,
    ReplacementProductReference,
    assess_historical_installed_surface,
    assess_legacy_radiator,
    assess_replacement_product,
    compare_legacy_to_replacement,
    forbid_surface_to_piece_conversion,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_p51_legacy_radal_replacement_gate.csv"
P42 = ROOT / "registry" / "b02_p42_radiator_stock_requirement.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P51_LEGACY_RADAL_REPLACEMENT_GATE.md"


def rows():
    with REGISTRY.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def legacy_reference(output_basis="SOURCE_NOMINAL_UNSPECIFIED_TEMP"):
    return LegacyRadiatorReference(
        anchor_id="JASZAPATI_RADAL600_10",
        radiator_family="RADAL 600",
        connection_distance_mm=600,
        section_count=10,
        length_mm=860,
        nominal_output_w=1779,
        output_basis=output_basis,
        observed_unit_count=4,
        residential_scope=False,
        source_url="https://example.test/legacy",
        exact_locator="exact row",
        reproducible_binding=True,
    )


def replacement_reference(element_count=10, length_mm=712, high=1184, low=607):
    return ReplacementProductReference(
        product_id=f"VIKING600_E{element_count:02d}",
        product_family="LEHEL Viking",
        material="ALUMINIUM",
        connection_distance_mm=600,
        element_count=element_count,
        length_mm=length_mm,
        output_w_78_62_20=high,
        output_w_55_45_20=low,
        manufacturer_family_interchangeable_with_radal=True,
        source_url="https://example.test/catalogue",
        exact_locator="600 mm performance table",
        reproducible_binding=True,
    )


class B02P51LegacyRadalReplacementGateTests(unittest.TestCase):
    def test_historical_30m_surface_is_magnitude_only(self):
        decision = assess_historical_installed_surface(
            HistoricalInstalledSurfaceReference(
                anchor_id="RADAL_HISTORICAL_HU_HEATING_SURFACE",
                radiator_family="RADAL",
                heating_surface_m2=30_000_000,
                magnitude_precision="APPROXIMATE",
                geography="HU",
                historical_installation=True,
                source_url="https://example.test/catalogue",
                exact_locator="brand-history section",
                reproducible_binding=True,
            )
        )
        self.assertEqual(decision.status, "QUALIFIED_HISTORICAL_SURFACE_MAGNITUDE")
        self.assertEqual(decision.heating_surface_m2, 30_000_000)
        self.assertIsNone(decision.physical_piece_count)
        self.assertFalse(decision.current_stock_authority)
        self.assertFalse(decision.p42_national_authority)

    def test_surface_to_piece_conversion_is_explicitly_forbidden(self):
        with self.assertRaisesRegex(
            ValueError,
            "HEATING_SURFACE_M2_TO_PHYSICAL_RADIATOR_PIECES_FORBIDDEN",
        ):
            forbid_surface_to_piece_conversion(30_000_000)

    def test_invalid_historical_surface_reference_fails_closed(self):
        decision = assess_historical_installed_surface(
            HistoricalInstalledSurfaceReference(
                anchor_id="",
                radiator_family="RADAL",
                heating_surface_m2=-1,
                magnitude_precision="GUESS",
                geography="EU",
                historical_installation=False,
                source_url="",
                exact_locator="",
                reproducible_binding=False,
            )
        )
        self.assertEqual(decision.status, "Q")
        self.assertIsNone(decision.heating_surface_m2)
        self.assertIn("INVALID_HEATING_SURFACE", decision.reasons)
        self.assertIn("WRONG_GEOGRAPHY", decision.reasons)

    def test_jaszapati_exact_six_legacy_rows_reconcile_to_18_units(self):
        legacy_rows = [
            row for row in rows()
            if row["row_role"] == "NONRES_LEGACY_TECHNICAL_REFERENCE"
        ]
        expected = {
            6: (485, 1067, 1),
            8: (710, 1423, 1),
            10: (860, 1779, 4),
            15: (1310, 2669, 4),
            16: (1385, 2846, 6),
            22: (1835, 3914, 2),
        }
        self.assertEqual(len(legacy_rows), 6)
        actual = {
            int(row["section_or_element_count"]): (
                int(row["length_mm"]),
                int(row["nominal_output_w"]),
                int(row["observed_unit_count"]),
            )
            for row in legacy_rows
        }
        self.assertEqual(actual, expected)
        self.assertEqual(sum(value[2] for value in actual.values()), 18)

    def test_legacy_reference_never_self_authorizes_stock_weight(self):
        nonres = assess_legacy_radiator(legacy_reference())
        residential = assess_legacy_radiator(
            replace(legacy_reference(), residential_scope=True)
        )
        self.assertTrue(nonres.technical_reference_qualified)
        self.assertTrue(residential.technical_reference_qualified)
        self.assertFalse(nonres.residential_stock_weight_allowed)
        self.assertFalse(residential.residential_stock_weight_allowed)
        self.assertFalse(residential.p42_national_authority)

    def test_jaszapati_nominal_output_basis_remains_unspecified(self):
        legacy_rows = [
            row for row in rows()
            if row["row_role"] == "NONRES_LEGACY_TECHNICAL_REFERENCE"
        ]
        self.assertTrue(legacy_rows)
        self.assertEqual(
            {row["output_basis"] for row in legacy_rows},
            {"SOURCE_NOMINAL_UNSPECIFIED_TEMP"},
        )

    def test_real_legacy_rows_cannot_be_compared_to_viking_without_common_basis(self):
        decision = compare_legacy_to_replacement(
            legacy_reference(), replacement_reference(), "78_62_20"
        )
        self.assertEqual(decision.status, "Q")
        self.assertFalse(decision.output_comparison_qualified)
        self.assertIn("LEGACY_OUTPUT_BASIS_NOT_COMPARABLE", decision.reasons)
        self.assertIsNone(decision.output_delta_w)
        self.assertFalse(decision.exact_replacement_selection_authorized)

    def test_explicit_common_basis_can_compare_but_never_select_product(self):
        decision = compare_legacy_to_replacement(
            replace(
                legacy_reference(output_basis="78_62_20"),
                nominal_output_w=1100,
            ),
            replacement_reference(),
            "78_62_20",
        )
        self.assertEqual(decision.status, "QUALIFIED_OUTPUT_COMPARISON_ONLY")
        self.assertTrue(decision.output_comparison_qualified)
        self.assertEqual(decision.legacy_output_w, 1100)
        self.assertEqual(decision.replacement_output_w, 1184)
        self.assertEqual(decision.output_delta_w, 84)
        self.assertTrue(decision.manufacturer_family_interchangeability_only)
        self.assertFalse(decision.exact_replacement_selection_authorized)

    def test_connection_distance_mismatch_blocks_comparison(self):
        decision = compare_legacy_to_replacement(
            replace(legacy_reference(output_basis="78_62_20"), nominal_output_w=1100),
            replace(replacement_reference(), connection_distance_mm=500),
            "78_62_20",
        )
        self.assertEqual(decision.status, "Q")
        self.assertIn("CONNECTION_DISTANCE_MISMATCH", decision.reasons)

    def test_current_viking_catalogue_has_exact_23_continuous_rows(self):
        product_rows = [
            row for row in rows()
            if row["row_role"] == "CURRENT_PRODUCT_PERFORMANCE_REFERENCE"
        ]
        self.assertEqual(len(product_rows), 23)
        self.assertEqual(
            [int(row["section_or_element_count"]) for row in product_rows],
            list(range(3, 26)),
        )

    def test_viking_lengths_and_outputs_are_strictly_increasing(self):
        product_rows = [
            row for row in rows()
            if row["row_role"] == "CURRENT_PRODUCT_PERFORMANCE_REFERENCE"
        ]
        lengths = [int(row["length_mm"]) for row in product_rows]
        high = [int(row["output_w_78_62_20"]) for row in product_rows]
        low = [int(row["output_w_55_45_20"]) for row in product_rows]
        self.assertTrue(all(a < b for a, b in zip(lengths, lengths[1:])))
        self.assertTrue(all(a < b for a, b in zip(high, high[1:])))
        self.assertTrue(all(a < b for a, b in zip(low, low[1:])))
        self.assertTrue(all(l < h for l, h in zip(low, high)))

    def test_viking_exact_catalogue_anchor_values_are_frozen(self):
        product_rows = {
            int(row["section_or_element_count"]): row
            for row in rows()
            if row["row_role"] == "CURRENT_PRODUCT_PERFORMANCE_REFERENCE"
        }
        for element, expected in {
            10: (712, 1184, 607),
            22: (1612, 2730, 1398),
            25: (1837, 3111, 1593),
        }.items():
            row = product_rows[element]
            self.assertEqual(
                (
                    int(row["length_mm"]),
                    int(row["output_w_78_62_20"]),
                    int(row["output_w_55_45_20"]),
                ),
                expected,
            )

    def test_replacement_product_gate_rejects_bad_low_temperature_output(self):
        decision = assess_replacement_product(
            replacement_reference(high=600, low=700)
        )
        self.assertEqual(decision.status, "Q")
        self.assertIn("LOW_TEMP_OUTPUT_NOT_LOWER", decision.reasons)
        self.assertFalse(decision.catalog_reference_qualified)
        self.assertFalse(decision.exact_replacement_selection_authorized)

    def test_family_interchangeability_never_authorizes_exact_sku(self):
        decision = assess_replacement_product(replacement_reference())
        self.assertEqual(decision.status, "QUALIFIED_REPLACEMENT_PRODUCT_REFERENCE")
        self.assertTrue(decision.catalog_reference_qualified)
        self.assertFalse(decision.exact_replacement_selection_authorized)
        self.assertFalse(decision.p42_national_authority)

    def test_registry_materializes_nonres_heat_pump_reuse_precedent(self):
        precedent = [
            row for row in rows()
            if row["row_role"] == "NONRES_HEAT_PUMP_REUSE_PRECEDENT"
        ]
        self.assertEqual(len(precedent), 1)
        self.assertEqual(
            precedent[0]["row_id"],
            "JASZAPATI_RADAL_RETAINED_AFTER_ENVELOPE_HP",
        )
        self.assertEqual(precedent[0]["residential_stock_weight_allowed"], "NO")
        self.assertEqual(precedent[0]["p42_national_authority"], "NO")

    def test_registry_contains_engineering_rule_and_family_control(self):
        role_set = {row["row_role"] for row in rows()}
        self.assertIn("RESIDENTIAL_ENGINEERING_RULE", role_set)
        self.assertIn("MANUFACTURER_FAMILY_INTERCHANGEABILITY_CONTROL", role_set)
        self.assertIn("HISTORICAL_INSTALLED_SURFACE_MAGNITUDE", role_set)

    def test_registry_never_authorizes_stock_weight_product_selection_or_p42(self):
        for row in rows():
            if row["residential_stock_weight_allowed"]:
                self.assertEqual(row["residential_stock_weight_allowed"], "NO")
            if row["exact_replacement_selection_authorized"]:
                self.assertEqual(row["exact_replacement_selection_authorized"], "NO")
            self.assertEqual(row["p42_national_authority"], "NO")

    def test_document_freezes_core_non_equivalence_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        required = (
            "HISTORICAL HEATING SURFACE M2 != PHYSICAL RADIATOR UNIT COUNT",
            "SYSTEM 70/55 C != NOMINAL TABLE OUTPUT BASIS",
            "MANUFACTURER FAMILY INTERCHANGEABILITY != EXACT REPLACEMENT SKU AUTHORITY",
            "ONE NONRES HEAT-PUMP REUSE PRECEDENT != RESIDENTIAL/NATIONAL KEEP SHARE",
            "SAME LENGTH / CONNECTION DISTANCE != SAME OUTPUT",
            "B02 REPLACEMENT NEED/COMPARISON != B06 PRODUCT/CAPEX SELECTION",
        )
        for boundary in required:
            self.assertIn(boundary, text)

    def test_document_records_historical_magnitude_version_drift(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("30 million m2", text)
        self.assertIn("20 million m2", text)
        self.assertIn("source-version magnitude claim", text)
        historical = next(
            row for row in rows()
            if row["row_id"] == "RADAL_HISTORICAL_HU_HEATING_SURFACE"
        )
        self.assertEqual(historical["magnitude_precision"], "APPROXIMATE")

    def test_p42_five_national_claims_remain_q_and_disabled(self):
        with P42.open(newline="", encoding="utf-8") as handle:
            p42_rows = list(csv.DictReader(handle))
        self.assertEqual(len(p42_rows), 5)
        self.assertEqual({row["current_status"] for row in p42_rows}, {"Q"})
        self.assertEqual({row["programme_use_allowed"] for row in p42_rows}, {"NO"})


if __name__ == "__main__":
    unittest.main()
