from pathlib import Path
import unittest

from modules.B10.dso_territorial_coverage_contract import (
    ADMINISTRATIVE_REPORTING_GRAIN,
    B10DsoTerritorialCoverageError,
    CANONICAL_NETWORK_REGIONAL_GRAIN,
    DSO_LICENSEE_INVENTORY,
    DSO_SERVICE_AREA_REGION_LABEL,
    DsoServiceAreaInventoryRecord,
    DsoTerritorialEvidence,
    EXPECTED_DSO_OPERATORS,
    NATIONAL_DSO_OPERATOR_INVENTORY_PROVEN,
    Q_EXACT_DSO_NODE_INVENTORY,
    Q_NATIONAL_DSO_OPERATOR_INVENTORY,
    Q_SERVICE_AREA_MEMBERSHIP_CROSSWALK,
    assess_national_dso_territorial_coverage,
    load_canonical_dso_inventory,
    require_national_dso_operator_inventory,
)
from modules.B10.spatial_authority_contract import DSO_SERVICE_AREA


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "registry/dso_service_area_inventory.csv"
SOURCE_REGISTRY = ROOT / "registry/dso_service_area_sources.csv"


class B10P14DsoTerritorialCoverageTests(unittest.TestCase):
    def canonical_records(self):
        return load_canonical_dso_inventory(INVENTORY)

    def test_registry_contains_exact_current_six_operator_inventory(self):
        records = self.canonical_records()
        self.assertEqual(6, len(records))
        self.assertEqual(set(EXPECTED_DSO_OPERATORS), {record.operator_id for record in records})
        self.assertEqual(
            set(EXPECTED_DSO_OPERATORS.values()),
            {record.network_operator for record in records},
        )

    def test_canonical_registry_proves_operator_inventory_only(self):
        decision = assess_national_dso_territorial_coverage(self.canonical_records())
        self.assertEqual(NATIONAL_DSO_OPERATOR_INVENTORY_PROVEN, decision.operator_inventory_status)
        self.assertEqual("OBS", decision.evidence_status)
        self.assertEqual(tuple(sorted(EXPECTED_DSO_OPERATORS)), decision.operator_ids)

    def test_network_regional_grain_is_dso_service_area_not_administrative_region(self):
        decision = assess_national_dso_territorial_coverage(self.canonical_records())
        self.assertEqual(DSO_SERVICE_AREA, CANONICAL_NETWORK_REGIONAL_GRAIN)
        self.assertEqual(DSO_SERVICE_AREA, decision.canonical_network_regional_grain)
        self.assertEqual("ADMINISTRATIVE_REGION", ADMINISTRATIVE_REPORTING_GRAIN)
        self.assertEqual("ADMINISTRATIVE_REGION", decision.administrative_reporting_grain)
        self.assertNotEqual(decision.canonical_network_regional_grain, decision.administrative_reporting_grain)

    def test_operator_inventory_does_not_promote_membership_crosswalk_or_node_inventory(self):
        decision = assess_national_dso_territorial_coverage(self.canonical_records())
        self.assertEqual(Q_SERVICE_AREA_MEMBERSHIP_CROSSWALK, decision.service_area_membership_crosswalk_status)
        self.assertEqual(Q_EXACT_DSO_NODE_INVENTORY, decision.exact_dso_node_inventory_status)
        self.assertFalse(hasattr(decision, "county_to_dso_mapping"))
        self.assertFalse(hasattr(decision, "substation_ids"))
        self.assertFalse(hasattr(decision, "hosting_capacity_mw"))

    def test_missing_one_operator_keeps_national_inventory_q(self):
        records = self.canonical_records()[:-1]
        decision = assess_national_dso_territorial_coverage(records)
        self.assertEqual(Q_NATIONAL_DSO_OPERATOR_INVENTORY, decision.operator_inventory_status)
        self.assertEqual("Q", decision.evidence_status)
        with self.assertRaisesRegex(B10DsoTerritorialCoverageError, "complete national DSO operator inventory"):
            require_national_dso_operator_inventory(decision)

    def test_duplicate_operator_record_is_rejected(self):
        records = list(self.canonical_records())
        records.append(records[0])
        with self.assertRaisesRegex(B10DsoTerritorialCoverageError, "duplicate DSO operator"):
            assess_national_dso_territorial_coverage(records)

    def test_wrong_operator_identity_fails_closed(self):
        base = self.canonical_records()[0]
        with self.assertRaisesRegex(B10DsoTerritorialCoverageError, "network_operator"):
            DsoServiceAreaInventoryRecord(
                operator_id=base.operator_id,
                network_operator="Wrong Operator",
                service_area_id=base.service_area_id,
                service_area_label=base.service_area_label,
                source_refs=base.source_refs,
                evidence=base.evidence,
            )

    def test_wrong_service_area_identity_fails_closed(self):
        base = self.canonical_records()[0]
        with self.assertRaisesRegex(B10DsoTerritorialCoverageError, "service_area_id"):
            DsoServiceAreaInventoryRecord(
                operator_id=base.operator_id,
                network_operator=base.network_operator,
                service_area_id="COUNTY:PEST",
                service_area_label=base.service_area_label,
                source_refs=base.source_refs,
                evidence=base.evidence,
            )

    def test_q_licensee_evidence_cannot_prove_national_inventory(self):
        records = list(self.canonical_records())
        base = records[0]
        q_license = DsoTerritorialEvidence(
            source_id="Q-SOURCE",
            authority_level=1,
            truth_status="Q",
            supports=(DSO_LICENSEE_INVENTORY, f"NETWORK_OPERATOR:{base.network_operator}"),
        )
        label = DsoTerritorialEvidence(
            source_id="LABEL-SOURCE",
            authority_level=2,
            truth_status="OBS",
            supports=(
                DSO_SERVICE_AREA_REGION_LABEL,
                f"NETWORK_OPERATOR:{base.network_operator}",
                f"SERVICE_AREA_ID:{base.service_area_id}",
                f"SERVICE_AREA_LABEL:{base.service_area_label}",
            ),
        )
        records[0] = DsoServiceAreaInventoryRecord(
            operator_id=base.operator_id,
            network_operator=base.network_operator,
            service_area_id=base.service_area_id,
            service_area_label=base.service_area_label,
            source_refs=("Q-SOURCE", "LABEL-SOURCE"),
            evidence=(q_license, label),
        )
        decision = assess_national_dso_territorial_coverage(records)
        self.assertEqual(Q_NATIONAL_DSO_OPERATOR_INVENTORY, decision.operator_inventory_status)
        self.assertEqual("Q", decision.evidence_status)

    def test_region_label_without_bound_claim_does_not_mint_crosswalk(self):
        records = self.canonical_records()
        decision = assess_national_dso_territorial_coverage(records)
        self.assertIn("broad source-published service-area labels", decision.reason)
        self.assertEqual(Q_SERVICE_AREA_MEMBERSHIP_CROSSWALK, decision.service_area_membership_crosswalk_status)

    def test_source_registry_resolves_every_inventory_source_reference(self):
        source_lines = SOURCE_REGISTRY.read_text(encoding="utf-8").splitlines()
        source_ids = {line.split(",", 1)[0] for line in source_lines[1:]}
        inventory_refs = {
            ref
            for record in self.canonical_records()
            for ref in record.source_refs
        }
        self.assertTrue(inventory_refs.issubset(source_ids))
        self.assertIn("SRC-B10-MVM-DEMASZ-SERVICE-AREA-2026", source_ids)

    def test_mvm_demasz_registry_note_does_not_generalize_partial_settlements(self):
        text = INVENTORY.read_text(encoding="utf-8")
        self.assertIn("MVM_DEMASZ:SERVICE_AREA", text)
        self.assertIn("partial-settlement exceptions", text)
        self.assertNotIn("COUNTY_TO_DSO_PROVEN", text)
        self.assertNotIn("EXACT_NODE_PROVEN", text)

    def test_require_inventory_returns_exact_six_only_after_proof(self):
        decision = assess_national_dso_territorial_coverage(self.canonical_records())
        self.assertEqual(tuple(sorted(EXPECTED_DSO_OPERATORS)), require_national_dso_operator_inventory(decision))


if __name__ == "__main__":
    unittest.main()
