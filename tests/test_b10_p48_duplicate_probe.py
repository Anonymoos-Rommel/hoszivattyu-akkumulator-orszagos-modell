import csv
from collections import defaultdict
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ("historical", ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"),
    ("opus_p44", ROOT / "registry/dso_service_area_membership_crosswalk_opus_p44.csv"),
    ("demasz_p45", ROOT / "registry/dso_service_area_membership_crosswalk_demasz_p45.csv"),
    ("elmu_p46", ROOT / "registry/dso_service_area_membership_crosswalk_elmu_p46.csv"),
    ("emasz_p47", ROOT / "registry/dso_service_area_membership_emasz_p47_pairs.csv"),
    ("ddasz_p48", ROOT / "registry/dso_service_area_membership_ddasz_p48_pairs.csv"),
]

class B10P48DuplicateProbe(unittest.TestCase):
    def test_print_duplicate_ksh_codes(self):
        by_code = defaultdict(list)
        for label, path in FILES:
            with path.open(encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    by_code[row["ksh_settlement_code"]].append((label, row.get("operator_id", ""), row["settlement_name"]))
        dup = {code: rows for code, rows in by_code.items() if len(rows) > 1}
        print("P48_DUPLICATES_BEGIN")
        for code, rows in sorted(dup.items()):
            print(code, repr(rows))
        print("P48_DUPLICATES_END")
        self.assertEqual(2, len(dup))

if __name__ == "__main__":
    unittest.main()
