import csv
import unittest
from pathlib import Path

from modules.B05.fan_coil_authority_separation import (
    DOCUMENT_POLICY_RESPONSE_TIME_S,
    GOVERNANCE_TRANSITION,
    HEM_REFERENCE_CODE_5A3AC972,
    HEM_TP12_V3_DOCUMENT_POLICY,
    Q_AUTHORITY_OR_OBS_REQUIRED,
    Q_MIXED_POL_OBS_AUTHORITY,
    REFERENCE_CODE_RESPONSE_TIME_S,
    UPSTREAM_DIVERGENCE_FACT,
    evaluate_fan_coil_onoff,
    p31_boundary,
    resolve_fan_coil_response_time,
)
from modules.B05.hourly_onoff_parameter_policy import (
    FAN_COIL,
    HEM_DEFAULT_SCENARIO,
    HEM_FANCOIL_DIVERGENCE,
    resolve_emitter_response_time,
)

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
HP_SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
REG = ROOT / "registry" / "b05_p31_fancoil_authority_separation.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P31_FANCOIL_POL_OBS_AUTHORITY_SEPARATION.md"
README = ROOT / "modules" / "B05" / "README.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P31FanCoilAuthoritySeparationTests(unittest.TestCase):
    def test_p25_legacy_generic_fancoil_resolver_still_fails_closed(self):
        legacy = resolve_emitter_response_time(FAN_COIL)
        self.assertEqual(legacy.status, HEM_FANCOIL_DIVERGENCE)
        self.assertIsNone(legacy.value_s)

    def test_no_silent_policy_selection(self):
        result = resolve_fan_coil_response_time()
        self.assertEqual(result.status, Q_AUTHORITY_OR_OBS_REQUIRED)
        self.assertIsNone(result.value_s)
        self.assertEqual(result.evidence_status, "Q")

    def test_document_and_code_policy_branches_are_explicit_and_separate(self):
        doc = resolve_fan_coil_response_time(authority=HEM_TP12_V3_DOCUMENT_POLICY)
        code = resolve_fan_coil_response_time(authority=HEM_REFERENCE_CODE_5A3AC972)

        self.assertEqual(doc.value_s, DOCUMENT_POLICY_RESPONSE_TIME_S)
        self.assertEqual(doc.value_s, 1370.0)
        self.assertEqual(doc.evidence_status, "POL")

        self.assertEqual(code.value_s, REFERENCE_CODE_RESPONSE_TIME_S)
        self.assertEqual(code.value_s, 360.0)
        self.assertEqual(code.evidence_status, "POL")

        self.assertNotEqual(doc.authority, code.authority)

    def test_explicit_obs_path_requires_source_and_is_independent(self):
        q = resolve_fan_coil_response_time(obs_response_time_s=225.0)
        self.assertIsNone(q.value_s)
        self.assertEqual(q.evidence_status, "Q")

        obs = resolve_fan_coil_response_time(
            obs_response_time_s=225.0,
            obs_source_id="SRC-LAB-FANCOIL-X",
        )
        self.assertEqual(obs.value_s, 225.0)
        self.assertEqual(obs.evidence_status, "OBS")
        self.assertEqual(obs.source_id, "SRC-LAB-FANCOIL-X")

    def test_policy_and_obs_authorities_cannot_be_mixed(self):
        result = resolve_fan_coil_response_time(
            authority=HEM_REFERENCE_CODE_5A3AC972,
            obs_response_time_s=225.0,
            obs_source_id="SRC-LAB-FANCOIL-X",
        )
        self.assertEqual(result.status, Q_MIXED_POL_OBS_AUTHORITY)
        self.assertIsNone(result.value_s)

    def test_document_policy_runtime_is_pol(self):
        result = evaluate_fan_coil_onoff(
            minimum_continuous_compressor_power_kw=0.5,
            load_ratio=0.2,
            minimum_continuous_load_ratio=0.4,
            tau_policy=HEM_DEFAULT_SCENARIO,
            fan_coil_authority=HEM_TP12_V3_DOCUMENT_POLICY,
        )
        self.assertEqual(result.tau_eq_s, 140.0)
        self.assertEqual(result.emitter_response_time_s, 1370.0)
        self.assertEqual(result.evidence_status, "POL")
        self.assertAlmostEqual(
            result.onoff_inertia_power_kw,
            0.5 * 140.0 * 0.2 * 0.8 / 1370.0,
            places=12,
        )

    def test_obs_runtime_can_bypass_upstream_policy_conflict_without_using_policy_value(self):
        result = evaluate_fan_coil_onoff(
            minimum_continuous_compressor_power_kw=0.5,
            load_ratio=0.2,
            minimum_continuous_load_ratio=0.4,
            tau_policy=None,
            product_specific_tau_eq_s=90.0,
            obs_emitter_response_time_s=225.0,
            obs_emitter_source_id="SRC-LAB-FANCOIL-X",
        )
        self.assertEqual(result.tau_eq_s, 90.0)
        self.assertEqual(result.emitter_response_time_s, 225.0)
        self.assertEqual(result.evidence_status, "DER_FROM_EXPLICIT_PHYSICAL_INPUTS")
        self.assertAlmostEqual(
            result.onoff_inertia_power_kw,
            0.5 * 90.0 * 0.2 * 0.8 / 225.0,
            places=12,
        )

    def test_registry_preserves_divergence_but_resolves_governance_blocker(self):
        reg = {r["claim"]: r for r in rows(REG)}
        self.assertEqual(
            reg["HEM_FANCOIL_DOC_CODE_DIVERGENCE_FACT"]["status"],
            UPSTREAM_DIVERGENCE_FACT,
        )
        self.assertEqual(
            reg["HEM_FANCOIL_EMITTER_TIME_DOC_CODE_DIVERGENCE_REQUIRED"]["status"],
            GOVERNANCE_TRANSITION,
        )
        self.assertEqual(
            reg["FANCOIL_OBS_EMITTER_RESPONSE_EVIDENCE_REQUIRED"]["status"],
            "OPEN",
        )
        self.assertEqual(
            reg["PRODUCT_OR_LAB_TRANSIENT_TEST_RECORD_REQUIRED"]["status"],
            "OPEN",
        )

    def test_q_b05_004_and_readiness_keep_open_physical_residuals(self):
        q = {r["question_id"]: r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B05-P31 authority separation", q["notes"])
        self.assertIn("RESOLVED_BY_AUTHORITY_SEPARATION_NO_SILENT_SELECTION", q["notes"])
        self.assertIn("FANCOIL_OBS_EMITTER_RESPONSE_EVIDENCE_REQUIRED", q["notes"])
        self.assertIn("PRODUCT_OR_LAB_TRANSIENT_TEST_RECORD_REQUIRED", q["notes"])

        readiness = {r["component_id"]: r for r in rows(READINESS)}["PART_LOAD_MODULATION"]
        self.assertEqual(readiness["readiness_percent"], "45")
        self.assertIn("P27", readiness["notes"])
        self.assertIn("P28", readiness["notes"])
        self.assertIn("P31", readiness["notes"])
        self.assertIn("B05 remains 64%", readiness["notes"])

    def test_variables_keep_policy_and_obs_separate(self):
        variables = {r["variable_id"]: r for r in rows(VARIABLES)}
        self.assertEqual(variables["VAR-B05-EMITTER-RESPONSE-TIME"]["status"], "Q")
        self.assertEqual(
            variables["VAR-B05-FANCOIL-HEM-DOCUMENT-POLICY-RESPONSE-TIME"]["status"],
            "POL",
        )
        self.assertEqual(
            variables["VAR-B05-FANCOIL-HEM-CODE-POLICY-RESPONSE-TIME"]["status"],
            "POL",
        )
        self.assertEqual(
            variables["VAR-B05-FANCOIL-OBS-EMITTER-RESPONSE-TIME"]["status"],
            "Q",
        )

    def test_current_sources_and_documentation_are_pinned(self):
        sources = {r["source_id"]: r for r in rows(HP_SOURCES)}
        self.assertIn("SRC-B05-UK-HEM-TP12-HOURLY-ONOFF-2026", sources)
        self.assertIn("SRC-B05-UK-HEM-RUST-ONOFF-CONSTANTS-2026", sources)
        self.assertIn(
            "5a3ac9728df712332a5625571c43d3bc10bd2bf3",
            sources["SRC-B05-UK-HEM-RUST-ONOFF-CONSTANTS-2026"]["reference_period"],
        )

        text = PACK.read_text(encoding="utf-8")
        self.assertIn("UPSTREAM HEM POLICY DISAGREEMENT", text)
        self.assertIn("TIME_CONSTANT_SPACE_FAN_COILS", text)
        self.assertIn("PART_LOAD_MODULATION: 45% -> 45%", text)

        readme = README.read_text(encoding="utf-8")
        self.assertIn("B05-P31 separates the current HEM fan-coil", readme)

        boundary = p31_boundary()
        self.assertIn("NO_SILENT_FANCOIL_POLICY_SELECTION", boundary)
        self.assertIn("OBS_PATH_DOES_NOT_REQUIRE_UPSTREAM_HEM_RECONCILIATION", boundary)


if __name__ == "__main__":
    unittest.main()
