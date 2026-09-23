import csv
import unittest
from pathlib import Path

from modules.B02.current_replaced_window_u_quality import (
    BME_TYPE5_WINDOW_U_FILTER_MAX_W_M2K,
    BME_TYPE5_WINDOW_U_FILTER_MIN_W_M2K,
    BME_TYPE5_WINDOW_U_MEAN_W_M2K,
    BME_TYPE5_WINDOW_U_SIGMA_W_M2K,
    CURRENT_REPLACED_WINDOW_U_UNRESOLVED,
    CURRENT_WOOD_PVC_U_MAX_W_M2K,
    P102_HP_ONLY_UPPER,
    P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR,
    P103_STATUS,
    PRIMARY_NEXT_RESIDUAL,
    REFERENCE_WINDOW_DEFICIT_VERIFIED_U,
    REFERENCE_WINDOW_SATISFIED_VERIFIED_U,
    assess_replaced_window,
    p103_state,
    regulatory_epochs,
    semantic_boundaries,
    type5_window_calibration,
)
from modules.B02.programme_envelope_action_selection_crosswalk import (
    REFERENCE_COMPONENT_U_MAX,
)


ROOT = Path(__file__).resolve().parents[1]
EPOCH = ROOT / "data" / "processed" / "b02" / "p103_window_regulatory_epoch_surface.csv"
EVIDENCE = ROOT / "data" / "processed" / "b02" / "p103_public_window_evidence_surface.csv"
P100_DATA = (
    ROOT / "data" / "processed" / "b02"
    / "p100_programme_envelope_action_selection_crosswalk.csv"
)
REG = ROOT / "registry" / "b02_p103_current_replaced_window_u_quality.csv"
SOURCES = ROOT / "registry" / "sources.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P103_CURRENT_REPLACED_WINDOW_U_QUALITY.md"
P100_DOC = ROOT / "docs" / "source_packs" / "B02_P100_PROGRAMME_ENVELOPE_ACTION_SELECTION_CROSSWALK.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


