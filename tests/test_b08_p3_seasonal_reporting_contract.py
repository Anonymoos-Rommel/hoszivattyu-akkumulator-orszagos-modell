import unittest
from datetime import datetime, timedelta, timezone

from modules.B08.observed_load_contract import (
    CONTROL_AREA_SCHEME,
    HUNGARY_CONTROL_AREA,
    ObservedLoadRecord,
)
from modules.B08.seasonal_reporting_contract import (
    ReportingWindowKind,
    assess_national_baseline,
    canonical_reporting_window,
    materialization_boundary,
    regional_claim_boundary,
    seasonal_peak,
)


def scn_record(start, end, power):
    return ObservedLoadRecord(
        source_series_id="SCN",
        timestamp_utc=start,
        interval_end_utc=end,
        timestep_hours=(end - start).total_seconds() / 3600.0,
        power_mw=power,
        region_id=HUNGARY_CONTROL_AREA,
        region_scheme=CONTROL_AREA_SCHEME,
        source_time_basis="UTC",
        interval_convention="INTERVAL_START",
        truth_context="SCN",
        evidence_status="SCN",
        source_refs=("SRC-B08-SCN-GRID-FIXTURE",),
    )


class B08P3SeasonalReportingContractTests(unittest.TestCase):
    def test_calendar_year_uses_budapest_local_boundary(self):
        window = canonical_reporting_window(
            ReportingWindowKind.CALENDAR_YEAR,
            2026,
        )
        self.assertEqual(window.local_start.isoformat(), "2026-01-01T00:00:00+01:00")
        self.assertEqual(window.local_end.isoformat(), "2027-01-01T00:00:00+01:00")
        self.assertEqual(window.utc_start.isoformat(), "2025-12-31T23:00:00+00:00")
        self.assertEqual(window.evidence_status, "POL")

    def test_winter_is_december_to_march_half_open(self):
        window = canonical_reporting_window(
            ReportingWindowKind.METEOROLOGICAL_WINTER,
            2026,
        )
        self.assertEqual(window.local_start.isoformat(), "2025-12-01T00:00:00+01:00")
        self.assertEqual(window.local_end.isoformat(), "2026-03-01T00:00:00+01:00")

    def test_complete_window_peak_keeps_ties(self):
        window = canonical_reporting_window(
            ReportingWindowKind.METEOROLOGICAL_WINTER,
            2026,
        )
        start = window.utc_start
        # Use two records that deliberately span the whole window.
        midpoint = start + (window.utc_end - start) / 2
        records = (
            scn_record(start, midpoint, 100.0),
            scn_record(midpoint, window.utc_end, 100.0),
        )
        result = seasonal_peak(records, window)
        self.assertEqual(result.peak_mw, 100.0)
        self.assertEqual(len(result.tied_timestamps_utc), 2)
        self.assertEqual(result.evidence_status, "SCN")

    def test_gap_fails_closed(self):
        window = canonical_reporting_window(
            ReportingWindowKind.METEOROLOGICAL_WINTER,
            2026,
        )
        start = window.utc_start
        midpoint = start + (window.utc_end - start) / 2
        records = (
            scn_record(start, midpoint, 100.0),
            scn_record(midpoint + timedelta(hours=1), window.utc_end, 90.0),
        )
        with self.assertRaisesRegex(ValueError, "gap or overlap"):
            seasonal_peak(records, window)

    def test_regional_mapping_not_required_for_national_baseline(self):
        result = assess_national_baseline(
            source_is_hungarian_control_area=True,
            numeric_panel_available=True,
            model_use_authorized=True,
            provenance_complete=True,
            regional_mapping_available=False,
        )
        self.assertEqual(result.status, "QUALIFIED_NATIONAL_CONTROL_AREA_BASELINE")
        self.assertEqual(result.blockers, ())
        self.assertIn(
            "REGIONAL_DSO_COUNTY_CLAIMS_REMAIN_SEPARATE_Q",
            result.warnings,
        )

    def test_current_numeric_baseline_can_remain_q_independently_of_region(self):
        result = assess_national_baseline(
            source_is_hungarian_control_area=True,
            numeric_panel_available=False,
            model_use_authorized=False,
            provenance_complete=False,
            regional_mapping_available=False,
        )
        self.assertEqual(result.status, "Q_NATIONAL_NUMERIC_BASELINE")
        self.assertIn("REAL_NUMERIC_LOAD_PANEL_REQUIRED", result.blockers)
        self.assertNotIn("REGIONAL_DSO_COUNTY_CLAIMS_REMAIN_SEPARATE_Q", result.blockers)

    def test_boundaries_preserve_regional_and_permission_gates(self):
        self.assertIn(
            "NATIONAL_CONTROL_AREA_SERIES_CANNOT_BE_DOWNSCALED_TO_DSO_OR_COUNTY_WITHOUT_AUTHORITY",
            regional_claim_boundary(),
        )
        self.assertIn(
            "PUBLIC_REPOSITORY_RAW_SNAPSHOT_REQUIRES_REUSE_PERMISSION",
            materialization_boundary(),
        )


if __name__ == "__main__":
    unittest.main()
