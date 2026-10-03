import copy
import csv
import hashlib
import json
import tempfile
import unittest
from decimal import localcontext
from pathlib import Path

from modules.B14.funding_reference import (
    AS_OF, COMPLETION_AS_OF, COMPLETION_PATH, CAPS_418_PATH, COMPLETION_MANIFEST_PATH,
    DATA_PATH, CAPS_PATH, MANIFEST_PATH, CALL_SOURCES, PROCEDURE_SOURCE, FAQ_SOURCE,
    PROGRAMME_417, PROGRAMME_418, SCOPES, DATED_RULE_REFERENCE, DATED_INTAKE_STATUS,
    GROSS_POLICY_UNIT_CAP, FundingReferenceError, _digest, load_funding_reference,
    validate_rule_completion,
)


class B14RuleCompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_funding_reference()
        cls.data = json.loads(COMPLETION_PATH.read_text())
        cls.manifest = json.loads(COMPLETION_MANIFEST_PATH.read_text())
        cls.historical = json.loads(DATA_PATH.read_text())
        cls.old_manifest = json.loads(MANIFEST_PATH.read_text())
        with CAPS_418_PATH.open(newline="") as stream: cls.caps = list(csv.DictReader(stream))

    def programme(self, pid=PROGRAMME_418, **changes):
        args = dict(scope=SCOPES[pid], as_of=COMPLETION_AS_OF, claim=DATED_RULE_REFERENCE)
        args.update(changes)
        return self.catalog.read_programme(pid, **args)

    def cap(self, cap_id="KEHOP418-CAP-33", **changes):
        args = dict(programme_id=PROGRAMME_418, scope=SCOPES[PROGRAMME_418],
                    as_of=COMPLETION_AS_OF, unit="HUF/set", vat_basis="GROSS", claim=GROSS_POLICY_UNIT_CAP)
        args.update(changes)
        return self.catalog.read_cap(cap_id, **args)

    def validate(self, data, manifest=None, caps=None):
        validate_rule_completion(data, self.caps if caps is None else caps,
                                 self.manifest if manifest is None else manifest,
                                 self.historical, self.old_manifest)

    def rebind(self, data, manifest):
        manifest["programme_bindings"] = [dict(programme_id=r["programme_id"], sha256=_digest(r))
                                            for r in data["programmes"]]
        manifest["currentness_sha256"] = _digest(data["currentness"])

    def test_historical_inputs_and_old_reads_remain_exact(self):
        for p in (DATA_PATH, CAPS_PATH, MANIFEST_PATH):
            relative = str(p.relative_to(DATA_PATH.parents[3]))
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),
                             self.manifest["historical_input_sha256"][relative])
        self.assertEqual(len(self.catalog.caps), 39)
        self.assertEqual(len(self.catalog.sources), 11)
        for original in self.historical["programmes"]:
            row = self.programme(original["programme_id"], as_of=AS_OF)
            self.assertNotIn("rule_details", row)
            self.assertEqual(row["as_of"], "2026-10-01")
            self.assertEqual(row["intake"]["checked_at"], "2026-10-01")
        with self.assertRaises(FundingReferenceError): self.cap(as_of=AS_OF)

    def test_both_named_completions_have_explicit_issuer_and_geography(self):
        for pid in SCOPES:
            row = self.programme(pid)
            self.assertEqual(row["as_of"], COMPLETION_AS_OF)
            self.assertEqual(row["historical_reference_as_of"], AS_OF)
            self.assertEqual(row["rule_details"]["issuer"]["name"], "MFB Zrt.")
            self.assertEqual(row["rule_details_truth_status"], "POL")
            self.assertFalse(self.manifest["confers_registry_acceptance"])
            self.assertEqual(row["rule_details"]["source_id"], CALL_SOURCES[pid])
            self.assertEqual(row["rule_details"]["geography"]["basis"], "PROJECT_IMPLEMENTATION_LOCATION")

    def test_caps_are_own_source_and_keep_all_39_rows_each(self):
        self.assertEqual(len(self.catalog.completed_caps), 78)
        for i in range(1, 40):
            old = self.catalog.caps[f"KEHOP417-CAP-{i:02}"]
            row = self.cap(f"KEHOP418-CAP-{i:02}", unit=old["unit"])
            self.assertEqual(row["source_id"], CALL_SOURCES[PROGRAMME_418])
            self.assertEqual(row["programme_id"], PROGRAMME_418)
            for key in ("material_cap", "labour_cap", "combined_cap", "unit", "category", "variant"):
                self.assertEqual(row[key], old[key])
            self.assertIn("printed/PDF page", row["source_locator"])
        self.assertEqual(self.cap()["combined_cap"], "8551847")
        self.assertEqual(self.cap("KEHOP418-CAP-36")["source_locator"], "Annex 1, printed/PDF page 24")

    def test_caps_refuse_cross_programme_and_scope_transfer(self):
        with self.assertRaises(FundingReferenceError): self.cap("KEHOP417-CAP-33")
        with self.assertRaises(FundingReferenceError): self.cap(programme_id=PROGRAMME_417, scope=SCOPES[PROGRAMME_417])
        with self.assertRaises(FundingReferenceError): self.cap(scope=SCOPES[PROGRAMME_417])
        self.assertEqual(self.cap("KEHOP417-CAP-33", programme_id=PROGRAMME_417,
                                  scope=SCOPES[PROGRAMME_417])["source_id"], CALL_SOURCES[PROGRAMME_417])

    def test_caps_refuse_price_claims_net_and_wrong_units(self):
        for change in ({"claim":"MARKET_PRICE"}, {"claim":"EXPECTED_CAPEX"}, {"vat_basis":"NET"},
                       {"unit":"HUF/m2"}, {"unit":"EUR/set"}):
            with self.subTest(change=change), self.assertRaises(FundingReferenceError): self.cap(**change)

    def test_cumulation_preserves_or_scope_and_named_schemes(self):
        for pid in SCOPES:
            rule = self.programme(pid)["rule_details"]["cumulation"]
            self.assertEqual(rule["in_current_programme"]["application_state"], "SUPPORTED_NOT_MERELY_SUBMITTED")
            cross = rule["cross_scheme"]
            self.assertIn("OR", cross["matching_scope_operator"])
            self.assertTrue(cross["no_requirement_that_both_scopes_match"])
            self.assertEqual({x["identifier"] for x in cross["scheme_set"]},
                             {pid, "RRF-REP-10.13.1-24", "RRF-6.2.1", None})

    def test_pv_only_exception_never_grants_eligibility_or_double_funding(self):
        pv = self.programme()["rule_details"]["cumulation"]["cross_scheme"]["pv_only_exception"]
        self.assertEqual(pv["qualifying_investment_scope"], "EXCLUSIVELY_PV_SYSTEM_INSTALLATION")
        self.assertIn("same-cost EU double funding prohibition", pv["does_not_waive"])
        self.assertIn("current intake suspension", pv["does_not_waive"])
        self.assertEqual(pv["unlisted_scheme_extension"], "NOT_INFERRED")
        self.assertIn("NO_AUTOMATIC_APPROVAL", pv["machine_decision_use"])
        same = self.programme()["rule_details"]["same_cost_funding"]
        self.assertTrue(same["other_EU_funded_grant_prohibited"])
        self.assertTrue(same["other_EU_funded_repayable_aid_prohibited"])

    def test_hem_is_optional_written_and_not_extra_cash(self):
        hem = self.programme()["rule_details"]["HEM"]
        self.assertFalse(hem["mandatory_to_use_HEM"])
        self.assertTrue(hem["written_agreement_required_for_HEM_transfer_or_intention"])
        self.assertFalse(hem["cash_plus_HEM_for_same_advice_or_subactivity_allowed"])
        self.assertFalse(hem["adviser_extra_fee_in_HEM_agreement_allowed"])
        self.assertTrue(hem["advance_fee_also_prohibited"])
        self.assertEqual(hem["max_generation_agreements_in_programme"]["value"], "1")
        self.assertEqual(hem["HEM_transfer_recipient_class"], "EKR_OBLIGATED_PARTY")

    def test_applicant_property_consent_is_not_a_decision_engine(self):
        details = self.programme()["rule_details"]
        self.assertTrue(details["applicant_and_consent"]["adult_and_legally_capable_required"])
        self.assertEqual(details["property_rule"]["economic_use"]["eligible_work_scope"], "RESIDENTIAL_USE_PARTS_ONLY")
        self.assertFalse(hasattr(self.catalog, "approve_household"))
        self.assertFalse(hasattr(self.catalog, "calculate_financing"))
        self.assertIn("NOT_LISTED", details["eligible_activity_rules"]["PV_and_storage_as_eligible_activities"])

    def test_fresh_observations_have_new_ids_and_exact_date(self):
        for pid in SCOPES:
            row = self.programme(pid)
            self.assertTrue(row["current_status_source_id"].endswith("20261003"))
            self.assertEqual(row["intake"]["checked_at"], COMPLETION_AS_OF)
            self.assertEqual(row["intake"]["status"], "SUSPENDED_FOR_ENVELOPE_EXHAUSTION")
            for source in row["currentness_observations"].values():
                self.assertTrue(source["retrieved_at"].startswith(COMPLETION_AS_OF + "T"))
                self.assertIsNone(source["repo_snapshot_path"])
                self.assertEqual(source["reuse_status"], "EXTERNAL_ONLY")

    def test_fresh_index_selection_not_a_new_procedure_byte_proof(self):
        row = self.programme()
        index = row["currentness_observations"][row["document_list_source_id"]]
        self.assertEqual(index["selected_call"]["source_id"], CALL_SOURCES[PROGRAMME_418])
        self.assertEqual(index["selected_common_procedure"]["byte_recovery_this_pass"], "NOT_RECOVERED")
        invoice = row["rule_details"]["invoice_endorsement"]
        self.assertFalse(invoice["fresh_bytes_recovered"])
        self.assertEqual(invoice["evidence_state"], "PRIOR_VERIFIED_V1_018_REVIEW_NOT_FRESHLY_REREAD")
        self.assertEqual(len(row["prior_review_reliance"]), 4)
        self.assertTrue(all(x["fresh_recovery"] is False for x in row["prior_review_reliance"]))

    def test_fresh_faq_does_not_invent_effective_day_or_available_money(self):
        fresh = self.programme()["processing_FAQ_recovery"]
        self.assertEqual(fresh["source_id"], FAQ_SOURCE)
        self.assertTrue(fresh["exact_historical_byte_identity"])
        self.assertEqual(self.catalog.operational_observations["date_precision"], "month")
        for pid in SCOPES:
            row = self.programme(pid)
            self.assertTrue(all(x["value"] is None and x["truth_status"] == "Q" for x in row["unknowns"].values()))
            self.assertIsNone(row["eligible_total_hard_cap"]["value"])

    def test_numeric_facts_remain_same_source_units_and_denominators(self):
        for pid in SCOPES:
            old, new = self.programme(pid, as_of=AS_OF), self.programme(pid)
            self.assertEqual(old["facts"], new["facts"])
            self.assertEqual(old["dates"], new["dates"])
            self.assertEqual(new["facts"]["grant_share"]["denominator"], "FINANCING_AMOUNT")
            self.assertEqual(new["facts"]["own_source_min_share"]["denominator"], "ELIGIBLE_PROJECT_COST")
            self.assertEqual(new["facts"]["loan_maturity_max"]["unit"], "year")

    def test_unsupported_dates_and_claims_remain_refused(self):
        for date in ("current", "today", "2026-10-02", "2026-10-04", "2026-10-03T00:00:00Z", None):
            with self.subTest(date=date), self.assertRaises(FundingReferenceError): self.programme(as_of=date)
        for claim in ("HOUSEHOLD_ELIGIBLE", "AVAILABLE_GRANT", "CONFIRMED_AWARD", "NATIONAL_ALLOCATION", "POLICY_DEFAULT"):
            with self.subTest(claim=claim), self.assertRaises(FundingReferenceError): self.programme(claim=claim)
        with self.assertRaises(FundingReferenceError):
            self.catalog.read_intake(PROGRAMME_418, scope=SCOPES[PROGRAMME_418], as_of=COMPLETION_AS_OF,
                                     claim="NEW_APPLICATION_AVAILABLE")

    def test_new_views_are_deeply_immutable(self):
        with self.assertRaises(TypeError): self.programme()["rule_details"]["issuer"]["name"] = "X"
        with self.assertRaises(TypeError): self.cap()["material_cap"] = "0"
        with self.assertRaises(TypeError): self.catalog.completed_programmes["X"] = {}

    def test_new_source_files_are_lf_and_digest_bound(self):
        for path, field in ((COMPLETION_PATH, "data_sha256"), (CAPS_418_PATH, "caps_sha256")):
            self.assertNotIn(b"\r", path.read_bytes())
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), self.manifest[field])
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "changed.json";p.write_text(COMPLETION_PATH.read_text()+" ")
            with self.assertRaises(FundingReferenceError): load_funding_reference(completion_path=p)

    def test_semantic_exception_mutations_fail_even_after_rebinding(self):
        mutations = [
            lambda r:r["cumulation"]["cross_scheme"].update(matching_scope_operator="AND"),
            lambda r:r["cumulation"]["in_current_programme"].update(application_state="SUBMITTED"),
            lambda r:r["cumulation"]["cross_scheme"]["pv_only_exception"].update(qualifying_investment_scope="ANY_PV"),
            lambda r:r["cumulation"]["cross_scheme"]["pv_only_exception"].update(does_not_waive=[]),
            lambda r:r["same_cost_funding"].update(other_EU_funded_repayable_aid_prohibited=False),
            lambda r:r["HEM"].update(mandatory_to_use_HEM=True),
            lambda r:r["HEM"].update(cash_plus_HEM_for_same_advice_or_subactivity_allowed=True),
            lambda r:r["invoice_endorsement"].update(fresh_bytes_recovered=True),
            lambda r:r["cost_rule"].update(finance_ceiling_is_total_eligible_cost_ceiling=True),
            lambda r:r["issuer"].update(name="UNVERIFIED_ISSUER"),
            lambda r:r["geography"].update(included="NATIONAL"),
        ]
        for mutation in mutations:
            d, m = copy.deepcopy(self.data), copy.deepcopy(self.manifest)
            mutation(d["programmes"][1]);self.rebind(d,m)
            with self.subTest(mutation=mutation), self.assertRaises(FundingReferenceError): self.validate(d,m)

        d = copy.deepcopy(self.data)
        d["programme_rules_truth_status"] = "OBS"
        with self.assertRaises(FundingReferenceError): self.validate(d)
        m = copy.deepcopy(self.manifest)
        m["confers_registry_acceptance"] = True
        with self.assertRaises(FundingReferenceError): self.validate(self.data,m)

    def test_currentness_mutations_fail_even_after_rebinding(self):
        mutations = [
            lambda f:f["observations"][0]["claims"].update(intake="OPEN"),
            lambda f:f["observations"][0].update(retrieved_at="2026-10-01T00:00:00Z"),
            lambda f:f["observations"][1]["selected_call"].update(_id="NEW_REVISION"),
            lambda f:f["observations"][1]["selected_common_procedure"].update(byte_recovery_this_pass="RECOVERED"),
            lambda f:f["prior_review_reliance"][0].update(fresh_recovery=True),
            lambda f:f["fresh_exact_call_recovery"][0].update(sha256="0"*64),
            lambda f:f.update(claims_allowed=["HOUSEHOLD_APPROVAL"]),
        ]
        for mutation in mutations:
            d,m = copy.deepcopy(self.data),copy.deepcopy(self.manifest)
            mutation(d["currentness"]);self.rebind(d,m)
            with self.subTest(mutation=mutation), self.assertRaises(FundingReferenceError): self.validate(d,m)

    def test_cap_mutations_and_duplicates_fail(self):
        for change in ({"programme_id":PROGRAMME_417}, {"source_id":CALL_SOURCES[PROGRAMME_417]},
                       {"vat_basis":"NET"}, {"material_cap":"NaN"}, {"combined_cap":"0"},
                       {"meaning":"EXPECTED_CAPEX"}):
            caps = copy.deepcopy(self.caps);caps[0].update(change)
            m = copy.deepcopy(self.manifest);m["cap_bindings"] = [dict(cap_id=x["cap_id"],sha256=_digest(x)) for x in caps]
            with self.subTest(change=change), self.assertRaises(FundingReferenceError): self.validate(self.data,m,caps)
        caps = copy.deepcopy(self.caps);caps[-1] = caps[0]
        with self.assertRaises(FundingReferenceError): self.validate(self.data,caps=caps)

    def test_completion_checks_actual_historical_override_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            paths = [folder / "historical.json", folder / "caps.csv", folder / "manifest.json"]
            originals = [DATA_PATH, CAPS_PATH, MANIFEST_PATH]
            kwargs = dict(zip(("data_path", "caps_path", "manifest_path"), paths))
            def restore():
                for target, source in zip(paths, originals): target.write_bytes(source.read_bytes())
            restore()
            identical = load_funding_reference(**kwargs)
            self.assertEqual(identical.completed_programmes[PROGRAMME_417]["facts"]["finance_max"]["value"], "10000000")
            data = json.loads(paths[0].read_text());manifest = json.loads(paths[2].read_text())
            data["programmes"][0]["facts"]["finance_max"]["value"] = "11000000"
            paths[0].write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n")
            manifest["data_sha256"] = hashlib.sha256(paths[0].read_bytes()).hexdigest()
            manifest["programme_bindings"] = [dict(programme_id=x["programme_id"],sha256=_digest(x)) for x in data["programmes"]]
            paths[2].write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n")
            with self.assertRaisesRegex(FundingReferenceError, "consumed historical"):
                load_funding_reference(**kwargs)
            restore()
            with paths[1].open(newline="") as stream: caps = list(csv.DictReader(stream))
            caps[0]["material_cap"] = str(int(caps[0]["material_cap"])+1)
            caps[0]["combined_cap"] = str(int(caps[0]["combined_cap"])+1)
            with paths[1].open("w",newline="") as stream:
                writer = csv.DictWriter(stream,fieldnames=list(caps[0]),lineterminator="\n")
                writer.writeheader();writer.writerows(caps)
            manifest = json.loads(paths[2].read_text())
            manifest["caps_sha256"] = hashlib.sha256(paths[1].read_bytes()).hexdigest()
            manifest["cap_bindings"] = [dict(cap_id=x["cap_id"],sha256=_digest(x)) for x in caps]
            paths[2].write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
            with self.assertRaisesRegex(FundingReferenceError, "consumed historical"):
                load_funding_reference(**kwargs)
            restore()
            paths[2].write_bytes(paths[2].read_bytes()+b" ")
            with self.assertRaisesRegex(FundingReferenceError, "consumed historical"):
                load_funding_reference(**kwargs)

    def test_low_decimal_precision_does_not_change_caps(self):
        with localcontext() as context:
            context.prec = 3
            catalog = load_funding_reference()
            self.assertEqual(catalog.completed_caps["KEHOP418-CAP-33"]["combined_cap"], "8551847")


if __name__ == "__main__": unittest.main()
