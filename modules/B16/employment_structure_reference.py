"""Pinned HU2023 persons/hours; vintage compatibility with IO is not established.

Read-only descriptive source accounting and one-way IO aggregation. No labour
coefficients, FTE, jobs effects, allocation back to IO leaves, or network access.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from modules.B16 import industry_structure_reference as industry

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "registry/b16_employment_structure_reference_manifest.json"
MANIFEST_SHA256 = "4a8b773ff92d0c87e0101f02c7e476d2afbeb4a1edf8f67f8a5394094711701d"
SOURCE_ID = "SRC-B16-EUROSTAT-KSH-HU-EMPLOYMENT-2023"
A10_SOURCE_ID = "SRC-B16-EUROSTAT-HU-EMPLOYMENT-A10-2023"
PE_SOURCE_ID = "SRC-B16-EUROSTAT-HU-POPULATION-EMPLOYMENT-2023"
CURRENT_NA_SOURCE_ID = "SRC-B16-EUROSTAT-HU-NATIONAL-ACCOUNTS-2023-CONTROL"
RUNTIME_SOURCE_IDS = frozenset((SOURCE_ID, A10_SOURCE_ID, PE_SOURCE_ID, CURRENT_NA_SOURCE_ID, industry.SOURCE_ID))
HISTORICAL_EMPLOYMENT_ATTACHMENT = "HISTORICAL_EMPLOYMENT_ATTACHMENT"
UNITS = ("THS_PER", "THS_HW")
INDICATORS = ("EMP_DC", "SAL_DC", "SELF_DC")


class EmploymentStructureReferenceError(ValueError):
    """Unadmitted source identity, schema, selection or classification bridge."""


def _require(condition, message):
    if not condition:
        raise EmploymentStructureReferenceError(message)


def _freeze(value):
    if isinstance(value, Mapping):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


def _plain(value):
    if isinstance(value, Mapping):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if isinstance(value, Decimal):
        return str(value)
    return value


def _exact_sum(values):
    """Exact base-ten integer-coefficient arithmetic, without Decimal context.

    Decimal constructors/copy_negate/copy_abs are exact; arithmetic operators,
    unary +/- and quantize are deliberately not used on Decimal values.
    """
    values = tuple(values)
    if not values:
        return Decimal(0)
    _require(all(isinstance(v, Decimal) and v.is_finite() for v in values), "finite Decimal addends required")
    exponent = min(v.as_tuple().exponent for v in values)
    total = 0
    for value in values:
        sign, digits, exp = value.as_tuple()
        coefficient = int("".join(map(str, digits)))
        total += (-coefficient if sign else coefficient) * 10 ** (exp - exponent)
    return Decimal((int(total < 0), tuple(map(int, str(abs(total)))), exponent))


def _difference(left, right):
    return None if left is None or right is None else _exact_sum((left, right.copy_negate()))


@dataclass(frozen=True)
class _Number:
    lexeme: str
    value: Decimal


def _number(lexeme):
    return _Number(lexeme, Decimal(lexeme))


def _unique(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _decode(raw, *, preserve_numbers=False):
    try:
        kwargs = {"parse_float": _number, "parse_int": _number} if preserve_numbers else {}
        return json.loads(raw, object_pairs_hook=_unique,
                          parse_constant=lambda v: _require(False, f"nonfinite JSON number: {v}"), **kwargs)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EmploymentStructureReferenceError("invalid source JSON") from exc


def _schema_integer(number):
    _require(isinstance(number, _Number) and re.fullmatch(r"0|[1-9][0-9]*", number.lexeme),
             "schema positions and sizes must be canonical nonnegative integers")
    return int(number.lexeme)


@dataclass(frozen=True)
class _Observation:
    value: Decimal | None
    lexeme: str | None
    presence: str
    status: str | None

    def fields(self):
        return {"value": self.value, "lexeme": self.lexeme, "presence": self.presence,
                "source_status": self.status, "truth_status": "Q" if self.value is None else "DER"}


@dataclass(frozen=True)
class _Cube:
    ids: tuple
    sizes: tuple
    dimensions: Mapping
    values: Mapping
    statuses: Mapping

    def observation(self, **coordinates):
        _require(set(coordinates) == set(self.ids), "exact source coordinates required")
        flat = 0
        for dim, size in zip(self.ids, self.sizes):
            code = coordinates[dim]
            positions = self.dimensions[dim]["category"]["index"]
            _require(isinstance(code, str) and code in positions, f"unknown {dim} code: {code}")
            flat = flat * size + positions[code]
        key = str(flat)
        value = self.values.get(key)
        presence = "SPARSE_ABSENT" if key not in self.values else "EXPLICIT_NULL" if value is None else "NUMERIC"
        return _Observation(None if value is None else value.value, None if value is None else value.lexeme,
                            presence, self.statuses.get(key))


def _parse_cube(raw, contract):
    """Private syntax test seam, not an admitted reference loader."""
    data = _decode(raw, preserve_numbers=True)
    required = {"version", "class", "label", "source", "updated", "value", "id", "size", "dimension", "extension"}
    _require(isinstance(data, dict) and set(data) in (required, required | {"status"}), "unexpected dataset fields")
    for field in ("version", "class", "label", "source", "updated", "id"):
        _require(data[field] == contract[field], f"source contract mismatch: {field}")
    _require(isinstance(data["size"], list), "dimension size array required")
    sizes = [_schema_integer(v) for v in data["size"]]
    _require(sizes == contract["size"] and all(v > 0 for v in sizes), "dimension size mismatch")
    _require(isinstance(data["extension"], dict) and data["extension"].get("id") == contract["extension_id"],
             "dataset identity mismatch")
    dimensions = data["dimension"]
    _require(isinstance(dimensions, dict) and set(dimensions) == set(data["id"]), "dimension set mismatch")
    for dim, size in zip(data["id"], sizes):
        entry = dimensions[dim]
        _require(isinstance(entry, dict) and isinstance(entry.get("label"), str) and
                 isinstance(entry.get("category"), dict), "invalid dimension metadata")
        category = entry["category"]
        _require(isinstance(category.get("index"), dict), "category index object required")
        positions = {k: _schema_integer(v) for k, v in category["index"].items()}
        expected = {code: index for index, code in enumerate(contract["codes"][dim])}
        _require(positions == expected and len(positions) == size, "ordered source categories mismatch")
        labels = category.get("label")
        _require(isinstance(labels, dict) and set(labels) == set(positions) and
                 all(isinstance(v, str) and v for v in labels.values()), "category labels mismatch")
        category["index"] = positions
    values, statuses = data["value"], data.get("status", {})
    _require(isinstance(values, dict) and isinstance(statuses, dict), "sparse value/status objects required")
    for field, entries in (("value", values), ("status", statuses)):
        for key, value in entries.items():
            _require(re.fullmatch(r"0|[1-9][0-9]*", key) and int(key) < math.prod(sizes), "invalid sparse index")
            if field == "value":
                _require(value is None or isinstance(value, _Number) and value.value.is_finite(),
                         "source value must be a finite JSON number or explicit null")
            else:
                _require(isinstance(value, str), "source status must be a string")
    return _Cube(tuple(data["id"]), tuple(sizes), _freeze(dimensions), _freeze(values), _freeze(statuses))


def _read(cube, unit, item, sector=None):
    coordinates = dict(freq="A", unit=unit, na_item=item, geo="HU", time="2023")
    if "nace_r2" in cube.ids:
        coordinates["nace_r2"] = sector
    return cube.observation(**coordinates)


def _validate_bridge(mappings, io_leaves, employment_codes):
    targets = [r["employment_nace_r2"] for r in mappings]
    assigned = [leaf for r in mappings for leaf in r["io_leaf_codes"]]
    _require(len(targets) == len(set(targets)) and "TOTAL" not in targets and set(targets) <= set(employment_codes),
             "bridge targets must be unique non-total source categories")
    _require(len(assigned) == len(set(assigned)) and set(assigned) == set(io_leaves),
             "bridge must cover each IO leaf exactly once, without parents or reverse allocation")
    for row in mappings:
        _require(bool(row["io_leaf_codes"]), "empty classification group")
        interval = row["official_nace_divisions"].split("-")
        low, high = int(interval[0]), int(interval[-1])
        target = row["employment_nace_r2"]
        section_ranges = {"B": (5, 9), "D": (35, 35), "F": (41, 43), "I": (55, 56),
                          "O": (84, 84), "P": (85, 85), "T": (97, 98), "U": (99, 99)}
        numbers = [int(n) for n in re.findall(r"\d+", target)]
        target_range = section_ranges.get(target, (numbers[0], numbers[-1]) if numbers else None)
        _require(target_range == (low, high), "employment target does not match the official A64 division range")
        divisions = set()
        for code in row["io_leaf_codes"]:
            aliases = {"D": 35, "O": 84, "P": 85, "U": 99}
            divisions.add(aliases[code] if code in aliases else int(re.search(r"\d+", code).group()))
        _require(divisions == set(range(low, high + 1)), "IO leaves do not match the official A64 division range")
    _require([r["official_a64_seq"] for r in mappings] == list(range(1, len(mappings) + 1)), "ordered A64 classification required")


def _aggregate_io(io_reference, mappings):
    results = {}
    for item in ("P1", "B1G"):
        results[item] = {}
        for row in mappings:
            values = [io_reference.read_cell(row=item, column=leaf, flow="TOTAL").value for leaf in row["io_leaf_codes"]]
            _require(all(type(v) is int for v in values), "missing frozen IO accounting amount")
            results[item][row["employment_nace_r2"]] = sum(values)
        total = io_reference.read_cell(row=item, column="TOTAL", flow="TOTAL").value
        _require(type(total) is int and sum(results[item].values()) == total, "IO aggregation must preserve its own source total")
        results[item]["TOTAL"] = total
    return _freeze(results)


def _diagnostics(employment, a10, pe, current, io_aggregates, sectors):
    coverage, totals, partial, within, controls, rows = {}, {}, [], {}, [], []
    for unit in UNITS:
        for item in INDICATORS:
            observations = {s: _read(employment, unit, item, s) for s in sectors}
            known = [v.value for v in observations.values() if v.value is not None]
            missing = [s for s, v in observations.items() if v.value is None]
            key = unit + "__" + item
            coverage[key] = {"present_count": len(known), "absent_count": len(missing), "absent_codes": missing,
                             "explicit_zero_count": sum(v == 0 for v in known), "negative_count": sum(v < 0 for v in known)}
            total = _read(employment, unit, item, "TOTAL")
            _require(total.value is not None, "native employment total is required")
            totals[key] = total.value
            observed_sum = _exact_sum(known)
            partial.append({"unit": unit, "na_item": item, "observed_sum": observed_sum, "reported_total": total.value,
                            "residual_observed_sum_minus_total": _difference(observed_sum, total.value),
                            "missing_codes": missing, "complete_partition_closure_claim": False})
            for source_id, cube in ((A10_SOURCE_ID, a10), (PE_SOURCE_ID, pe)):
                if source_id == PE_SOURCE_ID and unit != "THS_PER":
                    continue
                control = _read(cube, unit, item, "TOTAL")
                controls.append({"source_id": source_id, "unit": unit, "na_item": item,
                                 "a64_total": total.fields(), "control_total": control.fields(),
                                 "residual": _difference(total.value, control.value),
                                 "independent_corroboration": False})
            for sector in ("TOTAL", *sectors):
                observation = total if sector == "TOTAL" else observations[sector]
                rows.append({"nace_r2": sector, "unit": unit, "na_item": item, **observation.fields()})
        checks, skipped = [], []
        for sector in ("TOTAL", *sectors):
            values = [_read(employment, unit, item, sector).value for item in INDICATORS]
            if any(v is None for v in values):
                skipped.append(sector)
            else:
                checks.append({"nace_r2": sector, "residual_EMP_minus_SAL_minus_SELF":
                               _exact_sum((values[0], values[1].copy_negate(), values[2].copy_negate()))})
        within[unit] = {"tested": len(checks), "skipped_missing": skipped, "checks": checks,
                        "max_absolute_residual": max((r["residual_EMP_minus_SAL_minus_SELF"].copy_abs() for r in checks), default=Decimal(0)),
                        "rounding_display_quantum": "0.01" if unit == "THS_PER" else "1",
                        "balancing_adjustment_applied": False}
    comparisons, summary = [], {}
    for item in ("P1", "B1G"):
        summary[item] = {"matched": 0, "mismatched": 0, "missing": 0}
        for sector in ("TOTAL", *sectors):
            observation = _read(current, "CP_MNAC", item, sector)
            frozen = io_aggregates[item][sector]
            residual = _difference(observation.value, Decimal(frozen))
            summary[item]["missing" if residual is None else "matched" if residual == 0 else "mismatched"] += 1
            comparisons.append({"nace_r2": sector, "na_item": item, "io_vintage2025": frozen,
                                "current_nama_10_a64": observation.value, "current_lexeme": observation.lexeme,
                                "current_presence": observation.presence, "current_source_status": observation.status,
                                "residual_current_minus_io": residual, "unit": "million HUF",
                                "mismatch_is_not_employment_revision_measure": True})
    return _freeze({"full_cube": {"slots": math.prod(employment.sizes),
                    "numeric": sum(v is not None for v in employment.values.values()),
                    "sparse_absent": math.prod(employment.sizes) - len(employment.values),
                    "explicit_null": sum(v is None for v in employment.values.values()),
                    "observation_status_count": len(employment.statuses)},
                    "core_coverage": coverage, "totals": totals, "source_rows": rows,
                    "a64_observed_sum_controls": partial, "within_row_identity": within,
                    "reported_cross_table_controls": controls, "io_aggregates": io_aggregates,
                    "io_aggregation_controls": [{"na_item": item,
                        "aggregated_io89_to64_sum": sum(io_aggregates[item][s] for s in sectors),
                        "reported_io_total": io_aggregates[item]["TOTAL"],
                        "residual": sum(io_aggregates[item][s] for s in sectors) - io_aggregates[item]["TOTAL"],
                        "unit": "million HUF"} for item in ("P1", "B1G")],
                    "current_na_vs_io_controls": comparisons, "current_na_vs_io_mismatch_summary": summary,
                    "national_concept_employment_comparator_THSPER": _read(pe, "THS_PER", "EMP_NC").fields(),
                    "programme_calculation_performed": False, "matched_vintage_satellite_established": False,
                    "complete_employment_partition_closure_established": False})


@dataclass(frozen=True)
class EmploymentCell:
    industry_code: str
    indicator: str
    unit: str
    value: Decimal | None
    lexeme: str | None
    presence: str
    source_status: str | None
    truth_status: str
    metadata: Mapping


@dataclass(frozen=True)
class EmploymentStructureReference:
    _employment: _Cube
    metadata: Mapping
    diagnostics: Mapping

    @property
    def industry_codes(self):
        return tuple(r["employment_nace_r2"] for r in self.metadata["bridge"]["mappings"])

    @property
    def source_dimensions(self):
        return self._employment.dimensions

    def read_cell(self, *, industry_code, indicator, unit):
        _require(industry_code in (*self.industry_codes, "TOTAL") and indicator in INDICATORS and unit in UNITS,
                 "only admitted A64/TOTAL domestic persons and actual hours are readable; aliases and reverse allocation are unsupported")
        cell = _read(self._employment, unit, indicator, industry_code)
        return EmploymentCell(industry_code, indicator, unit, cell.value, cell.lexeme, cell.presence, cell.status,
                              "Q" if cell.value is None else "DER", self.metadata)

    def report(self):
        return _freeze({"metadata": self.metadata, "manifest_sha256": MANIFEST_SHA256,
                        "claim": HISTORICAL_EMPLOYMENT_ATTACHMENT, **self.diagnostics})


def load_employment_structure_reference(source_paths, *, reference_year, units, claim):
    """Read exactly five explicitly mapped originals; documentation stays provenance.

    Document snapshots are qualification evidence pinned in the manifest, not
    reparsed at runtime. The existing industry reader owns IO source admission.
    """
    _require(type(reference_year) is int and reference_year == 2023 and
             isinstance(units, (tuple, list)) and tuple(units) == UNITS and claim == HISTORICAL_EMPLOYMENT_ATTACHMENT,
             "explicit HU2023 THS_PER/THS_HW historical attachment required")
    _require(isinstance(source_paths, Mapping) and set(source_paths) == RUNTIME_SOURCE_IDS,
             "exact explicit five-source mapping required")
    _require(all(isinstance(path, (str, Path)) and bool(str(path)) for path in source_paths.values()), "explicit source paths required")
    manifest_bytes = MANIFEST_PATH.read_bytes()
    _require(hashlib.sha256(manifest_bytes).hexdigest() == MANIFEST_SHA256, "employment manifest identity mismatch")
    manifest = _decode(manifest_bytes)
    _require(manifest["io_manifest_sha256"] == industry.MANIFEST_SHA256, "frozen IO manifest lineage mismatch")
    artifacts = {r["source_id"]: r for r in manifest["source_artifacts"]}
    cubes = {}
    for source_id in (SOURCE_ID, A10_SOURCE_ID, PE_SOURCE_ID, CURRENT_NA_SOURCE_ID):
        raw = Path(source_paths[source_id]).read_bytes()
        artifact, contract = artifacts[source_id], manifest["parser_contracts"][source_id]
        _require(len(raw) == artifact["byte_count"] and hashlib.sha256(raw).hexdigest() == artifact["sha256"],
                 f"external source identity mismatch: {source_id}")
        cube = _parse_cube(raw, contract)
        _require(sum(v is not None for v in cube.values.values()) == contract["numeric_count"] and
                 len(cube.statuses) == contract["status_count"] and all(v is not None for v in cube.values.values()),
                 "source numeric/status coverage changed")
        cubes[source_id] = cube
    io_reference = industry.load_industry_structure_reference(source_paths[industry.SOURCE_ID],
        source_id=industry.SOURCE_ID, reference_year=reference_year, unit="MIO_NAC", claim=industry.HISTORICAL_ACCOUNTING_REFERENCE)
    mappings = manifest["bridge"]["mappings"]
    employment = cubes[SOURCE_ID]
    _require(len(mappings) == 64 and len(io_reference.leaf_codes) == 89, "qualified 64/89 partition required")
    _validate_bridge(mappings, io_reference.leaf_codes, employment.dimensions["nace_r2"]["category"]["index"])
    sectors = tuple(r["employment_nace_r2"] for r in mappings)
    aggregates = _aggregate_io(io_reference, mappings)
    report = _diagnostics(employment, cubes[A10_SOURCE_ID], cubes[PE_SOURCE_ID], cubes[CURRENT_NA_SOURCE_ID], aggregates, sectors)
    _require(report["core_coverage"] == _freeze(manifest["expected_core_coverage"]), "qualified core coverage changed")
    _require(all(report["full_cube"][k] == v for k, v in manifest["expected_full_cube"].items()) and
             report["full_cube"]["explicit_null"] == 0, "qualified full-cube coverage changed")
    _require(all(report["totals"][key] == Decimal(value) for key, value in manifest["expected_totals"].items()), "native total mismatch")
    _require(all(r["residual"] == 0 for r in report["reported_cross_table_controls"]), "reported A10/PE total control mismatch")
    _require(report["current_na_vs_io_mismatch_summary"] == manifest["expected_current_na_vs_io_mismatch_summary"], "accounting snapshot comparison mismatch")
    return EmploymentStructureReference(employment, _freeze(manifest), report)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="append", required=True, help="SOURCE_ID=/explicit/local/original; repeat five times")
    parser.add_argument("--reference-year", required=True, type=int)
    parser.add_argument("--units", nargs=2, required=True)
    parser.add_argument("--claim", required=True)
    args = parser.parse_args(argv)
    try:
        sources = {}
        for binding in args.source:
            source_id, separator, path = binding.partition("=")
            _require(separator and source_id not in sources and path, "unique SOURCE_ID=path bindings required")
            sources[source_id] = path
        reference = load_employment_structure_reference(sources, reference_year=args.reference_year, units=args.units, claim=args.claim)
    except (EmploymentStructureReferenceError, industry.IndustryStructureReferenceError, OSError) as exc:
        parser.exit(2, f"B16 employment reference rejected: {exc}\n")
    print(json.dumps(_plain(reference.report()), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
