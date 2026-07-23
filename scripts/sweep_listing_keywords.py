from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

try:
    from weekly_directory_query_check import clean_text, fetch_url
except ModuleNotFoundError:
    from scripts.weekly_directory_query_check import clean_text, fetch_url


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "tri_county_persona_resources.csv"
DEFAULT_INDEX = ROOT / "data" / "listing-keyword-index.json"
DEFAULT_OUT_DIR = ROOT / "review" / "keyword-sweep"
SCHEMA_VERSION = 1

LOW_SIGNAL_HOSTS = {
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "twitter.com",
    "x.com",
    "youtube.com",
}

GENERIC_CATEGORY_PHRASES = (
    "all tourism directory listings",
    "commercial directory lead",
    "local listing to confirm",
    "outreach lead",
    "travel guide businesses and attractions",
    "vacation directory listings and attractions",
)

GENERIC_NOTE_PHRASES = (
    "commercial-directory-only lead",
    "creative-directory lead added",
    "is listed as a",
    "listed category:",
    "open a source link",
    "outreach score",
    "review before publishing",
    "source-check candidate",
    "starting contact",
    "treat as unverified",
    "useful for promotion",
    "use this as a starting contact",
    "visitor-facing listing pulled",
    "verify current details",
    "yellowpages.com bulk listing",
    "when the fit and contact path make sense",
)

NAME_MATCH_STOPWORDS = {
    "and",
    "at",
    "co",
    "company",
    "corp",
    "corporation",
    "inc",
    "llc",
    "ltd",
    "of",
    "the",
}


