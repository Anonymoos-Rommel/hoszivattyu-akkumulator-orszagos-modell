"""Validate the bootstrap registry contracts using only the Python standard library."""

from __future__ import annotations

import csv
import re
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry"

EXPECTED_HEADERS = {
    "module_status.csv": [
        "module_id",
        "module_name",
        "depends_on",
        "status",
        "readiness_percent",
        "gate_note",
    ],
    "sources.csv": [
        "source_id",
        "module_id",
        "title",
        "institution",
        "url",
        "published_at",
        "retrieved_at",
        "reference_period",
        "source_tier",
        "evidence_status",
        "reliability",
        "license",
        "local_snapshot_sha256",
        "notes",
    ],
    "variables.csv": [
        "variable_id",
        "module_id",
        "name",
        "definition",
        "unit",
        "default_value",
        "min_value",
        "max_value",
        "status",
        "source_ids",
        "updated_at",
        "notes",
    ],
    "formulas.csv": [
        "formula_id",
        "module_id",
        "output_variable_id",
        "expression",
        "input_variable_ids",
        "output_unit",
        "status",
        "notes",
    ],
    "open_questions.csv": [
        "question_id",
        "module_id",
        "priority",
        "question",
        "decision_impact",
        "evidence_needed",
        "status",
        "owner",
        "notes",
    ],
    "datasets.csv": [
        "dataset_id",
        "module_id",
        "title",
        "institution",
        "source_id",
        "access_method",
        "source_version",
        "dataflow_id",
        "metadata_endpoint",
        "data_endpoint",
        "geography_grain",
        "reference_period",
        "dimensions",
        "measure_id",
        "unit",
        "evidence_status",
        "retrieved_at",
        "license",
        "snapshot_policy",
        "raw_storage_path",
        "notes",
    ],
    "archetype_dimensions.csv": [
        "dimension_id",
        "module_id",
        "name",
        "source_dataset_ids",
        "source_dimension_ids",
        "role",
        "canonical_grain",
        "observability",
        "required",
        "aggregation_rule",
        "unknown_policy",
        "status",
        "notes",
    ],
    "intervention_catalog.csv": [
        "intervention_id",
        "stage_from",
        "stage_to",
        "archetype_id",
        "region_id",
        "action_name",
        "prerequisites",
        "effect_outputs",
        "capex_unit",
        "opex_unit",
        "duration_years",
        "capacity_requirements",
        "evidence_status",
        "source_ids",
        "status",
        "notes",
    ],
    "priority_components.csv": [
        "component_id",
        "name",
        "definition",
        "unit",
        "evidence_status",
        "weight_status",
        "lower_bound",
        "upper_bound",
        "source_ids",
        "status",
        "notes",
    ],
    "portfolio_schedule.csv": [
        "plan_year",
        "region_id",
        "archetype_id",
        "intervention_id",
        "candidate_count",
        "selected_count",
        "waiting_years",
        "public_budget_huf",
        "binding_constraint_id",
        "explanation",
        "evidence_status",
        "status",
        "notes",
    ],
    "regional_readiness.csv": [
        "period",
        "region_id",
        "region_type",
        "grid_headroom_mw",
        "installer_fte",
        "supply_capacity",
        "permit_capacity",
        "public_budget_huf",
        "readiness_status",
        "source_ids",
        "evidence_status",
        "status",
        "notes",
    ],
    "baseline_infrastructure.csv": [
        "baseline_id",
        "asset_type",
        "region_id",
        "status_taxonomy",
        "scope_description",
        "committed_date",
        "counterfactual_cost_huf",
        "program_incremental_cost_huf",
        "source_ids",
        "evidence_status",
        "status",
        "notes",
    ],
    "incremental_capex_attribution.csv": [
        "attribution_id",
        "baseline_id",
        "intervention_id",
        "region_id",
        "cost_component",
        "baseline_cost_huf",
        "incremental_cost_huf",
        "allocation_rule",
        "source_ids",
        "evidence_status",
        "status",
        "notes",
    ],
    "fiscal_headroom.csv": [
        "fiscal_year",
        "earmark_id",
        "cash_in_huf",
        "committed_out_huf",
        "reinvestable_cash_huf",
        "headroom_huf",
        "debt_ratio",
        "cash_flow_floor_huf",
        "binding_constraint_id",
        "source_ids",
        "evidence_status",
        "status",
        "notes",
    ],
    "b02_readiness_bridge.csv": [
        "bridge_id",
        "state_id",
        "field_id",
        "field_name",
        "current_source_or_registry",
        "evidence_status",
        "required_for_gate",
        "allow_inference",
        "block_reason",
        "downstream_modules",
        "status",
        "notes",
    ],
    "b02_s0_s2_evidence_gap_matrix.csv": [
        "gap_id",
        "state_id",
        "readiness_field",
        "requirement",
        "current_source_ids",
        "current_source_coverage",
        "evidence_status",
        "grain",
        "coverage_scope",
        "allow_for_gate",
        "remaining_gap",
        "pilot_relevance",
        "downstream_modules",
        "status",
        "notes",
    ],
    "oeny_pilot_acceptance_contract.csv": [
        "field_id",
        "field_name",
        "schema_path",
        "readiness_state",
        "readiness_goal",
        "required_grain",
        "minimum_quality",
        "missing_tolerance",
        "sample_expectation",
        "privacy_minimum",
        "success_criteria",
        "failure_criteria",
        "prohibited_inferences",
        "status",
        "notes",
    ],
    "oeny_requested_field_manifest.csv": [
        "manifest_id",
        "request_stage",
        "field_name",
        "field_id",
        "schema_path",
        "requested_output",
        "required_grain",
        "required_or_optional",
        "privacy_limit",
        "acceptance_link",
        "status",
        "notes",
    ],
    "oeny_public_endpoints.csv": [
        "endpoint_id",
        "endpoint_url_or_pattern",
        "http_method",
        "provider",
        "officially_documented",
        "authentication_required",
        "request_parameters",
        "response_schema",
        "pagination",
        "filtering",
        "sorting",
        "incremental_query",
        "rate_limit",
        "cache_freshness",
        "license_tos_status",
        "personal_data_risk",
        "bulk_usable",
        "reproducibility",
        "evidence_status",
        "status",
        "notes",
    ],
    "oeny_public_field_mapping.csv": [
        "field_id",
        "field_name",
        "public_machine_sources",
        "availability_status",
        "grain",
        "minimum_quality",
        "readiness_use",
        "limitation",
        "evidence_status",
        "status",
        "notes",
    ],
    "gas_price_sources.csv": [
        "source_id", "module_id", "layer", "title", "institution", "url",
        "reference_period", "retrieved_at", "source_tier", "evidence_status",
        "license_status", "local_snapshot_status", "notes",
    ],
    "gas_price_variables.csv": [
        "variable_id", "module_id", "layer", "name", "definition", "unit",
        "status", "source_ids", "updated_at", "notes",
    ],
    "gas_price_formulas.csv": [
        "formula_id", "module_id", "layer", "output_variable_id", "expression",
        "input_variable_ids", "output_unit", "status", "notes",
    ],
    "electricity_price_sources.csv": [
        "source_id", "module_id", "layer", "title", "institution", "url",
        "reference_period", "retrieved_at", "source_tier", "evidence_status",
        "license_status", "local_snapshot_status", "notes",
    ],
    "electricity_price_variables.csv": [
        "variable_id", "module_id", "layer", "name", "definition", "unit",
        "status", "source_ids", "updated_at", "notes",
    ],
    "electricity_price_formulas.csv": [
        "formula_id", "module_id", "layer", "output_variable_id", "expression",
        "input_variable_ids", "output_unit", "status", "notes",
    ],
    "electricity_tariff_rules.csv": [
        "rule_id", "module_id", "layer", "tariff_id", "rule_type", "valid_from",
        "valid_to", "condition", "action", "status", "source_ids", "notes",
    ],
    "electricity_readiness.csv": [
        "component_id", "module_id", "layer", "status", "readiness_percent",
        "source_ids", "notes",
    ],
    "heat_pump_sources.csv": [
        "source_id", "module_id", "layer", "title", "institution", "url",
        "reference_period", "retrieved_at", "source_tier", "evidence_status",
        "license_status", "local_snapshot_status", "notes",
    ],
    "heat_pump_variables.csv": [
        "variable_id", "module_id", "layer", "name", "definition", "unit",
        "status", "source_ids", "updated_at", "notes",
    ],
    "heat_pump_formulas.csv": [
        "formula_id", "module_id", "layer", "output_variable_id", "expression",
        "input_variable_ids", "output_unit", "status", "notes",
    ],
    "heat_pump_scenarios.csv": [
        "scenario_id", "module_id", "emitter_case", "weather_case", "equipment_case",
        "supply_temperature_C", "weather_status", "equipment_status", "status", "source_ids", "notes",
    ],
    "heat_pump_readiness.csv": [
        "component_id", "module_id", "layer", "status", "readiness_percent",
        "source_ids", "notes",
    ],
}

