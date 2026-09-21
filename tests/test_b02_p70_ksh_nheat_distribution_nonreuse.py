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

    def test_p22_nheat_exact_population_control(self):
        a = build_distribution_nonreuse_assignment()
        self.assertEqual(a.occupied_dwellings, 4_008_541)
        self.assertEqual(a.room_by_room_or_no_heat_dwellings, 1_173_639)
        self.assertAlmostEqual(a.room_by_room_or_no_heat_share, 0.292784581722, places=12)

    def test_nheat_strengthens_gas_convector_floor(self):
        a = build_distribution_nonreuse_assignment()
        self.assertGreater(
            a.room_by_room_or_no_heat_share,
            a.gas_convector_calibrated_share,
        )
        self.assertAlmostEqual(
            a.proven_nonreuse_lower_share,
            a.room_by_room_or_no_heat_share,
        )
        self.assertEqual(a.proven_nonreuse_lower_dwellings, 1_173_639)
        self.assertAlmostEqual(a.reuse_upper_share, 0.707215418278, places=12)

    def test_nonreuse_floor_uses_max_not_sum(self):
        a = build_distribution_nonreuse_assignment()
        self.assertAlmostEqual(
            a.proven_nonreuse_lower_share,
            max(a.room_by_room_or_no_heat_share, a.gas_convector_calibrated_share),
        )
        self.assertLess(
            a.proven_nonreuse_lower_share,
            a.room_by_room_or_no_heat_share + a.gas_convector_calibrated_share,
        )

    def test_assignment_is_der_route_conditional_lower_bound(self):
        a = build_distribution_nonreuse_assignment()
        self.assertEqual(a.route_status, "QUALIFIED")
        self.assertEqual(a.evidence_status, "DER_ROUTE_CONDITIONAL_LOWER_BOUND")


if __name__ == "__main__":
    unittest.main()
