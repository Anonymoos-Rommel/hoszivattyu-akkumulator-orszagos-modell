from datetime import datetime, timezone
from pathlib import Path

import unittest
import tempfile


class _Raises:
    def __init__(self, expected):
        self.expected = expected
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, _traceback):
        if exc_type is None:
            raise AssertionError(f"expected {self.expected.__name__}")
        if not issubclass(exc_type, self.expected):
            return False
        return True


class _Mark:
    @staticmethod
    def parametrize(_names, _values):
        return lambda function: function


class _PytestCompat:
    mark = _Mark()
    raises = staticmethod(_Raises)


pytest = _PytestCompat()

from modules.B05.engine import HourlyDemand, OperatingConfig, PerformanceMap, PerformancePoint, simulate_hourly
from modules.B07.engine import BatteryEngine, BatterySpec, compute_household_balance, make_b08_handoff
from modules.B08.engine import B08ContractError, GridBoundaryRecord, aggregate_grid_load as _aggregate_grid_load, run_fixture


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ("SRC-B08-SCN-GRID-FIXTURE",)


def aggregate_grid_load(records, **kwargs):
    """Test helper makes the bounded SCN scope explicit for SCN fixtures."""
    kwargs.setdefault("scope", "BOUNDED_SCN_FIXTURE")
    return _aggregate_grid_load(records, **kwargs)


def record(**overrides):
    values = dict(timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc), timestep_hours=1.0,
                  source_entity_id="HH-1", region_id="R1", region_scheme="HU_COUNTY_SCN",
                  b01_state_id="S3", truth_context="SCN", evidence_status="SCN",
                  source_refs=SOURCE, net_grid_import_kw=2.0, net_grid_export_kw=0.0,
                  physical_up_flex_kw=0.5, physical_down_flex_kw=0.25)
    values.update(overrides)
    return GridBoundaryRecord(**values)


def test_import_export_net_identity_and_negative_net_is_retained():
    result = aggregate_grid_load([record(net_grid_import_kw=0.0, net_grid_export_kw=1.5)])
    row = result.scope_total_rows[0]
    assert row.net_grid_load_kw == -1.5
    assert row.import_kwh - row.export_kwh == row.net_kwh


def test_explicit_timestep_converts_power_to_energy():
    result = aggregate_grid_load([record(timestep_hours=0.5, net_grid_import_kw=4.0, net_grid_export_kw=0.0)])
    row = result.scope_total_rows[0]
    assert row.import_kwh == 2.0
    assert row.export_kwh == 0.0
    assert row.net_kwh == 2.0


def test_fixture_region_state_national_reconciliation_and_peaks():
    result = run_fixture(ROOT / "data/fixtures/b08_grid_load_scn.json")
    assert result.status == result.truth_context == "SCN"
    assert result.scope == "BOUNDED_SCN_FIXTURE"
    assert len(result.rows) == 6 and len(result.scope_total_rows) == 2
    for timestamp in {row.timestamp for row in result.scope_total_rows}:
        regional = [row for row in result.rows if row.timestamp == timestamp]
        national = next(row for row in result.scope_total_rows if row.timestamp == timestamp)
        assert sum(row.gross_grid_import_kw for row in regional) == national.gross_grid_import_kw
        assert sum(row.gross_grid_export_kw for row in regional) == national.gross_grid_export_kw
    assert result.peak_gross_import_kw == 4.5
    assert result.peak_gross_export_kw == 1.0
    assert result.peak_net_grid_load_kw == 4.5
    assert result.explanations[0]["bounded_scope_total_label"] == "BOUNDED_SCOPE_TOTAL"


def test_deterministic_tied_peak_timestamps():
    first = record(timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc), source_entity_id="HH-1")
    second = record(timestamp=datetime(2026, 1, 2, tzinfo=timezone.utc), source_entity_id="HH-1")
    result = aggregate_grid_load([second, first])
    assert result.peak_gross_import_timestamps == (datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 1, 2, tzinfo=timezone.utc))


def test_duplicate_canonical_key_rejected():
    with pytest.raises(B08ContractError):
        aggregate_grid_load([record(), record()])


