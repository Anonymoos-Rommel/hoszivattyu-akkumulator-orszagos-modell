"""Pinned, read-only Hungarian 2023 national input-output reference.

No programme inputs, technical coefficients, multiplier or effects engine.
Original source bytes are supplied explicitly from outside the repository.
All arithmetic is in source-native integer million HUF, independent of Decimal
context. Private parser/reconciler helpers do not confer source admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "registry/b16_industry_structure_reference_manifest.json"
MANIFEST_SHA256 = "f0da3653a5ccccde6d88bab13afbd0cf5f1872035e7d6c9a38d56bd5cf036c7c"
SOURCE_ID = "SRC-B16-EUROSTAT-KSH-HU-IOT-2023"
SOURCE_SHA256 = "157e5d50e13fb447b17e63d5298012f2038940320145cae419eebc4139e539b1"
SOURCE_BYTE_COUNT = 503908
HISTORICAL_ACCOUNTING_REFERENCE = "HISTORICAL_ACCOUNTING_REFERENCE"
FLOWS = ("TOTAL", "IMP", "DOM")
_ACCOUNT_ROWS = ("P1", "P7", "TS_BP", "P2_ADJ", "B1G", "D21X31", "D1", "B2A3G", "D29X39")
_CONTROL_COLUMNS = ("TOTAL", "P3", "P5", "P6", "TU", "TFU", "P51G", "P52", "P53")
_ALL_ACCOUNT_ROWS = frozenset((*_ACCOUNT_ROWS, "B2A3N", "B3G", "D11", "P7_B0", "P7_D0", "P7_U2", "P7_U3", "P51C", "IMP"))
_ALL_FINAL_COLUMNS = frozenset((*_CONTROL_COLUMNS, "P3_S13", "P3_S14", "P3_S15", "P5M", "P6_B0", "P6_D0", "P6_U2", "P6_U3"))


class IndustryStructureReferenceError(ValueError):
    """Unadmitted source, scope, schema or accounting inconsistency."""


def _require(condition, message):
    if not condition:
        raise IndustryStructureReferenceError(message)


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(val) for key, val in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(val) for val in value)
    return value


def _plain(value):
    if isinstance(value, Mapping):
        return {key: _plain(val) for key, val in value.items()}
    if isinstance(value, tuple):
        return [_plain(val) for val in value]
    return value


def _unique_object(pairs):
    result = {}
    for key, val in pairs:
        _require(key not in result, f"duplicate JSON key: {key}")
        result[key] = val
    return result


def _decode(raw):
    try:
        return json.loads(raw, object_pairs_hook=_unique_object,
                          parse_constant=lambda val: _require(False, f"nonfinite JSON value: {val}"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise IndustryStructureReferenceError("invalid UTF-8/JSON source") from exc


@dataclass(frozen=True)
class _Cube:
    """Immutable source-native JSON-stat; parsed does not mean admitted."""

    payload: Mapping

    @property
    def rows(self):
        return tuple(self.payload["dimension"]["ind_ava"]["category"]["index"])

    @property
    def columns(self):
        return tuple(self.payload["dimension"]["ind_use"]["category"]["index"])

    def value(self, row, column, flow):
        # Last dimension varies fastest in JSON-stat. Singleton dimensions are
        # still checked by the parser; do not rely on dictionary iteration order.
        indices = self.payload["dimension"]
        flat = 0
        coordinates = {"freq": "A", "unit": "MIO_NAC", "ind_ava": row,
                       "ind_use": column, "stk_flow": flow, "geo": "HU", "time": "2023"}
        for dim, size in zip(self.payload["id"], self.payload["size"]):
            code = coordinates[dim]
            index = indices[dim]["category"]["index"]
            _require(isinstance(code, str) and code in index, f"unknown {dim} code: {code}")
            flat = flat * size + index[code]
        return self.payload["value"].get(str(flat))

    def required(self, row, column, flow):
        value = self.value(row, column, flow)
        _require(value is not None, f"required accounting cell missing: {row}/{column}/{flow}")
        return value


def _parse_payload(raw, contract, updated):
    """Strict schema parser, independently testable with labelled synthetic data.

    The public loader additionally pins both source and manifest exact bytes.
    Calling this private helper does not produce an admitted reference object.
    """
    data = _decode(raw)
    _require(isinstance(data, dict), "dataset object required")
    required = {"version", "class", "label", "source", "updated", "value", "id", "size", "dimension", "extension"}
    _require(set(data) in (required, required | {"status"}), "unexpected dataset fields")
    for field in ("version", "class", "source", "label", "id", "size"):
        _require(data[field] == contract[field], f"source schema mismatch: {field}")
    _require(all(type(v) is int and v > 0 for v in data["size"]), "positive integer dimension sizes required")
    _require(data["updated"] == updated, "source revision mismatch")
    _require(isinstance(data["extension"], dict) and data["extension"].get("id") == contract["extension_id"],
             "dataset identity mismatch")
    _require(data.get("status", {}) == {}, "unreviewed observation flags")
    dimensions = data["dimension"]
    _require(isinstance(dimensions, dict) and set(dimensions) == set(data["id"]), "dimension set mismatch")
    for dim, size in zip(data["id"], data["size"]):
        entry = dimensions[dim]
        _require(isinstance(entry, dict) and isinstance(entry.get("label"), str) and
                 isinstance(entry.get("category"), dict), f"invalid dimension: {dim}")
        category = entry["category"]
        expected = {code: pos for pos, code in enumerate(contract["codes"][dim])}
        index, labels = category.get("index"), category.get("label")
        _require(isinstance(index, dict) and len(index) == size and index == expected and
                 all(type(v) is int for v in index.values()), f"ordered category mismatch: {dim}")
        _require(isinstance(labels, dict) and set(labels) == set(index) and
                 all(isinstance(v, str) and v for v in labels.values()), f"invalid category labels: {dim}")
    values = data["value"]
    _require(isinstance(values, dict), "sparse value object required")
    cell_count = math.prod(data["size"])
    for key, value in values.items():
        _require(re.fullmatch(r"0|[1-9][0-9]*", key) is not None and int(key) < cell_count,
                 "sparse cell index out of range or noncanonical")
        _require(type(value) is int, "source values must be signed integer million HUF; omit missing keys")
    return _Cube(_freeze(data))


def _validate_partition(cube, leaves, aggregates):
    _require(bool(leaves) and len(leaves) == len(set(leaves)), "unique nonempty industry leaves required")
    _require(not set(leaves) & set(aggregates), "overlapping parent/leaf partition")
    industry = set(leaves) | set(aggregates)
    _require(industry == set(cube.rows) - _ALL_ACCOUNT_ROWS - {"TOTAL"} ==
             set(cube.columns) - _ALL_FINAL_COLUMNS, "industry partition incomplete or codes absent from source")
    _require(not industry & ({"TOTAL"} | set(_ACCOUNT_ROWS) | set(_CONTROL_COLUMNS)), "accounting code is not an industry")
    for children in aggregates.values():
        _require(bool(children) and len(children) == len(set(children)) and set(children) <= set(leaves),
                 "aggregate children must be distinct admitted leaves")


def _reconcile(cube, leaves, aggregates):
    """Check only declared accounting domains; never invent missing addends."""
    _validate_partition(cube, leaves, aggregates)
    leaves = tuple(leaves)
    all_industries = leaves + ("TOTAL",)
    v = cube.required
    checks = []

    def check(name, residuals, unavailable=0):
        values = tuple(residuals)
        checks.append({"name": name, "tested_count": len(values), "unavailable_count": unavailable,
                       "max_absolute_residual_million_HUF": max(map(abs, values), default=0),
                       "passed": bool(values) and all(value == 0 for value in values)})

    check("intermediate matrix TOTAL equals DOM plus IMP",
          (v(a, u, "TOTAL") - v(a, u, "DOM") - v(a, u, "IMP") for a in leaves for u in leaves))
    check("leaf row sums equal reported intermediate-use total",
          (sum(v(a, u, f) for u in leaves) - v(a, "TOTAL", f) for a in leaves for f in FLOWS))
    check("leaf column sums equal reported total intermediate-input row",
          (sum(v(a, u, f) for a in leaves) - v("TOTAL", u, f) for u in leaves for f in FLOWS))
    check("source overlapping row aggregates equal children",
          (v(a, u, f) - sum(v(c, u, f) for c in children)
           for a, children in aggregates.items() for u in leaves for f in FLOWS))
    check("source overlapping column aggregates equal children",
          (v(a, u, f) - sum(v(a, c, f) for c in children)
           for u, children in aggregates.items() for a in leaves for f in FLOWS))
    check("gross output equals adjusted intermediate consumption plus GVA",
          (v("P1", u, "TOTAL") - v("P2_ADJ", u, "TOTAL") - v("B1G", u, "TOTAL") for u in all_industries))
    check("adjusted intermediate consumption equals basic-price inputs plus product taxes less subsidies",
          (v("P2_ADJ", u, "TOTAL") - v("TOTAL", u, "TOTAL") - v("D21X31", u, "TOTAL") for u in all_industries))
    check("domestic-table imported input row equals import-matrix column sum",
          (v("IMP", u, "DOM") - v("TOTAL", u, "IMP") for u in all_industries))
    check("domestic row total-use equals industry output",
          (v(a, "TU", "DOM") - v("P1", a, "TOTAL") for a in leaves))
    check("import row total-use equals imports by corresponding industry",
          (v(a, "TU", "IMP") - v("P7", a, "TOTAL") for a in leaves))
    check("total supply equals output plus imports",
          (v("TS_BP", u, "TOTAL") - v("P1", u, "TOTAL") - v("P7", u, "TOTAL") for u in all_industries))
    check("GVA equals compensation plus gross operating surplus mixed income plus other net production tax",
          (v("B1G", u, "TOTAL") - v("D1", u, "TOTAL") - v("B2A3G", u, "TOTAL") - v("D29X39", u, "TOTAL")
           for u in all_industries))
    check("total final use equals consumption plus capital formation plus exports",
          (v(a, "TFU", f) - v(a, "P3", f) - v(a, "P5", f) - v(a, "P6", f) for a in all_industries for f in FLOWS))
    check("capital formation preserves inventory and valuables signs",
          (v(a, "P5", f) - v(a, "P51G", f) - v(a, "P52", f) - v(a, "P53", f) for a in all_industries for f in FLOWS))
    check("row total use equals intermediate plus final use",
          (v(a, "TU", f) - v(a, "TOTAL", f) - v(a, "TFU", f) for a in all_industries for f in FLOWS))
    residuals, unavailable = [], 0
    for a in all_industries:
        for u in cube.columns:
            cells = tuple(cube.value(a, u, f) for f in FLOWS)
            if any(value is None for value in cells):
                _require(all(value is None for value in cells), "asymmetric origin-use missingness")
                unavailable += 1
            else:
                total, imported, domestic = cells
                residuals.append(total - imported - domestic)
    check("full use-block TOTAL equals DOM plus IMP", residuals, unavailable)
    return _freeze(checks)


def _counts(cube, rows, columns):
    result = {}
    for flow in FLOWS:
        values = [cube.value(row, col, flow) for row in rows for col in columns]
        result[flow] = {"numeric": sum(v is not None for v in values), "missing": sum(v is None for v in values),
                        "zero": sum(v == 0 for v in values), "negative": sum(v is not None and v < 0 for v in values)}
    return result


def _validate_admission(cube, manifest, checks):
    counts = manifest["expected_counts"]
    _require(math.prod(cube.payload["size"]) == counts["all_cells"] and
             len(cube.payload["value"]) == counts["numeric_cells"] and
             counts["all_cells"] - counts["numeric_cells"] == counts["sparse_missing_cells"],
             "source coverage mismatch")
    _require(_counts(cube, cube.rows, cube.columns) == counts["raw_flow_counts"], "flow coverage/sign mismatch")
    leaves = manifest["industry_partition"]["leaf_codes"]
    _require(_counts(cube, leaves, leaves) == counts["disjoint_core_flow_counts"], "core coverage/sign mismatch")
    account_presence = {row: {flow: sum(cube.value(row, col, flow) is not None for col in cube.columns)
                              for flow in FLOWS} for row in manifest["account_row_availability"]}
    _require(account_presence == manifest["account_row_availability"], "account-row structural availability mismatch")
    _require({c["name"]: c["tested_count"] for c in checks} == manifest["expected_identity_counts"] and
             all(c["passed"] for c in checks), "accounting reconciliation failed")


@dataclass(frozen=True)
class ReferenceCell:
    row: str
    column: str
    flow: str
    value: int | None
    truth_status: str
    metadata: Mapping


@dataclass(frozen=True)
class IndustryStructureReference:
    """Use load_industry_structure_reference to obtain an admitted instance."""

    _cube: _Cube
    metadata: Mapping
    checks: tuple

    @property
    def leaf_codes(self):
        return self.metadata["industry_partition"]["leaf_codes"]

    @property
    def source_dimensions(self):
        """Source-native immutable labels and positions, not inferred industries."""
        return self._cube.payload["dimension"]

    def read_cell(self, *, row, column, flow):
        value = self._cube.value(row, column, flow)
        return ReferenceCell(row, column, flow, value, "Q" if value is None else "DER", self.metadata)

    def report(self):
        """Return an immutable derived report; no file output or source republication."""
        return _freeze({
            "reference_id": self.metadata["reference_id"], "source_id": SOURCE_ID,
            "source_sha256": SOURCE_SHA256, "manifest_sha256": MANIFEST_SHA256,
            "claim": HISTORICAL_ACCOUNTING_REFERENCE, "reference_year": 2023,
            "unit": "million HUF", "source_tier": "P1", "truth_status": "DER",
            "evidence_tier": "E1", "leaf_count": len(self.leaf_codes),
            "checks": self.checks, "all_checks_passed": all(c["passed"] for c in self.checks),
            "coverage": self.metadata["expected_counts"],
            "source_accounting_controls_million_HUF": {
                flow: {col: self._cube.required("TOTAL", col, flow) for col in _CONTROL_COLUMNS} for flow in FLOWS},
            "source_accounting_rows_million_HUF": {
                row: self._cube.required(row, "TOTAL", "TOTAL") for row in _ACCOUNT_ROWS},
            "account_row_availability": self.metadata["account_row_availability"],
            "national_data_vintage": self.metadata["national_data_vintage"],
            "price_basis": self.metadata["price_basis"], "import_valuation": self.metadata["import_valuation"],
            "flow_meanings": self.metadata["flow_meanings"], "method_semantics": self.metadata["method_semantics"],
            "shared_lineage": self.metadata["shared_lineage"],
            "missingness_rule": self.metadata["missingness_rule"],
            "signed_value_boundary": self.metadata["signed_value_boundary"],
            "applicability_boundaries": self.metadata["applicability_boundaries"],
            "validation_debt": self.metadata["validation_debt"],
            "source_artifacts": self.metadata["source_artifacts"],
            "attribution": self.metadata["attribution"], "derived_output_notice": self.metadata["derived_output_notice"],
            "programme_calculation_performed": False,
        })


def load_industry_structure_reference(source_path, *, source_id, reference_year, unit, claim):
    """Explicit source/year/unit/claim only; local read, no discovery or download.

    A changed official payload requires a newly reviewed source/manifest, not a
    caller-supplied hash override. Source paths are never written to the report.
    """
    _require(source_id == SOURCE_ID and type(reference_year) is int and reference_year == 2023 and
             unit == "MIO_NAC" and claim == HISTORICAL_ACCOUNTING_REFERENCE,
             "only the explicit HU 2023 MIO_NAC historical accounting reference is admitted")
    _require(isinstance(source_path, (str, Path)) and bool(str(source_path)), "explicit external source path required")
    manifest_bytes = MANIFEST_PATH.read_bytes()
    _require(hashlib.sha256(manifest_bytes).hexdigest() == MANIFEST_SHA256, "manifest identity mismatch")
    manifest = _decode(manifest_bytes)
    raw = Path(source_path).read_bytes()
    _require(len(raw) == SOURCE_BYTE_COUNT and hashlib.sha256(raw).hexdigest() == SOURCE_SHA256,
             "external source identity mismatch")
    source = next(row for row in manifest["source_artifacts"] if row["source_id"] == SOURCE_ID)
    _require(source["sha256"] == SOURCE_SHA256 and source["byte_count"] == SOURCE_BYTE_COUNT,
             "manifest/source binding mismatch")
    cube = _parse_payload(raw, manifest["parser_contract"], manifest["source_global_updated"])
    partition = manifest["industry_partition"]
    checks = _reconcile(cube, partition["leaf_codes"], partition["excluded_overlapping_aggregates"])
    _validate_admission(cube, manifest, checks)
    return IndustryStructureReference(cube, _freeze(manifest), checks)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="explicit path to reviewed source original")
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--reference-year", required=True, type=int)
    parser.add_argument("--unit", required=True)
    parser.add_argument("--claim", required=True)
    args = parser.parse_args(argv)
    try:
        result = load_industry_structure_reference(args.source, source_id=args.source_id,
                    reference_year=args.reference_year, unit=args.unit, claim=args.claim)
    except (IndustryStructureReferenceError, OSError) as exc:
        parser.exit(2, f"B16 reference rejected: {exc}\n")
    print(json.dumps(_plain(result.report()), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