PROCESSED_EXPECTED_HEADERS = {
    "gas_price_history.csv": [
        "record_id", "layer", "benchmark", "reference_date", "reference_period",
        "scenario", "eur_per_mwh", "eur_huf", "huf_per_mwh",
        "heating_value_kwh_per_m3", "huf_per_m3", "status", "source_ids", "notes",
    ],
    "gas_price_forward_curve.csv": [
        "curve_id", "layer", "benchmark", "as_of_date", "delivery_start",
        "delivery_end", "scenario", "eur_per_mwh", "eur_huf", "huf_per_m3",
        "status", "source_ids", "notes",
    ],
    "gas_price_scenarios.csv": [
        "scenario_id", "scenario", "zone", "year", "layer",
        "wholesale_eur_per_mwh", "market_residential_huf_per_m3",
        "regulated_residential_huf_per_m3", "transition_rule", "status",
        "source_ids", "notes",
    ],
    "residential_gas_tariff_schedule.csv": [
        "tariff_id", "service_year", "valid_from", "valid_to", "tariff_band",
        "tariff_scope", "threshold_mj", "threshold_m3_reference",
        "gas_price_huf_per_mj", "price_status", "vat_rate",
        "gross_price_huf_per_mj", "gross_price_status",
        "reference_heating_value_mj_per_m3", "illustrative_gross_huf_per_m3",
        "illustrative_status", "annual_fixed_charge_huf", "fixed_charge_status",
        "status", "source_id", "notes",
    ],
    "gas_price_component_bridge.csv": [
        "bridge_id", "reference_period", "scenario", "layer",
        "commodity_huf_per_m3", "network_huf_per_m3", "storage_huf_per_m3",
        "commercial_huf_per_m3", "tax_huf_per_m3", "vat_huf_per_m3",
        "other_huf_per_m3", "final_huf_per_m3", "status", "source_ids", "notes",
    ],
    "electricity_price_history.csv": [
        "record_id", "layer", "market", "product", "reference_date", "reference_period",
        "eur_per_mwh", "eur_huf", "huf_per_mwh", "status", "source_id", "notes",
    ],
    "electricity_price_forward_curve.csv": [
        "curve_id", "layer", "market", "product", "as_of_date", "delivery_start",
        "delivery_end", "eur_per_mwh", "status", "source_id", "notes",
    ],
    "electricity_price_scenarios.csv": [
        "scenario_id", "scenario", "year", "layer", "wholesale_eur_per_mwh",
        "eur_huf", "wholesale_huf_per_kwh", "standard_residential_huf_per_kwh",
        "h_tariff_huf_per_kwh", "transition_rule", "status", "source_ids", "notes",
    ],
    "residential_electricity_tariff_schedule.csv": [
        "tariff_id", "distributor_area", "tariff_band", "valid_from", "valid_to",
        "threshold_kwh", "energy_price_net_huf_per_kwh", "energy_price_gross_huf_per_kwh",
        "network_charge_huf_per_kwh", "fixed_charge_huf_per_year", "final_gross_huf_per_kwh",
        "status", "source_id", "notes",
    ],
    "heat_pump_performance_coverage.csv": [
        "equipment_id", "outdoor_temperature_C", "supply_temperature_C",
        "evidence_status", "source_id", "notes",
    ],
    "h_tariff_schedule.csv": [
        "tariff_id", "distributor_area", "period_type", "valid_from", "valid_to",
        "net_huf_per_kwh", "gross_huf_per_kwh", "separate_meter_required", "eligible_load_scope",
        "battery_charging_status", "export_status", "status", "source_id", "notes",
    ],
    "electricity_price_component_bridge.csv": [
        "bridge_id", "reference_period", "tariff_id", "layer", "energy_net_huf_per_kwh",
        "network_charge_huf_per_kwh", "fixed_charge_huf_per_year", "tax_huf_per_kwh",
        "vat_rate", "final_gross_huf_per_kwh", "status", "source_id", "notes",
    ],
    "heat_pump_performance_points.csv": [
        "point_id", "equipment_id", "technology", "model_identifier", "outdoor_temperature_C",
        "supply_temperature_C", "return_temperature_C", "delta_temperature_C",
        "thermal_capacity_kW", "electrical_input_kW", "COP", "min_modulation_kW",
        "operating_limit_min_outdoor_C", "operating_limit_max_outdoor_C", "unit_boundary",
        "test_standard", "evidence_status", "source_id", "retrieved_at", "notes",
    ],
    "heat_pump_weather_scenarios.csv": [
        "record_id", "scenario_id", "timestamp", "outdoor_temperature_C",
        "relative_humidity_pct", "status", "source_id", "notes",
    ],
    "heat_pump_weather_hourly.csv": [
        "record_id", "weather_profile_id", "station_id", "timestamp_utc",
        "outdoor_temperature_C", "temperature_source_variable",
        "instantaneous_temperature_C", "relative_humidity_pct",
        "hourly_min_temperature_C", "hourly_max_temperature_C",
        "evidence_status", "source_id", "retrieved_at",
    ],
    "heat_pump_weather_profiles.csv": [
        "weather_profile_id", "profile_type", "station_id", "station_name",
        "latitude", "longitude", "elevation_m", "period_start_utc",
        "period_end_utc", "selection_method", "source_reference_period",
        "retrieved_at", "completeness", "status", "source_id", "notes",
    ],
    "heat_pump_weather_coverage.csv": [
        "weather_profile_id", "station_id", "equipment_id", "supply_temperature_C",
        "hours_total", "hours_below_minus7C", "hours_inside_performance_domain",
        "hours_above_plus7C", "share_inside_current_performance_domain",
        "minimum_observed_temperature_C", "new_hours_inside_performance_domain",
        "new_share_inside_performance_domain",
        "remaining_hours_below_new_minimum_performance_C",
        "new_minimum_performance_temperature_C", "status", "source_id", "notes",
    ],
    "heat_pump_weather_supply_coverage.csv": [
        "weather_profile_id", "station_id", "equipment_id", "supply_temperature_C",
        "performance_domain_min_Tout_C", "performance_domain_max_Tout_C",
        "weather_hours_total", "weather_hours_inside_domain",
        "weather_hours_below_domain", "weather_hours_above_domain",
        "coverage_share", "coldest_uncovered_Tout_C", "status", "source_id", "notes",
    ],
}

