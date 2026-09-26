import csv
import unittest
from pathlib import Path

from modules.B05.s2125_multitimestamp_public_history_contract import (
    RAW_SERIES_ADMITTED,
    PublicHistoryEvidence,
    p41_boundary,
    public_graph_admissible_as_raw_series,
    qualify_public_history,
    viewer_offer_admissible_as_public_data,
)


ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p41_s2125_multitimestamp_history_acquisition.csv"
INVENTORY = ROOT / "data" / "processed" / "b05_p41_s2125_history_surface_inventory.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P41_S2125_MULTITIMESTAMP_HISTORY_ACQUISITION.md"
README = ROOT / "modules" / "B05" / "README.md"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P41S2125MultitimestampHistoryTests(unittest.TestCase):
    def test_owner_local_history_does_not_close_public_raw_residual(self):
        evidence = PublicHistoryEvidence(
            exact_s2125_system=True,
            owner_side_history_proven=True,
            public_machine_readable_rows=False,
            multiple_timestamps=True,
            bt28_present=False,
            bt16_present=True,
            compressor_present=False,
            direct_defrost_present=True,
            common_timebase=False,
            cadence_known=False,
            scaling_units_known=False,
            unknown_aggregation=True,
        )
        result = qualify_public_history(evidence)
        self.assertFalse(result.admitted)
        self.assertTrue(result.owner_history_proven)
        self.assertIn("PUBLIC_RAW_SERIES_NOT_ACQUIRED", result.status)

    def test_complete_public_raw_series_would_close_residual(self):
        evidence = PublicHistoryEvidence(
            exact_s2125_system=True,
            owner_side_history_proven=True,
            public_machine_readable_rows=True,
            multiple_timestamps=True,
            bt28_present=True,
            bt16_present=True,
            compressor_present=True,
            direct_defrost_present=True,
            common_timebase=True,
            cadence_known=True,
            scaling_units_known=True,
            unknown_aggregation=False,
        )
        result = qualify_public_history(evidence)
        self.assertTrue(result.admitted)
        self.assertEqual(result.status, RAW_SERIES_ADMITTED)

    def test_grouped_graph_and_private_viewer_offer_are_not_raw_public_data(self):
        self.assertFalse(public_graph_admissible_as_raw_series(grouped_or_visual_only=True))
        self.assertFalse(viewer_offer_admissible_as_public_data(public_link_or_export_present=False))

    def test_public_raw_non_target_rows_do_not_close_four_signal_residual(self):
        evidence = PublicHistoryEvidence(
            exact_s2125_system=True,
            owner_side_history_proven=True,
            public_machine_readable_rows=True,
            multiple_timestamps=True,
            bt28_present=False,
            bt16_present=False,
            compressor_present=False,
            direct_defrost_present=False,
            common_timebase=True,
            cadence_known=True,
            scaling_units_known=True,
            unknown_aggregation=False,
        )
        result = qualify_public_history(evidence)
        self.assertFalse(result.admitted)
        self.assertEqual(
            result.status,
            "PUBLIC_RAW_S2125_ROWS_ACQUIRED_TARGET_FOUR_SIGNAL_SERIES_INCOMPLETE",
        )
        self.assertEqual(
            result.residual_gaps,
            ("Q_S2125_MULTI_TIMESTAMP_BT28_BT16_COMPRESSOR_DEFROST_SERIES_REQUIRED",),
        )

    def test_inventory_has_nine_exact_field_surfaces(self):
        inventory = rows(INVENTORY)
        self.assertEqual(len(inventory), 9)
        ids = {row["system_id"] for row in inventory}
        self.assertEqual(
            ids,
            {
                "SVENPAUSH",
                "BORISVKR_MARTIUS",
                "HAVISOFT",
                "WPNUTZER",
                "MLINZNER",
                "JKJAER_SILKEBORG",
                "HANS1966",
                "LASSECB",
                "SCHINGELDI",
            },
        )
        self.assertTrue(all(row["public_raw_four_signal_rows_acquired"] == "NO" for row in inventory))
        schingeldi = next(row for row in inventory if row["system_id"] == "SCHINGELDI")
        self.assertEqual(
            schingeldi["public_surface_status"],
            "PUBLIC_RAW_OTHER_CHANNEL_TIMESERIES",
        )
        havisoft = next(row for row in inventory if row["system_id"] == "HAVISOFT")
        self.assertEqual(havisoft["bt28_history"], "YES_SAME_SYSTEM_HISTORY")
        self.assertEqual(havisoft["bt16_history"], "YES_SAME_SYSTEM_HISTORY")
        self.assertEqual(havisoft["compressor_history"], "YES_SAME_SYSTEM_HISTORY")
        self.assertEqual(havisoft["direct_defrost_history"], "YES_SAME_SYSTEM_HISTORY")
        self.assertEqual(
            havisoft["public_surface_status"],
            "OWNER_COMPLETE_FOUR_SIGNAL_HISTORY_NOT_EXPORTED",
        )
        silkeborg = next(row for row in inventory if row["system_id"] == "JKJAER_SILKEBORG")
        self.assertIn("LIVE_RECHECK_UNCHANGED", silkeborg["public_surface_status"])

    def test_registry_preserves_exact_physical_residual(self):
        reg = {row["claim"]: row for row in rows(REG)}
        residual = reg["S2125_MULTI_TIMESTAMP_BT28_BT16_COMPRESSOR_DEFROST_SERIES_REQUIRED"]
        self.assertEqual(residual["status"], "OPEN")
        self.assertEqual(residual["evidence_status"], "Q")
        self.assertEqual(
            residual["residual_gap"],
            "S2125_MULTI_TIMESTAMP_BT28_BT16_COMPRESSOR_DEFROST_SERIES_REQUIRED",
        )

    def test_bounded_audit_is_not_global_absence(self):
        reg = {row["claim"]: row for row in rows(REG)}
        row = reg["AUDITED_PUBLIC_S2125_HISTORY_SURFACES_NO_RAW_FOUR_SIGNAL_EXPORT_FOUND"]
        self.assertEqual(row["status"], "RESOLVED_BOUNDED")
        self.assertIn("not global absence", row["notes"].lower())

    def test_complete_owner_history_is_not_public_raw_closure(self):
        reg = {row["claim"]: row for row in rows(REG)}
        row = reg["OWNER_SIDE_COMPLETE_FOUR_SIGNAL_HISTORY_EXISTS"]
        self.assertEqual(row["status"], "RESOLVED_BOUNDED")
        self.assertEqual(row["evidence_status"], "OBS")
        self.assertEqual(
            row["residual_gap"],
            "S2125_MULTI_TIMESTAMP_BT28_BT16_COMPRESSOR_DEFROST_SERIES_REQUIRED",
        )

    def test_bounded_public_search_exhaustion_is_not_global_absence(self):
        reg = {row["claim"]: row for row in rows(REG)}
        row = reg["BOUNDED_PUBLIC_TARGET_EXPORT_SEARCH_EXHAUSTED"]
        self.assertEqual(row["status"], "RESOLVED_BOUNDED")
        self.assertIn("not global source absence", row["notes"].lower())
        self.assertIn("targeted owner raw export", row["notes"].lower())

    def test_question_and_readiness_do_not_move(self):
        q = {row["question_id"]: row for row in rows(QUESTIONS)}["Q-B05-003"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn(
            "S2125_MULTI_TIMESTAMP_BT28_BT16_COMPRESSOR_DEFROST_SERIES_REQUIRED",
            q["notes"],
        )
        r = {row["component_id"]: row for row in rows(READINESS)}["DEFROST"]
        self.assertEqual(r["readiness_percent"], "20")
        self.assertIn("B05 overall remains 64%", r["notes"])

    def test_new_sources_are_registered(self):
        sources = {row["source_id"]: row for row in rows(SOURCES)}
        for source_id in (
            "SRC-B05-P41-SVENPAUSH-S2125-INFLUX-HISTORY-2025",
            "SRC-B05-P41-WPNUTZER-S2125-MYUPLINK-CSV-2024",
            "SRC-B05-P41-OEM-S2125-READONLY-VIEWER-OFFER-2025",
            "SRC-B05-P41-HANS1966-S2125-INFLUX-HISTORY-2023",
            "SRC-B05-P41-LASSECB-S2125-HA-DEFROST-HISTORY-2025",
            "SRC-B05-P41-SCHINGELDI-S2125-RAW-MULTITIMESTAMP-2024",
        ):
            self.assertIn(source_id, sources)

    def test_no_private_access_or_raw_third_party_history_is_committed(self):
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("neither requests nor attempts non-public access", text)
        self.assertNotIn("viewer_token", text.lower())
        self.assertNotIn("password", text.lower())
        self.assertFalse((ROOT / "data" / "raw" / "s2125_multitimestamp_history.csv").exists())

    def test_readme_and_boundary_are_pinned(self):
        self.assertIn("B05-P41", README.read_text(encoding="utf-8"))
        boundary = p41_boundary()
        self.assertIn(
            "EXACT_S2125_MULTI_TIMESTAMP_HISTORY_EXISTS != PUBLIC_RAW_FOUR_SIGNAL_SERIES_ACQUIRED",
            boundary,
        )
        self.assertIn(
            "PUBLIC_RAW_OTHER_CHANNEL_S2125_TIMESERIES != PUBLIC_RAW_TARGET_FOUR_SIGNAL_SERIES",
            boundary,
        )
        self.assertIn(
            "OWNER_SIDE_COMPLETE_FOUR_SIGNAL_HISTORY != PUBLIC_RAW_FOUR_SIGNAL_SERIES_ACQUIRED",
            boundary,
        )
        self.assertIn(
            "BOUNDED_PUBLIC_TARGET_EXPORT_SEARCH_EXHAUSTED != GLOBAL_SOURCE_ABSENCE",
            boundary,
        )
        self.assertIn(
            "BOUNDED_PUBLIC_AUDIT_NO_EXPORT_FOUND != GLOBAL_SOURCE_ABSENCE",
            boundary,
        )


if __name__ == "__main__":
    unittest.main()
