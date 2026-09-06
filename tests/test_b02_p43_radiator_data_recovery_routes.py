import csv
import unittest
from pathlib import Path

from modules.B02.radiator_data_recovery import (
    CURRENT_STOCK,
    DISTRICT_HEATING_CURRENT_STOCK,
    QUALIFIED_ROUTE,
    Q,
    REPLACEMENT_DESIGN,
    RadiatorRecoveryRouteCandidate,
    assess_radiator_recovery_route,
)


ROOT = Path(__file__).resolve().parents[1]
ROUTES = ROOT / "registry" / "b02_p43_radiator_data_recovery_routes.csv"
P42 = ROOT / "registry" / "b02_p42_radiator_stock_requirement.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P43_RADIATOR_DATA_RECOVERY_ROUTES.md"
BME_REQUEST = ROOT / "docs" / "data_requests" / "P43_BME_RADIATOR_DATA_REQUEST.md"
TECHEM_REQUEST = ROOT / "docs" / "data_requests" / "P43_TECHEM_RADIATOR_AGGREGATE_REQUEST.md"


class B02P43RadiatorDataRecoveryRouteTests(unittest.TestCase):
    def _valid_candidate(self, *, role: str, current_reference_possible: bool = True):
        return RadiatorRecoveryRouteCandidate(
            route_id="ROUTE",
            source_id="SRC",
            role=role,
            data_holder="holder",
            authority_url="https://example.invalid/source",
            exact_locator="section 1",
            availability_basis="existing bounded data asset",
            requested_field_families=(
                "EMITTER_IDENTITY",
                "UNIT_QUANTITY",
                "TYPE_CONFIGURATION",
                "DIMENSION_OR_OUTPUT",
                "SCOPE_OR_WEIGHT",
            ),
            current_reference_possible=current_reference_possible,
            anonymised_or_aggregate_request=True,
        )

    def test_all_three_bounded_roles_can_qualify_as_routes(self):
        for role, current_possible in (
            (CURRENT_STOCK, True),
            (DISTRICT_HEATING_CURRENT_STOCK, True),
            (REPLACEMENT_DESIGN, False),
        ):
            with self.subTest(role=role):
                decision = assess_radiator_recovery_route(
                    self._valid_candidate(
                        role=role, current_reference_possible=current_possible
                    )
                )
                self.assertEqual(QUALIFIED_ROUTE, decision.status)
                self.assertEqual((), decision.reasons)

    def test_recovery_route_cannot_self_authorize_p42(self):
        base = self._valid_candidate(role=CURRENT_STOCK)
        candidate = RadiatorRecoveryRouteCandidate(
            **{
                **base.__dict__,
                "claims_p42_quantity_without_recovered_data": True,
            }
        )
        decision = assess_radiator_recovery_route(candidate)
        self.assertEqual(Q, decision.status)
        self.assertIn("RECOVERY_ROUTE_CANNOT_SELF_AUTHORIZE_P42", decision.reasons)

    def test_current_stock_route_requires_current_reference_path(self):
        decision = assess_radiator_recovery_route(
            self._valid_candidate(
                role=DISTRICT_HEATING_CURRENT_STOCK,
                current_reference_possible=False,
            )
        )
        self.assertEqual(Q, decision.status)
        self.assertIn("NO_CURRENT_REFERENCE_RECOVERY_PATH", decision.reasons)

    def test_requests_are_data_minimised(self):
        base = self._valid_candidate(role=CURRENT_STOCK)
        candidate = RadiatorRecoveryRouteCandidate(
            **{
                **base.__dict__,
                "personal_data_requested": True,
                "external_binary_committed": True,
            }
        )
        decision = assess_radiator_recovery_route(candidate)
        self.assertEqual(Q, decision.status)
        self.assertIn("PERSONAL_DATA_REQUESTED", decision.reasons)
        self.assertIn("EXTERNAL_BINARY_MUST_NOT_BE_COMMITTED", decision.reasons)

    def test_registry_has_exact_three_non_promoting_routes(self):
        with ROUTES.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(
            {
                "NEER2_RAW_BUILDING_SURVEY",
                "BME_NMTK_HVAC_LAYOUTS",
                "TAVHO_COST_ALLOCATOR_INVENTORY",
            },
            {row["route_id"] for row in rows},
        )
        for row in rows:
            self.assertEqual("QUALIFIED_ROUTE", row["route_status"])
            self.assertEqual("NO", row["data_recovered"])
            self.assertEqual("NO", row["p42_quantity_authority"])
            self.assertEqual("READY_FOR_HUMAN_REVIEW", row["request_status"])

    def test_p42_programme_quantities_remain_q(self):
        with P42.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(5, len(rows))
        self.assertTrue(all(row["current_status"] == "Q" for row in rows))
        self.assertTrue(all(row["programme_use_allowed"] == "NO" for row in rows))

    def test_source_pack_freezes_recovery_boundaries_and_exact_locators(self):
        text = DOC.read_text(encoding="utf-8")
        for boundary in (
            "RECOVERY ROUTE != RECOVERED DATA != P42 QUANTITY AUTHORITY",
            "2015 OBSERVATION != 2026 OBSERVATION",
            "20 NMTK DESIGNS != EXISTING NATIONAL RADIATOR INVENTORY",
            "COST-ALLOCATOR RADIATOR INVENTORY != ALL HUNGARIAN RADIATORS",
            "RADIATOR MASS != RADIATOR UNIT COUNT",
        ):
            self.assertIn(boundary, text)
        self.assertIn("PDF page 127/167", text)
        self.assertIn("PDF page 128/167", text)
        self.assertIn("17/C § (1) a)", text)
        self.assertIn("5. melléklet 1.", text)
        self.assertIn("Data will be made available on request.", text)

    def test_both_external_requests_are_explicitly_not_sent(self):
        for path in (BME_REQUEST, TECHEM_REQUEST):
            text = path.read_text(encoding="utf-8")
            self.assertIn("READY_FOR_HUMAN_REVIEW", text)
            self.assertIn("NOT SENT", text)
        self.assertIn("csoknyai.tamas@gpk.bme.hu", BME_REQUEST.read_text(encoding="utf-8"))
        self.assertIn("techem@techem.hu", TECHEM_REQUEST.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
