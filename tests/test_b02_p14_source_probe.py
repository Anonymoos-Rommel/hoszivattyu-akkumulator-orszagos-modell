import json
import unittest
from urllib.request import Request, urlopen


API_BASE = "https://nepszamlalas2022.ksh.hu"
FLOW = "WBL011"
VERSION = "V67"


def fetch_json(url: str):
    req = Request(url, headers={"User-Agent": "B02-P14-source-probe/1.0"})
    with urlopen(req, timeout=60) as response:  # noqa: S310
        return json.load(response)


class B02P14SourceProbe(unittest.TestCase):
    def test_probe_wbl011_source_native_full_joint(self):
        # Narrow live source probe: every substantive WBL011 stock dimension
        # is selected with a non-TOTAL source-native code in one request.
        # Returned observations therefore prove a source-native joint surface,
        # rather than a synthetic cross-join of separately published margins.
        url = (
            f"{API_BASE}/api/dataflows/{FLOW}/{VERSION}/d/"
            "TIME_PERIOD:2022,TERUL_GEO3:HU110,TERUL_TELTIP2:FV,LAKAS_OCS:DW_OC,"
            "EPEV_POC1:Y1919-1945,FALA_V:WALL1,LAT_V:SQM60-79,KOMF:COMF1,"
            "FUTES_TOH:HEAT111+HEAT112+HEAT12+NHEAT,"
            "FUTAGOK:FUEL11+FUEL12+FUEL13+FUEL14+FUEL21+FUEL22+FUEL23+FUEL3"
        )
        payload = fetch_json(url)
        if not isinstance(payload, list):
            self.fail("B02_P14_SOURCE_PROBE=NONLIST_RESPONSE")

        summary = {
            "url": url,
            "returned_records": len(payload),
            "rows": [
                {
                    "EPEV_POC1": row.get("EPEV_POC1"),
                    "FALA_V": row.get("FALA_V"),
                    "LAT_V": row.get("LAT_V"),
                    "KOMF": row.get("KOMF"),
                    "FUTES_TOH": row.get("FUTES_TOH"),
                    "FUTAGOK": row.get("FUTAGOK"),
                    "OBS_VALUE": row.get("OBS_VALUE"),
                    "OBS_STATUS": row.get("OBS_STATUS"),
                }
                for row in payload
            ],
        }
        self.fail(
            "B02_P14_SOURCE_PROBE="
            + json.dumps(summary, ensure_ascii=False, separators=(",", ":"))
        )


if __name__ == "__main__":
    unittest.main()
