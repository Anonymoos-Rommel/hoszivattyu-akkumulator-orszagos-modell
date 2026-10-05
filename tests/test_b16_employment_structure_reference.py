"""Hermetic authored fixtures; no complete official numerical panel is embedded."""
import copy
import hashlib
import json
import re
import tempfile
import unittest
from dataclasses import dataclass
from decimal import Decimal, Inexact, Rounded, localcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from modules.B16 import employment_structure_reference as ref


@dataclass(frozen=True)
class Literal:
    text: str


SECTORS = ("A01", "A02", "U")
MAPPINGS = [{"employment_nace_r2": code, "io_leaf_codes": [code], "official_a64_seq": seq,
             "official_nace_divisions": div} for seq, code, div in ((1, "A01", "01"), (2, "A02", "02"), (3, "U", "99"))]


def encode(data):
    text = json.dumps(data, default=lambda v: "__NUMBER_" + v.text + "__")
    return re.sub(r'"__NUMBER_(.*?)__"', r'\1', text).encode()


def make_spec(kind):
    pe, monetary = kind == "pe", kind == "current"
    codes = {"freq": ["A"], "unit": ["CP_MNAC"] if monetary else list(ref.UNITS)}
    if not pe:
        codes["nace_r2"] = ["TOTAL", *SECTORS]
    codes["na_item"] = ["P1", "B1G"] if monetary else [*ref.INDICATORS, *(["EMP_NC"] if pe else [])]
    codes.update(geo=["HU"], time=["2023"])
    data = {"version": "2.0", "class": "dataset", "label": "AUTHORED SYNTHETIC " + kind,
            "source": "SYNTHETIC", "updated": "SYNTHETIC-NOT-OFFICIAL", "id": list(codes),
            "size": [len(v) for v in codes.values()], "dimension": {
                dim: {"label": "Synthetic " + dim, "category": {
                    "index": {code: i for i, code in enumerate(values)},
                    "label": {code: "Synthetic " + code for code in values}}} for dim, values in codes.items()},
            "extension": {"id": "SYNTHETIC_" + kind}, "value": {}}
    contract = {key: copy.deepcopy(data[key]) for key in ("version", "class", "label", "source", "updated", "id", "size")}
    contract.update(extension_id=data["extension"]["id"], codes=codes)
    if monetary:
        for item, values in {"P1": {"TOTAL": "301.0", "A01": "101.0", "A02": "200.0"},
                             "B1G": {"TOTAL": "119.0", "A01": "49.0", "A02": "70.0"}}.items():
            for sector, value in values.items():
                put(data, "CP_MNAC", item, sector, value)
    else:
        for unit, values in {"THS_PER": {"TOTAL": ("3.29", "3.10", "0.20"),
                                        "A01": ("1.10", "0.90", "0.21"), "A02": ("2.20", "2.20", None)},
                             "THS_HW": {"TOTAL": ("330", "310", "20"),
                                        "A01": ("110", "90", "20"), "A02": ("220", "220", None)}}.items():
            for sector, triplet in values.items():
                if pe and sector != "TOTAL":
                    continue
                for item, value in zip(ref.INDICATORS, triplet):
                    if value is not None:
                        put(data, unit, item, None if pe else sector, value)
            if pe:
                put(data, unit, "EMP_NC", None, "3.28" if unit == "THS_PER" else "329")
    return data, contract


def index(data, unit, item, sector):
    coords = dict(freq="A", unit=unit, nace_r2=sector, na_item=item, geo="HU", time="2023")
    flat = 0
    for dim, size in zip(data["id"], data["size"]):
        flat = flat * size + data["dimension"][dim]["category"]["index"][coords[dim]]
    return str(flat)


def put(data, unit, item, sector, value):
    data["value"][index(data, unit, item, sector)] = Literal(value)


def parse(data, contract):
    return ref._parse_cube(encode(data), contract)


