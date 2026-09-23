import csv
import json
import unittest
from pathlib import Path

from modules.B02.renovated_envelope_u_quality import (
    EXPECTED_OCCUPIED,
    NEXT_RESIDUALS,
    P102_STATUS,
    all_stratum_renovated_wall_quality,
    historical_renovated_component_audits,
    national_population_bounds,
    p102_state,
    semantic_boundaries,
    stratum_renovated_wall_quality,
    type_renovated_wall_quality,
)


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data" / "processed" / "b02" / "p102_historical_renovated_u_audit.csv"
TYPE = ROOT / "data" / "processed" / "b02" / "p102_current_wall_quality_surface.csv"
STRATUM = ROOT / "data" / "processed" / "b02" / "p102_renovated_wall_stratum_surface.csv"
REG = ROOT / "registry" / "b02_p102_renovated_envelope_u_quality.csv"
SOURCES = ROOT / "registry" / "sources.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P102_RENOVATED_ENVELOPE_U_QUALITY.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


class B02P102RenovatedEnvelopeUQualityTests(unittest.TestCase):
    def test_historical_component_audit_counts_are_exact(self):
        audits = {x.component: x for x in historical_renovated_component_audits()}
        self.assertEqual(
            (
                audits["EXTERNAL_WALL"].valid_type_count,
                audits["EXTERNAL_WALL"].deficit_mean_type_count,
                audits["EXTERNAL_WALL"].compliant_or_equal_mean_type_count,
                audits["EXTERNAL_WALL"].missing_or_nonphysical_type_count,
            ),
            (19, 19, 0, 4),
        )
        self.assertEqual(
            (
                audits["ATTIC_FLOOR"].valid_type_count,
                audits["ATTIC_FLOOR"].deficit_mean_type_count,
                audits["ATTIC_FLOOR"].compliant_or_equal_mean_type_count,
                audits["ATTIC_FLOOR"].missing_or_nonphysical_type_count,
            ),
            (14, 12, 2, 9),
        )
        self.assertEqual(
            (
                audits["FLAT_ROOF"].valid_type_count,
                audits["FLAT_ROOF"].deficit_mean_type_count,
                audits["FLAT_ROOF"].missing_or_nonphysical_type_count,
            ),
            (8, 8, 15),
        )
        self.assertEqual(
            (
                audits["PITCHED_ROOF"].valid_type_count,
                audits["PITCHED_ROOF"].deficit_mean_type_count,
                audits["PITCHED_ROOF"].compliant_or_equal_mean_type_count,
                audits["PITCHED_ROOF"].missing_or_nonphysical_type_count,
            ),
            (16, 15, 1, 7),
        )
        self.assertEqual(
            (
                audits["BASEMENT_CEILING"].valid_type_count,
                audits["BASEMENT_CEILING"].deficit_mean_type_count,
                audits["BASEMENT_CEILING"].missing_or_nonphysical_type_count,
            ),
            (11, 11, 12),
        )
        self.assertEqual(audits["WINDOW"].valid_type_count, 0)
        self.assertEqual(audits["WINDOW"].missing_or_nonphysical_type_count, 23)

        materialized = rows(AUDIT, "component")
        self.assertEqual(set(materialized), set(audits))
        for component, audit in audits.items():
            row = materialized[component]
            self.assertEqual(int(row["valid_type_count"]), audit.valid_type_count)
            self.assertEqual(
                int(row["deficit_mean_type_count"]),
                audit.deficit_mean_type_count,
            )
            self.assertEqual(
                int(row["missing_or_nonphysical_type_count"]),
                audit.missing_or_nonphysical_type_count,
            )

    def test_external_wall_tightening_is_type_mean_calibration_only(self):
        t1 = type_renovated_wall_quality(1)
        self.assertEqual(
            t1.historical_renovated_wall_state,
            "HISTORICAL_RENOVATED_TYPE_MEAN_ABOVE_REFERENCE",
        )
        self.assertAlmostEqual(t1.historical_renovated_wall_u_w_m2k, 0.64)
        self.assertAlmostEqual(t1.calibrated_wall_deficit_share, 1.0)
        self.assertAlmostEqual(t1.combined_calibrated_deficit_floor_share, 1.0)

        t12 = type_renovated_wall_quality(12)
        self.assertAlmostEqual(t12.historical_renovated_wall_u_w_m2k, 0.25)
        self.assertAlmostEqual(t12.calibrated_wall_deficit_share, 1.0)

        for type_id, expected_floor, expected_upper in (
            (11, 0.298, 0.572),
            (15, 0.265, 0.383),
            (16, 0.265, 0.383),
            (23, 0.106, 0.106),
        ):
            state = type_renovated_wall_quality(type_id)
            self.assertEqual(
                state.historical_renovated_wall_state,
                "HISTORICAL_RENOVATED_WALL_U_MISSING",
            )
            self.assertAlmostEqual(
                state.combined_calibrated_deficit_floor_share,
                expected_floor,
            )
            self.assertAlmostEqual(
                state.combined_calibrated_deficit_upper_share,
                expected_upper,
            )

        materialized = rows(TYPE, "type_id")
        self.assertEqual(len(materialized), 23)
        self.assertEqual(
            materialized["1"]["historical_renovated_wall_state"],
            "HISTORICAL_RENOVATED_TYPE_MEAN_ABOVE_REFERENCE",
        )
        self.assertEqual(
            materialized["23"]["historical_renovated_wall_state"],
            "HISTORICAL_RENOVATED_WALL_U_MISSING",
        )

    def test_all_fourteen_strata_propagate_complete_candidate_sets(self):
        runtime = {
            (x.wbl_period_code, x.building_group): x
            for x in all_stratum_renovated_wall_quality()
        }
        materialized = {
            (x["wbl_period_code"], x["building_group"]): x
            for x in rows(STRATUM)
        }
        self.assertEqual(len(runtime), 14)
        self.assertEqual(set(runtime), set(materialized))

        for key, state in runtime.items():
            row = materialized[key]
            self.assertEqual(
                ";".join(str(x) for x in state.candidate_type_ids),
                row["candidate_type_ids"],
            )
            self.assertAlmostEqual(
                state.calibrated_deficit_floor_lower_share,
                float(row["calibrated_deficit_floor_lower_share"]),
            )
            self.assertAlmostEqual(
                state.calibrated_deficit_floor_upper_share,
                float(row["calibrated_deficit_floor_upper_share"]),
            )

        self.assertAlmostEqual(
            stratum_renovated_wall_quality(
                "Y_LT1919", "FAMILY_HOUSE"
            ).calibrated_deficit_floor_lower_share,
            1.0,
        )
        self.assertAlmostEqual(
            stratum_renovated_wall_quality(
                "Y2001-2010", "MULTI_DWELLING"
            ).calibrated_deficit_floor_lower_share,
            0.106,
        )

    def test_national_runtime_tightens_p101_without_claiming_point_share(self):
        scenarios = national_population_bounds()
        self.assertEqual({x.scenario for x in scenarios}, {"CENTRAL", "FLAT"})
        for row in scenarios:
            self.assertAlmostEqual(row.occupied_dwellings, EXPECTED_OCCUPIED)
            self.assertGreater(
                row.calibrated_retrofit_floor_lower_share,
                0.37781217722501986,
            )
            self.assertLessEqual(
                row.calibrated_retrofit_floor_lower_share,
                row.calibrated_retrofit_floor_upper_share,
            )
            self.assertEqual(row.hp_only_share_lower, 0.0)
            self.assertAlmostEqual(
                row.hp_only_share_upper,
                1.0 - row.calibrated_retrofit_floor_lower_share,
            )
            self.assertEqual(row.residuals, NEXT_RESIDUALS)

        state = p102_state()
        self.assertEqual(state["status"], P102_STATUS)
        self.assertGreater(state["incremental_floor_gain"], 0.0)
        self.assertEqual(state["hp_only_share_lower"], 0.0)
        self.assertEqual(
            state["primary_residual"],
            "CURRENT_REPLACED_WINDOW_U_QUALITY_EVIDENCE_REQUIRED",
        )

        print(
            "B02_P102_STATE="
            + json.dumps(state, sort_keys=True, separators=(",", ":"))
        )

    def test_registry_sources_and_project_state_preserve_boundaries(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P102-U01"]["status"],
            "QUALIFIED_19_OF_23_ALL_VALID_MEANS_ABOVE_REFERENCE",
        )
        self.assertEqual(
            reg["B02-P102-U06"]["status"],
            "NO_HISTORICAL_REPLACED_WINDOW_U_VALUE",
        )

        sources = rows(SOURCES, "source_id")
        csok = sources["SRC-B02-HU-CSOKNYAI-HOUSING-STOCK-DISSERTATION-2022"]["notes"]
        self.assertIn("small renovated-case counts", csok)
        self.assertIn("N/A", csok)

        rekk = sources["SRC-B02-HU-REKK-TARKI-ENVELOPE-2022"]["notes"]
        self.assertIn("P102", rekk)
        self.assertIn("insulated facade", rekk)

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P102", q["notes"])
        self.assertIn("CURRENT_REPLACED_WINDOW_U_QUALITY_EVIDENCE_REQUIRED", q["notes"])

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P102", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P102", peak["notes"])

    def test_semantic_boundaries_and_document_are_frozen(self):
        boundary = semantic_boundaries()
        for item in (
            "HISTORICAL_RENOVATED_TYPE_MEAN_U_IS_NOT_CURRENT_RENOVATED_HOUSEHOLD_U",
            "RENOVATED_TYPE_MEAN_ABOVE_TARGET_IS_NOT_ALL_RENOVATED_HOUSEHOLDS_FAIL",
            "CALIBRATED_TYPE_BRANCH_DEFICIT_IS_NOT_OBSERVED_HOUSEHOLD_FAIL_SHARE",
            "CURRENT_INSULATED_ATTIC_IS_NOT_IDENTIFIED_P80_TOP_ENVELOPE_COMPONENT",
            "WINDOW_REPLACED_SHARE_IS_NOT_REPLACED_WINDOW_U",
        ):
            self.assertIn(item, boundary)

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "19/23",
            "CURRENT_REPLACED_WINDOW_U_QUALITY_EVIDENCE_REQUIRED",
            "MISSING_HISTORICAL_RENOVATED_WALL_U_TIGHTENING_REQUIRED",
            "WINDOW REPLACED SHARE != REPLACED WINDOW U",
            "**B02 remains 55%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
