import csv
import hashlib
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WINTERS = ROOT / "data" / "processed" / "b05_weather_winter_extremes.csv"
BRACKETS = ROOT / "data" / "processed" / "b05_weather_empirical_return_period.csv"
ENVELOPE = ROOT / "data" / "processed" / "b05_weather_empirical_station_envelope.csv"
RAW_MANIFEST = ROOT / "registry" / "b05_p9_hungaromet_raw_acquisition_manifest.csv"
P9_REG = ROOT / "registry" / "b05_p9_empirical_cold_stress_materialization.csv"
DOMAIN = ROOT / "registry" / "b05_p9_cold_stress_product_domain_audit.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
MODULES = ROOT / "registry" / "module_status.csv"
PROBE = ROOT / ".github" / "workflows" / "b05_p9_hungaromet_probe.yml"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P9HistoricalWinterMaterializationTests(unittest.TestCase):
    def test_complete_winter_block_counts_are_exact(self):
        data = rows(WINTERS)
        self.assertEqual(len(data), 104)
        counts = Counter(row["station_id"] for row in data)
        self.assertEqual(
            counts,
            {
                "15310": 23,
                "44527": 23,
                "58102": 23,
                "46304": 23,
                "52744": 12,
            },
        )
        self.assertTrue(
            all(row["expected_hours"] == row["observed_hours"] for row in data)
        )
        self.assertEqual({row["evidence_status"] for row in data}, {"DER"})

    def test_all_five_station_ten_year_brackets_are_materialized(self):
        data = rows(BRACKETS)
        self.assertEqual(len(data), 10)
        self.assertEqual({row["evidence_status"] for row in data}, {"DER"})
        self.assertEqual(
            {row["status"] for row in data},
            {"EMPIRICAL_ORDER_STATISTIC_BRACKET"},
        )
        by = {(row["station_id"], row["metric_id"]): row for row in data}
        expected_72h = {
            "15310": ("-12.376389", "-10.802778", "23"),
            "44527": ("-10.352778", "-10.186111", "23"),
            "58102": ("-11.656944", "-10.304167", "23"),
            "46304": ("-13.331944", "-12.952778", "23"),
            "52744": ("-11.656944", "-9.644444", "12"),
        }
        for station, (cold, warm, n) in expected_72h.items():
            row = by[(station, "WINTER_MIN_72H_MEAN_TA_C")]
            self.assertEqual(row["colder_bound_C"], cold)
            self.assertEqual(row["warmer_bound_C"], warm)
            self.assertEqual(row["complete_winter_blocks"], n)
            self.assertIn("NOT_OFFICIAL_HUNGAROMET_1_IN_10", row["notes"])

    def test_five_station_envelope_is_bounded_and_not_national_weighted(self):
        data = {row["metric_id"]: row for row in rows(ENVELOPE)}
        cold = data["WINTER_MIN_72H_MEAN_TA_C"]
        self.assertEqual(cold["station_count"], "5")
        self.assertEqual(cold["colder_envelope_C"], "-13.331944")
        self.assertEqual(cold["warmer_envelope_C"], "-9.644444")
        self.assertEqual(cold["status"], "PROJECT_STATION_ENVELOPE")
        self.assertIn("no national population", cold["notes"].lower())

    def test_raw_archives_are_pinned_but_not_committed(self):
        data = rows(RAW_MANIFEST)
        self.assertEqual(len(data), 5)
        self.assertEqual({row["raw_repository_status"] for row in data}, {"EXTERNAL_NOT_COMMITTED"})
        self.assertTrue(all(len(row["sha256"]) == 64 for row in data))
        self.assertFalse(any(ROOT.rglob("*.zip")))

    def test_product_domain_audit_quantifies_real_gaps(self):
        by = {row["item_id"]: row for row in rows(DOMAIN)}
        self.assertEqual(
            by["B05-P9-D02"]["status"],
            "STRESS_MEAN_BRACKET_INSIDE_DOMAIN",
        )
        self.assertEqual(
            by["B05-P9-D03"]["status"],
            "INSUFFICIENT_FOR_COLD_STRESS_COHORT",
        )
        self.assertEqual(
            by["B05-P9-D04"]["status"],
            "STRESS_MEAN_BRACKET_BELOW_DOMAIN",
        )
        self.assertIn(
            "MINUS13_331944",
            by["B05-P9-D04"]["residual_gap"],
        )
        self.assertEqual(by["B05-P9-D05"]["status"], "Q")

    def test_q_b05_002_is_resolved_for_model_use(self):
        questions = {row["question_id"]: row for row in rows(QUESTIONS)}
        q2 = questions["Q-B05-002"]
        self.assertEqual(q2["status"], "RESOLVED")
        self.assertIn("RESOLVED_FOR_MODEL_USE", q2["notes"])
        self.assertIn("project-derived empirical historical 10-year stress", q2["notes"].lower())
        self.assertIn("nem official hungaromet 1-in-10", q2["notes"].lower())

        q1 = questions["Q-B05-001"]
        self.assertEqual(q1["status"], "OPEN")
        self.assertIn("OPEN_NARROWED", q1["notes"])
        self.assertIn("-13.331944", q1["notes"])

    def test_weather_subgates_advance_without_module_uplift(self):
        readiness = {row["component_id"]: row for row in rows(READINESS)}
        self.assertEqual(readiness["WEATHER_INPUT"]["readiness_percent"], "75")
        self.assertEqual(readiness["COLD_1_IN_10"]["readiness_percent"], "80")
        self.assertEqual(
            readiness["WEATHER_PERFORMANCE_DOMAIN_COVERAGE"]["readiness_percent"],
            "60",
        )
        modules = {row["module_id"]: row for row in rows(MODULES)}
        self.assertEqual(modules["B05"]["readiness_percent"], "64")
        self.assertIn("B05-P9", modules["B05"]["gate_note"])

    def test_p9_registry_and_temporary_probe_cleanup(self):
        by = {row["item_id"]: row for row in rows(P9_REG)}
        self.assertEqual(by["B05-P9-R02"]["lower_bound"], "104")
        self.assertEqual(
            by["B05-P9-R07"]["status"],
            "RESOLVED_FOR_MODEL_USE",
        )
        self.assertFalse(PROBE.exists())


if __name__ == "__main__":
    unittest.main()
