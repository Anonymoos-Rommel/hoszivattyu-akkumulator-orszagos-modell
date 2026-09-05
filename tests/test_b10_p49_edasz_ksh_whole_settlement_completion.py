import csv
import hashlib
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
OPUS_P44 = ROOT / "registry/dso_service_area_membership_crosswalk_opus_p44.csv"
DEMASZ_P45 = ROOT / "registry/dso_service_area_membership_crosswalk_demasz_p45.csv"
ELMU_P46 = ROOT / "registry/dso_service_area_membership_crosswalk_elmu_p46.csv"
EMASZ_P47 = ROOT / "registry/dso_service_area_membership_emasz_p47_pairs.csv"
DDASZ_P48 = ROOT / "registry/dso_service_area_membership_ddasz_p48_pairs.csv"
PAIRS = ROOT / "registry/dso_service_area_membership_edasz_p49_pairs.csv"
MANIFEST = ROOT / "registry/dso_service_area_membership_edasz_p49_manifest.csv"
EXCEPTIONS = ROOT / "registry/dso_service_area_membership_edasz_p49_exceptions.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P49_B10_EDASZ_KSH_WHOLE_SETTLEMENT_COMPLETION.md"

EDASZ = "SRC-B10-EON-EDASZ-M1-CANDIDATE-2025"
KSH_2019 = "SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS"
KSH_2025 = "SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS"
KSH_DERIVATION = "SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026"
EXPECTED_PAIR_DIGEST = "086abb0c24601369f7455aeaac261d31e81c2933cc9a575c88478dd3bcd35692"

CROSS_DSO_EXCLUSIONS = {
    ("04321", "Bodorfa"),
    ("07922", "Szentgál"),
    ("17543", "Bocfölde"),
    ("18731", "Pilisszentkereszt"),
    ("20589", "Nagykapornak"),
    ("23490", "Mány"),
}

SPELLING_EDGE_TARGETS = {
    ("23153", "Bakonykúti"), ("21917", "Dör"), ("25946", "Egyházasrádóc"),
    ("29939", "Felcsút"), ("24369", "Felsőörs"), ("18193", "Gógánfa"),
    ("11156", "Gór"), ("02060", "Gönyű"), ("29771", "Gősfa"),
    ("27030", "Gyanógeregye"), ("15918", "Gyúró"), ("12733", "Horvátlövő"),
    ("08749", "Karakószörcsök"), ("19734", "Kemeneshőgyész"), ("02413", "Kisbabot"),
    ("23454", "Kővágóörs"), ("31194", "Lövő"), ("24509", "Nemesbőd"),
    ("22318", "Nyőgér"), ("27775", "Óhíd"), ("22044", "Ólmod"),
    ("13453", "Őrimagyarósd"), ("17011", "Paloznak"), ("07551", "Rádóckölked"),
    ("22983", "Sótony"), ("31990", "Súr"), ("22619", "Szomód"),
    ("20853", "Úrkút"), ("29373", "Vasszécseny"), ("30313", "Zalalövő"),
}


