"""Source integrity and non-admission checks; no new runtime or stock calibration.

Numeric oracle: independently verified original BOILeff Table 2 and UK Tables
9-11 joined to Appendix D. Only necessary factual values are retained here.
"""
import copy
import csv
import hashlib
import json
import re
import statistics
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from modules.B11.gas_efficiency_authority import (
    EfficiencyMetric, EnergyBasis, GasEfficiencyEvidence,
    authorize_fuel_volume_efficiency,
)
from modules.B11.gas_volume_bridge_contract import EvidenceStatus
from tools import validate_registry

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "registry/b11_seasonal_boiler_reference_manifest.json"
BOI = "BOILEFF"
UK = "EST-CONDENSING-FIELD-TRIAL"
EXPECTED_BOILEFF = {'HU 1': '93.4', 'HU 2': '90.1', 'HU 3': '88.9', 'HU 5': '83.8', 'HU 6': '80.7', 'HU 7': '80.0', 'AT 1': '86.7', 'AT 2': '87.8', 'AT 4': '82.4', 'AT 5': '94.8', 'AT 6': '87.5', 'AT 7': '91.3', 'AT 9': '88.8', 'AT 11': '89.8'}
EXPECTED_SOURCES = {'SRC-B11-BOILEFF-FINAL-2009': '706ed941885560de8b35da8360e0f6a897364b9b506fb1baaf5fad1e0d332cb9', 'SRC-B11-BOILEFF-EEDAL-2010': '0541e53b736931a34e74705a7ab924715cb8eee1eee624ba29e9d1163ab581d2', 'SRC-B11-EST-FIELD-2009': 'c3c484dcc8fc4bd5ee945d4a0f9d7c7a75c4453e403e6f1d240c5395d05f6fd3', 'SRC-B11-EST-TPI-2010': '3dcf7923186440d1983ede41275fe88976e4132d6d234f5c08ca55144fb42b6d', 'SRC-B11-JRC-EEDAL-RECORD': '8d9eeb30f3ebdf0a0f42d517a9078f87ba4e75e17a7230e4122ab98470052614'}
# case, class, source GCV percent, unchanged months, substitution months, days
EXPECTED_UK = {
    '343DNO': ('combination', '89.7', 12, 0, 0),
    '329PLE': ('combination', '87.4', 9, 3, 11),
    '319JBO': ('combination', '87.0', 12, 0, 0),
    '312PLO': ('combination', '87.0', 12, 0, 0),
    '356MJM': ('combination', '86.8', 12, 0, 0),
    '351WIL': ('combination', '84.7', 9, 3, 25),
    '347WMI': ('combination', '84.6', 11, 1, 1),
    '320ETH': ('combination', '84.3', 12, 0, 0),
    '309ADH': ('combination', '84.1', 12, 0, 0),
    '317MTR': ('combination', '84.0', 10, 2, 2),
    '307MLE': ('combination', '83.9', 11, 1, 3),
    '315EJO': ('combination', '83.9', 10, 2, 5),
    '339PRI': ('combination', '83.9', 12, 0, 0),
    '337JDI': ('combination', '83.5', 11, 1, 2),
    '352PLA': ('combination', '83.4', 12, 0, 0),
    '313KPE': ('combination', '83.1', 12, 0, 0),
    '344WBA': ('combination', '83.0', 12, 0, 0),
    '338CNE': ('combination', '83.0', 12, 0, 0),
    '311STW': ('combination', '82.9', 10, 2, 2),
    '340PCU': ('combination', '82.2', 10, 2, 8),
    '323RWA': ('combination', '81.6', 10, 2, 12),
    '302SWI': ('combination', '81.1', 12, 0, 0),
    '349JTI': ('combination', '81.0', 5, 7, 17),
    '326ABR': ('combination', '80.6', 11, 1, 1),
    '350AWI': ('combination', '80.6', 11, 1, 1),
    '355PCA': ('combination', '80.5', 12, 0, 0),
    '316MBA': ('combination', '80.1', 11, 1, 1),
    '357SHO': ('combination', '78.4', 10, 2, 13),
    '310MPO': ('combination', '76.6', 8, 4, 11),
    '335RHA': ('combination', '74.9', 12, 0, 0),
    '328CHI': ('combination', '68.6', 12, 0, 0),
    '314DPA': ('regular', '89.2', 10, 2, 2),
    '346CFR': ('regular', '88.0', 9, 3, 8),
    '331MMU': ('regular', '87.8', 12, 0, 0),
    '353HEB': ('regular', '86.2', 11, 1, 1),
    '321THB': ('regular', '85.4', 12, 0, 0),
    '341NSM': ('regular', '85.0', 12, 0, 0),
    '325JSE': ('regular', '83.7', 2, 10, 24),
    '345PYO': ('regular', '83.6', 11, 1, 1),
    '327BSW': ('regular', '82.7', 6, 6, 54),
    '336JON': ('regular', '81.2', 11, 1, 2),
    '359NPO': ('CPSU', '76.5', 7, 5, 15),
    '358MSC': ('CPSU', '64.1', 9, 3, 3),
}

