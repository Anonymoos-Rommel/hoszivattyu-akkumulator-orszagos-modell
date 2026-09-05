import csv
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment
from modules.B10.service_area_membership_contract import (
    KSH_SETTLEMENT_IDENTITY,
    PARTIAL_SETTLEMENT,
    PARTIAL_SETTLEMENT_BOUNDARY,
    ServiceAreaMembershipEvidence,
    ServiceAreaMembershipRecord,
    USAGE_LOCATION_MEMBERSHIP_PROVEN,
    USAGE_LOCATION_SERVICE_AREA_MEMBERSHIP,
    classify_service_area_membership,
    require_service_area_membership,
)


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "registry/dso_service_area_membership_demasz_p61_counterpart_authority_matrix.csv"
USAGE = ROOT / "registry/dso_service_area_membership_elmu_p61_usage_location.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_demasz_p61_source_authorities.csv"
P57 = ROOT / "registry/dso_service_area_membership_demasz_p57_partial_settlement_authority_audit.csv"
ELMU_P46 = ROOT / "registry/dso_service_area_membership_crosswalk_elmu_p46.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P61_B10_DEMASZ_PARTIAL_USAGE_LOCATION_AUTHORITY_ACQUISITION.md"

EXPECTED_PARTIAL = {
    "Baja", "Csongrád", "Csabacsűd", "Dabas", "Dévaványa", "Érsekcsanád",
    "Gyomaendrőd", "Kunszentmárton", "Mohács", "Péteri", "Solt", "Szeghalom",
    "Szentes", "Tápiószőlős", "Tass", "Tiszakécske", "Tiszasas", "Tiszaug",
    "Újhartyán", "Zsadány",
}
OPUS_OVERLAP = {
    "Csabacsűd", "Dévaványa", "Gyomaendrőd", "Kunszentmárton", "Szeghalom",
    "Tiszakécske", "Tiszasas", "Tiszaug", "Zsadány",
}
ELMU_ADMIN_OVERLAP = {"Dabas", "Péteri", "Újhartyán"}
NO_HIT = {"Baja", "Csongrád", "Érsekcsanád", "Solt", "Szentes", "Tápiószőlős"}


