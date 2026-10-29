"""Current executable sources use LF; evidence byte pins remain exact."""
from pathlib import Path
import unittest
from unittest.mock import patch

from modules.B07 import shared_use_schedule_contract as shared


ROOT = Path(__file__).resolve().parents[1]


class RepositoryLFContractTests(unittest.TestCase):
    def test_current_python_source_roots_use_only_lf(self):
        for area in ("modules", "tools", "tests"):
            paths = sorted((ROOT / area).rglob("*.py"))
            self.assertTrue(paths, area + " source root must not be empty")
            for path in paths:
                with self.subTest(path=path.relative_to(ROOT).as_posix()):
                    self.assertNotIn(b"\r", path.read_bytes())

    def test_current_shared_use_manifest_uses_only_lf(self):
        path = ROOT / "registry/b07_shared_use_schedule_contract.json"
        self.assertNotIn(b"\r", path.read_bytes())

    def test_shared_loader_rejects_changed_raw_dependency_bytes(self):
        target = (ROOT / "modules/B07/discharge_equivalent_reference.py").resolve()
        original_read_bytes = Path.read_bytes
        before = original_read_bytes(target)

        def changed_read_bytes(path):
            raw = original_read_bytes(path)
            if path.resolve() == target:
                return raw + b"\n# TEST_ONLY dependency-byte mutation\n"
            return raw

        with patch.object(Path, "read_bytes", changed_read_bytes):
            with self.assertRaisesRegex(
                shared.SharedUseError, "shared-use native dependency bytes changed"
            ):
                shared.load_shared_use_contract()

        self.assertEqual(original_read_bytes(target), before)
        shared.load_shared_use_contract()


if __name__ == "__main__":
    unittest.main()
