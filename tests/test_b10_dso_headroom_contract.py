from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import unittest

from modules.B10.dso_headroom_contract import (
    B10HeadroomContractError,
    DsoHeadroomProvenance,
    EXTERNAL_ONLY_REUSE_UNRESOLVED,
    REUSE_CLEARED,
    UNVERIFIED_EXTRACTION,
    VERIFIED_AGAINST_SOURCE,
    assess_incremental_demand,
    parse_mvm_demasz_consumption_headroom_text,
)


HEADERS = (
    "network_operator\tstation_name\tstation_code\tn1_capacity_current_mw\t"
    "n1_capacity_5y_mw\tvoltage_kv\twinter_evening_load_current_mw\t"
    "free_capacity_current_mw\twinter_evening_load_5y_mw\tfree_capacity_5y_mw\n"
)


def normalized_text(*, current_free="12.5", future_free="18.0"):
    return HEADERS + (
        "DEMASZ\tExample Station\tBAJA\t50\t60\t132\t37.5\t"
        f"{current_free}\t42\t{future_free}\n"
    )


BASE_PROVENANCE = DsoHeadroomProvenance(
    source_id="SRC-B10-MVM-DEMASZ-CONSUMPTION-HEADROOM-2026",
    publisher="MVM Démász Áramhálózati Kft.",
    dataset_name="MVM DEMASZ consumption-purpose free capacities",
    source_url="https://mvmhalozat.hu/attachments/41914",
    methodology_source_id="SRC-B10-MVM-DEMASZ-HEADROOM-METHOD-2026",
    methodology_url="https://mvmhalozat.hu/attachments/41913",
    retrieved_at=datetime(2026, 9, 1, 18, 30, tzinfo=timezone.utc),
    license_decision=EXTERNAL_ONLY_REUSE_UNRESOLVED,
    raw_storage_policy="EXTERNAL_ONLY",
    extraction_verification=UNVERIFIED_EXTRACTION,
)