class B10P61DemaszPartialUsageLocationAuthorityTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_matrix_covers_exact_p57_partial_population_once(self):
        rows = self.rows(MATRIX)
        self.assertEqual(20, len(rows))
        self.assertEqual(EXPECTED_PARTIAL, {r["settlement_name"] for r in rows})
        self.assertEqual(20, len({r["settlement_name"] for r in rows}))
        p57 = {r["source_token"] for r in self.rows(P57)}
        self.assertEqual(EXPECTED_PARTIAL, p57)
        self.assertTrue(all(r["mvm_partial_source_id"] == "SRC-B10-MVM-DEMASZ-M1-2026" for r in rows))

    def test_counterpart_partition_is_exact_and_fail_closed(self):
        rows = self.rows(MATRIX)
        by_status = {}
        for row in rows:
            by_status.setdefault(row["p61_authority_status"], set()).add(row["settlement_name"])
        self.assertEqual(
            OPUS_OVERLAP | ELMU_ADMIN_OVERLAP | {"Mohács"},
            by_status["CROSS_OPERATOR_ADMIN_UNIT_OVERLAP_BOUNDARY_UNRESOLVED"],
        )
        self.assertEqual(NO_HIT, by_status["NO_CURRENT_COUNTERPART_TOKEN_DISCOVERED_IN_TARGETED_P61_SCAN"])
        self.assertEqual({"Tass"}, by_status["ELMU_NAMED_USAGE_LOCATION_MEMBERSHIP_PROVEN"])
        self.assertEqual(13, len(by_status["CROSS_OPERATOR_ADMIN_UNIT_OVERLAP_BOUNDARY_UNRESOLVED"]))
        self.assertEqual(6, len(NO_HIT))

    def test_operator_specific_overlap_sets_are_frozen(self):
        rows = self.rows(MATRIX)
        self.assertEqual(
            OPUS_OVERLAP,
            {r["settlement_name"] for r in rows if r["counterpart_operator_id"] == "OPUS_TITASZ"},
        )
        self.assertEqual(
            ELMU_ADMIN_OVERLAP | {"Tass"},
            {r["settlement_name"] for r in rows if r["counterpart_operator_id"] == "ELMU"},
        )
        self.assertEqual(
            {"Mohács"},
            {r["settlement_name"] for r in rows if r["counterpart_operator_id"] == "EON_DDASZ"},
        )
        tass = next(r for r in rows if r["settlement_name"] == "Tass")
        self.assertEqual("Tass üdülőterület", tass["counterpart_source_token"])
        self.assertEqual("NAMED_TERRITORIAL_SUBSET", tass["counterpart_grain"])

    def test_current_mvm_m1_supersedes_incomplete_html_for_p61_partial_population(self):
        rows = {r["source_id"]: r for r in self.rows(SOURCES)}
        current = rows["SRC-B10-MVM-DEMASZ-M1-2026"]
        self.assertEqual("https://mvmhalozat.hu/attachments/41985", current["source_url"])
        self.assertEqual("OFFICIAL_CURRENT_M1_ATTACHMENT", current["source_kind"])
        self.assertEqual("CANONICAL_P61_MVM_PARTIAL_AUTHORITY", current["p61_status"])
        legacy = rows["SRC-B10-MVM-DEMASZ-SERVICE-AREA-2026"]
        self.assertEqual("NOT_CANONICAL_FOR_P61_PARTIAL_POPULATION", legacy["p61_status"])
        self.assertEqual("https://mvmhalozat.hu/aram/oldalak/6454", legacy["source_url"])

    def test_tass_usage_location_row_is_exactly_one_non_whole_membership(self):
        rows = self.rows(USAGE)
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("20525", row["ksh_settlement_code"])
        self.assertEqual("Tass", row["settlement_name"])
        self.assertEqual("ELMU", row["operator_id"])
        self.assertEqual("ELMU:SERVICE_AREA", row["service_area_id"])
        self.assertEqual("PARTIAL_SETTLEMENT", row["coverage_scope"])
        self.assertEqual("ELMU:TASS:UDULOTERULET", row["usage_location_id"])
        self.assertEqual("Tass üdülőterület", row["usage_location_label"])
        self.assertEqual("DER", row["evidence_status"])
        self.assertEqual("USAGE_LOCATION_MEMBERSHIP_PROVEN", row["status"])
        self.assertEqual(
            {
                "SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS",
                "SRC-B10-ELMU-OPERATING-LICENCE-805-2006",
                "SRC-B10-ELMU-M1-CANDIDATE-2025",
            },
            set(row["source_ids"].split(";")),
        )

    def test_tass_row_replays_through_p15_runtime_as_usage_location_membership(self):
        name = "Tass"
        code = "20525"
        operator = "ELMŰ Hálózati Kft."
        area = "ELMU:SERVICE_AREA"
        usage = "ELMU:TASS:UDULOTERULET"
        ksh = ServiceAreaMembershipEvidence(
            "SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS", 1, "OBS",
            (KSH_SETTLEMENT_IDENTITY, f"SETTLEMENT_NAME:{name}", f"KSH_SETTLEMENT_CODE:{code}"),
        )
        licence_boundary = ServiceAreaMembershipEvidence(
            "SRC-B10-ELMU-OPERATING-LICENCE-805-2006", 1, "OBS",
            (
                PARTIAL_SETTLEMENT_BOUNDARY,
                f"SETTLEMENT_NAME:{name}",
                f"NETWORK_OPERATOR:{operator}",
                f"SERVICE_AREA_ID:{area}",
                PARTIAL_SETTLEMENT,
            ),
        )
        current_location = ServiceAreaMembershipEvidence(
            "SRC-B10-ELMU-M1-CANDIDATE-2025", 2, "DER",
            (
                USAGE_LOCATION_SERVICE_AREA_MEMBERSHIP,
                f"SETTLEMENT_NAME:{name}",
                f"NETWORK_OPERATOR:{operator}",
                f"SERVICE_AREA_ID:{area}",
                f"USAGE_LOCATION_ID:{usage}",
            ),
        )
        record = ServiceAreaMembershipRecord(
            settlement_name=name,
            ksh_settlement_code=code,
            network_operator=operator,
            service_area_id=area,
            coverage_scope=PARTIAL_SETTLEMENT,
            usage_location_id=usage,
            source_refs=(
                "SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS",
                "SRC-B10-ELMU-OPERATING-LICENCE-805-2006",
                "SRC-B10-ELMU-M1-CANDIDATE-2025",
            ),
            evidence=(ksh, licence_boundary, current_location),
        )
        decision = classify_service_area_membership(record)
        self.assertEqual(USAGE_LOCATION_MEMBERSHIP_PROVEN, decision.status)
        self.assertEqual("DER", decision.evidence_status)
        self.assertEqual(usage, decision.usage_location_id)
        self.assertEqual(area, require_service_area_membership(decision))

    def test_tass_usage_location_does_not_promote_whole_tass_or_complement(self):
        elmu_whole = {r["settlement_name"] for r in self.rows(ELMU_P46)}
        self.assertNotIn("Tass", elmu_whole)
        self.assertEqual(1, len(CANONICAL.read_text(encoding="utf-8").splitlines()))
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "NAMED ELMŰ SUBSET != AUTHORITY TO INFER THE MVM DÉMÁSZ COMPLEMENT",
            "CURRENT CROSS-OPERATOR ADMINISTRATIVE-UNIT OVERLAP != EXACT USAGE-LOCATION BOUNDARY",
            "USAGE-LOCATION SERVICE-AREA MEMBERSHIP != EXACT DSO NODE",
            "one resolved usage-location is real progress, but it is not national completion",
        ):
            self.assertIn(marker, text)

    def test_global_partial_blocker_and_readiness_remain_until_population_is_resolved(self):
        assessment = current_b10_closure_assessment()
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", assessment.blocking_refs)
        by_module = {r["module_id"]: r for r in self.rows(MODULE_STATUS)}
        self.assertEqual("IN_PROGRESS", by_module["B10"]["status"])
        self.assertEqual("15", by_module["B10"]["readiness_percent"])


if __name__ == "__main__":
    unittest.main()
