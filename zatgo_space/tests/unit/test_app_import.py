"""Smoke tests proving the app package imports cleanly."""

from __future__ import annotations

import unittest

import frappe


class TestAppImport(unittest.TestCase):
    """Basic install / import checks."""

    def test_app_installed(self) -> None:
        installed = frappe.get_installed_apps()
        self.assertIn("zatgo_space", installed)

    def test_version_defined(self) -> None:
        from zatgo_space import __version__

        self.assertTrue(__version__)
