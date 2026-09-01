from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import unittest

from modules.B10.dso_headroom_contract import B10HeadroomContractError, assess_incremental_demand
from modules.B10.opus_headroom_contract import (
    EXTERNAL_ONLY_REUSE_UNRESOLVED,
    OPUS_TITASZ_DATA_URL,
    OPUS_TITASZ_EFFECTIVE_DATE,
    OPUS_TITASZ_LANDING_URL,
    OPUS_TITASZ_LEGAL_URL,
    OPUS_TITASZ_COMPANY_URL,
    OPUS_TITASZ_PUBLISHER,
    OPUS_TITASZ_SOURCE_ID,
    OPUS_TITASZ_SOURCE_PDF_SHA256,
    OPUS_TITASZ_SOURCE_REFS,
    OPUS_TITASZ_SOURCE_REVISION,
    OpusHeadroomContractError,
    OpusHeadroomProvenance,
    REUSE_CLEARED,
    UNVERIFIED_EXTRACTION,
    VERIFIED_AGAINST_SOURCE,
    parse_opus_titasz_consumption_headroom_text,
)


HEADERS = "station_code\tstation_name\tfree_capacity_current_mw\tfree_capacity_5y_mw\n"


def normalized_text(current="17.4", future="12.1", code="DBDK", name="Debrecen Délkelet"):
    return HEADERS + f"{code}\t{name}\t{current}\t{future}\n"


BASE_PROVENANCE = OpusHeadroomProvenance(
    source_id=OPUS_TITASZ_SOURCE_ID,
    publisher=OPUS_TITASZ_PUBLISHER,
    dataset_name="Alállomások szabad kapacitásai",
    source_url=OPUS_TITASZ_DATA_URL,
    landing_url=OPUS_TITASZ_LANDING_URL,
    legal_url=OPUS_TITASZ_LEGAL_URL,
    company_url=OPUS_TITASZ_COMPANY_URL,
    retrieved_at=datetime(2026, 9, 1, 20, 13, 58, tzinfo=timezone.utc),
    source_effective_date=OPUS_TITASZ_EFFECTIVE_DATE,
    source_revision=OPUS_TITASZ_SOURCE_REVISION,
    license_decision=EXTERNAL_ONLY_REUSE_UNRESOLVED,
    raw_storage_policy="EXTERNAL_ONLY",
    extraction_verification=UNVERIFIED_EXTRACTION,
)


