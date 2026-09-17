from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path
import unittest

from modules.B02.zfr_radiator_retrofit_portfolio import (
    APPROXIMATE,
    BUILDING_COUNT,
    COST_ALLOCATOR_COUNT,
    NEW_RADIATOR_COUNT,
    ZfrRadiatorRetrofitPortfolioError,
    ZfrRetrofitEvidence,
    portfolio_grants_exact_before_after_pair_authority,
    portfolio_grants_national_p42_authority,
    summarize_zfr_retrofit_portfolio,
    validate_zfr_retrofit_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_p53_zfr_radiator_retrofit_portfolio.csv"
SOURCE_PACK = ROOT / "docs" / "source_packs" / "B02_P53_ZFR_RADIATOR_RETROFIT_PORTFOLIO.md"


def _flag(value: str) -> bool:
    if value == "YES":
        return True
    if value == "NO":
        return False
    raise AssertionError(f"unexpected flag: {value}")


class TestB02P53ZfrRadiatorRetrofitPortfolio(unittest.TestCase):
    def rows(self) -> list[ZfrRetrofitEvidence]:
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            materialized = list(csv.DictReader(handle))
        return [
            ZfrRetrofitEvidence(
                evidence_id=row["evidence_id"],
                source_version=row["source_version"],
                source_role=row["source_role"],
                metric=row["metric"],
                value=float(row["value"]),
                unit=row["unit"],
                precision=row["precision"],
                residential_scope=_flag(row["residential_scope"]),
                implemented_scope=_flag(row["implemented_scope"]),
                source_url=row["source_url"],
                source_locator=row["source_locator"],
                source_date=row["source_date"],
                national_p42_authority_claimed=_flag(row["national_p42_authority_claimed"]),
                exact_before_after_pair_authority_claimed=_flag(
                    row["exact_before_after_pair_authority_claimed"]
                ),
                programme_use_claimed=_flag(row["programme_use_claimed"]),
            )
            for row in materialized
        ]

    def test_registry_has_exact_nine_source_native_rows(self) -> None:
        rows = self.rows()
        self.assertEqual(9, len(rows))
        self.assertEqual(9, len({row.evidence_id for row in rows}))

    def test_every_registry_row_qualifies_bounded_only(self) -> None:
        for row in self.rows():
            self.assertEqual(
                "QUALIFIED_BOUNDED_ZFR_RETROFIT_EVIDENCE",
                validate_zfr_retrofit_evidence(row),
            )

    def test_exact_bounded_portfolio_summary(self) -> None:
        summary = summarize_zfr_retrofit_portfolio(self.rows())
        self.assertEqual(3621, summary.dwelling_count)
        self.assertEqual(6000, summary.new_radiators_reported)
        self.assertEqual(12500, summary.cost_allocators_reported)
        self.assertTrue(summary.new_radiators_approximate)
        self.assertAlmostEqual(6000 / 3621, summary.new_radiators_per_dwelling)
        self.assertAlmostEqual(12500 / 3621, summary.cost_allocators_per_dwelling)
        self.assertAlmostEqual(6000 / 12500, summary.replacement_intensity_proxy)

    def test_building_count_conflict_is_preserved(self) -> None:
        summary = summarize_zfr_retrofit_portfolio(self.rows())
        self.assertTrue(summary.building_count_conflict)
        self.assertEqual((36, 38), summary.reported_building_counts)
        self.assertIsNone(summary.building_count)

    def test_official_schema_and_survey_process_are_proven(self) -> None:
        summary = summarize_zfr_retrofit_portfolio(self.rows())
        self.assertTrue(summary.official_before_after_matrix_schema)
        self.assertTrue(summary.itemized_dwelling_survey_executed)
        self.assertTrue(summary.radiator_replacement_optional)

    def test_filled_before_after_pair_is_not_claimed(self) -> None:
        summary = summarize_zfr_retrofit_portfolio(self.rows())
        self.assertFalse(summary.exact_before_after_pair_recovered)
        self.assertFalse(portfolio_grants_exact_before_after_pair_authority(summary))

    def test_portfolio_never_grants_national_p42_authority(self) -> None:
        summary = summarize_zfr_retrofit_portfolio(self.rows())
        self.assertFalse(summary.current_installed_stock_census)
        self.assertFalse(summary.representative_national_weight)
        self.assertFalse(summary.national_p42_authority)
        self.assertFalse(summary.programme_use_allowed)
        self.assertFalse(portfolio_grants_national_p42_authority(summary))

    def test_new_radiator_count_must_remain_approximate(self) -> None:
        rows = self.rows()
        index = next(i for i, row in enumerate(rows) if row.metric == NEW_RADIATOR_COUNT)
        rows[index] = replace(rows[index], precision="REPORTED_INTEGER")
        with self.assertRaisesRegex(
            ZfrRadiatorRetrofitPortfolioError,
            "NEW_RADIATOR_COUNT_MUST_RETAIN_APPROXIMATE_PRECISION",
        ):
            summarize_zfr_retrofit_portfolio(rows)

    def test_conflicting_dwelling_count_is_rejected(self) -> None:
        rows = self.rows()
        dwelling_rows = [i for i, row in enumerate(rows) if row.metric == "DWELLING_COUNT"]
        self.assertGreaterEqual(len(dwelling_rows), 2)
        index = dwelling_rows[-1]
        rows[index] = replace(rows[index], value=3622)
        with self.assertRaisesRegex(
            ZfrRadiatorRetrofitPortfolioError,
            "CONFLICTING_DWELLING_COUNT",
        ):
            summarize_zfr_retrofit_portfolio(rows)

    def test_national_p42_promotion_is_rejected(self) -> None:
        row = self.rows()[1]
        with self.assertRaisesRegex(
            ZfrRadiatorRetrofitPortfolioError,
            "CONTRACTOR_PORTFOLIO_IS_NOT_NATIONAL_P42_AUTHORITY",
        ):
            validate_zfr_retrofit_evidence(
                replace(row, national_p42_authority_claimed=True)
            )

    def test_exact_pair_promotion_is_rejected(self) -> None:
        row = self.rows()[1]
        with self.assertRaisesRegex(
            ZfrRadiatorRetrofitPortfolioError,
            "FILLED_BEFORE_AFTER_PAIR_TABLE_NOT_RECOVERED",
        ):
            validate_zfr_retrofit_evidence(
                replace(row, exact_before_after_pair_authority_claimed=True)
            )

    def test_programme_use_self_authorization_is_rejected(self) -> None:
        row = self.rows()[1]
        with self.assertRaisesRegex(
            ZfrRadiatorRetrofitPortfolioError,
            "BOUNDED_PORTFOLIO_DOES_NOT_SELF_AUTHORIZE_PROGRAMME_USE",
        ):
            validate_zfr_retrofit_evidence(replace(row, programme_use_claimed=True))

    def test_nonresidential_and_duplicate_rows_are_rejected(self) -> None:
        row = self.rows()[1]
        with self.assertRaisesRegex(
            ZfrRadiatorRetrofitPortfolioError,
            "NON_RESIDENTIAL_ROW_FORBIDDEN",
        ):
            validate_zfr_retrofit_evidence(replace(row, residential_scope=False))

        rows = self.rows()
        rows.append(rows[0])
        with self.assertRaisesRegex(
            ZfrRadiatorRetrofitPortfolioError,
            "DUPLICATE_EVIDENCE_ROW",
        ):
            summarize_zfr_retrofit_portfolio(rows)

    def test_source_pack_freezes_non_equivalence_boundaries(self) -> None:
        text = SOURCE_PACK.read_text(encoding="utf-8")
        self.assertIn("CONTRACTOR ZFR PORTFOLIO != NATIONAL RESIDENTIAL STOCK", text)
        self.assertIn("COST-ALLOCATOR COUNT != PRE-RETROFIT INSTALLED-RADIATOR CENSUS", text)
        self.assertIn(
            "~6000 NEW / 12500 COST ALLOCATORS != EXACT SAME-RADIATOR REPLACEMENT FRACTION",
            text,
        )
        self.assertIn(
            "IMPLEMENTED RETROFIT QUANTITY != ORIGINAL->NEW TYPE/SIZE PAIR TABLE",
            text,
        )
        self.assertIn("36 vs 38 BUILDING COUNT CONFLICT -> BUILDING DENOMINATOR BLOCKED", text)
        self.assertIn("3621 dwellings", text)

    def test_registry_retains_required_quantity_semantics(self) -> None:
        rows = self.rows()
        new_row = next(row for row in rows if row.metric == NEW_RADIATOR_COUNT)
        device_row = next(row for row in rows if row.metric == COST_ALLOCATOR_COUNT)
        building_rows = [row for row in rows if row.metric == BUILDING_COUNT]
        self.assertEqual(APPROXIMATE, new_row.precision)
        self.assertEqual("RADIATORS", new_row.unit)
        self.assertEqual("DEVICES", device_row.unit)
        self.assertEqual({36, 38}, {int(row.value) for row in building_rows})


if __name__ == "__main__":
    unittest.main()
