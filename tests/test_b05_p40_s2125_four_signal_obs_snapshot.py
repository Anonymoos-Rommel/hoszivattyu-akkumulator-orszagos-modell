import csv
import unittest
from pathlib import Path

from modules.B05.s2125_four_signal_snapshot_contract import (
    SNAPSHOT_ADMITTED,
    FourSignalSnapshotEvidence,
    p40_boundary,
    qualify_four_signal_snapshot,
    weather_bt16_model_admissible,
)


ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p40_s2125_four_signal_obs_snapshot.csv"
INVENTORY = ROOT / "data" / "processed" / "b05_p40_s2125_four_signal_obs_snapshot.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P40_S2125_FOUR_SIGNAL_OBS_SNAPSHOT.md"
README = ROOT / "modules" / "B05" / "README.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def exact_snapshot():
    return FourSignalSnapshotEvidence(
        exact_s2125_system=True,
        single_machine_readable_response=True,
        source_timestamp_present=True,
        bt28_raw_present=True,
        bt16_raw_present=True,
        compressor_raw_present=True,
        direct_defrost_raw_present=True,
        scaling_units_present=True,
        direct_defrost_value=0,
    )


class B05P40S2125FourSignalObsSnapshotTests(unittest.TestCase):
    def test_exact_snapshot_is_obs_but_not_timeseries(self):
        result = qualify_four_signal_snapshot(exact_snapshot())
        self.assertTrue(result.admitted)
        self.assertEqual(result.status, SNAPSHOT_ADMITTED)
        self.assertEqual(result.evidence_status, "OBS")
        self.assertFalse(result.event_observed)
        self.assertFalse(result.timeseries_admitted)

    def test_missing_signal_blocks_snapshot(self):
        evidence = FourSignalSnapshotEvidence(
            exact_s2125_system=True,
            single_machine_readable_response=True,
            source_timestamp_present=True,
            bt28_raw_present=True,
            bt16_raw_present=False,
            compressor_raw_present=True,
            direct_defrost_raw_present=True,
            scaling_units_present=True,
            direct_defrost_value=0,
        )
        self.assertFalse(qualify_four_signal_snapshot(evidence).admitted)

    def test_single_snapshot_cannot_admit_weather_model(self):
        result = qualify_four_signal_snapshot(exact_snapshot())
        self.assertFalse(
            weather_bt16_model_admissible(
                snapshot=result,
                multi_timestamp_series_acquired=False,
                validation_holdout_defined=True,
            )
        )

    def test_inventory_pins_exact_four_values(self):
        inv = {row["channel"]: row for row in rows(INVENTORY)}
        self.assertEqual(inv["EB101-BT28 outdoor temperature"]["modbus_id"], "1621")
        self.assertEqual(inv["EB101-BT28 outdoor temperature"]["raw_value"], "83")
        self.assertEqual(inv["EB101-BT16 evaporator"]["modbus_id"], "1622")
        self.assertEqual(inv["EB101-BT16 evaporator"]["raw_value"], "49")
        self.assertEqual(inv["EB101 current compressor frequency"]["modbus_id"], "1803")
        self.assertEqual(inv["EB101 current compressor frequency"]["raw_value"], "200")
        self.assertEqual(inv["EB101 direct Defrost"]["modbus_id"], "1805")
        self.assertEqual(inv["EB101 direct Defrost"]["raw_value"], "0")

    def test_source_timestamp_timezone_not_invented(self):
        for row in rows(INVENTORY):
            self.assertEqual(row["source_timestamp_source_native"], "2026-05-13 20:36:13")
            self.assertEqual(row["timezone_status"], "UNSPECIFIED")

    def test_registry_keeps_timeseries_open(self):
        reg = {row["claim"]: row for row in rows(REG)}
        snap = reg["S2125_FOUR_SIGNAL_SAME_RESPONSE_SNAPSHOT_ACQUIRED"]
        self.assertEqual(snap["status"], "RESOLVED_BOUNDED")
        self.assertEqual(snap["evidence_status"], "OBS")
        ts = reg["S2125_MULTI_TIMESTAMP_BT28_BT16_COMPRESSOR_DEFROST_SERIES_REQUIRED"]
        self.assertEqual(ts["status"], "OPEN")
        self.assertEqual(ts["evidence_status"], "Q")

    def test_weather_mapping_stays_q_and_snapshot_is_obs(self):
        variables = {row["variable_id"]: row for row in rows(VARIABLES)}
        self.assertEqual(
            variables["VAR-B05-WEATHER-TO-NIBE-BT16-MAPPING"]["status"], "Q"
        )
        self.assertEqual(
            variables["VAR-B05-S2125-FOUR-SIGNAL-OBS-SNAPSHOT"]["status"], "OBS"
        )

    def test_question_uses_multi_timestamp_residual(self):
        q = {row["question_id"]: row for row in rows(QUESTIONS)}["Q-B05-003"]
        self.assertIn(
            "OPEN_NARROWED_TO_COMPLETE_RAW_EVENT_PACKAGE_MULTI_TIMESTAMP_BT16_SERIES_AND_CROSS_PRODUCT",
            q["notes"],
        )
        self.assertIn(
            "S2125_MULTI_TIMESTAMP_BT28_BT16_COMPRESSOR_DEFROST_SERIES_REQUIRED",
            q["notes"],
        )

    def test_readiness_does_not_increase_for_one_snapshot(self):
        r = {row["component_id"]: row for row in rows(READINESS)}["DEFROST"]
        self.assertEqual(r["readiness_percent"], "20")
        self.assertIn("B05 overall remains 64%", r["notes"])

    def test_sources_are_registered(self):
        sources = {row["source_id"]: row for row in rows(SOURCES)}
        for source_id in (
            "SRC-B05-P40-SVENPAUSH-S2125-SYSTEM-IDENTITY-2026",
            "SRC-B05-P40-SVENPAUSH-S2125-REST-SNAPSHOT-FCE467-2026",
            "SRC-B05-P40-NIBEAPI-INFLUX-SEMANTICS-FCE467-2026",
        ):
            self.assertIn(source_id, sources)

    def test_raw_third_party_json_is_not_copied(self):
        self.assertFalse((ROOT / "data" / "raw" / "2026-5-13 20-36-13_device0_vvms320_S2125.json").exists())
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("not copied", text)
        self.assertIn("1d673572dbaeb399f8a701971da70dfe65e75315", text)

    def test_readme_and_boundary_are_pinned(self):
        self.assertIn("B05-P40", README.read_text(encoding="utf-8"))
        boundary = p40_boundary()
        self.assertIn(
            "FOUR_SIGNAL_SAME_SYSTEM_OBS_SNAPSHOT_ACQUIRED != RAW_TIMESERIES_ACQUIRED",
            boundary,
        )
        self.assertIn("THIRD_PARTY_RAW_JSON_NOT_COMMITTED", boundary)


if __name__ == "__main__":
    unittest.main()
