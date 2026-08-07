from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_update_sources import check_url  # noqa: E402


DEFAULT_GUIDE_DATA = ROOT / "dist" / "tri-county-netlify-guide-deep" / "data" / "guide-data.json"
DEFAULT_STATUS_OUT = ROOT / "data" / "directory-connectivity-status.json"
DEFAULT_REPORT_DIR = ROOT / "review" / "directory-connectivity"

ONLINE_CHECK_STATUSES = {"ok", "redirect"}
PLATFORM_DOMAINS = {
    "artup-nnm.org",
    "colorado.com",
    "coloradodirectory.com",
    "facebook.com",
    "google.com",
    "instagram.com",
    "localstash.com",
    "maps.app.goo.gl",
    "mapquest.com",
    "newmexico.org",
    "startupspace.app",
    "taos.org",
    "tripadvisor.com",
    "yellowpages.com",
    "yelp.com",
    "youtube.com",
    "youtu.be",
}
SHARED_HOST_OWNER_HINTS = {
    "angelfirechamber.org": ("angel fire chamber",),
    "exploreraton.com": ("explore raton",),
    "lavetacreativedistrict.org": ("la veta creative district",),
    "spanishpeakscountry.com": ("spanish peaks country",),
    "trinidadcreativedistrict.org": ("create trinidad", "trinidad creative district"),
    "visitangelfirenm.com": ("visit angel fire",),
    "visittrinidadcolorado.com": ("visit trinidad",),
    "walsenburgmercantile.com": ("walsenburg mercantile",),
}
BUSINESS_LISTING_TYPES = {
    "Arts & culture",
    "Auto & transportation",
    "Events & venues",
    "Food & drink",
    "Health & wellness",
    "Home, land & contracting",
    "Local business or service",
    "Lodging & stays",
    "Media & news",
    "Outdoor recreation",
    "Professional services",
    "Retail & local goods",
}
NON_ENTITY_NAME_TERMS = {
    "business directory",
    "calendar",
    "community resources",
    "directory",
    "funding",
    "grant",
    "guide",
    "resource directory",
    "resources",
    "support program",
}


def display_source_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def split_urls(value: object) -> list[str]:
    urls = []
    for part in clean(value).split(";"):
        url = part.strip()
        if url.startswith(("http://", "https://")) and url not in urls:
            urls.append(url)
    return urls


def normalized_host(url: object) -> str:
    try:
        return urlparse(clean(url)).netloc.casefold().removeprefix("www.")
    except ValueError:
        return ""


def normalized_name(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean(value).casefold()).strip()


def row_key(row: dict) -> str:
    explicit = clean(row.get("id"))
    if explicit:
        return explicit
    parts = [
        normalized_name(row.get("resource_name")),
        normalized_name(row.get("town")),
        normalized_name(row.get("county")),
    ]
    return "|".join(parts)


def unique_row_urls(row: dict) -> list[str]:
    urls: list[str] = []
    for field in ("website", "source_url"):
        for url in split_urls(row.get(field)):
            if url not in urls:
                urls.append(url)
    return urls


def host_usage_counts(rows: list[dict]) -> Counter:
    counts: Counter = Counter()
    for row in rows:
        for host in {normalized_host(url) for url in unique_row_urls(row)}:
            if host:
                counts[host] += 1
    return counts


def is_platform_host(host: str) -> bool:
    return any(host == domain or host.endswith("." + domain) for domain in PLATFORM_DOMAINS)


def is_first_party_candidate(row: dict, url: str, host_usage: Counter) -> bool:
    host = normalized_host(url)
    if not host or is_platform_host(host):
        return False
    if host_usage[host] <= 3:
        return True
    name = normalized_name(row.get("resource_name"))
    return any(hint in name for hint in SHARED_HOST_OWNER_HINTS.get(host, ()))


def row_url_groups(row: dict, host_usage: Counter) -> tuple[list[str], list[str]]:
    website_urls = split_urls(row.get("website"))
    source_urls = split_urls(row.get("source_url"))
    ordered_urls = list(dict.fromkeys(website_urls + source_urls))
    direct = [url for url in ordered_urls if is_first_party_candidate(row, url, host_usage)]
    profiles = [url for url in ordered_urls if url not in direct]
    return direct, profiles


def is_business_listing(row: dict) -> bool:
    listing_type = clean(row.get("public_listing_type") or row.get("resource_type"))
    name = normalized_name(row.get("resource_name"))
    return listing_type in BUSINESS_LISTING_TYPES and not any(term in name for term in NON_ENTITY_NAME_TERMS)


