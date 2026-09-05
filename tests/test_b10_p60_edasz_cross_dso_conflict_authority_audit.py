import csv
import hashlib
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "registry/dso_service_area_membership_edasz_p60_cross_dso_conflict_audit.csv"
MANIFEST = ROOT / "registry/dso_service_area_membership_edasz_p60_authority_manifest.csv"
P49_EXCEPTIONS = ROOT / "registry/dso_service_area_membership_edasz_p49_exceptions.csv"
P49_PAIRS = ROOT / "registry/dso_service_area_membership_edasz_p49_pairs.csv"
P50 = ROOT / "registry/dso_service_area_membership_edasz_p50_spelling_authority_audit.csv"
P51 = ROOT / "registry/dso_service_area_membership_edasz_p51_residual_authority_audit.csv"
HISTORICAL = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
DDASZ_P48 = ROOT / "registry/dso_service_area_membership_ddasz_p48_pairs.csv"
ELMU_P46 = ROOT / "registry/dso_service_area_membership_crosswalk_elmu_p46.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P60_B10_EDASZ_CROSS_DSO_CONFLICT_AUTHORITY_AUDIT.md"

EXPECTED_DIGEST = "1643326c0f67b228b4948d64a9ccde241b9d8dbe262d52ebe2864f5320fb885b"
EXPECTED_IDENTITIES = {
    ("04321", "Bodorfa"),
    ("07922", "Szentgál"),
    ("17543", "Bocfölde"),
    ("18731", "Pilisszentkereszt"),
    ("20589", "Nagykapornak"),
    ("23490", "Mány"),
}
EXPECTED_DDASZ = {
    ("04321", "Bodorfa"),
    ("07922", "Szentgál"),
    ("17543", "Bocfölde"),
    ("20589", "Nagykapornak"),
}
EXPECTED_ELMU = {
    ("18731", "Pilisszentkereszt"),
    ("23490", "Mány"),
}


