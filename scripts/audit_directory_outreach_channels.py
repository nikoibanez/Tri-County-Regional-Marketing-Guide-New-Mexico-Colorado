from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from directory_outreach import CHANNEL_DEFINITIONS, channel_status_map  # noqa: E402


DEFAULT_GUIDE_DATA = ROOT / "dist" / "tri-county-netlify-guide-deep" / "data" / "guide-data.json"
DEFAULT_OUT_DIR = ROOT / "review" / "directory-outreach"


def clean(value: object) -> str:
    return " ".join(str(value or "").split())


def load_guide_data(path: Path) -> tuple[list[dict], list[dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload if isinstance(payload, list) else payload.get("resources", [])
    if not isinstance(rows, list):
        raise ValueError("Guide data does not contain a resources list.")
    shortcuts = payload.get("directory_sources", []) if isinstance(payload, dict) else []
    if not isinstance(shortcuts, list):
        shortcuts = []
    return (
        [row for row in rows if isinstance(row, dict)],
        [row for row in shortcuts if isinstance(row, dict)],
    )


def build_report(rows: list[dict], source: Path, shortcuts: list[dict] | None = None) -> dict:
    shortcuts = shortcuts or []
    channel_counts = {
        definition["key"]: {"label": definition["label"], "listed": 0, "ask": 0, "not_indicated": 0}
        for definition in CHANNEL_DEFINITIONS
    }
    entries = []
    with_any_route = 0
    with_listed_route = 0
    with_ask_route = 0
    missing_structured_fields = 0

    for row in rows:
        channels = row.get("outreach_channels")
        if not isinstance(channels, list):
            channels = []
            missing_structured_fields += 1
        channels = [item for item in channels if isinstance(item, dict)]
        statuses = channel_status_map(channels)
        for key, status in statuses.items():
            channel_counts[key][status] += 1
        if channels:
            with_any_route += 1
        if any(item.get("status") == "listed" for item in channels):
            with_listed_route += 1
        if any(item.get("status") == "ask" for item in channels):
            with_ask_route += 1
        entries.append(
            {
                "entry_kind": "local_listing",
                "entry_id": clean(row.get("id")),
                "name": clean(row.get("resource_name")),
                "town": clean(row.get("town")),
                "county": clean(row.get("county")),
                "state": clean(row.get("state")),
                "listing_type": clean(row.get("public_listing_type") or row.get("resource_type")),
                "has_physical_location": str(row.get("has_physical_location") or "").casefold() == "true",
                "online_connection": clean(row.get("online_connection_group")),
                "website": clean(row.get("website")),
                "source_url": clean(row.get("source_url")),
                "channels": channels,
                "channel_status": statuses,
            }
        )

    shortcut_entries = []
    shortcuts_with_any_route = 0
    shortcuts_with_listed_route = 0
    shortcuts_with_ask_route = 0
    shortcuts_missing_structured_fields = 0
    shortcut_channel_counts = {
        definition["key"]: {"label": definition["label"], "listed": 0, "ask": 0, "not_indicated": 0}
        for definition in CHANNEL_DEFINITIONS
    }
    for row in shortcuts:
        raw_channels = row.get("outreach_channels")
        if not isinstance(raw_channels, list):
            raw_channels = []
            shortcuts_missing_structured_fields += 1
        channels = [item for item in raw_channels if isinstance(item, dict)]
        statuses = channel_status_map(channels)
        for key, status in statuses.items():
            shortcut_channel_counts[key][status] += 1
        if channels:
            shortcuts_with_any_route += 1
        if any(item.get("status") == "listed" for item in channels):
            shortcuts_with_listed_route += 1
        if any(item.get("status") == "ask" for item in channels):
            shortcuts_with_ask_route += 1
        shortcut_entries.append(
            {
                "entry_kind": "directory_shortcut",
                "entry_id": clean(row.get("id")),
                "name": clean(row.get("title")),
                "town": "",
                "county": clean(row.get("county")),
                "state": "",
                "listing_type": clean(row.get("kind")),
                "has_physical_location": False,
                "online_connection": "Directory shortcut",
                "website": clean(row.get("url")),
                "source_url": clean(row.get("url")),
                "channels": channels,
                "channel_status": statuses,
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source.resolve()),
        "summary": {
            "entries": len(entries),
            "directory_shortcuts": len(shortcut_entries),
            "total_records_reviewed": len(entries) + len(shortcut_entries),
            "with_any_route": with_any_route,
            "with_listed_route": with_listed_route,
            "with_ask_route": with_ask_route,
            "without_outreach_route": len(entries) - with_any_route,
            "missing_structured_fields": missing_structured_fields,
            "shortcuts_with_any_route": shortcuts_with_any_route,
            "shortcuts_with_listed_route": shortcuts_with_listed_route,
            "shortcuts_with_ask_route": shortcuts_with_ask_route,
            "shortcuts_without_outreach_route": len(shortcut_entries) - shortcuts_with_any_route,
            "shortcuts_missing_structured_fields": shortcuts_missing_structured_fields,
            "channel_counts": channel_counts,
            "shortcut_channel_counts": shortcut_channel_counts,
        },
        "definitions": list(CHANNEL_DEFINITIONS),
        "entries": entries,
        "shortcuts": shortcut_entries,
    }


def status_cell(entry: dict, key: str) -> str:
    status = entry["channel_status"].get(key, "not_indicated")
    matching = next((item for item in entry["channels"] if item.get("key") == key), None)
    if not matching:
        return "Not indicated"
    status_label = matching.get("status_label") or ("Listed route" if status == "listed" else "Ask first")
    return f"{status_label}: {matching.get('label') or matching.get('channel') or key}"


def write_csv(payload: dict, path: Path) -> None:
    channel_keys = [definition["key"] for definition in CHANNEL_DEFINITIONS]
    fieldnames = [
        "entry_kind",
        "entry_id",
        "name",
        "town",
        "county",
        "state",
        "listing_type",
        "has_physical_location",
        "online_connection",
        "website",
        "source_url",
        *channel_keys,
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for entry in payload["entries"] + payload.get("shortcuts", []):
            row = {key: entry.get(key, "") for key in fieldnames if key not in channel_keys}
            row.update({key: status_cell(entry, key) for key in channel_keys})
            writer.writerow(row)


def write_markdown(payload: dict, path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# Directory Outreach Channel Review",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "This report reviews every published directory listing for practical physical and digital outreach routes. A listed route means the attached listing information identifies that kind of channel. Ask first means the entity may be a sensible contact, but placement, sharing, price, eligibility, and acceptance are not promised.",
        "",
        "## Summary",
        "",
        f"- Published listings reviewed: {summary['entries']}",
        f"- Directory shortcuts reviewed: {summary['directory_shortcuts']}",
        f"- Total directory records reviewed: {summary['total_records_reviewed']}",
        f"- Listings with at least one outreach route: {summary['with_any_route']}",
        f"- Listings with at least one listed route: {summary['with_listed_route']}",
        f"- Listings with at least one ask-first route: {summary['with_ask_route']}",
        f"- Listings without an identified outreach route: {summary['without_outreach_route']}",
        f"- Listings missing structured outreach fields: {summary['missing_structured_fields']}",
        f"- Directory shortcuts with a listed or ask-first route: {summary['shortcuts_with_any_route']}",
        f"- Directory shortcuts without an identified route: {summary['shortcuts_without_outreach_route']}",
        f"- Directory shortcuts missing structured outreach fields: {summary['shortcuts_missing_structured_fields']}",
        "",
        "## Channel Coverage",
        "",
        "| Channel | Listed route | Ask first | Not indicated |",
        "| --- | ---: | ---: | ---: |",
    ]
    for definition in CHANNEL_DEFINITIONS:
        counts = summary["channel_counts"][definition["key"]]
        lines.append(
            f"| {definition['label']} | {counts['listed']} | {counts['ask']} | {counts['not_indicated']} |"
        )

    lines.extend(
        [
            "",
            "## Directory Shortcut Coverage",
            "",
            "| Channel | Listed route | Ask first | Not indicated |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for definition in CHANNEL_DEFINITIONS:
        counts = summary["shortcut_channel_counts"][definition["key"]]
        lines.append(
            f"| {definition['label']} | {counts['listed']} | {counts['ask']} | {counts['not_indicated']} |"
        )

    no_routes = [entry for entry in payload["entries"] if not entry["channels"]]
    lines.extend(["", "## Listings Without An Identified Route", ""])
    if not no_routes:
        lines.append("Every listing has at least one listed or ask-first route.")
    else:
        for entry in no_routes:
            place = ", ".join(part for part in (entry["town"], entry["county"], entry["state"]) if part) or "Region not listed"
            lines.append(f"- {entry['name']} - {place}; {entry['listing_type'] or 'Listing type not provided'}")
    lines.extend(
        [
            "",
            "## Review Boundary",
            "",
            "The CSV and JSON contain all listing-level statuses. Do not convert an ask-first route into an availability claim without checking the owner-controlled page or contacting the organization directly.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Review every published listing for physical and digital outreach channels.")
    parser.add_argument("--guide-data", type=Path, default=DEFAULT_GUIDE_DATA)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--fail-on-missing", action="store_true")
    args = parser.parse_args()

    rows, shortcuts = load_guide_data(args.guide_data)
    payload = build_report(rows, args.guide_data, shortcuts)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "directory-outreach-latest.json"
    csv_path = args.out_dir / "directory-outreach-latest.csv"
    md_path = args.out_dir / "directory-outreach-latest.md"
    compact_payload = {key: value for key, value in payload.items() if key not in {"entries", "shortcuts"}}
    json_path.write_text(json.dumps(compact_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(payload, csv_path)
    write_markdown(payload, md_path)
    print(json.dumps({"summary": payload["summary"], "json": str(json_path), "csv": str(csv_path), "markdown": str(md_path)}, indent=2))
    if args.fail_on_missing and (
        payload["summary"]["missing_structured_fields"]
        or payload["summary"]["shortcuts_missing_structured_fields"]
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
