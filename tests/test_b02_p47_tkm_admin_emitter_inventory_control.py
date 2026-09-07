import csv
import unittest
from pathlib import Path

from modules.B02.admin_emitter_inventory_control import (
    P42_CLAIMS,
    AdminEmitterInventoryCandidate,
    MarketFlowUnitCandidate,
    assess_admin_emitter_inventory,
    assess_market_flow_unit,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_p47_admin_emitter_inventory_controls.csv"
P42 = ROOT / "registry" / "b02_p42_radiator_stock_requirement.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P47_TKM_ADMIN_EMITTER_INVENTORY_AND_FLOW_UNIT_CONTROL.md"


def tkm_candidate(**overrides):
    values = dict(
        surface_id="TKM2025_PROJECT_EMITTER_INVENTORY",
        programme="TKM/2025",
        country="HU",
        authority_url="https://www.nffku.hu/images/tavolrol/02_Altalanos_Palyazati_%20Projekt_Megvalositasi_Utmutato.pdf",
        exact_locator="PDF p19 type/count invoice fields; PDF p29 heat-emitter-count inspection field",
        current_surface=True,
        dwelling_level_binding=True,
        cost_allocator_route=True,
        apartment_heat_meter_route=False,
        emitter_count_field=True,
        installed_device_type_field=True,
        realised_count_field=True,
        radiator_valve_type_count_field=True,
        heat_emitter_count_auditable=True,
        public_aggregate_emitter_count=False,
        national_stock_complete=False,
        reproducible_binding=True,
    )
    values.update(overrides)
    return AdminEmitterInventoryCandidate(**values)


def kg_flow_candidate(**overrides):
    values = dict(
        control_id="WITS_HU_HS732219_2022_FLOW_UNIT",
        source_label="IndexBox-like generic market units guarded by WITS",
        reported_quantity=42_000_000,
        reported_quantity_label="units",
        hs_code="732219",
        authoritative_quantity_unit="KG",
        authoritative_unit_url="https://wits.worldbank.org/trade/comtrade/en/country/HUN/year/2022/tradeflow/Exports/partner/ALL/product/732219",
        physical_piece_mapping_proven=False,
        reproducible_binding=True,
    )
    values.update(overrides)
    return MarketFlowUnitCandidate(**values)


class B02P47TkmAdminEmitterInventoryControlTests(unittest.TestCase):
    def test_tkm_cost_allocator_route_is_qualified_per_emitter_admin_surface(self):
        decision = assess_admin_emitter_inventory(tkm_candidate())
        self.assertEqual(decision.surface_status, "QUALIFIED_ADMIN_EMITTER_INVENTORY")
        self.assertTrue(decision.per_emitter_inventory_surface)
        self.assertFalse(decision.public_numeric_execution)
        self.assertFalse(decision.p42_national_authority)
        self.assertEqual(decision.unresolved_p42_claims, P42_CLAIMS)

    def test_apartment_heat_meter_route_cannot_be_relabelled_per_radiator_inventory(self):
        decision = assess_admin_emitter_inventory(
            tkm_candidate(cost_allocator_route=False, apartment_heat_meter_route=True)
        )
        self.assertEqual(decision.surface_status, "Q")
        self.assertFalse(decision.per_emitter_inventory_surface)
        self.assertIn("NO_PROVEN_PER_EMITTER_RECORD_SURFACE", decision.reasons)

    def test_tkm_surface_requires_realised_type_count_and_audit_fields(self):
        cases = (
            (dict(emitter_count_field=False),),
            (dict(installed_device_type_field=False),),
            (dict(realised_count_field=False),),
            (dict(heat_emitter_count_auditable=False),),
        )
        for (override,) in cases:
            with self.subTest(override=override):
                decision = assess_admin_emitter_inventory(tkm_candidate(**override))
                self.assertEqual(decision.surface_status, "Q")
                self.assertFalse(decision.per_emitter_inventory_surface)

    def test_public_project_aggregate_would_still_not_self_authorize_national_p42(self):
        decision = assess_admin_emitter_inventory(
            tkm_candidate(public_aggregate_emitter_count=True)
        )
        self.assertTrue(decision.public_numeric_execution)
        self.assertFalse(decision.p42_national_authority)
        self.assertEqual(decision.unresolved_p42_claims, P42_CLAIMS)

    def test_generic_units_with_authoritative_kg_basis_are_not_physical_pieces(self):
        decision = assess_market_flow_unit(kg_flow_candidate())
        self.assertEqual(decision.status, "QUALIFIED_FLOW_UNIT_CONTROL")
        self.assertFalse(decision.physical_radiator_piece_count_authority)
        self.assertIn("GENERIC_UNIT_LABEL_NOT_PIECE_AUTHORITY", decision.reasons)
        self.assertIn("AUTHORITATIVE_TRADE_UNIT_IS_KG", decision.reasons)

    def test_piece_authority_requires_both_piece_unit_and_explicit_mapping(self):
        no_mapping = assess_market_flow_unit(
            kg_flow_candidate(authoritative_quantity_unit="PIECE")
        )
        self.assertFalse(no_mapping.physical_radiator_piece_count_authority)
        mapped = assess_market_flow_unit(
            kg_flow_candidate(
                authoritative_quantity_unit="PIECE",
                physical_piece_mapping_proven=True,
            )
        )
        self.assertTrue(mapped.physical_radiator_piece_count_authority)

    def test_registry_separates_admin_legal_and_market_flow_roles(self):
        with REGISTRY.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 4)
        self.assertEqual(
            {row["source_role"] for row in rows},
            {
                "ADMINISTRATIVE_EMITTER_INVENTORY_SURFACE",
                "IMPLEMENTED_DWELLING_LEVEL_COMPLETION_SURFACE",
                "LEGAL_PER_EMITTER_SEMANTIC_CONTROL",
                "MARKET_FLOW_UNIT_CONTROL",
            },
        )
        self.assertTrue(all(row["p42_national_authority"] == "NO" for row in rows))

    def test_tkm_registry_rows_freeze_exact_non_public_aggregate_boundary(self):
        with REGISTRY.open(encoding="utf-8", newline="") as fh:
            rows = {row["control_id"]: row for row in csv.DictReader(fh)}
        project = rows["TKM2025_PROJECT_EMITTER_INVENTORY"]
        handover = rows["TKM2025_TECHNICAL_HANDOVER"]
        self.assertEqual(project["per_emitter_count_field"], "YES")
        self.assertEqual(project["device_type_field"], "YES")
        self.assertEqual(project["public_aggregate_emitter_count"], "NO")
        self.assertEqual(handover["realised_count_field"], "YES")
        self.assertEqual(handover["public_aggregate_emitter_count"], "NO")

    def test_p42_five_programme_claims_remain_q_and_disabled(self):
        with P42.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(tuple(row["claim_id"] for row in rows), P42_CLAIMS)
        self.assertTrue(all(row["current_status"] == "Q" for row in rows))
        self.assertTrue(all(row["programme_use_allowed"] == "NO" for row in rows))

    def test_document_freezes_programme_intent_and_unit_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for boundary in (
            "ADMIN RECORD SCHEMA != PUBLIC AGGREGATE != NATIONAL P42 STOCK AUTHORITY",
            "COST-ALLOCATOR ROUTE -> PER-EMITTER RECORD SURFACE",
            "APARTMENT HEAT-METER ROUTE != PER-RADIATOR RECORD SURFACE",
            "PROJECT COVERAGE != NATIONAL STOCK COMPLETENESS",
            "MARKET FLOW KG != INSTALLED STOCK UNIT COUNT",
            'GENERIC "UNITS" LABEL != PHYSICAL RADIATOR PIECES',
            "RECORD EXISTS IN ADMIN SYSTEM != RECORD IS PUBLICLY AGGREGATED",
            "TKM PROJECT POPULATION != ALL HUNGARIAN HYDRONIC DWELLINGS",
            "HS 732219 TRADE QUANTITY UNIT = KG",
            "KG != PIECE",
        ):
            self.assertIn(boundary, text)
        self.assertIn("No external request, email or purchase is performed in P47.", text)


if __name__ == "__main__":
    unittest.main()