def best_online_url(urls: list[str], checks: dict[str, dict]) -> str:
    return next((url for url in urls if checks.get(url, {}).get("status") in ONLINE_CHECK_STATUSES), "")


def connection_details(row: dict, checks: dict[str, dict], host_usage: Counter) -> dict:
    direct_urls, profile_urls = row_url_groups(row, host_usage)
    broken_urls = [
        url for url in direct_urls + profile_urls if checks.get(url, {}).get("status") == "broken"
    ]
    usable_direct = [url for url in direct_urls if url not in broken_urls]
    usable_profiles = [url for url in profile_urls if url not in broken_urls]
    live_direct = best_online_url(usable_direct, checks)
    live_profile = best_online_url(usable_profiles, checks)
    email = clean(row.get("contact_email"))
    phone = clean(row.get("contact_phone"))
    address = clean(row.get("physical_address"))

    if live_direct:
        status = "direct-live"
        group = "Direct website"
        label = "Connect online"
        url = live_direct
    elif usable_direct:
        status = "direct-unconfirmed"
        group = "Direct website"
        label = "Website link"
        url = usable_direct[0]
    elif live_profile:
        status = "profile-live"
        group = "Hosted profile"
        label = "Online profile"
        url = live_profile
    elif usable_profiles:
        status = "profile-unconfirmed"
        group = "Hosted profile"
        label = "Listing link"
        url = usable_profiles[0]
    elif email or phone:
        status = "contact-only"
        group = "Contact only"
        label = "No direct website listed"
        url = ""
    elif address:
        status = "address-only"
        group = "Contact only"
        label = "No direct website listed"
        url = ""
    else:
        status = "no-online-link"
        group = "No online link"
        label = "No online link listed"
        url = ""

    check = checks.get(url, {}) if url else {}
    animate = status == "direct-live" and is_business_listing(row)
    return {
        "entry_id": row_key(row),
        "resource_name": clean(row.get("resource_name")),
        "town": clean(row.get("town")),
        "county": clean(row.get("county")),
        "listing_type": clean(row.get("public_listing_type") or row.get("resource_type")),
        "connection_status": status,
        "connection_group": group,
        "public_label": label,
        "public_url": url,
        "animation_eligible": animate,
        "direct_website_candidates": direct_urls,
        "hosted_profile_urls": profile_urls,
        "confirmed_broken_urls": broken_urls,
        "email_available": bool(email),
        "phone_available": bool(phone),
        "address_available": bool(address),
        "check_status": clean(check.get("status")),
        "status_code": check.get("status_code"),
        "final_url": clean(check.get("final_url")),
    }


def check_urls(urls: list[str], workers: int, timeout: int) -> dict[str, dict]:
    checks: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = {executor.submit(check_url, url, timeout): url for url in urls}
        for index, future in enumerate(as_completed(futures), start=1):
            url = futures[future]
            try:
                checks[url] = future.result()
            except Exception as exc:  # pragma: no cover - defensive boundary around network workers
                checks[url] = {
                    "status": "error",
                    "status_code": None,
                    "final_url": url,
                    "error": str(exc),
                }
            if index % 50 == 0 or index == len(urls):
                print(f"Checked {index} of {len(urls)} URLs", flush=True)
    return checks


