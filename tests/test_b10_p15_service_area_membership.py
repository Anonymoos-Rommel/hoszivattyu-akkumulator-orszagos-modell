import csv
from pathlib import Path
import unittest

from modules.B10.service_area_membership_contract import (
    B10ServiceAreaMembershipError,
    DSO_SERVICE_AREA_MEMBERSHIP,
    KSH_SETTLEMENT_IDENTITY,
    PARTIAL_SETTLEMENT,
    PARTIAL_SETTLEMENT_BOUNDARY,
    Q_ADMINISTRATIVE_IDENTIFIER_NORMALIZATION,
    Q_PARTIAL_SETTLEMENT_USAGE_LOCATION_REQUIRED,
    Q_SERVICE_AREA_MEMBERSHIP_UNRESOLVED,
    ServiceAreaMembershipEvidence,
    ServiceAreaMembershipRecord,
    USAGE_LOCATION_MEMBERSHIP_PROVEN,
    USAGE_LOCATION_SERVICE_AREA_MEMBERSHIP,
    WHOLE_SETTLEMENT,
    WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN,
    classify_service_area_membership,
    require_service_area_membership,
)
from modules.B10.spatial_authority_contract import DSO_SERVICE_AREA


ROOT = Path(__file__).resolve().parents[1]


class B10P15ServiceAreaMembershipTests(unittest.TestCase):
    def evidence(self, *supports, source_id="SRC", level=2, truth="OBS"):
        return ServiceAreaMembershipEvidence(source_id=source_id, authority_level=level, truth_status=truth, supports=tuple(supports))

    def ksh(self, name="Kecskemét", code="26684", source_id="KSH"):
        return self.evidence(KSH_SETTLEMENT_IDENTITY, f"SETTLEMENT_NAME:{name}", f"KSH_SETTLEMENT_CODE:{code}", source_id=source_id)

    def whole(self, name="Kecskemét", operator="MVM Démász Áramhálózati Kft.", area="MVM_DEMASZ:SERVICE_AREA", source_id="DSO"):
        return self.evidence(DSO_SERVICE_AREA_MEMBERSHIP, f"SETTLEMENT_NAME:{name}", f"NETWORK_OPERATOR:{operator}", f"SERVICE_AREA_ID:{area}", WHOLE_SETTLEMENT, source_id=source_id)

    def test_whole_settlement_requires_ksh_and_dso_authority(self):
        record = ServiceAreaMembershipRecord(settlement_name="Kecskemét", ksh_settlement_code="26684", network_operator="MVM Démász Áramhálózati Kft.", service_area_id="MVM_DEMASZ:SERVICE_AREA", coverage_scope=WHOLE_SETTLEMENT, source_refs=("KSH", "DSO"), evidence=(self.ksh(), self.whole()))
        decision = classify_service_area_membership(record)
        self.assertEqual(WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN, decision.status)
        self.assertEqual("MVM_DEMASZ:SERVICE_AREA", require_service_area_membership(decision))
        self.assertEqual(DSO_SERVICE_AREA, decision.region_grain)

    def test_settlement_name_without_ksh_identity_remains_q(self):
        record = ServiceAreaMembershipRecord(settlement_name="Kecskemét", ksh_settlement_code=None, network_operator="MVM Démász Áramhálózati Kft.", service_area_id="MVM_DEMASZ:SERVICE_AREA", coverage_scope=WHOLE_SETTLEMENT, source_refs=("DSO",), evidence=(self.whole(),))
        decision = classify_service_area_membership(record)
        self.assertEqual(Q_ADMINISTRATIVE_IDENTIFIER_NORMALIZATION, decision.status)
        self.assertIsNone(decision.service_area_id)

    def test_ksh_code_without_bound_identity_evidence_remains_q(self):
        record = ServiceAreaMembershipRecord(settlement_name="Kecskemét", ksh_settlement_code="26684", network_operator="MVM Démász Áramhálózati Kft.", service_area_id="MVM_DEMASZ:SERVICE_AREA", coverage_scope=WHOLE_SETTLEMENT, source_refs=("DSO",), evidence=(self.whole(),))
        self.assertEqual(Q_ADMINISTRATIVE_IDENTIFIER_NORMALIZATION, classify_service_area_membership(record).status)

    def test_partial_settlement_cannot_promote_whole_settlement_membership(self):
        name = "Partialville"; operator = "MVM Démász Áramhálózati Kft."; area = "MVM_DEMASZ:SERVICE_AREA"
        partial = self.evidence(PARTIAL_SETTLEMENT_BOUNDARY, f"SETTLEMENT_NAME:{name}", f"NETWORK_OPERATOR:{operator}", f"SERVICE_AREA_ID:{area}", PARTIAL_SETTLEMENT, source_id="DSO")
        record = ServiceAreaMembershipRecord(settlement_name=name, ksh_settlement_code="99999", network_operator=operator, service_area_id=area, coverage_scope=PARTIAL_SETTLEMENT, source_refs=("KSH", "DSO"), evidence=(self.ksh(name=name, code="99999"), partial))
        decision = classify_service_area_membership(record)
        self.assertEqual(Q_PARTIAL_SETTLEMENT_USAGE_LOCATION_REQUIRED, decision.status)
        self.assertIsNone(decision.service_area_id)
        with self.assertRaises(B10ServiceAreaMembershipError):
            require_service_area_membership(decision)

    def test_partial_settlement_can_resolve_only_at_exact_usage_location(self):
        name = "Partialville"; operator = "MVM Démász Áramhálózati Kft."; area = "MVM_DEMASZ:SERVICE_AREA"; usage = "USAGE-001"
        partial = self.evidence(PARTIAL_SETTLEMENT_BOUNDARY, f"SETTLEMENT_NAME:{name}", f"NETWORK_OPERATOR:{operator}", f"SERVICE_AREA_ID:{area}", PARTIAL_SETTLEMENT, source_id="DSO")
        location = self.evidence(USAGE_LOCATION_SERVICE_AREA_MEMBERSHIP, f"SETTLEMENT_NAME:{name}", f"NETWORK_OPERATOR:{operator}", f"SERVICE_AREA_ID:{area}", f"USAGE_LOCATION_ID:{usage}", source_id="LOC", level=2)
        record = ServiceAreaMembershipRecord(settlement_name=name, ksh_settlement_code="99999", network_operator=operator, service_area_id=area, coverage_scope=PARTIAL_SETTLEMENT, usage_location_id=usage, source_refs=("KSH", "DSO", "LOC"), evidence=(self.ksh(name=name, code="99999"), partial, location))
        decision = classify_service_area_membership(record)
        self.assertEqual(USAGE_LOCATION_MEMBERSHIP_PROVEN, decision.status)
        self.assertEqual(area, require_service_area_membership(decision))
        self.assertEqual(usage, decision.usage_location_id)

    def test_wrong_operator_binding_does_not_authorize_membership(self):
        wrong = self.whole(operator="OPUS TITÁSZ Áramhálózati Zrt.")
        record = ServiceAreaMembershipRecord(settlement_name="Kecskemét", ksh_settlement_code="26684", network_operator="MVM Démász Áramhálózati Kft.", service_area_id="MVM_DEMASZ:SERVICE_AREA", coverage_scope=WHOLE_SETTLEMENT, source_refs=("KSH", "DSO"), evidence=(self.ksh(), ServiceAreaMembershipEvidence("DSO", 2, "OBS", wrong.supports)))
        self.assertEqual(Q_SERVICE_AREA_MEMBERSHIP_UNRESOLVED, classify_service_area_membership(record).status)

    def test_unreferenced_membership_evidence_cannot_authorize(self):
        record = ServiceAreaMembershipRecord(settlement_name="Kecskemét", ksh_settlement_code="26684", network_operator="MVM Démász Áramhálózati Kft.", service_area_id="MVM_DEMASZ:SERVICE_AREA", coverage_scope=WHOLE_SETTLEMENT, source_refs=("KSH",), evidence=(self.ksh(), self.whole()))
        self.assertEqual(Q_SERVICE_AREA_MEMBERSHIP_UNRESOLVED, classify_service_area_membership(record).status)

    def test_q_referenced_evidence_cannot_promote_membership(self):
        q = self.evidence("UNRESOLVED_MEMBERSHIP_CONTEXT", source_id="Q", truth="Q")
        record = ServiceAreaMembershipRecord(settlement_name="Kecskemét", ksh_settlement_code="26684", network_operator="MVM Démász Áramhálózati Kft.", service_area_id="MVM_DEMASZ:SERVICE_AREA", coverage_scope=WHOLE_SETTLEMENT, source_refs=("KSH", "DSO", "Q"), evidence=(self.ksh(), self.whole(), q))
        self.assertEqual(Q_SERVICE_AREA_MEMBERSHIP_UNRESOLVED, classify_service_area_membership(record).status)

    def test_membership_decision_does_not_mint_exact_node(self):
        record = ServiceAreaMembershipRecord(settlement_name="Kecskemét", ksh_settlement_code="26684", network_operator="MVM Démász Áramhálózati Kft.", service_area_id="MVM_DEMASZ:SERVICE_AREA", coverage_scope=WHOLE_SETTLEMENT, source_refs=("KSH", "DSO"), evidence=(self.ksh(), self.whole()))
        decision = classify_service_area_membership(record)
        self.assertFalse(hasattr(decision, "target_node_region_id"))
        self.assertFalse(hasattr(decision, "headroom_mw"))
        self.assertFalse(hasattr(decision, "hosting_capacity_mw"))

    def test_service_area_id_must_preserve_canonical_identity(self):
        with self.assertRaisesRegex(B10ServiceAreaMembershipError, "service_area_id"):
            ServiceAreaMembershipRecord(settlement_name="Kecskemét", ksh_settlement_code="26684", network_operator="MVM Démász Áramhálózati Kft.", service_area_id="COUNTY:BACS_KISKUN", coverage_scope=WHOLE_SETTLEMENT, source_refs=("KSH",), evidence=(self.ksh(),))

    def test_source_manifest_covers_exact_six_p14_operators(self):
        with (ROOT / "registry/dso_service_area_membership_sources.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(6, len(rows))
        self.assertEqual({"ELMU", "EON_DDASZ", "EON_EDASZ", "MVM_DEMASZ", "MVM_EMASZ", "OPUS_TITASZ"}, {row["operator_id"] for row in rows})
        by_operator = {row["operator_id"]: row for row in rows}
        for operator in {"ELMU", "EON_DDASZ", "EON_EDASZ"}:
            self.assertEqual("CURRENT_2026_DER_APPROVED_PACKAGE_REVISION_LINEAGE", by_operator[operator]["currentness_status"])
            self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", by_operator[operator]["extraction_status"])
        for operator in {"MVM_DEMASZ", "MVM_EMASZ", "OPUS_TITASZ"}:
            self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", by_operator[operator]["extraction_status"])

    def test_crosswalk_registry_remains_header_only(self):
        lines = (ROOT / "registry/dso_service_area_membership_crosswalk.csv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))
        self.assertTrue(lines[0].startswith("ksh_settlement_code,settlement_name,operator_id,"))


if __name__ == "__main__":
    unittest.main()
