"""Source contract tests for the official EQ brand icon in the Windows build."""
from pathlib import Path
from zipfile import ZipFile
import struct
import unittest

ROOT = Path(__file__).resolve().parent


class BrandIconInstallerTests(unittest.TestCase):
    def test_official_icon_is_multisize_windows_ico(self):
        data = (ROOT / "edgequant-icon.ico").read_bytes()
        self.assertGreater(len(data), 1024)
        reserved, image_type, count = struct.unpack_from("<HHH", data)
        self.assertEqual((reserved, image_type), (0, 1))
        self.assertGreaterEqual(count, 3)

    def test_exe_and_payload_bundle_icon(self):
        text = (ROOT / "BUILD-EXE.bat").read_text(encoding="utf-8")
        self.assertIn(' --icon "edgequant-icon.ico" ^', text)
        self.assertIn('--add-data "edgequant-icon.ico;."', text)
        self.assertIn('copy /y "edgequant-icon.ico"      "dist\\EdgeQuantSentinel"', text)
        self.assertIn('if not exist "dist\\EdgeQuantSentinel\\edgequant-icon.ico" goto fail', text)

    def test_installer_shortcut_icons_and_autocreate(self):
        text = (ROOT / "EdgeQuantSentinel-Client.iss").read_text(encoding="utf-8")
        self.assertIn('SetupIconFile=edgequant-icon.ico', text)
        lines = [line for line in text.splitlines() if line.startswith('Name: "{auto')]
        self.assertEqual(len(lines), 2)
        for line in lines:
            self.assertIn('Filename: "{app}\\EdgeQuantSentinel.exe"', line)
            self.assertIn('IconFilename: "{app}\\edgequant-icon.ico"', line)
            self.assertNotIn('Tasks:', line)
        self.assertNotIn('Flags: unchecked', text)


if __name__ == "__main__":
    unittest.main()
