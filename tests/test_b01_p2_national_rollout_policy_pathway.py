from pathlib import Path
import csv
import unittest

from modules.B01.national_rollout_pathway import (
    B01RolloutError,
    CAPACITY_LIMITED,
    HORIZON_MAX_YEARS,
    HORIZON_MIN_YEARS,
    LINEAR,
    LOGISTIC,
    NATIONAL_SELECTION_READY,
    POLICY_TARGET_BASELINE_HOUSEHOLDS,
    POLICY_TARGET_MAX_HOUSEHOLDS,
    Q_UPSTREAM_EVIDENCE,
    REPORT_POINTS_YEARS,
    NationalSelectionGate,
    RolloutScenario,
    assess_national_selection_gate,
    build_rollout_pathway,
    report_points,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/b01_national_rollout_policy_contract.csv"
DOC = ROOT / "docs/source_packs/B01_P2_NATIONAL_ROLLOUT_POLICY_PATHWAY.md"


class B01P2NationalRolloutPolicyPathwayTests(unittest.TestCase):
    def scenario(self, **changes):
        values = {
            "scenario_id": "SCN-B01-P2-BASE",
            "start_year": 2027,
            "horizon_years": 15,
            "policy_target_households": POLICY_TARGET_BASELINE_HOUSEHOLDS,
            "profile": LINEAR,
            "target_status": "POL",
            "source_refs": ("docs/source_packs/P1A_B01_B04.md",),
        }
        values.update(changes)
        return RolloutScenario(**values)

    def test_canonical_policy_envelope_is_exact(self):
        self.assertEqual(2_000_000, POLICY_TARGET_BASELINE_HOUSEHOLDS)
        self.assertEqual(2_500_000, POLICY_TARGET_MAX_HOUSEHOLDS)
        self.assertEqual(8, HORIZON_MIN_YEARS)
        self.assertEqual(25, HORIZON_MAX_YEARS)
        self.assertEqual((12, 15, 20), REPORT_POINTS_YEARS)

    def test_linear_path_is_monotone_conserves_flow_and_closes_target(self):
        rows = build_rollout_pathway(self.scenario())
        self.assertEqual(15, len(rows))
        self.assertEqual(2_000_000, rows[-1].cumulative_households)
        self.assertEqual(0, rows[-1].unmet_policy_target)
        self.assertEqual(2_000_000, sum(row.new_households for row in rows))
        cumulative = [row.cumulative_households for row in rows]
        self.assertEqual(cumulative, sorted(cumulative))
        self.assertTrue(all(row.evidence_status == "SCN" for row in rows))

    def test_logistic_requires_explicit_shape_and_closes_target(self):
        with self.assertRaises(B01RolloutError):
            build_rollout_pathway(self.scenario(profile=LOGISTIC))
        rows = build_rollout_pathway(
            self.scenario(
                profile=LOGISTIC,
                logistic_midpoint_fraction=0.55,
                logistic_steepness=9.0,
            )
        )
        self.assertEqual(2_000_000, rows[-1].cumulative_households)
        self.assertEqual(0, rows[-1].unmet_policy_target)
        self.assertTrue(all(b.cumulative_households >= a.cumulative_households for a, b in zip(rows, rows[1:])))

    def test_capacity_limited_requires_full_explicit_path_and_can_leave_unmet_target(self):
        with self.assertRaises(B01RolloutError):
            build_rollout_pathway(
                self.scenario(profile=CAPACITY_LIMITED, annual_capacity_households=(100_000,) * 14)
            )
        rows = build_rollout_pathway(
            self.scenario(profile=CAPACITY_LIMITED, annual_capacity_households=(100_000,) * 15)
        )
        self.assertEqual(1_500_000, rows[-1].cumulative_households)
        self.assertEqual(500_000, rows[-1].unmet_policy_target)
        self.assertEqual(1_500_000, sum(row.new_households for row in rows))

    def test_report_points_are_only_12_15_20_when_present(self):
        rows = build_rollout_pathway(self.scenario(horizon_years=20))
        self.assertEqual((12, 15, 20), tuple(row.plan_year_index for row in report_points(rows)))
        short = build_rollout_pathway(self.scenario(horizon_years=12))
        self.assertEqual((12,), tuple(row.plan_year_index for row in report_points(short)))

    def test_target_and_horizon_outside_policy_envelope_fail(self):
        with self.assertRaises(B01RolloutError):
            build_rollout_pathway(self.scenario(policy_target_households=2_500_001))
        with self.assertRaises(B01RolloutError):
            build_rollout_pathway(self.scenario(horizon_years=7))
        with self.assertRaises(B01RolloutError):
            build_rollout_pathway(self.scenario(horizon_years=26))

    def test_real_national_selection_gate_fails_closed_on_current_missing_upstreams(self):
        gate = NationalSelectionGate(
            technically_eligible_stock=None,
            technically_eligible_status="Q",
            real_annual_capacity_status="Q",
            target_definition_status="Q",
            source_refs=("Q-B01-001", "B02_NATIONAL_ELIGIBLE_STOCK", "REAL_ANNUAL_CAPACITY_PATH"),
        )
        self.assertEqual(Q_UPSTREAM_EVIDENCE, assess_national_selection_gate(gate))

    def test_real_national_selection_gate_can_only_open_with_real_or_derived_evidence(self):
        gate = NationalSelectionGate(
            technically_eligible_stock=2_100_000,
            technically_eligible_status="DER",
            real_annual_capacity_status="OBS",
            target_definition_status="DER",
            source_refs=("SRC-ELIGIBLE", "SRC-CAPACITY", "SRC-TARGET-DEFINITION"),
        )
        self.assertEqual(NATIONAL_SELECTION_READY, assess_national_selection_gate(gate))
        self.assertEqual(
            Q_UPSTREAM_EVIDENCE,
            assess_national_selection_gate(
                NationalSelectionGate(
                    technically_eligible_stock=2_100_000,
                    technically_eligible_status="DER",
                    real_annual_capacity_status="OBS",
                    target_definition_status="POL",
                    source_refs=("SRC-ELIGIBLE", "SRC-CAPACITY", "POL-TARGET"),
                )
            ),
        )

    def test_registry_and_document_freeze_no_overclaim_boundaries(self):
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("2000000", row["baseline_target_households"])
        self.assertEqual("SCN", row["pathway_output_status"])
        self.assertEqual("Q_UPSTREAM_EVIDENCE", row["national_selection_status"])
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "POLICY TARGET != TECHNICALLY ELIGIBLE STOCK != REAL ANNUAL CAPACITY != REAL SELECTED HOUSEHOLDS",
            "EXECUTABLE NATIONAL POLICY PATHWAY != REAL NATIONAL PROGRAMME SELECTION",
            "OPERATIONALLY_COMPLETE_WITH_DISCLOSED_RESIDUAL",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