def test_missing_or_q_values_fail_closed_without_fill_zero():
    with pytest.raises(B08ContractError):
        GridBoundaryRecord(**{**record().__dict__, "net_grid_import_kw": None})
    result = aggregate_grid_load([record(evidence_status="Q")])
    assert result.status == "Q" and result.scope_total_rows[0].gross_grid_import_kw == 2.0


def test_mixed_region_schemes_fail_closed_and_county_is_not_dso():
    with pytest.raises(B08ContractError):
        aggregate_grid_load([record(), record(source_entity_id="HH-2", region_scheme="DSO_SCN")])
    result = aggregate_grid_load([record()])
    assert result.region_scheme == "HU_COUNTY_SCN"
    assert not hasattr(result, "dso")


def test_state_trace_does_not_synthesize_population_load():
    result = aggregate_grid_load([record(net_grid_import_kw=2.0)])
    assert result.scope_total_rows[0].source_entity_count == 1
    assert result.scope_total_rows[0].gross_grid_import_kw == 2.0


def test_flexibility_is_aggregated_but_does_not_change_load():
    result = aggregate_grid_load([record(physical_up_flex_kw=3.0, physical_down_flex_kw=4.0)])
    row = result.scope_total_rows[0]
    assert (row.physical_up_flex_kw, row.physical_down_flex_kw) == (3.0, 4.0)
    assert row.net_grid_load_kw == 2.0


def test_export_permission_remains_q_and_no_legal_claim_is_created():
    result = aggregate_grid_load([record(net_grid_import_kw=0.0, net_grid_export_kw=2.0)])
    assert result.status == "SCN"
    assert not hasattr(result.scope_total_rows[0], "legal_export")


def test_b07_handoff_is_lossless():
    spec = BatterySpec(10, 10, 0, 1, 5, 5, 0.9, 0.9, 1.0, status="SCN")
    engine = BatteryEngine(spec, 5)
    step = engine.step()
    balance = compute_household_balance(1.0, 0.0, 0.5, 0.0, 0.0, 0.0)
    handoff = make_b08_handoff(balance, step, spec)
    row = GridBoundaryRecord.from_b07_handoff(timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc), timestep_hours=1.0,
        source_entity_id="HH-1", region_id="R1", region_scheme="HU_COUNTY_SCN", b01_state_id="S3",
        handoff=handoff, truth_context="SCN", evidence_status="SCN", source_refs=SOURCE)
    assert (row.net_grid_import_kw, row.net_grid_export_kw) == (handoff.net_grid_import_kw, handoff.net_grid_export_kw)


def test_b05_b07_b08_path_does_not_double_count_heat_pump():
    point = PerformancePoint(0.0, 35.0, thermal_capacity_kw=5.0, electrical_input_kw=2.0, cop=2.5, evidence_status="SCN")
    hp = simulate_hourly(PerformanceMap("SCN-HP", "air_water", [point]),
                         [HourlyDemand(datetime(2026, 1, 1, tzinfo=timezone.utc), 0.0, 3.0, 35.0)], OperatingConfig(timestep_hours=0.5))
    hp_kw = hp.hourly[0].heat_pump_electricity_kwh
    hp_load_kw = hp_kw / 0.5
    balance = compute_household_balance(0.0, hp_load_kw, 1.5, 0.0, 0.0, 0.0)
    spec = BatterySpec(10, 10, 0, 1, 5, 5, 0.9, 0.9, 0.5, status="SCN")
    handoff = make_b08_handoff(balance, BatteryEngine(spec, 5).step(), spec)
    result = aggregate_grid_load([GridBoundaryRecord.from_b07_handoff(timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc), timestep_hours=0.5,
        source_entity_id="HH-1", region_id="R1", region_scheme="HU_COUNTY_SCN", b01_state_id="S3",
        handoff=handoff, truth_context="SCN", evidence_status="SCN", source_refs=SOURCE)])
    assert result.scope_total_rows[0].net_grid_load_kw == 2.7
    assert result.scope_total_rows[0].net_kwh == 1.35
    assert result.scope_total_rows[0].net_grid_load_kw != 3.9  # B05 electricity is not added a second time.


