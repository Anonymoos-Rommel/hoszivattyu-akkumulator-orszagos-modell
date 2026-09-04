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
PAIRS = ROOT / "registry/dso_service_area_membership_ddasz_p48_pairs.csv"
MANIFEST = ROOT / "registry/dso_service_area_membership_ddasz_p48_manifest.csv"
EXCEPTIONS = ROOT / "registry/dso_service_area_membership_ddasz_p48_exceptions.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P48_B10_DDASZ_KSH_WHOLE_SETTLEMENT_COMPLETION.md"

DDASZ = "SRC-B10-EON-DDASZ-M1-CANDIDATE-2025"
DEMASZ = "SRC-B10-MVM-DEMASZ-SERVICE-AREA-2026"
KSH_2019 = "SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS"
KSH_2025 = "SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS"
KSH_2025_DERIVATION = "SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026"
EXPECTED_PAIR_DIGEST = "c12ddf8c6f246cb116ff8f4fa7e9aa97d3308b25c6189efcb124d1ceedba4878"

EXPECTED_EXCEPTIONS = {
    ("31431", "Husztót", "PDF_EXTRACTION_ARTIFACT_CORRECTION", "E.ON Dél-dunántúli Áramhálózati Zrt. - Elosztói Üzletszabályzat Husztót"),
    ("27553", "Pogányszentpéter", "PDF_EXTRACTION_ARTIFACT_CORRECTION", "E.ON Dél-dunántúli Áramhálózati Zrt. - Elosztói Üzletszabályzat Pogányszentpéter"),
    ("34032", "Szaporca", "PDF_EXTRACTION_ARTIFACT_CORRECTION", "S zaporca"),
    ("33233", "Gödre", "KSH2019_DIRECT", "Gödre"),
    ("10348", "Zalakomár", "KSH2019_DIRECT", "Zalakomár"),
    ("04109", "Dusnok", "CROSS_DSO_WHOLE_CONFLICT_EXCLUDED", "Dusnok"),
    ("16018", "Mélykút", "CROSS_DSO_WHOLE_CONFLICT_EXCLUDED", "Mélykút"),
}

SPELLING_EDGE_TARGETS = {
    ("11916", "Balatonőszöd"),
    ("20464", "Baranyahídvég"),
    ("30094", "Csikóstőttős"),
    ("11086", "Cún"),
    ("16531", "Fűzvölgy"),
    ("05537", "Kallósd"),
    ("16683", "Káloz"),
    ("26888", "Kazsok"),
    ("15510", "Kőröshegy"),
    ("06992", "Kővágótöttös"),
    ("08961", "Őcsény"),
    ("18740", "Szabadhídvég"),
    ("18582", "Túrony"),
    ("05892", "Vokány"),
}

CROSS_DSO_CONFLICTS = {("04109", "Dusnok"), ("16018", "Mélykút")}


