"""Validate the bootstrap registry contracts using only the Python standard library."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
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
        "status_date_basis",
        "physical_operational_status",
        "physical_in_service_date",
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
    "project_delivery_timing.csv": [
        'timing_id',
        'project_id',
        'network_operator',
        'target_claim_type',
        'target_date',
        'target_snapshot_status',
        'actual_completion_date',
        'schedule_variance_days',
        'schedule_variance_status',
        'completion_probability',
        'completion_probability_status',
        'source_ids',
        'evidence_status',
        'status',
        'target_source_id',
        'target_source_publication_date',
        'target_milestone_type',
        'target_scope_id',
        'target_scope_source_id',
        'target_date_relation',
        'target_date_precision',
        'target_date_authority',
        'actual_source_id',
        'actual_source_publication_date',
        'actual_claimed_date',
        'actual_milestone_type',
        'actual_scope_id',
        'actual_scope_source_id',
        'actual_date_relation',
        'actual_date_precision',
        'actual_date_authority',
        'actual_event_lower_bound',
        'actual_event_upper_bound',
        'pairing_status',
        'physical_actual_completion_date',
        'completion_report_source_id',
        'completion_report_publication_date',
        'completion_report_publication_source_id',
        'notes',
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
    "b05_p59_part_load_readiness_scorecard.csv": [
        "gate_id", "weight", "earned", "historical_earned", "status",
        "evidence_basis", "residual", "notes",
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
    "b06_p63_effect_surface_domains.csv": [
        "domain_id", "building_type", "construction_period", "before_state",
        "after_state", "validation_source_id",
        "annual_reference_existing_kwh_m2a", "annual_reference_after_kwh_m2a",
        "engine_default_factor", "national_prevalence_claim", "status", "notes",
    ],
    "b06_p64_realized_completion_authority.csv": [
        "claim_id", "claim_scope", "current_status", "authority_type",
        "required_completion_artifacts", "required_outcome_artifacts",
        "s1_rule", "source_ids", "national_completed_stock_claim", "notes",
    ],
    "b06_p64_completion_requirements.csv": [
        "artifact_id", "artifact_role", "evidence_status", "required",
        "record_link_required", "site_link_required", "scope_link_required", "notes",
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
        "annual_fixed_charge_vat_basis", "gross_annual_fixed_charge_huf", "gross_fixed_charge_status",
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
        "price_boundary", "final_gross_huf_per_kwh", "fixed_gross_huf_per_month", "final_price_status",
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
    "retrofit_peak_effect_evidence.csv": [
        "record_id", "intervention_id", "building_id", "building_type", "dwelling_count",
        "before_phase_id", "after_phase_id", "post_state_kind",
        "before_annual_net_space_heat_kwh", "after_annual_net_space_heat_kwh",
        "annual_reduction_kwh", "annual_reduction_fraction",
        "before_peak_heat_load_kw", "after_peak_heat_load_kw",
        "peak_reduction_kw", "peak_reduction_fraction",
        "before_design_indoor_temperature_c", "after_design_indoor_temperature_c",
        "before_design_outdoor_temperature_c", "after_design_outdoor_temperature_c",
        "before_heated_floor_area_m2", "after_heated_floor_area_m2",
        "before_heated_volume_m3", "after_heated_volume_m3",
        "before_winter_air_change_h", "after_winter_air_change_h",
        "before_transmission_specific_loss_w_m3k", "after_specific_heat_loss_w_m3k",
        "method_id", "before_source_id", "after_source_id", "scope_source_id",
        "evidence_status", "status", "notes",
    ],
    "retrofit_effect_surface_validation.csv": [
        "validation_id", "archetype_id", "building_type", "construction_period",
        "state_variant", "annual_net_heat_kwh_m2a", "source_id",
        "evidence_class", "usable_for_engine", "notes",
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
    """Validate B10-P3/P4/P5 truth plus the B10-P6 timing boundary."""
    module_path = REGISTRY / "module_status.csv"
    if module_path.is_file():
        _, module_rows = read_csv(module_path)
        b10 = next((row for row in module_rows if row.get("module_id") == "B10"), None)
        if b10 is None:
            errors.append("missing B10 module status row")
        else:
            if b10.get("readiness_percent") != "15":
                errors.append("B10-P6 must preserve readiness at 15")
            if any(name not in b10.get("gate_note", "") for name in ("B10-P3", "B10-P4", "B10-P5", "B10-P6")):
                errors.append("B10 module gate note must name B10-P3, B10-P4, B10-P5 and B10-P6")

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
        if (row.get("status_taxonomy") != "PROJECT_COMPLETED_REPORTED"
                or row.get("status_effective_date") != "2026-06-15"
                or row.get("status_date_basis") != "REPORTING_AS_OF_DATE"):
            errors.append(f"B10-P4 row must be PROJECT_COMPLETED_REPORTED as of 2026-06-15: {project_id}")
        if row.get("physical_operational_status") != "Q" or row.get("physical_in_service_date"):
            errors.append(f"B10-P4 physical operating status/date must remain Q: {project_id}")
        if row.get("evidence_status") != "OBS" or row.get("status") != "BASELINE":
            errors.append(f"B10-P4 row must be OBS BASELINE: {project_id}")
        refs = tuple(item for item in row.get("source_ids", "").split(";") if item)
        expected_refs = (expected["project_source"], expected["completion_source"])
        if project_id == "RRF-6.1.1-21-2022-00001":
            expected_refs += ("SRC-B10-OPUS-TITASZ-NEWS-INDEX-2026",)
        if refs != expected_refs:
            errors.append(f"B10-P4 row must bind project/funding and completion authorities: {project_id}")
        if expected["completion_source"] not in refs:
            errors.append(f"B10-P4 reported completion requires exact completion authority: {project_id}")
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
        "SRC-B10-OPUS-TITASZ-NEWS-INDEX-2026",
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

    required_p6_source = "SRC-B10-OPUS-TITASZ-RRF-TIMING-2024"
    p6_source = next((item for item in source_rows if item.get("source_id") == required_p6_source), None)
    if p6_source is None:
        errors.append(f"missing required B10-P6 timing authority: {required_p6_source}")
    elif p6_source.get("evidence_status") != "OBS" or p6_source.get("published_at") != "2024-09-30":
        errors.append("B10-P6 OPUS timing authority must remain dated source-native OBS")

    timing_path = REGISTRY / "project_delivery_timing.csv"
    if not timing_path.is_file():
        errors.append("missing B10 registry file: project_delivery_timing.csv")
    else:
        _, timing_rows = read_csv(timing_path)
        expected = {
            "RRF-6.1.1-21-2022-00006": (
                "MVM DEMASZ", "PLANNED_COMPLETION", "2026-04-30", "CURRENT_PAGE_ONLY",
                "SRC-B10-MVM-DEMASZ-RRF", "", "ON_OR_BEFORE",
            ),
            "RRF-6.1.1-21-2022-00001": (
                "OPUS TITÁSZ", "EXPECTED_COMPLETION", "2026-04-03", "EX_ANTE_VERIFIED",
                "SRC-B10-OPUS-TITASZ-RRF", "2026-06-15", "EXACT",
            ),
        }
        seen = set()
        for row in timing_rows:
            pid = row.get("project_id", "")
            exp = expected.get(pid)
            if exp is None or pid in seen:
                errors.append(f"unexpected/duplicate B10-P6 timing project: {pid!r}")
                continue
            seen.add(pid)
            operator, claim, target, snapshot, prefix, actual, relation = exp
            is_mvm = relation == "ON_OR_BEFORE"
            target_source = prefix + ("-PROJECT-2026" if is_mvm else "-TIMING-2024")
            actual_source = prefix + ("-COMPLETION-2026" if is_mvm else "-PROJECT-2026")
            report_source = prefix + "-COMPLETION-2026"
            expected_truth = {
                "network_operator": operator, "target_claim_type": claim, "target_date": target,
                "target_snapshot_status": snapshot, "actual_completion_date": actual,
                "schedule_variance_days": "", "schedule_variance_status": "Q",
                "target_source_id": target_source,
                "target_source_publication_date": "" if is_mvm else "2024-09-30",
                "target_milestone_type": "PROJECT_COMPLETION" if is_mvm else "CAPABILITY_TARGET",
                "target_scope_id": pid + (":CURRENT_PAGE_PROJECT_SCOPE" if is_mvm else ":378MW_ADDITIONAL_TRANSFER_CAPABILITY"),
                "target_scope_source_id": target_source,
                "target_date_relation": "EXACT", "target_date_precision": "DAY",
                "target_date_authority": "SOURCE_STATED_TARGET_DATE",
                "actual_source_id": actual_source,
                "actual_source_publication_date": "2026-06-15" if is_mvm else "",
                "actual_claimed_date": "2026-06-15", "actual_milestone_type": "PROJECT_COMPLETION",
                "actual_scope_id": pid + (":COMPLETION_REPORT_PROJECT_SCOPE" if is_mvm else ":PROJECT_SCOPE"),
                "actual_scope_source_id": actual_source,
                "actual_date_relation": relation, "actual_date_precision": "DAY",
                "actual_date_authority": "PUBLICATION_REPORTING_BOUND" if is_mvm else "SOURCE_STATED_EVENT_DATE",
                "actual_event_lower_bound": actual, "actual_event_upper_bound": "2026-06-15",
                "pairing_status": "UNRESOLVED",
                "physical_actual_completion_date": "",
                "completion_report_source_id": report_source,
                "completion_report_publication_date": "2026-06-15",
                "completion_report_publication_source_id": report_source if is_mvm else "SRC-B10-OPUS-TITASZ-NEWS-INDEX-2026",
            }
            for field, value in expected_truth.items():
                if row.get(field) != value:
                    errors.append(f"B10-P6 timing truth mismatch: {pid}: {field}")
            if row.get("completion_probability") or row.get("completion_probability_status") != "Q_NO_CALIBRATED_DELIVERY_MODEL":
                errors.append(f"B10-P6 probability gate mismatch: {pid}")
            refs = tuple(x for x in row.get("source_ids", "").split(";") if x)
            publication_source = report_source if is_mvm else "SRC-B10-OPUS-TITASZ-NEWS-INDEX-2026"
            refs_expected = tuple(dict.fromkeys((target_source, actual_source, report_source, publication_source)))
            if refs != refs_expected:
                errors.append(f"B10-P6 timing provenance mismatch: {pid}")
            if row.get("evidence_status") != "DER" or row.get("status") != "PARTIALLY_BOUNDED":
                errors.append(f"B10-P6 timing row status mismatch: {pid}")
        if seen != set(expected) or len(timing_rows) != 2:
            errors.append("B10-P6 must contain exactly the two bounded RRF timing projects")



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
    """Validate the retained S0-S5 compatibility contract and historical fixture."""
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


def validate_b03_fixed_fee(row: dict[str, str], errors: list[str]) -> None:
    """Keep source NET fees distinct from gross tariff arithmetic."""
    net = row.get("annual_fixed_charge_huf", "")
    gross = row.get("gross_annual_fixed_charge_huf", "")
    if row.get("tariff_band") == "ABOVE_THRESHOLD_BAND" and (net or gross):
        errors.append("B03 higher tariff band must not introduce a second fixed charge")
        return
    if not net:
        if (gross or row.get("annual_fixed_charge_vat_basis") != "NOT_SEPARATE_FEE"
                or row.get("gross_fixed_charge_status") != "Q"):
            errors.append("B03 absent per-band fee must not create another gross charge")
        return
    try:
        values = [Decimal(x) for x in (net, gross, row.get("vat_rate", ""))]
        if any(not x.is_finite() or x < 0 for x in values):
            raise ValueError("invalid fixed charge or VAT")
        with localcontext() as context:
            context.prec = 50
            expected = values[0] * (1 + values[2])
        if (row.get("annual_fixed_charge_vat_basis") != "NET"
                or row.get("gross_fixed_charge_status") != "DER"
                or values[1] != expected):
            errors.append("B03 fixed charge requires explicit NET plus VAT equals gross DER")
    except (InvalidOperation, ValueError, TypeError):
        errors.append("B03 fixed charge and VAT must be explicit finite numbers")


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
            if filename == "residential_gas_tariff_schedule.csv":
                validate_b03_fixed_fee(row, errors)


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
            if filename == "h_tariff_schedule.csv":
                if row.get("price_boundary") != "ENERGY_COMPONENT_ONLY":
                    errors.append(f"H legacy net/gross columns must be explicitly energy-only: {row.get('tariff_id')!r}")
                if row.get("final_price_status") not in {"OBS", "DER", "Q"}:
                    errors.append(f"invalid H final price status: {row.get('tariff_id')!r}")
                if row.get("final_price_status") in {"OBS", "DER"} and (not row.get("final_gross_huf_per_kwh") or not row.get("fixed_gross_huf_per_month")):
                    errors.append(f"H final price requires gross variable and fixed components: {row.get('tariff_id')!r}")
                if row.get("final_price_status") == "DER" and (
                    row.get("period_type") != "outside season discounted energy"
                    or "SRC-B04-MEKH-SYSTEM-FEES-2024" not in refs
                    or "SRC-B04-MVM-M1-2026" not in refs
                    or "SRC-B04-MVM-RESIDENTIAL-TARIFF-2026" not in refs
                ):
                    errors.append(f"derived outside-H rate requires scoped legal/energy/network sources: {row.get('tariff_id')!r}")
                if row.get("final_price_status") == "Q" and row.get("final_gross_huf_per_kwh"):
                    errors.append(f"unadmitted H final price must remain blank: {row.get('tariff_id')!r}")



def validate_b05_readiness_row(errors: list[str], row: dict[str, str]) -> None:
    """Keep one explicitly unassessed component distinct from numeric readiness."""
    component_id = row.get("component_id", "")
    if row.get("status") not in {"VALIDATED", "PARTIAL", "BLOCKED", "Q"}:
        errors.append(f"invalid B05 readiness status: {component_id!r}")
    if component_id == "PART_LOAD_MODULATION":
        if row.get("status") != "Q" or row.get("readiness_percent") != "":
            errors.append("PART_LOAD_MODULATION current readiness must be Q with a blank score")
        required_markers = (
            "CURRENT_SCORE_UNASSESSED",
            "HISTORICAL_P59_SCORE=75",
            "SUPPORTED_UNAFFECTED_SUBTOTAL=67",
            "UNASSESSED_GATE_WEIGHT=8",
            "UNASSESSED_GATE=EN14825_STANDARD_BIN_CYCLING_METHOD",
        )
        markers = {part.strip().rstrip(".") for part in row.get("notes", "").split(";")}
        for marker in required_markers:
            if marker not in markers:
                errors.append(f"missing B05 unassessed readiness marker: {marker}")
        return
    try:
        readiness = int(row.get("readiness_percent", ""))
    except ValueError:
        errors.append(f"non-numeric B05 readiness: {component_id!r}")
    else:
        if not 0 <= readiness <= 100:
            errors.append(f"invalid B05 readiness percent: {component_id!r}")


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
            if filename == "heat_pump_readiness.csv":
                validate_b05_readiness_row(errors, row)

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
        "ARCHETYPE_ESTIMATE", "POLICY_TARGET", "MATCHED_METERED_SAVINGS",
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
        if row["evidence_class"] == "MATCHED_METERED_SAVINGS":
            # Whole-meter matched statistics belong in their typed source manifest,
            # never in the existing space-heat/m2 or design-peak numeric interface.
            if any(row.get(field, "").strip() for field in numeric_fields):
                errors.append(f"matched meter savings cannot populate B06 physical-effect fields: {evidence_id!r}")
            if row["usable_for_engine"] != "NO" or row["status"] != "Q":
                errors.append(f"matched meter savings retain Q target authority and no engine admission: {evidence_id!r}")

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
    validate_b01_capability_artifacts(errors)
    validate_b01_annual_artifacts(errors)
    validate_b01_population_planning_artifacts(errors)
    validate_b01_benefit_metric_artifacts(errors, source_ids)
    validate_b03_artifacts(errors, source_ids)
    validate_b04_artifacts(errors, source_ids)
    validate_b05_artifacts(errors, source_ids)
    validate_b05_r290_references(errors, source_ids)
    validate_b05_wm50_installed_boundary_evidence(errors, source_ids)
    validate_b05_eoh_observed_boundary_evidence(errors, source_ids)
    validate_b06_artifacts(errors, source_ids)
    validate_b07_artifacts(errors, source_ids)
    validate_b07_shared_use_artifacts(errors)
    validate_b08_artifacts(errors, source_ids)
    validate_b09_artifacts(errors, source_ids)
    validate_b10_artifacts(errors, source_ids)
    validate_b11_seasonal_references(errors, source_ids)

    return errors


def validate_b01_capability_artifacts(errors: list[str]) -> None:
    """Validate the canonical component contract and its bounded SCN entry point."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        from modules.B01.capability_contract import load_contract
        from modules.B01.engine import run_capability_fixture
        contract = load_contract()
        policy = json.loads((REGISTRY / "owner_policy_decisions.json").read_text(encoding="utf-8"))
        required = policy["decisions"]["completed_cohort_subsidy_exit"]["completion_required"]
        if set(contract["components"]) != set(required):
            errors.append("B01 capability components differ from the explicit complete-package policy")
        if set(contract["programme_action_claims"]) != {"PROGRAMME_ELIGIBILITY", "HOUSEHOLD_CASHFLOW_PROTECTED"}:
            errors.append("B01 programme action must retain eligibility and first-day/interim household protection")
        if set(contract["exit_claims"]) != {"PROGRAMME_ELIGIBILITY", "UNSUBSIDIZED_TOTAL_BILL_LOWER", "HOUSEHOLD_CASHFLOW_PROTECTED", "SUBSIDY_EXIT_APPLICABLE"}:
            errors.append("B01 subsidy exit must retain the distinct policy conditions")
        for source in contract["source_bindings"]:
            if not (ROOT / source["path"]).is_file():
                errors.append(f"B01 capability source binding is missing: {source['path']}")
        result = run_capability_fixture(ROOT / "data/fixtures/b01_capability_scn.json")
        if result.identity.truth_context != "SCN" or result.selected_or_funded:
            errors.append("B01 capability fixture must remain an unfunded scenario assessment")
        if result.complete_triple.status != "UNKNOWN" or result.subsidy_exit_conditions.status != "UNKNOWN":
            errors.append("B01 battery-first fixture cannot imply a complete programme or subsidy exit")
    except (ValueError, TypeError, KeyError, OSError) as exc:
        errors.append(f"invalid B01 capability contract: {exc}")


