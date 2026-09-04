import csv
import io
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.request
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRANCHE = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
PDF_URL = "https://www.eon.hu/content/dam/eon/eon-hungary/documents/hatarozatok-szabalyzatok-aram/EDE/2025/EDE_elo_usz_melleklet_20241209%20%28v1%29.pdf"
KSH_URL = "https://raw.githubusercontent.com/ferenci-tamas/IrszHnk/master/IrszHnk.csv"


class B10P48DdaszLocatorProbe(unittest.TestCase):
    def test_probe(self):
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pypdf==6.0.0"], check=True)
        from pypdf import PdfReader

        with tempfile.TemporaryDirectory() as td:
            pdf = Path(td) / "ddasz.pdf"
            urllib.request.urlretrieve(PDF_URL, pdf)
            reader = PdfReader(str(pdf))
            text = "\n".join((reader.pages[i].extract_text() or "") for i in range(6, 9))

        start = text.index("TERÜLETI ILLETÉKESSÉGE") + len("TERÜLETI ILLETÉKESSÉGE")
        body = text[start:]
        if "M2 SZ. MELLÉKLET" in body:
            body = body.split("M2 SZ. MELLÉKLET", 1)[0]
        body = re.sub(r"E\.ON Dél-dunántúli Áramhálózati Zrt\.\s*-\s*Elosztói Üzletszabályzat", " ", body)
        body = re.sub(r"M1 sz\. melléklet", " ", body)
        body = re.sub(r"EDE_elo_usz_melleklet_20241209", " ", body)
        body = re.sub(r"\n\s*[78910]\s*\n", " ", body)
        body = body.replace("\x0c", " ").replace("\u0002", "")
        body = re.sub(r"\s+", " ", body)
        tokens = [re.sub(r"\s+", " ", t).strip() for t in body.split(",")]
        tokens = [t for t in tokens if t and not re.fullmatch(r"\d+", t)]

        with urllib.request.urlopen(KSH_URL) as r:
            ksh_text = r.read().decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(ksh_text), delimiter=";"))
        whole = {}
        for r in rows:
            if not (r.get("Településrész") or "").strip():
                whole.setdefault(r["Helység.megnevezése"].strip(), []).append(r)

        with TRANCHE.open(encoding="utf-8", newline="") as f:
            existing = {
                (r["ksh_settlement_code"], r["settlement_name"])
                for r in csv.DictReader(f)
                if r["operator_id"] == "EON_DDASZ"
            }

        matched = []
        ambiguous = []
        unresolved = []
        for token in tokens:
            hits = whole.get(token, [])
            if len(hits) == 1:
                pair = (hits[0]["Helység.KSH.kódja"].zfill(5), token)
                matched.append(pair)
            elif len(hits) > 1:
                ambiguous.append((token, [(h["Helység.KSH.kódja"].zfill(5), h["Vármegye.megnevezése"]) for h in hits]))
            else:
                unresolved.append(token)

        matched_unique = sorted(set(matched))
        new_pairs = [p for p in matched_unique if p not in existing]
        print("P48_PROBE_TOKEN_COUNT", len(tokens))
        print("P48_PROBE_TOKEN_UNIQUE_COUNT", len(set(tokens)))
        print("P48_PROBE_EXISTING_COUNT", len(existing))
        print("P48_PROBE_MATCHED_UNIQUE_COUNT", len(matched_unique))
        print("P48_PROBE_NEW_PAIR_COUNT", len(new_pairs))
        print("P48_PROBE_AMBIGUOUS", repr(ambiguous))
        print("P48_PROBE_UNRESOLVED_COUNT", len(unresolved))
        print("P48_PROBE_UNRESOLVED_BEGIN")
        for x in unresolved:
            print(x)
        print("P48_PROBE_UNRESOLVED_END")
        print("P48_PROBE_NEW_PAIRS_BEGIN")
        for code, name in new_pairs:
            print(f"{code}|{name}")
        print("P48_PROBE_NEW_PAIRS_END")
        self.assertGreater(len(new_pairs), 100)


if __name__ == "__main__":
    unittest.main()
