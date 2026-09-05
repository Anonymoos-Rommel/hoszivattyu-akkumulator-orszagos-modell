import csv
import hashlib
import io
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "registry/dso_service_area_membership_edasz_p49_pairs.csv"
TRANCHE = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
PDF_URL = "https://www.eon.hu/content/dam/eon/eon-hungary/documents/hatarozatok-szabalyzatok-aram/EED/2025/EED_elo_usz_melleklet_20241209%20%28v1%29.pdf"
KSH_URL = "https://raw.githubusercontent.com/ferenci-tamas/IrszHnk/master/IrszHnk.csv"
KSH_2019_URL = "https://www.ksh.hu/docs/hun/hnk/hnk_2019.pdf"

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pypdf==6.0.0", "cryptography>=3.1"], check=True)
from pypdf import PdfReader

with tempfile.TemporaryDirectory() as td:
    edasz_pdf = Path(td) / "edasz.pdf"
    ksh_pdf = Path(td) / "ksh2019.pdf"
    urllib.request.urlretrieve(PDF_URL, edasz_pdf)
    urllib.request.urlretrieve(KSH_2019_URL, ksh_pdf)
    reader = PdfReader(str(edasz_pdf))
    text = "\n".join((reader.pages[i].extract_text(extraction_mode="layout") or "") for i in range(6, 9))
    ksh_reader = PdfReader(str(ksh_pdf))
    ksh_2019_text = "\n".join((ksh_reader.pages[i].extract_text() or "") for i in range(103, min(125, len(ksh_reader.pages))))

start = re.search(r"\bAba\s*,", text)
assert start, "M1 start not found"
body = text[start.start():]
end = re.search(r"M2\s+(?:SZ\.|sz\.)\s+MELL[ÉE]KLET", body)
if end:
    body = body[:end.start()]
body = re.sub(r"E\.ON Észak-dunántúli Áramhálózati Zrt\.\s*-\s*Elosztói Üzletszabályzat", " ", body)
body = re.sub(r"M1\s+(?:SZ\.|sz\.)\s+melléklet", " ", body, flags=re.IGNORECASE)
body = re.sub(r"EED_elo_usz_melleklet_20241209", " ", body)
body = re.sub(r"\n\s*(?:7|8|9|10)\s*\n", " ", body)
body = body.replace("\x0c", " ").replace("\u0002", "")
body = re.sub(r"\s+", " ", body)
raw_tokens = [re.sub(r"\s+", " ", t).strip() for t in body.split(",")]
raw_tokens = [t for t in raw_tokens if t and not re.fullmatch(r"\d+", t)]

def repair(token):
    # Exact parser-only repairs corroborated against the official PDF text/rendering.
    if token == "P ázmándfalu":
        return "Pázmándfalu"
    if token == "Zsira 9":
        return "Zsira"
    return token

tokens = [repair(t) for t in raw_tokens]
repairs = [(a, b) for a, b in zip(raw_tokens, tokens) if a != b]
assert repairs == [("P ázmándfalu", "Pázmándfalu"), ("Zsira 9", "Zsira")], repairs
assert len(raw_tokens) == 874
assert len(set(tokens)) == 873

with urllib.request.urlopen(KSH_URL) as r:
    ksh_text = r.read().decode("utf-8-sig")
rows = list(csv.DictReader(io.StringIO(ksh_text), delimiter=";"))
by_name = {}
for r in rows:
    if (r.get("Településrész") or "").strip():
        continue
    name = r["Helység.megnevezése"].strip()
    pair = (r["Helység.KSH.kódja"].zfill(5), name)
    by_name.setdefault(name, set()).add(pair)

ksh2019 = {}
for line in ksh_2019_text.splitlines():
    m = re.match(r"^\s*(\d{5})\s+(.+?)\s*$", line)
    if not m:
        continue
    code, name = m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()
    name = re.sub(r"\s+1\. A helységek betűrendes névsorában.*$", "", name).strip()
    if name:
        ksh2019.setdefault(name, set()).add((code, name))

admitted = set()
direct = {}
unresolved = []
for token in tokens:
    pairs = by_name.get(token, set())
    if len(pairs) == 1:
        admitted.add(next(iter(pairs)))
    else:
        unresolved.append(token)
for token in unresolved:
    pairs = ksh2019.get(token, set())
    if len(pairs) == 1:
        pair = next(iter(pairs))
        admitted.add(pair)
        direct[token] = pair
assert direct == {"Jánossomorja": ("29221", "Jánossomorja")}, direct

with TRANCHE.open(encoding="utf-8", newline="") as f:
    existing = {(r["ksh_settlement_code"], r["settlement_name"]) for r in csv.DictReader(f) if r["operator_id"] == "EON_EDASZ"}
assert len(existing) == 45
# P39's two audited identity-specific equivalences remain historical and are not re-emitted.
assert {("15176", "Alcsútdoboz"), ("30526", "Alsóörs")} <= existing

candidates = sorted(admitted - existing)
assert len(candidates) == 775, len(candidates)

other_paths = [
    ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv",
    ROOT / "registry/dso_service_area_membership_crosswalk_opus_p44.csv",
    ROOT / "registry/dso_service_area_membership_crosswalk_demasz_p45.csv",
    ROOT / "registry/dso_service_area_membership_crosswalk_elmu_p46.csv",
    ROOT / "registry/dso_service_area_membership_emasz_p47_pairs.csv",
    ROOT / "registry/dso_service_area_membership_ddasz_p48_pairs.csv",
]
existing_by_code = {}
for path in other_paths:
    with path.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            code = r["ksh_settlement_code"]
            # Ignore historical EDASZ itself; candidate set already excludes it.
            if r.get("operator_id") == "EON_EDASZ":
                continue
            existing_by_code.setdefault(code, []).append((path.name, r.get("operator_id", ""), r["settlement_name"]))

collisions = [(code, name, existing_by_code[code]) for code, name in candidates if code in existing_by_code]
collision_codes = {c[0] for c in collisions}
final_pairs = [(code, name) for code, name in candidates if code not in collision_codes]

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["ksh_settlement_code", "settlement_name"])
    w.writerows(final_pairs)
canonical = "".join(f"{c}|{n}\n" for c, n in sorted(final_pairs))
digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
print("P49_EXPORT_RAW_TOKEN_COUNT", len(raw_tokens))
print("P49_EXPORT_UNIQUE_TOKEN_COUNT", len(set(tokens)))
print("P49_EXPORT_REPAIRS", repairs)
print("P49_EXPORT_ADMITTED_BEFORE_HISTORICAL", len(admitted))
print("P49_EXPORT_CANDIDATE_NEW_COUNT", len(candidates))
print("P49_EXPORT_COLLISION_COUNT", len(collisions))
print("P49_EXPORT_COLLISIONS_BEGIN")
for row in collisions:
    print(repr(row))
print("P49_EXPORT_COLLISIONS_END")
print("P49_EXPORT_FINAL_NEW_COUNT", len(final_pairs))
print("P49_EXPORT_FINAL_PAIR_DIGEST", digest)