def validate_b01_annual_artifacts(errors: list[str]) -> None:
    """Check annual planning authority/boundaries without creating numerical inputs."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        from modules.B01.annual_bundle_ledger import load_annual_contract
        contract = load_annual_contract()
        if contract["numeric_policy_defaults"] or contract["original_task_acceptance_changed"]:
            errors.append("B01 annual planning cannot introduce policy defaults or accept original tasks")
        for source in contract["source_bindings"]:
            if not (ROOT / source["path"]).is_file():
                errors.append(f"B01 annual planning source binding is missing: {source['path']}")
        if set(contract["opening_uses_states"]) != {"NONE", "USES", "Q"}:
            errors.append("B01 annual opening commitments must preserve Q versus explicit absence")
    except (ValueError, TypeError, KeyError, OSError) as exc:
        errors.append(f"invalid B01 annual bundle contract: {exc}")


def validate_b01_population_planning_artifacts(errors: list[str]) -> None:
    """Validate the bounded population bridge and reuse the actual P84 reader."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        from modules.B01.population_planning_bridge import load_population_contract
        from modules.B01.engine import population_source_demo
        contract = load_population_contract()
        for source in contract["source_bindings"]:
            if not (ROOT / source["path"]).is_file():
                errors.append(f"B01 population planning source binding is missing: {source['path']}")
        demo = population_source_demo()
        if (demo["control_count"], demo["represented_mass"], demo["native_unit"], demo["reference_date"]) != (40, 3389817, "DWELLING", "2022-10-01"):
            errors.append("B01 population bridge source controls differ from the 2022 P84 boundary")
        envelope = demo["terminal_eligibility"]
        if (envelope.status, envelope.eligible_lower_dwellings, envelope.eligible_upper_dwellings) != ("Q", 0, 3389817):
            errors.append("B01 population bridge cannot invent terminal eligibility")
        if demo["planning_state_distribution"] is not None or demo["intervention_eligible_mass"] is not None:
            errors.append("B01 source control demo cannot manufacture allocatable states")
    except (ValueError, TypeError, KeyError, OSError) as exc:
        errors.append(f"invalid B01 population planning contract: {exc}")


def validate_b01_benefit_metric_artifacts(errors: list[str], source_ids: set[str]) -> None:
    """Validate bounded metric semantics and method provenance; adopt no policy."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        from modules.B01.benefit_metric_contract import load_benefit_contract
        from modules.B01.engine import compare_benefit_ratios
        contract = load_benefit_contract()
        if not callable(compare_benefit_ratios):
            errors.append("B01 benefit comparison entrypoint is missing")
        owner = json.loads((REGISTRY / "owner_policy_decisions.json").read_text(encoding="utf-8"))
        priority = owner["decisions"]["selection_priority"]
        if any(priority[k] is not None for k in ("benefit_metric_definition", "public_cost_denominator", "normalization_and_weights")):
            errors.append("B01 bounded benefit contract cannot adopt canonical metrics or weights")
        for binding in contract["source_bindings"]:
            if not (ROOT / binding["path"]).is_file():
                errors.append(f"B01 benefit source binding missing: {binding['path']}")
        for source in contract["method_sources"]:
            if source["source_id"] not in source_ids:
                errors.append(f"B01 benefit method source absent from registry: {source['source_id']}")
            if (source["reuse_status"] != "EXTERNAL_ONLY_REPOSITORY_COPY_NOT_CLEARED" or
                    source["repo_snapshot_path"] is not None or len(source["sha256"]) != 64 or
                    source["admission"] != "METHOD_REFERENCE_ONLY_NO_PROGRAMME_VALUES_OR_CURRENT_SITE_ELIGIBILITY"):
                errors.append("B01 method source must retain its bounded provenance and no-copy boundary")
    except (ValueError, TypeError, KeyError, OSError) as exc:
        errors.append(f"invalid B01 benefit metric contract: {exc}")



def validate_b07_shared_use_artifacts(errors: list[str]) -> None:
    """Validate the conditional shared schedule contract without changing gates."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        from modules.B07.shared_use_schedule_contract import load_shared_use_contract
        load_shared_use_contract()
    except (ValueError, TypeError, KeyError, OSError) as exc:
        errors.append(f"invalid B07 shared-use schedule contract: {exc}")

