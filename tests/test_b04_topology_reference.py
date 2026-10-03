import csv
import hashlib
import json
import shutil
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from modules.B04.topology_reference import (
    AS_OF, DATA_RELATIVE, MANIFEST_RELATIVE, MANIFEST_SHA256, OPERATIONS,
    ROOT, TOPOLOGIES, TopologyReferenceError, load_topology_reference,
)


class B04TopologyReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = load_topology_reference(as_of=AS_OF)

    def copied_inputs(self, path):
        for name in (DATA_RELATIVE, MANIFEST_RELATIVE):
            target = path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def test_explicit_date_is_required(self):
        with self.assertRaises(TypeError):
            load_topology_reference()

    def test_unadmitted_dates_fail_closed(self):
        for value in (None, True, 20261003, "2026-10-02", "2026-10-04", "current", "2026-10-03T00:00:00Z"):
            with self.subTest(value=value), self.assertRaises(TopologyReferenceError):
                load_topology_reference(as_of=value)

    def test_exact_source_inventory(self):
        self.assertEqual(21, len(self.reference.sources))
        self.assertEqual(MANIFEST_SHA256, hashlib.sha256((ROOT / MANIFEST_RELATIVE).read_bytes()).hexdigest())
        for source in self.reference.sources.values():
            self.assertEqual(64, len(source["sha256"]))
            self.assertIsNone(source["repo_snapshot_path"])
            self.assertNotIn("private_snapshot_path", source)
            self.assertIn("NOT_CLEARED", source["reuse_status"])

    def test_exact_six_topologies_and_four_independent_operations(self):
        self.assertEqual(TOPOLOGIES, set(self.reference.topologies))
        for topology in self.reference.topologies.values():
            self.assertEqual(OPERATIONS, set(topology["operations"]))

    def test_all_twenty_four_actual_permissions_remain_open(self):
        for topology in TOPOLOGIES:
            for operation in OPERATIONS:
                row = self.reference.operation(topology, operation)
                self.assertEqual("OPEN", row["legal_status"])
                self.assertEqual("Q", row["compatibility_registry_status"])
                self.assertIs(row["execution_authorized"], False)
                with self.assertRaisesRegex(TopologyReferenceError, "actual permission is OPEN"):
                    self.reference.require_operation_permission(topology, operation)

    def test_unknown_ids_do_not_fall_back(self):
        for topology, operation in (("NORMAL", "VPP_AGGREGATION_CONTROL"), ("H-ONLY-DEDICATED", "export"), (None, None), ([], [])):
            with self.subTest(topology=topology, operation=operation), self.assertRaises(TopologyReferenceError):
                self.reference.operation(topology, operation)

    def test_reference_wiring_is_not_as_built(self):
        for topology in self.reference.topologies.values():
            self.assertEqual("REFERENCE_ONLY_NOT_AS_BUILT_NOT_INSTALLATION_APPROVAL", topology["schematic_type"])
            self.assertEqual("OPEN", topology["actual_topology_status"])
            self.assertEqual("OPEN", topology["connection_point_to_pod_mapping_status"])
            self.assertTrue(topology["reference_wiring"])

    def test_absent_path_is_disabled_without_fabricated_legal_no(self):
        row = self.reference.operation("H-ONLY-DEDICATED", "BATTERY_CHARGE_FROM_H")
        self.assertEqual("ABSENT_REFERENCE_PATH", row["operation_applicability"])
        self.assertEqual("DISABLED_REFERENCE_HAS_NO_H_PATH", row["execution_state"])
        self.assertEqual("OPEN", row["legal_status"])

    def test_no_path_does_not_fabricate_zero_foregone_value(self):
        for topology in self.reference.topologies.values():
            for row in topology["operations"].values():
                self.assertIsNone(row["value_of_foregone_benefit"])
                self.assertEqual("UNKNOWN_NOT_ZERO", row["foregone_benefit_status"])

    def test_every_open_has_sources_reason_and_route(self):
        for topology in self.reference.topologies.values():
            for row in topology["operations"].values():
                self.assertGreater(len(row["reason"]), 40)
                self.assertGreaterEqual(len(row["evidence_route"]), 4)
                self.assertTrue(set(row["source_ids"]) <= self.reference.sources.keys())

    def test_vpp_load_control_needs_neither_battery_nor_export_by_default(self):
        row = self.reference.operation("H-ONLY-DEDICATED", "VPP_AGGREGATION_CONTROL")
        self.assertEqual("POSSIBLE_OR_UNRESOLVED", row["operation_applicability"])
        self.assertIs(self.reference.claims["VPP_GENERAL_ROUTE"]["export_is_necessary"], False)
        self.assertIs(self.reference.dispatch_contract["vpp_requires_export_by_default"], False)
        self.assertIs(self.reference.dispatch_contract["vpp_with_actual_export_requires_separate_export_gate"], True)

    def test_supplier_brp_permission_not_added_to_statutory_route(self):
        self.assertIs(self.reference.dispatch_contract["supplier_or_BRP_approval_added_gate"], False)
        row = self.reference.operation("H-ONLY-DEDICATED", "VPP_AGGREGATION_CONTROL")
        self.assertTrue(any("do not demand supplier/BRP permission" in item for item in row["evidence_route"]))
        self.assertEqual("OPEN", self.reference.claims["VPP_GENERAL_ROUTE"]["actual_site_status"])

    def test_outside_h_vpp_does_not_acquire_h_contract_prerequisite(self):
        row = self.reference.operation("NORMAL-A1", "VPP_AGGREGATION_CONTROL")
        route = next(item for item in row["evidence_route"] if "H supply contract" in item)
        self.assertIn("For an actual H branch or H-tariff claim only", route)
        self.assertIn("not a prerequisite for outside-H aggregation", route)

    def test_operational_protocol_and_selected_service_debt_remains_explicit(self):
        claim = self.reference.claims["VPP_DSO_IMPLEMENTATION_ROUTE"]
        self.assertIn("Post2026-07-31", claim["remaining"])
        self.assertIn("consumer terms", claim["remaining"])
        self.assertEqual("OPEN", claim["site_status"])

    def test_hmke_exclusion_is_conditional_tariff_rule_not_operation_ban(self):
        claim = self.reference.claims["HMKE_SAME_CONNECTION_H_TARIFF"]
        self.assertEqual("NO", claim["conditional_status"])
        self.assertIn("csatlakozási pont", claim["target"])
        self.assertIn("affirmatively evidenced", claim["condition"])
        self.assertIn("VPP load control", claim["does_not_decide"])
        for row in self.reference.topologies["HMKE-EXPORT"]["operations"].values():
            self.assertEqual("OPEN", row["legal_status"])

    def test_connection_point_pod_address_not_conflated(self):
        boundaries = self.reference.boundaries
        self.assertIn("ownership boundary", boundaries["csatlakozasi_pont"])
        self.assertIn("not interchangeable", boundaries["felhasznalasi_hely"])
        self.assertIn("never infer from address", boundaries["mapping"])

    def test_historical_id_is_retained_and_repealed_not_retargeted(self):
        source = self.reference.sources["SRC-B04-NJT-H-TARIFF-2026"]
        self.assertIn("2008-44-20-2M", source["original_url"])
        self.assertEqual("REPEALED", source["lineage"]["status"])
        self.assertEqual("2011-02-01", source["lineage"]["repealed_from"])
        self.assertIn("§3(9)", source["locators"])
        self.assertIsNone(source["claim_current_as_of"])

    def test_current_instrument_and_clause_effectivity_are_distinct(self):
        source = self.reference.sources["SRC-B04-NJT-NFM4-2011-CURRENT-20261003"]
        self.assertEqual("2011-02-01", source["legal_or_contract_effective_from"])
        self.assertIn("2026-08-29", source["document_revision"])
        claim = self.reference.claims["H_CURRENT_SCOPE"]
        self.assertEqual("2025-08-01", claim["legal_effective_from"])
        self.assertEqual("2026-03-01", claim["contract_effective_from"])
        self.assertEqual("2026-10-03", source["claim_current_as_of"])

    def test_grandfather_exact_date_wording_without_automatic_predicate(self):
        claim = self.reference.claims["H_GRANDFATHER"]
        self.assertEqual("2020. január 1-ig", claim["source_boundary_text"])
        self.assertEqual("2020-01-01", claim["legal_effective_from"])
        self.assertIn("at least3", claim["threshold"])
        self.assertIs(claim["automatic_site_classification"], False)
        with (ROOT / "registry/electricity_price_variables.csv").open(newline="") as handle:
            row = next(row for row in csv.DictReader(handle) if row["variable_id"] == "VAR-B04-H-SPF-MIN")
        self.assertEqual("POL", row["status"])
        self.assertIn("General minimum 3.4", row["notes"])
        self.assertIn("grandfather minimum 3", row["notes"])
        self.assertIn("2020. január 1-ig", row["notes"])

    def test_storage_notification_is_not_h_or_export_permission(self):
        claim = self.reference.claims["STORAGE_NOTIFICATION"]
        self.assertEqual("2026-08-29", claim["clause_effective_from"])
        self.assertEqual(("H tariff entitlement", "export right", "VPP enrollment"), claim["does_not_create"])

    def test_nested_results_are_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            self.reference.as_of = "2027-01-01"
        with self.assertRaises(TypeError):
            self.reference.topologies["H-ONLY-DEDICATED"]["operations"]["VPP_AGGREGATION_CONTROL"]["legal_status"] = "YES"
        with self.assertRaises(TypeError):
            self.reference.sources["SRC-B04-NJT-VET-20261001"]["locators"][0] = "fake"

    def test_exact_relocated_copies_are_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.copied_inputs(root)
            other = load_topology_reference(as_of=AS_OF, root=root)
            self.assertEqual(self.reference.topologies, other.topologies)

    def test_modified_data_cannot_grant_permission(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.copied_inputs(root)
            path = root / DATA_RELATIVE; data = json.loads(path.read_text())
            data["topologies"][0]["operations"]["VPP_AGGREGATION_CONTROL"]["legal_status"] = "YES"
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(TopologyReferenceError, "byte identity mismatch"):
                load_topology_reference(as_of=AS_OF, root=root)

    def test_rebound_manifest_does_not_inherit_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.copied_inputs(root)
            path = root / DATA_RELATIVE; data = json.loads(path.read_text())
            data["topologies"][0]["operations"]["VPP_AGGREGATION_CONTROL"]["execution_authorized"] = True
            path.write_text(json.dumps(data))
            mpath = root / MANIFEST_RELATIVE; manifest = json.loads(mpath.read_text())
            manifest["artifact"].update(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            mpath.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(TopologyReferenceError, "manifest identity mismatch"):
                load_topology_reference(as_of=AS_OF, root=root)

    def test_missing_inputs_report_reference_error(self):
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(TopologyReferenceError):
            load_topology_reference(as_of=AS_OF, root=Path(directory))

    def test_registry_aliases_include_separate_vpp_gate_and_stay_q(self):
        for name in ("battery_variables.csv", "variables.csv"):
            with (ROOT / "registry" / name).open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            row = next(row for row in rows if row["variable_id"] == "VAR-B07-H-TARIFF-VPP-CONTROL-ALLOWED")
            self.assertEqual("Q", row["status"])
            self.assertIn("SRC-B04-NJT-VET-20261001", row["source_ids"])

    def test_researched_open_does_not_close_actual_legal_blocker(self):
        with (ROOT / "registry/project_blocker_evidence_audit.csv").open(newline="") as handle:
            row = next(row for row in csv.DictReader(handle) if row["blocker_id"] == "Q-B04-001")
        self.assertEqual("OPEN", row["current_status"])
        self.assertEqual("E3", row["evidence_tier"])
        self.assertEqual("FAIL_CLOSED", row["canonical_use"])
        self.assertIn("VPP", row["validation_debt"])


if __name__ == "__main__":
    unittest.main()
