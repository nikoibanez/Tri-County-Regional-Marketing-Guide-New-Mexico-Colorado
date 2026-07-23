from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import ssl
import sys
import time
import unicodedata
from collections import defaultdict
from datetime import date
from difflib import get_close_matches
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from directory_exclusions import references_excluded_directory_entity  # noqa: E402

DEFAULT_CONFIG = ROOT / "data" / "directory-watch-sources.json"
DEFAULT_DIRECTORY_FILES = [
    ROOT / "data" / "directory_of_absolutely_everything.csv",
    ROOT / "data" / "tri_county_persona_resources.csv",
]
DEFAULT_OUT_DIR = ROOT / "review" / "directory-watch"
DEFAULT_PUBLIC_CANDIDATES = ROOT / "data" / "directory-auto-update-candidates.json"


BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "dd",
    "div",
    "dl",
    "dt",
    "figcaption",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "section",
    "table",
    "td",
    "th",
    "tr",
    "ul",
}

HEADING_TAGS = {"h1", "h2", "h3", "h4"}

STOP_PHRASES = {
    "about",
    "about us",
    "add a listing",
    "add business listing",
    "advertise",
    "all",
    "back to top",
    "blog",
    "business directory",
    "calendar",
    "categories",
    "category",
    "contact",
    "contact us",
    "copyright",
    "directions",
    "directory",
    "directory page",
    "donate",
    "events",
    "facebook",
    "follow us",
    "gallery",
    "get directions",
    "closed",
    "home",
    "instagram",
    "learn more",
    "lodging",
    "map",
    "menu",
    "more",
    "next",
    "privacy policy",
    "read more",
    "resources",
    "search",
    "see all",
    "shop",
    "sign up",
    "skip to content",
    "submit",
    "submit event",
    "terms",
    "view all",
    "visit",
    "website",
    "apr",
    "aug",
    "dec",
    "feb",
    "fri",
    "jan",
    "jul",
    "jun",
    "mar",
    "mon",
    "nov",
    "oct",
    "sat",
    "sep",
    "sun",
    "thu",
    "tue",
    "wed",
}

STOP_CONTAINS = (
    " am - ",
    " pm - ",
    "cookie",
    "copyright",
    "email protected",
    "follow us",
    "learn more",
    "login",
    "newsletter",
    "privacy",
    "read more",
    "share this",
    "skip to",
    "supermarket created",
    "view more",
)

GENERIC_CATEGORY_TERMS = {
    "accountants",
    "accommodations",
    "activities",
    "activities and recreation",
    "accountants cpa",
    "air conditioning",
    "airlines",
    "airports",
    "animal boarding",
    "animal shelters",
    "antiques",
    "appraisers",
    "architects",
    "all terrain vehicles",
    "art galleries",
    "art gallery",
    "artists",
    "artists galleries studios",
    "associations",
    "attorneys",
    "auto parts and repair",
    "automotive",
    "banks",
    "banks financial institutions",
    "bed and breakfast",
    "bookkeeping services",
    "breweries",
    "building contractors",
    "building materials",
    "building services",
    "business resources",
    "campgrounds",
    "catering",
    "chamber of commerce",
    "charitable foundations",
    "churches",
    "cleaning services",
    "clubs",
    "coffee shop",
    "computer repair",
    "conference center",
    "contractors",
    "cooperative",
    "dining",
    "education",
    "electricians",
    "event services",
    "financial institutions",
    "food and beverage",
    "health care",
    "home services",
    "insurance",
    "lodging",
    "marketing",
    "nonprofit",
    "photography",
    "propane",
    "real estate",
    "road conditions",
    "restaurants",
    "retail",
    "shopping",
    "stables",
    "tourism",
    "transportation",
    "visitor services",
}

NON_LISTING_PATH_PARTS = (
    "/about",
    "/annual-calendar",
    "/area-facts",
    "/board",
    "/business-resources",
    "/business/category/",
    "/business/categories/",
    "/category/",
    "/categories/",
    "/contact",
    "/cart",
    "/directory-page",
    "/event/",
    "/events/",
    "/my-account",
    "/privacy",
    "/resources",
    "/submit",
    "/visitor/",
    "/who-we-are",
)

