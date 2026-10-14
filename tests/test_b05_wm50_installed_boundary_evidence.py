"""WM50 evidence-only contract and independently recorded manufacturer semantics.

Oracles: Grundfos99092813 03.2022 PDF18 (TM050006 / UPM3 table),
PDF18-19 optional flow feedback, PDF16 versus19 input-frequency discrepancy;
Grundfos59C90800 identity/spec API and original water20degC P1/Q PNG.
These fixed observations are not computed from a manifest hash. No physical
installed-system performance is validated by these metadata tests.
"""
import copy
import csv
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import validate_registry as validator

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "registry/b05_wm50_installed_boundary_evidence.json"
G = "SRC-B05-GRUNDFOS-UPM3-"
IDENTITY, SPEC, CURVE = (G + "59C90800-" + x + "-2026" for x in ("IDENTITY", "SPEC", "CURVE"))
BOOK = G + "DATABOOK-2022"
# Independently recorded original downloaded response identities, not manifest digests.
SOURCE_HASHES = {
    IDENTITY: "dbc66b8c0a62fe1e64d60f6162312320b9cdbfa5ba1470300f6813ec03a99b72",
    SPEC: "060977d79035b64b560bc6d83be3aa22068182f26835d0821512ea2794c85d50",
    CURVE: "57333919d8a64ca296976e700bb85c70a2f757cba4c44cab1af5e7f8df3b7a92",
    BOOK: "be5cf2a0b1be5705c2d2b413ae7be074fa7496340650806a21124639c435d0e0",
    "SRC-B05-MITSUBISHI-EHPT-PARTS-OCB714A": "d688c167aeabe8ea61d106fe86380ff0223496067b8d454cde363e7d44948814",
    "SRC-B05-MITSUBISHI-EHPT-PRODUCT-2020": "54c6146fd75462dd27a665dc74ad70d01da66e4eca099affbcd9960148096dda",
    "SRC-B05-MITSUBISHI-EHPT-SERVICE-OCH714A": "466f06c0e563fa195e74fa99dcfae02426057653795e7c53083443432bcece31",
}