@pytest.mark.parametrize("field", ["net_grid_import_kw", "net_grid_export_kw", "physical_up_flex_kw", "physical_down_flex_kw"])
def test_negative_physical_inputs_rejected(field=None):
    if field is None:
        for candidate in ("net_grid_import_kw", "net_grid_export_kw", "physical_up_flex_kw", "physical_down_flex_kw"):
            test_negative_physical_inputs_rejected(candidate)
        return
    with pytest.raises(B08ContractError):
        record(**{field: -0.1})


def test_mixed_truth_context_rejected():
    with pytest.raises(B08ContractError):
        aggregate_grid_load([record(), record(source_entity_id="HH-2", truth_context="REAL", evidence_status="OBS")])


def test_inconsistent_timestep_rejected():
    with pytest.raises(B08ContractError):
        aggregate_grid_load([record(), record(source_entity_id="HH-2", timestep_hours=0.5)])


def test_bounded_result_has_no_b09_b10_or_seasonal_authority():
    result = run_fixture(ROOT / "data/fixtures/b08_grid_load_scn.json")
    assert not hasattr(result, "generation_kw")
    assert not hasattr(result, "dispatch_kw")
    assert not hasattr(result, "available_headroom_kw")
    assert not hasattr(result, "reinforcement_kw")
    assert not hasattr(result, "seasonal_peak_kw")


def test_provenance_is_present_on_rows_and_result():
    result = run_fixture(ROOT / "data/fixtures/b08_grid_load_scn.json")
    assert result.source_refs == SOURCE
    assert all(row.source_refs and row.evidence_statuses for row in result.rows)
    assert result.explanations[0]["truth_context"] == "SCN"


def _panel_rows():
    return [record(source_entity_id=entity, timestamp=datetime(2026, 1, day, 1, tzinfo=timezone.utc), net_grid_import_kw=1.0)
            for day in (1, 2) for entity in ("HH-1", "HH-2", "HH-3")]


def test_complete_panel_passes_and_missing_pair_fails_closed():
    rows = _panel_rows()
    assert aggregate_grid_load(rows).scope_total_rows[0].source_entity_count == 3
    with pytest.raises(B08ContractError):
        aggregate_grid_load(rows[:-1])


def test_alternate_boundary_cannot_bypass_duplicate_gate():
    with pytest.raises(B08ContractError):
        aggregate_grid_load([record(), record(boundary_id="H_TARIFF")])


def test_fixture_real_row_or_region_header_mismatch_fails_closed():
    import json
    fixture_path = ROOT / "data/fixtures/b08_grid_load_scn.json"
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    payload["records"][0]["truth_context"] = "REAL"
    handle = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    broken = Path(handle.name)
    handle.close()
    broken.write_text(json.dumps(payload), encoding="utf-8")
    try:
        with pytest.raises(B08ContractError):
            run_fixture(broken)
    finally:
        broken.unlink()
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    payload["records"][0]["region_scheme"] = "OTHER"
    broken.write_text(json.dumps(payload), encoding="utf-8")
    try:
        with pytest.raises(B08ContractError):
            run_fixture(broken)
    finally:
        broken.unlink()


def test_truth_and_evidence_worlds_are_fail_closed_both_directions():
    with pytest.raises(B08ContractError):
        record(truth_context="REAL", evidence_status="SCN")
    with pytest.raises(B08ContractError):
        record(truth_context="REAL", evidence_status="ASS")
    with pytest.raises(B08ContractError):
        record(truth_context="REAL", evidence_status="POL")
    with pytest.raises(B08ContractError):
        record(truth_context="SCN", evidence_status="OBS")


