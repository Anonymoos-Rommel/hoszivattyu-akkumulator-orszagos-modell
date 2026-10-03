"""Hermetic tests use an authored two-industry accounting example, not source data.

The pinned original is separately checked by explicit local acceptance. These
parser/reconciler fixtures never become admitted source-reference objects.
"""
import copy
import hashlib
import json
import tempfile
import unittest
from decimal import Inexact, Rounded, localcontext
from pathlib import Path
from unittest.mock import patch

import modules.B16.industry_structure_reference as ref


LEAVES = ("A01", "A02")
AGGREGATES = {"A": LEAVES}
UPDATED = "SYNTHETIC-NOT-OFFICIAL"


def fixture():
    """Small signed economy with taxes, inventory, imports and source absence."""
    codes = {"freq": ["A"], "unit": ["MIO_NAC"],
             "ind_ava": ["TOTAL", "A", *LEAVES, *ref._ACCOUNT_ROWS, "IMP"],
             "ind_use": ["TOTAL", "A", *LEAVES, *ref._CONTROL_COLUMNS[1:], "P6_U2"],
             "stk_flow": list(ref.FLOWS), "geo": ["HU"], "time": ["2023"]}
    dimensions = {dim: {"label": "Synthetic " + dim, "category": {
        "index": {code: i for i, code in enumerate(members)},
        "label": {code: "Synthetic " + code for code in members}}} for dim, members in codes.items()}
    data = {"version": "2.0", "class": "dataset", "label": "AUTHORED SYNTHETIC FIXTURE",
            "source": "SYNTHETIC", "updated": UPDATED, "value": {}, "id": list(codes),
            "size": [len(v) for v in codes.values()], "dimension": dimensions,
            "extension": {"id": "SYNTHETIC"}}
    contract = {field: copy.deepcopy(data[field]) for field in ("version", "class", "label", "source", "id", "size")}
    contract.update(codes=codes, extension_id="SYNTHETIC")
    values = {}
    dom, imp = ((8, -2), (3, 11)), ((2, -1), (1, 4))
    # final use: consumption, fixed capital, signed inventory, valuables, export
    final = {"DOM": ((10, 5, -1, 1, 3), (20, 7, 2, 1, 4)),
             "IMP": ((1, 1, -1, 2, 1), (2, 2, 0, 1, 2))}
    for f, matrix in (("DOM", dom), ("IMP", imp)):
        for i, a in enumerate(LEAVES):
            for n, u in enumerate(LEAVES):
                values[a, u, f] = matrix[i][n]
            cons, fixed, inventory, valuables, exports = final[f][i]
            capital = fixed + inventory + valuables
            for col, val in {"P3": cons, "P51G": fixed, "P52": inventory, "P53": valuables,
                             "P5": capital, "P6": exports, "TFU": cons + capital + exports}.items():
                values[a, col, f] = val
            values[a, "TOTAL", f] = sum(matrix[i])
            values[a, "TU", f] = sum(matrix[i]) + cons + capital + exports
    for a in LEAVES:
        for col in [*LEAVES, *ref._CONTROL_COLUMNS]:
            values[a, col, "TOTAL"] = values[a, col, "DOM"] + values[a, col, "IMP"]
    for f in ref.FLOWS:
        for a in LEAVES:
            values[a, "A", f] = sum(values[a, u, f] for u in LEAVES)
        for col in codes["ind_use"]:
            if col == "P6_U2":
                continue  # structural absence in every origin flow, never zero
            for row in ("TOTAL", "A"):
                values[row, col, f] = sum(values[a, col, f] for a in LEAVES)
    for i, u in enumerate(LEAVES):
        output, imports = values[u, "TU", "DOM"], values[u, "TU", "IMP"]
        taxes = (-1, 2)[i]
        consumption = values["TOTAL", u, "TOTAL"] + taxes
        gva = output - consumption
        accounts = {"P1": output, "P7": imports, "TS_BP": output + imports,
                    "P2_ADJ": consumption, "B1G": gva, "D21X31": taxes,
                    "D1": 5, "B2A3G": gva - 6, "D29X39": 1}
        for row, val in accounts.items():
            values[row, u, "TOTAL"] = val
        values["IMP", u, "DOM"] = values["TOTAL", u, "IMP"]
    for row in ref._ACCOUNT_ROWS:
        for col in ("TOTAL", "A"):
            values[row, col, "TOTAL"] = sum(values[row, u, "TOTAL"] for u in LEAVES)
    for col in ("TOTAL", "A"):
        values["IMP", col, "DOM"] = sum(values["IMP", u, "DOM"] for u in LEAVES)
    for (row, col, flow), value in values.items():
        data["value"][index(data, row, col, flow)] = value
    return data, contract


