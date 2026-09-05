from pathlib import Path
import csv
import unittest

from modules.B01.non_district_population import (
    ALLOWED_HEATING_CODES,
    DISTRICT_HEATING_CODE,
    EXPECTED_DISTRICT_HEATED_DWELLINGS,
    EXPECTED_NON_DISTRICT_HEATED_DWELLINGS,
    EXPECTED_OCCUPIED_DWELLINGS,
    county_projection,
    load_committed_projection,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/b02/ksh_wbl_joint_cells_2022.csv"
REGISTRY = ROOT / "registry/b01_non_district_heated_population_2022.csv"
ROLLOUT_CONTRACT = ROOT / "registry/b01_national_rollout_policy_contract.csv"
DOC = ROOT / "docs/source_packs/B01_P3_EXACT_NON_DISTRICT_POPULATION_BASE.md"

EXPECTED_COUNTIES = {
    "HU110": ("Budapest", 800338, 233233, 567105),
    "HU120": ("Pest vármegye", 491227, 20194, 471033),
    "HU211": ("Fejér vármegye", 169752, 38769, 130983),
    "HU212": ("Komárom-Esztergom vármegye", 123133, 35431, 87702),
    "HU213": ("Veszprém vármegye", 137450, 20427, 117023),
    "HU221": ("Győr-Moson-Sopron vármegye", 187968, 32990, 154978),
    "HU222": ("Vas vármegye", 100985, 15101, 85884),
    "HU223": ("Zala vármegye", 109891, 1083, 108808),
    "HU231": ("Baranya vármegye", 152683, 36361, 116322),
    "HU232": ("Somogy vármegye", 121932, 7681, 114251),
    "HU233": ("Tolna vármegye", 87986, 10016, 77970),
    "HU311": ("Borsod-Abaúj-Zemplén vármegye", 249031, 49149, 199882),
    "HU312": ("Heves vármegye", 118784, 8481, 110303),
    "HU313": ("Nógrád vármegye", 75519, 4748, 70771),
    "HU321": ("Hajdú-Bihar vármegye", 210805, 31755, 179050),
    "HU322": ("Jász-Nagykun-Szolnok vármegye", 150641, 9257, 141384),
    "HU323": ("Szabolcs-Szatmár-Bereg vármegye", 200121, 18665, 181456),
    "HU331": ("Bács-Kiskun vármegye", 210884, 15837, 195047),
    "HU332": ("Békés vármegye", 139639, 213, 139426),
    "HU333": ("Csongrád-Csanád vármegye", 169772, 29333, 140439),
}


class B01P3ExactNonDistrictPopulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settlement_type_rows = load_committed_projection(SOURCE)
        cls.counties = county_projection(cls.settlement_type_rows)
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            cls.registry = list(csv.DictReader(handle))

    def test_frozen_heating_partition_and_district_code(self):
        self.assertEqual({"HEAT111", "HEAT112", "HEAT12", "NHEAT"}, set(ALLOWED_HEATING_CODES))
        self.assertEqual("HEAT12", DISTRICT_HEATING_CODE)

    def test_exact_national_controls_replace_rounded_share_estimate(self):
        self.assertEqual(4_008_541, EXPECTED_OCCUPIED_DWELLINGS)
        self.assertEqual(618_724, EXPECTED_DISTRICT_HEATED_DWELLINGS)
        self.assertEqual(3_389_817, EXPECTED_NON_DISTRICT_HEATED_DWELLINGS)
        self.assertEqual(
            EXPECTED_OCCUPIED_DWELLINGS,
            EXPECTED_DISTRICT_HEATED_DWELLINGS + EXPECTED_NON_DISTRICT_HEATED_DWELLINGS,
        )

    def test_exact_twenty_county_population_is_frozen(self):
        self.assertEqual(20, len(self.counties))
        actual = {
            row.county_code: (
                row.county_name_hu,
                row.occupied_dwellings,
                row.district_heated_dwellings,
                row.non_district_heated_dwellings,
            )
            for row in self.counties
        }
        self.assertEqual(EXPECTED_COUNTIES, actual)

    def test_county_rows_conserve_population_and_remain_derived(self):
        for row in self.counties:
            self.assertEqual(
                row.occupied_dwellings,
                row.district_heated_dwellings + row.non_district_heated_dwellings,
            )
            self.assertGreaterEqual(row.district_heated_dwellings, 0)
            self.assertGreater(row.non_district_heated_dwellings, 0)
            self.assertEqual("DER", row.evidence_status)
            self.assertEqual("WBL011_HEATING_FUEL", row.source_projection)

    def test_static_registry_matches_runtime_recomputation_exactly(self):
        self.assertEqual(21, len(self.registry))
        county_registry = {row["region_code"]: row for row in self.registry if row["grain"] != "NATIONAL"}
        self.assertEqual(set(EXPECTED_COUNTIES), set(county_registry))
        for county in self.counties:
            row = county_registry[county.county_code]
            self.assertEqual(county.county_name_hu, row["region_name"])
            self.assertEqual(county.occupied_dwellings, int(row["occupied_dwellings"]))
            self.assertEqual(county.district_heated_dwellings, int(row["district_heated_dwellings"]))
            self.assertEqual(county.non_district_heated_dwellings, int(row["non_district_heated_dwellings"]))
            self.assertEqual("DER", row["evidence_status"])
            self.assertEqual("SRC-B02-KSH-CENSUS-API-2022", row["source_id"])

        national = [row for row in self.registry if row["grain"] == "NATIONAL"]
        self.assertEqual(1, len(national))
        self.assertEqual("HU", national[0]["region_code"])
        self.assertEqual(4_008_541, int(national[0]["occupied_dwellings"]))
        self.assertEqual(618_724, int(national[0]["district_heated_dwellings"]))
        self.assertEqual(3_389_817, int(national[0]["non_district_heated_dwellings"]))

    def test_rollout_contract_marks_p2_approximation_superseded(self):
        with ROLLOUT_CONTRACT.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("3403746", row["historical_approx_non_district_heated_occupied_dwellings_2022"])
        self.assertEqual("SUPERSEDED_DER_FROM_ROUNDED_KSH_SHARES", row["historical_approximation_status"])
        self.assertEqual("3389817", row["exact_non_district_heated_occupied_dwellings_2022"])
        self.assertEqual("DER_FROM_OBS_WBL011_CELLS", row["exact_population_status"])
        self.assertEqual("", row["canonical_programme_target_households"])
        self.assertEqual("Q", row["canonical_programme_target_status"])

    def test_document_preserves_non_eligibility_and_spatial_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "3,389,817",
            "618,724",
            "3,403,746",
            "3,389,817 NON-DISTRICT-HEATED OCCUPIED DWELLINGS != B02 TECHNICALLY ELIGIBLE STOCK",
            "Gas and electricity customer/service-point statistics are not used as dwelling counts",
            "cannot be allocated to a DSO service area or exact substation",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