def test_complete_b07_handoff_payload_and_timestep_are_preserved():
    spec = BatterySpec(10, 10, 0, 1, 5, 5, 0.9, 0.9, 0.5, status="SCN")
    handoff = make_b08_handoff(compute_household_balance(1, 0, 0.5, 0, 0, 0), BatteryEngine(spec, 5).step(), spec)
    row = GridBoundaryRecord.from_b07_handoff(timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc), timestep_hours=0.5,
        source_entity_id="HH-1", region_id="R1", region_scheme="HU_COUNTY_SCN", b01_state_id="S3",
        handoff=handoff, truth_context="SCN", evidence_status="SCN", source_refs=SOURCE)
    assert row.battery_charge_kw == handoff.battery_charge_kw
    assert row.battery_discharge_kw == handoff.battery_discharge_kw
    assert row.soc_fraction == handoff.soc_fraction
    assert row.handoff_status == handoff.status == "SCN"
    assert row.upstream_timestep_hours == handoff.timestep_hours == 0.5
    with pytest.raises(B08ContractError):
        GridBoundaryRecord.from_b07_handoff(timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc), timestep_hours=1.0,
            source_entity_id="HH-1", region_id="R1", region_scheme="HU_COUNTY_SCN", b01_state_id="S3",
            handoff=handoff, truth_context="SCN", evidence_status="SCN", source_refs=SOURCE)


def test_scope_enum_and_strict_mapping_types():
    with pytest.raises(B08ContractError):
        aggregate_grid_load([record()], scope="HUNGARY_NATIONAL_VALIDATED")
    from modules.B08.engine import _record_from_mapping
    payload = {**record().__dict__, "timestamp": "2026-01-01T00:00:00Z", "source_refs": "SRC-X"}
    with pytest.raises(B08ContractError):
        _record_from_mapping(payload)
    payload["source_refs"] = ["SRC-X"]
    payload["source_entity_id"] = None
    with pytest.raises(B08ContractError):
        _record_from_mapping(payload)


def test_timezone_contract_normalizes_offsets_and_rejects_naive():
    first = record(timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc))
    second = record(timestamp=datetime(2026, 1, 1, 1, tzinfo=timezone.utc), source_entity_id="HH-1")
    # Same canonical instant requires the same entity and would be a duplicate.
    second = record(timestamp=datetime(2026, 1, 1, 1, tzinfo=timezone.utc).astimezone(timezone.utc), source_entity_id="HH-2")
    with pytest.raises(B08ContractError):
        GridBoundaryRecord(**{**record().__dict__, "timestamp": datetime(2026, 1, 1)})
    offset = record(timestamp=datetime.fromisoformat("2025-12-31T19:00:00-05:00"), source_entity_id="HH-2")
    result = aggregate_grid_load([first, offset])
    assert result.scope_total_rows[0].timestamp == datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_household_import_and_export_cannot_both_be_positive():
    with pytest.raises(B08ContractError):
        record(net_grid_import_kw=1.0, net_grid_export_kw=0.1)


def test_obs_inputs_produce_derived_real_aggregate_not_obs():
    result = aggregate_grid_load([record(truth_context="REAL", evidence_status="OBS")], scope="BOUNDED_REAL_AGGREGATE")
    assert result.status == "DER"
    assert result.scope_total_rows[0].evidence_status == "DER"


def test_bounded_totals_conserve_and_have_no_national_authority():
    result = run_fixture(ROOT / "data/fixtures/b08_grid_load_scn.json")
    assert result.scope_total_rows[0].region_id == "BOUNDED_SCOPE_TOTAL"
    assert not hasattr(result, "national_rows")
    assert sum(row.gross_grid_import_kw for row in result.rows if row.timestamp == result.scope_total_rows[0].timestamp) == result.scope_total_rows[0].gross_grid_import_kw


def test_scope_must_match_truth_context():
    real = record(truth_context="REAL", evidence_status="OBS")
    assert _aggregate_grid_load([real], scope="BOUNDED_REAL_AGGREGATE").status == "DER"
    scn = record()
    assert _aggregate_grid_load([scn], scope="BOUNDED_SCN_FIXTURE").status == "SCN"
    with pytest.raises(B08ContractError):
        _aggregate_grid_load([scn], scope="BOUNDED_REAL_AGGREGATE")
    with pytest.raises(B08ContractError):
        _aggregate_grid_load([real], scope="BOUNDED_SCN_FIXTURE")
    with pytest.raises(B08ContractError):
        _aggregate_grid_load([scn])


