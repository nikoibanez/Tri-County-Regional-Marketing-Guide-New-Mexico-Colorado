from __future__ import annotations

import hashlib
import json
import re
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
GUIDE_DATA = ROOT / "dist" / "tri-county-netlify-guide-deep" / "data" / "guide-data.json"
OUTPUT = ROOT / "data" / "update-source-registry.json"
MARKDOWN_OUTPUT = ROOT / "data" / "update-source-registry.md"


WEEKLY_TERMS = (
    "grant",
    "funding",
    "scholarship",
    "stipend",
    "calendar",
    "event",
    "newsletter",
    "public notice",
    "jobs",
    "bid",
    "rfp",
)

MONTHLY_TERMS = (
    "chamber",
    "tourism",
    "media",
    "directory",
    "creative",
    "economic",
    "nonprofit",
    "business",
    "posting",
)

HIGH_RISK_TERMS = (
    "grant",
    "funding",
    "scholarship",
    "stipend",
    "loan",
    "incentive",
    "permit",
    "license",
    "legal",
    "public notice",
    "advertising",
    "paid",
    "deadline",
    "eligibility",
)


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or "source"


def stable_id(prefix: str, title: str, url: str) -> str:
    digest = hashlib.sha1(f"{title}|{url}".encode("utf-8")).hexdigest()[:8]
    return f"{prefix}-{slugify(title)[:54]}-{digest}"


def text_blob(item: dict) -> str:
    return " ".join(str(value) for value in item.values() if value).lower()


def cadence_days(item: dict) -> int:
    blob = text_blob(item)
    if any(term in blob for term in WEEKLY_TERMS):
        return 7
    if any(term in blob for term in MONTHLY_TERMS):
        return 30
    return 90


def review_level(item: dict) -> str:
    blob = text_blob(item)
    if any(term in blob for term in HIGH_RISK_TERMS):
        return "human_approval_required"
    if item.get("verification_status") == "Needs field check":
        return "manual_verification_needed"
    return "standard_review"


def update_domain(item: dict) -> str:
    blob = text_blob(item)
    if any(term in blob for term in ("grant", "funding", "scholarship", "stipend", "loan", "incentive")):
        return "funding"
    if any(term in blob for term in ("calendar", "event", "submit event")):
        return "events"
    if any(term in blob for term in ("newspaper", "media", "radio", "newsletter", "social")):
        return "media"
    if any(term in blob for term in ("chamber", "directory", "business")):
        return "directory"
    if any(term in blob for term in ("creative", "arts", "gallery", "artist")):
        return "creative"
    if any(term in blob for term in ("public notice", "posting", "clerk", "permit", "license")):
        return "civic"
    return "general"


def hostname(url: str) -> str:
    if not url:
        return ""
    return urlparse(url).netloc.lower().removeprefix("www.")


def normalize_directory_source(item: dict) -> dict:
    title = item.get("title", "").strip()
    url = item.get("url", "").strip()
    days = cadence_days(item)
    return {
        "id": stable_id("directory", title, url),
        "source_group": "directory_sources",
        "title": title,
        "county": item.get("county", "Regional"),
        "category": item.get("kind", "Directory source"),
        "url": url,
        "host": hostname(url),
        "update_domain": update_domain(item),
        "cadence_days": days,
        "last_checked": None,
        "next_check": date.today().isoformat(),
        "verification_status": item.get("verification_label") or item.get("confidence") or "Source-linked lead",
        "review_level": review_level(item),
        "public_claim_boundary": "Verify current page, eligibility, contact path, rates, deadlines, and acceptance rules before publishing stronger claims.",
        "reader_action": item.get("action", ""),
    }


def normalize_amplifier(item: dict) -> dict:
    title = item.get("channel", "").strip()
    url = item.get("source_url", "").strip()
    days = cadence_days(item)
    return {
        "id": stable_id("amplifier", title, url),
        "source_group": "amplifier_channels",
        "title": title,
        "county": item.get("area_served", "Regional"),
        "category": item.get("channel_type", "Amplifier channel"),
        "url": url,
        "host": hostname(url),
        "update_domain": update_domain(item),
        "cadence_days": days,
        "last_checked": None,
        "next_check": date.today().isoformat(),
        "verification_status": item.get("verification_status", "Source-linked lead"),
        "review_level": review_level(item),
        "public_claim_boundary": "Do not infer free placement, ad availability, acceptance, audience size, or endorsement.",
        "reader_action": item.get("asks", ""),
    }


