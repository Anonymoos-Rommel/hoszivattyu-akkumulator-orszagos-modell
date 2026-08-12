"""Validate the pinned B02 KSH Census API structures and control observations."""

from __future__ import annotations

import json
from urllib.request import urlopen


API_BASE = "https://nepszamlalas2022.ksh.hu"
PINNED_VERSION = "V67"
EXPECTED_DIMENSIONS = {
    "WBL010": [
        "TIME_PERIOD",
        "TERUL_GEO4",
        "LAKAS_OCS",
        "EPEV_POC1",
        "FALA_V",
        "LAT_V",
        "KOMF",
        "FUTES_TOH",
        "FUTAGOK",
    ],
    "WBL011": [
        "TIME_PERIOD",
        "TERUL_GEO3",
        "TERUL_TELTIP2",
        "LAKAS_OCS",
        "EPEV_POC1",
        "FALA_V",
        "LAT_V",
        "KOMF",
        "FUTES_TOH",
        "FUTAGOK",
    ],
    "WBL016": [
        "TIME_PERIOD22",
        "TERUL_GEO4",
        "LAKAS_OCS",
        "EPEV_POC1",
        "FALA_V",
        "LAT_V",
        "KOMF",
        "FUTMODAG_V3",
        "INTERNET",
        "LEGKONDI",
        "HOSZIV",
        "NAPELEM",
        "NAPKOLL",
    ],
    "WBL017": [
        "TIME_PERIOD22",
        "TERUL_GEO3",
        "TERUL_TELTIP2",
        "LAKAS_OCS",
        "EPEV_POC1",
        "FALA_V",
        "LAT_V",
        "KOMF",
        "FUTMODAG_V3",
        "INTERNET",
        "LEGKONDI",
        "HOSZIV",
        "NAPELEM",
        "NAPKOLL",
    ],
}

HEAT_PUMP_CONTROL_PATH = (
    "/api/dataflows/WBL017/V67/d/"
    "TIME_PERIOD22:2022,TERUL_GEO3:HU,TERUL_TELTIP2:HU,LAKAS_OCS:DW_OC,"
    "EPEV_POC1:TOTAL,FALA_V:TOTAL,LAT_V:TOTAL,KOMF:TOTAL,FUTMODAG_V3:TOTAL,"
    "INTERNET:TOTAL,LEGKONDI:TOTAL,HOSZIV:1,NAPELEM:TOTAL,NAPKOLL:TOTAL"
)


def get_json(path: str) -> object:
    with urlopen(f"{API_BASE}{path}", timeout=30) as response:  # noqa: S310
        return json.load(response)


def main() -> int:
    latest = get_json("/api/version")
    latest_version = latest["version"]

    for flow, expected in EXPECTED_DIMENSIONS.items():
        structure = get_json(f"/api/structure/{flow}/{PINNED_VERSION}")
        dimensions = structure["data"]["dataStructures"][0][
            "dataStructureComponents"
        ]["dimensionList"]["dimensions"]
        actual = [item["id"] for item in sorted(dimensions, key=lambda item: item["position"])]
        if actual != expected:
            raise ValueError(f"{flow} dimension drift: expected={expected!r} actual={actual!r}")

    heat_pump_response = get_json(HEAT_PUMP_CONTROL_PATH)
    if not isinstance(heat_pump_response, list) or len(heat_pump_response) != 1:
        raise ValueError(f"unexpected WBL017 control response: {heat_pump_response!r}")
    heat_pump = heat_pump_response[0]
    if heat_pump["OBS_VALUE"] != "67853":
        raise ValueError(f"WBL017 control observation drift: {heat_pump!r}")

    print(
        "VALID: B02 KSH API "
        f"pinned={PINNED_VERSION} latest={latest_version} "
        "flows=WBL010,WBL011,WBL016,WBL017 heat_pump_control=67853"
    )
    if latest_version != PINNED_VERSION:
        print("NOTICE: a newer KSH API version exists; review before changing the pinned contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
