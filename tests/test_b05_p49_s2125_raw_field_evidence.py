import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p49_s2125_raw_field_evidence.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
MODULES = ROOT / "registry" / "module_status.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P49_S2125_RAW_FIELD_EVIDENCE.md"

def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))

class B05P49S2125RawFieldEvidenceTests(unittest.TestCase):
    def test_exact_external_raw_hashes_are_pinned(self):
        r = {row["claim"]: row for row in rows(REG)}
        self.assertEqual("01736c38535b25030800bd2fba12a54f5ddc676304c3458573be1950e8664d92", r["RAW_ARCHIVE"]["value"])
        self.assertEqual("ca79f165777f3626d68def05fda3331678bc73fa29371e74a2530ccc4d850440", r["NIBE_RAW_MEMBER"]["value"])
        self.assertEqual("a3b6e88a9e2783c35511096192aee1a5aef58b57a9a1b40c9a1eff93e55a4456", r["VICTRON_RAW_MEMBER"]["value"])
        self.assertTrue(all(row["status"] == "ACQUIRED_EXTERNAL_ONLY" for row in (r["RAW_ARCHIVE"], r["NIBE_RAW_MEMBER"], r["VICTRON_RAW_MEMBER"])))

    def test_direct_defrost_join_is_bounded_not_penalty(self):
        r = {row["claim"]: row for row in rows(REG)}
        self.assertEqual("381", r["ACTIVE_DEFROST_STATE_RUNS"]["value"])
        self.assertEqual("22", r["PASSIVE_DEFROST_STATE_RUNS"]["value"])
        self.assertEqual("99.3757", r["ACTIVE_DEFROST_VICTRON_TIME_COVERAGE"]["value"])
        self.assertEqual("0.298304", r["ACTIVE_DEFROST_MEASURED_COVERED_ELECTRIC_ENERGY"]["value"])
        self.assertIn("CALL_DEFROST_PENALTY", r["ACTIVE_DEFROST_MEASURED_COVERED_ELECTRIC_ENERGY"]["forbidden_use"])

    def test_acquisition_slice_does_not_mechanically_uplift_readiness(self):
        ready = {row["component_id"]: row for row in rows(READINESS)}
        self.assertGreaterEqual(int(ready["DEFROST"]["readiness_percent"]), 20)
        self.assertIn("P54 performs the deferred successor-aware recalibration", ready["DEFROST"]["notes"])
        self.assertEqual("45", ready["PART_LOAD_MODULATION"]["readiness_percent"])
        self.assertEqual("64", {row["module_id"]: row for row in rows(MODULES)}["B05"]["readiness_percent"])
        reg = {row["claim"]: row for row in rows(REG)}
        self.assertEqual("NO_MECHANICAL_UPLIFT", reg["DEFROST_READINESS"]["status"])
        self.assertEqual("NO_MECHANICAL_UPLIFT", reg["PART_LOAD_MODULATION_READINESS"]["status"])
        self.assertEqual("NO_MECHANICAL_UPLIFT", reg["B05_READINESS"]["status"])

    def test_questions_remain_e2_not_falsely_closed(self):
        q = {row["question_id"]: row for row in rows(QUESTIONS)}
        self.assertEqual("OPEN", q["Q-B05-003"]["status"])
        self.assertIn("RESOLVED_FOR_THIS_EXACT_SYSTEM", q["Q-B05-003"]["notes"])
        self.assertIn("MATCHED_DEFROST_PENALTY", q["Q-B05-003"]["notes"])
        self.assertEqual("OPEN", q["Q-B05-004"]["status"])
        self.assertIn("PRODUCT_OR_LAB_TRANSIENT_TEST_RECORD_REQUIRED", q["Q-B05-004"]["notes"])

    def test_cotimed_series_becomes_obs_but_full_event_energy_stays_q(self):
        v = {row["variable_id"]: row for row in rows(VARIABLES)}
        self.assertEqual("Q", v["VAR-B05-NIBE-DEFROST-COTIMED-EVENT-SERIES"]["status"])
        self.assertEqual("OBS", v["VAR-B05-S2125-P49-COTIMED-RAW-SERIES"]["status"])
        self.assertEqual("Q", v["VAR-B05-NIBE-DEFROST-EVENT-ENERGY"]["status"])
        self.assertEqual("DER", v["VAR-B05-S2125-P49-DEFROST-ELECTRIC-WINDOW"]["status"])
        self.assertEqual("OBS", v["VAR-B05-S2125-P49-FIELD-CYCLING-OBS"]["status"])

    def test_source_registered_without_raw_or_secret(self):
        src = {row["source_id"]: row for row in rows(SOURCES)}["SRC-B05-P49-SVENPAUSH-S2125-RAW-FIELD-2026"]
        self.assertEqual("OBS", src["evidence_status"])
        self.assertEqual("not stored", src["local_snapshot_status"])
        self.assertIn("public redistribution/reuse not established", src["license_status"])
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("EXTERNAL_ONLY", text)
        self.assertIn("No temporary transfer URL, password", text)

    def test_raw_archive_is_not_committed(self):
        forbidden={"nibe_daten_jan_maerz_2026.tar.xz","nibe_alle_daten_jan_maerz_2026.csv","nibe_energie_jan_maerz_2026.csv"}
        committed={p.name for p in ROOT.rglob("*") if p.is_file()}
        self.assertTrue(forbidden.isdisjoint(committed))

if __name__ == "__main__":
    unittest.main()
