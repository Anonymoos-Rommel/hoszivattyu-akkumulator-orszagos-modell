import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class B10P18PublishedNodeSetMaterializationTests(unittest.TestCase):
    def rows(self):
        with (ROOT / "registry/dso_published_node_set_materialization.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            return {row["operator_id"]: row for row in csv.DictReader(handle)}

    def test_manifest_is_bounded_to_two_consumption_node_set_publications(self):
        rows = self.rows()
        self.assertEqual({"MVM_DEMASZ", "OPUS_TITASZ"}, set(rows))
        self.assertTrue(
            all(
                row["source_semantics"] == "PUBLISHED_CONSUMPTION_HEADROOM_NODE_SET"
                for row in rows.values()
            )
        )

    def test_public_access_does_not_clear_repository_materialization(self):
        rows = self.rows()
        for row in rows.values():
            self.assertEqual(
                "REUSE_NOT_CLEARED_FOR_PUBLIC_REPOSITORY", row["reuse_status"]
            )
            self.assertEqual(
                "EXTERNAL_ONLY_NO_NODE_ROWS", row["repository_materialization_status"]
            )
            self.assertEqual(
                "Q_INVENTORY_COMPLETENESS_UNPROVEN",
                row["inventory_completeness_status"],
            )

    def test_mvm_current_source_is_consistent_but_still_not_materialized(self):
        row = self.rows()["MVM_DEMASZ"]
        self.assertEqual(
            "CURRENT_SOURCE_TEXT_RENDER_CONSISTENT_2026-09-03",
            row["source_snapshot_status"],
        )
        self.assertIn("prior written consent", row["notes"])
        self.assertIn("not evidence of exhaustive operator inventory", row["notes"])

    def test_opus_current_source_disagreement_fails_closed(self):
        row = self.rows()["OPUS_TITASZ"]
        self.assertEqual(
            "Q_CURRENT_SOURCE_RENDER_TEXT_DISAGREEMENT_2026-09-03",
            row["source_snapshot_status"],
        )
        self.assertIn("2026-07-22", row["notes"])
        self.assertIn("2026-04-01", row["notes"])
        self.assertIn("12.1 MW", row["notes"])
        self.assertIn("14.8 MW", row["notes"])

    def test_node_inventory_remains_header_only(self):
        lines = (ROOT / "registry/dso_node_inventory.csv").read_text(
            encoding="utf-8"
        ).splitlines()
        self.assertEqual(1, len(lines))
        self.assertTrue(
            lines[0].startswith(
                "operator_id,network_operator,service_area_id,node_id,node_label,node_kind,"
            )
        )

    def test_source_pack_keeps_materialization_and_completeness_separate(self):
        text = (ROOT / "docs/source_packs/P18_B10_PUBLISHED_NODE_SET_MATERIALIZATION.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "PUBLIC SOURCE ACCESS != REUSE CLEARANCE != REPOSITORY MATERIALIZATION",
            text,
        )
        self.assertIn(
            "SOURCE-PUBLISHED NODE SET != COMPLETE OPERATOR NODE INVENTORY", text
        )
        self.assertIn("B10-P3", text)
        self.assertIn("B10-P4", text)
        self.assertIn("B10-P5", text)
        self.assertIn("B10-P6", text)
        self.assertIn("readiness `15`", text)


if __name__ == "__main__":
    unittest.main()
