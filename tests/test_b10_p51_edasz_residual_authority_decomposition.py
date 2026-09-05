import csv
import hashlib
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
P49_PAIRS = ROOT / "registry/dso_service_area_membership_edasz_p49_pairs.csv"
P49_EXCEPTIONS = ROOT / "registry/dso_service_area_membership_edasz_p49_exceptions.csv"
P50_AUDIT = ROOT / "registry/dso_service_area_membership_edasz_p50_spelling_authority_audit.csv"
P51_AUDIT = ROOT / "registry/dso_service_area_membership_edasz_p51_residual_authority_audit.csv"
P51_MANIFEST = ROOT / "registry/dso_service_area_membership_edasz_p51_authority_manifest.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P51_B10_EDASZ_RESIDUAL_AUTHORITY_DECOMPOSITION.md"

EXPECTED_AUDIT_DIGEST = "042df54daae95c99a52c734aa397f7d9201616f9f61a138c5cf30d594346a70f"

SPECIAL_MIXED = {
    "Ács-Jegespuszta",
    "Gánt Vérteskozma",
    "Isztimér-Királysz.",
    "Kerkateskánd-hegy",
    "Lesencei-Uzsabánya",
    "Lovászi Luku-hegy",
    "Rábapaty-Felsőpaty",
    "Szőce-Rimány",
    "Szt.Királyszabadja",
}

STANDALONE_NONEXACT = {
    "Dunakilti",
    "Ferőhomok",
    "Fertőújlak",
    "Iklóbördöce",
    "Jóbháza",
    "Kajérpéc",
    "Kecséd",
    "Nádasladány",
    "Nagyszentjánosk",
    "Séska",
    "Srród",
    "Zalagyömrő",
    "Zichiújfalu",
    "Zsédely",
}


class B10P51EdaszResidualAuthorityDecompositionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_exact_23_residual_rows_and_24_occurrences_are_frozen(self):
        rows = self.rows(P51_AUDIT)
        self.assertEqual(23, len(rows))
        self.assertEqual(23, len({r["source_token"] for r in rows}))
        self.assertEqual(24, sum(int(r["source_occurrence_count"]) for r in rows))
        canonical = "".join(
            f'{r["source_token"]}|{r["source_occurrence_count"]}|{r["residual_class"]}|{r["admission_status"]}\n'
            for r in sorted(rows, key=lambda r: r["source_token"])
        )
        self.assertEqual(EXPECTED_AUDIT_DIGEST, hashlib.sha256(canonical.encode("utf-8")).hexdigest())

    def test_residual_classes_are_exactly_nine_special_and_fourteen_standalone(self):
        rows = self.rows(P51_AUDIT)
        special = {r["source_token"] for r in rows if r["residual_class"] == "SPECIAL_OR_MIXED_GRAIN"}
        standalone = {r["source_token"] for r in rows if r["residual_class"] == "STANDALONE_NONEXACT_IDENTITY"}
        self.assertEqual(SPECIAL_MIXED, special)
        self.assertEqual(STANDALONE_NONEXACT, standalone)
        self.assertFalse(special & standalone)
        self.assertTrue(all(r["admission_status"] == "UNRESOLVED_AUTHORITY_REQUIRED" for r in rows))

    def test_seska_is_one_identity_token_with_two_source_occurrences(self):
        rows = self.rows(P51_AUDIT)
        seska = [r for r in rows if r["source_token"] == "Séska"]
        self.assertEqual(1, len(seska))
        self.assertEqual("2", seska[0]["source_occurrence_count"])
        self.assertEqual("STANDALONE_NONEXACT_IDENTITY", seska[0]["residual_class"])

    def test_59_unique_and_60_occurrence_partition_is_exact_and_disjoint(self):
        spelling = {r["source_token"] for r in self.rows(P50_AUDIT)}
        residual_rows = self.rows(P51_AUDIT)
        residual = {r["source_token"] for r in residual_rows}
        cross_dso_rows = [
            r for r in self.rows(P49_EXCEPTIONS)
            if r["exception_class"] == "CROSS_DSO_WHOLE_CONFLICT_EXCLUDED"
        ]
        cross_dso = {r["source_token"] for r in cross_dso_rows}

        self.assertEqual(30, len(spelling))
        self.assertEqual(23, len(residual))
        self.assertEqual(6, len(cross_dso))
        self.assertFalse(spelling & residual)
        self.assertFalse(spelling & cross_dso)
        self.assertFalse(residual & cross_dso)
        self.assertEqual(59, len(spelling | residual | cross_dso))

        occurrence_count = len(spelling) + sum(int(r["source_occurrence_count"]) for r in residual_rows) + len(cross_dso_rows)
        self.assertEqual(60, occurrence_count)

    def test_manifest_freezes_partition_without_promotion(self):
        rows = self.rows(P51_MANIFEST)
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("EON_EDASZ", row["operator_id"])
        self.assertEqual("SRC-B10-EON-EDASZ-M1-CANDIDATE-2025", row["current_source_id"])
        self.assertEqual("20241209", row["current_source_revision"])
        for field, expected in {
            "p49_unresolved_unique": "59",
            "p49_unresolved_occurrences": "60",
            "p50_spelling_unique": "30",
            "p49_cross_dso_unique": "6",
            "p51_residual_unique": "23",
            "p51_residual_occurrences": "24",
            "p51_special_mixed_unique": "9",
            "p51_standalone_nonexact_unique": "14",
        }.items():
            self.assertEqual(expected, row[field])
        self.assertEqual("EXACT_UNRESOLVED_PARTITION_FROZEN", row["partition_status"])
        self.assertEqual("ZERO_NEW_MEMBERSHIP_ROWS", row["admission_impact"])

    def test_p51_changes_no_edasz_membership_population(self):
        historical = [r for r in self.rows(HISTORICAL) if r["operator_id"] == "EON_EDASZ"]
        p49 = self.rows(P49_PAIRS)
        self.assertEqual(45, len(historical))
        self.assertEqual(769, len(p49))
        self.assertEqual(814, len(historical) + len(p49))

        p49_names = {r["settlement_name"] for r in p49}
        residual = {r["source_token"] for r in self.rows(P51_AUDIT)}
        self.assertTrue(residual.isdisjoint(p49_names))

    def test_source_pack_preserves_fail_closed_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "30 P50 spelling diagnostics + 6 P49 cross-DSO conflicts + 23 P51 residual source forms = 59 unresolved unique tokens",
            "30 + 6 + 24 = 60 unresolved source occurrences",
            "SPECIAL OR MIXED SOURCE LABEL != WHOLE-SETTLEMENT MEMBERSHIP",
            "NONEXACT STANDALONE SOURCE FORM != AUTHORIZED CANONICAL IDENTITY",
            "DUPLICATE SOURCE OCCURRENCE != SECOND LOCALITY IDENTITY",
            "SOURCE FORM PRESENCE != WHOLE-SETTLEMENT IDENTITY AUTHORITY",
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
