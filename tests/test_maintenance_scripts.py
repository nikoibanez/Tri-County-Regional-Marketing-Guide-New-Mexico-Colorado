from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools"))

from audit_directory_quality import duplicate_groups, normalize_name  # noqa: E402
from audit_internal_links import audit_site  # noqa: E402
from build_netlify_deep_guide import inferred_listing_type  # noqa: E402
from smoke_test_site import validate_body  # noqa: E402
from sweep_listing_keywords import (  # noqa: E402
    KeywordSignalParser,
    canonical_signal,
    extract_controlled_keywords,
    listing_name_matches_signal,
    primary_source_url,
    select_urls,
)


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

    def test_catering_directory_is_classified_as_food_and_drink(self) -> None:
        row = {
            "resource_name": "Visit Angel Fire Catering and Event-Service Directory",
            "category": "Catering and event-service listing directory",
            "notes": "Useful for food, hospitality, event, and creative-service routing.",
        }
        self.assertEqual(inferred_listing_type(row), "Food & drink")


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


class SiteSmokeTests(unittest.TestCase):
    def test_directory_assistant_asset_requires_guided_search_logic(self) -> None:
        complete = "const ASSISTANT_INTENTS = []; assistantInterpretation(); data-assistant-followup"
        incomplete = "const ASSISTANT_INTENTS = []; assistantInterpretation();"

        self.assertEqual(validate_body("assets/app.js", complete), "")
        self.assertIn("data-assistant-followup", validate_body("assets/app.js", incomplete))


class KeywordSweepTests(unittest.TestCase):
    def test_canonical_signal_excludes_collection_provenance(self) -> None:
        signal = canonical_signal(
            {
                "resource_name": "Example Cafe",
                "category": "All tourism directory listings; Dining",
                "resource_type": "Visitor-facing listing",
                "source_type": "Chamber of commerce page",
                "notes": "Commercial-directory-only lead from a source sweep. Outreach score 5; confirm it through a current public source.",
            }
        )

        self.assertIn("Example Cafe", signal)
        self.assertIn("Dining", signal)
        self.assertNotIn("tourism directory", signal)
        self.assertNotIn("Chamber of commerce", signal)
        self.assertNotIn("Outreach score", signal)

    def test_signal_text_uses_concise_high_priority_page_metadata(self) -> None:
        parser = KeywordSignalParser()
        parser.title_parts = ["First Choice Market | Spanish Peaks Country"]
        parser.meta_parts = [
            "Neighborhood grocery market in La Veta with produce, pantry goods, and local products.",
            "First Choice Market",
            "Explore lodging, museums, restaurants, shops, and attractions across Huerfano County.",
        ]
        parser.heading_parts = ["First Choice Market", "Visit La Veta", "Things to do"]

        signal = parser.signal_text()

        self.assertIn("grocery market", signal)
        self.assertIn("Visit La Veta", signal)
        self.assertNotIn("Spanish Peaks Country", signal)
        self.assertNotIn("Explore lodging", signal)
        self.assertNotIn("Things to do", signal)

    def test_controlled_keywords_match_phrases_without_partial_words(self) -> None:
        keywords = extract_controlled_keywords("Cafe, catering, and live music in a historic district")
        self.assertIn("cafe", keywords)
        self.assertIn("catering", keywords)
        self.assertIn("live music", keywords)
        self.assertNotIn("art gallery", extract_controlled_keywords("Cart repair"))

    def test_primary_source_url_prefers_public_website(self) -> None:
        row = {
            "website": "https://example.com; https://secondary.example.com",
            "source_url": "https://directory.example.org/listing",
        }
        self.assertEqual(primary_source_url(row), "https://example.com")

    def test_primary_source_url_prefers_non_social_listing_page(self) -> None:
        row = {
            "website": "https://www.facebook.com/example/",
            "source_url": "https://tourism.example.org/listing/example",
        }
        self.assertEqual(primary_source_url(row), "https://tourism.example.org/listing/example")

    def test_listing_name_must_match_page_signal(self) -> None:
        self.assertTrue(listing_name_matches_signal("J & A's Cafe", "J and A's Cafe at the Roadrunner"))
        self.assertFalse(listing_name_matches_signal("Brick City Tattoo", "Trinidad shopping, museums, and antiques"))

    def test_url_selection_prioritizes_never_checked_sources(self) -> None:
        url_to_ids = {
            "https://checked.example.com": ["checked"],
            "https://new.example.com": ["new"],
        }
        old_entries = {"checked": {"last_checked": "2026-07-20"}}
        self.assertEqual(select_urls(url_to_ids, old_entries, 1), ["https://new.example.com"])


if __name__ == "__main__":
    unittest.main()
