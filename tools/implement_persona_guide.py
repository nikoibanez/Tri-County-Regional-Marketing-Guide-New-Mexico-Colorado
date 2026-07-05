from __future__ import annotations

import copy
import csv
import base64
import hashlib
import html as html_module
import json
import mimetypes
import re
import shutil
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from lxml import html


ROOT = Path(r"C:\Users\Alyxx and Niko\Downloads")
HTML_PATH = ROOT / "tri_county_guide_colfax_inventory_integrated.html"
JSON_PATH = ROOT / "tri_county_persona_resources.json"
CSV_PATH = ROOT / "tri_county_persona_resources.csv"
REPORT_PATH = ROOT / "Validation_Report.md"
DOWNLOAD_HTML_PATH = ROOT / "Tri_County_Regional_Marketing_Guide_Interactive.html"
DOWNLOAD_ZIP_PATH = ROOT / "Tri_County_Regional_Marketing_Guide_Download_Package.zip"
DOWNLOAD_README_PATH = ROOT / "Tri_County_Guide_Download_README.txt"
UPDATE_ISO = date.today().isoformat()
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
VISUAL_ASSET_DIR = WORKSPACE_ROOT / "assets" / "super_eukarya_vector_package" / "assets"
BRAND_ASSET_DIR = WORKSPACE_ROOT / "assets" / "brand"
DIST_DIR = WORKSPACE_ROOT / "dist"
SOURCE_TEXT_REPLACEMENTS = {
    "pueblochamber.org/sbdc": "https://county.pueblo.org/energy-and-economic-development-department/small-business-development-center",
}

PERSONA_ORDER = ["FP", "NP", "PG", "EN", "AR"]
PERSONA_LABELS = {
    "FP": "For-Profit",
    "NP": "Non-Profit",
    "PG": "Program",
    "EN": "Entrepreneur",
    "AR": "Artist",
}

GOAL_LABELS = {
    "START": "Start Something",
    "PROMOTE": "Promote Something",
    "FUNDING": "Find Money / Help",
    "MEDIA": "Get Media Coverage",
    "OFFLINE": "Reach People Offline",
    "ONLINE": "Improve Online Visibility",
    "LISTING": "Add / Correct Info",
    "TRACK": "Track Results",
}

TOWNS_BY_COUNTY = {
    "Colfax": [
        "Raton",
        "Springer",
        "Cimarron",
        "Eagle Nest",
        "Angel Fire",
        "Maxwell",
        "Ute Park",
        "Miami",
        "French Tract",
    ],
    "Las Animas": [
        "Trinidad",
        "Aguilar",
        "Branson",
        "Hoehne",
        "Weston",
        "Stonewall",
        "Cokedale",
        "Kim",
        "Model",
        "Starkville",
        "Boncarbo",
        "Segundo",
        "Trinchera",
        "Tyrone",
        "Villegreen",
    ],
    "Huerfano": [
        "Walsenburg",
        "La Veta",
        "Cuchara",
        "Gardner",
        "Farisita",
        "Chama",
        "Pictou",
        "Pryor",
        "Red Wing",
        "Badito",
        "Calumet",
        "Delcarbon",
        "Malachite",
        "Tioga",
    ],
}

OPERATIONAL_FIELD_ORDER = [
    "id",
    "resource_name",
    "category",
    "town",
    "county",
    "state",
    "website",
    "contact_email",
    "contact_phone",
    "physical_address",
    "source_url",
    "source_type",
    "last_verified_date",
    "verification_method",
    "confidence_level",
    "notes",
    "needs_follow_up",
    "resource_type",
    "audience_served",
    "cost_level",
    "access_mode",
    "goal_relevance",
]

SKIP_SECTION_IDS = {
    "toc",
    "introduction",
    "purpose",
    "index",
    "accessibility",
    "recommendations",
    "conclusion",
    "add-brochure-userfriendly-5-1-html-toc",
    "add-brochure-userfriendly-5-1-html-index",
    "add-brochure-userfriendly-5-1-html-conclusion",
}

RESOURCEISH_FIRST_HEADERS = {
    "audience question",
    "county",
    "county municipality",
    "data type",
    "research priority",
    "participation type",
    "program",
    "area",
    "channel type",
    "use case",
    "county & municipality",
    "county & municipalities",
    "county municipalities",
    "town / node",
    "town node",
    "town / corridor",
    "town corridor",
    "area / corridor",
    "area corridor",
    "community / node",
    "community node",
    "node",
    "town",
    "outlet / channel",
    "outlet channel",
    "location",
    "partner",
    "place / corridor",
    "place corridor",
    "locality / source",
    "locality source",
    "business / organization",
    "business organization",
    "business name",
    "gap",
    "resource",
    "organisation",
    "organization",
    "need",
    "strategy archetype",
    "partner type",
    "location type",
    "space or channel",
    "timing",
    "resource type",
    "support need",
    "channel",
    "wave",
    "record",
    "area",
}

URL_RE = re.compile(
    r"(?P<url>https?://[^\s<>()\"']+|(?<!@)\b(?:www\.)?[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)+(?::\d+)?(?:/[^\s<>()\"']*)?)",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s\u2011]?\d{3}[-.\s\u2011]?\d{4}(?:\s*(?:x|ext\.?)\s*\d+)?", re.IGNORECASE)
ADDRESS_RE = re.compile(
    r"\b\d{1,6}\s+[A-Za-z0-9.'#&\s-]+(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Drive|Dr\.?|Highway|Hwy\.?|Trail|Trl\.?|Lane|Ln\.?|Court|Ct\.?|Boulevard|Blvd\.?|Main|Oak|Ryus|Grand)\b[^;,.]*",
    re.IGNORECASE,
)


@dataclass
class RowContext:
    section_id: str
    section_heading: str
    table_heading: str
    headers: list[str]
    cells: list[str]
    links: list[str]


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = value.replace("\xa0", " ")
    value = value.replace("\u2011", "-")
    return " ".join(value.split()).strip()


def normalize_key(value: str) -> str:
    value = clean_text(value).lower()
    value = re.sub(r"\([^)]*\)", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def slugify(value: str) -> str:
    value = normalize_key(value)
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:72] or "resource"


def direct_text(node) -> str:
    return clean_text(" ".join(node.itertext()))


def nearest_section(node) -> tuple[str, str]:
    section = node.getparent()
    while section is not None and section.tag != "section":
        section = section.getparent()
    if section is None:
        return "", ""
    headings = section.xpath("./*[self::h2][1]")
    if not headings:
        headings = section.xpath(".//*[self::h2][1]")
    return section.get("id", ""), direct_text(headings[0]) if headings else ""


def nearest_table_heading(table) -> str:
    node = table.getprevious()
    while node is not None:
        if getattr(node, "tag", None) in {"h2", "h3", "h4"}:
            return direct_text(node)
        node = node.getprevious()
    section = table.getparent()
    while section is not None and section.tag != "section":
        section = section.getparent()
    if section is not None:
        headings = section.xpath("./*[self::h2 or self::h3 or self::h4][1]")
        if headings:
            return direct_text(headings[0])
    return ""


def extract_links(node) -> list[str]:
    links: list[str] = []
    for href in node.xpath(".//a/@href"):
        href = href.strip()
        if href.startswith("http://") or href.startswith("https://"):
            links.append(href)
    text = direct_text(node)
    for match in URL_RE.finditer(text):
        raw = match.group("url").strip(".,;)")
        if "@" in raw:
            continue
        if raw.lower().endswith((".gov", ".org", ".com", ".co", ".us", ".net")) or "/" in raw:
            if not raw.startswith(("http://", "https://")):
                raw = "https://" + raw
            links.append(raw)
    deduped = []
    seen = set()
    for link in links:
        key = link.rstrip("/")
        if key not in seen:
            deduped.append(link)
            seen.add(key)
    return deduped


def get_table_contexts(doc) -> list[RowContext]:
    contexts: list[RowContext] = []
    for table in doc.xpath("//table"):
        section_id, section_heading = nearest_section(table)
        if section_id in SKIP_SECTION_IDS:
            continue
        rows = table.xpath(".//tr")
        if len(rows) < 2:
            continue
        header_cells = rows[0].xpath("./th|./td")
        headers = [direct_text(cell) for cell in header_cells]
        if not headers:
            continue
        first_header = normalize_key(headers[0])
        if first_header not in RESOURCEISH_FIRST_HEADERS:
            continue
        table_heading = nearest_table_heading(table) or section_heading
        for row in rows[1:]:
            cells = [direct_text(cell) for cell in row.xpath("./td|./th")]
            if not cells or not cells[0] or len(cells) == 1:
                continue
            links = extract_links(row)
            contexts.append(
                RowContext(
                    section_id=section_id,
                    section_heading=section_heading,
                    table_heading=table_heading,
                    headers=headers,
                    cells=cells,
                    links=links,
                )
            )
    return contexts


def infer_county(text: str, section_id: str) -> str:
    t = text.lower()
    if section_id.startswith("huerfano"):
        return "Huerfano"
    if section_id.startswith("lasanimas"):
        return "Las Animas"
    if section_id.startswith("colfax") or section_id.startswith("raton"):
        return "Colfax"
    if "huerfano" in t or "walsenburg" in t or "la veta" in t or "cuchara" in t or "spanish peaks" in t:
        return "Huerfano"
    if "las animas" in t or "trinidad" in t or "aguilar" in t or "cokedale" in t:
        return "Las Animas"
    if (
        "colfax" in t
        or "raton" in t
        or "springer" in t
        or "angel fire" in t
        or "eagle nest" in t
        or "red river" in t
        or "cimarron" in t
        or "maxwell" in t
    ):
        return "Colfax"
    return "Regional"


def split_contact_and_category(headers: list[str], cells: list[str], table_heading: str) -> tuple[str, str, str]:
    pairs = {normalize_key(h): cells[i] for i, h in enumerate(headers[: len(cells)])}
    category = ""
    for key in ("category", "services role", "primary economic role", "resource type", "partner type", "channel type"):
        if key in pairs:
            category = pairs[key]
            break
    if not category:
        category = table_heading

    contact_parts = []
    for key in ("available contact", "contact info", "phone", "address", "where to find details", "contact information to use verify"):
        if key in pairs and pairs[key]:
            contact_parts.append(pairs[key])
    if not contact_parts:
        text = " ".join(cells)
        phones = PHONE_RE.findall(text)
        emails = EMAIL_RE.findall(text)
        if phones:
            contact_parts.extend(phones[:2])
        if emails:
            contact_parts.extend(emails[:2])
    contact_info = "; ".join(dict.fromkeys(contact_parts)) if contact_parts else ""

    description_parts = []
    skip_keys = {
        normalize_key(headers[0]) if headers else "",
        "category",
        "available contact",
        "contact info",
        "phone",
        "address",
    }
    for i, cell in enumerate(cells[1:], 1):
        header = headers[i] if i < len(headers) else f"Detail {i}"
        if normalize_key(header) in skip_keys or not cell:
            continue
        description_parts.append(f"{header}: {cell}")
    description = "; ".join(description_parts) or table_heading or category
    return clean_text(category), clean_text(contact_info), clean_text(description)


def persona_scores(text: str) -> Counter:
    t = text.lower()
    scores: Counter = Counter()
    keyword_scores = {
        "FP": [
            "business",
            "retail",
            "restaurant",
            "lodging",
            "hotel",
            "motel",
            "commerce",
            "sales",
            "customer",
            "paid",
            "ad ",
            "advertising",
            "shop",
            "market",
            "bank",
            "real estate",
            "contractor",
            "professional services",
            "tourism",
            "visitor",
            "grocery",
            "food",
        ],
        "NP": [
            "nonprofit",
            "non-profit",
            "foundation",
            "community",
            "public",
            "senior",
            "library",
            "victim",
            "human services",
            "volunteer",
            "social service",
            "grant",
            "donation",
            "fundraiser",
            "accessibility",
        ],
        "PG": [
            "program",
            "initiative",
            "city",
            "county",
            "government",
            "mainstreet",
            "calendar",
            "workforce",
            "training",
            "technical assistance",
            "tourism office",
            "economic development",
            "public notice",
            "data",
            "source",
            "policy",
        ],
        "EN": [
            "entrepreneur",
            "startup",
            "startups",
            "small business",
            "sba",
            "sbdc",
            "loan",
            "capital",
            "financing",
            "business plan",
            "mentor",
            "incubator",
            "pop-up",
            "vendor",
            "home-based",
            "business development",
            "market",
        ],
        "AR": [
            "art",
            "artist",
            "gallery",
            "creative",
            "culture",
            "cultural",
            "museum",
            "music",
            "theatre",
            "theater",
            "studio",
            "craft",
            "maker",
            "heritage",
            "historic",
            "performing",
            "festival",
        ],
    }
    for persona, keywords in keyword_scores.items():
        for keyword in keywords:
            if keyword in t:
                scores[persona] += 1

    # Required roadmap logic.
    if "grant" in t and ("art" in t or "artist" in t or "creative" in t):
        scores["NP"] += 5
        scores["AR"] += 5
    if "business development" in t or "sba" in t:
        scores["FP"] += 5
        scores["EN"] += 5
    if "community initiative" in t:
        scores["NP"] += 5
        scores["PG"] += 5
    return scores


def assign_personas(text: str) -> list[str]:
    scores = persona_scores(text)
    if not scores:
        scores["FP"] = 1
        scores["NP"] = 1
        scores["PG"] = 1
        scores["EN"] = 1
    ranked = sorted(PERSONA_ORDER, key=lambda p: (-scores[p], PERSONA_ORDER.index(p)))
    assigned = [p for p in ranked if scores[p] > 0]
    if len(assigned) < 2 and "PG" not in assigned:
        assigned.append("PG")
    return assigned


def classify_kind(category: str, description: str, source: str) -> str:
    text = f"{category} {description} {source}".lower()
    if any(term in text for term in ("loan", "grant", "financing", "capital", "tax credit", "funding")):
        return "Funding"
    if any(term in text for term in ("training", "technical assistance", "sbdc", "workshop", "mentor")):
        return "Training"
    if any(term in text for term in ("radio", "newspaper", "media", "advertising", "press", "publication", "broadcast")):
        return "Media"
    if any(term in text for term in ("calendar", "tourism", "event", "festival", "visitor")):
        return "Promotion"
    if any(term in text for term in ("restaurant", "retail", "lodging", "grocery", "food", "hotel", "shop")):
        return "Business / Partner"
    if any(term in text for term in ("data", "census", "broadband", "workforce", "research")):
        return "Data Source"
    if any(term in text for term in ("bulletin", "flyer", "notice board", "posting")):
        return "Bulletin / Notice"
    return "Resource"


def checklist_for(kind: str, persona: str) -> list[str]:
    if kind == "Funding":
        return [
            "Prepare a one-page project summary with budget, timeline, and local impact.",
            "Confirm eligibility, match requirements, and required registrations before applying.",
            "Gather tax records, ownership documents, quotes, and job or audience estimates.",
        ]
    if kind == "Training":
        return [
            "Define the exact question you need answered before requesting assistance.",
            "Collect basic business or program details, recent numbers, and known constraints.",
            "Leave the meeting with one assigned next step, deadline, and follow-up contact.",
        ]
    if kind == "Media":
        return [
            "Prepare date, time, location, cost, accessibility notes, and a public contact.",
            "Write a short plain-language blurb plus one longer press-release version.",
            "Ask about calendar deadlines, PSA rules, ad rates, and preferred file formats.",
        ]
    if kind == "Promotion":
        return [
            "Create a reusable event or offer blurb with dates, links, and image credits.",
            "Submit early enough for partner calendars, newsletters, and social scheduling.",
            "Track which partners repost, list, interview, or refer traffic back to you.",
        ]
    if kind == "Bulletin / Notice":
        return [
            "Print a high-contrast flyer with phone, date, location, and QR code.",
            "Ask each location about approval, size limits, takedown dates, and language rules.",
            "Record posting date, contact name, and whether digital cross-posting is possible.",
        ]
    if kind == "Business / Partner":
        return [
            "Verify the current owner or manager contact before making a campaign ask.",
            "Bring a specific, low-effort request such as flyer placement or one shared post.",
            "Offer reciprocal value: referral card, listing, bundle, or partner mention.",
        ]
    if kind == "Data Source":
        return [
            "Define the geography, audience, and date range before pulling the data.",
            "Record the source name, table, retrieval date, and any limitations.",
            "Translate the finding into one outreach decision such as channel, timing, or copy.",
        ]
    return [
        "Identify the person responsible for listings, promotion, or partnership decisions.",
        "Prepare concise materials that can be copied without rewriting.",
        "Record last contact date, response, next step, and verification status.",
    ]


def user_tip_for(persona: str, name: str, kind: str) -> str:
    label = PERSONA_LABELS[persona]
    tips = {
        "FP": f"For-profit users should approach {name} with a clear sales, foot-traffic, or customer-acquisition outcome tied to {kind.lower()}.",
        "NP": f"Non-profits should frame {name} around public benefit, service access, volunteer reach, or measurable community impact.",
        "PG": f"Program leads should use {name} as a coordination point and document participation so the result can support future funding or reporting.",
        "EN": f"Entrepreneurs should use {name} to test demand, sharpen the offer, and build a repeatable outreach habit before spending heavily.",
        "AR": f"Artists should connect {name} to a real event, portfolio, venue, or credited creative work rather than using generic promotion copy.",
    }
    return tips.get(persona, f"{label} users should prepare a specific request before contacting {name}.")


def assign_goal_tags(text: str, kind: str) -> list[str]:
    t = f"{text} {kind}".lower()
    goals: set[str] = set()
    if any(term in t for term in ("business", "startup", "entrepreneur", "program", "mentor", "service", "gallery", "artist", "vendor", "professional services", "retail", "restaurant", "lodging")):
        goals.add("START")
    if any(term in t for term in ("event", "calendar", "tourism", "visitor", "promotion", "partner", "cross-promotion", "festival", "market", "venue")):
        goals.add("PROMOTE")
    if any(term in t for term in ("funding", "grant", "loan", "capital", "sbdc", "technical assistance", "training", "economic development", "business support")):
        goals.add("FUNDING")
    if any(term in t for term in ("media", "radio", "newspaper", "press", "psa", "broadcast", "ad ", "advertising", "coverage")):
        goals.add("MEDIA")
    if any(term in t for term in ("flyer", "bulletin", "notice", "library", "visitor center", "post office", "physical", "board", "field check", "route", "front desk")):
        goals.add("OFFLINE")
    if any(term in t for term in ("website", "social", "facebook", "google", "directory", "online", "digital", "web", "profile")):
        goals.add("ONLINE")
    if any(term in t for term in ("directory", "listing", "correction", "verify", "verification", "contact unknown", "needs", "source missing")):
        goals.add("LISTING")
    if any(term in t for term in ("track", "metric", "report", "attendance", "results", "repost", "survey", "grant report", "log")):
        goals.add("TRACK")

    if kind == "Funding":
        goals.update({"FUNDING", "START"})
    if kind == "Training":
        goals.update({"FUNDING", "START"})
    if kind == "Media":
        goals.update({"MEDIA", "PROMOTE"})
    if kind == "Bulletin / Notice":
        goals.update({"OFFLINE", "PROMOTE"})
    if kind == "Promotion":
        goals.update({"PROMOTE", "ONLINE"})
    if kind == "Business / Partner":
        goals.update({"START", "PROMOTE"})
    if not goals:
        goals.update({"START", "LISTING"})
    return sorted(goals, key=lambda g: list(GOAL_LABELS).index(g))


def infer_confidence(text: str, website: str | None) -> str:
    t = text.lower()
    if "high" in t and "confidence" in t:
        return "High"
    if "medium-low" in t or "medium low" in t:
        return "Low"
    if "medium" in t and "confidence" in t:
        return "Medium"
    if "low" in t and "confidence" in t:
        return "Low"
    if any(term in t for term in ("official", "government", "town directory", "county-listed", "official tourism", "school district", "primary source")):
        return "High"
    if website:
        return "Medium"
    return "Unknown"


