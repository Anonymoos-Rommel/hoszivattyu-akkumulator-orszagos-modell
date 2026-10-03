"""V1-024: prevent the audited 109 function cases from disappearing from CI."""

import importlib
import inspect
import unittest


EXPECTED_CASES = {
    "test_b05_p10_nibe_cold_high_supply_capacity_domain": (
        "test_p10_preserves_complete_triple_and_defrost_boundaries",
        "test_p10_source_and_pack_are_fail_closed",
        "test_p10_three_supply_domains_cover_p9_stress",
        "test_p10_updates_live_question_and_readiness_without_uplift",
    ),
    "test_b05_p6_defrost_cycling": (
        "test_below_minimum_modulation_is_state_only_until_cycling_evidence_exists",
        "test_cdh_measured_is_unknown_and_regulatory_default_is_pol_only",
        "test_cold_operation_keeps_source_input_boundary_and_does_not_double_count_penalties",
        "test_defrost_unknown_and_humidity_missing_fail_closed_without_zero_imputation",
        "test_no_synthetic_or_pol_source_is_promoted_to_observed_performance",
        "test_runtime_penalty_variables_remain_separate_q_contracts",
        "test_steady_operation_has_no_unmodelled_defrost_or_cycling_penalty",
    ),
    "test_b06_p2_effect_evidence": (
        "test_annual_and_peak_effects_are_independent_fields",
        "test_applicability_mismatch_keeps_real_evidence_non_usable",
        "test_completion_gate_remains_separate_from_effect_evidence",
        "test_dhw_contaminated_source_fails_closed",
        "test_missing_supply_temperature_keeps_b05_handoff_q",
        "test_ranges_are_retained_without_midpoint_materialization",
        "test_weather_normalization_and_observation_status_are_preserved",
    ),
    "test_b06_p3_design_load": (
        "test_annual_factor_and_installed_capacity_are_not_inputs",
        "test_before_after_recomputes_physical_state_not_annual_factor",
        "test_emitter_and_result_datasets_are_lineaged_and_non_national",
        "test_known_transmission_and_ventilation_loss_are_dimensional",
        "test_lower_post_load_and_larger_emitter_each_reduce_required_supply",
        "test_missing_area_u_design_temperature_and_ventilation_fail_closed",
        "test_missing_emitter_fields_fail_closed",
        "test_no_automatic_w35_and_b05_out_of_domain_is_q",
        "test_no_w35_w45_w55_snapping",
        "test_p3_post_load_enters_b05_bridge_and_capacity_shortfall_is_explicit",
        "test_peak_evidence_layer_is_explicit_synthetic_fixture_only",
        "test_purmo_logarithmic_mean_branch_and_lower_water_reduce_output",
        "test_real_purmo_nominal_condition_reproduces_nominal_output",
        "test_supply_requires_explicit_emitter_and_return_temperature",
    ),
    "test_b06_p60_hu_s1_outcome_registry": (
        "test_authority_refuses_national_effect_claim",
        "test_hungarian_cases_are_bounded_and_not_engine_factors",
        "test_readiness_bridge_points_to_executable_record_gate",
        "test_s1_source_semantics_blocker_is_contracted_not_blanket_pass",
    ),
    "test_b06_p61_phase_linked_baseline_registry": (
        "test_p61_pair_does_not_authorize_unlinked_real_intervention_effect",
        "test_q_b06_006_is_resolved_without_national_claim",
        "test_readiness_percentage_is_not_uplifted_from_one_case",
        "test_real_der_engine_baseline_without_p61_pair_fails_closed",
        "test_zalavar_record_is_exact_same_phase_annual_peak_pair",
    ),
    "test_b06_p62_hu_peak_effect_registry": (
        "test_engine_accepts_exact_linked_zalavar_der_effect_but_does_not_complete_s1",
        "test_engine_rejects_arbitrary_der_peak_fraction_even_with_valid_pair",
        "test_peak_readiness_records_real_calibration_without_national_uplift",
        "test_q_b06_011_is_resolved_but_transferability_and_completion_remain_open",
        "test_zalavar_effect_pair_is_exact_and_independent",
    ),
    "test_b06_p63_effect_surface_registry": (
        "test_domains_do_not_mint_default_factors_or_national_prevalence",
        "test_p63_authority_is_parametric_not_percentage_lookup",
        "test_q_b06_007_is_resolved_without_claiming_national_input_coverage",
        "test_readiness_percentages_are_not_artificially_uplifted",
        "test_tabula_rows_are_validation_only_never_engine_defaults",
        "test_tabula_validation_has_three_distinct_hungarian_type_state_responses",
    ),
    "test_b06_p64_engine_s1_handoff": (
        "test_completion_and_outcome_must_link_same_record",
        "test_completion_obs_and_outcome_der_can_jointly_open_s1",
        "test_completion_status_is_bound_to_realized_obs_not_outcome_der",
        "test_outcome_without_realized_completion_cannot_open_s1",
        "test_realized_completion_without_outcome_cannot_open_s1",
        "test_unapproved_scope_deviation_blocks_s1",
    ),
    "test_b06_p64_registry_contract": (
        "test_completion_artifacts_do_not_collapse_roles",
        "test_completion_authority_requires_both_document_layers",
        "test_p57_p58_p59_stale_bridge_rows_are_repaired",
        "test_q_b06_009_is_resolved_as_completion_plus_outcome_contract",
        "test_readiness_percentage_is_not_uplifted_by_contract_only",
        "test_s1_has_separate_realized_completion_and_outcome_bridges",
    ),
    "test_b06_p65_emitter_temperature_gate": (
        "test_measured_route_cannot_extrapolate_from_warmer_weather",
        "test_p65_rejects_real_status_without_source_lineage",
        "test_room_by_room_route_requires_complete_heated_room_coverage",
        "test_room_by_room_route_uses_worst_room_not_average",
        "test_runtime_accepts_only_the_temperature_minted_by_p65",
        "test_runtime_rejects_naked_supply_temperature_claim",
        "test_runtime_rejects_temperature_evidence_for_a_different_post_peak",
        "test_signed_mep_design_requires_heat_loss_emitter_and_hydraulic_basis",
        "test_signed_mep_design_requires_identified_signed_authority",
    ),
    "test_b06_p65_registry_contract": (
        "test_b02_s2_bridge_uses_p65_as_record_transition_gate_not_national_precondition",
        "test_national_stock_gaps_remain_visible_but_no_longer_block_gate_execution",
        "test_p65_external_sources_are_registered_in_both_source_registries",
        "test_q_b06_008_is_resolved_without_claiming_national_coverage",
        "test_readiness_does_not_inflate_when_only_authority_blocker_is_closed",
        "test_source_pack_preserves_non_equivalence_and_fail_closed_boundary",
    ),
    "test_b06_retrofit_engine": (
        "test_conflicting_or_missing_applicability_is_not_promoted",
        "test_dhw_is_unchanged_by_envelope_intervention",
        "test_emitter_only_upgrade_changes_supply_not_envelope_demand",
        "test_missing_baseline_or_intervention_input_fails_closed",
        "test_no_retrofit_does_not_promote_s1",
        "test_realized_completion_and_linked_outcome_are_both_required_for_s1_gate",
        "test_sequential_interventions_apply_to_prior_state_not_original_baseline",
        "test_single_envelope_intervention_keeps_annual_and_peak_separate",
        "test_supply_temperature_missing_keeps_b05_handoff_q",
    ),
    "test_b10_p17_remaining_dso_node_source_discovery": (
        "test_elmu_generation_publication_does_not_promote_consumption_authority_without_later_evidence",
        "test_eon_ddasz_and_edasz_remain_fail_closed_until_exact_consumption_source_is_pinned",
        "test_existing_consumption_node_sources_remain_bounded_not_complete",
        "test_mvm_emasz_p17_q_may_be_refined_by_later_current_source_evidence",
        "test_no_operator_is_promoted_to_complete_inventory",
        "test_p17_keeps_exact_six_operator_manifest",
        "test_source_pack_preserves_historical_p17_blockers_and_no_readiness_uplift",
    ),
    "test_b10_p23_consumption_node_publication_expansion": (
        "test_current_law_remains_separate_from_p34_operator_url_authority",
        "test_eon_trio_is_now_bounded_but_inventory_completeness_remains_q",
        "test_exact_45_emasz_public_node_identity_facts_are_materialized",
        "test_existing_demasz_and_opus_bounded_sources_are_unchanged",
        "test_mvm_emasz_consumption_node_source_is_now_bounded",
        "test_no_complete_inventory_is_minted",
        "test_p23_document_remains_historical_and_preserves_original_boundaries",
    ),
    "test_b10_p34_eon_consumption_source_resolution": (
        "test_all_six_dso_rows_now_have_bounded_consumption_node_sources",
        "test_closure_audit_removes_only_the_eon_url_discovery_blockers",
        "test_eon_source_resolution_does_not_mint_inventory_completeness",
        "test_limiting_node_output_remains_q_after_source_resolution",
        "test_p34_does_not_materialize_eon_node_rows",
        "test_p34_pins_exact_current_eon_publication_for_all_three_dsos",
        "test_p34_source_pack_is_explicitly_evidence_only_and_fail_closed",
    ),
}