KEYWORD_RULES: dict[str, tuple[str, ...]] = {
    "accounting": ("accountant", "accountants", "accounting", "bookkeeping", "tax preparation"),
    "advertising": ("advertise", "advertising", "ad placement", "media buying"),
    "agriculture": ("agriculture", "farm", "farmer", "farming", "ranch", "ranching", "livestock"),
    "antiques": ("antique", "antiques", "vintage goods"),
    "art gallery": ("art gallery", "art galleries", "gallery space"),
    "artist": ("artist", "artists", "studio artist"),
    "automotive": ("auto repair", "automotive", "car repair", "tire shop", "vehicle repair"),
    "bakery": ("baker", "bakery", "baked goods", "pastry", "pastries"),
    "banking": ("bank", "banking", "credit union", "financial institution"),
    "bed and breakfast": ("bed and breakfast", "b&b", "bnb"),
    "brewery": ("breweries", "brewery", "craft beer", "taproom"),
    "bulletin board": ("bulletin board", "community board", "public posting board"),
    "business directory": ("business directory", "member directory", "merchant directory"),
    "business support": ("business assistance", "business development", "business support", "small business"),
    "cafe": ("cafe", "café", "coffee house", "coffee shop", "espresso bar"),
    "calendar": ("calendar", "community calendar", "event calendar"),
    "camping": ("campground", "camping", "rv park", "recreational vehicle park"),
    "catering": ("caterer", "caterers", "catering", "food service"),
    "chamber of commerce": ("chamber", "chamber of commerce", "business chamber"),
    "childcare": ("child care", "childcare", "day care", "daycare", "early childhood"),
    "clinic": ("clinic", "health clinic", "medical clinic", "community health center"),
    "community organization": ("community group", "community organization", "civic organization"),
    "construction": ("builder", "building contractor", "construction", "general contractor"),
    "consulting": ("business consultant", "consultancy", "consultant", "consulting"),
    "contractor": ("contractor", "contractors", "home services", "trade services"),
    "coworking": ("co-working", "coworking", "shared workspace"),
    "creative business": ("creative business", "creative entrepreneur", "creative industry"),
    "cultural heritage": ("cultural heritage", "heritage", "historic preservation", "tradition bearer"),
    "dance": ("dance", "dancer", "dance company", "dance studio"),
    "directory": ("directory", "listing directory", "resource directory"),
    "economic development": ("economic development", "economic opportunity", "economic vitality"),
    "education": ("education", "educational", "school", "college", "university"),
    "event services": ("event planning", "event rental", "event services", "party rental"),
    "event submission": ("add an event", "event submission", "submit an event", "submit event"),
    "event venue": ("event space", "event venue", "meeting space", "venue rental"),
    "festival": ("festival", "festivals", "street fair"),
    "fiber arts": ("fiber art", "fiber arts", "quilting", "textile art", "weaving"),
    "filmmaking": ("film production", "filmmaker", "filmmaking", "motion picture"),
    "financial services": ("financial advisor", "financial planning", "financial services"),
    "fishing": ("angler", "angling", "fishing", "fly fishing"),
    "flyer distribution": ("flyer", "flyers", "handbill", "poster placement"),
    "food truck": ("food truck", "mobile food", "mobile vendor"),
    "funding": ("financial assistance", "funding", "funding opportunity", "project funding"),
    "gift shop": ("gift shop", "gifts", "souvenir shop"),
    "golf": ("golf", "golf course", "golfing"),
    "grant": ("grant", "grant program", "grants", "grantmaking"),
    "graphic design": ("brand design", "graphic design", "graphic designer", "logo design"),
    "grocery": ("food market", "grocer", "groceries", "grocery", "supermarket"),
    "health services": ("health care", "health services", "healthcare", "medical services"),
    "hiking": ("hike", "hiking", "trail", "trails"),
    "hotel": ("hotel", "hotels", "motel", "motels"),
    "horseback riding": ("horse riding", "horseback ride", "horseback riding", "trail ride"),
    "hunting": ("game hunting", "hunting", "hunting guide"),
    "illustration": ("illustration", "illustrator", "visual illustration"),
    "insurance": ("insurance", "insurance agency", "insurance agent"),
    "jewelry": ("jeweler", "jewelry", "jewellery", "silversmith"),
    "legal services": ("attorney", "law firm", "lawyer", "legal aid", "legal services"),
    "library": ("libraries", "library", "public library"),
    "live music": ("concert", "live music", "music performance"),
    "loan": ("business loan", "loan", "loans", "microloan", "revolving loan"),
    "lodging": ("accommodation", "accommodations", "lodging", "places to stay"),
    "main street": ("downtown development", "main street", "mainstreet"),
    "maker": ("artisan", "craftsperson", "maker", "makers"),
    "marketing": ("digital marketing", "marketing", "marketing services", "promotion services"),
    "media": ("local media", "media outlet", "news media", "press"),
    "mentorship": ("business mentor", "mentoring", "mentorship", "peer mentoring"),
    "museum": ("museum", "museums", "museum exhibit"),
    "music": ("musician", "musicians", "music studio", "recording studio"),
    "newsletter": ("email newsletter", "newsletter", "newsletters"),
    "newspaper": ("local newspaper", "newspaper", "newspapers", "print news"),
    "nonprofit": ("charitable organization", "non-profit", "nonprofit", "public charity"),
    "outdoor recreation": ("adventure", "outdoor recreation", "recreation", "recreational"),
    "outfitter": ("guide service", "outfitter", "outfitters", "tour guide"),
    "painting": ("muralist", "painter", "painting", "paintings"),
    "performing arts": ("performing art", "performing arts", "performance arts"),
    "photography": ("photographer", "photography", "portrait photography"),
    "pottery": ("ceramic", "ceramics", "potter", "pottery"),
    "professional services": ("professional service", "professional services"),
    "public agency": ("city government", "county government", "government agency", "public agency"),
    "public art": ("mural", "public art", "public artwork"),
    "radio": ("broadcast radio", "community radio", "radio station"),
    "real estate": ("property management", "real estate", "realtor", "realty"),
    "restaurant": ("dining", "eatery", "restaurant", "restaurants"),
    "retail": ("local shop", "retail", "retailer", "shopping"),
    "salon": ("barber", "beauty salon", "hair salon", "salon"),
    "scholarship": ("scholarship", "scholarships", "tuition assistance"),
    "sculpture": ("sculptor", "sculpture", "sculptures"),
    "senior services": ("aging services", "older adults", "senior services", "seniors"),
    "skiing": ("ski area", "ski resort", "skiing", "snowboarding"),
    "social services": ("family services", "human services", "social service", "social services"),
    "spa and wellness": ("massage", "spa", "wellness", "wellness center"),
    "sponsorship": ("event sponsor", "sponsor", "sponsorship", "sponsorship opportunity"),
    "stipend": ("artist stipend", "stipend", "stipends"),
    "tattoo": ("body art", "tattoo", "tattoo artist", "tattoo studio"),
    "technical assistance": ("advising", "technical assistance", "technical support"),
    "theater": ("playhouse", "theater", "theatre", "theatrical"),
    "tourism": ("destination marketing", "tourism", "travel information", "visitor information"),
    "training": ("business training", "course", "training", "training program"),
    "transportation": ("public transit", "shuttle", "transportation", "transit"),
    "vacation rental": ("short-term rental", "vacation home", "vacation rental"),
    "visitor center": ("tourist information center", "visitor center", "visitors center"),
    "visitor guide": ("travel guide", "visitor guide", "visitors guide"),
    "volunteer": ("volunteer", "volunteering", "volunteer opportunity"),
    "web design": ("website design", "web design", "web designer", "web development"),
    "winery": ("vineyard", "wine tasting", "winery", "wineries"),
    "workshop": ("class", "classes", "community workshop", "workshop", "workshops"),
    "writing": ("author", "copywriter", "creative writing", "writer", "writing"),
}


class KeywordSignalParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.heading_parts: list[str] = []
        self.meta_parts: list[str] = []
        self._in_title = False
        self._heading_depth = 0
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = str(tag or "").casefold()
        attrs_dict = {str(name or "").casefold(): value or "" for name, value in attrs}
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "title":
            self._in_title = True
        elif tag in {"h1", "h2", "h3"}:
            self._heading_depth += 1
        elif tag == "meta":
            name = str(attrs_dict.get("name") or attrs_dict.get("property") or "").casefold()
            if name in {"description", "og:description", "og:title", "twitter:description", "twitter:title"}:
                content = clean_text(attrs_dict.get("content", ""))
                if content:
                    self.meta_parts.append(content)

    def handle_endtag(self, tag: str) -> None:
        tag = str(tag or "").casefold()
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == "title":
            self._in_title = False
        elif tag in {"h1", "h2", "h3"} and self._heading_depth:
            self._heading_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = clean_text(data)
        if not text:
            return
        if self._in_title:
            self.title_parts.append(text)
        if self._heading_depth:
            self.heading_parts.append(text)

    def signal_text(self) -> str:
        concise_titles = [
            re.split(r"\s+(?:\||-|–|—)\s+", part, maxsplit=1)[0]
            for part in self.title_parts
        ]
        concise_meta = [self.meta_parts[0][:180]] if self.meta_parts else []
        return " ".join(concise_titles + concise_meta + self.heading_parts[:2])


def normalize_match_text(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).casefold()
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def phrase_present(text: str, phrase: str) -> bool:
    phrase = normalize_match_text(phrase)
    if not phrase:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(phrase).replace(r"\ ", r"\s+") + r"(?![a-z0-9])"
    return bool(re.search(pattern, text))


def extract_controlled_keywords(value: object) -> list[str]:
    text = normalize_match_text(value)
    return [
        keyword
        for keyword, aliases in KEYWORD_RULES.items()
        if any(phrase_present(text, alias) for alias in aliases)
    ]


