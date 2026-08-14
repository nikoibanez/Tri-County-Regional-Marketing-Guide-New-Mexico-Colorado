from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools"))

import audit_resource_discovery_sources as discovery  # noqa: E402
import build_netlify_deep_guide as guide_builder  # noqa: E402


class ResourceDiscoveryRegistryTests(unittest.TestCase):
    def test_registry_ids_urls_and_keyword_groups_are_complete(self) -> None:
        sources = json.loads((ROOT / "data" / "resource-discovery-sources.json").read_text(encoding="utf-8"))["sources"]
        groups = json.loads((ROOT / "data" / "resource-keyword-registry.json").read_text(encoding="utf-8"))["groups"]
        group_ids = {item["id"] for item in groups}
        source_ids = [item["id"] for item in sources]
        self.assertGreaterEqual(len(sources), 20)
        self.assertEqual(len(source_ids), len(set(source_ids)))
        self.assertTrue(all(item["category"] in group_ids for item in sources))
        self.assertTrue(all(str(item["url"]).startswith("https://") for item in sources))

    def test_artist_routes_are_numerous_and_user_labeled(self) -> None:
        sources = json.loads((ROOT / "data" / "resource-discovery-sources.json").read_text(encoding="utf-8"))["sources"]
        artist_sources = [item for item in sources if item["category"] == "artists-creative-opportunities"]
        self.assertGreaterEqual(len(artist_sources), 15)
        self.assertTrue(all(item.get("resource_type") for item in artist_sources))
        self.assertTrue(all(item.get("action_label") for item in artist_sources))

    def test_candidate_extractor_uses_whole_phrases_and_ignores_scripts(self) -> None:
        markup = """
        <html><body>
          <script><a href="/wrong-grant">Grant deadline</a></script>
          <a href="/starting-a-company">Starting a company</a>
          <a href="/artist-open-call">Artist open call with stipend</a>
        </body></html>
        """
        text, links = discovery.parse_page(markup)
        self.assertNotIn("wrong", text)
        group = {
            "artists-creative-opportunities": {
                "include_phrases": ["art", "artist", "open call"],
                "decision_terms": ["stipend"],
                "exclude_phrases": [],
            }
        }
        source = {"category": "artists-creative-opportunities", "query_groups": []}
        candidates = discovery.extract_candidates(source, "https://example.org/", links, group)
        self.assertEqual([item["title"] for item in candidates], ["Artist open call with stipend"])

    def test_decision_and_location_terms_do_not_create_candidates_alone(self) -> None:
        links = [
            ("Contact", "/contact"),
            ("Colorado", "/colorado"),
            ("Artist grant deadline", "/artist-grant"),
        ]
        groups = {
            "artists-creative-opportunities": {
                "include_phrases": ["artist grant"],
                "decision_terms": ["deadline", "contact"],
                "exclude_phrases": [],
            }
        }
        source = {
            "category": "artists-creative-opportunities",
            "automation_mode": "page_links",
            "query_groups": ["Colorado"],
        }
        candidates = discovery.extract_candidates(source, "https://example.org/", links, groups)
        self.assertEqual([item["title"] for item in candidates], ["Artist grant deadline"])

    def test_failed_fetch_preserves_previous_successful_state(self) -> None:
        sources = [{"id": "example", "name": "Example", "url": "https://example.org", "category": "grants-public-funding"}]
        groups = {"grants-public-funding": {"include_phrases": ["grant"], "decision_terms": [], "exclude_phrases": []}}
        previous = {"sources": {"example": {"content_hash": "abc", "candidate_count": 3}}}
        with patch.object(
            discovery,
            "fetch_source",
            return_value={"status": "access_blocked", "status_code": 403, "final_url": "https://example.org", "error": "blocked", "candidates": []},
        ):
            results, state = discovery.audit_sources(sources, groups, previous, timeout=1)
        self.assertEqual(results[0]["change_status"], "check_failed")
        self.assertEqual(state["sources"]["example"]["content_hash"], "abc")
        self.assertEqual(state["sources"]["example"]["candidate_count"], 3)


