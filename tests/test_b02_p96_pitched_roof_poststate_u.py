import csv
import unittest
from pathlib import Path

from modules.B02.national_design_load_input_coverage import (
    QUALIFIED_REFERENCE_PROGRAMME_COMPONENT_U_SURFACE,
    current_design_load_blockers,
    national_design_load_input_coverage,
)
from modules.B02.pitched_roof_poststate_u import (
    PITCHED_ROOF_BASE_U_UPPER_W_M2K,
    PITCHED_ROOF_CORRECTED_U_UPPER_W_M2K,
    PITCHED_ROOF_ZETA_LOWER,
    PITCHED_ROOF_ZETA_UPPER,
    QUALIFIED_REFERENCE_PROGRAMME_PITCHED_ROOF_U,
    p96_state,
    reference_programme_pitched_roof_u,
    reference_programme_top_envelope_thermal_surface,
    semantic_boundaries,
)


ROOT = Path(__file__).resolve().parents[1]
SURFACE = (
    ROOT / "data" / "processed" / "b02"
    / "p96_pitched_roof_top_envelope_thermal_surface.csv"
)
REG = ROOT / "registry" / "b02_p96_pitched_roof_poststate_u.csv"
P83_REG = ROOT / "registry" / "b02_p83_bounded_physical_state_surface.csv"
P91_REG = ROOT / "registry" / "b02_p91_reference_programme_thermal_bridge_correction.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
SOURCES = ROOT / "registry" / "sources.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P96_PITCHED_ROOF_POSTSTATE_U.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