class LegacyDiscoveryTests(unittest.TestCase):
    def test_all_109_legacy_functions_are_individually_discovered_once(self):
        self.assertEqual(len(EXPECTED_CASES), 16)
        self.assertEqual(sum(map(len, EXPECTED_CASES.values())), 109)
        for module_name, names in EXPECTED_CASES.items():
            with self.subTest(module=module_name):
                module = importlib.import_module(module_name)
                local_functions = {
                    name for name, value in vars(module).items()
                    if name.startswith("test_") and inspect.isfunction(value)
                    and value.__module__ == module_name
                }
                self.assertEqual(local_functions, set(names))
                suite = unittest.TestLoader().loadTestsFromModule(module)
                cases = list(suite)
                self.assertEqual(suite.countTestCases(), len(names))
                self.assertTrue(all(isinstance(case, unittest.FunctionTestCase) for case in cases))
                self.assertCountEqual([case.id() for case in cases], names)
                self.assertEqual(len({case.id() for case in cases}), len(names))
        # B08 already invokes its 31 functions through its existing single bridge.
        b08 = importlib.import_module("test_b08_grid_load_aggregation")
        self.assertEqual(unittest.TestLoader().loadTestsFromModule(b08).countTestCases(), 1)
        b05 = importlib.import_module("test_b05_heat_pump_engine")
        self.assertEqual(unittest.TestLoader().loadTestsFromModule(b05).countTestCases(), 15)