class B02P103CurrentReplacedWindowUQualityTests(unittest.TestCase):
    def test_current_reference_window_target_supersedes_historical_p80_value(self):
        self.assertAlmostEqual(CURRENT_WOOD_PVC_U_MAX_W_M2K, 1.10)
        self.assertAlmostEqual(REFERENCE_COMPONENT_U_MAX["WINDOW"], 1.10)

        p100 = rows(P100_DATA, "item_id")
        self.assertAlmostEqual(float(p100["B02-P100-T06"]["upper_value"]), 1.10)
        self.assertEqual(
            p100["B02-P100-T06"]["status"],
            "QUALIFIED_CURRENT_REFERENCE_PROGRAMME_TARGET",
        )
        self.assertIn("B02-P103", p100["B02-P100-T06"]["source_refs"])

        p100_doc = P100_DOC.read_text(encoding="utf-8")
        self.assertIn("1.10 W/m2K", p100_doc)
        self.assertIn("P80's **1.15 W/m2K**", p100_doc)

    def test_regulatory_epochs_are_exact_and_do_not_claim_realized_u(self):
        runtime = {x.epoch_id: x for x in regulatory_epochs()}
        self.assertEqual(
            set(runtime),
            {"PRE_2018_GENERIC", "POST_2017_ENERGY_SAVING", "CURRENT_9_2023"},
        )
        self.assertAlmostEqual(runtime["PRE_2018_GENERIC"].wood_pvc_u_max_w_m2k, 1.60)
        self.assertAlmostEqual(runtime["PRE_2018_GENERIC"].metal_u_max_w_m2k, 2.00)
        self.assertAlmostEqual(
            runtime["POST_2017_ENERGY_SAVING"].wood_pvc_u_max_w_m2k, 1.15
        )
        self.assertAlmostEqual(
            runtime["POST_2017_ENERGY_SAVING"].metal_u_max_w_m2k, 1.40
        )
        self.assertAlmostEqual(runtime["CURRENT_9_2023"].wood_pvc_u_max_w_m2k, 1.10)
        self.assertAlmostEqual(runtime["CURRENT_9_2023"].metal_u_max_w_m2k, 1.40)
        self.assertTrue(runtime["CURRENT_9_2023"].wood_pvc_matches_current_reference)
        self.assertFalse(runtime["CURRENT_9_2023"].metal_matches_current_reference)

        materialized = rows(EPOCH, "epoch_id")
        self.assertEqual(set(materialized), set(runtime))
        for key, item in runtime.items():
            row = materialized[key]
            self.assertAlmostEqual(
                float(row["wood_pvc_u_max_w_m2k"]),
                item.wood_pvc_u_max_w_m2k,
            )
            self.assertAlmostEqual(
                float(row["metal_u_max_w_m2k"]),
                item.metal_u_max_w_m2k,
            )

    def test_only_explicit_realized_uw_can_classify_reference_compliance(self):
        sat = assess_replaced_window(
            replacement_status_confirmed=True,
            realized_uw_w_m2k=1.09,
            evidence_status="OBS",
        )
        self.assertEqual(sat.state, REFERENCE_WINDOW_SATISFIED_VERIFIED_U)
        self.assertEqual(sat.blockers, ())

        deficit = assess_replaced_window(
            replacement_status_confirmed=True,
            realized_uw_w_m2k=1.11,
            evidence_status="OBS",
        )
        self.assertEqual(deficit.state, REFERENCE_WINDOW_DEFICIT_VERIFIED_U)

        legal_only = assess_replaced_window(
            replacement_status_confirmed=True,
            frame_material="WOOD_PVC",
            regulatory_epoch="CURRENT_9_2023",
        )
        self.assertEqual(legal_only.state, CURRENT_REPLACED_WINDOW_U_UNRESOLVED)
        self.assertEqual(
            legal_only.regulatory_validation_state,
            "CURRENT_REGULATORY_REQUIREMENT_AT_REFERENCE_BUT_REALIZED_U_UNVERIFIED",
        )
        self.assertEqual(legal_only.blockers, (PRIMARY_NEXT_RESIDUAL,))

        historical = assess_replaced_window(
            replacement_status_confirmed=True,
            frame_material="WOOD_PVC",
            regulatory_epoch="POST_2017_ENERGY_SAVING",
        )
        self.assertEqual(historical.state, CURRENT_REPLACED_WINDOW_U_UNRESOLVED)
        self.assertAlmostEqual(historical.regulatory_requirement_u_max_w_m2k, 1.15)
        self.assertEqual(
            historical.regulatory_validation_state,
            "REGULATORY_LIMIT_LOOSER_THAN_CURRENT_REFERENCE",
        )

        metal = assess_replaced_window(
            replacement_status_confirmed=True,
            frame_material="METAL",
            regulatory_epoch="CURRENT_9_2023",
        )
        self.assertAlmostEqual(metal.regulatory_requirement_u_max_w_m2k, 1.40)
        self.assertEqual(metal.state, CURRENT_REPLACED_WINDOW_U_UNRESOLVED)

        with self.assertRaises(ValueError):
            assess_replaced_window(
                replacement_status_confirmed=True,
                realized_uw_w_m2k=-1.0,
            )

    def test_bme_type5_window_calibration_is_exact_but_not_replaced_subset(self):
        x = type5_window_calibration()
        self.assertAlmostEqual(x.filter_min_u_w_m2k, BME_TYPE5_WINDOW_U_FILTER_MIN_W_M2K)
        self.assertAlmostEqual(x.filter_max_u_w_m2k, BME_TYPE5_WINDOW_U_FILTER_MAX_W_M2K)
        self.assertAlmostEqual(x.mean_u_w_m2k, BME_TYPE5_WINDOW_U_MEAN_W_M2K)
        self.assertAlmostEqual(x.sigma_u_w_m2k, BME_TYPE5_WINDOW_U_SIGMA_W_M2K)
        self.assertAlmostEqual(x.current_reference_z_from_mean, -2.116417910447761)
        self.assertIn("REPLACED_WINDOW_SUBSET_DISTRIBUTION", x.forbidden_use)
        self.assertIn("NATIONAL_WINDOW_POPULATION_DISTRIBUTION", x.forbidden_use)

        evidence = rows(EVIDENCE, "evidence_id")
        self.assertEqual(
            evidence["B02-P103-E04"]["status"],
            "QUALIFIED_TYPE5_EPC_CALIBRATION_DOMAIN",
        )
        self.assertAlmostEqual(float(evidence["B02-P103-E05"]["lower_value"]), 2.518)
        self.assertAlmostEqual(float(evidence["B02-P103-E06"]["lower_value"]), 0.670)

    def test_public_ksh_schema_does_not_mint_national_recency_or_u_distribution(self):
        evidence = rows(EVIDENCE, "evidence_id")
        self.assertEqual(
            evidence["B02-P103-E02"]["status"],
            "QUALIFIED_PUBLIC_SURVEY_SCHEMA",
        )
        self.assertEqual(
            evidence["B02-P103-E03"]["status"],
            "QUALIFIED_PUBLIC_SURVEY_SCHEMA",
        )
        self.assertIn(
            "PUBLIC_REPLACEMENT_RECENCY_X_FRAME_MATERIAL_CROSSWALK_REQUIRED",
            evidence["B02-P103-E03"]["residual_gap"],
        )

        state = p103_state()
        self.assertTrue(state["ksh_public_replacement_status_schema_available"])
        self.assertTrue(state["ksh_public_replacement_recency_schema_available"])
        self.assertFalse(state["ksh_public_recency_response_distribution_available"])
        self.assertFalse(
            state["public_frame_material_distribution_for_replaced_windows_available"]
        )
        self.assertFalse(
            state["public_realized_replaced_window_uw_distribution_available"]
        )

    def test_p103_does_not_change_p102_national_bounds_without_valid_window_distribution(self):
        state = p103_state()
        self.assertEqual(state["status"], P103_STATUS)
        self.assertEqual(
            state["window_target_temporal_repair"],
            "RESOLVED_1_15_TO_1_10",
        )
        self.assertFalse(
            state["national_replaced_window_reference_compliance_share_identified"]
        )
        self.assertFalse(state["p103_numeric_national_action_tightening"])
        self.assertAlmostEqual(
            state["p102_structural_calibrated_retrofit_floor_lower_share"],
            P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR,
        )
        self.assertEqual(state["hp_only_share_lower"], 0.0)
        self.assertAlmostEqual(state["hp_only_share_upper"], P102_HP_ONLY_UPPER)
        self.assertEqual(state["primary_residual"], PRIMARY_NEXT_RESIDUAL)

        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P103-U07"]["status"],
            "NOT_IDENTIFIED",
        )
        self.assertAlmostEqual(
            float(reg["B02-P103-U08"]["lower_bound"]),
            P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR,
        )

    def test_sources_project_state_and_boundaries_are_frozen(self):
        sources = rows(SOURCES, "source_id")
        self.assertIn("SRC-B02-HU-TNM-ENERGY-RULES-2006", sources)
        self.assertIn("SRC-B02-KSH-HKF-ENERGY-2020", sources)
        self.assertIn(
            "1.10 W/m2K",
            sources["SRC-B02-HU-ENERGY-RULES-2023"]["notes"],
        )
        self.assertIn(
            "mu=2.518",
            sources["SRC-B02-BME-RBSM-2026"]["notes"],
        )

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P103", q["notes"])
        self.assertIn(PRIMARY_NEXT_RESIDUAL, q["notes"])

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P103", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P103", peak["notes"])

        for boundary in (
            "LEGAL_U_REQUIREMENT_IS_NOT_VERIFIED_REALIZED_U",
            "WINDOW_REPLACED_STATUS_IS_NOT_REALIZED_U",
            "KSH_REPLACEMENT_RECENCY_IS_NOT_FRAME_MATERIAL",
            "BME_TYPE5_FULL_WINDOW_U_DISTRIBUTION_IS_NOT_REPLACED_WINDOW_U_DISTRIBUTION",
            "TYPE5_EPC_CALIBRATION_IS_NOT_NATIONAL_WINDOW_POPULATION_DISTRIBUTION",
            "REGULATORY_LIMIT_MATCH_IS_NOT_REALIZED_COMPLIANCE",
        ):
            self.assertIn(boundary, semantic_boundaries())

        doc = DOC.read_text(encoding="utf-8")
        for phrase in (
            "1.15 -> 1.10 W/m2K",
            "2.518 W/m2K",
            "0.670 W/m2K",
            "CURRENT_REPLACED_WINDOW_REALIZED_UW_DISTRIBUTION_REQUIRED",
            "82.7861029945%",
            "17.2138970055%",
            "**B02 remains 55%**",
        ):
            self.assertIn(phrase, doc)


if __name__ == "__main__":
    unittest.main()
