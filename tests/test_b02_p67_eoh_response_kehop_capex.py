import csv
import unittest
from pathlib import Path

from modules.B02.foreign_response_authority import (
    ForeignResponseEnvelope,
    OfficialCostCeiling,
    Q,
    QUALIFIED_OFFICIAL_UPPER_BOUND,
    QUALIFIED_VALIDATION_ONLY,
    assess_cost_use,
    assess_hungarian_use,
    validate_foreign_response_envelope,
    validate_official_cost_ceiling,
)

ROOT = Path(__file__).resolve().parents[1]
RESP = ROOT / "registry" / "b02_p67_eoh_response_envelope.csv"
COST = ROOT / "registry" / "b02_p67_kehop_cost_ceiling.csv"
STATUS = ROOT / "registry" / "b02_p67_authority_status.csv"
OPEN_Q = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"


def read_rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B02P67EohResponseKehopCapexTests(unittest.TestCase):
    def test_eoh_installed_cohort_reconciles_to_official_total(self):
        rows = read_rows(RESP, "scope_id")
        all_row = rows["EOH-ALL"]
        self.assertEqual(all_row["installed_n"], "742")
        self.assertEqual(all_row["emitter_measure_n"], "689")
        self.assertAlmostEqual(float(all_row["emitter_measure_share"]), 689 / 742, places=6)
        self.assertEqual(all_row["population_use"], "NO_HUNGARIAN_PREVALENCE")

    def test_foreign_response_envelope_validates_but_is_not_hungarian_weight(self):
        row = ForeignResponseEnvelope(
            source_country="GB",
            scope_id="EOH-ALL",
            installed_n=742,
            emitter_measure_n=689,
            emitter_measure_share=689 / 742,
            emitter_units_p10=3,
            emitter_units_p50=9,
            emitter_units_p90=13,
            mean_sh_flow_c_p10=31.986,
            mean_sh_flow_c_p50=37.84,
            mean_sh_flow_c_p90=44.106,
            spfh4_p10=2.172,
            spfh4_p50=2.747,
            spfh4_p90=3.316,
        )
        self.assertEqual(validate_foreign_response_envelope(row).status, QUALIFIED_VALIDATION_ONLY)
        blocked = assess_hungarian_use(row, requested_use="HUNGARIAN_POPULATION_PREVALENCE")
        self.assertEqual(blocked.status, Q)
        self.assertIn("FOREIGN_FREQUENCY_NOT_HUNGARIAN_WEIGHT", blocked.blockers)

    def test_p66_action_use_requires_crosswalk_and_hungarian_reweighting(self):
        row = ForeignResponseEnvelope(
            "GB", "EOH-ALL", 742, 689, 689 / 742, 3, 9, 13,
            31.986, 37.84, 44.106, 2.172, 2.747, 3.316,
        )
        blocked = assess_hungarian_use(row, requested_use="P66_ACTION_OUTCOME")
        self.assertEqual(blocked.status, Q)
        self.assertIn("NO_HUNGARIAN_P21_REWEIGHTING_AUTHORITY", blocked.blockers)
        self.assertIn("NO_P66_ACTION_CROSSWALK", blocked.blockers)

    def test_kehop_cost_ceiling_is_exact_upper_bound_authority(self):
        rows = read_rows(COST, "cost_id")
        radiator = rows["KEHOP-EMITTER-PACKAGE"]
        self.assertEqual(radiator["material_max_huf"], "1422400")
        self.assertEqual(radiator["labour_max_huf"], "2133600")
        self.assertEqual(radiator["total_max_huf"], "3556000")
        hp = rows["KEHOP-AWHP-SYSTEM"]
        self.assertEqual(int(hp["material_max_huf"]) + int(hp["labour_max_huf"]), int(hp["total_max_huf"]))
        self.assertEqual(hp["total_max_huf"], "8551847")

    def test_cost_ceiling_cannot_be_promoted_to_market_typical(self):
        ceiling = OfficialCostCeiling(
            "KEHOP-EMITTER-PACKAGE", 1422400, 2133600, 3556000, "Ft/készlet"
        )
        self.assertEqual(validate_official_cost_ceiling(ceiling).status, QUALIFIED_OFFICIAL_UPPER_BOUND)
        self.assertEqual(assess_cost_use(ceiling, requested_use="PROGRAMME_COST_UPPER_BOUND").status, QUALIFIED_OFFICIAL_UPPER_BOUND)
        blocked = assess_cost_use(ceiling, requested_use="MARKET_TYPICAL")
        self.assertEqual(blocked.status, Q)
        self.assertIn("OFFICIAL_MAXIMUM_IS_NOT_MARKET_DISTRIBUTION", blocked.blockers)

    def test_authority_status_keeps_transfer_residual_explicit(self):
        rows = read_rows(STATUS, "authority_id")
        self.assertEqual(rows["B02-P67-A01"]["status"], "QUALIFIED_FOREIGN_RESPONSE_ENVELOPE")
        self.assertEqual(rows["B02-P67-A05"]["status"], "QUALIFIED_OFFICIAL_UPPER_BOUND")
        self.assertIn("P66_ACTION_CROSSWALK", rows["B02-P67-A07"]["residual_gap"])
        self.assertIn("P21_HUNGARIAN_REWEIGHTING", rows["B02-P67-A07"]["residual_gap"])

    def test_q_b02_004_and_readiness_remain_open(self):
        questions = read_rows(OPEN_Q, "question_id")
        q4 = questions["Q-B02-004"]
        self.assertEqual(q4["status"], "OPEN")
        self.assertIn("B02-P67", q4["notes"])
        self.assertIn("P66_ACTION_CROSSWALK", q4["notes"])
        self.assertIn("P21_HUNGARIAN_REWEIGHTING", q4["notes"])
        modules = read_rows(MODULE_STATUS, "module_id")
        self.assertEqual(modules["B02"]["readiness_percent"], "55")
        self.assertIn("B02-P67", modules["B02"]["gate_note"])


if __name__ == "__main__":
    unittest.main()
