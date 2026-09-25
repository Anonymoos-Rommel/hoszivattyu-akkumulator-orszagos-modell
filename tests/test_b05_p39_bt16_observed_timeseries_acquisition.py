import csv
import unittest
from pathlib import Path

from modules.B05.bt16_observed_timeseries_contract import (
    DIRECT_MODBUS,
    GRAPH_ONLY,
    RAW_INFLUX,
    RAW_SERIES_ADMITTED,
    ROUTE_QUALIFIED,
    USB_RAW_LOG,
    Bt16AcquisitionEvidence,
    p39_boundary,
    qualify_bt16_acquisition,
    weather_to_bt16_model_admissible,
)


ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p39_bt16_observed_timeseries_acquisition.csv"
INVENTORY = ROOT / "data" / "processed" / "b05_p39_bt16_acquisition_route_inventory.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P39_BT16_OBSERVED_TIMESERIES_ACQUISITION.md"
README = ROOT / "modules" / "B05" / "README.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def complete(kind=DIRECT_MODBUS):
    return Bt16AcquisitionEvidence(
        source_kind=kind,
        exact_s2125_system=True,
        timestamped_bt28=True,
        timestamped_bt16=True,
        compressor_state_or_frequency=True,
        direct_defrost_0_1_2=True,
        common_timebase=True,
        source_native_cadence_known=True,
        scaling_units_known=True,
        unknown_aggregation=False,
        machine_readable_rows=True,
    )


