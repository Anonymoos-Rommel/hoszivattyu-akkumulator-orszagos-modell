"""Verify B10 reference intake and optionally its four external-only TED PDFs.

Pass each exact source as --source SOURCE_ID=/local/file.pdf. This reads local
bytes only; it never acquires, archives or redistributes documents. Scope/VAT/
quantity interpretation remains a source-review obligation, not a regex claim.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from decimal import Decimal, localcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.B10.cost_reference import (  # noqa: E402
    BILL_ITEM, DATA_PATH, MANIFEST_PATH, CostReferenceError, load_reference_catalog,
)


def _amount(value):
    return Decimal(re.sub(r"\s", "", value).replace(",", "."))


def extract_winning_awards(text):
    """Select winner sections by lot; never take a minimum across all bids."""
    text = " ".join(text.split())
    blocks = re.split(r"6\.1\. Eredmény – részazonosító: (LOT-\d{4})", text)
    result = {}
    for index in range(1, len(blocks), 2):
        lot, block = blocks[index:index + 2]
        winner = block.split("6.1.2. Információk a nyertesekről", 1)
        if len(winner) != 2 or lot in result:
            raise CostReferenceError("one winner section per lot required")
        winner = re.split(r"6\.1\.[34]\.", winner[1], maxsplit=1)[0]
        prices = re.findall(r"Ajánlat értéke: ([\d ]+,\d{2}) (EUR|HUF)", winner)
        dates = re.findall(r"A szerződés megkötésének időpontja: (\d{2}/\d{2}/\d{4})", winner)
        if len(prices) != 1 or len(dates) != 1:
            raise CostReferenceError("one award amount and contract date required")
        result[lot] = dict(value=_amount(prices[0][0]), currency=prices[0][1], contract_date=dates[0])
    if not result:
        raise CostReferenceError("no winning award sections found")
    return result


def extract_amended_item(text):
    text = " ".join(text.split())
    parts = text.split("Változást követő tételek", 1)
    if len(parts) != 2:
        raise CostReferenceError("amended bill section absent")
    # Exact reviewed item and column boundaries; the old 80-m item is excluded.
    pattern = (r"122 236 Kábel építés 10 kV hálózaton m "
               r"(700) (32 640) (22 848 000) 122 237")
    matches = re.findall(pattern, parts[1])
    if len(matches) != 1:
        raise CostReferenceError("reviewed amended-item columns not found uniquely")
    return tuple(_amount(value) for value in matches[0])


def verify_external_sources(catalog, paths):
    if set(paths) != set(catalog.sources):
        raise CostReferenceError("provide exactly four source-ID/path bindings")
    checks = []
    for sid, source in catalog.sources.items():
        path = Path(paths[sid])
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != source["sha256"]:
            raise CostReferenceError(f"external source revision mismatch: {sid}")
        text = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                              check=True, capture_output=True, text=True, timeout=30).stdout
        rows = [r for r in catalog.observations.values() if r["source_id"] == sid]
        comparisons = 0
        if rows[0]["observation_kind"] == BILL_ITEM:
            extracted = extract_amended_item(text)
            expected = tuple(Decimal(rows[0]["facts"][k]["value"])
                             for k in ("quantity", "unit_price", "line_total"))
            with localcontext() as ctx:
                ctx.prec = 40
                if extracted != expected or extracted[0] * extracted[1] != extracted[2]:
                    raise CostReferenceError("amended item differs from curated record")
            comparisons = 3
        else:
            awards = extract_winning_awards(text)
            if set(awards) != {r["lot_or_item_id"] for r in rows}:
                raise CostReferenceError("source/curated lot-set mismatch")
            for row in rows:
                award = awards[row["lot_or_item_id"]]
                day = "/".join(reversed(row["contract_date"].split("-")))
                if award != dict(value=Decimal(row["facts"]["lot_amount"]["value"]),
                                 currency=row["currency"], contract_date=day):
                    raise CostReferenceError("winner price/currency/date mismatch")
                comparisons += 1
            totals = re.findall(r"Az értesítésben odaítélt összes szerződés értéke: "
                                r"([\d ]+,\d{2}) (EUR|HUF)", " ".join(text.split()))
            with localcontext() as ctx:
                ctx.prec = 40
                if len(totals) != 1 or _amount(totals[0][0]) != sum(a["value"] for a in awards.values()) or \
                        totals[0][1] != rows[0]["currency"]:
                    raise CostReferenceError("notice-total reconciliation mismatch")
            comparisons += 1
        checks.append(dict(source_id=sid, sha256=digest, numeric_row_checks=comparisons,
                           result="PASS"))
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="append", default=[], metavar="SOURCE_ID=PDF_PATH")
    args = parser.parse_args()
    try:
        catalog = load_reference_catalog()
        paths = {}
        for binding in args.source:
            sid, separator, path = binding.partition("=")
            if not separator or not path or sid in paths:
                raise CostReferenceError("unique SOURCE_ID=PDF_PATH required")
            paths[sid] = path
        checks = verify_external_sources(catalog, paths) if paths else []
        print(json.dumps({
            "result": "PASS", "observations": len(catalog.observations),
            "procurement_clusters": len({r["correlation_cluster_id"] for r in catalog.observations.values()}),
            "data_sha256": hashlib.sha256(DATA_PATH.read_bytes()).hexdigest(),
            "manifest_sha256": hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest(),
            "source_verification": "PASS" if checks else "NOT_RUN_NO_EXTERNAL_PDFS_SUPPLIED",
            "external_checks": checks,
            "scope_vat_quantity_review": "SEPARATE_MANUAL_SOURCE_REVIEW",
            "national_input_status": "Q_INSUFFICIENT_APPLICABILITY_AND_COHORT",
        }, ensure_ascii=False, indent=2))
    except (CostReferenceError, OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
