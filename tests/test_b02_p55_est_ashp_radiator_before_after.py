from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path
import unittest

from modules.B02.ashp_radiator_before_after_testhouse import (
    AshpRadiatorBeforeAfterError,
    AshpRadiatorPair,
    QUALIFIED_BOUNDED_ASHP_PAIR,
    pairs_grant_hungarian_stock_authority,
    pairs_grant_national_p42_authority,
    pairs_grant_occupied_household_authority,
    summarize_ashp_radiator_pairs,
    validate_ashp_radiator_pair,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_p55_est_ashp_radiator_before_after.csv"
SOURCE_PACK = ROOT / "docs" / "source_packs" / "B02_P55_EST_ASHP_RADIATOR_BEFORE_AFTER.md"


def _flag(value: str) -> bool:
    if value == "YES":
        return True
    if value == "NO":
        return False
    raise AssertionError(f"unexpected flag: {value}")


class TestB02P55EstAshpRadiatorBeforeAfter(unittest.TestCase):
    def rows(self) -> list[AshpRadiatorPair]:
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        return [
            AshpRadiatorPair(
                evidence_id=row["evidence_id"],
                room=row["room"],
                residential_scope=_flag(row["residential_scope"]),
                implemented_ashp_scope=_flag(row["implemented_ashp_scope"]),
                source_role=row["source_role"],
                original_type=row["original_type"],
                original_height_mm=int(row["original_height_mm"]),
                original_length_mm=int(row["original_length_mm"]),
                original_output_w=int(row["original_output_w"]),
                original_output_basis=row["original_output_basis"],
                proposed_type=row["proposed_type"],
                proposed_height_mm=int(row["proposed_height_mm"]),
                proposed_length_mm=int(row["proposed_length_mm"]),
                proposed_output_w=int(row["proposed_output_w"]),
                design_room_temp_c=int(row["design_room_temp_c"]),
                target_flow_c=float(row["target_flow_c"]),
                target_return_c=float(row["target_return_c"]),
                source_url=row["source_url"],
                source_locator=row["source_locator"],
                source_date=row["source_date"],
                occupied_household_claimed=_flag(row["occupied_household_claimed"]),
                hungarian_stock_authority_claimed=_flag(row["hungarian_stock_authority_claimed"]),
                national_p42_authority_claimed=_flag(row["national_p42_authority_claimed"]),
                programme_use_claimed=_flag(row["programme_use_claimed"]),
            )
            for row in rows
        ]

    def test_registry_contains_exact_twelve_room_pairs(self) -> None:
        rows = self.rows()
        self.assertEqual(12, len(rows))
        self.assertEqual(12, len({row.evidence_id for row in rows}))
        self.assertEqual(12, len({row.room for row in rows}))

    def test_all_rows_qualify_bounded_only(self) -> None:
        for row in self.rows():
            self.assertEqual(QUALIFIED_BOUNDED_ASHP_PAIR, validate_ashp_radiator_pair(row))

    def test_exact_summary_counts(self) -> None:
        summary = summarize_ashp_radiator_pairs(self.rows())
        self.assertEqual(12, summary.rooms)
        self.assertEqual(9, summary.changed_rooms)
        self.assertEqual(3, summary.unchanged_rooms)

    def test_exact_source_totals(self) -> None:
        summary = summarize_ashp_radiator_pairs(self.rows())
        self.assertAlmostEqual(6.445, summary.original_total_output_kw)
        self.assertAlmostEqual(6.421, summary.upgraded_total_output_kw)
        self.assertAlmostEqual(1.6, summary.original_at_target_total_output_kw)

    def test_exact_ashp_design_context(self) -> None:
        summary = summarize_ashp_radiator_pairs(self.rows())
        self.assertEqual(45.0, summary.target_flow_c)
        self.assertEqual(35.0, summary.target_return_c)
        self.assertEqual(4.4, summary.whole_house_design_heat_loss_kw)
        self.assertEqual(6.0, summary.heat_pump_capacity_kw)
        self.assertTrue(summary.implemented_ashp_precedent)

    def test_expected_unchanged_rooms(self) -> None:
        rows = {row.room: row for row in self.rows()}
        for room in ("Landing", "Bathroom", "En-suite"):
            row = rows[room]
            self.assertEqual(row.original_type, row.proposed_type)
            self.assertEqual(row.original_height_mm, row.proposed_height_mm)
            self.assertEqual(row.original_length_mm, row.proposed_length_mm)

    def test_lounge_exact_before_after_pair(self) -> None:
        row = next(row for row in self.rows() if row.room == "Lounge")
        self.assertEqual("STELRAD_ELITE_P1", row.original_type)
        self.assertEqual((600, 1400, 1225), (row.original_height_mm, row.original_length_mm, row.original_output_w))
        self.assertEqual("MYSON_SELECT_STANDARD_K2", row.proposed_type)
        self.assertEqual((700, 1600, 993), (row.proposed_height_mm, row.proposed_length_mm, row.proposed_output_w))

    def test_flow_return_drift_is_rejected(self) -> None:
        row = self.rows()[0]
        with self.assertRaisesRegex(AshpRadiatorBeforeAfterError, "TARGET_FLOW_RETURN_MUST_BE_EXACT_45_35"):
            validate_ashp_radiator_pair(replace(row, target_return_c=40.0))

    def test_nonresidential_promotion_is_rejected(self) -> None:
        row = self.rows()[0]
        with self.assertRaisesRegex(AshpRadiatorBeforeAfterError, "NON_RESIDENTIAL_ROW_FORBIDDEN"):
            validate_ashp_radiator_pair(replace(row, residential_scope=False))

    def test_nonimplemented_ashp_scope_is_rejected(self) -> None:
        row = self.rows()[0]
        with self.assertRaisesRegex(AshpRadiatorBeforeAfterError, "IMPLEMENTED_ASHP_SCOPE_REQUIRED"):
            validate_ashp_radiator_pair(replace(row, implemented_ashp_scope=False))

    def test_occupied_household_promotion_is_rejected(self) -> None:
        row = self.rows()[0]
        with self.assertRaisesRegex(AshpRadiatorBeforeAfterError, "CONTROLLED_TEST_HOUSE_IS_NOT_OCCUPIED_HOUSEHOLD_SAMPLE"):
            validate_ashp_radiator_pair(replace(row, occupied_household_claimed=True))

    def test_hungarian_and_national_promotions_are_rejected(self) -> None:
        row = self.rows()[0]
        with self.assertRaisesRegex(AshpRadiatorBeforeAfterError, "UK_TEST_HOUSE_IS_NOT_HUNGARIAN_STOCK_AUTHORITY"):
            validate_ashp_radiator_pair(replace(row, hungarian_stock_authority_claimed=True))
        with self.assertRaisesRegex(AshpRadiatorBeforeAfterError, "BOUNDED_TEST_HOUSE_IS_NOT_NATIONAL_P42_AUTHORITY"):
            validate_ashp_radiator_pair(replace(row, national_p42_authority_claimed=True))

    def test_programme_use_promotion_is_rejected(self) -> None:
        row = self.rows()[0]
        with self.assertRaisesRegex(AshpRadiatorBeforeAfterError, "ENGINEERING_PRECEDENT_DOES_NOT_SELF_AUTHORIZE_PROGRAMME_USE"):
            validate_ashp_radiator_pair(replace(row, programme_use_claimed=True))

    def test_summary_never_grants_population_authority(self) -> None:
        summary = summarize_ashp_radiator_pairs(self.rows())
        self.assertFalse(pairs_grant_occupied_household_authority(summary))
        self.assertFalse(pairs_grant_hungarian_stock_authority(summary))
        self.assertFalse(pairs_grant_national_p42_authority(summary))
        self.assertFalse(summary.programme_use_allowed)

    def test_duplicate_room_pair_is_rejected(self) -> None:
        rows = self.rows()
        rows[-1] = replace(rows[-1], room=rows[0].room, evidence_id="P55-EST-DUP")
        with self.assertRaisesRegex(AshpRadiatorBeforeAfterError, "DUPLICATE_ROOM_PAIR"):
            summarize_ashp_radiator_pairs(rows)

    def test_source_pack_freezes_core_boundaries(self) -> None:
        text = SOURCE_PACK.read_text(encoding="utf-8")
        self.assertIn("CONTROLLED RESIDENTIAL TEST HOUSE != OCCUPIED HOUSEHOLD SAMPLE", text)
        self.assertIn("UK ASHP ENGINEERING PRECEDENT != HUNGARIAN RADIATOR STOCK WEIGHT", text)
        self.assertIn("45/35/20 C", text)
        self.assertIn("12 paired room positions", text)
        self.assertIn("24 Waterloo Crescent", text)


if __name__ == "__main__":
    unittest.main()
