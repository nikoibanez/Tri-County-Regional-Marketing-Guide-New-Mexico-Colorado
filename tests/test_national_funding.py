from __future__ import annotations

import inspect
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools"))

import audit_national_funding_sources as funding_watch  # noqa: E402
import build_netlify_deep_guide as guide_builder  # noqa: E402
from validate_national_funding_data import validate  # noqa: E402


OPPORTUNITIES = ROOT / "data" / "national-funding-opportunities.json"
WATCH_SOURCES = ROOT / "data" / "national-funding-watch-sources.json"


class NationalFundingDataTests(unittest.TestCase):
    def test_curated_directory_and_watch_list_are_complete(self) -> None:
        self.assertEqual(validate(OPPORTUNITIES, WATCH_SOURCES), [])
        opportunities = json.loads(OPPORTUNITIES.read_text(encoding="utf-8"))["opportunities"]
        watch_payload = json.loads(WATCH_SOURCES.read_text(encoding="utf-8"))
        sources = watch_payload["sources"]
        self.assertGreaterEqual(len(opportunities), 99)
        self.assertGreaterEqual(len(sources), 30)
        self.assertEqual(
            {item["id"] for item in watch_payload["required_sweeps"]},
            {"economic-development", "education", "healthcare", "nonprofits", "arts-culture"},
        )
        covered = {topic for source in sources for topic in source["sweep_topics"]}
        self.assertEqual(covered, {"economic-development", "education", "healthcare", "nonprofits", "arts-culture"})

    def test_regional_infographic_programs_are_structured_directory_records(self) -> None:
        opportunities = json.loads(OPPORTUNITIES.read_text(encoding="utf-8"))["opportunities"]
        opportunity_ids = {item["id"] for item in opportunities}
        self.assertTrue(
            {
                "colorado-rural-jump-start",
                "usda-redlg",
                "nm-mainstreet-funding-opportunities",
                "nm-mainstreet-frontier-services",
                "nm-healthy-food-financing-fund",
                "nm-sbir-matching-grant",
                "nm-outdoor-recreation-trails-plus",
                "nm-rural-tribal-agriculture-microgrants",
                "pnm-power-grant",
                "scedd-business-resource-fairs",
                "nm-creative-support-organization-grant",
                "nm-creative-business-development-grant",
                "nm-creative-public-development-projects-grant",
            }.issubset(opportunity_ids)
        )

    def test_five_subject_sweeps_added_region_specific_non_loan_support(self) -> None:
        opportunities = json.loads(OPPORTUNITIES.read_text(encoding="utf-8"))["opportunities"]
        opportunity_ids = {item["id"] for item in opportunities}
        self.assertTrue(
            {
                "nm-edd-leads",
                "first-southwest-workshop-grants",
                "trinidad-state-learn-local-scholarship",
                "mary-john-goree-scholarship",
                "cuchara-chapel-scholarship",
                "nmcf-northeastern-regional-health-fund",
                "health-solutions-community-sponsorship",
                "spanish-peaks-healthcare-foundation-scholarships",
                "brindle-early-childhood-grants",
                "robert-hoag-rawlings-foundation-grants",
                "john-g-duncan-charitable-trust",
                "taos-community-foundation-impact-grants",
                "nm-arts-southwest-artist-purchase",
                "nm-arts-indigenous-artist-purchase",
            }.issubset(opportunity_ids)
        )

    def test_public_funding_cards_expose_requested_decision_fields(self) -> None:
        page = guide_builder.funding_page([])
        self.assertIn('id="funding-search"', page)
        self.assertIn("Marketing or advertising costs", page)
        self.assertIn("Fiscal sponsor", page)
        self.assertIn("Cost to apply or enroll", page)
        self.assertIn("Funding or support", page)
        self.assertEqual(page.count("data-funding-card"), len(guide_builder.NATIONAL_FUNDING_OPPORTUNITIES))
        self.assertNotIn("verification status", page.casefold())

    def test_every_public_support_filter_has_at_least_one_entry(self) -> None:
        groups = {guide_builder.funding_program_group(item) for item in guide_builder.NATIONAL_FUNDING_OPPORTUNITIES}
        self.assertEqual(
            groups,
            {
                "Cash grants",
                "Fellowships",
                "Free support programs",
                "Funding search tools",
                "Incentives and reimbursements",
                "Loans and capital",
            },
        )

    def test_non_loan_awards_use_the_cash_grant_filter(self) -> None:
        for program_type in (
            "Education scholarship",
            "Healthcare scholarship",
            "Community sponsorship or donation",
            "Artwork purchase award",
            "Artist stipend",
        ):
            self.assertEqual(guide_builder.funding_program_group({"program_type": program_type}), "Cash grants")

    def test_directory_assistant_searches_funding_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            asset_dir = Path(temp_dir)
            with patch.object(guide_builder, "ASSET_OUT", asset_dir):
                guide_builder.write_static_assets()
            app_js = (asset_dir / "app.js").read_text(encoding="utf-8")
        self.assertIn("DATA.national_funding_opportunities", app_js)
        self.assertIn('assistant_type: "Funding opportunity"', app_js)
        self.assertIn("item.application_url", app_js)

    def test_homepage_omits_mixed_current_entries_and_grant_infographic(self) -> None:
        page = guide_builder.home_page({"row_count": 0, "county": {}})
        self.assertNotIn("Current funding and directory entries", page)
        self.assertNotIn("grant-opportunity-map", page)

    def test_public_build_does_not_copy_legacy_infographic_assets(self) -> None:
        self.assertNotIn("infographics", inspect.getsource(guide_builder.copy_assets).casefold())

    def test_funding_cards_put_nearest_active_deadlines_first(self) -> None:
        entries = [
            {"name": "Rolling", "status": "Open rolling", "deadline_date": ""},
            {"name": "Later", "status": "Upcoming", "deadline_date": "2026-10-30"},
            {"name": "Sooner", "status": "Open", "deadline_date": "2026-08-28"},
            {"name": "Closed", "status": "Monitor next cycle", "deadline_date": "2026-07-27"},
        ]
        ordered = sorted(entries, key=guide_builder.funding_deadline_sort_key)
        self.assertEqual([item["name"] for item in ordered], ["Sooner", "Later", "Rolling", "Closed"])

    def test_free_services_catalog_includes_structured_support_programs(self) -> None:
        catalog_ids = {item["id"] for item in guide_builder.tools_catalog()}
        self.assertIn("support-nm-mainstreet-frontier-services", catalog_ids)
        self.assertIn("support-scedd-business-resource-fairs", catalog_ids)
        page = guide_builder.free_tools_page()
        self.assertIn("Free &amp; discounted tools", page)
        self.assertIn("New Mexico Frontier Community Initiative", page)