def index(data, row, col, flow):
    dimensions = data["dimension"]
    r = dimensions["ind_ava"]["category"]["index"][row]
    c = dimensions["ind_use"]["category"]["index"][col]
    f = dimensions["stk_flow"]["category"]["index"][flow]
    return str((r * data["size"][3] + c) * 3 + f)


def parse(data, contract):
    return ref._parse_payload(json.dumps(data).encode(), contract, UPDATED)


class B16IndustryStructureReferenceTests(unittest.TestCase):
    def setUp(self):
        self.data, self.contract = fixture()
        self.cube = parse(self.data, self.contract)
        self.manifest = json.loads(ref.MANIFEST_PATH.read_text())

    def test_manifest_exact_byte_binding(self):
        self.assertEqual(hashlib.sha256(ref.MANIFEST_PATH.read_bytes()).hexdigest(), ref.MANIFEST_SHA256)
        source = next(r for r in self.manifest["source_artifacts"] if r["source_id"] == ref.SOURCE_ID)
        self.assertEqual(source["sha256"], ref.SOURCE_SHA256)
        self.assertEqual(source["byte_count"], ref.SOURCE_BYTE_COUNT)
        self.assertEqual(len(self.manifest["source_artifacts"]), 5)
        self.assertNotIn(b"\r", ref.MANIFEST_PATH.read_bytes())

    def test_manifest_keeps_compiled_source_and_reuse_boundaries(self):
        m = self.manifest
        self.assertEqual((m["source_tier"], m["truth_status"], m["evidence_tier"]), ("P1", "DER", "E1"))
        self.assertEqual((m["reference_year"], m["national_data_vintage"]), (2023, 2025))
        self.assertIn("Model D", m["method_semantics"])
        self.assertIn("CIF", m["import_valuation"])
        self.assertIn("not responsible", m["derived_output_notice"])
        self.assertTrue(all(r["reuse_status"] == "EXTERNAL_ONLY" and r["repo_snapshot_path"] is None
                            for r in m["source_artifacts"]))
        self.assertEqual(m["evidence_family"], "KSH_HUNGARIAN_NATIONAL_ACCOUNTS")

    def test_exact_source_partition_keeps_89_leaves_and_15_parents(self):
        p = self.manifest["industry_partition"]
        leaves, parents = p["leaf_codes"], p["excluded_overlapping_aggregates"]
        self.assertEqual((len(leaves), len(parents)), (89, 15))
        self.assertFalse(set(leaves) & set(parents))
        self.assertTrue({"L68A", "L68B", "T97", "T98", "U"} <= set(leaves))
        self.assertIn("inferred", p["source_detail_description"])
        self.assertIn("T97 output and GVA are nonzero", p["source_detail_description"])

    def test_parser_preserves_integer_negative_zero_and_missing(self):
        self.assertEqual(self.cube.value("A01", "A02", "DOM"), -2)
        self.assertEqual(self.cube.value("A02", "P52", "IMP"), 0)
        self.assertIsNone(self.cube.value("B1G", "A01", "IMP"))
        self.assertIsNone(self.cube.value("A01", "P6_U2", "TOTAL"))
        self.assertIs(type(self.cube.value("A01", "A02", "TOTAL")), int)

    def test_source_payload_deeply_immutable(self):
        with self.assertRaises(TypeError):
            self.cube.payload["value"]["0"] = 5
        with self.assertRaises(TypeError):
            self.cube.payload["dimension"]["ind_ava"]["category"]["label"]["A01"] = "changed"
        with self.assertRaises((AttributeError, TypeError)):
            self.cube.payload["size"][0] = 3
        self.data["value"].clear()
        self.assertEqual(self.cube.value("A01", "A02", "DOM"), -2)

    def test_unknown_codes_are_not_missing_cells(self):
        for args in (("BAD", "A01", "DOM"), ("A01", "BAD", "DOM"), ("A01", "A01", "BAD"),
                     ([], "A01", "DOM")):
            with self.subTest(args=args), self.assertRaises(ref.IndustryStructureReferenceError):
                self.cube.value(*args)

    def test_required_missing_cell_fails_closed(self):
        with self.assertRaisesRegex(ref.IndustryStructureReferenceError, "required accounting cell missing"):
            self.cube.required("B1G", "A01", "IMP")

    def test_duplicate_json_keys_rejected(self):
        for raw in (b'{"value":{},"value":{}}', b'{"value":{"0":1,"0":2}}'):
            with self.assertRaisesRegex(ref.IndustryStructureReferenceError, "duplicate JSON key"):
                ref._parse_payload(raw, self.contract, UPDATED)

    def test_bad_json_and_nonfinite_rejected(self):
        for raw in (b'{', b'\xff', b'{"x":NaN}', b'{"x":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ref.IndustryStructureReferenceError):
                ref._parse_payload(raw, self.contract, UPDATED)

    def test_noninteger_values_rejected(self):
        for value in (True, False, 1.0, 0.5, "1", None):
            with self.subTest(value=value), self.assertRaises(ref.IndustryStructureReferenceError):
                changed = copy.deepcopy(self.data)
                changed["value"]["0"] = value
                parse(changed, self.contract)

    def test_sparse_indices_canonical_and_in_range(self):
        size = 1
        for n in self.data["size"]:
            size *= n
        for key in ("-1", "00", "01", "1.0", "+1", " 1", str(size), "x"):
            with self.subTest(key=key), self.assertRaises(ref.IndustryStructureReferenceError):
                changed = copy.deepcopy(self.data)
                changed["value"][key] = 7
                parse(changed, self.contract)

    def test_dimension_order_size_and_labels_required(self):
        changes = [lambda d: d["id"].reverse(), lambda d: d["size"].__setitem__(0, True),
                   lambda d: d["dimension"]["ind_ava"]["category"]["index"].__setitem__("A01", 99),
                   lambda d: d["dimension"]["ind_use"]["category"]["label"].pop("A01"),
                   lambda d: d["dimension"]["ind_ava"]["category"]["index"].__setitem__("TOTAL", False)]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ref.IndustryStructureReferenceError):
                changed = copy.deepcopy(self.data)
                change(changed)
                parse(changed, self.contract)

    def test_reordered_json_objects_keep_dimension_position_semantics(self):
        for dimension in self.data["dimension"].values():
            dimension["category"]["index"] = dict(reversed(list(dimension["category"]["index"].items())))
        cube = parse(self.data, self.contract)
        self.assertEqual(cube.value("A01", "A02", "DOM"), -2)
        self.assertTrue(all(c["passed"] for c in ref._reconcile(cube, LEAVES, AGGREGATES)))

    def test_changed_country_year_unit_dataset_or_revision_rejected(self):
        for dim in ("geo", "time", "unit"):
            with self.subTest(dim=dim), self.assertRaises(ref.IndustryStructureReferenceError):
                changed = copy.deepcopy(self.data)
                changed["dimension"][dim]["category"]["index"] = {"OTHER": 0}
                parse(changed, self.contract)
        for field, val in (("source", "OTHER"), ("updated", "OTHER"), ("class", "collection"), ("version", "1.0")):
            with self.subTest(field=field), self.assertRaises(ref.IndustryStructureReferenceError):
                changed = copy.deepcopy(self.data)
                changed[field] = val
                parse(changed, self.contract)

    def test_new_observation_flags_and_extra_fields_rejected(self):
        for key, value in (("status", {"0": "p"}), ("scenario", "optimistic"), ("value", [1, 2])):
            with self.subTest(key=key), self.assertRaises(ref.IndustryStructureReferenceError):
                changed = copy.deepcopy(self.data)
                changed[key] = value
                parse(changed, self.contract)

    def test_partition_rejects_double_counting_omissions_and_accounts(self):
        cases = [(LEAVES + ("A",), AGGREGATES), (("A01",), AGGREGATES),
                 (LEAVES + ("A01",), AGGREGATES), (LEAVES + ("B1G",), AGGREGATES),
                 (LEAVES, {"A": ("A01", "A01")}), (LEAVES, {"A": ("UNKNOWN",)})]
        for leaves, aggregates in cases:
            with self.subTest(leaves=leaves, aggregates=aggregates), self.assertRaises(ref.IndustryStructureReferenceError):
                ref._validate_partition(self.cube, leaves, aggregates)

    def test_all_16_accounting_families_balance_in_authored_example(self):
        checks = ref._reconcile(self.cube, LEAVES, AGGREGATES)
        self.assertEqual(len(checks), 16)
        self.assertTrue(all(c["passed"] and c["max_absolute_residual_million_HUF"] == 0 for c in checks))
        self.assertEqual(checks[0]["tested_count"], 4)
        self.assertEqual(checks[-1]["unavailable_count"], 3)

    def test_each_identity_family_detects_targeted_corruption(self):
        targets = [("A01", "A01", "TOTAL"), ("A01", "TOTAL", "DOM"),
                   ("TOTAL", "A01", "DOM"), ("A", "A01", "DOM"),
                   ("A01", "A", "DOM"), ("P1", "A01", "TOTAL"),
                   ("D21X31", "A01", "TOTAL"), ("IMP", "A01", "DOM"),
                   ("A01", "TU", "DOM"), ("A01", "TU", "IMP"),
                   ("TS_BP", "A01", "TOTAL"), ("D1", "A01", "TOTAL"),
                   ("A01", "P3", "DOM"), ("A01", "P52", "IMP"),
                   ("A01", "TU", "TOTAL"), ("A01", "P6", "TOTAL")]
        for family, target in enumerate(targets):
            with self.subTest(family=family):
                changed = copy.deepcopy(self.data)
                changed["value"][index(changed, *target)] += 1
                checks = ref._reconcile(parse(changed, self.contract), LEAVES, AGGREGATES)
                self.assertFalse(checks[family]["passed"])
                self.assertGreater(checks[family]["max_absolute_residual_million_HUF"], 0)

    def test_no_abs_or_zero_clipping_for_signed_core_and_inventory(self):
        for target in (("A01", "A02", "DOM"), ("A01", "P52", "IMP"), ("D21X31", "A01", "TOTAL")):
            changed = copy.deepcopy(self.data)
            changed["value"][index(changed, *target)] = 0
            self.assertFalse(all(c["passed"] for c in ref._reconcile(parse(changed, self.contract), LEAVES, AGGREGATES)))

    def test_required_core_and_account_missingness_fail(self):
        for target in (("A01", "A01", "DOM"), ("B1G", "A01", "TOTAL")):
            changed = copy.deepcopy(self.data)
            del changed["value"][index(changed, *target)]
            with self.assertRaisesRegex(ref.IndustryStructureReferenceError, "required accounting cell missing"):
                ref._reconcile(parse(changed, self.contract), LEAVES, AGGREGATES)

    def test_asymmetric_optional_origin_missingness_rejected(self):
        self.data["value"][index(self.data, "A01", "P6_U2", "DOM")] = 0
        with self.assertRaisesRegex(ref.IndustryStructureReferenceError, "asymmetric origin-use missingness"):
            ref._reconcile(parse(self.data, self.contract), LEAVES, AGGREGATES)

    def test_supplementary_accounts_not_subject_to_dom_plus_imp(self):
        self.assertIsNone(self.cube.value("B1G", "A01", "IMP"))
        self.assertIsNone(self.cube.value("B1G", "A01", "DOM"))
        checks = ref._reconcile(self.cube, LEAVES, AGGREGATES)
        self.assertTrue(all(c["passed"] for c in checks))
        self.assertEqual(self.manifest["account_row_availability"]["B1G"]["IMP"], 0)
        self.assertEqual(self.manifest["account_row_availability"]["P7"], {"TOTAL": 105, "IMP": 0, "DOM": 0})

    def test_math_independent_of_hostile_decimal_context(self):
        expected = ref._reconcile(self.cube, LEAVES, AGGREGATES)
        with localcontext() as context:
            context.prec = 1
            context.Emax = 1
            context.Emin = -1
            context.traps[Inexact] = True
            context.traps[Rounded] = True
            actual = ref._reconcile(self.cube, LEAVES, AGGREGATES)
        self.assertEqual(actual, expected)

    def test_source_path_and_all_selection_arguments_required(self):
        with self.assertRaises(TypeError):
            ref.load_industry_structure_reference()
        with self.assertRaises(TypeError):
            ref.load_industry_structure_reference("anything")
        with self.assertRaises(ref.IndustryStructureReferenceError):
            self.load(None)

    def load(self, path, **changes):
        args = dict(source_id=ref.SOURCE_ID, reference_year=2023, unit="MIO_NAC", claim=ref.HISTORICAL_ACCOUNTING_REFERENCE)
        args.update(changes)
        return ref.load_industry_structure_reference(path, **args)

    def test_wrong_scope_rejected_before_accessing_source(self):
        for changes in ({"source_id": "OTHER"}, {"reference_year": 2024}, {"reference_year": "2023"},
                        {"reference_year": True}, {"unit": "EUR"}, {"unit": "HUF"},
                        {"claim": "NET_GDP"}, {"claim": "CURRENT_CAPACITY"}, {"claim": "EMPLOYMENT_FTE"}):
            with self.subTest(changes=changes), self.assertRaises(ref.IndustryStructureReferenceError):
                self.load("nonexistent", **changes)

    def test_synthetic_and_wrong_source_originals_cannot_be_admitted(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "original.json"
            path.write_text(json.dumps(self.data))
            with self.assertRaisesRegex(ref.IndustryStructureReferenceError, "external source identity mismatch"):
                self.load(path)
            path.write_bytes(b" " * ref.SOURCE_BYTE_COUNT)
            with self.assertRaisesRegex(ref.IndustryStructureReferenceError, "external source identity mismatch"):
                self.load(path)

    def test_mutated_manifest_is_not_a_trusted_override(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            self.manifest["truth_status"] = "OBS"
            path.write_text(json.dumps(self.manifest))
            with patch.object(ref, "MANIFEST_PATH", path), self.assertRaisesRegex(ref.IndustryStructureReferenceError, "manifest identity mismatch"):
                self.load("nonexistent")
        with self.assertRaises(TypeError):
            self.load("nonexistent", manifest=self.manifest)

    def test_no_effects_or_programme_api(self):
        self.assertFalse(any(hasattr(ref.IndustryStructureReference, name) for name in
                             ("multiplier", "shock", "net_gdp", "jobs", "convert_currency", "scenario")))
        self.assertEqual(set(self.manifest["expected_identity_counts"]),
                         {c["name"] for c in ref._reconcile(self.cube, LEAVES, AGGREGATES)})


if __name__ == "__main__":
    unittest.main()
