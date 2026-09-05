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
PDF_URL = "https://www.eon.hu/content/dam/eon/eon-hungary/documents/hatarozatok-szabalyzatok-aram/EED/2025/EED_elo_usz_melleklet_20241209%20%28v1%29.pdf"
KSH_URL = "https://raw.githubusercontent.com/ferenci-tamas/IrszHnk/master/IrszHnk.csv"


def loose_key(value):
    value = unicodedata.normalize("NFD", value.casefold())
    value = "".join(c for c in value if unicodedata.category(c) != "Mn")
    return "".join(c for c in value if c.isalnum())


class B10P49EdaszLocatorProbe(unittest.TestCase):
    def test_probe(self):
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pypdf==6.0.0"], check=True)
        from pypdf import PdfReader

        with tempfile.TemporaryDirectory() as td:
            pdf = Path(td) / "edasz.pdf"
            urllib.request.urlretrieve(PDF_URL, pdf)
            reader = PdfReader(str(pdf))
            text = "\n".join(
                (reader.pages[i].extract_text(extraction_mode="layout") or "")
                for i in range(6, 9)
            )

        start = text.index("TERÜLETI ILLETÉKESSÉGE") + len("TERÜLETI ILLETÉKESSÉGE")
        body = text[start:]
        if "M2 SZ. MELLÉKLET" in body:
            body = body.split("M2 SZ. MELLÉKLET", 1)[0]
        body = re.sub(r"E\.ON Észak-dunántúli Áramhálózati Zrt\.\s*-\s*Elosztói Üzletszabályzat", " ", body)
        body = re.sub(r"M1 sz\. melléklet", " ", body)
        body = re.sub(r"EED_elo_usz_melleklet_20241209", " ", body)
        body = re.sub(r"\n\s*(?:7|8|9|10)\s*\n", " ", body)
        body = body.replace("\x0c", " ").replace("\u0002", "")
        body = re.sub(r"\s+", " ", body)
        tokens = [re.sub(r"\s+", " ", t).strip() for t in body.split(",")]
        tokens = [t for t in tokens if t and not re.fullmatch(r"\d+", t)]

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

        with TRANCHE.open(encoding="utf-8", newline="") as f:
            existing = {
                (r["ksh_settlement_code"], r["settlement_name"])
                for r in csv.DictReader(f)
                if r["operator_id"] == "EON_EDASZ"
            }

        matched = []
        ambiguous = []
        unresolved = []
        for token in tokens:
            pairs = whole_pairs_by_name.get(token, set())
            if len(pairs) == 1:
                matched.append(next(iter(pairs)))
            elif len(pairs) > 1:
                ambiguous.append((token, sorted(pairs)))
            else:
                unresolved.append(token)

        matched_unique = sorted(set(matched))
        new_pairs = [p for p in matched_unique if p not in existing]
        current_exact = set(matched_unique)
        old_present = sorted(existing & current_exact)
        old_absent = sorted(existing - current_exact)

        loose_candidates = []
        for token in unresolved:
            candidates = sorted(loose_index.get(loose_key(token), set()))
            if candidates:
                loose_candidates.append((token, candidates))

        print("P49_PROBE_TOKEN_COUNT", len(tokens))
        print("P49_PROBE_TOKEN_UNIQUE_COUNT", len(set(tokens)))
        print("P49_PROBE_EXISTING_COUNT", len(existing))
        print("P49_PROBE_MATCHED_UNIQUE_COUNT", len(matched_unique))
        print("P49_PROBE_NEW_PAIR_COUNT", len(new_pairs))
        print("P49_PROBE_AMBIGUOUS", repr(ambiguous))
        print("P49_PROBE_OLD_PRESENT_COUNT", len(old_present))
        print("P49_PROBE_OLD_ABSENT", repr(old_absent))
        print("P49_PROBE_UNRESOLVED_COUNT", len(unresolved))
        print("P49_PROBE_LOOSE_CANDIDATES_BEGIN")
        for token, candidates in loose_candidates:
            print(f"{token} => {candidates!r}")
        print("P49_PROBE_LOOSE_CANDIDATES_END")
        print("P49_PROBE_UNRESOLVED_BEGIN")
        for x in unresolved:
            print(x)
        print("P49_PROBE_UNRESOLVED_END")
        print("P49_PROBE_NEW_PAIRS_BEGIN")
        for code, name in new_pairs:
            print(f"{code}|{name}")
        print("P49_PROBE_NEW_PAIRS_END")
        self.assertGreater(len(tokens), 500)
        self.assertGreater(len(new_pairs), 500)


if __name__ == "__main__":
    unittest.main()
