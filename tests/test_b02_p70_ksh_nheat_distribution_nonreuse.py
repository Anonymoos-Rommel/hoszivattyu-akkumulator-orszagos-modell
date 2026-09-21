import unittest

from modules.B02.distribution_nonreuse_assignment import (
    CENTRAL_HYDRONIC_AWHP,
    Q,
    assess_programme_route,
    build_distribution_nonreuse_assignment,
)


class B02P70KshNheatDistributionNonreuseTests(unittest.TestCase):
    def test_route_is_explicitly_bounded(self):
        self.assertEqual(
            assess_programme_route(CENTRAL_HYDRONIC_AWHP).status,
            "QUALIFIED",
        )
        blocked = assess_programme_route("AIR_TO_AIR_HEAT_PUMP")
        self.assertEqual(blocked.status, Q)
        self.assertIn(
            "P70_ONLY_AUTHORIZES_CENTRAL_HYDRONIC_AWHP_ROUTE",
            blocked.blockers,
        )

    def test_p22_nheat_is_exact_runtime_population_control(self):
        a = build_distribution_nonreuse_assignment()
        self.assertEqual(a.occupied_dwellings, 4_008_541)
        self.assertGreater(a.room_by_room_or_no_heat_dwellings, 0)
        self.assertLess(a.room_by_room_or_no_heat_dwellings, a.occupied_dwellings)
        self.assertAlmostEqual(
            a.room_by_room_or_no_heat_share,
            a.room_by_room_or_no_heat_dwellings / a.occupied_dwellings,
        )
        print(f"P70_NHEAT_DWELLINGS={a.room_by_room_or_no_heat_dwellings}")
        print(f"P70_NHEAT_SHARE={a.room_by_room_or_no_heat_share:.12f}")
        print(f"P70_NONREUSE_LOWER_SHARE={a.proven_nonreuse_lower_share:.12f}")

    def test_nonreuse_floor_uses_max_not_sum(self):
        a = build_distribution_nonreuse_assignment()
        self.assertAlmostEqual(
            a.proven_nonreuse_lower_share,
            max(a.room_by_room_or_no_heat_share, a.gas_convector_calibrated_share),
        )
        self.assertLessEqual(a.proven_nonreuse_lower_share, 1.0)
        self.assertAlmostEqual(
            a.reuse_upper_share,
            1.0 - a.proven_nonreuse_lower_share,
        )

    def test_assignment_remains_mixed_der_ass_bound(self):
        a = build_distribution_nonreuse_assignment()
        self.assertEqual(a.route_status, "QUALIFIED")
        self.assertEqual(a.evidence_status, "DER+ASS_SET_BOUND")


if __name__ == "__main__":
    unittest.main()
