import csv
import io
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unicodedata
import urllib.request
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRANCHE = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
PDF_URL = "https://www.eon.hu/content/dam/eon/eon-hungary/documents/hatarozatok-szabalyzatok-aram/EDE/2025/EDE_elo_usz_melleklet_20241209%20%28v1%29.pdf"
KSH_URL = "https://raw.githubusercontent.com/ferenci-tamas/IrszHnk/master/IrszHnk.csv"
KSH_2019_URL = "https://www.ksh.hu/docs/hun/hnk/hnk_2019.pdf"
HEADER_PREFIX = "E.ON Dél-dunántúli Áramhálózati Zrt. - Elosztói Üzletszabályzat "


def loose_key(value):
    value = unicodedata.normalize("NFD", value.casefold())
    value = "".join(c for c in value if unicodedata.category(c) != "Mn")
    return "".join(c for c in value if c.isalnum())


def repair_extraction_artifact(token):
    if token.startswith(HEADER_PREFIX):
        token = token[len(HEADER_PREFIX):].strip()
    if token == "S zaporca":
        token = "Szaporca"
    return token


class B10P48DdaszLocatorProbe(unittest.TestCase):
    def test_probe(self):
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pypdf==6.0.0"], check=True)
        from pypdf import PdfReader

        with tempfile.TemporaryDirectory() as td:
            ddasz_pdf = Path(td) / "ddasz.pdf"
            ksh_pdf = Path(td) / "ksh2019.pdf"
            urllib.request.urlretrieve(PDF_URL, ddasz_pdf)
            urllib.request.urlretrieve(KSH_2019_URL, ksh_pdf)

            reader = PdfReader(str(ddasz_pdf))
            text = "\n".join(
                (reader.pages[i].extract_text(extraction_mode="layout") or "")
                for i in range(6, 9)
            )

            ksh_reader = PdfReader(str(ksh_pdf))
            # KSH 2019 section IV: alphabetical locality-name / five-digit-ID registry.
            ksh_2019_text = "\n".join(
                (ksh_reader.pages[i].extract_text() or "")
                for i in range(103, min(125, len(ksh_reader.pages)))
            )

        start = text.index("TERÜLETI ILLETÉKESSÉGE") + len("TERÜLETI ILLETÉKESSÉGE")
        body = text[start:]
        if "M2 SZ. MELLÉKLET" in body:
            body = body.split("M2 SZ. MELLÉKLET", 1)[0]
        body = re.sub(r"E\.ON Dél-dunántúli Áramhálózati Zrt\.\s*-\s*Elosztói Üzletszabályzat", " ", body)
        body = re.sub(r"M1 sz\. melléklet", " ", body)
        body = re.sub(r"EDE_elo_usz_melleklet_20241209", " ", body)
        body = re.sub(r"\n\s*(?:7|8|9|10)\s*\n", " ", body)
        body = body.replace("\x0c", " ").replace("\u0002", "")
        body = re.sub(r"\s+", " ", body)
        raw_tokens = [re.sub(r"\s+", " ", t).strip() for t in body.split(",")]
        raw_tokens = [t for t in raw_tokens if t and not re.fullmatch(r"\d+", t)]
        tokens = [repair_extraction_artifact(t) for t in raw_tokens]

        extraction_repairs = [
            (raw, fixed) for raw, fixed in zip(raw_tokens, tokens) if raw != fixed
        ]

        with urllib.request.urlopen(KSH_URL) as r:
            ksh_text = r.read().decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(ksh_text), delimiter=";"))
        whole_pairs_by_name = {}
        loose_index = {}
        for r in rows:
            if (r.get("Településrész") or "").strip():
                continue
            name = r["Helység.megnevezése"].strip()
            pair = (r["Helység.KSH.kódja"].zfill(5), name)
            whole_pairs_by_name.setdefault(name, set()).add(pair)
            loose_index.setdefault(loose_key(name), set()).add(pair)

        ksh_2019_by_name = {}
        for line in ksh_2019_text.splitlines():
            m = re.match(r"^\s*(\d{5})\s+(.+?)\s*$", line)
            if not m:
                continue
            code, name = m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()
            # Strip page-continuation heading if extraction appends it to the final row.
            name = re.sub(r"\s+1\. A helységek betűrendes névsorában.*$", "", name).strip()
            if name:
                ksh_2019_by_name.setdefault(name, set()).add((code, name))

        with TRANCHE.open(encoding="utf-8", newline="") as f:
            existing = {
                (r["ksh_settlement_code"], r["settlement_name"])
                for r in csv.DictReader(f)
                if r["operator_id"] == "EON_DDASZ"
            }

        matched = []
        unresolved = []
        for token in tokens:
            pairs = whole_pairs_by_name.get(token, set())
            if len(pairs) == 1:
                matched.append(next(iter(pairs)))
            else:
                unresolved.append(token)

        matched_unique = set(matched)
        direct_2019 = {}
        still_unresolved = []
        for token in unresolved:
            pairs = ksh_2019_by_name.get(token, set())
            if len(pairs) == 1:
                direct_2019[token] = next(iter(pairs))
            else:
                still_unresolved.append(token)

        admitted = matched_unique | set(direct_2019.values())
        new_pairs = sorted(admitted - existing)
        old_present = sorted(existing & admitted)
        old_absent = sorted(existing - admitted)

        loose_candidates = []
        for token in still_unresolved:
            candidates = sorted(loose_index.get(loose_key(token), set()))
            if candidates:
                loose_candidates.append((token, candidates))

        print("P48_PROBE_RAW_TOKEN_COUNT", len(raw_tokens))
        print("P48_PROBE_TOKEN_UNIQUE_COUNT", len(set(tokens)))
        print("P48_PROBE_EXTRACTION_REPAIRS", repr(extraction_repairs))
        print("P48_PROBE_EXISTING_COUNT", len(existing))
        print("P48_PROBE_LOCATOR_MATCHED_UNIQUE_COUNT", len(matched_unique))
        print("P48_PROBE_KSH2019_DIRECT_COUNT", len(direct_2019))
        print("P48_PROBE_KSH2019_DIRECT_BEGIN")
        for token, pair in sorted(direct_2019.items()):
            print(f"{token} => {pair[0]}|{pair[1]}")
        print("P48_PROBE_KSH2019_DIRECT_END")
        print("P48_PROBE_ADMITTED_CURRENT_COUNT", len(admitted))
        print("P48_PROBE_NEW_PAIR_COUNT", len(new_pairs))
        print("P48_PROBE_OLD_PRESENT_COUNT", len(old_present))
        print("P48_PROBE_OLD_ABSENT", repr(old_absent))
        print("P48_PROBE_STILL_UNRESOLVED_COUNT", len(still_unresolved))
        print("P48_PROBE_LOOSE_CANDIDATES_BEGIN")
        for token, candidates in loose_candidates:
            print(f"{token} => {candidates!r}")
        print("P48_PROBE_LOOSE_CANDIDATES_END")
        print("P48_PROBE_NEW_PAIRS_BEGIN")
        for code, name in new_pairs:
            print(f"{code}|{name}")
        print("P48_PROBE_NEW_PAIRS_END")
        self.assertEqual(1116, len(raw_tokens))
        self.assertEqual(43, len(old_present))
        self.assertFalse(old_absent)
        self.assertGreater(len(new_pairs), 770)


if __name__ == "__main__":
    unittest.main()
