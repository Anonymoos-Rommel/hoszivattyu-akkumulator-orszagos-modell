"""Versioned expenditure classifications and historical import-origin ratios.

This is a descriptive handoff, not a monetary spending-vector or GDP engine.
The existing reader admits the exact external HU2023 source. Classification
sources stay private; the reviewed manifest carries their hashes and witnesses.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Mapping

from modules.B16 import industry_structure_reference as industry

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "registry/b16_spending_classification_manifest.json"
MANIFEST_SHA256 = "39242eb63e449b299b1310655144ca03d1782c3ce6c9471b25d47811126461e6"
CLASSIFICATION_CLAIM = "HISTORICAL_STRUCTURE_CLASSIFICATION_REFERENCE"
IMPORT_CLAIM = "HISTORICAL_ORIGIN_USE_RATIO"


class SpendingClassificationError(ValueError):
    """Unsupported classification, source, claim or origin-use grain."""


def _require(condition, message):
    if not condition:
        raise SpendingClassificationError(message)


def _load_manifest():
    raw = MANIFEST_PATH.read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == MANIFEST_SHA256, "classification manifest identity mismatch")
    manifest = industry._decode(raw)
    root = MANIFEST_PATH.parents[1]
    for dependency in manifest["dependencies"]:
        _require(hashlib.sha256((root / dependency["path"]).read_bytes()).hexdigest() == dependency["sha256"],
                 "reviewed historical dependency changed")
    return industry._freeze(manifest)


@dataclass(frozen=True)
class SpendingClassificationReference:
    metadata: Mapping

    @property
    def package_groups(self):
        return self.metadata["package_groups"]

    @property
    def route_ids(self):
        return tuple(route["route_id"] for route in self.metadata["routes"])

    def read_route(self, *, route_id, product_classification, activity_classification):
        _require(product_classification == "CPA2.1" and activity_classification == "NACE Rev.2",
                 "explicit CPA2.1 and NACE Rev.2 basis required; no automatic version conversion")
        matches = [r for r in self.metadata["routes"] if r["route_id"] == route_id]
        _require(len(matches) == 1, "unknown route; named products/invoices require their own qualification")
        return matches[0]

    def read_package(self, *, package_group, product_classification, activity_classification):
        _require(package_group in self.package_groups, "unlisted package remains unresolved")
        routes = [self.read_route(route_id=r["route_id"], product_classification=product_classification,
                                 activity_classification=activity_classification)
                  for r in self.metadata["routes"] if r["package_group"] == package_group]
        return industry._freeze({"package_group": package_group, "conditional_routes": routes,
            "truth_status": "DER", "selected_route": None, "actual_supplier_industry": None,
            "monetary_allocation": None, "classification_proves_actual_purchase": False,
            "selection_rule": self.metadata["package_boundary"]["route_selection"]})

    def report(self):
        return industry._freeze({"claim": CLASSIFICATION_CLAIM, "manifest_sha256": MANIFEST_SHA256,
            "metadata": self.metadata, "programme_calculation_performed": False})


def load_spending_classification_reference(*, claim):
    """Read the fixed qualified catalogue; never classify an arbitrary invoice."""
    _require(claim == CLASSIFICATION_CLAIM, "explicit historical classification claim required")
    return SpendingClassificationReference(_load_manifest())


def _origin_ratio(*, total, imported, domestic):
    """Exact arithmetic for source-native amounts; this helper admits no source."""
    values = (total, imported, domestic)
    _require(all(v is None or type(v) is int for v in values), "integer source-native amounts or explicit absence required")
    if any(v is None for v in values):
        _require(all(v is None for v in values), "asymmetric origin-use missingness")
        status, ratio = "MISSING", None
    else:
        _require(total == domestic + imported, "TOTAL must equal DOM plus IMP")
        if total == 0:
            status, ratio = "UNDEFINED_ZERO_DENOMINATOR", None
        else:
            ratio = Fraction(imported, total)
            status = ("NONNEGATIVE_ORIGIN_SHARE" if total > 0 and imported >= 0 and domestic >= 0
                      else "SIGNED_ACCOUNTING_RATIO")
    return industry._freeze({"total_million_HUF": total, "imported_million_HUF": imported,
        "domestic_million_HUF": domestic, "status": status,
        "truth_status": "Q" if ratio is None else "DER",
        "exact_ratio": None if ratio is None else {"numerator": ratio.numerator, "denominator": ratio.denominator},
        "ratio_unit": "dimensionless", "clamped": False,
        "programme_import_propensity": None})


@dataclass(frozen=True)
class HistoricalImportReference:
    _reference: industry.IndustryStructureReference
    metadata: Mapping

    @property
    def industry_rows(self):
        return (*self._reference.leaf_codes, "TOTAL")

    @property
    def use_columns(self):
        native = self._reference.source_dimensions["ind_use"]["category"]["index"]
        # Existing reviewed source exposes individual leaves and final/control
        # use fields. Overlapping industry parents cannot enter this interface.
        return tuple(code for code in native if code in self._reference.leaf_codes or code in industry._ALL_FINAL_COLUMNS)

    def read_import_ratio(self, *, row, column):
        _require(isinstance(row, str) and row in self.industry_rows,
                 "only nonoverlapping industry leaves or TOTAL use row; no accounting rows")
        _require(isinstance(column, str) and column in self.use_columns,
                 "only industry leaves or named native final/control use columns")
        values = {flow: self._reference.read_cell(row=row, column=column, flow=flow).value
                  for flow in industry.FLOWS}
        ratio = _origin_ratio(total=values["TOTAL"], imported=values["IMP"], domestic=values["DOM"])
        return industry._freeze({"claim": IMPORT_CLAIM, "row": row, "column": column,
            "source_id": industry.SOURCE_ID, "source_sha256": industry.SOURCE_SHA256,
            "source_manifest_sha256": industry.MANIFEST_SHA256,
            "reference_year": 2023, "geography": "HU", "classification": "NACE Rev.2 national ModelD industry-by-industry",
            "price_basis": self._reference.metadata["price_basis"],
            "import_valuation": self._reference.metadata["import_valuation"],
            "denominator": "TOTAL = DOM + IMP for this same named origin-use cell",
            **ratio})

    def report(self):
        counts = {}
        for row in self.industry_rows:
            for col in self.use_columns:
                status = self.read_import_ratio(row=row, column=col)["status"]
                counts[status] = counts.get(status, 0) + 1
        return industry._freeze({"claim": IMPORT_CLAIM, "manifest_sha256": MANIFEST_SHA256,
            "source_id": industry.SOURCE_ID, "source_sha256": industry.SOURCE_SHA256,
            "reference_year": 2023, "row_count": len(self.industry_rows), "column_count": len(self.use_columns),
            "ratio_status_counts": counts, "origin_ratio_contract": self.metadata["origin_ratio_contract"],
            "programme_calculation_performed": False})


def load_historical_import_reference(source_path, *, source_id, reference_year, unit, claim):
    """The fixed official source is re-admitted by its existing canonical reader."""
    _require(claim == IMPORT_CLAIM, "explicit historical origin-use ratio claim required")
    metadata = _load_manifest()
    reference = industry.load_industry_structure_reference(source_path, source_id=source_id,
        reference_year=reference_year, unit=unit, claim=industry.HISTORICAL_ACCOUNTING_REFERENCE)
    return HistoricalImportReference(reference, metadata)