class GuideTaxonomyTests(unittest.TestCase):
    def test_art_term_does_not_match_starting(self) -> None:
        row = {"resource_name": "Starting a Business Center", "description": "General business planning"}
        self.assertFalse(guide_builder.row_matches_terms(row, ["art"]))
        self.assertTrue(guide_builder.row_matches_terms({"resource_name": "Regional Art Center"}, ["art"]))

    def test_audience_text_does_not_change_preview_identity(self) -> None:
        row = {
            "resource_name": "111 Park Espresso Bar",
            "category": "Dining",
            "resource_type": "Visitor-facing listing",
            "audience_served": "Artist; Creative business; Visitors / tourists",
            "public_listing_type": "Food & drink",
            "public_category": "Dining",
        }
        self.assertFalse(guide_builder.row_matches_terms(row, ["artist", "creative"]))

    def test_listing_type_prefers_concrete_category_and_whole_words(self) -> None:
        self.assertEqual(
            guide_builder.inferred_listing_type(
                {
                    "resource_name": "Andreatta Beef",
                    "category": "Local food producer / vendor",
                    "resource_type": "Maker / Artist Vendor",
                }
            ),
            "Food & drink",
        )
        self.assertEqual(
            guide_builder.inferred_listing_type(
                {
                    "resource_name": "Advance Auto Parts",
                    "category": "Commercial directory lead / local business",
                    "resource_type": "Outreach lead / source-check candidate",
                }
            ),
            "Auto & transportation",
        )

    def test_initials_normalize_with_or_without_periods(self) -> None:
        self.assertEqual(
            guide_builder.normalized_resource_name_key("A.R. Mitchell Museum"),
            guide_builder.normalized_resource_name_key("AR Mitchell Museum"),
        )

    def test_physical_location_shortlist_balances_counties(self) -> None:
        rows = []
        for county in ("Colfax", "Las Animas", "Huerfano"):
            for index in range(12):
                rows.append(
                    {
                        "id": f"{county}-{index}",
                        "resource_name": f"{county} Library {index}",
                        "county": county,
                        "town": f"Town {index % 2}",
                        "physical_address": f"{100 + index} Main Street",
                        "public_listing_type": "Public offices",
                    }
                )
        selected = guide_builder.physical_ad_location_rows(rows, limit=18)
        counts = {county: sum(1 for row in selected if row["county"] == county) for county in ("Colfax", "Las Animas", "Huerfano")}
        self.assertEqual(counts, {"Colfax": 6, "Las Animas": 6, "Huerfano": 6})

    def test_physical_promotion_keywords_reach_master_directory_search(self) -> None:
        enriched = guide_builder.enrich_resource_row(
            {
                "id": "sample-bookstore",
                "resource_name": "Sample Bookstore",
                "county": "Colfax",
                "town": "Raton",
                "physical_address": "100 Main Street",
                "public_listing_type": "Retail & local goods",
                "category": "Bookstore",
            }
        )
        self.assertEqual(enriched["physical_ad_candidate"], "true")
        self.assertEqual(enriched["physical_promotion_category"], "Bookstores and pharmacies")
        self.assertIn("Bookstore", enriched["public_keywords"])
        self.assertIn("physical promotion location", enriched["physical_promotion_keywords"])
        self.assertIn("bulletin boards", enriched["physical_promotion_keywords"])

    def test_short_physical_terms_do_not_match_inside_unrelated_words(self) -> None:
        self.assertEqual(
            guide_builder.physical_promotion_category(
                {
                    "resource_name": "Regional Service Company",
                    "category": "Professional service",
                    "public_listing_type": "Local business or service",
                }
            ),
            "",
        )
        self.assertEqual(
            guide_builder.physical_promotion_category(
                {
                    "resource_name": "A Taylor Made Haircut",
                    "category": "Service / personal care",
                    "public_listing_type": "Health & wellness",
                }
            ),
            "Personal service and auto shops",
        )

    def test_duplicate_directory_routes_on_same_host_render_once(self) -> None:
        markup = guide_builder.contact_links_for_row(
            {
                "website": "https://example.org/; https://www.example.org/about",
                "source_url": "https://example.com/directory/one; https://example.com/directory/two",
            }
        )
        self.assertEqual(markup.count(">Website<"), 1)
        self.assertEqual(markup.count("Listing page"), 1)

    def test_promote_and_physical_pages_use_searchable_shared_data(self) -> None:
        promote = guide_builder.promote_page()
        physical = guide_builder.posting_page([])
        self.assertIn('id="promote-results"', promote)
        self.assertIn('id="promote-county-filter"', promote)
        self.assertIn('id="physical-location-list"', physical)
        self.assertIn('id="physical-category-filter"', physical)
        self.assertNotIn("Ask first", physical)

    def test_discovery_shortlist_balances_requested_categories(self) -> None:
        sources = [
            {"name": f"Grant {index}", "category": "grants-public-funding"}
            for index in range(10)
        ] + [
            {"name": f"Capital {index}", "category": "business-capital"}
            for index in range(3)
        ] + [
            {"name": f"Sponsor {index}", "category": "fiscal-sponsorship"}
            for index in range(3)
        ]
        with patch.object(guide_builder, "RESOURCE_DISCOVERY_SOURCES", sources):
            selected = guide_builder.selected_discovery_sources(
                ["grants-public-funding", "business-capital", "fiscal-sponsorship"],
                limit=9,
            )
        counts = {
            category: sum(1 for item in selected if item["category"] == category)
            for category in ("grants-public-funding", "business-capital", "fiscal-sponsorship")
        }
        self.assertEqual(counts, {"grants-public-funding": 3, "business-capital": 3, "fiscal-sponsorship": 3})


if __name__ == "__main__":
    unittest.main()
