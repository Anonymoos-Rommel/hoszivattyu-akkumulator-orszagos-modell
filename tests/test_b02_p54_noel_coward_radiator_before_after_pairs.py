from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path
import unittest

from modules.B02.low_temp_radiator_before_after_pairs import (
    QUALIFIED_BOUNDED_BEFORE_AFTER_PAIR,
    LowTempRadiatorPairError,
    RadiatorBeforeAfterPair,
    pair_table_grants_heat_pump_authority,
    pair_table_grants_hungarian_stock_authority,
    pair_table_grants_implementation_authority,
    pair_table_grants_national_p42_authority,
    summarize_radiator_before_after_pairs,
    validate_radiator_before_after_pair,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_p54_noel_coward_radiator_before_after_pairs.csv"
SOURCE_PACK = ROOT / "docs" / "source_packs" / "B02_P54_NOEL_COWARD_RADIATOR_BEFORE_AFTER_PAIRS.md"


def _flag(value: str) -> bool:
    if value == "YES":
        return True
    if value == "NO":
        return False
    raise AssertionError(f"unexpected flag: {value}")


def _optional_float(value: str) -> float | None:
    return None if value == "" else float(value)


class TestB02P54NoelCowardRadiatorBeforeAfterPairs(unittest.TestCase):
    def rows(self) -> list[RadiatorBeforeAfterPair]:
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            materialized = list(csv.DictReader(handle))
        return [
            RadiatorBeforeAfterPair(
                evidence_id=row["evidence_id"],
                dwelling_id=row["dwelling_id"],
                room=row["room"],
                residential_scope=_flag(row["residential_scope"]),
                source_role=row["source_role"],
                heating_context=row["heating_context"],
                source_url=row["source_url"],
                source_locator=row["source_locator"],
                source_date=row["source_date"],
                existing_type=row["existing_type"],
                existing_size=row["existing_size"],
                existing_flow_c=float(row["existing_flow_c"]),
                existing_return_c=float(row["existing_return_c"]),
                existing_mean_c=float(row["existing_mean_c"]),
                existing_sample_model=row["existing_sample_model"],
                existing_sample_size=row["existing_sample_size"],
                existing_estimated_capacity_kw=float(row["existing_estimated_capacity_kw"]),
                existing_sample_model_exact_identity_claimed=_flag(
                    row["existing_sample_model_exact_identity_claimed"]
                ),
                proposed_model=row["proposed_model"],
                proposed_size=row["proposed_size"],
                proposed_count=int(row["proposed_count"]),
                proposed_mean_c=float(row["proposed_mean_c"]),
                proposed_flow_c=float(row["proposed_flow_c"]),
                proposed_return_c=float(row["proposed_return_c"]),
                proposed_required_capacity_kw=float(row["proposed_required_capacity_kw"]),
                proposed_estimated_capacity_source_token=row[
                    "proposed_estimated_capacity_source_token"
                ],
                proposed_estimated_capacity_kw=_optional_float(
                    row["proposed_estimated_capacity_kw"]
                ),
                proposed_capacity_source_unit_anomaly=_flag(
                    row["proposed_capacity_source_unit_anomaly"]
                ),
                implemented_claimed=_flag(row["implemented_claimed"]),
                heat_pump_claimed=_flag(row["heat_pump_claimed"]),
                hungarian_stock_authority_claimed=_flag(
                    row["hungarian_stock_authority_claimed"]
                ),
                national_p42_authority_claimed=_flag(
                    row["national_p42_authority_claimed"]
                ),
                programme_use_claimed=_flag(row["programme_use_claimed"]),
            )
            for row in materialized
        ]

    def test_registry_has_exact_six_room_pairs(self) -> None:
        rows = self.rows()
        self.assertEqual(6, len(rows))
        self.assertEqual(6, len({row.evidence_id for row in rows}))
        self.assertEqual(
            {"NOEL_COWARD_FLAT_11", "NOEL_COWARD_FLAT_18"},
            {row.dwelling_id for row in rows},
        )

    def test_every_registry_row_qualifies_bounded_pair_only(self) -> None:
        for row in self.rows():
            self.assertEqual(
                QUALIFIED_BOUNDED_BEFORE_AFTER_PAIR,
                validate_radiator_before_after_pair(row),
            )

    def test_summary_counts_are_exact_for_bounded_table(self) -> None:
        summary = summarize_radiator_before_after_pairs(self.rows())
        self.assertEqual(2, summary.dwelling_count)
        self.assertEqual(6, summary.room_pair_count)
        self.assertEqual(6, summary.existing_radiator_positions)
        self.assertEqual(7, summary.proposed_radiator_units)

    def test_temperature_transition_is_exact(self) -> None:
        summary = summarize_radiator_before_after_pairs(self.rows())
        self.assertEqual((80.0, 60.0), summary.existing_flow_return)
        self.assertEqual((65.0, 35.0), summary.proposed_flow_return)
        self.assertEqual(70.0, summary.existing_mean_c)
        self.assertEqual(50.0, summary.proposed_mean_c)
        self.assertEqual(20.0, summary.mean_water_temperature_drop_c)

    def test_five_clean_numeric_outputs_and_one_source_anomaly(self) -> None:
        summary = summarize_radiator_before_after_pairs(self.rows())
        self.assertEqual(5, summary.clean_numeric_proposed_capacity_rows)
        self.assertEqual(1, summary.source_unit_anomaly_rows)

    def test_flat18_bedroom_pair_is_materialized_exactly(self) -> None:
        row = next(r for r in self.rows() if r.evidence_id == "P54-NCH-18-BED1")
        self.assertEqual("Double Panel", row.existing_type)
        self.assertEqual("800 x 600", row.existing_size)
        self.assertEqual(1.385, row.existing_estimated_capacity_kw)
        self.assertEqual("Stelrad Classic Compact K2", row.proposed_model)
        self.assertEqual("1600 x 600", row.proposed_size)
        self.assertEqual(1.421, row.proposed_estimated_capacity_kw)

    def test_flat11_bathroom_pair_is_materialized_exactly(self) -> None:
        row = next(r for r in self.rows() if r.evidence_id == "P54-NCH-11-BATH")
        self.assertEqual("Single Panel", row.existing_type)
        self.assertEqual("410 x 450", row.existing_size)
        self.assertEqual(0.302, row.existing_estimated_capacity_kw)
        self.assertEqual("Stelrad Caliente Rail (Straight Single)", row.proposed_model)
        self.assertEqual("450 x 1199", row.proposed_size)
        self.assertEqual(0.315, row.proposed_estimated_capacity_kw)

    def test_source_2250_token_is_preserved_without_silent_normalization(self) -> None:
        row = next(r for r in self.rows() if r.evidence_id == "P54-NCH-18-LIVING")
        self.assertEqual("2250", row.proposed_estimated_capacity_source_token)
        self.assertIsNone(row.proposed_estimated_capacity_kw)
        self.assertTrue(row.proposed_capacity_source_unit_anomaly)
        with self.assertRaisesRegex(
            LowTempRadiatorPairError,
            "SOURCE_UNIT_ANOMALY_MUST_NOT_BE_SILENTLY_NORMALIZED",
        ):
            validate_radiator_before_after_pair(
                replace(row, proposed_estimated_capacity_kw=2.250)
            )

    def test_sample_existing_model_cannot_be_promoted_to_exact_installed_sku(self) -> None:
        row = self.rows()[0]
        with self.assertRaisesRegex(
            LowTempRadiatorPairError,
            "SAMPLE_MODEL_IS_NOT_EXACT_EXISTING_SKU_IDENTITY",
        ):
            validate_radiator_before_after_pair(
                replace(row, existing_sample_model_exact_identity_claimed=True)
            )

    def test_design_schedule_cannot_be_promoted_to_implementation(self) -> None:
        row = self.rows()[0]
        with self.assertRaisesRegex(
            LowTempRadiatorPairError,
            "DESIGN_SCHEDULE_IS_NOT_IMPLEMENTATION_EVIDENCE",
        ):
            validate_radiator_before_after_pair(replace(row, implemented_claimed=True))

    def test_district_heating_pair_cannot_be_promoted_to_heat_pump_evidence(self) -> None:
        row = self.rows()[0]
        with self.assertRaisesRegex(
            LowTempRadiatorPairError,
            "DISTRICT_HEATING_DESIGN_IS_NOT_HEAT_PUMP_EVIDENCE",
        ):
            validate_radiator_before_after_pair(replace(row, heat_pump_claimed=True))

    def test_population_and_programme_promotions_are_rejected(self) -> None:
        row = self.rows()[0]
        for candidate, message in (
            (
                replace(row, hungarian_stock_authority_claimed=True),
                "UK_PROJECT_IS_NOT_HUNGARIAN_STOCK_AUTHORITY",
            ),
            (
                replace(row, national_p42_authority_claimed=True),
                "BOUNDED_PAIR_TABLE_IS_NOT_NATIONAL_P42_AUTHORITY",
            ),
            (
                replace(row, programme_use_claimed=True),
                "BOUNDED_PAIR_TABLE_DOES_NOT_SELF_AUTHORIZE_PROGRAMME_USE",
            ),
        ):
            with self.assertRaisesRegex(LowTempRadiatorPairError, message):
                validate_radiator_before_after_pair(candidate)

    def test_required_capacity_must_bind_existing_estimate(self) -> None:
        row = self.rows()[0]
        with self.assertRaisesRegex(
            LowTempRadiatorPairError,
            "PAIR_REQUIRED_CAPACITY_DOES_NOT_BIND_EXISTING_ESTIMATE",
        ):
            validate_radiator_before_after_pair(
                replace(row, proposed_required_capacity_kw=9.999)
            )

    def test_proposed_temperature_must_be_lower(self) -> None:
        row = self.rows()[0]
        with self.assertRaisesRegex(
            LowTempRadiatorPairError,
            "PROPOSED_MEAN_NOT_LOWER_THAN_EXISTING",
        ):
            validate_radiator_before_after_pair(
                replace(
                    row,
                    proposed_flow_c=80,
                    proposed_return_c=60,
                    proposed_mean_c=70,
                )
            )

    def test_duplicate_dwelling_room_pair_is_rejected(self) -> None:
        rows = self.rows()
        rows.append(replace(rows[0], evidence_id="P54-DUPLICATE-ID"))
        with self.assertRaisesRegex(
            LowTempRadiatorPairError,
            "DUPLICATE_DWELLING_ROOM_PAIR",
        ):
            summarize_radiator_before_after_pairs(rows)

    def test_all_authority_helpers_remain_false(self) -> None:
        summary = summarize_radiator_before_after_pairs(self.rows())
        self.assertFalse(pair_table_grants_implementation_authority(summary))
        self.assertFalse(pair_table_grants_heat_pump_authority(summary))
        self.assertFalse(pair_table_grants_hungarian_stock_authority(summary))
        self.assertFalse(pair_table_grants_national_p42_authority(summary))

    def test_source_pack_freezes_scope_and_reserve_boundaries(self) -> None:
        text = SOURCE_PACK.read_text(encoding="utf-8")
        self.assertIn(
            "UK RESIDENTIAL ENGINEERING PAIR TABLE != HUNGARIAN RESIDENTIAL STOCK",
            text,
        )
        self.assertIn("PROPOSED SCHEDULE != IMPLEMENTED / COMMISSIONED OUTCOME", text)
        self.assertIn("DISTRICT-HEATING RETROFIT DESIGN != HEAT-PUMP RETROFIT EVIDENCE", text)
        self.assertIn("SOURCE TOKEN 2250 UNDER kW HEADER != SILENTLY NORMALIZED 2.250 kW", text)
        self.assertIn("Reserve A — Cozy Energy", text)
        self.assertIn("Reserve B — 21 Highfield Road", text)
        self.assertIn("Reserve C — ECO4 Daikin EDLA08", text)


if __name__ == "__main__":
    unittest.main()