def test_generic_record_has_no_fabricated_b07_diagnostic_payload():
    row = record()
    assert row.battery_charge_kw is None
    assert row.battery_discharge_kw is None
    assert row.soc_fraction is None
    assert row.handoff_status is None
    assert row.upstream_timestep_hours is None
    aggregate = aggregate_grid_load([row]).scope_total_rows[0]
    assert aggregate.diagnostic_complete is False
    assert aggregate.battery_charge_kw is None
    assert aggregate.battery_discharge_kw is None


def test_partial_diagnostic_payload_fails_closed():
    with pytest.raises(B08ContractError):
        record(battery_charge_kw=0.0)


def test_b07_truth_status_cannot_be_relabelled():
    spec = BatterySpec(10, 10, 0, 1, 5, 5, 0.9, 0.9, 0.5, status="SCN")
    handoff = make_b08_handoff(compute_household_balance(1, 0, 0, 0, 0, 0), BatteryEngine(spec, 5).step(), spec)
    with pytest.raises(B08ContractError):
        GridBoundaryRecord.from_b07_handoff(timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            source_entity_id="HH-1", region_id="R1", region_scheme="HU_COUNTY_SCN", b01_state_id="S3",
            handoff=handoff, truth_context="SCN", evidence_status="DER", source_refs=SOURCE)
    real_spec = BatterySpec(10, 10, 0, 1, 5, 5, 0.9, 0.9, 0.5, status="DER")
    real_handoff = make_b08_handoff(compute_household_balance(1, 0, 0, 0, 0, 0), BatteryEngine(real_spec, 5).step(), real_spec)
    real_row = GridBoundaryRecord.from_b07_handoff(timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        source_entity_id="HH-1", region_id="R1", region_scheme="HU_COUNTY_SCN", b01_state_id="S3",
        handoff=real_handoff, truth_context="REAL", evidence_status="DER", source_refs=SOURCE)
    assert real_row.handoff_status == "DER"


class B08UnittestBridge(unittest.TestCase):
    """Expose the pytest-style contract tests to the repository unittest runner."""

    def test_contract_suite(self):
        functions = (
            test_import_export_net_identity_and_negative_net_is_retained,
            test_explicit_timestep_converts_power_to_energy,
            test_fixture_region_state_national_reconciliation_and_peaks,
            test_deterministic_tied_peak_timestamps,
            test_duplicate_canonical_key_rejected,
            test_missing_or_q_values_fail_closed_without_fill_zero,
            test_mixed_region_schemes_fail_closed_and_county_is_not_dso,
            test_state_trace_does_not_synthesize_population_load,
            test_flexibility_is_aggregated_but_does_not_change_load,
            test_export_permission_remains_q_and_no_legal_claim_is_created,
            test_b07_handoff_is_lossless,
            test_b05_b07_b08_path_does_not_double_count_heat_pump,
            test_negative_physical_inputs_rejected,
            test_mixed_truth_context_rejected,
            test_inconsistent_timestep_rejected,
            test_bounded_result_has_no_b09_b10_or_seasonal_authority,
            test_provenance_is_present_on_rows_and_result,
            test_complete_panel_passes_and_missing_pair_fails_closed,
            test_alternate_boundary_cannot_bypass_duplicate_gate,
            test_fixture_real_row_or_region_header_mismatch_fails_closed,
            test_truth_and_evidence_worlds_are_fail_closed_both_directions,
            test_complete_b07_handoff_payload_and_timestep_are_preserved,
            test_scope_enum_and_strict_mapping_types,
            test_timezone_contract_normalizes_offsets_and_rejects_naive,
            test_household_import_and_export_cannot_both_be_positive,
            test_obs_inputs_produce_derived_real_aggregate_not_obs,
            test_bounded_totals_conserve_and_have_no_national_authority,
            test_scope_must_match_truth_context,
            test_generic_record_has_no_fabricated_b07_diagnostic_payload,
            test_partial_diagnostic_payload_fails_closed,
            test_b07_truth_status_cannot_be_relabelled,
        )
        for function in functions:
            with self.subTest(function=function.__name__):
                function()
