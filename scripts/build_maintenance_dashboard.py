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
    quality = load_json(DEFAULT_OUT_DIR / "directory-quality-latest.json")
    link_audit = load_json(DEFAULT_OUT_DIR / "internal-link-audit-latest.json")

    candidate_summary = candidates.get("summary") or directory_watch.get("summary") or {}
    audit_summary = source_audit.get("summary") or {}
    quality_summary = quality.get("canonical_source") or {}
    public_quality = quality.get("published_directory") or quality.get("consolidated_directory") or {}
    link_summary = link_audit.get("summary") or {}
    keyword_summary = keyword_sweep.get("summary") or {}
    action_queue = []

    def add_action(count: int, label: str, next_action: str, priority: str) -> None:
        if count:
            action_queue.append({"priority": priority, "count": count, "label": label, "next_action": next_action})

    add_action(
        int(audit_summary.get("needs_attention") or 0),
        "monitored sources needing attention",
        "Open the latest source-audit report and confirm failures in a normal browser.",
        "high",
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

    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "review_policy": "Automation detects and drafts. A person approves public claims, directory changes, contact details, funding terms, deadlines, rates, and civic guidance.",
        "inventory": {
            "canonical_resource_rows": count_csv(ROOT / "data" / "tri_county_persona_resources.csv"),
            "consolidated_directory_entries": count_csv(ROOT / "data" / "directory_of_absolutely_everything.csv"),
            "registered_update_sources": int((registry.get("counts") or {}).get("records") or 0),
            "deep_watch_sources": int(candidate_summary.get("sources_watched") or candidate_summary.get("sources") or 0),
            "keyword_index_entries": len((load_json(ROOT / "data" / "listing-keyword-index.json").get("entries") or {})),
        },
        "latest_checks": {
            "directory_quality": quality.get("status") or "not run",
            "internal_links": link_audit.get("status") or "not run",
            "source_urls_checked": int(audit_summary.get("checked") or 0),
            "source_urls_needing_attention": int(audit_summary.get("needs_attention") or 0),
            "watch_pages_checked": int(candidate_summary.get("pages_checked") or 0),
            "watch_pages_failed": int(candidate_summary.get("pages_failed") or 0),
            "priority_new_leads": int(candidate_summary.get("priority_new_leads") or 0),
            "keyword_urls_checked": int(keyword_summary.get("urls_checked") or 0),
            "keyword_entries_changed": int(keyword_summary.get("entries_changed") or 0),
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
        "",
        "## Latest Checks",
        "",
        f"- Directory quality: {checks['directory_quality']}",
        f"- Internal links: {checks['internal_links']}",
        f"- Source URLs checked: {checks['source_urls_checked']}",
        f"- Source URLs needing attention: {checks['source_urls_needing_attention']}",
        f"- Deep-watch pages checked: {checks['watch_pages_checked']}",
        f"- Deep-watch pages failed: {checks['watch_pages_failed']}",
        f"- Priority new leads: {checks['priority_new_leads']}",
        f"- Keyword source URLs checked: {checks['keyword_urls_checked']}",
        f"- Keyword sets proposed for review: {checks['keyword_entries_changed']}",
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
