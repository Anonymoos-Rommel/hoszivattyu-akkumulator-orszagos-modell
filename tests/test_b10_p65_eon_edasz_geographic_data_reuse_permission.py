from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path
import unittest

from modules.B10.source_reuse_permission import (
    OPERATING_LICENCE_GEOGRAPHIC_DATA,
    PRIVATE_ARCHIVE_ONLY,
    QUALIFIED_SOURCE_REUSE_PERMISSION,
    USE_ALLOWED,
    SourceReusePermission,
    SourceReusePermissionError,
    permission_grants_model_admission,
    permission_grants_source_truth_authority,
    validate_source_reuse_permission,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "dso_source_reuse_permissions.csv"
SOURCE_PACK = ROOT / "docs" / "source_packs" / "P65_B10_EON_EDASZ_GEOGRAPHIC_DATA_REUSE_PERMISSION.md"
EXPECTED_SHA256 = "9cb9a07e9cf317db56700072850f09e916f5c3817b5b9babc467e36ba3fa7771"


class TestB10P65EonEdaszGeographicDataReusePermission(unittest.TestCase):
    def _permission(self) -> SourceReusePermission:
        return SourceReusePermission(
            permission_id="PERM-B10-EON-EDASZ-GEODATA-20260909",
            operator_id="EON_EDASZ",
            issuer="E.ON Ügyfélszolgálati Kft.",
            represented_entity="E.ON Észak-dunántúli Áramhálózati Zrt.",
            request_date="2026-09-03",
            response_date="2026-09-09",
            docket_id="1/02182346-01/2026/1",
            permission_scope=OPERATING_LICENCE_GEOGRAPHIC_DATA,
            permission_decision=USE_ALLOWED,
            private_evidence_storage=PRIVATE_ARCHIVE_ONLY,
            private_evidence_sha256=EXPECTED_SHA256,
        )

    def test_qualified_exact_permission_passes(self) -> None:
        self.assertEqual(
            QUALIFIED_SOURCE_REUSE_PERMISSION,
            validate_source_reuse_permission(self._permission()),
        )

    def test_permission_does_not_mint_source_truth_or_model_admission(self) -> None:
        permission = self._permission()
        self.assertFalse(permission_grants_source_truth_authority(permission))
        self.assertFalse(permission_grants_model_admission(permission))

    def test_scope_expansion_fails_closed(self) -> None:
        with self.assertRaisesRegex(SourceReusePermissionError, "PERMISSION_SCOPE_OVERREACH"):
            validate_source_reuse_permission(
                replace(self._permission(), permission_scope="ALL_EON_DATA")
            )
        with self.assertRaisesRegex(SourceReusePermissionError, "PERMISSION_SCOPE_EXPANSION_FORBIDDEN"):
            validate_source_reuse_permission(
                replace(self._permission(), scope_expansion_allowed=True)
            )

    def test_private_artifact_commit_flags_fail_closed(self) -> None:
        flag_errors = {
            "private_evidence_committed": "PRIVATE_EVIDENCE_MUST_NOT_BE_COMMITTED",
            "raw_correspondence_committed": "RAW_CORRESPONDENCE_MUST_NOT_BE_COMMITTED",
            "personal_data_committed": "PERSONAL_DATA_MUST_NOT_BE_COMMITTED",
            "source_binary_committed": "PRIVATE_SOURCE_BINARY_MUST_NOT_BE_COMMITTED",
        }
        for field, error in flag_errors.items():
            with self.subTest(field=field):
                with self.assertRaisesRegex(SourceReusePermissionError, error):
                    validate_source_reuse_permission(
                        replace(self._permission(), **{field: True})
                    )

    def test_private_storage_must_remain_private(self) -> None:
        with self.assertRaisesRegex(SourceReusePermissionError, "PRIVATE_EVIDENCE_STORAGE_NOT_PRIVATE"):
            validate_source_reuse_permission(
                replace(self._permission(), private_evidence_storage="PUBLIC_REPOSITORY")
            )

    def test_hash_must_be_exact_sha256_shape(self) -> None:
        with self.assertRaisesRegex(SourceReusePermissionError, "INVALID_PRIVATE_EVIDENCE_SHA256"):
            validate_source_reuse_permission(
                replace(self._permission(), private_evidence_sha256="abc")
            )

    def test_response_cannot_precede_request(self) -> None:
        with self.assertRaisesRegex(SourceReusePermissionError, "RESPONSE_PRECEDES_REQUEST"):
            validate_source_reuse_permission(
                replace(self._permission(), response_date="2026-09-02")
            )

    def test_registry_contains_exact_bounded_permission(self) -> None:
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("PERM-B10-EON-EDASZ-GEODATA-20260909", row["permission_id"])
        self.assertEqual("EON_EDASZ", row["operator_id"])
        self.assertEqual("2026-09-03", row["request_date"])
        self.assertEqual("2026-09-09", row["response_date"])
        self.assertEqual("1/02182346-01/2026/1", row["docket_id"])
        self.assertEqual(OPERATING_LICENCE_GEOGRAPHIC_DATA, row["permission_scope"])
        self.assertEqual(USE_ALLOWED, row["permission_decision"])
        self.assertEqual(PRIVATE_ARCHIVE_ONLY, row["private_evidence_storage"])
        self.assertEqual(EXPECTED_SHA256, row["private_evidence_sha256"])
        self.assertEqual("NO", row["private_evidence_committed"])
        self.assertEqual("NO", row["raw_correspondence_committed"])
        self.assertEqual("NO", row["personal_data_committed"])
        self.assertEqual("NO", row["source_binary_committed"])
        self.assertEqual("NO", row["scope_expansion_allowed"])
        self.assertEqual("SRC-B10-EON-EDASZ-M1-CANDIDATE-2025", row["related_public_source_id"])
        self.assertEqual(QUALIFIED_SOURCE_REUSE_PERMISSION, row["authority_result"])

    def test_registry_never_contains_private_file_locator_or_correspondence_body(self) -> None:
        text = REGISTRY.read_text(encoding="utf-8")
        forbidden = (
            "Eon_valasz_20260909_02182346-01-2026.pdf",
            "/mnt/data/",
            "joseph.bakus@outlook.com",
            "Málovics Melinda",
            "Sándor Petra",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, text)

    def test_source_pack_preserves_private_boundary(self) -> None:
        text = SOURCE_PACK.read_text(encoding="utf-8")
        self.assertIn("PRIVATE_ARCHIVE_ONLY", text)
        self.assertIn(EXPECTED_SHA256, text)
        self.assertIn(
            "OPERATING-LICENCE GEOGRAPHIC-DATA PERMISSION != BLANKET PERMISSION FOR ALL M1 CONTENT",
            text,
        )
        self.assertIn("REUSE PERMISSION != SOURCE-TRUTH AUTHORITY", text)
        self.assertIn("No E.ON correspondence file or correspondence text is committed.", text)
        self.assertNotIn("Eon_valasz_20260909_02182346-01-2026.pdf", text)
        self.assertNotIn("/mnt/data/", text)


if __name__ == "__main__":
    unittest.main()
