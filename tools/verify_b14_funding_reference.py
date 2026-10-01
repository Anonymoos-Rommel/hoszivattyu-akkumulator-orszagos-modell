"""Verify the dated B14 intake and optional exact external source snapshots.

--source SOURCE_ID=LOCAL_PATH must bind all eleven admitted sources. This tool
reads local files only. It never downloads, signs in, publishes or copies raw
source content into the repository. Targeted text checks complement exact-byte
identity; they do not replace manual table/scope interpretation.
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
from modules.B14.funding_reference import (  # noqa: E402
    AS_OF, CALL_SOURCES, CAPS_PATH, DATA_PATH, FAQ_SOURCE, MANIFEST_PATH,
    PROCEDURE_SOURCE, PROGRAMME_417, PROGRAMME_418,
    FundingReferenceError, load_funding_reference,
)


def _require(condition, message):
    if not condition:
        raise FundingReferenceError(message)


def _pdf_text(path):
    return subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True,
                          capture_output=True, text=True, timeout=30).stdout


def _normal(text):
    return " ".join(text.split())


def extract_call_finance(text):
    """Read four source-native finance rules; not an applicant funding result."""
    text = _normal(text)
    patterns = {
        "original_envelope": (r"Keretösszeg: ([\d,]+) milliárd forint", "1000000000"),
        "grant_share": (r"Finanszírozási összegen belül a vissza nem térítendő támogatás mértéke (\d+)%", "0.01"),
        "own_source_min_share": (r"Saját forrás elvárt mértéke a Projekt elszámolható költségének minimum (\d+)%", "0.01"),
    }
    result = {}
    with localcontext() as context:
        context.prec = 40
        for key, (pattern, multiplier) in patterns.items():
            matches = re.findall(pattern, text)
            _require(len(matches) == 1, f"unique source rule not found: {key}")
            result[key] = Decimal(matches[0].replace(",", ".")) * Decimal(multiplier)
        finance = re.findall(r"minimum bruttó ([\d,]+) millió forint [–-] maximum bruttó ([\d,]+) millió forint", text)
        _require(len(finance) == 1, "unique combined-finance limits not found")
        result["finance_min"], result["finance_max"] = (
            Decimal(v.replace(",", ".")) * Decimal("1000000") for v in finance[0])
    return result


def verify_external_sources(catalog, paths):
    """Verify all pinned source bytes, then selected facts/labels at their loci."""
    _require(set(paths) == set(catalog.sources), "provide exactly eleven source-ID/path bindings")
    checks = []
    call_reverse = {sid: pid for pid, sid in CALL_SOURCES.items()}
    for sid, source in catalog.sources.items():
        path = Path(paths[sid])
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        _require(digest == source["sha256"] and len(content) == source["bytes"],
                 f"external source revision mismatch: {sid}")
        comparison_count = 0
        if content.startswith(b"%PDF"):
            text = _pdf_text(path)
            normalized = _normal(text)
            if sid in call_reverse:
                pid = call_reverse[sid]
                facts = catalog.programmes[pid]["facts"]
                for name, value in extract_call_finance(text).items():
                    _require(value == Decimal(facts[name]["value"]), f"source rule mismatch: {name}")
                    comparison_count += 1
                _require("2025. október 15" in normalized and "2027. március 30" in normalized
                         and "2029. november 30" in normalized, "call date identity mismatch")
                comparison_count += 3
                if pid == PROGRAMME_417:
                    appendix = _normal(" ".join(text.split("\f")[20:23]))
                    for cap in catalog.caps.values():
                        for key in ("material_cap", "labour_cap"):
                            number = f"{int(cap[key]):,}".replace(",", " ")
                            _require(re.search(r"(?<!\d)" + re.escape(number) + r"(?!\d)", appendix),
                                     f"cap component absent from Annex 1: {cap['cap_id']} {key}")
                            comparison_count += 1
            elif sid == FAQ_SOURCE:
                pages = text.split("\f")
                _require("2026.szeptember" in _normal(pages[0]), "FAQ month identity mismatch")
                _require("várólistára" in pages[0] and "nincs megosztható, biztos információnk" in
                         _normal(pages[2]) and "Jelenleg erről nincs információnk" in _normal(pages[2]),
                         "dated FAQ uncertainty/queue evidence missing")
                comparison_count = 4
            elif "SUSPENSION" in sid:
                day = "2026.04.23." if "LHH" in sid else "2026.04.17."
                _require(day in normalized and "nyitvatartási idejének végéig" in normalized,
                         "closing-day evidence missing")
                comparison_count = 2
            elif sid == PROCEDURE_SOURCE:
                _require("10.8.2. SZÁMLÁK ZÁRADÉKOLÁSA" in _normal(text.split("\f")[39]),
                         "invoice-endorsement locus missing")
                comparison_count = 1
        elif "DOCUMENT-LIST" in sid:
            docs = json.loads(content)["documents"]
            pid = PROGRAMME_417 if "417" in sid else PROGRAMME_418
            call = catalog.sources[CALL_SOURCES[pid]]
            _require(len(docs) == 1 and docs[0]["_id"] == call["original_url"].rsplit("/", 1)[1]
                     and docs[0]["size"] == call["bytes"] and "20251015" in docs[0]["title"],
                     "official current document-list binding mismatch")
            comparison_count = 3
        else:
            _require("Benyújtás felfüggesztve" in content.decode("utf-8"),
                     "current MFB suspension label missing")
            comparison_count = 1
        checks.append(dict(source_id=sid,sha256=digest,result="PASS",
                           targeted_fact_or_locator_checks=comparison_count))
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="append", default=[], metavar="SOURCE_ID=LOCAL_PATH")
    args = parser.parse_args()
    try:
        catalog = load_funding_reference()
        paths = {}
        for binding in args.source:
            sid, separator, path = binding.partition("=")
            _require(bool(separator and path) and sid not in paths, "unique SOURCE_ID=LOCAL_PATH required")
            paths[sid] = path
        checks = verify_external_sources(catalog, paths) if paths else []
        print(json.dumps(dict(result="PASS",as_of=AS_OF,programmes=len(catalog.programmes),
            caps_417=len(catalog.caps),data_sha256=hashlib.sha256(DATA_PATH.read_bytes()).hexdigest(),
            caps_sha256=hashlib.sha256(CAPS_PATH.read_bytes()).hexdigest(),
            manifest_sha256=hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest(),
            external_source_verification="PASS" if checks else "NOT_RUN_NO_EXTERNAL_SOURCES_SUPPLIED",
            external_checks=checks,scope_and_cap_column_review="SEPARATE_MANUAL_SOURCE_REVIEW",
            availability_or_financing_result="NOT_PRODUCED",B15_gate="UNCHANGED"),ensure_ascii=False,indent=2))
    except (FundingReferenceError, OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