class B02P96PitchedRoofPostStateUTests(unittest.TestCase):
    def test_exact_current_legal_and_corrected_values(self):
        self.assertEqual(PITCHED_ROOF_BASE_U_UPPER_W_M2K, 0.17)
        self.assertEqual(PITCHED_ROOF_ZETA_LOWER, 0.10)
        self.assertEqual(PITCHED_ROOF_ZETA_UPPER, 0.20)
        self.assertAlmostEqual(PITCHED_ROOF_CORRECTED_U_UPPER_W_M2K, 0.204)

        u = reference_programme_pitched_roof_u()
        self.assertEqual(
            u.status,
            QUALIFIED_REFERENCE_PROGRAMME_PITCHED_ROOF_U,
        )
        self.assertIsNone(u.blocker)
        self.assertAlmostEqual(u.base_u_upper_w_m2k, 0.17)
        self.assertAlmostEqual(u.corrected_u_upper_w_m2k, 0.204)

    def test_fourteen_stratum_top_envelope_thermal_surface(self):
        surface = reference_programme_top_envelope_thermal_surface()
        self.assertEqual(len(surface), 14)
        self.assertEqual(
            {(row.wbl_period_code, row.building_group) for row in surface},
            {
                (period, group)
                for period in (
                    "Y_LT1919",
                    "Y1919-1945",
                    "Y1946-1960",
                    "Y1961-1980",
                    "Y1981-2000",
                    "Y2001-2010",
                    "Y_GE2011",
                )
                for group in ("FAMILY_HOUSE", "MULTI_DWELLING")
            },
        )
        self.assertEqual(
            {row.base_u_upper_w_m2k for row in surface},
            {0.17},
        )
        self.assertTrue(
            all(
                abs(row.corrected_u_upper_w_m2k - 0.204) < 1e-12
                for row in surface
            )
        )
        self.assertAlmostEqual(
            max(row.top_envelope_h_upper_w_per_k_per_dwelling for row in surface),
            40.063968,
            places=9,
        )

    def test_materialized_csv_matches_runtime(self):
        data = rows(SURFACE)
        self.assertEqual(len(data), 14)
        self.assertEqual(
            {row["status"] for row in data},
            {"QUALIFIED_REFERENCE_PROGRAMME_PITCHED_ROOF_U"},
        )
        self.assertEqual(
            {float(row["pitched_roof_base_u_upper_w_m2k"]) for row in data},
            {0.17},
        )
        self.assertEqual(
            {float(row["pitched_roof_corrected_u_upper_w_m2k"]) for row in data},
            {0.204},
        )
        self.assertAlmostEqual(
            max(float(row["top_envelope_h_upper_w_per_k_per_dwelling"]) for row in data),
            40.063968,
        )

    def test_current_component_u_coverage_is_qualified(self):
        by = {item.input_id: item for item in national_design_load_input_coverage()}
        item = by["POST_RETROFIT_COMPONENT_U_VALUES"]
        self.assertEqual(
            item.status,
            QUALIFIED_REFERENCE_PROGRAMME_COMPONENT_U_SURFACE,
        )
        self.assertIsNone(item.blocker)
        self.assertIn("B02-P80", item.source_refs)
        self.assertIn("B02-P91", item.source_refs)
        self.assertIn("B02-P96", item.source_refs)
        self.assertIn("SRC-B06-HU-ENERGY-RULES-2023", item.source_refs)

        blockers = set(current_design_load_blockers())
        self.assertNotIn(
            "POST_RETROFIT_COMPONENT_U_VALUE_SURFACE_REQUIRED",
            blockers,
        )

    def test_p96_supersedes_without_rewriting_historical_slices(self):
        p83 = rows(P83_REG, "item_id")
        self.assertEqual(p83["B02-P83-S11"]["status"], "Q")
        self.assertEqual(
            p83["B02-P83-S11"]["residual_gap"],
            "PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED",
        )

        p91 = rows(P91_REG, "item_id")
        self.assertEqual(
            p91["B02-P91-T06"]["status"],
            "QUALIFIED_METHOD_BUT_U_Q",
        )
        self.assertEqual(
            p91["B02-P91-T06"]["residual_gap"],
            "PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED",
        )

        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P96-U04"]["status"],
            "RESOLVED_FOR_REFERENCE_PROGRAMME",
        )
        self.assertEqual(
            reg["B02-P96-U06"]["status"],
            "RESOLVED_FOR_REFERENCE_PROGRAMME_COMPONENT_U_SURFACE",
        )

    def test_provenance_and_nonpromotion_are_explicit(self):
        sources = rows(SOURCES, "source_id")
        note = sources["SRC-B06-HU-ENERGY-RULES-2023"]["notes"]
        self.assertIn("P96 pitched-roof authority", note)
        self.assertIn("0.17 W/m2K", note)
        self.assertIn("structures enclosing heated attic space", note)
        self.assertIn("not observed or guaranteed realized U", note)

        state = p96_state()
        self.assertEqual(state["stratum_count"], 14)
        self.assertEqual(
            state["status"],
            QUALIFIED_REFERENCE_PROGRAMME_PITCHED_ROOF_U,
        )
        self.assertIsNone(state["pitched_roof_blocker"])
        self.assertAlmostEqual(
            state["top_envelope_h_upper_global_w_per_k_per_dwelling"],
            40.063968,
        )

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P96", q["notes"])
        self.assertIn(
            "RESOLVED_FOR_REFERENCE_PROGRAMME_COMPONENT_U_SURFACE",
            q["notes"],
        )

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P96", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P96", peak["notes"])

    def test_semantic_boundaries_and_document_are_frozen(self):
        boundary = semantic_boundaries()
        for item in (
            "REGULATORY_U_REQUIREMENT_IS_NOT_OBSERVED_REALIZED_U",
            "HEATED_ATTIC_ENCLOSURE_IS_NOT_ALL_ROOF_GEOMETRY",
            "PITCHED_ROOF_U_BOUND_IS_NOT_ROOF_TYPE_PREVALENCE",
            "P91_ZETA_SIMPLIFIED_ROUTE_IS_NOT_DETAILED_PSI_CHI_ROUTE",
            "P96_SUPERSEDES_P80_PITCHED_GAP_IS_NOT_P80_SOURCE_REWRITE",
        ):
            self.assertIn(item, boundary)

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "structures enclosing heated attic space",
            "0.17 W/m2K",
            "0.204 W/m2K",
            "40.063968 W/K/dwelling",
            "P96 SUPERSEDES P80 PITCHED GAP != P80 SOURCE REWRITE",
            "B02 remains **55%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
