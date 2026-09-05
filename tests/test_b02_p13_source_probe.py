import json
import re
import unittest
from collections import defaultdict
from urllib.request import Request, urlopen


API_BASE = "https://nepszamlalas2022.ksh.hu"
FLOW = "WBL017"
VERSION = "V67"


def fetch_json(url: str):
    req = Request(url, headers={"User-Agent": "B02-P13-source-probe/1.1"})
    with urlopen(req, timeout=60) as response:  # noqa: S310
        return json.load(response)


def codelist_id(enumeration: str) -> str:
    match = re.search(r"Codelist=HCSO:([^()]+)", enumeration)
    if not match:
        raise AssertionError(f"unrecognised codelist URN: {enumeration!r}")
    return match.group(1)


class B02P13SourceProbe(unittest.TestCase):
    def test_probe_wbl017_source_native_codes_and_counts(self):
        structure = fetch_json(f"{API_BASE}/api/structure/{FLOW}/{VERSION}")
        dimensions = structure["data"]["dataStructures"][0]["dataStructureComponents"]["dimensionList"]["dimensions"]
        dim = next(item for item in dimensions if item["id"] == "FUTMODAG_V3")
        cid = codelist_id(dim["localRepresentation"]["enumeration"])
        codelists = {item["id"]: item for item in structure["data"]["codelists"]}
        code_items = codelists[cid]["codes"]

        code_meta = []
        selected = []
        for item in code_items:
            code = str(item["id"])
            name = item.get("names", {}).get("hu", item.get("name", code))
            parent = item.get("parentCode") or item.get("parent") or item.get("parentCodeId") or ""
            code_meta.append({"id": code, "name": name, "parent": parent})
            if code != "TOTAL":
                selected.append(code)

        query = (
            f"{API_BASE}/api/dataflows/{FLOW}/{VERSION}/d/"
            "TIME_PERIOD22:2022,TERUL_GEO3:HU,TERUL_TELTIP2:HU,LAKAS_OCS:DW_OC,"
            "EPEV_POC1:TOTAL,FALA_V:TOTAL,LAT_V:TOTAL,KOMF:TOTAL,"
            f"FUTMODAG_V3:{'+'.join(selected)},INTERNET:TOTAL,LEGKONDI:TOTAL,"
            "HOSZIV:1+0+9,NAPELEM:TOTAL,NAPKOLL:TOTAL"
        )
        payload = fetch_json(query)
        by_code = defaultdict(lambda: {"1": 0, "0": 0, "9": 0, "rows": 0})
        for row in payload:
            code = str(row.get("FUTMODAG_V3", ""))
            hp = str(row.get("HOSZIV", ""))
            raw = row.get("OBS_VALUE")
            value = int(raw) if raw not in (None, "") else 0
            by_code[code][hp] += value
            by_code[code]["rows"] += 1

        for item in code_meta:
            code = item["id"]
            if code != "TOTAL":
                item.update(by_code.get(code, {}))
                item["sum_presence"] = sum(item.get(k, 0) for k in ("1", "0", "9"))

        total_all_url = (
            f"{API_BASE}/api/dataflows/{FLOW}/{VERSION}/d/"
            "TIME_PERIOD22:2022,TERUL_GEO3:HU,TERUL_TELTIP2:HU,LAKAS_OCS:DW_OC,"
            "EPEV_POC1:TOTAL,FALA_V:TOTAL,LAT_V:TOTAL,KOMF:TOTAL,FUTMODAG_V3:TOTAL,"
            "INTERNET:TOTAL,LEGKONDI:TOTAL,HOSZIV:TOTAL,NAPELEM:TOTAL,NAPKOLL:TOTAL"
        )
        total_hp_url = total_all_url.replace("HOSZIV:TOTAL", "HOSZIV:1")
        total_all = fetch_json(total_all_url)
        total_hp = fetch_json(total_hp_url)
        summary = {
            "code_meta": code_meta,
            "multi_query_rows": len(payload),
            "sum_selected_presence": sum(v["1"] + v["0"] + v["9"] for v in by_code.values()),
            "sum_selected_hp1": sum(v["1"] for v in by_code.values()),
            "total_all": total_all,
            "total_hp1": total_hp,
        }
        self.fail("B02_P13_SOURCE_PROBE=" + json.dumps(summary, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    unittest.main()