ALLOWED_MODULE_STATUS = {"NOT_STARTED", "IN_PROGRESS", "BLOCKED", "VALIDATED"}
ALLOWED_EVIDENCE_STATUS = {"OBS", "DER", "ASS", "SCN", "POL", "Q"}
ALLOWED_SOURCE_TIERS = {"P1", "P2", "P3", "P4"}
ALLOWED_RELIABILITY = {"HIGH", "MEDIUM", "LOW"}
ALLOWED_QUESTION_PRIORITY = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
ALLOWED_QUESTION_STATUS = {"OPEN", "BLOCKED", "RESOLVED"}
ALLOWED_DIMENSION_OBSERVABILITY = {"OBS", "MODELLED", "Q"}
ALLOWED_DIMENSION_REQUIRED = {"yes", "no"}
ALLOWED_DIMENSION_STATUS = {"CONTRACTED", "PROPOSED", "GAP"}
ALLOWED_DIMENSION_ROLES = {
    "archetype_key",
    "baseline_flag",
    "eligibility_input",
    "energy_input",
    "stratifier",
    "universe_filter",
}
ALLOWED_DATASET_ACCESS_METHODS = {"KSH_CENSUS_API", "EMBEDDED_HTML", "PDF_TABLE"}

MODULE_ID_PATTERN = re.compile(r"B(?:0[1-9]|1[0-9]|20)")
SOURCE_ID_PATTERN = re.compile(r"SRC-(B(?:0[1-9]|1[0-9]|20))-[A-Z0-9-]+")
VARIABLE_ID_PATTERN = re.compile(r"VAR-(B(?:0[1-9]|1[0-9]|20))-[A-Z0-9-]+")
QUESTION_ID_PATTERN = re.compile(r"Q-(B(?:0[1-9]|1[0-9]|20))-\d{3}")
DATASET_ID_PATTERN = re.compile(r"DATA-(B(?:0[1-9]|1[0-9]|20))-[A-Z0-9-]+")
DIMENSION_ID_PATTERN = re.compile(r"DIM-(B(?:0[1-9]|1[0-9]|20))-[A-Z0-9-]+")
SOURCE_VERSION_PATTERN = re.compile(r"(?:V\d+|Y\d{4}|\d{4}-\d{2}-\d{2})")
FORMULA_ID_PATTERN = re.compile(r"FORM-(B(?:0[1-9]|1[0-9]|20))-[A-Z0-9-]+")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def is_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def validate_b03_artifacts(errors: list[str], source_ids: set[str]) -> None:
    """Validate B03's layer/status/source invariants in addition to headers."""
    b03_registry = REGISTRY
    b03_processed = ROOT / "data" / "processed"
    allowed_layers = {"FX", "WHOLESALE_IMPORT", "MARKET_RESIDENTIAL_FINAL", "REGULATED_RESIDENTIAL_TARIFF"}

    for filename in ("gas_price_sources.csv", "gas_price_variables.csv", "gas_price_formulas.csv"):
        path = b03_registry / filename
        if not path.is_file():
            continue
        _, rows = read_csv(path)
        id_field = {"gas_price_sources.csv": "source_id", "gas_price_variables.csv": "variable_id", "gas_price_formulas.csv": "formula_id"}[filename]
        duplicates = duplicate_values([row[id_field] for row in rows])
        if duplicates:
            errors.append(f"duplicate B03 IDs in {filename}: {duplicates!r}")
        for row in rows:
            if row["module_id"] != "B03":
                errors.append(f"B03 artifact has non-B03 module in {filename}: {row[id_field]!r}")
            if row.get("layer") not in allowed_layers and filename != "gas_price_formulas.csv":
                errors.append(f"invalid B03 layer in {filename}: {row[id_field]!r}")
            if filename == "gas_price_sources.csv" and row["source_id"] not in source_ids:
                errors.append(f"B03 source not mirrored in sources.csv: {row['source_id']!r}")
            if filename == "gas_price_variables.csv" and row["status"] not in ALLOWED_EVIDENCE_STATUS:
                errors.append(f"invalid B03 variable status: {row['variable_id']!r}")
            if filename == "gas_price_formulas.csv" and row["status"] not in {"DER", "ASS"}:
                errors.append(f"invalid B03 formula status: {row['formula_id']!r}")

    for filename in ("gas_price_history.csv", "gas_price_forward_curve.csv", "gas_price_scenarios.csv",
                     "residential_gas_tariff_schedule.csv", "gas_price_component_bridge.csv"):
        path = b03_processed / filename
        if not path.is_file():
            continue
        _, rows = read_csv(path)
        for row in rows:
            status = row.get("status", "")
            if status not in ALLOWED_EVIDENCE_STATUS:
                errors.append(f"invalid B03 processed status in {filename}: {status!r}")
            raw_refs = row.get("source_ids", "") or row.get("source_id", "")
            refs = [item for item in raw_refs.split(";") if item]
            unknown = [item for item in refs if item not in source_ids]
            if unknown:
                errors.append(f"unknown B03 processed source references in {filename}: {unknown!r}")


