"""Cross-platform regression for the Windows WinError 32 XLSX cleanup bug.

The workbook loader is observed so this test fails even on Linux if the
read-only workbook remains open when its owning temp directory exits.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import openpyxl
import test_provider_studio_v510 as report_tests


class _WorkbookLifetimeObserver:
    def __init__(self, workbook, path):
        self._workbook = workbook
        self.path = Path(path).resolve()
        self.closed = False

    def close(self):
        try:
            self._workbook.close()
        finally:
            self.closed = True

    def __getitem__(self, key):
        return self._workbook[key]

    def __getattr__(self, name):
        return getattr(self._workbook, name)


class WindowsXlsxCleanupTests(unittest.TestCase):
    def test_provider_excel_workbook_closed_before_temp_dir_cleanup(self):
        real_loader = openpyxl.load_workbook
        real_tmp_dir = tempfile.TemporaryDirectory
        workbooks = []
        tempdirs = []

        def observed_load_workbook(filename, *args, **kwargs):
            result = real_loader(filename, *args, **kwargs)
            observer = _WorkbookLifetimeObserver(result, filename)
            workbooks.append(observer)
            return observer

        class ObservedTempDirectory:
            def __init__(self, *args, **kwargs):
                self._inner = real_tmp_dir(*args, **kwargs)
                self.root = None

            def __enter__(self):
                self.root = Path(self._inner.__enter__()).resolve()
                tempdirs.append(self.root)
                return str(self.root)

            def __exit__(self, exc_type, exc_value, exc_tb):
                # On Windows, deleting these open .xlsx files raises WinError 32.
                # Catch the same error before actually deleting the directory,
                # so the check is reproducible on Linux too.
                still_open = [book for book in workbooks
                              if self.root in book.path.parents and not book.closed]
                try:
                    self._inner.__exit__(exc_type, exc_value, exc_tb)
                finally:
                    if still_open:
                        raise AssertionError(
                            f"Unclosed XLSX before temp directory cleanup: "
                            f"{[str(book.path) for book in still_open]}")

        with patch.object(openpyxl, 'load_workbook', observed_load_workbook), \
             patch.object(tempfile, 'TemporaryDirectory', ObservedTempDirectory):
            test = report_tests.ProviderStudioV510Tests(
                'test_excel_provider_report_exports_best_destination_and_trade_counts')
            result = unittest.TestResult()
            test.run(result)
        self.assertTrue(result.wasSuccessful(),
                        f"errors={result.errors!r}; failures={result.failures!r}")
        self.assertTrue(workbooks, 'The test never opened a workbook')
        self.assertTrue(tempdirs)
        self.assertTrue(all(book.closed for book in workbooks))


if __name__ == '__main__':
    unittest.main()
