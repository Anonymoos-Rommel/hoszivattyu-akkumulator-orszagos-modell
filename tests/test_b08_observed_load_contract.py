from datetime import datetime, timezone
from dataclasses import replace
import hashlib
import unittest

from modules.B08.observed_load_contract import (
    CONTROL_AREA_SCHEME,
    EXTERNAL_ONLY_REUSE_UNRESOLVED,
    HUNGARY_CONTROL_AREA,
    ObservedLoadContractError,
    ObservedLoadRecord,
    REUSE_CLEARED,
    REUSE_RESTRICTED,
    REUSE_UNKNOWN,
    SourceProvenance,
    derive_energy_mwh,
    parse_entsoe_actual_total_load,
    validate_record_panel,
)


BASE_REQUEST_URL = (
    "https://web-api.tp.entsoe.eu/api?documentType=A65&processType=A16&businessType=A04"
    "&outBiddingZone_Domain=10YHU-MAVIR----U&periodStart=202601010000&periodEnd=202601010030"
)

PROVENANCE = SourceProvenance(
    source_id="SRC-B08-ENTSOE-ACTUAL-TOTAL-LOAD-2026",
    publisher="ENTSO-E",
    dataset_name="Actual Total Load [6.1.A]",
    request_url=BASE_REQUEST_URL,
    retrieved_at=datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc),
    license_decision=EXTERNAL_ONLY_REUSE_UNRESOLVED,
    raw_storage_policy="EXTERNAL_ONLY",
    source_revision="NOT_PROVIDED_BY_SOURCE",
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


def cleared_provenance(xml_text: str, *, request_url: str = BASE_REQUEST_URL) -> SourceProvenance:
    return replace(
        PROVENANCE,
        request_url=request_url,
        license_decision=REUSE_CLEARED,
        source_sha256=hashlib.sha256(xml_text.encode("utf-8")).hexdigest(),
    )


def direct_record(*, provenance: SourceProvenance, evidence_status: str = "OBS") -> ObservedLoadRecord:
    return ObservedLoadRecord(
        source_series_id="HU-TEST-SERIES",
        timestamp_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
        interval_end_utc=datetime(2026, 1, 1, 0, 15, tzinfo=timezone.utc),
        timestep_hours=0.25,
        power_mw=1.0,
        region_id=HUNGARY_CONTROL_AREA,
        region_scheme=CONTROL_AREA_SCHEME,
        source_time_basis="UTC",
        interval_convention="INTERVAL_START",
        truth_context="REAL",
        evidence_status=evidence_status,
        source_refs=(provenance.source_id,),
        source_revision=provenance.source_revision,
        provenance=provenance,
    )


