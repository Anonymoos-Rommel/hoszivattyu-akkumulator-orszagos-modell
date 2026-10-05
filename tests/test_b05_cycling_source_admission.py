"""Source admission is distinct from preserved P18 conditional arithmetic."""
import csv
from datetime import date
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import unittest

from modules.B05.manufacturer_wm50_reference import load_wm50_reference
from modules.B05.qualified_cycling_point import (
    CONDITIONAL_POINT, SOURCE_JOIN_REQUIRED, CyclingSourceContext,
    QualifiedCyclingPoint, evaluate_conditional_cycling_point,
    evaluate_exact_cycling_point,
)
from modules.B05.cycling_input_colocation import MEASUREMENT_DETERMINED

ROOT = Path(__file__).resolve().parents[1]


def point(**changes):
    context = CyclingSourceContext(
        observation_id="WM50-20261002-average-low_temperature-A7",
        source_id="SRC-B05-HPKEYMARK-MITSUBISHI-WM50-2026",
        document_revision="037-0032-20 / rev.2; certification date 2023-12-19",
        component="Outdoor", climate="average", application="low_temperature",
    )
    p = QualifiedCyclingPoint(
        "PUZ-WM50VHA", "PUZ-WM50VHA(-BS)", 7, 35, 1.8, .33, 5.46,
        .95, MEASUREMENT_DETERMINED, True, True,
        minimum_source_id="SRC-B05-MITSUBISHI-PUZ-WM-MINNOMMAX-2024",
        source_context=context,
        minimum_document_revision="2024 technical sheet rev.1",
    )
    return replace(p, **changes)