class B10P48DdaszKshWholeSettlementCompletionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def p48_pairs(self):
        return self.rows(PAIRS)

    def test_exact_777_p48_pairs_are_frozen_by_digest(self):
        rows = self.p48_pairs()
        self.assertEqual(777, len(rows))
        canonical = "".join(
            f'{row["ksh_settlement_code"]}|{row["settlement_name"]}\n'
            for row in sorted(rows, key=lambda r: (r["ksh_settlement_code"], r["settlement_name"]))
        )
        self.assertEqual(EXPECTED_PAIR_DIGEST, hashlib.sha256(canonical.encode("utf-8")).hexdigest())

    def test_p48_pairs_are_unique_five_digit_identifiers(self):
        rows = self.p48_pairs()
        codes = [row["ksh_settlement_code"] for row in rows]
        names = [row["settlement_name"] for row in rows]
        self.assertEqual(777, len(set(codes)))
        self.assertEqual(777, len(set(names)))
        self.assertTrue(all(len(code) == 5 and code.isdigit() for code in codes))
        actual = {(r["ksh_settlement_code"], r["settlement_name"]) for r in rows}
        for pair in {("31431", "Husztót"), ("27553", "Pogányszentpéter"), ("34032", "Szaporca"), ("33233", "Gödre"), ("10348", "Zalakomár")}:
            self.assertIn(pair, actual)
        self.assertTrue(CROSS_DSO_CONFLICTS.isdisjoint(actual))

    def test_manifest_reconstructs_exact_ddasz_der_semantics(self):
        rows = self.rows(MANIFEST)
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("EON_DDASZ", row["operator_id"])
        self.assertEqual("E.ON Dél-dunántúli Áramhálózati Zrt.", row["network_operator"])
        self.assertEqual("EON_DDASZ:SERVICE_AREA", row["service_area_id"])
        self.assertEqual("WHOLE_SETTLEMENT", row["coverage_scope"])
        self.assertEqual("NONE", row["usage_location_requirement"])
        self.assertEqual("DER", row["evidence_status"])
        self.assertEqual("WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN", row["status"])
        self.assertEqual({DDASZ, KSH_2025, KSH_2025_DERIVATION}, set(row["normal_source_ids"].split(";")))
        self.assertEqual(str(PAIRS.relative_to(ROOT)), row["pairs_file"])
        self.assertEqual(str(EXCEPTIONS.relative_to(ROOT)), row["exception_file"])
        self.assertIn("777", row["notes"])
        self.assertIn("cross-DSO", row["notes"])

    def test_seven_exception_paths_are_exact_and_nongeneralized(self):
        rows = self.rows(EXCEPTIONS)
        actual = {
            (r["ksh_settlement_code"], r["settlement_name"], r["exception_class"], r["source_token"])
            for r in rows
        }
        self.assertEqual(EXPECTED_EXCEPTIONS, actual)
        extraction = [r for r in rows if r["exception_class"] == "PDF_EXTRACTION_ARTIFACT_CORRECTION"]
        direct = [r for r in rows if r["exception_class"] == "KSH2019_DIRECT"]
        conflicts = [r for r in rows if r["exception_class"] == "CROSS_DSO_WHOLE_CONFLICT_EXCLUDED"]
        self.assertEqual(3, len(extraction))
        self.assertEqual(2, len(direct))
        self.assertEqual(2, len(conflicts))
        normal_sources = {DDASZ, KSH_2025, KSH_2025_DERIVATION}
        self.assertTrue(all(set(r["source_ids"].split(";")) == normal_sources for r in extraction))
        self.assertTrue(all(set(r["source_ids"].split(";")) == {DDASZ, KSH_2019} for r in direct))
        self.assertTrue(all(set(r["source_ids"].split(";")) == {DDASZ, DEMASZ, KSH_2025} for r in conflicts))
        self.assertTrue(all("fuzzy" in r["notes"].lower() or "spelling equivalence" in r["notes"].lower() for r in extraction))
        self.assertTrue(all("second whole-settlement" in r["notes"] for r in conflicts))

    def test_historical_43_plus_p48_777_equals_820_current_whole_identities(self):
        historical = [r for r in self.rows(HISTORICAL) if r["operator_id"] == "EON_DDASZ"]
        self.assertEqual(43, len(historical))
        old_pairs = {(r["ksh_settlement_code"], r["settlement_name"]) for r in historical}
        new_pairs = {(r["ksh_settlement_code"], r["settlement_name"]) for r in self.p48_pairs()}
        self.assertFalse(old_pairs & new_pairs)
        self.assertEqual(820, len(old_pairs | new_pairs))

    def test_cross_dso_conflicts_are_recorded_but_not_promoted(self):
        pairs = {(r["ksh_settlement_code"], r["settlement_name"]) for r in self.p48_pairs()}
        self.assertTrue(CROSS_DSO_CONFLICTS.isdisjoint(pairs))
        historical = {(r["ksh_settlement_code"], r["settlement_name"], r["operator_id"]) for r in self.rows(HISTORICAL)}
        demasz_p45 = {(r["ksh_settlement_code"], r["settlement_name"], r["operator_id"]) for r in self.rows(DEMASZ_P45)}
        self.assertIn(("04109", "Dusnok", "MVM_DEMASZ"), historical)
        self.assertIn(("16018", "Mélykút", "MVM_DEMASZ"), demasz_p45)
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("EXACT ADMINISTRATIVE-UNIT NAME MATCH != SECOND WHOLE-SETTLEMENT DSO MEMBERSHIP", text)

    def test_fourteen_spelling_equivalence_targets_remain_fail_closed(self):
        pairs = {(r["ksh_settlement_code"], r["settlement_name"]) for r in self.p48_pairs()}
        self.assertTrue(SPELLING_EDGE_TARGETS.isdisjoint(pairs))
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "Balatonöszöd` | `Balatonőszöd` | `11916`",
            "Szabadhidvég` | `Szabadhídvég` | `18740`",
            "Vókány` | `Vokány` | `05892`",
            "SOURCE SPELLING DIFFERENCE != AUTHORIZED IDENTITY EQUIVALENCE",
        ):
            self.assertIn(marker, text)

    def test_global_materialized_ksh_codes_remain_unique(self):
        codes = []
        for path in (HISTORICAL, OPUS_P44, DEMASZ_P45, ELMU_P46):
            codes.extend(r["ksh_settlement_code"] for r in self.rows(path))
        codes.extend(r["ksh_settlement_code"] for r in self.rows(EMASZ_P47))
        codes.extend(r["ksh_settlement_code"] for r in self.p48_pairs())
        self.assertEqual(len(codes), len(set(codes)))

    def test_source_registry_records_p48_completion_but_keeps_operator_partial(self):
        by_operator = {r["operator_id"]: r for r in self.rows(SOURCES)}
        row = by_operator["EON_DDASZ"]
        self.assertEqual(DDASZ, row["source_id"])
        self.assertEqual("CURRENT_2026_DER_APPROVED_PACKAGE_REVISION_LINEAGE", row["currentness_status"])
        self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", row["extraction_status"])
        for marker in ("P48", "777", "820", "1116", "296", "14", "Dusnok", "Mélykút", "Balatonöszöd", "Szabadhidvég"):
            self.assertIn(marker, row["notes"])

    def test_source_pack_preserves_complete_accounting_and_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "1116 unique source tokens",
            "43 historical + 777 P48 = 820 materialized current provable whole-settlement identities",
            "1116 - 820 = 296",
            "PDF EXTRACTION ARTIFACT CORRECTION != FUZZY IDENTITY MATCH",
            "EXACT ADMINISTRATIVE-UNIT NAME MATCH != SECOND WHOLE-SETTLEMENT DSO MEMBERSHIP",
            "SOURCE SPELLING DIFFERENCE != AUTHORIZED IDENTITY EQUIVALENCE",
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
