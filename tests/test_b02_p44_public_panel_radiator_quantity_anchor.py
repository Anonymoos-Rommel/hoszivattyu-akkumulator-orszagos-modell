import csv
import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_p44_panel_radiator_quantity_anchor.csv"
P42 = ROOT / "registry" / "b02_p42_radiator_stock_requirement.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P44_PUBLIC_PANEL_RADIATOR_QUANTITY_ANCHOR.md"
MODULE = ROOT / "modules" / "B02" / "panel_radiator_quantity_anchor.py"

spec = importlib.util.spec_from_file_location("panel_radiator_quantity_anchor", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class B02P44PublicPanelRadiatorQuantityAnchorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with REGISTRY.open(encoding="utf-8", newline="") as fh:
            cls.rows = list(csv.DictReader(fh))
        cls.by_id = {row["anchor_id"]: row for row in cls.rows}

    def test_registry_has_exact_nine_bounded_anchors(self):
        self.assertEqual(len(self.rows), 9)
        self.assertEqual(len(self.by_id), 9)
        self.assertTrue(all(row["p42_national_authority"] == "NO" for row in self.rows))

    def test_arpadhidfo_dwelling_type_counts_reconcile_exactly(self):
        r40 = self.by_id["ARPADHIDFO_40M2_2015"]
        r61 = self.by_id["ARPADHIDFO_61M2_2015"]
        total = self.by_id["ARPADHIDFO_ALL_DWELLINGS_2015"]

        self.assertEqual(int(r40["dwelling_count"]), 20 * 12)
        self.assertEqual(int(r40["radiator_unit_count"]), 20 * 12 * 3)
        self.assertEqual(float(r40["radiators_per_dwelling"]), 3.0)
        self.assertEqual(int(r61["dwelling_count"]), 16 * 12)
        self.assertEqual(int(r61["radiator_unit_count"]), 16 * 12 * 5)
        self.assertEqual(float(r61["radiators_per_dwelling"]), 5.0)

        self.assertEqual(int(total["dwelling_count"]), 432)
        self.assertEqual(int(total["radiator_unit_count"]), 1680)
        self.assertEqual(int(total["cost_allocator_count"]), 1700)
        self.assertAlmostEqual(float(total["radiators_per_dwelling"]), 1680 / 432, places=6)
        self.assertEqual(int(total["cost_allocator_count"]) - int(total["radiator_unit_count"]), 20)

    def test_lehel_implemented_retrofit_quantities_and_ratios_are_bounded(self):
        row = self.by_id["LEHEL_2021_PANEL_RETROFIT"]
        self.assertEqual(row["evidence_status"], "OBS")
        self.assertEqual(int(row["dwelling_count"]), 2122)
        self.assertEqual(int(row["replacement_radiator_count"]), 3307)
        self.assertEqual(int(row["cost_allocator_count"]), 6709)
        self.assertAlmostEqual(float(row["cost_allocators_per_dwelling"]), 6709 / 2122, places=6)
        self.assertAlmostEqual(float(row["replacement_radiators_per_dwelling"]), 3307 / 2122, places=6)
        self.assertAlmostEqual(float(row["replacement_share_of_allocator_positions"]), 3307 / 6709, places=6)
        self.assertEqual(row["radiator_unit_count"], "")
        self.assertIn("not silently relabelled", row["notes"])

    def test_bme_matasz_large_current_segment_controls_are_frozen(self):
        sample = self.by_id["MATASZ_BME_2023_TAVHO_SAMPLE"]
        onepipe = self.by_id["MATASZ_BME_2023_ONEPIPE"]
        self.assertEqual(int(sample["dwelling_count"]), 499738)
        self.assertIn("75.4%", sample["exact_locator"])
        self.assertEqual(int(onepipe["dwelling_count"]), 257085)
        self.assertIn("21%", onepipe["exact_locator"])
        self.assertIn("6%", onepipe["exact_locator"])
        self.assertIn("73%", onepipe["exact_locator"])

    def test_baj_reference_and_pecs_existing_case_keep_distinct_semantics(self):
        baj = self.by_id["BAJ_2024_30_DWELLING_REFERENCE"]
        pecs = self.by_id["PECS_RADAL_GARZON_2025"]
        self.assertEqual(baj["claim_kind"], "REFERENCE_COST_ALLOCATOR_LAYOUT")
        self.assertEqual(int(baj["dwelling_count"]), 30)
        self.assertEqual(int(baj["cost_allocator_count"]), 110)
        self.assertAlmostEqual(float(baj["cost_allocators_per_dwelling"]), 110 / 30, places=6)
        self.assertEqual(baj["radiator_unit_count"], "")
        self.assertEqual(pecs["radiator_type"], "RADAL_600")
        self.assertEqual(float(pecs["radiators_per_dwelling"]), 3.0)
        self.assertIn("pipe emitters", pecs["notes"])

    def test_executable_anchor_gate_computes_only_bounded_ratios(self):
        candidate = mod.BoundedQuantityAnchor(
            anchor_id="TEST",
            source_id="SRC-TEST",
            evidence_status="OBS",
            scope_boundary="one building",
            dwelling_count=432,
            radiator_unit_count=1680,
            cost_allocator_count=1700,
            reproducible_binding=True,
        )
        decision = mod.assess_bounded_quantity_anchor(candidate)
        self.assertEqual(decision.status, "QUALIFIED")
        self.assertEqual(decision.reasons, ())
        self.assertAlmostEqual(decision.radiators_per_dwelling, 1680 / 432)
        self.assertAlmostEqual(decision.cost_allocators_per_dwelling, 1700 / 432)
        self.assertFalse(decision.national_p42_authority)

    def test_bounded_gate_fails_closed_and_never_mints_national_authority(self):
        invalid = mod.BoundedQuantityAnchor(
            anchor_id="",
            source_id="",
            evidence_status="ASS",
            scope_boundary="",
            dwelling_count=-1,
            reproducible_binding=False,
        )
        decision = mod.assess_bounded_quantity_anchor(invalid)
        self.assertEqual(decision.status, "Q")
        self.assertIn("NO_ANCHOR_ID", decision.reasons)
        self.assertIn("INVALID_EVIDENCE_STATUS", decision.reasons)
        self.assertIn("INVALID_DWELLING_COUNT", decision.reasons)
        self.assertFalse(decision.national_p42_authority)

    def test_p42_five_national_programme_quantities_remain_q(self):
        with P42.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(row["current_status"] == "Q" for row in rows))
        self.assertTrue(all(row["programme_use_allowed"] == "NO" for row in rows))

    def test_source_pack_freezes_programme_intent_and_non_promotion(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "HOW MANY + WHAT TYPE + KEEP/CHANGE + HOW MANY NEW UNITS -> B06",
            "PUBLIC RECOVERY != DATA REQUEST",
            "PANEL/TAVHO SEGMENT != ALL OCCUPIED DWELLINGS",
            "SEGMENT QUANTITY ANCHOR != NATIONAL P42 AUTHORITY",
            "40 m2 -> 3",
            "61 m2 -> 5",
            "3,307",
            "RADAL 600",
            "non-district central-hydronic residential segment",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
