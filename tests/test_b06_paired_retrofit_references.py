"""Source-fact integrity and non-admission checks for the V1-067 handoff.

These tests do not confer target applicability or validate physical model effects.
"""
import copy
import csv
import json
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from tools import validate_registry
from modules.B06.s1_demand_outcome_gate import (
    MEASURED_USAGE, OBS, Q, S1DemandOutcomeEvidence, assess_s1_demand_outcome,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "registry/b06_paired_retrofit_reference_manifest.json"
EFFECT_PATH = ROOT / "data/processed/retrofit_effect_evidence.csv"
SOL_ID = "B06-EFF-SOLANOVA-MONITORED"
NEED_ID = "B06-EFF-NEED-EW-MATCHED-2026"
PHYSICAL_FIELDS = (
    "annual_before_kwh_m2a", "annual_after_kwh_m2a",
    "annual_before_min_kwh_m2a", "annual_before_max_kwh_m2a",
    "annual_after_min_kwh_m2a", "annual_after_max_kwh_m2a",
    "annual_reduction_fraction", "annual_reduction_min", "annual_reduction_max",
    "peak_before_kw", "peak_after_kw", "peak_reduction_fraction",
)
# Independent review of original native XML cells D:H, not rounded table displays.
EXPECTED_NEED = {
    ("Table 1", 5): ("354312", "2.27979167756901E-2", "9.4189993566782208E-3", "236.028135345029", "259.60201915825297"),
    ("Table 1", 6): ("2411", "0.172758601491735", "0.16850789401101601", "1857.04531661942", "2009.07724265826"),
    ("Table 1", 7): ("2191", "0.119819792291204", "0.111381983330503", "1207.5184549826299", "1428.4002673444199"),
    ("Table 1", 8): ("1486", "3.21169156666163E-2", "2.89229885628914E-2", "323.615262313838", "390.93592338961503"),
    ("Table 1", 9): ("25199", "0.12228015322168199", "9.3464484576783205E-2", "303.70800000000003", "314.81882906045098"),
    ("Table 2", 5): ("1609", "0.143121750351656", "0.13251670997637699", "1550.5716632973499", "1723.98127889336"),
    ("Table 2", 6): ("2192", "9.1493813843610203E-2", "8.0731686165707195E-2", "999.87883682181098", "1214.82816979375"),
    ("Table 2", 7): ("4841", "0.10274181212828", "8.73139861568311E-2", "1082.4791881650899", "1387.21760293899"),
    ("Table 2", 8): ("2297", "8.3764844805140098E-2", "7.7794480912676198E-2", "878.86102079933596", "809.37448758824496"),
    ("Table 2", 9): ("5191", "0.11522675364865401", "8.8662496481891603E-2", "1218.1495644454899", "1328.4561977383"),
    ("Table 2", 10): ("7044", "9.6326239917874104E-2", "7.0830598697160602E-2", "1009.10048027497", "1162.2279943860501"),
}
EXPECTED_SOURCES = {
    "SRC-B06-SOLANOVA-TREES-CASE": "7372de1a8b8950d7c713648e8fb1a3b8613cf13c6142094955cda54ab94e6ceb",
    "SRC-B06-SOLANOVA-TREES-SLIDES": "22168c00366fadae8e5f17a60ed6fc398c265c9f5a3e1f162104a50baab83d6c",
    "SRC-B06-SOLANOVA-ACEEE-2006": "ac3e3984cc3445d8c1086f53afd60ff0b8546ea0e089533f4244b52291a056dd",
    "SRC-B06-DESNZ-NEED-HEADLINE-EW-2026": "bde31f1752cf75b0f696eef95dcc3cedd96ec13c7036f8b09b8a429052be1600",
    "SRC-B06-DESNZ-NEED-ANNEX-A-2026": "b4a6398a78c5acbe145f175903ec2269c6d598296ea6fd0178fdff7bb70c53f0",
    "SRC-B06-DESNZ-NEED-ANNEX-D-2026": "3a573a68dbf7287d279ad5e761f661c712d2347dc82a30f81bbbc83b64680dde",
    "SRC-B06-DESNZ-NEED-REPORT-2026": "1f47d838cf5bd68c7039b5a9e212ebd95929c90e2c993e49dc703d64d7c403d8",
}


def csv_rows(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class PairedRetrofitReferenceTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(MANIFEST_PATH.read_text())
        self.sources = {s["source_id"]: s for s in self.manifest["sources"]}
        self.sol = self.manifest["families"]["SOLANOVA"]
        self.need = self.manifest["families"]["NEED-EW-2026"]
        self.effects = {r["evidence_id"]: r for r in csv_rows(EFFECT_PATH)}

    def test_original_document_hashes_and_registry_identity(self):
        self.assertEqual(EXPECTED_SOURCES, {s: r["sha256"] for s, r in self.sources.items()})
        global_rows = {r["source_id"]: r for r in csv_rows(ROOT / "registry/sources.csv")}
        local_rows = {r["source_id"]: r for r in csv_rows(ROOT / "registry/retrofit_sources.csv")}
        for sid, source in self.sources.items():
            with self.subTest(source=sid):
                self.assertEqual(source["sha256"], global_rows[sid]["local_snapshot_sha256"])
                self.assertEqual(source["original_url"], global_rows[sid]["url"])
                self.assertEqual(source["original_url"], local_rows[sid]["url"])
                self.assertTrue(source["authority"])
                self.assertTrue(source["reference_period"])
                self.assertRegex(source["retrieved_at"], r"^2026-10-05T\d{2}:\d{2}:\d{2}")
                self.assertIsNone(source["repo_snapshot_path"])
                self.assertEqual("EXTERNAL_ONLY_REPOSITORY_COPY_NOT_CLEARED", source["reuse_status"])

    def test_sources_belong_to_exactly_one_original_family(self):
        families = self.manifest["families"]
        self.assertEqual({"SOLANOVA", "NEED-EW-2026"}, set(families))
        member_ids = [sid for family in families.values() for sid in family["source_ids"]]
        self.assertEqual(len(member_ids), len(set(member_ids)))
        self.assertEqual(set(self.sources), set(member_ids))
        for fid, family in families.items():
            self.assertTrue(all(self.sources[sid]["family_id"] == fid for sid in family["source_ids"]))
        self.assertIn("not independent corroboration", self.sol["companion_policy"])

    def test_document_dates_are_not_invented_from_filename_or_metadata(self):
        for sid in ("SRC-B06-SOLANOVA-TREES-CASE", "SRC-B06-SOLANOVA-TREES-SLIDES"):
            source = self.sources[sid]
            self.assertIsNone(source["document_date"])
            self.assertEqual("unknown", source["document_date_precision"])
            self.assertIn("filename", source["document_date_basis"])
            self.assertIn("PDF creation", source["document_date_basis"])
        original = self.sources["SRC-B06-SOLANOVA-ACEEE-2006"]
        self.assertEqual(("2006", "year"), (original["document_date"], original["document_date_precision"]))
        for sid in self.need["source_ids"]:
            self.assertEqual("2026-06-11", self.sources[sid]["document_date"])

    def test_qualified_observations_are_separate_from_q_target_authority(self):
        self.assertEqual("OBS", self.sol["source_observation_status"])
        self.assertEqual("DER", self.need["published_estimate_status"])
        for family in self.manifest["families"].values():
            self.assertEqual("Q", family["applicability_status"])
            self.assertEqual("Q", family["outcome_authority_status"])
            self.assertIs(False, family["usable_for_engine"])
            row = self.effects[family["evidence_id"]]
            self.assertEqual("Q", row["status"])
            self.assertEqual("NO", row["usable_for_engine"])

    def test_solanova_building_heat_source_and_bundle_boundaries(self):
        self.assertEqual(1, self.sol["buildings"]["value"])
        self.assertEqual(42, self.sol["flats"]["value"])
        self.assertEqual("DISTRICT_HEATING", self.sol["heat_source"])
        self.assertIn("shops", self.sol["service_scope"])
        self.assertIn("not a probability sample", self.sol["selection"])
        self.assertFalse(self.sol["component_effects_identified"])
        self.assertFalse(self.sol["heat_pump_effect_identified"])

    def test_solanova_separately_rounded_observed_totals_and_reported_percent(self):
        pair = self.sol["monitored_aggregate"]
        self.assertEqual((2100, 394, 81.3), tuple(pair[k]["value"] for k in ("before", "after", "published_saving")))
        self.assertEqual(("OBS", "OBS", "DER"), tuple(pair[k]["truth"] for k in ("before", "after", "published_saving")))
        self.assertIn("two seasons", pair["before_period"])
        self.assertEqual("2005-2006 heating season", pair["after_period"])
        self.assertEqual("NOT_DOCUMENTED_FOR_THIS_PAIR", pair["normalization"])
        self.assertNotAlmostEqual((2100 - 394) / 2100 * 100, 81.3, places=4)
        self.assertEqual("", self.effects[SOL_ID]["annual_reduction_fraction"])

    def test_solanova_observed_intensities_include_shops_without_denominator_repair(self):
        p = self.sol["monitored_intensity"]
        self.assertEqual((213, 39, 35, 71), tuple(p[k]["value"] for k in ("before", "after", "after_flats", "after_shops")))
        self.assertFalse(p["floor_denominator_reconciled"])
        area = self.sol["area_context"]
        self.assertEqual((2350, 300, 2650), tuple(area[k]["value"] for k in ("residential", "shops", "treated")))
        self.assertFalse(area["used_to_recalculate_later_intensities"])
        row = self.effects[SOL_ID]
        self.assertEqual(("213", "39", ""), tuple(row[k] for k in ("annual_before_kwh_m2a", "annual_after_kwh_m2a", "area_m2")))

    def test_solanova_normalized_baseline_cannot_be_joined_to_post(self):
        p = self.sol["separate_normalized_baseline"]
        self.assertEqual(210, p["before"]["value"])
        self.assertEqual("DER", p["before"]["truth"])
        self.assertEqual("2004-2005 heating season", p["before_period"])
        self.assertIsNone(p["after"])
        self.assertFalse(p["joined_to_monitored_pair"])
        self.assertEqual("NOT_DOCUMENTED", p["matching_post_normalization"])
        self.assertEqual("NOT_DISCLOSED", self.effects[SOL_ID]["weather_normalization"])

    def test_solanova_service_temperature_not_annual_setpoint_or_rebound(self):
        s = self.sol["service_change"]
        self.assertEqual(24.7, s["february_mean"]["value"])
        self.assertEqual("February 2006", s["february_mean"]["period"])
        self.assertIn("excludes ground floor and cellar", s["february_mean"]["boundary"])
        self.assertIsNone(s["annual_setpoint"])
        self.assertIsNone(s["rebound_factor"])

    def test_planned_and_ambiguous_outcomes_are_not_measured(self):
        excluded = self.sol["excluded_claims"]
        self.assertEqual({29.4, 87, 78}, {p["quantity"]["value"] for p in excluded})
        self.assertTrue(all(p["observed_outcome"] is False for p in excluded))
        self.assertTrue(all(p["quantity"]["truth"] != "OBS" for p in excluded))
        sankey = next(p for p in excluded if p["quantity"]["value"] == 78)
        self.assertEqual("MEASUREMENT_STATUS_UNRESOLVED", sankey["kind"])
        self.assertIn("no current CAPEX", self.sol["historical_cost_policy"])

    def test_need_gas_years_are_dated_consumption_windows(self):
        windows = self.need["gas_windows"]
        self.assertEqual("mid-May 2022 to mid-May 2023", windows["before"])
        self.assertEqual("mid-May 2023 to mid-May 2024", windows["installation"])
        self.assertEqual("mid-May 2024 to mid-May 2025", windows["after"])
        self.assertEqual("2026-06-11", self.need["publication_date"])
        self.assertIn("Year 0", self.need["year_label_policy"])

    def test_need_whole_property_aq_has_no_heat_or_floor_denominator(self):
        self.assertEqual("WHOLE_PROPERTY_GAS_NOT_SPACE_HEAT_OR_USEFUL_HEAT", self.need["service_boundary"])
        self.assertIn("six months", self.need["input_basis"]["method"])
        self.assertIn("Xoserve", self.need["input_basis"]["method"])
        self.assertIn("not EPC", self.need["input_basis"]["empirical_input"])
        self.assertIsNone(self.need["floor_area_denominator"])
        self.assertEqual("MATCHED_METERED_SAVINGS", self.effects[NEED_ID]["evidence_class"])
        for field in PHYSICAL_FIELDS + ("area_m2",):
            self.assertEqual("", self.effects[NEED_ID][field], field)

    def test_need_exact_original_numeric_cells(self):
        table = self.need["published_table"]
        self.assertEqual(set(EXPECTED_NEED), {(r["sheet"], r["row"]) for r in table["rows"]})
        columns = tuple(table["columns"])
        for row in table["rows"]:
            key = row["sheet"], row["row"]
            with self.subTest(source_row=key):
                self.assertEqual(set(columns), set(row["numeric_cells"]))
                actual = tuple(row["numeric_cells"][f] for f in columns)
                self.assertEqual(EXPECTED_NEED[key], actual)
                self.assertTrue(all(Decimal(value).is_finite() for value in actual))

    def test_need_count_mean_median_and_quantile_types_are_distinct(self):
        columns = self.need["published_table"]["columns"]
        self.assertEqual("PUBLISHED_NUMBER_IN_SAMPLE", columns["sample_n"]["statistic"])
        self.assertEqual("OBS", columns["sample_n"]["truth"])
        self.assertTrue(columns["sample_n"]["not_recruitment_or_attrition_denominator"])
        for field, col in columns.items():
            if field != "sample_n":
                self.assertEqual("DER", col["truth"])
                self.assertIn("MEDIAN" if field.startswith("median") else "MEAN", col["statistic"])
        q = self.need["quantile_policy"]
        self.assertEqual("DER", q["truth"])
        self.assertIn("QUANTILES", q["statistic"])
        self.assertFalse(q["confidence_intervals"])
        self.assertFalse(q["raw_single_cohort_distribution"])

    def test_need_pv_is_excluded_context_and_not_a_gas_outcome(self):
        rows = self.need["published_table"]["rows"]
        context = [r for r in rows if r["use_in_this_handoff"] == "context_only_outside_fabric_heating_scope"]
        self.assertEqual([("Table 1", 9, "Solar PV", "Electricity savings")], [(r["sheet"], r["row"], r["measure"], r["fuel_saving"]) for r in context])
        gas = [r for r in rows if r not in context]
        self.assertTrue(all(r["fuel_saving"] == "Gas savings" for r in gas))
        self.assertEqual(set(EXPECTED_NEED) - {("Table 1", 9)}, {(r["sheet"], r["row"]) for r in gas})

    def test_need_no_synthetic_pairs_from_separate_medians_or_additive_packages(self):
        estimator = self.need["estimator"]
        self.assertTrue(estimator["percent_and_kwh_are_separate_estimators"])
        self.assertFalse(estimator["individual_household_pairs_published"])
        self.assertFalse(estimator["cohort_effects_additive"])
        for row in self.need["published_table"]["rows"]:
            self.assertEqual(set(self.need["published_table"]["columns"]), set(row["numeric_cells"]))
            self.assertNotIn("baseline_kwh", row)
            self.assertNotIn("after_kwh", row)

    def test_need_selection_matching_repeats_and_weights_remain_explicit(self):
        s = self.need["selection"]
        for term in ("Flats", "smart-meter", "imputation", "after 1999", "missing"):
            self.assertIn(term, s["excludes"])
        self.assertFalse(s["attrition_funnel_published"])
        self.assertIn("not Hungarian", s["weights"])
        self.assertIn("owner planning weights", s["weights"])
        self.assertIn("hidden measures", s["measure_scope"])
        self.assertEqual(50, self.need["estimator"]["repeats"]["value"])
        self.assertEqual(2.5, self.need["estimator"]["tail_trim_each"]["value"])
        self.assertFalse(self.need["estimator"]["randomized_intervention"])

    def test_need_raw_sign_ambiguity_is_preserved_without_repair_or_gate(self):
        p = self.need["sign_policy"]
        self.assertEqual("UNRESOLVED_RAW_CHANGE_SIGN_CONVENTION", p["status"])
        self.assertIn("explicitly labelled positive savings", p["handling"])
        self.assertIn("Do not reconstruct or repair", p["handling"])
        self.assertIn("does not prevent", p["handling"])
        self.assertFalse(self.need["heat_pump_effect_identified"])
        self.assertFalse(self.need["control_or_emitter_physical_effect_identified"])

    def test_need_loft_label_includes_roof_and_room_in_roof_for_combinations(self):
        scope = self.need["measure_label_scope"]
        self.assertEqual("SRC-B06-DESNZ-NEED-HEADLINE-EW-2026", scope["source_id"])
        self.assertEqual("Notes!B4", scope["locator"])
        self.assertEqual(["loft insulation", "roof insulation", "room-in-roof insulation"], scope["included_measures"])
        self.assertIn("Single-measure and combination", scope["applies_to"])

    def test_need_estimates_are_first_year_not_persistent_lifetime_savings(self):
        horizon = self.need["observation_horizon"]
        self.assertEqual("SRC-B06-DESNZ-NEED-HEADLINE-EW-2026", horizon["source_id"])
        self.assertEqual("Cover sheet!A3", horizon["locator"])
        self.assertEqual((1, "year after installation", "DER"), (horizon["value"], horizon["unit"], horizon["truth"]))
        self.assertFalse(horizon["persistent_lifetime_savings_demonstrated"])

    def test_need_xml_decimal_exactness_is_not_statistical_precision(self):
        uncertainty = self.need["uncertainty_assessment"]
        self.assertEqual("SRC-B06-DESNZ-NEED-ANNEX-D-2026", uncertainty["source_id"])
        self.assertEqual("p16, Variations in estimated savings between years", uncertainty["locator"])
        self.assertFalse(uncertainty["full_assessment_completed"])
        self.assertTrue(uncertainty["estimates_are_indicative_not_precise"])
        self.assertIn("does not establish statistical precision", uncertainty["exact_numeric_storage_meaning"])

    def test_need_release_method_changes_preclude_assumed_direct_comparability(self):
        comparability = self.need["release_comparability"]
        self.assertEqual("SRC-B06-DESNZ-NEED-HEADLINE-EW-2026", comparability["source_id"])
        self.assertEqual("Cover sheet!A4", comparability["locator"])
        self.assertFalse(comparability["direct_comparability_with_previous_releases_assumed"])
        self.assertIn("Methodological changes", comparability["reason"])
        self.assertIn("source-coherent Impact of Measures by year of installation", comparability["later_time_series_use"])

    def test_only_research_progress_with_explicit_residual_debt(self):
        plan = json.loads((ROOT / "registry/v1_research_plan.json").read_text())
        task = next(s for m in plan["modules"] for s in m["slices"] if s["slice_id"] == "B06-D03")
        self.assertEqual("RESEARCHING", task["status"])
        self.assertEqual([], task["accepted_artifacts"])
        self.assertEqual([], task["canonical_source_ids"])
        self.assertEqual([], task["consumer_tests"])
        self.assertIsNone(task["reviewed_commit"])
        self.assertEqual({d["id"] for d in self.manifest["validation_debt"]}, set(task["validation_debt_ids"]))
        self.assertTrue(task["research_log"])
        self.assertFalse(self.manifest["target_authority"]["task_accepted"])

    def test_reference_retention_does_not_require_universal_household_or_census_data(self):
        self.assertIn("does not universally require private household bills or exhaustive census", self.manifest["allowed_next_use"])
        for debt in self.manifest["validation_debt"]:
            self.assertTrue(debt["scope"])
            self.assertEqual("Q", debt["status"])
        sign_debt = next(d for d in self.manifest["validation_debt"] if d["id"] == "B06-REF-NEED-SIGNED-DELTAS")
        self.assertIn("not a gate", sign_debt["required"])

    def test_no_source_defaults_or_production_consumers_are_added(self):
        for key in ("usable_for_engine", "model_default_admitted", "national_factor_admitted", "task_accepted"):
            self.assertFalse(self.manifest["target_authority"][key])
        for directory in ("modules", "model"):
            for path in (ROOT / directory).rglob("*.py"):
                text = path.read_text()
                self.assertNotIn(MANIFEST_PATH.name, text, str(path))
                for sid in self.sources:
                    self.assertNotIn(sid, text, str(path))
        for name in ("retrofit_interventions.csv", "b06_p60_s1_demand_outcome_authority.csv", "b06_p62_peak_effect_authority.csv", "b06_p64_realized_completion_authority.csv"):
            text = (ROOT / "registry" / name).read_text()
            self.assertTrue(all(sid not in text for sid in self.sources), name)

    def test_public_manifest_has_no_private_paths_or_embedded_originals(self):
        text = MANIFEST_PATH.read_text()
        for token in ("libfile_", "sediment://", "/workspace/", "data:application/", "base64", "extracted_text", "response_headers"):
            self.assertNotIn(token, text)
        self.assertTrue(all(s["repo_snapshot_path"] is None for s in self.sources.values()))

    def _validate_effect_mutation(self, changes):
        rows = copy.deepcopy(list(self.effects.values()))
        next(r for r in rows if r["evidence_id"] == NEED_ID).update(changes)
        original_read = validate_registry.read_csv

        def read(path):
            if path == EFFECT_PATH:
                return list(rows[0]), rows
            return original_read(path)

        errors = []
        source_ids = {r["source_id"] for r in csv_rows(ROOT / "registry/sources.csv")}
        with patch.object(validate_registry, "read_csv", side_effect=read):
            validate_registry.validate_b06_artifacts(errors, source_ids)
        return errors

    def test_canonical_validator_accepts_reference_only_handoff(self):
        self.assertEqual([], self._validate_effect_mutation({}))

    def test_adversarial_need_cannot_be_relabelled_as_physical_annual_or_peak_values(self):
        for field in PHYSICAL_FIELDS:
            with self.subTest(field=field):
                errors = self._validate_effect_mutation({field: "0.1"})
                self.assertTrue(any("cannot populate B06 physical-effect fields" in e for e in errors))

    def test_adversarial_need_cannot_be_promoted_into_engine_or_outcome_authority(self):
        for changes in ({"usable_for_engine": "YES"}, {"status": "DER"}, {"status": "OBS"}):
            with self.subTest(changes=changes):
                errors = self._validate_effect_mutation(changes)
                self.assertTrue(any("retain Q target authority and no engine admission" in e for e in errors))

    def test_adversarial_solanova_observation_does_not_open_existing_outcome_gate(self):
        # Real source facts retained; missing normalized same-service authority
        # continues to fail the existing gate without altering physical code.
        sid = "SRC-B06-SOLANOVA-TREES-CASE"
        evidence = S1DemandOutcomeEvidence(
            record_id="SOLANOVA", intervention_id="B06-COMBINED-PACKAGE",
            evidence_kind=MEASURED_USAGE, evidence_status=OBS,
            phase_link_id="S0_TO_S1:SOLANOVA:B06-COMBINED-PACKAGE",
            before_value=213, after_value=39,
            before_metric_id="HEATING_CONSUMPTION", after_metric_id="HEATING_CONSUMPTION",
            before_unit="kWh_m2a", after_unit="kWh_m2a",
            before_method_id="TREES_MONITORING", after_method_id="TREES_MONITORING",
            before_source_refs=(sid,), after_source_refs=(sid,),
            normalization_basis_documented=False, end_use_scope_documented=True,
        )
        result = assess_s1_demand_outcome(evidence)
        self.assertEqual(Q, result.status)
        self.assertIn("MEASURED_USAGE_NORMALIZATION_MISSING", result.reasons)


if __name__ == "__main__":
    unittest.main()
