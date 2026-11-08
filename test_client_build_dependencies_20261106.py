"""Offline contract checks for the Windows client build dependency preflight.

These check script ordering and manifest consistency, NOT a Windows installer run.
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class ClientBuildDependencyContractTests(unittest.TestCase):
    def test_cryptography_and_requests_declared_in_runtime_dependencies(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("cryptography>=44,<47", requirements)
        self.assertIn("requests>=2.31,<3", requirements)

    def test_build_manifest_keeps_base_requirements(self):
        build = (ROOT / "requirements-build.txt").read_text(encoding="utf-8")
        self.assertIn("-r requirements.txt", build)
        self.assertIn("pyinstaller>=6.22.0", build)

    def test_preflight_before_regression_tests_and_same_venv_python(self):
        build = (ROOT / "BUILD-CLIENT-INSTALLER-CORE.bat").read_text(encoding="utf-8")
        self.assertLess(build.index('call "%~dp0PREPARE-CLIENT-BUILD-ENV.bat"'),
                        build.index('python -m unittest discover'))
        self.assertLess(build.index('set "PATH=%BUILD_ENV_DIR%\\Scripts;%PATH%"'),
                        build.index('python -m unittest discover'))
        self.assertIn('if errorlevel 1 goto build_dependencies_fail', build)

    def test_preflight_fails_closed_when_install_or_import_fails(self):
        preflight = (ROOT / "PREPARE-CLIENT-BUILD-ENV.bat").read_text(encoding="utf-8")
        self.assertIn('"%BUILD_ENV_PY%" -m pip install', preflight)
        self.assertIn('import cryptography, requests, telethon', preflight)
        self.assertIn('if errorlevel 1 goto pip_failed', preflight)
        self.assertIn('exit /b 24', preflight)
        self.assertIn('exit /b 21', preflight)

    def test_exe_build_uses_same_manifest(self):
        exe = (ROOT / "BUILD-EXE.bat").read_text(encoding="utf-8")
        self.assertIn('-r "requirements-build.txt"', exe)
        self.assertIn('import cryptography, requests', exe)


if __name__ == "__main__":
    unittest.main()
