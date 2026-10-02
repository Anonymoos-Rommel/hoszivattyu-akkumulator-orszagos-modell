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
    # P10 remains historical; P11/P12/P13 now close the live physical-map question.
    questions = {r["question_id"]: r for r in _rows(QUESTIONS)}
    q = questions["Q-B05-001"]
    assert q["status"] == "RESOLVED"
    for authority in ("B05-P11", "B05-P12", "B05-P13", "RESOLVED_FOR_PHYSICAL_MODEL"):
        assert authority in q["notes"]
    assert "physical product-map acquisition question only" in q["notes"]
    assert "market share, Hungarian procurement/distribution, universal product qualification" in q["notes"]

    sources = {r["source_id"]: r for r in _rows(SOURCES)}
    for filename, claim, status, source_id in (
        ("b05_p11_teknopoint_cold_high_supply_rectangle.csv", "TEKNOPOINT_A0732_COLD_RECTANGLE",
         "QUALIFIED_COMPLETE_RECTANGLE", "SRC-B05-TEKNOPOINT-ATHENA-R32-2025"),
        ("b05_p12_ecpower_cross_manufacturer_cold_surface.csv", "ECPOWER_PMH6_COLD_RECTANGLE",
         "QUALIFIED_DER_COMPLETE_RECTANGLE", "SRC-B05-ECPOWER-PMH-2023"),
        ("b05_p13_wamak_extreme_cold_closure.csv", "WAMAK_AWK35_EXTREME_RECTANGLE",
         "QUALIFIED_MIXED_OBS_DER_RECTANGLE", "SRC-B05-WAMAK-AWK35-EVI-2026"),
    ):
        record = next(r for r in _rows(ROOT / "registry" / filename) if r["claim"] == claim)
        assert record["status"] == status
        assert record["authority"] == source_id
        assert record["allowed_use"] == "PRODUCT_SPECIFIC_BOUNDED_INTERPOLATION"
        assert sources[source_id]["evidence_status"] == "OBS"

    closure = next(r for r in _rows(ROOT / "registry" / "b05_p13_wamak_extreme_cold_closure.csv")
                   if r["claim"] == "Q-B05-001")
    assert closure["status"] == "RESOLVED_FOR_PHYSICAL_MODEL"
    assert closure["allowed_use"] == "PHYSICAL_PERFORMANCE_MAP"
    assert {"MARKET_SHARE_INFERENCE", "PROCUREMENT_AUTHORIZATION", "UNIVERSAL_PRODUCT_QUALIFICATION"} <= set(closure["forbidden_use"].split(";"))

    readiness = {r["component_id"]: r for r in _rows(READINESS)}
    assert readiness["PERFORMANCE_MAP"]["readiness_percent"] == "80"
    assert "SRC-B05-NIBE-S2125-IHB" in readiness["PERFORMANCE_MAP"]["source_ids"]
    assert readiness["WEATHER_PERFORMANCE_DOMAIN_COVERAGE"]["readiness_percent"] == "60"
    assert "SRC-B05-NIBE-S2125-IHB" in readiness["WEATHER_PERFORMANCE_DOMAIN_COVERAGE"]["source_ids"]


def load_tests(loader, tests, pattern):
    """Admit the explicit legacy cases to the configured unittest runner."""
    import unittest

    tests.addTests(
        unittest.FunctionTestCase(test, description=f"{__name__}.{test.__name__}")
        for test in (
            test_p10_preserves_complete_triple_and_defrost_boundaries,
            test_p10_source_and_pack_are_fail_closed,
            test_p10_three_supply_domains_cover_p9_stress,
            test_p10_updates_live_question_and_readiness_without_uplift,
        )
    )
    return tests
