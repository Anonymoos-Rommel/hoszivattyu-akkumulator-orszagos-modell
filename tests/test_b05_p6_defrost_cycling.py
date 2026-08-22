import csv
from datetime import datetime
from pathlib import Path

from modules.B05.engine import HourlyDemand, OperatingConfig, PerformanceMap, PerformancePoint, simulate_hourly


ROOT = Path(__file__).parents[1]


def p6_map() -> PerformanceMap:
    return PerformanceMap(
        "P6-FIXTURE",
        "air_to_water",
        [
            PerformancePoint(-10, 35, 5.0, 2.0, 2.5, 2.0, evidence_status="SCN", source_id="SRC-B05-SYNTHETIC-TEST-GRID"),
            PerformancePoint(0, 35, 6.0, 2.0, 3.0, 2.0, evidence_status="SCN", source_id="SRC-B05-SYNTHETIC-TEST-GRID"),
        ],
    )


def run(load: float, *, humidity: float | None, defrost_status: str = "Q"):
    return simulate_hourly(
        p6_map(),
        [HourlyDemand(datetime(2026, 1, 3), -10, load, 35, relative_humidity_pct=humidity)],
        OperatingConfig(defrost_status=defrost_status),
    )


def registry_rows(filename: str):
    with (ROOT / "registry" / filename).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_steady_operation_has_no_unmodelled_defrost_or_cycling_penalty():
    result = run(4.0, humidity=90.0)
    hour = result.hourly[0]
    assert hour.operating_state == "CONTINUOUS_MODULATION"
    assert hour.heat_pump_electricity_kwh == 4.0 / 2.5
    assert hour.defrost_energy_penalty_kwh is None
    assert hour.defrost_heat_penalty_kwh is None


def test_below_minimum_modulation_is_state_only_until_cycling_evidence_exists():
    result = run(1.0, humidity=90.0)
    hour = result.hourly[0]
    assert "CYCLING_REQUIRED" in hour.operating_state
    assert hour.heat_pump_electricity_kwh == 1.0 / 2.5
    assert hour.defrost_energy_penalty_kwh is None


def test_defrost_unknown_and_humidity_missing_fail_closed_without_zero_imputation():
    missing = run(4.0, humidity=None)
    present = run(4.0, humidity=95.0)
    assert missing.defrost_status == "Q"
    assert missing.hourly[0].defrost_energy_penalty_kwh is None
    assert present.hourly[0].defrost_energy_penalty_kwh is None
    assert missing.seasonal_total_electricity_kwh == present.seasonal_total_electricity_kwh


def test_cold_operation_keeps_source_input_boundary_and_does_not_double_count_penalties():
    result = run(4.0, humidity=90.0)
    hour = result.hourly[0]
    assert hour.total_electricity_kwh == hour.heat_pump_electricity_kwh + hour.backup_electricity_kwh
    assert result.seasonal_total_electricity_kwh == result.seasonal_heat_pump_electricity_kwh


def test_cdh_measured_is_unknown_and_regulatory_default_is_pol_only():
    variables = {row["variable_id"]: row for row in registry_rows("variables.csv")}
    assert variables["VAR-B05-CDH-MEASURED"]["status"] == "Q"
    default = variables["VAR-B05-CDH-REGULATORY-DEFAULT"]
    assert default["status"] == "POL"
    assert default["default_value"] == ""
    assert "0.9" in default["notes"]


def test_runtime_penalty_variables_remain_separate_q_contracts():
    variables = {row["variable_id"]: row for row in registry_rows("variables.csv")}
    for variable_id in (
        "VAR-B05-DEFROST-ACCOUNTING-BOUNDARY",
        "VAR-B05-DEFROST-RUNTIME-PENALTY",
        "VAR-B05-CYCLING-PENALTY-RUNTIME",
    ):
        assert variables[variable_id]["status"] == "Q"


def test_no_synthetic_or_pol_source_is_promoted_to_observed_performance():
    points = registry_rows("../data/processed/heat_pump_performance_points.csv")
    observed = [row for row in points if row["evidence_status"] == "OBS"]
    assert all(not row["source_id"].startswith("SRC-B05-SYNTHETIC") for row in observed)
    assert all(row["evidence_status"] != "POL" for row in points)