def infer_source_type(text: str, website: str | None) -> str:
    t = text.lower()
    if not website:
        return "Unknown"
    if any(term in t for term in ("county", "city", "town", "government", ".gov", "municipal", "official town", "official county")):
        return "Government website"
    if "facebook" in t:
        return "Facebook page"
    if any(term in t for term in ("official tourism", "tourism", "spanish peaks country", "visit trinidad", "explore raton")):
        return "Organization website"
    if "secondary" in t or "wikipedia" in t:
        return "Secondary directory"
    return "Organization website"


def verification_method_for(text: str, website: str | None, confidence: str) -> str:
    t = text.lower()
    if "phone" in t and "verified" in t:
        return "Phone verified"
    if "email" in t and "verified" in t:
        return "Email verified"
    if "field" in t or "in-person" in t:
        return "Manual field check" if confidence in {"Low", "Unknown"} else "In-person verified"
    if "facebook" in t and not website:
        return "Social media only"
    if website:
        return "Primary source checked" if confidence in {"High", "Medium"} else "Secondary source only"
    return "Unverified"


def needs_follow_up_for(text: str, website: str | None, confidence: str) -> bool:
    t = text.lower()
    if confidence in {"Low", "Unknown"}:
        return True
    if not website:
        return True
    return any(term in t for term in ("needs verification", "verify", "unknown", "unspecified", "seasonal", "facebook-only", "field check", "source missing", "inaccessible", "blocked"))


def infer_town(text: str, county: str) -> str:
    normalized = text.lower()
    for town in TOWNS_BY_COUNTY.get(county, []):
        if re.search(rf"\b{re.escape(town.lower())}\b", normalized):
            return town
    if "regional" in normalized or county == "Regional":
        return "Regional"
    return ""


def first_match(pattern: re.Pattern, text: str) -> str:
    match = pattern.search(text)
    return clean_text(match.group(0)) if match else ""


def infer_audience_served(text: str, personas: list[str]) -> list[str]:
    t = text.lower()
    audience = {PERSONA_LABELS[p] for p in personas}
    if any(term in t for term in ("visitor", "tourism", "hotel", "lodging", "rv", "state park", "traveler")):
        audience.add("Visitors / tourists")
    if any(term in t for term in ("youth", "school", "student", "family", "families")):
        audience.add("Youth / families")
    if any(term in t for term in ("senior", "veteran", "health", "clinic", "hospital")):
        audience.add("Health / service audiences")
    if any(term in t for term in ("rural", "ranch", "farm", "post office", "fire district")):
        audience.add("Rural residents")
    if any(term in t for term in ("arts", "gallery", "museum", "creative", "artist", "performance")):
        audience.add("Arts / culture audiences")
    return sorted(audience)


def infer_cost_level(text: str) -> str:
    t = text.lower()
    if any(term in t for term in ("grant", "free", "library", "public", "technical assistance", "sbdc")):
        return "Free or public-service path likely; verify requirements"
    if any(term in t for term in ("paid", "advertising", "ad ", "sponsor", "hotel", "lodging", "restaurant", "retail")):
        return "Paid / commercial or permission-based"
    return "Unknown / verify"


def infer_access_mode(text: str, website: str | None) -> str:
    t = text.lower()
    modes = []
    if website or any(term in t for term in ("website", "facebook", "online", "digital", "directory")):
        modes.append("Online")
    if any(term in t for term in ("address", "street", "st.", "ave", "main", "physical", "flyer", "bulletin", "post office", "library", "visitor center", "front desk")):
        modes.append("Physical")
    if any(term in t for term in ("phone", "call", "719-", "(719)", "email", "@")):
        modes.append("Phone / email")
    return " + ".join(modes) if modes else "Unknown"


def state_for_county(county: str) -> str:
    if county == "Colfax":
        return "NM"
    if county in {"Las Animas", "Huerfano"}:
        return "CO"
    return "NM / CO"


def row_to_resource(ctx: RowContext) -> dict:
    name = clean_text(ctx.cells[0])
    category, contact_info, description = split_contact_and_category(ctx.headers, ctx.cells, ctx.table_heading)
    row_text = " ".join([ctx.section_heading, ctx.table_heading, *ctx.headers, *ctx.cells])
    county = infer_county(row_text, ctx.section_id)
    personas = assign_personas(row_text)
    kind = classify_kind(category, description, ctx.table_heading)
    website = ctx.links[0] if ctx.links else None
    confidence = infer_confidence(row_text, website)
    source_type = infer_source_type(row_text, website)
    verification_method = verification_method_for(row_text, website, confidence)
    contact_blob = " ".join([contact_info, description, row_text])
    town = infer_town(row_text, county)
    resource_id_base = slugify(f"{name}-{county}-{category}")
    return {
        "Name": name,
        "Category": category,
        "Description": description,
        "Contact_Info": contact_info,
        "Town": town,
        "State": state_for_county(county),
        "Contact_Email": first_match(EMAIL_RE, contact_blob),
        "Contact_Phone": first_match(PHONE_RE, contact_blob),
        "Physical_Address": first_match(ADDRESS_RE, contact_blob),
        "Website": website,
        "Source_URL": website,
        "Source_Type": source_type,
        "Verification_Method": verification_method,
        "Confidence_Level": confidence,
        "Needs_Follow_Up": needs_follow_up_for(row_text, website, confidence),
        "Last_Verified_Date": UPDATE_ISO if website and confidence in {"High", "Medium"} else None,
        "Goal_Relevance": assign_goal_tags(row_text, kind),
        "Persona_Relevance": personas,
        "Primary_Persona": personas[0],
        "Audience_Served": infer_audience_served(row_text, personas),
        "Cost_Level": infer_cost_level(row_text),
        "Access_Mode": infer_access_mode(row_text, website),
        "Operational_Notes": "Use as a launch/outreach lead; verify details before spending money, printing materials, or promising eligibility.",
        "County": county,
        "Resource_Type": kind,
        "Source_Section": ctx.section_heading or ctx.table_heading,
        "Source_Anchor": ctx.section_id or None,
        "Last_Updated": UPDATE_ISO,
        "Validation_Status": "not_checked" if website else "no_url",
        "Action_Module": {
            "Requirement_Checklist": checklist_for(kind, personas[0])[:3],
            "Primary_Source_Link": website,
            "User_Tip": user_tip_for(personas[0], name, kind),
        },
        "_id_base": resource_id_base,
    }


CONFIDENCE_RANK = {"Unknown": 0, "Low": 1, "Medium": 2, "High": 3}


def stronger_confidence(a: str | None, b: str | None) -> str:
    first = a or "Unknown"
    second = b or "Unknown"
    return first if CONFIDENCE_RANK.get(first, 0) >= CONFIDENCE_RANK.get(second, 0) else second


def merge_sorted(existing: list[str], incoming: list[str], preferred_order: list[str] | None = None) -> list[str]:
    values = set(existing or []) | set(incoming or [])
    if preferred_order:
        return sorted(values, key=lambda value: preferred_order.index(value) if value in preferred_order else len(preferred_order))
    return sorted(values)


def extract_resources(doc) -> list[dict]:
    resources = [row_to_resource(ctx) for ctx in get_table_contexts(doc)]
    seen: dict[str, dict] = {}
    for resource in resources:
        key = "|".join(
            [
                normalize_key(resource["Name"]),
                normalize_key(resource.get("County", "")),
                normalize_key(resource.get("Category", "")),
            ]
        )
        if key in seen:
            current = seen[key]
            # Preserve direct source links and richer descriptions if duplicates differ.
            if not current.get("Website") and resource.get("Website"):
                current["Website"] = resource["Website"]
                current["Source_URL"] = resource.get("Source_URL") or resource["Website"]
                current["Source_Type"] = resource.get("Source_Type") or current.get("Source_Type")
                current["Verification_Method"] = resource.get("Verification_Method") or current.get("Verification_Method")
                current["Last_Verified_Date"] = resource.get("Last_Verified_Date") or current.get("Last_Verified_Date")
                current["Action_Module"]["Primary_Source_Link"] = resource["Website"]
                current["Validation_Status"] = "not_checked"
            if len(resource.get("Description", "")) > len(current.get("Description", "")):
                current["Description"] = resource["Description"]
            for field in ("Town", "Contact_Email", "Contact_Phone", "Physical_Address"):
                if not current.get(field) and resource.get(field):
                    current[field] = resource[field]
            current["Confidence_Level"] = stronger_confidence(current.get("Confidence_Level"), resource.get("Confidence_Level"))
            current["Needs_Follow_Up"] = bool(current.get("Needs_Follow_Up") or resource.get("Needs_Follow_Up"))
            current["Goal_Relevance"] = merge_sorted(
                current.get("Goal_Relevance", []),
                resource.get("Goal_Relevance", []),
                list(GOAL_LABELS),
            )
            current["Persona_Relevance"] = sorted(
                set(current["Persona_Relevance"]) | set(resource["Persona_Relevance"]),
                key=PERSONA_ORDER.index,
            )
            current["Audience_Served"] = merge_sorted(current.get("Audience_Served", []), resource.get("Audience_Served", []))
            if current.get("Cost_Level", "").startswith("Unknown") and not resource.get("Cost_Level", "").startswith("Unknown"):
                current["Cost_Level"] = resource["Cost_Level"]
            if current.get("Access_Mode") in {"", "Unknown"} and resource.get("Access_Mode"):
                current["Access_Mode"] = resource["Access_Mode"]
            continue
        seen[key] = resource

    id_counts: Counter = Counter()
    final = []
    for resource in seen.values():
        base = resource.pop("_id_base")
        id_counts[base] += 1
        resource["id"] = base if id_counts[base] == 1 else f"{base}-{id_counts[base]}"
        final.append(resource)
    return sorted(final, key=lambda r: (r["County"], r["Resource_Type"], r["Name"].lower()))


def normalized_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
    return url


def check_url(url: str) -> tuple[str, int | None, str]:
    url = normalized_url(url) or ""
    context = ssl.create_default_context()
    headers = {"User-Agent": "TriCountyGuideLinkCheck/1.0"}
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=5, context=context) as response:
                status = getattr(response, "status", None) or response.getcode()
                if status and status < 400:
                    return "ok", status, ""
                return "broken", status, f"HTTP {status}"
        except urllib.error.HTTPError as exc:
            if method == "HEAD" and exc.code in {403, 405, 406, 501}:
                continue
            return "broken", exc.code, f"HTTP {exc.code}"
        except Exception as exc:
            if method == "HEAD":
                continue
            return "timeout_or_error", None, type(exc).__name__
    return "timeout_or_error", None, "unknown_error"


def validate_links(resources: list[dict]) -> dict[str, dict]:
    unique = {}
    for resource in resources:
        url = resource.get("Website") or resource.get("Action_Module", {}).get("Primary_Source_Link")
        if url:
            unique[normalized_url(url).rstrip("/")] = normalized_url(url)

    statuses: dict[str, dict] = {}
    for key, url in sorted(unique.items()):
        state, status, error = check_url(url)
        statuses[key] = {"url": url, "state": state, "status": status, "error": error}
        time.sleep(0.15)

    for resource in resources:
        url = resource.get("Website") or resource.get("Action_Module", {}).get("Primary_Source_Link")
        if not url:
            resource["Validation_Status"] = "no_url"
            resource["Needs_Follow_Up"] = True
            resource["Last_Verified_Date"] = None
            continue
        result = statuses.get(normalized_url(url).rstrip("/"))
        if result:
            resource["Validation_Status"] = result["state"]
            resource["Validation_Checked"] = UPDATE_ISO
            if result["state"] == "ok":
                resource["Last_Verified_Date"] = UPDATE_ISO
                if resource.get("Confidence_Level") in {"High", "Medium"}:
                    resource["Needs_Follow_Up"] = False
                    resource["Verification_Method"] = "Automated link check plus source review"
            else:
                resource["Needs_Follow_Up"] = True
    return statuses


def recommended_replacement(resource: dict) -> str:
    county = resource.get("County", "Regional")
    name = resource.get("Name", "this resource")
    category_text = f"{resource.get('Category', '')} {resource.get('Description', '')} {name}".lower()
    if "sbdc" in name.lower() or "small business development center" in name.lower():
        return "Use the current official Pueblo County SBDC page or the Colorado SBDC Network directory."
    if "Colfax" in county:
        return f"Verify {name} through City of Raton, Explore Raton, GrowRaton, Raton MainStreet, or the relevant town/chamber contact."
    if "Las Animas" in county:
        if "aguilar" in category_text or name in {"Aguilar Country Cottages", "The Station"}:
            return "Verify against the Town of Aguilar tourism/business pages and call the listed business phone before publication: https://www.aguilarco.us/tourism"
        if any(term in category_text for term in ("hotel", "motel", "lodging", "rv", "inn", "resort", "b&b")):
            return "Use the official Visit Trinidad Stay directory as the replacement source path, then phone-verify the listing: https://visittrinidadcolorado.com/stay/"
        if any(term in category_text for term in ("restaurant", "food", "bar", "cafe", "bakery", "sweets")):
            return "Use the official Visit Trinidad Dine directory as the replacement source path, then phone-verify the listing: https://visittrinidadcolorado.com/dine/"
        return f"Verify {name} through Visit Trinidad Colorado, City of Trinidad, The Chronicle-News, or county/chamber contacts."
    if "Huerfano" in county:
        if "city of walsenburg" in name.lower():
            return "Verify through the Huerfano County portal and the current City of Walsenburg state-hosted page; 403 may be bot protection rather than a missing page."
        if "health" in category_text:
            return "Use the official Las Animas-Huerfano Counties District Health Department page path and phone-verify contact details if the site blocks automated checks."
        if "fox theatre" in name.lower():
            return "Verify through the Fox Theatre Walsenburg public site, Huerfano County community-resource links, and current social pages."
        if "fair" in name.lower():
            return "Verify through Huerfano County Fair Board channels and the county events/community-resource links."
        return f"Verify {name} through Spanish Peaks Country, Huerfano County, La Veta/Cuchara Chamber, or World Journal contacts."
    return f"Search the current official website or call the listed organization before publication."