class B05P39Bt16ObservedTimeseriesAcquisitionTests(unittest.TestCase):
    def test_direct_modbus_complete_series_is_admissible(self):
        result = qualify_bt16_acquisition(complete(DIRECT_MODBUS))
        self.assertTrue(result.admitted)
        self.assertTrue(result.route_qualified)
        self.assertEqual(result.status, RAW_SERIES_ADMITTED)
        self.assertEqual(result.evidence_status, "OBS")

    def test_usb_and_raw_influx_are_allowed_routes(self):
        for kind in (USB_RAW_LOG, RAW_INFLUX):
            result = qualify_bt16_acquisition(complete(kind))
            self.assertTrue(result.admitted, kind)

    def test_graph_only_evidence_is_forbidden_as_raw_bt16(self):
        evidence = complete(GRAPH_ONLY)
        result = qualify_bt16_acquisition(evidence)
        self.assertFalse(result.admitted)
        self.assertFalse(result.route_qualified)

    def test_unknown_aggregation_blocks_route(self):
        evidence = Bt16AcquisitionEvidence(
            source_kind=RAW_INFLUX,
            exact_s2125_system=True,
            timestamped_bt28=True,
            timestamped_bt16=True,
            compressor_state_or_frequency=True,
            direct_defrost_0_1_2=True,
            common_timebase=True,
            source_native_cadence_known=True,
            scaling_units_known=True,
            unknown_aggregation=True,
            machine_readable_rows=True,
        )
        result = qualify_bt16_acquisition(evidence)
        self.assertFalse(result.admitted)
        self.assertFalse(result.route_qualified)

    def test_qualified_route_without_rows_does_not_close_residual(self):
        evidence = Bt16AcquisitionEvidence(
            source_kind=USB_RAW_LOG,
            exact_s2125_system=True,
            timestamped_bt28=False,
            timestamped_bt16=False,
            compressor_state_or_frequency=False,
            direct_defrost_0_1_2=False,
            common_timebase=False,
            source_native_cadence_known=True,
            scaling_units_known=True,
            unknown_aggregation=False,
            machine_readable_rows=False,
        )
        result = qualify_bt16_acquisition(evidence)
        self.assertFalse(result.admitted)
        self.assertTrue(result.route_qualified)
        self.assertEqual(result.status, ROUTE_QUALIFIED)

    def test_weather_model_requires_observed_series_and_holdout(self):
        admitted = qualify_bt16_acquisition(complete())
        self.assertFalse(
            weather_to_bt16_model_admissible(
                observed_series=admitted,
                weather_covariates_joined=True,
                validation_holdout_defined=False,
            )
        )
        self.assertTrue(
            weather_to_bt16_model_admissible(
                observed_series=admitted,
                weather_covariates_joined=True,
                validation_holdout_defined=True,
            )
        )

    def test_inventory_preserves_public_emoncms_negative_result(self):
        inv = {row["record_id"]: row for row in rows(INVENTORY)}
        self.assertEqual(inv["B05-P39-E02"]["bt16"], "NO")
        self.assertIn("outside_temperature", inv["B05-P39-E02"]["notes"])
        self.assertEqual(inv["B05-P39-E03"]["direct_defrost"], "NO")

    def test_registry_narrows_weather_bt16_residual(self):
        reg = {row["claim"]: row for row in rows(REG)}
        old = reg["WEATHER_TO_NIBE_BT16_OR_OBS_TIMESERIES_REQUIRED"]
        self.assertEqual(
            old["status"],
            "OPEN_NARROWED_TO_RAW_BT28_BT16_COMPRESSOR_DEFROST_SERIES",
        )
        self.assertEqual(
            old["residual_gap"],
            "S2125_RAW_BT28_BT16_COMPRESSOR_DEFROST_TIMESERIES_REQUIRED",
        )
        new = reg["S2125_RAW_BT28_BT16_COMPRESSOR_DEFROST_TIMESERIES_REQUIRED"]
        self.assertEqual(new["status"], "OPEN")
        self.assertEqual(new["evidence_status"], "Q")

    def test_weather_mapping_remains_q_while_route_classification_is_der(self):
        variables = {row["variable_id"]: row for row in rows(VARIABLES)}
        self.assertEqual(
            variables["VAR-B05-WEATHER-TO-NIBE-BT16-MAPPING"]["status"],
            "Q",
        )
        self.assertEqual(
            variables["VAR-B05-S2125-BT16-OBS-ACQUISITION-ROUTE"]["status"],
            "DER",
        )

    def test_question_keeps_three_physical_residual_families(self):
        q = {row["question_id"]: row for row in rows(QUESTIONS)}["Q-B05-003"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn(
            "OPEN_NARROWED_TO_COMPLETE_RAW_EVENT_PACKAGE_RAW_BT16_SERIES_AND_CROSS_PRODUCT",
            q["notes"],
        )
        self.assertIn("S2125_COMPLETE_RAW_DIRECT_EVENT_PACKAGE_REQUIRED", q["notes"])
        self.assertIn(
            "S2125_RAW_BT28_BT16_COMPRESSOR_DEFROST_TIMESERIES_REQUIRED",
            q["notes"],
        )
        self.assertIn("CROSS_PRODUCT_DEFROST_RUNTIME_COVERAGE_REQUIRED", q["notes"])

    def test_readiness_stays_20(self):
        readiness = {row["component_id"]: row for row in rows(READINESS)}["DEFROST"]
        self.assertEqual(readiness["status"], "PARTIAL")
        self.assertEqual(readiness["readiness_percent"], "20")
        self.assertIn("B05 overall remains 64%", readiness["notes"])

    def test_sources_are_registered(self):
        sources = {row["source_id"]: row for row in rows(SOURCES)}
        for source_id in (
            "SRC-B05-P39-PUBLIC-EMONCMS-BT16-PROBE-2026",
            "SRC-B05-S2125-HA-BT16-DEFROST-FIELD-2025",
            "SRC-B05-S2125-SMO-S40-USB-LOGGING-FIELD-2023",
            "SRC-B05-HA-MYUPLINK-S2125-SMO20-SURFACE-2024",
        ):
            self.assertIn(source_id, sources)

    def test_no_credentials_or_third_party_raw_payload_are_committed(self):
        for path in (PACK, INVENTORY, REG):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("readkey=", text)
            self.assertNotIn("apikey=", text)

    def test_docs_readme_and_boundary_are_pinned(self):
        text = PACK.read_text(encoding="utf-8")
        self.assertIn(
            "S2125_RAW_BT28_BT16_COMPRESSOR_DEFROST_TIMESERIES_REQUIRED",
            text,
        )
        self.assertIn("36130996547", text)
        self.assertIn("DEFROST: 20% -> 20%", text)
        self.assertIn("B05-P39", README.read_text(encoding="utf-8"))

        boundary = p39_boundary()
        self.assertIn("AMBIENT_T_RH != BT16_EVAPORATOR_STATE", boundary)
        self.assertIn(
            "DIRECT_MODBUS_OR_USB_OR_RAW_INFLUX = QUALIFIED_ACQUISITION_ROUTE",
            boundary,
        )


if __name__ == "__main__":
    unittest.main()
