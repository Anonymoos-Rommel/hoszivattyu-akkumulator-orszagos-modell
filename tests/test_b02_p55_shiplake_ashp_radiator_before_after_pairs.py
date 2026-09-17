from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path
import unittest

from modules.B02.ashp_radiator_before_after_pairs import (
    AshpRadiatorBeforeAfterPair,
    AshpRadiatorPairError,
    EXACT_DERIVED_FROM_SOURCE_NATIVE_FLOW_AND_MWT,
    QUALIFIED_BOUNDED_ASHP_BEFORE_AFTER_PAIR,
    SOURCE_NATIVE,
    pair_table_grants_ashp_design_authority,
    pair_table_grants_commissioning_authority,
    pair_table_grants_hungarian_stock_authority,
    pair_table_grants_implementation_authority,
    pair_table_grants_national_p42_authority,
    summarize_ashp_radiator_before_after_pairs,
    validate_ashp_radiator_before_after_pair,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_p55_shiplake_ashp_radiator_before_after_pairs.csv"
SOURCE_PACK = ROOT / "docs" / "source_packs" / "B02_P55_SHIPLAKE_ASHP_RADIATOR_BEFORE_AFTER_PAIRS.md"


def _flag(value: str) -> bool:
    if value == "YES":
        return True
    if value == "NO":
        return False
    raise AssertionError(f"unexpected flag: {value}")


class TestB02P55ShiplakeAshpRadiatorBeforeAfterPairs(unittest.TestCase):
    def rows(self) -> list[AshpRadiatorBeforeAfterPair]:
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            materialized = list(csv.DictReader(handle))
        return [
            AshpRadiatorBeforeAfterPair(
                evidence_id=row["evidence_id"],
                dwelling_id=row["dwelling_id"],
                room=row["room"],
                residential_scope=_flag(row["residential_scope"]),
                source_role=row["source_role"],
                heating_context=row["heating_context"],
                source_url=row["source_url"],
                source_locator=row["source_locator"],
                source_date=row["source_date"],
                heating_type=row["heating_type"],
                design_external_temp_c=float(row["design_external_temp_c"]),
                building_heat_source_required_kw=float(row["building_heat_source_required_kw"]),
                heat_pump_output_design_kw=float(row["heat_pump_output_design_kw"]),
                max_designed_flow_c=float(row["max_designed_flow_c"]),
                max_flow_provenance=row["max_flow_provenance"],
                custom_mwt_c=float(row["custom_mwt_c"]),
                mwt_provenance=row["mwt_provenance"],
                derived_return_c=float(row["derived_return_c"]),
                return_provenance=row["return_provenance"],
                return_source_native_claimed=_flag(row["return_source_native_claimed"]),
                room_heat_loss_w=float(row["room_heat_loss_w"]),
                existing_radiator_type=row["existing_radiator_type"],
                existing_height_mm=int(row["existing_height_mm"]),
                existing_length_mm=int(row["existing_length_mm"]),
                proposed_emitters=row["proposed_emitters"],
                proposed_count=int(row["proposed_count"]),
                proposed_output_at_custom_mwt_w=float(row["proposed_output_at_custom_mwt_w"]),
                implemented_claimed=_flag(row["implemented_claimed"]),
                commissioned_claimed=_flag(row["commissioned_claimed"]),
                hungarian_stock_authority_claimed=_flag(row["hungarian_stock_authority_claimed"]),
                national_p42_authority_claimed=_flag(row["national_p42_authority_claimed"]),
                programme_use_claimed=_flag(row["programme_use_claimed"]),
            )
            for row in materialized
        ]

    def test_registry_has_exact_ten_room_pairs(self) -> None:
        rows = self.rows()
        self.assertEqual(10, len(rows))
        self.assertEqual({"CHO-612_SHIPLAKE_LOCK"}, {row.dwelling_id for row in rows})
        self.assertEqual(10, len({row.evidence_id for row in rows}))

    def test_every_row_qualifies_bounded_ashp_design_pair(self) -> None:
        for row in self.rows():
            self.assertEqual(
                QUALIFIED_BOUNDED_ASHP_BEFORE_AFTER_PAIR,
                validate_ashp_radiator_before_after_pair(row),
            )

    def test_temperature_provenance_is_exact(self) -> None:
        row = self.rows()[0]
        self.assertEqual(50.0, row.max_designed_flow_c)
        self.assertEqual(SOURCE_NATIVE, row.max_flow_provenance)
        self.assertEqual(46.5, row.custom_mwt_c)
        self.assertEqual(SOURCE_NATIVE, row.mwt_provenance)
        self.assertEqual(43.0, row.derived_return_c)
        self.assertEqual(
            EXACT_DERIVED_FROM_SOURCE_NATIVE_FLOW_AND_MWT,
            row.return_provenance,
        )
        self.assertFalse(row.return_source_native_claimed)

    def test_return_is_exactly_derived_from_source_native_flow_and_mwt(self) -> None:
        row = self.rows()[0]
        self.assertEqual(43.0, 2 * row.custom_mwt_c - row.max_designed_flow_c)
        with self.assertRaisesRegex(AshpRadiatorPairError, "RETURN_DERIVATION_MISMATCH"):
            validate_ashp_radiator_before_after_pair(replace(row, derived_return_c=42.9))

    def test_derived_return_cannot_be_promoted_to_source_native(self) -> None:
        row = self.rows()[0]
        with self.assertRaisesRegex(
            AshpRadiatorPairError,
            "DERIVED_RETURN_MUST_NOT_BE_CLAIMED_SOURCE_NATIVE",
        ):
            validate_ashp_radiator_before_after_pair(
                replace(row, return_source_native_claimed=True)
            )

    def test_project_context_is_ashp(self) -> None:
        row = self.rows()[0]
        self.assertEqual("ASHP", row.heating_type)
        self.assertEqual(-1.8, row.design_external_temp_c)
        self.assertEqual(9.85, row.building_heat_source_required_kw)
        self.assertEqual(10.0, row.heat_pump_output_design_kw)

    def test_exact_examples_are_materialized(self) -> None:
        boot = next(r for r in self.rows() if r.evidence_id == "P55-CHO612-BOOT")
        self.assertEqual("K1", boot.existing_radiator_type)
        self.assertEqual((600, 700), (boot.existing_height_mm, boot.existing_length_mm))
        self.assertEqual("K3 700x700", boot.proposed_emitters)
        self.assertEqual(913.0, boot.proposed_output_at_custom_mwt_w)

        lounge = next(r for r in self.rows() if r.evidence_id == "P55-CHO612-LOUNGE")
        self.assertEqual("P+", lounge.existing_radiator_type)
        self.assertEqual("P+ 600x2100", lounge.proposed_emitters)
        self.assertEqual(1275.03, lounge.room_heat_loss_w)
        self.assertEqual(1269.0, lounge.proposed_output_at_custom_mwt_w)

    def test_room_level_deficit_is_not_hidden_by_aggregate_margin(self) -> None:
        summary = summarize_ashp_radiator_before_after_pairs(self.rows())
        self.assertEqual(1, summary.dwelling_count)
        self.assertEqual(10, summary.room_pair_count)
        self.assertEqual(9, summary.rooms_meeting_or_exceeding_heat_loss)
        self.assertEqual(1, summary.rooms_below_heat_loss)
        self.assertAlmostEqual(8526.09, summary.total_room_heat_loss_w, places=2)
        self.assertAlmostEqual(8940.0, summary.total_proposed_output_at_custom_mwt_w, places=2)
        self.assertAlmostEqual(413.91, summary.aggregate_output_margin_w, places=2)

    def test_design_authority_only(self) -> None:
        summary = summarize_ashp_radiator_before_after_pairs(self.rows())
        self.assertTrue(pair_table_grants_ashp_design_authority(summary))
        self.assertFalse(pair_table_grants_implementation_authority(summary))
        self.assertFalse(pair_table_grants_commissioning_authority(summary))
        self.assertFalse(pair_table_grants_hungarian_stock_authority(summary))
        self.assertFalse(pair_table_grants_national_p42_authority(summary))

    def test_forbidden_promotions_are_rejected(self) -> None:
        row = self.rows()[0]
        cases = (
            (replace(row, implemented_claimed=True), "DESIGN_REPORT_IS_NOT_IMPLEMENTATION_EVIDENCE"),
            (replace(row, commissioned_claimed=True), "DESIGN_REPORT_IS_NOT_COMMISSIONING_EVIDENCE"),
            (replace(row, hungarian_stock_authority_claimed=True), "UK_DWELLING_IS_NOT_HUNGARIAN_STOCK_AUTHORITY"),
            (replace(row, national_p42_authority_claimed=True), "BOUNDED_ASHP_PAIR_TABLE_IS_NOT_NATIONAL_P42_AUTHORITY"),
            (replace(row, programme_use_claimed=True), "BOUNDED_ASHP_PAIR_TABLE_DOES_NOT_SELF_AUTHORIZE_PROGRAMME_USE"),
        )
        for candidate, message in cases:
            with self.assertRaisesRegex(AshpRadiatorPairError, message):
                validate_ashp_radiator_before_after_pair(candidate)

    def test_source_pack_freezes_key_boundaries(self) -> None:
        text = SOURCE_PACK.read_text(encoding="utf-8")
        self.assertIn("EXACT DERIVATION FROM TWO SOURCE-NATIVE INPUTS != SOURCE-NATIVE RETURN FIELD", text)
        self.assertIn("1269 W < 1275.03 W -> ROOM-LEVEL DEFICIT RETAINED", text)
        self.assertIn("UK RESIDENTIAL ASHP DESIGN != HUNGARIAN RESIDENTIAL STOCK", text)
        self.assertIn("DESIGN REPORT != INSTALLED / COMMISSIONED OUTCOME", text)


if __name__ == "__main__":
    unittest.main()
