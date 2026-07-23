from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from directory_exclusions import row_references_excluded_directory_entity  # noqa: E402

DEFAULT_SOURCE = ROOT / "data" / "tri_county_persona_resources.csv"
DEFAULT_DIRECTORY = ROOT / "data" / "directory_of_absolutely_everything.csv"
DEFAULT_GUIDE_DATA = ROOT / "dist" / "tri-county-netlify-guide-deep" / "data" / "guide-data.json"
DEFAULT_OUT_DIR = ROOT / "review" / "maintenance"

SOURCE_REQUIRED = {
    "resource_name",
    "category",
    "town",
    "county",
    "website",
    "source_url",
    "resource_type",
}

DIRECTORY_REQUIRED = {
    "name",
    "county",
    "town",
    "category",
    "entry_type",
    "description",
    "websites",
    "emails",
    "phones",
    "addresses",
    "source_urls",
    "audiences",
    "keywords",
    "marketing_channels",
}

PUBLIC_REQUIRED = {
    "resource_name",
    "county",
    "town",
    "public_description",
    "public_keywords",
    "public_listing_type",
}

GENERALIZED_IDEAS = {
    "community groups and digital bulletin boards",
    "main street chamber pages",
    "official city county pages",
    "tourism offices and visitor facing pages",
    "tourism pages",
    "tourism websites google business profiles social pages and email newsletters",
}

GENERIC_DESCRIPTION_PATTERNS = (
    r"visitor-facing listing from a public tourism or travel source",
    r"use this as a starting contact",
    r"open a source link when available",
    r"send an update if details have changed",
    r"use as a launch/outreach lead",
)


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_name(value: object) -> str:
    text = unicodedata.normalize("NFKD", clean(value))
    text = text.encode("ascii", "ignore").decode("ascii").lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def load_csv(path: Path, required: set[str]) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], [f"Missing file: {path}"]
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = sorted(required - fields)
        rows = list(reader)
    errors = [f"{path.name} is missing required column: {field}" for field in missing]
    return rows, errors


def load_public_resources(path: Path) -> tuple[list[dict], list[str]]:
    if not path.exists():
        return [], [f"Missing generated guide data: {path}. Build the site before running directory QA."]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [], [f"Unable to read generated guide data: {exc}"]
    rows = payload.get("resources") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return [], ["Generated guide data does not contain a resources list."]
    fields = set().union(*(row.keys() for row in rows if isinstance(row, dict))) if rows else set()
    errors = [f"Generated public resources are missing required field: {field}" for field in sorted(PUBLIC_REQUIRED - fields)]
    return [row for row in rows if isinstance(row, dict)], errors


