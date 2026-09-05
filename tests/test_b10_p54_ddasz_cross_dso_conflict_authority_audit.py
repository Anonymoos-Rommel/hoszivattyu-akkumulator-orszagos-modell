import csv
import hashlib
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "registry/dso_service_area_membership_ddasz_p54_cross_dso_conflict_audit.csv"
MANIFEST = ROOT / "registry/dso_service_area_membership_ddasz_p54_authority_manifest.csv"
P48_EXCEPTIONS = ROOT / "registry/dso_service_area_membership_ddasz_p48_exceptions.csv"
HISTORICAL = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
DEMASZ_P45 = ROOT / "registry/dso_service_area_membership_crosswalk_demasz_p45.csv"
DDASZ_P48 = ROOT / "registry/dso_service_area_membership_ddasz_p48_pairs.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P54_B10_DDASZ_CROSS_DSO_CONFLICT_AUTHORITY_AUDIT.md"

EXPECTED_DIGEST = "e6b1bb101d87390a17e0d6c30527dc0ae07edb528993e5a86731f3b983fa0be6"
EXPECTED_IDENTITIES = {("04109", "Dusnok"), ("16018", "Mélykút")}


class B10P54DdaszCrossDsoConflictAuthorityAuditTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_exact_two_conflicts_are_frozen_by_digest(self):
        rows = self.rows(AUDIT)
        self.assertEqual(2, len(rows))
        fields = (
            "ksh_settlement_code",
            "settlement_name",
            "current_ddasz_source_form",
            "current_ddasz_source_semantics",
            "current_mvm_operator",
            "current_mvm_status",
            "historical_eon_operator",
            "historical_reference_date",
            "conflict_class",
            "ddasz_admission_result",
            "required_future_authority",
        )
        canonical = "".join(
            "|".join(row[field] for field in fields) + "\n"
            for row in sorted(rows, key=lambda row: row["ksh_settlement_code"])
        )
        self.assertEqual(EXPECTED_DIGEST, hashlib.sha256(canonical.encode("utf-8")).hexdigest())

    def test_audit_matches_exact_p48_cross_dso_exception_set(self):
        audit_ids = {(r["ksh_settlement_code"], r["settlement_name"]) for r in self.rows(AUDIT)}
        p48_ids = {
            (r["ksh_settlement_code"], r["settlement_name"])
            for r in self.rows(P48_EXCEPTIONS)
            if r["exception_class"] == "CROSS_DSO_WHOLE_CONFLICT_EXCLUDED"
        }
        self.assertEqual(EXPECTED_IDENTITIES, audit_ids)
        self.assertEqual(EXPECTED_IDENTITIES, p48_ids)

    def test_current_mvm_whole_memberships_are_preserved(self):
        historical = {
            (r["ksh_settlement_code"], r["settlement_name"], r["operator_id"], r["coverage_scope"], r["status"])
            for r in self.rows(HISTORICAL)
        }
        p45 = {
            (r["ksh_settlement_code"], r["settlement_name"], r["operator_id"], r["coverage_scope"], r["status"])
            for r in self.rows(DEMASZ_P45)
        }
        expected_dusnok = ("04109", "Dusnok", "MVM_DEMASZ", "WHOLE_SETTLEMENT", "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN")
        expected_melykut = ("16018", "Mélykút", "MVM_DEMASZ", "WHOLE_SETTLEMENT", "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN")
        self.assertIn(expected_dusnok, historical)
        self.assertIn(expected_melykut, p45)

    def test_historical_ddasz_corroboration_does_not_mint_second_whole_membership(self):
        for row in self.rows(AUDIT):
            self.assertEqual("ADMINISTRATIVE_UNIT_TOKEN", row["current_ddasz_source_semantics"])
            self.assertEqual("MVM_DEMASZ", row["current_mvm_operator"])
            self.assertEqual("WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN", row["current_mvm_status"])
            self.assertEqual("EON_DDASZ", row["historical_eon_operator"])
            self.assertEqual("2022", row["historical_reference_date"])
            self.assertEqual(
                "CURRENT_ADMIN_UNIT_VS_WHOLE_MEMBERSHIP_CONFLICT_HISTORICAL_DDASZ_CORROBORATED",
                row["conflict_class"],
            )
            self.assertEqual("NO_SECOND_WHOLE_SETTLEMENT_PROMOTION", row["ddasz_admission_result"])
            self.assertEqual(
                "CURRENT_CLAIM_SPECIFIC_BOUNDARY_OR_USAGE_LOCATION_AUTHORITY",
                row["required_future_authority"],
            )

    def test_manifest_is_comparison_only_and_preserves_p48_accounting(self):
        rows = self.rows(MANIFEST)
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("EON_DDASZ_P48_TWO_CROSS_DSO_CONFLICTS", row["audit_scope"])
        self.assertEqual("SRC-B10-EON-DDASZ-M1-CANDIDATE-2025", row["current_ddasz_source_id"])
        self.assertEqual("SRC-B10-MVM-DEMASZ-SERVICE-AREA-2026", row["current_mvm_source_id"])
        self.assertEqual("ADMINISTRATIVE_UNITS_IN_M1", row["current_ddasz_semantics"])
        self.assertEqual("KEEP_MVM_WHOLE_BLOCK_SECOND_DDASZ_WHOLE", row["result"])
        self.assertEqual("296=14_SPELLING+2_CROSS_DSO+280_OTHER_UNRESOLVED", row["p48_residual_accounting"])

    def test_p54_adds_no_ddasz_membership_rows(self):
        historical_ddasz = [r for r in self.rows(HISTORICAL) if r["operator_id"] == "EON_DDASZ"]
        self.assertEqual(43, len(historical_ddasz))
        self.assertEqual(777, len(self.rows(DDASZ_P48)))
        self.assertEqual(820, len(historical_ddasz) + len(self.rows(DDASZ_P48)))
        admitted = {(r["ksh_settlement_code"], r["settlement_name"]) for r in self.rows(DDASZ_P48)}
        self.assertTrue(EXPECTED_IDENTITIES.isdisjoint(admitted))

    def test_source_pack_freezes_authority_boundaries_and_280_residual(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "CURRENT DDÁSZ M1 ADMINISTRATIVE-UNIT PRESENCE != CURRENT DDÁSZ WHOLE-SETTLEMENT MEMBERSHIP",
            "HISTORICAL DDÁSZ NETWORK-LICENSEE ASSIGNMENT != CURRENT DDÁSZ WHOLE-SETTLEMENT MEMBERSHIP",
            "HISTORICAL + CURRENT SOURCE PRESENCE != CURRENT BOUNDARY AUTHORITY",
            "CONFLICTING OPERATOR SURFACES != DUAL WHOLE-SETTLEMENT MEMBERSHIP",
            "296 = 14 spelling diagnostics + 2 cross-DSO conflicts + 280 other unresolved source tokens",
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