def validate_b04_artifacts(errors: list[str], source_ids: set[str]) -> None:
    """Validate B04 layer separation and fail-closed H tariff constraints."""
    allowed_layers = {
        "WHOLESALE_ELECTRICITY", "REGULATED_RESIDENTIAL_ELECTRICITY", "H_TARIFF",
        "MARKET_BASED_RESIDENTIAL_ELECTRICITY", "DYNAMIC_ELECTRICITY", "COMPONENT_BRIDGE",
    }
    registry_files = {
        "electricity_price_sources.csv": "source_id",
        "electricity_price_variables.csv": "variable_id",
        "electricity_price_formulas.csv": "formula_id",
        "electricity_tariff_rules.csv": "rule_id",
        "electricity_readiness.csv": "component_id",
    }
    for filename, id_field in registry_files.items():
        path = REGISTRY / filename
        if not path.is_file():
            continue
        _, rows = read_csv(path)
        duplicates = duplicate_values([row[id_field] for row in rows])
        if duplicates:
            errors.append(f"duplicate B04 IDs in {filename}: {duplicates!r}")
        for row in rows:
            if row["module_id"] != "B04":
                errors.append(f"B04 artifact has non-B04 module in {filename}: {row[id_field]!r}")
            if row.get("layer") not in allowed_layers and filename not in {"electricity_price_formulas.csv", "electricity_readiness.csv"}:
                errors.append(f"invalid B04 layer in {filename}: {row[id_field]!r}")
            if filename == "electricity_price_sources.csv" and row["source_id"] not in source_ids:
                errors.append(f"B04 source not mirrored in sources.csv: {row['source_id']!r}")
            if filename in {"electricity_price_variables.csv", "electricity_tariff_rules.csv"} and row["status"] not in ALLOWED_EVIDENCE_STATUS:
                errors.append(f"invalid B04 evidence status in {filename}: {row[id_field]!r}")
            if filename == "electricity_price_formulas.csv" and row["status"] not in {"DER", "ASS"}:
                errors.append(f"invalid B04 formula status: {row['formula_id']!r}")
            if filename == "electricity_readiness.csv" and row["status"] not in {"VALIDATED", "PARTIAL", "BLOCKED", "Q"}:
                errors.append(f"invalid B04 readiness status: {row['component_id']!r}")

    processed = ROOT / "data" / "processed"
    for filename in ("electricity_price_history.csv", "electricity_price_forward_curve.csv",
                     "electricity_price_scenarios.csv", "residential_electricity_tariff_schedule.csv",
                     "h_tariff_schedule.csv", "electricity_price_component_bridge.csv"):
        path = processed / filename
        if not path.is_file():
            continue
        _, rows = read_csv(path)
        for row in rows:
            if row.get("status") not in ALLOWED_EVIDENCE_STATUS:
                errors.append(f"invalid B04 processed status in {filename}: {row.get('status')!r}")
            raw_refs = row.get("source_ids", "") or row.get("source_id", "")
            refs = [item for item in raw_refs.split(";") if item]
            unknown = [item for item in refs if item not in source_ids]
            if unknown:
                errors.append(f"unknown B04 processed source references in {filename}: {unknown!r}")
            if filename == "h_tariff_schedule.csv" and row.get("battery_charging_status") != "Q":
                errors.append(f"H battery charging must remain Q: {row.get('tariff_id')!r}")
            if filename == "h_tariff_schedule.csv" and row.get("export_status") != "Q":
                errors.append(f"H export must remain Q: {row.get('tariff_id')!r}")