def validate_b11_seasonal_references(errors: list[str], source_ids: set[str]) -> None:
    """Validate this bounded source inventory, without creating a runtime consumer."""
    path = REGISTRY / "b11_seasonal_boiler_reference_manifest.json"
    prefix = "B11 seasonal reference"

    def require(condition, message):
        if not condition:
            errors.append(f"{prefix}: {message}")

    authority = {
        "applicability_status": "Q", "fuel_volume_authority_status": "Q",
        "usable_for_engine": False, "model_default_admitted": False,
        "national_factor_admitted": False, "task_accepted": False,
    }
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        require(set(manifest) == {"schema_version", "handoff_id", "status", "owner_module", "research_slice_id", "source_fact_policy", "target_authority", "sources", "families", "validation_debt", "allowed_next_use"}, "unexpected/missing manifest fields")
        require(manifest["schema_version"] == 1 and manifest["status"] == "QUALIFIED_SOURCE_REFERENCES_ONLY", "invalid source-reference contract")
        require(manifest["owner_module"] == "B11" and manifest["research_slice_id"] == "B11-D01", "invalid owner/slice")
        require(all(type(manifest["target_authority"][k]) is type(v) for k, v in authority.items()), "invalid top-level authority field types")
        require(manifest["target_authority"] == authority, "retain Q authority and no admission/default/task acceptance")
        sources = manifest["sources"]
        by_id = {s["source_id"]: s for s in sources}
        require(len(by_id) == len(sources) == 5, "source identities must be unique and complete")
        global_rows = {r["source_id"]: r for r in read_csv(REGISTRY / "sources.csv")[1]}
        local_rows = read_csv(REGISTRY / "b11_gas_efficiency_sources.csv")[1]
        for sid, source in by_id.items():
            matches = [r for r in local_rows if r["source_id"] == sid]
            require(sid in source_ids and sid in global_rows and len(matches) == 1, f"missing/duplicate global or local source {sid}")
            if sid not in global_rows or len(matches) != 1:
                continue
            global_row, local_row = global_rows[sid], matches[0]
            for field in ("original_url", "retrieved_at", "reference_period", "authority", "document_date_basis", "reuse_note"):
                require(isinstance(source[field], str) and bool(source[field].strip()), f"missing {field} for {sid}")
            require(source["original_url"].startswith("https://"), f"invalid original URL {sid}")
            require(bool(re.fullmatch(r"[a-f0-9]{64}", source["sha256"])), f"invalid source hash {sid}")
            require(type(source["bytes"]) is int and source["bytes"] > 0, f"invalid original byte count {sid}")
            require(source["sha256"] == global_row["local_snapshot_sha256"], f"global source hash mismatch {sid}")
            require(source["original_url"] == global_row["url"] == local_row["url"], f"source URL mismatch {sid}")
            require(source["retrieved_at"][:10] == global_row["retrieved_at"] == local_row["retrieved_at"], f"retrieval date mismatch {sid}")
            require(source["reference_period"] == global_row["reference_period"] == local_row["reference_period"], f"source period mismatch {sid}")
            require(source["source_tier"] == global_row["source_tier"] == local_row["source_tier"], f"source tier mismatch {sid}")
            require(source["title"] == global_row["title"] == local_row["title"], f"source title mismatch {sid}")
            require(source["authority"] == global_row["institution"] == local_row["institution"], f"source authority mismatch {sid}")
            expected_status = "DER" if source["family_id"] == "EST-CONDENSING-FIELD-TRIAL" else "OBS"
            require(global_row["evidence_status"] == local_row["evidence_status"] == expected_status, f"source evidence type mismatch {sid}")
            require(global_row["module_id"] == local_row["module_id"] == "B11", f"source owner mismatch {sid}")
            require(local_row["authority_status"] == "SOURCE_REFERENCE_ONLY_NO_RUNTIME_ADMISSION", f"local source admitted {sid}")
            require(source["repo_snapshot_path"] is None and source["reuse_status"] == "EXTERNAL_ONLY_REPOSITORY_COPY_NOT_CLEARED", f"original-document copy not cleared {sid}")
        families = manifest["families"]
        require(set(families) == {"BOILEFF", "EST-CONDENSING-FIELD-TRIAL"}, "family identity mismatch")
        memberships = [sid for family in families.values() for sid in family["source_ids"]]
        require(len(memberships) == len(set(memberships)) and set(memberships) == set(by_id), "each source must belong to exactly one family")
        expected_row_fields = {"case_id", "geography", "appliance_class", "gcv_efficiency_pct", "truth", "source_id", "family_id", "locator", "boundary_id", "period_id", "use_scope"}
        family_fields = {"source_ids", "target_authority", "record_kind", "records", "record_field_policy", "period", "gas_basis", "calibration", "records_sha256"}
        extra_family_fields = {
            "BOILEFF": {"cohort", "heat_boundary", "aggregate_discrepancy", "lineage", "case_detail_limits"},
            "EST-CONDENSING-FIELD-TRIAL": {"heat_boundaries", "boundary_locator", "denominator", "selection", "source_subgroups", "substitution", "subgroup_audit", "limits", "continuation_2010"},
        }
        for fid, family in families.items():
            require(set(family) == family_fields | extra_family_fields[fid], f"unexpected/missing family fields {fid}")
            require(all(type(family["target_authority"][k]) is type(v) for k, v in authority.items()), f"invalid authority field types {fid}")
            require(family["target_authority"] == authority, f"family authority/default promotion {fid}")
            require(all(by_id[sid]["family_id"] == fid for sid in family["source_ids"]), f"mixed source families {fid}")
            basis = family["gas_basis"]
            require(basis["reported_energy_basis"] == "GCV" and basis["status"] == "Q", f"energy basis mislabelled {fid}")
            for field in ("fuel_subtype", "calorific_reference_temperature_c", "gas_quality_context_id", "compatible_gcv_lhv_pair", "volume_reference_state", "lhv_efficiency", "runtime_fuel_volume"):
                require(basis[field] is None, f"invented gas-basis/volume field {fid}/{field}")
            require(family["calibration"] == {"case_instrument_certificates": None, "propagated_efficiency_uncertainty": None, "status": "Q"}, f"invented uncertainty {fid}")
            records = family["records"]
            require(len(records) == len({r["case_id"] for r in records}), f"duplicate case IDs {fid}")
            digest = hashlib.sha256(json.dumps(records, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
            require(digest == family["records_sha256"], f"native record integrity mismatch {fid}")
            is_boi = fid == "BOILEFF"
            extra_fields = set() if is_boi else {"months_without_substitution", "months_with_substitution", "substituted_days", "substitution_locator"}
            expected_source = "SRC-B11-BOILEFF-FINAL-2009" if is_boi else "SRC-B11-EST-FIELD-2009"
            expected_policy = {
                "gcv_efficiency_pct": {
                    "unit": "percent_GCV", "truth": "OBS" if is_boi else "DER",
                    "statistic": "SOURCE_LABELLED_MEASURED_EFFICIENCY" if is_boi else "SOURCE_PROCESSED_ACCEPTED_ANNUAL_HEAT_OUTPUT_OVER_GAS_ENERGY",
                    "raw_uninterrupted_measurement_claim": False,
                },
            }
            if not is_boi:
                expected_policy.update({
                    "months_without_substitution": {"unit": "month", "truth": "OBS", "statistic": "SOURCE_REPORTED_ACCEPTANCE_COUNT"},
                    "months_with_substitution": {"unit": "month", "truth": "OBS", "statistic": "SOURCE_REPORTED_ACCEPTANCE_COUNT"},
                    "substituted_days": {"unit": "day", "truth": "OBS", "statistic": "SOURCE_REPORTED_SUBSTITUTION_COUNT"},
                })
            require(family["record_field_policy"] == expected_policy, f"source field policy mismatch {fid}")
            require(family["record_field_policy"]["gcv_efficiency_pct"]["raw_uninterrupted_measurement_claim"] is False, f"raw uninterrupted claim {fid}")
            for row in records:
                case = row["case_id"]
                require(set(row) == expected_row_fields | extra_fields, f"unexpected/missing native fields {case}")
                require(row["family_id"] == fid and row["source_id"] == expected_source and expected_source in family["source_ids"], f"mixed row/source family {case}")
                require(row["truth"] == ("OBS" if is_boi else "DER") == family["record_field_policy"]["gcv_efficiency_pct"]["truth"], f"source fact type mismatch {case}")
                require(isinstance(row["locator"], str) and bool(row["locator"]), f"missing native locator {case}")
                value = Decimal(row["gcv_efficiency_pct"])
                require(value.is_finite() and 0 < value <= 100, f"invalid native GCV percent {case}")
                if is_boi:
                    require(row["appliance_class"] == "gas_condensing_installation", f"BOILeff source-qualified appliance class mismatch {case}")
                    country = case.split()[0]
                    require(country in {"HU", "AT"} and row["geography"] == country, f"mixed BOILeff geography {case}")
                    require(row["use_scope"] == ("HISTORICAL_HU_REFERENCE" if country == "HU" else "SAME_FAMILY_AT_AGGREGATE_CONTEXT"), f"mixed BOILeff applicability {case}")
                    require(row["boundary_id"] == "BOILEFF_CASE_BOUNDARY_UNRESOLVED" and row["period_id"] == "BOILEFF_STUDY_2008_2009_CASE_COVERAGE_UNKNOWN", f"invented BOILeff boundary/coverage {case}")
                else:
                    boundaries = {"combination": "COMBI_BOILER_SH_DHW_OUTPUT", "regular": "REGULAR_BOILER_OUTPUT_BEFORE_CYLINDER", "CPSU": "CPSU_INTEGRAL_STORE"}
                    require(row["geography"] == "UK" and row["boundary_id"] == boundaries.get(row["appliance_class"]), f"mixed UK service/geography boundary {case}")
                    require(row["period_id"] == "EST_SITE_ACCEPTED_12_MONTHS" and row["use_scope"] == "HISTORICAL_UK_REFERENCE", f"UK period/applicability mismatch {case}")
                    counts = [row[k] for k in ("months_without_substitution", "months_with_substitution", "substituted_days")]
                    require(all(type(x) is int and x >= 0 for x in counts) and sum(counts[:2]) == 12, f"invalid UK substitution counts {case}")
                    require(bool(row["substitution_locator"]), f"missing substitution join locator {case}")
        boi, uk = families["BOILEFF"], families["EST-CONDENSING-FIELD-TRIAL"]
        require({k: sum(r["geography"] == k for r in boi["records"]) for k in ("HU", "AT")} == {"HU": 6, "AT": 8}, "BOILeff cohort must retain six HU and eight separate AT rows")
        require({k: sum(r["appliance_class"] == k for r in uk["records"]) for k in ("combination", "regular", "CPSU")} == {"combination": 31, "regular": 10, "CPSU": 2}, "UK cohort/class counts changed")
        for key in ("individual_make_model", "commissioning_date_or_age", "case_control_details"):
            require(boi["case_detail_limits"][key] is None, f"invented BOILeff case detail {key}")
        for key in ("predicted_efficiency_or_guarantee_band_is_measurement_uncertainty", "climate_corrected_saving_is_old_new_conversion_pair", "old_conventional_baseline_established"):
            require(boi["case_detail_limits"][key] is False, f"BOILeff unsupported inference {key}")
        aggregate = boi["aggregate_discrepancy"]
        require({k: v["value"] for k, v in aggregate["source_reported"].items()} == {"HU": "86.00", "AT": "89.63", "ALL_14": "87.9"}, "source aggregates must not be repaired")
        require(aggregate["status"] == "UNRESOLVED_SOURCE_AGGREGATION" and aggregate["weights"] is None and aggregate["source_aggregates_repaired"] is False and aggregate["default_selected"] is False, "aggregate discrepancy/default boundary changed")
        require(boi["period"]["blank_agreement"]["completed_observation_evidence"] is False and boi["period"]["completed_case_intervals"] is None, "planned readings are not completion evidence")
        require(boi["lineage"]["independent_replication"] is False and boi["lineage"]["jrc_available_date_is_print_publication_date"] is False, "BOILeff lineage/date authority changed")
        for key in ("pooled_unlike_boundaries", "sd_is_measurement_uncertainty_or_ci", "extrema_are_population_or_prediction_intervals", "usage_weighted_table_14_substituted"):
            require(uk["source_subgroups"][key] is False, f"UK statistic boundary changed {key}")
        for key in ("annual_table_heat_adjustment_applied", "illustrative_cylinder_loss_adjustment_adopted", "sap_factor_adopted", "qa_thresholds_are_measurement_uncertainty", "controls_service_weather_standardized"):
            require(uk["limits"][key] is False, f"UK unsupported adjustment {key}")
        for kind, mean, sd in (("combination", "82.5", "4.0"), ("regular", "85.3", "2.5")):
            published = uk["source_subgroups"][kind]
            require((published["mean"]["value"], published["sample_sd"]["value"]) == (mean, sd), f"UK published statistics changed {kind}")
            require(all(published[k]["truth"] == "DER" for k in ("mean", "sample_sd", "minimum", "maximum")), f"UK statistic type mismatch {kind}")
        require(uk["source_subgroups"]["CPSU"]["pooled_mean_adopted"] is None and uk["source_subgroups"]["CPSU"]["pooled_sd_adopted"] is None, "CPSU pooling not admitted")
        require(uk["subgroup_audit"]["truth"] == "DER", "UK subgroup audit is derived")
        for kind, audit in uk["subgroup_audit"]["subgroups"].items():
            rows = [r for r in uk["records"] if r["appliance_class"] == kind]
            expected = (len(rows), sum(r["substituted_days"] > 0 for r in rows), sum(r["substituted_days"] for r in rows), sum(r["months_without_substitution"] for r in rows), sum(r["months_with_substitution"] for r in rows), len(rows) * 365)
            fields = ("n", "sites_with_substitution", "sum_substituted_days", "months_without_substitution", "months_with_substitution", "source_convention_days_denominator")
            require(tuple(audit[k] for k in fields) == expected, f"UK subgroup audit reconciliation {kind}")
        substitution = uk["substitution"]
        for key, expected in (("months_without_substitution", 449), ("months_with_substitution", 67), ("substituted_days", 225)):
            require(sum(row[key] for row in uk["records"]) == substitution[key]["value"] == expected, f"UK substitution reconciliation {key}")
        require(substitution["contradictory_prose_percent"]["value"] == "2.3" and substitution["source_prose_repaired"] is False and substitution["raw_uninterrupted_measurement_claim"] is False, "UK source-prose/raw-record boundary changed")
        continuation = uk["continuation_2010"]
        require(continuation["same_cohort_family"] is True, "UK continuation must retain same family")
        for key in ("independent_replication", "counts_reconciled", "added_to_2009_cohort", "tpi_savings_factor_adopted"):
            require(continuation[key] is False, f"UK continuation is not additive/reconciled {key}")
        require(continuation["unique_homes_inferred"] is None, "UK unique-home inference forbidden")
        plan = json.loads((REGISTRY / "v1_research_plan.json").read_text(encoding="utf-8"))
        task = next(s for m in plan["modules"] for s in m["slices"] if s["slice_id"] == "B11-D01")
        require(task["status"] == "INTEGRATING" and not task["accepted_artifacts"] and not task["consumer_tests"] and task["reviewed_commit"] is None, "original task acceptance cannot change")
        require(task["canonical_source_ids"] == ["SRC-B06-TABULA-HU-CALCULATOR-2016", "SRC-B06-TABULA-METHOD-2013-LOCAL-REFERENCE"], "seasonal references cannot replace/admit canonical defaults")
        require(set(task["validation_debt_ids"]) == {d["id"] for d in manifest["validation_debt"]} and all(d["status"] == "Q" for d in manifest["validation_debt"]), "source debt must remain explicit")
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, StopIteration, InvalidOperation) as exc:
        errors.append(f"{prefix}: invalid or incomplete manifest: {exc}")



def validate_b05_wm50_installed_boundary_evidence(errors: list[str], source_ids: set[str]) -> None:
    """Validate source references, not installed performance or an engine input."""
    prefix = "B05 WM50 installed evidence"

    def require(condition, message):
        if not condition:
            errors.append(f"{prefix}: {message}")

    g = "SRC-B05-GRUNDFOS-UPM3-"
    identity, spec, curve = (g + "59C90800-" + part + "-2026"
                             for part in ("IDENTITY", "SPEC", "CURVE"))
    book = g + "DATABOOK-2022"
    binding = "SRC-B05-MITSUBISHI-WM50-FTC6-BINDING-2026"
    mitsubishi = {
        "SRC-B05-MITSUBISHI-EHPT-PARTS-OCB714A",
        "SRC-B05-MITSUBISHI-EHPT-PRODUCT-2020",
        "SRC-B05-MITSUBISHI-EHPT-SERVICE-OCH714A",
    }
    expected_sources = {identity, spec, curve, book} | mitsubishi
    expected_debts = {
        "B05-WM50-OEM-PROFILE": ("OPTIONAL_EXTENSION", "no", "claim_specific",
                                 "OPTIONAL_EXACT_COMPONENT_ROUTE"),
        "B05-WM50-INSTALLED-ANNUAL": ("MODEL_BLOCKER", "yes", "yes",
                                      "COMPLETE_INSTALLED_CLAIM_ONLY"),
        "B05-WM50-INSTALLED-HOURLY": ("MODEL_BLOCKER", "yes", "yes",
                                      "COMPLETE_INSTALLED_CLAIM_ONLY"),
    }
    try:
        from datetime import datetime
        manifest = json.loads((REGISTRY / "b05_wm50_installed_boundary_evidence.json").read_text(encoding="utf-8"))
        require(manifest["schema_version"] == 1 and manifest["handoff_id"] == "B05-WM50-INSTALLED-BOUNDARY-EVIDENCE"
                and manifest["status"] == "QUALIFIED_SOURCE_REFERENCES_ONLY", "source-reference identity/status")
        require(manifest["owner_module"] == "B05" and manifest["research_slice_ids"] == ["B05-D01", "B05-D03"],
                "owner and existing research slices")
        authority = manifest["target_authority"]
        require(authority["applicability_status"] == authority["exact_oem_binding_status"] == "Q",
                "OEM applicability remains Q")
        flags = ("usable_for_engine", "model_default_admitted", "product_selected",
                 "annual_installed_performance_admitted", "hourly_installed_performance_admitted",
                 "installed_heat_service_admitted", "national_factor_admitted", "readiness_closed", "task_accepted")
        require(all(authority[k] is False for k in flags), "no runtime/default/installed/task admission")
        sources = manifest["sources"]
        by_id = {s["source_id"]: s for s in sources}
        require(set(by_id) == expected_sources and len(by_id) == len(sources), "unique artifact identity inventory")
        global_rows = read_csv(REGISTRY / "sources.csv")[1]
        local_rows = read_csv(REGISTRY / "heat_pump_sources.csv")[1]
        for sid, source in by_id.items():
            for name in ("title", "authority", "original_url", "retrieved_at", "retrieval_time_basis",
                         "document_revision", "reference_period", "locator", "claim_scope", "reuse_note"):
                require(isinstance(source[name], str) and bool(source[name].strip()), f"missing provenance {sid}/{name}")
            require(source["original_url"].startswith("https://"), f"source URL {sid}")
            require(datetime.fromisoformat(source["retrieved_at"].replace("Z", "+00:00")).utcoffset() is not None,
                    f"timezone required {sid}")
            require(bool(re.fullmatch(r"[0-9a-f]{64}", source["sha256"]))
                    and type(source["bytes"]) is int and source["bytes"] > 0, f"original byte identity {sid}")
            require(source["repo_snapshot_path"] is None
                    and source["reuse_status"] == "EXTERNAL_ONLY_REPOSITORY_COPY_NOT_CLEARED", f"uncleared copy {sid}")
            require(sid in source_ids, f"unregistered source {sid}")
            for rows in (global_rows, local_rows):
                matches = [r for r in rows if r["source_id"] == sid]
                require(len(matches) == 1, f"missing/duplicate registry source {sid}")
                if len(matches) != 1:
                    continue
                row = matches[0]
                for sk, rk in (("original_url", "url"), ("title", "title"), ("authority", "institution"),
                               ("reference_period", "reference_period"), ("source_tier", "source_tier")):
                    require(source[sk] == row[rk], f"cross-registry provenance {sid}/{rk}")
                require(row["retrieved_at"] == source["retrieved_at"][:10]
                        and row["module_id"] == "B05" and row["evidence_status"] == "OBS", f"source date/type {sid}")
                if "local_snapshot_sha256" in row:
                    require(row["local_snapshot_sha256"] == source["sha256"]
                            and row["license"] == source["reuse_status"], f"source digest/reuse {sid}")
                else:
                    require(row["license_status"] == source["reuse_status"] and row["layer"] == "OPERATING_CONFIG",
                            f"source layer/reuse {sid}")
        reused = manifest["reused_sources"]
        require(len(reused) == 1 and reused[0]["source_id"] == binding,
                "reuse existing named binding source separately from seven new artifacts")
        binding_source = reused[0]
        require(binding in source_ids and binding not in by_id, "binding is existing reuse, not an eighth artifact")
        require(binding_source["sha256"] == "ed8090f77ffa0be787ba970254c72348b471e86275136fa77a1c12d98f70084c"
                and binding_source["document_id"] == "BRE EPD000522 Issue01"
                and binding_source["document_date"] == "2023-08-14", "reused EPD document identity")
        require(binding_source["repo_snapshot_path"] is None
                and binding_source["reuse_status"] == "EXTERNAL_ONLY_REPOSITORY_COPY_NOT_CLEARED"
                and binding_source["independent_replication"] is False, "reused source copy/independence boundary")
        for rows in (global_rows, local_rows):
            matches = [row for row in rows if row["source_id"] == binding]
            require(len(matches) == 1, "existing binding source resolves uniquely in both registries")
            if len(matches) == 1:
                row = matches[0]
                require(binding_source["original_url"] == row["url"]
                        == "https://library.mitsubishielectric.co.uk/pdf/download_full/4888"
                        and binding_source["authority"] == row["institution"], "reused binding provenance")
                if "local_snapshot_sha256" in row:
                    require(binding_source["sha256"] == row["local_snapshot_sha256"], "reused binding original digest")
        aliases = manifest["source_aliases"]
        require(len(aliases) == len(set(aliases.values())) and set(aliases.values()) == expected_sources,
                "research aliases resolve without duplicate source identity")
        families = manifest["source_families"]
        memberships = [sid for f in families for sid in f["members"]]
        require(set(memberships) == expected_sources and len(memberships) == len(set(memberships)),
                "each artifact belongs to one source family")
        require(all(f["independent_replication"] is False for f in families), "linked artifacts are not independent replications")
        api_family = next(f for f in families if identity in f["members"])
        require(set(api_family["members"]) == {identity, spec, curve}
                and api_family["binding_key"] == "pumpsystemid=3064924080", "preserve linked API dependency")
        require(any(set(f["members"]) == mitsubishi for f in families), "preserve Mitsubishi manufacturer dependency")
        claims = {c["id"]: c for c in manifest["claims"]}
        statuses = {**{f"OEM-{i:02d}": "OBS" for i in range(1, 9)},
                    "OEM-09": "DER", "OEM-10": "Q", "OEM-11": "SCN", "OEM-12": "Q", "OEM-13": "Q"}
        require(set(claims) == set(statuses) and len(claims) == len(manifest["claims"]), "unique scoped claim inventory")
        for cid, claim in claims.items():
            require(claim["status"] == statuses.get(cid), f"claim evidence type {cid}")
            require(bool(claim["source_ids"]) and set(claim["source_ids"]) <= (expected_sources | {binding} if cid == "OEM-11" else expected_sources)
                    and bool(claim["locator"]) and bool(claim["unit"]), f"claim source/unit/locator {cid}")
        derivation = claims["OEM-09"]
        require(derivation.get("method_id") == "STANDARD_UPM3_POWER_FEEDBACK"
                and not ({"formula", "conditions", "numeric_result", "numerical_result"} & set(derivation)),
                "OEM-09 references one authoritative method; duplicated derivation fields forbidden")
        pairing = claims["OEM-11"]
        require(binding in pairing["source_ids"]
                and pairing["source_locators"][binding] == "PDF3 Product Description; PDF7 Functional unit",
                "pairing lineage requires existing PDF4888 Product Description and functional unit")
        require(pairing["limits"] == {"combined_heating_DHW_LCA_source": True,
                                     "rating_specimen_proven": False, "actual_installation_proven": False},
                "pairing is combined SH/DHW LCA, not rating specimen or actual installation")
        require(claims["OEM-01"]["values"] == {"product_number": "59C90800", "name": "UPM3 15-75 130 AZA",
                                              "pumpsystemid": "3064924080"}, "candidate API identity")
        require(claims["OEM-02"]["values"] == {"P1_min_W": 2, "P1_max_W": 60, "curve_set": "c0016333"},
                "candidate P1 specs, not an installed average")
        cv = claims["OEM-03"]["values"]
        require((cv["medium"], cv["liquid_temperature_degC"], cv["density_kg_m3"],
                 cv["electrical_power_unit"], cv["flow_unit"]) == ("Water", 20, 998.2, "W", "m3/h"),
                "curve medium/temperature/axes are not W55 or head-derived power")
        require(cv["control_selector"] is None and cv["W55_transfer_admitted"] is False, "no selected curve or W55 transfer")
        command = claims["OEM-05"]["values"]
        require(command["input_is_speed_command"] is True and command["input_is_runtime_fraction"] is False
                and command["MP1_profile_selected"] is None, "input PWM is not runtime or a selected MP1 profile")
        fb = claims["OEM-06"]["values"]
        # Source oracle: Grundfos99092813 03.2022 PDF18 TM050006 and standard UPM3 table.
        require(fb["family"] == "UPM3" and fb["profile"] == "STANDARD_POWER_FEEDBACK", "standard UPM3 profile only")
        require(fb["normal_output_percent"] == [0, 70] and fb["normal_power_W"] == [0, 70]
                and fb["slope_W_per_percentagepoint"] == 1 and fb["saturation_W"] == 70, "UPM3 power scale/saturation")
        require(tuple(fb[k] for k in ("warning_percent", "electrical_fault_percent", "blocked_percent", "standby_percent"))
                == (75, 85, 90, 95) and fb["status_codes_are_power_samples"] is False, "status codes are not watt samples")
        require(fb["output_frequency_Hz"] == 75 and fb["output_frequency_tolerance_percent"] == 5
                and fb["accuracy_source_wording"] == "±2% of PWM signal", "frequency/accuracy is not annual energy accuracy")
        require(claims["OEM-07"]["values"] == {"optional_flow_feedback_exists": True, "exact_MP1_feedback_semantics": "Q"},
                "optional flow feedback forbids automatic power interpretation")
        require(claims["OEM-08"]["values"] == {"text_range": [100, 1500], "table_range": [100, 4000]},
                "retain internal input-frequency discrepancy")
        require(len(manifest["conditional_methods"]) == 1, "one documented conditional method")
        method = manifest["conditional_methods"][0]
        require(method["profile"] == method["method_id"] == "STANDARD_UPM3_POWER_FEEDBACK" and method["status"] == "DER",
                "conditional method profile/type")
        require(method["source_ids"] == [book] and method["normal_domain_percentagepoint"]
                == {"lower_exclusive": 0, "upper_exclusive": 70}, "normal unsaturated samples only")
        require(method["units"] == {"feedback": "percentagepoint", "power": "W", "duration": "h", "energy": "kWh",
                                     "slope": "W/percentagepoint"}, "conditional method dimensions")
        require(type(method["slope_W_per_percentagepoint"]) in (int, float)
                and method["slope_W_per_percentagepoint"] == 1 and method["energy_Wh_to_kWh"] == 0.001,
                "conditional unit conversion")
        require(method["numeric_result"] is None and "numerical_result" not in method
                and method["applied_to_MP1"] is False, "not an applied installed result")
        required_conditions = {
            "STANDARD_POWER_FEEDBACK_BINDING": "Exact MP1 is independently bound to the standard UPM3 power-feedback profile.",
            "NORMAL_UNSATURATED_SAMPLES": "Only normal samples with 0 < D_fb < 70 percentagepoints; alarm, standby and saturation codes are excluded.",
            "QUALIFIED_ACQUISITION_TIME_COVERAGE": "Signal acquisition, sample durations, time coverage, missing-data treatment and uncertainty are qualified.",
        }
        conditions = method["conditions"]
        require(len(conditions) == len(required_conditions)
                and {c["condition_id"]: c["requirement"] for c in conditions} == required_conditions,
                "all mandatory method conditions and their meanings must be preserved")
        require(derivation["source_ids"] == method["source_ids"], "claim and authoritative method source lineage")
        require(method["formula"] == "P1_i[W] = (1 W/percentagepoint)*D_fb_i[percentagepoint]; E_valid[kWh] = 1e-3*sum(P1_i[W]*delta_t_i[h])",
                "documented conditional formula")
        require(len(manifest["configurations"]) == 1, "one named conditional candidate configuration")
        config = manifest["configurations"][0]
        require(config["status"] == "SCN" and config["canonical_configuration_selected"] is False
                and config["candidate_component_is_exact_MP1"] is False and config["exact_MP1_equivalence_status"] == "Q",
                "hardware candidate is not exact or selected")
        output = manifest["current_output_contract"]
        require(output["rating_reference_E2"] == "UNCHANGED"
                and output["accepted_rating_E2_continuation_blocked"] is False, "accepted rating E2 must continue")
        require(output["annual_signed_residual"] == {"status": "Q", "sign": "SIGNED_UNKNOWN", "value_kwh": None}
                and output["hourly_signed_residual"] == {"status": "Q", "timing": None}, "annual/hourly residuals remain unknown")
        require(output["installed_heat_service"] == {"status": "Q", "installed_heat_delivery_kwh": None,
                                                       "installed_service_completion": None}, "installed thermal/service remains Q")
        require(output["national_admission"] is False and output["already_included_unit_control_safety"] is True
                and output["no_blanket_extra_FTC_load"] is True and output["no_W35_allowance_extrapolation_to_W55"] is True,
                "rating overlap and national boundary")
        require(set(output["rating_boundary_source_ids"]) <= source_ids, "reuse existing rating source IDs")
        require({e["condition"] for e in output["e2_assessment"]} == set(range(1, 9)), "all eight E2 conditions")
        debt_assessment = next(e for e in output["e2_assessment"] if e["condition"] == 7)
        require(debt_assessment["verdict"] == "REGISTERED_IN_LOCAL_CANDIDATE"
                and debt_assessment["reason"] == "Three E3/Q debt rows and B05-D01/D03 research references are present in the local candidate; no completed full-suite validation, merge or task acceptance is claimed.",
                "debt assessment must describe registered local candidate, not historical research-only state")
        debts = {d["id"]: d for d in manifest["validation_debt"]}
        require(set(debts) == set(expected_debts), "installed debt inventory")
        audit_rows = read_csv(REGISTRY / "project_blocker_evidence_audit.csv")[1]
        for did, expected in expected_debts.items():
            debt = debts[did]
            matches = [r for r in audit_rows if r["blocker_id"] == did]
            require(len(matches) == 1, f"unique audit debt {did}")
            require(debt["status"] == "Q" and debt["evidence_tier"] == "E3"
                    and debt["blocks_accepted_rating_E2"] is False and debt["scope_of_blocking"] == expected[3],
                    f"debt applies only to declared target {did}")
            require(debt["blocks_complete_installed_claim"] is (expected[1] == "yes"), f"debt blocking scope {did}")
            if len(matches) == 1:
                row = matches[0]
                require((row["blocker_class"], row["model_blocker"], row["finalization_blocker"]) == expected[:3]
                        and row["evidence_tier"] == "E3" and row["current_status"] == "OPEN", f"audit classification {did}")
                require(row["source_registry"] == "b05_wm50_installed_boundary_evidence.json"
                        and row["linked_question_id"] == "" and row["module_id"] == "B05", f"audit linkage {did}")
                require(expected[3] in row["reason"] and "ACCEPTED_RATING_E2_CONTINUES" in row["canonical_use"],
                        f"blocker cannot restrict accepted rating E2 {did}")
                require(row["validation_debt"] == debt["scope"] and row["closure_requirement"] == debt["required"],
                        f"debt acquisition plan consistent {did}")
        plan = json.loads((REGISTRY / "v1_research_plan.json").read_text(encoding="utf-8"))
        tasks = {s["slice_id"]: s for mod in plan["modules"] for s in mod["slices"]}
        for sid, required in (("B05-D03", set(expected_debts)), ("B05-D01", {"B05-WM50-INSTALLED-HOURLY"})):
            task = tasks[sid]
            require(task["status"] == "INTEGRATING" and task["accepted_artifacts"] == task["consumer_tests"] == []
                    and task["reviewed_commit"] is None, f"no whole-task acceptance {sid}")
            require(required <= set(task["validation_debt_ids"]), f"research debt link {sid}")
            require(any(x.get("evidence") == "docs/source_packs/B05_WM50_INSTALLED_BOUNDARY_EVIDENCE.md"
                        for x in task["research_log"]), f"research journal evidence link {sid}")
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, StopIteration) as exc:
        errors.append(f"{prefix}: invalid or incomplete manifest: {exc}")