class FrozenIOFixture:
    leaf_codes = SECTORS
    values = {"P1": {"A01": 100, "A02": 200, "U": 0, "TOTAL": 300},
              "B1G": {"A01": 50, "A02": 70, "U": 0, "TOTAL": 120}}

    def read_cell(self, *, row, column, flow):
        if flow != "TOTAL":
            raise AssertionError("non-total IO flow requested")
        return SimpleNamespace(value=self.values[row][column])


class B16EmploymentStructureReferenceTests(unittest.TestCase):
    def setUp(self):
        self.data, self.contract = make_spec("employment")
        self.employment = parse(self.data, self.contract)
        self.a10 = parse(*make_spec("a10"))
        self.pe = parse(*make_spec("pe"))
        self.current = parse(*make_spec("current"))
        self.io = ref._aggregate_io(FrozenIOFixture(), MAPPINGS)
        self.report = self.diagnostics()
        self.manifest = json.loads(ref.MANIFEST_PATH.read_text())

    def diagnostics(self, **changes):
        args = dict(employment=self.employment, a10=self.a10, pe=self.pe, current=self.current,
                    io_aggregates=self.io, sectors=SECTORS)
        args.update(changes)
        return ref._diagnostics(**args)

    def load(self, paths, **changes):
        args = dict(reference_year=2023, units=ref.UNITS, claim=ref.HISTORICAL_EMPLOYMENT_ATTACHMENT)
        args.update(changes)
        return ref.load_employment_structure_reference(paths, **args)

    def test_manifest_pin_source_set_and_prior_snapshot_lineage(self):
        self.assertEqual(hashlib.sha256(ref.MANIFEST_PATH.read_bytes()).hexdigest(), ref.MANIFEST_SHA256)
        sources = self.manifest["source_artifacts"]
        self.assertEqual(len(sources), 10)
        self.assertEqual(len({r["source_id"] for r in sources}), 10)
        reuse = next(r for r in sources if r["source_id"] == "SRC-B16-EUROSTAT-REUSE-2026")
        self.assertNotEqual(reuse["sha256"], reuse["previous_snapshots"][0]["sha256"])
        self.assertEqual(reuse["original_url"], reuse["previous_snapshots"][0]["original_url"])
        self.assertTrue(all(r["reuse_status"] == "EXTERNAL_ONLY" and r["repo_snapshot_path"] is None for r in sources))

    def test_manifest_semantics_are_historical_mixed_vintage_not_effects(self):
        m = self.manifest
        self.assertEqual((m["source_tier"], m["evidence_tier"], m["truth_status"]), ("P1", "E1", "DER"))
        self.assertEqual(m["employment_source_vintage"], "NOT_COUNTRY_SPECIFICALLY_ESTABLISHED")
        self.assertEqual(m["evidence_family"], "KSH_HUNGARIAN_NATIONAL_ACCOUNTS")
        self.assertIn("not employment revision estimates", m["vintage_boundary"])
        self.assertEqual(m["io_manifest_sha256"], ref.industry.MANIFEST_SHA256)
        self.assertEqual((m["bridge"]["io_leaf_count"], m["bridge"]["a64_count"]), (89, 64))

    def test_metadata_content_dates_remain_distinct_from_retrieval_and_global_updates(self):
        sources = {r["source_id"]: r for r in self.manifest["source_artifacts"]}
        for source_id, date in (("SRC-B16-EUROSTAT-EMPLOYMENT-METADATA-2026", "2025-01-16"),
                                ("SRC-B16-EUROSTAT-HU-EMPLOYMENT-METADATA-2025", "2025-10-22"),
                                ("SRC-B16-EUROSTAT-HU-NATIONAL-ACCOUNTS-METADATA-2026", "2025-10-22")):
            self.assertEqual(sources[source_id]["document_date_or_revision"], "Content update " + date)
            self.assertTrue(sources[source_id]["retrieved_at"].startswith("2026-10-03T"))
        self.assertEqual(self.manifest["employment_source_vintage"], "NOT_COUNTRY_SPECIFICALLY_ESTABLISHED")

    def test_decimal_source_lexemes_are_exact(self):
        values = ("1.2300", "12345678901234567890.12345678901234567890", "-0", "-0.00", "1.20e2")
        for value in values:
            with self.subTest(value=value):
                changed = copy.deepcopy(self.data)
                put(changed, "THS_PER", "EMP_DC", "A01", value)
                cell = ref._read(parse(changed, self.contract), "THS_PER", "EMP_DC", "A01")
                self.assertEqual(cell.lexeme, value)
                self.assertEqual(cell.value.as_tuple(), Decimal(value).as_tuple())
                self.assertIs(type(cell.value), Decimal)

    def test_exact_arithmetic_independent_of_precision_exponents_and_traps(self):
        values = tuple(map(Decimal, ("123456789012345678901234567890.12", "-123456789012345678901234567890.11", "-0.005")))
        with localcontext() as context:
            context.prec = 1
            context.Emax = 1
            context.Emin = -1
            context.traps[Inexact] = True
            context.traps[Rounded] = True
            self.assertEqual(ref._exact_sum(values), Decimal("0.005"))
            self.assertEqual(ref._difference(Decimal("10000.01"), Decimal("10000")), Decimal("0.01"))
            actual = self.diagnostics()
        self.assertEqual(actual, self.report)
        self.assertEqual(ref._exact_sum(()), Decimal(0))

    def test_nonfinite_and_nonnative_arithmetic_addends_rejected(self):
        for value in (Decimal("NaN"), Decimal("Infinity"), 1, 1.0):
            with self.subTest(value=value), self.assertRaises(ref.EmploymentStructureReferenceError):
                ref._exact_sum((value,))

    def test_sparse_null_zero_and_flag_distinctions(self):
        changed = copy.deepcopy(self.data)
        zero = index(changed, "THS_PER", "EMP_DC", "A01")
        null = index(changed, "THS_PER", "SELF_DC", "A02")
        absent = index(changed, "THS_PER", "EMP_DC", "U")
        changed["value"][zero] = Literal("0.00")
        changed["value"][null] = None
        changed["status"] = {zero: "p", null: "c", absent: "u"}
        cube = parse(changed, self.contract)
        cells = [ref._read(cube, "THS_PER", item, sector) for item, sector in
                 (("EMP_DC", "A01"), ("SELF_DC", "A02"), ("EMP_DC", "U"), ("SAL_DC", "U"))]
        self.assertEqual([(c.presence, c.status) for c in cells],
                         [("NUMERIC", "p"), ("EXPLICIT_NULL", "c"), ("SPARSE_ABSENT", "u"), ("SPARSE_ABSENT", None)])
        self.assertEqual(cells[0].value, 0)
        self.assertTrue(all(c.value is None for c in cells[1:]))
        self.assertEqual(cells[0].fields()["truth_status"], "DER")
        self.assertEqual(cells[1].fields()["truth_status"], "Q")

    def test_native_negative_values_never_clipped(self):
        put(self.data, "THS_PER", "SELF_DC", "A01", "-0.21")
        cell = ref._read(parse(self.data, self.contract), "THS_PER", "SELF_DC", "A01")
        self.assertEqual(cell.value, Decimal("-0.21"))

    def test_partial_sum_zero_does_not_establish_complete_partition(self):
        hours = [r for r in self.report["a64_observed_sum_controls"] if r["unit"] == "THS_HW"]
        self.assertTrue(all(r["residual_observed_sum_minus_total"] == 0 for r in hours))
        self.assertTrue(all(r["missing_codes"] and not r["complete_partition_closure_claim"] for r in hours))
        self.assertFalse(self.report["complete_employment_partition_closure_established"])

    def test_missing_self_remains_unknown_despite_employee_equality(self):
        emp = ref._read(self.employment, "THS_PER", "EMP_DC", "A02")
        sal = ref._read(self.employment, "THS_PER", "SAL_DC", "A02")
        own = ref._read(self.employment, "THS_PER", "SELF_DC", "A02")
        self.assertEqual(emp.value, sal.value)
        self.assertIsNone(own.value)
        self.assertIn("A02", self.report["within_row_identity"]["THS_PER"]["skipped_missing"])

    def test_within_row_rounding_residual_is_retained(self):
        result = self.report["within_row_identity"]["THS_PER"]
        self.assertEqual(result["max_absolute_residual"], Decimal("0.01"))
        self.assertEqual(result["checks"][1]["residual_EMP_minus_SAL_minus_SELF"], Decimal("-0.01"))
        self.assertFalse(result["balancing_adjustment_applied"])
        self.assertEqual(result["tested"], 2)

    def test_partial_person_sums_not_rounded_into_equality(self):
        rows = [r for r in self.report["a64_observed_sum_controls"] if r["unit"] == "THS_PER"]
        self.assertEqual([r["residual_observed_sum_minus_total"] for r in rows],
                         [Decimal("0.01"), Decimal("0.00"), Decimal("0.01")])

    def test_a10_pe_controls_and_national_comparator_are_separate(self):
        controls = self.report["reported_cross_table_controls"]
        self.assertEqual(len(controls), 9)
        self.assertTrue(all(r["residual"] == 0 and not r["independent_corroboration"] for r in controls))
        self.assertEqual(self.report["national_concept_employment_comparator_THSPER"]["value"], Decimal("3.28"))
        self.assertEqual(self.report["totals"]["THS_PER__EMP_DC"], Decimal("3.29"))

    def test_source_controls_with_missing_values_are_not_filled(self):
        data, contract = make_spec("a10")
        del data["value"][index(data, "THS_PER", "EMP_DC", "TOTAL")]
        diagnostic = self.diagnostics(a10=parse(data, contract))["reported_cross_table_controls"][0]
        self.assertIsNone(diagnostic["control_total"]["value"])
        self.assertIsNone(diagnostic["residual"])

    def test_current_io_differences_have_signed_values_and_missing_u(self):
        rows = self.report["current_na_vs_io_controls"]
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[0]["residual_current_minus_io"], Decimal("1.0"))
        self.assertEqual(rows[4]["residual_current_minus_io"], Decimal("-1.0"))
        for row in (rows[3], rows[7]):
            self.assertEqual(row["io_vintage2025"], 0)
            self.assertIsNone(row["current_nama_10_a64"])
            self.assertIsNone(row["residual_current_minus_io"])
        self.assertFalse(self.report["matched_vintage_satellite_established"])
        self.assertTrue(all(r["mismatch_is_not_employment_revision_measure"] for r in rows))

    def test_all_native_selected_rows_are_present_in_report(self):
        self.assertEqual(len(self.report["source_rows"]), 24)
        self.assertEqual({(r["unit"], r["na_item"], r["nace_r2"]) for r in self.report["source_rows"]},
                         {(u, i, s) for u in ref.UNITS for i in ref.INDICATORS for s in ("TOTAL", *SECTORS)})

    def test_source_and_report_are_deeply_immutable(self):
        for mapping in (self.report, self.report["core_coverage"], self.employment.values,
                        self.employment.dimensions["nace_r2"]["category"]["label"]):
            with self.assertRaises(TypeError):
                mapping["injected"] = 4
        self.data["value"].clear()
        self.assertEqual(ref._read(self.employment, "THS_PER", "EMP_DC", "A01").value, Decimal("1.10"))

    def test_schema_rejects_changed_dates_units_geography_and_dimensions(self):
        changes = [lambda d: d.__setitem__("updated", "OTHER"), lambda d: d["id"].reverse(),
                   lambda d: d["size"].__setitem__(0, True), lambda d: d["extension"].__setitem__("id", "OTHER")]
        for dim in ("geo", "time", "unit"):
            changes.append(lambda d, dim=dim: d["dimension"][dim]["category"].__setitem__("index", {"OTHER": 0}))
        for change in changes:
            changed = copy.deepcopy(self.data)
            change(changed)
            with self.assertRaises(ref.EmploymentStructureReferenceError):
                parse(changed, self.contract)

    def test_schema_rejects_malformed_labels_indices_and_extra_fields(self):
        changes = [lambda d: d["dimension"]["geo"]["category"]["index"].__setitem__("HU", False),
                   lambda d: d["dimension"]["geo"]["category"]["label"].clear(),
                   lambda d: d.__setitem__("programme", "scenario"), lambda d: d.__setitem__("value", [1, 2])]
        for change in changes:
            changed = copy.deepcopy(self.data)
            change(changed)
            with self.assertRaises(ref.EmploymentStructureReferenceError):
                parse(changed, self.contract)

    def test_duplicate_json_keys_and_invalid_json_rejected(self):
        for raw in (b'{"value":{},"value":{}}', b'{"status":{"1":"p","1":"c"}}', b'\xff', b'{', b'{"x":NaN}'):
            with self.subTest(raw=raw), self.assertRaises(ref.EmploymentStructureReferenceError):
                ref._parse_cube(raw, self.contract)

    def test_non_numeric_values_and_non_string_flags_rejected(self):
        for value in (True, False, "3.00", [], {}):
            changed = copy.deepcopy(self.data)
            changed["value"]["0"] = value
            with self.subTest(value=value), self.assertRaises(ref.EmploymentStructureReferenceError):
                parse(changed, self.contract)
        self.data["status"] = {"0": None}
        with self.assertRaises(ref.EmploymentStructureReferenceError):
            parse(self.data, self.contract)

    def test_sparse_indices_canonical_and_in_range(self):
        for key in ("-1", "01", "1.0", "+1", "999999", "bad"):
            changed = copy.deepcopy(self.data)
            changed["value"][key] = Literal("1")
            with self.subTest(key=key), self.assertRaises(ref.EmploymentStructureReferenceError):
                parse(changed, self.contract)

    def test_dictionary_order_not_substituted_for_source_positions(self):
        for dimension in self.data["dimension"].values():
            dimension["category"]["index"] = dict(reversed(list(dimension["category"]["index"].items())))
        self.assertEqual(ref._read(parse(self.data, self.contract), "THS_PER", "EMP_DC", "A01").value, Decimal("1.10"))

    def test_unknown_codes_raise_instead_of_becoming_missing(self):
        with self.assertRaises(ref.EmploymentStructureReferenceError):
            ref._read(self.employment, "THS_PER", "EMP_DC", "BAD")
        with self.assertRaises(ref.EmploymentStructureReferenceError):
            self.employment.observation(unit="THS_PER")

    def test_bridge_covers_each_leaf_once_and_preserves_io_totals(self):
        ref._validate_bridge(MAPPINGS, SECTORS, ("TOTAL", *SECTORS))
        for item, total in (("P1", 300), ("B1G", 120)):
            self.assertEqual(self.io[item]["TOTAL"], total)
            self.assertEqual(sum(self.io[item][s] for s in SECTORS), total)
        self.assertEqual(len(self.report["io_aggregation_controls"]), 2)
        self.assertTrue(all(row["residual"] == 0 for row in self.report["io_aggregation_controls"]))

    def test_bridge_rejects_duplicate_omitted_alias_and_wrong_target_mappings(self):
        cases = []
        for change in (lambda m: m[1]["io_leaf_codes"].append("A01"), lambda m: m.pop(),
                       lambda m: m[0].__setitem__("employment_nace_r2", "TOTAL"),
                       lambda m: m[0].__setitem__("official_nace_divisions", "02"),
                       lambda m: m[0].__setitem__("employment_nace_r2", "A02"),
                       lambda m: m[0].__setitem__("official_a64_seq", 2)):
            changed = copy.deepcopy(MAPPINGS)
            change(changed)
            cases.append(changed)
        for mappings in cases:
            with self.subTest(mappings=mappings), self.assertRaises(ref.EmploymentStructureReferenceError):
                ref._validate_bridge(mappings, SECTORS, ("TOTAL", *SECTORS))

    def test_io_aggregation_does_not_fill_missing_or_adjust_source_totals(self):
        for value in (None, 99):
            io = FrozenIOFixture()
            io.values = copy.deepcopy(io.values)
            io.values["P1"]["A01"] = value
            with self.assertRaises(ref.EmploymentStructureReferenceError):
                ref._aggregate_io(io, MAPPINGS)

    def test_public_read_boundary_rejects_source_aliases_fte_jobs_and_reverse_mapping(self):
        metadata = ref._freeze({"bridge": {"mappings": MAPPINGS}, "source_id": "SYNTHETIC-UNADMITTED"})
        reference = ref.EmploymentStructureReference(self.employment, metadata, self.report)
        for changes in ({"industry_code": "D35"}, {"industry_code": "L68A"}, {"indicator": "EMP_NC"},
                        {"unit": "THS_JOB"}, {"unit": "FTE"}, {"unit": "PCH_PRE_PER"}):
            args = dict(industry_code="A01", indicator="EMP_DC", unit="THS_PER")
            args.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ref.EmploymentStructureReferenceError):
                reference.read_cell(**args)
        self.assertFalse(any(hasattr(reference, name) for name in ("fte", "jobs_created", "labour_coefficient", "reverse_allocate", "multiplier")))

    def test_explicit_mapping_year_units_claim_are_required(self):
        with self.assertRaises(TypeError):
            ref.load_employment_structure_reference()
        with self.assertRaises(TypeError):
            ref.load_employment_structure_reference({})
        for paths in ({}, {"OTHER": "x"}, {k: None for k in ref.RUNTIME_SOURCE_IDS}):
            with self.assertRaises(ref.EmploymentStructureReferenceError):
                self.load(paths)
        paths = {k: "nonexistent" for k in ref.RUNTIME_SOURCE_IDS}
        for changes in ({"reference_year": 2024}, {"reference_year": "2023"}, {"reference_year": True},
                        {"units": ("THS_PER", "THS_JOB")}, {"units": ("THS_PER",)},
                        {"claim": "FTE"}, {"claim": "CURRENT_JOBS"}, {"claim": "MATCHED_LABOUR_COEFFICIENT"}):
            with self.subTest(changes=changes), self.assertRaises(ref.EmploymentStructureReferenceError):
                self.load(paths, **changes)

    def test_original_byte_and_manifest_pins_have_no_caller_override(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "synthetic.json"
            path.write_bytes(encode(self.data))
            paths = {k: path for k in ref.RUNTIME_SOURCE_IDS}
            with self.assertRaisesRegex(ref.EmploymentStructureReferenceError, "external source identity"):
                self.load(paths)
            manifest = Path(temp) / "manifest.json"
            changed = copy.deepcopy(self.manifest)
            changed["truth_status"] = "OBS"
            manifest.write_text(json.dumps(changed))
            with patch.object(ref, "MANIFEST_PATH", manifest), self.assertRaisesRegex(ref.EmploymentStructureReferenceError, "manifest identity"):
                self.load(paths)
            with self.assertRaises(TypeError):
                self.load(paths, manifest=self.manifest)

    def test_pinned_bridge_has_no_overlap_and_matches_official_range_semantics(self):
        manifest = self.manifest
        io_manifest = json.loads(ref.industry.MANIFEST_PATH.read_text())
        ref._validate_bridge(manifest["bridge"]["mappings"], io_manifest["industry_partition"]["leaf_codes"],
                             manifest["parser_contracts"][ref.SOURCE_ID]["codes"]["nace_r2"])
        groups = {r["employment_nace_r2"]: r["io_leaf_codes"] for r in manifest["bridge"]["mappings"]}
        self.assertEqual(groups["L68"], ["L68A", "L68B"])
        self.assertEqual(groups["T"], ["T97", "T98"])
        self.assertNotIn("L68A", groups)


if __name__ == "__main__":
    unittest.main()
