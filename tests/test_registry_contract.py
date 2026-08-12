from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.validate_registry import QUESTION_ID_PATTERN, read_csv, validate  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
