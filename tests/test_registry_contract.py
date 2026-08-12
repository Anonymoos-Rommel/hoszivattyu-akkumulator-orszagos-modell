from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.validate_registry import (  # noqa: E402
    API_VERSION_PATTERN,
    DATASET_ID_PATTERN,
    DIMENSION_ID_PATTERN,
    QUESTION_ID_PATTERN,
    read_csv,
    validate,
)


class RegistryContractTests(unittest.TestCase):
    def test_registry_contract_is_valid(self) -> None:
        self.assertEqual([], validate())

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
        flows = {row["dataflow_id"] for row in rows if row["module_id"] == "B02"}
        self.assertEqual({"WBL010", "WBL011", "WBL016", "WBL017"}, flows)
        for row in rows:
            self.assertIsNotNone(DATASET_ID_PATTERN.fullmatch(row["dataset_id"]))
            self.assertIsNotNone(API_VERSION_PATTERN.fullmatch(row["api_version"]))
            self.assertIn(f"/{row['dataflow_id']}/{row['api_version']}", row["data_endpoint"])

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


if __name__ == "__main__":
    unittest.main()