def listing_name_matches_signal(name: object, signal: object) -> bool:
    normalized_name = normalize_match_text(name)
    normalized_signal = normalize_match_text(signal)
    if not normalized_name or not normalized_signal:
        return False
    if phrase_present(normalized_signal, normalized_name):
        return True
    tokens = [token for token in normalized_name.split() if token not in NAME_MATCH_STOPWORDS and len(token) > 1]
    if not tokens:
        return False
    matched = sum(1 for token in tokens if phrase_present(normalized_signal, token))
    required = 1 if len(tokens) == 1 else max(2, (len(tokens) * 2 + 2) // 3)
    return matched >= required


def split_values(value: object) -> list[str]:
    return [part.strip() for part in str(value or "").split(";") if part.strip()]


def primary_source_url(row: dict) -> str:
    candidates = []
    for field in ("website", "source_url"):
        for candidate in split_values(row.get(field)):
            parsed = urlparse(candidate)
            if parsed.scheme in {"http", "https"} and parsed.netloc:
                candidates.append(candidate)
    for candidate in candidates:
        host = urlparse(candidate).netloc.casefold().removeprefix("www.")
        if host not in LOW_SIGNAL_HOSTS and not any(host.endswith(f".{domain}") for domain in LOW_SIGNAL_HOSTS):
            return candidate
    return ""


def canonical_signal(row: dict) -> str:
    category_parts = [
        part
        for part in split_values(row.get("category"))
        if not any(phrase in part.casefold() for phrase in GENERIC_CATEGORY_PHRASES)
    ]
    note = clean_text(row.get("notes", ""))
    if any(phrase in note.casefold() for phrase in GENERIC_NOTE_PHRASES):
        note = ""
    return " ".join(
        part
        for part in [
            clean_text(row.get("resource_name", "")),
            " ".join(category_parts),
            clean_text(row.get("resource_type", "")),
            note,
        ]
        if part
    )


def load_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = []
        for row in csv.DictReader(handle):
            cleaned = {key: clean_text(value) for key, value in row.items()}
            if cleaned.get("id") and cleaned.get("resource_name"):
                rows.append(cleaned)
    return rows


def load_index(path: Path) -> dict:
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION, "entries": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": SCHEMA_VERSION, "entries": {}}
    if not isinstance(payload.get("entries"), dict):
        payload["entries"] = {}
    return payload


def fetch_keyword_signals(url: str, timeout: int) -> dict:
    result = fetch_url(url, timeout)
    if not result["ok"]:
        return {
            "ok": False,
            "status": "fetch_error",
            "status_code": result.get("status_code"),
            "final_url": result.get("final_url") or url,
            "keywords": [],
            "content_hash": "",
            "signal_text": "",
            "error": clean_text(result.get("error")),
        }
    content_type = clean_text(result.get("content_type")).casefold()
    if content_type and "html" not in content_type and "xhtml" not in content_type:
        return {
            "ok": False,
            "status": "unsupported_content",
            "status_code": result.get("status_code"),
            "final_url": result.get("final_url") or url,
            "keywords": [],
            "content_hash": "",
            "signal_text": "",
            "error": f"Unsupported content type: {content_type}",
        }
    parser = KeywordSignalParser()
    try:
        parser.feed(result.get("html", ""))
    except Exception as exc:  # HTMLParser tolerates malformed HTML; retain a report if a page still defeats it.
        return {
            "ok": False,
            "status": "parse_error",
            "status_code": result.get("status_code"),
            "final_url": result.get("final_url") or url,
            "keywords": [],
            "content_hash": "",
            "signal_text": "",
            "error": clean_text(str(exc)),
        }
    signal = clean_text(parser.signal_text())
    return {
        "ok": True,
        "status": "checked",
        "status_code": result.get("status_code"),
        "final_url": result.get("final_url") or url,
        "keywords": extract_controlled_keywords(signal)[:20],
        "content_hash": hashlib.sha256(signal.encode("utf-8")).hexdigest() if signal else "",
        "signal_text": signal,
        "error": "",
    }


def oldest_check_for_url(url: str, resource_ids: list[str], old_entries: dict) -> str:
    checks = [clean_text(old_entries.get(resource_id, {}).get("last_checked")) for resource_id in resource_ids]
    populated = [item for item in checks if item]
    return min(populated) if populated else "0000-00-00"


def url_status_rank(resource_ids: list[str], old_entries: dict, retry_errors_first: bool) -> int:
    statuses = {clean_text(old_entries.get(resource_id, {}).get("status")) for resource_id in resource_ids}
    has_error = bool(statuses & {"fetch_error", "parse_error", "unsupported_content"})
    has_pending = bool(statuses & {"", "pending_source_check"})
    if retry_errors_first:
        return 0 if has_error else 1 if has_pending else 2
    return 0 if has_pending else 1 if has_error else 2


def select_urls(url_to_ids: dict[str, list[str]], old_entries: dict, limit: int, retry_errors_first: bool = False) -> list[str]:
    ordered = sorted(
        url_to_ids,
        key=lambda url: (
            url_status_rank(url_to_ids[url], old_entries, retry_errors_first),
            oldest_check_for_url(url, url_to_ids[url], old_entries),
            hashlib.sha1(url.encode("utf-8")).hexdigest(),
        ),
    )
    return ordered if limit <= 0 else ordered[:limit]


def run_sweep(args: argparse.Namespace) -> dict:
    today = date.today().isoformat()
    rows = load_rows(args.source)
    old_payload = load_index(args.index)
    old_entries = old_payload.get("entries", {})
    rows_by_id = {row["id"]: row for row in rows}
    url_to_ids: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        url = primary_source_url(row)
        if url:
            url_to_ids[url].append(row["id"])

    selected_urls = [] if args.no_network else select_urls(url_to_ids, old_entries, args.limit, args.retry_errors_first)
    fetch_results: dict[str, dict] = {}
    if selected_urls:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
            futures = {executor.submit(fetch_keyword_signals, url, args.timeout): url for url in selected_urls}
            for future in as_completed(futures):
                url = futures[future]
                try:
                    fetch_results[url] = future.result()
                except Exception as exc:
                    fetch_results[url] = {
                        "ok": False,
                        "status": "fetch_error",
                        "status_code": None,
                        "final_url": url,
                        "keywords": [],
                        "content_hash": "",
                        "signal_text": "",
                        "error": clean_text(str(exc)),
                    }

    new_entries: dict[str, dict] = {}
    changes = []
    source_keyword_changes = 0
    for resource_id, row in rows_by_id.items():
        old = old_entries.get(resource_id, {})
        source_url = primary_source_url(row)
        canonical_keywords = extract_controlled_keywords(canonical_signal(row))
        source_keywords = list(old.get("source_keywords") or [])
        status = clean_text(old.get("status")) or ("pending_source_check" if source_url else "no_source")
        last_checked = clean_text(old.get("last_checked"))
        status_code = old.get("status_code")
        final_url = clean_text(old.get("final_url")) or source_url
        content_hash = clean_text(old.get("content_hash"))
        error = clean_text(old.get("error"))

        if args.reset_source_keywords:
            source_keywords = []
            status = "pending_source_check" if source_url else "no_source"
            last_checked = ""
            status_code = None
            final_url = source_url
            content_hash = ""
            error = ""

        if source_url != clean_text(old.get("source_url")):
            source_keywords = []
            status = "pending_source_check" if source_url else "no_source"
            last_checked = ""
            status_code = None
            final_url = source_url
            content_hash = ""
            error = ""

        if source_url in fetch_results:
            fetched = fetch_results[source_url]
            status = fetched["status"]
            status_code = fetched.get("status_code")
            final_url = fetched.get("final_url") or source_url
            last_checked = today
            content_hash = fetched.get("content_hash", "")
            error = fetched.get("error", "")
            if fetched["ok"]:
                if listing_name_matches_signal(row.get("resource_name"), fetched.get("signal_text")):
                    source_keywords = fetched["keywords"]
                else:
                    source_keywords = []
                    status = "checked_no_name_match"

        keywords = list(dict.fromkeys(canonical_keywords + source_keywords))[:32]
        previous_keywords = list(old.get("keywords") or [])
        previous_source_keywords = list(old.get("source_keywords") or [])
        added = [keyword for keyword in keywords if keyword not in previous_keywords]
        removed = [keyword for keyword in previous_keywords if keyword not in keywords]
        if source_keywords != previous_source_keywords:
            source_keyword_changes += 1
        changed = bool(added or removed)
        if changed:
            changes.append(
                {
                    "id": resource_id,
                    "name": row.get("resource_name"),
                    "county": row.get("county"),
                    "town": row.get("town"),
                    "added": added,
                    "removed": removed,
                    "status": status,
                    "source_url": source_url,
                }
            )

        new_entries[resource_id] = {
            "resource_name": row.get("resource_name"),
            "keywords": keywords,
            "canonical_keywords": canonical_keywords,
            "source_keywords": source_keywords,
            "source_url": source_url,
            "final_url": final_url,
            "status": status,
            "status_code": status_code,
            "last_checked": last_checked,
            "last_changed": today if changed else clean_text(old.get("last_changed")),
            "content_hash": content_hash,
            "error": error,
        }

    status_counts = Counter(entry["status"] for entry in new_entries.values())
    failed_urls = sum(1 for result in fetch_results.values() if not result["ok"])
    index_payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": today,
        "description": "Controlled search keywords derived from canonical listing fields and current public-page title, metadata, and heading signals.",
        "entries": new_entries,
    }
    summary = {
        "rows": len(rows),
        "rows_with_source_url": sum(1 for row in rows if primary_source_url(row)),
        "distinct_source_urls": len(url_to_ids),
        "urls_selected": len(selected_urls),
        "urls_checked": len(fetch_results),
        "urls_failed": failed_urls,
        "entries_changed": len(changes),
        "source_keyword_changes": source_keyword_changes,
        "status_counts": dict(sorted(status_counts.items())),
    }
    payload = {
        "generated_at": today,
        "index_path": str(args.index),
        "network_enabled": not args.no_network,
        "summary": summary,
        "changes": changes,
        "fetch_failures": [
            {
                "url": url,
                "status": result["status"],
                "status_code": result.get("status_code"),
                "error": result.get("error"),
            }
            for url, result in sorted(fetch_results.items())
            if not result["ok"]
        ],
    }
    if args.write_index:
        args.index.parent.mkdir(parents=True, exist_ok=True)
        args.index.write_text(json.dumps(index_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def write_markdown(payload: dict, path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# Listing Keyword Sweep",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "This is a review queue. Source-page terms improve directory search only after the generated index change is reviewed and merged.",
        "",
        "## Summary",
        "",
        f"- Canonical rows: {summary['rows']}",
        f"- Rows with a public source URL: {summary['rows_with_source_url']}",
        f"- Distinct source URLs: {summary['distinct_source_urls']}",
        f"- URLs selected this run: {summary['urls_selected']}",
        f"- URLs checked: {summary['urls_checked']}",
        f"- URL checks needing attention: {summary['urls_failed']}",
        f"- Listing keyword sets changed: {summary['entries_changed']}",
        f"- Source-derived keyword sets changed: {summary['source_keyword_changes']}",
        "",
        "## Status",
        "",
    ]
    for status, count in summary["status_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Proposed Keyword Changes", ""])
    if not payload["changes"]:
        lines.append("No keyword changes were proposed.")
    else:
        for item in payload["changes"][:100]:
            place = ", ".join(part for part in [item.get("town"), item.get("county")] if part)
            lines.append(f"### {item['name']} ({place})")
            lines.append("")
            lines.append(f"- Status: {item['status']}")
            lines.append(f"- Add: {', '.join(item['added']) if item['added'] else 'None'}")
            lines.append(f"- Remove: {', '.join(item['removed']) if item['removed'] else 'None'}")
            if item.get("source_url"):
                lines.append(f"- Public page: {item['source_url']}")
            lines.append("")
        if len(payload["changes"]) > 100:
            lines.append(f"Report truncated after 100 entries; machine-readable JSON contains all {len(payload['changes'])} changes.")
    lines.extend(["", "## Fetches Needing Attention", ""])
    if not payload["fetch_failures"]:
        lines.append("No selected source fetches failed.")
    else:
        for item in payload["fetch_failures"][:100]:
            detail = f"HTTP {item['status_code']}" if item.get("status_code") else item.get("error") or item["status"]
            lines.append(f"- {item['url']}: {detail}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh controlled search-keyword suggestions for Tri-County listings.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--limit", type=int, default=120, help="Maximum distinct source URLs to fetch; 0 checks all.")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--timeout", type=int, default=14)
    parser.add_argument("--no-network", action="store_true")
    parser.add_argument("--retry-errors-first", action="store_true")
    parser.add_argument("--reset-source-keywords", action="store_true")
    parser.add_argument("--write-index", action="store_true")
    parser.add_argument("--fail-on-fetch-error", action="store_true")
    args = parser.parse_args()

    payload = run_sweep(args)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    dated_json = args.out_dir / f"keyword-sweep-{date.today().isoformat()}.json"
    dated_md = args.out_dir / f"keyword-sweep-{date.today().isoformat()}.md"
    latest_json = args.out_dir / "keyword-sweep-latest.json"
    latest_md = args.out_dir / "keyword-sweep-latest.md"
    for target in (dated_json, latest_json):
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    for target in (dated_md, latest_md):
        write_markdown(payload, target)
    print(json.dumps({"summary": payload["summary"], "index_written": args.write_index}, indent=2))
    if args.fail_on_fetch_error and payload["summary"]["urls_failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