class WM50InstalledEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(PATH.read_text(encoding="utf-8"))
        self.claims = {c["id"]: c for c in self.manifest["claims"]}

    def _errors(self, mutate=None, csv_mutate=None):
        candidate = copy.deepcopy(self.manifest)
        if mutate:
            mutate(candidate)
        original_text, original_csv = Path.read_text, validator.read_csv

        def text(path, *args, **kwargs):
            if path == PATH:
                return json.dumps(candidate)
            return original_text(path, *args, **kwargs)

        def rows(path):
            header, data = original_csv(path)
            if csv_mutate:
                csv_mutate(path, data)
            return header, data

        ids = {r["source_id"] for r in original_csv(ROOT / "registry/sources.csv")[1]}
        errors = []
        with patch.object(Path, "read_text", text), patch.object(validator, "read_csv", rows):
            validator.validate_b05_wm50_installed_boundary_evidence(errors, ids)
        return errors

    def _claim(self, manifest, cid):
        return next(c for c in manifest["claims"] if c["id"] == cid)

    def test_complete_source_reference_contract(self):
        self.assertEqual([], self._errors())

    def test_original_source_identities_are_not_a_self_hash_oracle(self):
        self.assertEqual(SOURCE_HASHES, {s["source_id"]: s["sha256"] for s in self.manifest["sources"]})
        sources = {s["source_id"]: s for s in self.manifest["sources"]}
        self.assertEqual(41861, sources[CURVE]["bytes"])
        self.assertEqual(24526489, sources[BOOK]["bytes"])
        self.assertEqual("2022-03", sources[BOOK]["document_date"])
        self.assertIn("99092813 03.2022", sources[BOOK]["document_revision"])
        self.assertEqual("https://api.grundfos.com/literature/Grundfosliterature-6154040.pdf",
                         sources[BOOK]["original_url"])
        self.assertIn("pumpcurve?pumpsystemid=3064924080", sources[CURVE]["original_url"])

    def test_manufacturer_power_scale_and_status_code_oracle(self):
        value = self.claims["OEM-06"]["values"]
        self.assertIn("PDF18", self.claims["OEM-06"]["locator"])
        self.assertEqual([0, 70], value["normal_power_W"])
        self.assertEqual(1, value["slope_W_per_percentagepoint"])
        self.assertEqual((75, 85, 90, 95), tuple(value[k] for k in (
            "warning_percent", "electrical_fault_percent", "blocked_percent", "standby_percent")))
        self.assertFalse(value["status_codes_are_power_samples"])
        self.assertEqual("±2% of PWM signal", value["accuracy_source_wording"])

    def test_curve_is_candidate_water20_electrical_not_head_or_W55(self):
        value = self.claims["OEM-03"]["values"]
        self.assertEqual(("Water", 20, 998.2, "W", "m3/h"),
                         tuple(value[k] for k in ("medium", "liquid_temperature_degC", "density_kg_m3",
                                                  "electrical_power_unit", "flow_unit")))
        self.assertEqual({"P1_min_W": 2, "P1_max_W": 60, "curve_set": "c0016333"},
                         self.claims["OEM-02"]["values"])
        self.assertIsNone(value["control_selector"])

    def test_status_and_UPM3L_power_mapping_substitutions_reject(self):
        cases = [("family", "UPM3L"), ("slope_W_per_percentagepoint", 2),
                 ("normal_power_W", [0, 140]), ("status_codes_are_power_samples", True),
                 ("standby_percent", 0), ("accuracy_source_wording", "±2% annual electricity")]
        for key, value in cases:
            with self.subTest(key=key):
                self.assertTrue(self._errors(lambda m: self._claim(m, "OEM-06")["values"].__setitem__(key, value)))

    def test_input_PWM_cannot_be_runtime_share(self):
        self.assertTrue(self._errors(lambda m: self._claim(m, "OEM-05")["values"].__setitem__("input_is_runtime_fraction", True)))

    def test_optional_flow_semantics_cannot_be_deleted(self):
        self.assertTrue(self._errors(lambda m: self._claim(m, "OEM-07")["values"].__setitem__("optional_flow_feedback_exists", False)))

    def test_frequency_discrepancy_cannot_be_silently_repaired(self):
        self.assertEqual({"text_range": [100, 1500], "table_range": [100, 4000]}, self.claims["OEM-08"]["values"])
        self.assertTrue(self._errors(lambda m: self._claim(m, "OEM-08")["values"].__setitem__("table_range", [100, 1500])))

    def test_curve_relabelling_or_branch_selection_reject(self):
        for key, value in (("liquid_temperature_degC", 55), ("medium", "Glycol"),
                           ("electrical_power_unit", "m"), ("control_selector", 5), ("W55_transfer_admitted", True)):
            with self.subTest(key=key):
                self.assertTrue(self._errors(lambda m: self._claim(m, "OEM-03")["values"].__setitem__(key, value)))

    def test_method_dimensions_and_domain_are_conditional(self):
        method = self.manifest["conditional_methods"][0]
        self.assertEqual("DER", method["status"])
        self.assertEqual({"lower_exclusive": 0, "upper_exclusive": 70}, method["normal_domain_percentagepoint"])
        self.assertEqual(0.001, method["energy_Wh_to_kWh"])
        self.assertFalse(method["applied_to_MP1"])
        for key, value in (("profile", "FLOW_FEEDBACK"), ("applied_to_MP1", True), ("numeric_result", 0),
                           ("normal_domain_percentagepoint", {"lower_exclusive": 0, "upper_exclusive": 100}),
                           ("slope_W_per_percentagepoint", True), ("energy_Wh_to_kWh", 1)):
            with self.subTest(key=key):
                self.assertTrue(self._errors(lambda m: m["conditional_methods"][0].__setitem__(key, value)))
        self.assertTrue(self._errors(lambda m: m["conditional_methods"][0]["units"].__setitem__("duration", "s")))
        self.assertTrue(self._errors(lambda m: m["conditional_methods"][0].__setitem__("formula", "P1 = input PWM")))

    def test_hardware_candidate_and_exact_OEM_Q_are_separate(self):
        for key in ("canonical_configuration_selected", "candidate_component_is_exact_MP1"):
            with self.subTest(key=key):
                self.assertTrue(self._errors(lambda m: m["configurations"][0].__setitem__(key, True)))
        self.assertTrue(self._errors(lambda m: m["target_authority"].__setitem__("exact_oem_binding_status", "E1")))

    def test_no_runtime_default_or_acceptance_promotion(self):
        for key, value in self.manifest["target_authority"].items():
            if value is False:
                with self.subTest(key=key):
                    self.assertTrue(self._errors(lambda m: m["target_authority"].__setitem__(key, True)))

    def test_linked_artifacts_are_not_independent_supports(self):
        self.assertTrue(self._errors(lambda m: m["source_families"][0].__setitem__("independent_replication", True)))
        self.assertTrue(self._errors(lambda m: m["source_families"][0]["members"].pop()))
        self.assertTrue(self._errors(lambda m: m["source_aliases"].__setitem__("ANOTHER_ALIAS", IDENTITY)))

    def test_uncleared_copy_and_cross_registry_identity_reject(self):
        self.assertTrue(self._errors(lambda m: m["sources"][0].__setitem__("repo_snapshot_path", "evidence/page.png")))
        self.assertTrue(self._errors(lambda m: m["sources"][0].__setitem__("reuse_status", "CLEARED")))
        self.assertTrue(self._errors(lambda m: m["sources"][0].__setitem__("sha256", "0" * 64)))
        self.assertTrue(self._errors(lambda m: m["claims"][0].__setitem__("source_ids", ["UNKNOWN"])))

    def test_missing_or_malformed_metadata_report_errors(self):
        self.assertTrue(self._errors(lambda m: m.pop("claims")))
        self.assertTrue(self._errors(lambda m: m["sources"][0].__setitem__("retrieved_at", "unknown")))
        self.assertTrue(self._errors(lambda m: m["sources"].append(copy.deepcopy(m["sources"][0]))))

    def test_installed_unknowns_and_accepted_rating_continuation(self):
        output = self.manifest["current_output_contract"]
        self.assertEqual("UNCHANGED", output["rating_reference_E2"])
        self.assertFalse(output["accepted_rating_E2_continuation_blocked"])
        self.assertIsNone(output["annual_signed_residual"]["value_kwh"])
        self.assertIsNone(output["hourly_signed_residual"]["timing"])
        self.assertTrue(self._errors(lambda m: m["current_output_contract"]["annual_signed_residual"].__setitem__("value_kwh", 0)))
        self.assertTrue(self._errors(lambda m: m["current_output_contract"].__setitem__("accepted_rating_E2_continuation_blocked", True)))
        self.assertTrue(self._errors(lambda m: m["current_output_contract"]["installed_heat_service"].__setitem__("installed_service_completion", True)))

    def test_audit_model_blockers_cannot_block_accepted_rating(self):
        def mutate(path, rows):
            if path.name == "project_blocker_evidence_audit.csv":
                for row in rows:
                    if row["blocker_id"] == "B05-WM50-INSTALLED-ANNUAL":
                        row["reason"] = "All B05 modelling blocked"
                        row["canonical_use"] = "NO_RATING_E2_CONTINUATION"
        self.assertTrue(self._errors(csv_mutate=mutate))
        self.assertTrue(self._errors(lambda m: m["validation_debt"][1].__setitem__("blocks_accepted_rating_E2", True)))
        self.assertTrue(self._errors(lambda m: m["validation_debt"][0].__setitem__("blocks_complete_installed_claim", True)))

    def test_audit_and_manifest_acquisition_debt_must_match(self):
        self.assertTrue(self._errors(lambda m: m["validation_debt"][1].__setitem__("required", "Measure every component separately at E1")))


    def test_claim_uses_one_authoritative_method_without_shadow_values(self):
        claim = self.claims["OEM-09"]
        self.assertEqual("STANDARD_UPM3_POWER_FEEDBACK", claim["method_id"])
        self.assertFalse({"formula", "conditions", "numeric_result", "numerical_result"} & set(claim))
        for key, value in (("formula", "P1 = input PWM"), ("numeric_result", 0),
                           ("numerical_result", 0), ("conditions", []), ("method_id", "UNQUALIFIED_METHOD")):
            with self.subTest(key=key):
                errors = self._errors(lambda m: self._claim(m, "OEM-09").__setitem__(key, value))
                self.assertTrue(any("duplicated derivation fields forbidden" in e for e in errors), errors)

    def test_each_mandatory_condition_and_its_meaning_are_required(self):
        expected = {
            "STANDARD_POWER_FEEDBACK_BINDING": "Exact MP1 is independently bound to the standard UPM3 power-feedback profile.",
            "NORMAL_UNSATURATED_SAMPLES": "Only normal samples with 0 < D_fb < 70 percentagepoints; alarm, standby and saturation codes are excluded.",
            "QUALIFIED_ACQUISITION_TIME_COVERAGE": "Signal acquisition, sample durations, time coverage, missing-data treatment and uncertainty are qualified.",
        }
        conditions = self.manifest["conditional_methods"][0]["conditions"]
        self.assertEqual(expected, {c["condition_id"]: c["requirement"] for c in conditions})
        for index in range(3):
            for mutation in ("delete", "replace_id", "replace_meaning"):
                with self.subTest(condition=conditions[index]["condition_id"], mutation=mutation):
                    def change(m):
                        rows = m["conditional_methods"][0]["conditions"]
                        if mutation == "delete":
                            rows.pop(index)
                        elif mutation == "replace_id":
                            rows[index]["condition_id"] = "OPTIONAL_UNRELATED_CONDITION"
                        else:
                            rows[index]["requirement"] = "Unqualified samples are sufficient; no binding or coverage required."
                    errors = self._errors(change)
                    self.assertTrue(any("mandatory method conditions" in e for e in errors), errors)
        self.assertTrue(self._errors(lambda m: m["conditional_methods"][0]["conditions"].__setitem__(
            1, copy.deepcopy(m["conditional_methods"][0]["conditions"][0]))))
        self.assertTrue(self._errors(lambda m: m["conditional_methods"][0].__setitem__("numerical_result", None)))

    def test_existing_binding_source_is_reused_without_eighth_artifact(self):
        binding = "SRC-B05-MITSUBISHI-WM50-FTC6-BINDING-2026"
        self.assertEqual(7, len(self.manifest["sources"]))
        self.assertNotIn(binding, {s["source_id"] for s in self.manifest["sources"]})
        self.assertEqual([binding], [s["source_id"] for s in self.manifest["reused_sources"]])
        self.assertEqual("ed8090f77ffa0be787ba970254c72348b471e86275136fa77a1c12d98f70084c",
                         self.manifest["reused_sources"][0]["sha256"])
        pairing = self.claims["OEM-11"]
        self.assertIn(binding, pairing["source_ids"])
        self.assertEqual("PDF3 Product Description; PDF7 Functional unit", pairing["source_locators"][binding])
        self.assertEqual({"combined_heating_DHW_LCA_source": True, "rating_specimen_proven": False,
                          "actual_installation_proven": False}, pairing["limits"])
        self.assertTrue(self._errors(lambda m: self._claim(m, "OEM-11")["source_ids"].remove(binding)))
        self.assertTrue(self._errors(lambda m: self._claim(m, "OEM-11")["source_locators"].pop(binding)))
        self.assertTrue(self._errors(lambda m: self._claim(m, "OEM-11")["limits"].__setitem__("rating_specimen_proven", True)))
        self.assertTrue(self._errors(lambda m: self._claim(m, "OEM-11")["limits"].__setitem__("actual_installation_proven", True)))
        self.assertTrue(self._errors(lambda m: m["reused_sources"].append(copy.deepcopy(m["reused_sources"][0]))))

    def test_debt_assessment_describes_local_candidate_without_acceptance(self):
        assessment = next(e for e in self.manifest["current_output_contract"]["e2_assessment"] if e["condition"] == 7)
        self.assertEqual("REGISTERED_IN_LOCAL_CANDIDATE", assessment["verdict"])
        self.assertIn("Three E3/Q debt rows", assessment["reason"])
        self.assertFalse(self.manifest["target_authority"]["task_accepted"])
        for key, value in (("verdict", "DOCUMENTED_IN_RESEARCH_ONLY"),
                           ("reason", "Debt below is actionable; no canonical registry mutation authorized.")):
            with self.subTest(key=key):
                def change(m):
                    row = next(e for e in m["current_output_contract"]["e2_assessment"] if e["condition"] == 7)
                    row[key] = value
                errors = self._errors(change)
                self.assertTrue(any("registered local candidate" in e for e in errors), errors)



if __name__ == "__main__":
    unittest.main()