def previous_checks(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    checks = payload.get("checks", {})
    return checks if isinstance(checks, dict) else {}


def build_summary(entries: list[dict], checks: dict[str, dict]) -> dict:
    entry_counts = Counter(entry["connection_status"] for entry in entries)
    check_counts = Counter(check.get("status") or "unknown" for check in checks.values())
    return {
        "entries": len(entries),
        "connection_status_counts": dict(sorted(entry_counts.items())),
        "direct_website_candidates": sum(bool(entry["direct_website_candidates"]) for entry in entries),
        "animated_business_connections": sum(bool(entry["animation_eligible"]) for entry in entries),
        "without_any_url": sum(
            not entry["direct_website_candidates"] and not entry["hosted_profile_urls"] for entry in entries
        ),
        "without_any_contact_path": entry_counts.get("no-online-link", 0),
        "unique_urls_checked": len(checks),
        "url_check_counts": dict(sorted(check_counts.items())),
        "confirmed_broken_urls": check_counts.get("broken", 0),
        "script_access_limited": check_counts.get("access_blocked", 0) + check_counts.get("tls_error", 0),
    }


def write_csv(entries: list[dict], path: Path) -> None:
    fields = [
        "entry_id",
        "resource_name",
        "town",
        "county",
        "listing_type",
        "connection_status",
        "connection_group",
        "public_label",
        "public_url",
        "animation_eligible",
        "check_status",
        "status_code",
        "email_available",
        "phone_available",
        "address_available",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for entry in entries:
            writer.writerow({field: entry.get(field, "") for field in fields})


def write_markdown(payload: dict, path: Path) -> None:
    summary = payload["summary"]
    counts = summary["connection_status_counts"]
    entries = payload["entries"]
    no_url = [
        entry
        for entry in entries
        if not entry["direct_website_candidates"] and not entry["hosted_profile_urls"]
    ]
    broken_direct = [entry for entry in entries if entry["confirmed_broken_urls"]]
    lines = [
        "# Directory Online Connection Review",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "This review distinguishes a first-party website from a hosted directory, tourism page, social profile, email, phone, street address, or missing contact route. An HTTP response does not prove that an organization is active or that page content is current.",
        "",
        "## Summary",
        "",
        f"- Published directory entries reviewed: {summary['entries']}",
        f"- First-party website candidates: {summary['direct_website_candidates']}",
        f"- Live first-party business links eligible for the public animation: {summary['animated_business_connections']}",
        f"- Live direct websites: {counts.get('direct-live', 0)}",
        f"- Direct website links needing a normal-browser check: {counts.get('direct-unconfirmed', 0)}",
        f"- Live hosted profiles or directory pages: {counts.get('profile-live', 0)}",
        f"- Hosted links needing a normal-browser check: {counts.get('profile-unconfirmed', 0)}",
        f"- Entries with contact details but no URL: {counts.get('contact-only', 0) + counts.get('address-only', 0)}",
        f"- Entries with no online or direct contact path: {counts.get('no-online-link', 0)}",
        f"- Unique URLs checked: {summary['unique_urls_checked']}",
        f"- Confirmed broken URLs: {summary['confirmed_broken_urls']}",
        f"- Script-access limits such as 403 or TLS errors: {summary['script_access_limited']}",
        "",
        "The companion CSV contains all entries and their assigned connection group.",
        "",
        "## Confirmed Broken Listing URLs",
        "",
    ]
    if broken_direct:
        for entry in broken_direct:
            lines.append(
                f"- {entry['resource_name']} ({entry['town'] or entry['county'] or 'Regional'}): "
                f"{', '.join(entry['confirmed_broken_urls'])}"
            )
    else:
        lines.append("- None found by this scripted check.")
    lines.extend(["", "## Listings Without Any URL", ""])
    if no_url:
        for entry in sorted(no_url, key=lambda item: (item["county"], item["town"], item["resource_name"].casefold())):
            available = ", ".join(
                label
                for label, present in [
                    ("email", entry["email_available"]),
                    ("phone", entry["phone_available"]),
                    ("address", entry["address_available"]),
                ]
                if present
            ) or "no contact path"
            lines.append(
                f"- {entry['resource_name']} - {entry['town'] or 'Regional'}, "
                f"{entry['county'] or 'Regional'} ({available})"
            )
    else:
        lines.append("- None.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Review online connection paths for every published directory listing.")
    parser.add_argument("--data", type=Path, default=DEFAULT_GUIDE_DATA)
    parser.add_argument("--status-out", type=Path, default=DEFAULT_STATUS_OUT)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args()

    payload = json.loads(args.data.read_text(encoding="utf-8"))
    rows = [row for row in payload.get("resources", []) if isinstance(row, dict)]
    host_usage = host_usage_counts(rows)
    urls = sorted({url for row in rows for url in unique_row_urls(row)})
    checks = previous_checks(args.status_out) if args.no_network else check_urls(urls, args.workers, args.timeout)
    entries = [connection_details(row, checks, host_usage) for row in rows]
    entries.sort(key=lambda item: (item["resource_name"].casefold(), item["county"], item["town"]))
    generated_at = datetime.now(timezone.utc).isoformat()
    summary = build_summary(entries, checks)
    output = {
        "generated_at": generated_at,
        "source": display_source_path(args.data),
        "summary": summary,
        "entries": entries,
        "checks": checks,
    }

    args.status_out.parent.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    args.status_out.write_text(json.dumps(output, indent=2), encoding="utf-8")
    latest_json = args.report_dir / "directory-connectivity-latest.json"
    latest_csv = args.report_dir / "directory-connectivity-latest.csv"
    latest_md = args.report_dir / "directory-connectivity-latest.md"
    report_summary = {
        "generated_at": generated_at,
        "source": display_source_path(args.data),
        "summary": summary,
        "detail_files": {
            "status": display_source_path(args.status_out),
            "csv": display_source_path(latest_csv),
            "markdown": display_source_path(latest_md),
        },
    }
    latest_json.write_text(json.dumps(report_summary, indent=2), encoding="utf-8")
    write_csv(entries, latest_csv)
    write_markdown(output, latest_md)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
