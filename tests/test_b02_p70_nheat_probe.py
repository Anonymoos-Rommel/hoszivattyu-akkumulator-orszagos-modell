import unittest

from modules.B02.heating_system_assignment import build_heating_system_assignment


class B02P70NheatProbe(unittest.TestCase):
    def test_print_exact_topology_summary(self):
        _rows, summary = build_heating_system_assignment()
        print(
            "P70_PROBE "
            f"occupied={summary.occupied_dwellings} "
            f"central={summary.central_heating_dwellings} "
            f"district={summary.district_heating_dwellings} "
            f"nheat={summary.room_by_room_or_no_heat_dwellings}"
        )
        self.assertEqual(
            summary.occupied_dwellings,
            summary.central_heating_dwellings
            + summary.district_heating_dwellings
            + summary.room_by_room_or_no_heat_dwellings,
        )


if __name__ == "__main__":
    unittest.main()