def validate_b05_r290_references(errors: list[str], source_ids: set[str]) -> None:
    """Check a bounded manufacturer inventory; no loader or runtime admission."""
    prefix = "B05 R290 reference"
    def require(condition, message):
        if not condition:
            errors.append(f"{prefix}: {message}")

    m1 = "SRC-B05-MITSUBISHI-WZ-DATABOOK-2025"
    m2 = "SRC-B05-MITSUBISHI-WZ50-PI-2025"
    m3 = "SRC-B05-MITSUBISHI-FTC7-MANUAL-2024"
    h1 = "SRC-B05-MITSUBISHI-HU-CATALOGUE-2024"
    authority = {
        "applicability_status": "Q", "usable_for_engine": False,
        "model_default_admitted": False, "product_selected": False,
        "wm50_replaced": False, "annual_performance_admitted": False,
        "installed_cost_qualified": False, "current_complete_hu_price_qualified": False,
        "procurement_2028_legal_eligibility_certified": False, "scenario_widened": False,
        "readiness_closed": False, "task_accepted": False,
    }
    # Independent source-native identity and six-row oracle; not derived from the manifest digest.
    expected_sources = {
        m1: ("d6cc1ca7c6bb2e2af75e15930c0031623de6c25bbf49b636bb42c56004077886", 44665136, "2025-05", "month", "https://library.mitsubishielectric.co.uk/pdf/download_full/5483", "2026-10-05T18:02:29.140130+00:00"),
        m2: ("dabe22096af02a3954365c5cb0f36f89d447b201ebf599dbf75893c473f0d0c6", 775721, "2025-01", "month", "https://library.mitsubishielectric.co.uk/pdf/download_full/4927", "2026-10-05T18:02:35.793186+00:00"),
        m3: ("17cab38d2b723369e6036ec2c7886164a732ed8891a9d4d6e0707948af630082", 5351021, None, "unknown", "https://library.mitsubishielectric.co.uk/pdf/download_full/4950", "2026-10-05T18:05:16.093047+00:00"),
        h1: ("50f77a80e559b1179114cfe8efd2b644f3dab972775979e4f1e5d8cbad22f9c4", 9408582, "2024-12", "month", "https://mklima.hu/storage/app/uploads/public/689/995/2d6/6899952d6676a549765922.pdf", "2026-10-05T18:04:29.916224+00:00"),
    }
    expected_source_descriptions = {'SRC-B05-MITSUBISHI-WZ-DATABOOK-2025': ('Ecodan ATW Databook PUZ-WZ Vol.1.0',
                                             'Mitsubishi Electric',
                                             'Manufacturer original hosted by Mitsubishi Electric UK; models and geography must be preserved'),
     'SRC-B05-MITSUBISHI-WZ50-PI-2025': ('PUZ-WZ50VAA product information sheet',
                                         'Mitsubishi Electric Europe UK/Ireland',
                                         'UK/Ireland product sheet, not HU pricing or certification'),
     'SRC-B05-MITSUBISHI-HU-CATALOGUE-2024': ('Hungarian air-to-water heat pump catalogue',
                                              'Mitsubishi Electric Europe B.V., manufacturer-authored catalogue hosted at mklima.hu',
                                              'Hungarian translation/distributor-hosted manufacturer material; not independent performance corroboration '
                                              'or price list'),
     'SRC-B05-MITSUBISHI-FTC7-MANUAL-2024': ('PAC-IF081/082/083B-E installation manual DG79H200H02',
                                             'Mitsubishi Electric',
                                             'Manufacturer original; installer manual, not evidence of a fully priced system')}
    expected_document_roles = {
        m1: ("Issued May 2025; M-E0977 SIZ2025<MEE>; PDF metadata creation 2025-05-16, modification 2025-06-13", "ISSUE_MONTH", "Issued May 2025; creation/modification metadata is not issue date"),
        m2: ("Effective January 2025; original PDF metadata created/modified 2026-02-03", "EFFECTIVE_MONTH", "Effective January 2025; PDF created/modified February 2026, not a new effective date"),
        m3: ("DG79H200H02; PDF metadata April 2024", "ISSUE_DATE_UNKNOWN", "Revision DG79H200H02; April 2024 PDF metadata, exact issue date not established"),
        h1: ("HU-00386 // 12/2024; PDF metadata Jan/Apr 2025; HTTP Last-Modified 2025-08-11", "ISSUE_MONTH", "HU-00386 // 12/2024; August 2025 HTTP hosting timestamp is not issue date"),
    }
    expected_anchors = {
        "M1-A7-W35": (m1, "capacity table", "M1_CAPACITY_2018", "7", None, None, "4.00", "5.10", "0.78", "11.5", "NOT_STATED_IN_CAPACITY_TABLE"),
        "M1-A2-W35": (m1, "capacity table", "M1_CAPACITY_2018", "2", None, None, "5.00", "3.15", "1.59", "14.3", "NOT_STATED_IN_CAPACITY_TABLE"),
        # M1 p40/A-36: these W35 cells are white; p38/A-34 does not
        # state that non-grey data excludes defrost operation.
        "M1-A-7-W35-PARTLOAD1": (m1, "Partload1", "M1_GRID_REFERENCE", "-7", None, None, "5.0", "2.70", None, None, "NOT_GRAY_NOT_ZERO_DEFROST"),
        "M1-A-7-W35-MAX": (m1, "Max", "M1_GRID_REFERENCE", "-7", None, None, "5.2", "2.68", None, None, "NOT_GRAY_NOT_ZERO_DEFROST"),
        "M2-A-7-W35-NORMAL": (m2, "normal heating conditions", "M2_PI_NORMAL_HEATING", "-7", "-8", "30", "5.2", "2.68", "1.94", None, "NOT_STATED"),
        "M1-A-25-W35-MAX": (m1, "Max", "M1_GRID_REFERENCE", "-25", None, None, "3.2", "1.85", None, None, "NOT_GRAY_NOT_ZERO_DEFROST"),
    }
    try:
        manifest = json.loads((REGISTRY / "b05_r290_reference_manifest.json").read_text(encoding="utf-8"))
        require(set(manifest) == {"schema_version", "handoff_id", "status", "owner_module", "research_slice_id", "source_fact_policy", "target_authority", "sources", "identity", "anchor_units", "methods", "anchors", "anchors_sha256", "configurations", "context", "conflicts", "validation_debt", "allowed_next_use"}, "unexpected/missing manifest fields")
        require(manifest["schema_version"] == 1 and manifest["handoff_id"] == "B05-R290-MANUFACTURER-REFERENCE-2026" and manifest["status"] == "QUALIFIED_SOURCE_REFERENCES_ONLY", "invalid reference identity/status")
        require(manifest["owner_module"] == "B05" and manifest["research_slice_id"] == "B05-D02", "invalid module/slice")
        require(manifest["target_authority"] == authority and all(type(manifest["target_authority"][k]) is type(v) for k, v in authority.items()), "retain Q authority and no admission/default/selection/closure")
        sources = manifest["sources"]
        by_id = {s["source_id"]: s for s in sources}
        require(set(by_id) == set(expected_sources) and len(sources) == 4, "four unique source identities required")
        global_rows = read_csv(REGISTRY / "sources.csv")[1]
        local_rows = read_csv(REGISTRY / "heat_pump_sources.csv")[1]
        source_fields = {"source_id", "title", "authority", "original_url", "retrieved_at", "document_date", "document_date_precision", "document_date_basis", "document_revision", "reference_period", "geography_and_authority", "source_tier", "sha256", "bytes", "repo_snapshot_path", "reuse_status", "reuse_note", "document_date_role"}
        for sid, source in by_id.items():
            require(set(source) == source_fields, f"unexpected/missing source fields {sid}")
            fields = ("sha256", "bytes", "document_date", "document_date_precision", "original_url", "retrieved_at")
            require(tuple(source[k] for k in fields) == expected_sources.get(sid), f"source identity/date changed {sid}")
            require(type(source["bytes"]) is int, f"source byte count must be integer {sid}")
            require(tuple(source[k] for k in ("document_revision", "document_date_role", "document_date_basis")) == expected_document_roles.get(sid), f"source revision/date role changed {sid}")
            require(source["reference_period"] == source["document_revision"], f"source revision/period binding changed {sid}")
            require(tuple(source[k] for k in ("title", "authority", "geography_and_authority")) == expected_source_descriptions.get(sid), f"original document/authority/geography binding changed {sid}")
            matches = [[r for r in rows if r["source_id"] == sid] for rows in (global_rows, local_rows)]
            require(sid in source_ids and all(len(rows) == 1 for rows in matches), f"missing/duplicate source registry identity {sid}")
            if not all(len(rows) == 1 for rows in matches):
                continue
            global_row, local_row = (rows[0] for rows in matches)
            for key, field in (("title", "title"), ("authority", "institution"), ("original_url", "url"), ("reference_period", "reference_period"), ("source_tier", "source_tier")):
                require(source[key] == global_row[field] == local_row[field], f"registry {field} mismatch {sid}")
            require(global_row["local_snapshot_sha256"] == source["sha256"], f"registry hash mismatch {sid}")
            require(global_row["retrieved_at"] == local_row["retrieved_at"] == source["retrieved_at"][:10], f"registry retrieval mismatch {sid}")
            require(global_row["published_at"] == "undated", f"do not invent day precision {sid}")
            require(global_row["module_id"] == local_row["module_id"] == "B05" and local_row["layer"] == "OPERATING_CONFIG", f"source ownership/scope mismatch {sid}")
            require(global_row["evidence_status"] == local_row["evidence_status"] == "OBS" and source["source_tier"] == "P2", f"source classification mismatch {sid}")
            require(source["repo_snapshot_path"] is None and source["reuse_status"] == global_row["license"] == local_row["license_status"] == "EXTERNAL_ONLY_REPOSITORY_COPY_NOT_CLEARED", f"original-document reuse not cleared {sid}")
            for key in ("document_date_basis", "document_revision", "reference_period", "geography_and_authority", "reuse_note"):
                require(isinstance(source[key], str) and bool(source[key].strip()), f"missing source boundary {sid}/{key}")
        # Check references/fact wrappers throughout without treating dates and IDs as quantities.
        def check_facts(value):
            if isinstance(value, dict):
                if "source_id" in value:
                    require(value["source_id"] in by_id, "unknown claim source")
                    if "locator" in value:
                        require(isinstance(value["locator"], str) and value["locator"].startswith("PDF p"), "missing primary page trace")
                if "value" in value:
                    require(value["truth"] == "OBS" and value["unit"] in {"kg", "phase", "V", "Hz", "kW", "L", "L/min", "degC", "ratio", "percent", "tCO2eq", "mm", "kPa"}, "invalid native fact truth/unit")
                    require(isinstance(value["value"], str) and Decimal(value["value"]).is_finite(), "native fact must be a finite source decimal string")
                for item in value.values():
                    check_facts(item)
            elif isinstance(value, list):
                for item in value:
                    check_facts(item)
        check_facts(manifest)
        require(bool(manifest["source_fact_policy"]) and bool(manifest["allowed_next_use"]), "source-fact/non-admission explanation required")
        identity = manifest["identity"]
        require(set(identity) == {"source_id", "locator", "truth", "base_model", "covered_commercial_variant", "manufacturer_table_scope", "refrigerant", "charge", "phase", "voltage", "frequency", "connection", "refrigerant_water_exchanger", "base_variant_commercial_equivalence_inferred", "boundary"} and identity["locator"] == "PDF p6 / A-2", "identity provenance/schema changed")
        require((identity["source_id"], identity["truth"], identity["base_model"], identity["covered_commercial_variant"], identity["manufacturer_table_scope"], identity["refrigerant"], identity["connection"], identity["refrigerant_water_exchanger"]) == (m1, "OBS", "PUZ-WZ50VAA", "PUZ-WZ50VAA-BS", "PUZ-WZ50VAA(-BS)", "R290", "WATER_CONNECTED_MONOBLOCK", "BUILT_IN_OUTDOOR"), "exact outdoor/variant identity required")
        require(identity["base_variant_commercial_equivalence_inferred"] is False, "base and -BS commercial equivalence not admitted")
        for key, value, unit in (("charge", "0.6", "kg"), ("phase", "1", "phase"), ("voltage", "230", "V"), ("frequency", "50", "Hz")):
            require(identity[key] == {"value": value, "unit": unit, "truth": "OBS"}, f"native identity fact changed {key}")
        units = {"ambient_dry_bulb_c": "degC", "ambient_wet_bulb_c": "degC", "water_outlet_c": "degC", "water_inlet_c": "degC", "capacity_kw": "kW", "cop": "ratio", "electrical_input_kw": "kW", "test_flow_l_per_min": "L/min"}
        require(manifest["anchor_units"] == units, "anchor dimensional boundary changed")
        anchors = manifest["anchors"]
        require(len(anchors) == 6 and {r["anchor_id"] for r in anchors} == set(expected_anchors), "exact six-anchor selection required")
        fields = ("source_id", "mode_label", "method_id", "ambient_dry_bulb_c", "ambient_wet_bulb_c", "water_inlet_c", "capacity_kw", "cop", "electrical_input_kw", "test_flow_l_per_min", "defrost_annotation")
        for row in anchors:
            require(set(row) == set(fields) | {"anchor_id", "locator", "model_scope", "truth", "water_outlet_c", "use_scope"}, "unexpected/missing anchor fields")
            require(tuple(row[k] for k in fields) == expected_anchors.get(row["anchor_id"]), f"native anchor semantics changed {row['anchor_id']}")
            require(row["truth"] == "OBS" and row["water_outlet_c"] == "35" and row["use_scope"] == "SOURCE_REFERENCE_ONLY", "anchor truth/condition/admission changed")
            location = {
                "M1_CAPACITY_2018": "PDF p11 / A-7; capacity table",
                "M1_GRID_REFERENCE": f"PDF p40 / A-36; WZ50 {row['mode_label']} row",
                "M2_PI_NORMAL_HEATING": "PDF p2; HEATING and note 2",
            }.get(row["method_id"])
            require(row["locator"] == location, "anchor primary page trace changed")
            require(row["model_scope"] == ("PUZ-WZ50VAA" if row["source_id"] == m2 else "PUZ-WZ50VAA(-BS)"), "anchor variant scope changed")
        actual_hash = hashlib.sha256(json.dumps(anchors, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        require(manifest["anchors_sha256"] == actual_hash, "anchor integrity hash mismatch")
        methods = manifest["methods"]
        require(set(methods) == {"M1_CAPACITY_2018", "M1_GRID_REFERENCE", "M2_PI_NORMAL_HEATING"}, "method inventory changed")
        method_fields = {
            "M1_CAPACITY_2018": {"source_id", "locator", "standard", "standard_year_applies_to", "pump_input_included", "method_boundary"},
            "M1_GRID_REFERENCE": {"source_id", "locator", "standard", "values_may_include_interpolation_or_calculation", "all_points_directly_measured", "gray_includes_defrost", "not_gray_means_no_defrost", "mode_definitions", "method_boundary"},
            "M2_PI_NORMAL_HEATING": {"source_id", "locator", "standard", "native_label", "max_label_stated", "method_boundary"},
        }
        for mid, method in methods.items():
            require(set(method) == method_fields.get(mid), "unexpected/missing method fields")
        method_refs = {
            "M1_CAPACITY_2018": (m1, "PDF p11 / A-7, WZ50/60/80 capacity table"),
            "M1_GRID_REFERENCE": (m1, "PDF p38 / A-34, performance notes and modes"),
            "M2_PI_NORMAL_HEATING": (m2, "PDF p2, HEATING row and note 2"),
        }
        for mid, method in methods.items():
            require((method["source_id"], method["locator"]) == method_refs.get(mid), f"method source/page role changed {mid}")
        cap, grid, pi = (methods[k] for k in ("M1_CAPACITY_2018", "M1_GRID_REFERENCE", "M2_PI_NORMAL_HEATING"))
        require(cap["standard_year_applies_to"] == "WZ50/60/80 capacity table only; 2022 line belongs to other models", "capacity standard model/year role changed")
        require(cap["source_id"] == m1 and cap["standard"] == "EN14511 parts 1-4:2018" and cap["pump_input_included"] is True, "capacity-table standard/pump boundary changed")
        require(grid["source_id"] == m1 and grid["standard"] == "EN14511; year not specified in grid notes" and grid["values_may_include_interpolation_or_calculation"] is True and grid["all_points_directly_measured"] is False, "grid method must retain manufacturer calculation limits")
        require(grid["gray_includes_defrost"] is True and grid["not_gray_means_no_defrost"] is False, "defrost semantics changed")
        require(grid["mode_definitions"] == {"Max": "Maximum capacity", "Partload1": "Heating reference capacity defined at A-7/W35", "Min": "Minimum capacity"}, "manufacturer capacity mode definitions changed")
        require(pi["source_id"] == m2 and pi["standard"] == "Not specified for note 2 heating point" and pi["native_label"] == "normal heating conditions" and pi["max_label_stated"] is False, "PI source label/standard cannot be borrowed")
        configs = manifest["configurations"]
        require(set(configs) == {"ERPX", "ERPT20X", "PAC_IF081"}, "three separate configuration alternatives required")
        expected_config = {
            "ERPX": ("PUZ-WZ50VAA", "ERPX-VM2E", "INTEGRATED_HYDROBOX", True, False, "INTEGRATED_CONTROL_AND_MAIN_REMOTE", "SPACE_HEATING_ONLY_REFERENCE"),
            "ERPT20X": ("PUZ-WZ50VAA", "ERPT20X-VM2E", "INTEGRATED_CYLINDER_UNIT", True, True, "INTEGRATED_INDOOR_CONTROL", "SEPARATE_DHW_ALTERNATIVE"),
            "PAC_IF081": ("PUZ-WZ50VAA(-BS)", None, "STANDALONE_CONTROLLER_LOCAL_HYDRAULICS", None, False, "PAC-IF081B-E", "SEPARATE_CONTROLLER_ALTERNATIVE"),
        }
        config_refs = {
            "ERPX": [(m1, "PDF p68 / B-2; compatibility"), (m1, "PDF p72 / B-6; ERPX-VM2E specification"), (m1, "PDF p73 / B-7; combination performance"), (m1, "PDF pp152-153 / B-86-B-87; components/hydraulics")],
            "ERPT20X": [(m1, "PDF p68 / B-2; compatibility"), (m1, "PDF p70 / B-4; ERPT20X-VM2E specification"), (m1, "PDF p73 / B-7; combination performance")],
            "PAC_IF081": [(m1, "PDF p187 / C-3; WZ50 compatible controller and mandatory flow sensor"), (m3, "PDF pp3,6-8 / printed pp2,5-7; kit contents and system requirements")],
        }
        config_fields = ("outdoor", "indoor", "architecture", "hardware_reversible", "dhw_cylinder_included", "controller_arrangement", "service_scenario")
        for cid, config in configs.items():
            allowed = set(config_fields) | {"service_scenario_truth", "standalone_controller_added_to_integrated_route", "mandatory_external_controller", "components", "facts", "references", "boundary"}
            if cid == "PAC_IF081":
                allowed |= {"mandatory_flow_sensor", "complete_hydraulic_module", "locally_supplied"}
            require(set(config) == allowed, f"unexpected/missing configuration fields {cid}")
            require(type(config["dhw_cylinder_included"]) is bool and (type(config["hardware_reversible"]) is bool or config["hardware_reversible"] is None), "configuration flags must retain boolean/null types")
            require(tuple(config[k] for k in config_fields) == expected_config.get(cid), f"configuration identity/service/controller changed {cid}")
            require(config["service_scenario_truth"] == "SCN" and config["standalone_controller_added_to_integrated_route"] is False and config["mandatory_external_controller"] is None, f"integrated versus standalone or service truth changed {cid}")
            require(config["references"] == [{"source_id": sid, "locator": loc} for sid, loc in config_refs[cid]] and bool(config["boundary"]), f"configuration provenance/boundary changed {cid}")
        require(configs["ERPX"]["components"] == ["control/main remote", "primary circulation pump", "flow sensor", "expansion vessel", "booster heater", "magnetic filter"], "ERPX component scope changed")
        require(configs["ERPT20X"]["components"] == ["integrated cylinder unit"], "ERPT components cannot add standalone controller or another indoor route")
        require(configs["PAC_IF081"]["components"] == ["main remote", "supplied thermistors"], "standalone kit contents cannot become integrated hydraulics")
        for cid, expected in (("ERPX", {"booster": ("2", "kW"), "expansion_vessel": ("10", "L"), "internal_heating_water": ("4.5", "L")}), ("ERPT20X", {"dhw_cylinder": ("200", "L"), "booster": ("2", "kW"), "expansion_vessel": ("12", "L")})):
            require(configs[cid]["facts"] == {k: {"value": v, "unit": u, "truth": "OBS"} for k, (v, u) in expected.items()}, f"native indoor facts changed {cid}")
        control = configs["PAC_IF081"]
        require(control["mandatory_flow_sensor"] == "PAC-FS01-E" and control["complete_hydraulic_module"] is False and control["facts"] == {}, "standalone sensor/hydraulic boundary changed")
        require(control["locally_supplied"] == ["water circulation pump", "flow protection and hydraulic safety components", "hydraulic circuit", "DHW tank and valve if that service is required"], "standalone local-supply boundary changed")
        context = manifest["context"]
        context_fields = {
            "erp_rating": {"source_id", "locator", "outdoor", "indoor", "condition", "rated_heat_output", "legal_maximum_rated_capacity_determination"},
            "operating_limits": {"references", "heating_ambient_min", "heating_ambient_max", "dhw_ambient_min", "dhw_ambient_max", "cooling_ambient_min", "cooling_ambient_max", "max_outlet_at_ambient_minus25", "max_outlet_at_ambient_minus15", "boundary", "model_scope"},
            "family_naming": {"source_id", "locator", "control_generation", "scope", "exact_compatibility_authority", "independent_performance_corroboration"},
            "rating_crosswalk": {"references", "A7_A2_capacity_values_match", "A2_Partload1_defrost_annotation", "M2_normal_values_numerically_match", "M2_mode_relabelled", "boundary"},
            "conditional_hydraulics": {"references", "table_indoor_reference", "additional_average_or_warmer", "additional_colder", "universal_buffer_size_admitted", "site_climate_or_circuit_volume_known", "boundary", "volume_scope", "model_scope"},
            "installation": {"references", "site_safe_design_certified", "unpriced_scope", "boundary", "model_scope"},
        }
        context_fields["water_data"] = {"readings", "source_reading_correction", "m2_flow_min_or_max_label", "rounding_reconciliation_admitted", "harmonised_hydraulic_default", "boundary"}
        context_refs = {
            "operating_limits": [(m1, "PDF p6 / A-2"), (m1, "PDF p26 / A-22"), (m1, "PDF p27 / A-23")],
            "rating_crosswalk": [(m1, "PDF p40 / A-36"), (m1, "PDF p73 / B-7")],
            "conditional_hydraulics": [(m1, "PDF p158 / B-92; Table 5.6.2"), (m1, "PDF p27 / A-23"), (m1, "PDF p160 / B-94")],
            "installation": [(m1, "PDF pp62-66 / A-58-A-62; R290 installation"), (m1, "PDF p153 / B-87; hydraulic design")],
        }
        for cid, section in context.items():
            require(set(section) == context_fields.get(cid), f"unexpected/missing context fields {cid}")
            if cid in context_refs:
                require(section["references"] == [{"source_id": sid, "locator": loc} for sid, loc in context_refs[cid]], f"context exact reference role/cardinality changed {cid}")
        require(set(context) == {"erp_rating", "operating_limits", "family_naming", "rating_crosswalk", "conditional_hydraulics", "installation", "water_data"}, "context scope changed")
        erp = context["erp_rating"]
        require(erp["locator"] == "PDF p13 / A-9; PUZ-WZ50VAA(-BS) + ERPX-VM2E row", "ErP primary page/row role changed")
        require((erp["source_id"], erp["outdoor"], erp["indoor"], erp["condition"]) == (m1, "PUZ-WZ50VAA(-BS)", "ERPX-VM2E", "ErP medium-temperature average climate"), "ErP model/condition changed")
        require(erp["rated_heat_output"] == {"value": "5.0", "unit": "kW", "truth": "OBS"} and erp["legal_maximum_rated_capacity_determination"] is False, "ErP legal/output boundary changed")
        limits = context["operating_limits"]
        require(limits["model_scope"] == "PUZ-WZ50VAA(-BS)", "operating limit model scope changed")
        for key, value in {"heating_ambient_min": "-25", "heating_ambient_max": "24", "dhw_ambient_min": "-25", "dhw_ambient_max": "46", "cooling_ambient_min": "10", "cooling_ambient_max": "46", "max_outlet_at_ambient_minus25": "65", "max_outlet_at_ambient_minus15": "75"}.items():
            require(limits[key] == {"value": value, "unit": "degC", "truth": "OBS"}, f"operating mode limit changed {key}")
        naming = context["family_naming"]
        require(naming["locator"] == "PDF pp8,30; model/controller naming and R290 family" and naming["scope"] == "E-generation indoor / R290 Power Inverter monoblock family", "family naming exact page/scope changed")
        require(naming["source_id"] == h1 and naming["control_generation"] == "FTC7" and naming["exact_compatibility_authority"] == m1 and naming["independent_performance_corroboration"] is False, "supplementary naming cannot become compatibility/performance authority")
        crosswalk = context["rating_crosswalk"]
        require(crosswalk["A7_A2_capacity_values_match"] == "Partload1" and crosswalk["A2_Partload1_defrost_annotation"] == "GRAY_INCLUDES_DEFROST" and crosswalk["M2_normal_values_numerically_match"] == "M1 Max at A-7/W35" and crosswalk["M2_mode_relabelled"] is False, "numeric agreement cannot overwrite native labels")
        hydraulic = context["conditional_hydraulics"]
        require(hydraulic["volume_scope"] == "GENERIC_INDOOR_REFERENCE_WITH_WZ50_ADDITIONAL_WATER_TABLE" and hydraulic["model_scope"] == "PUZ-WZ50 row; generic indoor reference, not ERPX-VM2E actual internal volume", "generic hydraulic volume cannot be assigned to actual product")
        require(context["installation"]["model_scope"] == "PUZ-WZ50VAA(-BS) and ERPX hydraulic design context", "installation model scope changed")
        require(context["installation"]["unpriced_scope"] == ["site piping", "insulation", "drainage", "electrical work", "emitters", "commissioning", "conditional buffer"], "unpriced installation scope changed")
        for key, value in (("table_indoor_reference", "5"), ("additional_average_or_warmer", "2"), ("additional_colder", "24")):
            require(hydraulic[key] == {"value": value, "unit": "L", "truth": "OBS"}, f"conditional hydraulic fact changed {key}")
        require(hydraulic["universal_buffer_size_admitted"] is False and hydraulic["site_climate_or_circuit_volume_known"] is False and context["installation"]["site_safe_design_certified"] is False, "site/hydraulic admission not established")
        # Exact source/page/model/quantity roles, independently bound to the native rows.
        water = context["water_data"]
        expected_water = [
            (m1, "PDF p6 / A-2", "PUZ-WZ50VAA(-BS)", "Water Flow rate range", "6.5", "L/min", "RANGE_MINIMUM"),
            (m1, "PDF p6 / A-2", "PUZ-WZ50VAA(-BS)", "Water Flow rate range", "14.3", "L/min", "RANGE_MAXIMUM"),
            (m3, "PDF p7 / printed p6; Table 3.4.1", "PUZ-WZ50", "Water flow rate range [L/min]", "6.5", "L/min", "RANGE_MINIMUM"),
            (m3, "PDF p7 / printed p6; Table 3.4.1", "PUZ-WZ50", "Water flow rate range [L/min]", "14.3", "L/min", "RANGE_MAXIMUM"),
            (m2, "PDF p2; WATER DATA", "PUZ-WZ50VAA", "Pipework Size (mm)", "22", "mm", "PIPEWORK_SIZE"),
            (m2, "PDF p2; WATER DATA", "PUZ-WZ50VAA", "Flow Rate (l/min)", "14", "L/min", "SINGLE_FLOW_RATE"),
            (m2, "PDF p2; WATER DATA", "PUZ-WZ50VAA", "Water Pressure Drop (kPa)", "18.16", "kPa", "WATER_PRESSURE_DROP"),
        ]
        water_fields = ("source_id", "locator", "model_scope", "source_label", "value", "unit", "quantity_role")
        require([tuple(r[k] for k in water_fields) for r in water["readings"]] == expected_water, "native water-data source/page/model/unit/role changed")
        for reading in water["readings"]:
            require(set(reading) == set(water_fields) | {"truth", "test_condition"} and reading["truth"] == "OBS" and reading["test_condition"] is None, "water-data condition/truth/schema changed")
        require(water["m2_flow_min_or_max_label"] is None and water["rounding_reconciliation_admitted"] is False and water["harmonised_hydraulic_default"] is None, "single M2 flow cannot acquire minimum/maximum, rounding or default authority")
        require(water["source_reading_correction"] == "M2 has no Min/Max flow labels; an earlier qualification misread pipework size as flow. That qualification is withdrawn, not treated as a manufacturer discrepancy.", "false earlier flow conclusion must remain withdrawn")
        expected_conflicts = {
            "GWP_CO2EQ": [
                (m1, "PDF p6 / A-2; refrigerant row", "PUZ-WZ50VAA(-BS)", "R290 (GWP)", "3", "ratio"),
                (m2, "PDF p2; refrigerant row and legal footer", "PUZ-WZ50VAA", "R290 GWP / IPCC6", "0.02", "ratio"),
                (m2, "PDF p2; refrigerant charge / CO2 equivalent", "PUZ-WZ50VAA", "charge", "0.6", "kg"),
                (m2, "PDF p2; refrigerant charge / CO2 equivalent", "PUZ-WZ50VAA", "CO2 equivalent", "0.0018", "tCO2eq"),
            ],
            "COOLING_INPUT_A35_W18": [
                (m1, "PDF p11 / A-7; A35/W18", "PUZ-WZ50VAA(-BS)", "outdoor power input", "0.35", "kW"),
                (m1, "PDF p73 / B-7; A35/W18", "PUZ-WZ50VAA(-BS) + listed indoor combinations", "combination power input", "1.31", "kW"),
            ],
            "DHW_EFFICIENCY_EHPT20X": [
                (m1, "PDF p13 / A-9; WZ50 + EHPT20X-MEHEW", "PUZ-WZ50VAA(-BS) + EHPT20X-MEHEW", "water heating efficiency", "134", "percent"),
                (m2, "PDF p2; combination heater and note 1", "PUZ-WZ50VAA + EHPT20X-MEHEW", "water heating efficiency", "143", "percent"),
            ],
            "INDOOR_WATER_REFERENCE": [
                (m1, "PDF p72 / B-6", "ERPX-VM2E", "internal heating water", "4.5", "L"),
                (m1, "PDF p158 / B-92; Table 5.6.2", "generic indoor reference used with PUZ-WZ50 row", "indoor unit water amount", "5", "L"),
            ],
        }
        conflicts = manifest["conflicts"]
        require(len(conflicts) == 4 and {c["conflict_id"] for c in conflicts} == set(expected_conflicts), "unresolved discrepancies cannot be omitted")
        for conflict in conflicts:
            cid = conflict["conflict_id"]
            require(set(conflict) == {"conflict_id", "readings", "status", "harmonised_default", "source_repaired", "boundary"}, f"unexpected/missing conflict fields {cid}")
            require([(r["source_id"], r["locator"], r["model_scope"], r["source_label"], r["value"], r["unit"]) for r in conflict["readings"]] == expected_conflicts.get(cid), f"literal source discrepancy changed {cid}")
            require(conflict["status"] == "UNRESOLVED_SOURCE_DISCREPANCY" and conflict["harmonised_default"] is None and conflict["source_repaired"] is False and bool(conflict["boundary"]), f"source discrepancy cannot be repaired/defaulted {cid}")
            for reading in conflict["readings"]:
                require(set(reading) == {"source_id", "locator", "model_scope", "source_label", "value", "unit", "truth"}, "unexpected/missing native discrepancy fields")
            if cid == "DHW_EFFICIENCY_EHPT20X":
                require([r["model_scope"] for r in conflict["readings"]] == ["PUZ-WZ50VAA(-BS) + EHPT20X-MEHEW", "PUZ-WZ50VAA + EHPT20X-MEHEW"], "DHW conflict cannot transfer to another cylinder")
        debts = manifest["validation_debt"]
        require(len(debts) == 3 and {d["debt_id"] for d in debts} == {"B05-R290-TARGET-INSTALLATION", "B05-R290-SOURCE-CONFLICTS", "B05-R290-PRICE-PROCUREMENT"} and all(d["status"] == "Q" and d["scope"] and d["next_evidence"] for d in debts), "validation debt cannot be closed")
    except (ValueError, TypeError, KeyError, OSError, InvalidOperation) as exc:
        errors.append(f"{prefix}: invalid or incomplete manifest: {exc}")


def validate_b05_eoh_observed_boundary_evidence(errors: list[str], source_ids: set[str]) -> None:
    """Evidence metadata only: no raw parser, physical validation or calibration."""
    prefix = "B05 EOH observed evidence"

    def require(condition, message):
        if not condition:
            errors.append(f"{prefix}: {message}")

    try:
        m = json.loads((REGISTRY / "b05_eoh_observed_boundary_manifest.json").read_text(encoding="utf-8"))
        require(m["schema_version"] == 1 and m["handoff_id"] == "B05-EOH-OBSERVED-BOUNDARY-EVIDENCE"
                and m["status"] == "EVIDENCE_RECORDING_ONLY", "evidence-only identity")
        i = m["inspection"]
        require(i["consumer_textual_excerpts_reviewed"] is True
                and i["consumer_original_bytes_hashed"] is False
                and i["consumer_full_artifact_files_inspected"] is False
                and i["consumer_library_zip_materialized"] is False, "consumer inspection scope")
        require(i["reviewer_original_artifacts_inspected"] is True
                and i["reviewer_manifest_files_checked"] == 53 and i["reviewer_manifest_mismatches"] == 0
                and i["reviewer_check_is_independent_physical_measurement"] is False
                and i["producer_paths_are_consumer_local"] is False, "reviewer attribution")
        sources = {s["source_id"]: s for s in m["sources"]}
        require(len(sources) == len(m["sources"]) and set(sources) <= source_ids, "unique registered sources")
        require("SRC-B02-DESNZ-EOH-PDI-2024" in sources
                and "SRC-B02-DESNZ-EOH-PERF-2024" not in sources, "PDI reuse; summary not two-minute authority")
        require(len({s["original_url"] for s in sources.values()}) == len(sources), "distinct document roles")
        global_rows = read_csv(REGISTRY / "sources.csv")[1]
        local_rows = read_csv(REGISTRY / "heat_pump_sources.csv")[1]
        for sid, s in sources.items():
            require(s["repo_snapshot_path"] is None and s["reuse_status"], f"external source policy {sid}")
            if s.get("sha256") is not None:
                require(bool(re.fullmatch(r"[0-9a-f]{64}", s["sha256"]))
                        and type(s["bytes"]) is int and s["bytes"] > 0, f"reported byte identity {sid}")
            require(s["original_url"].startswith("https://"), f"URL {sid}")
            if sid.startswith("SRC-B05-"):
                for rows in (global_rows, local_rows):
                    found = [r for r in rows if r["source_id"] == sid]
                    require(len(found) == 1, f"registry linkage {sid}")
                    if len(found) == 1:
                        r = found[0]
                        require(r["url"] == s["original_url"] and r["title"] == s["title"]
                                and r["institution"] == s["authority"] and r["reference_period"] == s["reference_period"]
                                and r["evidence_status"] == s["evidence_status"], f"registry provenance {sid}")
                        if "local_snapshot_sha256" in r:
                            require(r["local_snapshot_sha256"] == (s["sha256"] or ""), f"registry digest {sid}")
        monitor = sources["SRC-B05-DESNZ-EOH-MONITORING-2024"]
        require(monitor["sha256"] is None and monitor["byte_identity"] == "NOT_ACQUIRED"
                and monitor["diagram_inspection_claimed"] is False, "no invented PDF hash/diagram inspection")
        bundle = sources["SRC-B05-EOH-ALL-YEARS-EVIDENCE-2026"]
        require(bundle["library_version"] == 0
                and bundle["hash_basis"] == "OWNER_REPORTED_NOT_CONSUMER_VERIFIED", "bundle not local verification")
        require(m["processing_reference"]["exact_released_archive_code_binding"] == "Q"
                and m["processing_reference"]["individual_alteration_histories"] == "Q", "code/archive binding debt")
        arts = {a["file"]: a for a in m["artifacts"]}
        require(len(arts) == len(m["artifacts"]), "unique derivative artifacts")
        for name, a in arts.items():
            require(bool(re.fullmatch(r"[0-9a-f]{64}", a["sha256"]))
                    and a["hash_basis"] == "REVIEWER_REPORTED_ORIGINAL_FILE_BYTES"
                    and a["consumer_full_file_inspected"] is False
                    and type(a["consumer_textual_excerpt_inspected"]) is bool
                    and a["repo_snapshot_path"] is None, f"artifact inspection provenance {name}")
        claims = {c["id"]: c for c in m["claims"]}
        require(len(claims) == len(m["claims"]) and set(claims) == {f"EOH-{n:02d}" for n in range(1, 10)},
                "bounded claim inventory")
        for c in claims.values():
            require(c["status"] in {"OBS", "DER", "Q"} and c["unit"] and c["locator"]
                    and c["artifact"] in arts and c["source_ids"] and set(c["source_ids"]) <= set(sources)
                    and c["independent_physical_replication"] is False, f"claim provenance {c['id']}")
            obj = m
            for part in c["manifest_locator"].split("."):
                obj = obj[part]
        require(claims["EOH-05"]["status"] == "OBS" and claims["EOH-09"]["status"] == "Q"
                and all(claims[f"EOH-{n:02d}"]["status"] == "DER" for n in (1, 2, 3, 4, 6, 7, 8)),
                "native identity versus diagnostic derivation")
        pdi_claim = claims["EOH-05"]
        pdi_artifact = arts[pdi_claim["artifact"]]
        require(pdi_claim["artifact"] == "pdi_public_current_2026-10-14.csv"
                and pdi_claim["source_ids"] == ["SRC-B02-DESNZ-EOH-PDI-2024"]
                and pdi_claim["snapshot_date"] == "2026-10-14"
                and pdi_claim["row_key"] == {"Property_ID": "EOH2074"}
                and set(pdi_claim["original_fields"]) == set(m["target"]["pdi_fields"])
                and pdi_artifact["source_id"] == "SRC-B02-DESNZ-EOH-PDI-2024"
                and pdi_artifact["sha256"] == sources["SRC-B02-DESNZ-EOH-PDI-2024"]["sha256"]
                and pdi_artifact["role"] == "EXTERNAL_SOURCE_SNAPSHOT_NOT_DERIVATIVE_BUNDLE_MEMBER",
                "PDI identity claim must resolve to dated original PDI row, not target diagnostic JSON")
        pop = m["populations"]
        require(pop["status"] == "DER" and (pop["members"], pop["nonempty_systems"], pop["rows"],
                pop["system_years"]) == (185, 184, 102564000, 538), "observed package scope")
        primary = pop["primary"]
        require((primary["systems"], primary["windows"], primary["intervals"]) == (33, 4546, 96019),
                "primary population not all installations")
        ids = [p for g in m["primary_identity_groups"] for p in g["property_ids"]]
        require(len(ids) == len(set(ids)) == 33
                and all(g["service_scope"] == "hybrid_SH_separate_meters" for g in m["primary_identity_groups"]),
                "unique separate-meter cohort")
        require({s["property_id"] for s in m["sime_exceptions"]} == {"EOH2004", "EOH1751"}
                and not ({s["property_id"] for s in m["sime_exceptions"]} & set(ids)), "SIME remains separate")
        require(m["metering"]["PDI_model_is_automatically_outdoor_identity"] is False,
                "PDI model not automatic outdoor identity")
        target = m["target"]
        require(target["property_id"] == target["pdi_fields"]["Property_ID"] == "EOH2074"
                and target["pdi_fields"]["HP_Model"] == "PUZ-WM50VHA-BS"
                and target["service_scope"] == "mixed_SH_DHW_unallocated"
                and target["timezone"] == target["exact_indoor_controller_pairing"] == "Q"
                and target["W55_transfer_admitted"] is False, "target identity/service qualification")
        require(all(s["runs_10min"] == 0 for s in target["near55_screens"].values()), "no sustained target W55 evidence")
        d = m["definitions"]
        require(d["window_key"] == ["property_id", "boundary_screen", "start", "end"]
                and d["adjacency"]["seconds"] == 120 and d["adjacency"]["gap_fill"] is False
                and d["adjacency"]["signed_counter_changes_retained"] is True, "original interval/key semantics")
        require(d["near55"]["mask_before_segmentation"] is True and d["near55"]["COP_selection"] is False
                and d["near55"]["scope"] == "RESEARCH_DIAGNOSTIC_NOT_EN14511_TOLERANCE_OR_E2_GATE"
                and d["heating_proxy"]["true_mode_telemetry"] is False, "screen not admission or mode telemetry")
        require(d["e_minus_cp"]["compressor_only"] is False and d["e_minus_cp"]["overlaps_whole_E_population"] is True,
                "E-minus-CP interpretation and overlap")
        common = d["common_interval"]
        require(common["zero_or_negative_heat"] == "he AND dH <= 1e-8 kWh"
                and common["calendar_assignment"] == "CURRENT endpoint"
                and common["state_ledger_exists"] is False and common["IH_BUH_common_intersection_exists"] is False
                and common["E_minus_CP_uses"] == "Exactly hec sums", "common audit is not a state ledger")
        require(d["cells"]["script"] == "summarize_archive.py" and d["cells"]["independent_validation"] is False
                and d["cells"]["right"] is False and d["cells"]["clock_block"] == "start.hour//6",
                "descriptive cell method")
        require(d["year_drift"]["year"] == "WINDOW START YEAR" and d["year_drift"]["residual_drift"] is False
                and d["year_drift"]["configuration_or_duty_explanation_measured"] is False
                and d["exact_count_support"]["unit"] == "interval COUNT"
                and d["exact_count_support"]["window_energy_split_across_year_or_clock"] is False,
                "start-year ratio drift versus exact count support")
        require(set(d["not_existing_columns"]) == {"configuration_segment_id", "validated_duty_state",
                "interval_level_window_id", "per_home_LOSO_output"}, "do not invent produced columns")
        rows = m["selected_rows"]
        require(rows["year"]["key"] == rows["IH"]["key"] == {"property_id": "EOH2074", "year": 2022}
                and rows["year"]["artifact"] == "all_period_common_interval_year.csv"
                and rows["IH"]["artifact"] == "system_year_coverage.csv"
                and rows["IH"]["HP_E_IH_common_intersection"] == "NOT_COMPUTED", "separate original masks")
        for w in rows["windows"]:
            require(w["artifact"] in arts and list(w["key"]) == d["window_key"], "original window composite key")
            require(arts[w["artifact"]]["consumer_textual_excerpt_inspected"] is True,
                    "selected window excerpts were read; not a full-file inspection")
        cp = next(w for w in rows["windows"] if w["key"]["start"] == "2021-10-07 04:32:00")["fields"]
        require(cp["CP_all_steps_observed"] is False and cp["CP_common_residual_E_kWh"] is None,
                "incomplete CP residual remains null")
        require(m["debt_links"] == ["B05-WM50-OEM-PROFILE", "B05-WM50-INSTALLED-ANNUAL",
                "B05-WM50-INSTALLED-HOURLY"], "existing debt links")
        n = m["non_admission"]
        required_false_flags = {
            "runtime_parser_added", "usable_for_engine", "model_default_admitted", "numerical_calibration",
            "annual_residual_admitted", "W55_transfer_admitted", "hourly_timing_admitted",
            "installed_service_completion_admitted", "national_admission", "task_accepted",
            "readiness_credit", "required_raw_samples_for_evidence_recording",
        }
        require(set(n) == required_false_flags | {"rating_reference_E2", "exact_OEM_route"},
                "complete explicit non-admission key set required")
        require(all(n.get(k) is False for k in required_false_flags)
                and n["rating_reference_E2"] == "UNCHANGED" and n["exact_OEM_route"] == "OPTIONAL",
                "evidence only; no runtime/numeric/task admission")
        wm = json.loads((REGISTRY / "b05_wm50_installed_boundary_evidence.json").read_text(encoding="utf-8"))
        link = wm["aggregate_evidence_updates"][-1]
        require(link["evidence_manifest"] == "registry/b05_eoh_observed_boundary_manifest.json"
                and link["numerical_installed_admission"] is False, "dated aggregate link")
        out = wm["current_output_contract"]
        require(out["annual_signed_residual"]["value_kwh"] is None
                and out["hourly_signed_residual"]["timing"] is None
                and out["installed_heat_service"]["installed_service_completion"] is None
                and out["rating_reference_E2"] == "UNCHANGED", "existing outputs remain Q")
        audit = read_csv(REGISTRY / "project_blocker_evidence_audit.csv")[1]
        for row in audit:
            if row["blocker_id"] in m["debt_links"]:
                require(row["current_status"] == "OPEN" and row["evidence_tier"] == "E3", "no debt closure")
        plan = json.loads((REGISTRY / "v1_research_plan.json").read_text(encoding="utf-8"))
        tasks = {s["slice_id"]: s for mod in plan["modules"] for s in mod["slices"]}
        for sid in m["research_slice_ids"]:
            task = tasks[sid]
            require(task["status"] == "INTEGRATING" and not task["accepted_artifacts"]
                    and not task["consumer_tests"] and task["reviewed_commit"] is None
                    and any(r.get("decision") == "EOH_EVIDENCE_RECORDED_NO_NUMERICAL_ADMISSION"
                            for r in task["research_log"]), f"bounded research update {sid}")
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, StopIteration) as exc:
        errors.append(f"{prefix}: invalid or incomplete manifest: {exc}")



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
