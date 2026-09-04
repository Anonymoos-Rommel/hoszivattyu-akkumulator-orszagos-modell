import csv
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "tests/p47_candidate_names.txt"
PAIRS = ROOT / "registry/dso_service_area_membership_emasz_p47_pairs.csv"


class P47PairProbe(unittest.TestCase):
    def test_pair_names_match_transformed_source_candidates(self):
        expected = {line.strip() for line in CANDIDATES.read_text(encoding="utf-8").splitlines() if line.strip()}
        expected -= {"Fóny", "Hídvégardó", "Márkháza Mályi", "Szentistván Szentistvánbaksa"}
        expected |= {"Márkháza", "Mályi", "Szentistván", "Szentistvánbaksa"}
        with PAIRS.open(encoding="utf-8", newline="") as handle:
            actual = {row["settlement_name"] for row in csv.DictReader(handle)}
        print("P47_PAIR_MISSING=" + "|".join(sorted(expected - actual)))
        print("P47_PAIR_EXTRA=" + "|".join(sorted(actual - expected)))
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
