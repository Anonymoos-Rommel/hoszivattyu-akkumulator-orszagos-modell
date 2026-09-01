from datetime import date
from dataclasses import replace
import hashlib
import unittest

from modules.B08.observed_load_contract import (
    CONTROL_AREA_SCHEME,
    HUNGARY_CONTROL_AREA,
    ObservedLoadContractError,
    SourceProvenance,
    derive_energy_mwh,
    parse_entsoe_actual_total_load,
    validate_record_panel,
)


PROVENANCE = SourceProvenance(
    source_id="SRC-B08-ENTSOE-ACTUAL-TOTAL-LOAD-2026",
    publisher="ENTSO-E",
    dataset_name="Actual Total Load [6.1.A]",
    request_url="https://web-api.tp.entsoe.eu/api",
    retrieved_at=date(2026, 9, 1),
    license_decision="EXTERNAL_ONLY_REUSE_UNRESOLVED",
    raw_storage_policy="EXTERNAL_ONLY",
)


def payload(*, process="A16", resolution="PT15M", quantities=(100.0, 0.0)):
    duration_minutes = {"PT15M": 15, "PT30M": 30, "PT60M": 60}[resolution] * len(quantities)
    end_hour, end_minute = divmod(duration_minutes, 60)
    points = "".join(
        f"<Point><position>{index}</position><quantity>{value}</quantity></Point>"
        for index, value in enumerate(quantities, start=1)
    )
    return f"""<GL_MarketDocument xmlns=\"urn:entsoe.eu:wgedi:gl:marketdocument:7:0\">
      <documentType>A65</documentType>
      <TimeSeries>
        <mRID>HU-TEST-SERIES</mRID>
        <businessType>A04</businessType><processType>{process}</processType>
        <outBiddingZone_Domain.mRID>10YHU-MAVIR----U</outBiddingZone_Domain.mRID>
        <Period><timeInterval><start>2026-01-01T00:00Z</start><end>2026-01-01T{end_hour:02d}:{end_minute:02d}Z</end></timeInterval>
          <resolution>{resolution}</resolution>{points}
        </Period>
      </TimeSeries>
    </GL_MarketDocument>"""


class ObservedLoadContractTests(unittest.TestCase):
    def test_entsoe_actual_load_is_control_area_and_keeps_15min_power(self):
        provenance = replace(
            PROVENANCE,
            source_sha256=hashlib.sha256(payload().encode("utf-8")).hexdigest(),
        )
        rows = parse_entsoe_actual_total_load(payload(), provenance=provenance)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].region_id, HUNGARY_CONTROL_AREA)
        self.assertEqual(rows[0].region_scheme, CONTROL_AREA_SCHEME)
        self.assertEqual(rows[0].timestep_hours, 0.25)
        self.assertEqual(rows[0].power_mw, 100.0)
        self.assertEqual(rows[0].evidence_status, "OBS")
        self.assertEqual(derive_energy_mwh(rows), (25.0, 0.0))

    def test_source_native_30_and_60_minute_resolution_is_preserved(self):
        half_hour = parse_entsoe_actual_total_load(
            payload(resolution="PT30M", quantities=(10.0,)), provenance=PROVENANCE
        )[0]
        hourly = parse_entsoe_actual_total_load(
            payload(resolution="PT60M", quantities=(10.0,)), provenance=PROVENANCE
        )[0]
        self.assertEqual(half_hour.timestep_hours, 0.5)
        self.assertEqual(hourly.timestep_hours, 1.0)
        self.assertEqual(derive_energy_mwh((half_hour, hourly)), (5.0, 10.0))


    def test_forecast_cannot_become_obs(self):
        with self.assertRaises(ObservedLoadContractError):
            parse_entsoe_actual_total_load(payload(process="A01"), provenance=PROVENANCE)


    def test_missing_is_q_and_not_zero(self):
        xml = payload(quantities=(100.0, ""))
        rows = parse_entsoe_actual_total_load(xml, provenance=PROVENANCE)
        self.assertIsNone(rows[1].power_mw)
        self.assertEqual(rows[1].evidence_status, "Q")
        self.assertIsNone(derive_energy_mwh(rows)[1])

    def test_missing_checksum_keeps_numeric_source_external_as_q(self):
        rows = parse_entsoe_actual_total_load(payload(quantities=(100.0,)), provenance=PROVENANCE)
        self.assertEqual(rows[0].evidence_status, "Q")


    def test_timezone_aware_source_time_and_dst_offsets_are_deterministic(self):
        xml = payload().replace("2026-01-01T00:00Z", "2026-10-25T02:00+02:00").replace("2026-01-01T00:30Z", "2026-10-25T02:30+02:00")
        first = parse_entsoe_actual_total_load(xml, provenance=PROVENANCE)[0]
        xml_late = payload().replace("2026-01-01T00:00Z", "2026-10-25T02:00+01:00").replace("2026-01-01T00:30Z", "2026-10-25T02:30+01:00")
        second = parse_entsoe_actual_total_load(xml_late, provenance=PROVENANCE)[0]
        self.assertNotEqual(first.timestamp_utc, second.timestamp_utc)
        self.assertTrue(first.timestamp_utc.isoformat().endswith("00:00:00+00:00"))
        self.assertTrue(second.timestamp_utc.isoformat().endswith("01:00:00+00:00"))


    def test_naive_source_timestamp_rejected(self):
        with self.assertRaises(ObservedLoadContractError):
            parse_entsoe_actual_total_load(payload().replace("2026-01-01T00:00Z", "2026-01-01T00:00"), provenance=PROVENANCE)


    def test_duplicate_source_key_rejected_and_gaps_are_not_filled(self):
        rows = parse_entsoe_actual_total_load(payload(quantities=(100.0,)), provenance=PROVENANCE)
        validate_record_panel(rows)
        with self.assertRaises(ObservedLoadContractError):
            validate_record_panel(rows + rows)


    def test_malformed_provenance_rejected(self):
        with self.assertRaises(ObservedLoadContractError):
            SourceProvenance(**{**PROVENANCE.__dict__, "source_sha256": "not-a-sha"})


    def test_non_hungarian_or_dso_relabel_rejected(self):
        with self.assertRaises(ObservedLoadContractError):
            parse_entsoe_actual_total_load(payload().replace("10YHU-MAVIR----U", "10YDE-TEST"), provenance=PROVENANCE)


    def test_scn_fixture_context_stays_scn(self):
        rows = parse_entsoe_actual_total_load(payload(), provenance=PROVENANCE, truth_context="SCN")
        self.assertTrue(all(row.truth_context == row.evidence_status == "SCN" for row in rows))


if __name__ == "__main__":
    unittest.main()