BUSINESS_SUFFIXES = {
    "co",
    "company",
    "corp",
    "corporation",
    "inc",
    "incorporated",
    "llc",
    "ltd",
    "pllc",
}


def clean_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    words = [word for word in value.split() if word not in BUSINESS_SUFFIXES]
    return " ".join(words).strip()


def compact_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize_name(value))


def stable_id(*parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:10]
    slug = re.sub(r"[^a-z0-9]+", "-", parts[0].lower()).strip("-")[:50] or "candidate"
    return f"{slug}-{digest}"


def looks_like_listing_name(text: str) -> bool:
    text = clean_text(text)
    lower = text.casefold()
    if not text or lower in STOP_PHRASES:
        return False
    if text[:1].islower():
        return False
    if text.endswith((",", ":")):
        return False
    if any(phrase in lower for phrase in STOP_CONTAINS):
        return False
    if is_non_listing_fact(text) or is_probable_category(text):
        return False
    if len(text) < 3 or len(text) > 90:
        return False
    if len(text.split()) > 12:
        return False
    if not re.search(r"[A-Za-z]", text):
        return False
    if re.search(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b", text):
        return False
    if text.count("@") or lower.startswith(("http", "www.")):
        return False
    if lower.endswith((" menu", " policies", " policy")):
        return False
    if re.fullmatch(r"[A-Z]{2}", text):
        return False
    return True


def is_non_listing_fact(text: str) -> bool:
    text = clean_text(text)
    lower = f" {text.casefold()} "
    if re.fullmatch(r":?\s*\d{1,2}:\d{2}\s*(am|pm)\s*(-|to)\s*\d{1,2}:\d{2}\s*(am|pm)", text, re.I):
        return True
    if re.search(r"\b\d{1,2}:\d{2}\s*(am|pm)\b", lower):
        return True
    if re.search(r"\b(phone|fax|email):?\b", lower):
        return True
    if re.search(r"\b(open|closed|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", lower):
        return True
    if re.search(r"\b\d{5}(?:-\d{4})?", text):
        return True
    if re.match(r"^p\.?\s*o\.?\s+box\b", text, re.I):
        return True
    if re.match(r"^\d{1,6}\s+[\w .'-]+(?:street|st\.?|avenue|ave\.?|road|rd\.?|lane|ln\.?|drive|dr\.?|boulevard|blvd\.?|highway|hwy\.?|court|ct\.?)\b", text, re.I):
        return True
    return False


def is_probable_category(text: str) -> bool:
    key = normalize_name(text)
    if key in GENERIC_CATEGORY_TERMS:
        return True
    if "/" in text and len(text.split()) <= 4:
        return True
    if len(text.split()) <= 3 and key.endswith((" services", " repair", " rentals", " lodging", " restaurants")):
        return True
    return False


def is_listing_link(source: dict, page_url: str, href: str) -> bool:
    parsed = urlparse(href)
    if parsed.scheme not in {"http", "https"}:
        return False
    path = parsed.path.casefold()
    configured_excludes = [str(part).casefold() for part in source.get("exclude_url_path_contains", [])]
    configured_includes = [str(part).casefold() for part in source.get("include_url_path_contains", [])]
    if any(part in path for part in NON_LISTING_PATH_PARTS):
        return False
    if any(part and part in path for part in configured_excludes):
        return False
    if configured_includes:
        return any(part and part in path for part in configured_includes)
    page_path = urlparse(page_url).path.rstrip("/").casefold()
    if path.rstrip("/") == page_path:
        return False
    if path.rstrip("/") in {"", "/"}:
        return False
    return True


def contextual_text_candidates(lines: list[str]) -> list[str]:
    candidates: list[str] = []
    for index, line in enumerate(lines):
        line = clean_text(line)
        if not looks_like_listing_name(line):
            continue
        following = lines[index + 1 : index + 4]
        if not following:
            continue
        if any(is_non_listing_fact(item) for item in following[:2]):
            candidates.append(line)
            continue
        if len(following) >= 2 and looks_like_listing_name(following[0]) and is_non_listing_fact(following[1]):
            joined = clean_text(f"{line} {following[0]}")
            if looks_like_listing_name(joined) and not is_probable_category(line):
                candidates.append(joined)
    return candidates


class DirectoryHTMLParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.text_parts: list[str] = []
        self.anchors: list[dict] = []
        self.headings: list[dict] = []
        self._skip_depth = 0
        self._anchor_href = ""
        self._anchor_parts: list[str] = []
        self._heading_tag = ""
        self._heading_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in BLOCK_TAGS:
            self.text_parts.append("\n")
        attrs_dict = {name.lower(): value or "" for name, value in attrs}
        if tag == "a":
            self._anchor_href = urljoin(self.base_url, attrs_dict.get("href", ""))
            self._anchor_parts = []
        if tag in HEADING_TAGS:
            self._heading_tag = tag
            self._heading_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == "a" and self._anchor_href:
            text = clean_text(" ".join(self._anchor_parts))
            if text:
                self.anchors.append({"text": text, "href": self._anchor_href})
            self._anchor_href = ""
            self._anchor_parts = []
        if tag == self._heading_tag:
            text = clean_text(" ".join(self._heading_parts))
            if text:
                self.headings.append({"text": text, "tag": tag})
            self._heading_tag = ""
            self._heading_parts = []
        if tag in BLOCK_TAGS:
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = clean_text(data)
        if not text:
            return
        self.text_parts.append(text)
        if self._anchor_href:
            self._anchor_parts.append(text)
        if self._heading_tag:
            self._heading_parts.append(text)

    def lines(self) -> list[str]:
        text = "\n".join(self.text_parts)
        return [clean_text(line) for line in text.splitlines() if clean_text(line)]


def fetch_url(url: str, timeout: int) -> dict:
    headers = {
        "User-Agent": "TriCountyGuideDirectoryWatch/1.1 (+https://statelineguide.org)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    context = ssl.create_default_context()
    started = time.monotonic()
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=timeout, context=context) as response:
            body = response.read(2_500_000)
            content_type = response.headers.get("content-type", "")
            charset = response.headers.get_content_charset() or "utf-8"
            html = body.decode(charset, errors="replace")
            return {
                "ok": True,
                "status_code": getattr(response, "status", None),
                "final_url": response.geturl(),
                "content_type": content_type,
                "elapsed_ms": round((time.monotonic() - started) * 1000),
                "html": html,
                "error": "",
            }
    except HTTPError as exc:
        return {
            "ok": False,
            "status_code": exc.code,
            "final_url": url,
            "content_type": "",
            "elapsed_ms": round((time.monotonic() - started) * 1000),
            "html": "",
            "error": str(exc),
        }
    except (TimeoutError, URLError, OSError) as exc:
        return {
            "ok": False,
            "status_code": None,
            "final_url": url,
            "content_type": "",
            "elapsed_ms": round((time.monotonic() - started) * 1000),
            "html": "",
            "error": str(exc),
        }


def load_existing_names(paths: list[Path]) -> dict:
    names: dict[str, set[str]] = defaultdict(set)
    for path in paths:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                raw_name = clean_text(row.get("name") or row.get("resource_name") or "")
                if not raw_name:
                    continue
                key = normalize_name(raw_name)
                compact = compact_key(raw_name)
                if key:
                    names[key].add(raw_name)
                if compact:
                    names[compact].add(raw_name)
    return names


def match_existing(candidate_name: str, existing_names: dict) -> dict:
    key = normalize_name(candidate_name)
    compact = compact_key(candidate_name)
    if key in existing_names:
        return {"status": "already_in_guide", "matched_name": sorted(existing_names[key])[0], "match_type": "exact_normalized"}
    if compact in existing_names:
        return {"status": "already_in_guide", "matched_name": sorted(existing_names[compact])[0], "match_type": "exact_compact"}
    keys = [candidate for candidate in existing_names.keys() if " " in candidate]
    close = get_close_matches(key, keys, n=1, cutoff=0.94)
    if close:
        return {"status": "already_in_guide", "matched_name": sorted(existing_names[close[0]])[0], "match_type": "near_match"}
    return {"status": "possible_new_lead", "matched_name": "", "match_type": ""}


def same_site(source_url: str, target_url: str) -> bool:
    source_host = urlparse(source_url).netloc.casefold().removeprefix("www.")
    target_host = urlparse(target_url).netloc.casefold().removeprefix("www.")
    return bool(source_host and target_host and source_host == target_host)


def extract_candidates(source: dict, page_url: str, html: str, existing_names: dict) -> list[dict]:
    parser = DirectoryHTMLParser(page_url)
    parser.feed(html)
    candidates: dict[str, dict] = {}

    def add_candidate(name: str, url: str, evidence_type: str, confidence: str) -> None:
        name = clean_text(name)
        if references_excluded_directory_entity(name) or references_excluded_directory_entity(url):
            return
        if not looks_like_listing_name(name):
            return
        key = normalize_name(name)
        if not key:
            return
        match = match_existing(name, existing_names)
        existing = candidates.get(key)
        candidate = {
            "id": stable_id(name, url, source["id"]),
            "name": name,
            "source_id": source["id"],
            "source_title": source["title"],
            "county": source.get("county", "Regional"),
            "state": source.get("state", ""),
            "source_type": source.get("source_type", ""),
            "source_page": page_url,
            "listing_url": url,
            "evidence_type": evidence_type,
            "confidence": confidence,
            "priority_candidate": bool(source.get("priority_link_candidates", False) and evidence_type == "linked_text"),
            "match_status": match["status"],
            "matched_name": match["matched_name"],
            "match_type": match["match_type"],
            "review_note": "Human review required before adding, removing, or changing public directory data.",
        }
        if not existing:
            candidates[key] = candidate
            return
        if existing["listing_url"] == page_url and url != page_url:
            existing.update(candidate)

    if source.get("allow_link_candidates", True):
        for anchor in parser.anchors:
            href = anchor["href"]
            if not href or href.startswith(("mailto:", "tel:", "javascript:")):
                continue
            parsed = urlparse(href)
            if parsed.fragment and not parsed.path:
                continue
            if not is_listing_link(source, page_url, href):
                continue
            confidence = "medium"
            if same_site(page_url, href):
                confidence = "medium-high"
            add_candidate(anchor["text"], href, "linked_text", confidence)

    if source.get("allow_text_candidates", False):
        for line in contextual_text_candidates(parser.lines()):
            add_candidate(line, page_url, "text_listing_block", "low")

    return sorted(candidates.values(), key=lambda item: (item["match_status"], item["name"].casefold()))


def summarize(results: list[dict]) -> dict:
    summary = {
        "sources": len(results),
        "pages_checked": 0,
        "pages_failed": 0,
        "candidates": 0,
        "already_in_guide": 0,
        "possible_new_leads": 0,
        "priority_new_leads": 0,
        "low_confidence_new_leads": 0,
    }
    for source in results:
        for page in source["pages"]:
            summary["pages_checked"] += 1
            if not page["fetch"]["ok"]:
                summary["pages_failed"] += 1
            summary["candidates"] += len(page["candidates"])
            summary["already_in_guide"] += sum(1 for item in page["candidates"] if item["match_status"] == "already_in_guide")
            summary["possible_new_leads"] += sum(1 for item in page["candidates"] if item["match_status"] == "possible_new_lead")
            summary["priority_new_leads"] += sum(1 for item in page["candidates"] if is_priority_new_lead(item))
            summary["low_confidence_new_leads"] += sum(
                1
                for item in page["candidates"]
                if item["match_status"] == "possible_new_lead" and not is_priority_new_lead(item)
            )
    return summary


def is_priority_new_lead(item: dict) -> bool:
    return item.get("match_status") == "possible_new_lead" and bool(item.get("priority_candidate"))


def write_markdown(payload: dict, path: Path) -> None:
    lines = [
        "# Weekly Directory Query Check",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["review_policy"],
        "",
        "## Summary",
        "",
        f"- Sources watched: {payload['summary']['sources']}",
        f"- Pages checked: {payload['summary']['pages_checked']}",
        f"- Pages failed: {payload['summary']['pages_failed']}",
        f"- Listing-like candidates found: {payload['summary']['candidates']}",
        f"- Already represented in guide: {payload['summary']['already_in_guide']}",
        f"- Possible new leads: {payload['summary']['possible_new_leads']}",
        f"- Priority new leads: {payload['summary']['priority_new_leads']}",
        f"- Low-confidence text leads: {payload['summary']['low_confidence_new_leads']}",
        "",
        "## Watch Sources",
        "",
    ]
    for source in payload["results"]:
        lines.append(f"### {source['title']}")
        lines.append("")
        lines.append(f"- County: {source.get('county', 'Regional')}")
        lines.append(f"- Source type: {source.get('source_type', '')}")
        lines.append(f"- Why watch: {source.get('why_watch', '')}")
        lines.append(f"- Pages checked: {len(source['pages'])}")
        source_new = sum(
            1
            for page in source["pages"]
            for item in page["candidates"]
            if item["match_status"] == "possible_new_lead"
        )
        source_priority_new = sum(1 for page in source["pages"] for item in page["candidates"] if is_priority_new_lead(item))
        lines.append(f"- Possible new leads: {source_new}")
        lines.append(f"- Priority new leads: {source_priority_new}")
        lines.append("")
        failures = [page for page in source["pages"] if not page["fetch"]["ok"]]
        if failures:
            lines.append("Fetch issues:")
            for page in failures:
                lines.append(f"- [{page['url']}]({page['url']}) - {page['fetch'].get('error', '')}")
            lines.append("")

    possible_new = [
        item
        for source in payload["results"]
        for page in source["pages"]
        for item in page["candidates"]
        if item["match_status"] == "possible_new_lead"
    ]
    priority_new = [item for item in possible_new if is_priority_new_lead(item)]
    low_confidence_new = [item for item in possible_new if not is_priority_new_lead(item)]

    lines.extend(["## Priority New Leads", ""])
    if not priority_new:
        lines.append("No priority new leads were found by this run.")
    else:
        lines.append("These have linked listing-page evidence. They are still not publication-ready additions until a human confirms the source page.")
        lines.append("")
        for item in sorted(priority_new, key=lambda value: (value["county"], value["name"].casefold()))[:120]:
            listing_url = item["listing_url"] or item["source_page"]
            lines.append(
                f"- [{item['name']}]({listing_url}) - {item['county']}; "
                f"{item['source_title']}; evidence: {item['evidence_type']}; confidence: {item['confidence']}"
            )
        if len(priority_new) > 120:
            lines.append(f"- Additional priority leads omitted from Markdown: {len(priority_new) - 120}. See JSON.")

    lines.extend(["", "## Low-Confidence Text Candidates", ""])
    if not low_confidence_new:
        lines.append("No low-confidence text candidates were found by this run.")
    else:
        lines.append("These came from directory page text rather than individual listing links. Review them more carefully before using.")
        lines.append("")
        for item in sorted(low_confidence_new, key=lambda value: (value["county"], value["name"].casefold()))[:80]:
            lines.append(f"- {item['name']} - {item['county']}; {item['source_title']}; source page: {item['source_page']}")
        if len(low_confidence_new) > 80:
            lines.append(f"- Additional low-confidence candidates omitted from Markdown: {len(low_confidence_new) - 80}. See JSON.")

    lines.extend(["", "## Already Represented Sample", ""])
    represented = [
        item
        for source in payload["results"]
        for page in source["pages"]
        for item in page["candidates"]
        if item["match_status"] == "already_in_guide"
    ]
    if not represented:
        lines.append("No existing guide matches were found.")
    else:
        for item in sorted(represented, key=lambda value: value["name"].casefold())[:40]:
            lines.append(f"- {item['name']} -> {item['matched_name']} ({item['match_type']})")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def public_candidate_item(item: dict) -> dict:
    return {
        "name": item.get("name", ""),
        "county": item.get("county", ""),
        "state": item.get("state", ""),
        "source_title": item.get("source_title", ""),
        "source_type": item.get("source_type", ""),
        "source_page": item.get("source_page", ""),
        "listing_url": item.get("listing_url", ""),
        "evidence_type": item.get("evidence_type", ""),
        "confidence": item.get("confidence", ""),
    }


def write_public_candidates(payload: dict, path: Path) -> None:
    possible_new = [
        item
        for source in payload["results"]
        for page in source["pages"]
        for item in page["candidates"]
        if item["match_status"] == "possible_new_lead"
    ]
    priority_new = [item for item in possible_new if is_priority_new_lead(item)]
    low_confidence_new = [item for item in possible_new if not is_priority_new_lead(item)]
    public_payload = {
        "generated_at": payload["generated_at"],
        "publication_note": "Automatically refreshed from watched public directory and tourism pages. Treat these as candidate updates, not official directory additions, until a human confirms the linked source.",
        "summary": {
            "sources_watched": payload["summary"]["sources"],
            "pages_checked": payload["summary"]["pages_checked"],
            "pages_failed": payload["summary"]["pages_failed"],
            "already_represented": payload["summary"]["already_in_guide"],
            "possible_new_leads": payload["summary"]["possible_new_leads"],
            "priority_new_leads": payload["summary"]["priority_new_leads"],
            "low_confidence_text_leads": payload["summary"]["low_confidence_new_leads"],
        },
        "watched_sources": [
            {
                "id": source.get("id", ""),
                "title": source.get("title", ""),
                "county": source.get("county", ""),
                "source_type": source.get("source_type", ""),
                "source_role": source.get("source_role", ""),
                "why_watch": source.get("why_watch", ""),
                "pages_checked": len(source.get("pages", [])),
                "possible_new_leads": sum(
                    1
                    for page in source.get("pages", [])
                    for item in page.get("candidates", [])
                    if item.get("match_status") == "possible_new_lead"
                ),
                "priority_new_leads": sum(
                    1
                    for page in source.get("pages", [])
                    for item in page.get("candidates", [])
                    if is_priority_new_lead(item)
                ),
            }
            for source in payload["results"]
        ],
        "priority_new_leads": [public_candidate_item(item) for item in sorted(priority_new, key=lambda value: (value["county"], value["name"].casefold()))],
        "low_confidence_text_leads": [
            public_candidate_item(item)
            for item in sorted(low_confidence_new, key=lambda value: (value["county"], value["name"].casefold()))[:100]
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(public_payload, indent=2, ensure_ascii=False), encoding="utf-8")


def run_check(args: argparse.Namespace) -> dict:
    config = json.loads(args.config.read_text(encoding="utf-8"))
    directory_files = args.directory_file or DEFAULT_DIRECTORY_FILES
    existing_names = load_existing_names(directory_files)
    results = []

    for source in config.get("sources", []):
        source_result = {key: source.get(key) for key in ("id", "title", "county", "state", "source_type", "why_watch")}
        source_result["source_role"] = source.get("source_role", "")
        source_result["pages"] = []
        for url in source.get("seed_urls", []):
            if args.no_network:
                fetch = {
                    "ok": False,
                    "status_code": None,
                    "final_url": url,
                    "content_type": "",
                    "elapsed_ms": 0,
                    "error": "Network disabled by --no-network.",
                }
                candidates = []
            else:
                fetched = fetch_url(url, args.timeout)
                fetch = {key: value for key, value in fetched.items() if key != "html"}
                candidates = extract_candidates(source, fetched.get("final_url") or url, fetched.get("html", ""), existing_names) if fetched["ok"] else []
            source_result["pages"].append({"url": url, "fetch": fetch, "candidates": candidates})
        results.append(source_result)

    payload = {
        "generated_at": date.today().isoformat(),
        "config": str(args.config.relative_to(ROOT) if args.config.is_relative_to(ROOT) else args.config),
        "directory_files": [str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path) for path in directory_files],
        "review_policy": config.get("review_policy", ""),
        "summary": summarize(results),
        "results": results,
    }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Weekly query check for high-signal Tri-County business directory sources.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--directory-file", type=Path, action="append", help="CSV file with current guide names. Can be repeated.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--public-candidates", type=Path, default=DEFAULT_PUBLIC_CANDIDATES)
    parser.add_argument("--timeout", type=int, default=18)
    parser.add_argument("--no-network", action="store_true")
    parser.add_argument("--fail-on-fetch-error", action="store_true")
    args = parser.parse_args()

    payload = run_check(args)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    dated_json = args.out_dir / f"directory-watch-{date.today().isoformat()}.json"
    dated_md = args.out_dir / f"directory-watch-{date.today().isoformat()}.md"
    latest_json = args.out_dir / "directory-watch-latest.json"
    latest_md = args.out_dir / "directory-watch-latest.md"

    dated_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    latest_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(payload, dated_md)
    write_markdown(payload, latest_md)
    write_public_candidates(payload, args.public_candidates)

    print(json.dumps({"json": str(dated_json), "markdown": str(dated_md), "summary": payload["summary"]}, indent=2))

    if args.fail_on_fetch_error and payload["summary"]["pages_failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
