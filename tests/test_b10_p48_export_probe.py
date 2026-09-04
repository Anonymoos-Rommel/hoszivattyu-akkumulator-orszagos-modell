import contextlib
import hashlib
import io
from pathlib import Path
import unittest

from test_b10_p48_ddasz_locator_probe import B10P48DdaszLocatorProbe


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "registry/dso_service_area_membership_ddasz_p48_pairs.csv"
EXPECTED_DIGEST = "6c2515bab72425333479b466ec34d1deb2f08035380a43739e9b11eb2410bc9d"


class B10P48ExportProbe(unittest.TestCase):
    def test_export_final_pair_surface(self):
        capture = io.StringIO()
        with contextlib.redirect_stdout(capture):
            B10P48DdaszLocatorProbe().test_probe()
        text = capture.getvalue()
        payload = text.split("P48_PROBE_NEW_PAIRS_BEGIN\n", 1)[1].split("P48_PROBE_NEW_PAIRS_END", 1)[0]
        pairs = [line.strip() for line in payload.splitlines() if line.strip()]
        self.assertEqual(779, len(pairs))
        canonical = "".join(f"{line}\n" for line in sorted(pairs))
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        self.assertEqual(EXPECTED_DIGEST, digest)
        csv_text = "ksh_settlement_code,settlement_name\n" + "".join(
            f"{line.split('|', 1)[0]},{line.split('|', 1)[1]}\n" for line in sorted(pairs)
        )
        OUT.write_text(csv_text, encoding="utf-8")
        self.assertEqual(780, len(OUT.read_text(encoding="utf-8").splitlines()))
        print("P48_PAIR_DIGEST", digest)
        print("P48_PAIR_FILE", OUT.relative_to(ROOT))


if __name__ == "__main__":
    unittest.main()
