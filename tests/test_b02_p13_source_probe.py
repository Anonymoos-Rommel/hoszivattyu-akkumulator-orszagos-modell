import json
import re
import unittest
from urllib.request import Request, urlopen


API_BASE = "https://nepszamlalas2022.ksh.hu"
FLOW = "WBL017"
VERSION = "V67"


def fetch_json(url: str):
    req = Request(url, headers={"User-Agent": "B02-P13-source-probe/1.0"})
    with urlopen(req, timeout=60) as response:  # noqa: S310
        return json.load(response)


def codelist_id(enumeration: str) -> str:
    match = re.search(r"Codelist=HCSO:([^()]+)", enumeration)
    if not match:
        raise AssertionError(f"unrecognised codelist URN: {enumeration!r}")
    return match.group(1)


def one_value(code: str, hosziv: str) -> str:
    url = (
        f"{API_BASE}/api/dataflows/{FLOW}/{VERSION}/d/"
        "TIME_PERIOD22:2022,TERUL_GEO3:HU,TERUL_TELTIP2:HU,LAKAS_OCS:DW_OC,"
        "EPEV_POC1:TOTAL,FALA_V:TOTAL,LAT_V:TOTAL,KOMF:TOTAL,"
        f"FUTMODAG_V3:{code},INTERNET:TOTAL,LEGKONDI:TOTAL,HOSZIV:{hosziv},"
        "NAPELEM:TOTAL,NAPKOLL:TOTAL"
    )
    payload = fetch_json(url)
    if not isinstance(payload, list) or len(payload) != 1:
        return f"RESPONSE_{len(payload) if isinstance(payload, list) else 'NONLIST'}"
    return str(payload[0].get("OBS_VALUE", ""))


class B02P13SourceProbe(unittest.TestCase):
    def test_probe_wbl017_source_native_codes_and_counts(self):
        structure = fetch_json(f"{API_BASE}/api/structure/{FLOW}/{VERSION}")
        dimensions = structure["data"]["dataStructures"][0]["dataStructureComponents"]["dimensionList"]["dimensions"]
        dim = next(item for item in dimensions if item["id"] == "FUTMODAG_V3")
        cid = codelist_id(dim["localRepresentation"]["enumeration"])
        codelists = {item["id"]: item for item in structure["data"]["codelists"]}
        codes = codelists[cid]["codes"]

        rows = []
        for item in codes:
            code = str(item["id"])
            if code == "TOTAL":
                continue
            name = item.get("names", {}).get("hu", item.get("name", code))
            parent = item.get("parentCode") or item.get("parent") or item.get("parentCodeId") or ""
            rows.append({
                "id": code,
                "name": name,
                "parent": parent,
                "all": one_value(code, "TOTAL"),
                "hp1": one_value(code, "1"),
            })

        summary = {
            "codes": rows,
            "total_all": one_value("TOTAL", "TOTAL"),
            "total_hp1": one_value("TOTAL", "1"),
        }
        self.fail("B02_P13_SOURCE_PROBE=" + json.dumps(summary, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    unittest.main()