def write_validation_report(resources: list[dict], statuses: dict[str, dict]) -> None:
    resources_by_url: dict[str, list[dict]] = defaultdict(list)
    for resource in resources:
        url = resource.get("Website") or resource.get("Action_Module", {}).get("Primary_Source_Link")
        if url:
            resources_by_url[normalized_url(url).rstrip("/")].append(resource)

    broken_states = {"broken", "timeout_or_error"}
    broken_urls = [key for key, result in statuses.items() if result["state"] in broken_states]
    lines = [
        "# Validation_Report",
        "",
        f"- Generated: {UPDATE_ISO}",
        f"- Total unique URLs checked: {len(statuses)}",
        f"- Broken, timed out, or blocked URLs: {len(broken_urls)}",
        f"- Timeout per request: 5 seconds",
        "",
        "## Summary By Persona",
        "",
    ]
    for persona in PERSONA_ORDER:
        persona_resources = [r for r in resources if persona in r["Persona_Relevance"]]
        checked = [r for r in persona_resources if r.get("Validation_Status") not in {"no_url", "not_checked"}]
        broken = [r for r in checked if r.get("Validation_Status") in broken_states]
        lines.append(f"- {PERSONA_LABELS[persona]}: {len(checked)} linked resources checked; {len(broken)} need manual review.")
    lines.extend(["", "## Broken Or Unconfirmed Links", ""])
    if not broken_urls:
        lines.append("No broken, timed-out, or blocked URLs were detected in the checked set.")
    else:
        for key in broken_urls:
            result = statuses[key]
            linked_resources = resources_by_url[key]
            personas = sorted(
                {p for resource in linked_resources for p in resource["Persona_Relevance"]},
                key=PERSONA_ORDER.index,
            )
            names = ", ".join(resource["Name"] for resource in linked_resources[:4])
            replacement = recommended_replacement(linked_resources[0])
            lines.extend(
                [
                    f"### {result['url']}",
                    "",
                    f"- Status: {result['state']} {result.get('status') or ''} {result.get('error') or ''}".strip(),
                    f"- Resource(s): {names}",
                    f"- Persona categories: {', '.join(PERSONA_LABELS[p] for p in personas)}",
                    f"- Recommended replacement path: {replacement}",
                    "",
                ]
            )
    lines.extend(
        [
            "## Maintenance Notes",
            "",
            "- Treat `no_url` resources as phone/manual-verification records rather than broken links.",
            "- Re-run the extractor/link checker whenever the source tables are updated.",
            "- Record `Last_Updated` and `Validation_Checked` dates before publication.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_css() -> str:
    return r"""
    /* Persona-guided resource finder: implemented from the transformation roadmap. */
    :root {
      --ink: #142B44;
      --paper: #F7F3EA;
      --gold: #B9A36A;
      --moss: #5BAEAD;
      --plum: #6F8FC9;
      --ember: #D48964;
      --growth: #6CB894;
      --danger: #A95656;
      --line: #ded6c6;
      --surface: #ffffff;
      --muted: #4A5563;
      --sky: #d8e7ee;
      --sky-deep: #bdd7df;
      --sage: #b8c4a2;
    }
    *, *::before, *::after { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      font-size: 17px;
      font-family: Arial, sans-serif;
      color: var(--ink);
      background: var(--paper);
      line-height: 1.6;
    }
    h1, h2, h3, h4, nav, button, input, select, textarea {
      font-family: Arial, sans-serif;
      letter-spacing: 0;
    }
    img, svg { max-width: 100%; height: auto; }
    section, table, th, td, p, li, a, .guide-card, .example-box, .warning-box {
      overflow-wrap: anywhere;
    }
    .sr-only {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }
    .site-hero {
      position: relative;
      overflow: hidden;
      padding: 0 0 34px;
      background: linear-gradient(180deg, #e9f0ef 0%, var(--paper) 82%);
      color: var(--ink);
      border-bottom: 3px solid rgba(185,163,106,.58);
    }
    .site-hero::after {
      content: "";
      position: absolute;
      left: 0;
      right: 0;
      bottom: 0;
      height: 8px;
      background: linear-gradient(90deg, var(--gold), var(--plum), var(--ember));
      pointer-events: none;
    }
    .site-hero > * { position: relative; z-index: 1; }
    .hero-copy {
      max-width: 1220px;
      margin: 0 auto;
      padding: 26px 40px 0;
    }
    .mountain-banner {
      position: relative;
      min-height: 260px;
      overflow: hidden;
      background: linear-gradient(180deg, var(--sky) 0%, #edf2ee 62%, var(--paper) 100%);
      border-bottom: 1px solid rgba(185,163,106,.42);
    }
    .mountain-banner svg {
      display: block;
      width: 100%;
      height: 260px;
    }
    .cloud-a { animation: cloudDriftA 44s linear infinite; }
    .cloud-b { animation: cloudDriftB 62s linear infinite; opacity: .78; }
    .cloud-c { animation: cloudDriftC 54s linear infinite; opacity: .62; }
    @keyframes cloudDriftA {
      from { transform: translateX(-220px); }
      to { transform: translateX(1220px); }
    }
    @keyframes cloudDriftB {
      from { transform: translateX(1180px); }
      to { transform: translateX(-360px); }
    }
    @keyframes cloudDriftC {
      from { transform: translateX(-480px); }
      to { transform: translateX(1060px); }
    }
    .brand-row {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 18px;
      flex-wrap: wrap;
      margin-bottom: 18px;
    }
    .brand-lockup {
      display: flex;
      align-items: center;
      gap: 12px;
      font-family: Arial, sans-serif;
    }
    .brand-token {
      width: 42px;
      height: 42px;
      display: inline-grid;
      place-items: center;
      background: var(--gold);
      color: var(--ink);
      border-radius: 50%;
      font-weight: 700;
      border: 2px solid rgba(247,245,240,.7);
      flex: 0 0 auto;
    }
    .brand-text {
      display: grid;
      gap: 2px;
      line-height: 1.15;
      font-size: .82rem;
      letter-spacing: 0;
      text-transform: uppercase;
    }
    .hero-meta {
      margin: 0;
      font-family: Arial, sans-serif;
      font-size: .84rem;
      color: var(--muted);
    }
    .site-hero h1 {
      max-width: 980px;
      font-size: 3.3rem;
      line-height: 1.03;
      margin: 0;
      letter-spacing: 0;
    }
    .site-hero p {
      max-width: 940px;
      margin: 14px 0 0;
      font-size: 1.02rem;
      color: #314256;
    }
    nav {
      gap: 8px;
      align-items: center;
      padding: 12px 40px;
    }
    nav a {
      margin: 0;
      padding: 6px 8px;
      border-radius: 4px;
      line-height: 1.1;
    }
    nav a.active,
    nav a:hover {
      background: var(--gold);
      color: var(--ink);
    }
    nav a:focus-visible,
    .persona-button:focus-visible,
    .goal-button:focus-visible,
    .search-input:focus-visible,
    .filter-select:focus-visible,
    .clear-button:focus-visible,
    .download-strip a:focus-visible,
    .download-strip button:focus-visible,
    .back-to-top:focus-visible {
      outline: 3px solid var(--gold);
      outline-offset: 2px;
    }
    .operational-section {
      max-width: 1220px;
      margin: 0 auto;
      padding: 42px 40px;
      background: var(--paper);
    }
    .operational-section + .operational-section {
      border-top: 3px solid var(--gold);
    }
    .section-kicker {
      margin: 0 0 6px;
      font-weight: 800;
      text-transform: uppercase;
      color: var(--plum);
      font-size: .78rem;
    }
    .download-strip {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 18px 0 24px;
      padding: 12px;
      border: 1px solid var(--line);
      background: #fff;
      border-left: 4px solid var(--gold);
    }
    .download-strip a,
    .download-strip button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 38px;
      border: 1px solid var(--moss);
      background: var(--moss);
      color: #fff;
      border-radius: 4px;
      padding: 7px 10px;
      font-weight: 700;
      text-decoration: none;
      cursor: pointer;
    }
    .download-strip button {
      font-size: 1rem;
    }
    .figure-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
      margin: 22px 0;
    }
    .system-figure {
      margin: 0;
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 6px;
      overflow: hidden;
    }
    .system-figure-art {
      background: var(--paper);
      line-height: 0;
    }
    .system-figure-svg {
      display: block;
      width: 100%;
      height: auto;
    }
    .system-figure figcaption {
      padding: 10px 12px 12px;
      font-size: .88rem;
      color: #3d4654;
      border-top: 1px solid var(--line);
    }
    .decision-grid,
    .workflow-grid,
    .method-grid,
    .template-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 14px;
      margin: 18px 0;
    }
    .decision-grid article,
    .workflow-card,
    .method-grid article,
    .template-box,
    .trust-box {
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 6px;
      padding: 16px;
    }
    .decision-grid article {
      display: grid;
      gap: 6px;
      border-left: 4px solid var(--moss);
    }
    .decision-grid span,
    .workflow-card p,
    .method-grid article,
    .trust-box {
      color: #3d4654;
    }
    .workflow-card h3 {
      margin-top: 0;
      color: var(--ink);
    }
    .step-list {
      margin: 0 0 0 20px;
      padding: 0;
    }
    .step-list li {
      margin: 0 0 8px;
    }
    .template-box summary {
      cursor: pointer;
      font-weight: 800;
      color: var(--ink);
    }
    .template-box pre {
      white-space: pre-wrap;
      background: #f7f5ef;
      border: 1px solid #e1d8c6;
      padding: 12px;
      border-radius: 4px;
      overflow-x: auto;
      font-size: .88rem;
    }
    .trust-box {
      border-left: 4px solid var(--ember);
      margin: 18px 0;
    }
    .table-scroll {
      width: 100%;
      overflow-x: auto;
      margin: 14px 0 24px;
    }
    .table-scroll table {
      margin: 0;
      min-width: 760px;
    }
    .table-scroll th {
      position: sticky;
      top: 0;
      z-index: 1;
    }
    .persona-dashboard {
      padding: 0;
      background: #fff;
      border-bottom: 1px solid #ddd;
    }
    .persona-inner {
      max-width: 1220px;
      margin: 0 auto;
      padding: 32px 40px 40px;
    }
    .persona-kicker {
      margin: 0 0 6px;
      font-family: Arial, sans-serif;
      font-size: .78rem;
      letter-spacing: 0;
      text-transform: uppercase;
      color: var(--plum);
      font-weight: 700;
    }
    .persona-dashboard h2 {
      border-left: 0;
      padding-left: 0;
      margin: 0 0 10px;
      color: var(--ink);
      font-size: 2rem;
    }
    .persona-lede {
      max-width: 900px;
      margin: 0 0 20px;
      color: #424242;
    }
    .persona-controls {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(280px, 420px);
      gap: 16px;
      align-items: end;
      margin: 22px 0;
    }
    .persona-selector {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }
    .persona-button {
      border: 1px solid #bdb6aa;
      background: #fff;
      color: var(--ink);
      padding: 9px 12px;
      border-radius: 4px;
      font-family: Arial, sans-serif;
      font-size: .88rem;
      font-weight: 700;
      cursor: pointer;
    }
    .goal-selector {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 10px 0 0;
    }
    .goal-button {
      border: 1px solid #bdb6aa;
      background: #fff;
      color: var(--ink);
      padding: 8px 10px;
      border-radius: 4px;
      font-family: Arial, sans-serif;
      font-size: .84rem;
      font-weight: 700;
      cursor: pointer;
    }
    .persona-button[aria-pressed="true"],
    .goal-button[aria-pressed="true"] {
      background: var(--moss);
      border-color: var(--moss);
      color: var(--paper);
    }
    .filter-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin: 0 0 20px;
    }
    .filter-grid label {
      display: grid;
      gap: 5px;
      font-size: .8rem;
      font-weight: 700;
      color: #3f3f3f;
    }
    .filter-select {
      min-height: 40px;
      border: 1px solid #bbb;
      border-radius: 4px;
      padding: 7px 8px;
      background: #fff;
      color: var(--ink);
      font: 1rem Arial, sans-serif;
    }
    .search-wrap label {
      display: block;
      font-family: Arial, sans-serif;
      font-size: .8rem;
      font-weight: 700;
      margin-bottom: 6px;
      color: #3f3f3f;
    }
    .search-row {
      display: flex;
      gap: 8px;
    }
    .search-input {
      width: 100%;
      min-height: 42px;
      border: 1px solid #bbb;
      border-radius: 4px;
      padding: 8px 10px;
      font: 1rem Arial, sans-serif;
    }
    .clear-button {
      border: 1px solid var(--moss);
      background: var(--moss);
      color: var(--paper);
      border-radius: 4px;
      padding: 8px 12px;
      font-family: Arial, sans-serif;
      cursor: pointer;
    }
    .status-strip {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 10px;
      margin: 18px 0 22px;
    }
    .status-item {
      border: 1px solid #ddd;
      background: var(--paper);
      padding: 12px;
      border-radius: 4px;
      min-height: 70px;
    }
    .status-item strong {
      display: block;
      font-family: Arial, sans-serif;
      font-size: 1.2rem;
      color: var(--moss);
    }
    .status-item span {
      display: block;
      font-family: Arial, sans-serif;
      font-size: .77rem;
      color: #555;
      margin-top: 3px;
    }
    .resource-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
      gap: 14px;
    }
    .resource-card {
      display: grid;
      gap: 10px;
      border: 1px solid #d8d3c8;
      border-left: 4px solid var(--gold);
      background: #fff;
      border-radius: 6px;
      padding: 16px;
      min-width: 0;
      box-shadow: 0 1px 2px rgba(0,0,0,.04);
    }
    .resource-card h3 {
      color: var(--ink);
      font-size: 1.12rem;
      line-height: 1.25;
      margin: 0;
    }
    .card-meta,
    .card-source,
    .card-contact {
      font-family: Arial, sans-serif;
      color: #4f4f4f;
      font-size: .84rem;
      overflow-wrap: anywhere;
    }
    .card-description {
      margin: 0;
      color: #333;
      font-size: .94rem;
      line-height: 1.55;
    }
    .persona-chip-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .persona-chip,
    .resource-type,
    .goal-chip,
    .confidence-chip,
    .follow-up-chip {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      border-radius: 999px;
      padding: 3px 8px;
      font-family: Arial, sans-serif;
      font-size: .72rem;
      font-weight: 700;
      background: #f1eee6;
      color: #2f2f2f;
      border: 1px solid #ded8cb;
    }
    .resource-type {
      background: #edf3ec;
      border-color: #cbdacb;
      color: var(--moss);
    }
    .goal-chip {
      background: #eef4ff;
      border-color: #c7d7ff;
      color: var(--plum);
    }
    .confidence-chip {
      background: #fff8e2;
      border-color: #ead48f;
      color: #654a00;
    }
    .follow-up-chip {
      background: #fff0ea;
      border-color: #ffc5aa;
      color: #8a2f00;
    }
    .resource-link {
      font-family: Arial, sans-serif;
      color: var(--moss);
      font-weight: 700;
      overflow-wrap: anywhere;
    }
    .resource-actions {
      border-top: 1px solid #e4dfd5;
      padding-top: 8px;
    }
    .resource-actions summary {
      cursor: pointer;
      font-family: Arial, sans-serif;
      font-weight: 700;
      color: var(--moss);
    }
    .resource-actions ul {
      margin: 8px 0 8px 20px;
      padding: 0;
    }
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-family: Arial, sans-serif;
      font-size: .78rem;
      color: #555;
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #777;
    }
    .status-dot.ok { background: #2f7d32; }
    .status-dot.no-url { background: #8a8174; }
    .status-dot.timeout-or-error,
    .status-dot.broken { background: var(--ember); }
    .card-detail-list {
      display: grid;
      gap: 4px;
      margin: 0;
      padding: 0;
      list-style: none;
      color: #4f4f4f;
      font-size: .84rem;
    }
    .empty-state {
      border: 1px dashed #bbb;
      background: var(--paper);
      padding: 20px;
      border-radius: 4px;
      color: #444;
    }
    .noscript-note {
      border: 1px solid var(--line);
      background: #fff8e2;
      padding: 12px;
      border-radius: 4px;
      margin: 16px 0;
    }
    .source-guide-note {
      max-width: 1220px;
      margin: 0 auto;
      padding: 20px 40px 0;
      font-family: Arial, sans-serif;
      color: #555;
      font-size: .88rem;
    }
    .guide-brand-footer {
      background: #f1eadf;
      border-top: 3px solid rgba(185,163,106,.58);
      padding: 30px 40px 34px;
    }
    .footer-inner {
      max-width: 1220px;
      margin: 0 auto;
      display: grid;
      gap: 18px;
    }
    .logo-row {
      display: flex;
      gap: 18px;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
    }
    .logo-card {
      min-height: 104px;
      display: flex;
      align-items: center;
      gap: 14px;
      flex: 1 1 320px;
      padding: 14px 16px;
      border: 1px solid rgba(20,43,68,.14);
      background: rgba(255,255,255,.66);
      border-radius: 8px;
    }
    .logo-card img {
      display: block;
      max-height: 72px;
      max-width: 210px;
      object-fit: contain;
      flex: 0 0 auto;
    }
    .logo-card.super-eukarya img {
      max-width: 260px;
      max-height: 76px;
    }
    .logo-card span {
      display: grid;
      gap: 2px;
      color: var(--muted);
      font-size: .86rem;
    }
    .logo-card strong {
      color: var(--ink);
      font-size: .95rem;
    }
    .brand-source-note {
      margin: 0;
      color: var(--muted);
      font-size: .82rem;
    }
    .back-to-top {
      position: fixed;
      right: 18px;
      bottom: 18px;
      z-index: 10;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 38px;
      padding: 8px 10px;
      background: var(--ink);
      color: #fff;
      border-radius: 4px;
      text-decoration: none;
      font-weight: 800;
      box-shadow: 0 2px 8px rgba(0,0,0,.18);
    }
    @media (max-width: 900px) {
      .persona-controls,
      .status-strip,
      .filter-grid {
        grid-template-columns: 1fr;
      }
      .site-hero,
      nav,
      .persona-inner,
      .source-guide-note,
      .operational-section,
      .guide-brand-footer,
      .hero-copy {
        padding-left: 22px;
        padding-right: 22px;
      }
      .site-hero h1 { font-size: 2.45rem; }
    }
    @media (max-width: 768px) {
      section {
        padding: 28px 22px;
      }
      table, thead, tbody, th, td, tr {
        width: 100%;
        max-width: 100%;
        box-sizing: border-box;
      }
      td {
        padding: 8px 0;
      }
      td::before {
        content: none;
        display: none;
      }
      .ad-spot {
        width: 100%;
      }
    }
    @media (max-width: 560px) {
      .site-hero h1 { font-size: 2rem; }
      .mountain-banner,
      .mountain-banner svg { min-height: 200px; height: 200px; }
      .persona-button { flex: 1 1 calc(50% - 8px); }
      .goal-button { flex: 1 1 calc(50% - 8px); }
      .resource-grid { grid-template-columns: 1fr; }
      .search-row { flex-direction: column; }
      nav {
        max-height: 48vh;
        overflow-y: auto;
      }
    }
    @media (prefers-reduced-motion: reduce) {
      html { scroll-behavior: auto; }
      *, *::before, *::after {
        animation-duration: .01ms !important;
        animation-iteration-count: 1 !important;
        scroll-behavior: auto !important;
        transition-duration: .01ms !important;
      }
      .cloud-a,
      .cloud-b,
      .cloud-c {
        animation: none !important;
      }
    }
    @media print {
      nav,
      .persona-controls,
      .filter-grid,
      .download-strip,
      .clear-button,
      .back-to-top {
        display: none !important;
      }
      body {
        background: #fff;
        color: #000;
        font-size: 11pt;
      }
      .site-hero,
      .persona-dashboard,
      .operational-section,
      .guide-brand-footer,
      section {
        padding: 18px 0 !important;
        max-width: none !important;
        background: #fff !important;
      }
      a[href^="http"]::after {
        content: " (" attr(href) ")";
        font-size: .85em;
      }
      table {
        page-break-inside: auto;
      }
      tr {
        break-inside: avoid;
        page-break-inside: avoid;
      }
      .resource-card,
      .workflow-card,
      .template-box,
      .system-figure {
        break-inside: avoid;
        box-shadow: none;
      }
    }
"""


def asset_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime_type};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def make_mountain_banner() -> str:
    return """<div class="mountain-banner" aria-label="Animated clouds drifting over a mountain skyline">
<svg viewBox="0 0 1200 300" preserveAspectRatio="none" role="img" aria-labelledby="mountain-banner-title mountain-banner-desc">
<title id="mountain-banner-title">Clouds over mountain banner</title>
<desc id="mountain-banner-desc">Soft animated clouds move across layered mountains above the guide heading.</desc>
<defs>
<linearGradient id="banner-sky" x1="0" x2="0" y1="0" y2="1">
<stop offset="0%" stop-color="#D8E7EE"/>
<stop offset="58%" stop-color="#EAF1EE"/>
<stop offset="100%" stop-color="#F7F3EA"/>
</linearGradient>
<linearGradient id="banner-mountain" x1="0" x2="0" y1="0" y2="1">
<stop offset="0%" stop-color="#6F8FC9" stop-opacity=".74"/>
<stop offset="100%" stop-color="#142B44" stop-opacity=".58"/>
</linearGradient>
<filter id="cloud-soften" x="-30%" y="-50%" width="160%" height="200%">
<feGaussianBlur stdDeviation="1.6"/>
</filter>
</defs>
<rect width="1200" height="300" fill="url(#banner-sky)"/>
<circle cx="980" cy="72" r="42" fill="#F4DDAE" opacity=".48"/>
<path d="M0 218 C132 164 214 168 326 220 C426 266 548 142 650 196 C770 260 856 150 968 194 C1060 230 1120 206 1200 176 V300 H0 Z" fill="#9DB6C7" opacity=".42"/>
<path d="M0 244 C120 200 240 220 332 178 C434 132 528 212 616 174 C736 122 850 200 940 168 C1038 132 1110 180 1200 148 V300 H0 Z" fill="url(#banner-mountain)"/>
<path d="M0 258 C120 224 244 238 360 210 C486 178 570 246 690 214 C828 176 938 238 1044 210 C1112 192 1164 192 1200 184 V300 H0 Z" fill="#142B44" opacity=".28"/>
<g class="cloud-a" filter="url(#cloud-soften)">
<ellipse cx="90" cy="78" rx="58" ry="19" fill="#FFFFFF" opacity=".80"/>
<ellipse cx="138" cy="72" rx="38" ry="15" fill="#FFFFFF" opacity=".72"/>
<ellipse cx="52" cy="82" rx="32" ry="13" fill="#FFFFFF" opacity=".62"/>
</g>
<g class="cloud-b" filter="url(#cloud-soften)">
<ellipse cx="990" cy="114" rx="72" ry="22" fill="#FFFFFF" opacity=".74"/>
<ellipse cx="1048" cy="108" rx="44" ry="16" fill="#FFFFFF" opacity=".66"/>
<ellipse cx="930" cy="118" rx="38" ry="14" fill="#FFFFFF" opacity=".56"/>
</g>
<g class="cloud-c" filter="url(#cloud-soften)">
<ellipse cx="340" cy="48" rx="48" ry="15" fill="#FFFFFF" opacity=".52"/>
<ellipse cx="378" cy="43" rx="30" ry="11" fill="#FFFFFF" opacity=".48"/>
</g>
<path d="M0 280 C160 266 260 278 410 266 C620 250 740 280 930 260 C1050 248 1138 258 1200 246 V300 H0 Z" fill="#F7F3EA" opacity=".95"/>
</svg>
</div>"""


def make_logo_footer() -> str:
    raton_logo = asset_data_uri(BRAND_ASSET_DIR / "raton-logo.png")
    se_logo = asset_data_uri(BRAND_ASSET_DIR / "super-eukarya-logo.png")
    raton_image = f'<img src="{raton_logo}" alt="Raton, New Mexico logo"/>' if raton_logo else '<strong>City of Raton</strong>'
    se_image = f'<img src="{se_logo}" alt="Super Eukarya Design logo"/>' if se_logo else '<strong>Super Eukarya</strong>'
    return f"""<footer id="guide-brand-footer" class="guide-brand-footer" aria-labelledby="brand-footer-title">
<div class="footer-inner">
<h2 id="brand-footer-title" class="sr-only">Guide credits and logo sources</h2>
<div class="logo-row">
<div class="logo-card raton-logo">
{raton_image}
<span><strong>City of Raton / Explore Raton</strong><small>Official local branding reference for the Raton portion of the guide.</small></span>
</div>
<div class="logo-card super-eukarya">
{se_image}
<span><strong>Super Eukarya Design</strong><small>Local brand asset used for guide design and visual system credit.</small></span>
</div>
</div>
<p class="brand-source-note">Raton logo source: official Explore Raton tourism site. Super Eukarya logo source: local brand asset on this computer. Logos are placed here as credits, not as endorsement claims.</p>
</div>
</footer>"""


def make_header() -> str:
    return f"""<header class="site-hero" id="top">
{make_mountain_banner()}
<div class="hero-copy">
<p class="hero-meta">Structured resource layer updated {UPDATE_ISO} · Regional outreach, funding, media, and partner pathways</p>
<h1>Tri-County Marketing Guide &amp; Business Support Resources</h1>
<p>Outreach, funding, promotion, and partnership resources for Colfax County, Las Animas County, and Huerfano County businesses, nonprofits, programs, entrepreneurs, and artists.</p>
</div>
</header>"""


def make_nav() -> str:
    links = [
        ("#start-here", "Start Here"),
        ("#persona-dashboard", "Resource Directory"),
        ("#launch-pathways", "Step-by-Step"),
        ("#county-recipes", "County Recipes"),
        ("#templates", "Templates"),
        ("#metrics-reporting", "Metrics"),
        ("#submit-correct", "Submit / Correct"),
        ("#about-methodology", "Method"),
        ("#toc", "Contents"),
        ("#funding", "Funding"),
        ("#training", "Training"),
        ("#marketing", "Marketing"),
        ("#media", "Media"),
        ("#bulletins", "Bulletins"),
        ("#retail", "Retail"),
        ("#social", "Social"),
        ("#visibility", "Visibility"),
        ("#demographics-deep-research", "Audience Data"),
        ("#county-resources", "County Resources"),
        ("#colfax-business-inventory", "Colfax Inventory"),
        ("#lasanimas-outreach-inventory", "Las Animas Inventory"),
        ("#huerfano-outreach-inventory", "Huerfano Inventory"),
        ("#events", "Events"),
        ("#accessibility", "Accessibility"),
        ("#recommendations", "Recommendations"),
    ]
    return "<nav aria-label=\"Primary navigation\">\n" + "\n".join(
        f'<a href="{href}">{label}</a>' for href, label in links
    ) + "\n</nav>"


def inline_svg(filename: str, title: str, caption: str) -> str:
    path = VISUAL_ASSET_DIR / filename
    if not path.exists():
        return ""
    svg = path.read_text(encoding="utf-8")
    prefix = slugify(filename)
    svg = svg.replace('aria-labelledby="title desc"', f'aria-labelledby="{prefix}-title {prefix}-desc"')
    svg = svg.replace('id="title"', f'id="{prefix}-title"', 1)
    svg = svg.replace('id="desc"', f'id="{prefix}-desc"', 1)
    if "system-figure-svg" not in svg:
        svg = svg.replace("<svg ", '<svg class="system-figure-svg" ', 1)
    return f"""<figure class="system-figure">
<div class="system-figure-art">{svg}</div>
<figcaption><strong>{html_module.escape(title)}</strong> {html_module.escape(caption)}</figcaption>
</figure>"""


def make_start_here_section() -> str:
    return f"""<section class="guide-section operational-section" id="start-here" aria-labelledby="start-here-title">
<p class="section-kicker">Start here</p>
<h2 id="start-here-title">Choose the job you need the guide to do today</h2>
<p>This guide is organized for people starting or growing a nonprofit, business, gallery, program, service, mentorship, event, or creative practice with limited time, limited background resources, and uneven local information. Use the closest path below, then use the Resource Directory to find local partners, posting locations, media channels, funders, and verification leads.</p>
<div class="download-strip" aria-label="Download options">
<a href="{DOWNLOAD_ZIP_PATH.name}" download>Download full package</a>
<a href="{DOWNLOAD_HTML_PATH.name}" download>Download standalone HTML</a>
<a href="{CSV_PATH.name}" download>Download CSV resource table</a>
<a href="{JSON_PATH.name}" download>Download JSON data</a>
<a href="{REPORT_PATH.name}" download>Open validation report</a>
<button type="button" onclick="window.print()">Print / save as PDF</button>
</div>
<div class="figure-grid">
{inline_svg("se_system_map.svg", "Regional system map.", "The guide treats visibility as a working system: civic anchors, media, tourism, funders, storefronts, libraries, schools, and physical routes all reinforce each other.")}
{inline_svg("se_persona_finder_diagram.svg", "Persona finder logic.", "Resources are tagged for for-profits, nonprofits, programs, entrepreneurs, and artists, then filtered by the task the user is trying to complete.")}
</div>
<div class="decision-grid">
<article><strong>Promote an event.</strong><span>Use the event pathway, then filter for Promotion, Media, Bulletin / Notice, Tourism, and Business / Partner records.</span></article>
<article><strong>Find funding or business support.</strong><span>Use the funding pathway, then filter for Funding, Training, Economic Development, SBDC, chamber, and public-service records.</span></article>
<article><strong>Get media coverage.</strong><span>Use the media pathway, then filter for Media, radio, newspaper, tourism offices, and calendars.</span></article>
<article><strong>Place flyers or reach offline audiences.</strong><span>Use the flyer pathway, then filter for Bulletin / Notice, libraries, visitor centers, lodging, schools, post offices, and storefront routes.</span></article>
<article><strong>Improve online visibility.</strong><span>Use the online pathway, then filter for directories, tourism pages, social channels, websites, and partner listings.</span></article>
<article><strong>Add or correct a listing.</strong><span>Use the submit/correct form spec and prioritize records marked Manual verification, Low confidence, Unknown, or Needs follow-up.</span></article>
</div>
<div class="trust-box"><strong>Plain-language premise:</strong> this is a launch and outreach tool, not an endorsement list, legal guide, grant guarantee, media guarantee, or final authority on eligibility. Verify dates, requirements, costs, permissions, and current contacts before committing money or public promises.</div>
</section>"""


def make_launch_pathways_section() -> str:
    return f"""<section class="guide-section operational-section" id="launch-pathways" aria-labelledby="launch-pathways-title">
<p class="section-kicker">Step-by-step methodologies</p>
<h2 id="launch-pathways-title">Use repeatable launch pathways instead of starting from a blank page</h2>
<p>Each pathway is designed for a person who may not already know the local ecosystem. The method is intentionally practical: define the ask, prepare a small packet, choose channels, log outreach, then update the guide when reality disagrees with the record.</p>
<div class="figure-grid">
{inline_svg("se_visibility_stack.svg", "Visibility stack.", "Online directories, event calendars, social posts, physical flyers, media, and partner referrals work best as a stack rather than isolated tasks.")}
{inline_svg("se_funding_pipeline.svg", "Funding pipeline.", "Funding work starts with fit and readiness before applications, sponsorship asks, or reporting.")}
</div>
<div class="workflow-grid">
<article class="workflow-card">
<h3>Promote an Event</h3>
<ol class="step-list">
<li>Write one verified event fact sheet: title, date, time, address, cost, audience, accessibility, contact, image, and deadline.</li>
<li>Submit to tourism, chamber, city, county, library, college, venue, and calendar channels first.</li>
<li>Send media and radio copy with a short local angle, not only a flyer.</li>
<li>Ask three aligned partners for a repost, counter flyer, newsletter mention, or staff reminder.</li>
<li>Record where it was submitted, who approved it, and what response came back.</li>
</ol>
</article>
<article class="workflow-card">
<h3>Find Funding / Business Support</h3>
<ol class="step-list">
<li>Name the actual need: startup cost, equipment, rent, training, staff time, marketing, accessibility, inventory, or working capital.</li>
<li>Separate grant, loan, sponsorship, donation, technical assistance, and earned-revenue paths.</li>
<li>Confirm eligibility, deadlines, match requirements, reporting burden, tax status, and geography before applying.</li>
<li>Prepare a one-page budget, plain-language project summary, timeline, audience, and proof of community need.</li>
<li>Log every contact and follow-up so the next person does not restart the research.</li>
</ol>
</article>
<article class="workflow-card">
<h3>Get Media Coverage</h3>
<ol class="step-list">
<li>Decide whether the story is news, calendar, feature, paid ad, interview, PSA, or community announcement.</li>
<li>Write a 150-word release and a 30-second spoken PSA from the same facts.</li>
<li>Send at least two weeks ahead when possible, then follow up once with a specific local hook.</li>
<li>Offer one named spokesperson, one image, and a reliable phone/email contact.</li>
<li>Archive links, clippings, air dates, and reporter notes for future funding reports.</li>
</ol>
</article>
<article class="workflow-card">
<h3>Flyers / Offline Outreach</h3>
<ol class="step-list">
<li>Print a readable flyer with high contrast, large date/time, plain location, QR code, phone number, and accessibility note.</li>
<li>Call or ask in person before posting at libraries, schools, public buildings, visitor centers, lodging desks, shops, and boards.</li>
<li>Build a route by county and town, then photograph or log completed drops.</li>
<li>Refresh high-traffic sites seven to ten days before an event or deadline.</li>
<li>Record "no posting allowed" and "ask this person next time" notes in the directory.</li>
</ol>
</article>
<article class="workflow-card">
<h3>Online Visibility</h3>
<ol class="step-list">
<li>Make one canonical public page with current facts, images, location, phone/email, accessibility, and cost.</li>
<li>Claim or update relevant directory profiles and tourism/chamber listings.</li>
<li>Use consistent names, addresses, hours, and links across every listing.</li>
<li>Add alt text, image credits, and plain-language descriptions for accessibility and credibility.</li>
<li>Review search results monthly and correct stale listings before launching new promotions.</li>
</ol>
</article>
<article class="workflow-card">
<h3>Add / Correct a Listing</h3>
<ol class="step-list">
<li>Collect the correction source: official site, phone confirmation, email confirmation, public page, or field observation.</li>
<li>Label the confidence level and verification method.</li>
<li>Do not publish private contacts unless they are intended for public use.</li>
<li>Keep outdated or uncertain records in the follow-up list instead of deleting useful leads too early.</li>
<li>Re-export the HTML, CSV, JSON, and validation report after changes.</li>
</ol>
</article>
</div>
{inline_svg("se_bulletin_media_network.svg", "Bulletin and media network.", "Offline posting and local media work best when they are routed, permissioned, and logged.")}
</section>"""


def make_county_recipes_section() -> str:
    return f"""<section class="guide-section operational-section" id="county-recipes" aria-labelledby="county-recipes-title">
<p class="section-kicker">County campaign recipes</p>
<h2 id="county-recipes-title">Pick a route, then adapt it to the project</h2>
<p>These recipes convert the inventory into first-wave outreach routes. They should be treated as working campaign plans that get better after each phone call, flyer drop, calendar submission, and correction.</p>
<div class="figure-grid">
{inline_svg("se_tri_county_route_nodes.svg", "Tri-county route nodes.", "The strongest campaigns combine hub towns with smaller rural verification nodes rather than assuming one online channel reaches everyone.")}
{inline_svg("se_cross_promotion_loop.svg", "Cross-promotion loop.", "Partners become more useful when asks, reposts, physical materials, and follow-up notes cycle back into the directory.")}
</div>
<div class="workflow-grid">
<article class="workflow-card"><h3>Colfax / Raton First Wave</h3><p>Start with Raton civic, tourism, MainStreet, media, downtown storefront, library, school, event, and business-support nodes. Add Springer, Cimarron, Eagle Nest, Angel Fire, Maxwell, and Ute Park after the core message is stable.</p><p><strong>Best for:</strong> startup announcements, downtown promotions, events, tourism tie-ins, artist visibility, and business-support referrals.</p></article>
<article class="workflow-card"><h3>Las Animas / Trinidad First Wave</h3><p>Start with Visit Trinidad, downtown food/lodging/arts nodes, Space to Create, CREATE Trinidad, museums, Main Street LIVE, Trinidad Chronicle-News, college, hospital, and library/community anchors. Add Aguilar, Branson, Hoehne, Weston, Cokedale, Kim, and Model by route.</p><p><strong>Best for:</strong> event promotion, visitor-facing projects, arts/culture, lodging partnerships, rural flyer circuits, and verification-heavy county updates.</p></article>
<article class="workflow-card"><h3>Huerfano / Walsenburg First Wave</h3><p>Start with Huerfano County, Walsenburg civic anchors, Spanish Peaks Library District, Spanish Peaks Regional Health Center, KSPK-FM, Fox Theatre, Walsenburg Mining Museum, Heritage Park visitor information, and countywide organizations.</p><p><strong>Best for:</strong> countywide public-service outreach, radio reminders, health/service campaigns, visitor information, and funding/business-support routing.</p></article>
<article class="workflow-card"><h3>La Veta / Cuchara Extension</h3><p>Use La Veta's official business directory and arts/culture density for a second-wave merchant route. Use Cuchara and Gardner as seasonal, outdoor, valley, and public-service follow-up routes.</p><p><strong>Best for:</strong> arts, wellness, lodging, tourism, mountain recreation, summer campaigns, and Main Street cross-promotion.</p></article>
<article class="workflow-card"><h3>Cross-County Recipe</h3><p>Create one fact sheet, one press release, one square image, one flyer, one radio PSA, one partner email, and one tracker. Submit digitally first, then complete physical routes by hub town and rural corridor.</p><p><strong>Best for:</strong> regional events, shared services, mentorship programs, nonprofit launches, traveling exhibits, and campaigns that need broad trust.</p></article>
<article class="workflow-card"><h3>Rural / Offline Recipe</h3><p>Do not assume a missing website means no audience. Use schools, libraries, post offices, fire districts, churches, visitor centers, lodging desks, stores, resident referrals, and field notes. Mark unknown records clearly.</p><p><strong>Best for:</strong> services for residents, public meetings, health information, youth/family programming, and rural business discovery.</p></article>
</div>
</section>"""


def make_templates_section() -> str:
    return """<section class="guide-section operational-section" id="templates" aria-labelledby="templates-title">
<p class="section-kicker">Templates</p>
<h2 id="templates-title">Copy-ready outreach templates</h2>
<p>Replace bracketed fields with verified facts. Keep claims narrow, local, and checkable.</p>
<div class="template-grid">
<details class="template-box" open><summary>Press Release</summary><pre>FOR IMMEDIATE RELEASE
[Organization / project] announces [event / service / launch] in [town]

[Town, State] - [One-sentence news hook]. [Who is doing what, when, where, and why it matters locally.]

Details: [date], [time], [address], [cost], [registration link or phone].
Accessibility / language / family note: [verified note].
Contact: [public name], [phone], [email], [website].
</pre></details>
<details class="template-box"><summary>Calendar Listing</summary><pre>[Title]
[Date], [time]
[Venue], [street address], [town]
[One or two sentence description]
Cost: [free / paid / suggested donation]
More info: [public phone/email/link]</pre></details>
<details class="template-box"><summary>Radio PSA</summary><pre>Hi, this is [name] with [organization]. Join us for [event/service] on [date] at [time] at [location] in [town]. [One benefit or community reason]. Learn more at [short link] or call [phone].</pre></details>
<details class="template-box"><summary>Facebook Event Post</summary><pre>You're invited: [event title]
[Date/time] at [location]

[Plain-language value for the audience]. Bring [what to bring]. Cost is [cost]. Questions: [contact].</pre></details>
<details class="template-box"><summary>Instagram Caption</summary><pre>[Short hook].

[What is happening] in [town] on [date]. Good for [audience]. Details at [link in bio / short URL].

Alt text: [brief factual image description].
#RatonNM #TrinidadCO #WalsenburgCO #LaVetaCO #SouthernColorado #NorthernNewMexico</pre></details>
<details class="template-box"><summary>Flyer Text</summary><pre>[BIG TITLE]
[Date] | [Time]
[Venue name], [street address], [town]

[One sentence: who this is for and what they will get.]

Cost: [cost]
Questions: [phone] | [email]
Accessibility: [verified note]
Scan for details: [QR code]</pre></details>
<details class="template-box"><summary>Partner Outreach Email</summary><pre>Subject: Local cross-promotion request for [event/project]

Hi [name],

I'm reaching out because [reason this fits their audience]. Could you share [event/project] with [specific channel: calendar, newsletter, counter flyer, staff, social]?

Verified details are below. I can send a square image, flyer PDF, or shorter blurb if useful.

[details]

Thank you,
[name]</pre></details>
<details class="template-box"><summary>Sponsor / Funder Ask</summary><pre>We are seeking [amount / in-kind support] for [specific need]. The support will help [audience] by [measurable benefit]. We will acknowledge support through [channels] and report back with [attendance, reach, photos, outcomes]. Deadline: [date].</pre></details>
<details class="template-box"><summary>Post-Event Recap</summary><pre>[Number] people attended / participated in [event/service]. Outreach came from [top channels]. Partners included [partners]. What worked: [notes]. What to change next time: [notes]. New directory corrections found: [notes].</pre></details>
<details class="template-box"><summary>Alt Text</summary><pre>[Image type] showing [main subject] at [location/context]. Include visible text only if it is important. Avoid "image of" unless needed.</pre></details>
<details class="template-box"><summary>Campaign Tracker Fields</summary><pre>Campaign | County | Town | Channel | Resource/contact | Sent/dropped date | Permission status | Cost | Response | Link/photo proof | Follow-up date | Result | Directory correction needed</pre></details>
<details class="template-box"><summary>"Where did you hear about this?" Survey</summary><pre>Where did you hear about this?
[ ] Friend/family
[ ] Flyer/poster
[ ] Facebook/Instagram
[ ] Website/search
[ ] Newspaper/radio
[ ] Library/school/public building
[ ] Business/partner referral
[ ] Other: ______</pre></details>
</div>
</section>"""


def make_metrics_section() -> str:
    return """<section class="guide-section operational-section" id="metrics-reporting" aria-labelledby="metrics-title">
<p class="section-kicker">Metrics and reporting</p>
<h2 id="metrics-title">Track enough to learn, report, and improve</h2>
<p>A simple campaign log makes the guide useful for people with limited time because it preserves what worked, what failed, who answered, and which records need correction.</p>
<table><thead><tr><th>Metric</th><th>Why it matters</th><th>Low-effort collection method</th></tr></thead><tbody>
<tr><td>Submissions sent</td><td>Shows whether promotion was actually distributed.</td><td>Log calendar, media, partner, and directory submissions by date.</td></tr>
<tr><td>Approvals / placements</td><td>Separates submitted from published.</td><td>Save links, screenshots, clippings, email replies, or photos.</td></tr>
<tr><td>Physical route completion</td><td>Protects rural/offline outreach from becoming guesswork.</td><td>Use a route checklist and photo log for permitted flyer drops.</td></tr>
<tr><td>Cost and volunteer hours</td><td>Helps plan future budgets and sponsorship asks.</td><td>Track printing, ads, mileage, staff time, and donated time.</td></tr>
<tr><td>Attendance, inquiries, referrals, or sales</td><td>Connects outreach to actual outcomes.</td><td>Count sign-ins, calls, emails, sales, registrations, or partner referrals.</td></tr>
<tr><td>Source-of-awareness survey</td><td>Identifies which channels deserve repeat use.</td><td>Ask one question at sign-in, checkout, registration, or follow-up.</td></tr>
<tr><td>Directory corrections found</td><td>Keeps the guide alive and honest.</td><td>Record bad links, moved businesses, new contacts, closed locations, and posting rules.</td></tr>
</tbody></table>
<div class="trust-box"><strong>Reporting rule:</strong> do not inflate reach. Use "submitted to," "published by," "estimated foot traffic," and "confirmed attendance" as separate numbers.</div>
</section>"""


def make_intake_correction_section() -> str:
    return """<section class="guide-section operational-section" id="submit-correct" aria-labelledby="submit-correct-title">
<p class="section-kicker">Submit / correct</p>
<h2 id="submit-correct-title">Use one intake standard for new listings and corrections</h2>
<p>The best version of this guide needs a predictable intake form. These fields match the downloadable CSV and JSON so a steward can review changes without retyping everything.</p>
<table><thead><tr><th>Field</th><th>Purpose</th><th>Required?</th></tr></thead><tbody>
<tr><td>Resource name</td><td>Public name of the organization, business, venue, channel, or program.</td><td>Yes</td></tr>
<tr><td>Category and resource type</td><td>Funding, media, bulletin, business support, lodging, arts, food, training, tourism, service, or other.</td><td>Yes</td></tr>
<tr><td>Town, county, state</td><td>Supports county and route filtering.</td><td>Yes</td></tr>
<tr><td>Website / source URL</td><td>Primary public source if available.</td><td>If available</td></tr>
<tr><td>Public phone and public email</td><td>Only publish contacts intended for public use.</td><td>If available</td></tr>
<tr><td>Physical address</td><td>Useful for flyer routes and in-person access.</td><td>If public</td></tr>
<tr><td>Verification method</td><td>Official website, phone, email, field check, public social page, partner referral, or secondary source.</td><td>Yes</td></tr>
<tr><td>Confidence level</td><td>High, Medium, Low, or Unknown.</td><td>Yes</td></tr>
<tr><td>Posting / calendar / contact rules</td><td>Captures permission boundaries and practical use notes.</td><td>Recommended</td></tr>
<tr><td>Submitter name and contact</td><td>For stewardship follow-up; not automatically published.</td><td>Yes for corrections</td></tr>
</tbody></table>
<div class="method-grid">
<article><strong>Accept.</strong> Official source, public contact, clear category, clear location, no privacy concern.</article>
<article><strong>Hold for follow-up.</strong> Social-only, stale source, unclear ownership, missing town, seasonal status, or conflicting information.</article>
<article><strong>Reject or redact.</strong> Private contact, unverifiable claim, discriminatory language, personal data, or implied endorsement that cannot be supported.</article>
</div>
</section>"""


def make_methodology_section() -> str:
    return f"""<section class="guide-section operational-section" id="about-methodology" aria-labelledby="about-methodology-title">
<p class="section-kicker">Method and governance</p>
<h2 id="about-methodology-title">What agrees with the utilitarian direction, what gets constrained, and what still needs research</h2>
<p>The implementation brief agrees with the guide's most useful premise when it reduces confusion, adds reusable workflows, preserves source uncertainty, and gives beginners concrete next steps. It disagrees when it drifts toward a marketing landing page, vague inspiration, overdesigned persuasion, invented contact authority, or polished certainty where the underlying county data is incomplete.</p>
<div class="method-grid">
<article><strong>Keep.</strong> Task-first navigation, local resource tables, persona filtering, county routes, templates, metrics, downloadable data, and direct links back to sources.</article>
<article><strong>Revise.</strong> Any brochure-style framing, generic hero copy, unsupported claims, implied endorsements, decorative-only visuals, and long text blocks without action steps.</article>
<article><strong>Guardrails.</strong> Never invent deadlines, grant eligibility, posting permission, private contacts, active status, pricing, ownership, accessibility, or official endorsement.</article>
<article><strong>Uncertainty labels.</strong> High means official/current source or successful link check. Medium means plausible public source but details need review. Low/Unknown means verify before use.</article>
</div>
{inline_svg("se_accessibility_contrast.svg", "Accessibility and contrast.", "Use readable type, high contrast, direct language, alt text, and non-color status labels so the guide works for more people.")}
<h3>Research required in optimal conditions</h3>
<p>Yes. The site can launch with conservative labels, but the strongest version requires recurring research into current grant deadlines and eligibility, business-support program status, media submission rules, public-building posting permissions, tourism and chamber intake processes, active/closed businesses, seasonal hours, accessibility details, costs, rural bulletin locations, and who owns guide stewardship.</p>
<h3>QA and human follow-up list</h3>
<ul>
<li>Call or email Low and Unknown confidence records before featuring them in a campaign plan.</li>
<li>Confirm public posting rules for libraries, schools, public buildings, visitor centers, lodging desks, and storefronts.</li>
<li>Verify current media contacts, publication deadlines, PSA policies, ad rates, and calendar submission rules.</li>
<li>Review every funding or business-support listing for eligibility, geography, tax-status requirements, and deadlines.</li>
<li>Run county field sweeps for Walsenburg private storefronts, Cuchara seasonal merchants, Trinidad/Aguilar updates, and sparse rural nodes.</li>
<li>Re-run link validation and update the CSV/JSON/HTML package before each public release.</li>
</ul>
<div class="trust-box"><strong>Ownership note:</strong> designate a guide steward before public intake opens. Until then, the submit/correct form is a specification, not a promise that every submitted listing will be published.</div>
</section>"""


def make_las_animas_inventory_section() -> str:
    return """<section class="guide-section" id="lasanimas-outreach-inventory">
<h2>Las Animas County Outreach &amp; Visibility Inventory</h2>
<p>This section integrates the Las Animas County Outreach and Visibility Inventory supplied for the guide. It translates the county's uneven public footprint into practical outreach targets: high-confidence Trinidad and Aguilar records, institution-centered rural nodes, corridor routes, and verification-priority communities.</p>
<div class="guide-card"><strong>Source hierarchy:</strong> official municipal, tourism, school, hospital, newspaper, and institutional pages first; public social or booking pages second; secondary geographic references only where official pages were unavailable. Treat medium and low-confidence rows as route-planning leads until field verified.</div>
<h3>Outreach Route &amp; Priority Map</h3>
<table><thead><tr><th>Town / corridor</th><th>Priority targets</th><th>Why they matter most</th><th>Verification priority</th></tr></thead><tbody>
<tr><td>Trinidad hub</td><td>Visit Trinidad Tourism Office; Space to Create; CREATE Trinidad; A.R. Mitchell Museum; Trinidad History Museum; Main Street LIVE; The Well Hotel &amp; Taproom; Hilton Garden Inn / Gagliardi's 489; Brick Road Bakery; Trinidad Chronicle-News.</td><td>Downtown foot traffic, visitor reach, lodging partnerships, event-hosting capacity, media distribution, and business-support intake.</td><td>High-confidence hub; retail inventory still needs a focused downtown block check.</td></tr>
<tr><td>Trinidad supplemental flyer circuit</td><td>Mutiny Trinidad; Carnegie Public Library; Coach John Gagliardi Sports Complex; Furiosa Sports &amp; Games; Owl Den Vintage; Frontier Geeks.</td><td>Physical-promotion leads from the worksheet; useful for posters, niche audiences, sports/event crowds, and cultural cross-promotion.</td><td>Verify public posting rules and current operating status before publication.</td></tr>
<tr><td>I-25 north: Cokedale and Aguilar</td><td>Aguilar Main Street cluster; Cokedale Mining Museum / Town Hall / Post Office complex.</td><td>Compact small-town saturation, heritage outreach, and physical notice routing north of Trinidad.</td><td>Aguilar is high confidence; Cokedale requires phone or field verification.</td></tr>
<tr><td>SH 389: Branson and Trinchera area</td><td>Town of Branson; Branson School; Louden Community Library; Branson Community Church; Branson Post Office; Branson Hi-Lo Gravel Grinder / Bike Club; Branson-Trinchera Reunion.</td><td>Public life is organized through school, library, church, post office, town channels, and recurring events rather than storefront density.</td><td>Use Branson nodes while verifying separate Trinchera contacts.</td></tr>
<tr><td>County roads / northeast: Hoehne</td><td>Hoehne School District RE-3; Hoehne Post Office.</td><td>The school is the dominant family, youth, athletics, FFA, art-show, and public-program audience; the post office remains a conservative notice node.</td><td>High confidence for school; post office contact/hours need local confirmation.</td></tr>
<tr><td>Highway 12 west: Trinidad Lake, Weston, Stonewall</td><td>Trinidad Lake State Park; Monument Lake Resort; Weston Supply &amp; U.S. Post Office; heritage sites on the corridor.</td><td>Best route for scenic-byway, outdoor-recreation, lodging, weekend, and visitor materials.</td><td>Confirm Weston/Stonewall stores, cafes, churches, galleries, and posting points.</td></tr>
<tr><td>US 350: Model and Kim</td><td>Kim school system if active; Kim town/post office core; Model Post Office.</td><td>Sparse online commerce makes school, postal, and town-core anchors the likely physical outreach path.</td><td>Field-check school contact, any store or cafe, post office hours, and bulletin boards.</td></tr>
<tr><td>South / rural corridor nodes</td><td>Starkville, Boncarbo, Segundo, Trinchera, Tyrone/Villegreen.</td><td>These places may still support physical outreach even when they do not register well online.</td><td>Verification-priority towns before final guide lock.</td></tr>
</tbody></table>
<h3>Trinidad Food, Lodging, Visitor &amp; Media Records</h3>
<table><thead><tr><th>Business / organization</th><th>Available contact</th><th>Category</th><th>Outreach use</th><th>Confidence / source</th></tr></thead><tbody>
<tr><td>AlMack's Kitchen</td><td>443 N. Commercial St., Trinidad, CO 81082; almackskitchen.com; 719-679-4577</td><td>Restaurant</td><td>Downtown dining stop; useful for posters, rack cards, and event mentions.</td><td>High - official tourism directory.</td></tr>
<tr><td>Bob &amp; Earl's</td><td>1118 Robinson Ave., Trinidad, CO 81082; Facebook; 719-846-0144</td><td>Restaurant</td><td>Classic local restaurant with everyday local traffic.</td><td>High - official tourism directory.</td></tr>
<tr><td>Boom Noodles</td><td>326 N. Commercial St., Trinidad, CO 81082; boom-noodles.com; 719-210-4553</td><td>Restaurant</td><td>Marketplace food-court tenant; strong multi-business cross-promotion point.</td><td>High - official tourism directory.</td></tr>
<tr><td>Brick Road Bakery</td><td>132 N. Commercial St. Ste. A, Trinidad, CO 81082; 719-680-3701</td><td>Bakery / cafe</td><td>Downtown bakery near other walkable businesses; strong flyer value.</td><td>High - official tourism directory.</td></tr>
<tr><td>El Rancho Mexican Restaurant</td><td>1901 Santa Fe Trail, Trinidad, CO 81082; Snapchat listed; 719-846-9049</td><td>Restaurant</td><td>Highway and local-dining visibility.</td><td>High - official tourism directory.</td></tr>
<tr><td>Family Seed II</td><td>525 San Juan St., Trinidad, CO 81082; 719-845-8057</td><td>Restaurant</td><td>Neighborhood dining and local repeat traffic.</td><td>High - official tourism directory.</td></tr>
<tr><td>Flatt's Burgers &amp; Shakes</td><td>326 N. Commercial St., Trinidad, CO 81082; flattsburger.com; 719-680-3122</td><td>Restaurant</td><td>Marketplace stall; useful for event flyer placement in a shared venue.</td><td>High - official tourism directory.</td></tr>
<tr><td>Gagliardi's 489</td><td>201 Americana Rd., Trinidad, CO 81082; gagliardis489.com; 719-671-0449</td><td>Restaurant</td><td>Visitor- and lodging-linked restaurant inside Hilton property.</td><td>High - official tourism directory.</td></tr>
<tr><td>Gluten Free in the 303</td><td>326 N. Commercial St., Trinidad, CO 81082; glutenfreeinthe303.com; 575-643-6082</td><td>Specialty food</td><td>Niche food offering inside the Marketplace cluster.</td><td>High - official tourism directory.</td></tr>
<tr><td>Great Wall Restaurant</td><td>321 State St., Trinidad, CO 81082; 719-846-1688</td><td>Restaurant</td><td>Established local restaurant with local order volume.</td><td>High - official tourism directory.</td></tr>
<tr><td>Grill 14</td><td>326 N. Commercial St., Trinidad, CO 81082; grill14.com; 719-845-4803</td><td>Restaurant</td><td>Marketplace food-court tenant; shared visitor traffic.</td><td>High - official tourism directory.</td></tr>
<tr><td>Hollywood Bar &amp; Cafe</td><td>1133 N. Linden Ave., Trinidad, CO 81082; hollywoodbarandcafe.com; 719-680-3285</td><td>Bar / cafe</td><td>Evening and local gathering spot; event mention potential.</td><td>High - official tourism directory.</td></tr>
<tr><td>I Love Sugar Sweets &amp; Eats</td><td>259 N. Commercial St., Trinidad, CO 81082; 719-846-2000</td><td>Sweets / cafe</td><td>Central Commercial Street foot traffic.</td><td>High - official tourism directory.</td></tr>
<tr><td>Kangaroo Coffee</td><td>326 N. Commercial St., Trinidad, CO 81082; kangaroocoffeellc.com; 719-388-0150 ext. 1011</td><td>Coffee</td><td>Coffee anchor in the Marketplace cluster.</td><td>High - official tourism directory.</td></tr>
<tr><td>Las Animas Grill</td><td>341 N. Commercial St., Trinidad, CO 81082; Facebook; 719-846-7621</td><td>Restaurant</td><td>Downtown food-district exposure.</td><td>High - official tourism directory.</td></tr>
<tr><td>Lee's BBQ</td><td>825 San Pedro Ave., Trinidad, CO 81082; 719-846-8462</td><td>Restaurant</td><td>Neighborhood food stop and local circulation.</td><td>High - official tourism directory.</td></tr>
<tr><td>Little Rox's Ice Cream Shop</td><td>208 Prospect St., Trinidad, CO 81082; Facebook</td><td>Dessert / retail food</td><td>Visitor-friendly seasonal-style stop and easy event handout point.</td><td>High - official tourism directory.</td></tr>
<tr><td>Mission at the Bell</td><td>134 W. Main St., Trinidad, CO 81082; missionatthebell.com; 719-845-1513</td><td>Restaurant / venue</td><td>Main Street dining and event-friendly venue.</td><td>High - official tourism directory.</td></tr>
<tr><td>Budget Host &amp; Summit RV Park</td><td>9800 Santa Fe Trail, Trinidad, CO 81082; Booking listing; 719-846-2251</td><td>Motel / RV park</td><td>Highway traveler capture point and lodging-partner potential.</td><td>High - official tourism directory.</td></tr>
<tr><td>Cawthon RV Park &amp; Motel</td><td>1701 Santa Fe Trail, Trinidad, CO 81082; cawthonpark.com; 719-846-3303</td><td>Motel / RV park</td><td>Overnight wayfinding and flyer placement for pass-through traffic.</td><td>High - official tourism directory.</td></tr>
<tr><td>Days Inn &amp; Suites by Wyndham</td><td>900 W. Adams St., Trinidad, CO 81082; Wyndham; 719-497-8080</td><td>Hotel</td><td>Reliable lodging partner for traveler-facing promotions.</td><td>High - official tourism directory.</td></tr>
<tr><td>Hilton Garden Inn</td><td>201 Americana Rd., Trinidad, CO 81082; Hilton; 719-845-8000</td><td>Hotel</td><td>Conference and visitor anchor; strong event-lodging partner.</td><td>High - official tourism directory.</td></tr>
<tr><td>Holiday Inn Express and Suites</td><td>3130 Santa Fe Trail Dr., Trinidad, CO 81082; IHG; 719-845-8400</td><td>Hotel</td><td>Interstate traveler reach and front-desk flyer handoff potential.</td><td>High - official tourism directory.</td></tr>
<tr><td>La Quinta Inn &amp; Suites</td><td>2833 Toupal Dr., Trinidad, CO 81082; Wyndham; 719-845-0102</td><td>Hotel</td><td>Visitor and pet-traveler audience.</td><td>High - official tourism directory.</td></tr>
<tr><td>Monument Lake Resort</td><td>4789 Colorado Hwy 12, Trinidad, CO 81082; themonumentlakeresort.com; 719-695-7048</td><td>Resort / lodging</td><td>Important scenic-byway lodging partner for Weston/Stonewall corridor outreach.</td><td>High - official tourism directory.</td></tr>
<tr><td>Quality Inn</td><td>3125 Toupal Dr., Trinidad, CO 81082; Choice Hotels; 719-497-8000</td><td>Hotel</td><td>Interstate traveler catchment; easy brochure or flyer drop.</td><td>High - official tourism directory.</td></tr>
<tr><td>Summit RV Park</td><td>9800 Santa Fe Trail Dr., Trinidad, CO 81082; Google listing; 719-846-2251</td><td>RV park</td><td>RV traveler node overlapping Budget Host listing.</td><td>High - official tourism directory.</td></tr>
<tr><td>Tarabino Inn</td><td>310 E. 2nd St., Trinidad, CO 81082; Facebook; 719-680-1241</td><td>Inn / B&amp;B</td><td>Historic-core lodging and guest concierge distribution point.</td><td>High - official tourism directory.</td></tr>
<tr><td>The Well Hotel &amp; Taproom</td><td>155 E. Main St., Trinidad, CO 81082; wellhoteltrinidad.com; 719-422-8030</td><td>Boutique hotel / taproom</td><td>Downtown visitor-facing cross-promotion site.</td><td>High - official tourism directory.</td></tr>
<tr><td>Tower 64 Motel &amp; RV Park</td><td>10301 Santa Fe Trail Dr., Trinidad, CO 81082; tower64motelandrv.com; 719-846-3307</td><td>Motel / RV park</td><td>Edge-of-town overnight node.</td><td>High - official tourism directory.</td></tr>
<tr><td>Trails End Motel</td><td>616 E. Main St., Trinidad, CO 81082; jimandmelissa.org; 719-846-4425</td><td>Motel</td><td>East Main corridor lodging visibility.</td><td>High - official tourism directory.</td></tr>
<tr><td>Travelodge by Wyndham</td><td>702 W. Main St., Trinidad, CO 81082; Wyndham; 719-846-2271</td><td>Hotel</td><td>Main Street traveler exposure.</td><td>High - official tourism directory.</td></tr>
<tr><td>Trinidad Lake State Park</td><td>32610 Colorado Hwy 12, Trinidad, CO 81082; CPW; 719-846-6951</td><td>Camping / recreation</td><td>Major outdoor-visitation node and seasonal outreach partner.</td><td>High - official tourism directory / state park listing.</td></tr>
<tr><td>Trinidad Super 8</td><td>1924 Freedom Rd., Trinidad, CO 81082; Wyndham; 719-846-8280</td><td>Hotel</td><td>Budget overnight traveler reach.</td><td>High - official tourism directory.</td></tr>
<tr><td>Visit Trinidad Tourism / Events Office</td><td>210 W. Main St., Trinidad, CO 81082; https://visittrinidadcolorado.com/resources-for-locals/; 719-846-9843 x160</td><td>Tourism / government</td><td>Central visitor-information node; event calendar, social media co-op, and business-support gateway.</td><td>High - official tourism resources page.</td></tr>
<tr><td>Space to Create</td><td>204 W. Main St., Trinidad, CO 81082; https://visittrinidadcolorado.com/attraction/space-to-create/; 719-422-8074</td><td>Arts / venue / event space</td><td>Event, exhibit, and cross-promotion venue.</td><td>High - official attraction page.</td></tr>
<tr><td>CREATE Trinidad</td><td>210 W. Main St., Trinidad, CO 81082; https://visittrinidadcolorado.com/attraction/create-trinidad/; 719-846-9843</td><td>Creative district / cultural hub</td><td>Arts calendars, open mics, exhibits, and partner promotion.</td><td>High - official attraction page.</td></tr>
<tr><td>A.R. Mitchell Museum of Western Art</td><td>150 E. Main St., Trinidad, CO 81082; https://visittrinidadcolorado.com/attraction/a-r-mitchell-museum-of-western-art/; 719-846-4224</td><td>Museum / arts</td><td>Visitor-relevant rack-card and event-posting partner.</td><td>High - official attraction page.</td></tr>
<tr><td>Trinidad History Museum</td><td>312 E. Main St., Trinidad, CO 81082; https://visittrinidadcolorado.com/attraction/trinidad-history-museum/; 719-846-7217</td><td>Museum / heritage</td><td>Cultural-tourism node and event-listing partner.</td><td>High - official attraction page.</td></tr>
<tr><td>Main Street LIVE</td><td>131 W. Main St., Trinidad, CO 81082; https://visittrinidadcolorado.com/attraction/main-street-live/; 719-846-4765</td><td>Performance venue</td><td>Event cross-promotion and audience capture.</td><td>High - official attraction page.</td></tr>
<tr><td>Trinidad State College</td><td>Trinidad, CO; trinidadstate.edu</td><td>Higher education</td><td>Student, workforce, public-program, bulletin, and event-distribution audience.</td><td>High - college profile with official site listed.</td></tr>
<tr><td>Mt. San Rafael Hospital</td><td>Trinidad, CO; msrhc.org</td><td>Healthcare</td><td>Major county institution; health-fair and service-outreach partner.</td><td>High - hospital profile with official site listed.</td></tr>
<tr><td>Trinidad Chronicle-News</td><td>313 W. Main St., Trinidad, CO; thechronicle-news.com</td><td>Media</td><td>Calendars, earned media, paid notices, and community announcements.</td><td>High - newspaper profile with official site listed.</td></tr>
<tr><td>Fishers Peak State Park</td><td>Near Trinidad; official state park presence noted</td><td>Outdoor recreation / tourism</td><td>High-interest visitor draw for tourism-aligned campaigns.</td><td>Medium - state park reference source accessible in the PDF pass.</td></tr>
</tbody></table>
<h3>Aguilar, Branson, Hoehne &amp; Corridor Records</h3>
<table><thead><tr><th>Business / organization</th><th>Available contact</th><th>Category</th><th>Outreach use</th><th>Confidence / source</th></tr></thead><tbody>
<tr><td>Aguilar Bar &amp; Grill</td><td>211 Main Street, Aguilar, CO 81020; Facebook</td><td>Restaurant / bar</td><td>Main Street gathering point; good flyer and event-mention location.</td><td>High - official town business page.</td></tr>
<tr><td>Aguilar Bakery &amp; Cafe</td><td>111 Main Street, Aguilar, CO 81020; Facebook</td><td>Bakery / cafe</td><td>Breakfast and walk-in traffic; strong community visibility.</td><td>High - official town business page.</td></tr>
<tr><td>Aguilar Country Cottages</td><td>100 Coyote Trail, Aguilar, CO 81020; aguilarcountrycottages.com</td><td>Lodging</td><td>Lodging partner for visitor and event campaigns.</td><td>High - official town business page.</td></tr>
<tr><td>Ol'e Smokes</td><td>100 Linares Drive, Aguilar, CO 81020; Facebook</td><td>Retail</td><td>Edge-of-town retail stop and local visibility.</td><td>High - official town business page.</td></tr>
<tr><td>Ace-Hi Tavern</td><td>151 E. Main Street, Aguilar, CO 81020</td><td>Bar</td><td>Main Street social venue with event-flyer value.</td><td>High - official town business page; public website not visible in source.</td></tr>
<tr><td>The Station</td><td>173 W. Main Street, Aguilar, CO 81020; aguilarstation.com</td><td>Restaurant / bar / venue</td><td>Music, event, and traveler cross-promotion.</td><td>High - official town business page.</td></tr>
<tr><td>Town of Branson</td><td>Branson, CO; bransoncolorado.com; townofbranson@gmail.com</td><td>Government / community hub</td><td>Central communications channel for townwide notices and events.</td><td>High - official town site.</td></tr>
<tr><td>Branson School / Branson School Online</td><td>Branson, CO; bransonschoolonline.com; bransonbearcats.org</td><td>Education</td><td>Regional gathering point and youth/family outreach anchor.</td><td>High - official town site linking school pages.</td></tr>
<tr><td>Branson Community Church</td><td>Branson, CO; Facebook page listed on official town site</td><td>Faith / community</td><td>Weekly local audience and community-announcement channel.</td><td>High - official town site.</td></tr>
<tr><td>Louden Community Library</td><td>Branson, CO; 719-946-5656</td><td>Library / community venue</td><td>Meeting, community-history, and special-event venue; seasonal by arrangement off-season.</td><td>High - official town site.</td></tr>
<tr><td>U.S. Post Office - Branson</td><td>Branson, CO</td><td>Government / service</td><td>Identified by town as the area's official notice board.</td><td>High - official town site.</td></tr>
<tr><td>Branson Bike Club / Branson Hi-Lo Gravel Grinder</td><td>Branson area; Facebook page listed on official town site</td><td>Recreation / event</td><td>Event-based outreach and seasonal visitor audience.</td><td>High - official town site.</td></tr>
<tr><td>Branson-Trinchera Reunion</td><td>Branson / Trinchera area; Facebook page listed on official town site</td><td>Community event</td><td>Heritage and community calendar insertion point.</td><td>High - official town site.</td></tr>
<tr><td>Hoehne School District RE-3</td><td>19851 County Road 75.1, Trinidad, CO 81082; hoehnesd.org; 719-846-4457; christine.maldonado@hoehnesd.org</td><td>Education / community hub</td><td>Strongest documented node in Hoehne: families, events, athletics, FFA, and art-show audience.</td><td>High - official district site.</td></tr>
<tr><td>Hoehne Post Office</td><td>Hoehne, CO 81046</td><td>Government / service</td><td>Conservative posting or notice-check node in a sparse rural community.</td><td>Medium - USPS/geographic references via town profile.</td></tr>
<tr><td>Weston Supply &amp; U.S. Post Office</td><td>Weston, CO 81091</td><td>Retail / service / postal</td><td>Rural service node for community-level physical outreach.</td><td>Medium - public place profile/image caption; verify before publication.</td></tr>
<tr><td>Our Lady of Guadalupe Church and Medina Cemetery</td><td>Near Weston</td><td>Heritage / cultural site</td><td>Cultural and heritage-route relevance rather than routine commercial traffic.</td><td>Medium - public place profile; verify access and use.</td></tr>
<tr><td>Cokedale Mining Museum / Town Hall / Post Office complex</td><td>Cokedale, CO; town website existed but was inaccessible in the PDF pass</td><td>Museum / government / service</td><td>Historic and heritage-outreach node; likely town's best physical posting or check-in point.</td><td>Medium - secondary public reference; verify locally.</td></tr>
</tbody></table>
<h3>Verification-Priority Sparse Nodes</h3>
<table><thead><tr><th>Community / node</th><th>Provisional anchor found</th><th>Sector</th><th>Outreach use</th><th>Recommended verification step</th></tr></thead><tbody>
<tr><td>Kim</td><td>Kim school system / Kim Undivided High School</td><td>Education</td><td>Likely main community anchor if active.</td><td>Verify current school contact, any current store or cafe, and town notice locations.</td></tr>
<tr><td>Kim</td><td>Kim Post Office / town core</td><td>Government / service</td><td>Possible notice or check-in point where commerce is sparse.</td><td>Confirm post office hours, bulletin board access, and local community contacts.</td></tr>
<tr><td>Model</td><td>Model Post Office</td><td>Government / service</td><td>Likely one of the only consistent physical-public nodes on US 350.</td><td>Field-check post office, mercantile, fuel, or community board possibilities.</td></tr>
<tr><td>Starkville</td><td>No high-confidence public-facing business found in this pass</td><td>Verification zone</td><td>Town identified, but no current business directory located.</td><td>Use local resident, county, church, fire hall, or mail-stop contacts.</td></tr>
<tr><td>Trinchera</td><td>No distinct current storefront verified in this pass</td><td>Verification zone</td><td>Branson-Trinchera ties show community activity; separate business listing not captured.</td><td>Pair Branson outreach with one route-based verification pass.</td></tr>
<tr><td>Boncarbo</td><td>No high-confidence public-facing business found in this pass</td><td>Verification zone</td><td>Routing node only from the PDF pass.</td><td>Inspect bulletin boards, churches, mail stops, fire halls, or community buildings.</td></tr>
<tr><td>Segundo</td><td>No high-confidence public-facing business found in this pass</td><td>Verification zone</td><td>Routing node only from the PDF pass.</td><td>Use county or local resident contacts before final publication.</td></tr>
<tr><td>Tyrone / Villegreen</td><td>No high-confidence public-facing business found in this pass</td><td>Verification zone</td><td>Routing node only from the PDF pass.</td><td>Confirm ranch-related public interfaces, event sites, and notice locations.</td></tr>
</tbody></table>
<p><strong>Maintenance note:</strong> Trinidad and Aguilar can be maintained through formal tourism or town intake channels. Branson, Hoehne, Cokedale, Kim, Model, Starkville, Boncarbo, Segundo, Trinchera, and Tyrone/Villegreen require phone, partner, or field verification because online inventory coverage is uneven.</p>
</section>"""


def make_huerfano_inventory_section() -> str:
    return """<section class="guide-section" id="huerfano-outreach-inventory">
<h2>Huerfano County Business Inventory &amp; Outreach Targets</h2>
<p>This section integrates the Huerfano County Business Inventory and Outreach Targets Report. It treats Huerfano as a two-hub county with one seasonal mountain submarket: Walsenburg first for countywide civic, healthcare, library, radio, and visitor-center amplification; La Veta second for merchant density and arts/culture; Cuchara and Gardner third for outdoor recreation, seasonal tourism, and valley institutions; then rural follow-up by phone and field verification.</p>
<div class="guide-card"><strong>Source logic:</strong> Huerfano County government, Town of La Veta, Spanish Peaks Country, county-linked schools/libraries/healthcare/special districts, and media records are the strongest sources. La Veta is close to directory-grade completeness. Walsenburg private-sector rows, Cuchara seasonal merchants, and rural nodes still need a storefront, phone, and bulletin-board verification pass.</div>
<h3>County Market Context &amp; Outreach Geography</h3>
<table><thead><tr><th>Town / corridor</th><th>Priority targets</th><th>Why they matter most</th><th>Verification priority</th></tr></thead><tbody>
<tr><td>Walsenburg county hub</td><td>Huerfano County Government; City of Walsenburg; courthouse area; Walsenburg Mining Museum; Fox Theatre; Spanish Peaks Library District; Spanish Peaks Regional Health Center; KSPK-FM; Heritage Park visitor information area.</td><td>Countywide civic reach, healthcare/public-service audience, radio amplification, visitor stopping point, and public-building flyer permissions.</td><td>High-confidence public anchors; private storefront and highway-business inventory remains incomplete.</td></tr>
<tr><td>La Veta town and arts hub</td><td>Town Hall; Main Street business directory; SPACe Gallery; Francisco Fort Museum; La Veta Inn; La Veta Public Library; RE-2 La Veta School District; lodging, retail, food, wellness, and arts rows.</td><td>Strongest official small-business directory in the Huerfano pass, with arts/culture and visitor-facing density.</td><td>High confidence for listed town-directory rows; confirm hours, websites, and posting permissions.</td></tr>
<tr><td>Cuchara / Gardner valley</td><td>Cuchara Mountain Park; Cuchara Water and Sanitation District; Upper Huerfano Fire District; Gardner Public Improvement District; Navajo Western Water District; Mission:Wolf; La Veta Fire Protection District.</td><td>Seasonal mountain/outdoor market, corridor governance, emergency-service touchpoints, and attraction-based outreach.</td><td>Medium to high public-anchor confidence; seasonal restaurants, lodges, bars, shops, guides, and boards need a summer verification pass.</td></tr>
<tr><td>Rural unincorporated nodes</td><td>Farisita, Chama, Pictou, Pryor, Red Wing, Badito, Calumet, Delcarbon, Malachite, Tioga.</td><td>Important for rural residents, ranch, guide, faith, contractor, and home-based business outreach even when no town-style directory exists.</td><td>Field-check, phone, county, church, fire, mail-stop, ranch, and resident referrals required before final publication.</td></tr>
</tbody></table>
<h3>Walsenburg Core Inventory &amp; Countywide Anchors</h3>
<table><thead><tr><th>Business / organization</th><th>Available contact</th><th>Category</th><th>Outreach use</th><th>Confidence / source</th></tr></thead><tbody>
<tr><td>Huerfano County Government</td><td>401 Main Street, Walsenburg, CO 81089; (719) 738-3000; https://www.huerfano.us/</td><td>Government</td><td>Countywide civic channel; maps, parks, community resources, business/economic-development links, and public-notice adjacency.</td><td>High - official county portal.</td></tr>
<tr><td>City of Walsenburg</td><td>Walsenburg, CO; cityofwalsenburg.colorado.gov</td><td>Government</td><td>Municipal channel for city notices, local services, and Walsenburg-specific public coordination.</td><td>Medium - official municipal link published by county; details need direct verification.</td></tr>
<tr><td>Huerfano County Courthouse</td><td>400 Main St., Walsenburg, CO</td><td>Government / landmark</td><td>Public-government landmark and downtown orientation point.</td><td>High - courthouse listing.</td></tr>
<tr><td>Walsenburg Mining Museum / Huerfano County Historical Society</td><td>112 W. Fifth Street, Walsenburg, CO</td><td>Arts / culture</td><td>Heritage visitor audience; useful for posters, local history programs, and cultural-route promotion.</td><td>High - historical listing.</td></tr>
<tr><td>Huerfano Heritage Center</td><td>Walsenburg, CO</td><td>Arts / culture</td><td>Potential cultural/history outreach node.</td><td>Low - named on county history imagery; direct operating page not retrieved.</td></tr>
<tr><td>Fox Theatre Walsenburg</td><td>Walsenburg, CO; foxtheatrewalsenburg.org</td><td>Arts / culture / venue</td><td>Countywide event audience; possible calendar and cross-promotion partner.</td><td>High - county community-resource listing.</td></tr>
<tr><td>Spanish Peaks Regional Health Center</td><td>Walsenburg area; sprhc.org</td><td>Healthcare</td><td>Health-fair, service outreach, employer, and public-information partner.</td><td>High - county-linked regional hospital.</td></tr>
<tr><td>Spanish Peaks Veterans Community Living Center</td><td>Walsenburg area; sprhc.org</td><td>Healthcare</td><td>Senior and veteran-serving outreach consideration.</td><td>Medium - same health-campus footprint in retrieved reference.</td></tr>
<tr><td>Las Animas-Huerfano Counties District Health Department</td><td>Walsenburg area; la-h-health.colorado.gov</td><td>Government / healthcare</td><td>Public-health notices, clinics, emergency preparedness, and service-access campaigns.</td><td>High - county-linked public-health partner.</td></tr>
<tr><td>Spanish Peaks Library District, Walsenburg Branch</td><td>415 Walsen Ave., Walsenburg, CO; spld.org</td><td>Library / education / community</td><td>Community posting, cultural programming, public computer access, and civic information.</td><td>High - district branch listing.</td></tr>
<tr><td>Peakview School</td><td>Walsenburg, CO; huerfano.k12.co.us</td><td>Education</td><td>Family, youth, and school-community outreach.</td><td>Medium - retrieved town reference.</td></tr>
<tr><td>Walsenburg Jr./Sr. High School</td><td>Walsenburg, CO; huerfano.k12.co.us</td><td>Education</td><td>Teen, family, sports, workforce, and school-event outreach.</td><td>Medium - retrieved town reference.</td></tr>
<tr><td>CSU Pueblo at Spanish Peaks</td><td>Walsenburg, CO</td><td>Education / workforce</td><td>Adult education, nursing/workforce, and training campaign audience.</td><td>Medium - satellite campus reference.</td></tr>
<tr><td>KSPK-FM 102.3</td><td>Walsenburg and broader Southern Colorado footprint; kspk.com</td><td>Media / radio</td><td>Local radio mentions, interviews, reminders, and paid spot planning.</td><td>High - radio record.</td></tr>
<tr><td>KFEZ 101.3 / Gnarly 101.3</td><td>Walsenburg-Pueblo region</td><td>Media / radio</td><td>Potential radio option only after current status is verified.</td><td>Medium - retrieved source says station has been off air since 2020.</td></tr>
<tr><td>Lathrop State Park</td><td>Walsenburg area</td><td>Tourism / outdoor recreation</td><td>Major visitor anchor; reported about 121,000 visitors in 2023 and useful for tourism awareness planning.</td><td>High - state park/tourism reference.</td></tr>
<tr><td>Walsenburg Golf Course</td><td>Walsenburg area</td><td>Tourism / recreation</td><td>Public-course and recreation touchpoint associated with Lathrop/city recreation narrative.</td><td>Medium - verify current operations and posting options.</td></tr>
<tr><td>Spanish Peaks Regional Airport</td><td>Walsenburg area; county airport page linked from county site</td><td>Government / transportation</td><td>County logistics and service node; useful for business, emergency, and visitor-infrastructure context.</td><td>High - county key service.</td></tr>
</tbody></table>
<h3>La Veta Official Business Directory Records</h3>
<table><thead><tr><th>Business / organization</th><th>Available contact</th><th>Category</th><th>Outreach use</th><th>Confidence / source</th></tr></thead><tbody>
<tr><td>Alys' Restaurant</td><td>604 S. Oak Street, La Veta, CO; (719) 742-3742</td><td>Restaurant / food</td><td>Local dining and flyer route stop.</td><td>High - Town of La Veta official business directory.</td></tr>
<tr><td>Artisans on Main LLC</td><td>210 South Main Street, La Veta, CO; (719) 742-3666</td><td>Retail / arts</td><td>Main Street retail and maker-facing outreach.</td><td>High - Town of La Veta official business directory.</td></tr>
<tr><td>A Taylor Made Haircut</td><td>313 W. Ryus Ave, La Veta, CO; (719) 742-3289</td><td>Service / personal care</td><td>Personal-service customer traffic and local notices.</td><td>High - Town directory.</td></tr>
<tr><td>Bachman &amp; Associates Real Estate</td><td>222 South Main Street, La Veta, CO; (719) 742-5551</td><td>Professional services / real estate</td><td>Homebuyer, property, and relocation audience.</td><td>High - Town directory.</td></tr>
<tr><td>Big R La Veta</td><td>1010 Cherry Street, La Veta, CO; (719) 742-3071</td><td>Retail / farm-ranch</td><td>Farm, ranch, contractor, resident, and rural-service traffic.</td><td>High - Town directory.</td></tr>
<tr><td>Book Nook</td><td>207 South Main Street, La Veta, CO; (719) 742-3572</td><td>Retail</td><td>Main Street foot traffic and community browsing audience.</td><td>High - Town directory.</td></tr>
<tr><td>Capture Colorado</td><td>200 South Main St., La Veta, CO; (719) 742-6000</td><td>Arts / culture</td><td>Creative/visual audience; verify service mix for campaign targeting.</td><td>Medium - category inferred from name in town directory.</td></tr>
<tr><td>Casa de Pajaros</td><td>213 South Main St., La Veta, CO; (719) 742-3417</td><td>Retail</td><td>Main Street retail stop; verify merchandise focus.</td><td>Medium - category inferred from name in town directory.</td></tr>
<tr><td>Charlie's Market</td><td>212 South Main Street, La Veta, CO; (719) 742-3651</td><td>Retail / grocery</td><td>High-frequency local market traffic and rural household reach.</td><td>High - Town directory.</td></tr>
<tr><td>Code of the West Real Estate</td><td>215 South Main St., La Veta, CO; (719) 742-3626</td><td>Professional services / real estate</td><td>Property, relocation, and visitor-to-resident audience.</td><td>High - Town directory.</td></tr>
<tr><td>Corner Cottage Skin Care</td><td>139 West Grand, La Veta, CO; (303) 903-2175</td><td>Service / wellness</td><td>Wellness/personal-care audience; verify license type if healthcare classification matters.</td><td>Medium - Town directory.</td></tr>
<tr><td>Crafted in Colorado</td><td>205 S. Main Street, La Veta, CO; (719) 742-3361</td><td>Retail / maker</td><td>Local product, gift, and visitor shopping audience.</td><td>High - Town directory.</td></tr>
<tr><td>Cuchara Valley Mini Storage</td><td>305 North Main Street, La Veta, CO; (719) 251-0469</td><td>Service / storage</td><td>Resident, seasonal, and moving/storage audience.</td><td>High - Town directory.</td></tr>
<tr><td>Go Ask Alys Catering</td><td>604 S. Oak Street, La Veta, CO; (719) 742-3742</td><td>Restaurant / food / catering</td><td>Catering and event-food partner.</td><td>High - Town directory.</td></tr>
<tr><td>H Unlimited</td><td>815 S. Oak Street, La Veta, CO; (719) 565-8173</td><td>Service / repair</td><td>Local service lead; verify storefront type.</td><td>Medium - Town directory.</td></tr>
<tr><td>Kathy Hill's Studio Gallery</td><td>133 E. Virginia St., La Veta, CO; (719) 742-5756</td><td>Arts / gallery</td><td>Artist, gallery, and cultural-route outreach.</td><td>High - Town directory.</td></tr>
<tr><td>Just in Time Bakery</td><td>107 West Francisco Street, La Veta, CO</td><td>Restaurant / food</td><td>Bakery and walk-in traffic; phone not published in retrieved page.</td><td>Medium - Town directory.</td></tr>
<tr><td>La Veta Country Store Valero</td><td>200 North Main Street, La Veta, CO; (719) 206-2899</td><td>Retail / fuel / convenience</td><td>Fuel, convenience, highway, resident, and traveler stop.</td><td>High - Town directory.</td></tr>
<tr><td>La Veta Inn</td><td>103 West Ryus Avenue, La Veta, CO; (719) 742-5566</td><td>Lodging</td><td>Town-center lodging anchor and guest handout partner.</td><td>High - Town directory.</td></tr>
<tr><td>La Veta Liquors</td><td>105 West Francisco Street, La Veta, CO; (719) 742-3216</td><td>Retail</td><td>Local retail traffic.</td><td>High - Town directory.</td></tr>
<tr><td>La Veta Mercantile</td><td>300 South Main Street, La Veta, CO; (719) 742-3387</td><td>Retail</td><td>Main Street retail and visitor shopping.</td><td>High - Town directory.</td></tr>
<tr><td>La Veta Oil Company</td><td>114 South Main Street, La Veta, CO; (719) 742-3664</td><td>Service / fuel</td><td>Fuel/energy service; verify exact line of business.</td><td>Medium - Town directory.</td></tr>
<tr><td>La Veta Physical Therapy</td><td>815 Oak Street, La Veta, CO; (719) 742-5474</td><td>Healthcare</td><td>Wellness, rehabilitation, and healthcare-adjacent outreach.</td><td>High - Town directory.</td></tr>
<tr><td>La Veta Pines RV Park</td><td>226 West Grand Street, La Veta, CO; (719) 742-3252</td><td>Lodging / RV</td><td>Seasonal traveler and RV guest audience.</td><td>High - Town directory.</td></tr>
<tr><td>La Veta Propane</td><td>132 West High Street, La Veta, CO; (719) 742-3291</td><td>Service / utility</td><td>Utility/fuel service with resident and rural household reach.</td><td>High - Town directory.</td></tr>
<tr><td>La Veta Schools of the Arts</td><td>105 West Ryus Avenue, La Veta, CO; (719) 742-3421</td><td>Arts / culture / education</td><td>Arts education and culture anchor.</td><td>High - Town directory.</td></tr>
<tr><td>La Veta Yoga Studio</td><td>315 S. Main Street, La Veta, CO; (415) 233-2632</td><td>Healthcare / wellness</td><td>Wellness, class, and visitor/resident health audience.</td><td>Medium - Town directory.</td></tr>
<tr><td>Legends on Main</td><td>305 S. Main Street, La Veta, CO; (719) 742-3372</td><td>Retail</td><td>Main Street customer traffic; verify exact merchandise mix.</td><td>Medium - Town directory.</td></tr>
<tr><td>Lou's Diner</td><td>700 South Main Street, La Veta, CO</td><td>Restaurant / food</td><td>Dining and traveler/resident traffic; phone not published on retrieved page.</td><td>Medium - Town directory.</td></tr>
<tr><td>Mountain Merman Brewing Company</td><td>220 South Main Street, La Veta, CO</td><td>Restaurant / food / brewery</td><td>Brewery/taproom and event-friendly visitor traffic.</td><td>Medium - Town directory.</td></tr>
<tr><td>Mountain Time Pilates</td><td>127 West Ryus, La Veta, CO</td><td>Healthcare / wellness</td><td>Wellness class and resident/visitor health audience.</td><td>Medium - Town directory.</td></tr>
<tr><td>Parmelee's</td><td>202 South Main Street, La Veta, CO</td><td>Restaurant / food</td><td>Restaurant-style outreach; verify exact concept.</td><td>Medium - Town directory.</td></tr>
<tr><td>Peakview Self-Storage</td><td>915 Cherry Street, La Veta, CO; (719) 989-8490</td><td>Service / storage</td><td>Storage and seasonal/resident service audience.</td><td>High - Town directory.</td></tr>
<tr><td>Petrichor IV Hydration</td><td>815 S. Oak Street, La Veta, CO; (719) 244-2269</td><td>Healthcare / wellness</td><td>Wellness/medical-adjacent service audience.</td><td>High - Town directory.</td></tr>
<tr><td>Ranch House Inn</td><td>1012 Cherry St., La Veta, CO; (719) 742-0260</td><td>Lodging</td><td>Highway-access lodging partner.</td><td>High - Town directory.</td></tr>
<tr><td>Roger Batchelor, DAOM Acupuncture</td><td>606 East Virginia Street, La Veta, CO; (503) 208-5183</td><td>Healthcare</td><td>Acupuncture and health/wellness audience.</td><td>High - Town directory.</td></tr>
<tr><td>The Salon LTD</td><td>208 South Main Street, La Veta, CO; (719) 742-3019</td><td>Service / personal care</td><td>Personal-service traffic and local notices.</td><td>High - Town directory.</td></tr>
<tr><td>Sammie's RV Park</td><td>124 N. Main Street, La Veta, CO; (719) 742-5435</td><td>Lodging / RV</td><td>RV traveler and seasonal audience.</td><td>High - Town directory.</td></tr>
<tr><td>Silvershoe</td><td>213 S. Main Street, La Veta, CO; (719) 742-3435</td><td>Retail</td><td>Main Street retail; verify merchandise mix.</td><td>Medium - Town directory.</td></tr>
<tr><td>Shalawalla</td><td>115 W. Ryus Ave, La Veta, CO; (719) 742-3453</td><td>Retail</td><td>Retail and visitor/resident browsing audience.</td><td>Medium - Town directory.</td></tr>
<tr><td>Spanish Peaks Arts Council / SPACe Gallery</td><td>132 W. Ryus Ave, La Veta, CO; (719) 742-3074</td><td>Arts / culture</td><td>Important arts anchor and likely outreach partner.</td><td>High - Town directory.</td></tr>
<tr><td>Trailhead General Store / Sinclair</td><td>5519 State Hwy 12, La Veta, CO; (719) 742-3442</td><td>Retail / gas / convenience</td><td>Highway of Legends traveler stop.</td><td>High - Town directory.</td></tr>
<tr><td>Two Fox Cabins &amp; RVs</td><td>404 Oak St., La Veta, CO; (719) 742-0260</td><td>Lodging</td><td>Cabin/RV lodging audience.</td><td>High - Town directory.</td></tr>
<tr><td>Two Peaks Fitness</td><td>216 South Main Street, La Veta, CO; (719) 742-3555</td><td>Healthcare / wellness / fitness</td><td>Fitness and wellness audience.</td><td>Medium - Town directory.</td></tr>
<tr><td>Two Mountain Treasures</td><td>206 South Main Street, La Veta, CO</td><td>Retail</td><td>Main Street retail; phone not published on retrieved page.</td><td>Medium - Town directory.</td></tr>
<tr><td>Tutu's Washateria</td><td>903 South Oak Street, La Veta, CO</td><td>Service / laundromat</td><td>Resident and traveler service stop.</td><td>Medium - Town directory.</td></tr>
<tr><td>Whispering Oaks</td><td>804 South Oak Street / P.O. Box 285, La Veta, CO; (719) 742-3240</td><td>Lodging / hospitality</td><td>Lodging/residential hospitality; confirm exact format.</td><td>Medium - Town directory.</td></tr>
<tr><td>We RV Champions of La Veta</td><td>126 W. 2nd St., La Veta, CO; (512) 422-0720</td><td>Service / RV</td><td>RV-related service; verify whether retail, repair, or dealer.</td><td>Medium - Town directory.</td></tr>
</tbody></table>
<h3>La Veta Civic, Cuchara/Gardner &amp; Rural Nodes</h3>
<table><thead><tr><th>Business / organization</th><th>Available contact</th><th>Category</th><th>Outreach use</th><th>Confidence / source</th></tr></thead><tbody>
<tr><td>Town of La Veta</td><td>209 S. Main St., La Veta, CO 81055; (719) 742-3631; https://townoflaveta-co.gov/</td><td>Government</td><td>Townwide notices, business-directory maintenance, hours/permission checks, and Main Street routing.</td><td>High - official town site.</td></tr>
<tr><td>Francisco Fort Museum</td><td>312 S. Main St., La Veta, CO; franciscofort.org</td><td>Arts / culture / heritage</td><td>Major heritage and cultural anchor.</td><td>High - civic/cultural listing.</td></tr>
<tr><td>RE-2 La Veta School District</td><td>La Veta, CO; lvk12.org</td><td>Education</td><td>La Veta-centered school, family, arts, and youth outreach.</td><td>High - county-linked district.</td></tr>
<tr><td>La Veta Public Library District</td><td>La Veta, CO; lvpl.org</td><td>Library / community</td><td>Posting, public engagement, and civic information partner.</td><td>High - county-linked library district.</td></tr>
<tr><td>Cuchara Mountain Park / Panadero Ski Corporation</td><td>Cuchara, CO</td><td>Tourism / outdoor recreation</td><td>Year-round park use and seasonal ski-area reopening activity; major Cuchara campaign anchor.</td><td>Medium - retrieved sources describe park and January 2026 ski-area reopening activity.</td></tr>
<tr><td>Cuchara Water and Sanitation District</td><td>Cuchara, CO; cuchara.org</td><td>Government / special district</td><td>Corridor touchpoint and local permission/referral contact.</td><td>High - county-listed special district.</td></tr>
<tr><td>Upper Huerfano Fire District</td><td>Gardner area; 5280fire.com</td><td>Government / fire district</td><td>Upper-valley safety, event, and rural outreach contact.</td><td>High - county-listed fire district.</td></tr>
<tr><td>Gardner Public Improvement District</td><td>Gardner, CO; county page linked from huerfano.us</td><td>Government / special district</td><td>Gardner service and corridor contact.</td><td>High - county key-service listing.</td></tr>
<tr><td>Navajo Western Water District</td><td>Gardner / western county; nwwd.us</td><td>Government / special district</td><td>Western-county service touchpoint and rural contact path.</td><td>High - county-listed special district.</td></tr>
<tr><td>Mission:Wolf</td><td>Gardner area</td><td>Nonprofit / attraction</td><td>Tourism/education attraction partner if direct operating contact is confirmed.</td><td>Medium - named by official tourism site; direct page not retrieved in report pass.</td></tr>
<tr><td>La Veta Fire Protection District</td><td>La Veta / Cuchara corridor; lavetafire.org</td><td>Government / fire district</td><td>Corridor outreach partner for event calendars, safety coordination, and bulletin permission asks.</td><td>High - county-listed district.</td></tr>
</tbody></table>
<h3>Rural Verification Nodes</h3>
<table><thead><tr><th>Community / node</th><th>Provisional anchor found</th><th>Sector</th><th>Outreach use</th><th>Recommended verification step</th></tr></thead><tbody>
<tr><td>Farisita</td><td>No currently operating public-facing business or organization confirmed in this pass</td><td>Rural verification zone</td><td>Field-check node for ranch, faith, fire, and resident referral routes.</td><td>Ask county, churches, fire, and ranch contacts locally.</td></tr>
<tr><td>Chama</td><td>No currently operating public-facing business or organization confirmed in this pass</td><td>Rural verification zone</td><td>Rural route add-on rather than first-wave drop.</td><td>Confirm any churches, mail stops, community boards, guides, or home-based businesses.</td></tr>
<tr><td>Pictou</td><td>No currently operating public-facing business or organization confirmed in this pass</td><td>Rural verification zone</td><td>Rural/industrial-history node.</td><td>Verify on ground and through county or local resident contacts.</td></tr>
<tr><td>Pryor</td><td>No currently operating public-facing business or organization confirmed in this pass</td><td>Rural verification zone</td><td>Low-priority field check.</td><td>Confirm public posting, faith, fire, mail, or ranch interfaces before listing.</td></tr>
<tr><td>Red Wing</td><td>No currently operating public-facing business or organization confirmed in this pass</td><td>Rural verification zone</td><td>Outdoor/recreation and rural-resident outreach may matter more than storefront drops.</td><td>Verify trail/outdoor, resident, mail, fire, and local community contacts.</td></tr>
<tr><td>Badito</td><td>No current public-facing target confirmed</td><td>Ghost-town / legacy node</td><td>Historical interest only unless current venue is confirmed.</td><td>Remove from first-wave outreach unless a current ranch, church, or venue is independently verified.</td></tr>
<tr><td>Calumet / Delcarbon / Malachite / Tioga</td><td>No current public-facing target confirmed</td><td>Ghost-town / legacy mining nodes</td><td>Historical context only for routine outreach.</td><td>Remove from first-wave outreach.</td></tr>
</tbody></table>
<h3>Huerfano Media, Posting, Lodging &amp; Organization Targets</h3>
<table><thead><tr><th>Business / organization</th><th>Available contact</th><th>Category</th><th>Outreach use</th><th>Confidence / source</th></tr></thead><tbody>
<tr><td>Spanish Peaks Country Tourism</td><td>Countywide tourism / visitor audience; spanishpeakscountry.com</td><td>Tourism / destination marketing</td><td>Best tourism-facing amplification partner; directory, event, and earned visibility path.</td><td>High - official tourism platform.</td></tr>
<tr><td>Huerfano County Economic Development Inc.</td><td>huerfano.org</td><td>Economic development</td><td>Business, employer, and local economic-development outreach.</td><td>High - county-listed anchor.</td></tr>
<tr><td>Spanish Peaks Business Alliance</td><td>spba.huerfano.org</td><td>Business network</td><td>Business-list and campaign partner; direct page not retrievable in report pass.</td><td>Medium - county-listed business alliance.</td></tr>
<tr><td>Spanish Peaks Chamber of Commerce</td><td>spanishpeakschamber.com</td><td>Chamber</td><td>Business advocacy and networking; direct directory details need verification.</td><td>Medium - county-listed chamber.</td></tr>
<tr><td>Huerfano County Fair Board</td><td>huerfanofair.com</td><td>Events / community</td><td>Seasonal and event cross-promotion.</td><td>High - organization listing.</td></tr>
<tr><td>Tourist Information Center at Heritage Park</td><td>Walsenburg area</td><td>Visitor center</td><td>Highest-value visitor posting point and county-endorsed visitor stop.</td><td>Medium - county directs visitors there; posting rules unspecified.</td></tr>
<tr><td>Huerfano County Government building</td><td>401 Main Street, Walsenburg, CO</td><td>Bulletin / public building</td><td>Public-notice adjacency; ask about public-facing flyer area.</td><td>Medium - permission required.</td></tr>
<tr><td>La Veta Inn</td><td>103 W. Ryus Ave., La Veta, CO; (719) 742-5566</td><td>Lodging partner</td><td>Strong downtown lodging partner for flyer drops and guest handouts.</td><td>High - Town directory.</td></tr>
<tr><td>Ranch House Inn</td><td>1012 Cherry St., La Veta, CO; (719) 742-0260</td><td>Lodging partner</td><td>Highway-access lodging partner.</td><td>High - Town directory.</td></tr>
<tr><td>La Veta Pines RV Park</td><td>226 W. Grand St., La Veta, CO; (719) 742-3252</td><td>Lodging partner</td><td>Seasonal traveler audience.</td><td>High - Town directory.</td></tr>
<tr><td>Sammie's RV Park</td><td>124 N. Main St., La Veta, CO; (719) 742-5435</td><td>Lodging partner</td><td>RV traveler audience.</td><td>High - Town directory.</td></tr>
<tr><td>Two Fox Cabins &amp; RVs</td><td>404 Oak St., La Veta, CO; (719) 742-0260</td><td>Lodging partner</td><td>Cabin/RV audience.</td><td>High - Town directory.</td></tr>
<tr><td>Whispering Oaks</td><td>804 South Oak Street / P.O. Box 285, La Veta, CO; (719) 742-3240</td><td>Lodging partner</td><td>Confirm exact lodging format before partnership ask.</td><td>Medium - Town directory.</td></tr>
</tbody></table>
<h3>Huerfano Three-Week Campaign Timeline</h3>
<table><thead><tr><th>Timing</th><th>Action</th><th>Example</th><th>Tools / streamlining</th></tr></thead><tbody>
<tr><td>Week 1</td><td>Build master contact sheet; finalize flyer, square graphic, press release, event blurb; submit to county channels, Spanish Peaks Country, radio, and key organizations; call Walsenburg anchors for posting permission.</td><td>Prepare a Huerfano-ready packet with title, 120-150 word blurb, full press release, square image, vertical flyer PDF, landscape graphic, date/time/location, price, accessibility note, and contact person.</td><td>Shared spreadsheet; reusable press release; pre-approved partner copy; permission log.</td></tr>
<tr><td>Week 2</td><td>Complete Walsenburg flyer route; complete La Veta flyer route; push first social wave; confirm calendar placements and radio mentions.</td><td>Walsenburg: county building, courthouse, mining museum, Fox Theatre, library, hospital campus, Heritage Park visitor area. La Veta: Town Hall, Main Street, SPACe, Francisco Fort, Ryus Avenue, lodging, Oak Street, highway stops.</td><td>Route checklist; photo log; contact sheet fields for physical drop done and digital send done.</td></tr>
<tr><td>Week 3</td><td>Run Cuchara/Gardner valley route; refresh high-traffic boards and lodging partners; push reminder social posts; capture field notes and missing-business updates.</td><td>Cuchara Mountain Park access area, district office touchpoints, Gardner public-improvement/fire/corridor boards, Mission:Wolf or attraction partners if permission is secured.</td><td>Field notes; verification status; repost tracker; updated business inventory.</td></tr>
</tbody></table>
<p><strong>Maintenance note:</strong> Before final publication, run a Walsenburg storefront sweep, a Cuchara summer-season merchant pass, and rural-node phone/field verification. Log posting permissions for libraries, museums, schools, public buildings, lodging partners, and visitor centers rather than assuming flyers are allowed.</p>
</section>"""


def json_for_script(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2).replace("</script", "<\\/script")


def make_dashboard(resources: list[dict], statuses: dict[str, dict]) -> str:
    total = len(resources)
    linked = sum(1 for r in resources if r.get("Website"))
    ok = sum(1 for r in resources if r.get("Validation_Status") == "ok")
    no_url = sum(1 for r in resources if r.get("Validation_Status") == "no_url")
    needs_follow_up = sum(1 for r in resources if r.get("Needs_Follow_Up"))
    goal_buttons = "\n".join(
        f'<button class="goal-button" type="button" data-goal="{goal}" aria-pressed="false">{label}</button>'
        for goal, label in GOAL_LABELS.items()
    )
    return f"""<section id="persona-dashboard" class="persona-dashboard" aria-labelledby="persona-title">
<div class="persona-inner">
<p class="persona-kicker">Operational directory</p>
<h2 id="persona-title">Filter local resources by person, task, county, and verification status</h2>
<p class="persona-lede">Each result is pulled from the guide's inventory, tagged by audience fit, expanded with a practical action module, and labeled for source confidence and follow-up. Blank fields stay blank instead of being treated as known.</p>
<div class="persona-controls">
<div>
<div class="persona-selector" role="group" aria-label="Persona selector">
<button class="persona-button" type="button" data-persona="ALL" aria-pressed="true">All</button>
<button class="persona-button" type="button" data-persona="FP" aria-pressed="false">For-Profit</button>
<button class="persona-button" type="button" data-persona="NP" aria-pressed="false">Non-Profit</button>
<button class="persona-button" type="button" data-persona="PG" aria-pressed="false">Program</button>
<button class="persona-button" type="button" data-persona="EN" aria-pressed="false">Entrepreneur</button>
<button class="persona-button" type="button" data-persona="AR" aria-pressed="false">Artist</button>
</div>
<div class="goal-selector" role="group" aria-label="Task selector">
<button class="goal-button" type="button" data-goal="ALL" aria-pressed="true">Any task</button>
{goal_buttons}
</div>
</div>
<div class="search-wrap">
<label for="resource-search">Search current view</label>
<div class="search-row">
<input id="resource-search" class="search-input" type="search" placeholder="Try grant, radio, gallery, Raton, La Veta..." autocomplete="off"/>
<button id="resource-clear" class="clear-button" type="button">Clear</button>
</div>
</div>
</div>
<div class="filter-grid" aria-label="Directory filters">
<label for="county-filter">County
<select id="county-filter" class="filter-select"><option value="ALL">All counties</option></select>
</label>
<label for="type-filter">Resource type
<select id="type-filter" class="filter-select"><option value="ALL">All types</option></select>
</label>
<label for="status-filter">Verification
<select id="status-filter" class="filter-select">
<option value="ALL">All records</option>
<option value="verified">Verified link / source</option>
<option value="needs_follow_up">Needs follow-up</option>
<option value="manual">Manual verification</option>
<option value="has_url">Has source URL</option>
<option value="no_url">No source URL</option>
</select>
</label>
</div>
<div class="status-strip" aria-label="Resource data status">
<div class="status-item"><strong>{total}</strong><span>normalized resource records</span></div>
<div class="status-item"><strong>{linked}</strong><span>records with primary source links</span></div>
<div class="status-item"><strong>{ok}</strong><span>links verified by checker</span></div>
<div class="status-item"><strong>{no_url}</strong><span>manual or phone-verification records</span></div>
<div class="status-item"><strong>{needs_follow_up}</strong><span>records flagged for follow-up</span></div>
</div>
<noscript><div class="noscript-note">The filtered directory needs JavaScript. The long-form guide, tables, county inventories, templates, and downloadable CSV remain usable without scripts.</div></noscript>
<p id="resource-count" class="card-source" aria-live="polite"></p>
<div id="resource-grid" class="resource-grid"></div>
</div>
<script type="application/json" id="resource-data">
{json_for_script(resources)}
</script>
<script type="application/json" id="persona-schema">
{json_for_script({"personas": PERSONA_LABELS, "goals": GOAL_LABELS, "visibility_logic": {p: f"Display resources whose Persona_Relevance includes {p}." for p in PERSONA_ORDER}, "last_updated": UPDATE_ISO, "validation_report": str(REPORT_PATH.name), "csv_export": str(CSV_PATH.name)})}
</script>
</section>
<div class="source-guide-note"><strong>Reference guide:</strong> The original long-form sections remain below for context, narrative guidance, and table-level review. The finder above is the normalized, tagged, action-oriented layer requested by the implementation roadmap.</div>"""


def make_runtime_script() -> str:
    return r"""<script>
(function () {
  const labels = { FP: "For-Profit", NP: "Non-Profit", PG: "Program", EN: "Entrepreneur", AR: "Artist" };
  const goalLabels = {
    START: "Start Something",
    PROMOTE: "Promote Something",
    FUNDING: "Find Money / Help",
    MEDIA: "Get Media Coverage",
    OFFLINE: "Reach People Offline",
    ONLINE: "Improve Online Visibility",
    LISTING: "Add / Correct Info",
    TRACK: "Track Results"
  };
  const dataNode = document.getElementById("resource-data");
  const resources = dataNode ? JSON.parse(dataNode.textContent) : [];
  const grid = document.getElementById("resource-grid");
  const count = document.getElementById("resource-count");
  const search = document.getElementById("resource-search");
  const clear = document.getElementById("resource-clear");
  const buttons = Array.from(document.querySelectorAll(".persona-button"));
  const goalButtons = Array.from(document.querySelectorAll(".goal-button"));
  const countyFilter = document.getElementById("county-filter");
  const typeFilter = document.getElementById("type-filter");
  const statusFilter = document.getElementById("status-filter");
  let activePersona = "ALL";
  let activeGoal = "ALL";

  function escapeHtml(value) {
    return String(value || "").replace(/[&<>"']/g, function (char) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char];
    });
  }

  function hasValue(value) {
    if (value === null || value === undefined) return false;
    const text = String(value).trim();
    return text && text.toLowerCase() !== "null" && text.toLowerCase() !== "none";
  }

  function joinList(value) {
    return Array.isArray(value) ? value.filter(hasValue).join(", ") : (hasValue(value) ? String(value) : "");
  }

  function detail(label, value) {
    return hasValue(value) ? `<li><strong>${escapeHtml(label)}:</strong> ${escapeHtml(value)}</li>` : "";
  }

  function statusClass(value) {
    return String(value || "no-url").replace(/_/g, "-");
  }

  function statusLabel(value) {
    if (value === "ok") return "Link verified";
    if (value === "broken") return "Link needs review";
    if (value === "timeout_or_error") return "Link unconfirmed";
    if (value === "no_url") return "Manual verification";
    return "Not checked";
  }

  function statusFilterMatch(resource) {
    const selected = statusFilter ? statusFilter.value : "ALL";
    if (selected === "ALL") return true;
    if (selected === "verified") return resource.Validation_Status === "ok" && !resource.Needs_Follow_Up;
    if (selected === "needs_follow_up") return Boolean(resource.Needs_Follow_Up) || ["broken", "timeout_or_error"].includes(resource.Validation_Status);
    if (selected === "manual") return resource.Validation_Status === "no_url" || resource.Verification_Method === "Unverified";
    if (selected === "has_url") return hasValue(resource.Website);
    if (selected === "no_url") return !hasValue(resource.Website);
    return true;
  }

  function populateSelect(select, field) {
    if (!select) return;
    const values = Array.from(new Set(resources.map(function (resource) {
      return resource[field];
    }).filter(hasValue))).sort(function (a, b) {
      return String(a).localeCompare(String(b));
    });
    values.forEach(function (value) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      select.appendChild(option);
    });
  }

  function resourceText(resource) {
    return [
      resource.Name,
      resource.Category,
      resource.Description,
      resource.Contact_Info,
      resource.Contact_Email,
      resource.Contact_Phone,
      resource.Physical_Address,
      resource.Town,
      resource.County,
      resource.Resource_Type,
      resource.Source_Section,
      resource.Source_Type,
      resource.Verification_Method,
      resource.Confidence_Level,
      joinList(resource.Goal_Relevance),
      joinList(resource.Audience_Served)
    ].join(" ").toLowerCase();
  }

  function renderCard(resource) {
    const chips = (resource.Persona_Relevance || []).map(function (persona) {
      return `<span class="persona-chip">${escapeHtml(labels[persona] || persona)}</span>`;
    }).join("");
    const goalChips = (resource.Goal_Relevance || []).map(function (goal) {
      return `<span class="goal-chip">${escapeHtml(goalLabels[goal] || goal)}</span>`;
    }).join("");
    const checklist = ((resource.Action_Module && resource.Action_Module.Requirement_Checklist) || []).map(function (item) {
      return `<li>${escapeHtml(item)}</li>`;
    }).join("");
    const website = resource.Website
      ? `<a class="resource-link" href="${escapeHtml(resource.Website)}" target="_blank" rel="noopener">${escapeHtml(resource.Website)}</a>`
      : `<span class="card-source">No direct URL in source; verify by phone, local partner, or current directory.</span>`;
    const anchor = resource.Source_Anchor
      ? `<a href="#${escapeHtml(resource.Source_Anchor)}">${escapeHtml(resource.Source_Section)}</a>`
      : escapeHtml(resource.Source_Section || "Source table");
    const contacts = [
      detail("Public phone", resource.Contact_Phone),
      detail("Public email", resource.Contact_Email),
      detail("Address", resource.Physical_Address),
      detail("Contact notes", resource.Contact_Info)
    ].join("");
    const sourceDetails = [
      detail("Source type", resource.Source_Type),
      detail("Verification method", resource.Verification_Method),
      detail("Last verified", resource.Last_Verified_Date),
      detail("Audience served", joinList(resource.Audience_Served)),
      detail("Access mode", resource.Access_Mode),
      detail("Cost signal", resource.Cost_Level)
    ].join("");
    const followUp = resource.Needs_Follow_Up ? `<span class="follow-up-chip">Needs follow-up</span>` : "";
    const tip = resource.Action_Module && resource.Action_Module.User_Tip ? resource.Action_Module.User_Tip : "";
    const primarySource = resource.Action_Module && resource.Action_Module.Primary_Source_Link ? resource.Action_Module.Primary_Source_Link : "";
    return `<article class="resource-card">
      <div class="persona-chip-row">
        <span class="resource-type">${escapeHtml(resource.Resource_Type)}</span>
        <span class="confidence-chip">${escapeHtml(resource.Confidence_Level || "Unknown")} confidence</span>
        ${followUp}${chips}${goalChips}
      </div>
      <h3>${escapeHtml(resource.Name)}</h3>
      <div class="card-meta">${escapeHtml([resource.Town, resource.County, resource.State].filter(hasValue).join(" · "))} · ${escapeHtml(resource.Category)}</div>
      <p class="card-description">${escapeHtml(resource.Description)}</p>
      ${contacts ? `<ul class="card-detail-list">${contacts}</ul>` : ""}
      <div>${website}</div>
      <details class="resource-actions">
        <summary>Action module</summary>
        <ul>${checklist}</ul>
        ${tip ? `<p class="card-description"><strong>Tip:</strong> ${escapeHtml(tip)}</p>` : ""}
        ${primarySource ? `<p class="card-source"><strong>Primary source:</strong> ${escapeHtml(primarySource)}</p>` : ""}
        ${sourceDetails ? `<ul class="card-detail-list">${sourceDetails}</ul>` : ""}
      </details>
      <div class="card-source"><strong>Source:</strong> ${anchor}</div>
      <div class="status-badge"><span class="status-dot ${statusClass(resource.Validation_Status)}" aria-hidden="true"></span>${statusLabel(resource.Validation_Status)} · Updated ${escapeHtml(resource.Last_Updated)}</div>
    </article>`;
  }

  function applyFilters() {
    if (!grid || !count) return;
    const query = (search && search.value || "").trim().toLowerCase();
    const county = countyFilter ? countyFilter.value : "ALL";
    const type = typeFilter ? typeFilter.value : "ALL";
    const filtered = resources.filter(function (resource) {
      const personaMatch = activePersona === "ALL" || (resource.Persona_Relevance || []).includes(activePersona);
      const goalMatch = activeGoal === "ALL" || (resource.Goal_Relevance || []).includes(activeGoal);
      const countyMatch = county === "ALL" || resource.County === county;
      const typeMatch = type === "ALL" || resource.Resource_Type === type;
      const queryMatch = !query || resourceText(resource).includes(query);
      return personaMatch && goalMatch && countyMatch && typeMatch && statusFilterMatch(resource) && queryMatch;
    });
    count.textContent = `${filtered.length} of ${resources.length} resources shown`;
    grid.innerHTML = filtered.length
      ? filtered.map(renderCard).join("")
      : `<div class="empty-state">No resources match this combination. Try clearing search, switching the task, or including records that need follow-up.</div>`;
  }

  function setupTableScroll() {
    document.querySelectorAll("section table").forEach(function (table, index) {
      if (table.parentElement && table.parentElement.classList.contains("table-scroll")) return;
      if (!table.caption) {
        const nearestHeading = table.closest("section") && table.closest("section").querySelector("h2, h3");
        const caption = document.createElement("caption");
        caption.className = "sr-only";
        caption.textContent = nearestHeading ? `${nearestHeading.textContent} table` : `Guide data table ${index + 1}`;
        table.prepend(caption);
      }
      const wrapper = document.createElement("div");
      wrapper.className = "table-scroll";
      table.parentNode.insertBefore(wrapper, table);
      wrapper.appendChild(table);
    });
  }

  function setupActiveNav() {
    const links = Array.from(document.querySelectorAll("nav a[href^='#']"));
    const sections = links.map(function (link) {
      return document.querySelector(link.getAttribute("href"));
    }).filter(Boolean);
    if (!("IntersectionObserver" in window) || !sections.length) return;
    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        links.forEach(function (link) {
          link.classList.toggle("active", link.getAttribute("href") === `#${entry.target.id}`);
        });
      });
    }, { rootMargin: "-20% 0px -70% 0px", threshold: 0.01 });
    sections.forEach(function (section) { observer.observe(section); });
  }

  setupTableScroll();
  setupActiveNav();
  populateSelect(countyFilter, "County");
  populateSelect(typeFilter, "Resource_Type");
  buttons.forEach(function (button) {
    button.addEventListener("click", function () {
      activePersona = button.dataset.persona;
      buttons.forEach(function (other) {
        other.setAttribute("aria-pressed", String(other === button));
      });
      applyFilters();
    });
  });
  goalButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      activeGoal = button.dataset.goal;
      goalButtons.forEach(function (other) {
        other.setAttribute("aria-pressed", String(other === button));
      });
      applyFilters();
    });
  });
  [countyFilter, typeFilter, statusFilter].forEach(function (select) {
    if (select) select.addEventListener("change", applyFilters);
  });
  if (search) search.addEventListener("input", applyFilters);
  if (clear && search) clear.addEventListener("click", function () {
    search.value = "";
    search.focus();
    applyFilters();
  });
  applyFilters();
})();
</script>"""


def replace_between(pattern: str, replacement: str, source: str, flags: int = 0) -> str:
    new_source, count = re.subn(pattern, replacement, source, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f"Expected to replace exactly one block for pattern: {pattern[:50]}")
    return new_source


def upsert_section(source: str, section_id: str, section_html: str, before_section_id: str) -> str:
    pattern = rf'<section\b[^>]*id="{re.escape(section_id)}"[^>]*>.*?</section>'
    if re.search(pattern, source, flags=re.DOTALL):
        return re.sub(pattern, section_html, source, count=1, flags=re.DOTALL)
    before_pattern = rf'<section\b[^>]*id="{re.escape(before_section_id)}"'
    if not re.search(before_pattern, source):
        raise RuntimeError(f"Could not find insertion point section: {before_section_id}")
    return re.sub(before_pattern, section_html + "\n" + re.search(before_pattern, source).group(0), source, count=1)


def ensure_inventory_sections(source: str) -> str:
    source = upsert_section(
        source,
        "lasanimas-outreach-inventory",
        make_las_animas_inventory_section(),
        "lasanimas-deep",
    )
    source = upsert_section(
        source,
        "huerfano-outreach-inventory",
        make_huerfano_inventory_section(),
        "huerfano-deep",
    )
    return source


def ensure_operational_sections(source: str) -> str:
    start_insertion = "persona-dashboard" if 'id="persona-dashboard"' in source else "toc"
    source = upsert_section(source, "start-here", make_start_here_section(), start_insertion)
    for section_id, section_html in [
        ("launch-pathways", make_launch_pathways_section()),
        ("county-recipes", make_county_recipes_section()),
        ("templates", make_templates_section()),
        ("metrics-reporting", make_metrics_section()),
        ("submit-correct", make_intake_correction_section()),
        ("about-methodology", make_methodology_section()),
    ]:
        source = upsert_section(source, section_id, section_html, "toc")
    return source


def update_html(original: str, resources: list[dict], statuses: dict[str, dict]) -> str:
    updated = original
    for old, new in SOURCE_TEXT_REPLACEMENTS.items():
        updated = updated.replace(old, new)
    updated = updated.replace('content="width=device‑width, initial‑scale=1.0"', 'content="width=device-width, initial-scale=1.0"')
    updated = re.sub(r"letter-spacing:\s*(?:0\.5px|\.08em|\.03em);", "letter-spacing: 0;", updated)
    updated = replace_between(r"<header\b[^>]*>.*?</header>", make_header(), updated, flags=re.DOTALL)
    updated = replace_between(r"<nav\b[^>]*>.*?</nav>", make_nav(), updated, flags=re.DOTALL)
    updated = ensure_inventory_sections(updated)
    if "/* Persona-guided resource finder" not in updated:
        updated = updated.replace("</style>", build_css() + "\n</style>")
    else:
        updated = re.sub(
            r"\n\s*/\* Persona-guided resource finder: implemented from the transformation roadmap\..*?\n</style>",
            "\n" + build_css() + "\n</style>",
            updated,
            count=1,
            flags=re.DOTALL,
        )
    dashboard = make_dashboard(resources, statuses)
    if '<section id="persona-dashboard"' in updated:
        updated = replace_between(r'<section id="persona-dashboard".*?<div class="source-guide-note">.*?</div>', dashboard, updated, flags=re.DOTALL)
    else:
        updated = updated.replace("</nav>", "</nav>\n" + dashboard, 1)
    updated = ensure_operational_sections(updated)
    runtime_script = make_runtime_script()
    if "const labels = { FP:" in updated:
        updated = replace_between(r"<script>\s*\(function \(\) \{\s*const labels = \{ FP:.*?</script>", runtime_script, updated, flags=re.DOTALL)
    else:
        updated = updated.replace("</body>", runtime_script + "\n</body>")
    updated = re.sub(r'\n?<footer id="guide-brand-footer".*?</footer>', "", updated, count=1, flags=re.DOTALL)
    updated = updated.replace("</body>", make_logo_footer() + "\n</body>", 1)
    if 'class="back-to-top"' not in updated:
        updated = updated.replace("</body>", '<a class="back-to-top" href="#top">Top</a>\n</body>', 1)
    return updated


def csv_cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "; ".join(str(item) for item in value if item is not None)
    return str(value)


def resource_to_operational_row(resource: dict) -> dict[str, str]:
    return {
        "id": resource.get("id"),
        "resource_name": resource.get("Name"),
        "category": resource.get("Category"),
        "town": resource.get("Town"),
        "county": resource.get("County"),
        "state": resource.get("State"),
        "website": resource.get("Website"),
        "contact_email": resource.get("Contact_Email"),
        "contact_phone": resource.get("Contact_Phone"),
        "physical_address": resource.get("Physical_Address"),
        "source_url": resource.get("Source_URL"),
        "source_type": resource.get("Source_Type"),
        "last_verified_date": resource.get("Last_Verified_Date"),
        "verification_method": resource.get("Verification_Method"),
        "confidence_level": resource.get("Confidence_Level"),
        "notes": resource.get("Operational_Notes") or resource.get("Description"),
        "needs_follow_up": resource.get("Needs_Follow_Up"),
        "resource_type": resource.get("Resource_Type"),
        "audience_served": resource.get("Audience_Served"),
        "cost_level": resource.get("Cost_Level"),
        "access_mode": resource.get("Access_Mode"),
        "goal_relevance": [GOAL_LABELS.get(goal, goal) for goal in resource.get("Goal_Relevance", [])],
    }


def write_resource_csv(resources: list[dict]) -> None:
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OPERATIONAL_FIELD_ORDER)
        writer.writeheader()
        for resource in resources:
            row = resource_to_operational_row(resource)
            writer.writerow({field: csv_cell(row.get(field)) for field in OPERATIONAL_FIELD_ORDER})


