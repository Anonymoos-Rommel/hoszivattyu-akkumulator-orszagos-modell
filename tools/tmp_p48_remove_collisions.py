import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "registry/dso_service_area_membership_ddasz_p48_pairs.csv"
EXCLUDE = {("04109", "Dusnok"), ("16018", "Mélykút")}

with PATH.open(encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle))

before = {(r["ksh_settlement_code"], r["settlement_name"]) for r in rows}
assert EXCLUDE <= before, EXCLUDE - before
kept = [r for r in rows if (r["ksh_settlement_code"], r["settlement_name"]) not in EXCLUDE]
assert len(rows) == 779
assert len(kept) == 777
assert len({r["ksh_settlement_code"] for r in kept}) == 777

with PATH.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["ksh_settlement_code", "settlement_name"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(kept)

canonical = "".join(
    f'{r["ksh_settlement_code"]}|{r["settlement_name"]}\n'
    for r in sorted(kept, key=lambda r: (r["ksh_settlement_code"], r["settlement_name"]))
)
print("P48_COLLISION_EXCLUSIONS", sorted(EXCLUDE))
print("P48_FINAL_PAIR_COUNT", len(kept))
print("P48_FINAL_PAIR_DIGEST", hashlib.sha256(canonical.encode("utf-8")).hexdigest())
