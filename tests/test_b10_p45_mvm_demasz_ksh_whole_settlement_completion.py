import csv
import hashlib
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
COMPLETION = ROOT / "registry/dso_service_area_membership_crosswalk_demasz_p45.csv"
OPUS_P44 = ROOT / "registry/dso_service_area_membership_crosswalk_opus_p44.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P45_B10_MVM_DEMASZ_KSH_WHOLE_SETTLEMENT_COMPLETION.md"

MVM = "SRC-B10-MVM-DEMASZ-SERVICE-AREA-2026"
KSH_2025 = "SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS"
KSH_2025_DERIVATION = "SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026"
EXPECTED_P45_PAIR_SHA256 = "bc365bafc17bb3d10067e7873fe1af725f4b20fd1d5b183f9a0cfa896fd78b92"

PARTIAL_20 = {
    "Baja", "Csongrád", "Csabacsűd", "Dabas", "Dévaványa",
    "Érsekcsanád", "Gyomaendrőd", "Kunszentmárton", "Mohács", "Péteri",
    "Solt", "Szeghalom", "Szentes", "Tápiószőlős", "Tass", "Tiszakécske",
    "Tiszasas", "Tiszaug", "Újhartyán", "Zsadány",
}


class B10P45MvmDemaszKshWholeSettlementCompletionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def historical_demasz(self):
        return [row for row in self.rows(HISTORICAL) if row["operator_id"] == "MVM_DEMASZ"]

    def completion_rows(self):
        return self.rows(COMPLETION)

    def current_demasz_whole_rows(self):
        return self.historical_demasz() + self.completion_rows()

    def test_exact_216_p45_pairs_are_frozen_by_digest(self):
        rows = self.completion_rows()
        self.assertEqual(216, len(rows))
        canonical = "\n".join(sorted(
            f'{row["ksh_settlement_code"]}|{row["settlement_name"]}' for row in rows
        ))
        self.assertEqual(
            EXPECTED_P45_PAIR_SHA256,
            hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        )
        pairs = {(row["ksh_settlement_code"], row["settlement_name"]) for row in rows}
        for pair in {
            ("26383", "Gátér"), ("03577", "Géderlak"), ("07834", "Derekegyház"),
            ("21209", "Lőkösháza"), ("16294", "Uszód"), ("10667", "Városföld"),
            ("22585", "Vasad"), ("28343", "Vaskút"), ("29531", "Vésztő"),
            ("15158", "Zsana"),
        }:
            self.assertIn(pair, pairs)

    def test_historical_40_plus_p45_216_equals_exact_256_whole_population(self):
        historical = self.historical_demasz()
        completion = self.completion_rows()
        current = historical + completion
        self.assertEqual(40, len(historical))
        self.assertEqual(216, len(completion))
        self.assertEqual(256, len(current))
        self.assertEqual(
            256,
            len({(row["ksh_settlement_code"], row["settlement_name"]) for row in current}),
        )

    def test_all_p45_rows_are_exact_der_whole_settlement_memberships(self):
        rows = self.completion_rows()
        self.assertEqual(216, len(rows))
        for row in rows:
            self.assertEqual("MVM_DEMASZ", row["operator_id"])
            self.assertEqual("MVM Démász Áramhálózati Kft.", row["network_operator"])
            self.assertEqual("MVM_DEMASZ:SERVICE_AREA", row["service_area_id"])
            self.assertEqual("WHOLE_SETTLEMENT", row["coverage_scope"])
            self.assertEqual("NONE", row["usage_location_requirement"])
            self.assertEqual("DER", row["evidence_status"])
            self.assertEqual("WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN", row["status"])
            self.assertEqual(
                {MVM, KSH_2025, KSH_2025_DERIVATION},
                set(row["source_ids"].split(";")),
            )

    def test_all_20_partial_settlements_are_accounted_but_not_promoted(self):
        current_names = {row["settlement_name"] for row in self.current_demasz_whole_rows()}
        self.assertEqual(20, len(PARTIAL_20))
        self.assertFalse(current_names & PARTIAL_20)
        text = DOC.read_text(encoding="utf-8")
        for name in PARTIAL_20:
            self.assertIn(f"`{name}`", text)
        self.assertIn("Q_PARTIAL_SETTLEMENT_USAGE_LOCATION_REQUIRED", text)

    def test_source_registry_records_whole_population_completion_but_keeps_partial_gate_open(self):
        by_operator = {row["operator_id"]: row for row in self.rows(SOURCES)}
        src = by_operator["MVM_DEMASZ"]
        self.assertEqual(MVM, src["source_id"])
        self.assertEqual("CURRENT_2026", src["currentness_status"])
        self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", src["extraction_status"])
        self.assertEqual("WHOLE_AND_PARTIAL_SETTLEMENTS", src["membership_semantics"])
        for marker in (
            "256 settlements wholly inside", "20 partial settlements", "P45", "216",
            "256 current whole-settlement memberships", "usage-location",
            "complete operator membership crosswalk",
        ):
            self.assertIn(marker, src["notes"])

    def test_ksh_codes_are_unique_across_all_materialized_membership_surfaces(self):
        rows = self.rows(HISTORICAL) + self.rows(OPUS_P44) + self.rows(COMPLETION)
        codes = [row["ksh_settlement_code"] for row in rows]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(len(code) == 5 and code.isdigit() for code in codes))

    def test_canonical_crosswalk_blockers_and_readiness_remain_fail_closed(self):
        self.assertEqual(1, len(CANONICAL.read_text(encoding="utf-8").splitlines()))
        blockers = set(current_b10_closure_assessment().blocking_refs)
        self.assertIn("NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK", blockers)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", blockers)

        by_module = {row["module_id"]: row for row in self.rows(MODULE_STATUS)}
        self.assertEqual("IN_PROGRESS", by_module["B10"]["status"])
        self.assertEqual("15", by_module["B10"]["readiness_percent"])

    def test_source_pack_preserves_completion_boundary_and_non_claims(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "256/256 current whole-settlement population",
            "216",
            "20 settlements partly inside",
            "276 settlement labels in total",
            "COMPLETE WHOLE-SETTLEMENT M1 MATERIALIZATION != COMPLETE OPERATOR MEMBERSHIP CROSSWALK",
            "20 PARTIAL SETTLEMENTS ACCOUNTED != EXACT USAGE-LOCATION RESOLUTION",
            "KSH PRIMARY SOURCE LOCATOR + REPRODUCIBLE DERIVED ROW LOCATOR != DIRECT PRIMARY ROW OBSERVATION",
            "DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE",
            "PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION",
            "evidence_status = DER",
            "readiness remains **15%**",
        ):
            self.assertIn(marker, text)

        for non_claim in (
            "complete MVM Démász operator membership crosswalk",
            "complete national KSH-to-DSO membership coverage",
            "exact programme entity-to-node mapping",
            "headroom sufficiency",
            "limiting-node status",
            "reinforcement need",
            "programme-incremental CAPEX",
        ):
            self.assertIn(non_claim, text)


if __name__ == "__main__":
    unittest.main()
