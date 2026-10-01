import copy
import hashlib
import json
import tempfile
import unittest
from decimal import Decimal, localcontext
from pathlib import Path

from modules.B10.cost_reference import (
    BILL_ITEM, CONNECTION, DATA_PATH, EXACT_REFERENCE_ONLY, MANIFEST_PATH,
    PRICE_KINDS, REJECTED_PRICE_KINDS, SUBSTATION, SUPPLY, UNKNOWN_FIELDS,
    CostReferenceError, load_reference_catalog, validate_payload,
)
from modules.B10.national_network_inference_layer import (
    Q_NATIONAL_NETWORK_INFERENCE, assess_national_network_inference,
)
from tools.verify_b10_cost_reference import extract_amended_item, extract_winning_awards, verify_external_sources


class B10CostReferenceTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_reference_catalog()
        self.data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        self.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.rows = list(self.catalog.observations.values())

    def read(self, row, fact="lot_amount", **overrides):
        args = dict(unit=row["facts"][fact]["unit"], price_basis=row["price_basis"])
        args.update(overrides)
        return self.catalog.read(row["observation_id"], fact, **args)

    def derive(self, row, calculation, unit, **overrides):
        args = dict(unit=unit, price_basis=row["price_basis"])
        args.update(overrides)
        return self.catalog.derive(row["observation_id"], calculation, **args)

    def test_seven_records_four_admitted_and_three_rejected_price_kinds(self):
        self.assertEqual(len(self.rows), 7)
        self.assertEqual({r["observation_kind"] for r in self.rows}, {SUPPLY, CONNECTION, SUBSTATION, BILL_ITEM})
        self.assertEqual(len(PRICE_KINDS), 7)
        self.assertEqual(set(self.manifest["excluded_price_kinds"]), REJECTED_PRICE_KINDS)

    def test_six_awarded_amounts_remain_source_native(self):
        expected = ["1119836.62", "2231873.24", "59982087", "121995641", "303985846", "1394532243"]
        for row, amount in zip(self.rows[:6], expected):
            value = self.read(row)
            self.assertEqual(value.value, Decimal(amount))
            self.assertEqual(value.truth_status, "OBS")
            self.assertEqual(value.metadata["permitted_use"], EXACT_REFERENCE_ONLY)
            self.assertEqual(value.source["source_id"], row["source_id"])
            self.assertIsNone(value.calculation)

    def test_within_lot_supply_arithmetic_exact_and_labelled(self):
        for row, unit, per_mva in zip(self.rows[:2], ["1119836.62", "1115936.62"], ["27995.9155", "27898.4155"]):
            result = self.derive(row, "SUPPLY_PER_TRANSFORMER", "EUR/transformer")
            self.assertEqual(result.value, Decimal(unit))
            self.assertEqual(result.truth_status, "DER")
            self.assertEqual(result.input_facts, ("lot_amount", "asset_count"))
            result = self.derive(row, "SUPPLY_PER_NAMEPLATE_MVA", "EUR/nameplate_MVA")
            self.assertEqual(result.value, Decimal(per_mva))
            self.assertIn("nameplate_per_asset", result.input_facts)

    def test_rail_rate_is_literal_allocation_and_line_product_is_derived(self):
        row = self.rows[6]
        self.assertEqual(self.read(row, "unit_price").value, Decimal("32640"))
        self.assertEqual(self.read(row, "quantity").value, Decimal("700"))
        self.assertEqual(self.read(row, "line_total").truth_status, "OBS")
        result = self.derive(row, "BILL_LINE_RECONCILIATION", "HUF")
        self.assertEqual(result.value, Decimal("22848000"))
        self.assertEqual(result.truth_status, "DER")
        self.assertIn("VINTAGE_UNKNOWN", row["price_basis"])
        self.assertEqual(row["contract_date"], "2022-11-04")

    def test_caller_decimal_precision_does_not_change_intake_or_derivation(self):
        with localcontext() as context:
            context.prec = 4
            catalog = load_reference_catalog()
            row = self.rows[1]
            result = catalog.derive(row["observation_id"], "SUPPLY_PER_NAMEPLATE_MVA",
                                    unit="EUR/nameplate_MVA", price_basis=row["price_basis"])
            self.assertEqual(result.value, Decimal("27898.4155"))
            row = self.rows[6]
            result = catalog.derive(row["observation_id"], "BILL_LINE_RECONCILIATION",
                                    unit="HUF", price_basis=row["price_basis"])
            self.assertEqual(result.value, Decimal("22848000"))

    def test_source_totals_are_auditable_without_portfolio_aggregation(self):
        self.assertEqual(sum(self.read(r).value for r in self.rows[:2]), Decimal("3351709.86"))
        self.assertEqual(sum(self.read(r).value for r in self.rows[2:5]), Decimal("485963574"))
        self.assertFalse(hasattr(self.catalog, "aggregate_national_cost"))

    def test_four_procurement_clusters_are_not_seven_independent_samples(self):
        clusters = [r["correlation_cluster_id"] for r in self.rows]
        self.assertEqual(len(set(clusters)), 4)
        self.assertEqual(clusters[0], clusters[1])
        self.assertEqual(len(set(clusters[2:5])), 1)
        self.assertTrue(all(r["unknowns"]["cohort_weight"] is None for r in self.rows))

    def test_scope_geography_and_source_native_overhead_are_retained(self):
        bugac = self.rows[4]
        self.assertEqual(bugac["source_nuts_label"], "Csongrád-Csanád (HU333)")
        self.assertTrue(bugac["geography_warning"])
        overhead = self.read(bugac, "overhead_source_quantity")
        self.assertEqual(overhead.value, Decimal("4.66"))
        self.assertEqual(overhead.unit, "km_source_declared_1x3_conductor_scope")
        self.assertIn("WAREHOUSE", self.rows[0]["geography_semantics"])

    def test_planned_duration_is_not_actual_completion(self):
        self.assertEqual(self.read(self.rows[0], "planned_duration").unit, "month_planned")
        self.assertEqual(self.read(self.rows[2], "planned_duration").unit, "calendar_day_planned")
        self.assertEqual(self.read(self.rows[5], "planned_duration").value, Decimal("850"))
        self.assertEqual(self.read(self.rows[5], "notice_duration_display").value, Decimal("29"))
        for row in self.rows:
            self.assertIsNone(row["unknowns"]["actual_completion_date"])

    def test_unknowns_and_reserves_are_not_zero_filled_or_added(self):
        for row in self.rows:
            self.assertEqual(set(row["unknowns"]), UNKNOWN_FIELDS)
            self.assertTrue(all(v is None for v in row["unknowns"].values()))
        with self.assertRaises(CostReferenceError):
            self.derive(self.rows[2], "AWARD_PLUS_RESERVE", "HUF")

    def test_rejects_all_broader_claims_for_every_record(self):
        for row in self.rows:
            fact = "unit_price" if row["observation_kind"] == BILL_ITEM else "lot_amount"
            for claim in ("NATIONAL_COST", "INSTALLED_TOTAL", "PROGRAMME_INCREMENTAL_CAPEX",
                          "ACTUAL_PAID", "ACTUAL_TIMING", "HOUSEHOLD_CHARGE", "ANNUAL_CASHFLOW"):
                with self.subTest(record=row["observation_id"], claim=claim), self.assertRaises(CostReferenceError):
                    self.read(row, fact, claim=claim)

    def test_rejects_fx_inflation_vat_and_nameplate_to_usable_mw(self):
        for kwargs in ({"unit": "HUF"}, {"price_basis": "2026_HUF"}, {"unit": "EUR_gross"}):
            with self.assertRaises(CostReferenceError):
                self.read(self.rows[0], **kwargs)
        with self.assertRaises(CostReferenceError):
            self.derive(self.rows[0], "SUPPLY_PER_NAMEPLATE_MVA", "EUR/usable_MW")
        with self.assertRaises(CostReferenceError):
            self.read(self.rows[4], "overhead_source_quantity", unit="km_route")

    def test_rejects_generic_package_ratios_and_cross_kind_arithmetic(self):
        for row in self.rows[2:]:
            for calculation in ("SUPPLY_PER_TRANSFORMER", "SUPPLY_PER_NAMEPLATE_MVA",
                                "PACKAGE_PER_MW", "PACKAGE_PER_M", "GENERIC_CABLE_RATE"):
                with self.assertRaises(CostReferenceError):
                    self.derive(row, calculation, "HUF/MW")
        with self.assertRaises(CostReferenceError):
            self.derive(self.rows[0], "BILL_LINE_RECONCILIATION", "HUF")

    def test_rejects_unknown_ids_and_missing_facts(self):
        with self.assertRaises(CostReferenceError):
            self.catalog.read("unknown", "lot_amount", unit="HUF", price_basis="unknown")
        with self.assertRaises(CostReferenceError):
            self.catalog.read(self.rows[0]["observation_id"], "normalized_2026_huf",
                              unit="HUF", price_basis=self.rows[0]["price_basis"])

    def test_loaded_values_and_metadata_are_immutable(self):
        result = self.read(self.rows[0])
        with self.assertRaises(TypeError):
            result.metadata["facts"]["lot_amount"]["value"] = "1"
        with self.assertRaises(TypeError):
            self.catalog.observations["new"] = {}

    def test_semantic_mutations_rejected_even_with_recomputed_record_digest(self):
        mutations = [
            lambda r: r.update(currency="HUF"),
            lambda r: r.update(price_basis="2026_HUF"),
            lambda r: r.update(observation_kind="LIFECYCLE_BID_SCORE"),
            lambda r: r.update(correlation_cluster_id="INDEPENDENT_LOT"),
            lambda r: r.update(national_input_status="E2"),
            lambda r: r["unknowns"].update(programme_incremental_capex_huf=0),
            lambda r: r["unknowns"].update(reserve_included=False),
            lambda r: r["facts"]["lot_amount"].update(unit="HUF"),
            lambda r: r["facts"]["lot_amount"].update(truth_status="DER"),
            lambda r: r["facts"].update(normalized_2026_huf={"value": "1", "unit": "HUF", "truth_status": "DER"}),
        ]
        for mutate in mutations:
            data, manifest = copy.deepcopy(self.data), copy.deepcopy(self.manifest)
            row = data["observations"][0]
            mutate(row)
            manifest["record_bindings"][0]["record_sha256"] = hashlib.sha256(json.dumps(
                row, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            with self.assertRaises(CostReferenceError):
                validate_payload(data, manifest)

    def test_bad_numeric_representations_and_nonpositive_values_rejected(self):
        for value in (True, 1.5, "NaN", "Infinity", "-1", "0", "1e3", None):
            data = copy.deepcopy(self.data)
            data["observations"][0]["facts"]["lot_amount"]["value"] = value
            with self.subTest(value=value), self.assertRaises(CostReferenceError):
                validate_payload(data, self.manifest)

    def test_missing_duplicate_rows_sources_and_provenance_rejected(self):
        for target in ("rows", "sources", "binding", "scope", "locator", "raw", "sha", "rendition"):
            data, manifest = copy.deepcopy(self.data), copy.deepcopy(self.manifest)
            if target == "rows": data["observations"][1] = data["observations"][0]
            if target == "sources": manifest["sources"][1] = manifest["sources"][0]
            if target == "binding": manifest["record_bindings"].pop()
            if target == "scope": data["observations"][0]["technical_scope"] = ""
            if target == "locator": data["observations"][0]["source_locator"] = ""
            if target == "raw": manifest["sources"][0]["repo_snapshot_path"] = "evidence/file.pdf"
            if target == "sha": manifest["sources"][0]["sha256"] = ""
            if target == "rendition": manifest["sources"][0]["original_url"] += "/xml"
            with self.subTest(target=target), self.assertRaises(CostReferenceError):
                validate_payload(data, manifest)

    def test_exact_file_digest_and_record_digest_are_both_required(self):
        self.data["observations"][0]["facts"]["lot_amount"]["value"] = "99"
        with self.assertRaises(CostReferenceError):
            validate_payload(self.data, self.manifest)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "changed.json"
            path.write_text(json.dumps(self.data), encoding="utf-8")
            with self.assertRaises(CostReferenceError):
                load_reference_catalog(path, MANIFEST_PATH)

    def test_winner_parser_ignores_lower_losing_bid(self):
        text = """6.1. Eredmény – részazonosító: LOT-0003
        6.1.2. Információk a nyertesekről Ajánlat értéke: 303 985 846,00 HUF
        A szerződés megkötésének időpontja: 10/06/2026
        6.1.3. Nem nyertes ajánlattevők Ajánlat értéke: 232 963 154,00 HUF"""
        self.assertEqual(extract_winning_awards(text)["LOT-0003"]["value"], Decimal("303985846"))
        with self.assertRaises(CostReferenceError):
            extract_winning_awards(text + text)

    def test_bill_parser_excludes_previous_item_and_fails_on_changed_columns(self):
        text = ("122 236 Kábel építés 10 kV hálózaton m 80 101 916 8 153 280 "
                "Változást követő tételek 122 236 Kábel építés 10 kV hálózaton m "
                "700 32 640 22 848 000 122 237")
        self.assertEqual(extract_amended_item(text), (Decimal("700"), Decimal("32640"), Decimal("22848000")))
        with self.assertRaises(CostReferenceError):
            extract_amended_item(text.replace("32 640", "32 641"))

    def test_external_verifier_requires_all_source_ids_and_pinned_bytes(self):
        with self.assertRaises(CostReferenceError):
            verify_external_sources(self.catalog, {})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wrong.pdf"
            path.write_bytes(b"not the reviewed source")
            with self.assertRaises(CostReferenceError):
                verify_external_sources(self.catalog, {sid: path for sid in self.catalog.sources})

    def test_p67_remains_q_without_population_and_attribution_evidence(self):
        result = assess_national_network_inference(
            independent_dso_strata=2, programme_demand_distribution=False,
            representative_headroom_cohort=False, reinforcement_project_cohort=False,
            programme_incremental_capex_attribution=False, delivery_timing_distribution=False,
            managed_peak_survivability_model=False, population_calibration=False, uncertainty_explicit=False,
        )
        self.assertEqual(result.status, Q_NATIONAL_NETWORK_INFERENCE)
        self.assertIn("REPRESENTATIVE_REINFORCEMENT_COHORT_AND_INCREMENTAL_CAPEX_DISTRIBUTION_REQUIRED", result.blockers)


if __name__ == "__main__":
    unittest.main()
