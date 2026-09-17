from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path
import unittest

from modules.B02.residential_radiator_schedule_recovery import (
    HYBRID_RADIATOR_FLOOR,
    QUALIFIED_BOUNDED_RESIDENTIAL_SCHEDULE,
    ResidentialRadiatorScheduleError,
    ResidentialRadiatorScheduleRow,
    schedule_grants_current_stock_authority,
    schedule_grants_national_p42_authority,
    summarize_residential_radiator_schedule,
    validate_residential_radiator_schedule_row,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_p52_residential_radiator_schedule_recovery.csv"
SOURCE_PACK = ROOT / "docs" / "source_packs" / "B02_P52_RESIDENTIAL_RADIATOR_SCHEDULE_RECOVERY.md"


def _flag(value: str) -> bool:
    if value == "YES":
        return True
    if value == "NO":
        return False
    raise AssertionError(f"unexpected flag: {value}")


class TestB02P52ResidentialRadiatorScheduleRecovery(unittest.TestCase):
    def rows(self) -> list[ResidentialRadiatorScheduleRow]:
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            materialized = list(csv.DictReader(handle))
        return [
            ResidentialRadiatorScheduleRow(
                evidence_id=row["evidence_id"],
                cohort_id=row["cohort_id"],
                coverage_id=row["coverage_id"],
                source_role=row["source_role"],
                installation_status=row["installation_status"],
                residential_scope=_flag(row["residential_scope"]),
                heating_system_scope=row["heating_system_scope"],
                manufacturer=row["manufacturer"],
                product_family=row["product_family"],
                type_size_token=row["type_size_token"],
                emitter_family=row["emitter_family"],
                quantity=int(row["quantity"]),
                dwelling_count_scope=int(row["dwelling_count_scope"]),
                source_url=row["source_url"],
                source_locator=row["source_locator"],
                source_date=row["source_date"],
                hybrid_floor_heating_present=_flag(row["hybrid_floor_heating_present"]),
                current_installed_stock_claimed=_flag(row["current_installed_stock_claimed"]),
                pre_retrofit_stock_claimed=_flag(row["pre_retrofit_stock_claimed"]),
                national_p42_authority_claimed=_flag(row["national_p42_authority_claimed"]),
                programme_use_claimed=_flag(row["programme_use_claimed"]),
            )
            for row in materialized
        ]

    def test_registry_has_exact_33_source_native_rows(self) -> None:
        rows = self.rows()
        self.assertEqual(33, len(rows))
        self.assertEqual(33, len({row.evidence_id for row in rows}))
        self.assertEqual({"SZOVA_SZOLLOSI_8_DWELLING_2017"}, {row.cohort_id for row in rows})

    def test_every_registry_row_qualifies_bounded_only(self) -> None:
        for row in self.rows():
            self.assertEqual(
                QUALIFIED_BOUNDED_RESIDENTIAL_SCHEDULE,
                validate_residential_radiator_schedule_row(row),
            )

    def test_exact_eight_dwelling_summary(self) -> None:
        summary = summarize_residential_radiator_schedule(self.rows())
        self.assertEqual(8, summary.dwelling_count)
        self.assertEqual(53, summary.total_radiators)
        self.assertEqual(44, summary.panel_radiators)
        self.assertEqual(9, summary.towel_radiators)
        self.assertAlmostEqual(6.625, summary.radiators_per_dwelling)
        self.assertEqual(HYBRID_RADIATOR_FLOOR, summary.heating_system_scope)

    def test_exact_configuration_counts(self) -> None:
        summary = summarize_residential_radiator_schedule(self.rows())
        self.assertEqual(
            {"11KV": 14, "22KV": 29, "33KV": 1, "TOWEL_RADIATOR": 9},
            summary.configuration_counts,
        )

    def test_exact_type_size_counts(self) -> None:
        summary = summarize_residential_radiator_schedule(self.rows())
        self.assertEqual(
            {
                "11KV-600-400": 8,
                "11KV-600-520": 3,
                "11KV-600-600": 3,
                "22KV-600-1000": 4,
                "22KV-600-1120": 3,
                "22KV-600-1200": 1,
                "22KV-600-1400": 1,
                "22KV-600-520": 2,
                "22KV-600-600": 2,
                "22KV-600-720": 6,
                "22KV-600-800": 5,
                "22KV-600-920": 5,
                "33KV-900-520": 1,
                "DELLA-1100x600": 9,
            },
            summary.type_size_counts,
        )

    def test_design_schedule_never_grants_stock_or_p42_authority(self) -> None:
        summary = summarize_residential_radiator_schedule(self.rows())
        self.assertFalse(schedule_grants_current_stock_authority(summary))
        self.assertFalse(schedule_grants_national_p42_authority(summary))
        self.assertFalse(summary.current_stock_authority)
        self.assertFalse(summary.national_p42_authority)

    def test_current_stock_promotion_is_rejected(self) -> None:
        row = replace(self.rows()[0], current_installed_stock_claimed=True)
        with self.assertRaisesRegex(
            ResidentialRadiatorScheduleError,
            "DESIGN_SCHEDULE_IS_NOT_CURRENT_INSTALLED_STOCK",
        ):
            validate_residential_radiator_schedule_row(row)

    def test_pre_retrofit_stock_promotion_is_rejected(self) -> None:
        row = replace(self.rows()[0], pre_retrofit_stock_claimed=True)
        with self.assertRaisesRegex(
            ResidentialRadiatorScheduleError,
            "NEW_BUILD_SCHEDULE_IS_NOT_PRE_RETROFIT_STOCK",
        ):
            validate_residential_radiator_schedule_row(row)

    def test_national_and_programme_promotion_are_rejected(self) -> None:
        row = self.rows()[0]
        with self.assertRaisesRegex(
            ResidentialRadiatorScheduleError,
            "BOUNDED_SCHEDULE_IS_NOT_NATIONAL_P42_AUTHORITY",
        ):
            validate_residential_radiator_schedule_row(
                replace(row, national_p42_authority_claimed=True)
            )
        with self.assertRaisesRegex(
            ResidentialRadiatorScheduleError,
            "BOUNDED_SCHEDULE_DOES_NOT_SELF_AUTHORIZE_PROGRAMME_USE",
        ):
            validate_residential_radiator_schedule_row(
                replace(row, programme_use_claimed=True)
            )

    def test_hybrid_heating_must_be_disclosed(self) -> None:
        row = replace(self.rows()[0], hybrid_floor_heating_present=False)
        with self.assertRaisesRegex(
            ResidentialRadiatorScheduleError,
            "HYBRID_FLOOR_HEATING_MUST_BE_DISCLOSED",
        ):
            validate_residential_radiator_schedule_row(row)

    def test_nonresidential_and_nonpositive_rows_are_rejected(self) -> None:
        row = self.rows()[0]
        with self.assertRaisesRegex(
            ResidentialRadiatorScheduleError,
            "NON_RESIDENTIAL_ROW_FORBIDDEN",
        ):
            validate_residential_radiator_schedule_row(
                replace(row, residential_scope=False)
            )
        with self.assertRaisesRegex(
            ResidentialRadiatorScheduleError,
            "NON_POSITIVE_PHYSICAL_COUNT",
        ):
            validate_residential_radiator_schedule_row(replace(row, quantity=0))

    def test_cross_cohort_pooling_is_rejected(self) -> None:
        rows = self.rows()
        rows[-1] = replace(rows[-1], cohort_id="OTHER_COHORT")
        with self.assertRaisesRegex(
            ResidentialRadiatorScheduleError,
            "CROSS_COHORT_POOLING_FORBIDDEN",
        ):
            summarize_residential_radiator_schedule(rows)

    def test_duplicate_evidence_row_is_rejected(self) -> None:
        rows = self.rows()
        rows.append(rows[0])
        with self.assertRaisesRegex(
            ResidentialRadiatorScheduleError,
            "DUPLICATE_EVIDENCE_ROW",
        ):
            summarize_residential_radiator_schedule(rows)

    def test_coverage_denominator_mismatch_is_rejected(self) -> None:
        rows = self.rows()
        rows[0] = replace(rows[0], dwelling_count_scope=3)
        with self.assertRaisesRegex(
            ResidentialRadiatorScheduleError,
            "COVERAGE_DENOMINATOR_MISMATCH",
        ):
            summarize_residential_radiator_schedule(rows)

    def test_source_pack_freezes_non_equivalence_boundaries(self) -> None:
        text = SOURCE_PACK.read_text(encoding="utf-8")
        self.assertIn(
            "FILLED RESIDENTIAL RADIATOR SCHEDULE != CURRENT INSTALLED-STOCK CENSUS",
            text,
        )
        self.assertIn("NEW-BUILD DESIGN QUANTITY != PRE-RETROFIT STOCK QUANTITY", text)
        self.assertIn("BOUNDED 53/8 RATIO != NATIONAL RADIATORS-PER-DWELLING WEIGHT", text)
        self.assertIn("53 radiators", text)
        self.assertIn("70/50 °C", text)


if __name__ == "__main__":
    unittest.main()
