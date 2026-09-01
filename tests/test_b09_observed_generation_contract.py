from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import unittest

from modules.B09.observed_generation_contract import (
    EXTERNAL_ONLY_REUSE_UNRESOLVED,
    GenerationSourceProvenance,
    ObservedGenerationContractError,
    REUSE_CLEARED,
    parse_entsoe_actual_generation_per_type,
    to_b09_supply_records,
)


BASE_REQUEST_URL = (
    "https://web-api.tp.entsoe.eu/api?documentType=A75&processType=A16"
    "&in_Domain=10YHU-MAVIR----U&periodStart=202601010000&periodEnd=202601010030"
)

PROVENANCE = GenerationSourceProvenance(
    source_id="SRC-B09-ENTSOE-ACTUAL-GENERATION-TYPE-2026",
    publisher="ENTSO-E",
    dataset_name="Actual Generation per Production Type [16.1.B&C]",
    request_url=BASE_REQUEST_URL,
    retrieved_at=datetime(2026, 9, 1, 13, 0, tzinfo=timezone.utc),
    license_decision=EXTERNAL_ONLY_REUSE_UNRESOLVED,
    raw_storage_policy="EXTERNAL_ONLY",
    source_revision="NOT_PROVIDED_BY_SOURCE",
)


def series(*, series_id="GEN-B16", business="A01", psr="B16", in_domain=True, out_domain=False,
           resolution="PT15M", quantities=(100.0, 101.0), measure_unit="MAW", object_aggregation="A08"):
    duration_minutes = {"PT15M": 15, "PT30M": 30, "PT60M": 60}[resolution] * len(quantities)
    hour, minute = divmod(duration_minutes, 60)
    points = "".join(
        f"<Point><position>{index}</position><quantity>{value}</quantity></Point>"
        for index, value in enumerate(quantities, start=1)
    )
    domains = ""
    if in_domain:
        domains += "<inBiddingZone_Domain.mRID>10YHU-MAVIR----U</inBiddingZone_Domain.mRID>"
    if out_domain:
        domains += "<outBiddingZone_Domain.mRID>10YHU-MAVIR----U</outBiddingZone_Domain.mRID>"
    return f"""
      <TimeSeries>
        <mRID>{series_id}</mRID>
        <businessType>{business}</businessType>
        {domains}
        <objectAggregation>{object_aggregation}</objectAggregation>
        <measurement_Unit.name>{measure_unit}</measurement_Unit.name>
        <MktPSRType><psrType>{psr}</psrType></MktPSRType>
        <Period><timeInterval><start>2026-01-01T00:00Z</start><end>2026-01-01T{hour:02d}:{minute:02d}Z</end></timeInterval>
          <resolution>{resolution}</resolution>{points}
        </Period>
      </TimeSeries>
    """


def payload(*series_xml):
    body = "".join(series_xml or (series(),))
    return f"""<GL_MarketDocument xmlns=\"urn:entsoe.eu:wgedi:gl:marketdocument:7:0\">
      <documentType>A75</documentType><process.processType>A16</process.processType>{body}
    </GL_MarketDocument>"""


def cleared(xml_text, *, request_url=BASE_REQUEST_URL):
    return replace(
        PROVENANCE,
        request_url=request_url,
        license_decision=REUSE_CLEARED,
        source_sha256=hashlib.sha256(xml_text.encode("utf-8")).hexdigest(),
    )