class B10P60EdaszCrossDsoConflictAuthorityAuditTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_exact_six_conflicts_are_frozen_by_digest(self):
        rows = self.rows(AUDIT)
        self.assertEqual(6, len(rows))
        fields = (
            "ksh_settlement_code",
            "settlement_name",
            "current_edasz_source_form",
            "current_edasz_source_semantics",
            "current_proven_operator",
            "current_proven_status",
            "historical_edasz_operator",
            "historical_other_operator",
            "historical_reference_date",
            "conflict_class",
            "edasz_admission_result",
            "required_future_authority",
        )
        canonical = "".join(
            "|".join(row[field] for field in fields) + "\n"
            for row in sorted(rows, key=lambda row: row["ksh_settlement_code"])
        )
        self.assertEqual(EXPECTED_DIGEST, hashlib.sha256(canonical.encode("utf-8")).hexdigest())

    def test_audit_matches_exact_p49_cross_dso_exception_set(self):
        audit_ids = {(r["ksh_settlement_code"], r["settlement_name"]) for r in self.rows(AUDIT)}
        p49_ids = {
            (r["ksh_settlement_code"], r["settlement_name"])
            for r in self.rows(P49_EXCEPTIONS)
            if r["exception_class"] == "CROSS_DSO_WHOLE_CONFLICT_EXCLUDED"
        }
        self.assertEqual(EXPECTED_IDENTITIES, audit_ids)
        self.assertEqual(EXPECTED_IDENTITIES, p49_ids)

    def test_current_competing_whole_memberships_are_preserved(self):
        ddasz = {(r["ksh_settlement_code"], r["settlement_name"]) for r in self.rows(DDASZ_P48)}
        elmu = {
            (r["ksh_settlement_code"], r["settlement_name"])
            for r in self.rows(ELMU_P46)
            if r["coverage_scope"] == "WHOLE_SETTLEMENT" and r["status"] == "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN"
        }
        self.assertTrue(EXPECTED_DDASZ <= ddasz)
        self.assertTrue(EXPECTED_ELMU <= elmu)

    def test_historical_authority_classes_do_not_mint_second_edasz_whole_membership(self):
        rows = self.rows(AUDIT)
        by_id = {(r["ksh_settlement_code"], r["settlement_name"]): r for r in rows}
        for identity in EXPECTED_DDASZ:
            row = by_id[identity]
            self.assertEqual("EON_DDASZ", row["current_proven_operator"])
            self.assertEqual("EON_EDASZ", row["historical_edasz_operator"])
            self.assertEqual("EON_DDASZ", row["historical_other_operator"])
            self.assertEqual(
                "CURRENT_EDASZ_ADMIN_UNIT_VS_OTHER_DSO_WHOLE_MEMBERSHIP_CONFLICT_HISTORICAL_DUAL_EON_LICENSEE_CORROBORATED",
                row["conflict_class"],
            )
        for identity in EXPECTED_ELMU:
            row = by_id[identity]
            self.assertEqual("ELMU", row["current_proven_operator"])
            self.assertEqual("EON_EDASZ", row["historical_edasz_operator"])
            self.assertEqual("NOT_ESTABLISHED_BY_THIS_HISTORICAL_SOURCE", row["historical_other_operator"])
            self.assertEqual(
                "CURRENT_EDASZ_ADMIN_UNIT_VS_ELMU_WHOLE_MEMBERSHIP_CONFLICT_HISTORICAL_EDASZ_CORROBORATED",
                row["conflict_class"],
            )
        for row in rows:
            self.assertEqual("ADMINISTRATIVE_UNIT_TOKEN", row["current_edasz_source_semantics"])
            self.assertEqual("WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN", row["current_proven_status"])
            self.assertEqual("2022", row["historical_reference_date"])
            self.assertEqual("NO_SECOND_WHOLE_SETTLEMENT_PROMOTION", row["edasz_admission_result"])
            self.assertEqual(
                "CURRENT_CLAIM_SPECIFIC_BOUNDARY_OR_USAGE_LOCATION_AUTHORITY",
                row["required_future_authority"],
            )

    def test_manifest_preserves_p49_p51_accounting_and_non_promoting_result(self):
        rows = self.rows(MANIFEST)
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("EON_EDASZ_P49_SIX_CROSS_DSO_CONFLICTS", row["audit_scope"])
        self.assertEqual("SRC-B10-EON-EDASZ-M1-CANDIDATE-2025", row["current_edasz_source_id"])
        self.assertEqual("SRC-B10-EON-DDASZ-M1-CANDIDATE-2025", row["current_ddasz_source_id"])
        self.assertEqual("SRC-B10-ELMU-M1-CANDIDATE-2025", row["current_elmu_source_id"])
        self.assertEqual("ADMINISTRATIVE_UNITS_IN_M1", row["current_edasz_semantics"])
        self.assertEqual("KEEP_CURRENT_DDASZ_OR_ELMU_WHOLE_BLOCK_SECOND_EDASZ_WHOLE", row["result"])
        self.assertEqual("59=30_SPELLING+6_CROSS_DSO+23_OTHER_RESIDUAL", row["p49_unresolved_accounting"])
        self.assertEqual(EXPECTED_DIGEST, row["audit_sha256"])
        self.assertEqual(30, len(self.rows(P50)))
        self.assertEqual(23, len(self.rows(P51)))
        self.assertEqual(59, len(self.rows(P50)) + len(self.rows(AUDIT)) + len(self.rows(P51)))

    def test_p60_adds_no_edasz_membership_rows(self):
        historical_edasz = [r for r in self.rows(HISTORICAL) if r["operator_id"] == "EON_EDASZ"]
        self.assertEqual(45, len(historical_edasz))
        self.assertEqual(769, len(self.rows(P49_PAIRS)))
        self.assertEqual(814, len(historical_edasz) + len(self.rows(P49_PAIRS)))
        admitted = {(r["ksh_settlement_code"], r["settlement_name"]) for r in self.rows(P49_PAIRS)}
        self.assertTrue(EXPECTED_IDENTITIES.isdisjoint(admitted))

    def test_source_pack_freezes_authority_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "CURRENT ÉDÁSZ M1 ADMINISTRATIVE-UNIT PRESENCE != CURRENT ÉDÁSZ WHOLE-SETTLEMENT MEMBERSHIP",
            "HISTORICAL DUAL-LICENSEE ROWS != CURRENT DUAL WHOLE-SETTLEMENT MEMBERSHIP",
            "HISTORICAL ÉDÁSZ ASSIGNMENT != CURRENT ÉDÁSZ WHOLE-SETTLEMENT MEMBERSHIP",
            "HISTORICAL + CURRENT SOURCE PRESENCE != CURRENT BOUNDARY AUTHORITY",
            "CONFLICTING OPERATOR SURFACES != DUAL WHOLE-SETTLEMENT MEMBERSHIP",
            "59 = 30 P50 spelling diagnostics + 6 P60 cross-DSO conflicts + 23 P51 residual source forms",
            "RESIDUAL ACCOUNTING != RESIDUAL IDENTITY RESOLUTION",
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
