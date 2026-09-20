import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAPS = ROOT / "registry" / "b02_s0_s2_evidence_gap_matrix.csv"
BRIDGE = ROOT / "registry" / "b02_readiness_bridge.csv"
EFFECTS = ROOT / "data" / "processed" / "retrofit_effect_evidence.csv"
AUTHORITY = ROOT / "registry" / "b06_p60_s1_demand_outcome_authority.csv"


def csv_by(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


def test_s1_source_semantics_blocker_is_contracted_not_blanket_pass():
    gaps = csv_by(GAPS, "gap_id")
    row = gaps["GAP-B02-S1-DEMAND-OUTCOME"]
    assert row["status"] == "CONTRACTED"
    assert row["evidence_status"] == "DER"
    assert row["allow_for_gate"] == "partial"
    assert "Each real S0->S1 transition" in row["remaining_gap"]
    assert "no national completed-project microdata" in row["coverage_scope"]


def test_readiness_bridge_points_to_executable_record_gate():
    bridge = csv_by(BRIDGE, "bridge_id")["BR-B02-S1-DEMAND-OUTCOME"]
    assert bridge["status"] == "CONTRACTED"
    assert bridge["evidence_status"] == "OBS/DER_PER_RECORD"
    assert "modules/B06/s1_demand_outcome_gate.py" in bridge["current_source_or_registry"]
    assert bridge["allow_inference"] == "no"


def test_authority_refuses_national_effect_claim():
    rows = csv_by(AUTHORITY, "claim_id")
    row = rows["S1_DEMAND_OUTCOME_AUTHORITY"]
    assert row["current_status"] == "CONTRACTED"
    assert row["national_effect_claim"] == "NO"
    assert "MEASURED_USAGE:OBS" in row["admitted_paths"]
    assert "CERTIFIED_CALCULATION:DER" in row["admitted_paths"]


def test_hungarian_cases_are_bounded_and_not_engine_factors():
    effects = csv_by(EFFECTS, "evidence_id")

    cert = effects["B06-EFF-HU-KESZTHELY-CERT"]
    assert cert["status"] == "DER"
    assert cert["usable_for_engine"] == "NO"
    assert cert["annual_before_kwh_m2a"] == "220"
    assert cert["annual_after_min_kwh_m2a"] == "126"
    assert cert["annual_after_max_kwh_m2a"] == "129"
    assert cert["annual_reduction_fraction"] == ""

    billing = effects["B06-EFF-HU-KESZTHELY-BILLING"]
    assert billing["status"] == "Q"
    assert billing["usable_for_engine"] == "NO"
    assert billing["weather_normalization"] == "NOT_DISCLOSED"

    family = effects["B06-EFF-HU-FAMILY-GAS-3600-1600"]
    assert family["status"] == "Q"
    assert family["usable_for_engine"] == "NO"
    assert family["annual_reduction_fraction"] == "0.56"
    assert family["annual_before_kwh_m2a"] == ""
    assert family["annual_after_kwh_m2a"] == ""
