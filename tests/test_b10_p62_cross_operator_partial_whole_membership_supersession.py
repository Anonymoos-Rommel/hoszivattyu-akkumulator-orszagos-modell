import csv
from collections import Counter
from pathlib import Path
import unittest

from modules.B10.effective_service_area_membership_contract import (
    B10EffectiveMembershipError,
    EFFECTIVE_WHOLE_SETTLEMENT_MEMBERSHIP,
    WHOLE_SETTLEMENT_CLAIM_SUPERSEDED,
    WholeMembershipSupersession,
    classify_effective_whole_membership,
    require_effective_whole_membership,
)
from modules.B10.integration_closure_contract import current_b10_closure_assessment


ROOT = Path(__file__).resolve().parents[1]
SUPERSESSIONS = ROOT / "registry/dso_service_area_membership_p62_effective_supersessions.csv"
COUNTS = ROOT / "registry/dso_service_area_membership_p62_effective_counts.csv"
P61_MATRIX = ROOT / "registry/dso_service_area_membership_demasz_p61_counterpart_authority_matrix.csv"
P61_USAGE = ROOT / "registry/dso_service_area_membership_elmu_p61_usage_location.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P62_B10_CROSS_OPERATOR_PARTIAL_WHOLE_MEMBERSHIP_SUPERSESSION.md"

RAW_MEMBERSHIP_FILES = (
    ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv",
    ROOT / "registry/dso_service_area_membership_crosswalk_opus_p44.csv",
    ROOT / "registry/dso_service_area_membership_crosswalk_demasz_p45.csv",
    ROOT / "registry/dso_service_area_membership_crosswalk_elmu_p46.csv",
    ROOT / "registry/dso_service_area_membership_crosswalk_emasz_p47.csv",
    ROOT / "registry/dso_service_area_membership_crosswalk_ddasz_p48.csv",
    ROOT / "registry/dso_service_area_membership_crosswalk_edasz_p49.csv",
)

EXPECTED_SUPERSESSIONS = {
    ("Csabacsűd", "OPUS_TITASZ"),
    ("Dabas", "ELMU"),
    ("Dévaványa", "OPUS_TITASZ"),
    ("Gyomaendrőd", "OPUS_TITASZ"),
    ("Kunszentmárton", "OPUS_TITASZ"),
    ("Mohács", "EON_DDASZ"),
    ("Péteri", "ELMU"),
    ("Szeghalom", "OPUS_TITASZ"),
    ("Tiszakécske", "OPUS_TITASZ"),
    ("Tiszasas", "OPUS_TITASZ"),
    ("Tiszaug", "OPUS_TITASZ"),
    ("Újhartyán", "ELMU"),
    ("Zsadány", "OPUS_TITASZ"),
}

RAW_COUNTS = {
    "ELMU": 130,
    "EON_DDASZ": 820,
    "EON_EDASZ": 814,
    "MVM_DEMASZ": 256,
    "MVM_EMASZ": 650,
    "OPUS_TITASZ": 395,
}

EFFECTIVE_COUNTS = {
    "ELMU": 127,
    "EON_DDASZ": 819,
    "EON_EDASZ": 814,
    "MVM_DEMASZ": 256,
    "MVM_EMASZ": 650,
    "OPUS_TITASZ": 386,
}