def duplicate_groups(rows: list[dict[str, str]], name_field: str, include_place: bool = True) -> list[list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        parts = [normalize_name(row.get(name_field))]
        if include_place:
            parts.extend([normalize_name(row.get("town")), normalize_name(row.get("county"))])
        groups["|".join(parts)].append(row)
    return [group for key, group in groups.items() if key.strip("|") and len(group) > 1]


def sample_names(rows: list[dict[str, str]], field: str, limit: int = 20) -> list[str]:
    return sorted({clean(row.get(field)) for row in rows if clean(row.get(field))}, key=str.casefold)[:limit]


def assess(source_path: Path, directory_path: Path, guide_data_path: Path = DEFAULT_GUIDE_DATA) -> dict:
    source_rows, source_errors = load_csv(source_path, SOURCE_REQUIRED)
    directory_rows, directory_errors = load_csv(directory_path, DIRECTORY_REQUIRED)
    public_rows, public_errors = load_public_resources(guide_data_path)
    blocking = source_errors + directory_errors + public_errors

    excluded_source_rows = [row for row in source_rows if row_references_excluded_directory_entity(row)]
    excluded_directory_rows = [row for row in directory_rows if row_references_excluded_directory_entity(row)]
    excluded_public_rows = [row for row in public_rows if row_references_excluded_directory_entity(row)]

    blank_source_names = [row for row in source_rows if not clean(row.get("resource_name"))]
    source_duplicate_groups = duplicate_groups(source_rows, "resource_name")
    source_no_link = [row for row in source_rows if not clean(row.get("website")) and not clean(row.get("source_url"))]

    blank_directory_names = [row for row in directory_rows if not clean(row.get("name"))]
    directory_duplicate_groups = duplicate_groups(directory_rows, "name")
    directory_name_only_duplicates = duplicate_groups(directory_rows, "name", include_place=False)
    concept_rows = [row for row in directory_rows if normalize_name(row.get("name")) in GENERALIZED_IDEAS]
    missing_description = [row for row in directory_rows if not clean(row.get("description"))]
    generic_descriptions = [
        row
        for row in directory_rows
        if any(re.search(pattern, clean(row.get("description")), flags=re.I) for pattern in GENERIC_DESCRIPTION_PATTERNS)
    ]
    missing_keywords = [row for row in directory_rows if not clean(row.get("keywords"))]
    missing_audiences = [row for row in directory_rows if not clean(row.get("audiences"))]
    missing_channels = [row for row in directory_rows if not clean(row.get("marketing_channels"))]
    missing_entry_type = [row for row in directory_rows if not clean(row.get("entry_type"))]
    no_direct_contact = [
        row
        for row in directory_rows
        if not any(clean(row.get(field)) for field in ("websites", "emails", "phones", "addresses"))
    ]
    no_contact_or_source = [row for row in no_direct_contact if not clean(row.get("source_urls"))]

    blank_public_names = [row for row in public_rows if not clean(row.get("resource_name"))]
    public_duplicate_groups = duplicate_groups(public_rows, "resource_name")
    public_concept_rows = [row for row in public_rows if normalize_name(row.get("resource_name")) in GENERALIZED_IDEAS]
    public_missing_description = [row for row in public_rows if not clean(row.get("public_description"))]
    public_generic_descriptions = [
        row
        for row in public_rows
        if any(re.search(pattern, clean(row.get("public_description")), flags=re.I) for pattern in GENERIC_DESCRIPTION_PATTERNS)
    ]
    public_missing_keywords = [row for row in public_rows if not clean(row.get("public_keywords"))]
    public_missing_type = [row for row in public_rows if not clean(row.get("public_listing_type"))]

    if blank_source_names:
        blocking.append(f"Canonical source has {len(blank_source_names)} blank resource names.")
    if excluded_source_rows:
        blocking.append(f"Canonical source contains {len(excluded_source_rows)} explicitly excluded organization rows.")
    if excluded_directory_rows:
        blocking.append(f"Consolidated directory contains {len(excluded_directory_rows)} explicitly excluded organization rows.")
    if excluded_public_rows:
        blocking.append(f"Published directory contains {len(excluded_public_rows)} explicitly excluded organization rows.")
    if source_duplicate_groups:
        blocking.append(f"Canonical source has {len(source_duplicate_groups)} exact name/place duplicate groups.")
    if blank_directory_names:
        blocking.append(f"Consolidated directory has {len(blank_directory_names)} blank names.")
    if blank_public_names:
        blocking.append(f"Published directory has {len(blank_public_names)} blank listing names.")
    if public_duplicate_groups:
        blocking.append(f"Published directory has {len(public_duplicate_groups)} exact name/place duplicate groups.")
    if public_concept_rows:
        blocking.append(f"Published directory has {len(public_concept_rows)} generalized ideas presented as listings.")
    if public_missing_description:
        blocking.append(f"Published directory has {len(public_missing_description)} entries without descriptions.")
    if public_generic_descriptions:
        blocking.append(f"Published directory has {len(public_generic_descriptions)} generic placeholder descriptions.")
    if public_missing_keywords:
        blocking.append(f"Published directory has {len(public_missing_keywords)} entries without search keywords.")
    if public_missing_type:
        blocking.append(f"Published directory has {len(public_missing_type)} entries without an entity type.")

    warnings: list[str] = []
    if source_no_link:
        warnings.append(f"{len(source_no_link)} canonical rows lack both a website and source URL; prioritize contact enrichment.")
    if no_direct_contact:
        warnings.append(f"{len(no_direct_contact)} consolidated entries rely on a source route instead of direct contact details.")
    if directory_name_only_duplicates:
        warnings.append(
            f"{len(directory_name_only_duplicates)} names occur in more than one place; review aliases before merging across towns."
        )
    if directory_duplicate_groups or concept_rows or missing_description or generic_descriptions or missing_keywords or missing_audiences or missing_channels or missing_entry_type or no_contact_or_source:
        warnings.append(
            "The legacy 688-row consolidated export still contains structural cleanup work. It is not the active Network data source; keep it internal until rebuilt from published rows."
        )

    return {
        "generated_at": date.today().isoformat(),
        "status": "pass" if not blocking else "fail",
        "blocking": blocking,
        "warnings": warnings,
        "canonical_source": {
            "path": str(source_path),
            "rows": len(source_rows),
            "excluded_organization_rows": len(excluded_source_rows),
            "blank_names": len(blank_source_names),
            "exact_name_place_duplicate_groups": len(source_duplicate_groups),
            "without_website_or_source": len(source_no_link),
            "without_phone": sum(1 for row in source_rows if not clean(row.get("contact_phone"))),
            "without_email": sum(1 for row in source_rows if not clean(row.get("contact_email"))),
            "without_address": sum(1 for row in source_rows if not clean(row.get("physical_address"))),
            "contact_enrichment_sample": sample_names(source_no_link, "resource_name"),
        },
        "published_directory": {
            "path": str(guide_data_path),
            "rows": len(public_rows),
            "excluded_organization_rows": len(excluded_public_rows),
            "blank_names": len(blank_public_names),
            "exact_name_place_duplicate_groups": len(public_duplicate_groups),
            "generalized_idea_rows": len(public_concept_rows),
            "generic_descriptions": len(public_generic_descriptions),
            "missing_descriptions": len(public_missing_description),
            "missing_keywords": len(public_missing_keywords),
            "missing_entry_type": len(public_missing_type),
            "generalized_idea_sample": sample_names(public_concept_rows, "resource_name"),
            "generic_description_sample": sample_names(public_generic_descriptions, "resource_name"),
        },
        "consolidated_directory": {
            "path": str(directory_path),
            "rows": len(directory_rows),
            "excluded_organization_rows": len(excluded_directory_rows),
            "blank_names": len(blank_directory_names),
            "exact_name_place_duplicate_groups": len(directory_duplicate_groups),
            "name_only_duplicate_groups": len(directory_name_only_duplicates),
            "generalized_idea_rows": len(concept_rows),
            "generic_descriptions": len(generic_descriptions),
            "missing_descriptions": len(missing_description),
            "missing_keywords": len(missing_keywords),
            "missing_audiences": len(missing_audiences),
            "missing_marketing_channels": len(missing_channels),
            "missing_entry_type": len(missing_entry_type),
            "without_direct_contact": len(no_direct_contact),
            "without_contact_or_source": len(no_contact_or_source),
            "generalized_idea_sample": sample_names(concept_rows, "name"),
            "generic_description_sample": sample_names(generic_descriptions, "name"),
        },
    }


def write_markdown(payload: dict, path: Path) -> None:
    canonical = payload["canonical_source"]
    published = payload["published_directory"]
    directory = payload["consolidated_directory"]
    lines = [
        "# Directory Quality Report",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        f"Status: **{payload['status'].upper()}**",
        "",
        "## Blocking Findings",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["blocking"] or ["None."])
    lines.extend(["", "## Maintenance Warnings", ""])
    lines.extend(f"- {item}" for item in payload["warnings"] or ["None."])
    lines.extend(
        [
            "",
            "## Canonical Resource Rows",
            "",
            f"- Rows: {canonical['rows']}",
            f"- Explicitly excluded organization rows: {canonical['excluded_organization_rows']}",
            f"- Exact name/place duplicate groups: {canonical['exact_name_place_duplicate_groups']}",
            f"- Without website or source URL: {canonical['without_website_or_source']}",
            f"- Without phone: {canonical['without_phone']}",
            f"- Without email: {canonical['without_email']}",
            f"- Without address: {canonical['without_address']}",
            "",
            "## Published Network Directory",
            "",
            f"- Entries: {published['rows']}",
            f"- Explicitly excluded organization rows: {published['excluded_organization_rows']}",
            f"- Exact name/place duplicate groups: {published['exact_name_place_duplicate_groups']}",
            f"- Generalized ideas presented as listings: {published['generalized_idea_rows']}",
            f"- Generic descriptions: {published['generic_descriptions']}",
            f"- Missing descriptions: {published['missing_descriptions']}",
            f"- Missing keywords: {published['missing_keywords']}",
            f"- Missing entity types: {published['missing_entry_type']}",
            "",
            "## Legacy Consolidated Export",
            "",
            f"- Entries: {directory['rows']}",
            f"- Explicitly excluded organization rows: {directory['excluded_organization_rows']}",
            f"- Exact name/place duplicate groups: {directory['exact_name_place_duplicate_groups']}",
            f"- Generalized ideas presented as listings: {directory['generalized_idea_rows']}",
            f"- Generic descriptions: {directory['generic_descriptions']}",
            f"- Missing descriptions: {directory['missing_descriptions']}",
            f"- Missing keywords: {directory['missing_keywords']}",
            f"- Missing audiences: {directory['missing_audiences']}",
            f"- Missing marketing channels: {directory['missing_marketing_channels']}",
            f"- Without direct contact details: {directory['without_direct_contact']}",
            f"- Without contact details or source route: {directory['without_contact_or_source']}",
            "",
            "Warnings are enrichment priorities, not reasons to hide otherwise useful listings. Blocking findings protect the public directory from structural regressions.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Tri-County directory structure and public-card completeness.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--guide-data", type=Path, default=DEFAULT_GUIDE_DATA)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--fail-on-blocking", action="store_true")
    args = parser.parse_args()

    payload = assess(args.source, args.directory, args.guide_data)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "directory-quality-latest.json"
    md_path = args.out_dir / "directory-quality-latest.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(payload, md_path)
    print(json.dumps({"status": payload["status"], "json": str(json_path), "markdown": str(md_path)}, indent=2))

    if args.fail_on_blocking and payload["blocking"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
