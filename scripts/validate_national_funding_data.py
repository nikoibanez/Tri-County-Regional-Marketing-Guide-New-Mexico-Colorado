from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OPPORTUNITIES = ROOT / "data" / "national-funding-opportunities.json"
DEFAULT_WATCH_SOURCES = ROOT / "data" / "national-funding-watch-sources.json"
REQUIRED_FIELDS = {
    "id",
    "name",
    "provider",
    "program_type",
    "summary",
    "source_url",
    "application_url",
    "geography",
    "audiences",
    "applicant_types",
    "deadline_type",
    "deadline_display",
    "status",
    "funding_range",
    "requires_501c3",
    "fiscal_sponsor_policy",
    "advertising_marketing_eligibility",
    "free_to_apply_or_enroll",
    "match_requirement",
    "keywords",
}
REQUIRED_KEYWORD_SIGNALS = (
    ("deadline",),
    ("funding", "no cash award"),
    ("501c3",),
    ("fiscal sponsor",),
    ("advertising", "marketing"),
    ("free", "fee", "membership required", "application cost"),
)
SWEEP_TOPICS = {
    "economic-development": "Economic development",
    "education": "Education",
    "healthcare": "Healthcare",
    "nonprofits": "Nonprofits",
    "arts-culture": "Arts & culture",
}


def valid_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate(opportunity_path: Path, watch_path: Path) -> list[str]:
    opportunity_payload = json.loads(opportunity_path.read_text(encoding="utf-8"))
    watch_payload = json.loads(watch_path.read_text(encoding="utf-8"))
    opportunities = opportunity_payload.get("opportunities") or []
    watch_sources = watch_payload.get("sources") or []
    required_sweeps = watch_payload.get("required_sweeps") or []
    errors: list[str] = []
    seen_ids: set[str] = set()

    configured_sweeps = {
        str(item.get("id") or "")
        for item in required_sweeps
        if isinstance(item, dict)
    }
    if configured_sweeps != set(SWEEP_TOPICS):
        errors.append(
            "Funding watch required_sweeps must contain exactly: "
            + ", ".join(SWEEP_TOPICS)
            + "."
        )
    if not watch_sources:
        errors.append("At least one funding watch source is required.")
    watch_ids = [str(item.get("id") or "") for item in watch_sources]
    if any(not item_id for item_id in watch_ids):
        errors.append("Every funding watch source needs an id.")
    if len(watch_ids) != len(set(watch_ids)):
        errors.append("Funding watch source IDs must be unique.")
    covered_sweeps: set[str] = set()
    for source in watch_sources:
        source_id = str(source.get("id") or "<missing id>")
        if not valid_http_url(str(source.get("url") or "")):
            errors.append(f"Watch source {source_id} has an invalid URL.")
        if int(source.get("cadence_days") or 0) <= 0:
            errors.append(f"Watch source {source_id} needs a positive cadence_days value.")
        source_sweeps = source.get("sweep_topics") or []
        if not isinstance(source_sweeps, list) or not source_sweeps:
            errors.append(f"Watch source {source_id} needs at least one sweep_topics value.")
        else:
            unsupported = sorted(set(source_sweeps) - set(SWEEP_TOPICS))
            if unsupported:
                errors.append(f"Watch source {source_id} has unsupported sweep topics: {', '.join(unsupported)}.")
            covered_sweeps.update(set(source_sweeps) & set(SWEEP_TOPICS))
        if not source.get("funding_forms"):
            errors.append(f"Watch source {source_id} needs at least one funding_forms value.")
        if not str(source.get("regional_scope") or "").strip():
            errors.append(f"Watch source {source_id} needs a regional_scope value.")
    missing_coverage = sorted(set(SWEEP_TOPICS) - covered_sweeps)
    if missing_coverage:
        errors.append(f"Funding watch sources do not cover: {', '.join(missing_coverage)}.")

    if not opportunities:
        errors.append("No regional or national funding opportunities are configured.")
    for item in opportunities:
        item_id = str(item.get("id") or "")
        missing = sorted(field for field in REQUIRED_FIELDS if item.get(field) in (None, "", []))
        if missing:
            errors.append(f"{item_id or '<missing id>'} is missing: {', '.join(missing)}.")
        if item_id in seen_ids:
            errors.append(f"Duplicate opportunity id: {item_id}.")
        seen_ids.add(item_id)
        for field in ("source_url", "application_url"):
            if not valid_http_url(str(item.get(field) or "")):
                errors.append(f"{item_id or '<missing id>'} has an invalid {field}.")
        keyword_blob = " ".join(str(value) for value in item.get("keywords") or []).casefold()
        for alternatives in REQUIRED_KEYWORD_SIGNALS:
            if not any(term in keyword_blob for term in alternatives):
                errors.append(f"{item_id or '<missing id>'} keywords need one of: {', '.join(alternatives)}.")
        for numeric_field in ("funding_min", "funding_max"):
            value = item.get(numeric_field, 0)
            if not isinstance(value, (int, float)) or value < 0:
                errors.append(f"{item_id or '<missing id>'} has an invalid {numeric_field}.")
        if item.get("funding_max", 0) and item.get("funding_min", 0) > item.get("funding_max", 0):
            errors.append(f"{item_id or '<missing id>'} funding_min exceeds funding_max.")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the curated regional and national funding directory and subject-specific watch list.")
    parser.add_argument("--opportunities", type=Path, default=DEFAULT_OPPORTUNITIES)
    parser.add_argument("--watch-sources", type=Path, default=DEFAULT_WATCH_SOURCES)
    args = parser.parse_args()
    errors = validate(args.opportunities, args.watch_sources)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    payload = json.loads(args.opportunities.read_text(encoding="utf-8"))
    watch_payload = json.loads(args.watch_sources.read_text(encoding="utf-8"))
    print(
        json.dumps(
            {
                "status": "pass",
                "opportunities": len(payload.get("opportunities") or []),
                "watch_sources": len(watch_payload.get("sources") or []),
                "subject_sweeps": len(watch_payload.get("required_sweeps") or []),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
