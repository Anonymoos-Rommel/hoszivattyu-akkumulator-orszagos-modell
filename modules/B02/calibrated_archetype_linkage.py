"""Reproducible public-data calibrated linkage for the B02 occupied stock.

B02-P21 consumes, rather than replaces, the existing canonical inputs:

* the P1-D settlement-type building-type proxy for the 2022 occupied WBL stock;
* the P15 materialized WBL011 full occupied-stock joint; and
* the public KSH 2022 building-type x construction-period energy benchmarks.

The central building-type linkage preserves the occupied settlement-type proxy
margins exactly while using the current KSH 2022 modelled construction-period
family/multi odds only as a within-margin shape.  A flat-within-settlement
scenario is carried in parallel as a structural sensitivity.  Both scenarios
remain model output: building type is ``ASS`` and primary energy is ``MODELLED``.
No output from this module is OBS/DER evidence.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed" / "b02"
DEFAULT_WBL = DATA_DIR / "ksh_wbl_joint_cells_2022.csv"
DEFAULT_PROXY = DATA_DIR / "ksh_building_type_proxy_2022.csv"
DEFAULT_ENERGY = DATA_DIR / "ksh_energy_archetype_benchmarks_2022.csv"

FULL_PROJECTION = "WBL011_FULL_STOCK_JOINT"
EXPECTED_WBL_ROWS = 116_452
EXPECTED_OCCUPIED_DWELLINGS = 4_008_541

BUILDING_MODEL_ID = "B02-P21-PUBLIC-KSH-BUILDING-TYPE-LINKAGE"
ENERGY_MODEL_ID = "B02-P21-PUBLIC-KSH-PRIMARY-ENERGY-LINKAGE"
BUILDING_EVIDENCE_STATUS = "ASS"
ENERGY_EVIDENCE_STATUS = "MODELLED"

# WBL011 has one post-2010 band, while the public KSH energy publication splits
# 2011-2015 and 2016-2022.  P21 combines those two KSH rows by their published
# modelled dwelling counts; all earlier bands map one-to-one.
WBL_TO_KSH_PERIODS = {
    "Y_LT1919": ("1919 előtt",),
    "Y1919-1945": ("1919–1945",),
    "Y1946-1960": ("1946–1960",),
    "Y1961-1980": ("1961–1980",),
    "Y1981-2000": ("1981–2000",),
    "Y2001-2010": ("2001–2010",),
    "Y_GE2011": ("2011–2015", "2016–2022"),
}


@dataclass(frozen=True)
class PeriodBenchmark:
    family_count: int
    multi_count: int
    family_mean_energy: float
    multi_mean_energy: float
    family_odds_ratio: float


@dataclass(frozen=True)
class LinkageSummary:
    row_count: int
    occupied_dwellings: int
    family_target_dwellings: int
    multi_target_dwellings: int
    central_family_expected: float
    flat_family_expected: float
    maximum_settlement_reconciliation_residual: float
    dwelling_weighted_central_primary_energy: float
    dwelling_weighted_flat_primary_energy: float
    dwelling_weighted_structural_energy_delta: float

    def as_dict(self) -> dict[str, object]:
        return {
            "row_count": self.row_count,
            "occupied_dwellings": self.occupied_dwellings,
            "family_target_dwellings": self.family_target_dwellings,
            "multi_target_dwellings": self.multi_target_dwellings,
            "central_family_expected": self.central_family_expected,
            "flat_family_expected": self.flat_family_expected,
            "maximum_settlement_reconciliation_residual": (
                self.maximum_settlement_reconciliation_residual
            ),
            "dwelling_weighted_central_primary_energy": (
                self.dwelling_weighted_central_primary_energy
            ),
            "dwelling_weighted_flat_primary_energy": (
                self.dwelling_weighted_flat_primary_energy
            ),
            "dwelling_weighted_structural_energy_delta": (
                self.dwelling_weighted_structural_energy_delta
            ),
            "building_model_id": BUILDING_MODEL_ID,
            "primary_energy_model_id": ENERGY_MODEL_ID,
            "building_evidence_status": BUILDING_EVIDENCE_STATUS,
            "primary_energy_evidence_status": ENERGY_EVIDENCE_STATUS,
        }


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _weighted_mean(rows: Iterable[dict[str, str]]) -> tuple[int, float]:
    total_count = 0
    weighted_energy = 0.0
    for row in rows:
        count = int(row["published_bin_dwelling_count"])
        energy = float(row["mean_primary_energy_kwh_m2_year"])
        if count < 0 or not math.isfinite(energy) or energy <= 0:
            raise ValueError(f"invalid KSH energy benchmark row: {row!r}")
        total_count += count
        weighted_energy += count * energy
    if total_count <= 0:
        raise ValueError("KSH period benchmark has no positive dwelling count")
    return total_count, weighted_energy / total_count


def build_period_benchmarks(
    energy_rows: list[dict[str, str]],
) -> dict[str, PeriodBenchmark]:
    """Collapse public KSH building-type x age controls to the WBL age bands."""

    keyed: dict[tuple[str, str], dict[str, str]] = {}
    for row in energy_rows:
        if row["evidence_status"] != ENERGY_EVIDENCE_STATUS:
            raise ValueError(f"unexpected energy evidence status: {row!r}")
        key = (row["building_type"], row["construction_period"])
        if key in keyed:
            raise ValueError(f"duplicate KSH energy benchmark: {key!r}")
        keyed[key] = row

    family_total = sum(
        int(row["published_bin_dwelling_count"])
        for row in energy_rows
        if row["building_type"] == "FAMILY_HOUSE"
    )
    multi_total = sum(
        int(row["published_bin_dwelling_count"])
        for row in energy_rows
        if row["building_type"] == "MULTI_DWELLING"
    )
    if family_total <= 0 or multi_total <= 0:
        raise ValueError("KSH national building-type benchmark counts must be positive")
    national_odds = family_total / multi_total

    result: dict[str, PeriodBenchmark] = {}
    for wbl_period, source_periods in WBL_TO_KSH_PERIODS.items():
        family_rows = [keyed[("FAMILY_HOUSE", period)] for period in source_periods]
        multi_rows = [keyed[("MULTI_DWELLING", period)] for period in source_periods]
        family_count, family_energy = _weighted_mean(family_rows)
        multi_count, multi_energy = _weighted_mean(multi_rows)
        period_odds = family_count / multi_count
        result[wbl_period] = PeriodBenchmark(
            family_count=family_count,
            multi_count=multi_count,
            family_mean_energy=family_energy,
            multi_mean_energy=multi_energy,
            family_odds_ratio=period_odds / national_odds,
        )

    if set(result) != set(WBL_TO_KSH_PERIODS):
        raise ValueError("incomplete WBL/KSH construction-period benchmark map")
    return result


def _proxy_targets(
    proxy_rows: list[dict[str, str]],
) -> tuple[dict[str, int], dict[str, int]]:
    family: dict[str, int] = {}
    totals: dict[str, int] = {}
    for row in proxy_rows:
        if row["evidence_status"] != BUILDING_EVIDENCE_STATUS:
            raise ValueError(f"building proxy must remain ASS: {row!r}")
        code = row["wbl_settlement_code"]
        total = int(row["wbl_2022_occupied_dwellings"])
        previous = totals.setdefault(code, total)
        if previous != total:
            raise ValueError(f"settlement proxy total drift for {code}")
        if row["canonical_building_type"] == "FAMILY_HOUSE":
            family[code] = int(row["proxy_2022_dwelling_count"])
    if set(family) != set(totals):
        raise ValueError("building proxy is missing a family-house settlement target")
    return family, totals


def _probability(scale: float, age_factor: float) -> float:
    if scale <= 0:
        return 0.0
    product = scale * age_factor
    if not math.isfinite(product) or product > 1e300:
        return 1.0
    return product / (1.0 + product)


def _solve_settlement_scale(
    rows: list[dict[str, object]],
    target_family: int,
    benchmarks: dict[str, PeriodBenchmark],
) -> float:
    total = sum(int(row["dwelling_count"]) for row in rows)
    if target_family < 0 or target_family > total:
        raise ValueError("family target lies outside settlement dwelling universe")
    if target_family == 0:
        return 0.0
    if target_family == total:
        return math.inf

    def expected(scale: float) -> float:
        return sum(
            int(row["dwelling_count"])
            * _probability(
                scale,
                benchmarks[str(row["construction_period_code"])].family_odds_ratio,
            )
            for row in rows
        )

    low = 0.0
    high = 1.0
    while expected(high) < target_family:
        high *= 2.0
        if high > 1e15:
            raise ValueError("unable to bracket settlement odds-raking solution")

    # Deterministic bisection is sufficient because expected(scale) is strictly
    # monotonic for every positive-count WBL row.
    for _ in range(100):
        mid = (low + high) / 2.0
        if expected(mid) < target_family:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def build_calibrated_linkage(
    *,
    wbl_path: Path = DEFAULT_WBL,
    proxy_path: Path = DEFAULT_PROXY,
    energy_path: Path = DEFAULT_ENERGY,
) -> tuple[list[dict[str, object]], LinkageSummary]:
    """Bind building type and primary energy to every committed WBL full-joint row.

    Central scenario:
      settlement-specific occupied building-type margins from P1-D are preserved
      exactly in expectation; 2022 KSH modelled age-specific family/multi odds
      provide the only within-settlement shape.

    Structural sensitivity:
      the same settlement margins are spread flat across construction periods.
      The difference between central and flat is propagated through the primary-
      energy mixture and exposed as a per-cell min/max envelope.  This envelope
      is a structural scenario range, not a statistical confidence interval.
    """

    raw_wbl = _read_csv(wbl_path)
    wbl_rows: list[dict[str, object]] = []
    for row in raw_wbl:
        if row["projection_id"] != FULL_PROJECTION:
            continue
        if row["evidence_status"] != "OBS":
            raise ValueError(f"full-joint WBL input must be numeric OBS: {row!r}")
        count = int(row["dwelling_count"])
        if count <= 0:
            raise ValueError(f"full-joint WBL row must have positive count: {row!r}")
        period = row["construction_period_code"]
        if period not in WBL_TO_KSH_PERIODS:
            raise ValueError(f"unmapped WBL construction period: {period!r}")
        wbl_rows.append(
            {
                "cell_id": row["cell_id"],
                "settlement_type_code": row["settlement_type_code"],
                "construction_period_code": period,
                "dwelling_count": count,
            }
        )

    if len(wbl_rows) != EXPECTED_WBL_ROWS:
        raise ValueError(
            f"WBL full-joint row-count drift: expected={EXPECTED_WBL_ROWS} "
            f"actual={len(wbl_rows)}"
        )
    occupied_total = sum(int(row["dwelling_count"]) for row in wbl_rows)
    if occupied_total != EXPECTED_OCCUPIED_DWELLINGS:
        raise ValueError(
            f"WBL occupied total drift: expected={EXPECTED_OCCUPIED_DWELLINGS} "
            f"actual={occupied_total}"
        )

    proxy_family, proxy_totals = _proxy_targets(_read_csv(proxy_path))
    benchmarks = build_period_benchmarks(_read_csv(energy_path))

    rows_by_settlement: dict[str, list[dict[str, object]]] = {}
    for row in wbl_rows:
        rows_by_settlement.setdefault(str(row["settlement_type_code"]), []).append(row)
    if set(rows_by_settlement) != set(proxy_totals):
        raise ValueError("WBL settlement codes do not match the canonical P1-D proxy")

    scales: dict[str, float] = {}
    flat_probabilities: dict[str, float] = {}
    for code, rows in rows_by_settlement.items():
        actual_total = sum(int(row["dwelling_count"]) for row in rows)
        if actual_total != proxy_totals[code]:
            raise ValueError(
                f"WBL/proxy settlement total drift for {code}: "
                f"wbl={actual_total} proxy={proxy_totals[code]}"
            )
        scales[code] = _solve_settlement_scale(rows, proxy_family[code], benchmarks)
        flat_probabilities[code] = proxy_family[code] / actual_total

    output: list[dict[str, object]] = []
    central_family_by_settlement = {code: 0.0 for code in rows_by_settlement}
    flat_family_by_settlement = {code: 0.0 for code in rows_by_settlement}
    central_energy_weighted = 0.0
    flat_energy_weighted = 0.0
    structural_energy_delta_weighted = 0.0

    for row in wbl_rows:
        code = str(row["settlement_type_code"])
        period = str(row["construction_period_code"])
        count = int(row["dwelling_count"])
        benchmark = benchmarks[period]

        central_p = _probability(scales[code], benchmark.family_odds_ratio)
        flat_p = flat_probabilities[code]
        probability_low = min(central_p, flat_p)
        probability_high = max(central_p, flat_p)

        central_family = count * central_p
        flat_family = count * flat_p
        central_family_by_settlement[code] += central_family
        flat_family_by_settlement[code] += flat_family

        central_energy = (
            central_p * benchmark.family_mean_energy
            + (1.0 - central_p) * benchmark.multi_mean_energy
        )
        flat_energy = (
            flat_p * benchmark.family_mean_energy
            + (1.0 - flat_p) * benchmark.multi_mean_energy
        )
        energy_low = min(central_energy, flat_energy)
        energy_high = max(central_energy, flat_energy)
        central_energy_weighted += count * central_energy
        flat_energy_weighted += count * flat_energy
        structural_energy_delta_weighted += count * abs(central_energy - flat_energy)

        output.append(
            {
                "cell_id": row["cell_id"],
                "settlement_type_code": code,
                "construction_period_code": period,
                "dwelling_count": count,
                "central_family_probability": central_p,
                "flat_family_probability": flat_p,
                "family_probability_low": probability_low,
                "family_probability_high": probability_high,
                "central_family_expected_dwellings": central_family,
                "central_multi_expected_dwellings": count - central_family,
                "central_primary_energy_kwh_m2_year": central_energy,
                "flat_primary_energy_kwh_m2_year": flat_energy,
                "primary_energy_low_kwh_m2_year": energy_low,
                "primary_energy_high_kwh_m2_year": energy_high,
                "building_type_model_id": BUILDING_MODEL_ID,
                "primary_energy_model_id": ENERGY_MODEL_ID,
                "building_type_evidence_status": BUILDING_EVIDENCE_STATUS,
                "primary_energy_evidence_status": ENERGY_EVIDENCE_STATUS,
                "uncertainty_basis": "AGE_SHAPED_VS_FLAT_WITHIN_SETTLEMENT",
            }
        )

    maximum_residual = 0.0
    for code in rows_by_settlement:
        central_residual = central_family_by_settlement[code] - proxy_family[code]
        flat_residual = flat_family_by_settlement[code] - proxy_family[code]
        maximum_residual = max(maximum_residual, abs(central_residual), abs(flat_residual))
    if maximum_residual > 1e-5:
        raise ValueError(f"building-type marginal reconciliation failed: {maximum_residual}")

    family_target = sum(proxy_family.values())
    summary = LinkageSummary(
        row_count=len(output),
        occupied_dwellings=occupied_total,
        family_target_dwellings=family_target,
        multi_target_dwellings=occupied_total - family_target,
        central_family_expected=sum(central_family_by_settlement.values()),
        flat_family_expected=sum(flat_family_by_settlement.values()),
        maximum_settlement_reconciliation_residual=maximum_residual,
        dwelling_weighted_central_primary_energy=central_energy_weighted / occupied_total,
        dwelling_weighted_flat_primary_energy=flat_energy_weighted / occupied_total,
        dwelling_weighted_structural_energy_delta=(
            structural_energy_delta_weighted / occupied_total
        ),
    )
    return output, summary


def write_linkage_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("cannot materialize an empty linkage")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_DIR / "b02_calibrated_archetype_linkage_2022.csv",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=DATA_DIR / "b02_calibrated_archetype_linkage_summary_2022.json",
    )
    args = parser.parse_args()

    rows, summary = build_calibrated_linkage()
    write_linkage_csv(args.output, rows)
    args.summary.write_text(
        json.dumps(summary.as_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "VALID: B02-P21 calibrated linkage "
        f"rows={summary.row_count} occupied={summary.occupied_dwellings} "
        f"family={summary.family_target_dwellings} "
        f"multi={summary.multi_target_dwellings} "
        f"max_reconciliation_residual={summary.maximum_settlement_reconciliation_residual:.3g}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