def csv_rows(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class SeasonalBoilerReferenceTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(MANIFEST_PATH.read_text())
        self.sources = {s["source_id"]: s for s in self.manifest["sources"]}
        self.boi = self.manifest["families"][BOI]
        self.uk = self.manifest["families"][UK]

    def _errors(self, mutate=None, csv_mutate=None, rehash=False):
        candidate = copy.deepcopy(self.manifest)
        if mutate:
            mutate(candidate)
        if rehash:
            for family in candidate["families"].values():
                family["records_sha256"] = hashlib.sha256(json.dumps(family["records"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        original_read = Path.read_text
        original_csv = validate_registry.read_csv

        def read(path, *args, **kwargs):
            if path == MANIFEST_PATH:
                return json.dumps(candidate)
            return original_read(path, *args, **kwargs)

        def read_csv(path):
            header, rows = original_csv(path)
            if csv_mutate:
                csv_mutate(path, rows)
            return header, rows

        source_ids = {r["source_id"] for r in csv_rows(ROOT / "registry/sources.csv")}
        errors = []
        with patch.object(Path, "read_text", read), patch.object(validate_registry, "read_csv", read_csv):
            validate_registry.validate_b11_seasonal_references(errors, source_ids)
        return errors

    def test_original_hashes_and_source_identities_are_pinned(self):
        self.assertEqual(EXPECTED_SOURCES, {sid: s["sha256"] for sid, s in self.sources.items()})
        global_rows = {r["source_id"]: r for r in csv_rows(ROOT / "registry/sources.csv")}
        local_rows = {r["source_id"]: r for r in csv_rows(ROOT / "registry/b11_gas_efficiency_sources.csv")}
        for sid, s in self.sources.items():
            self.assertEqual(s["sha256"], global_rows[sid]["local_snapshot_sha256"])
            self.assertEqual(s["original_url"], global_rows[sid]["url"])
            self.assertEqual(s["original_url"], local_rows[sid]["url"])
            self.assertRegex(s["retrieved_at"], r"^2026-10-05T\d{2}:\d{2}:\d{2}")
            self.assertIsNone(s["repo_snapshot_path"])
            self.assertEqual("EXTERNAL_ONLY_REPOSITORY_COPY_NOT_CLEARED", s["reuse_status"])

    def test_dates_retain_source_precision_and_repository_availability(self):
        expected = {"SRC-B11-BOILEFF-FINAL-2009": ("2009-11", "month"), "SRC-B11-BOILEFF-EEDAL-2010": ("2010", "year"), "SRC-B11-JRC-EEDAL-RECORD": (None, "unknown"), "SRC-B11-EST-FIELD-2009": ("2009-06", "month"), "SRC-B11-EST-TPI-2010": ("2010-09", "month")}
        self.assertEqual(expected, {sid: (s["document_date"], s["document_date_precision"]) for sid, s in self.sources.items()})
        self.assertEqual("2010-02-08", self.boi["lineage"]["jrc_repository_available_date"])
        self.assertFalse(self.boi["lineage"]["jrc_available_date_is_print_publication_date"])
        self.assertIn("Date available", self.sources["SRC-B11-JRC-EEDAL-RECORD"]["document_date_basis"])

    def test_exact_boileff_fourteen_native_values(self):
        self.assertEqual(EXPECTED_BOILEFF, {r["case_id"]: r["gcv_efficiency_pct"] for r in self.boi["records"]})
        for r in self.boi["records"]:
            self.assertEqual("OBS", r["truth"])
            self.assertEqual("gas_condensing_installation", r["appliance_class"])
            self.assertEqual("Table 2; printed p12 / PDF p22", r["locator"])

    def test_hu_and_at_remain_separate_same_family(self):
        for geo, count, scope in (("HU", 6, "HISTORICAL_HU_REFERENCE"), ("AT", 8, "SAME_FAMILY_AT_AGGREGATE_CONTEXT")):
            rows = [r for r in self.boi["records"] if r["geography"] == geo]
            self.assertEqual(count, len(rows))
            self.assertTrue(all(r["case_id"].startswith(geo) and r["family_id"] == BOI and r["use_scope"] == scope for r in rows))
        self.assertFalse(self.boi["lineage"]["independent_replication"])

    def test_boileff_cohort_denominators_are_not_interchangeable(self):
        c = self.boi["cohort"]
        self.assertEqual((53, 44, 29, 14), tuple(c[k]["value"] for k in ("participating_consumers", "participating_installers", "metered_systems", "detailed_selected_gas_systems")))
        self.assertEqual({"gas": 23, "oil": 3, "biomass": 3}, {k: v["value"] for k, v in c["metered_by_fuel"].items()})
        self.assertEqual({"AT": 13, "DE": 6, "HU": 10}, {k: v["value"] for k, v in c["metered_by_country"].items()})
        self.assertIsNone(c["country_by_fuel_cross_tab"])
        self.assertIsNone(c["national_weights"])
        self.assertIn("not a probability sample", c["selection"])

    def test_boileff_aggregate_discrepancy_not_repaired(self):
        a = self.boi["aggregate_discrepancy"]
        self.assertEqual({"HU": "86.00", "AT": "89.63", "ALL_14": "87.9"}, {k: v["value"] for k, v in a["source_reported"].items()})
        for key in ("HU", "AT", "ALL_14"):
            rows = [r for r in self.boi["records"] if key == "ALL_14" or r["geography"] == key]
            mean = sum(Decimal(r["gcv_efficiency_pct"]) for r in rows) / len(rows)
            self.assertAlmostEqual(float(mean), float(a["rounded_row_arithmetic"][key]["value"]), places=12)
            self.assertNotEqual(mean, Decimal(a["source_reported"][key]["value"]))
            self.assertEqual("DER", a["source_reported"][key]["truth"])
            self.assertEqual("DER", a["rounded_row_arithmetic"][key]["truth"])
        self.assertIsNone(a["weights"])
        self.assertFalse(a["source_aggregates_repaired"])
        self.assertFalse(a["default_selected"])
        self.assertIn("AT 7 / AT 11", a["chart_order_note"])

    def test_boileff_planned_protocol_cannot_supply_completion_or_boundary(self):
        period = self.boi["period"]
        self.assertEqual("2009-12-31", period["blank_agreement"]["planned_end_date"])
        self.assertFalse(period["blank_agreement"]["completed_observation_evidence"])
        self.assertIsNone(period["completed_case_intervals"])
        boundary = self.boi["heat_boundary"]
        self.assertEqual(2, boundary["dhw_separation"]["value"])
        self.assertIsNone(boundary["cases_without_separate_dhw_ids"])
        self.assertIsNone(boundary["case_meter_storage_distribution_boundary"])
        self.assertIsNone(boundary["auxiliary_electricity_boundary"])

    def test_exact_uk_43_values_classes_and_substitution_joins(self):
        fields = ("appliance_class", "gcv_efficiency_pct", "months_without_substitution", "months_with_substitution", "substituted_days")
        self.assertEqual(EXPECTED_UK, {r["case_id"]: tuple(r[k] for k in fields) for r in self.uk["records"]})
        for r in self.uk["records"]:
            self.assertEqual("DER", r["truth"])
            self.assertEqual("UK", r["geography"])
            self.assertIn("PDF p.109", r["substitution_locator"])
        self.assertNotIn("348HIG", EXPECTED_UK)

    def test_uk_service_boundaries_are_distinct(self):
        boundaries = {"combination": "COMBI_BOILER_SH_DHW_OUTPUT", "regular": "REGULAR_BOILER_OUTPUT_BEFORE_CYLINDER", "CPSU": "CPSU_INTEGRAL_STORE"}
        for row in self.uk["records"]:
            self.assertEqual(boundaries[row["appliance_class"]], row["boundary_id"])
        self.assertIn("not old non-condensing", self.uk["heat_boundaries"][boundaries["regular"]])
        self.assertIn("Electricity", self.uk["denominator"])
        self.assertIn("not whole-property fiscal gas", self.uk["denominator"])

    def test_uk_published_mean_sd_not_rounded_row_replacements(self):
        for kind, mean, sd in (("combination", "82.5", "4.0"), ("regular", "85.3", "2.5")):
            source = self.uk["source_subgroups"][kind]
            self.assertEqual((mean, sd), (source["mean"]["value"], source["sample_sd"]["value"]))
            self.assertEqual("DER", source["mean"]["truth"])
            self.assertEqual("percentage_point", source["sample_sd"]["unit"])
            rows = [float(r["gcv_efficiency_pct"]) for r in self.uk["records"] if r["appliance_class"] == kind]
            audit = self.uk["subgroup_audit"]["subgroups"][kind]
            self.assertAlmostEqual(statistics.mean(rows), audit["mean_from_rounded_rows"], places=12)
            self.assertAlmostEqual(statistics.stdev(rows), audit["sample_sd_from_rounded_rows"], places=12)
            self.assertNotEqual(statistics.mean(rows), float(mean))
        self.assertGreater(self.uk["subgroup_audit"]["subgroups"]["regular"]["sample_sd_from_rounded_rows"], 2.55)
        self.assertFalse(self.uk["source_subgroups"]["sd_is_measurement_uncertainty_or_ci"])
        self.assertFalse(self.uk["source_subgroups"]["extrema_are_population_or_prediction_intervals"])

    def test_uk_cpsu_not_pooled(self):
        self.assertEqual(["76.5", "64.1"], [r["gcv_efficiency_pct"] for r in self.uk["records"] if r["appliance_class"] == "CPSU"])
        self.assertIsNone(self.uk["source_subgroups"]["CPSU"]["pooled_mean_adopted"])
        self.assertIsNone(self.uk["source_subgroups"]["CPSU"]["pooled_sd_adopted"])
        self.assertNotIn("mean_from_rounded_rows", self.uk["subgroup_audit"]["subgroups"]["CPSU"])

    def test_uk_subgroup_join_arithmetic_is_derived(self):
        expected = {"combination": (31, 16, 115, 337, 35, 11315), "regular": (10, 7, 92, 96, 24, 3650), "CPSU": (2, 2, 18, 16, 8, 730)}
        fields = ("n", "sites_with_substitution", "sum_substituted_days", "months_without_substitution", "months_with_substitution", "source_convention_days_denominator")
        self.assertEqual("DER", self.uk["subgroup_audit"]["truth"])
        for kind, values in expected.items():
            audit = self.uk["subgroup_audit"]["subgroups"][kind]
            rows = [r for r in self.uk["records"] if r["appliance_class"] == kind]
            self.assertEqual(values, tuple(audit[k] for k in fields))
            actual = (len(rows), sum(r["substituted_days"] > 0 for r in rows), sum(r["substituted_days"] for r in rows), sum(r["months_without_substitution"] for r in rows), sum(r["months_with_substitution"] for r in rows), len(rows) * 365)
            self.assertEqual(values, actual)

    def test_uk_substitution_source_error_remains_visible(self):
        s = self.uk["substitution"]
        self.assertEqual((449, 67, 225, 15695), tuple(s[k]["value"] for k in ("months_without_substitution", "months_with_substitution", "substituted_days", "source_denominator_days")))
        self.assertEqual(("1.4", "1.43", "2.3"), tuple(s[k]["value"] for k in ("table8_percent", "appendix_percent", "contradictory_prose_percent")))
        self.assertAlmostEqual(225 / 15695 * 100, float(s["arithmetic_percent"]["value"]))
        self.assertFalse(s["source_prose_repaired"])
        self.assertFalse(s["raw_uninterrupted_measurement_claim"])
        self.assertEqual(54, next(r for r in self.uk["records"] if r["case_id"] == "327BSW")["substituted_days"])

    def test_uk_processed_records_keep_breakdown_bias_and_rating_limits(self):
        limits = self.uk["limits"]
        self.assertIn("breakdown", limits["case_328CHI"])
        self.assertIn("short draw-offs", limits["short_dhw_draws"])
        self.assertIn("omitted CPSU", limits["product_rating_metadata"])
        self.assertIn("B-rated regular", limits["case_325JSE"])
        self.assertFalse(limits["annual_table_heat_adjustment_applied"])
        self.assertFalse(limits["illustrative_cylinder_loss_adjustment_adopted"])
        self.assertFalse(limits["sap_factor_adopted"])
        self.assertIsNone(limits["measurement_uncertainty"])

    def test_uk_period_scopes_and_selection_not_national_or_calendar_claim(self):
        self.assertIn("September 2007-November 2008", self.uk["period"]["overview"])
        self.assertIn("June 2007-October 2008", self.uk["period"]["acceptance_table"])
        self.assertFalse(self.uk["period"]["degree_day_adjusted"])
        self.assertFalse(self.uk["period"]["one_common_calendar_year_assumed"])
        self.assertEqual((60, 43), tuple(self.uk["selection"][k]["value"] for k in ("initial_sites", "accepted_sites")))
        self.assertIn("non-random", self.uk["selection"]["recruitment"])
        self.assertIsNone(self.uk["selection"]["national_weights"])
        self.assertFalse(self.uk["selection"]["old_conventional_baseline"])

    def test_2010_continuation_retains_overlap_and_count_discrepancy(self):
        c = self.uk["continuation_2010"]
        self.assertEqual((52, 37, 29, 8, 28, 82, 46, 43, 338, 29930, 882, 102), tuple(c[k]["value"] for k in ("monitored_homes", "accepted_extension_sets", "tpi_sets", "non_tpi_sets", "paired_tpi_sites", "combined_sets", "prose_original_sets", "table2_original_sets", "substituted_days", "source_denominator_days", "unchanged_months", "months_with_substitution")))
        self.assertEqual({"combination": 21, "regular": 6, "CPSU": 1}, {k: v["value"] for k, v in c["paired_classes"].items()})
        self.assertTrue(c["same_cohort_family"])
        for key in ("independent_replication", "counts_reconciled", "added_to_2009_cohort", "tpi_savings_factor_adopted"):
            self.assertFalse(c[key])
        self.assertIsNone(c["unique_homes_inferred"])

    def test_typed_quantities_have_status_and_unit(self):
        def walk(value):
            if isinstance(value, dict):
                if "value" in value:
                    self.assertIn(value["truth"], {"OBS", "DER", "ASS", "SCN", "POL", "Q"})
                    self.assertTrue(value["unit"])
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(self.manifest)
        for family in self.manifest["families"].values():
            self.assertEqual("percent_GCV", family["record_field_policy"]["gcv_efficiency_pct"]["unit"])

    def test_actual_efficiency_gate_rejects_all_57_native_records(self):
        # The fraction is dimensional scaling only, never GCV-to-LHV conversion.
        # No fake CalorificBasis or borrowed gas-quality context is constructed.
        for family in self.manifest["families"].values():
            self.assertIsNone(family["gas_basis"]["calorific_reference_temperature_c"])
            self.assertIsNone(family["gas_basis"]["gas_quality_context_id"])
            self.assertIsNone(family["gas_basis"]["compatible_gcv_lhv_pair"])
            for row in family["records"]:
                with self.subTest(case=row["case_id"]):
                    evidence = GasEfficiencyEvidence(float(row["gcv_efficiency_pct"]) / 100, EvidenceStatus(row["truth"]), EfficiencyMetric.SEASONAL_FUEL_CONVERSION_EFFICIENCY, EnergyBasis.GCV, row["source_id"])
                    with self.assertRaisesRegex(ValueError, "explicit efficiency calorific reference and gas-quality context"):
                        authorize_fuel_volume_efficiency(evidence)

    def test_research_progress_does_not_change_existing_acceptance_or_readiness(self):
        plan = json.loads((ROOT / "registry/v1_research_plan.json").read_text())
        task = next(s for m in plan["modules"] for s in m["slices"] if s["slice_id"] == "B11-D01")
        self.assertEqual("INTEGRATING", task["status"])
        self.assertEqual(["SRC-B06-TABULA-HU-CALCULATOR-2016", "SRC-B06-TABULA-METHOD-2013-LOCAL-REFERENCE"], task["canonical_source_ids"])
        self.assertEqual([], task["accepted_artifacts"])
        self.assertEqual([], task["consumer_tests"])
        self.assertIsNone(task["reviewed_commit"])
        self.assertEqual(set(task["validation_debt_ids"]), {d["id"] for d in self.manifest["validation_debt"]})
        self.assertEqual("30", next(r for r in csv_rows(ROOT / "registry/module_status.csv") if r["module_id"] == "B11")["readiness_percent"])

    def test_no_production_consumer_or_source_default_added(self):
        for directory in ("modules", "model"):
            for path in (ROOT / directory).rglob("*.py"):
                content = path.read_text()
                self.assertNotIn(MANIFEST_PATH.name, content, str(path))
                for sid in self.sources:
                    self.assertNotIn(sid, content, str(path))
        for family in self.manifest["families"].values():
            self.assertEqual("Q", family["target_authority"]["applicability_status"])
            for key in ("usable_for_engine", "model_default_admitted", "national_factor_admitted", "task_accepted"):
                self.assertIs(False, family["target_authority"][key])

    def test_no_private_artifacts_or_original_source_dump(self):
        text = MANIFEST_PATH.read_text()
        for token in ("libfile_", "sediment://", "/workspace/", "data:application/", "base64", "extracted_text", "response_headers"):
            self.assertNotIn(token, text)
        self.assertIsNone(re.search(r"(?i)\b[0-9a-f]{16}!(?:s[0-9a-f]{32}|\d+)\b", text))
        self.assertTrue(all(s["repo_snapshot_path"] is None for s in self.sources.values()))

    def test_privacy_item_id_pattern_uses_synthetic_examples_only(self):
        pattern = r"(?i)\b[0-9a-f]{16}!(?:s[0-9a-f]{32}|\d+)\b"
        for example in ("0" * 16 + "!s" + "1" * 32, "0" * 16 + "!123"):
            self.assertIsNotNone(re.search(pattern, example))
        self.assertIsNone(re.search(pattern, "SRC-B11-EST-FIELD-2009"))

    def test_registry_accepts_exact_candidate(self):
        self.assertEqual([], self._errors())

    def test_validator_is_integrated_into_normal_registry_check(self):
        with patch.object(validate_registry, "validate_b11_seasonal_references") as check:
            validate_registry.validate()
        check.assert_called_once()

    def test_adversarial_unknown_default_fields_and_source_statistics_are_rejected(self):
        self.assertTrue(self._errors(lambda m: m.update(default_efficiency=0.9)))
        self.assertTrue(self._errors(lambda m: m["families"][BOI].update(default_efficiency=0.9)))
        self.assertTrue(self._errors(lambda m: m["families"][UK]["source_subgroups"]["regular"]["mean"].update(value="90.0")))
        self.assertTrue(self._errors(lambda m: m["families"][UK]["source_subgroups"]["CPSU"].update(pooled_mean_adopted="70.3")))
        self.assertTrue(self._errors(lambda m: m["families"][UK]["subgroup_audit"]["subgroups"]["regular"].update(sum_substituted_days=91)))

    def test_record_field_policies_match_native_family_semantics(self):
        boileff_policy = {
            "gcv_efficiency_pct": {"unit": "percent_GCV", "truth": "OBS", "statistic": "SOURCE_LABELLED_MEASURED_EFFICIENCY", "raw_uninterrupted_measurement_claim": False},
        }
        uk_policy = {
            "gcv_efficiency_pct": {"unit": "percent_GCV", "truth": "DER", "statistic": "SOURCE_PROCESSED_ACCEPTED_ANNUAL_HEAT_OUTPUT_OVER_GAS_ENERGY", "raw_uninterrupted_measurement_claim": False},
            "months_without_substitution": {"unit": "month", "truth": "OBS", "statistic": "SOURCE_REPORTED_ACCEPTANCE_COUNT"},
            "months_with_substitution": {"unit": "month", "truth": "OBS", "statistic": "SOURCE_REPORTED_ACCEPTANCE_COUNT"},
            "substituted_days": {"unit": "day", "truth": "OBS", "statistic": "SOURCE_REPORTED_SUBSTITUTION_COUNT"},
        }
        self.assertEqual(boileff_policy, self.boi["record_field_policy"])
        self.assertEqual(uk_policy, self.uk["record_field_policy"])
        for family in (self.boi, self.uk):
            for row in family["records"]:
                self.assertEqual(family["record_field_policy"]["gcv_efficiency_pct"]["truth"], row["truth"])

    def test_adversarial_rehashed_boileff_classes_cannot_be_reclassified_or_removed(self):
        for index in range(len(self.boi["records"])):
            for value in ("old_non_condensing", "regular", "", None):
                with self.subTest(case=self.boi["records"][index]["case_id"], value=value):
                    errors = self._errors(lambda m: m["families"][BOI]["records"][index].update(appliance_class=value), rehash=True)
                    self.assertTrue(any("source-qualified appliance class mismatch" in e for e in errors))
                    self.assertFalse(any("record integrity mismatch" in e for e in errors))

    def test_adversarial_field_policy_truth_unit_and_statistic_conflicts_are_rejected(self):
        for family_id, family in self.manifest["families"].items():
            for field, policy in family["record_field_policy"].items():
                mutations = {"truth": "OBS" if policy["truth"] == "DER" else "DER", "unit": "fraction_LHV", "statistic": "RAW_UNINTERRUPTED_MEASUREMENT"}
                for key, value in mutations.items():
                    with self.subTest(family=family_id, field=field, key=key):
                        errors = self._errors(lambda m: m["families"][family_id]["record_field_policy"][field].update({key: value}), rehash=True)
                        self.assertTrue(any("source field policy mismatch" in e for e in errors))
                        self.assertFalse(any("record integrity mismatch" in e for e in errors))

    def test_adversarial_rehashed_policy_and_records_cannot_jointly_change_truth(self):
        def mutate(m):
            family = m["families"][UK]
            family["record_field_policy"]["gcv_efficiency_pct"]["truth"] = "OBS"
            for row in family["records"]:
                row["truth"] = "OBS"
        errors = self._errors(mutate, rehash=True)
        self.assertTrue(any("source field policy mismatch" in e for e in errors))
        self.assertTrue(any("source fact type mismatch" in e for e in errors))
        self.assertFalse(any("record integrity mismatch" in e for e in errors))

    def test_adversarial_native_value_tampering_is_rejected(self):
        for family in (BOI, UK):
            with self.subTest(family=family):
                self.assertTrue(any("record integrity" in e for e in self._errors(lambda m: m["families"][family]["records"][0].update(gcv_efficiency_pct="90.0"))))

    def test_adversarial_missing_or_changed_provenance_is_rejected(self):
        for field, value in (("sha256", "0" * 64), ("original_url", ""), ("authority", ""), ("retrieved_at", ""), ("reference_period", "")):
            with self.subTest(field=field):
                self.assertTrue(self._errors(lambda m: m["sources"][0].update({field: value})))
        self.assertTrue(self._errors(lambda m: m["families"][UK]["records"][0].pop("locator")))
        self.assertTrue(self._errors(lambda m: m["families"][UK]["records"][0].pop("substitution_locator")))

    def test_adversarial_global_and_local_source_drift_is_rejected(self):
        sid = "SRC-B11-EST-FIELD-2009"
        for filename, field, value in (("sources.csv", "local_snapshot_sha256", "0" * 64), ("sources.csv", "url", "https://example.invalid"), ("b11_gas_efficiency_sources.csv", "url", "https://example.invalid"), ("b11_gas_efficiency_sources.csv", "authority_status", "ACCEPTED")):
            def mutate(path, rows):
                if path.name == filename:
                    next(r for r in rows if r["source_id"] == sid)[field] = value
            with self.subTest(file=filename, field=field):
                self.assertTrue(self._errors(csv_mutate=mutate))

    def test_adversarial_mixed_families_geographies_and_boundaries_are_rejected(self):
        for family, changes in ((BOI, {"geography": "UK"}), (BOI, {"family_id": UK}), (BOI, {"use_scope": "HISTORICAL_UK_REFERENCE"}), (UK, {"boundary_id": "REGULAR_BOILER_OUTPUT_BEFORE_CYLINDER"}), (UK, {"geography": "HU"}), (UK, {"source_id": "SRC-B11-BOILEFF-FINAL-2009"})):
            with self.subTest(changes=changes):
                self.assertTrue(self._errors(lambda m: m["families"][family]["records"][0].update(changes), rehash=True))

    def test_adversarial_fake_admission_or_default_is_rejected(self):
        for family in (None, BOI, UK):
            for key, value in (("usable_for_engine", True), ("model_default_admitted", True), ("task_accepted", True), ("applicability_status", "OBS"), ("fuel_volume_authority_status", "DER"), ("national_factor_admitted", True)):
                def mutate(m):
                    obj = m if family is None else m["families"][family]
                    obj["target_authority"][key] = value
                with self.subTest(family=family, key=key):
                    self.assertTrue(any("authority" in e or "admission" in e for e in self._errors(mutate)))

    def test_adversarial_invented_calorific_context_or_conversion_is_rejected(self):
        for family in (BOI, UK):
            for field in ("fuel_subtype", "calorific_reference_temperature_c", "gas_quality_context_id", "compatible_gcv_lhv_pair", "volume_reference_state", "lhv_efficiency", "runtime_fuel_volume"):
                with self.subTest(family=family, field=field):
                    self.assertTrue(any("invented gas-basis" in e for e in self._errors(lambda m: m["families"][family]["gas_basis"].update({field: "invented"}))))

    def test_adversarial_aggregate_repair_or_averaging_into_default_is_rejected(self):
        self.assertTrue(any("must not be repaired" in e for e in self._errors(lambda m: m["families"][BOI]["aggregate_discrepancy"]["source_reported"]["HU"].update(value="86.15"))))
        for changes in ({"weights": [1] * 14}, {"default_selected": True}, {"source_aggregates_repaired": True}):
            self.assertTrue(self._errors(lambda m: m["families"][BOI]["aggregate_discrepancy"].update(changes)))

    def test_adversarial_source_uncertainty_adjustments_or_raw_claims_are_rejected(self):
        for key in ("pooled_unlike_boundaries", "sd_is_measurement_uncertainty_or_ci", "extrema_are_population_or_prediction_intervals", "usage_weighted_table_14_substituted"):
            self.assertTrue(self._errors(lambda m: m["families"][UK]["source_subgroups"].update({key: True})))
        for key in ("annual_table_heat_adjustment_applied", "illustrative_cylinder_loss_adjustment_adopted", "sap_factor_adopted", "qa_thresholds_are_measurement_uncertainty"):
            self.assertTrue(self._errors(lambda m: m["families"][UK]["limits"].update({key: True})))
        self.assertTrue(self._errors(lambda m: m["families"][UK]["substitution"].update(raw_uninterrupted_measurement_claim=True)))

    def test_adversarial_2010_additive_merge_and_reconciliation_are_rejected(self):
        for key in ("independent_replication", "counts_reconciled", "added_to_2009_cohort", "tpi_savings_factor_adopted"):
            self.assertTrue(self._errors(lambda m: m["families"][UK]["continuation_2010"].update({key: True})))
        self.assertTrue(self._errors(lambda m: m["families"][UK]["continuation_2010"].update(unique_homes_inferred=82)))

    def test_adversarial_blank_agreement_and_document_redistribution_are_rejected(self):
        self.assertTrue(self._errors(lambda m: m["families"][BOI]["period"]["blank_agreement"].update(completed_observation_evidence=True)))
        self.assertTrue(self._errors(lambda m: m["sources"][0].update(repo_snapshot_path="evidence/original.pdf")))
        self.assertTrue(self._errors(lambda m: m["sources"][0].update(reuse_status="CLEARED")))

    def test_adversarial_missing_or_duplicate_rows_are_rejected(self):
        for family in (BOI, UK):
            self.assertTrue(self._errors(lambda m: m["families"][family]["records"].pop(), rehash=True))
            self.assertTrue(self._errors(lambda m: m["families"][family]["records"].append(copy.deepcopy(m["families"][family]["records"][0])), rehash=True))


if __name__ == "__main__":
    unittest.main()
