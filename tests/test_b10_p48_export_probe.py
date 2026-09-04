import base64
import contextlib
import hashlib
import io
import unittest

from test_b10_p48_ddasz_locator_probe import B10P48DdaszLocatorProbe


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
        csv_text = "ksh_settlement_code,settlement_name\n" + "".join(
            f"{line.split('|', 1)[0]},{line.split('|', 1)[1]}\n" for line in sorted(pairs)
        )
        print("P48_PAIR_DIGEST", hashlib.sha256(canonical.encode("utf-8")).hexdigest())
        print("P48_PAIRS_CSV_B64_BEGIN")
        encoded = base64.b64encode(csv_text.encode("utf-8")).decode("ascii")
        for i in range(0, len(encoded), 2000):
            print(encoded[i:i+2000])
        print("P48_PAIRS_CSV_B64_END")


if __name__ == "__main__":
    unittest.main()
