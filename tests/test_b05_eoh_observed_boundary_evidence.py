"""Owner-supplied exact excerpts are metadata oracles, not a new measurement.

No runtime parser/calibration or original-source byte inspection is performed.
"""
import copy
import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import validate_registry as validator

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "registry/b05_eoh_observed_boundary_manifest.json"


class EOHObservedEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.m = json.loads(PATH.read_text(encoding="utf-8"))

    def errors(self, mutate=None):
        candidate = copy.deepcopy(self.m)
        if mutate:
            mutate(candidate)
        original = Path.read_text

        def text(path, *args, **kwargs):
            if path == PATH:
                return json.dumps(candidate)
            return original(path, *args, **kwargs)

        source_ids = {r["source_id"] for r in validator.read_csv(ROOT / "registry/sources.csv")[1]}
        errors = []
        with patch.object(Path, "read_text", text):
            validator.validate_b05_eoh_observed_boundary_evidence(errors, source_ids)
        return errors

    def test_complete_metadata_contract(self):
        self.assertEqual([], self.errors())

    def test_reviewer_consumer_and_bundle_verification_are_distinct(self):
        for key in ("consumer_original_bytes_hashed", "consumer_full_artifact_files_inspected",
                    "consumer_library_zip_materialized", "reviewer_check_is_independent_physical_measurement"):
            with self.subTest(key=key):
                self.assertTrue(self.errors(lambda m: m["inspection"].__setitem__(key, True)))
        self.assertTrue(self.m["inspection"]["consumer_textual_excerpts_reviewed"])

    def test_reported_original_identities_match_the_handoff(self):
        sources = {s["source_id"]: s for s in self.m["sources"]}
        self.assertEqual(("325a0f8edcfd2b3935ca8ee9b666d6ab7a4b2137af82ed14fe7f9b485b82004f", 1286711795),
                         (sources["SRC-B05-DESNZ-EOH-CLEANSED-2MIN-9050"]["sha256"],
                          sources["SRC-B05-DESNZ-EOH-CLEANSED-2MIN-9050"]["bytes"]))
        self.assertEqual("46429fe7948a55da4afb6e3429e6c859cb9bd2ac05f4bebb54b102ce84702e59",
                         sources["SRC-B02-DESNZ-EOH-PDI-2024"]["sha256"])
        self.assertEqual("b0df7899064e0d33679d760b6bc2be52d06f1d3093d7b20aa283a632db4175f7",
                         sources["SRC-B05-DESNZ-EOH-DICTIONARY-V2"]["sha256"])
        artifacts = {a["file"]: a for a in self.m["artifacts"]}
        self.assertEqual("da5aadb46df1952a5e72d73b6780ec166bb9d77c5371f23ccc0549fe0459cf9a",
                         artifacts["all_period_common_interval_year.csv"]["sha256"])
        self.assertEqual("cf8af2357fcc5a6e936232e37b55ab316f4bf06e0031fddfe76977a6ae2de5bf",
                         artifacts["EOH2074_target_family_review.json"]["sha256"])

    def test_unregistered_or_duplicate_source_rejected(self):
        self.assertTrue(self.errors(lambda m: m["sources"][0].__setitem__("source_id", "SRC-B05-INVENTED")))
        self.assertTrue(self.errors(lambda m: m["sources"].append(copy.deepcopy(m["sources"][0]))))

    def test_no_raw_snapshot_or_invented_monitoring_pdf_digest(self):
        self.assertTrue(self.errors(lambda m: m["sources"][0].__setitem__("repo_snapshot_path", "evidence/raw.zip")))
        self.assertTrue(self.errors(lambda m: m["sources"][3].__setitem__("sha256", "a"*64)))
        self.assertTrue(self.errors(lambda m: m["sources"][3].__setitem__("diagram_inspection_claimed", True)))

    def test_original_package_scope_not_742_project_records(self):
        self.assertTrue(self.errors(lambda m: m["populations"].__setitem__("members", 742)))
        p = self.m["populations"]["primary"]
        self.assertEqual((33, 4546, 96019, 3200.6333), (p["systems"], p["windows"], p["intervals"], p["observed_hours_reported"]))

    def test_primary_identity_and_sime_exception_oracles(self):
        ids = {p for g in self.m["primary_identity_groups"] for p in g["property_ids"]}
        expected = set("EOH2205 EOH1701 EOH1792 EOH2155 EOH2285 EOH2022 EOH1876 EOH2264 EOH2206 EOH1999 EOH1970 EOH1980 EOH1708 EOH2012 EOH1847 EOH1699 EOH1935 EOH2167 EOH2198 EOH2350 EOH2228 EOH1884 EOH2397 EOH1712 EOH2308 EOH2058 EOH1837 EOH2089 EOH2005 EOH2003 EOH2045 EOH1694 EOH2056".split())
        self.assertEqual(expected, ids)
        self.assertTrue(self.errors(lambda m: m["primary_identity_groups"][0]["property_ids"].append("EOH2004")))
        self.assertTrue(self.errors(lambda m: m["metering"].__setitem__("PDI_model_is_automatically_outdoor_identity", True)))

    def test_original_year_fields_keep_different_common_masks(self):
        row = self.m["selected_rows"]["year"]["fields"]
        self.assertEqual((261997, 261847), (row["HP_E_common_steps"], row["HP_E_CP_common_steps"]))
        self.assertEqual((2515.232000000001, 1272.3270000000025),
                         (row["HP_heat_kWh_HP_E_common"], row["whole_E_kWh_HP_E_common"]))
        self.assertEqual((2514.0880000000006, 1271.6850000000027, 407.46500000000003),
                         (row["HP_heat_kWh_HP_E_CP_common"], row["whole_E_kWh_HP_E_CP_common"], row["CP_kWh_HP_E_CP_common"]))
        self.assertEqual("NOT_COMPUTED", self.m["selected_rows"]["IH"]["HP_E_IH_common_intersection"])
        self.assertTrue(self.errors(lambda m: m["selected_rows"]["IH"].__setitem__("HP_E_IH_common_intersection", 131.2)))

    def test_zero_heat_is_not_standby_and_no_state_ledger_is_invented(self):
        for k, value in (("zero_or_negative_heat", "standby"), ("state_ledger_exists", True),
                         ("IH_BUH_common_intersection_exists", True)):
            with self.subTest(k=k):
                self.assertTrue(self.errors(lambda m: m["definitions"]["common_interval"].__setitem__(k, value)))

    def test_original_window_key_and_incomplete_CP_null(self):
        a = next(a for a in self.m["artifacts"] if a["file"] == "documented_SH_primary_comparative_population.csv")
        self.assertTrue(a["consumer_textual_excerpt_inspected"])
        self.assertFalse(a["consumer_full_file_inspected"])
        def hide_excerpt(m):
            next(a for a in m["artifacts"] if a["file"] == "documented_SH_primary_comparative_population.csv")["consumer_textual_excerpt_inspected"] = False
        self.assertTrue(self.errors(hide_excerpt))
        w = self.m["selected_rows"]["windows"][2]
        self.assertEqual({"property_id": "EOH1694", "boundary_screen": "whole_E_aggregate",
                          "start": "2021-10-07 04:32:00", "end": "2021-10-07 05:08:00"}, w["key"])
        self.assertEqual((18, 16, False, None), tuple(w["fields"][k] for k in
                         ("steps", "CP_valid_steps", "CP_all_steps_observed", "CP_common_residual_E_kWh")))
        self.assertTrue(self.errors(lambda m: m["selected_rows"]["windows"][2]["fields"].__setitem__("CP_common_residual_E_kWh", 0)))

    def test_simultaneous_boiler_window_is_preserved(self):
        w = self.m["selected_rows"]["windows"][0]
        self.assertEqual("EOH1694", w["key"]["property_id"])
        self.assertEqual((28, 28), (w["fields"]["steps"], w["fields"]["boiler_positive_steps"]))
        self.assertEqual(0.7119999999999891, w["fields"]["boiler_signed_kWh_valid_steps_only"])
        self.assertIn("Boiler-off is not required", self.m["metering"]["standard_hybrids"])

    def test_proxy_and_research_screen_cannot_become_modes_or_admission(self):
        self.assertTrue(self.errors(lambda m: m["definitions"]["heating_proxy"].__setitem__("true_mode_telemetry", True)))
        self.assertTrue(self.errors(lambda m: m["definitions"]["near55"].__setitem__("COP_selection", True)))
        self.assertTrue(self.errors(lambda m: m["definitions"]["e_minus_cp"].__setitem__("compressor_only", True)))

    def test_year_assignment_count_support_and_descriptive_LOSO(self):
        self.assertEqual("summarize_archive.py", self.m["definitions"]["cells"]["script"])
        for section, key, value in (("year_drift", "year", "INTERVAL YEAR"),
                                    ("year_drift", "residual_drift", True),
                                    ("cells", "independent_validation", True),
                                    ("exact_count_support", "window_energy_split_across_year_or_clock", True)):
            with self.subTest(section=section, key=key):
                self.assertTrue(self.errors(lambda m: m["definitions"][section].__setitem__(key, value)))

    def test_target_actual_flow_does_not_admit_W55_or_timezone(self):
        target = self.m["target"]
        self.assertEqual((31.04, 34.25), (target["activity_selected_flow_c"]["median"], target["activity_selected_flow_c"]["p90"]))
        self.assertTrue(self.errors(lambda m: m["target"].__setitem__("timezone", "UTC")))
        self.assertTrue(self.errors(lambda m: m["target"].__setitem__("W55_transfer_admitted", True)))

    def test_no_new_runtime_numeric_or_task_admission(self):
        for key, value in self.m["non_admission"].items():
            if type(value) is bool:
                with self.subTest(key=key):
                    self.assertTrue(self.errors(lambda m: m["non_admission"].__setitem__(key, True)))
        self.assertTrue(self.errors(lambda m: m["non_admission"].__setitem__("exact_OEM_route", "MANDATORY")))

    def test_all_non_admission_keys_are_required_even_when_flags_are_deleted(self):
        for key in self.m["non_admission"]:
            with self.subTest(deleted=key):
                self.assertTrue(self.errors(lambda m: m["non_admission"].pop(key)))
        self.assertTrue(self.errors(lambda m: m.__setitem__("non_admission", {})))
        self.assertTrue(self.errors(lambda m: m.__setitem__("non_admission", {
            "rating_reference_E2": "UNCHANGED", "exact_OEM_route": "OPTIONAL"})))
        self.assertTrue(self.errors(lambda m: m["non_admission"].__setitem__("invented_flag", False)))

    def test_PDI_identity_locator_is_original_snapshot_not_target_diagnostics(self):
        c = next(c for c in self.m["claims"] if c["id"] == "EOH-05")
        self.assertEqual("pdi_public_current_2026-10-14.csv", c["artifact"])
        self.assertEqual({"Property_ID": "EOH2074"}, c["row_key"])
        self.assertEqual(["SRC-B02-DESNZ-EOH-PDI-2024"], c["source_ids"])
        self.assertEqual("2026-10-14", c["snapshot_date"])
        self.assertEqual({"Property_ID", "HP_Installed", "HP_Installed_Detail", "HP_Brand", "HP_Model",
                          "HP_Size_kW", "HP_Refrigerant", "MCS_Flow_Temp", "TS_Type", "TS_Water_Size",
                          "HP_Control_Zones"}, set(c["original_fields"]))
        def change(m, key, value):
            next(c for c in m["claims"] if c["id"] == "EOH-05")[key] = value
        self.assertTrue(self.errors(lambda m: change(m, "artifact", "EOH2074_target_family_review.json")))
        self.assertTrue(self.errors(lambda m: change(m, "row_key", {"Property_ID": "EOH0000"})))
        self.assertTrue(self.errors(lambda m: change(m, "original_fields", ["Property_ID"])))

    def test_runtime_and_annual_contract_bytes_unchanged_from_pinned_base(self):
        expected = {
            "modules/B05/annual_device_reference.py": "760088357610d2c41103c37d08761c63b7cc7c18b13b4c45de8ecef061d4a680",
            "modules/B11/annual_retrofit_reference.py": "e8852b6560b42e3754a110ebf54e01b4b0439da77b4146d5b0c1bd41428e41e6",
            "modules/B11/annual_same_service_reference.py": "595ffa907e0da7a62fa827c6d77a67841d64457887a317888c21df8ebbe0d9cd",
            "registry/b05_annual_device_reference_manifest.json": "d4f53d6b8c60633723875d3cc815b40d29edd0d4f737535de3d88324cd810b15",
            "registry/b11_annual_retrofit_reference_manifest.json": "192b6aa0b0547373fadbe362b89969a7828002bc04305a07dca912b405479791",
            "registry/b11_annual_same_service_reference_manifest.json": "830363647476b66dfa141bac791c89fc3098aec85cd45d3a684fd378537c9adc",
        }
        for name, digest in expected.items():
            with self.subTest(name=name):
                self.assertEqual(digest, hashlib.sha256((ROOT/name).read_bytes()).hexdigest())

    def test_malformed_missing_metadata_reports_error(self):
        for key in ("inspection", "sources", "definitions", "selected_rows", "non_admission"):
            with self.subTest(key=key):
                self.assertTrue(self.errors(lambda m: m.pop(key)))


if __name__ == "__main__":
    unittest.main()
