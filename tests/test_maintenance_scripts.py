from __future__ import annotations

import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools"))

from audit_directory_quality import duplicate_groups, normalize_name  # noqa: E402
from audit_directory_connectivity import connection_details, display_source_path, is_first_party_candidate  # noqa: E402
from audit_directory_outreach_channels import build_report as build_outreach_report  # noqa: E402
from audit_internal_links import audit_site  # noqa: E402
from audit_free_tools import audit as audit_free_tools, candidate_links as free_tool_candidate_links, validate_payload as validate_free_tools  # noqa: E402
from audit_update_sources import check_record, check_url, summarize  # noqa: E402
from apply_directory_link_repairs import apply_repairs_to_rows  # noqa: E402
import build_netlify_deep_guide as guide_builder  # noqa: E402
from build_update_source_registry import normalize_posting  # noqa: E402
from build_netlify_deep_guide import (  # noqa: E402
    ROUTE_TYPE_CARDS,
    best_entity_contact_url,
    inferred_listing_type,
    publishable_resource_row,
)
from directory_exclusions import (  # noqa: E402
    filter_excluded_directory_rows,
    references_excluded_directory_entity,
)
from directory_outreach import channel_status_map, classify_outreach_channels  # noqa: E402
from smoke_test_site import validate_body  # noqa: E402
from weekly_directory_query_check import (  # noqa: E402
    extract_candidates,
    load_existing_names,
    load_existing_urls,
    match_existing,
)
from sweep_listing_keywords import (  # noqa: E402
    KeywordSignalParser,
    canonical_signal,
    extract_controlled_keywords,
    filter_source_keywords,
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

    def test_weekly_directory_sweep_matches_aliases_and_known_listing_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory_path = Path(temp_dir) / "directory.csv"
            directory_path.write_text(
                "name,aliases,source_urls\n"
                '"Kathy Hills Studio Gallery / Spanish Peaks Art","[\'Kathy Hills Studio Gallery\']","[]"\n'
                '"The World Journal","[]","[\'https://spanishpeakscountry.com/business-directory/listing/world-journal\']"\n',
                encoding="utf-8",
            )
            names = load_existing_names([directory_path])
            urls = load_existing_urls([directory_path])

        alias_match = match_existing("Kathy Hills Studio Gallery", names)
        url_match = match_existing(
            "World Journal",
            names,
            "https://spanishpeakscountry.com/business-directory/listing/world-journal/",
            urls,
        )
        self.assertEqual(alias_match["match_type"], "exact_normalized")
        self.assertEqual(url_match["match_type"], "exact_url")

    def test_reviewed_link_repairs_replace_stale_urls_and_keep_fallbacks(self) -> None:
        rows = [
            {
                "id": "example",
                "website": "https://old.example.org/",
                "source_url": "https://old.example.org/; https://directory.example.org/category",
            }
        ]
        repairs = [
            {
                "id": "example",
                "remove_urls": ["https://old.example.org/"],
                "replacement_website": "https://new.example.org/",
                "add_source_urls": ["https://directory.example.org/listing/example"],
            }
        ]

        repaired, changed = apply_repairs_to_rows(rows, repairs)

        self.assertEqual(changed, ["example"])
        self.assertEqual(repaired[0]["website"], "https://new.example.org/")
        self.assertIn("https://directory.example.org/category", repaired[0]["source_url"])
        self.assertNotIn("https://old.example.org/", repaired[0]["source_url"])

    def test_entity_contact_prefers_website_then_listing_page(self) -> None:
        row = {
            "resource_name": "Example Studio",
            "website": "https://example-studio.org",
            "source_url": "https://directory.example.org/example-studio",
            "contact_email": "hello@example-studio.org",
        }
        self.assertEqual(best_entity_contact_url(row), "https://example-studio.org")
        row["website"] = ""
        self.assertEqual(best_entity_contact_url(row), "https://directory.example.org/example-studio")

    def test_entity_contact_falls_back_through_email_phone_map_and_search(self) -> None:
        self.assertEqual(
            best_entity_contact_url({"resource_name": "Example Artist", "contact_email": "artist@example.org"}),
            "mailto:artist@example.org",
        )
        self.assertEqual(
            best_entity_contact_url({"resource_name": "Example Artist", "contact_phone": "(575) 555-0199"}),
            "tel:5755550199",
        )
        self.assertIn(
            "google.com/maps/search",
            best_entity_contact_url({"resource_name": "Example Artist", "physical_address": "100 Main St, Raton, NM"}),
        )
        search_url = best_entity_contact_url(
            {"resource_name": "Example Artist", "town": "Raton", "county": "Colfax", "state": "NM"}
        )
        self.assertIn("google.com/search", search_url)
        self.assertIn("Example+Artist", search_url)

    def test_every_route_color_card_opens_a_filtered_directory(self) -> None:
        self.assertEqual(len(ROUTE_TYPE_CARDS), 5)
        for card in ROUTE_TYPE_CARDS:
            self.assertTrue(card.get("query"), card["label"])

    def test_capability_tags_cover_flyers_newsletters_and_social_sharing(self) -> None:
        flyer_tags = guide_builder.outreach_capability_tags(
            {
                "resource_name": "Example Market",
                "public_listing_type": "Retail & local goods",
                "physical_address": "100 Main St, Raton, NM",
                "yellowpages_flyer_likelihood": "High: likely local flyer-friendly",
                "yellowpages_recommended_action": "Ask owner/manager to post flyer near entrance/register.",
            }
        )
        newsletter_tags = guide_builder.outreach_capability_tags(
            {
                "resource_name": "Example Chamber",
                "public_listing_type": "Business support",
                "notes": "Newsletter signup and mailing list path for member updates and local events.",
            }
        )
        social_tags = guide_builder.outreach_capability_tags(
            {
                "resource_name": "Example Venue",
                "public_listing_type": "Events & venues",
                "website": "https://www.facebook.com/examplevenue/",
            }
        )

        self.assertIn("Physical promotion contact", flyer_tags)
        self.assertIn("Newsletter sharing", newsletter_tags)
        self.assertIn("Social sharing", social_tags)

    def test_audience_badges_do_not_repeat_outreach_channels(self) -> None:
        tags = guide_builder.organization_tags(
            {
                "audience_served": "Artist; For-Profit",
                "outreach_channels": [
                    {"key": "physical_flyers", "label": "Flyer/poster contact", "status": "ask"}
                ],
            }
        )

        self.assertEqual(tags, ["Artists", "Businesses"])


class DirectoryConnectivityTests(unittest.TestCase):
    def test_live_first_party_business_site_gets_connection_animation(self) -> None:
        row = {
            "id": "example-cafe",
            "resource_name": "Example Cafe",
            "public_listing_type": "Food & drink",
            "website": "https://examplecafe.com/",
        }
        checks = {
            "https://examplecafe.com/": {
                "status": "ok",
                "status_code": 200,
                "final_url": "https://examplecafe.com/",
            }
        }

        details = connection_details(row, checks, Counter({"examplecafe.com": 1}))

        self.assertEqual(details["connection_status"], "direct-live")
        self.assertEqual(details["public_label"], "Connect online")
        self.assertTrue(details["animation_eligible"])

    def test_shared_directory_page_is_a_hosted_profile(self) -> None:
        row = {
            "id": "example-shop",
            "resource_name": "Example Shop",
            "public_listing_type": "Retail & local goods",
            "website": "https://www.yellowpages.com/example-shop",
        }
        checks = {
            "https://www.yellowpages.com/example-shop": {
                "status": "ok",
                "status_code": 200,
                "final_url": "https://www.yellowpages.com/example-shop",
            }
        }
        host_usage = Counter({"yellowpages.com": 400})

        self.assertFalse(is_first_party_candidate(row, row["website"], host_usage))
        details = connection_details(row, checks, host_usage)
        self.assertEqual(details["connection_status"], "profile-live")
        self.assertEqual(details["public_label"], "Online profile")
        self.assertFalse(details["animation_eligible"])

    def test_phone_only_listing_does_not_imply_business_is_offline(self) -> None:
        details = connection_details(
            {
                "id": "example-service",
                "resource_name": "Example Service",
                "public_listing_type": "Professional services",
                "contact_phone": "(575) 555-0100",
            },
            {},
            Counter(),
        )

        self.assertEqual(details["connection_status"], "contact-only")
        self.assertEqual(details["public_label"], "No direct website listed")
        self.assertFalse(details["animation_eligible"])

    def test_confirmed_broken_site_falls_back_to_remaining_contact_path(self) -> None:
        url = "https://closed-example.com/"
        details = connection_details(
            {
                "id": "closed-example",
                "resource_name": "Closed Example",
                "public_listing_type": "Local business or service",
                "website": url,
                "contact_phone": "(719) 555-0100",
            },
            {url: {"status": "broken", "status_code": 404, "final_url": url}},
            Counter({"closed-example.com": 1}),
        )

        self.assertEqual(details["connection_status"], "contact-only")
        self.assertEqual(details["public_url"], "")
        self.assertEqual(details["confirmed_broken_urls"], [url])

    def test_generator_fallback_keeps_first_party_website_without_connectivity_sidecar(self) -> None:
        with (
            patch.object(guide_builder, "DIRECTORY_CONNECTIVITY_ENTRIES", {}),
            patch.object(guide_builder, "DIRECTORY_CONNECTIVITY_CHECKS", {}),
        ):
            details = guide_builder.online_connection_fields(
                {
                    "id": "example-cafe",
                    "resource_name": "Example Cafe",
                    "website": "https://examplecafe.com/",
                }
            )

        self.assertEqual(details["online_connection_group"], "Direct website")
        self.assertEqual(details["online_connection_status"], "direct-unconfirmed")

    def test_connectivity_report_uses_repo_relative_source_path(self) -> None:
        path = ROOT / "dist" / "tri-county-netlify-guide-deep" / "data" / "guide-data.json"
        self.assertEqual(display_source_path(path), "dist/tri-county-netlify-guide-deep/data/guide-data.json")


class DirectoryOutreachTests(unittest.TestCase):
    def test_explicit_newsletter_and_advertising_pages_are_listed_routes(self) -> None:
        channels = classify_outreach_channels(
            {
                "resource_name": "Regional Visitor Newsletter",
                "public_listing_type": "Tourism & visitor info",
                "website": "https://example.org/newsletter-signup/",
                "notes": "Advertising rates and newsletter signup are available on the linked pages.",
            }
        )
        statuses = channel_status_map(channels)
        self.assertEqual(statuses["newsletter_mailing_list"], "listed")
        self.assertEqual(statuses["paid_digital_advertising"], "listed")

    def test_social_profile_is_an_ask_first_route_not_a_sharing_promise(self) -> None:
        channels = classify_outreach_channels(
            {
                "resource_name": "Example Gallery",
                "public_listing_type": "Arts & culture",
                "website": "https://www.facebook.com/example-gallery/",
            }
        )
        statuses = channel_status_map(channels)
        self.assertEqual(statuses["social_cross_promotion"], "ask")

    def test_physical_address_never_implies_flyer_permission(self) -> None:
        channels = classify_outreach_channels(
            {
                "resource_name": "Example Cafe",
                "public_listing_type": "Food & drink",
                "physical_address": "100 Main Street",
            },
            has_physical_location=True,
            physical_ad_candidate=True,
        )
        statuses = channel_status_map(channels)
        self.assertEqual(statuses["physical_flyers"], "ask")
        self.assertNotEqual(statuses["physical_flyers"], "listed")

    def test_generated_guide_language_does_not_create_channel_claims(self) -> None:
        channels = classify_outreach_channels(
            {
                "resource_name": "Example Shop",
                "public_listing_type": "Retail & local goods",
                "notes": (
                    "Example Shop is a retail business. Search here for promotion, online listing cleanup, "
                    "flyer posting, sponsorship, and cross-promotion when you need an outreach route."
                ),
            }
        )
        statuses = channel_status_map(channels)
        self.assertEqual(statuses["physical_flyers"], "not_indicated")
        self.assertEqual(statuses["sponsorship"], "not_indicated")
        self.assertEqual(statuses["partner_cross_promotion"], "not_indicated")

    def test_report_reviews_every_supplied_listing(self) -> None:
        rows = [
            {"id": "one", "resource_name": "One", "outreach_channels": []},
            {
                "id": "two",
                "resource_name": "Two",
                "outreach_channels": [{"key": "event_calendar", "status": "listed", "label": "Event/calendar route"}],
            },
        ]
        report = build_outreach_report(rows, ROOT / "example-guide-data.json")
        self.assertEqual(report["summary"]["entries"], 2)
        self.assertEqual(report["summary"]["without_outreach_route"], 1)
        self.assertEqual(report["summary"]["missing_structured_fields"], 0)


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


class SourceAuditTests(unittest.TestCase):
    def test_offline_posting_guidance_is_not_a_broken_link(self) -> None:
        record = normalize_posting(
            {
                "place": "General regional pattern",
                "county": "Regional",
                "status": "Field-check needed",
                "source_url": "",
            }
        )

        self.assertEqual(record["check_mode"], "field")
        self.assertEqual(check_record(record, 1)["status"], "field_check")

    def test_summary_separates_broken_links_from_automation_limits(self) -> None:
        results = [
            {"record": {"review_level": "standard_review"}, "check": {"status": "ok"}},
            {"record": {"review_level": "standard_review"}, "check": {"status": "broken"}},
            {"record": {"review_level": "standard_review"}, "check": {"status": "access_blocked"}},
            {"record": {"review_level": "standard_review"}, "check": {"status": "tls_error"}},
            {"record": {"review_level": "standard_review"}, "check": {"status": "field_check"}},
        ]

        summary = summarize(results)

        self.assertEqual(summary["confirmed_broken"], 1)
        self.assertEqual(summary["needs_attention"], 1)
        self.assertEqual(summary["browser_check_needed"], 0)
        self.assertEqual(summary["script_access_limited"], 2)
        self.assertEqual(summary["field_checks"], 1)
        self.assertEqual(summary["web_checked"], 4)

    def test_url_without_web_scheme_is_a_confirmed_format_error(self) -> None:
        self.assertEqual(check_url("example.org/directory", 1)["status"], "invalid_url")


class WorkflowTests(unittest.TestCase):
    def test_weekly_directory_query_check_builds_before_connectivity_audit(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "weekly-directory-query-check.yml").read_text(encoding="utf-8")
        self.assertLess(
            workflow.index("python tools/build_netlify_deep_guide.py"),
            workflow.index("python scripts/audit_directory_connectivity.py --workers 16 --timeout 10"),
        )


class SiteSmokeTests(unittest.TestCase):
    def test_reset_output_dir_preserves_root_and_clears_contents(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "build-output"
            nested = out / "nested"
            nested.mkdir(parents=True)
            (out / "stale.txt").write_text("old", encoding="utf-8")
            (nested / "old.html").write_text("old", encoding="utf-8")

            guide_builder.reset_output_dir(out)

            self.assertTrue(out.exists())
            self.assertEqual(list(out.iterdir()), [])

    def test_navigation_yucca_is_generated_with_motion_safeguards(self) -> None:
        page = guide_builder.page_shell("Test", "Test page", "about", "<section>Test</section>")
        self.assertIn('data-nav-yucca aria-hidden="true"', page)

        with tempfile.TemporaryDirectory() as folder:
            asset_out = Path(folder)
            with patch.object(guide_builder, "ASSET_OUT", asset_out):
                guide_builder.write_static_assets()
            css = (asset_out / "styles.css").read_text(encoding="utf-8")
            js = (asset_out / "app.js").read_text(encoding="utf-8")

        self.assertIn("navYuccaVisit 3000ms", css)
        self.assertIn("prefers-reduced-motion: reduce", css)
        self.assertIn("NAV_YUCCA_KEY", js)
        self.assertIn("initNavigationYucca();", js)

    def test_primary_navigation_combines_direct_resources_with_county_promote_routes(self) -> None:
        page = guide_builder.page_shell("Test", "Test page", "about", "<section>Test</section>")
        nav = page.split('<nav class="site-nav" aria-label="Primary navigation">', 1)[1].split("</nav>", 1)[0]
        ordered_labels = [
            ">Home</a>",
            ">Directory</a>",
            ">Funding</a>",
            ">Arts &amp; Culture</a>",
            ">Promote</summary>",
            ">Counties</summary>",
            ">Guide</summary>",
            ">Tools</summary>",
        ]
        positions = [nav.index(label) for label in ordered_labels]

        self.assertEqual(positions, sorted(positions))
        self.assertNotIn(">More</summary>", nav)
        self.assertIn('class="nav-menu nav-menu--promote"', nav)
        for heading in ("Events", "Advertising + media", "Business visibility", "Nonprofit outreach", "Calendars", "Galleries + arts"):
            self.assertIn(f'<p class="nav-menu-label">{heading}</p>', nav)
        self.assertIn("promote/index.html?county=Colfax&amp;route=events#promotion-results", nav)
        self.assertIn("promote/index.html?county=Las+Animas&amp;route=advertising#promotion-results", nav)
        self.assertIn("promote/index.html?county=Huerfano&amp;route=galleries#promotion-results", nav)

        with tempfile.TemporaryDirectory() as folder:
            asset_out = Path(folder)
            with patch.object(guide_builder, "ASSET_OUT", asset_out):
                guide_builder.write_static_assets()
            css = (asset_out / "styles.css").read_text(encoding="utf-8")

        self.assertIn("grid-template-columns: repeat(4, minmax(0, 1fr))", css)
        self.assertIn(".nav-menu-grid { grid-template-columns: repeat(2, minmax(0, 1fr))", css)

    def test_music_bar_only_renders_on_arts_culture_page(self) -> None:
        about_page = guide_builder.page_shell("Test", "Test page", "about", "<section>Test</section>")
        arts_page = guide_builder.page_shell("Test", "Test page", "arts-culture", "<section>Test</section>")

        self.assertNotIn('data-music-bar', about_page)
        self.assertNotIn('id="site-music-loop"', about_page)
        self.assertIn('data-music-bar', arts_page)
        self.assertIn('id="site-music-loop"', arts_page)
        self.assertGreaterEqual(len(guide_builder.REGIONAL_AUDIO_TRACKS), 6)
        for track in guide_builder.REGIONAL_AUDIO_TRACKS:
            self.assertIn(track["local_audio_filename"], arts_page)
            self.assertIn(track["item_url"], arts_page)

    def test_draft_watermark_is_limited_to_preview_hosts(self) -> None:
        page = guide_builder.page_shell("Test", "Test page", "about", "<section>Test</section>")
        self.assertIn('data-preview-watermark hidden aria-hidden="true">Draft preview</div>', page)

        with tempfile.TemporaryDirectory() as folder:
            asset_out = Path(folder)
            with patch.object(guide_builder, "ASSET_OUT", asset_out):
                guide_builder.write_static_assets()
            css = (asset_out / "styles.css").read_text(encoding="utf-8")
            js = (asset_out / "app.js").read_text(encoding="utf-8")

        self.assertIn(".site-watermark", css)
        self.assertIn("bottom: max(8vh, env(safe-area-inset-bottom));", css)
        self.assertIn("opacity: 0.10;", css)
        self.assertNotIn(".site-watermark__detail", css)
        self.assertIn('host.startsWith("deploy-preview-")', js)
        self.assertIn("initPreviewWatermark();", js)

    def test_free_tools_are_structured_filterable_and_routed_by_assistant(self) -> None:
        payload = {
            "tools": guide_builder.PROMOTION_TOOLS,
            "discovery_sources": guide_builder.FREE_TOOL_DISCOVERY_SOURCES,
        }
        self.assertEqual(validate_free_tools(payload), [])
        self.assertGreaterEqual(len(guide_builder.PROMOTION_TOOLS), 20)
        self.assertIn("Nonprofit benefits", {item["category"] for item in guide_builder.PROMOTION_TOOLS})
        self.assertTrue(any("Free/open-source software" in item["access_types"] for item in guide_builder.PROMOTION_TOOLS))
        self.assertTrue(any(any("nonprofit" in label.casefold() for label in item["access_types"]) for item in guide_builder.PROMOTION_TOOLS))

        page = guide_builder.templates_page()
        self.assertIn('id="free-tools"', page)
        self.assertIn("data-tool-filters", page)
        self.assertIn("data-tool-card", page)
        self.assertIn("TechSoup", page)
        self.assertIn("Open-source software", page)

        shell = guide_builder.page_shell("Test", "Test page", "about", "<section>Test</section>")
        self.assertIn("data-site-root=", shell)
        routes = guide_builder.assistant_site_routes()
        route_paths = {item["path"] for item in routes}
        self.assertIn("network/", route_paths)
        self.assertIn("resources/funding/", route_paths)
        self.assertIn("templates/#free-tools", route_paths)
        self.assertTrue(any(path.startswith("promote/?county=Colfax") for path in route_paths))

        with tempfile.TemporaryDirectory() as folder:
            asset_out = Path(folder)
            with patch.object(guide_builder, "ASSET_OUT", asset_out):
                guide_builder.write_static_assets()
            css = (asset_out / "styles.css").read_text(encoding="utf-8")
            js = (asset_out / "app.js").read_text(encoding="utf-8")
        self.assertIn("...(DATA.free_tools || [])", js)
        self.assertIn("...(DATA.site_routes || [])", js)
        self.assertIn("function assistantSiteUrl", js)
        self.assertIn("function initFreeToolFilters", js)
        self.assertIn('["Site route", "Free tool"].includes(item.assistant_type)', js)
        self.assertIn(".tool-card[hidden] { display: none; }", css)

    def test_free_tool_audit_preserves_review_boundary(self) -> None:
        payload = {
            "tools": [
                {
                    "id": "example",
                    "name": "Example Tool",
                    "url": "https://example.com/",
                    "source_url": "https://example.com/pricing",
                    "category": "Design & print",
                    "format": "Web app",
                    "access_types": ["Free plan"],
                    "use": "Create a flyer.",
                    "note": "Check current limits.",
                    "watch_terms": ["free"],
                }
            ],
            "discovery_sources": [],
        }
        results, summary, state = audit_free_tools(payload, {"schema_version": 1, "pages": {}}, 1, no_network=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(summary["checked_ok"], 0)
        self.assertEqual(summary["review_count"], 0)
        self.assertEqual(state["pages"], {})

        candidates = free_tool_candidate_links(
            {"candidate_terms": ["nonprofit", "software"]},
            "https://example.org/catalog/",
            [("Nonprofit design software", "/offers/design"), ("Privacy", "/privacy")],
            set(),
        )
        self.assertEqual([item["url"] for item in candidates], ["https://example.org/offers/design"])

    def test_landscapes_and_assistant_use_accessible_southwest_motion(self) -> None:
        page = guide_builder.page_shell("Test", "Test page", "about", "<section>Test</section>")
        self.assertIn('class="directory-assistant__desert-motion" aria-hidden="true"', page)

        landscape_files = sorted((ROOT / "assets" / "animations").glob("hero-*.svg"))
        self.assertEqual(len(landscape_files), 11)
        for landscape_file in landscape_files:
            svg = landscape_file.read_text(encoding="utf-8")
            self.assertIn('class="plains-layer"', svg, landscape_file.name)
            self.assertIn("@keyframes geo-plains", svg, landscape_file.name)
            self.assertIn("prefers-reduced-motion: reduce", svg, landscape_file.name)

        with tempfile.TemporaryDirectory() as folder:
            asset_out = Path(folder)
            with patch.object(guide_builder, "ASSET_OUT", asset_out):
                guide_builder.write_static_assets()
            css = (asset_out / "styles.css").read_text(encoding="utf-8")
            js = (asset_out / "app.js").read_text(encoding="utf-8")

        self.assertIn("assistant-desert-open", css)
        self.assertIn("assistant-desert-close", css)
        self.assertIn("replayAssistantMotion(panel, \"open\")", js)
        self.assertIn('panel.addEventListener("cancel"', js)
        self.assertIn('playGuideSfx("intro", { armOnGesture: true })', js)

    def test_directory_assistant_asset_requires_guided_search_logic(self) -> None:
        complete = (
            "const ASSISTANT_INTENTS = []; assistantInterpretation(); data-assistant-followup "
            "bestEntityContact(); entityNameMarkup();"
        )
        incomplete = "const ASSISTANT_INTENTS = []; assistantInterpretation();"

        self.assertEqual(validate_body("assets/app.js", complete), "")
        self.assertIn("data-assistant-followup", validate_body("assets/app.js", incomplete))

    def test_directory_connection_ui_is_filterable_and_motion_safe(self) -> None:
        page = guide_builder.network_page([])
        self.assertIn('id="online-connection-filter"', page)
        self.assertIn('id="outreach-channel-filter"', page)
        self.assertIn('id="outreach-status-filter"', page)
        self.assertIn("How to read a listing", page)
        self.assertNotIn('id="access-mode-filter"', page)

        with tempfile.TemporaryDirectory() as folder:
            asset_out = Path(folder)
            with patch.object(guide_builder, "ASSET_OUT", asset_out):
                guide_builder.write_static_assets()
            css = (asset_out / "styles.css").read_text(encoding="utf-8")
            js = (asset_out / "app.js").read_text(encoding="utf-8")

        self.assertIn("@keyframes connection-online-pulse", css)
        self.assertIn("function onlineConnectionMarkup(item)", js)
        self.assertIn("function outreachChannelMarkup(item", js)
        self.assertIn('document.querySelector("#outreach-channel-filter")', js)
        self.assertIn('uniqueValues(DATA.resources, "online_connection_group")', js)
        self.assertIn('window.matchMedia("(max-width: 640px)")', js)
        self.assertIn("prefers-reduced-motion: reduce", css)

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

    def test_keyword_guardrails_block_host_context_and_listing_specific_noise(self) -> None:
        row = {
            "id": "music-example",
            "resource_name": "Example Music Festival",
            "category": "Music festival",
            "resource_type": "Arts and culture",
        }
        guardrails = {
            "global_rules": {
                "chamber of commerce": {"required_canonical_phrases": ["chamber"]}
            },
            "listing_rules": {
                "music-example": {"blocked_source_keywords": ["visitor center"]}
            },
        }

        allowed, blocked = filter_source_keywords(
            row,
            ["festival", "chamber of commerce", "visitor center"],
            guardrails,
        )

        self.assertEqual(allowed, ["festival"])
        self.assertEqual(blocked, ["chamber of commerce", "visitor center"])

        positive_row = {
            "id": "library-example",
            "resource_name": "Example Public Library",
            "category": "Library and community",
            "resource_type": "Bulletin and notice",
        }
        allowed, blocked = filter_source_keywords(
            positive_row,
            ["library"],
            guardrails,
        )
        self.assertEqual(allowed, ["library"])
        self.assertEqual(blocked, [])


if __name__ == "__main__":
    unittest.main()
