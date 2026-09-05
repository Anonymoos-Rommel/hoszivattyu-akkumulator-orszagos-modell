from dataclasses import replace
from pathlib import Path
import csv
import unittest

from modules.B02.construction_period_bridge import (
    EXPECTED_ENERGY_BINS,
    OUTPUT_EVIDENCE_STATUS,
    SOURCE_EVIDENCE_STATUS,
    SOURCE_PERIODS,
    TARGET_PERIOD,
    EnergyDistributionRecord,
    bridge_y_ge2011,
    dwelling_totals_by_building_type,
)


ROOT = Path(__file__).resolve().parents[1]
DISTRIBUTION = ROOT / "data/processed/b02/ksh_energy_distribution_2022.csv"
BENCHMARKS = ROOT / "data/processed/b02/ksh_energy_archetype_benchmarks_2022.csv"
CONTRACT = ROOT / "registry/b02_construction_period_bridge.csv"
OPEN_QUESTIONS = ROOT / "registry/open_questions.csv"
DOC = ROOT / "docs/source_packs/B02_P7_CONSTRUCTION_PERIOD_BRIDGE.md"


class B02P7ConstructionPeriodBridgeTests(unittest.TestCase):
    def _source_records(self):
        rows = []
        with DISTRIBUTION.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row["construction_period"] not in SOURCE_PERIODS:
                    continue
                rows.append(
                    EnergyDistributionRecord(
                        building_type=row["building_type"],
                        construction_period=row["construction_period"],
                        energy_bin_kwh_m2_year=int(row["published_energy_bin_kwh_m2_year"]),
                        dwelling_count=int(row["dwelling_count"]),
                        evidence_status=row["evidence_status"],
                    )
                )
        return rows

    def test_canonical_source_panel_is_complete(self):
        records = self._source_records()
        self.assertEqual(236, len(records))
        self.assertEqual({SOURCE_EVIDENCE_STATUS}, {row.evidence_status for row in records})
        for building_type in ("FAMILY_HOUSE", "MULTI_DWELLING"):
            for period in SOURCE_PERIODS:
                bins = {
                    row.energy_bin_kwh_m2_year
                    for row in records
                    if row.building_type == building_type
                    and row.construction_period == period
                }
                self.assertEqual(set(EXPECTED_ENERGY_BINS), bins)

    def test_bridge_preserves_building_type_and_energy_bin_grain(self):
        bridged = bridge_y_ge2011(self._source_records())
        self.assertEqual(118, len(bridged))
        self.assertEqual({TARGET_PERIOD}, {row.construction_period for row in bridged})
        self.assertEqual({OUTPUT_EVIDENCE_STATUS}, {row.evidence_status for row in bridged})
        self.assertEqual({SOURCE_EVIDENCE_STATUS}, {row.source_evidence_status for row in bridged})
        self.assertEqual(
            {"FAMILY_HOUSE", "MULTI_DWELLING"},
            {row.building_type for row in bridged},
        )

    def test_exact_2011_plus_totals_match_benchmark_source(self):
        bridged = bridge_y_ge2011(self._source_records())
        totals = dwelling_totals_by_building_type(bridged)
        self.assertEqual(147922, totals["FAMILY_HOUSE"])
        self.assertEqual(85074, totals["MULTI_DWELLING"])
        self.assertEqual(232996, sum(totals.values()))

        benchmark_totals = {"FAMILY_HOUSE": 0, "MULTI_DWELLING": 0}
        with BENCHMARKS.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row["construction_period"] in SOURCE_PERIODS:
                    benchmark_totals[row["building_type"]] += int(
                        row["published_bin_dwelling_count"]
                    )
        self.assertEqual(totals, benchmark_totals)

    def test_every_derived_bin_is_exact_sum_of_the_two_source_periods(self):
        records = self._source_records()
        source = {
            (row.building_type, row.construction_period, row.energy_bin_kwh_m2_year): row.dwelling_count
            for row in records
        }
        for row in bridge_y_ge2011(records):
            expected = sum(
                source[(row.building_type, period, row.energy_bin_kwh_m2_year)]
                for period in SOURCE_PERIODS
            )
            self.assertEqual(expected, row.dwelling_count)

    def test_missing_or_duplicate_source_row_fails_closed(self):
        records = self._source_records()
        with self.assertRaises(ValueError):
            bridge_y_ge2011(records[:-1])
        with self.assertRaises(ValueError):
            bridge_y_ge2011(records + [records[0]])

    def test_non_modelled_source_or_negative_count_fails_closed(self):
        records = self._source_records()
        bad_status = list(records)
        bad_status[0] = replace(bad_status[0], evidence_status="OBS")
        with self.assertRaises(ValueError):
            bridge_y_ge2011(bad_status)

        bad_count = list(records)
        bad_count[0] = replace(bad_count[0], dwelling_count=-1)
        with self.assertRaises(ValueError):
            bridge_y_ge2011(bad_count)

    def test_machine_contract_forbids_join_and_obs_upgrade(self):
        with CONTRACT.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("Y_GE2011", row["target_code"])
        self.assertEqual("MODELLED", row["source_evidence_status"])
        self.assertEqual("DER", row["output_evidence_status"])
        self.assertEqual("no", row["can_join_wbl_building_type"])
        self.assertEqual("no", row["can_upgrade_to_obs"])
        self.assertEqual("OPEN", row["q_b02_002_effect"])

    def test_q_b02_002_remains_open(self):
        with OPEN_QUESTIONS.open(encoding="utf-8", newline="") as handle:
            questions = {row["question_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual("OPEN", questions["Q-B02-002"]["status"])

    def test_source_pack_freezes_non_inference_boundary(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "AGE-BIN HARMONIZATION != BUILDING-TYPE JOIN != OBSERVATION UPGRADE",
            "147,922",
            "85,074",
            "232,996",
            "Q-B02-002` remains **OPEN**",
            "No readiness uplift",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
