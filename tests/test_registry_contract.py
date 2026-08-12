from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.validate_registry import validate  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
