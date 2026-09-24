import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "docs" / "source_packs" / "B05_P10_NIBE_COLD_HIGH_SUPPLY_CAPACITY_DOMAIN.md"
REG = ROOT / "registry" / "b05_p10_nibe_cold_high_supply_capacity_domain.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"


def _rows(path):
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_p10_three_supply_domains_cover_p9_stress():
    rows = {r["claim"]: r for r in _rows(REG)}
    for claim in (
        "NIBE_W35_CONTINUOUS_CAPACITY_DOMAIN",
        "NIBE_W45_CONTINUOUS_CAPACITY_DOMAIN",
        "NIBE_W55_CONTINUOUS_CAPACITY_DOMAIN",
    ):
        row = rows[claim]
        assert row["status"] == "QUALIFIED_CAPACITY_DOMAIN"
        assert float(row["lower_bound"]) == -13.331944
        assert float(row["upper_bound"]) == -9.644444
        assert "COP_INFERENCE" in row["forbidden_use"]


def test_p10_preserves_complete_triple_and_defrost_boundaries():
    rows = {r["claim"]: r for r in _rows(REG)}
    q = rows["Q-B05-001"]
    assert q["status"] == "OPEN_NARROWED"
    for residual in (
        "SECOND_MANUFACTURER_COLD_W35_COMPLETE_TRIPLE_REQUIRED",
        "COLD_W45_TOTAL_INPUT_COP_SURFACE_REQUIRED",
        "COLD_W55_TOTAL_INPUT_COP_SURFACE_REQUIRED",
    ):
        assert residual in q["residual_gap"]

    d = rows["NIBE_CONTINUOUS_CURVE_DEFROST_BOUNDARY"]
    assert d["status"] == "QUALIFIED_EXCLUSION"
    assert "DEFROST_INCLUSIVE_RUNTIME_INFERENCE" in d["forbidden_use"]


def test_p10_source_and_pack_are_fail_closed():
    sources = {r["source_id"]: r for r in _rows(SOURCES)}
    assert "SRC-B05-NIBE-S2125-IHB" in sources
    assert sources["SRC-B05-NIBE-S2125-IHB"]["evidence_status"] == "OBS"

    text = PACK.read_text(encoding="utf-8")
    for phrase in (
        "CAPACITY CURVE != CAPACITY / INPUT / COP PERFORMANCE TRIPLE",
        "GRAPH DOMAIN COVERAGE != DIGITIZED EXACT PERFORMANCE VALUE",
        "DEFROST EXCLUDED != WINTER RUNTIME INCLUDING DEFROST",
        "Q-B05-001 remains `OPEN_NARROWED`",
        "B05 module readiness remains **64%**",
    ):
        assert phrase in text


def test_p10_updates_live_question_and_readiness_without_uplift():
    questions = {r["question_id"]: r for r in _rows(QUESTIONS)}
    q = questions["Q-B05-001"]
    assert q["status"] == "OPEN"
    assert "B05-P10" in q["notes"]
    assert "COLD_W45_TOTAL_INPUT_COP_SURFACE_REQUIRED" in q["notes"]

    readiness = {r["component_id"]: r for r in _rows(READINESS)}
    assert readiness["PERFORMANCE_MAP"]["readiness_percent"] == "80"
    assert "SRC-B05-NIBE-S2125-IHB" in readiness["PERFORMANCE_MAP"]["source_ids"]
    assert readiness["WEATHER_PERFORMANCE_DOMAIN_COVERAGE"]["readiness_percent"] == "60"
    assert "SRC-B05-NIBE-S2125-IHB" in readiness["WEATHER_PERFORMANCE_DOMAIN_COVERAGE"]["source_ids"]
