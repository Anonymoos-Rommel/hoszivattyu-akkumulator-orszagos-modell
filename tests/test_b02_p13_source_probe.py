import json
import unittest
from urllib.request import Request, urlopen


API_BASE = "https://nepszamlalas2022.ksh.hu"
VERSION = "V67"


def fetch_json(url: str):
    req = Request(url, headers={"User-Agent": "B02-P13-source-probe/1.2"})
    with urlopen(req, timeout=60) as response:  # noqa: S310
        return json.load(response)


class B02P13SourceProbe(unittest.TestCase):
    def test_probe_wbl011_nheat_control(self):
        url = (
            f"{API_BASE}/api/dataflows/WBL011/{VERSION}/d/"
            "TIME_PERIOD:2022,TERUL_GEO3:HU,TERUL_TELTIP2:HU,LAKAS_OCS:DW_OC,"
            "EPEV_POC1:TOTAL,FALA_V:TOTAL,LAT_V:TOTAL,KOMF:TOTAL,"
            "FUTES_TOH:NHEAT,FUTAGOK:TOTAL"
        )
        payload = fetch_json(url)
        self.fail("B02_P13_NHEAT_PROBE=" + json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    unittest.main()