class CyclingSourceAdmissionTests(unittest.TestCase):
    def rejected(self, p):
        result = evaluate_exact_cycling_point(p, required_capacity_kw=.9)
        self.assertEqual(result.status, SOURCE_JOIN_REQUIRED)
        self.assertIsNone(result.cop_bin)
        self.assertIsNone(result.electrical_input_kw)
        return result.residual_gaps

    def test_conditional_arithmetic_preserves_both_coefficients_without_admission(self):
        for cdh, cop, input_kw in ((.95, 5.2, .17307692307692307),
                                   (.98, 5.352941176470588, .16813186813186815)):
            with self.subTest(cdh=cdh):
                result = evaluate_conditional_cycling_point(point(cdh=cdh), required_capacity_kw=.9)
                self.assertEqual(result.status, CONDITIONAL_POINT)
                self.assertEqual(result.capacity_ratio, .5)
                self.assertAlmostEqual(result.cop_bin, cop, places=12)
                self.assertAlmostEqual(result.electrical_input_kw, input_kw, places=12)
                self.rejected(point(cdh=cdh))

    def test_p20_current_observation_does_not_prove_test_water_or_join(self):
        gaps = self.rejected(point())
        for gap in ("TEST_WATER_CONTROL_AUTHORITY_REQUIRED", "TEST_WATER_TEMPERATURE_C_AUTHORITY_REQUIRED",
                    "SOURCE_BOUND_TEST_CONDITION_AUTHORITY_REQUIRED", "SOURCE_BOUND_MINIMUM_POINT_JOIN_REQUIRED"):
            self.assertIn(gap, gaps)

    def test_missing_and_mismatched_scope_never_admits(self):
        context = point().source_context
        alternatives = dict(source_id="OTHER-SOURCE", document_revision="037-0032-20 / rev.1",
                            component="Outdoor+Indoor", climate="warmer", application="medium_temperature",
                            test_water_control="fixed", test_water_temperature_c=35)
        for field, wrong in alternatives.items():
            for value in (None, wrong):
                with self.subTest(field=field, value=value):
                    gaps = self.rejected(point(source_context=replace(context, **{field: value})))
                    prefix = field.upper()
                    self.assertTrue(any(g.startswith(prefix) for g in gaps))
        self.rejected(point(source_context=None))
        self.rejected(point(source_context=replace(context, observation_id="invented")))

    def test_temperature_model_and_current_value_mismatch_are_explicit(self):
        for changes, gap in ((dict(outdoor_temperature_c=2), "OUTDOOR_TEMPERATURE_MISMATCH"),
                             (dict(supply_temperature_c=55), "EXACT_WATER_COORDINATE_AUTHORITY_REQUIRED"),
                             (dict(certified_model_identifier="PUZ-WM50VHA+INDOOR"), "CERTIFIED_MODEL_MISMATCH"),
                             (dict(cdh=.98), "CDH_VALUE_MISMATCH")):
            with self.subTest(changes=changes):
                self.assertIn(gap, self.rejected(point(**changes)))

    def test_switching_to_correct_warmer_value_still_cannot_admit(self):
        context = replace(point().source_context,
                          observation_id="WM50-20261002-warmer-low_temperature-A7",
                          climate="warmer", test_water_control="fixed", test_water_temperature_c=35)
        gaps = self.rejected(point(cdh=.98, source_context=context))
        self.assertNotIn("CDH_VALUE_MISMATCH", gaps)
        self.assertIn("SOURCE_BOUND_MINIMUM_POINT_JOIN_REQUIRED", gaps)

    def test_all_four_p22_rows_keep_independent_facts_and_fail_source_join(self):
        with (ROOT / "data/processed/b05_p22_mitsubishi_w35_cycling_bins.csv").open() as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            context = replace(point().source_context, observation_id=row["current_source_observation_id"])
            p = point(outdoor_temperature_c=float(row["outdoor_temperature_C"]),
                      minimum_capacity_kw=float(row["min_modulation_kW"]),
                      declared_minimum_cop=float(row["min_point_COP"]),
                      minimum_input_kw=float(row["min_modulation_kW"])/float(row["min_point_COP"]),
                      cdh=float(row["Cdh_Tj"]), minimum_source_id=row["min_source_id"], source_context=context)
            self.rejected(p)
            result = evaluate_conditional_cycling_point(p, required_capacity_kw=.9)
            self.assertEqual(result.status, CONDITIONAL_POINT)
            self.assertGreater(result.electrical_input_kw, 0)

    def dimplex_point(self, row):
        return QualifiedCyclingPoint(
            manufacturer_model_identifier="LA 2030CP", certified_model_identifier="LA 2030CP",
            outdoor_temperature_c=float(row["outdoor_temperature_C"]), supply_temperature_c=35,
            minimum_capacity_kw=float(row["min_capacity_kW"]), minimum_input_kw=float(row["min_input_kW"]),
            declared_minimum_cop=float(row["min_COP"]),
            cdh={-7: .99, 2: .97, 7: .953, 12: .912}[int(row["outdoor_temperature_C"])],
            cdh_status=MEASUREMENT_DETERMINED, identity_correlated=True, point_pairing_explicit=True,
            minimum_source_id="SRC-B05-DIMPLEX-LA2030CP-DETAILED-MIN-SURFACE-2026",
            minimum_document_revision="System C Version 03/2026",
            source_context=CyclingSourceContext(
                observation_id="LA2030CP-20261002-average-low_temperature-A" + row["outdoor_temperature_C"],
                source_id="SRC-B05-HPKEYMARK-DIMPLEX-LA2030CP-2026",
                document_revision="registration 40060852; certification date 2025-08-29; revision unstated",
                component="Outdoor", climate="average", application="low_temperature"),
        )

    def test_current_p42_facts_and_each_dimplex_physical_join_are_distinct(self):
        with (ROOT / "data/processed/b05_p42_coordinate_gap_closure.csv").open() as f:
            rows = [r for r in csv.DictReader(f) if r["row_id"] in
                    ("B05-P42-D04", "B05-P42-D05", "B05-P42-D06", "B05-P42-D07")]
        self.assertEqual(len(rows), 4)
        for row in rows:
            p = self.dimplex_point(row)
            with self.subTest(row=row["row_id"]):
                self.assertIn("SOURCE_BOUND_MINIMUM_POINT_JOIN_REQUIRED", self.rejected(p))
                load = p.minimum_capacity_kw / 2
                result = evaluate_conditional_cycling_point(p, required_capacity_kw=load)
                # Independent rearranged input oracle; no source admission follows.
                expected = (p.cdh * load + (1-p.cdh) * p.minimum_capacity_kw) / p.declared_minimum_cop
                self.assertEqual(result.status, CONDITIONAL_POINT)
                self.assertAlmostEqual(result.electrical_input_kw, expected, places=12)
                self.assertAlmostEqual(result.cop_bin * result.electrical_input_kw, load, places=12)
        a7 = next(r for r in rows if r["outdoor_temperature_C"] == "7")
        self.assertEqual((a7["min_capacity_kW"], a7["min_input_kW"], a7["min_COP"]), ("7.72", "1.41", "5.49"))
        a12 = next(r for r in rows if r["outdoor_temperature_C"] == "12")
        self.assertEqual((a12["min_capacity_kW"], a12["min_input_kW"], a12["min_COP"]), ("8.87", "1.32", "6.70"))

    def test_dimplex_caller_metadata_and_cross_product_or_revision_substitution_fail(self):
        with (ROOT / "data/processed/b05_p42_coordinate_gap_closure.csv").open() as f:
            row = next(r for r in csv.DictReader(f) if r["row_id"] == "B05-P42-D06")
        p = self.dimplex_point(row)
        for field, wrong in dict(climate="warmer", application="medium_temperature", component="Indoor",
                                 document_revision="40060852-old", test_water_control="fixed",
                                 test_water_temperature_c=35).items():
            for value in (None, wrong):
                with self.subTest(field=field, value=value):
                    gaps = self.rejected(replace(p, source_context=replace(p.source_context, **{field: value})))
                    self.assertTrue(any(g.startswith(field.upper()) for g in gaps))
        self.assertIn("CERTIFIED_MODEL_MISMATCH", self.rejected(replace(p, source_context=point().source_context)))
        self.assertIn("CURRENT_MANUFACTURER_REVISION_REQUIRED", self.rejected(replace(
            p, minimum_source_id="SRC-B05-DIMPLEX-LA2030CP-MIN-SURFACE-2026")))
        self.assertIn("MANUFACTURER_DOCUMENT_REVISION_MISMATCH", self.rejected(replace(
            p, minimum_document_revision="historical P23 summary")))
        self.assertIn("MANUFACTURER_DOCUMENT_REVISION_REQUIRED", self.rejected(replace(
            p, minimum_document_revision=None)))
        # The correct source ID cannot transfer to another manufacturer's point.
        self.assertIn("MANUFACTURER_MODEL_MISMATCH", self.rejected(replace(
            point(), minimum_source_id=p.minimum_source_id, minimum_document_revision=p.minimum_document_revision)))

    def test_invalid_numeric_inputs_do_not_hide_behind_unknown_source(self):
        for changes in (dict(minimum_capacity_kw=float("nan")), dict(cdh=float("inf")),
                        dict(outdoor_temperature_c=float("nan")), dict(minimum_input_kw=0)):
            for evaluate in (evaluate_exact_cycling_point, evaluate_conditional_cycling_point):
                with self.subTest(changes=changes, evaluate=evaluate.__name__):
                    with self.assertRaises(ValueError): evaluate(point(**changes), required_capacity_kw=.9)
        for load in (0, -1, 1.8, 2, float("nan"), float("inf")):
            with self.assertRaises(ValueError): evaluate_conditional_cycling_point(point(), required_capacity_kw=load)

    def test_source_manifest_keeps_revision_limitation_and_no_invented_byte_hash(self):
        manifest = json.loads((ROOT / "registry/b05_cycling_source_admission_manifest.json").read_text())
        self.assertEqual(len(manifest["sources"]), 2)
        self.assertTrue(all(s["sha256"] is None for s in manifest["sources"]))
        self.assertTrue(all(s["repo_snapshot_path"] is None for s in manifest["sources"]))
        self.assertEqual(manifest["historical_claim"]["climate"], "warmer")
        self.assertEqual(manifest["historical_claim"]["status"], "CURRENT_CORROBORATION_MISMATCH_HISTORICAL_CAUSE_UNRESOLVED")
        self.assertTrue(all(o["admitted_minimum_point_join"] is None for o in manifest["observations"]))
        self.assertTrue(all(o["test_water_control"] is None for o in manifest["observations"]))

    def test_manifest_source_ids_dates_and_current_revisions_are_consistent(self):
        manifest = json.loads((ROOT / "registry/b05_cycling_source_admission_manifest.json").read_text())
        with (ROOT / "registry/sources.csv").open() as f:
            registered = {r["source_id"] for r in csv.DictReader(f)}
        self.assertEqual(manifest["schema_version"], 2)
        sources = {r["source_id"]: r for r in manifest["sources"]}
        self.assertEqual(len(sources), len(manifest["sources"]))
        self.assertEqual(len(manifest["observations"]), 11)
        self.assertEqual(len({r["observation_id"] for r in manifest["observations"]}), 11)
        for source in sources.values():
            self.assertIn(source["source_id"], registered)
            self.assertEqual(date.fromisoformat(source["retrieved_at"]), date(2026, 10, 2))
            self.assertTrue(source["exact_component_locator"])
        for obs in manifest["observations"]:
            source = sources[obs["source_id"]]
            self.assertEqual(obs["observation_date"], source["retrieved_at"])
            for field in ("model_identifier", "component", "document_revision"):
                self.assertEqual(obs[field], source[field])
        for reference in manifest["current_manufacturer_revisions"]:
            self.assertIn(reference["source_id"], registered)
            self.assertTrue(reference["document_revision"])
        self.assertIn(manifest["method_condition_authority"]["source_id"], registered)

    def test_independent_v53_capacity_consumer_and_grid_bytes_are_unchanged(self):
        manifest = json.loads((ROOT / "evidence/history/B05-CYCLING-ADMISSION-2026-10-02/manifest.json").read_text())
        for path, digest in manifest["unchanged_independent_contracts"].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest, path)
        minimum = load_wm50_reference("MIN", fixed_supply_c=55).evaluate(-7, 55).point
        maximum = load_wm50_reference("MAX", fixed_supply_c=55).evaluate(-7, 55).point
        self.assertEqual(minimum.thermal_capacity_kw, 2)
        self.assertEqual(maximum.thermal_capacity_kw, 4.4)
        self.assertEqual(minimum.cop, 1.76)


if __name__ == "__main__":
    unittest.main()
