import csv
import unittest
from pathlib import Path

from modules.B11.national_gas_displacement_inference import (
    Q_NATIONAL_GAS_DISPLACEMENT,
    QUALIFIED_NATIONAL_BOUNDED_GAS_DISPLACEMENT,
    appliance_class_population_control,
    assess_national_gas_displacement,
    blocker_repairs,
    exact_claim_boundary,
    repaired_requirement,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "b11_gas_appliance_class_population_control.csv"
REG = ROOT / "registry" / "b11_p6_national_gas_displacement_inference.csv"
DOC = ROOT / "docs" / "source_packs" / "P6_B11_NATIONAL_GAS_DISPLACEMENT_INFERENCE.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B11P6NationalGasDisplacementInferenceTests(unittest.TestCase):
    def test_weighted_hungarian_appliance_mix_is_materialized(self):
        rows_ = appliance_class_population_control()
        self.assertEqual(len(rows_), 3)
        self.assertAlmostEqual(sum(row.share for row in rows_), 1.0)
        shares = {row.appliance_class: row.share for row in rows_}
        self.assertEqual(
            shares,
            {
                "TRADITIONAL_GAS_BOILER": 0.2666,
                "CONDENSING_GAS_BOILER": 0.3273,
                "GAS_CONVECTOR": 0.4061,
            },
        )

    def test_exact_participant_mapping_not_required_for_national_bcm_layer(self):
        repair = repaired_requirement(
            "EXACT_PROGRAMME_PARTICIPANT_TO_GAS_QUALITY_POINT_MAPPING_REQUIRED"
        )
        self.assertEqual(
            repair.status,
            "RETIRED_AS_NATIONAL_BCM_PREREQUISITE",
        )
        self.assertIn("EXACT_MAPPING", repair.exact_claim_boundary)

    def test_public_repository_materialization_is_separate(self):
        repair = repaired_requirement(
            "PUBLIC_REPOSITORY_POINT_VALUE_MATERIALIZATION_REQUIRED"
        )
        self.assertEqual(
            repair.status,
            "RETIRED_AS_PUBLIC_REPOSITORY_PREREQUISITE",
        )
        self.assertIn("RAW_REPUBLICATION", repair.exact_claim_boundary)

    def test_appliance_mix_alone_does_not_create_efficiency(self):
        result = assess_national_gas_displacement(
            gas_population_bound=True,
            useful_heat_distribution=True,
            appliance_class_weights=True,
            class_specific_efficiency_bounds=False,
            temporally_aligned_gas_quality_distribution=False,
            multi_fuel_decomposition=False,
            dhw_cooking_boundary=False,
            rebound_boundary=False,
            calibration_to_observed_gas_sales=False,
            uncertainty_explicit=False,
        )
        self.assertEqual(result.status, Q_NATIONAL_GAS_DISPLACEMENT)
        self.assertIn(
            "APPLIANCE_CLASS_WEIGHTED_BOUNDED_SEASONAL_EFFICIENCY_REQUIRED",
            result.blockers,
        )
        self.assertIn(
            "APPLIANCE_MIX_AVAILABLE_BUT_EFFICIENCY_BOUNDS_MISSING",
            result.warnings,
        )

    def test_national_admission_does_not_require_exact_participant_mapping(self):
        result = assess_national_gas_displacement(
            gas_population_bound=True,
            useful_heat_distribution=True,
            appliance_class_weights=True,
            class_specific_efficiency_bounds=True,
            temporally_aligned_gas_quality_distribution=True,
            multi_fuel_decomposition=True,
            dhw_cooking_boundary=True,
            rebound_boundary=True,
            calibration_to_observed_gas_sales=True,
            uncertainty_explicit=True,
        )
        self.assertEqual(
            result.status,
            QUALIFIED_NATIONAL_BOUNDED_GAS_DISPLACEMENT,
        )
        self.assertEqual(result.blockers, ())

    def test_exact_claim_boundary_remains_fail_closed(self):
        boundary = exact_claim_boundary()
        self.assertIn(
            "SPECIFIC_PARTICIPANT_GAS_QUALITY_REQUIRES_EXACT_POINT_MAPPING",
            boundary,
        )
        self.assertIn(
            "SPECIFIC_POINT_GCV_LHV_REQUIRES_EXACT_POINT_PERIOD_EVIDENCE",
            boundary,
        )
        self.assertIn(
            "SPECIFIC_APPLIANCE_FUEL_VOLUME_REQUIRES_APPLICABLE_EFFICIENCY_EVIDENCE",
            boundary,
        )

    def test_four_legacy_requirements_have_explicit_repairs(self):
        repairs = blocker_repairs()
        self.assertEqual(len(repairs), 4)
        self.assertEqual(len({x.legacy_requirement for x in repairs}), 4)

    def test_materialized_csv_matches_population_control(self):
        with DATA.open(encoding="utf-8", newline="") as handle:
            data = list(csv.DictReader(handle))
        self.assertEqual(len(data), 3)
        self.assertEqual({row["sample_n"] for row in data}, {"657"})
        self.assertAlmostEqual(sum(float(row["share"]) for row in data), 1.0)

    def test_registry_and_document_freeze_nonpromotion(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B11-P6-R01"]["status"],
            "RETIRED_AS_NATIONAL_BCM_PREREQUISITE",
        )
        self.assertEqual(
            reg["B11-P6-R05"]["current_state"],
            "Q_NATIONAL_GAS_DISPLACEMENT",
        )
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "NATIONAL GAS QUALITY DISTRIBUTION != PARTICIPANT GAS-QUALITY POINT",
            "NATIONAL APPLIANCE CLASS MIX != SEASONAL EFFICIENCY DISTRIBUTION",
            "PUBLIC REPOSITORY MATERIALIZATION != MODEL USABILITY",
            "B11 remains **30%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