class B10P62CrossOperatorPartialWholeSupersessionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def raw_whole_rows(self):
        rows = []
        for path in RAW_MEMBERSHIP_FILES:
            rows.extend(
                row
                for row in self.rows(path)
                if row["status"] == "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN"
            )
        return rows

    def supersession_objects(self):
        return tuple(
            WholeMembershipSupersession(
                settlement_name=row["settlement_name"],
                prior_operator_id=row["prior_operator_id"],
                conflict_operator_id=row["conflict_operator_id"],
                authority_source_id=row["conflict_authority_source_id"],
                reason=row["notes"],
            )
            for row in self.rows(SUPERSESSIONS)
        )

    def test_supersession_ledger_is_exactly_the_p61_thirteen_conflicts(self):
        rows = self.rows(SUPERSESSIONS)
        self.assertEqual(13, len(rows))
        actual = {(row["settlement_name"], row["prior_operator_id"]) for row in rows}
        self.assertEqual(EXPECTED_SUPERSESSIONS, actual)
        self.assertEqual(13, len(actual))
        self.assertTrue(all(row["prior_raw_status"] == "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN" for row in rows))
        self.assertTrue(all(row["conflict_operator_id"] == "MVM_DEMASZ" for row in rows))
        self.assertTrue(all(row["conflict_authority_source_id"] == "SRC-B10-MVM-DEMASZ-M1-2026" for row in rows))
        self.assertTrue(all(row["p62_effective_status"] == WHOLE_SETTLEMENT_CLAIM_SUPERSEDED for row in rows))
        self.assertTrue(all(row["admission_rule"] == "ADMINISTRATIVE_UNIT_PRESENCE_ONLY_UNTIL_BOUNDARY_AUTHORITY" for row in rows))

        p61 = self.rows(P61_MATRIX)
        p61_pairs = {
            (row["settlement_name"], row["counterpart_operator_id"])
            for row in p61
            if row["p61_authority_status"] == "CROSS_OPERATOR_ADMIN_UNIT_OVERLAP_BOUNDARY_UNRESOLVED"
        }
        self.assertEqual(EXPECTED_SUPERSESSIONS, p61_pairs)

    def test_every_supersession_targets_one_existing_raw_proven_whole_claim(self):
        raw = self.raw_whole_rows()
        pair_counts = Counter((row["settlement_name"], row["operator_id"]) for row in raw)
        for key in EXPECTED_SUPERSESSIONS:
            self.assertEqual(1, pair_counts[key], key)

    def test_raw_materialization_counts_are_preserved_for_audit(self):
        raw = self.raw_whole_rows()
        counts = Counter(row["operator_id"] for row in raw)
        self.assertEqual(RAW_COUNTS, {operator: counts[operator] for operator in RAW_COUNTS})

    def test_effective_counts_apply_only_the_exact_thirteen_supersessions(self):
        supersessions = self.supersession_objects()
        effective = Counter()
        superseded = Counter()
        for row in self.raw_whole_rows():
            decision = classify_effective_whole_membership(
                settlement_name=row["settlement_name"],
                operator_id=row["operator_id"],
                raw_status=row["status"],
                supersessions=supersessions,
            )
            if decision.effective_status == EFFECTIVE_WHOLE_SETTLEMENT_MEMBERSHIP:
                effective[row["operator_id"]] += 1
            else:
                superseded[row["operator_id"]] += 1

        self.assertEqual(EFFECTIVE_COUNTS, {operator: effective[operator] for operator in EFFECTIVE_COUNTS})
        self.assertEqual(13, sum(superseded.values()))
        self.assertEqual(9, superseded["OPUS_TITASZ"])
        self.assertEqual(3, superseded["ELMU"])
        self.assertEqual(1, superseded["EON_DDASZ"])
        self.assertEqual(0, superseded["EON_EDASZ"])
        self.assertEqual(0, superseded["MVM_DEMASZ"])
        self.assertEqual(0, superseded["MVM_EMASZ"])

    def test_machine_readable_count_summary_matches_computed_effective_surface(self):
        rows = self.rows(COUNTS)
        self.assertEqual(set(RAW_COUNTS), {row["operator_id"] for row in rows})
        for row in rows:
            operator = row["operator_id"]
            self.assertEqual(RAW_COUNTS[operator], int(row["raw_materialized_whole_count"]))
            self.assertEqual(EFFECTIVE_COUNTS[operator], int(row["p62_effective_whole_count"]))
            self.assertEqual(
                RAW_COUNTS[operator] - EFFECTIVE_COUNTS[operator],
                int(row["p62_superseded_whole_claims"]),
            )
            self.assertEqual("EFFECTIVE_AFTER_P62_EXACT_SUPERSESSIONS", row["count_semantics"])

    def test_superseded_claim_fails_closed_at_effective_admission(self):
        supersessions = self.supersession_objects()
        decision = classify_effective_whole_membership(
            settlement_name="Dabas",
            operator_id="ELMU",
            raw_status="WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN",
            supersessions=supersessions,
        )
        self.assertEqual(WHOLE_SETTLEMENT_CLAIM_SUPERSEDED, decision.effective_status)
        self.assertEqual("SRC-B10-MVM-DEMASZ-M1-2026", decision.authority_source_id)
        with self.assertRaises(B10EffectiveMembershipError):
            require_effective_whole_membership(decision)

    def test_unaffected_exact_pair_remains_effectively_admitted(self):
        supersessions = self.supersession_objects()
        decision = classify_effective_whole_membership(
            settlement_name="Kecskemét",
            operator_id="MVM_DEMASZ",
            raw_status="WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN",
            supersessions=supersessions,
        )
        self.assertEqual(EFFECTIVE_WHOLE_SETTLEMENT_MEMBERSHIP, decision.effective_status)
        self.assertIsNone(decision.authority_source_id)
        require_effective_whole_membership(decision)

    def test_supersession_is_exact_not_fuzzy_or_propagated(self):
        supersessions = self.supersession_objects()
        for name, operator in (
            ("DABAS", "ELMU"),
            ("Dabas ", "ELMU"),
            ("Dabas", "MVM_DEMASZ"),
            ("Mohacs", "EON_DDASZ"),
        ):
            decision = classify_effective_whole_membership(
                settlement_name=name,
                operator_id=operator,
                raw_status="WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN",
                supersessions=supersessions,
            )
            self.assertEqual(EFFECTIVE_WHOLE_SETTLEMENT_MEMBERSHIP, decision.effective_status)

    def test_p61_tass_usage_location_is_not_a_p62_whole_claim_supersession(self):
        usage = self.rows(P61_USAGE)
        self.assertEqual(1, len(usage))
        self.assertEqual("Tass", usage[0]["settlement_name"])
        self.assertEqual("ELMU:TASS:UDULOTERULET", usage[0]["usage_location_id"])
        self.assertEqual("USAGE_LOCATION_MEMBERSHIP_PROVEN", usage[0]["status"])
        self.assertNotIn(("Tass", "ELMU"), EXPECTED_SUPERSESSIONS)

    def test_document_freezes_no_boundary_inference_and_append_only_semantics(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "RAW MATERIALIZED WHOLE CLAIM != EFFECTIVE CURRENT WHOLE-SETTLEMENT ADMISSION",
            "CURRENT PARTIAL-SETTLEMENT AUTHORITY + COUNTERPART ADMINISTRATIVE-UNIT TOKEN != TWO WHOLE-SETTLEMENT MEMBERSHIPS",
            "RAW HISTORICAL MATERIALIZATION != CURRENT EFFECTIVE ADMISSION",
            "CLAIM SUPERSESSION != SOURCE-TOKEN DELETION",
            "CROSS-OPERATOR CONFLICT != AUTHORITY TO INFER THE INTERNAL BOUNDARY",
            "SUPERSEDED WHOLE CLAIM != PROVEN COUNTERPART PARTIAL USAGE-LOCATION MEMBERSHIP",
        ):
            self.assertIn(marker, text)

    def test_global_spatial_blockers_and_readiness_remain_fail_closed(self):
        assessment = current_b10_closure_assessment()
        self.assertIn("NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK", assessment.blocking_refs)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", assessment.blocking_refs)
        lines = CANONICAL.read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))
        by_module = {row["module_id"]: row for row in self.rows(MODULE_STATUS)}
        self.assertEqual("IN_PROGRESS", by_module["B10"]["status"])
        self.assertEqual("15", by_module["B10"]["readiness_percent"])


if __name__ == "__main__":
    unittest.main()
