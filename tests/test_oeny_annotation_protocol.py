from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.validate_oeny_annotations import validate_batch, validate_record  # noqa: E402


def annotation(role: str, annotation_id: str, rater: str) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "annotation_id": annotation_id,
        "document_id": "DOC-0123456789ABCDEF0123456789ABCDEF",
        "redacted_source_sha256": "a" * 64,
        "annotation_role": role,
        "annotator_id": rater,
        "emitter_status": "OBS",
        "emitter_types": ["RADIATOR"],
        "emitter_evidence": ["TABLE_EXPLICIT"],
        "temperature_status": "OBS",
        "supply_temperature_c": 55,
        "return_temperature_c": 45,
        "temperature_basis": "DESIGN_EXPLICIT",
        "page_references": [
            {"page": 3, "evidence_kind": "EMITTER_AND_TEMPERATURE"}
        ],
        "review_flags": [],
        "pii_check": "PASS",
        "adjudication_of": [],
    }


class OenyAnnotationProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.first = annotation("ANNOTATOR_A", "ANN-AAAAAAAAAAAAAAAA", "RATER-ALFA")
        self.second = annotation("ANNOTATOR_B", "ANN-BBBBBBBBBBBBBBBB", "RATER-BETA")

    def test_matching_double_blind_pair_is_valid(self) -> None:
        self.assertEqual([], validate_record(self.first))
        self.assertEqual([], validate_record(self.second))
        self.assertEqual([], validate_batch([self.first, self.second]))

    def test_json_schema_and_validator_require_the_same_top_level_fields(self) -> None:
        schema = json.loads(
            (ROOT / "schemas" / "oeny_heat_emitter_annotation.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(set(self.first), set(schema["required"]))
        self.assertFalse(schema["additionalProperties"])

    def test_disagreement_requires_independent_adjudicator(self) -> None:
        self.second["emitter_types"] = ["FLOOR_HEATING"]
        errors = validate_batch([self.first, self.second])
        self.assertTrue(any("disagreement requires" in error for error in errors))

        adjudicator = copy.deepcopy(self.second)
        adjudicator.update(
            {
                "annotation_id": "ANN-CCCCCCCCCCCCCCCC",
                "annotation_role": "ADJUDICATOR",
                "annotator_id": "RATER-GAMMA",
                "adjudication_of": [
                    "ANN-AAAAAAAAAAAAAAAA",
                    "ANN-BBBBBBBBBBBBBBBB",
                ],
            }
        )
        self.assertEqual([], validate_record(adjudicator))
        self.assertEqual([], validate_batch([self.first, self.second, adjudicator]))

    def test_direct_identifier_fields_are_rejected(self) -> None:
        self.first["address"] = "1111 Budapest"
        errors = validate_record(self.first)
        self.assertTrue(any("prohibited direct-identifier key" in error for error in errors))
        self.assertTrue(any("unsupported fields" in error for error in errors))

    def test_pii_check_fails_closed(self) -> None:
        self.first["pii_check"] = "FAIL"
        self.assertTrue(any("must be PASS" in error for error in validate_record(self.first)))

    def test_reference_temperature_is_not_observation(self) -> None:
        self.first.update(
            {
                "temperature_status": "Q",
                "supply_temperature_c": None,
                "return_temperature_c": None,
                "temperature_basis": "REFERENCE_ASSUMPTION",
                "page_references": [{"page": 2, "evidence_kind": "EMITTER"}],
            }
        )
        self.assertEqual([], validate_record(self.first))

    def test_partial_or_reversed_temperature_pair_is_rejected(self) -> None:
        self.first["return_temperature_c"] = None
        self.assertTrue(any("must form a pair" in error for error in validate_record(self.first)))
        self.first["return_temperature_c"] = 60
        self.assertTrue(any("must exceed return" in error for error in validate_record(self.first)))

    def test_unknown_emitter_cannot_be_observed_or_mixed(self) -> None:
        self.first["emitter_types"] = ["NOT_STATED", "RADIATOR"]
        errors = validate_record(self.first)
        self.assertTrue(any("must stand alone" in error for error in errors))
        self.assertTrue(any("cannot be OBS" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
