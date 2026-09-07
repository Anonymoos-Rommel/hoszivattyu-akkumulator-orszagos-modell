import csv
import unittest
from pathlib import Path

from modules.B02.radiator_type_size_calibration import (
    P42_CLAIMS,
    RadiatorTypeSizeCandidate,
    assess_radiator_type_size,
    summarize_bounded_cohort,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_p50_radiator_type_size_calibration.csv"
P42 = ROOT / "registry" / "b02_p42_radiator_stock_requirement.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P50_RADIATOR_TYPE_SIZE_AND_LOW_TEMP_CALIBRATION.md"


def pecs_candidate(
    anchor_id="PECS_RADAL_V",
    radiator_type="RADAL 600-11",
    output=873,
    heat_loss=750,
    **overrides,
):
    values = dict(
        anchor_id=anchor_id,
        cohort_id="PECS_PANEL_FIVE_FLOOR_ROOM_CIRCUIT",
        role="DOCUMENTED_RESIDENTIAL_PARTIAL_CIRCUIT",
        source_quality="PEER_REVIEWED_ENGINEERING_CASE",
        source_url="https://ojs.emt.ro/EPKO/article/download/2032/2100/3148",
        exact_locator="PDF page 2/6 table 2",
        radiator_type_source_native=radiator_type,
        unit_count=1,
        residential_scope=True,
        current_stock_observation=False,
        whole_dwelling_inventory=False,
        same_cohort_binding=True,
        reproducible_binding=True,
        output_at_target_w=output,
        target_supply_temp_c=55,
        room_heat_loss_after_envelope_w=heat_loss,
        output_scope="RADIATOR_PLUS_PIPE",
        source_intervention_conclusion=(
            "FULL_ENVELOPE_CENTRAL_55C_NO_IN_DWELLING_CAPACITY_WORK_REQUIRED"
        ),
    )
    values.update(overrides)
    return RadiatorTypeSizeCandidate(**values)


def kerepes_candidates():
    common = dict(
        cohort_id="KEREPES_85M2_22K_SELF_REPORT",
        role="CURRENT_RESIDENTIAL_WHOLE_DWELLING",
        source_quality="PUBLIC_SELF_REPORT",
        source_url="https://qjob.hu/bekescsaba/munka/kazangepesz-allas",
        exact_locator="Kazancsere request for Kerepes 85 m2 family house",
        radiator_type_source_native="22K",
        residential_scope=True,
        current_stock_observation=True,
        whole_dwelling_inventory=True,
        same_cohort_binding=True,
        reproducible_binding=True,
        dwelling_count=1,
        floor_area_m2=85,
        height_mm=600,
        length_semantics="SOURCE_REPORTED_DIMENSION",
    )
    return [
        RadiatorTypeSizeCandidate(
            anchor_id="KEREPES_22K_H600_L1560",
            unit_count=2,
            length_mm=1560,
            **common,
        ),
        RadiatorTypeSizeCandidate(
            anchor_id="KEREPES_22K_H600_L730",
            unit_count=1,
            length_mm=730,
            **common,
        ),
        RadiatorTypeSizeCandidate(
            anchor_id="KEREPES_22K_H600_L600",
            unit_count=1,
            length_mm=600,
            **common,
        ),
        RadiatorTypeSizeCandidate(
            anchor_id="KEREPES_22K_H600_L400",
            unit_count=1,
            length_mm=400,
            **common,
        ),
    ]


def erdokertes_candidate(**overrides):
    values = dict(
        anchor_id="ERDOKERTES_22K_10",
        cohort_id="ERDOKERTES_HZ036690",
        role="CURRENT_RESIDENTIAL_WHOLE_DWELLING",
        source_quality="PUBLIC_PROPERTY_LISTING",
        source_url=(
            "https://ingatlan.jofogas.hu/pest/"
            "175_nm_es_haz_elado_Erdokertes_151880838.htm"
        ),
        exact_locator="engineering section: 10 db 22K type radiators installed",
        radiator_type_source_native="22K",
        unit_count=10,
        residential_scope=True,
        current_stock_observation=True,
        whole_dwelling_inventory=True,
        same_cohort_binding=True,
        reproducible_binding=True,
        dwelling_count=1,
        floor_area_m2=175,
    )
    values.update(overrides)
    return RadiatorTypeSizeCandidate(**values)


class B02P50RadiatorTypeSizeCalibrationTests(unittest.TestCase):
    def test_pecs_target_temperature_rows_are_bounded_and_numeric(self):
        rows = (
            pecs_candidate("PECS_RADAL_V", "RADAL 600-11", 873, 750),
            pecs_candidate("PECS_RADAL_IV", "RADAL 600-9", 627, 662),
            pecs_candidate("PECS_RADAL_III", "RADAL 600-10", 635, 662),
            pecs_candidate("PECS_RADAL_II", "RADAL 600-11", 636, 662),
            pecs_candidate("PECS_RADAL_I", "RADAL 600-22", 864, 782),
        )
        margins = [123.0, -35.0, -27.0, -26.0, 82.0]
        for candidate, margin in zip(rows, margins):
            with self.subTest(candidate=candidate.anchor_id):
                decision = assess_radiator_type_size(candidate)
                self.assertEqual(
                    decision.status, "QUALIFIED_BOUNDED_TYPE_SIZE_CALIBRATION"
                )
                self.assertTrue(decision.target_temp_performance_qualified)
                self.assertEqual(decision.room_capacity_margin_w, margin)
                self.assertFalse(decision.dwelling_ratio_qualified)
                self.assertFalse(decision.national_p42_authority)

    def test_negative_room_margin_does_not_make_candidate_fail_or_mint_change(self):
        candidate = pecs_candidate(
            "PECS_RADAL_IV", "RADAL 600-9", 627, 662
        )
        decision = assess_radiator_type_size(candidate)
        self.assertEqual(decision.room_capacity_margin_w, -35.0)
        self.assertEqual(
            candidate.source_intervention_conclusion,
            "FULL_ENVELOPE_CENTRAL_55C_NO_IN_DWELLING_CAPACITY_WORK_REQUIRED",
        )
        self.assertEqual(decision.status, "QUALIFIED_BOUNDED_TYPE_SIZE_CALIBRATION")

    def test_pecs_partial_circuit_has_exact_variant_mix_but_no_dwelling_ratio(self):
        candidates = [
            pecs_candidate("PECS_RADAL_V", "RADAL 600-11", 873, 750),
            pecs_candidate("PECS_RADAL_IV", "RADAL 600-9", 627, 662),
            pecs_candidate("PECS_RADAL_III", "RADAL 600-10", 635, 662),
            pecs_candidate("PECS_RADAL_II", "RADAL 600-11", 636, 662),
            pecs_candidate("PECS_RADAL_I", "RADAL 600-22", 864, 782),
        ]
        summary = summarize_bounded_cohort(candidates)
        self.assertEqual(summary.total_units, 5)
        self.assertIsNone(summary.units_per_dwelling)
        self.assertEqual(summary.type_share["RADAL 600-11"], 0.4)
        self.assertEqual(summary.type_share["RADAL 600-9"], 0.2)
        self.assertEqual(summary.type_share["RADAL 600-10"], 0.2)
        self.assertEqual(summary.type_share["RADAL 600-22"], 0.2)
        self.assertFalse(summary.national_p42_authority)

    def test_kerepes_complete_household_reconciles_five_units_and_size_mix(self):
        summary = summarize_bounded_cohort(kerepes_candidates())
        self.assertEqual(summary.total_units, 5)
        self.assertEqual(summary.dwelling_count, 1)
        self.assertEqual(summary.units_per_dwelling, 5.0)
        self.assertAlmostEqual(summary.units_per_100m2, 5 / 85 * 100)
        self.assertEqual(summary.type_share, {"22K": 1.0})
        self.assertEqual(summary.variant_share["22K|H600|L1560"], 0.4)
        self.assertEqual(summary.variant_share["22K|H600|L730"], 0.2)
        self.assertEqual(summary.variant_share["22K|H600|L600"], 0.2)
        self.assertEqual(summary.variant_share["22K|H600|L400"], 0.2)

    def test_kerepes_source_dimensions_are_not_normalized_to_catalogue_sizes(self):
        lengths = [candidate.length_mm for candidate in kerepes_candidates()]
        self.assertEqual(lengths, [1560, 730, 600, 400])
        self.assertNotIn(1600, lengths)
        self.assertNotIn(700, lengths)
        self.assertNotIn(720, lengths)

    def test_erdokertes_is_exact_type_count_with_unknown_size(self):
        decision = assess_radiator_type_size(erdokertes_candidate())
        summary = summarize_bounded_cohort([erdokertes_candidate()])
        self.assertEqual(decision.status, "QUALIFIED_BOUNDED_TYPE_SIZE_CALIBRATION")
        self.assertEqual(summary.total_units, 10)
        self.assertEqual(summary.units_per_dwelling, 10.0)
        self.assertAlmostEqual(summary.units_per_100m2, 10 / 175 * 100)
        self.assertEqual(summary.variant_share, {"22K": 1.0})

    def test_cross_cohort_pooling_is_forbidden(self):
        with self.assertRaisesRegex(ValueError, "CROSS_COHORT_POOLING_FORBIDDEN"):
            summarize_bounded_cohort([kerepes_candidates()[0], erdokertes_candidate()])

    def test_duplicate_anchor_cannot_be_double_counted(self):
        candidate = kerepes_candidates()[0]
        with self.assertRaisesRegex(ValueError, "DUPLICATE_ANCHOR_IN_COHORT"):
            summarize_bounded_cohort([candidate, candidate])

    def test_whole_dwelling_role_cannot_self_authorize_without_scope_gates(self):
        for override, reason in (
            ({"current_stock_observation": False}, "CURRENT_ROLE_WITHOUT_CURRENT_OBSERVATION"),
            ({"whole_dwelling_inventory": False}, "WHOLE_DWELLING_ROLE_WITHOUT_COMPLETE_INVENTORY"),
            ({"residential_scope": False}, "RESIDENTIAL_ROLE_WITHOUT_RESIDENTIAL_SCOPE"),
            ({"dwelling_count": None}, "WHOLE_DWELLING_ROLE_WITHOUT_DWELLING_COUNT"),
        ):
            with self.subTest(override=override):
                candidate = erdokertes_candidate(**override)
                decision = assess_radiator_type_size(candidate)
                self.assertEqual(decision.status, "Q")
                self.assertIn(reason, decision.reasons)

    def test_target_temperature_tuple_is_fail_closed(self):
        partial = pecs_candidate(room_heat_loss_after_envelope_w=None)
        no_scope = pecs_candidate(output_scope="NOT_REPORTED")
        self.assertEqual(assess_radiator_type_size(partial).status, "Q")
        self.assertIn(
            "PARTIAL_TARGET_TEMP_PERFORMANCE_TUPLE",
            assess_radiator_type_size(partial).reasons,
        )
        self.assertEqual(assess_radiator_type_size(no_scope).status, "Q")
        self.assertIn(
            "TARGET_PERFORMANCE_WITHOUT_OUTPUT_SCOPE",
            assess_radiator_type_size(no_scope).reasons,
        )

    def test_invalid_counts_dimensions_and_binding_fail_closed(self):
        cases = (
            {"unit_count": 0},
            {"unit_count": True},
            {"height_mm": -1},
            {"length_mm": 0},
            {"same_cohort_binding": False},
            {"reproducible_binding": False},
        )
        for override in cases:
            with self.subTest(override=override):
                decision = assess_radiator_type_size(erdokertes_candidate(**override))
                self.assertEqual(decision.status, "Q")

    def test_registry_materializes_exact_ten_bounded_rows(self):
        with REGISTRY.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 10)
        self.assertTrue(all(row["p42_national_authority"] == "NO" for row in rows))
        self.assertEqual(
            sum(int(row["unit_count"]) for row in rows if row["cohort_id"] == "PECS_PANEL_FIVE_FLOOR_ROOM_CIRCUIT"),
            5,
        )
        self.assertEqual(
            sum(int(row["unit_count"]) for row in rows if row["cohort_id"] == "KEREPES_85M2_22K_SELF_REPORT"),
            5,
        )
        self.assertEqual(
            sum(int(row["unit_count"]) for row in rows if row["cohort_id"] == "ERDOKERTES_HZ036690"),
            10,
        )

    def test_registry_freezes_published_55c_values_and_source_dimensions(self):
        with REGISTRY.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        by_id = {row["anchor_id"]: row for row in rows}
        self.assertEqual(by_id["PECS_RADAL_V"]["output_at_target_w"], "873")
        self.assertEqual(by_id["PECS_RADAL_IV"]["room_capacity_margin_w"], "-35")
        self.assertEqual(by_id["PECS_RADAL_I"]["radiator_type_source_native"], "RADAL 600-22")
        self.assertEqual(by_id["KEREPES_22K_H600_L1560"]["unit_count"], "2")
        self.assertEqual(by_id["KEREPES_22K_H600_L730"]["length_mm"], "730")
        self.assertEqual(by_id["ERDOKERTES_22K_10"]["height_mm"], "")
        self.assertEqual(by_id["ERDOKERTES_22K_10"]["length_mm"], "")

    def test_p42_five_national_claims_remain_q_and_disabled(self):
        with P42.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(tuple(row["claim_id"] for row in rows), P42_CLAIMS)
        self.assertTrue(all(row["current_status"] == "Q" for row in rows))
        self.assertTrue(all(row["programme_use_allowed"] == "NO" for row in rows))

    def test_document_freezes_model_intent_and_non_promotion_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for boundary in (
            "BOUNDED TYPE-SIZE OBSERVATION != NATIONAL TYPE-SIZE DISTRIBUTION",
            "PUBLIC SELF-REPORT != REPRESENTATIVE STOCK",
            "SOURCE-REPORTED DIMENSION != CATALOGUE NOMINAL SIZE",
            "PARTIAL ROOM CIRCUIT != WHOLE-DWELLING EMITTER INVENTORY",
            "HISTORICAL HEATING SURFACE M2 != PHYSICAL RADIATOR UNIT COUNT",
            "ZFR REQUIRED TABLE != PUBLICLY RECOVERED BENEFICIARY TABLE",
            "DUPLICATED PROPERTY/REQUEST COPY != INDEPENDENT OBSERVATION",
            "NON-RESIDENTIAL TYPE-SIZE MAPPING != RESIDENTIAL STOCK DISTRIBUTION",
            "BOUNDED COHORT SHARE != NATIONAL WEIGHT",
            "CROSS-COHORT POOLING WITHOUT EXPLICIT POPULATION WEIGHTS/DISJOINTNESS = FORBIDDEN",
        ):
            self.assertIn(boundary, text)
        self.assertIn(
            "POST-ENVELOPE ROOM HEAT LOSS + EXISTING EMITTER OUTPUT AT TARGET WATER TEMP + HYDRAULICS -> KEEP / UPSIZE / CHANGE",
            text,
        )
        self.assertIn("No external request, email or purchase is performed in P50.", text)

    def test_document_keeps_zfr_schema_separate_from_recovered_numeric_evidence(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("original radiator dimensions", text)
        self.assertIn("new radiator dimensions", text)
        self.assertIn("performance change", text)
        self.assertIn("water-temperature change", text)
        self.assertIn(
            "MANDATORY BENEFICIARY TABLE SCHEMA != PUBLICLY RECOVERED NUMERIC TABLE",
            text,
        )


if __name__ == "__main__":
    unittest.main()