def normalize_posting(item: dict) -> dict:
    title = item.get("place", "").strip()
    url = item.get("source_url", "").strip()
    days = cadence_days(item)
    return {
        "id": stable_id("posting", title, url or item.get("notes", "")),
        "source_group": "posting_spaces",
        "title": title,
        "county": item.get("county", "Regional"),
        "category": item.get("type", "Posting pathway"),
        "url": url,
        "host": hostname(url),
        "update_domain": "civic",
        "cadence_days": days,
        "last_checked": None,
        "next_check": date.today().isoformat(),
        "verification_status": item.get("status", "Needs manual verification"),
        "review_level": "manual_verification_needed" if not url else review_level(item),
        "public_claim_boundary": "Verify physical board access, posting permission, office hours, and public-notice rules directly.",
        "reader_action": item.get("notes", ""),
    }


def load_registry() -> dict:
    data = json.loads(GUIDE_DATA.read_text(encoding="utf-8"))
    previous_records: dict[str, dict] = {}
    if OUTPUT.exists():
        try:
            previous_payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            previous_payload = {}
        previous_records = {
            item.get("id", ""): item
            for item in previous_payload.get("records", [])
            if item.get("id")
        }
    records = []
    records.extend(normalize_directory_source(item) for item in data.get("directory_sources", []))
    records.extend(normalize_amplifier(item) for item in data.get("amplifier_channels", []))
    records.extend(normalize_posting(item) for item in data.get("posting_spaces", []))
    for record in records:
        previous = previous_records.get(record["id"])
        if not previous or previous.get("url") != record.get("url"):
            continue
        for field in ("last_checked", "next_check", "last_check_status", "last_status_code"):
            if field in previous:
                record[field] = previous[field]
    records = sorted(records, key=lambda item: (item["update_domain"], item["county"], item["title"].casefold()))
    return {
        "generated_at": date.today().isoformat(),
        "source": str(GUIDE_DATA.relative_to(ROOT)),
        "review_policy": "Automation may propose updates. Human approval is required for public claims, eligibility, rates, deadlines, contact changes, listing removal, and civic/legal guidance.",
        "counts": {
            "records": len(records),
            "human_approval_required": sum(1 for item in records if item["review_level"] == "human_approval_required"),
            "manual_verification_needed": sum(1 for item in records if item["review_level"] == "manual_verification_needed"),
        },
        "records": records,
    }


def write_markdown(registry: dict) -> None:
    records = registry["records"]
    lines = [
        "# Update Source Registry",
        "",
        f"Generated: {registry['generated_at']}",
        "",
        registry["review_policy"],
        "",
        "## Counts",
        "",
        f"- Records: {registry['counts']['records']}",
        f"- Human approval required: {registry['counts']['human_approval_required']}",
        f"- Manual verification needed: {registry['counts']['manual_verification_needed']}",
        "",
        "## Records",
        "",
    ]
    for item in records:
        label = item["title"]
        url = item["url"]
        linked = f"[{label}]({url})" if url else label
        check_note = "not checked yet"
        if item.get("last_checked"):
            check_note = f"last checked {item['last_checked']}; {item.get('last_check_status') or 'status not recorded'}; next {item.get('next_check') or 'unscheduled'}"
        lines.append(
            f"- {linked} - {item['county']}; {item['update_domain']}; every {item['cadence_days']} days; "
            f"{item['review_level']}; {check_note}"
        )
    MARKDOWN_OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if not GUIDE_DATA.exists():
        raise SystemExit(f"Build the site first: missing {GUIDE_DATA}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    registry = load_registry()
    OUTPUT.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    write_markdown(registry)
    print(json.dumps({"output": str(OUTPUT), "records": registry["counts"]["records"]}, indent=2))


if __name__ == "__main__":
    main()