class ObservedLoadContractTests(unittest.TestCase):
    def test_entsoe_actual_load_is_control_area_and_keeps_15min_power(self):
        xml = payload()
        rows = parse_entsoe_actual_total_load(xml, provenance=cleared_provenance(xml))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].region_id, HUNGARY_CONTROL_AREA)
        self.assertEqual(rows[0].region_scheme, CONTROL_AREA_SCHEME)
        self.assertEqual(rows[0].timestep_hours, 0.25)
        self.assertEqual(rows[0].power_mw, 100.0)
        self.assertEqual(rows[0].evidence_status, "OBS")
        self.assertEqual(rows[0].provenance.license_decision, REUSE_CLEARED)
        self.assertEqual(derive_energy_mwh(rows), (25.0, 0.0))

    def test_source_native_30_and_60_minute_resolution_is_preserved(self):
        half_hour = parse_entsoe_actual_total_load(
            payload(resolution="PT30M", quantities=(10.0,)),
            provenance=replace(PROVENANCE, request_url=BASE_REQUEST_URL.replace("periodEnd=202601010030", "periodEnd=202601010100")),
        )[0]
        hourly = parse_entsoe_actual_total_load(
            payload(resolution="PT60M", quantities=(10.0,)),
            provenance=replace(PROVENANCE, request_url=BASE_REQUEST_URL.replace("periodEnd=202601010030", "periodEnd=202601010100")),
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

    def test_matching_checksum_does_not_clear_unresolved_reuse(self):
        xml = payload()
        provenance = replace(PROVENANCE, source_sha256=hashlib.sha256(xml.encode("utf-8")).hexdigest())
        rows = parse_entsoe_actual_total_load(xml, provenance=provenance)
        self.assertTrue(all(row.evidence_status == "Q" for row in rows))

    def test_restricted_and_unknown_reuse_never_become_obs(self):
        xml = payload()
        checksum = hashlib.sha256(xml.encode("utf-8")).hexdigest()
        for decision in (REUSE_RESTRICTED, REUSE_UNKNOWN):
            with self.subTest(decision=decision):
                rows = parse_entsoe_actual_total_load(
                    xml,
                    provenance=replace(PROVENANCE, license_decision=decision, source_sha256=checksum),
                )
                self.assertTrue(all(row.evidence_status == "Q" for row in rows))

    def test_raw_storage_policy_alone_does_not_clear_reuse(self):
        xml = payload()
        checksum = hashlib.sha256(xml.encode("utf-8")).hexdigest()
        rows = parse_entsoe_actual_total_load(
            xml,
            provenance=replace(PROVENANCE, source_sha256=checksum, raw_storage_policy="REPOSITORY_ALLOWED"),
        )
        self.assertTrue(all(row.evidence_status == "Q" for row in rows))

    def test_checksum_mismatch_is_fail_closed(self):
        with self.assertRaisesRegex(ObservedLoadContractError, "exact UTF-8 payload"):
            parse_entsoe_actual_total_load(
                payload(),
                provenance=replace(PROVENANCE, license_decision=REUSE_CLEARED, source_sha256="0" * 64),
            )

    def test_one_character_payload_change_is_rejected_against_declared_hash(self):
        original = payload()
        provenance = cleared_provenance(original)
        changed = original.replace("100.0", "100.1", 1)
        with self.assertRaises(ObservedLoadContractError):
            parse_entsoe_actual_total_load(changed, provenance=provenance)

    def test_explicit_zero_is_obs_when_all_gates_pass(self):
        xml = payload(quantities=(0.0,))
        row = parse_entsoe_actual_total_load(xml, provenance=cleared_provenance(xml))[0]
        self.assertEqual(row.power_mw, 0.0)
        self.assertEqual(row.evidence_status, "OBS")

    def test_naive_retrieval_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ObservedLoadContractError, "timezone-aware"):
            SourceProvenance(**{**PROVENANCE.__dict__, "retrieved_at": datetime(2026, 9, 1, 12, 0)})

    def test_retrieval_timestamp_is_normalized_to_utc(self):
        provenance = replace(PROVENANCE, retrieved_at=datetime(2026, 9, 1, 14, 0, tzinfo=timezone.utc))
        self.assertEqual(provenance.retrieved_at, datetime(2026, 9, 1, 14, 0, tzinfo=timezone.utc))

    def test_missing_required_provenance_is_rejected(self):
        with self.assertRaises(ObservedLoadContractError):
            SourceProvenance(**{**PROVENANCE.__dict__, "publisher": ""})

    def test_exact_request_query_is_required_for_runtime_provenance(self):
        with self.assertRaises(ObservedLoadContractError):
            SourceProvenance(**{**PROVENANCE.__dict__, "request_url": "https://web-api.tp.entsoe.eu/api"})

    def test_request_query_parameter_order_does_not_matter(self):
        reordered = (
            "https://web-api.tp.entsoe.eu/api?periodEnd=202601010030&businessType=A04"
            "&outBiddingZone_Domain=10YHU-MAVIR----U&documentType=A65&periodStart=202601010000&processType=A16"
        )
        provenance = replace(PROVENANCE, request_url=reordered)
        self.assertEqual(provenance.request_url, reordered)

    def test_wrong_required_request_values_are_rejected(self):
        replacements = {
            "documentType=A65": "documentType=A01",
            "processType=A16": "processType=A01",
            "businessType=A04": "businessType=A01",
            "outBiddingZone_Domain=10YHU-MAVIR----U": "outBiddingZone_Domain=10YDE-TEST",
        }
        for old, new in replacements.items():
            with self.subTest(field=old):
                with self.assertRaises(ObservedLoadContractError):
                    replace(PROVENANCE, request_url=BASE_REQUEST_URL.replace(old, new))

    def test_missing_request_period_fields_are_rejected(self):
        for fragment in ("&periodStart=202601010000", "&periodEnd=202601010030"):
            with self.subTest(fragment=fragment):
                with self.assertRaises(ObservedLoadContractError):
                    replace(PROVENANCE, request_url=BASE_REQUEST_URL.replace(fragment, ""))

    def test_duplicate_required_request_parameter_is_rejected(self):
        with self.assertRaises(ObservedLoadContractError):
            replace(PROVENANCE, request_url=BASE_REQUEST_URL + "&documentType=A01")

    def test_payload_period_must_be_covered_by_request_window(self):
        xml = payload()
        too_short = BASE_REQUEST_URL.replace("periodEnd=202601010030", "periodEnd=202601010015")
        provenance = replace(PROVENANCE, request_url=too_short)
        with self.assertRaisesRegex(ObservedLoadContractError, "request window"):
            parse_entsoe_actual_total_load(xml, provenance=provenance)

    def test_unsupported_resolution_is_rejected(self):
        with self.assertRaises(ObservedLoadContractError):
            parse_entsoe_actual_total_load(payload().replace("PT15M", "PT05M"), provenance=PROVENANCE)

    def test_wrong_business_type_is_rejected(self):
        with self.assertRaises(ObservedLoadContractError):
            parse_entsoe_actual_total_load(
                payload().replace("<businessType>A04</businessType>", "<businessType>A01</businessType>"),
                provenance=PROVENANCE,
            )

    def test_timezone_aware_source_time_and_dst_offsets_are_deterministic(self):
        request = BASE_REQUEST_URL.replace("periodStart=202601010000&periodEnd=202601010030", "periodStart=202610250000&periodEnd=202610250200")
        provenance = replace(PROVENANCE, request_url=request)
        xml = payload().replace("2026-01-01T00:00Z", "2026-10-25T02:00+02:00").replace("2026-01-01T00:30Z", "2026-10-25T02:30+02:00")
        first = parse_entsoe_actual_total_load(xml, provenance=provenance)[0]
        xml_late = payload().replace("2026-01-01T00:00Z", "2026-10-25T02:00+01:00").replace("2026-01-01T00:30Z", "2026-10-25T02:30+01:00")
        second = parse_entsoe_actual_total_load(xml_late, provenance=provenance)[0]
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

    def test_invalid_reuse_decision_is_rejected(self):
        with self.assertRaises(ObservedLoadContractError):
            SourceProvenance(**{**PROVENANCE.__dict__, "license_decision": "PUBLIC"})

    def test_direct_obs_with_unresolved_provenance_is_rejected(self):
        with self.assertRaisesRegex(ObservedLoadContractError, "canonical verified parser path"):
            direct_record(provenance=PROVENANCE)

    def test_direct_obs_with_cleared_reuse_but_missing_hash_is_rejected(self):
        with self.assertRaises(ObservedLoadContractError):
            direct_record(provenance=replace(PROVENANCE, license_decision=REUSE_CLEARED))

    def test_direct_obs_with_apparently_complete_provenance_is_still_rejected(self):
        xml = payload()
        with self.assertRaisesRegex(ObservedLoadContractError, "canonical verified parser path"):
            direct_record(provenance=cleared_provenance(xml))

    def test_direct_q_with_unresolved_provenance_remains_allowed(self):
        row = direct_record(provenance=PROVENANCE, evidence_status="Q")
        self.assertEqual(row.evidence_status, "Q")

    def test_non_hungarian_or_dso_relabel_rejected(self):
        with self.assertRaises(ObservedLoadContractError):
            parse_entsoe_actual_total_load(payload().replace("10YHU-MAVIR----U", "10YDE-TEST"), provenance=PROVENANCE)

    def test_scn_fixture_context_stays_scn(self):
        rows = parse_entsoe_actual_total_load(payload(), provenance=PROVENANCE, truth_context="SCN")
        self.assertTrue(all(row.truth_context == row.evidence_status == "SCN" for row in rows))


if __name__ == "__main__":
    unittest.main()