def validate_b05_artifacts(errors: list[str], source_ids: set[str]) -> None:
    """Validate B05 physical evidence labels, units, and fail-closed data."""
    allowed_layers = {"PHYSICAL_PERFORMANCE", "THERMAL_DEMAND_INTERFACE", "WEATHER_INPUT", "OPERATING_CONFIG", "PHYSICAL_OUTPUT", "TEST_FIXTURE"}
    registry_files = {
        "heat_pump_sources.csv": "source_id", "heat_pump_variables.csv": "variable_id",
        "heat_pump_formulas.csv": "formula_id", "heat_pump_scenarios.csv": "scenario_id",
        "heat_pump_readiness.csv": "component_id",
    }
    for filename, id_field in registry_files.items():
        path = REGISTRY / filename
        if not path.is_file():
            continue
        _, rows = read_csv(path)
        duplicates = duplicate_values([row[id_field] for row in rows])
        if duplicates:
            errors.append(f"duplicate B05 IDs in {filename}: {duplicates!r}")
        for row in rows:
            if row["module_id"] != "B05":
                errors.append(f"B05 artifact has non-B05 module in {filename}: {row[id_field]!r}")
            if row.get("layer") not in allowed_layers and filename not in {"heat_pump_formulas.csv", "heat_pump_readiness.csv", "heat_pump_scenarios.csv"}:
                errors.append(f"invalid B05 layer in {filename}: {row[id_field]!r}")
            if filename == "heat_pump_sources.csv" and row["source_id"] not in source_ids:
                errors.append(f"B05 source not mirrored in sources.csv: {row['source_id']!r}")
            if filename in {"heat_pump_variables.csv", "heat_pump_scenarios.csv"} and row.get("status", row.get("weather_status", "")) not in ALLOWED_EVIDENCE_STATUS:
                errors.append(f"invalid B05 evidence status in {filename}: {row[id_field]!r}")
            if filename == "heat_pump_formulas.csv" and row["status"] not in {"DER", "ASS"}:
                errors.append(f"invalid B05 formula status: {row['formula_id']!r}")
            if filename == "heat_pump_readiness.csv" and row["status"] not in {"VALIDATED", "PARTIAL", "BLOCKED", "Q"}:
                errors.append(f"invalid B05 readiness status: {row['component_id']!r}")

    processed = ROOT / "data" / "processed"
    for filename in (
        "heat_pump_performance_points.csv",
        "heat_pump_weather_scenarios.csv",
        "heat_pump_weather_hourly.csv",
        "heat_pump_weather_profiles.csv",
        "heat_pump_weather_coverage.csv",
        "heat_pump_weather_supply_coverage.csv",
    ):
        path = processed / filename
        if not path.is_file():
            continue
        _, rows = read_csv(path)
        for row in rows:
            status = row.get("evidence_status", row.get("status", ""))
            if status not in ALLOWED_EVIDENCE_STATUS:
                errors.append(f"invalid B05 processed status in {filename}: {status!r}")
            raw_refs = row.get("source_ids", "") or row.get("source_id", "")
            refs = [item for item in raw_refs.split(";") if item]
            unknown = [item for item in refs if item not in source_ids]
            if unknown:
                errors.append(f"unknown B05 processed source references in {filename}: {unknown!r}")
            if filename == "heat_pump_performance_points.csv":
                if row.get("unit_boundary") != "total_unit_input":
                    errors.append(f"B05 performance point must use total-unit input: {row['point_id']!r}")
                try:
                    capacity = float(row["thermal_capacity_kW"])
                    electrical = float(row["electrical_input_kW"])
                    cop = float(row["COP"])
                except ValueError:
                    errors.append(f"non-numeric B05 performance point: {row['point_id']!r}")
                else:
                    if capacity < 0 or electrical < 0 or cop <= 0:
                        errors.append(f"invalid physical bounds in B05 point: {row['point_id']!r}")
                    elif abs(capacity / electrical - cop) > 0.05:
                        errors.append(f"inconsistent capacity/input/COP in B05 point: {row['point_id']!r}")
                if status == "OBS" and row.get("source_id") == "SRC-B05-SYNTHETIC-TEST-GRID":
                    errors.append(f"synthetic B05 point cannot be OBS: {row['point_id']!r}")
            if filename == "heat_pump_weather_hourly.csv":
                if row.get("temperature_source_variable") != "ta":
                    errors.append(f"B05 canonical weather must map ta: {row['record_id']!r}")
                if not row.get("timestamp_utc", "").endswith("Z"):
                    errors.append(f"B05 weather timestamp must be UTC Z: {row['record_id']!r}")
                if "-999" in row.get("outdoor_temperature_C", ""):
                    errors.append(f"B05 weather missing sentinel leaked into canonical value: {row['record_id']!r}")
            if filename == "heat_pump_weather_profiles.csv":
                try:
                    completeness = float(row["completeness"])
                except ValueError:
                    errors.append(f"non-numeric B05 weather completeness: {row['weather_profile_id']!r}")
                else:
                    if not 0 <= completeness <= 1:
                        errors.append(f"invalid B05 weather completeness: {row['weather_profile_id']!r}")
            if filename == "heat_pump_weather_coverage.csv":
                try:
                    share = float(row["share_inside_current_performance_domain"])
                except ValueError:
                    if row["hours_total"] != "0":
                        errors.append(f"non-numeric B05 weather domain share: {row['weather_profile_id']!r}")
                else:
                    if not 0 <= share <= 1:
                        errors.append(f"invalid B05 weather domain share: {row['weather_profile_id']!r}")
                try:
                    new_share = float(row["new_share_inside_performance_domain"])
                except ValueError:
                    errors.append(f"non-numeric B05 new weather domain share: {row['weather_profile_id']!r}")
                else:
                    if not 0 <= new_share <= 1:
                        errors.append(f"invalid B05 new weather domain share: {row['weather_profile_id']!r}")
            if filename == "heat_pump_weather_supply_coverage.csv":
                try:
                    total = int(row["weather_hours_total"])
                except ValueError:
                    errors.append(f"non-numeric B05 supply coverage total: {row['weather_profile_id']!r}")
                    continue
                if total < 0:
                    errors.append(f"negative B05 supply coverage total: {row['weather_profile_id']!r}")
                if row.get("status") == "Q":
                    if any(row.get(field, "") for field in ("weather_hours_inside_domain", "weather_hours_below_domain", "weather_hours_above_domain", "coverage_share")):
                        errors.append(f"incomplete B05 supply surface must remain unquantified: {row['equipment_id']!r}/{row['supply_temperature_C']!r}")
                else:
                    try:
                        inside = int(row["weather_hours_inside_domain"])
                        below = int(row["weather_hours_below_domain"])
                        above = int(row["weather_hours_above_domain"])
                        share = float(row["coverage_share"])
                    except ValueError:
                        errors.append(f"non-numeric B05 supply coverage: {row['weather_profile_id']!r}")
                    else:
                        if inside < 0 or below < 0 or above < 0 or inside + below + above != total:
                            errors.append(f"inconsistent B05 supply coverage counts: {row['weather_profile_id']!r}")
                        if not 0 <= share <= 1:
                            errors.append(f"invalid B05 supply coverage share: {row['weather_profile_id']!r}")



