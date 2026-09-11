from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path
import unittest

from modules.B10.mvm_public_data_confirmation import (
    DSO_DISTRIBUTION_TERRITORY,
    EXPECTED_OPERATORS,
    INFORMATIVE,
    OPERATING_LICENCE_AND_BUSINESS_RULES,
    PRIVATE_ARCHIVE_ONLY,
    PUBLIC_DATA_CONFIRMED,
    QUALIFIED_PUBLIC_DATA_CONFIRMATION,
    MvmPublicDataConfirmation,
    MvmPublicDataConfirmationError,
    confirmation_grants_exact_boundary_geometry,
    confirmation_grants_model_admission,
    confirmation_grants_reuse_permission,
    validate_mvm_public_data_confirmation,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "dso_source_public_data_confirmations.csv"
SOURCE_PACK = ROOT / "docs" / "source_packs" / "P66_B10_MVM_DSO_TERRITORY_PUBLIC_DATA_CONFIRMATION.md"
EXPECTED_SHA256 = "bb38bdd2139ee92411111abcbdbafddc1e524321bc91a4708c96a34f0278f3f1"


class TestB10P66MvmPublicDataConfirmation(unittest.TestCase):
    def _confirmation(self) -> MvmPublicDataConfirmation:
        return MvmPublicDataConfirmation(
            confirmation_id="CONF-B10-MVM-DSO-TERRITORY-PUBLIC-20260911",
            covered_operator_ids=EXPECTED_OPERATORS,
            issuer="MVM Ügyfélkapcsolati Kft.",
            request_date="2026-09-09",
            response_date="2026-09-11",
            docket_id="EM0140-15118-1/2026",
            data_scope=DSO_DISTRIBUTION_TERRITORY,
            public_data_status=PUBLIC_DATA_CONFIRMED,
            referred_source_family=OPERATING_LICENCE_AND_BUSINESS_RULES,
            publication_character=INFORMATIVE,
            private_evidence_storage=PRIVATE_ARCHIVE_ONLY,
            private_evidence_sha256=EXPECTED_SHA256,
        )

    def test_exact_bounded_confirmation_qualifies(self) -> None:
        self.assertEqual(
            QUALIFIED_PUBLIC_DATA_CONFIRMATION,
            validate_mvm_public_data_confirmation(self._confirmation()),
        )

    def test_operator_scope_is_exactly_emasz_and_demasz(self) -> None:
        with self.assertRaisesRegex(MvmPublicDataConfirmationError, "OPERATOR_SCOPE_MISMATCH"):
            validate_mvm_public_data_confirmation(
                replace(self._confirmation(), covered_operator_ids=frozenset({"MVM_EMASZ"}))
            )

    def test_public_data_status_is_not_explicit_reuse_permission(self) -> None:
        confirmation = self._confirmation()
        self.assertFalse(confirmation_grants_reuse_permission(confirmation))
        with self.assertRaisesRegex(
            MvmPublicDataConfirmationError,
            "PUBLIC_DATA_IS_NOT_EXPLICIT_REUSE_PERMISSION",
        ):
            validate_mvm_public_data_confirmation(
                replace(confirmation, explicit_reuse_permission_claimed=True)
            )

    def test_informative_publication_is_not_exact_boundary_geometry(self) -> None:
        confirmation = self._confirmation()
        self.assertFalse(confirmation_grants_exact_boundary_geometry(confirmation))
        with self.assertRaisesRegex(
            MvmPublicDataConfirmationError,
            "PUBLIC_TERRITORY_DATA_IS_NOT_EXACT_BOUNDARY_GEOMETRY",
        ):
            validate_mvm_public_data_confirmation(
                replace(confirmation, exact_boundary_geometry_claimed=True)
            )

    def test_public_status_does_not_mint_truth_completeness_or_model_admission(self) -> None:
        confirmation = self._confirmation()
        self.assertFalse(confirmation_grants_model_admission(confirmation))
        error_by_field = {
            "source_truth_authority_claimed": "PUBLIC_STATUS_IS_NOT_SOURCE_TRUTH_AUTHORITY",
            "completeness_authority_claimed": "PUBLIC_STATUS_IS_NOT_COMPLETENESS_AUTHORITY",
            "model_admission_claimed": "PUBLIC_STATUS_IS_NOT_MODEL_ADMISSION",
        }
        for field, error in error_by_field.items():
            with self.subTest(field=field):
                with self.assertRaisesRegex(MvmPublicDataConfirmationError, error):
                    validate_mvm_public_data_confirmation(
                        replace(confirmation, **{field: True})
                    )

    def test_private_artifact_commit_flags_fail_closed(self) -> None:
        confirmation = self._confirmation()
        error_by_field = {
            "private_evidence_committed": "PRIVATE_EVIDENCE_MUST_NOT_BE_COMMITTED",
            "raw_correspondence_committed": "RAW_CORRESPONDENCE_MUST_NOT_BE_COMMITTED",
            "personal_data_committed": "PERSONAL_DATA_MUST_NOT_BE_COMMITTED",
            "source_binary_committed": "PRIVATE_SOURCE_BINARY_MUST_NOT_BE_COMMITTED",
        }
        for field, error in error_by_field.items():
            with self.subTest(field=field):
                with self.assertRaisesRegex(MvmPublicDataConfirmationError, error):
                    validate_mvm_public_data_confirmation(
                        replace(confirmation, **{field: True})
                    )

    def test_private_storage_and_hash_are_fail_closed(self) -> None:
        with self.assertRaisesRegex(
            MvmPublicDataConfirmationError,
            "PRIVATE_EVIDENCE_STORAGE_NOT_PRIVATE",
        ):
            validate_mvm_public_data_confirmation(
                replace(self._confirmation(), private_evidence_storage="PUBLIC_REPOSITORY")
            )
        with self.assertRaisesRegex(
            MvmPublicDataConfirmationError,
            "INVALID_PRIVATE_EVIDENCE_SHA256",
        ):
            validate_mvm_public_data_confirmation(
                replace(self._confirmation(), private_evidence_sha256="abc")
            )

    def test_scope_source_family_and_publication_character_are_exact(self) -> None:
        cases = (
            ("data_scope", "ALL_MVM_DATA", "PUBLIC_DATA_SCOPE_OVERREACH"),
            ("referred_source_family", "ANY_PUBLIC_PAGE", "SOURCE_FAMILY_MISMATCH"),
            ("publication_character", "BINDING_EXACT_GEOMETRY", "PUBLICATION_CHARACTER_MISMATCH"),
        )
        for field, value, error in cases:
            with self.subTest(field=field):
                with self.assertRaisesRegex(MvmPublicDataConfirmationError, error):
                    validate_mvm_public_data_confirmation(
                        replace(self._confirmation(), **{field: value})
                    )

    def test_response_cannot_precede_request(self) -> None:
        with self.assertRaisesRegex(MvmPublicDataConfirmationError, "RESPONSE_PRECEDES_REQUEST"):
            validate_mvm_public_data_confirmation(
                replace(self._confirmation(), response_date="2026-09-08")
            )

    def test_registry_contains_one_exact_non_promoting_confirmation(self) -> None:
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("MVM_EMASZ;MVM_DEMASZ", row["covered_operator_ids"])
        self.assertEqual("PUBLIC_DATA_CONFIRMED", row["public_data_status"])
        self.assertEqual("OPERATING_LICENCE_AND_BUSINESS_RULES", row["referred_source_family"])
        self.assertEqual("INFORMATIVE", row["publication_character"])
        self.assertEqual(EXPECTED_SHA256, row["private_evidence_sha256"])
        for field in (
            "private_evidence_committed",
            "raw_correspondence_committed",
            "personal_data_committed",
            "source_binary_committed",
            "explicit_reuse_permission_claimed",
            "exact_boundary_geometry_claimed",
            "source_truth_authority_claimed",
            "completeness_authority_claimed",
            "model_admission_claimed",
        ):
            self.assertEqual("NO", row[field])
        self.assertEqual("QUALIFIED_PUBLIC_DATA_CONFIRMATION", row["authority_result"])

    def test_public_repo_contains_no_private_binary_or_locator(self) -> None:
        combined = REGISTRY.read_text(encoding="utf-8") + SOURCE_PACK.read_text(encoding="utf-8")
        self.assertNotIn("/mnt/data/", combined)
        self.assertNotIn("C:\\Users\\", combined)
        self.assertNotIn(".pdf", combined.lower())

    def test_source_pack_preserves_non_equivalence_boundaries(self) -> None:
        text = SOURCE_PACK.read_text(encoding="utf-8")
        self.assertIn("PUBLIC DATA != EXPLICIT REUSE LICENCE", text)
        self.assertIn("PUBLIC DISTRIBUTION-TERRITORY DATA != EXACT CURRENT BOUNDARY GEOMETRY", text)
        self.assertIn("PUBLIC STATUS != DSO_SUBSTATION MAPPING", text)
        self.assertIn("PUBLIC STATUS != HOSTING-CAPACITY AUTHORITY", text)
        self.assertIn("does not by itself alter B10 readiness", text)


if __name__ == "__main__":
    unittest.main()
