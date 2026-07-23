from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

from directory_exclusions import (
    EXCLUDED_DIRECTORY_ENTITIES,
    filter_excluded_directory_rows,
    references_excluded_directory_entity,
    row_references_excluded_directory_entity,
)


ROOT = Path(__file__).resolve().parents[1]

CSV_PATHS = (
    ROOT / "data" / "tri_county_persona_resources.csv",
    ROOT / "data" / "directory_of_absolutely_everything.csv",
    ROOT / "dist" / "site" / "data" / "tri_county_persona_resources.csv",
    ROOT / "dist" / "site" / "data" / "directory_of_absolutely_everything.csv",
)

JSON_PATHS = (
    ROOT / "data" / "tri_county_persona_resources.json",
    ROOT / "data" / "directory_of_absolutely_everything.json",
    ROOT / "data" / "directory-metadata.json",
    ROOT / "data" / "listing-keyword-index.json",
    ROOT / "data" / "guide-data.json",
    ROOT / "review" / "DIRECTORY_RAW_PROVENANCE_SNAPSHOT_20260701.json",
    ROOT / "dist" / "site" / "data" / "tri_county_persona_resources.json",
    ROOT / "dist" / "site" / "data" / "directory_of_absolutely_everything.json",
    ROOT / "dist" / "site" / "data" / "directory-metadata.json",
    ROOT / "dist" / "site" / "data" / "guide-data.json",
)

SITE_DATA_PATHS = (
    ROOT / "assets" / "site-data.js",
    ROOT / "dist" / "site" / "assets" / "site-data.js",
)

MARKDOWN_PATHS = (
    ROOT / "review" / "DIGITAL_ONLY_CREATIVE_DIRECTORY_EXPANSION_20260627.md",
)


def entity_record(value: dict) -> bool:
    return bool({"id", "entry_id", "resource_name", "name", "title"} & set(value))


def scrub_payload(value: object) -> object:
    if isinstance(value, list):
        cleaned = []
        for item in value:
            if isinstance(item, dict) and row_references_excluded_directory_entity(item):
                continue
            if isinstance(item, str) and references_excluded_directory_entity(item):
                continue
            cleaned.append(scrub_payload(item))
        return cleaned
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            if references_excluded_directory_entity(key):
                continue
            if isinstance(item, dict) and entity_record(item) and row_references_excluded_directory_entity(item):
                continue
            cleaned[key] = scrub_payload(item)
        refresh_counts(cleaned)
        return cleaned
    return value


def refresh_counts(payload: dict) -> None:
    entries = payload.get("entries")
    if isinstance(entries, list) and "entry_count" in payload:
        shortcut_count = sum(1 for item in entries if item.get("entry_kind") == "directory_shortcut")
        payload["entry_count"] = len(entries)
        payload["shortcut_count"] = shortcut_count
        payload["local_inventory_count"] = len(entries) - shortcut_count

    resources = payload.get("resources")
    summary = payload.get("summary")
    if isinstance(resources, list) and isinstance(summary, dict):
        summary["row_count"] = len(resources)
        summary["county"] = dict(Counter(item.get("county") or "Unknown" for item in resources).most_common())
        type_key = "public_listing_type" if any(item.get("public_listing_type") for item in resources) else "resource_type"
        summary["resource_type"] = dict(Counter(item.get(type_key) or "Resource" for item in resources).most_common())
        for field, summary_key in (("goal_relevance", "goal"), ("audience_served", "audience")):
            counts: Counter[str] = Counter()
            for item in resources:
                for part in str(item.get(field) or "").split(";"):
                    if part.strip():
                        counts[part.strip()] += 1
            summary[summary_key] = dict(counts.most_common())

    metadata = payload.get("directory_metadata")
    if isinstance(metadata, dict) and isinstance(resources, list):
        metadata["local_inventory_count"] = len(resources)
        metadata["entry_count"] = int(metadata.get("shortcut_count") or 0) + len(resources)


