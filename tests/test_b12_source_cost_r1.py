"""R1 stale-review and normalization regressions; new evidence is TEST_ONLY."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from modules.B12.input_accounting_contract import B12ContractError
from modules.B12.source_cost_inputs import (
    load_source_catalogue, resolve_cost_inputs, normalization_input_revision,
    offer_evidence_revision,
)
from test_b12_source_cost_inputs import Fixture, BASIS, TEST_CONTEXT, PACKAGE


class ActiveOfferRevisionTests(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()
        self.addCleanup(self.f.temp.cleanup)

    def payload(self):
        self.f.build()
        return json.loads((self.f.root / "catalogue.json").read_text(encoding="utf-8"))

    def normalize(self, offer, qualification_pin=None):
        offer["normalization_pin"] = self.f.pin("normalization-new.json", dict(
            input_revision=normalization_input_revision(offer),
            normalized={k: offer[k] for k in ("tax_basis", "price_kind", "reference_period", "inclusions")},
            qualification_pin=qualification_pin))

    def load_new(self, payload):
        path = self.f.write("catalogue-new.json", payload)
        return load_source_catalogue(self.f.root, path.name,
                                     expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    def resolve(self, catalogue):
        return resolve_cost_inputs(catalogue, (self.f.binding,), BASIS, case_context=TEST_CONTEXT)

    def renew_review(self, payload):
        # A new content-bound use review, not a new owner-per-datum approval.
        uses = copy.deepcopy(payload["use_reviews_pin"]["expected"])
        uses[0]["offer_evidence_revision"] = offer_evidence_revision(payload["offers"][0])
        payload["use_reviews_pin"] = self.f.pin("reviews-new.json", uses)

    def test_new_source_same_id_old_review_cannot_use_old_still_existing_evidence(self):
        data = self.payload();offer = data["offers"][0]
        revised = dict(self.f.fact, value="999")
        offer.update(value="999", fact_pin=self.f.pin("new-price-source.json", revised))
        self.normalize(offer)
        # Old fact.json and the old review's own evidence pin remain valid.
        catalogue = self.load_new(data)
        with self.assertRaisesRegex(B12ContractError, "reviewed offer evidence revision changed"):
            self.resolve(catalogue)

    def test_new_qualifier_revision_with_same_amount_requires_current_review(self):
        data = self.payload();offer = data["offers"][0]
        offer["qualifier_pin"] = self.f.pin("new-qualifier.json", dict(
            value=offer["value"], tax_basis="GROSS", price_kind="EXACT_PRICE", revision="TEST_ONLY:new"))
        self.normalize(offer)
        with self.assertRaisesRegex(B12ContractError, "reviewed offer evidence revision changed"):
            self.resolve(self.load_new(data))

    def test_new_source_period_same_offer_id_cannot_inherit_review(self):
        data = self.payload();offer = data["offers"][0]
        offer["reference_period"] = ["2026-10-22", "2026-10-22"]
        offer["period_pin"] = self.f.pin("new-period.json", "2026-10-22")
        self.normalize(offer)
        with self.assertRaisesRegex(B12ContractError, "reviewed offer evidence revision changed"):
            self.resolve(self.load_new(data))

    def test_changed_package_content_same_id_cannot_inherit_review(self):
        data = self.payload();offer = data["offers"][0]
        offer["inclusions"] = ["outdoor", "pump"]
        offer["package_pin"] = self.f.pin("new-package.json", {"inclusions": offer["inclusions"]})
        self.normalize(offer)
        with self.assertRaisesRegex(B12ContractError, "reviewed offer evidence revision changed"):
            self.resolve(self.load_new(data))

    def test_price_kind_cannot_be_relabelled_after_rehashing_catalogue_and_normalization(self):
        data = self.payload();offer = data["offers"][0]
        offer["qualifier_pin"] = self.f.pin("starting-price.json", dict(
            value=offer["value"], tax_basis="GROSS", price_kind="STARTING_FROM"))
        offer["original_price_kind"] = "STARTING_FROM"
        # Attacker retains EXACT_PRICE and repins their normalized label.
        self.normalize(offer)
        with self.assertRaisesRegex(B12ContractError, "contradicts pinned observation"):
            self.load_new(data)

    def test_fresh_review_of_correctly_preserved_starting_price_still_yields_q(self):
        data = self.payload();offer = data["offers"][0]
        offer["qualifier_pin"] = self.f.pin("starting-price.json", dict(
            value=offer["value"], tax_basis="GROSS", price_kind="STARTING_FROM"))
        offer.update(price_kind="STARTING_FROM", original_price_kind="STARTING_FROM")
        self.normalize(offer);self.renew_review(data)
        result = self.resolve(self.load_new(data))
        self.assertFalse(result.costs)
        self.assertEqual(result.observations[0].price_kind, "STARTING_FROM")

    def fs01_payload(self):
        path = PACKAGE / "inputs/preserved/b12-072-fs01-hu-price-applicability-20261022-v1/SOURCE_PRICE_OBSERVATIONS.json"
        observation = json.loads(path.read_text(encoding="utf-8"))["observations"][2]
        self.f.fact = copy.deepcopy(observation)
        self.f.offer.update(source_id=observation["id"], product=observation["model"], value=observation["current_price"],
                            amount_field="current_price", tax_basis=observation["tax"],
                            original_price_kind="CURRENT_OBSERVATION", scope_field=None)
        self.f.binding["product"] = observation["model"]
        return self.payload()

    def test_real_fs01_fact_tax_enforced_when_qualifier_pin_is_null(self):
        data = self.fs01_payload();offer = data["offers"][0]
        self.assertIsNone(offer["qualifier_pin"])
        self.assertFalse(self.resolve(self.load_new(data)).costs)
        offer["tax_basis"] = "GROSS"
        self.normalize(offer)
        with self.assertRaisesRegex(B12ContractError, "contradicts pinned observation"):
            self.load_new(data)

    def test_fs01_qualifier_cannot_erase_contradicting_raw_tax_field(self):
        data = self.fs01_payload();offer = data["offers"][0]
        offer["tax_basis"] = "GROSS"
        offer["qualifier_pin"] = self.f.pin("unsupported-gross-qualifier.json", dict(
            value=offer["value"], tax_basis="GROSS", price_kind="CURRENT_OBSERVATION"))
        self.normalize(offer)
        with self.assertRaisesRegex(B12ContractError, "contradicts pinned observation"):
            self.load_new(data)

    def test_separate_scoped_qualification_requires_pinned_support_and_new_use_review(self):
        self.f.fact["tax"] = self.f.offer["tax_basis"] = "TEST_ONLY:TAX_Q"
        data = self.payload();offer = data["offers"][0]
        offer["tax_basis"] = "GROSS"
        support = self.f.pin("TEST_ONLY-new-merchant-tax-evidence.json", dict(
            source_id="TEST_ONLY:tax-declaration", original_url="https://example.invalid/test-only-tax",
            product=offer["product"], tax_basis="GROSS"))
        qualification = self.f.pin("TEST_ONLY-tax-qualification.json", dict(
            input_revision=normalization_input_revision(offer), claims={"tax_basis": "GROSS"},
            reason="TEST_ONLY:explicit product-scoped tax evidence, not an owner permission",
            evidence_pins=[support]))
        self.normalize(offer, qualification)
        with self.assertRaisesRegex(B12ContractError, "reviewed offer evidence revision changed"):
            self.resolve(self.load_new(data))
        self.renew_review(data)
        result = self.resolve(self.load_new(data))
        self.assertEqual(len(result.costs), 1)
        self.assertEqual(result.costs[0].net.truth, "Q")
        self.assertEqual(result.costs[0].vat.truth, "Q")

    def test_qualification_reason_without_supporting_content_does_not_authorize_tax_upgrade(self):
        self.f.fact["tax"] = self.f.offer["tax_basis"] = "TEST_ONLY:TAX_Q"
        data = self.payload();offer = data["offers"][0];offer["tax_basis"] = "GROSS"
        qualification = self.f.pin("unsupported-qualification.json", dict(
            input_revision=normalization_input_revision(offer), claims={"tax_basis": "GROSS"},
            reason="TEST_ONLY:explanatory text alone", evidence_pins=[]))
        self.normalize(offer, qualification)
        with self.assertRaisesRegex(B12ContractError, "qualification evidence required"):
            self.load_new(data)

    def test_source_period_and_package_labels_cannot_diverge_from_active_pins(self):
        for field, value, message in [
            ("reference_period", ["2026-10-22", "2026-10-22"], "reference period changed"),
            ("inclusions", ["outdoor", "pump"], "package inclusion evidence changed"),
        ]:
            data = self.payload();offer = data["offers"][0];offer[field] = value
            self.normalize(offer)
            with self.subTest(field=field), self.assertRaisesRegex(B12ContractError, message):
                self.load_new(data)

    def test_relevant_underlying_proof_change_detected_even_if_old_primary_fact_survives(self):
        data = self.payload();catalogue = self.load_new(data)
        # Direct mutation without repinning is rejected before any row arithmetic.
        (self.f.root / "package-0.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(B12ContractError, "evidence bytes changed"):
            self.resolve(catalogue)

    def test_unrelated_catalogue_addition_does_not_invalidate_unchanged_offer_review(self):
        data = self.payload();unused = copy.deepcopy(data["offers"][0])
        unused["offer_id"] = "TEST_ONLY:unrelated-offer"
        self.normalize(unused)
        # Keep the first offer's normalization file intact as a separate revision.
        data["offers"].append(unused)
        self.assertEqual(len(self.resolve(self.load_new(data)).costs), 1)

    def raw_restriction_with_point_qualifier(self, kind="STARTING_FROM"):
        data = self.payload()
        offer = data["offers"][0]
        offer["fact_pin"] = self.f.pin("TEST_ONLY-restricted-raw-fact.json",
                                       dict(self.f.fact, price_kind=kind))
        offer["qualifier_pin"] = self.f.pin("TEST_ONLY-point-qualifier.json", dict(
            value=offer["value"], tax_basis="GROSS", price_kind="EXACT_PRICE"))
        offer.update(original_price_kind="EXACT_PRICE", price_kind="EXACT_PRICE")
        self.normalize(offer)
        self.renew_review(data)
        return data

    def test_raw_starting_or_other_limit_cannot_be_erased_by_fresh_exact_qualifier_and_review(self):
        for kind in ("STARTING_FROM", "MINIMUM_FEE", "INDICATIVE", "POLICY_CAP"):
            data = self.raw_restriction_with_point_qualifier(kind)
            # Every hash and the use review are current; raw fact still limits price.
            with self.subTest(raw_kind=kind), self.assertRaisesRegex(
                    B12ContractError, "contradicts pinned observation"):
                self.resolve(self.load_new(data))

    def point_price_qualification(self, offer, supported_kind):
        support = self.f.pin("TEST_ONLY-product-point-price-evidence.json", dict(
            source_id="TEST_ONLY:product-price-declaration",
            original_url="https://example.invalid/test-only-product-price",
            product=offer["product"], price_kind=supported_kind))
        return self.f.pin("TEST_ONLY-price-kind-qualification.json", dict(
            input_revision=normalization_input_revision(offer),
            claims={"price_kind": "EXACT_PRICE"},
            reason="TEST_ONLY:product-scoped supporting evidence for this point price",
            evidence_pins=[support]))

    def test_raw_starting_limit_upgrade_requires_supported_qualification_and_current_review(self):
        data = self.raw_restriction_with_point_qualifier()
        offer = data["offers"][0]
        self.normalize(offer, self.point_price_qualification(offer, "EXACT_PRICE"))
        with self.assertRaisesRegex(B12ContractError, "reviewed offer evidence revision changed"):
            self.resolve(self.load_new(data))
        self.renew_review(data)
        result = self.resolve(self.load_new(data))
        self.assertEqual(len(result.costs), 1)
        self.assertEqual(str(result.costs[0].gross.value), "200.50")
        self.assertEqual(result.costs[0].net.truth, "Q")
        self.assertEqual(result.costs[0].vat.truth, "Q")
        self.assertIsNone(result.full_capex)

    def test_raw_starting_upgrade_qualification_must_actually_support_point_price(self):
        data = self.raw_restriction_with_point_qualifier()
        offer = data["offers"][0]
        self.normalize(offer, self.point_price_qualification(offer, "STARTING_FROM"))
        self.renew_review(data)
        with self.assertRaisesRegex(B12ContractError, "claim lacks pinned supporting content"):
            self.resolve(self.load_new(data))


if __name__ == "__main__":
    unittest.main()
