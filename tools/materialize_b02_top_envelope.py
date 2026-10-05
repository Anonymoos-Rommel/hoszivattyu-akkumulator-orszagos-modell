"""Regenerate only the existing derived P93/P96 top-envelope CSV artifacts.

--check compares canonical computations with both files without writing.
--write explicitly replaces those two files in this checkout, in dependency
order. No network access, raw source extraction or other output path is used.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, fields
import io
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.B02.hungarian_top_envelope_area import (
    StratumTopEnvelopeArea,
    reference_programme_top_envelope_surface,
)
from modules.B02.pitched_roof_poststate_u import (
    StratumTopEnvelopeThermalBound,
    reference_programme_top_envelope_thermal_surface,
)

P93_PATH = ROOT / "data/processed/b02/p93_hungarian_top_envelope_area.csv"
P96_PATH = ROOT / "data/processed/b02/p96_pitched_roof_top_envelope_thermal_surface.csv"
P93_NOTE = (
    "HU TABULA/EPISCOPE class-average A_Roof/A_C_Ref calibration applied to "
    "canonical heated-floor-area bounds. A_Roof is thermal-envelope top area "
    "and may represent roof plane or upper ceiling depending attic state. "
    "This is a reference-programme proxy, not realized geometry."
)
P96_NOTE = (
    "Current 9/2023 EKM Annex 1 section 1.1 supplies 0.17 W/m2K for structures "
    "enclosing heated attic space; P91 supplies zeta 0.10..0.20. H upper uses "
    "P93 top-envelope area upper and corrected U upper 0.204. Regulatory "
    "requirement/reference-programme bound only, not realized project performance."
)
P96_RENAMES = {
    "base_u_upper_w_m2k": "pitched_roof_base_u_upper_w_m2k",
    "zeta_lower": "pitched_roof_zeta_lower",
    "zeta_upper": "pitched_roof_zeta_upper",
    "corrected_u_upper_w_m2k": "pitched_roof_corrected_u_upper_w_m2k",
}


def _csv_bytes(names, records):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=names, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return stream.getvalue().encode("utf-8")


def p93_bytes():
    """Preserve the established P93 precision, ordering, schema and notes."""
    reference_programme_top_envelope_surface.cache_clear()
    records = []
    for item in reference_programme_top_envelope_surface():
        row = asdict(item)
        for name, value in row.items():
            if name.startswith("top_to_conditioned_floor_ratio_"):
                row[name] = f"{value:.2f}"
            elif name.startswith("top_envelope_area_"):
                row[name] = f"{value:.12f}"
        row["notes"] = P93_NOTE
        records.append(row)
    return _csv_bytes([field.name for field in fields(StratumTopEnvelopeArea)] + ["notes"], records)


def p96_bytes():
    """Use the P96 computation after its materialized P93 dependency is checked."""
    reference_programme_top_envelope_thermal_surface.cache_clear()
    records = []
    for item in reference_programme_top_envelope_thermal_surface():
        row = {}
        for name, value in asdict(item).items():
            if name in ("base_u_upper_w_m2k", "zeta_lower", "zeta_upper"):
                value = f"{value:.2f}"
            elif name == "corrected_u_upper_w_m2k":
                value = f"{value:.3f}"
            elif isinstance(value, float):
                value = f"{value:.12f}".rstrip("0").rstrip(".")
            row[P96_RENAMES.get(name, name)] = value
        row["notes"] = P96_NOTE
        records.append(row)
    names = [P96_RENAMES.get(field.name, field.name) for field in fields(StratumTopEnvelopeThermalBound)]
    return _csv_bytes(names + ["notes"], records)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    for path, render in ((P93_PATH, p93_bytes), (P96_PATH, p96_bytes)):
        expected = render()
        if args.write:
            path.write_bytes(expected)
            print(f"Wrote {path.relative_to(ROOT)}")
        elif not path.is_file() or path.read_bytes() != expected:
            print(f"Stale artifact: {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
        else:
            print(f"Verified {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