def cleared(text):
    return replace(
        BASE_PROVENANCE,
        license_decision=REUSE_CLEARED,
        extraction_verification=VERIFIED_AGAINST_SOURCE,
        source_pdf_sha256=OPUS_TITASZ_SOURCE_PDF_SHA256,
        normalized_text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


class OpusHeadroomContractTests(unittest.TestCase):
    def test_unresolved_reuse_is_q_and_normalized_row_never_obs(self):
        batch = parse_opus_titasz_consumption_headroom_text(normalized_text(), provenance=BASE_PROVENANCE)
        self.assertEqual("Q", batch.evidence_status)
        self.assertEqual({"Q"}, {row.evidence_status for row in batch.records})

    def test_verified_synthetic_acquisition_is_der_only_through_parser(self):
        text = normalized_text()
        batch = parse_opus_titasz_consumption_headroom_text(text, provenance=cleared(text))
        self.assertEqual("DER", batch.evidence_status)
        self.assertEqual("DER", batch.records[0].evidence_status)

    def test_missing_pdf_hash_keeps_row_q(self):
        text = normalized_text()
        provenance = replace(cleared(text), source_pdf_sha256=None)
        batch = parse_opus_titasz_consumption_headroom_text(text, provenance=provenance)
        self.assertEqual("Q", batch.evidence_status)

    def test_wrong_pdf_hash_is_rejected(self):
        text = normalized_text()
        with self.assertRaisesRegex(OpusHeadroomContractError, "source_pdf_sha256"):
            replace(cleared(text), source_pdf_sha256="0" * 64)

    def test_exact_normalized_hash_is_required(self):
        text = normalized_text()
        with self.assertRaisesRegex(OpusHeadroomContractError, "normalized text"):
            parse_opus_titasz_consumption_headroom_text(text, provenance=replace(cleared(text), normalized_text_sha256="0" * 64))

    def test_effective_date_and_revision_are_bound(self):
        with self.assertRaisesRegex(OpusHeadroomContractError, "effective_date"):
            replace(BASE_PROVENANCE, source_effective_date="2026-04-01")
        with self.assertRaisesRegex(OpusHeadroomContractError, "source_revision"):
            replace(BASE_PROVENANCE, source_revision="EFFECTIVE_2026-04-01")

    def test_current_and_five_year_values_remain_separate(self):
        text = normalized_text(current="17.4", future="12.1")
        row = parse_opus_titasz_consumption_headroom_text(text, provenance=cleared(text)).records[0]
        self.assertEqual(17.4, row.free_capacity_current_mw)
        self.assertEqual(12.1, row.free_capacity_5y_mw)

    def test_explicit_zero_is_valid_but_missing_is_q_not_zero(self):
        zero_text = normalized_text(current="0,0", future="0,0")
        zero_row = parse_opus_titasz_consumption_headroom_text(zero_text, provenance=cleared(zero_text)).records[0]
        self.assertEqual("DER", zero_row.evidence_status)
        self.assertEqual(0.0, zero_row.free_capacity_current_mw)
        missing_text = normalized_text(current="", future="12.1")
        missing_row = parse_opus_titasz_consumption_headroom_text(missing_text, provenance=cleared(missing_text)).records[0]
        self.assertEqual("Q", missing_row.evidence_status)
        self.assertIsNone(missing_row.free_capacity_current_mw)

    def test_negative_value_is_rejected(self):
        with self.assertRaisesRegex(OpusHeadroomContractError, "non-negative"):
            parse_opus_titasz_consumption_headroom_text(normalized_text(current="-1"), provenance=BASE_PROVENANCE)

    def test_malformed_row_is_rejected(self):
        with self.assertRaises(OpusHeadroomContractError):
            parse_opus_titasz_consumption_headroom_text(normalized_text(code=""), provenance=BASE_PROVENANCE)
        with self.assertRaises(OpusHeadroomContractError):
            parse_opus_titasz_consumption_headroom_text(HEADERS + "DBDK\tDebrecen\t1\t2\textra\n", provenance=BASE_PROVENANCE)

    def test_duplicate_source_row_key_is_rejected_but_duplicate_code_can_be_disambiguated(self):
        distinct = HEADERS + "DEBR\tDebrecen OVIT 11 kV\t22.6\t22.6\nDEBR\tDebrecen OVIT 22 kV\t0\t0\n"
        batch = parse_opus_titasz_consumption_headroom_text(distinct, provenance=BASE_PROVENANCE)
        self.assertEqual(2, len(batch.records))
        duplicate = distinct + "DEBR\tDebrecen OVIT 11 kV\t22.6\t22.6\n"
        with self.assertRaisesRegex(OpusHeadroomContractError, "duplicate"):
            parse_opus_titasz_consumption_headroom_text(duplicate, provenance=BASE_PROVENANCE)

    def test_no_voltage_n1_or_peak_is_invented_and_mvm_assessment_rejects_opus_row(self):
        text = normalized_text()
        row = parse_opus_titasz_consumption_headroom_text(text, provenance=cleared(text)).records[0]
        self.assertFalse(hasattr(row, "voltage_kv"))
        self.assertFalse(hasattr(row, "n_minus_1_capacity_mw"))
        self.assertFalse(hasattr(row, "winter_evening_peak_load_mw"))
        with self.assertRaisesRegex(B10HeadroomContractError, "DsoHeadroomRecord"):
            assess_incremental_demand(
                row,
                incremental_demand_mw=1.0,
                demand_region_id=row.region_id,
                demand_region_scheme="DSO_SUBSTATION",
                demand_evidence_status="DER",
                demand_source_refs=OPUS_TITASZ_SOURCE_REFS,
            )

    def test_mgt_and_non_additive_boundaries_are_preserved(self):
        text = normalized_text()
        batch = parse_opus_titasz_consumption_headroom_text(text, provenance=cleared(text))
        self.assertEqual("MGT_REQUIRED", batch.records[0].connection_authority)
        self.assertEqual("NONE_NON_ADDITIVE", batch.aggregation_authority)

    def test_q_propagates_from_incomplete_row(self):
        text = normalized_text(current="", future="12.1")
        batch = parse_opus_titasz_consumption_headroom_text(text, provenance=cleared(text))
        self.assertEqual("Q", batch.evidence_status)

    def test_opus_identity_is_not_mvm_identity(self):
        text = normalized_text()
        row = parse_opus_titasz_consumption_headroom_text(text, provenance=cleared(text)).records[0]
        self.assertTrue(row.region_id.startswith("OPUS_TITASZ:"))
        self.assertNotIn("MVM_DEMASZ", row.region_id)


if __name__ == "__main__":
    unittest.main()
