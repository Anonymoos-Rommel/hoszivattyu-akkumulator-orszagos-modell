"""Six manufacturer anchors and exact configuration references, with no admission.

Oracles are the reviewed primary WZ Vol.1.0 pages 6/11/13/38/40/68/70/72/73/
152/153/158/187, PI page 2 and DG79H200H02 pages 3/6-8. Original PDFs are not
redistributed or required by these source-native semantic regression tests.
"""
import copy
import csv
import hashlib
import json
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from tools import validate_registry

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "registry/b05_r290_reference_manifest.json"
M1 = "SRC-B05-MITSUBISHI-WZ-DATABOOK-2025"
M2 = "SRC-B05-MITSUBISHI-WZ50-PI-2025"
M3 = "SRC-B05-MITSUBISHI-FTC7-MANUAL-2024"
H1 = "SRC-B05-MITSUBISHI-HU-CATALOGUE-2024"


def rows(name):
    with (ROOT / "registry" / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class R290ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(PATH.read_text())
        self.anchors = {a["anchor_id"]: a for a in self.manifest["anchors"]}
        self.conflicts = {c["conflict_id"]: c for c in self.manifest["conflicts"]}

    def _errors(self, mutation=None, csv_mutation=None, rehash=False):
        candidate = copy.deepcopy(self.manifest)
        if mutation:
            mutation(candidate)
        if rehash:
            candidate["anchors_sha256"] = hashlib.sha256(json.dumps(candidate["anchors"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        original_read, original_csv = Path.read_text, validate_registry.read_csv
        def read(path, *args, **kwargs):
            return json.dumps(candidate) if path == PATH else original_read(path, *args, **kwargs)
        def read_csv(path):
            header, records = original_csv(path)
            if csv_mutation:
                csv_mutation(path, records)
            return header, records
        errors = []
        with patch.object(Path, "read_text", read), patch.object(validate_registry, "read_csv", read_csv):
            validate_registry.validate_b05_r290_references(errors, {r["source_id"] for r in rows("sources.csv")})
        return errors

    def test_clean_reference_passes_registry_validator(self):
        self.assertEqual([], self._errors())

    def test_exact_source_bytes_and_date_precision(self):
        expected = {
            M1: ("d6cc1ca7c6bb2e2af75e15930c0031623de6c25bbf49b636bb42c56004077886", 44665136, "2025-05", "month"),
            M2: ("dabe22096af02a3954365c5cb0f36f89d447b201ebf599dbf75893c473f0d0c6", 775721, "2025-01", "month"),
            M3: ("17cab38d2b723369e6036ec2c7886164a732ed8891a9d4d6e0707948af630082", 5351021, None, "unknown"),
            H1: ("50f77a80e559b1179114cfe8efd2b644f3dab972775979e4f1e5d8cbad22f9c4", 9408582, "2024-12", "month"),
        }
        self.assertEqual(expected, {s["source_id"]: tuple(s[k] for k in ("sha256", "bytes", "document_date", "document_date_precision")) for s in self.manifest["sources"]})
        global_sources = {r["source_id"]: r for r in rows("sources.csv")}
        local_sources = {r["source_id"]: r for r in rows("heat_pump_sources.csv")}
        for source in self.manifest["sources"]:
            sid = source["source_id"]
            self.assertEqual(source["sha256"], global_sources[sid]["local_snapshot_sha256"])
            self.assertEqual(source["original_url"], global_sources[sid]["url"])
            self.assertEqual(source["original_url"], local_sources[sid]["url"])
            self.assertEqual("undated", global_sources[sid]["published_at"])
            self.assertIsNone(source["repo_snapshot_path"])
            self.assertEqual("EXTERNAL_ONLY_REPOSITORY_COPY_NOT_CLEARED", source["reuse_status"])
        self.assertIn("2026-02-03", self.manifest["sources"][1]["document_revision"])

    def test_six_exact_native_heating_anchor_values(self):
        expected = {
            "M1-A7-W35": ("7", "4.00", "5.10", "0.78", "11.5"),
            "M1-A2-W35": ("2", "5.00", "3.15", "1.59", "14.3"),
            "M1-A-7-W35-PARTLOAD1": ("-7", "5.0", "2.70", None, None),
            "M1-A-7-W35-MAX": ("-7", "5.2", "2.68", None, None),
            "M2-A-7-W35-NORMAL": ("-7", "5.2", "2.68", "1.94", None),
            "M1-A-25-W35-MAX": ("-25", "3.2", "1.85", None, None),
        }
        fields = ("ambient_dry_bulb_c", "capacity_kw", "cop", "electrical_input_kw", "test_flow_l_per_min")
        self.assertEqual(expected, {key: tuple(a[k] for k in fields) for key, a in self.anchors.items()})
        for a in self.anchors.values():
            self.assertEqual("OBS", a["truth"])
            self.assertEqual("35", a["water_outlet_c"])
            self.assertEqual("SOURCE_REFERENCE_ONLY", a["use_scope"])

    def test_unreported_inputs_are_not_division_filled(self):
        for key in ("M1-A-7-W35-PARTLOAD1", "M1-A-7-W35-MAX", "M1-A-25-W35-MAX"):
            self.assertIsNone(self.anchors[key]["electrical_input_kw"])
        a = self.anchors["M1-A7-W35"]
        self.assertNotEqual(Decimal(a["capacity_kw"]) / Decimal(a["cop"]), Decimal(a["electrical_input_kw"]))

    def test_source_specific_modes_and_pi_conditions(self):
        pi = self.anchors["M2-A-7-W35-NORMAL"]
        self.assertEqual((M2, "normal heating conditions", "-7", "-8", "35", "30"), tuple(pi[k] for k in ("source_id", "mode_label", "ambient_dry_bulb_c", "ambient_wet_bulb_c", "water_outlet_c", "water_inlet_c")))
        self.assertEqual("Partload1", self.anchors["M1-A-7-W35-PARTLOAD1"]["mode_label"])
        self.assertEqual("Max", self.anchors["M1-A-7-W35-MAX"]["mode_label"])
        for a in self.manifest["anchors"]:
            if a["source_id"] == M1:
                self.assertIsNone(a["water_inlet_c"])
                self.assertIsNone(a["ambient_wet_bulb_c"])

    def test_2018_applies_only_to_capacity_table_and_pump_inclusion(self):
        cap = self.manifest["methods"]["M1_CAPACITY_2018"]
        self.assertEqual("EN14511 parts 1-4:2018", cap["standard"])
        self.assertTrue(cap["pump_input_included"])
        self.assertIn("2022 line belongs to other models", cap["standard_year_applies_to"])
        self.assertEqual("EN14511; year not specified in grid notes", self.manifest["methods"]["M1_GRID_REFERENCE"]["standard"])
        self.assertEqual("Not specified for note 2 heating point", self.manifest["methods"]["M2_PI_NORMAL_HEATING"]["standard"])

    def test_grid_interpolation_and_defrost_are_manufacturer_conditioned(self):
        grid = self.manifest["methods"]["M1_GRID_REFERENCE"]
        self.assertTrue(grid["values_may_include_interpolation_or_calculation"])
        self.assertFalse(grid["all_points_directly_measured"])
        self.assertTrue(grid["gray_includes_defrost"])
        self.assertFalse(grid["not_gray_means_no_defrost"])
        for key in ("M1-A-7-W35-PARTLOAD1", "M1-A-7-W35-MAX"):
            self.assertEqual("NOT_GRAY_NOT_ZERO_DEFROST", self.anchors[key]["defrost_annotation"])
        self.assertEqual("GRAY_INCLUDES_DEFROST", self.manifest["context"]["rating_crosswalk"]["A2_Partload1_defrost_annotation"])
        self.assertEqual("NOT_GRAY_NOT_ZERO_DEFROST", self.anchors["M1-A-25-W35-MAX"]["defrost_annotation"])
        self.assertFalse(self.manifest["context"]["rating_crosswalk"]["M2_mode_relabelled"])

    def test_mutation_defrost_shading_cannot_restore_prior_error_or_infer_zero_even_rehashed(self):
        # M1 PDF p40/A-36 has white A-7 W35 cells; p38/A-34 states only
        # that grey includes defrost. Keep the grey A2 control separate.
        for anchor_id in ("M1-A-7-W35-PARTLOAD1", "M1-A-7-W35-MAX"):
            for annotation in ("GRAY_INCLUDES_DEFROST", "NOT_GRAY_ZERO_DEFROST"):
                with self.subTest(anchor=anchor_id, annotation=annotation):
                    def mutate(m):
                        next(a for a in m["anchors"] if a["anchor_id"] == anchor_id)["defrost_annotation"] = annotation
                    self.assertTrue(self._errors(mutate, rehash=True))
        self.assertTrue(self._errors(lambda m: m["context"]["rating_crosswalk"].__setitem__("A2_Partload1_defrost_annotation", "NOT_GRAY_NOT_ZERO_DEFROST"), rehash=True))
        self.assertTrue(self._errors(lambda m: m["methods"]["M1_GRID_REFERENCE"].__setitem__("not_gray_means_no_defrost", True), rehash=True))

    def test_outdoor_water_connected_and_commercial_variants_separate(self):
        i = self.manifest["identity"]
        self.assertEqual(("PUZ-WZ50VAA", "PUZ-WZ50VAA-BS", "R290", "WATER_CONNECTED_MONOBLOCK", "BUILT_IN_OUTDOOR"), tuple(i[k] for k in ("base_model", "covered_commercial_variant", "refrigerant", "connection", "refrigerant_water_exchanger")))
        self.assertFalse(i["base_variant_commercial_equivalence_inferred"])
        self.assertEqual({"value": "0.6", "unit": "kg", "truth": "OBS"}, i["charge"])

    def test_integrated_erp_x_is_reversible_heating_only_scenario(self):
        c = self.manifest["configurations"]["ERPX"]
        self.assertEqual("ERPX-VM2E", c["indoor"])
        self.assertTrue(c["hardware_reversible"])
        self.assertEqual("SPACE_HEATING_ONLY_REFERENCE", c["service_scenario"])
        self.assertEqual("SCN", c["service_scenario_truth"])
        self.assertFalse(c["dhw_cylinder_included"])
        self.assertFalse(c["standalone_controller_added_to_integrated_route"])
        self.assertIsNone(c["mandatory_external_controller"])
        self.assertEqual("INTEGRATED_CONTROL_AND_MAIN_REMOTE", c["controller_arrangement"])
        self.assertEqual({"booster": "2", "expansion_vessel": "10", "internal_heating_water": "4.5"}, {k: v["value"] for k, v in c["facts"].items()})
        self.assertIn("control/main remote", c["components"])

    def test_erpt_dhw_alternative_is_not_ehpt_or_extra_tank(self):
        c = self.manifest["configurations"]["ERPT20X"]
        self.assertEqual("ERPT20X-VM2E", c["indoor"])
        self.assertEqual("SEPARATE_DHW_ALTERNATIVE", c["service_scenario"])
        self.assertTrue(c["hardware_reversible"])
        self.assertTrue(c["dhw_cylinder_included"])
        self.assertEqual({"dhw_cylinder": "200", "booster": "2", "expansion_vessel": "12"}, {k: v["value"] for k, v in c["facts"].items()})
        self.assertIn("EHPT20X-MEHEW", c["boundary"])
        self.assertIn("Replaces the ERPX", c["boundary"])

    def test_standalone_controller_requires_exact_sensor_local_hydraulics(self):
        c = self.manifest["configurations"]["PAC_IF081"]
        self.assertEqual("PAC-IF081B-E", c["controller_arrangement"])
        self.assertEqual("PAC-FS01-E", c["mandatory_flow_sensor"])
        self.assertFalse(c["complete_hydraulic_module"])
        self.assertFalse(c["dhw_cylinder_included"])
        self.assertIsNone(c["indoor"])
        self.assertEqual(["main remote", "supplied thermistors"], c["components"])
        self.assertIn("water circulation pump", c["locally_supplied"])
        self.assertEqual({M1, M3}, {r["source_id"] for r in c["references"]})

    def test_erp_not_legal_capacity_and_family_naming_not_exact_compatibility(self):
        erp = self.manifest["context"]["erp_rating"]
        self.assertEqual("ErP medium-temperature average climate", erp["condition"])
        self.assertEqual("ERPX-VM2E", erp["indoor"])
        self.assertEqual({"value": "5.0", "unit": "kW", "truth": "OBS"}, erp["rated_heat_output"])
        self.assertFalse(erp["legal_maximum_rated_capacity_determination"])
        naming = self.manifest["context"]["family_naming"]
        self.assertEqual((H1, "FTC7", M1, False), tuple(naming[k] for k in ("source_id", "control_generation", "exact_compatibility_authority", "independent_performance_corroboration")))

    def test_separate_operating_modes_and_conditional_water_volumes(self):
        limits = self.manifest["context"]["operating_limits"]
        self.assertEqual(["-25", "24", "-25", "46", "10", "46", "65", "75"], [v["value"] for v in limits.values() if isinstance(v, dict)])
        h = self.manifest["context"]["conditional_hydraulics"]
        self.assertEqual(["5", "2", "24"], [h[k]["value"] for k in ("table_indoor_reference", "additional_average_or_warmer", "additional_colder")])
        self.assertFalse(h["universal_buffer_size_admitted"])
        self.assertFalse(h["site_climate_or_circuit_volume_known"])

    def test_correct_m2_water_rows_do_not_invent_min_max_flow(self):
        water = self.manifest["context"]["water_data"]
        self.assertNotIn("FLOW_LABELS", self.conflicts)
        self.assertEqual({"GWP_CO2EQ", "COOLING_INPUT_A35_W18", "DHW_EFFICIENCY_EHPT20X", "INDOOR_WATER_REFERENCE"}, set(self.conflicts))
        self.assertEqual([
            (M1, "Water Flow rate range", "6.5", "L/min", "RANGE_MINIMUM"),
            (M1, "Water Flow rate range", "14.3", "L/min", "RANGE_MAXIMUM"),
            (M3, "Water flow rate range [L/min]", "6.5", "L/min", "RANGE_MINIMUM"),
            (M3, "Water flow rate range [L/min]", "14.3", "L/min", "RANGE_MAXIMUM"),
            (M2, "Pipework Size (mm)", "22", "mm", "PIPEWORK_SIZE"),
            (M2, "Flow Rate (l/min)", "14", "L/min", "SINGLE_FLOW_RATE"),
            (M2, "Water Pressure Drop (kPa)", "18.16", "kPa", "WATER_PRESSURE_DROP"),
        ], [tuple(r[k] for k in ("source_id", "source_label", "value", "unit", "quantity_role")) for r in water["readings"]])
        self.assertTrue(all(r["truth"] == "OBS" and r["test_condition"] is None for r in water["readings"]))
        self.assertIsNone(water["m2_flow_min_or_max_label"])
        self.assertIsNone(water["harmonised_hydraulic_default"])
        self.assertFalse(water["rounding_reconciliation_admitted"])
        self.assertIn("withdrawn", water["source_reading_correction"])

    def test_inconsistent_gwp_co2eq_preserved_without_default(self):
        c = self.conflicts["GWP_CO2EQ"]
        self.assertEqual(["3", "0.02", "0.6", "0.0018"], [r["value"] for r in c["readings"]])
        charge, reported = Decimal("0.6"), Decimal("0.0018")
        self.assertEqual(charge * Decimal("3") / 1000, reported)
        self.assertNotEqual(charge * Decimal("0.02") / 1000, reported)
        self.assertIsNone(c["harmonised_default"])

    def test_unused_cooling_dhw_and_water_discrepancies_retained(self):
        for key, expected in (("COOLING_INPUT_A35_W18", ["0.35", "1.31"]), ("DHW_EFFICIENCY_EHPT20X", ["134", "143"]), ("INDOOR_WATER_REFERENCE", ["4.5", "5"])):
            c = self.conflicts[key]
            self.assertEqual(expected, [r["value"] for r in c["readings"]])
            self.assertFalse(c["source_repaired"])
            self.assertIsNone(c["harmonised_default"])
        self.assertTrue(all("EHPT20X-MEHEW" in r["model_scope"] for r in self.conflicts["DHW_EFFICIENCY_EHPT20X"]["readings"]))

    def test_no_runtime_module_loads_reference_or_sources(self):
        needles = [PATH.name, M1, M2, M3, H1]
        for path in (ROOT / "modules").rglob("*.py"):
            text = path.read_text()
            self.assertFalse(any(needle in text for needle in needles), str(path.relative_to(ROOT)))
        self.assertEqual("Q", self.manifest["target_authority"]["applicability_status"])
        self.assertTrue(all(value is False for key, value in self.manifest["target_authority"].items() if key != "applicability_status"))

    def test_mutation_every_anchor_numeric_semantic_field_even_rehashed(self):
        for i, row in enumerate(self.manifest["anchors"]):
            for key in ("capacity_kw", "cop", "electrical_input_kw", "test_flow_l_per_min", "ambient_dry_bulb_c", "ambient_wet_bulb_c", "water_inlet_c", "water_outlet_c", "mode_label", "source_id", "method_id", "truth", "use_scope", "model_scope", "defrost_annotation", "locator"):
                with self.subTest(anchor=row["anchor_id"], field=key):
                    self.assertTrue(self._errors(lambda m: m["anchors"][i].__setitem__(key, "1.0"), rehash=True))

    def test_mutation_anchor_addition_duplication_removal_and_integrity(self):
        for mutation in (lambda m: m["anchors"].pop(), lambda m: m["anchors"].append(copy.deepcopy(m["anchors"][0])), lambda m: m.__setitem__("anchors_sha256", "0" * 64)):
            self.assertTrue(self._errors(mutation))
        self.assertTrue(self._errors(lambda m: m["anchors"][1].__setitem__("anchor_id", m["anchors"][0]["anchor_id"]), rehash=True))

    def test_mutation_every_authority_flag_and_type_fails_closed(self):
        for key, value in self.manifest["target_authority"].items():
            with self.subTest(key=key):
                replacement = "OBS" if key == "applicability_status" else True
                self.assertTrue(self._errors(lambda m: m["target_authority"].__setitem__(key, replacement)))
        self.assertTrue(self._errors(lambda m: m["target_authority"].__setitem__("usable_for_engine", 0)))
        self.assertTrue(self._errors(lambda m: m.__setitem__("runtime_default", "PUZ-WZ50VAA")))

    def test_mutation_unit_truth_and_manufacturer_method_promotions(self):
        mutations = [
            lambda m: m["anchor_units"].__setitem__("capacity_kw", "W"),
            lambda m: m["identity"]["charge"].__setitem__("truth", "DER"),
            lambda m: m["identity"]["charge"].__setitem__("value", "NaN"),
            lambda m: m["methods"]["M1_CAPACITY_2018"].__setitem__("standard", "EN14511 parts 1-4:2022"),
            lambda m: m["methods"]["M1_CAPACITY_2018"].__setitem__("pump_input_included", False),
            lambda m: m["methods"]["M1_GRID_REFERENCE"].__setitem__("values_may_include_interpolation_or_calculation", False),
            lambda m: m["methods"]["M1_GRID_REFERENCE"].__setitem__("all_points_directly_measured", True),
            lambda m: m["methods"]["M1_GRID_REFERENCE"].__setitem__("not_gray_means_no_defrost", True),
            lambda m: m["methods"]["M2_PI_NORMAL_HEATING"].__setitem__("max_label_stated", True),
            lambda m: m["context"]["rating_crosswalk"].__setitem__("M2_mode_relabelled", True),
        ]
        for i, mutation in enumerate(mutations):
            with self.subTest(mutation=i):
                self.assertTrue(self._errors(mutation))

    def test_mutation_configuration_merging_dhw_transfer_or_controller_double_count(self):
        mutations = [
            lambda m: m["configurations"]["ERPX"].__setitem__("hardware_reversible", False),
            lambda m: m["configurations"]["ERPX"].__setitem__("service_scenario_truth", "OBS"),
            lambda m: m["configurations"]["ERPX"].__setitem__("dhw_cylinder_included", True),
            lambda m: m["configurations"]["ERPX"].__setitem__("standalone_controller_added_to_integrated_route", True),
            lambda m: m["configurations"]["ERPX"].__setitem__("mandatory_external_controller", "PAC-IF081B-E"),
            lambda m: m["configurations"]["ERPX"]["facts"]["expansion_vessel"].__setitem__("value", "12"),
            lambda m: m["configurations"]["ERPT20X"].__setitem__("indoor", "EHPT20X-MEHEW"),
            lambda m: m["configurations"]["ERPT20X"].__setitem__("service_scenario", "ADDITIONAL_DHW_TANK"),
            lambda m: m["configurations"]["PAC_IF081"].__setitem__("mandatory_flow_sensor", None),
            lambda m: m["configurations"]["PAC_IF081"].__setitem__("complete_hydraulic_module", True),
            lambda m: m["configurations"]["PAC_IF081"].__setitem__("locally_supplied", []),
            lambda m: m["configurations"]["ERPX"].__setitem__("model_default_admitted", True),
            lambda m: m["identity"].__setitem__("base_variant_commercial_equivalence_inferred", True),
        ]
        for i, mutation in enumerate(mutations):
            with self.subTest(mutation=i):
                self.assertTrue(self._errors(mutation))

    def test_mutation_conflicts_cannot_be_dropped_swapped_or_harmonised(self):
        for i, conflict in enumerate(self.manifest["conflicts"]):
            for key, value in (("harmonised_default", "1"), ("source_repaired", True), ("status", "RESOLVED")):
                with self.subTest(conflict=conflict["conflict_id"], key=key):
                    self.assertTrue(self._errors(lambda m: m["conflicts"][i].__setitem__(key, value)))
            self.assertTrue(self._errors(lambda m: m["conflicts"][i]["readings"][0].__setitem__("value", "1.0")))
        self.assertTrue(self._errors(lambda m: m["conflicts"].pop()))
        self.assertTrue(self._errors(lambda m: m["context"]["water_data"]["readings"][5].__setitem__("source_label", "Flow Rate (Max)")))
        self.assertTrue(self._errors(lambda m: next(c for c in m["conflicts"] if c["conflict_id"] == "DHW_EFFICIENCY_EHPT20X")["readings"][0].__setitem__("model_scope", "ERPT20X-VM2E")))

    def test_mutation_context_does_not_promote_site_legal_or_family_authority(self):
        for section, key, value in (
            ("erp_rating", "legal_maximum_rated_capacity_determination", True),
            ("erp_rating", "condition", "maximum legal capacity"),
            ("family_naming", "exact_compatibility_authority", H1),
            ("family_naming", "independent_performance_corroboration", True),
            ("conditional_hydraulics", "universal_buffer_size_admitted", True),
            ("conditional_hydraulics", "site_climate_or_circuit_volume_known", True),
            ("installation", "site_safe_design_certified", True),
        ):
            with self.subTest(section=section, key=key):
                self.assertTrue(self._errors(lambda m: m["context"][section].__setitem__(key, value)))
        self.assertTrue(self._errors(lambda m: m["context"]["operating_limits"]["heating_ambient_max"].__setitem__("value", "46")))
        self.assertTrue(self._errors(lambda m: m["validation_debt"][0].__setitem__("status", "CLOSED")))

    def test_mutation_configuration_source_and_page_trace_rejected(self):
        for cid in ("ERPX", "ERPT20X", "PAC_IF081"):
            for key, value in (("source_id", H1), ("locator", "PDF p1; wrong reference")):
                with self.subTest(configuration=cid, field=key):
                    self.assertTrue(self._errors(lambda m: m["configurations"][cid]["references"][0].__setitem__(key, value)))

    def test_mutation_hidden_nested_default_or_source_transfer_rejected(self):
        for context in self.manifest["context"]:
            with self.subTest(context=context):
                self.assertTrue(self._errors(lambda m: m["context"][context].__setitem__("runtime_default", "admitted")))
        self.assertTrue(self._errors(lambda m: m["context"]["operating_limits"]["references"][0].__setitem__("source_id", M2)))
        self.assertTrue(self._errors(lambda m: m["methods"]["M1_GRID_REFERENCE"].__setitem__("runtime_interpolation_allowed", True)))

    def test_source_document_roles_and_revision_are_bound_to_original(self):
        expected = {
            M1: ("Issued May 2025; M-E0977 SIZ2025<MEE>; PDF metadata creation 2025-05-16, modification 2025-06-13", "ISSUE_MONTH"),
            M2: ("Effective January 2025; original PDF metadata created/modified 2026-02-03", "EFFECTIVE_MONTH"),
            M3: ("DG79H200H02; PDF metadata April 2024", "ISSUE_DATE_UNKNOWN"),
            H1: ("HU-00386 // 12/2024; PDF metadata Jan/Apr 2025; HTTP Last-Modified 2025-08-11", "ISSUE_MONTH"),
        }
        for source in self.manifest["sources"]:
            self.assertEqual(expected[source["source_id"]], (source["document_revision"], source["document_date_role"]))
            self.assertEqual(source["document_revision"], source["reference_period"])

    def test_exact_method_and_context_primary_page_roles(self):
        self.assertEqual({
            "M1_CAPACITY_2018": (M1, "PDF p11 / A-7, WZ50/60/80 capacity table"),
            "M1_GRID_REFERENCE": (M1, "PDF p38 / A-34, performance notes and modes"),
            "M2_PI_NORMAL_HEATING": (M2, "PDF p2, HEATING row and note 2"),
        }, {key: (v["source_id"], v["locator"]) for key, v in self.manifest["methods"].items()})
        context = self.manifest["context"]
        self.assertEqual("PDF p13 / A-9; PUZ-WZ50VAA(-BS) + ERPX-VM2E row", context["erp_rating"]["locator"])
        self.assertEqual([(M1, "PDF p158 / B-92; Table 5.6.2"), (M1, "PDF p27 / A-23"), (M1, "PDF p160 / B-94")], [(r["source_id"], r["locator"]) for r in context["conditional_hydraulics"]["references"]])
        self.assertEqual("PDF pp8,30; model/controller naming and R290 family", context["family_naming"]["locator"])

    def test_generic_volume_and_actual_product_volume_keep_separate_sources(self):
        product, generic = self.conflicts["INDOOR_WATER_REFERENCE"]["readings"]
        self.assertEqual((M1, "PDF p72 / B-6", "ERPX-VM2E", "4.5", "L"), tuple(product[k] for k in ("source_id", "locator", "model_scope", "value", "unit")))
        self.assertEqual((M1, "PDF p158 / B-92; Table 5.6.2", "generic indoor reference used with PUZ-WZ50 row", "5", "L"), tuple(generic[k] for k in ("source_id", "locator", "model_scope", "value", "unit")))
        h = self.manifest["context"]["conditional_hydraulics"]
        self.assertEqual("GENERIC_INDOOR_REFERENCE_WITH_WZ50_ADDITIONAL_WATER_TABLE", h["volume_scope"])
        self.assertEqual("PUZ-WZ50 row; generic indoor reference, not ERPX-VM2E actual internal volume", h["model_scope"])
        self.assertEqual(["integrated cylinder unit"], self.manifest["configurations"]["ERPT20X"]["components"])

    def test_r2_all_seven_reported_bypasses_rejected_even_rehashed(self):
        cases = [
            ("wrong_M1_revision", lambda m: m["sources"][0].__setitem__("document_revision", "Issued January 2028; Vol.9.9")),
            ("wrong_M1_method_primary_page", lambda m: m["methods"]["M1_CAPACITY_2018"].__setitem__("locator", "PDF p187 / C-3; unrelated optional parts")),
            ("remove_hydraulic_primary_references", lambda m: m["context"]["conditional_hydraulics"].__setitem__("references", [])),
            ("wrong_ErP_primary_page", lambda m: m["context"]["erp_rating"].__setitem__("locator", "PDF p187 / C-3; unrelated optional parts")),
            ("generic_water_reassigned_as_actual_ERPX", lambda m: next(c for c in m["conflicts"] if c["conflict_id"] == "INDOOR_WATER_REFERENCE")["readings"][1].__setitem__("model_scope", "ERPX-VM2E product-specific internal water")),
            ("ERPT_components_add_duplicate_PAC_controller", lambda m: m["configurations"]["ERPT20X"]["components"].append("PAC-IF081B-E")),
            ("flow_primary_page_replaced", lambda m: m["context"]["water_data"]["readings"][0].__setitem__("locator", "PDF p230; back cover")),
        ]
        for name, mutation in cases:
            with self.subTest(case=name):
                self.assertTrue(self._errors(mutation, rehash=True))

    def test_mutation_revision_issue_effective_metadata_and_period_roles(self):
        for i in range(4):
            for field, value in (("document_revision", "Issued January 2028; Vol.9.9"), ("document_date_role", "PDF_CREATION_IS_ISSUE"), ("document_date_basis", "PDF metadata establishes current issue"), ("reference_period", "2028 current product")):
                with self.subTest(source=i, field=field):
                    self.assertTrue(self._errors(lambda m: m["sources"][i].__setitem__(field, value), rehash=True))
        def joint_relabel(m):
            m["sources"][1].update(document_date="2026-02-03", document_date_precision="day", document_date_role="ISSUE_DATE", document_revision="Issued February 2026", reference_period="Issued February 2026")
        self.assertTrue(self._errors(joint_relabel, rehash=True))

    def test_mutation_source_description_cannot_jointly_relabel_original(self):
        for i in range(4):
            self.assertTrue(self._errors(lambda m: m["sources"][i].__setitem__("geography_and_authority", "independent Hungarian certification")))
        def csv_mutation(path, records):
            if path.name in {"sources.csv", "heat_pump_sources.csv"}:
                next(r for r in records if r["source_id"] == M1)["title"] = "Different product revision"
        self.assertTrue(self._errors(lambda m: m["sources"][0].__setitem__("title", "Different product revision"), csv_mutation=csv_mutation))

    def test_mutation_method_within_source_page_and_cross_source_transfer(self):
        for key in self.manifest["methods"]:
            for field, value in (("source_id", H1), ("locator", "PDF p187 / C-3; unrelated optional parts")):
                with self.subTest(method=key, field=field):
                    self.assertTrue(self._errors(lambda m: m["methods"][key].__setitem__(field, value), rehash=True))
        self.assertTrue(self._errors(lambda m: m["methods"]["M1_CAPACITY_2018"].__setitem__("standard_year_applies_to", "2022 for WZ50")))

    def test_mutation_context_reference_omission_duplication_wrong_page_or_source(self):
        for key in ("operating_limits", "rating_crosswalk", "conditional_hydraulics", "installation"):
            for mode in ("empty", "remove", "duplicate", "wrong_page", "wrong_source", "extra_role"):
                def mutate(m):
                    refs = m["context"][key]["references"]
                    if mode == "empty": refs.clear()
                    elif mode == "remove": refs.pop()
                    elif mode == "duplicate": refs.append(copy.deepcopy(refs[0]))
                    elif mode == "wrong_page": refs[0]["locator"] = "PDF p230; back cover"
                    elif mode == "wrong_source": refs[0]["source_id"] = M2
                    else: refs[0]["model_scope"] = "unrelated product"
                with self.subTest(context=key, mode=mode):
                    self.assertTrue(self._errors(mutate, rehash=True))

    def test_mutation_exact_context_model_scope_erp_and_naming_roles(self):
        for key, field, value in (
            ("erp_rating", "source_id", M2), ("erp_rating", "locator", "PDF p187 / C-3"),
            ("erp_rating", "indoor", "ERPT20X-VM2E"), ("erp_rating", "condition", "ErP low-temperature colder climate"),
            ("family_naming", "locator", "PDF p97; unrelated date page"), ("family_naming", "scope", "exact system performance verification"),
            ("operating_limits", "model_scope", "PUZ-WM50VHA"),
            ("conditional_hydraulics", "volume_scope", "ERPX_ACTUAL_INTERNAL_VOLUME"),
            ("conditional_hydraulics", "model_scope", "ERPX-VM2E actual volume"),
            ("installation", "model_scope", "any heat pump"),
        ):
            with self.subTest(context=key, field=field):
                self.assertTrue(self._errors(lambda m: m["context"][key].__setitem__(field, value), rehash=True))

    def test_mutation_each_conflict_reading_source_page_model_and_condition(self):
        for i, conflict in enumerate(self.manifest["conflicts"]):
            for j, reading in enumerate(conflict["readings"]):
                for field, value in (("source_id", H1), ("locator", "PDF p230; back cover"), ("model_scope", "ERPX-VM2E product-specific internal water"), ("source_label", "different condition")):
                    with self.subTest(conflict=conflict["conflict_id"], reading=j, field=field):
                        self.assertTrue(self._errors(lambda m: m["conflicts"][i]["readings"][j].__setitem__(field, value), rehash=True))

    def test_mutation_all_water_rows_exact_source_page_model_units_and_roles(self):
        for i, reading in enumerate(self.manifest["context"]["water_data"]["readings"]):
            for field, value in (("source_id", H1), ("locator", "PDF p230; back cover"), ("model_scope", "ERPX-VM2E"), ("source_label", "Flow Rate (Max)"), ("value", "14.3" if reading["value"] != "14.3" else "14"), ("unit", "W"), ("quantity_role", "ASSUMED_TEST_FLOW"), ("test_condition", "A7/W35")):
                with self.subTest(reading=i, field=field):
                    self.assertTrue(self._errors(lambda m: m["context"]["water_data"]["readings"][i].__setitem__(field, value), rehash=True))
        for key, value in (("m2_flow_min_or_max_label", "maximum"), ("rounding_reconciliation_admitted", True), ("harmonised_hydraulic_default", "14.3")):
            self.assertTrue(self._errors(lambda m: m["context"]["water_data"].__setitem__(key, value)))
        self.assertTrue(self._errors(lambda m: m["context"]["water_data"]["readings"].pop()))
        self.assertTrue(self._errors(lambda m: m["context"]["water_data"]["readings"].append(copy.deepcopy(m["context"]["water_data"]["readings"][0]))))

    def test_mutation_configuration_components_and_reference_cardinality(self):
        for key in self.manifest["configurations"]:
            for mode in ("add_controller", "remove_component", "add_cylinder", "remove_refs", "duplicate_ref"):
                def mutate(m):
                    c = m["configurations"][key]
                    if mode == "add_controller": c["components"].append("PAC-IF081B-E")
                    elif mode == "remove_component": c["components"].pop()
                    elif mode == "add_cylinder": c["components"].append("ERPT20X-VM2E")
                    elif mode == "remove_refs": c["references"].clear()
                    else: c["references"].append(copy.deepcopy(c["references"][0]))
                with self.subTest(configuration=key, mode=mode):
                    self.assertTrue(self._errors(mutate, rehash=True))

    def test_mutation_source_identity_date_copy_and_csv_join_rejected(self):
        for key, value in (("sha256", "0" * 64), ("bytes", 1), ("original_url", "https://example.org/wrong"), ("document_date", "2026-02-03"), ("document_date_precision", "day"), ("retrieved_at", "2025-01-01"), ("repo_snapshot_path", "evidence/original.pdf"), ("reuse_status", "CLEARED")):
            with self.subTest(key=key):
                self.assertTrue(self._errors(lambda m: m["sources"][1].__setitem__(key, value)))
        self.assertTrue(self._errors(lambda m: m["sources"].append(copy.deepcopy(m["sources"][0]))))
        for fname, key in (("sources.csv", "local_snapshot_sha256"), ("sources.csv", "published_at"), ("heat_pump_sources.csv", "url"), ("heat_pump_sources.csv", "reference_period"), ("heat_pump_sources.csv", "evidence_status")):
            def mutate(path, records):
                if path.name == fname:
                    next(r for r in records if r["source_id"] == M1)[key] = "changed"
            with self.subTest(file=fname, key=key):
                self.assertTrue(self._errors(csv_mutation=mutate))


if __name__ == "__main__":
    unittest.main()
