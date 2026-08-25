from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "review" / "maintenance"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def count_csv(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def build_dashboard() -> dict:
    registry = load_json(ROOT / "data" / "update-source-registry.json")
    candidates = load_json(ROOT / "data" / "directory-auto-update-candidates.json")
    source_audit = load_json(ROOT / "review" / "update-audits" / "update-audit-latest.json")
    directory_watch = load_json(ROOT / "review" / "directory-watch" / "directory-watch-latest.json")
    keyword_sweep = load_json(ROOT / "review" / "keyword-sweep" / "keyword-sweep-latest.json")
    outreach_review = load_json(ROOT / "review" / "directory-outreach" / "directory-outreach-latest.json")
    funding_directory = load_json(ROOT / "data" / "national-funding-opportunities.json")
    funding_watch = load_json(ROOT / "review" / "national-funding-watch" / "national-funding-watch-latest.json")
    discovery_registry = load_json(ROOT / "data" / "resource-discovery-sources.json")
    resource_discovery = load_json(ROOT / "review" / "resource-discovery" / "resource-discovery-latest.json")
    free_tools = load_json(ROOT / "data" / "free-tools.json")
    free_tools_review = load_json(ROOT / "review" / "free-tools" / "free-tools-latest.json")
    quality = load_json(DEFAULT_OUT_DIR / "directory-quality-latest.json")
    link_audit = load_json(DEFAULT_OUT_DIR / "internal-link-audit-latest.json")

    candidate_summary = directory_watch.get("summary") or candidates.get("summary") or {}
    audit_summary = source_audit.get("summary") or {}
    quality_summary = quality.get("canonical_source") or {}
    public_quality = quality.get("published_directory") or quality.get("consolidated_directory") or {}
    link_summary = link_audit.get("summary") or {}
    keyword_summary = keyword_sweep.get("summary") or {}
    outreach_summary = outreach_review.get("summary") or {}
    funding_watch_summary = funding_watch.get("summary") or {}
    discovery_summary = resource_discovery.get("summary") or {}
    free_tools_summary = free_tools_review.get("summary") or {}
    action_queue = []

    def add_action(count: int, label: str, next_action: str, priority: str) -> None:
        if count:
            action_queue.append({"priority": priority, "count": count, "label": label, "next_action": next_action})

    add_action(
        int(audit_summary.get("confirmed_broken") or audit_summary.get("needs_attention") or 0),
        "confirmed broken or missing monitored sources",
        "Repair, replace, or intentionally retire each URL before publishing the next source update.",
        "high",
    )
    add_action(
        int(audit_summary.get("browser_check_needed") or 0),
        "sources the automated checker could not confirm",
        "Open these in a normal browser; do not remove a link solely because of a timeout, network problem, or temporary server response.",
        "low",
    )
    add_action(
        int(audit_summary.get("field_checks") or 0),
        "offline posting pathways awaiting a field check",
        "Confirm the physical location or owner-controlled posting policy locally.",
        "low",
    )
    add_action(
        int(candidate_summary.get("priority_new_leads") or 0),
        "priority directory candidates",
        "Confirm each linked listing page before adding it to canonical data.",
        "high",
    )
    add_action(
        len(quality.get("blocking") or []),
        "blocking directory-quality findings",
        "Resolve structural findings before merging a public-directory change.",
        "high",
    )
    add_action(
        int(link_summary.get("missing_targets") or 0) + int(link_summary.get("missing_anchors") or 0),
        "broken internal routes or anchors",
        "Repair the generator route or target before deployment.",
        "high",
    )
    add_action(
        int(quality_summary.get("without_website_or_source") or 0),
        "canonical rows without a website or source URL",
        "Enrich high-value entries first; do not invent contact paths.",
        "medium",
    )
    add_action(
        int(candidate_summary.get("low_confidence_text_leads") or 0),
        "low-confidence text candidates",
        "Review only after the linked priority queue; do not publish from page text alone.",
        "low",
    )
    add_action(
        int(keyword_summary.get("entries_changed") or 0),
        "listing keyword sets proposed for review",
        "Review additions and removals in the latest keyword-sweep report before merging the keyword index.",
        "medium",
    )
    add_action(
        int(keyword_summary.get("urls_failed") or 0),
        "keyword source pages needing attention",
        "Open failed pages normally before removing retained source-derived keywords.",
        "low",
    )
    add_action(
        int(outreach_summary.get("missing_structured_fields") or 0)
        + int(outreach_summary.get("shortcuts_missing_structured_fields") or 0),
        "public directory records missing structured outreach fields",
        "Rebuild and rerun the outreach audit before deployment.",
        "high",
    )
    add_action(
        int(outreach_summary.get("without_outreach_route") or 0),
        "listings without an identified promotion route",
        "Enrich these only when a public page or direct contact supports a useful route; do not invent availability.",
        "low",
    )
    add_action(
        int(funding_watch_summary.get("changed") or 0) + int(funding_watch_summary.get("new_baselines") or 0),
        "national funding pages waiting for claim review",
        "Open each official page and confirm deadlines, eligibility, award range, application cost, fiscal-sponsor rules, and allowed uses before changing the public funding directory.",
        "high",
    )
    add_action(
        int(funding_watch_summary.get("confirmed_broken") or 0),
        "confirmed broken national funding source URLs",
        "Replace or intentionally retire each source URL without changing public program claims until a current official page is confirmed.",
        "high",
    )
    add_action(
        int(funding_watch_summary.get("check_failures") or 0),
        "national funding pages needing a normal-browser check",
        "Open these pages normally; do not treat bot blocking or a temporary network error as a closed program.",
        "low",
    )
    add_action(
        int(discovery_summary.get("candidate_links") or 0),
        "resource candidate links waiting for review",
        "Review the highest-scoring links, confirm current public details and terms of use, then add only useful entities or programs to canonical data.",
        "medium",
    )
    add_action(
        int(discovery_summary.get("confirmed_broken") or 0),
        "confirmed broken resource-discovery hubs",
        "Replace or intentionally retire each hub URL before relying on its candidate queue.",
        "high",
    )
    add_action(
        int(discovery_summary.get("check_failures") or 0),
        "resource-discovery hubs needing a normal-browser check",
        "Open these pages normally; do not remove a source because of bot blocking or a temporary request failure.",
        "low",
    )
    add_action(
        int(free_tools_summary.get("changed") or 0)
        + int(free_tools_summary.get("new_baselines") or 0)
        + int(free_tools_summary.get("term_reviews") or 0),
        "free-tool or nonprofit-offer pages waiting for wording review",
        "Confirm current free-plan limits, nonprofit eligibility, geographic availability, and provider terms before changing the public tool inventory.",
        "medium",
    )
    add_action(
        int(free_tools_summary.get("candidate_links") or 0),
        "free-tool candidate links waiting for review",
        "Open each official candidate and add it only when it fills a real guide task without duplicating an existing tool.",
        "low",
    )
    add_action(
        int(free_tools_summary.get("failed") or 0),
        "free-tool pages needing a normal-browser check",
        "Open failed pages normally; do not remove a tool solely because automation was blocked or timed out.",
        "low",
    )

    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "review_policy": "Automation detects and drafts. A person approves public claims, directory changes, contact details, funding terms, deadlines, rates, and civic guidance.",
        "inventory": {
            "canonical_resource_rows": count_csv(ROOT / "data" / "tri_county_persona_resources.csv"),
            "consolidated_directory_entries": count_csv(ROOT / "data" / "directory_of_absolutely_everything.csv"),
            "registered_update_sources": int((registry.get("counts") or {}).get("records") or 0),
            "deep_watch_sources": int(candidate_summary.get("sources_watched") or candidate_summary.get("sources") or 0),
            "keyword_index_entries": len((load_json(ROOT / "data" / "listing-keyword-index.json").get("entries") or {})),
            "outreach_review_entries": int(outreach_summary.get("entries") or 0),
            "outreach_review_shortcuts": int(outreach_summary.get("directory_shortcuts") or 0),
            "outreach_review_total": int(outreach_summary.get("total_records_reviewed") or 0),
            "national_funding_opportunities": len(funding_directory.get("opportunities") or []),
            "national_funding_watch_sources": int(funding_watch_summary.get("sources") or 0),
            "resource_discovery_sources": len(discovery_registry.get("sources") or []),
            "free_tools": len(free_tools.get("tools") or []),
            "free_tool_discovery_sources": len(free_tools.get("discovery_sources") or []),
        },
        "latest_checks": {
            "directory_quality": quality.get("status") or "not run",
            "internal_links": link_audit.get("status") or "not run",
            "source_urls_checked": int(audit_summary.get("web_checked") or audit_summary.get("checked") or 0),
            "source_urls_confirmed_broken": int(audit_summary.get("confirmed_broken") or audit_summary.get("needs_attention") or 0),
            "source_urls_browser_check": int(audit_summary.get("browser_check_needed") or 0),
            "source_urls_script_limited": int(audit_summary.get("script_access_limited") or 0),
            "source_field_checks": int(audit_summary.get("field_checks") or 0),
            "watch_pages_checked": int(candidate_summary.get("pages_checked") or 0),
            "watch_pages_failed": int(candidate_summary.get("pages_failed") or 0),
            "priority_new_leads": int(candidate_summary.get("priority_new_leads") or 0),
            "keyword_urls_checked": int(keyword_summary.get("urls_checked") or 0),
            "keyword_entries_changed": int(keyword_summary.get("entries_changed") or 0),
            "outreach_listed_routes": int(outreach_summary.get("with_listed_route") or 0),
            "outreach_ask_routes": int(outreach_summary.get("with_ask_route") or 0),
            "outreach_without_routes": int(outreach_summary.get("without_outreach_route") or 0),
            "shortcut_outreach_listed_routes": int(outreach_summary.get("shortcuts_with_listed_route") or 0),
            "shortcut_outreach_ask_routes": int(outreach_summary.get("shortcuts_with_ask_route") or 0),
            "shortcut_outreach_without_routes": int(outreach_summary.get("shortcuts_without_outreach_route") or 0),
            "funding_watch_pages_checked": int(funding_watch_summary.get("checked") or 0),
            "funding_watch_pages_changed": int(funding_watch_summary.get("changed") or 0),
            "funding_watch_new_baselines": int(funding_watch_summary.get("new_baselines") or 0),
            "funding_watch_confirmed_broken": int(funding_watch_summary.get("confirmed_broken") or 0),
            "funding_watch_check_failures": int(funding_watch_summary.get("check_failures") or 0),
            "resource_discovery_candidates": int(discovery_summary.get("candidate_links") or 0),
            "resource_discovery_changed": int(discovery_summary.get("changed") or 0),
            "resource_discovery_broken": int(discovery_summary.get("confirmed_broken") or 0),
            "resource_discovery_failures": int(discovery_summary.get("check_failures") or 0),
            "free_tool_pages_checked": int(free_tools_summary.get("checked_ok") or 0),
            "free_tool_pages_changed": int(free_tools_summary.get("changed") or 0),
            "free_tool_candidate_links": int(free_tools_summary.get("candidate_links") or 0),
            "free_tool_checks_failed": int(free_tools_summary.get("failed") or 0),
        },
        "action_queue": sorted(action_queue, key=lambda item: ({"high": 0, "medium": 1, "low": 2}[item["priority"]], -item["count"])),
    }


