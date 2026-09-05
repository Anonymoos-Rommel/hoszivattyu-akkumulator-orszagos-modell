from pathlib import Path
import json
import unittest

from modules.B01.non_district_population import county_projection, load_committed_projection


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/b02/ksh_wbl_joint_cells_2022.csv"


class B01P3ExactPopulationProbeTests(unittest.TestCase):
    def test_exact_county_projection_probe(self):
        rows = load_committed_projection(SOURCE)
        counties = county_projection(rows)
        self.assertEqual(20, len(counties))
        payload = [
            {
                "county_code": row.county_code,
                "county_name_hu": row.county_name_hu,
                "occupied": row.occupied_dwellings,
                "district": row.district_heated_dwellings,
                "non_district": row.non_district_heated_dwellings,
            }
            for row in counties
        ]
        print("B01P3_EXACT_COUNTIES=" + json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    unittest.main()