def scrub_csv(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    cleaned = filter_excluded_directory_rows(rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned)
    return len(rows) - len(cleaned)


def scrub_json(path: Path) -> int:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    before = json.dumps(payload, ensure_ascii=False)
    cleaned = scrub_payload(payload)
    path.write_text(json.dumps(cleaned, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return int(references_excluded_directory_entity(before))


def scrub_site_data(path: Path) -> int:
    source = path.read_text(encoding="utf-8-sig")
    prefix = "window.TRI_COUNTY_GUIDE_DATA = "
    if not source.startswith(prefix):
        raise ValueError(f"Unexpected site-data format: {path}")
    payload = json.loads(source[len(prefix) :].rstrip().removesuffix(";"))
    contained = row_references_excluded_directory_entity(payload)
    cleaned = scrub_payload(payload)
    path.write_text(prefix + json.dumps(cleaned, ensure_ascii=False) + ";\n", encoding="utf-8")
    return int(contained)


def scrub_generated_html(path: Path) -> int:
    source = path.read_text(encoding="utf-8-sig")
    cleaned = source
    removals = 0
    for name in EXCLUDED_DIRECTORY_ENTITIES:
        escaped = re.escape(name)
        for pattern in (
            rf"<article\b[^>]*>(?:(?!</article>).)*?{escaped}(?:(?!</article>).)*?</article>",
            rf"<tr\b[^>]*>(?:(?!</tr>).)*?{escaped}(?:(?!</tr>).)*?</tr>",
        ):
            cleaned, count = re.subn(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)
            removals += count
    if references_excluded_directory_entity(cleaned):
        raise ValueError(f"Excluded organization remains in generated HTML: {path}")
    if cleaned != source:
        path.write_text(cleaned, encoding="utf-8")
    return removals


def scrub_markdown(path: Path) -> int:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    cleaned = [line for line in lines if not references_excluded_directory_entity(line)]
    path.write_text("\n".join(cleaned).rstrip() + "\n", encoding="utf-8")
    return len(lines) - len(cleaned)


def public_artifact_matches() -> list[str]:
    matches = []
    roots = (ROOT / "data", ROOT / "assets", ROOT / "dist" / "site", ROOT / "dist" / "tri-county-netlify-guide-deep")
    allowed_suffixes = {".csv", ".html", ".js", ".json", ".md", ".txt", ".xml"}
    for root in roots:
        if not root.exists():
            continue
        paths = [root] if root.is_file() else root.rglob("*")
        for path in paths:
            if not path.is_file() or path.suffix.casefold() not in allowed_suffixes:
                continue
            try:
                source = path.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeDecodeError):
                continue
            if references_excluded_directory_entity(source):
                matches.append(str(path.relative_to(ROOT)))
    return sorted(set(matches))


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove permanently excluded organizations from directory data and generated artifacts.")
    parser.add_argument("--check", action="store_true", help="Only check public artifacts; do not rewrite files.")
    args = parser.parse_args()

    if args.check:
        matches = public_artifact_matches()
        print(json.dumps({"status": "pass" if not matches else "fail", "matches": matches}, indent=2))
        if matches:
            raise SystemExit(1)
        return

    changed: dict[str, int] = {}
    for path in CSV_PATHS:
        if path.exists():
            changed[str(path.relative_to(ROOT))] = scrub_csv(path)
    for path in JSON_PATHS:
        if path.exists():
            changed[str(path.relative_to(ROOT))] = scrub_json(path)
    for path in SITE_DATA_PATHS:
        if path.exists():
            changed[str(path.relative_to(ROOT))] = scrub_site_data(path)
    for path in MARKDOWN_PATHS:
        if path.exists():
            changed[str(path.relative_to(ROOT))] = scrub_markdown(path)
    legacy_site = ROOT / "dist" / "site"
    if legacy_site.exists():
        for path in legacy_site.rglob("*.html"):
            if references_excluded_directory_entity(path.read_text(encoding="utf-8-sig")):
                changed[str(path.relative_to(ROOT))] = scrub_generated_html(path)

    matches = public_artifact_matches()
    print(json.dumps({"status": "pass" if not matches else "fail", "changed": changed, "remaining": matches}, indent=2))
    if matches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