def write_markdown(payload: dict, path: Path) -> None:
    inventory = payload["inventory"]
    checks = payload["latest_checks"]
    lines = [
        "# Tri-County Guide Maintenance Dashboard",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["review_policy"],
        "",
        "## Inventory",
        "",
        f"- Canonical resource rows: {inventory['canonical_resource_rows']}",
        f"- Consolidated directory entries: {inventory['consolidated_directory_entries']}",
        f"- Registered update sources: {inventory['registered_update_sources']}",
        f"- Deep-watch source groups: {inventory['deep_watch_sources']}",
        f"- Listing keyword index entries: {inventory['keyword_index_entries']}",
        f"- Directory outreach rows reviewed: {inventory['outreach_review_entries']}",
        f"- Directory shortcuts reviewed: {inventory['outreach_review_shortcuts']}",
        f"- Total outreach records reviewed: {inventory['outreach_review_total']}",
        f"- Curated national funding opportunities: {inventory['national_funding_opportunities']}",
        f"- National funding watch sources: {inventory['national_funding_watch_sources']}",
        f"- Resource-discovery source hubs: {inventory['resource_discovery_sources']}",
        f"- Curated free tools and nonprofit offers: {inventory['free_tools']}",
        f"- Free-tool discovery pages: {inventory['free_tool_discovery_sources']}",
        "",
        "## Latest Checks",
        "",
        f"- Directory quality: {checks['directory_quality']}",
        f"- Internal links: {checks['internal_links']}",
        f"- Source URLs checked: {checks['source_urls_checked']}",
        f"- Confirmed broken or missing source URLs: {checks['source_urls_confirmed_broken']}",
        f"- Source URLs requiring normal-browser confirmation: {checks['source_urls_browser_check']}",
        f"- Script-access limitations (not broken): {checks['source_urls_script_limited']}",
        f"- Offline field-check records: {checks['source_field_checks']}",
        f"- Deep-watch pages checked: {checks['watch_pages_checked']}",
        f"- Deep-watch pages failed: {checks['watch_pages_failed']}",
        f"- Priority new leads: {checks['priority_new_leads']}",
        f"- Keyword source URLs checked: {checks['keyword_urls_checked']}",
        f"- Keyword sets proposed for review: {checks['keyword_entries_changed']}",
        f"- Listings with at least one listed outreach route: {checks['outreach_listed_routes']}",
        f"- Listings with at least one ask-first outreach route: {checks['outreach_ask_routes']}",
        f"- Listings without an identified outreach route: {checks['outreach_without_routes']}",
        f"- Shortcuts with at least one listed outreach route: {checks['shortcut_outreach_listed_routes']}",
        f"- Shortcuts with at least one ask-first outreach route: {checks['shortcut_outreach_ask_routes']}",
        f"- Shortcuts without an identified outreach route: {checks['shortcut_outreach_without_routes']}",
        f"- National funding pages checked: {checks['funding_watch_pages_checked']}",
        f"- National funding pages changed: {checks['funding_watch_pages_changed']}",
        f"- National funding watch baselines added: {checks['funding_watch_new_baselines']}",
        f"- Confirmed broken national funding URLs: {checks['funding_watch_confirmed_broken']}",
        f"- National funding source checks needing attention: {checks['funding_watch_check_failures']}",
        f"- Resource candidate links collected: {checks['resource_discovery_candidates']}",
        f"- Resource-discovery pages changed: {checks['resource_discovery_changed']}",
        f"- Confirmed broken resource-discovery hubs: {checks['resource_discovery_broken']}",
        f"- Resource-discovery checks needing attention: {checks['resource_discovery_failures']}",
        f"- Free-tool pages checked: {checks['free_tool_pages_checked']}",
        f"- Free-tool pages changed: {checks['free_tool_pages_changed']}",
        f"- Free-tool candidate links collected: {checks['free_tool_candidate_links']}",
        f"- Free-tool checks needing attention: {checks['free_tool_checks_failed']}",
        "",
        "## Action Queue",
        "",
    ]
    if not payload["action_queue"]:
        lines.append("No current maintenance action is reported.")
    else:
        for item in payload["action_queue"]:
            lines.append(f"- **{item['priority'].upper()} - {item['count']} {item['label']}:** {item['next_action']}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a private maintenance summary from deterministic Tri-County reports.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    payload = build_dashboard()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "maintenance-dashboard-latest.json"
    md_path = args.out_dir / "maintenance-dashboard-latest.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(payload, md_path)
    print(json.dumps({"json": str(json_path), "markdown": str(md_path), "actions": len(payload["action_queue"])}, indent=2))


if __name__ == "__main__":
    main()
