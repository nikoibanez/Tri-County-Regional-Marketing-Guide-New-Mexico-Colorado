from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_directory_quality import duplicate_groups, normalize_name  # noqa: E402
from audit_internal_links import audit_site  # noqa: E402


class DirectoryQualityTests(unittest.TestCase):
    def test_normalize_name_handles_punctuation_and_suffix_spacing(self) -> None:
        self.assertEqual(normalize_name("Angel's Glow & Oxygen-Bar"), "angel s glow and oxygen bar")

    def test_duplicate_groups_respects_place(self) -> None:
        rows = [
            {"name": "Example Studio", "town": "Raton", "county": "Colfax"},
            {"name": "Example Studio", "town": "Raton", "county": "Colfax"},
            {"name": "Example Studio", "town": "Trinidad", "county": "Las Animas"},
        ]
        self.assertEqual(len(duplicate_groups(rows, "name")), 1)


class InternalLinkTests(unittest.TestCase):
    def test_audit_site_detects_missing_target(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            site = Path(folder)
            (site / "index.html").write_text('<html><body><a href="missing/">Missing</a></body></html>', encoding="utf-8")
            result = audit_site(site)
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["summary"]["missing_targets"], 1)

    def test_audit_site_accepts_valid_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            site = Path(folder)
            (site / "index.html").write_text('<html><body><a href="#target">Jump</a><div id="target"></div></body></html>', encoding="utf-8")
            result = audit_site(site)
            self.assertEqual(result["status"], "pass")


if __name__ == "__main__":
    unittest.main()
