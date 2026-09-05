import hashlib
import json
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen


API_BASE = "https://nepszamlalas2022.ksh.hu"
FLOW = "WBL011"
VERSION = "V67"
COUNTIES = (
    "HU110", "HU120", "HU211", "HU212", "HU213", "HU221", "HU222",
    "HU223", "HU231", "HU232", "HU233", "HU311", "HU312", "HU313",
    "HU321", "HU322", "HU323", "HU331", "HU332", "HU333",
)
SETTLEMENT_TYPES = "FV+MJV+EV+K"
PERIODS = "Y_LT1919+Y1919-1945+Y1946-1960+Y1961-1980+Y1981-2000+Y2001-2010+Y_GE2011"
WALLS = "WALL1+WALL2+WALL3+WALL5+WALL6"
AREAS = "SQM_LT30+SQM30-39+SQM40-49+SQM50-59+SQM60-79+SQM80-99+SQM100-119+SQM_GE120"
COMFORTS = "COMF1+COMF2+COMF3+COMF4+COMF5"
MODES = "HEAT111+HEAT112+HEAT12+NHEAT"
FUELS = "FUEL11+FUEL12+FUEL13+FUEL14+FUEL21+FUEL22+FUEL23+FUEL3"


def fetch_json(url: str):
    req = Request(url, headers={"User-Agent": "B02-P14-source-probe/1.0"})
    with urlopen(req, timeout=120) as response:  # noqa: S310
        raw = response.read()
    return json.loads(raw), raw


def joint_url(county: str) -> str:
    return (
        f"{API_BASE}/api/dataflows/{FLOW}/{VERSION}/d/"
        f"TIME_PERIOD:2022,TERUL_GEO3:{county},TERUL_TELTIP2:{SETTLEMENT_TYPES},"
        f"LAKAS_OCS:DW_OC,EPEV_POC1:{PERIODS},FALA_V:{WALLS},LAT_V:{AREAS},"
        f"KOMF:{COMFORTS},FUTES_TOH:{MODES},FUTAGOK:{FUELS}"
    )


def total_url(county: str) -> str:
    return (
        f"{API_BASE}/api/dataflows/{FLOW}/{VERSION}/d/"
        f"TIME_PERIOD:2022,TERUL_GEO3:{county},TERUL_TELTIP2:HU,LAKAS_OCS:DW_OC,"
        "EPEV_POC1:TOTAL,FALA_V:TOTAL,LAT_V:TOTAL,KOMF:TOTAL,"
        "FUTES_TOH:TOTAL,FUTAGOK:TOTAL"
    )


def probe_county(county: str) -> dict[str, object]:
    joint, joint_raw = fetch_json(joint_url(county))
    total, total_raw = fetch_json(total_url(county))
    if not isinstance(joint, list) or not isinstance(total, list) or len(total) != 1:
        raise AssertionError(f"unexpected response shape for {county}")
    joint_sum = sum(int(row["OBS_VALUE"]) for row in joint if row.get("OBS_VALUE") not in (None, ""))
    total_value = int(total[0]["OBS_VALUE"])
    return {
        "county": county,
        "joint_records": len(joint),
        "joint_sum": joint_sum,
        "total": total_value,
        "delta": total_value - joint_sum,
        "joint_bytes": len(joint_raw),
        "joint_sha256": hashlib.sha256(joint_raw).hexdigest(),
        "total_bytes": len(total_raw),
        "total_sha256": hashlib.sha256(total_raw).hexdigest(),
    }


class B02P14SourceProbe(unittest.TestCase):
    def test_probe_wbl011_national_source_native_full_joint(self):
        summaries = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(probe_county, county): county for county in COUNTIES}
            for future in as_completed(futures):
                summaries.append(future.result())
        summaries.sort(key=lambda row: str(row["county"]))
        national_joint = sum(int(row["joint_sum"]) for row in summaries)
        national_total = sum(int(row["total"]) for row in summaries)
        result = {
            "counties": summaries,
            "national_joint_sum": national_joint,
            "national_total_sum": national_total,
            "national_delta": national_total - national_joint,
            "returned_records": sum(int(row["joint_records"]) for row in summaries),
            "response_bytes": sum(int(row["joint_bytes"]) for row in summaries),
        }
        self.fail(
            "B02_P14_NATIONAL_SOURCE_PROBE="
            + json.dumps(result, ensure_ascii=False, separators=(",", ":"))
        )


if __name__ == "__main__":
    unittest.main()