def write_download_readme(resources: list[dict], statuses: dict[str, dict]) -> None:
    needs_follow_up = sum(1 for resource in resources if resource.get("Needs_Follow_Up"))
    lines = [
        "Tri-County Regional Marketing Guide Download Package",
        "",
        f"Generated: {UPDATE_ISO}",
        f"Resources: {len(resources)}",
        f"Unique URLs checked: {len(statuses)}",
        f"Records flagged for follow-up: {needs_follow_up}",
        "",
        "Files:",
        f"- {DOWNLOAD_HTML_PATH.name}: standalone interactive HTML guide",
        f"- {CSV_PATH.name}: operational resource table for review, correction, and import",
        f"- {JSON_PATH.name}: full structured resource data used by the interactive finder",
        f"- {REPORT_PATH.name}: automated link validation and manual review notes",
        "- assets/brand/raton-logo.png: local copy of the Raton logo used in the footer credit",
        "- assets/brand/super-eukarya-logo.png: local copy of the Super Eukarya logo used in the footer credit",
        "",
        "Publication note:",
        "Verify deadlines, eligibility, contact names, posting permissions, costs, accessibility details, and active business status before relying on any record for public commitments or spending.",
    ]
    DOWNLOAD_README_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_download_package() -> None:
    DOWNLOAD_HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HTML_PATH, DOWNLOAD_HTML_PATH)
    shutil.copy2(DOWNLOAD_HTML_PATH, DIST_DIR / DOWNLOAD_HTML_PATH.name)
    with zipfile.ZipFile(DOWNLOAD_ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in [DOWNLOAD_HTML_PATH, CSV_PATH, JSON_PATH, REPORT_PATH, DOWNLOAD_README_PATH]:
            if path.exists():
                archive.write(path, arcname=path.name)
        for path in sorted(BRAND_ASSET_DIR.glob("*")):
            if path.is_file():
                archive.write(path, arcname=f"assets/brand/{path.name}")


def main() -> int:
    if not HTML_PATH.exists():
        print(f"Missing HTML file: {HTML_PATH}", file=sys.stderr)
        return 1
    original = HTML_PATH.read_text(encoding="utf-8", errors="replace")
    for old, new in SOURCE_TEXT_REPLACEMENTS.items():
        original = original.replace(old, new)
    backup_path = HTML_PATH.with_name(f"{HTML_PATH.stem}.backup_before_persona_{UPDATE_ISO.replace('-', '')}.html")
    if not backup_path.exists():
        shutil.copy2(HTML_PATH, backup_path)

    original = ensure_inventory_sections(original)
    doc = html.fromstring(original)
    resources = extract_resources(doc)
    pre_validation_resources = copy.deepcopy(resources)
    statuses = validate_links(resources)
    JSON_PATH.write_text(json.dumps(resources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_resource_csv(resources)
    write_validation_report(resources, statuses)
    updated = update_html(original, resources, statuses)
    HTML_PATH.write_text(updated, encoding="utf-8")
    write_download_readme(resources, statuses)
    write_download_package()

    print(json.dumps({
        "resources": len(resources),
        "persona_counts": {PERSONA_LABELS[p]: sum(1 for r in resources if p in r["Persona_Relevance"]) for p in PERSONA_ORDER},
        "goal_counts": {GOAL_LABELS[g]: sum(1 for r in resources if g in r.get("Goal_Relevance", [])) for g in GOAL_LABELS},
        "unique_urls_checked": len(statuses),
        "backup": str(backup_path),
        "json": str(JSON_PATH),
        "csv": str(CSV_PATH),
        "report": str(REPORT_PATH),
        "html": str(HTML_PATH),
        "download_html": str(DOWNLOAD_HTML_PATH),
        "download_zip": str(DOWNLOAD_ZIP_PATH),
        "workspace_dist_html": str(DIST_DIR / DOWNLOAD_HTML_PATH.name),
        "changed_resource_count_by_validation": len(pre_validation_resources) == len(resources),
        "html_sha256": hashlib.sha256(updated.encode("utf-8")).hexdigest(),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