class B09ObservedGenerationContractTests(unittest.TestCase):
    def test_source_native_a75_generation_stays_control_area_and_obs_when_cleared(self):
        xml = payload(series(psr="B16", quantities=(100.0, 0.0)))
        batch = parse_entsoe_actual_generation_per_type(xml, provenance=cleared(xml))
        self.assertEqual(len(batch.records), 2)
        self.assertTrue(all(row.region_id == "HUNGARY_CONTROL_AREA" for row in batch.records))
        self.assertTrue(all(row.region_scheme == "ENTSOE_CONTROL_AREA" for row in batch.records))
        self.assertTrue(all(row.evidence_status == "OBS" for row in batch.records))
        self.assertEqual(batch.records[0].power_mw, 100.0)
        self.assertEqual(batch.records[1].power_mw, 0.0)

    def test_unresolved_reuse_with_numeric_payload_remains_q(self):
        batch = parse_entsoe_actual_generation_per_type(payload(), provenance=PROVENANCE)
        self.assertTrue(all(row.evidence_status == "Q" for row in batch.records))

    def test_matching_hash_does_not_clear_unresolved_reuse(self):
        xml = payload()
        provenance = replace(PROVENANCE, source_sha256=hashlib.sha256(xml.encode("utf-8")).hexdigest())
        batch = parse_entsoe_actual_generation_per_type(xml, provenance=provenance)
        self.assertTrue(all(row.evidence_status == "Q" for row in batch.records))

    def test_checksum_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ObservedGenerationContractError, "exact UTF-8 payload"):
            parse_entsoe_actual_generation_per_type(payload(), provenance=replace(PROVENANCE, source_sha256="0" * 64))

    def test_missing_quantity_is_q_and_blocks_supply_handoff(self):
        xml = payload(series(quantities=(100.0, "")))
        batch = parse_entsoe_actual_generation_per_type(xml, provenance=cleared(xml))
        self.assertEqual(batch.records[1].evidence_status, "Q")
        self.assertIsNone(batch.records[1].power_mw)
        with self.assertRaisesRegex(ObservedGenerationContractError, "missing generation quantity"):
            to_b09_supply_records(batch, expected_production_types=("B16",))

    def test_consumption_direction_is_excluded_not_negated(self):
        xml = payload(
            series(series_id="PROD", psr="B12", in_domain=True, out_domain=False),
            series(series_id="CONS", psr="B12", in_domain=False, out_domain=True),
        )
        batch = parse_entsoe_actual_generation_per_type(xml, provenance=cleared(xml))
        self.assertEqual(batch.excluded_consumption_series_count, 1)
        self.assertTrue(all(row.source_series_id == "PROD" for row in batch.records))

    def test_generation_series_cannot_carry_both_directions(self):
        with self.assertRaises(ObservedGenerationContractError):
            parse_entsoe_actual_generation_per_type(payload(series(in_domain=True, out_domain=True)), provenance=PROVENANCE)

    def test_wind_and_solar_business_types_are_accepted_as_production(self):
        xml = payload(
            series(series_id="WIND", business="A93", psr="B19"),
            series(series_id="SOLAR", business="A94", psr="B16"),
        )
        batch = parse_entsoe_actual_generation_per_type(xml, provenance=cleared(xml))
        self.assertEqual({row.business_type for row in batch.records}, {"A93", "A94"})

    def test_wrong_request_semantics_are_rejected(self):
        replacements = (
            ("documentType=A75", "documentType=A65"),
            ("processType=A16", "processType=A01"),
            ("in_Domain=10YHU-MAVIR----U", "in_Domain=10YDE-TEST"),
        )
        for old, new in replacements:
            with self.subTest(new=new):
                with self.assertRaises(ObservedGenerationContractError):
                    replace(PROVENANCE, request_url=BASE_REQUEST_URL.replace(old, new))

    def test_reordered_query_is_accepted_and_duplicate_required_query_is_rejected(self):
        reordered = (
            "https://web-api.tp.entsoe.eu/api?periodEnd=202601010030&in_Domain=10YHU-MAVIR----U"
            "&processType=A16&periodStart=202601010000&documentType=A75"
        )
        replace(PROVENANCE, request_url=reordered)
        duplicate = BASE_REQUEST_URL + "&documentType=A75"
        with self.assertRaises(ObservedGenerationContractError):
            replace(PROVENANCE, request_url=duplicate)

    def test_payload_period_must_fit_request_window(self):
        short_request = BASE_REQUEST_URL.replace("periodEnd=202601010030", "periodEnd=202601010015")
        xml = payload()
        with self.assertRaisesRegex(ObservedGenerationContractError, "outside the canonical request window"):
            parse_entsoe_actual_generation_per_type(xml, provenance=replace(PROVENANCE, request_url=short_request))

    def test_wrong_resolution_unit_aggregation_or_area_is_rejected(self):
        cases = (
            payload(series(resolution="PT15M")).replace("PT15M", "PT05M", 1),
            payload(series(measure_unit="MWH")),
            payload(series(object_aggregation="A01")),
            payload(series()).replace("10YHU-MAVIR----U", "10YDE-TEST", 1),
        )
        for xml in cases:
            with self.subTest(xml=xml[:80]):
                with self.assertRaises(ObservedGenerationContractError):
                    parse_entsoe_actual_generation_per_type(xml, provenance=PROVENANCE)

    def test_duplicate_production_type_timestamp_fails_closed(self):
        xml = payload(series(series_id="A", psr="B16"), series(series_id="B", psr="B16"))
        with self.assertRaisesRegex(ObservedGenerationContractError, "duplicate production-type/timestamp"):
            parse_entsoe_actual_generation_per_type(xml, provenance=cleared(xml))

    def test_supply_handoff_requires_explicit_complete_production_type_manifest(self):
        xml = payload(series(series_id="NUCLEAR", psr="B14"), series(series_id="SOLAR", psr="B16"))
        batch = parse_entsoe_actual_generation_per_type(xml, provenance=cleared(xml))
        with self.assertRaisesRegex(ObservedGenerationContractError, "production types"):
            to_b09_supply_records(batch, expected_production_types=("B14",))

    def test_complete_obs_panel_converts_mw_to_kw_as_der(self):
        xml = payload(series(series_id="NUCLEAR", psr="B14"), series(series_id="SOLAR", psr="B16"))
        batch = parse_entsoe_actual_generation_per_type(xml, provenance=cleared(xml))
        rows = to_b09_supply_records(batch, expected_production_types=("B14", "B16"))
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row.truth_context == "REAL" for row in rows))
        self.assertTrue(all(row.evidence_status == "DER" for row in rows))
        self.assertEqual(rows[0].delivered_generation_kw, batch.records[0].power_mw * 1000.0)

    def test_q_source_rows_never_become_obs_or_der_handoff(self):
        batch = parse_entsoe_actual_generation_per_type(payload(), provenance=PROVENANCE)
        rows = to_b09_supply_records(batch, expected_production_types=("B16",))
        self.assertTrue(all(row.evidence_status == "Q" for row in rows))


if __name__ == "__main__":
    unittest.main()
