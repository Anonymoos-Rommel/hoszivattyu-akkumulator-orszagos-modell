"""Validate the bootstrap registry contracts using only the Python standard library."""

from __future__ import annotations

import csv
import json
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
        "project_id",
        "asset_type",
        "network_operator",
        "region_id",
        "region_grain",
        "status_taxonomy",
        "scope_description",
        "status_effective_date",
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
    "retrofit_sources.csv": [
        "source_id", "module_id", "layer", "title", "institution", "url",
        "reference_period", "retrieved_at", "source_tier", "evidence_status",
        "license_status", "local_snapshot_status", "notes",
    ],
    "retrofit_variables.csv": [
        "variable_id", "module_id", "layer", "name", "definition", "unit",
        "status", "source_ids", "updated_at", "notes",
    ],
    "retrofit_formulas.csv": [
        "formula_id", "module_id", "layer", "output_variable_id", "expression",
        "input_variable_ids", "output_unit", "status", "notes",
    ],
    "retrofit_interventions.csv": [
        "intervention_id", "module_id", "family", "description", "applicability_gates",
        "annual_effect_basis", "peak_effect_basis", "supply_temperature_effect",
        "capex_interface", "evidence_status", "source_ids", "status", "notes",
    ],
    "retrofit_readiness.csv": [
        "component_id", "module_id", "layer", "status", "readiness_percent",
        "source_ids", "notes",
    ],
    "battery_sources.csv": [
        "source_id", "module_id", "layer", "title", "institution", "url",
        "published_at", "retrieved_at", "source_tier", "evidence_status",
        "reliability", "license", "notes",
    ],
    "battery_products.csv": [
        "product_id", "module_id", "manufacturer", "model", "chemistry",
        "nominal_capacity_kwh", "usable_capacity_kwh", "usable_capacity_status",
        "max_charge_power_kw", "max_discharge_power_kw", "efficiency_value",
        "efficiency_type", "efficiency_status", "charge_efficiency_value",
        "charge_efficiency_status", "discharge_efficiency_value",
        "discharge_efficiency_status", "round_trip_efficiency_value",
        "round_trip_efficiency_status", "efficiency_boundary", "operating_temp_min_c",
        "operating_temp_max_c", "capacity_boundary", "power_boundary",
        "inverter_relationship", "warranty_years", "warranty_cycles",
        "warranty_retention_pct", "origin_status", "status", "source_ids", "notes",
    ],
    "battery_variables.csv": [
        "variable_id", "module_id", "layer", "name", "definition", "unit",
        "status", "source_ids", "notes",
    ],
    "battery_formulas.csv": [
        "formula_id", "module_id", "layer", "output_variable_id", "expression",
        "input_variable_ids", "output_unit", "status", "notes",
    ],
    "battery_readiness.csv": [
        "component_id", "module_id", "layer", "status", "readiness_percent",
        "source_ids", "notes",
    ],
    "b08_variables.csv": [
        "variable_id", "module_id", "layer", "name", "definition", "unit",
        "status", "source_ids", "notes",
    ],
    "b08_formulas.csv": [
        "formula_id", "module_id", "layer", "output_variable_id", "expression",
        "input_variable_ids", "output_unit", "status", "notes",
    ],
    "b08_readiness.csv": [
        "component_id", "module_id", "layer", "status", "readiness_percent",
        "source_ids", "notes",
    ],
    "b09_variables.csv": [
        "variable_id", "module_id", "layer", "name", "definition", "unit",
        "status", "source_ids", "notes",
    ],
    "b09_formulas.csv": [
        "formula_id", "module_id", "layer", "output_variable_id", "expression",
        "input_variable_ids", "output_unit", "status", "notes",
    ],
    "b09_readiness.csv": [
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
    "retrofit_effect_evidence.csv": [
        "evidence_id", "intervention_id", "intervention_family", "geography",
        "building_type", "construction_period", "area_m2", "study_year",
        "study_type", "evidence_class", "annual_before_kwh_m2a",
        "annual_after_kwh_m2a", "annual_before_min_kwh_m2a",
        "annual_before_max_kwh_m2a", "annual_after_min_kwh_m2a",
        "annual_after_max_kwh_m2a", "annual_reduction_fraction",
        "annual_reduction_min", "annual_reduction_max", "peak_before_kw",
        "peak_after_kw", "peak_reduction_fraction", "weather_normalization",
        "dhw_separation", "occupancy_control", "applicability_status",
        "usable_for_engine", "status", "source_id", "notes",
    ],
    "retrofit_peak_design_evidence.csv": [
        "record_id", "archetype_or_building_id", "location_or_climate_zone",
        "design_outdoor_temperature_c", "design_indoor_temperature_c", "component",
        "u_value_w_m2k", "area_m2", "boundary", "correction_factor",
        "thermal_bridge_h_w_per_k", "ventilation_volume_m3", "ventilation_air_change_rate_h",
        "ventilation_airflow_m3_h", "heat_recovery_efficiency",
        "air_volumetric_heat_capacity_wh_m3k", "baseline_design_heat_load_kw",
        "post_design_heat_load_kw", "peak_reduction_kw", "peak_reduction_fraction",
        "method_id", "source_ids", "evidence_status", "provenance", "limitations",
    ],
    "emitter_performance_evidence.csv": [
        "emitter_id", "manufacturer", "model_type", "emitter_type", "height_mm", "length_mm",
        "quantity", "nominal_output_kw", "nominal_flow_temperature_c",
        "nominal_return_temperature_c", "nominal_room_temperature_c", "nominal_delta_t_k",
        "temperature_exponent_n", "correction_method", "source_id", "status", "retrieval_date",
        "limitations",
    ],
    "emitter_supply_temperature_results.csv": [
        "case_id", "design_load_kw", "emitter_id", "emitter_quantity", "room_temp_c",
        "flow_temp_c", "return_temp_c", "mean_water_temp_c", "delta_t_mean_k",
        "available_emitter_output_kw", "required_supply_temperature_c",
        "design_outdoor_temperature_c", "dhw_required_kw", "scenario_role", "b05_equipment_id",
        "b05_available_capacity_kw", "b05_electrical_input_kw", "b05_cop",
        "b05_capacity_shortfall_kw", "status", "source_ids", "notes",
    ],
    "battery_product_evidence.csv": [
        "product_id", "manufacturer", "model", "chemistry", "nominal_capacity_kwh",
        "usable_capacity_kwh", "usable_capacity_status", "max_charge_power_kw",
        "max_discharge_power_kw", "peak_power_kw", "efficiency_value", "efficiency_type",
        "efficiency_status", "charge_efficiency_value", "charge_efficiency_status",
        "discharge_efficiency_value", "discharge_efficiency_status",
        "round_trip_efficiency_value", "round_trip_efficiency_status", "efficiency_boundary",
        "operating_temp_min_c", "operating_temp_max_c",
        "capacity_boundary", "power_boundary", "inverter_relationship", "warranty_years",
        "warranty_cycles", "warranty_retention_pct", "origin_claim", "origin_status",
        "source_ids", "retrieved_at", "status", "limitations",
    ],
    "battery_physical_fixture_results.csv": [
        "case_id", "step_index", "timestep_hours", "requested_charge_kw",
        "requested_discharge_kw", "actual_charge_kw", "actual_discharge_kw",
        "soc_before_kwh", "soc_after_kwh", "charge_curtailed_kwh",
        "discharge_unserved_kwh", "grid_import_kw", "grid_export_kw",
        "physical_up_flex_kw", "physical_down_flex_kw", "status", "source_ids", "notes",
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
ALLOWED_DATASET_ACCESS_METHODS = {"KSH_CENSUS_API", "EMBEDDED_HTML", "PDF_TABLE", "CSV_CURATED"}

MODULE_ID_PATTERN = re.compile(r"B(?:0[1-9]|1[0-9]|20)")
SOURCE_ID_PATTERN = re.compile(r"SRC-(B(?:0[1-9]|1[0-9]|20))-[A-Z0-9-]+")
VARIABLE_ID_PATTERN = re.compile(r"VAR-(B(?:0[1-9]|1[0-9]|20))-[A-Z0-9-]+")
QUESTION_ID_PATTERN = re.compile(r"Q-(B(?:0[1-9]|1[0-9]|20))-\d{3}")
DATASET_ID_PATTERN = re.compile(r"DATA-(B(?:0[1-9]|1[0-9]|20))-[A-Z0-9-]+")
DIMENSION_ID_PATTERN = re.compile(r"DIM-(B(?:0[1-9]|1[0-9]|20))-[A-Z0-9-]+")
SOURCE_VERSION_PATTERN = re.compile(r"(?:V\d+|Y\d{4}|\d{4}-\d{2}-\d{2})")
FORMULA_ID_PATTERN = re.compile(r"FORM-(B(?:0[1-9]|1[0-9]|20))-[A-Z0-9-]+")


def validate_b10_artifacts(errors: list[str], source_ids: set[str]) -> None:
    """Validate B10-P3/P4 truth plus the B10-P5 fail-closed registry boundary."""
    module_path = REGISTRY / "module_status.csv"
    if module_path.is_file():
        _, module_rows = read_csv(module_path)
        b10 = next((row for row in module_rows if row.get("module_id") == "B10"), None)
        if b10 is None:
            errors.append("missing B10 module status row")
        else:
            if b10.get("readiness_percent") != "15":
                errors.append("B10-P5 must preserve readiness at 15")
            if any(name not in b10.get("gate_note", "") for name in ("B10-P3", "B10-P4", "B10-P5")):
                errors.append("B10 module gate note must name B10-P3, B10-P4 and B10-P5")

    baseline_path = REGISTRY / "baseline_infrastructure.csv"
    if not baseline_path.is_file():
        errors.append("missing B10 registry file: baseline_infrastructure.csv")
        baseline_rows: list[dict[str, str]] = []
    else:
        _, baseline_rows = read_csv(baseline_path)

    expected_projects = {
        "RRF-6.1.1-21-2022-00006": {
            "baseline_id": "B10-BASE-MVM-DEMASZ-RRF-6.1.1-21-2022-00006",
            "region_id": "MVM_DEMASZ:SERVICE_AREA",
            "project_source": "SRC-B10-MVM-DEMASZ-RRF-PROJECT-2026",
            "completion_source": "SRC-B10-MVM-DEMASZ-RRF-COMPLETION-2026",
            "cost": "",
        },
        "RRF-6.1.1-21-2022-00001": {
            "baseline_id": "B10-BASE-OPUS-TITASZ-RRF-6.1.1-21-2022-00001",
            "region_id": "OPUS_TITASZ:SERVICE_AREA",
            "project_source": "SRC-B10-OPUS-TITASZ-RRF-PROJECT-2026",
            "completion_source": "SRC-B10-OPUS-TITASZ-RRF-COMPLETION-2026",
            "cost": "41489280000",
        },
    }
    seen_baselines: set[str] = set()
    seen_projects: set[str] = set()
    for row in baseline_rows:
        baseline_id = row.get("baseline_id", "")
        project_id = row.get("project_id", "")
        if not baseline_id or baseline_id in seen_baselines:
            errors.append(f"duplicate or missing B10 baseline_id: {baseline_id!r}")
        seen_baselines.add(baseline_id)
        if not project_id or project_id in seen_projects:
            errors.append(f"duplicate or missing B10 project_id: {project_id!r}")
        seen_projects.add(project_id)
        expected = expected_projects.get(project_id)
        if expected is None:
            errors.append(f"unexpected B10-P4 project identity: {project_id!r}")
            continue
        for field in ("asset_type", "network_operator", "region_id", "region_grain", "status_taxonomy", "scope_description", "status_effective_date", "source_ids", "evidence_status", "status", "notes"):
            if not row.get(field, "").strip():
                errors.append(f"missing {field} for B10 baseline {project_id}")
        if baseline_id != expected["baseline_id"]:
            errors.append(f"baseline identity mismatch for {project_id}: {baseline_id!r}")
        if row.get("asset_type") != "MULTI_ASSET_DSO_NETWORK_DEVELOPMENT_PROGRAM":
            errors.append(f"invalid B10-P4 asset type for {project_id}")
        if row.get("region_grain") != "DSO_SERVICE_AREA" or row.get("region_id") != expected["region_id"]:
            errors.append(f"B10-P4 row must remain at its canonical DSO_SERVICE_AREA grain: {project_id}")
        if row.get("region_grain") == "DSO_SUBSTATION" or row.get("region_id") == "NATIONAL":
            errors.append(f"B10-P4 row has forbidden headroom/national grain: {project_id}")
        if row.get("status_taxonomy") != "OPERATING" or row.get("status_effective_date") != "2026-06-15":
            errors.append(f"B10-P4 row must be OPERATING effective 2026-06-15: {project_id}")
        if row.get("evidence_status") != "OBS" or row.get("status") != "BASELINE":
            errors.append(f"B10-P4 row must be OBS BASELINE: {project_id}")
        refs = tuple(item for item in row.get("source_ids", "").split(";") if item)
        expected_refs = (expected["project_source"], expected["completion_source"])
        if refs != expected_refs:
            errors.append(f"B10-P4 row must bind project/funding and completion authorities: {project_id}")
        if expected["completion_source"] not in refs:
            errors.append(f"B10-P4 OPERATING requires exact completion authority: {project_id}")
        for field in ("counterfactual_cost_huf", "program_incremental_cost_huf"):
            value = row.get(field, "")
            if value:
                try:
                    numeric = float(value)
                except ValueError:
                    errors.append(f"invalid numeric {field} for B10 baseline {project_id}")
                else:
                    if numeric < 0 or numeric != numeric or numeric in (float("inf"), float("-inf")):
                        errors.append(f"negative/non-finite {field} for B10 baseline {project_id}")
        if row.get("counterfactual_cost_huf", "") != expected["cost"]:
            errors.append(f"cost verdict mismatch for B10 baseline {project_id}")
        if row.get("counterfactual_cost_huf", "") and expected["project_source"] not in refs:
            errors.append(f"exact B10-P4 cost requires its project/funding source: {project_id}")
        if row.get("program_incremental_cost_huf", ""):
            errors.append(f"B10-P4 cannot publish programme-incremental CAPEX: {project_id}")

    if set(seen_projects) != set(expected_projects):
        errors.append(f"B10-P4 must contain exactly the two bounded RRF projects: {sorted(seen_projects)!r}")

    incremental_path = REGISTRY / "incremental_capex_attribution.csv"
    if not incremental_path.is_file():
        errors.append("missing B10 registry file: incremental_capex_attribution.csv")
    else:
        _, incremental_rows = read_csv(incremental_path)
        if incremental_rows:
            errors.append("B10-P5 incremental_capex_attribution.csv must remain header-only")

    for filename in ("regional_readiness.csv",):
        path = REGISTRY / filename
        if path.is_file():
            _, rows = read_csv(path)
            for row in rows:
                if row.get("region_type") == "NATIONAL":
                    errors.append("B10-P5 cannot publish national regional_readiness")
                if row.get("evidence_status") not in ALLOWED_EVIDENCE_STATUS:
                    errors.append(f"invalid B10 readiness evidence status: {row.get('region_id')!r}")

    # Keep the source registry as the sole source identity authority.
    _, source_rows = read_csv(REGISTRY / "sources.csv") if (REGISTRY / "sources.csv").is_file() else ([], [])
    b10_source_ids = {row.get("source_id") for row in source_rows if row.get("module_id") == "B10"}
    if not b10_source_ids:
        errors.append("B10 requires at least one source-audit entry")
    for source_id in b10_source_ids:
        if source_id not in source_ids:
            errors.append(f"B10 source not present in source authority set: {source_id!r}")
    required_p4_sources = {
        "SRC-B10-MVM-DEMASZ-RRF-PROJECT-2026",
        "SRC-B10-MVM-DEMASZ-RRF-COMPLETION-2026",
        "SRC-B10-OPUS-TITASZ-RRF-PROJECT-2026",
        "SRC-B10-OPUS-TITASZ-RRF-COMPLETION-2026",
    }
    for source_id in required_p4_sources:
        row = next((item for item in source_rows if item.get("source_id") == source_id), None)
        if row is None:
            errors.append(f"missing required B10-P4 source authority: {source_id}")
        elif row.get("evidence_status") != "OBS":
            errors.append(f"B10-P4 source authority must be OBS: {source_id}")
    required_p5_source = "SRC-B10-MVM-DEMASZ-NETWORK-BUILD-MGT-2026"
    p5_source = next((item for item in source_rows if item.get("source_id") == required_p5_source), None)
    if p5_source is None:
        errors.append(f"missing required B10-P5 process authority: {required_p5_source}")
    elif p5_source.get("evidence_status") != "OBS":
        errors.append("B10-P5 MVM process authority must remain source-native OBS")



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


def validate_b01_artifacts(errors: list[str]) -> None:
    """Validate the single canonical B01 state/portfolio contract and SCN fixture."""
    model_path = REGISTRY / "household_state_model.json"
    if not model_path.is_file():
        errors.append("missing B01 household state model")
        return
    try:
        model = json.loads(model_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid B01 household state model JSON: {exc}")
        return
    state_ids = [row.get("state_id") for row in model.get("states", [])]
    if state_ids != ["S0", "S1", "S2", "S3", "S4", "S5"]:
        errors.append(f"invalid B01 state order: {state_ids!r}")
    record_schema = model.get("household_record_schema", {})
    required_record_fields = {
        "household_id", "archetype_id", "region_id", "current_state", "evidence_refs",
        "state_as_of", "owner", "next_gate", "blocked_reason", "eligibility_status",
        "eligibility_evidence_status", "truth_context",
    }
    if set(record_schema.get("required", [])) != required_record_fields:
        errors.append("B01 household record schema is missing required fields")
    if set(record_schema.get("truth_contexts", [])) != {"REAL", "SCN"}:
        errors.append("B01 household record truth_context contract is incomplete")
    if not model.get("transition_gate_semantics"):
        errors.append("B01 transition gate semantics are missing")
    transitions = model.get("transition_contract", [])
    transition_ids = [row.get("transition_id") for row in transitions]
    if transition_ids != ["S0_TO_S1", "S1_TO_S2", "S2_TO_S3", "S3_TO_S4", "S4_TO_S5"]:
        errors.append(f"invalid B01 transition contract order: {transition_ids!r}")
    state_exit_gates = {
        row.get("state_id"): row.get("exit_gate")
        for row in model.get("states", [])
    }
    for transition in transitions:
        source_exit_gate = state_exit_gates.get(transition.get("from_state"))
        target_completion_gate = state_exit_gates.get(transition.get("to_state"))
        if (
            not transition.get("required_gates")
            or set(transition.get("allowed_completion_status", [])) != {"OBS", "DER"}
            or transition.get("source_exit_gate") != source_exit_gate
            or transition.get("target_completion_gate") != target_completion_gate
            or transition.get("required_gates") != [source_exit_gate, target_completion_gate]
        ):
            errors.append(f"B01 transition is not fail-closed: {transition.get('transition_id')!r}")
    expected_components = {
        "SOCIAL_NEED", "ENERGY_WASTE", "HOUSEHOLD_GAIN", "PUBLIC_EFFICIENCY",
        "FISCAL_EFFECT", "SYSTEM_VALUE", "ENV_HEALTH", "READINESS", "REGIONAL_EQUITY",
    }
    portfolio = model.get("portfolio_contract", {})
    if set(portfolio.get("components", [])) != expected_components:
        errors.append("B01 portfolio component contract is incomplete")
    if portfolio.get("missing_value_policy") != "FAIL_CLOSED":
        errors.append("B01 portfolio missing-value policy is not FAIL_CLOSED")
    if set(portfolio.get("policy_parameter_statuses", [])) != {"POL", "SCN"}:
        errors.append("B01 policy parameter statuses must be POL or SCN")
    expected_constraints = {
        "public_money", "household_cashflow_floor", "installer_FTE", "supplier_capacity",
        "permitting_capacity", "grid_headroom", "regional_minimum", "debt_headroom",
    }
    if set(model.get("capacity_constraint_contract", {}).get("constraints", [])) != expected_constraints:
        errors.append("B01 capacity constraint contract is incomplete")

    fixture_path = ROOT / "data" / "fixtures" / "b01_state_stock_scn.json"
    if not fixture_path.is_file():
        errors.append("missing B01 SCN fixture")
        return
    try:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid B01 SCN fixture JSON: {exc}")
        return
    if fixture.get("status") != "SCN":
        errors.append("B01 fixture must remain SCN")
    if fixture.get("truth_context") != "SCN":
        errors.append("B01 fixture truth_context must remain SCN")
    if not isinstance(fixture.get("plan_year"), int):
        errors.append("B01 fixture must expose an explicit plan_year")
    if fixture.get("dataset_license") != "CC BY-SA 4.0":
        errors.append("B01 fixture is missing its dataset-level license")
    if not fixture.get("households") or not fixture.get("candidates") or not fixture.get("constraints"):
        errors.append("B01 fixture must contain households, candidates, and explicit constraints")
    for household in fixture.get("households", []):
        if household.get("truth_context") != "SCN":
            errors.append(f"B01 SCN household is not SCN truth: {household.get('household_id')!r}")
        if household.get("eligibility_evidence_status") not in {"SCN", "Q"}:
            errors.append(f"B01 SCN household has non-SCN eligibility evidence: {household.get('household_id')!r}")
        for evidence in household.get("transition_evidence", []):
            if evidence.get("truth_context") != "SCN" or evidence.get("status") != "SCN":
                errors.append(f"B01 SCN transition evidence is not SCN: {household.get('household_id')!r}")
    transition_by_states = {
        (row.get("from_state"), row.get("to_state")): row
        for row in transitions
    }
    for candidate in fixture.get("candidates", []):
        transition = transition_by_states.get((candidate.get("from_state"), candidate.get("target_state")))
        if transition is None or candidate.get("required_gate") != transition.get("target_completion_gate"):
            errors.append(f"B01 candidate gate is not canonical: {candidate.get('intervention_id')!r}")
        gate_status = candidate.get("required_gate_status")
        refs = candidate.get("required_gate_evidence_refs", [])
        if candidate.get("truth_context") != "SCN" or gate_status not in {"SCN", "Q"}:
            errors.append(f"B01 SCN candidate is not SCN truth: {candidate.get('intervention_id')!r}")
        if (gate_status == "Q" and refs) or (gate_status == "SCN" and not refs):
            errors.append(f"B01 SCN candidate gate evidence mismatch: {candidate.get('intervention_id')!r}")


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



def validate_b06_artifacts(errors: list[str], source_ids: set[str]) -> None:
    """Validate B06 physical retrofit contract registries."""
    allowed_layers = {
        "BASELINE_DEMAND", "ENVELOPE_PHYSICS", "SUPPLY_TEMPERATURE_EFFECT",
        "THERMAL_DEMAND_INTERFACE", "RETROFIT_INTERVENTION", "PHYSICAL_OUTPUT",
        "STATE_GATE", "B05_HANDOFF", "PHYSICAL_CONTRACT", "PEAK_LOAD_METHOD", "EMITTER_EVIDENCE",
    }
    registry_files = {
        "retrofit_sources.csv": "source_id",
        "retrofit_variables.csv": "variable_id",
        "retrofit_formulas.csv": "formula_id",
        "retrofit_interventions.csv": "intervention_id",
        "retrofit_readiness.csv": "component_id",
    }
    variable_ids: set[str] = set()
    intervention_ids: set[str] = set()
    for filename, id_field in registry_files.items():
        path = REGISTRY / filename
        if not path.is_file():
            continue
        _, rows = read_csv(path)
        duplicates = duplicate_values([row[id_field] for row in rows])
        if duplicates:
            errors.append(f"duplicate B06 IDs in {filename}: {duplicates!r}")
        if filename == "retrofit_variables.csv":
            variable_ids = {row["variable_id"] for row in rows}
        if filename == "retrofit_interventions.csv":
            intervention_ids = {row["intervention_id"] for row in rows}
        for row in rows:
            if row["module_id"] != "B06":
                errors.append(f"B06 artifact has non-B06 module in {filename}: {row[id_field]!r}")
            if filename in {"retrofit_sources.csv", "retrofit_variables.csv", "retrofit_formulas.csv", "retrofit_readiness.csv"} and row.get("layer") not in allowed_layers:
                errors.append(f"invalid B06 layer in {filename}: {row[id_field]!r}")
            if filename == "retrofit_sources.csv" and row["source_id"] not in source_ids:
                errors.append(f"B06 source not mirrored in sources.csv: {row['source_id']!r}")
            if filename in {"retrofit_variables.csv", "retrofit_interventions.csv"}:
                if row.get("status", "") not in ALLOWED_EVIDENCE_STATUS:
                    errors.append(f"invalid B06 evidence status in {filename}: {row[id_field]!r}")
                refs = [item for item in row.get("source_ids", "").split(";") if item]
                unknown = [item for item in refs if item not in source_ids]
                if unknown:
                    errors.append(f"unknown B06 source references in {filename}: {unknown!r}")
            if filename == "retrofit_formulas.csv" and row["status"] not in {"DER", "ASS"}:
                errors.append(f"invalid B06 formula status: {row['formula_id']!r}")
            if filename == "retrofit_readiness.csv":
                if row["status"] not in {"VALIDATED", "PARTIAL", "BLOCKED", "Q"}:
                    errors.append(f"invalid B06 readiness status: {row['component_id']!r}")
                try:
                    readiness = int(row["readiness_percent"])
                except ValueError:
                    errors.append(f"non-numeric B06 readiness: {row['component_id']!r}")
                else:
                    if not 0 <= readiness <= 100:
                        errors.append(f"invalid B06 readiness percent: {row['component_id']!r}")
    formula_path = REGISTRY / "retrofit_formulas.csv"
    if formula_path.is_file():
        _, formula_rows = read_csv(formula_path)
        for row in formula_rows:
            if row["output_variable_id"] not in variable_ids:
                errors.append(f"unknown B06 formula output: {row['formula_id']!r}")
            unknown_inputs = [item for item in row["input_variable_ids"].split(";") if item and item not in variable_ids]
            if unknown_inputs:
                errors.append(f"unknown B06 formula inputs for {row['formula_id']!r}: {unknown_inputs!r}")

    effect_path = ROOT / "data" / "processed" / "retrofit_effect_evidence.csv"
    if not effect_path.is_file():
        return
    _, effect_rows = read_csv(effect_path)
    allowed_classes = {
        "MEASURED_BEFORE_AFTER", "MODELLED_BEFORE_AFTER", "STANDARD_CALCULATION",
        "ARCHETYPE_ESTIMATE", "POLICY_TARGET",
    }
    numeric_fields = {
        "annual_before_kwh_m2a", "annual_after_kwh_m2a",
        "annual_before_min_kwh_m2a", "annual_before_max_kwh_m2a",
        "annual_after_min_kwh_m2a", "annual_after_max_kwh_m2a",
        "annual_reduction_fraction", "annual_reduction_min", "annual_reduction_max",
        "peak_before_kw", "peak_after_kw", "peak_reduction_fraction",
    }

    def as_float(row: dict[str, str], field: str) -> float | None:
        value = row.get(field, "").strip()
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            errors.append(f"non-numeric B06 effect evidence {field}: {row.get('evidence_id')!r}")
            return None

    for row in effect_rows:
        evidence_id = row["evidence_id"]
        if not evidence_id.startswith("B06-"):
            errors.append(f"invalid B06 effect evidence ID: {evidence_id!r}")
        if row["intervention_id"] not in intervention_ids:
            errors.append(f"unknown B06 effect intervention: {evidence_id!r}")
        if row["evidence_class"] not in allowed_classes:
            errors.append(f"invalid B06 effect evidence class: {evidence_id!r}")
        if row["status"] not in ALLOWED_EVIDENCE_STATUS:
            errors.append(f"invalid B06 effect evidence status: {evidence_id!r}")
        if row["source_id"] not in source_ids:
            errors.append(f"unknown B06 effect evidence source: {evidence_id!r}")
        for field in numeric_fields:
            as_float(row, field)

        before = as_float(row, "annual_before_kwh_m2a")
        after = as_float(row, "annual_after_kwh_m2a")
        reduction = as_float(row, "annual_reduction_fraction")
        if before is not None and after is not None:
            if before <= 0 or after < 0:
                errors.append(f"invalid B06 annual effect values: {evidence_id!r}")
            if reduction is not None and abs(reduction - (before - after) / before) > 0.02:
                errors.append(f"annual reduction does not match before/after values: {evidence_id!r}")
        if reduction is not None and not 0 <= reduction <= 1:
            errors.append(f"annual reduction outside 0-1: {evidence_id!r}")
        annual_min = as_float(row, "annual_reduction_min")
        annual_max = as_float(row, "annual_reduction_max")
        if annual_min is not None and annual_max is not None:
            if not (0 <= annual_min <= annual_max <= 1):
                errors.append(f"invalid B06 annual reduction range: {evidence_id!r}")
            if reduction is not None and not annual_min <= reduction <= annual_max:
                errors.append(f"annual reduction outside stored range: {evidence_id!r}")

        peak_before = as_float(row, "peak_before_kw")
        peak_after = as_float(row, "peak_after_kw")
        peak_reduction = as_float(row, "peak_reduction_fraction")
        if (peak_before is None) != (peak_after is None):
            errors.append(f"peak before/after must be paired: {evidence_id!r}")
        if peak_before is not None and peak_after is not None:
            if peak_before <= 0 or peak_after < 0:
                errors.append(f"invalid B06 peak effect values: {evidence_id!r}")
            if peak_reduction is not None and abs(peak_reduction - (peak_before - peak_after) / peak_before) > 0.02:
                errors.append(f"peak reduction does not match before/after values: {evidence_id!r}")
        if peak_reduction is not None and not 0 <= peak_reduction <= 1:
            errors.append(f"peak reduction outside 0-1: {evidence_id!r}")
        if row["status"] == "OBS" and row["weather_normalization"] in {"", "NOT_NORMALIZED", "NOT_DISCLOSED"}:
            errors.append(f"weather-un-normalized B06 evidence cannot be OBS: {evidence_id!r}")
        if row["dhw_separation"] == "INCLUDED_NOT_SEPARABLE" and row["status"] != "Q":
            errors.append(f"DHW-contaminated B06 evidence must remain Q: {evidence_id!r}")
        if row["usable_for_engine"] == "YES" and row["status"] not in {"OBS", "DER", "ASS"}:
            errors.append(f"only evidence-backed B06 rows can be engine-usable: {evidence_id!r}")


def _validate_product_efficiency_fields(errors: list[str], row: dict[str, str], context: str) -> None:
    """Keep direction-specific product efficiencies explicit and fail-closed."""
    for field in (
        "charge_efficiency",
        "discharge_efficiency",
        "round_trip_efficiency",
    ):
        value = row.get(f"{field}_value", "")
        status = row.get(f"{field}_status", "")
        if status not in ALLOWED_EVIDENCE_STATUS:
            errors.append(f"invalid {field} status in {context}")
        if status == "OBS" and not value:
            errors.append(f"OBS {field} requires a value in {context}")
        if value:
            try:
                numeric = float(value)
            except ValueError:
                errors.append(f"non-numeric {field} value in {context}")
            else:
                if not 0 < numeric <= 1:
                    errors.append(f"invalid {field} range in {context}")
    if not row.get("efficiency_boundary", ""):
        errors.append(f"missing efficiency boundary in {context}")


def validate_b07_source_rows(
    errors: list[str], headers: list[str], rows: list[dict[str, str | list[str] | None]]
) -> None:
    """Reject malformed B07 source rows before field-level checks can pass them through."""
    expected = EXPECTED_HEADERS["battery_sources.csv"]
    if headers != expected:
        return
    for row_number, row in enumerate(rows, start=2):
        extra = row.get(None)
        if extra is not None:
            errors.append(f"misaligned CSV row in registry/battery_sources.csv:{row_number}: extra fields")
        missing = [field for field in expected if not str(row.get(field) or "").strip()]
        if missing:
            errors.append(
                f"missing required B07 source fields in registry/battery_sources.csv:{row_number}: {missing!r}"
            )
        reliability = row.get("reliability")
        if reliability not in ALLOWED_RELIABILITY:
            errors.append(f"invalid B07 source reliability at row {row_number}: {reliability!r}")


def validate_b07_artifacts(errors: list[str], source_ids: set[str]) -> None:
    """Validate B07 battery physical evidence and fail-closed policy edges."""
    allowed_layers = {
        "BATTERY_PHYSICAL_CONTRACT", "SOC_STATE_ENGINE", "POWER_ENERGY_LIMITS",
        "EFFICIENCY_BOUNDARY", "PRODUCT_EVIDENCE", "DEGRADATION_MODEL",
        "TEMPERATURE_ENVELOPE", "HOUSEHOLD_POWER_BALANCE", "PHYSICAL_FLEXIBILITY",
        "B04_TARIFF_INTERFACE", "VPP_LEGAL_MARKET_INTERFACE", "B08_HANDOFF",
        "PRODUCT_ORIGIN", "TEST_FIXTURE",
    }
    registry_files = {
        "battery_sources.csv": "source_id", "battery_products.csv": "product_id",
        "battery_variables.csv": "variable_id", "battery_formulas.csv": "formula_id",
        "battery_readiness.csv": "component_id",
    }
    variable_ids: set[str] = set()
    for filename, id_field in registry_files.items():
        path = REGISTRY / filename
        if not path.is_file():
            continue
        headers, rows = read_csv(path)
        if filename == "battery_sources.csv":
            validate_b07_source_rows(errors, headers, rows)
        duplicates = duplicate_values([row[id_field] for row in rows])
        if duplicates:
            errors.append(f"duplicate B07 IDs in {filename}: {duplicates!r}")
        if filename == "battery_variables.csv":
            variable_ids = {row["variable_id"] for row in rows}
        for row in rows:
            if row["module_id"] != "B07":
                errors.append(f"B07 artifact has non-B07 module in {filename}: {row[id_field]!r}")
            if filename != "battery_products.csv" and row.get("layer") not in allowed_layers:
                errors.append(f"invalid B07 layer in {filename}: {row[id_field]!r}")
            if filename == "battery_sources.csv" and row["source_id"] not in source_ids:
                errors.append(f"B07 source not mirrored in sources.csv: {row['source_id']!r}")
            if filename in {"battery_variables.csv", "battery_products.csv"}:
                if row.get("status", "") not in ALLOWED_EVIDENCE_STATUS | {"PARTIAL"}:
                    errors.append(f"invalid B07 evidence status in {filename}: {row[id_field]!r}")
                refs = [item for item in row.get("source_ids", "").split(";") if item]
                unknown = [item for item in refs if item not in source_ids and item not in variable_ids]
                if unknown:
                    errors.append(f"unknown B07 source references in {filename}: {unknown!r}")
            if filename == "battery_products.csv":
                _validate_product_efficiency_fields(errors, row, f"{filename}:{row[id_field]}")
            if filename == "battery_formulas.csv" and row["status"] not in {"DER", "ASS"}:
                errors.append(f"invalid B07 formula status: {row['formula_id']!r}")
            if filename == "battery_readiness.csv":
                if row["status"] not in {"VALIDATED", "PARTIAL", "BLOCKED", "Q"}:
                    errors.append(f"invalid B07 readiness status: {row['component_id']!r}")
                try:
                    readiness = int(row["readiness_percent"])
                except ValueError:
                    errors.append(f"non-numeric B07 readiness: {row['component_id']!r}")
                else:
                    if not 0 <= readiness <= 100:
                        errors.append(f"invalid B07 readiness percent: {row['component_id']!r}")
    formula_path = REGISTRY / "battery_formulas.csv"
    if formula_path.is_file():
        _, formula_rows = read_csv(formula_path)
        for row in formula_rows:
            if row["output_variable_id"] not in variable_ids:
                errors.append(f"unknown B07 formula output: {row['formula_id']!r}")
            unknown_inputs = [item for item in row["input_variable_ids"].split(";") if item and item not in variable_ids]
            if unknown_inputs:
                errors.append(f"unknown B07 formula inputs for {row['formula_id']!r}: {unknown_inputs!r}")
    products_path = REGISTRY / "battery_products.csv"
    if products_path.is_file():
        _, product_rows = read_csv(products_path)
        for row in product_rows:
            if row["origin_status"] != "OBS":
                errors.append(f"EU-first B07 product origin must be explicit OBS: {row['product_id']!r}")
            try:
                nominal = float(row["nominal_capacity_kwh"])
                charge = float(row["max_charge_power_kw"])
                discharge = float(row["max_discharge_power_kw"])
            except ValueError:
                errors.append(f"non-numeric B07 product physical field: {row['product_id']!r}")
                continue
            if nominal <= 0 or charge < 0 or discharge < 0:
                errors.append(f"invalid B07 product physical bounds: {row['product_id']!r}")
            if row["usable_capacity_kwh"]:
                try:
                    usable = float(row["usable_capacity_kwh"])
                except ValueError:
                    errors.append(f"non-numeric B07 usable capacity: {row['product_id']!r}")
                else:
                    if usable <= 0 or usable > nominal:
                        errors.append(f"invalid B07 usable capacity: {row['product_id']!r}")
    processed = ROOT / "data" / "processed"
    for filename in ("battery_product_evidence.csv", "battery_physical_fixture_results.csv"):
        path = processed / filename
        if not path.is_file():
            continue
        _, rows = read_csv(path)
        for row in rows:
            if row.get("status") not in ALLOWED_EVIDENCE_STATUS | {"PARTIAL"}:
                errors.append(f"invalid B07 processed status in {filename}: {row.get('product_id', row.get('case_id'))!r}")
            refs = [item for item in row.get("source_ids", "").split(";") if item]
            unknown = [item for item in refs if item not in source_ids]
            if unknown:
                errors.append(f"unknown B07 processed source references in {filename}: {unknown!r}")
            if filename == "battery_product_evidence.csv" and row.get("origin_status") != "OBS":
                errors.append(f"EU-first product evidence origin is not OBS: {row['product_id']!r}")
            if filename == "battery_product_evidence.csv":
                _validate_product_efficiency_fields(errors, row, f"{filename}:{row['product_id']}")
            if filename == "battery_physical_fixture_results.csv" and row.get("status") != "SCN":
                errors.append(f"B07 physical fixture must remain SCN: {row['case_id']!r}")


def validate_b08_artifacts(errors: list[str], source_ids: set[str]) -> None:
    """Validate B08's single bounded aggregation authority and SCN fixture."""
    registry_files = {
        "b08_variables.csv": "variable_id",
        "b08_formulas.csv": "formula_id",
        "b08_readiness.csv": "component_id",
    }
    variable_ids: set[str] = set()
    for filename, id_field in registry_files.items():
        path = REGISTRY / filename
        if not path.is_file():
            errors.append(f"missing B08 registry file: {filename}")
            continue
        headers, rows = read_csv(path)
        ids = [str(row.get(id_field, "")) for row in rows]
        duplicates = duplicate_values(ids)
        if duplicates:
            errors.append(f"duplicate B08 IDs in {filename}: {duplicates!r}")
        if filename == "b08_variables.csv":
            variable_ids = set(ids)
        for row in rows:
            identifier = row.get(id_field, "")
            if row.get("module_id") != "B08":
                errors.append(f"B08 artifact has non-B08 module in {filename}: {identifier!r}")
            required = [id_field, "module_id", "layer", "notes"]
            missing = [field for field in required if not str(row.get(field) or "").strip()]
            if missing:
                errors.append(f"missing B08 fields in {filename}:{identifier!r}: {missing!r}")
            refs = [item for item in str(row.get("source_ids", "")).split(";") if item]
            unknown = [item for item in refs if item not in source_ids]
            if unknown:
                errors.append(f"unknown B08 source references in {filename}:{identifier!r}: {unknown!r}")
            if filename == "b08_variables.csv" and row.get("status") not in ALLOWED_EVIDENCE_STATUS:
                errors.append(f"invalid B08 variable status: {identifier!r}")
            if filename == "b08_formulas.csv" and row.get("status") not in {"DER", "ASS"}:
                errors.append(f"invalid B08 formula status: {identifier!r}")
            if filename == "b08_readiness.csv":
                if row.get("status") not in {"VALIDATED", "PARTIAL", "BLOCKED", "Q"}:
                    errors.append(f"invalid B08 readiness status: {identifier!r}")
                try:
                    readiness = int(row.get("readiness_percent", ""))
                except ValueError:
                    errors.append(f"non-numeric B08 readiness: {identifier!r}")
                else:
                    if not 0 <= readiness <= 100:
                        errors.append(f"invalid B08 readiness percent: {identifier!r}")
    formula_path = REGISTRY / "b08_formulas.csv"
    if formula_path.is_file():
        _, rows = read_csv(formula_path)
        for row in rows:
            if row.get("output_variable_id") not in variable_ids:
                errors.append(f"unknown B08 formula output: {row.get('formula_id')!r}")
            unknown = [item for item in row.get("input_variable_ids", "").split(";") if item and item not in variable_ids]
            if unknown:
                errors.append(f"unknown B08 formula inputs: {row.get('formula_id')!r}: {unknown!r}")
    fixture_path = ROOT / "data" / "fixtures" / "b08_grid_load_scn.json"
    if not fixture_path.is_file():
        errors.append("missing B08 SCN fixture")
        return
    try:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid B08 SCN fixture JSON: {exc}")
        return
    if fixture.get("status") != "SCN" or fixture.get("truth_context") != "SCN":
        errors.append("B08 fixture must remain SCN truth")
    if fixture.get("dataset_license") != "CC BY-SA 4.0":
        errors.append("B08 fixture is missing its dataset-level license")
    if fixture.get("scope") != "BOUNDED_SCN_FIXTURE":
        errors.append("B08 fixture must be bounded SCN scope")
    if not isinstance(fixture.get("region_scheme"), str) or not fixture.get("region_scheme", "").strip():
        errors.append("B08 fixture requires top-level region_scheme")
    records = fixture.get("records", [])
    if not isinstance(records, list) or not records:
        errors.append("B08 fixture requires explicit records")
        return
    schemes = {row.get("region_scheme") for row in records}
    if len(schemes) != 1 or None in schemes:
        errors.append("B08 fixture must use one explicit region scheme")
    seen: set[tuple[object, object, object]] = set()
    required = {"timestamp", "timestep_hours", "source_entity_id", "region_id", "region_scheme", "b01_state_id", "truth_context", "evidence_status", "source_refs", "net_grid_import_kw", "net_grid_export_kw", "physical_up_flex_kw", "physical_down_flex_kw", "boundary_id"}
    for row in records:
        missing = sorted(required - set(row))
        if missing:
            errors.append(f"B08 fixture row missing fields: {missing!r}")
            continue
        if row.get("truth_context") != "SCN" or row.get("evidence_status") not in {"SCN", "Q"}:
            errors.append(f"B08 fixture row is not SCN: {row.get('source_entity_id')!r}")
        if row.get("region_scheme") != fixture.get("region_scheme"):
            errors.append(f"B08 fixture row region scheme mismatch: {row.get('source_entity_id')!r}")
        if row.get("boundary_id") != "AC_GRID":
            errors.append(f"B08 fixture boundary must be AC_GRID: {row.get('source_entity_id')!r}")
        if not isinstance(row.get("timestamp"), str) or not row["timestamp"].endswith(("Z", "+00:00")):
            errors.append(f"B08 fixture timestamp must be explicit UTC: {row.get('source_entity_id')!r}")
        if not isinstance(row.get("source_refs"), list) or not row.get("source_refs"):
            errors.append(f"B08 fixture source_refs must be a non-empty list: {row.get('source_entity_id')!r}")
        refs = row.get("source_refs", [])
        unknown = [item for item in refs if item not in source_ids]
        if unknown:
            errors.append(f"unknown B08 fixture source references: {unknown!r}")
        key = (row.get("timestamp"), row.get("source_entity_id"), row.get("boundary_id", "AC_GRID"))
        if key in seen:
            errors.append(f"duplicate B08 fixture key: {key!r}")
        seen.add(key)


def validate_b09_artifacts(errors: list[str], source_ids: set[str]) -> None:
    """Validate B09's bounded supply panel and physical adequacy registry."""
    registry_files = {
        "b09_variables.csv": "variable_id",
        "b09_formulas.csv": "formula_id",
        "b09_readiness.csv": "component_id",
    }
    variable_ids: set[str] = set()
    for filename, id_field in registry_files.items():
        path = REGISTRY / filename
        if not path.is_file():
            errors.append(f"missing B09 registry file: {filename}")
            continue
        _, rows = read_csv(path)
        ids = [row.get(id_field, "") for row in rows]
        duplicates = duplicate_values(ids)
        if duplicates:
            errors.append(f"duplicate B09 IDs in {filename}: {duplicates!r}")
        if filename == "b09_variables.csv":
            variable_ids = set(ids)
        for row in rows:
            identifier = row.get(id_field, "")
            if row.get("module_id") != "B09":
                errors.append(f"B09 artifact has non-B09 module in {filename}: {identifier!r}")
            missing = [field for field in (id_field, "module_id", "layer", "notes") if not str(row.get(field) or "").strip()]
            if missing:
                errors.append(f"missing B09 fields in {filename}:{identifier!r}: {missing!r}")
            refs = [item for item in str(row.get("source_ids", "")).split(";") if item]
            unknown = [item for item in refs if item not in source_ids]
            if unknown:
                errors.append(f"unknown B09 source references in {filename}:{identifier!r}: {unknown!r}")
            if filename == "b09_variables.csv" and row.get("status") not in ALLOWED_EVIDENCE_STATUS:
                errors.append(f"invalid B09 variable status: {identifier!r}")
            if filename == "b09_formulas.csv" and row.get("status") not in {"DER", "ASS"}:
                errors.append(f"invalid B09 formula status: {identifier!r}")
            if filename == "b09_readiness.csv":
                if row.get("status") not in {"VALIDATED", "PARTIAL", "BLOCKED", "Q"}:
                    errors.append(f"invalid B09 readiness status: {identifier!r}")
                try:
                    readiness = int(row.get("readiness_percent", ""))
                except ValueError:
                    errors.append(f"non-numeric B09 readiness: {identifier!r}")
                else:
                    if not 0 <= readiness <= 100:
                        errors.append(f"invalid B09 readiness percent: {identifier!r}")
    formula_path = REGISTRY / "b09_formulas.csv"
    if formula_path.is_file():
        _, rows = read_csv(formula_path)
        for row in rows:
            if row.get("output_variable_id") not in variable_ids:
                errors.append(f"unknown B09 formula output: {row.get('formula_id')!r}")
            unknown = [item for item in row.get("input_variable_ids", "").split(";") if item and item not in variable_ids]
            if unknown:
                errors.append(f"unknown B09 formula inputs: {row.get('formula_id')!r}: {unknown!r}")
    fixture_path = ROOT / "data" / "fixtures" / "b09_supply_adequacy_scn.json"
    if not fixture_path.is_file():
        errors.append("missing B09 SCN fixture")
        return
    try:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid B09 SCN fixture JSON: {exc}")
        return
    if fixture.get("status") != "SCN" or fixture.get("truth_context") != "SCN":
        errors.append("B09 fixture must remain SCN truth")
    if fixture.get("dataset_license") != "CC BY-SA 4.0":
        errors.append("B09 fixture is missing its dataset-level license")
    if fixture.get("scope") != "BOUNDED_SCN_FIXTURE" or not isinstance(fixture.get("region_scheme"), str):
        errors.append("B09 fixture requires bounded scope and region scheme")
    records = fixture.get("supply_records", [])
    if not isinstance(records, list) or not records:
        errors.append("B09 fixture requires explicit supply records")
        return
    seen: set[tuple[object, object, object, object]] = set()
    components: set[tuple[object, object, object]] = set()
    timestamps: set[object] = set()
    required = {"timestamp", "timestep_hours", "source_component_id", "region_id", "region_scheme", "truth_context", "evidence_status", "source_refs", "delivered_generation_kw", "boundary_id"}
    for row in records:
        missing = sorted(required - set(row))
        if missing:
            errors.append(f"B09 fixture row missing fields: {missing!r}")
            continue
        if row.get("truth_context") != "SCN" or row.get("evidence_status") != "SCN":
            errors.append(f"B09 fixture row is not SCN: {row.get('source_component_id')!r}")
        if row.get("region_scheme") != fixture.get("region_scheme"):
            errors.append(f"B09 fixture region scheme mismatch: {row.get('source_component_id')!r}")
        if row.get("boundary_id") != "GENERATION_AC":
            errors.append(f"B09 fixture generation boundary is unsupported: {row.get('source_component_id')!r}")
        if not isinstance(row.get("timestamp"), str) or not row["timestamp"].endswith(("Z", "+00:00")):
            errors.append(f"B09 fixture timestamp must be explicit UTC: {row.get('source_component_id')!r}")
        refs = row.get("source_refs", [])
        if not isinstance(refs, list) or not refs:
            errors.append(f"B09 fixture source_refs must be a non-empty list: {row.get('source_component_id')!r}")
        unknown = [item for item in refs if item not in source_ids]
        if unknown:
            errors.append(f"unknown B09 fixture source references: {unknown!r}")
        key = (row.get("source_component_id"), row.get("region_id"), row.get("region_scheme"), row.get("timestamp"))
        if key in seen:
            errors.append(f"duplicate B09 fixture generation key: {key!r}")
        seen.add(key)
        components.add((row.get("source_component_id"), row.get("region_id"), row.get("region_scheme")))
        timestamps.add(row.get("timestamp"))
    expected_panel = {(component, region, scheme, timestamp) for component, region, scheme in components for timestamp in timestamps}
    if seen != expected_panel:
        errors.append(f"incomplete B09 fixture generation panel: {sorted(expected_panel - seen)!r}")


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

    validate_b01_artifacts(errors)
    validate_b03_artifacts(errors, source_ids)
    validate_b04_artifacts(errors, source_ids)
    validate_b05_artifacts(errors, source_ids)
    validate_b06_artifacts(errors, source_ids)
    validate_b07_artifacts(errors, source_ids)
    validate_b08_artifacts(errors, source_ids)
    validate_b09_artifacts(errors, source_ids)
    validate_b10_artifacts(errors, source_ids)

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