class B10P49EdaszKshWholeSettlementCompletionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def p49_pairs(self):
        return self.rows(PAIRS)

    def test_exact_769_p49_pairs_are_frozen_by_digest(self):
        rows = self.p49_pairs()
        self.assertEqual(769, len(rows))
        canonical = "".join(
            f'{r["ksh_settlement_code"]}|{r["settlement_name"]}\n'
            for r in sorted(rows, key=lambda r: (r["ksh_settlement_code"], r["settlement_name"]))
        )
        self.assertEqual(EXPECTED_PAIR_DIGEST, hashlib.sha256(canonical.encode("utf-8")).hexdigest())

    def test_p49_pairs_are_unique_and_include_only_exact_exception_admissions(self):
        rows = self.p49_pairs()
        codes = [r["ksh_settlement_code"] for r in rows]
        names = [r["settlement_name"] for r in rows]
        self.assertEqual(769, len(set(codes)))
        self.assertEqual(769, len(set(names)))
        self.assertTrue(all(len(c) == 5 and c.isdigit() for c in codes))
        actual = {(r["ksh_settlement_code"], r["settlement_name"]) for r in rows}
        for pair in {("29221", "Jánossomorja"), ("12715", "Pázmándfalu"), ("04622", "Zsira")}:
            self.assertIn(pair, actual)

    def test_manifest_reconstructs_exact_edasz_der_semantics(self):
        rows = self.rows(MANIFEST)
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("EON_EDASZ", row["operator_id"])
        self.assertEqual("EON_EDASZ:SERVICE_AREA", row["service_area_id"])
        self.assertEqual("WHOLE_SETTLEMENT", row["coverage_scope"])
        self.assertEqual("NONE", row["usage_location_requirement"])
        self.assertEqual("DER", row["evidence_status"])
        self.assertEqual("WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN", row["status"])
        self.assertEqual({EDASZ, KSH_2025, KSH_DERIVATION}, set(row["normal_source_ids"].split(";")))
        self.assertIn("769", row["notes"])

    def test_nine_exception_paths_are_exact_and_nongeneralized(self):
        rows = self.rows(EXCEPTIONS)
        self.assertEqual(9, len(rows))
        classes = [r["exception_class"] for r in rows]
        self.assertEqual(1, classes.count("KSH2019_DIRECT"))
        self.assertEqual(2, classes.count("PDF_EXTRACTION_ARTIFACT_CORRECTION"))
        self.assertEqual(6, classes.count("CROSS_DSO_WHOLE_CONFLICT_EXCLUDED"))
        direct = next(r for r in rows if r["exception_class"] == "KSH2019_DIRECT")
        self.assertEqual(("29221", "Jánossomorja"), (direct["ksh_settlement_code"], direct["settlement_name"]))
        self.assertEqual({EDASZ, KSH_2019}, set(direct["source_ids"].split(";")))
        parser = {(r["ksh_settlement_code"], r["settlement_name"], r["source_token"]) for r in rows if r["exception_class"] == "PDF_EXTRACTION_ARTIFACT_CORRECTION"}
        self.assertEqual({("12715", "Pázmándfalu", "P ázmándfalu"), ("04622", "Zsira", "Zsira 9")}, parser)
        excluded = {(r["ksh_settlement_code"], r["settlement_name"]) for r in rows if r["exception_class"] == "CROSS_DSO_WHOLE_CONFLICT_EXCLUDED"}
        self.assertEqual(CROSS_DSO_EXCLUSIONS, excluded)

    def test_historical_45_plus_p49_769_equals_814_current_whole_identities(self):
        historical = [r for r in self.rows(HISTORICAL) if r["operator_id"] == "EON_EDASZ"]
        self.assertEqual(45, len(historical))
        old_pairs = {(r["ksh_settlement_code"], r["settlement_name"]) for r in historical}
        self.assertTrue({("15176", "Alcsútdoboz"), ("30526", "Alsóörs")} <= old_pairs)
        new_pairs = {(r["ksh_settlement_code"], r["settlement_name"]) for r in self.p49_pairs()}
        self.assertFalse(old_pairs & new_pairs)
        self.assertEqual(814, len(old_pairs | new_pairs))

    def test_cross_dso_conflicts_and_30_spelling_targets_remain_fail_closed(self):
        pairs = {(r["ksh_settlement_code"], r["settlement_name"]) for r in self.p49_pairs()}
        self.assertTrue(CROSS_DSO_EXCLUSIONS.isdisjoint(pairs))
        self.assertEqual(30, len(SPELLING_EDGE_TARGETS))
        self.assertTrue(SPELLING_EDGE_TARGETS.isdisjoint(pairs))
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("EXACT ADMINISTRATIVE-UNIT NAME MATCH != SECOND WHOLE-SETTLEMENT DSO MEMBERSHIP", text)
        self.assertIn("SOURCE SPELLING DIFFERENCE != AUTHORIZED IDENTITY EQUIVALENCE", text)

    def test_global_materialized_ksh_codes_remain_unique(self):
        codes = []
        for path in (HISTORICAL, OPUS_P44, DEMASZ_P45, ELMU_P46):
            codes.extend(r["ksh_settlement_code"] for r in self.rows(path))
        for path in (EMASZ_P47, DDASZ_P48, PAIRS):
            codes.extend(r["ksh_settlement_code"] for r in self.rows(path))
        self.assertEqual(len(codes), len(set(codes)))

    def test_source_registry_records_p49_completion_but_keeps_operator_partial(self):
        by_operator = {r["operator_id"]: r for r in self.rows(SOURCES)}
        row = by_operator["EON_EDASZ"]
        self.assertEqual(EDASZ, row["source_id"])
        self.assertEqual("CURRENT_2026_DER_APPROVED_PACKAGE_REVISION_LINEAGE", row["currentness_status"])
        self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", row["extraction_status"])
        for marker in ("P49", "874", "873", "769", "814", "59", "30", "Bodorfa", "Mány"):
            self.assertIn(marker, row["notes"])

    def test_source_pack_preserves_complete_accounting_and_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "874 source-token occurrences", "873 unique source tokens",
            "45 historical + 769 P49 = 814 materialized current provable whole-settlement identities",
            "873 unique source tokens - 814 represented whole-settlement identities = 59 unresolved unique tokens",
            "PDF EXTRACTION ARTIFACT CORRECTION != FUZZY IDENTITY MATCH",
            "NORMALIZED STORAGE != WEAKER ROW-LEVEL EVIDENCE",
            "COMPLETE PROVABLE WHOLE-SETTLEMENT MATERIALIZATION != COMPLETE OPERATOR MEMBERSHIP CROSSWALK",
            "readiness remains **15%**",
        ):
            self.assertIn(marker, text)

    def test_canonical_crosswalk_blockers_and_readiness_remain_fail_closed(self):
        self.assertEqual(1, len(CANONICAL.read_text(encoding="utf-8").splitlines()))
        blockers = set(current_b10_closure_assessment().blocking_refs)
        self.assertIn("NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK", blockers)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", blockers)
        by_module = {r["module_id"]: r for r in self.rows(MODULE_STATUS)}
        self.assertEqual("IN_PROGRESS", by_module["B10"]["status"])
        self.assertEqual("15", by_module["B10"]["readiness_percent"])


if __name__ == "__main__":
    unittest.main()
