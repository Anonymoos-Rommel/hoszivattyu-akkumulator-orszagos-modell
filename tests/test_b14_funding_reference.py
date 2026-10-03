import copy
import csv
import hashlib
import json
import tempfile
import unittest
from decimal import Decimal, localcontext
from pathlib import Path

from modules.B14.funding_reference import (
    AS_OF, CALL_SOURCES, CAPS_PATH, DATA_PATH, DATED_INTAKE_STATUS,
    DATED_RULE_REFERENCE, GROSS_POLICY_UNIT_CAP, MANIFEST_PATH,
    PROGRAMME_417, PROGRAMME_418, SCOPES, UNKNOWN_FIELDS,
    FundingReferenceError, _digest, load_funding_reference, validate_snapshot,
)
from tools.verify_b14_funding_reference import extract_call_finance, verify_external_sources


class B14FundingReferenceTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_funding_reference()
        self.data = json.loads(DATA_PATH.read_text())
        self.manifest = json.loads(MANIFEST_PATH.read_text())
        with CAPS_PATH.open(newline="") as stream:
            self.caps = list(csv.DictReader(stream))

    def read(self, programme=PROGRAMME_417, **changes):
        args = dict(scope=SCOPES[programme], as_of=AS_OF, claim=DATED_RULE_REFERENCE)
        args.update(changes)
        return self.catalog.read_programme(programme, **args)

    def fact(self, name, programme=PROGRAMME_417, unit="HUF", **changes):
        args = dict(scope=SCOPES[programme], as_of=AS_OF, unit=unit, claim=DATED_RULE_REFERENCE)
        args.update(changes)
        return self.catalog.read_fact(programme, name, **args)

    def cap(self, cap_id="KEHOP417-CAP-33", **changes):
        args = dict(programme_id=PROGRAMME_417, scope=SCOPES[PROGRAMME_417], as_of=AS_OF,
                    unit="HUF/set", vat_basis="GROSS", claim=GROSS_POLICY_UNIT_CAP)
        args.update(changes)
        return self.catalog.read_cap(cap_id, **args)

    def rebind_programmes(self, data, manifest):
        manifest["programme_bindings"] = [dict(programme_id=p["programme_id"], sha256=_digest(p))
                                            for p in data["programmes"]]

    def test_curated_bytes_follow_repository_lf_contract(self):
        # .gitattributes normalizes these public files to LF. Hashes must bind
        # the same bytes in the working tree and a clean Git checkout.
        for path in (CAPS_PATH, DATA_PATH, MANIFEST_PATH):
            self.assertNotIn(b"\r", path.read_bytes(), str(path))
        self.assertEqual(hashlib.sha256(CAPS_PATH.read_bytes()).hexdigest(),
                         self.manifest["caps_sha256"])

    def test_reference_cardinality_and_source_family(self):
        self.assertEqual(len(self.catalog.programmes), 2)
        self.assertEqual(len(self.catalog.caps), 39)
        self.assertEqual(len(self.catalog.sources), 11)
        self.assertEqual({s["evidence_family"] for s in self.catalog.sources.values()},
                         {"MFB_KEHOP_HOUSEHOLD_PROGRAMME"})

    def test_original_envelopes_are_policy_amounts_not_current_headroom(self):
        self.assertEqual(self.fact("original_envelope").value, Decimal("66820000000"))
        self.assertEqual(self.fact("original_envelope", PROGRAMME_418).value, Decimal("6190000000"))
        self.assertEqual(self.fact("original_envelope").truth_status, "POL")
        for pid in SCOPES:
            row = self.read(pid)
            self.assertEqual(set(row["unknowns"]), UNKNOWN_FIELDS)
            for unknown in row["unknowns"].values():
                self.assertIsNone(unknown["value"])
                self.assertEqual(unknown["truth_status"], "Q")

    def test_source_native_finance_and_own_source_denominators(self):
        for pid in SCOPES:
            self.assertEqual(self.fact("finance_min", pid).value, Decimal("2500000"))
            self.assertEqual(self.fact("finance_max", pid).value, Decimal("10000000"))
            grant = self.fact("grant_share", pid, "ratio")
            own = self.fact("own_source_min_share", pid, "ratio")
            self.assertEqual(grant.value, Decimal("0.5"))
            self.assertEqual(grant.metadata["denominator"], "FINANCING_AMOUNT")
            self.assertEqual(own.value, Decimal("0.05"))
            self.assertEqual(own.metadata["denominator"], "ELIGIBLE_PROJECT_COST")
            self.assertEqual(self.fact("own_source_example_at_max_finance", pid).value, Decimal("526316"))
            self.assertIsNone(self.read(pid)["eligible_total_hard_cap"]["value"])

    def test_maturity_and_extensions_are_qualified_source_rules(self):
        for pid in SCOPES:
            self.assertEqual(self.fact("loan_maturity_max", pid, "year").value, Decimal("15"))
            labels = self.read(pid)["financing_constraint_labels"]
            self.assertIn("LOAN_MATURITY_INCLUDES_AVAILABILITY_AND_GRACE", labels)
            self.assertIn("EXECUTION_EXTENSION_ONCE_JUSTIFIED_NOT_AUTOMATIC", labels)
            self.assertIn("AVAILABILITY_EXTENSION_JUSTIFIED_NOT_AUTOMATIC", labels)
            self.assertEqual(self.fact("execution_max", pid, "month").value, Decimal("24"))
            self.assertEqual(self.fact("execution_extension_max", pid, "month").value, Decimal("6"))

    def test_intakes_are_suspended_at_exact_snapshot_only(self):
        for pid in SCOPES:
            intake = self.catalog.read_intake(pid, scope=SCOPES[pid], as_of=AS_OF,
                                              claim=DATED_INTAKE_STATUS)
            self.assertEqual(intake["status"], "SUSPENDED_FOR_ENVELOPE_EXHAUSTION")
            self.assertEqual(intake["truth_status"], "OBS")
            self.assertEqual(self.read(pid)["dates"]["nominal_submission_end"]["value"], "2027-03-30")
            self.assertIn("TERMS_NOMINAL_DEADLINE_SUBORDINATE_TO_CURRENT_SUSPENSION",
                          self.read(pid)["financing_constraint_labels"])

    def test_branch_closing_is_date_grain_without_fabricated_time(self):
        for pid in SCOPES:
            for window in self.read(pid)["intake"]["windows"]:
                self.assertEqual(window["precision"], "day")
                self.assertEqual(window["cutoff"], "BRANCH_CLOSING_TIME_NOT_OBSERVED_AS_CLOCK_TIME")
                self.assertNotIn("T", window["last_submission_day"])
        self.assertEqual([w["last_submission_day"] for w in self.read()["intake"]["windows"]],
                         ["2026-04-17", "2026-04-23"])

    def test_september_unknowns_do_not_mean_zero_refusal_or_no_successor(self):
        note = self.catalog.operational_observations
        self.assertEqual(note["document_revision"], "2026-09")
        self.assertEqual(note["date_precision"], "month")
        self.assertEqual(note["claims"]["envelope_expansion_information"], "DATED_UNKNOWN_NOT_ZERO_OR_REFUSAL")
        self.assertEqual(note["claims"]["successor_programme_information"],
                         "DATED_UNKNOWN_NOT_ABSENCE_OF_FUTURE_PROGRAMME")
        self.assertEqual(note["claims"]["pre_suspension_application"],
                         "APPROVAL_WAITLIST_OR_REJECTION_DEPENDING_ON_RULES_AND_RESOURCES")

    def test_caps_keep_material_labour_gross_units_and_derived_sum(self):
        cap = self.cap()
        self.assertEqual((cap["material_cap"], cap["labour_cap"], cap["combined_cap"]),
                         ("6438980", "2112867", "8551847"))
        self.assertEqual(cap["truth_status"], "POL")
        self.assertEqual(cap["combined_truth_status"], "DER")
        self.assertEqual(cap["meaning"], "MAX_ELIGIBLE_UNIT_COST_NOT_MARKET_PRICE")
        self.assertEqual(cap["source_id"], CALL_SOURCES[PROGRAMME_417])
        self.assertEqual(self.cap("KEHOP417-CAP-34", unit="HUF/m2")["combined_cap"], "37084")

    def test_nested_cost_caps_are_not_additive_entitlements(self):
        row = self.read()
        self.assertEqual(self.fact("preparation_total_cap").value, Decimal("450000"))
        self.assertEqual(self.fact("other_costs_total_cap").value, Decimal("300000"))
        self.assertIn("CAPS_ARE_NOT_ADDITIVE_ENTITLEMENTS", row["cost_constraint_labels"])
        self.assertIn("PREPARATION_INCLUDES_OPENING_HET_PLAN_AND_ADVICE", row["cost_constraint_labels"])
        self.assertIn("OTHER_COSTS_INCLUDE_CLOSING_HET", row["cost_constraint_labels"])
        self.assertIn("MAX_ONE_HEM_GENERATION_AGREEMENT", row["cumulation_labels"])

    def test_record_level_and_nonhousehold_boundaries_remain(self):
        for pid in SCOPES:
            row = self.read(pid)
            self.assertTrue(row["gates"]["applicant"].startswith("RECORD_LEVEL"))
            self.assertTrue(row["gates"]["property"].startswith("RECORD_LEVEL"))
            self.assertTrue(row["gates"]["technical"].startswith("RECORD_LEVEL"))
            self.assertEqual(row["gates"]["national_programme"], "NO_ALLOCATION_ESTABLISHED")
            self.assertEqual(row["gates"]["university_or_pilot"], "NOT_ESTABLISHED_BY_HOUSEHOLD_CALL")
        self.assertFalse(hasattr(self.catalog, "calculate_financing"))
        self.assertFalse(hasattr(self.catalog, "approve_household"))

    def test_existing_source_ids_and_mirror_lineage_are_preserved(self):
        for sid in CALL_SOURCES.values():
            source = self.catalog.sources[sid]
            self.assertTrue(source["original_url"].startswith("https://www.palyazat.gov.hu/api/download/"))
            self.assertTrue(source["mirror_byte_identity"])
            self.assertIsNone(source["repo_snapshot_path"])
            self.assertEqual(source["reuse_status"], "EXTERNAL_ONLY")
        source = self.catalog.sources[CALL_SOURCES[PROGRAMME_417]]
        self.assertIn("SRC-B02-HU-KEHOP-417-MAX-COST-2025", source["same_document_alias_source_ids"])

    def test_every_read_requires_explicit_scope_asof_and_claim(self):
        with self.assertRaises(TypeError): self.catalog.read_programme(PROGRAMME_417)
        with self.assertRaises(TypeError): self.catalog.read_intake(PROGRAMME_417)
        with self.assertRaises(TypeError): self.catalog.read_cap("KEHOP417-CAP-01")
        with self.assertRaises(TypeError): self.catalog.read_fact(PROGRAMME_417, "finance_max")

    def test_rejects_current_future_historical_and_datetime_extrapolation(self):
        for as_of in ("current", "today", "2026-10-02", "2025-10-15", "2026-10-01T00:00:00Z", None):
            with self.subTest(as_of=as_of), self.assertRaises(FundingReferenceError): self.read(as_of=as_of)
        with self.assertRaises(FundingReferenceError): self.read(scope="ALL_HUNGARIAN_DWELLINGS")
        with self.assertRaises(FundingReferenceError):
            self.catalog.read_programme("UNKNOWN", scope=SCOPES[PROGRAMME_417],
                                        as_of=AS_OF, claim=DATED_RULE_REFERENCE)

    def test_rejects_availability_award_cost_and_policy_claims(self):
        for claim in ("CURRENT_AVAILABILITY", "AVAILABLE_GRANT", "CONFIRMED_AWARD", "HOUSEHOLD_ELIGIBLE",
                      "EXPECTED_CAPEX", "NATIONAL_ALLOCATION", "UNIVERSITY_FUNDING", "POLICY_DEFAULT"):
            with self.subTest(claim=claim), self.assertRaises(FundingReferenceError): self.read(claim=claim)
        with self.assertRaises(FundingReferenceError):
            self.catalog.read_intake(PROGRAMME_417, scope=SCOPES[PROGRAMME_417], as_of=AS_OF,
                                     claim="NEW_APPLICATION_AVAILABLE")

    def test_rejects_zero_filled_or_numeric_reads_of_unknown_funding(self):
        for name in UNKNOWN_FIELDS:
            with self.subTest(name=name), self.assertRaises(FundingReferenceError): self.fact(name)
        for value in (0, "0", "66820000000"):
            data, manifest = copy.deepcopy(self.data), copy.deepcopy(self.manifest)
            data["programmes"][0]["unknowns"]["remaining_funds"]["value"] = value
            self.rebind_programmes(data, manifest)
            with self.assertRaises(FundingReferenceError): validate_snapshot(data, self.caps, manifest)

    def test_rejects_unit_currency_net_and_budapest_cap_transfer(self):
        for changes in ({"unit":"EUR"}, {"unit":"HUF/MW"}, {"vat_basis":"NET"},
                        {"claim":"MARKET_PRICE"}, {"claim":"EXPECTED_CAPEX"},
                        {"programme_id":PROGRAMME_418, "scope":SCOPES[PROGRAMME_418]}):
            with self.subTest(changes=changes), self.assertRaises(FundingReferenceError): self.cap(**changes)
        with self.assertRaises(FundingReferenceError): self.fact("finance_max", unit="EUR")
        with self.assertRaises(FundingReferenceError): self.fact("grant_share", unit="share_of_project_cost")
        with self.assertRaises(FundingReferenceError): self.cap("missing")

    def test_loaded_snapshot_and_metadata_are_deeply_immutable(self):
        with self.assertRaises(TypeError): self.read()["facts"]["finance_max"]["value"] = "1"
        with self.assertRaises(TypeError): self.catalog.caps["new"] = {}
        with self.assertRaises(TypeError): self.catalog.operational_observations["claims"]["waitlist"] = "FUNDED"

    def test_semantic_mutations_rejected_even_after_programme_rebinding(self):
        mutations = [
            lambda r:r.update(scope="NATIONAL"),
            lambda r:r["facts"]["grant_share"].update(denominator="PROJECT_COST"),
            lambda r:r["facts"]["own_source_min_share"].update(denominator="FINANCING_AMOUNT"),
            lambda r:r["eligible_total_hard_cap"].update(value="10500000"),
            lambda r:r["intake"].update(status="OPEN"),
            lambda r:r["intake"]["windows"][0].update(last_submission_time="17:00"),
            lambda r:r["gates"].update(applicant="APPROVED"),
            lambda r:r.update(cost_cap_source_status="NATIONAL_PRICE_INPUT"),
            lambda r:r["financing_constraint_labels"].remove("EXECUTION_EXTENSION_ONCE_JUSTIFIED_NOT_AUTOMATIC"),
            lambda r:r["cumulation_labels"].remove("MAX_ONE_HEM_GENERATION_AGREEMENT"),
        ]
        for mutate in mutations:
            data, manifest = copy.deepcopy(self.data), copy.deepcopy(self.manifest)
            mutate(data["programmes"][0]); self.rebind_programmes(data, manifest)
            with self.assertRaises(FundingReferenceError): validate_snapshot(data, self.caps, manifest)

    def test_operational_unknowns_and_month_grain_are_fail_closed(self):
        for mutate in (lambda x:x.update(date_precision="day"),
                       lambda x:x["claims"].update(successor_programme_information="NONE_EXISTS"),
                       lambda x:x["claims"].update(envelope_expansion_information="ZERO")):
            data, manifest = copy.deepcopy(self.data), copy.deepcopy(self.manifest)
            mutate(data["operational_observations"])
            manifest["operational_observations_sha256"] = _digest(data["operational_observations"])
            with self.assertRaises(FundingReferenceError): validate_snapshot(data, self.caps, manifest)

    def test_malformed_numbers_cap_math_identity_and_duplicates_rejected(self):
        for value in (True, 1.5, "NaN", "Infinity", "1e5", "-1", None):
            data = copy.deepcopy(self.data);data["programmes"][0]["facts"]["finance_max"]["value"] = value
            with self.subTest(value=value), self.assertRaises(FundingReferenceError):
                validate_snapshot(data, self.caps, self.manifest)
        for mutation in (lambda rows:rows.pop(),lambda rows:rows[0].update(combined_cap="1"),
                         lambda rows:rows[0].update(cap_id=rows[1]["cap_id"]),
                         lambda rows:rows[0].update(meaning="MARKET_PRICE")):
            caps=copy.deepcopy(self.caps);mutation(caps)
            with self.assertRaises(FundingReferenceError): validate_snapshot(self.data,caps,self.manifest)

    def test_file_and_record_bindings_reject_unreviewed_changes(self):
        data = copy.deepcopy(self.data); data["programmes"][0]["facts"]["finance_max"]["value"] = "999"
        with self.assertRaises(FundingReferenceError): validate_snapshot(data, self.caps, self.manifest)
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory)/"snapshot.json";changed.write_text(json.dumps(data))
            with self.assertRaises(FundingReferenceError): load_funding_reference(data_path=changed)
        manifest=copy.deepcopy(self.manifest);manifest["sources"][0]["repo_snapshot_path"]="evidence/raw.pdf"
        with self.assertRaises(FundingReferenceError): validate_snapshot(self.data,self.caps,manifest)

    def test_call_finance_parser_keeps_native_amount_and_denominators(self):
        text = """Keretösszeg: 66,82 milliárd forint.
        minimum bruttó 2,5 millió forint – maximum bruttó 10 millió forint.
        A Finanszírozási összegen belül a vissza nem térítendő támogatás mértéke 50%.
        A Saját forrás elvárt mértéke a Projekt elszámolható költségének minimum 5%."""
        values=extract_call_finance(text)
        self.assertEqual(values["original_envelope"],Decimal("66820000000"))
        self.assertEqual(values["finance_min"],Decimal("2500000"))
        self.assertEqual(values["own_source_min_share"],Decimal("0.05"))
        with self.assertRaises(FundingReferenceError): extract_call_finance(text+text)

    def test_external_verifier_requires_full_exact_source_set(self):
        with self.assertRaises(FundingReferenceError): verify_external_sources(self.catalog,{})
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"wrong.pdf";path.write_bytes(b"%PDF-wrong")
            with self.assertRaises(FundingReferenceError):
                verify_external_sources(self.catalog,{sid:str(path) for sid in self.catalog.sources})

    def test_decimal_context_does_not_change_cap_validation(self):
        with localcontext() as context:
            context.prec=3
            catalog=load_funding_reference()
            self.assertEqual(catalog.caps["KEHOP417-CAP-33"]["combined_cap"],"8551847")


if __name__ == "__main__":
    unittest.main()
