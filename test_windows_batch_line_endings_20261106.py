"""Build gate: verify Windows CMD batch scripts have CRLF and navigable labels."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent

class WindowsBatchLineEndingsTests(unittest.TestCase):
    def test_batch_files_use_crlf_without_stray_lf(self):
        paths = sorted(ROOT.glob("*.bat"))
        self.assertGreaterEqual(len(paths), 3)
        for path in paths:
            with self.subTest(path=path.name):
                contents = path.read_bytes()
                self.assertIn(b"\r\n", contents)
                self.assertNotIn(b"\n", contents.replace(b"\r\n", b""))
                self.assertNotIn(b"\r", contents.replace(b"\r\n", b""))

    def test_exe_builder_goto_build_target(self):
        content = (ROOT / "BUILD-EXE.bat").read_bytes().decode("utf-8-sig").lower()
        self.assertIn("goto build\r\n", content)
        self.assertIn("\r\n:build\r\n", content)

    def test_core_builder_goto_fail_targets(self):
        content = (ROOT / "BUILD-CLIENT-INSTALLER-CORE.bat").read_bytes().decode("utf-8-sig").lower()
        self.assertIn("\r\n:fail_build\r\n", content)
        self.assertIn("\r\n:release_tests_fail\r\n", content)

if __name__ == "__main__":
    unittest.main()
