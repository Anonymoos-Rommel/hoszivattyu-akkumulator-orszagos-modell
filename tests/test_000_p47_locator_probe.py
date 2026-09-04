import csv
import io
from pathlib import Path
import unittest
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "tests/p47_candidate_names.txt"
LOCATOR_URL = "https://raw.githubusercontent.com/ferenci-tamas/IrszHnk/master/IrszHnk.csv"


class P47LocatorProbe(unittest.TestCase):
    def test_emit_exact_empty_telepulesresz_mapping(self):
        names = [line.strip() for line in CANDIDATES.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(605, len(names))
        with urlopen(LOCATOR_URL, timeout=30) as response:
            text = response.read().decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text), delimiter=";"))
        base = {}
        for row in rows[1:]:
            if len(row) < 4 or row[2] != "":
                continue
            base.setdefault(row[0], []).append(row[3])
        mapped = []
        unmatched = []
        ambiguous = []
        for name in names:
            codes = base.get(name, [])
            if len(codes) == 1:
                mapped.append((codes[0], name))
            elif len(codes) == 0:
                unmatched.append(name)
            else:
                ambiguous.append((name, codes))
        print("P47_MAPPING_BEGIN")
        for code, name in mapped:
            print(f"{code},{name}")
        print("P47_MAPPING_END")
        print("P47_UNMATCHED=" + "|".join(unmatched))
        print("P47_AMBIGUOUS=" + "|".join(f"{n}:{'/'.join(c)}" for n, c in ambiguous))
        print(f"P47_COUNTS candidates={len(names)} mapped={len(mapped)} unmatched={len(unmatched)} ambiguous={len(ambiguous)}")
        self.fail("P47 locator probe intentionally fails; remove after harvesting exact mapping")


if __name__ == "__main__":
    unittest.main()
