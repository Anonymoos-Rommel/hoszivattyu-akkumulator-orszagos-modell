import csv
import unittest
from pathlib import Path

from modules.B02.radiator_data_provider_route import (
    REQUIRED_P42_CLAIMS,
    RadiatorDataProviderCandidate,
    assess_radiator_data_provider_route,
)


ROOT = Path(__file__).resolve().parents[1]
ROUTES = ROOT / "registry" / "b02_p46_radiator_data_provider_routes.csv"
P42 = ROOT / "registry" / "b02_p42_radiator_stock_requirement.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P46_NATIONAL_RADIATOR_DATA_PROVIDER_ROUTE.md"


def brg_candidate(**overrides):
    values = dict(
        route_id="BRG_HUHC2026_RAD_PARK",
        provider="BRG Building Solutions",
        report_ref="HUHC2026",
        country="HU",
        publication_date="2026-06-30",
        authority_url="https://www.brgbuildingsolutions.com/Reports-Details?ProductID=a283546d-c5b7-4f07-9e28-16f77aaeaa73",
        exact_locator="Residential Heating and Cooling Park > A.8.2 Residential Radiators Park; HU - Radiators - Report > 3.1-3.8",
        current_report=True,
        national_scope=True,
        residential_radiator_park=True,
        hydronic_radiator_scope=True,
        end_use_segmentation=True,
        product_type_segmentation=True,
        direct_acquisition_route=True,
        public_numeric_stock_cells=False,
        installed_stock_type_distribution_verified=False,
        reuse_upgrade_classification_verified=False,
        replacement_quantity_verified=False,
        reproducible_binding=True,
    )
    values.update(overrides)
    return RadiatorDataProviderCandidate(**values)


class B02P46NationalRadiatorDataProviderRouteTests(unittest.TestCase):
    def test_brg_route_is_qualified_without_minting_p42_authority(self):
        decision = assess_radiator_data_provider_route(brg_candidate())
        self.assertEqual(decision.route_status, "QUALIFIED_PROVIDER_ROUTE")
        self.assertFalse(decision.p42_national_authority)
        self.assertEqual(decision.unresolved_p42_claims, REQUIRED_P42_CLAIMS)

    def test_provider_route_requires_exact_hungary_current_stock_scope(self):
        cases = (
            (dict(country="DE"), "NOT_HUNGARY"),
            (dict(current_report=False), "REPORT_NOT_CURRENT"),
            (dict(national_scope=False), "NO_NATIONAL_SCOPE"),
            (dict(residential_radiator_park=False), "NO_RESIDENTIAL_RADIATOR_PARK"),
            (dict(hydronic_radiator_scope=False), "NO_HYDRONIC_RADIATOR_SCOPE"),
            (dict(direct_acquisition_route=False), "NO_DIRECT_ACQUISITION_ROUTE"),
        )
        for override, expected_reason in cases:
            with self.subTest(override=override):
                decision = assess_radiator_data_provider_route(brg_candidate(**override))
                self.assertEqual(decision.route_status, "Q")
                self.assertIn(expected_reason, decision.reasons)
                self.assertFalse(decision.p42_national_authority)

    def test_catalogue_scope_cannot_promote_uninspected_numeric_cells(self):
        decision = assess_radiator_data_provider_route(
            brg_candidate(
                end_use_segmentation=True,
                product_type_segmentation=True,
                public_numeric_stock_cells=False,
            )
        )
        self.assertEqual(decision.route_status, "QUALIFIED_PROVIDER_ROUTE")
        self.assertFalse(decision.p42_national_authority)

    def test_even_numeric_stock_cells_do_not_replace_reuse_upgrade_engineering(self):
        decision = assess_radiator_data_provider_route(
            brg_candidate(
                public_numeric_stock_cells=True,
                installed_stock_type_distribution_verified=True,
                reuse_upgrade_classification_verified=False,
                replacement_quantity_verified=False,
            )
        )
        self.assertFalse(decision.p42_national_authority)
        self.assertEqual(decision.unresolved_p42_claims, REQUIRED_P42_CLAIMS)

    def test_registry_has_exact_three_separated_route_roles(self):
        with ROUTES.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 3)
        self.assertEqual(
            {row["source_role"] for row in rows},
            {
                "PRIMARY_COMMERCIAL_STOCK_ROUTE",
                "INDEPENDENT_PUBLIC_CALIBRATION_ROUTE",
                "INDEPENDENT_MARKET_FLOW_DIAGNOSTIC",
            },
        )

    def test_brg_registry_row_freezes_exact_current_scope_and_non_promotion(self):
        with ROUTES.open(encoding="utf-8", newline="") as fh:
            rows = {row["route_id"]: row for row in csv.DictReader(fh)}
        row = rows["BRG_HUHC2026_RAD_PARK"]
        self.assertEqual(row["reference_year"], "2026")
        self.assertEqual(row["report_ref"], "HUHC2026")
        self.assertEqual(row["residential_radiator_park"], "YES")
        self.assertEqual(row["hydronic_radiator_scope"], "YES")
        self.assertEqual(row["public_numeric_stock_cells"], "NO")
        self.assertEqual(row["p42_national_authority"], "NO")

    def test_p42_five_programme_claims_remain_q_and_disabled(self):
        with P42.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(tuple(row["claim_id"] for row in rows), REQUIRED_P42_CLAIMS)
        self.assertTrue(all(row["current_status"] == "Q" for row in rows))
        self.assertTrue(all(row["programme_use_allowed"] == "NO" for row in rows))

    def test_document_freezes_core_non_equivalence_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for boundary in (
            "DATA-PACKAGE SCOPE MATCH != ACQUIRED NUMERIC EVIDENCE != P42 NATIONAL AUTHORITY",
            "MARKET SHARE != INSTALLED PARK COMPOSITION",
            "ANNUAL SALES != INSTALLED STOCK",
            "ANNUAL IMPORT/EXPORT != INSTALLED STOCK",
            "REPLACEMENT-MARKET SALES != HEAT-PUMP PROGRAMME REPLACEMENT REQUIREMENT",
            "NÉER2 2000-BUILDING TYPOLOGY != CURRENT NATIONAL RADIATOR UNIT INVENTORY",
        ):
            self.assertIn(boundary, text)
        self.assertIn("No sample request, enquiry, email or purchase is performed in P46.", text)


if __name__ == "__main__":
    unittest.main()