def cleared(text):
    return replace(
        BASE_PROVENANCE,
        license_decision=REUSE_CLEARED,
        extraction_verification=VERIFIED_AGAINST_SOURCE,
        source_pdf_sha256="1" * 64,
        normalized_text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


class B10DsoHeadroomContractTests(unittest.TestCase):
    def test_unverified_or_uncleared_normalization_remains_q(self):
        batch = parse_mvm_demasz_consumption_headroom_text(normalized_text(), provenance=BASE_PROVENANCE)
        self.assertEqual("Q", batch.evidence_status)
        self.assertTrue(all(row.evidence_status == "Q" for row in batch.records))

    def test_verified_normalization_is_der_never_obs(self):
        text = normalized_text()
        batch = parse_mvm_demasz_consumption_headroom_text(text, provenance=cleared(text))
        self.assertEqual("DER", batch.evidence_status)
        self.assertEqual(2, len(batch.records))
        self.assertTrue(all(row.evidence_status == "DER" for row in batch.records))
        self.assertEqual({"CURRENT", "FIVE_YEAR"}, {row.horizon for row in batch.records})

    def test_current_and_five_year_values_remain_separate(self):
        text = normalized_text(current_free="12.5", future_free="18.0")
        batch = parse_mvm_demasz_consumption_headroom_text(text, provenance=cleared(text))
        by_horizon = {row.horizon: row for row in batch.records}
        self.assertEqual(12.5, by_horizon["CURRENT"].theoretical_free_capacity_mw)
        self.assertEqual(18.0, by_horizon["FIVE_YEAR"].theoretical_free_capacity_mw)

    def test_substation_grain_is_canonical_and_not_county(self):
        text = normalized_text()
        row = parse_mvm_demasz_consumption_headroom_text(text, provenance=cleared(text)).records[0]
        self.assertEqual("DSO_SUBSTATION", row.region_scheme)
        self.assertEqual("MVM_DEMASZ:BAJA:132KV", row.region_id)

    def test_source_native_four_letter_station_code_is_preserved(self):
        text = normalized_text().replace("BAJA", "BAJD")
        row = parse_mvm_demasz_consumption_headroom_text(text, provenance=cleared(text)).records[0]
        self.assertEqual("BAJD", row.station_code)
        self.assertEqual("MVM_DEMASZ:BAJD:132KV", row.region_id)

    def test_non_letter_or_empty_station_code_fails_closed(self):
        with self.assertRaisesRegex(B10HeadroomContractError, "station_code"):
            parse_mvm_demasz_consumption_headroom_text(normalized_text().replace("BAJA", "AB12"), provenance=BASE_PROVENANCE)
        with self.assertRaisesRegex(B10HeadroomContractError, "station_code"):
            parse_mvm_demasz_consumption_headroom_text(normalized_text().replace("BAJA", ""), provenance=BASE_PROVENANCE)

    def test_headroom_is_not_connection_authority(self):
        text = normalized_text()
        row = parse_mvm_demasz_consumption_headroom_text(text, provenance=cleared(text)).records[0]
        self.assertEqual("MGT_REQUIRED", row.connection_authority)

    def test_exact_normalized_checksum_is_required_for_der(self):
        text = normalized_text()
        provenance = replace(
            cleared(text),
            normalized_text_sha256="0" * 64,
        )
        with self.assertRaisesRegex(B10HeadroomContractError, "normalized text"):
            parse_mvm_demasz_consumption_headroom_text(text, provenance=provenance)

    def test_wrong_operator_headers_or_duplicate_key_fail_closed(self):
        text = normalized_text()
        with self.assertRaises(B10HeadroomContractError):
            parse_mvm_demasz_consumption_headroom_text(text.replace("DEMASZ", "OTHER", 1), provenance=BASE_PROVENANCE)
        with self.assertRaises(B10HeadroomContractError):
            parse_mvm_demasz_consumption_headroom_text(text.replace("station_code", "station", 1), provenance=BASE_PROVENANCE)
        duplicate = text + text.splitlines()[1] + "\n"
        with self.assertRaisesRegex(B10HeadroomContractError, "duplicate"):
            parse_mvm_demasz_consumption_headroom_text(duplicate, provenance=cleared(duplicate))

    def test_missing_or_negative_numeric_value_fails_closed(self):
        with self.assertRaises(B10HeadroomContractError):
            parse_mvm_demasz_consumption_headroom_text(normalized_text(current_free=""), provenance=BASE_PROVENANCE)
        with self.assertRaises(B10HeadroomContractError):
            parse_mvm_demasz_consumption_headroom_text(normalized_text(current_free="-1"), provenance=BASE_PROVENANCE)

    def test_assessment_requires_exact_dso_substation_mapping(self):
        text = normalized_text()
        row = parse_mvm_demasz_consumption_headroom_text(text, provenance=cleared(text)).records[0]
        with self.assertRaisesRegex(B10HeadroomContractError, "exactly match"):
            assess_incremental_demand(
                row,
                incremental_demand_mw=5.0,
                demand_region_id="HUNGARY_CONTROL_AREA",
                demand_region_scheme="ENTSOE_CONTROL_AREA",
                demand_evidence_status="DER",
                demand_source_refs=("SRC-B08-EXAMPLE",),
            )

    def test_assessment_computes_remaining_and_overload_without_permission_claim(self):
        text = normalized_text(current_free="12.5")
        row = parse_mvm_demasz_consumption_headroom_text(text, provenance=cleared(text)).records[0]
        result = assess_incremental_demand(
            row,
            incremental_demand_mw=10.0,
            demand_region_id=row.region_id,
            demand_region_scheme=row.region_scheme,
            demand_evidence_status="DER",
            demand_source_refs=("SRC-B08-EXAMPLE",),
        )
        self.assertEqual(2.5, result.remaining_headroom_mw)
        self.assertEqual(0.0, result.overload_mw)
        self.assertEqual("DER", result.evidence_status)
        self.assertEqual("MGT_REQUIRED", result.connection_authority)

    def test_q_headroom_propagates_q(self):
        row = parse_mvm_demasz_consumption_headroom_text(normalized_text(), provenance=BASE_PROVENANCE).records[0]
        result = assess_incremental_demand(
            row,
            incremental_demand_mw=5.0,
            demand_region_id=row.region_id,
            demand_region_scheme=row.region_scheme,
            demand_evidence_status="DER",
            demand_source_refs=("SRC-B08-EXAMPLE",),
        )
        self.assertEqual("Q", result.evidence_status)
        self.assertIsNone(result.remaining_headroom_mw)
        self.assertIsNone(result.overload_mw)

    def test_scn_demand_stays_scn_when_headroom_is_der(self):
        text = normalized_text()
        row = parse_mvm_demasz_consumption_headroom_text(text, provenance=cleared(text)).records[0]
        result = assess_incremental_demand(
            row,
            incremental_demand_mw=20.0,
            demand_region_id=row.region_id,
            demand_region_scheme=row.region_scheme,
            demand_evidence_status="SCN",
            demand_source_refs=("SRC-SCN-DEMAND",),
        )
        self.assertEqual("SCN", result.evidence_status)
        self.assertEqual(0.0, result.remaining_headroom_mw)
        self.assertEqual(7.5, result.overload_mw)


if __name__ == "__main__":
    unittest.main()