class NationalFundingWatchTests(unittest.TestCase):
    def test_each_requested_subject_is_a_distinct_reported_sweep(self) -> None:
        payload = json.loads(WATCH_SOURCES.read_text(encoding="utf-8"))
        self.assertEqual(funding_watch.validate_watch_registry(payload), [])
        results = [
            {
                "source": source,
                "check": {"status": "ok"},
                "change_status": "unchanged",
            }
            for source in payload["sources"]
        ]
        summary = funding_watch.summarize(results)
        self.assertEqual(set(summary["sweep_counts"]), set(funding_watch.SWEEP_TOPIC_LABELS))
        for counts in summary["sweep_counts"].values():
            self.assertGreater(counts["configured"], 0)
            self.assertEqual(counts["checked"], counts["configured"])

        report_payload = {
            "generated_at": "2026-08-25T12:00:00-06:00",
            "summary": summary,
            "results": results,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "funding-watch.md"
            funding_watch.write_markdown(report_payload, report_path)
            report = report_path.read_text(encoding="utf-8")
        for label in funding_watch.SWEEP_TOPIC_LABELS.values():
            self.assertIn(f"### {label}", report)

    def test_text_extractor_ignores_scripts_and_keeps_review_signals(self) -> None:
        markup = """
        <html><head><script>deadline = 'wrong';</script></head>
        <body><h1>Program</h1><p>Applications open now. Deadline: October 10, 2026.</p></body></html>
        """
        text = funding_watch.normalize_page_text(markup)
        self.assertNotIn("wrong", text)
        self.assertIn("Deadline: October 10, 2026", text)
        self.assertTrue(funding_watch.extract_signal_snippets(text))

    def test_failed_fetch_preserves_last_successful_hash(self) -> None:
        sources = [{"id": "example", "name": "Example", "url": "https://example.org", "focus": [], "cadence_days": 7}]
        previous = {"sources": {"example": {"content_hash": "abc", "signal_snippets": ["Deadline old"]}}}
        with patch.object(
            funding_watch,
            "fetch_source",
            return_value={"status": "access_blocked", "status_code": 403, "final_url": "https://example.org", "error": "blocked"},
        ):
            results, state = funding_watch.audit_sources(sources, previous, timeout=1)
        self.assertEqual(results[0]["change_status"], "check_failed")
        self.assertEqual(state["sources"]["example"]["content_hash"], "abc")
        self.assertEqual(state["sources"]["example"]["signal_snippets"], ["Deadline old"])


if __name__ == "__main__":
    unittest.main()
