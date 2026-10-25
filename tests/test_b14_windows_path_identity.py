"""Canonical manifest identities and byte pins on native Windows and POSIX."""
import copy
import csv
import json
from pathlib import Path
import tempfile
import unittest

from modules.B14 import funding_reference as funding


class B14ManifestPathIdentityTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(funding.DATA_PATH.read_text(encoding="utf-8"))
        self.manifest = json.loads(funding.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.completion = json.loads(funding.COMPLETION_PATH.read_text(encoding="utf-8"))
        self.completion_manifest = json.loads(funding.COMPLETION_MANIFEST_PATH.read_text(encoding="utf-8"))
        with funding.CAPS_PATH.open(encoding="utf-8", newline="") as stream:
            self.caps = list(csv.DictReader(stream))
        with funding.CAPS_418_PATH.open(encoding="utf-8", newline="") as stream:
            self.completed_caps = list(csv.DictReader(stream))
        self.temp = tempfile.TemporaryDirectory(prefix="b14-path-identity-")
        self.addCleanup(self.temp.cleanup)

    def invalid_references(self, expected):
        return [None, 1, [], {}, "", "other/" + expected, "/" + expected,
                "C:/" + expected, "C:" + expected, "//server/share/" + expected,
                "file:///" + expected, "https://example.invalid/" + expected,
                "../" + expected, "./" + expected, expected + "/..",
                expected.replace("data/", "data/../data/"),
                expected.replace("/", "\\"), expected.replace("/", "//"),
                expected.replace("/", "%2F"), expected.upper(), expected + " ",
                expected + "\x00", expected + ":alternate-stream",
                expected.rsplit("/", 1)[-1]]

    def test_real_manifests_load_both_dated_stages_with_exact_posix_identities(self):
        self.assertEqual(self.manifest["data_path"], funding.DATA_PATH.relative_to(funding.ROOT).as_posix())
        self.assertEqual(self.manifest["caps_path"], funding.CAPS_PATH.relative_to(funding.ROOT).as_posix())
        self.assertEqual(self.completion_manifest["data_path"], funding.COMPLETION_PATH.relative_to(funding.ROOT).as_posix())
        self.assertEqual(set(self.completion_manifest["historical_input_sha256"]), {
            p.relative_to(funding.ROOT).as_posix()
            for p in (funding.DATA_PATH, funding.CAPS_PATH, funding.MANIFEST_PATH)})
        reference = funding.load_funding_reference()
        for as_of in (funding.AS_OF, funding.COMPLETION_AS_OF):
            row = reference.read_programme(funding.PROGRAMME_417,
                scope=funding.SCOPES[funding.PROGRAMME_417], as_of=as_of,
                claim=funding.DATED_RULE_REFERENCE)
            self.assertEqual(row["as_of"], as_of)
            self.assertTrue(all(x["value"] is None for x in row["unknowns"].values()))

    def test_snapshot_rejects_wrong_data_identity_without_path_normalization(self):
        for invalid in self.invalid_references(self.manifest["data_path"]):
            manifest = copy.deepcopy(self.manifest)
            manifest["data_path"] = invalid
            with self.subTest(path=invalid), self.assertRaisesRegex(funding.FundingReferenceError, "data identity mismatch"):
                funding.validate_snapshot(self.data, self.caps, manifest)

    def test_snapshot_rejects_wrong_caps_identity_without_path_normalization(self):
        for invalid in self.invalid_references(self.manifest["caps_path"]):
            manifest = copy.deepcopy(self.manifest)
            manifest["caps_path"] = invalid
            with self.subTest(path=invalid), self.assertRaisesRegex(funding.FundingReferenceError, "data identity mismatch"):
                funding.validate_snapshot(self.data, self.caps, manifest)

    def test_completion_rejects_wrong_data_or_caps_identity(self):
        for field in ("data_path", "caps_path"):
            for invalid in self.invalid_references(self.completion_manifest[field]):
                manifest = copy.deepcopy(self.completion_manifest)
                manifest[field] = invalid
                with self.subTest(field=field, path=invalid), self.assertRaisesRegex(
                        funding.FundingReferenceError, "completion file identity mismatch"):
                    funding.validate_rule_completion(self.completion, self.completed_caps,
                                                     manifest, self.data, self.manifest)

    def completion_manifest_override(self, manifest):
        path = Path(self.temp.name) / "completion-manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def test_completion_rejects_noncanonical_or_extra_historical_identity_keys(self):
        expected = self.manifest["data_path"]
        for invalid in (expected.replace("/", "\\"), "../" + expected,
                        "C:/" + expected, "other/" + expected):
            manifest = copy.deepcopy(self.completion_manifest)
            manifest["historical_input_sha256"][invalid] = manifest["historical_input_sha256"].pop(expected)
            with self.subTest(path=invalid), self.assertRaisesRegex(
                    funding.FundingReferenceError, "exact historical input identity set required"):
                funding.load_funding_reference(completion_manifest_path=self.completion_manifest_override(manifest))
        manifest = copy.deepcopy(self.completion_manifest)
        manifest["historical_input_sha256"]["extra.json"] = "0" * 64
        with self.assertRaisesRegex(funding.FundingReferenceError, "exact historical input identity set required"):
            funding.load_funding_reference(completion_manifest_path=self.completion_manifest_override(manifest))

    def test_consumed_historical_byte_pin_still_rejects_wrong_digest(self):
        manifest = copy.deepcopy(self.completion_manifest)
        manifest["historical_input_sha256"][self.manifest["data_path"]] = "0" * 64
        with self.assertRaisesRegex(funding.FundingReferenceError, "consumed historical dated evidence changed"):
            funding.load_funding_reference(completion_manifest_path=self.completion_manifest_override(manifest))

    def test_snapshot_data_and_caps_byte_revisions_remain_checked(self):
        for key, source in (("data_path", funding.DATA_PATH), ("caps_path", funding.CAPS_PATH)):
            path = Path(self.temp.name) / source.name
            path.write_bytes(source.read_bytes() + b"\n")
            with self.subTest(input=key), self.assertRaisesRegex(funding.FundingReferenceError, "file revision mismatch"):
                funding.load_funding_reference(**{key: path})

    def test_completion_data_and_caps_byte_revisions_remain_checked(self):
        for key, source in (("completion_path", funding.COMPLETION_PATH), ("caps_418_path", funding.CAPS_418_PATH)):
            path = Path(self.temp.name) / source.name
            path.write_bytes(source.read_bytes() + b"\n")
            with self.subTest(input=key), self.assertRaisesRegex(funding.FundingReferenceError, "completion file revision mismatch"):
                funding.load_funding_reference(**{key: path})


if __name__ == "__main__":
    unittest.main()
