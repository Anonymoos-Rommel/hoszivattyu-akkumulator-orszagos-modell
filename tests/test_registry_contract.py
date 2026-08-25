from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.validate_registry import (  # noqa: E402
    ALLOWED_RELIABILITY,
    DATASET_ID_PATTERN,
    DIMENSION_ID_PATTERN,
    EXPECTED_HEADERS,
    QUESTION_ID_PATTERN,
    SOURCE_VERSION_PATTERN,
    read_csv,
    validate,
    validate_b01_artifacts,
    validate_b07_source_rows,
)


class RegistryContractTests(unittest.TestCase):
    def test_registry_contract_is_valid(self) -> None:
        self.assertEqual([], validate())

    def test_b07_validator_rejects_misaligned_source_row(self) -> None:
        headers = EXPECTED_HEADERS["battery_sources.csv"]
        row = {field: "valid" for field in headers}
        row["reliability"] = "HIGH"
        row[None] = ["shifted notes"]
        errors: list[str] = []
        validate_b07_source_rows(errors, headers, [row])
        self.assertTrue(any("misaligned CSV row" in error for error in errors))

    def test_b07_validator_rejects_invalid_reliability(self) -> None:
        headers = EXPECTED_HEADERS["battery_sources.csv"]
        row = {field: "valid" for field in headers}
        row["reliability"] = "Independent certified performance report"
        errors: list[str] = []
        validate_b07_source_rows(errors, headers, [row])
        self.assertTrue(any("invalid B07 source reliability" in error for error in errors))
        self.assertNotIn(row["reliability"], ALLOWED_RELIABILITY)

    def test_b01_validator_rejects_scn_fixture_observed_transition(self) -> None:
        from tools import validate_registry

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "registry").mkdir()
            (root / "data" / "fixtures").mkdir(parents=True)
            model = ROOT / "registry" / "household_state_model.json"
            fixture = ROOT / "data" / "fixtures" / "b01_state_stock_scn.json"
            (root / "registry" / model.name).write_text(model.read_text(encoding="utf-8"), encoding="utf-8")
            payload = json.loads(fixture.read_text(encoding="utf-8"))
            payload["households"][1]["transition_evidence"][0]["status"] = "OBS"
            (root / "data" / "fixtures" / fixture.name).write_text(json.dumps(payload), encoding="utf-8")
            errors: list[str] = []
            with patch.object(validate_registry, "ROOT", root), patch.object(validate_registry, "REGISTRY", root / "registry"):
                validate_b01_artifacts(errors)
            self.assertTrue(any("SCN transition evidence is not SCN" in error for error in errors))

    def test_b01_validator_rejects_noncanonical_candidate_gate(self) -> None:
        from tools import validate_registry

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "registry").mkdir()
            (root / "data" / "fixtures").mkdir(parents=True)
            model = ROOT / "registry" / "household_state_model.json"
            fixture = ROOT / "data" / "fixtures" / "b01_state_stock_scn.json"
            (root / "registry" / model.name).write_text(model.read_text(encoding="utf-8"), encoding="utf-8")
            payload = json.loads(fixture.read_text(encoding="utf-8"))
            payload["candidates"][1]["required_gate"] = "audit_complete"
            (root / "data" / "fixtures" / fixture.name).write_text(json.dumps(payload), encoding="utf-8")
            errors: list[str] = []
            with patch.object(validate_registry, "ROOT", root), patch.object(validate_registry, "REGISTRY", root / "registry"):
                validate_b01_artifacts(errors)
            self.assertTrue(any("candidate gate is not canonical" in error for error in errors))

    def test_internal_source_documents_are_gitignored(self) -> None:
        ignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(
            "/Hoszivattyu_akkumulator_program_Codex_kutatasi_prompt_V1.1.docx",
            ignore_text,
        )
        self.assertIn(
            "/Hoszivattyu_akkumulator_program_javaslat.docx",
            ignore_text,
        )

    def test_question_ids_are_module_scoped(self) -> None:
        _, rows = read_csv(ROOT / "registry" / "open_questions.csv")
        self.assertGreater(len(rows), 0)
        for row in rows:
            match = QUESTION_ID_PATTERN.fullmatch(row["question_id"])
            self.assertIsNotNone(match)
            self.assertEqual(row["module_id"], match.group(1))

    def test_source_pack_does_not_claim_validated_prices(self) -> None:
        source_pack = (ROOT / "docs" / "source_packs" / "P1A_B01_B04.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("számszerű modellkapu nincs lezárva", source_pack)
        self.assertIn("egyikhez sincs numerikus érték", source_pack)

    def test_b02_dataset_contract_pins_expected_ksh_flows(self) -> None:
        _, rows = read_csv(ROOT / "registry" / "datasets.csv")
        flows = {
            row["dataflow_id"]
            for row in rows
            if row["access_method"] == "KSH_CENSUS_API"
        }
        self.assertEqual({"WBL010", "WBL011", "WBL016", "WBL017"}, flows)
        for row in rows:
            self.assertIsNotNone(DATASET_ID_PATTERN.fullmatch(row["dataset_id"]))
            self.assertIsNotNone(SOURCE_VERSION_PATTERN.fullmatch(row["source_version"]))
            if row["access_method"] == "KSH_CENSUS_API":
                self.assertIn(
                    f"/{row['dataflow_id']}/{row['source_version']}",
                    row["data_endpoint"],
                )
        housing_survey = next(
            row for row in rows if row["dataset_id"] == "DATA-B02-KSH-HOUSING-SURVEY-2015"
        )
        self.assertEqual("PDF_TABLE", housing_survey["access_method"])
        self.assertEqual("Y2015", housing_survey["source_version"])

    def test_b02_contracted_dimensions_have_source_datasets(self) -> None:
        _, rows = read_csv(ROOT / "registry" / "archetype_dimensions.csv")
        for row in rows:
            self.assertIsNotNone(DIMENSION_ID_PATTERN.fullmatch(row["dimension_id"]))
            if row["status"] == "CONTRACTED":
                self.assertTrue(row["source_dataset_ids"])

    def test_b02_contract_keeps_baseline_separate_from_eligibility(self) -> None:
        contract = (ROOT / "modules" / "B02" / "data_contract.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("nem a technikailag alkalmas célállomány", contract)
        self.assertIn("HOSZIV=9", contract)
        self.assertIn("nem azonos a `HOSZIV=0`", contract)

    def test_p1e_oeny_audit_does_not_promote_document_fields_to_observations(self) -> None:
        audit = (
            ROOT / "docs" / "source_packs" / "P1E_B02_OENY_HEAT_EMITTER_FIELD_AUDIT.md"
        ).read_text(encoding="utf-8")
        self.assertIn("közvetlen országos hőleadó-adatmező nem igazolt", audit)
        self.assertIn("nem tartalmaz külön mezőt", audit)
        self.assertIn("dokumentumszintű adatjelölt", audit)
        self.assertIn("nincs országos radiátor-", audit)

    def test_p1e_heat_emitter_variables_remain_questions(self) -> None:
        _, rows = read_csv(ROOT / "registry" / "variables.csv")
        by_id = {row["variable_id"]: row for row in rows}
        for variable_id in (
            "VAR-B02-HEAT-EMITTER",
            "VAR-B02-HEATING-WATER-TEMPERATURE",
        ):
            self.assertEqual("Q", by_id[variable_id]["status"])
            self.assertEqual("", by_id[variable_id]["default_value"])

    def test_p1e_oeny_sources_are_version_pinned(self) -> None:
        _, rows = read_csv(ROOT / "registry" / "sources.csv")
        by_id = {row["source_id"]: row for row in rows}
        for source_id in (
            "SRC-B02-OENY-SCHEMA-DICTIONARY-2026",
            "SRC-B02-OENY-VALIDATION-2026",
            "SRC-B02-OENY-FULL-EXAMPLE-2026",
        ):
            row = by_id[source_id]
            self.assertIn("v3.0.14801", row["url"])
            self.assertEqual(64, len(row["local_snapshot_sha256"]))

    def test_p1f_request_remains_human_gated_and_data_minimised(self) -> None:
        request = (
            ROOT / "docs" / "data_requests" / "P1F_OENY_DATA_REQUEST_DRAFT.md"
        ).read_text(encoding="utf-8")
        protocol = (
            ROOT / "docs" / "protocols" / "P1F_OENY_SAMPLE_PROCESSING_PROTOCOL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("KÜLDÉSRE NEM JÓVÁHAGYOTT TERVEZET", request)
        self.assertIn("Ilyen dokumentumot e levél alapján még nem kérünk", request)
        self.assertIn("személyes adat", request)
        self.assertIn("két, egymástól független annotátor", protocol)
        self.assertIn("Egyetlen PII-jelzés is `BLOCKED`", protocol)
        ignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("/data/quarantine/", ignore_text)
        self.assertIn("/data/restricted/", ignore_text)


if __name__ == "__main__":
    unittest.main()
