"""Build the B02 settlement-type building-type proxy from official KSH sources.

The script extracts Table 1 from the KSH 2015 housing survey PDF, reads the
pinned KSH Census 2022 WBL011 settlement-type controls, and applies the 2015
occupied-dwelling shares to the 2022 occupied-dwelling universe. The resulting
counts are assumptions (ASS), not observed building-type counts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import platform
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.request import urlopen

import pypdf
from pypdf import PdfReader


PDF_URL = "https://www.ksh.hu/docs/hun/xftp/idoszaki/pdf/miben_elunk15.pdf"
API_BASE = "https://nepszamlalas2022.ksh.hu"
PINNED_VERSION = "V67"
SOURCE_ID = "SRC-B02-KSH-HOUSING-SURVEY-2015"
API_SOURCE_ID = "SRC-B02-KSH-CENSUS-API-2022"

SETTLEMENTS = [
    ("FV", "Budapest", "Budapest", "EXACT"),
    ("MJV", "Megyei jogú város", "Megyeszékhely", "APPROXIMATE"),
    ("EV", "Egyéb város", "Város", "APPROXIMATE"),
    ("K", "Község", "Község", "EXACT"),
]
SIZE_BANDS = [
    ("1-3", r"1–\s*3", "FAMILY_HOUSE"),
    ("4-12", r"4–12", "MULTI_DWELLING"),
    ("13-24", r"13–24", "MULTI_DWELLING"),
    ("25-50", r"25–50", "MULTI_DWELLING"),
    ("GT50", r"50-nél több", "MULTI_DWELLING"),
]
EXPECTED_ALL_BAND_TOTAL = 4_420_700
EXPECTED_OCCUPIED_BAND_TOTAL = 3_860_700
PUBLISHED_OCCUPIED_NATIONAL_TOTAL = 3_860_600
OCCUPIED_SETTLEMENT_TOTALS = {
    "FV": 852_300,
    "MJV": 717_800,
    "EV": 1_285_200,
    "K": 1_005_400,
}
EXPECTED_WBL_CONTROLS = {
    "FV": 800_338,
    "MJV": 867_129,
    "EV": 1_243_229,
    "K": 1_097_845,
}


def fetch_bytes(url: str) -> bytes:
    with urlopen(url, timeout=60) as response:  # noqa: S310 - fixed official URLs
        return response.read()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_count(token: str) -> int:
    return int(re.sub(r"\s+", "", token))


def parse_table_section(section: str) -> dict[str, list[int]]:
    rows: dict[str, list[int]] = {}
    for size_code, label_pattern, _building_type in SIZE_BANDS:
        match = re.search(rf"(?m)^\s*{label_pattern}\s+(.+)$", section)
        if not match:
            raise ValueError(f"KSH Table 1 row not found: {size_code}")
        tokens = re.split(r"\s{2,}", match.group(1).strip())
        if len(tokens) != 5:
            raise ValueError(f"unexpected KSH Table 1 row shape for {size_code}: {tokens!r}")
        rows[size_code] = [parse_count(token) for token in tokens]
    return rows


def extract_ksh_table(pdf_bytes: bytes) -> tuple[list[dict[str, object]], str]:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    if len(reader.pages) != 52:
        raise ValueError(f"unexpected KSH PDF page count: {len(reader.pages)}")
    page_text = reader.pages[5].extract_text()
    controls = [
        "A 2015. évi lakásfelmérés",
        "20 ezer lakást",
        "1. tábla",
        "Ebből: lakott lakás",
    ]
    missing = [control for control in controls if control not in page_text]
    if missing:
        raise ValueError(f"KSH PDF control text missing: {missing!r}")

    dwelling_section = page_text.split("\nLakás\n", 1)[1]
    all_section, occupied_section = dwelling_section.split("Ebből: lakott lakás", 1)
    occupied_section = occupied_section.split("Összesen", 1)[0]
    all_rows = parse_table_section(all_section)
    occupied_rows = parse_table_section(occupied_section)

    records: list[dict[str, object]] = []
    for scope, table in (("ALL_DWELLINGS", all_rows), ("OCCUPIED_DWELLINGS", occupied_rows)):
        for settlement_index, (wbl_code, wbl_label, survey_label, alignment) in enumerate(SETTLEMENTS):
            for size_code, _pattern, building_type in SIZE_BANDS:
                records.append(
                    {
                        "occupancy_scope": scope,
                        "wbl_settlement_code": wbl_code,
                        "wbl_settlement_label": wbl_label,
                        "ksh_2015_settlement_type": survey_label,
                        "category_alignment": alignment,
                        "building_size_band": size_code,
                        "canonical_building_type": building_type,
                        "dwelling_count": table[size_code][settlement_index],
                    }
                )

    all_total = sum(row["dwelling_count"] for row in records if row["occupancy_scope"] == "ALL_DWELLINGS")
    occupied_total = sum(
        row["dwelling_count"] for row in records if row["occupancy_scope"] == "OCCUPIED_DWELLINGS"
    )
    if all_total != EXPECTED_ALL_BAND_TOTAL or occupied_total != EXPECTED_OCCUPIED_BAND_TOTAL:
        raise ValueError(
            "KSH Table 1 totals drift: "
            f"all={all_total} occupied={occupied_total}"
        )
    return records, page_text


def wbl_url(settlement_code: str) -> str:
    return (
        f"{API_BASE}/api/dataflows/WBL011/{PINNED_VERSION}/d/"
        "TIME_PERIOD:2022,TERUL_GEO3:HU,"
        f"TERUL_TELTIP2:{settlement_code},LAKAS_OCS:DW_OC,"
        "EPEV_POC1:TOTAL,FALA_V:TOTAL,LAT_V:TOTAL,KOMF:TOTAL,"
        "FUTES_TOH:TOTAL,FUTAGOK:TOTAL"
    )


def fetch_wbl_controls() -> tuple[dict[str, int], dict[str, str], str]:
    structure_bytes = fetch_bytes(f"{API_BASE}/api/structure/WBL011/{PINNED_VERSION}")
    structure = json.loads(structure_bytes)
    dimensions = structure["data"]["dataStructures"][0]["dataStructureComponents"]["dimensionList"]["dimensions"]
    dimension_ids = [item["id"] for item in sorted(dimensions, key=lambda item: item["position"])]
    if "BUILDING_TYPE" in dimension_ids or "EPITMENY_TIPUS" in dimension_ids:
        raise ValueError("WBL011 unexpectedly gained a building-type dimension; review proxy necessity")
    if "TERUL_TELTIP2" not in dimension_ids:
        raise ValueError("WBL011 settlement-type dimension missing")

    values: dict[str, int] = {}
    response_hashes: dict[str, str] = {}
    for code, _label, _survey_label, _alignment in SETTLEMENTS:
        response_bytes = fetch_bytes(wbl_url(code))
        response_hashes[code] = sha256(response_bytes)
        payload = json.loads(response_bytes)
        if not isinstance(payload, list) or len(payload) != 1:
            raise ValueError(f"unexpected WBL011 response for {code}: {payload!r}")
        values[code] = int(payload[0]["OBS_VALUE"])
    if values != EXPECTED_WBL_CONTROLS:
        raise ValueError(f"WBL011 control drift: expected={EXPECTED_WBL_CONTROLS!r} actual={values!r}")
    return values, response_hashes, sha256(structure_bytes)


def build_proxy(
    source_records: list[dict[str, object]], wbl_values: dict[str, int]
) -> list[dict[str, object]]:
    occupied = [row for row in source_records if row["occupancy_scope"] == "OCCUPIED_DWELLINGS"]
    proxy_rows: list[dict[str, object]] = []
    for code, label, survey_label, alignment in SETTLEMENTS:
        settlement_rows = [row for row in occupied if row["wbl_settlement_code"] == code]
        source_total = OCCUPIED_SETTLEMENT_TOTALS[code]
        family_source = sum(
            int(row["dwelling_count"])
            for row in settlement_rows
            if row["canonical_building_type"] == "FAMILY_HOUSE"
        )
        family_share = Decimal(family_source) / Decimal(source_total)
        family_proxy = int(
            (Decimal(wbl_values[code]) * family_share).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
        source_counts = {
            "FAMILY_HOUSE": family_source,
            "MULTI_DWELLING": source_total - family_source,
        }
        counts = {
            "FAMILY_HOUSE": family_proxy,
            "MULTI_DWELLING": wbl_values[code] - family_proxy,
        }
        shares = {
            "FAMILY_HOUSE": family_share,
            "MULTI_DWELLING": Decimal(1) - family_share,
        }
        for building_type in ("FAMILY_HOUSE", "MULTI_DWELLING"):
            proxy_rows.append(
                {
                    "wbl_settlement_code": code,
                    "wbl_settlement_label": label,
                    "ksh_2015_settlement_type": survey_label,
                    "category_alignment": alignment,
                    "canonical_building_type": building_type,
                    "source_2015_occupied_dwellings": source_counts[building_type],
                    "source_2015_share": format(shares[building_type], ".15f"),
                    "wbl_2022_occupied_dwellings": wbl_values[code],
                    "proxy_2022_dwelling_count": counts[building_type],
                }
            )
    return proxy_rows


def write_csv(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(headers)
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/b02"))
    parser.add_argument("--retrieved-at", default="2026-08-12")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    pdf_bytes = fetch_bytes(PDF_URL)
    pdf_hash = sha256(pdf_bytes)
    source_records, _page_text = extract_ksh_table(pdf_bytes)
    wbl_values, response_hashes, structure_hash = fetch_wbl_controls()
    proxy_rows = build_proxy(source_records, wbl_values)

    source_csv = args.output_dir / "ksh_building_type_source_2015.csv"
    proxy_csv = args.output_dir / "ksh_building_type_proxy_2022.csv"
    manifest_json = args.output_dir / "ksh_building_type_proxy_manifest.json"

    source_output: list[list[object]] = []
    for index, row in enumerate(source_records, start=1):
        source_output.append(
            [
                f"SRCROW-B02-BTYPE-{index:03d}",
                SOURCE_ID,
                2015,
                row["occupancy_scope"],
                row["ksh_2015_settlement_type"],
                row["wbl_settlement_code"],
                row["wbl_settlement_label"],
                row["category_alignment"],
                row["building_size_band"],
                row["canonical_building_type"],
                row["dwelling_count"],
                "OBS",
                PDF_URL,
                6,
                args.retrieved_at,
                pdf_hash,
                "KSH 2015 housing survey Table 1; survey-weighted estimate.",
            ]
        )
    write_csv(
        source_csv,
        [
            "source_row_id",
            "source_id",
            "reference_period",
            "occupancy_scope",
            "ksh_2015_settlement_type",
            "wbl_settlement_code",
            "wbl_settlement_label",
            "category_alignment",
            "building_size_band",
            "canonical_building_type",
            "dwelling_count",
            "evidence_status",
            "source_url",
            "source_pdf_page",
            "retrieved_at",
            "source_sha256",
            "notes",
        ],
        source_output,
    )

    proxy_output: list[list[object]] = []
    for index, row in enumerate(proxy_rows, start=1):
        code = str(row["wbl_settlement_code"])
        proxy_output.append(
            [
                f"PROXY-B02-BTYPE-{index:02d}",
                f"{SOURCE_ID};{API_SOURCE_ID}",
                2022,
                code,
                row["wbl_settlement_label"],
                row["ksh_2015_settlement_type"],
                row["category_alignment"],
                row["canonical_building_type"],
                row["source_2015_occupied_dwellings"],
                row["source_2015_share"],
                row["wbl_2022_occupied_dwellings"],
                row["proxy_2022_dwelling_count"],
                "ASS",
                "round_half_up(WBL011_2022_occupied_dwellings * KSH_2015_occupied_building_type_share)",
                wbl_url(code),
                args.retrieved_at,
                response_hashes[code],
                "Settlement-type proxy only; do not treat as an observed WBL building-type join.",
            ]
        )
    write_csv(
        proxy_csv,
        [
            "proxy_row_id",
            "source_ids",
            "reference_period",
            "wbl_settlement_code",
            "wbl_settlement_label",
            "ksh_2015_settlement_type",
            "category_alignment",
            "canonical_building_type",
            "source_2015_occupied_dwellings",
            "source_2015_share",
            "wbl_2022_occupied_dwellings",
            "proxy_2022_dwelling_count",
            "evidence_status",
            "formula",
            "wbl_request_url",
            "retrieved_at",
            "wbl_response_sha256",
            "notes",
        ],
        proxy_output,
    )

    family_total = sum(
        int(row["proxy_2022_dwelling_count"])
        for row in proxy_rows
        if row["canonical_building_type"] == "FAMILY_HOUSE"
    )
    multi_total = sum(
        int(row["proxy_2022_dwelling_count"])
        for row in proxy_rows
        if row["canonical_building_type"] == "MULTI_DWELLING"
    )
    wbl_total = sum(wbl_values.values())
    if family_total + multi_total != wbl_total:
        raise ValueError("proxy totals do not reconcile to WBL011 occupied-dwelling universe")

    manifest = {
        "schema_version": "1.0",
        "retrieved_at": args.retrieved_at,
        "evidence_status": "ASS",
        "runtime": {
            "python": platform.python_version(),
            "pypdf": pypdf.__version__,
        },
        "sources": {
            SOURCE_ID: {"url": PDF_URL, "sha256": pdf_hash, "source_pdf_page": 6},
            API_SOURCE_ID: {
                "version": PINNED_VERSION,
                "structure_url": f"{API_BASE}/api/structure/WBL011/{PINNED_VERSION}",
                "structure_sha256": structure_hash,
                "response_sha256_by_settlement_code": response_hashes,
            },
        },
        "controls": {
            "ksh_2015_all_dwelling_band_sum": EXPECTED_ALL_BAND_TOTAL,
            "ksh_2015_occupied_dwelling_band_sum": EXPECTED_OCCUPIED_BAND_TOTAL,
            "ksh_2015_published_occupied_national_total": PUBLISHED_OCCUPIED_NATIONAL_TOTAL,
            "ksh_2015_occupied_settlement_totals": OCCUPIED_SETTLEMENT_TOTALS,
            "ksh_2015_rounding_residual": PUBLISHED_OCCUPIED_NATIONAL_TOTAL
            - EXPECTED_OCCUPIED_BAND_TOTAL,
            "wbl_2022_occupied_dwellings_by_settlement_code": wbl_values,
            "wbl_2022_occupied_dwellings": wbl_total,
            "proxy_family_house_dwellings": family_total,
            "proxy_multi_dwelling_dwellings": multi_total,
            "proxy_reconciliation_residual": wbl_total - family_total - multi_total,
        },
        "method": {
            "family_house_definition": "1-3 dwellings in building",
            "multi_dwelling_definition": "4 or more dwellings in building",
            "allocation": "2015 occupied-dwelling building-type share by settlement type applied to 2022 WBL011 occupied-dwelling count",
            "rounding": "ROUND_HALF_UP; multi-dwelling count is the settlement residual",
            "limitations": [
                "The 2015 survey and 2022 Census API have different reference years.",
                "Megyeszékhely is only an approximate match to MJV; Város is only an approximate match to EV.",
                "The proxy does not vary by county, construction period, wall, area, comfort, heating mode, or fuel.",
                "The proxy is not a heat-emitter observation and cannot establish heat-pump eligibility.",
            ],
        },
        "outputs": {},
    }
    for output_path in (source_csv, proxy_csv):
        output_bytes = output_path.read_bytes()
        manifest["outputs"][output_path.name] = {
            "sha256": sha256(output_bytes),
            "bytes": len(output_bytes),
        }
    manifest_json.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        "VALID: B02 building-type proxy "
        f"source_rows={len(source_records)} proxy_rows={len(proxy_rows)} "
        f"wbl={wbl_total} family={family_total} multi={multi_total} residual=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