def validate() -> list[str]:
    errors: list[str] = []

    for filename, expected in EXPECTED_HEADERS.items():
        path = REGISTRY / filename
        if not path.is_file():
            errors.append(f"missing registry file: {path.relative_to(ROOT)}")
            continue
        headers, _ = read_csv(path)
        if headers != expected:
            errors.append(
                f"invalid headers in {path.relative_to(ROOT)}: expected={expected!r} actual={headers!r}"
            )

    processed = ROOT / "data" / "processed"
    for filename, expected in PROCESSED_EXPECTED_HEADERS.items():
        path = processed / filename
        if not path.is_file():
            errors.append(f"missing processed B03 file: {path.relative_to(ROOT)}")
            continue
        headers, _ = read_csv(path)
        if headers != expected:
            errors.append(
                f"invalid headers in {path.relative_to(ROOT)}: expected={expected!r} actual={headers!r}"
            )

    module_path = REGISTRY / "module_status.csv"
    if not module_path.is_file():
        return errors

    _, rows = read_csv(module_path)
    expected_ids = [f"B{index:02d}" for index in range(1, 21)]
    actual_ids = [row["module_id"] for row in rows]
    if actual_ids != expected_ids:
        errors.append(f"module IDs must be exactly B01-B20 in order: actual={actual_ids!r}")

    known_ids = set(actual_ids)
    for row in rows:
        module_id = row["module_id"]
        if not MODULE_ID_PATTERN.fullmatch(module_id):
            errors.append(f"invalid module ID: {module_id!r}")
        if row["status"] not in ALLOWED_MODULE_STATUS:
            errors.append(f"invalid status for {module_id}: {row['status']!r}")
        try:
            readiness = int(row["readiness_percent"])
        except ValueError:
            errors.append(f"readiness is not an integer for {module_id}")
        else:
            if not 0 <= readiness <= 100:
                errors.append(f"readiness is outside 0-100 for {module_id}: {readiness}")
        dependencies = [item for item in row["depends_on"].split(";") if item]
        unknown = [item for item in dependencies if item not in known_ids]
        if unknown:
            errors.append(f"unknown dependencies for {module_id}: {unknown!r}")
        if module_id in dependencies:
            errors.append(f"self dependency for {module_id}")

    b15 = next((row for row in rows if row["module_id"] == "B15"), None)
    if b15 and set(b15["depends_on"].split(";")) != {"B12", "B13", "B14"}:
        errors.append("B15 must depend exactly on B12, B13, and B14")

    b20 = next((row for row in rows if row["module_id"] == "B20"), None)
    if b20:
        expected_b20 = {f"B{index:02d}" for index in range(1, 20)}
        if set(b20["depends_on"].split(";")) != expected_b20:
            errors.append("B20 must depend on every module from B01 through B19")

    source_path = REGISTRY / "sources.csv"
    source_ids: set[str] = set()
    if source_path.is_file():
        _, source_rows = read_csv(source_path)
        all_source_ids = [row["source_id"] for row in source_rows]
        duplicates = duplicate_values(all_source_ids)
        if duplicates:
            errors.append(f"duplicate source IDs: {duplicates!r}")
        source_ids = set(all_source_ids)

        for row in source_rows:
            source_id = row["source_id"]
            match = SOURCE_ID_PATTERN.fullmatch(source_id)
            if not match:
                errors.append(f"invalid source ID: {source_id!r}")
            elif match.group(1) != row["module_id"]:
                errors.append(f"source/module mismatch: {source_id!r} -> {row['module_id']!r}")
            if row["module_id"] not in known_ids:
                errors.append(f"unknown source module for {source_id}: {row['module_id']!r}")
            for field in (
                "title",
                "institution",
                "url",
                "published_at",
                "retrieved_at",
                "reference_period",
                "source_tier",
                "evidence_status",
                "reliability",
                "license",
                "notes",
            ):
                if not row[field].strip():
                    errors.append(f"missing {field} for source {source_id}")
            if not row["url"].startswith(("https://", "http://")):
                errors.append(f"invalid source URL for {source_id}: {row['url']!r}")
            if row["published_at"] != "undated" and not is_iso_date(row["published_at"]):
                errors.append(f"invalid published_at for {source_id}: {row['published_at']!r}")
            if not is_iso_date(row["retrieved_at"]):
                errors.append(f"invalid retrieved_at for {source_id}: {row['retrieved_at']!r}")
            if row["source_tier"] not in ALLOWED_SOURCE_TIERS:
                errors.append(f"invalid source tier for {source_id}: {row['source_tier']!r}")
            if row["evidence_status"] not in ALLOWED_EVIDENCE_STATUS:
                errors.append(
                    f"invalid source evidence status for {source_id}: {row['evidence_status']!r}"
                )
            if row["reliability"] not in ALLOWED_RELIABILITY:
                errors.append(f"invalid reliability for {source_id}: {row['reliability']!r}")
            snapshot = row["local_snapshot_sha256"]
            if snapshot and not re.fullmatch(r"[0-9a-f]{64}", snapshot):
                errors.append(f"invalid snapshot SHA-256 for {source_id}")

    variable_ids_set: set[str] = set()
    variable_status_by_id: dict[str, str] = {}
    variable_path = REGISTRY / "variables.csv"
    if variable_path.is_file():
        _, variable_rows = read_csv(variable_path)
        variable_ids = [row["variable_id"] for row in variable_rows]
        variable_ids_set = set(variable_ids)
        variable_status_by_id = {row["variable_id"]: row["status"] for row in variable_rows}
        duplicates = duplicate_values(variable_ids)
        if duplicates:
            errors.append(f"duplicate variable IDs: {duplicates!r}")

        for row in variable_rows:
            variable_id = row["variable_id"]
            match = VARIABLE_ID_PATTERN.fullmatch(variable_id)
            if not match:
                errors.append(f"invalid variable ID: {variable_id!r}")
            elif match.group(1) != row["module_id"]:
                errors.append(f"variable/module mismatch: {variable_id!r} -> {row['module_id']!r}")
            if row["module_id"] not in known_ids:
                errors.append(f"unknown variable module for {variable_id}: {row['module_id']!r}")
            for field in ("name", "definition", "unit", "status", "updated_at", "notes"):
                if not row[field].strip():
                    errors.append(f"missing {field} for variable {variable_id}")
            if row["status"] not in ALLOWED_EVIDENCE_STATUS:
                errors.append(f"invalid variable status for {variable_id}: {row['status']!r}")
            if not is_iso_date(row["updated_at"]):
                errors.append(f"invalid updated_at for {variable_id}: {row['updated_at']!r}")
            referenced_sources = [item for item in row["source_ids"].split(";") if item]
            unknown_sources = [item for item in referenced_sources if item not in source_ids]
            if unknown_sources:
                errors.append(f"unknown source references for {variable_id}: {unknown_sources!r}")
            if row["status"] in {"OBS", "DER"} and not referenced_sources:
                errors.append(f"{row['status']} variable has no source for {variable_id}")

    formula_path = REGISTRY / "formulas.csv"
    if formula_path.is_file():
        _, formula_rows = read_csv(formula_path)
        formula_ids = [row["formula_id"] for row in formula_rows]
        duplicates = duplicate_values(formula_ids)
        if duplicates:
            errors.append(f"duplicate formula IDs: {duplicates!r}")

        for row in formula_rows:
            formula_id = row["formula_id"]
            match = FORMULA_ID_PATTERN.fullmatch(formula_id)
            if not match:
                errors.append(f"invalid formula ID: {formula_id!r}")
            elif match.group(1) != row["module_id"]:
                errors.append(f"formula/module mismatch: {formula_id!r} -> {row['module_id']!r}")
            if row["module_id"] not in known_ids:
                errors.append(f"unknown formula module for {formula_id}: {row['module_id']!r}")
            for field in (
                "output_variable_id",
                "expression",
                "input_variable_ids",
                "output_unit",
                "status",
                "notes",
            ):
                if not row[field].strip():
                    errors.append(f"missing {field} for formula {formula_id}")
            if row["output_variable_id"] not in variable_ids_set:
                errors.append(
                    f"unknown output variable for {formula_id}: {row['output_variable_id']!r}"
                )
            inputs = [item for item in row["input_variable_ids"].split(";") if item]
            unknown_inputs = [item for item in inputs if item not in variable_ids_set]
            if unknown_inputs:
                errors.append(f"unknown input variables for {formula_id}: {unknown_inputs!r}")
            if row["status"] not in {"DER", "ASS"}:
                errors.append(f"formula status must be DER or ASS for {formula_id}")
            output_status = variable_status_by_id.get(row["output_variable_id"])
            if output_status and output_status != row["status"]:
                errors.append(
                    f"formula/output status mismatch for {formula_id}: "
                    f"formula={row['status']!r} output={output_status!r}"
                )

    dataset_ids: set[str] = set()
    dataset_path = REGISTRY / "datasets.csv"
    if dataset_path.is_file():
        _, dataset_rows = read_csv(dataset_path)
        all_dataset_ids = [row["dataset_id"] for row in dataset_rows]
        duplicates = duplicate_values(all_dataset_ids)
        if duplicates:
            errors.append(f"duplicate dataset IDs: {duplicates!r}")
        dataset_ids = set(all_dataset_ids)

        for row in dataset_rows:
            dataset_id = row["dataset_id"]
            match = DATASET_ID_PATTERN.fullmatch(dataset_id)
            if not match:
                errors.append(f"invalid dataset ID: {dataset_id!r}")
            elif match.group(1) != row["module_id"]:
                errors.append(f"dataset/module mismatch: {dataset_id!r} -> {row['module_id']!r}")
            if row["module_id"] not in known_ids:
                errors.append(f"unknown dataset module for {dataset_id}: {row['module_id']!r}")
            for field in (
                "title",
                "institution",
                "source_id",
                "access_method",
                "source_version",
                "dataflow_id",
                "metadata_endpoint",
                "data_endpoint",
                "geography_grain",
                "reference_period",
                "dimensions",
                "measure_id",
                "unit",
                "evidence_status",
                "retrieved_at",
                "license",
                "snapshot_policy",
                "raw_storage_path",
                "notes",
            ):
                if not row[field].strip():
                    errors.append(f"missing {field} for dataset {dataset_id}")
            if row["source_id"] not in source_ids:
                errors.append(f"unknown source for dataset {dataset_id}: {row['source_id']!r}")
            if row["access_method"] not in ALLOWED_DATASET_ACCESS_METHODS:
                errors.append(
                    f"invalid access method for dataset {dataset_id}: {row['access_method']!r}"
                )
            if not SOURCE_VERSION_PATTERN.fullmatch(row["source_version"]):
                errors.append(
                    f"invalid source version for dataset {dataset_id}: {row['source_version']!r}"
                )
            if not row["metadata_endpoint"].startswith("https://"):
                errors.append(f"invalid metadata endpoint for dataset {dataset_id}")
            if not row["data_endpoint"].startswith("https://"):
                errors.append(f"invalid data endpoint for dataset {dataset_id}")
            if row["evidence_status"] not in ALLOWED_EVIDENCE_STATUS:
                errors.append(f"invalid evidence status for dataset {dataset_id}")
            if not is_iso_date(row["retrieved_at"]):
                errors.append(f"invalid retrieved_at for dataset {dataset_id}")
            if not row["raw_storage_path"].startswith("data/raw/"):
                errors.append(f"dataset raw path must be under data/raw for {dataset_id}")

    dimension_path = REGISTRY / "archetype_dimensions.csv"
    if dimension_path.is_file():
        _, dimension_rows = read_csv(dimension_path)
        dimension_ids = [row["dimension_id"] for row in dimension_rows]
        duplicates = duplicate_values(dimension_ids)
        if duplicates:
            errors.append(f"duplicate dimension IDs: {duplicates!r}")

        for row in dimension_rows:
            dimension_id = row["dimension_id"]
            match = DIMENSION_ID_PATTERN.fullmatch(dimension_id)
            if not match:
                errors.append(f"invalid dimension ID: {dimension_id!r}")
            elif match.group(1) != row["module_id"]:
                errors.append(f"dimension/module mismatch: {dimension_id!r} -> {row['module_id']!r}")
            if row["module_id"] not in known_ids:
                errors.append(f"unknown dimension module for {dimension_id}: {row['module_id']!r}")
            for field in (
                "name",
                "role",
                "canonical_grain",
                "observability",
                "required",
                "aggregation_rule",
                "unknown_policy",
                "status",
                "notes",
            ):
                if not row[field].strip():
                    errors.append(f"missing {field} for dimension {dimension_id}")
            referenced_datasets = [item for item in row["source_dataset_ids"].split(";") if item]
            unknown_datasets = [item for item in referenced_datasets if item not in dataset_ids]
            if unknown_datasets:
                errors.append(f"unknown dataset references for {dimension_id}: {unknown_datasets!r}")
            if row["status"] == "CONTRACTED" and not referenced_datasets:
                errors.append(f"contracted dimension has no dataset for {dimension_id}")
            if row["role"] not in ALLOWED_DIMENSION_ROLES:
                errors.append(f"invalid role for {dimension_id}: {row['role']!r}")
            if row["observability"] not in ALLOWED_DIMENSION_OBSERVABILITY:
                errors.append(f"invalid observability for {dimension_id}: {row['observability']!r}")
            if row["required"] not in ALLOWED_DIMENSION_REQUIRED:
                errors.append(f"invalid required flag for {dimension_id}: {row['required']!r}")
            if row["status"] not in ALLOWED_DIMENSION_STATUS:
                errors.append(f"invalid dimension status for {dimension_id}: {row['status']!r}")

    question_path = REGISTRY / "open_questions.csv"
    if question_path.is_file():
        _, question_rows = read_csv(question_path)
        question_ids = [row["question_id"] for row in question_rows]
        duplicates = duplicate_values(question_ids)
        if duplicates:
            errors.append(f"duplicate question IDs: {duplicates!r}")

        for row in question_rows:
            question_id = row["question_id"]
            match = QUESTION_ID_PATTERN.fullmatch(question_id)
            if not match:
                errors.append(f"invalid question ID: {question_id!r}")
            elif match.group(1) != row["module_id"]:
                errors.append(f"question/module mismatch: {question_id!r} -> {row['module_id']!r}")
            if row["module_id"] not in known_ids:
                errors.append(f"unknown question module for {question_id}: {row['module_id']!r}")
            for field in ("question", "decision_impact", "evidence_needed", "status", "owner", "notes"):
                if not row[field].strip():
                    errors.append(f"missing {field} for question {question_id}")
            if row["priority"] not in ALLOWED_QUESTION_PRIORITY:
                errors.append(f"invalid priority for {question_id}: {row['priority']!r}")
            if row["status"] not in ALLOWED_QUESTION_STATUS:
                errors.append(f"invalid question status for {question_id}: {row['status']!r}")

    validate_b03_artifacts(errors, source_ids)
    validate_b04_artifacts(errors, source_ids)
    validate_b05_artifacts(errors, source_ids)

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("VALID: registry contracts and B01-B20 dependency gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
