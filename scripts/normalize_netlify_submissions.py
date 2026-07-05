from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "review" / "submission-review"


def clean(value: object) -> str:
    return str(value or "").strip()


def classify(row: dict) -> str:
    blob = " ".join(clean(value).lower() for value in row.values())
    if any(term in blob for term in ("grant", "funding", "scholarship", "stipend", "loan")):
        return "funding"
    if any(term in blob for term in ("correction", "remove", "outdated", "wrong")):
        return "correction"
    if any(term in blob for term in ("event", "calendar")):
        return "event"
    if any(term in blob for term in ("artist", "creative", "gallery", "venue")):
        return "creative"
    return "listing"


def normalize(row: dict) -> dict:
    return {
        "received_at": clean(row.get("created_at") or row.get("Created At") or row.get("date")),
        "submission_type": clean(row.get("submission_type") or row.get("Submission type")),
        "guide_section": clean(row.get("guide_section") or row.get("Guide section")),
        "county_or_region": clean(row.get("county_or_region") or row.get("County or region")),
        "community": clean(row.get("community") or row.get("Community or service area")),
        "listing_name": clean(row.get("listing_name") or row.get("Name to list")),
        "category": clean(row.get("category") or row.get("Category")),
        "source_url": clean(row.get("source_url") or row.get("Website or public source link")),
        "contact_email": clean(row.get("contact_email") or row.get("Contact email")),
        "short_description": clean(row.get("short_description") or row.get("Short public description")),
        "reader_action": clean(row.get("reader_action") or row.get("Reader action")),
        "verification_notes": clean(row.get("verification_notes") or row.get("Verification notes")),
        "submitter_email": clean(row.get("submitter_email") or row.get("Your email")),
        "review_bucket": classify(row),
        "recommended_status": "user_submitted_pending_review",
    }


def write_markdown(rows: list[dict], path: Path) -> None:
    lines = [
        "# Netlify Submission Review",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "Submissions are review requests, not automatic publication approvals.",
        "",
        f"Total submissions: {len(rows)}",
        "",
    ]
    for idx, row in enumerate(rows, start=1):
        lines.extend(
            [
                f"## {idx}. {row['listing_name'] or 'Untitled submission'}",
                "",
                f"- Bucket: {row['review_bucket']}",
                f"- County/region: {row['county_or_region']}",
                f"- Section: {row['guide_section']}",
                f"- Source URL: {row['source_url'] or 'Needs source'}",
                f"- Submitter: {row['submitter_email'] or 'Not supplied'}",
                "",
                row["short_description"] or "No description supplied.",
                "",
                f"Reader action: {row['reader_action'] or 'Needs review'}",
                "",
                f"Verification notes: {row['verification_notes'] or 'Needs review'}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize exported Netlify form submissions into a review queue.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    with args.csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [normalize(row) for row in csv.DictReader(handle)]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / f"submissions-{date.today().isoformat()}.json"
    md_path = args.out_dir / f"submissions-{date.today().isoformat()}.md"
    json_path.write_text(json.dumps({"generated_at": date.today().isoformat(), "submissions": rows}, indent=2), encoding="utf-8")
    write_markdown(rows, md_path)
    print(json.dumps({"json": str(json_path), "markdown": str(md_path), "submissions": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
