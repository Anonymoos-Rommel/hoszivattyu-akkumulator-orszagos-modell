import csv
import hashlib
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "registry/dso_service_area_membership_demasz_p57_partial_settlement_authority_audit.csv"
MANIFEST = ROOT / "registry/dso_service_area_membership_demasz_p57_authority_manifest.csv"
HISTORICAL = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
P45 = ROOT / "registry/dso_service_area_membership_crosswalk_demasz_p45.csv"
P55_AUDIT = ROOT / "registry/dso_service_area_membership_elmu_p55_residual_authority_audit.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P57_B10_DEMASZ_PARTIAL_SETTLEMENT_AUTHORITY_DECOMPOSITION.md"

EXPECTED_DIGEST = "6dad102a2d23f18daf88620761c786072111990b2882261bd48539a05e767c7f"
EXPECTED_PARTIAL = {
    "Baja", "Csongrád", "Csabacsűd", "Dabas", "Dévaványa",
    "Érsekcsanád", "Gyomaendrőd", "Kunszentmárton", "Mohács", "Péteri",
    "Solt", "Szeghalom", "Szentes", "Tápiószőlős", "Tass", "Tiszakécske",
    "Tiszasas", "Tiszaug", "Újhartyán", "Zsadány",
}
DIGEST_FIELDS = (
    "source_token",
    "source_occurrence_count",
    "residual_class",
    "admission_status",
    "authority_basis",
    "cross_operator_context",
)


class B10P57DemaszPartialSettlementAuthorityDecompositionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_exact_twenty_partial_rows_are_frozen_by_digest(self):
        rows = self.rows(AUDIT)
        self.assertEqual(20, len(rows))
        self.assertEqual(EXPECTED_PARTIAL, {row["source_token"] for row in rows})
        canonical = "".join(
            "|".join(row[field] for field in DIGEST_FIELDS) + "\n"
            for row in sorted(rows, key=lambda row: row["source_token"])
        )
        self.assertEqual(EXPECTED_DIGEST, hashlib.sha256(canonical.encode("utf-8")).hexdigest())

    def test_all_rows_are_single_occurrence_partial_grain_and_fail_closed(self):
        rows = self.rows(AUDIT)
        for row in rows:
            self.assertEqual("1", row["source_occurrence_count"])
            self.assertEqual("PARTIAL_SETTLEMENT_ADMINISTRATIVE_SCOPE", row["residual_class"])
            self.assertEqual("UNRESOLVED_USAGE_LOCATION_AUTHORITY_REQUIRED", row["admission_status"])
            self.assertEqual("P45_CURRENT_MVM_DEMASZ_PARTIAL_SETTLEMENT_GRAIN", row["authority_basis"])
            self.assertIn("only partly inside", row["notes"])
            self.assertIn("exact usage-location authority is required", row["notes"])

    def test_tass_is_the_only_bounded_cross_operator_context(self):
        rows = {row["source_token"]: row for row in self.rows(AUDIT)}
        marked = {token for token, row in rows.items() if row["cross_operator_context"]}
        self.assertEqual({"Tass"}, marked)
        self.assertEqual(
            "P55_ELMU_EXPLICIT_SUBSETTLEMENT_AREA_PRESENT",
            rows["Tass"]["cross_operator_context"],
        )
        p55 = {row["source_token"]: row for row in self.rows(P55_AUDIT)}
        self.assertIn("Tass üdülőterület", p55)
        self.assertEqual("EXPLICIT_SUBSETTLEMENT_AREA", p55["Tass üdülőterület"]["residual_class"])
        self.assertIn("does not prove a complete boundary", rows["Tass"]["notes"])
        self.assertIn("complement", rows["Tass"]["notes"])

    def test_manifest_freezes_complete_residual_accounting_without_promotion(self):
        rows = self.rows(MANIFEST)
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("MVM_DEMASZ", row["operator_id"])
        self.assertEqual("MVM_DEMASZ:SERVICE_AREA", row["service_area_id"])
        self.assertEqual("SRC-B10-MVM-DEMASZ-SERVICE-AREA-2026", row["source_id"])
        self.assertEqual("CURRENT_2026", row["currentness_status"])
        self.assertEqual("20", row["residual_unique_tokens"])
        self.assertEqual("20", row["residual_occurrences"])
        self.assertEqual("PARTIAL_SETTLEMENT_ADMINISTRATIVE_SCOPE", row["residual_class"])
        self.assertEqual("UNRESOLVED_USAGE_LOCATION_AUTHORITY_REQUIRED", row["admission_status"])
        self.assertEqual("1", row["cross_operator_context_rows"])
        self.assertEqual(str(AUDIT.relative_to(ROOT)), row["audit_file"])
        self.assertIn("zero", row["notes"].lower())

    def test_p57_changes_no_demasz_membership_population(self):
        historical = [row for row in self.rows(HISTORICAL) if row["operator_id"] == "MVM_DEMASZ"]
        completion = self.rows(P45)
        self.assertEqual(40, len(historical))
        self.assertEqual(216, len(completion))
        current = historical + completion
        self.assertEqual(256, len(current))
        names = {row["settlement_name"] for row in current}
        self.assertTrue(EXPECTED_PARTIAL.isdisjoint(names))

    def test_operator_state_remains_partial(self):
        by_operator = {row["operator_id"]: row for row in self.rows(SOURCES)}
        row = by_operator["MVM_DEMASZ"]
        self.assertEqual("SRC-B10-MVM-DEMASZ-SERVICE-AREA-2026", row["source_id"])
        self.assertEqual("CURRENT_2026", row["currentness_status"])
        self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", row["extraction_status"])
        self.assertEqual("WHOLE_AND_PARTIAL_SETTLEMENTS", row["membership_semantics"])

    def test_canonical_crosswalk_blockers_and_readiness_remain_fail_closed(self):
        self.assertEqual(1, len(CANONICAL.read_text(encoding="utf-8").splitlines()))
        blockers = set(current_b10_closure_assessment().blocking_refs)
        self.assertIn("NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK", blockers)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", blockers)
        by_module = {row["module_id"]: row for row in self.rows(MODULE_STATUS)}
        self.assertEqual("IN_PROGRESS", by_module["B10"]["status"])
        self.assertEqual("15", by_module["B10"]["readiness_percent"])

    def test_source_pack_preserves_fail_closed_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "256 settlements wholly inside",
            "20 settlements partly inside",
            "6dad102a2d23f18daf88620761c786072111990b2882261bd48539a05e767c7f",
            "PARTIAL SETTLEMENT LABEL != WHOLE-SETTLEMENT MEMBERSHIP",
            "PARTIAL SETTLEMENT LABEL != EXACT USAGE-LOCATION MEMBERSHIP",
            "CROSS-OPERATOR SUBSETTLEMENT CONTEXT != COMPLETE TERRITORIAL BOUNDARY",
            "NAMED SUBSETTLEMENT != AUTHORITY TO INFER THE COMPLEMENT AREA",
            "SOURCE-GRAIN CLASSIFICATION != MEMBERSHIP AUTHORITY",
            "40 historical + 216 P45 = 256 materialized current whole-settlement memberships",
            "readiness remains **15%**",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
