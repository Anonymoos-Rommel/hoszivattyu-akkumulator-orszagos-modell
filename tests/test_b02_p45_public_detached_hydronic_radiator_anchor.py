import csv
import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_p45_detached_hydronic_radiator_anchor.csv"
P42 = ROOT / "registry" / "b02_p42_radiator_stock_requirement.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P45_PUBLIC_DETACHED_HYDRONIC_RADIATOR_ANCHOR.md"
MODULE = ROOT / "modules" / "B02" / "detached_hydronic_radiator_anchor.py"

spec = importlib.util.spec_from_file_location("detached_hydronic_radiator_anchor", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class B02P45PublicDetachedHydronicRadiatorAnchorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with REGISTRY.open(encoding="utf-8", newline="") as fh:
            cls.rows = list(csv.DictReader(fh))
        cls.by_id = {row["anchor_id"]: row for row in cls.rows}

    def test_registry_has_exact_seven_bounded_anchors(self):
        self.assertEqual(len(self.rows), 7)
        self.assertEqual(len(self.by_id), 7)
        self.assertTrue(all(row["p42_national_authority"] == "NO" for row in self.rows))

    def test_household_quantity_anchors_are_exact_and_bounded(self):
        expected = {
            "URI_70M2_PURMO_2026": (70, 4),
            "JASZFENYSZARU_77M2_2026": (77, 6),
            "SZENTLORINCKATA_86M2_2026": (86, 8),
        }
        for anchor_id, (area, count) in expected.items():
            row = self.by_id[anchor_id]
            self.assertEqual(row["source_quality"], "PUBLIC_LISTING")
            self.assertEqual(int(row["dwelling_count"]), 1)
            self.assertEqual(int(row["floor_area_m2"]), area)
            self.assertEqual(int(row["radiator_unit_count"]), count)
            self.assertEqual(float(row["radiators_per_dwelling"]), float(count))
            self.assertAlmostEqual(float(row["radiators_per_100m2"]), count / area * 100, places=6)

    def test_uri_anchor_preserves_type_split(self):
        row = self.by_id["URI_70M2_PURMO_2026"]
        self.assertIn("PURMO", row["radiator_type"])
        self.assertIn("towel-rail", row["radiator_type"])
        self.assertEqual(row["generator_type"], "21_KW_WATER_FIREPLACE")

    def test_sopron_is_replacement_quantity_not_existing_stock_count(self):
        row = self.by_id["SOPRON_120M2_RETROFIT_2026"]
        self.assertEqual(row["source_quality"], "IMPLEMENTED_REFERENCE")
        self.assertEqual(row["radiator_unit_count"], "")
        self.assertEqual(int(row["replacement_radiator_count"]), 7)
        self.assertEqual(float(row["replacement_radiators_per_dwelling"]), 7.0)
        self.assertIn("does not prove", row["notes"])

    def test_type_only_anchor_does_not_invent_quantity(self):
        row = self.by_id["NEMETKER_150M2_22K_2026"]
        self.assertEqual(row["radiator_type"], "22K_PANEL_RADIATOR")
        self.assertEqual(row["radiator_unit_count"], "")
        self.assertEqual(row["replacement_radiator_count"], "")
        self.assertIn("not stated", row["notes"])

    def test_engineering_controls_are_not_quantity_observations(self):
        proreno = self.by_id["PROReno_KEEP_CHANGE_2026"]
        mezofalva = self.by_id["MEZOFALVA_KADAR_LOW_TEMP_2017"]
        for row in (proreno, mezofalva):
            self.assertEqual(row["source_quality"], "ENGINEERING_GUIDANCE")
            self.assertEqual(row["radiator_unit_count"], "")
            self.assertEqual(row["replacement_radiator_count"], "")
            self.assertEqual(row["p42_national_authority"], "NO")
        self.assertIn("65-70 C", proreno["exact_locator"])
        self.assertIn("45-55 C", proreno["exact_locator"])
        self.assertIn("double", mezofalva["exact_locator"])
        self.assertIn("5.7 kW", mezofalva["exact_locator"])

    def test_executable_gate_computes_only_bounded_household_ratios(self):
        candidate = mod.DetachedHydronicAnchor(
            anchor_id="TEST",
            source_id="SRC-TEST",
            evidence_status="OBS",
            source_quality="PUBLIC_LISTING",
            scope_boundary="one dwelling",
            floor_area_m2=86,
            dwelling_count=1,
            radiator_unit_count=8,
            generator_type="GAS_BOILER",
            reproducible_binding=True,
        )
        decision = mod.assess_detached_hydronic_anchor(candidate)
        self.assertEqual(decision.status, "QUALIFIED")
        self.assertEqual(decision.reasons, ())
        self.assertEqual(decision.radiators_per_dwelling, 8.0)
        self.assertAlmostEqual(decision.radiators_per_100m2, 8 / 86 * 100)
        self.assertFalse(decision.national_p42_authority)

    def test_gate_fails_closed_and_never_mints_national_authority(self):
        invalid = mod.DetachedHydronicAnchor(
            anchor_id="",
            source_id="",
            evidence_status="ASS",
            source_quality="UNKNOWN",
            scope_boundary="",
            floor_area_m2=-1,
            reproducible_binding=False,
        )
        decision = mod.assess_detached_hydronic_anchor(invalid)
        self.assertEqual(decision.status, "Q")
        self.assertIn("NO_ANCHOR_ID", decision.reasons)
        self.assertIn("INVALID_EVIDENCE_STATUS", decision.reasons)
        self.assertIn("INVALID_SOURCE_QUALITY", decision.reasons)
        self.assertIn("INVALID_FLOOR_AREA", decision.reasons)
        self.assertIn("NO_RADIATOR_OR_TECHNICAL_PAYLOAD", decision.reasons)
        self.assertFalse(decision.national_p42_authority)

    def test_p42_five_national_programme_quantities_remain_q(self):
        with P42.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(row["current_status"] == "Q" for row in rows))
        self.assertTrue(all(row["programme_use_allowed"] == "NO" for row in rows))

    def test_source_pack_freezes_intent_and_non_promotion(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "HOW MANY + WHAT TYPE + KEEP/CHANGE + HOW MANY NEW UNITS -> B06",
            "PUBLIC RECOVERY != DATA REQUEST",
            "HOUSEHOLD-LEVEL PUBLIC ANCHOR != NATIONAL P42 AUTHORITY",
            "70 m2 detached house -> 4 radiators",
            "77 m2 detached house -> 6 radiators",
            "86 m2 brick detached house -> 8 radiators",
            "120 m2 detached house -> 7 actually replaced radiators",
            "22K panel-radiator type",
            "POST-ENVELOPE HEAT LOSS + EXISTING EMITTER OUTPUT AT TARGET WATER TEMPERATURE + HYDRAULICS -> KEEP / UPSIZE / CHANGE",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
