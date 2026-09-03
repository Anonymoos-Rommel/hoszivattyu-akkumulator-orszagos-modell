import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FACTS = ROOT / "registry" / "dso_published_node_facts.csv"


class B10P19PublicDsoFactMaterializationTests(unittest.TestCase):
    def rows(self):
        with FACTS.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_fact_registry_materializes_exact_two_bounded_publication_families(self):
        rows = self.rows()
        self.assertEqual(91, len(rows))
        counts = {}
        for row in rows:
            counts[row["operator_id"]] = counts.get(row["operator_id"], 0) + 1
        self.assertEqual({"MVM_DEMASZ": 43, "OPUS_TITASZ": 48}, counts)

    def test_all_rows_are_attributed_observed_node_identity_facts(self):
        rows = self.rows()
        self.assertTrue(all(row["evidence_status"] == "OBS" for row in rows))
        self.assertTrue(all(row["status"] == "NODE_IDENTITY_PROVEN" for row in rows))
        self.assertTrue(all(row["node_kind"] == "DSO_SUBSTATION" for row in rows))
        self.assertTrue(all(row["source_ids"] for row in rows))
        self.assertEqual(len(rows), len({row["node_id"] for row in rows}))

    def test_demasz_voltage_grain_is_preserved(self):
        rows = {row["node_id"]: row for row in self.rows()}
        self.assertIn("MVM_DEMASZ:BCSA:22KV", rows)
        self.assertIn("MVM_DEMASZ:BCSA:35KV", rows)
        self.assertIn("MVM_DEMASZ:KSZU:11KV", rows)
        self.assertIn("MVM_DEMASZ:KSZU:22KV", rows)
        self.assertIn("MVM_DEMASZ:SZEG:22KV", rows)
        self.assertIn("MVM_DEMASZ:SZEG:35KV", rows)

    def test_opus_revision_disagreement_does_not_enter_fact_registry_as_capacity(self):
        rows = {row["node_id"]: row for row in self.rows()}
        self.assertEqual("Debrecen Délkelet", rows["OPUS_TITASZ:DBDK"]["node_label"])
        self.assertNotIn("capacity", rows["OPUS_TITASZ:DBDK"])
        self.assertIn("capacity/revision disagreement", rows["OPUS_TITASZ:DBDK"]["notes"])

    def test_public_fact_registry_is_not_promoted_to_complete_node_inventory(self):
        lines = (ROOT / "registry/dso_node_inventory.csv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))
        self.assertTrue(lines[0].startswith("operator_id,network_operator,service_area_id,node_id,"))

    def test_source_pack_preserves_fact_vs_inventory_boundary(self):
        text = (ROOT / "docs/source_packs/P19_B10_PUBLIC_DSO_FACT_MATERIALIZATION.md").read_text(encoding="utf-8")
        self.assertIn("PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION", text)
        self.assertIn("ATTRIBUTED PUBLISHED NODE FACT != CANONICAL COMPLETE NODE INVENTORY", text)
        self.assertIn("91", text)
        self.assertIn("readiness 15%", text)


if __name__ == "__main__":
    unittest.main()
