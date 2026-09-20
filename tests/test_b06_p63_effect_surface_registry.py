import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "data" / "processed" / "retrofit_effect_surface_validation.csv"
DOMAINS = ROOT / "registry" / "b06_p63_effect_surface_domains.csv"
AUTHORITY = ROOT / "registry" / "b06_p63_effect_surface_authority.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def by(path, key):
    return {row[key]: row for row in rows(path)}


def reduction(existing, after):
    return (existing - after) / existing


def test_tabula_validation_has_three_distinct_hungarian_type_state_responses():
    data = by(VALIDATION, "validation_id")

    sfh_std = reduction(
        float(data["B06-P63-SFH01-BEL80-EXISTING"]["annual_net_heat_kwh_m2a"]),
        float(data["B06-P63-SFH01-BEL80-STANDARD"]["annual_net_heat_kwh_m2a"]),
    )
    mfh_std = reduction(
        float(data["B06-P63-MFH02-EXISTING"]["annual_net_heat_kwh_m2a"]),
        float(data["B06-P63-MFH02-STANDARD"]["annual_net_heat_kwh_m2a"]),
    )
    ab_std = reduction(
        float(data["B06-P63-AB03-IND-EXISTING"]["annual_net_heat_kwh_m2a"]),
        float(data["B06-P63-AB03-IND-STANDARD"]["annual_net_heat_kwh_m2a"]),
    )

    assert round(sfh_std, 6) == round((320.5 - 145.8) / 320.5, 6)
    assert round(mfh_std, 6) == round((136.4 - 60.0) / 136.4, 6)
    assert round(ab_std, 6) == round((89.9 - 56.3) / 89.9, 6)
    assert len({round(sfh_std, 6), round(mfh_std, 6), round(ab_std, 6)}) == 3

    ambitious = {
        round(reduction(320.5, 102.6), 6),
        round(reduction(136.4, 38.9), 6),
        round(reduction(89.9, 37.0), 6),
    }
    assert len(ambitious) == 3


def test_tabula_rows_are_validation_only_never_engine_defaults():
    data = rows(VALIDATION)
    assert len(data) == 9
    assert all(row["source_id"] == "SRC-B06-HU-TABULA-TYPOLOGY-2014" for row in data)
    assert all(row["evidence_class"] == "MODELLED_ARCHETYPE_REFERENCE" for row in data)
    assert all(row["usable_for_engine"] == "NO" for row in data)


def test_domains_do_not_mint_default_factors_or_national_prevalence():
    data = rows(DOMAINS)
    assert len(data) == 6
    assert all(row["engine_default_factor"] == "" for row in data)
    assert all(row["national_prevalence_claim"] == "NO" for row in data)
    assert all(row["status"] == "VALIDATION_ONLY" for row in data)


def test_p63_authority_is_parametric_not_percentage_lookup():
    authority = by(AUTHORITY, "claim_id")["TRANSFERABLE_RETROFIT_EFFECT_SURFACE"]
    assert authority["current_status"] == "CONTRACTED"
    assert authority["authority_type"] == "PARAMETRIC_PHYSICAL_STATE_SURFACE"
    assert authority["national_prevalence_claim"] == "NO"
    assert "monthly net space-heating balance" in authority["annual_method"]
    assert "Independent design heat load" in authority["peak_method"]
    assert "overlapping" in authority["double_count_contract"]


def test_q_b06_007_is_resolved_without_claiming_national_input_coverage():
    q = by(QUESTIONS, "question_id")["Q-B06-007"]
    assert q["status"] == "RESOLVED"
    assert "No generic percentage" in q["notes"]
    assert "missing physical inputs remain Q" in q["notes"]


def test_readiness_percentages_are_not_artificially_uplifted():
    r = by(READINESS, "component_id")
    assert r["RETROFIT_CONTRACT"]["readiness_percent"] == "70"
    assert r["ENVELOPE_PHYSICS"]["readiness_percent"] == "45"
    assert r["PEAK_LOAD_EFFECT"]["readiness_percent"] == "50"
    assert r["INTERVENTION_APPLICABILITY"]["readiness_percent"] == "25"
    assert "intentionally unchanged" in r["ENVELOPE_PHYSICS"]["notes"]
