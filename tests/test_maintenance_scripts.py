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
from build_netlify_deep_guide import inferred_listing_type, publishable_resource_row  # noqa: E402
from directory_exclusions import (  # noqa: E402
    filter_excluded_directory_rows,
    references_excluded_directory_entity,
)
from smoke_test_site import validate_body  # noqa: E402
from weekly_directory_query_check import extract_candidates  # noqa: E402
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

    def test_excluded_organizations_never_become_publishable_rows(self) -> None:
        blocked_rows = [
            {"resource_name": "Raton Art Space LLC", "town": "Raton", "county": "Colfax"},
            {
                "resource_name": "Example Gallery",
                "town": "Raton",
                "county": "Colfax",
                "website": "https://example.org/meditatingmonkeyartemporium",
            },
        ]

        self.assertTrue(references_excluded_directory_entity(blocked_rows[0]["resource_name"]))
        self.assertEqual(filter_excluded_directory_rows(blocked_rows), [])
        self.assertFalse(publishable_resource_row(blocked_rows[0]))

    def test_weekly_directory_sweep_discards_excluded_candidates(self) -> None:
        source = {
            "id": "test-directory",
            "title": "Test Directory",
            "county": "Colfax",
            "state": "NM",
            "source_type": "Test",
        }
        html = (
            '<a href="/listing/raton-art-space">Raton Art Space</a>'
            '<a href="/listing/allowed-gallery">Allowed Gallery</a>'
        )

        candidates = extract_candidates(source, "https://example.org/directory/", html, {})

        self.assertEqual([candidate["name"] for candidate in candidates], ["Allowed Gallery"])


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

    def test_public_output_rejects_excluded_organization_names(self) -> None:
        body = '{"resource_name": "Raton Art Space"}'
        self.assertIn("explicitly excluded organization", validate_body("data/guide-data.json", body))

    def test_public_resource_json_accepts_an_array(self) -> None:
        self.assertEqual(validate_body("data/tri_county_persona_resources.json", "[]"), "")


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
