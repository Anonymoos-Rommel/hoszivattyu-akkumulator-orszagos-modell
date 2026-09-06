import unittest
from pathlib import Path

from modules.B02.emitter_marginal_reconciliation import reconcile_gas_convector_margin


ROOT = Path(__file__).resolve().parents[1]
WBL = ROOT / "data" / "processed" / "b02" / "ksh_wbl_joint_cells_2022.csv"


class B02P30EmitterMarginalReconciliationTests(unittest.TestCase):
    def test_exact_wbl_domain_diagnostic_is_bounded(self):
        result = reconcile_gas_convector_margin(WBL)
        self.assertEqual(result.occupied_dwellings, 4_008_541)
        self.assertGreater(result.wbl_gas_heating_dwellings, 0)
        self.assertGreater(result.wbl_room_gas_dwellings, 0)
        self.assertLessEqual(result.wbl_room_gas_dwellings, result.wbl_gas_heating_dwellings)
        self.assertIn(result.blocker, {None, "ROOM_GAS_DOMAIN_TOO_SMALL", "NONZERO_MARGINAL_RESIDUAL"})
        print(
            "P30_DIAGNOSTIC "
            f"occupied={result.occupied_dwellings} "
            f"gas={result.wbl_gas_heating_dwellings} "
            f"gas_share={result.wbl_gas_share:.12f} "
            f"survey_gas_share={result.survey_gas_share:.12f} "
            f"delta_pp={result.gas_share_delta_pp:.12f} "
            f"room_gas={result.wbl_room_gas_dwellings} "
            f"target_convector={result.target_convector_dwellings:.12f} "
            f"p_room_gas={result.room_gas_probability} "
            f"residual={result.marginal_residual_dwellings} "
            f"reconciled={result.marginal_reconciled} "
            f"blocker={result.blocker}"
        )

    def test_non_room_gas_is_never_auto_classified_as_convector(self):
        result = reconcile_gas_convector_margin(WBL)
        self.assertLessEqual(result.wbl_room_gas_dwellings, result.wbl_gas_heating_dwellings)
        # The module only computes a bounded calibration probability; it does not
        # materialize or promote any WBL emitter row.
        self.assertFalse((ROOT / "data" / "processed" / "b02" / "b02_gas_convector_emitter_assignment_2022.csv").exists())


if __name__ == "__main__":
    unittest.main()
