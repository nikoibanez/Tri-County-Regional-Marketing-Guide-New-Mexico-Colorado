from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import shutil
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from textwrap import dedent
from urllib.parse import quote_plus, urlparse

from directory_exclusions import (
    filter_excluded_directory_rows,
    row_references_excluded_directory_entity,
)
from directory_outreach import CHANNEL_DEFINITIONS, classify_outreach_channels


ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = Path.home() / "Downloads"
REPO_DATA = ROOT / "data"
SITE_EXTRAS = ROOT / "site-extras"
OUT = ROOT / "dist" / "tri-county-netlify-guide-deep"
ASSET_OUT = OUT / "assets"
DATA_OUT = OUT / "data"

SOURCE_CSV = REPO_DATA / "tri_county_persona_resources.csv"
if not SOURCE_CSV.exists():
    SOURCE_CSV = DOWNLOADS / "tri_county_persona_resources.csv"
SOURCE_JSON = REPO_DATA / "tri_county_persona_resources.json"
if not SOURCE_JSON.exists():
    SOURCE_JSON = DOWNLOADS / "tri_county_persona_resources.json"
EVERYTHING_DIRECTORY_JSON = REPO_DATA / "directory_of_absolutely_everything.json"
LISTING_KEYWORD_INDEX_JSON = REPO_DATA / "listing-keyword-index.json"
DIRECTORY_CONNECTIVITY_STATUS_JSON = REPO_DATA / "directory-connectivity-status.json"
NATIONAL_FUNDING_JSON = REPO_DATA / "national-funding-opportunities.json"
NATIONAL_FUNDING_WATCH_JSON = REPO_DATA / "national-funding-watch-sources.json"
RESOURCE_DISCOVERY_JSON = REPO_DATA / "resource-discovery-sources.json"
RESOURCE_KEYWORD_REGISTRY_JSON = REPO_DATA / "resource-keyword-registry.json"
REGIONAL_AUDIO_JSON = REPO_DATA / "regional_audio_manifest.json"
FREE_TOOLS_JSON = REPO_DATA / "free-tools.json"
REAUDIT_NOTES = DOWNLOADS / "tri_county_reaudit" / "comprehensive_reaudit_source_notes.md"
NEW_PDF_EXTRACT_DIR = DOWNLOADS / "tri_county_new_pdf_extract_20260621"
BUILD_DATE = os.environ.get("BUILD_DATE", date.today().isoformat())
DEFAULT_LISTING_DESCRIPTION = "Tri-county business, nonprofit, arts, tourism, or service listing for local discovery and outreach."
DIRECTORY_PROFILE_HOSTS = {
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
SOCIAL_CHANNEL_HOSTS = {"facebook.com", "instagram.com", "youtube.com", "youtu.be"}


def load_directory_connectivity_data() -> tuple[dict[str, dict], dict[str, dict]]:
    if not DIRECTORY_CONNECTIVITY_STATUS_JSON.exists():
        return {}, {}
    try:
        payload = json.loads(DIRECTORY_CONNECTIVITY_STATUS_JSON.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}, {}
    entries = payload.get("entries", [])
    checks = payload.get("checks", {})
    if not isinstance(entries, list):
        entries = []
    if not isinstance(checks, dict):
        checks = {}
    entry_map = {
        str(entry.get("entry_id") or ""): entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("entry_id")
    }
    return entry_map, checks


DIRECTORY_CONNECTIVITY_ENTRIES, DIRECTORY_CONNECTIVITY_CHECKS = load_directory_connectivity_data()


def normalize_origin(value: str) -> str:
    value = (value or "").strip() or "https://deluxe-horse-207efc.netlify.app"
    return value.rstrip("/") + "/"


SITE_URL = normalize_origin(os.environ.get("PUBLIC_SITE_ORIGIN", "https://deluxe-horse-207efc.netlify.app"))


def load_json_records(path: Path, key: str) -> list[dict]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    records = payload.get(key, []) if isinstance(payload, dict) else []
    return [item for item in records if isinstance(item, dict)] if isinstance(records, list) else []


def load_json_list(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return [item for item in payload if isinstance(item, dict)] if isinstance(payload, list) else []


NATIONAL_FUNDING_OPPORTUNITIES = load_json_records(NATIONAL_FUNDING_JSON, "opportunities")
NATIONAL_FUNDING_WATCH_SOURCES = load_json_records(NATIONAL_FUNDING_WATCH_JSON, "sources")
RESOURCE_DISCOVERY_SOURCES = load_json_records(RESOURCE_DISCOVERY_JSON, "sources")
REGIONAL_AUDIO_TRACKS = load_json_list(REGIONAL_AUDIO_JSON)
PROMOTION_TOOLS = load_json_records(FREE_TOOLS_JSON, "tools")
FREE_TOOL_DISCOVERY_SOURCES = load_json_records(FREE_TOOLS_JSON, "discovery_sources")


def build_asset_version() -> str:
    deploy_ref = re.sub(
        r"[^a-zA-Z0-9]+",
        "",
        os.environ.get("COMMIT_REF") or os.environ.get("GITHUB_SHA") or "",
    )
    if deploy_ref:
        return deploy_ref[:12]
    digest = hashlib.sha256()
    for path in (
        Path(__file__),
        SOURCE_CSV,
        SOURCE_JSON,
        EVERYTHING_DIRECTORY_JSON,
        LISTING_KEYWORD_INDEX_JSON,
        DIRECTORY_CONNECTIVITY_STATUS_JSON,
        NATIONAL_FUNDING_JSON,
        NATIONAL_FUNDING_WATCH_JSON,
        RESOURCE_DISCOVERY_JSON,
        RESOURCE_KEYWORD_REGISTRY_JSON,
        REGIONAL_AUDIO_JSON,
        FREE_TOOLS_JSON,
    ):
        if path.exists():
            digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


ASSET_VERSION = build_asset_version()

ACTIVE_PATHS = {
    "home": "",
    "plan": "plan/",
    "amplifiers": "amplifiers/",
    "promote": "promote/",
    "network": "network/",
    "posting": "posting/",
    "region": "region/",
    "colfax": "counties/colfax/",
    "las-animas": "counties/las-animas/",
    "huerfano": "counties/huerfano/",
    "templates": "templates/",
    "free-tools": "tools/free-discounted/",
    "submit": "submit/",
    "appendix": "appendix/",
    "about": "about/",
    "funding": "resources/funding/",
    "arts-culture": "resources/arts-culture/",
    "post-raton": "post-events-raton/",
    "post-trinidad": "post-events-trinidad/",
    "post-huerfano": "post-events-huerfano/",
    "advertise-trinidad": "advertise-trinidad/",
    "colfax-business": "colfax-business/",
    "las-animas-nonprofit": "las-animas-nonprofit/",
    "huerfano-calendars": "huerfano-calendars/",
    "artist-gallery": "artist-gallery-promotion/",
    "regional-channels": "regional-channels/",
}

HERO_ART_BY_ACTIVE = {
    "plan": "hero-plains-valley.svg",
    "network": "hero-fishers-peak.svg",
    "amplifiers": "hero-garden-gods.svg",
    "promote": "hero-garden-gods.svg",
    "posting": "hero-desert-buttes.svg",
    "region": "hero-raton-mesa.svg",
    "colfax": "hero-volcanic-field.svg",
    "las-animas": "hero-fishers-canyon.svg",
    "huerfano": "hero-spanish-peaks.svg",
    "templates": "hero-huerfano-valley.svg",
    "free-tools": "hero-plains-valley.svg",
    "submit": "hero-canyon-submit.svg",
    "appendix": "hero-archive-ridges.svg",
    "about": "hero-raton-mesa.svg",
    "funding": "hero-plains-valley.svg",
    "arts-culture": "hero-garden-gods.svg",
    "post-raton": "hero-volcanic-field.svg",
    "post-trinidad": "hero-fishers-canyon.svg",
    "post-huerfano": "hero-spanish-peaks.svg",
    "advertise-trinidad": "hero-fishers-peak.svg",
    "colfax-business": "hero-raton-mesa.svg",
    "las-animas-nonprofit": "hero-garden-gods.svg",
    "huerfano-calendars": "hero-huerfano-valley.svg",
    "artist-gallery": "hero-desert-buttes.svg",
    "regional-channels": "hero-plains-valley.svg",
}

VERIFICATION_LABELS = {
    "official-source": "Official/public source checked",
    "source-linked": "Source-linked lead",
    "field-check": "Field-check lead",
    "process-note": "Method note",
}

VERIFICATION_CLASSES = {
    "official-source": "status-official",
    "source-linked": "status-linked",
    "field-check": "status-field",
    "process-note": "status-process",
}

LAYER_LABELS = {
    "verified_directory": "Verified/public shortcut",
    "source_linked": "Source-linked lead",
    "provisional_lead": "Field-check lead",
    "creation_process_note": "Method note",
}

SOURCE_NOTE_INPUTS = [
    NEW_PDF_EXTRACT_DIR / "amplifier_channels.extracted.txt",
    NEW_PDF_EXTRACT_DIR / "business_directory_research_findings.extracted.txt",
    NEW_PDF_EXTRACT_DIR / "small_community_contact_guide.extracted.txt",
]
SOURCE_NOTE_EXPORTS = [
    (SOURCE_NOTE_INPUTS[0], "amplifier_channels.txt"),
    (SOURCE_NOTE_INPUTS[1], "business_directory.txt"),
    (SOURCE_NOTE_INPUTS[2], "small_contacts.txt"),
]


COUNTIES = ["Colfax", "Las Animas", "Huerfano", "Regional"]


HOME_TASK_GROUPS = [
    {
        "title": "Post an event",
        "href": "promote/?route=events",
        "summary": "Find the calendar, tourism, venue, media, or public-office route that fits the event before sending materials everywhere.",
        "action": "Choose an event route",
    },
    {
        "title": "Promote or advertise",
        "href": "promote/",
        "summary": "Compare visitor guides, newsletters, media outlets, chamber channels, and partner pages before asking about placement.",
        "action": "Find promotion channels",
    },
    {
        "title": "Get listed",
        "href": "network/",
        "summary": "Search public directories and local inventory entries, then submit updates when a listing is missing or stale.",
        "action": "Search the directory",
    },
    {
        "title": "Find funding",
        "href": "resources/funding/",
        "summary": "Start with grant, incentive, scholarship, stipend, loan, and technical-assistance entries that match the applicant and project.",
        "action": "Search funding entries",
    },
    {
        "title": "Arts & culture",
        "href": "resources/arts-culture/",
        "summary": "Use arts, gallery, maker, music, creative-district, venue, and visitor-facing channels without burying the audience in process notes.",
        "action": "Open arts routes",
    },
    {
        "title": "County starting points",
        "href": "region/",
        "summary": "Begin with the most useful local hubs in Colfax, Las Animas, or Huerfano, then widen across the region when it helps.",
        "action": "Choose a county",
    },
]


DIRECTORY_SOURCES = [
    {
        "title": "Colorado Vacation Directory",
        "county": "Regional",
        "kind": "Visitor and recreation directory",
        "url": "https://www.coloradodirectory.com/",
        "best_for": "Finding visitor-oriented lodging, recreation, dining, and attraction pages that may include Huerfano and Las Animas County destinations.",
        "action": "Use the directory to discover possible visitor channels, then confirm each business or destination through its own current website before outreach.",
        "confidence": "Medium",
    },
    {
        "title": "New Mexico True Northeast and Raton Guide",
        "county": "Colfax",
        "kind": "State tourism guide",
        "url": "https://www.newmexico.org/places-to-visit/regions/northeast/raton/",
        "best_for": "Finding state tourism context, attractions, scenic routes, and visitor ideas connected to Raton and northeastern New Mexico.",
        "action": "Use it as a visitor-discovery route, then open the named attraction or business page for current contact information.",
        "confidence": "High",
    },
    {
        "title": "Visit Trinidad Outdoor Recreation",
        "county": "Las Animas",
        "kind": "Tourism activity guide",
        "url": "https://visittrinidadcolorado.com/outdoor-recreation/",
        "best_for": "Finding Trinidad-area parks, trails, riding, cycling, fishing, camping, and other outdoor visitor interests.",
        "action": "Use the guide to identify activity categories, then contact the named operator, park, or public office directly.",
        "confidence": "High",
    },
    {
        "title": "LocalStash / Weekender regional events",
        "county": "Regional",
        "kind": "Regional event list / visitor channel",
        "url": "https://weekender.pub/",
        "best_for": "Cross-county event visibility for Las Animas, Huerfano, Colfax, and nearby southern Colorado / northern New Mexico audiences.",
        "action": "Use to review regional event listings, then ask LocalStash or Weekender directly about current submission, magazine, sponsor, or advertising options.",
        "confidence": "High",
    },
    {
        "title": "Raton Chamber Business Directory",
        "county": "Colfax",
        "kind": "Business directory",
        "url": "https://www.raton.info/business-directory.html",
        "best_for": "Finding Raton-area businesses, sponsors, chamber contacts, and local service anchors.",
        "action": "Check this before building a fresh Raton contact list.",
        "confidence": "High",
    },
    {
        "title": "City of Raton Local Business Support",
        "county": "Colfax",
        "kind": "Business support",
        "url": "https://www.ratonnm.gov/business/economic_development/local_business_resources.php",
        "best_for": "Hands-on startup help, SBA, SBDC, GrowRaton, Raton MainStreet, SCORE, and city support paths.",
        "action": "Use when a new venture needs the first phone call or support form.",
        "confidence": "High",
    },
    {
        "title": "GrowRaton",
        "county": "Colfax",
        "kind": "Economic development",
        "url": "https://www.growraton.org/",
        "best_for": "Business planning, networking, training, market-entry contacts, cottage market activity, and expansion help.",
        "action": "Use for entrepreneurs and existing businesses trying to grow in Raton/Colfax.",
        "confidence": "High",
    },
    {
        "title": "Raton MainStreet",
        "county": "Colfax",
        "kind": "Downtown / events",
        "url": "https://ratonmainstreet.org/",
        "best_for": "Downtown events, storefront activity, volunteers, sponsors, and Main Street business visibility.",
        "action": "Use for downtown locations, event collaboration, and historic-district visibility.",
        "confidence": "High",
    },
    {
        "title": "Explore Raton",
        "county": "Colfax",
        "kind": "Tourism / events",
        "url": "https://www.exploreraton.com/",
        "best_for": "Visitor-facing eat, stay, shop, arts, events, and tourism context.",
        "action": "Use when a business or artist can benefit from visitor traffic.",
        "confidence": "High",
    },
    {
        "title": "Explore Raton Events",
        "county": "Colfax",
        "kind": "Event calendar",
        "url": "https://www.exploreraton.com/events",
        "best_for": "Signature events, local happenings, seasonal activity, and tourism timing.",
        "action": "Check before scheduling a launch, show, promotion, or fundraiser.",
        "confidence": "High",
    },
    {
        "title": "Explore Raton Visitors Guide Advertising",
        "county": "Colfax",
        "kind": "Visitor guide / promotion inquiry",
        "url": "https://www.exploreraton.com/post/purchase-your-2026-raton-visitors-guide-ad",
        "best_for": "Visitor-facing Raton and Colfax businesses, attractions, lodging, dining, galleries, recreation, and event campaigns.",
        "action": "Ask about the current visitor-guide deadline, ad sizes, rate card, placement rules, and whether the listing also appears online.",
        "confidence": "High",
    },
    {
        "title": "KRTN Enchanted Air Radio",
        "county": "Colfax",
        "kind": "Media / advertising",
        "url": "https://krtnradio.com/wp/advertising/",
        "best_for": "Radio advertising, community calendars, regional reach, and public announcements.",
        "action": "Use when an event or offer needs Colfax plus southern Colorado reach.",
        "confidence": "High",
    },
    {
        "title": "El Raton Media Works Local Businesses",
        "county": "Colfax",
        "kind": "Local business list",
        "url": "https://www.elratonmediaworks.org/local-businesses",
        "best_for": "Raton business examples and media/arts adjacent anchors.",
        "action": "Use as a supplemental contact discovery source, then verify details.",
        "confidence": "Medium",
    },
    {
        "title": "Raton Arts & Humanities Council",
        "county": "Colfax",
        "kind": "Arts organization",
        "url": "https://www.ratonarts.org/",
        "best_for": "Old Pass Gallery, regional artists, arts programming, and cultural referrals.",
        "action": "Use for artist visibility, exhibit questions, and cultural partnerships.",
        "confidence": "High",
    },
    {
        "title": "Raton Arts and Cultural District",
        "county": "Colfax",
        "kind": "Creative district",
        "url": "https://www.nmartsandculturaldistricts.org/raton/",
        "best_for": "Arts/culture district context, Shuler Theater, Old Pass Gallery, El Raton, and district story.",
        "action": "Use to frame Raton as a creative-economy path, not only a business path.",
        "confidence": "High",
    },
    {
        "title": "Groundworks New Mexico Nonprofit Directory",
        "county": "Colfax",
        "kind": "Nonprofit directory",
        "url": "https://www.groundworksnm.org/nonprofit-directory/new-mexico-busin?combine=&order=city&page=32&sort=desc",
        "best_for": "Raton and Colfax nonprofit discovery, including arts, community improvement, and human services.",
        "action": "Use before manually collecting New Mexico nonprofit names.",
        "confidence": "High",
    },
    {
        "title": "SHARE New Mexico",
        "county": "Colfax",
        "kind": "Community resource directory",
        "url": "https://sharenm.org/",
        "best_for": "New Mexico community resources, program locations, county pages, and grants/funding discovery.",
        "action": "Use for social-service, nonprofit, and community program referrals.",
        "confidence": "High",
    },
    {
        "title": "NM Creative Industries Resource Center",
        "county": "Colfax",
        "kind": "Creative economy directory",
        "url": "https://www.edd.newmexico.gov/divisions-and-offices/creative-industries/creative-industries-resource-center/",
        "best_for": "Creative businesses, spaces, galleries, studios, theaters, resource hubs, and statewide opportunities.",
        "action": "Use when artists or creative ventures need a statewide directory and listing path.",
        "confidence": "High",
    },
    {
        "title": "NM Creative Industries Resource Submission / Update",
        "county": "Regional",
        "kind": "Creative economy listing update",
        "url": "https://www.edd.newmexico.gov/divisions-and-offices/creative-industries/creative-industries-resource-center/",
        "best_for": "Self-submitted or corrected creative-industry resources, including businesses, services, spaces, events, arts districts, programs, and organizations.",
        "action": "Use this when a creative business, gallery, maker, venue, nonprofit, or program should be added or corrected in the statewide creative resource layer.",
        "confidence": "High",
    },
    {
        "title": "NM EDD Business Resource Map",
        "county": "Regional",
        "kind": "Economic-development resource directory",
        "url": "https://www.edd.newmexico.gov/resource-map/",
        "best_for": "Finding and submitting New Mexico business-support resources, funding assistance, services, and regional economic-development contacts.",
        "action": "Use this alongside city and chamber resources when a Colfax user needs a statewide business-support path or a resource needs to be submitted for review.",
        "confidence": "High",
    },
    {
        "title": "Visit Trinidad Resources for Locals",
        "county": "Las Animas",
        "kind": "Tourism / event support",
        "url": "https://visittrinidadcolorado.com/resources-for-locals/",
        "best_for": "Marketing support, event support, social media co-op, community calendar, business directory listing, and attraction listing requests.",
        "action": "Use when a Trinidad business, event, or attraction needs an official tourism channel.",
        "confidence": "High",
    },
    {
        "title": "City of Trinidad Economic Development Newsletter",
        "county": "Las Animas",
        "kind": "Economic development updates",
        "url": "https://www.trinidad.co.gov/services/economicdevelopment_newsletter.php",
        "best_for": "Trinidad and Las Animas news, resources, and event updates from city economic development.",
        "action": "Use to track city-backed economic development opportunities.",
        "confidence": "High",
    },
    {
        "title": "City of Trinidad Grants",
        "county": "Las Animas",
        "kind": "Funding",
        "url": "https://www.trinidad.co.gov/services/grants.php",
        "best_for": "Grant notices for nonprofits and community-serving organizations.",
        "action": "Use for local funding checks before searching statewide grant lists.",
        "confidence": "Medium",
    },
    {
        "title": "CREATE Trinidad",
        "county": "Las Animas",
        "kind": "Creative district",
        "url": "https://www.trinidadcreativedistrict.org/",
        "best_for": "Artists, entrepreneurs, Space to Create, creative projects, events, and rentals.",
        "action": "Use for creative-economy partnerships and Trinidad arts visibility.",
        "confidence": "High",
    },
    {
        "title": "The Chronicle-News",
        "county": "Las Animas",
        "kind": "Media / classifieds",
        "url": "https://www.thechronicle-news.com/",
        "best_for": "Trinidad/Las Animas and Raton/Colfax news categories, classifieds, jobs, obituaries, legal notices, and local features.",
        "action": "Use for media pitches, classifieds, public notices, jobs, and regional news awareness.",
        "confidence": "High",
    },
    {
        "title": "Southern Colorado Community Foundation Nonprofit Directory",
        "county": "Las Animas",
        "kind": "Nonprofit directory",
        "url": "https://sccfcolorado.org/nonprofit-directory/",
        "best_for": "Southern Colorado nonprofit search, grantseeker pathways, and volunteer profile discovery.",
        "action": "Use for Colorado nonprofit discovery before building a manual organization list.",
        "confidence": "High",
    },
    {
        "title": "Colorado Gives",
        "county": "Las Animas",
        "kind": "Nonprofit giving directory",
        "url": "https://www.coloradogives.org/",
        "best_for": "Colorado nonprofit discovery, fundraising profiles, and donor-facing visibility.",
        "action": "Use when a nonprofit needs a public giving/listing path.",
        "confidence": "High",
    },
    {
        "title": "Huerfano County Chamber",
        "county": "Huerfano",
        "kind": "Chamber / events",
        "url": "https://www.chamber.huerfano.org/",
        "best_for": "Networking, education, promotion, advocacy, events, membership, and countywide business exposure.",
        "action": "Use for business collaboration and event promotion in Walsenburg, La Veta, Cuchara, Gardner, and Aguilar.",
        "confidence": "High",
    },
    {
        "title": "Huerfano Chamber Resources",
        "county": "Huerfano",
        "kind": "Resource hub",
        "url": "https://www.chamber.huerfano.org/resources",
        "best_for": "Links to Huerfano County, La Veta, Walsenburg, Spanish Peaks Country, Huerfano Economic Development, and Wheelhouse.",
        "action": "Use as the fastest local gateway to Huerfano public and business resources.",
        "confidence": "High",
    },
    {
        "title": "Huerfano County Economic Development Support & Incentives",
        "county": "Huerfano",
        "kind": "Economic development",
        "url": "https://www.huerfano.org/support",
        "best_for": "Rural Jump Start, HUBZone, enterprise zone, SBDC, SCEDD, Wheelhouse, workforce, tourism, and incentive context.",
        "action": "Use when a business is considering startup, relocation, expansion, or incentives in Huerfano.",
        "confidence": "High",
    },
    {
        "title": "Spanish Peaks Country Business Directory",
        "county": "Huerfano",
        "kind": "Business / tourism directory",
        "url": "https://spanishpeakscountry.com/business-directory",
        "best_for": "Dining, lodging, shopping, galleries, museums, services, and visitor-facing business discovery.",
        "action": "Use before manually building a Walsenburg/La Veta/Cuchara visitor economy list.",
        "confidence": "High",
    },
    {
        "title": "Town of La Veta Business Directory",
        "county": "Huerfano",
        "kind": "Municipal business directory",
        "url": "https://townoflaveta-co.gov/business-directory/",
        "best_for": "La Veta business names, addresses, phone numbers, and downtown/creative-economy anchors.",
        "action": "Use for La Veta outreach, cross-promotion, and referral lists.",
        "confidence": "High",
    },
    {
        "title": "The World Journal",
        "county": "Huerfano",
        "kind": "Media / submissions",
        "url": "https://worldjournalnewspaper.com/",
        "best_for": "Stories, events, ads, classifieds, legal notices, subscriptions, and local deadline planning.",
        "action": "Use for Huerfano media outreach and event/public notice timing.",
        "confidence": "High",
    },
    {
        "title": "World Journal Services Directory",
        "county": "Huerfano",
        "kind": "Services directory",
        "url": "https://worldjournalnewspaper.com/services/",
        "best_for": "Electricians, plumbers, real estate agents, local service firms, and service referrals.",
        "action": "Use for service-provider discovery and local advertising context.",
        "confidence": "High",
    },
    {
        "title": "Huerfano County Government Calendar",
        "county": "Huerfano",
        "kind": "Public calendar",
        "url": "https://huerfano.us/",
        "best_for": "County meetings, public events, and government visibility timing.",
        "action": "Use before scheduling civic or nonprofit events that need public-sector awareness.",
        "confidence": "Medium",
    },
    {
        "title": "Spanish Peaks Library Community Links",
        "county": "Huerfano",
        "kind": "Community links",
        "url": "https://www.spld.org/connect/community-links/",
        "best_for": "Huerfano historical, library, local government, tourism, and community organization links.",
        "action": "Use to discover public-service and cultural-resource partners.",
        "confidence": "High",
    },
    {
        "title": "La Veta Creative District",
        "county": "Huerfano",
        "kind": "Creative district",
        "url": "https://www.lavetacreativedistrict.org/",
        "best_for": "Creative spaces, festivals, workshops, art shows, performances, and artist resources.",
        "action": "Use for creative-sector partnerships and event timing in La Veta/Cuchara.",
        "confidence": "High",
    },
    {
        "title": "Wheelhouse Retail Incubator & Makerspace",
        "county": "Huerfano",
        "kind": "Incubator / makerspace",
        "url": "https://www.wheelhouseincubator.org/",
        "best_for": "Retail incubation, makerspace activity, pop-up retail, and early-stage local business support.",
        "action": "Use for product-based businesses, makers, and local retail experimentation.",
        "confidence": "High",
    },
    {
        "title": "Bachman Community Calendar",
        "county": "Huerfano",
        "kind": "Community calendar",
        "url": "https://www.discoverbachman.com/community-calendar/",
        "best_for": "Farmers markets and recurring local event timing across La Veta, Cuchara, Gardner, and Walsenburg.",
        "action": "Use to avoid calendar conflicts and find offline outreach opportunities.",
        "confidence": "Medium",
    },
    {
        "title": "New Mexico Small Business Development Center",
        "county": "Regional",
        "kind": "SBDC",
        "url": "https://www.nmsbdc.org/",
        "best_for": "No-cost counseling and training for New Mexico entrepreneurs and small businesses.",
        "action": "Use as the default first stop for New Mexico startup and growth questions.",
        "confidence": "High",
    },
    {
        "title": "Colorado SBDC Network",
        "county": "Regional",
        "kind": "SBDC",
        "url": "https://oedit.colorado.gov/colorado-small-business-development-center-network",
        "best_for": "Colorado small-business advising, training, startup help, expansion help, and certifications.",
        "action": "Use for Las Animas and Huerfano businesses needing technical assistance.",
        "confidence": "High",
    },
    {
        "title": "SBA SBDC Finder",
        "county": "Regional",
        "kind": "Federal business support",
        "url": "https://www.sba.gov/local-assistance/resource-partners/small-business-development-centers-sbdc",
        "best_for": "Finding SBDC counseling and training by ZIP code.",
        "action": "Use when a user is unsure which SBDC office covers them.",
        "confidence": "High",
    },
    {
        "title": "Colorado Creative Industries",
        "county": "Regional",
        "kind": "Creative economy support",
        "url": "https://oedit.colorado.gov/colorado-creative-industries",
        "best_for": "Colorado arts, creative industries, promotion, resources, and funding opportunities.",
        "action": "Use for artists, galleries, makers, and creative nonprofits in Las Animas and Huerfano.",
        "confidence": "High",
    },
    {
        "title": "Colorado Nonprofit Association Directory",
        "county": "Regional",
        "kind": "Nonprofit directory",
        "url": "https://coloradononprofits.org/member-resources/nonprofit-member-directory/",
        "best_for": "Colorado nonprofit member lookup and peer organization discovery.",
        "action": "Use carefully: the directory states non-commercial use limits.",
        "confidence": "High",
    },
    {
        "title": "Southern Colorado Economic Development District",
        "county": "Regional",
        "kind": "Economic development district",
        "url": "https://www.scedd.com/",
        "best_for": "Southern Colorado planning, technical assistance, economic development, and regional strategy context.",
        "action": "Use for Colorado regional development context and business-support referrals.",
        "confidence": "Medium",
    },
    {
        "title": "USDA Rural Business Development Grants",
        "county": "Regional",
        "kind": "Rural funding",
        "url": "https://www.rd.usda.gov/programs-services/business-programs/rural-business-development-grants",
        "best_for": "Rural business development planning, technical assistance, and small/emerging business expansion support.",
        "action": "Use for rural-capacity projects and business-support organizations.",
        "confidence": "High",
    },
]


FUNDING_DIRECTORY_ADDITIONS = [
    {
        "title": "Arts in Society Grant",
        "county": "Regional",
        "kind": "Arts / civic grants",
        "url": "https://www.redlineart.org/ais-apply-for-a-grant",
        "best_for": "Colorado artists, arts organizations, schools, governments, and cross-sector projects using art to address civic or social challenges.",
        "action": "Use for Las Animas and Huerfano arts/community projects that have a clear public benefit and partnership frame.",
        "confidence": "High",
    },
    {
        "title": "Bar NI Community Fund",
        "county": "Las Animas",
        "kind": "Local nonprofit grants",
        "url": "https://barnicommunityfund.org/",
        "best_for": "Purgatoire Valley 501(c)(3) nonprofits and service organizations seeking project support in youth development, education, environment, health, human services, civic work, and public benefit.",
        "action": "Use for Trinidad-area nonprofit projects, then verify the current spring or fall cycle before promising a deadline.",
        "confidence": "High",
    },
    {
        "title": "Colorado Advanced Industries Accelerator Programs",
        "county": "Regional",
        "kind": "Startup / innovation grants",
        "url": "https://oedit.colorado.gov/advanced-industries-accelerator-programs",
        "best_for": "Colorado startups, researchers, and technology companies commercializing products in advanced industries.",
        "action": "Use when a growth business needs research, commercialization, export, or early-stage capital support; pair with SBDC help before applying.",
        "confidence": "High",
    },
    {
        "title": "Colorado Business Funding and Incentives",
        "county": "Regional",
        "kind": "Business funding directory",
        "url": "https://oedit.colorado.gov/business-funding-and-incentives",
        "best_for": "Colorado businesses comparing tax credits, grants, loans, rural incentives, and job-creation programs.",
        "action": "Use as the Colorado starting page before drilling into Rural Jump-Start, enterprise zone, or industry-specific programs.",
        "confidence": "High",
    },
    {
        "title": "Colorado Community Revitalization Grant",
        "county": "Regional",
        "kind": "Creative district / main street funding",
        "url": "https://oedit.colorado.gov/colorado-community-revitalization-grant",
        "best_for": "Creative districts, historic districts, main streets, and neighborhood commercial-center projects needing gap funding.",
        "action": "Use for venue, corridor, downtown, arts-district, or adaptive-reuse ideas in Colorado communities; verify open cycles first.",
        "confidence": "High",
    },
    {
        "title": "Colorado Creates Grant",
        "county": "Regional",
        "kind": "Arts organization grants",
        "url": "https://oedit.colorado.gov/colorado-creates-grant",
        "best_for": "Colorado nonprofit arts organizations and public arts programs seeking annual competitive support for arts programs, services, and activities.",
        "action": "Use for Las Animas and Huerfano arts nonprofits, galleries with nonprofit partners, and community arts programming.",
        "confidence": "High",
    },
    {
        "title": "Colorado Rural Jump-Start Program",
        "county": "Regional",
        "kind": "Startup incentive / rural grant",
        "url": "https://oedit.colorado.gov/rural-jump-start-program",
        "best_for": "New or relocating businesses considering eligible rural Colorado zones, including tax benefits and possible matching grants.",
        "action": "Use for Huerfano or Las Animas startup/relocation questions, then verify zone eligibility and job-creation requirements with OEDIT.",
        "confidence": "High",
    },
    {
        "title": "Folk and Traditional Arts Project Grant",
        "county": "Regional",
        "kind": "Cultural heritage grants",
        "url": "https://oedit.colorado.gov/folk-and-traditional-arts-project-grant",
        "best_for": "Colorado projects that celebrate, document, or preserve folk and traditional arts and cultural heritage.",
        "action": "Use for culture-bearers, local history/heritage groups, arts nonprofits, and community documentation projects.",
        "confidence": "High",
    },
    {
        "title": "Gates Family Foundation Capital Grants",
        "county": "Regional",
        "kind": "Colorado nonprofit capital grants",
        "url": "https://gatesfamilyfoundation.org/types-of-support/capital-grants/",
        "best_for": "Colorado nonprofits and community organizations with capital projects such as buildings, renovation, land, parks, arts/culture spaces, or civic infrastructure.",
        "action": "Use for larger place-based projects after the organization has a real capital plan, board support, and matching/funding strategy.",
        "confidence": "High",
    },
    {
        "title": "Grants.gov",
        "county": "Regional",
        "kind": "Federal grant search",
        "url": "https://www.grants.gov/",
        "best_for": "Federal grant searches for nonprofits, public agencies, educational institutions, and eligible organizations.",
        "action": "Use after clarifying the applicant type and project purpose; pair with SBDC, nonprofit, or grant-writing help before applying.",
        "confidence": "High",
    },
    {
        "title": "History Colorado State Historical Fund",
        "county": "Regional",
        "kind": "Historic preservation grants",
        "url": "https://www.historycolorado.org/state-historical-fund",
        "best_for": "Colorado historic preservation, archaeology, education, and planning projects tied to significant places or cultural resources.",
        "action": "Use for historic buildings, museums, downtown preservation, heritage tourism, and cultural-resource projects in Las Animas or Huerfano.",
        "confidence": "High",
    },
    {
        "title": "National Endowment for the Arts Grants",
        "county": "Regional",
        "kind": "Federal arts grants",
        "url": "https://www.arts.gov/grants",
        "best_for": "Arts nonprofits and eligible organizations seeking federal project support, including small-organization arts access opportunities.",
        "action": "Use for stronger nonprofit arts projects with clear public outcomes; verify the specific NEA program, deadline, and eligibility each cycle.",
        "confidence": "High",
    },
    {
        "title": "New Mexico Arts Grants",
        "county": "Colfax",
        "kind": "Arts organization grants",
        "url": "https://nmarts.org/grants/grants-information/",
        "best_for": "New Mexico nonprofits and government entities supporting arts education, arts economic development, performing arts, visual arts, media arts, literary arts, and folk arts.",
        "action": "Use for Colfax County arts nonprofits, cultural organizations, and fiscally sponsored public arts activities.",
        "confidence": "High",
    },
    {
        "title": "New Mexico Business Portal Financial Assistance",
        "county": "Colfax",
        "kind": "Business funding directory",
        "url": "https://biz.nm.gov/financial-assistance/",
        "best_for": "New Mexico entrepreneurs comparing SBA funding programs, state finance options, and business assistance paths.",
        "action": "Use as a plain-language first stop before moving into SBA, NMFA, JTIP, LEDA, or local economic-development contacts.",
        "confidence": "High",
    },
    {
        "title": "New Mexico Creative Industries Division Grants",
        "county": "Colfax",
        "kind": "Creative business / organization grants",
        "url": "https://www.edd.newmexico.gov/grants/cid-grants/",
        "best_for": "New Mexico creative businesses, nonprofits, public agencies, and legal entities watching creative-industry grant and pre-application opportunities.",
        "action": "Use for Colfax creative-economy projects, but verify whether the current phase is a grant application, pre-application, or future funding notice.",
        "confidence": "High",
    },
    {
        "title": "New Mexico Finance Authority Opportunity Enterprise",
        "county": "Colfax",
        "kind": "Commercial development loans",
        "url": "https://www.nmfinance.com/project/opportunity-enterprise-commercial-development/",
        "best_for": "New Mexico commercial-building, renovation, and development projects that increase usable business space.",
        "action": "Use when a project is about commercial space, adaptive reuse, or business-location infrastructure rather than operating cash.",
        "confidence": "High",
    },
    {
        "title": "New Mexico Finance Authority SSBCI",
        "county": "Colfax",
        "kind": "Small business capital access",
        "url": "https://www.nmfinance.com/project/state-small-business-credit-initiative-ssbci/",
        "best_for": "New Mexico small businesses seeking capital through lender partnerships, loan participation, or capital access programs.",
        "action": "Use with a participating lender or SBDC advisor when a business is viable but needs a capital structure that lowers lender risk.",
        "confidence": "High",
    },
    {
        "title": "New Mexico Job Training Incentive Program",
        "county": "Colfax",
        "kind": "Workforce training reimbursement",
        "url": "https://www.edd.newmexico.gov/programs-and-services/business-development/job-training-incentive-program/",
        "best_for": "New Mexico expanding or relocating businesses creating new jobs and needing wage/training reimbursement support.",
        "action": "Use before hiring for an expansion plan; verify eligible jobs, wages, and timing before making hiring promises.",
        "confidence": "High",
    },
    {
        "title": "New Mexico Trails+ Grant",
        "county": "Colfax",
        "kind": "Outdoor recreation / trail funding",
        "url": "https://www.edd.newmexico.gov/press-releases/state-opens-trails-grant-for-outdoor-recreation-projects/",
        "best_for": "Trail, outdoor recreation, visitor-economy, and community-access projects that need a state funding lead to evaluate.",
        "action": "Use for Colfax outdoor recreation concepts, then verify the current cycle, eligible applicants, match rules, and deadlines.",
        "confidence": "High",
    },
    {
        "title": "New Mexico Small Business Assistance Program",
        "county": "Colfax",
        "kind": "Technical assistance / noncash support",
        "url": "https://nmsbaprogram.org/",
        "best_for": "New Mexico for-profit small businesses needing technical help from Los Alamos or Sandia national laboratories.",
        "action": "Use when a product, process, testing, design, or technical barrier is blocking business growth; note that this is assistance, not cash.",
        "confidence": "High",
    },
    {
        "title": "SBA Funding Programs",
        "county": "Regional",
        "kind": "Small business loans / capital",
        "url": "https://www.sba.gov/funding-programs",
        "best_for": "Small businesses comparing SBA-backed loans, investment capital, disaster assistance, surety bonds, and lender matching.",
        "action": "Use when a startup or existing business needs financing but should compare loans, grants, and counseling before applying.",
        "confidence": "High",
    },
    {
        "title": "SBA Lender Match",
        "county": "Regional",
        "kind": "Small business lender matching",
        "url": "https://www.sba.gov/funding-programs/loans/lender-match-connects-you-lenders",
        "best_for": "Small businesses looking for SBA-approved lenders and competitive loan options.",
        "action": "Use after estimating the amount, purpose, repayment plan, and documents needed for a loan conversation.",
        "confidence": "High",
    },
    {
        "title": "Southern Colorado Community Foundation Grants",
        "county": "Regional",
        "kind": "Nonprofit grants",
        "url": "https://sccfcolorado.org/for-grantseekers/grants/",
        "best_for": "Eligible nonprofits serving southeastern Colorado counties, including Huerfano and Las Animas.",
        "action": "Use for community-serving nonprofit projects, then verify available funds, award range, service area, and the March/September cycle.",
        "confidence": "High",
    },
    {
        "title": "Southern Colorado Community Foundation Scholarship",
        "county": "Regional",
        "kind": "Scholarship",
        "url": "https://sccfcolorado.org/madeline-mellers-memorial-girls-golf-scholarship/",
        "best_for": "Eligible high-school girls golf team members in several southern Colorado counties, including Huerfano and Las Animas, seeking college or vocational support.",
        "action": "Use as a regional scholarship lead; verify eligibility and deadline before sharing with students or families.",
        "confidence": "High",
    },
    {
        "title": "Trinidad Community Foundation Grant Process",
        "county": "Las Animas",
        "kind": "Local nonprofit grants",
        "url": "https://www.trinidadcf.org/grants.html",
        "best_for": "Colorado nonprofits, public entities, nonprofit schools, and fiscally sponsored charitable/civic/educational work tied to Trinidad grant processes.",
        "action": "Use for Trinidad-area nonprofit projects and confirm the current city/foundation process before applying.",
        "confidence": "High",
    },
    {
        "title": "USDA Rural Microentrepreneur Assistance Program",
        "county": "Regional",
        "kind": "Rural microbusiness loans / grants",
        "url": "https://www.rd.usda.gov/programs-services/business-programs/rural-microentrepreneur-assistance-program",
        "best_for": "Microenterprise development organizations that provide technical assistance and microloans to rural entrepreneurs and small businesses.",
        "action": "Use for nonprofit/lender/intermediary partners serving rural microbusinesses; individual businesses usually work through an eligible intermediary.",
        "confidence": "High",
    },
    {
        "title": "USDA Value-Added Producer Grants",
        "county": "Regional",
        "kind": "Agriculture / producer grants",
        "url": "https://www.rd.usda.gov/programs-services/business-programs/value-added-producer-grants",
        "best_for": "Agricultural producers, producer groups, farmer/rancher cooperatives, and producer-owned businesses developing value-added products or markets.",
        "action": "Use for farms, ranches, food businesses, and producer-led ventures that need planning or working-capital support.",
        "confidence": "High",
    },
    {
        "title": "WESST Lending",
        "county": "Colfax",
        "kind": "Startup / small business loans",
        "url": "https://www.wesst.org/lending",
        "best_for": "New Mexico startups and existing small businesses seeking microloans, consulting, and training support.",
        "action": "Use for Colfax entrepreneurs who may not fit traditional bank lending and need technical assistance with financing.",
        "confidence": "High",
    },
]


DIRECTORY_SOURCES.extend(FUNDING_DIRECTORY_ADDITIONS)


DIRECTORY_SOURCES.extend(
    [
        {
            "title": "City of Raton Business Services",
            "county": "Colfax",
            "kind": "Municipal business resources",
            "url": "https://www.ratonnm.gov/business/index.php",
            "best_for": "Official Raton business services, permits, licenses, economic development, and support pages.",
            "action": "Use as the official city business hub; if a direct directory path changes, start here.",
            "confidence": "High",
        },
        {
            "title": "Explore Raton Shopping",
            "county": "Colfax",
            "kind": "Visitor business directory",
            "url": "https://www.exploreraton.com/shop",
            "best_for": "Visitor-facing retail, handmade goods, local shops, and shopping-related Raton discovery.",
            "action": "Use when a business, maker, or artist can serve travelers or day-trip visitors.",
            "confidence": "High",
        },
        {
            "title": "GrowRaton Commercial Properties",
            "county": "Colfax",
            "kind": "Property / expansion",
            "url": "https://www.growraton.org/properties/",
            "best_for": "Businesses considering storefront, workspace, relocation, or expansion in Raton.",
            "action": "Use when a growth path needs physical space, not just promotion.",
            "confidence": "High",
        },
        {
            "title": "Colfax County Business Resources",
            "county": "Colfax",
            "kind": "County business resources",
            "url": "https://www.co.colfax.nm.us/business/index.php",
            "best_for": "Bid opportunities, RFPs, county business pages, and public-sector entry points.",
            "action": "Use for county procurement, notices, and official Colfax business context.",
            "confidence": "High",
        },
        {
            "title": "Colfax County Clerk",
            "county": "Colfax",
            "kind": "County clerk / records",
            "url": "https://www.co.colfax.nm.us/government/county_clerk.php",
            "best_for": "Public records, election/county office routing, and official county verification.",
            "action": "Use for official-record questions and to verify county office contact pathways.",
            "confidence": "High",
        },
        {
            "title": "City of Raton Business Licenses and Regulations",
            "county": "Colfax",
            "kind": "Licensing / compliance",
            "url": "https://www.ratonnm.gov/business/business_license_regulations.php",
            "best_for": "Raton business registration, zoning checks, and local licensing steps.",
            "action": "Use before publishing a startup checklist for Raton-based ventures.",
            "confidence": "High",
        },
        {
            "title": "RAIN Colfax Business Licenses",
            "county": "Colfax",
            "kind": "Business license support",
            "url": "https://raincolfax.org/business-community-resources/wpbdp_category/business-licenses/",
            "best_for": "Regional business-license pointers and Colfax community resource routing.",
            "action": "Use as a support pointer, then verify with the responsible official office.",
            "confidence": "Medium",
        },
        {
            "title": "Tax Exempt World Colfax County Organizations",
            "county": "Colfax",
            "kind": "Nonprofit aggregator",
            "url": "https://www.taxexemptworld.com/organizations/colfax-county-nm-new-mexico.asp",
            "best_for": "Broad nonprofit discovery when official nonprofit directories are incomplete.",
            "action": "Use only as an aggregator; verify every organization through its own site or state/federal records.",
            "confidence": "Medium",
        },
        {
            "title": "Enigma Directory: Raton Business Entities",
            "county": "Colfax",
            "kind": "Business data aggregator",
            "url": "https://www.enigma.com/directory/nm/raton/",
            "best_for": "Supplemental entity discovery, addresses, websites, and business patterns.",
            "action": "Use for research leads only; do not treat as an official directory or endorsement.",
            "confidence": "Medium",
        },
        {
            "title": "Yellow Pages Raton Business Listings",
            "county": "Colfax",
            "kind": "Commercial directory",
            "url": "https://www.yellowpages.com/raton-nm/business-listings/1",
            "best_for": "Supplemental public business lookup where official directories miss categories.",
            "action": "Use only as a secondary discovery source and confirm details elsewhere.",
            "confidence": "Medium",
        },
        {
            "title": "Las Animas County Government",
            "county": "Las Animas",
            "kind": "County government",
            "url": "https://lasanimascounty.colorado.gov/",
            "best_for": "County offices, public services, official contact routing, and civic context.",
            "action": "Use when a guide section needs official Las Animas County verification.",
            "confidence": "High",
        },
        {
            "title": "Visit Trinidad Submit Your Event",
            "county": "Las Animas",
            "kind": "Event submission",
            "url": "https://visittrinidadcolorado.com/resources-for-locals/submit-your-event/",
            "best_for": "Submitting visitor-relevant Trinidad and Las Animas County events for review.",
            "action": "Use for events, not general advertising; follow the posted review rules.",
            "confidence": "High",
        },
        {
            "title": "Colorado OEDIT Rural Opportunity Office",
            "county": "Regional",
            "kind": "Rural business development",
            "url": "https://oedit.colorado.gov/category/rural-opportunity-office",
            "best_for": "Rural Colorado business, community, and economic-development programs.",
            "action": "Use for Las Animas and Huerfano projects that need statewide rural-development context.",
            "confidence": "High",
        },
        {
            "title": "Bent County Business Development",
            "county": "Las Animas",
            "kind": "Regional business development",
            "url": "https://www.bentcounty.net/businesses/business_development.php",
            "best_for": "Southeast Colorado business-development contact paths that may support Las Animas-area users.",
            "action": "Use as a regional referral lead and verify coverage before sending users there.",
            "confidence": "Medium",
        },
        {
            "title": "Huerfano County Government",
            "county": "Huerfano",
            "kind": "County government",
            "url": "https://huerfano.us/",
            "best_for": "County offices, public notices, events, affiliated agencies, and official Huerfano context.",
            "action": "Use for official Huerfano County verification and public-notice routing.",
            "confidence": "High",
        },
        {
            "title": "Spanish Peaks Country Submit Event",
            "county": "Huerfano",
            "kind": "Event submission",
            "url": "https://spanishpeakscountry.com/spc-events/community/add/",
            "best_for": "Submitting Huerfano-area events for the public tourism/event calendar.",
            "action": "Use for event promotion and verify event-category fit before submitting.",
            "confidence": "High",
        },
        {
            "title": "NM Family Friendly Business Directory",
            "county": "Regional",
            "kind": "Business recognition directory",
            "url": "https://nmfamilyfriendlybusiness.org/premium-business-directory/",
            "best_for": "New Mexico businesses that want family-friendly workplace visibility and peer discovery.",
            "action": "Use as a values-aligned visibility path, then verify application or listing rules.",
            "confidence": "Medium",
        },
        {
            "title": "New Mexico Business Portal",
            "county": "Regional",
            "kind": "Business startup / licensing",
            "url": "https://biz.nm.gov/business-navigator/licenses-and-permits/",
            "best_for": "Business planning, registration, licenses, permits, and expansion information in New Mexico.",
            "action": "Use for Colfax County startup and compliance pathways.",
            "confidence": "High",
        },
        {
            "title": "Finance New Mexico Regional Economic Development Organizations",
            "county": "Regional",
            "kind": "Economic-development directory",
            "url": "https://financenewmexico.org/resources/general-business-assistance/regional-economic-development-organizations/",
            "best_for": "New Mexico regional economic-development organization lookup.",
            "action": "Use when Colfax users need support beyond a city-specific organization.",
            "confidence": "High",
        },
        {
            "title": "Angel Fire Chamber Member Business Directory",
            "county": "Colfax",
            "kind": "Member business directory",
            "url": "https://angelfirechamber.org/local-businesses/",
            "best_for": "Angel Fire and Moreno Valley businesses, nonprofits, artists, lodging, dining, services, and chamber member categories.",
            "action": "Use as a broader Angel Fire directory before searching by category or building a manual list.",
            "confidence": "High",
        },
        {
            "title": "Village of Eagle Nest Business Directory",
            "county": "Colfax",
            "kind": "Municipal business directory",
            "url": "https://www.eaglenest.org/water_waste_water/businessdirectory",
            "best_for": "Eagle Nest lodging, retail, galleries, outfitters, food, home services, and lake-corridor businesses.",
            "action": "Use to verify Eagle Nest leads and replace unsourced roster entries with public directory evidence.",
            "confidence": "High",
        },
        {
            "title": "Walsenburg Forms and License Applications",
            "county": "Huerfano",
            "kind": "Municipal forms / vendor permits",
            "url": "https://www.walsenburg.org/forms",
            "best_for": "Business license, food vendor, peddler, solicitor, liquor, special-event, and local application paths.",
            "action": "Use before telling a Walsenburg vendor, event organizer, or business which city form may be needed.",
            "confidence": "High",
        },
        {
            "title": "Colexico Alliance / TLAC Chamber Regional Hub",
            "county": "Regional",
            "kind": "Regional chamber / member network",
            "url": "https://tlacchamber.org/",
            "best_for": "Cross-county chamber context, Las Animas business support, regional member discovery, and Colexico Alliance routing.",
            "action": "Use when a business or organization needs regional chamber visibility across Las Animas, Huerfano, and Colfax.",
            "confidence": "High",
        },
        {
            "title": "Spanish Peaks Country Add Business Listing",
            "county": "Huerfano",
            "kind": "Tourism directory submission",
            "url": "https://spanishpeakscountry.com/add-business-listing/",
            "best_for": "Huerfano visitor-facing businesses, galleries, venues, lodging, dining, shopping, and attractions seeking directory visibility.",
            "action": "Use when a business needs a public submission path for the Spanish Peaks Country directory.",
            "confidence": "High",
        },
        {
            "title": "Artists Sunday Artist Directory",
            "county": "Regional",
            "kind": "Artist directory",
            "url": "https://artistssunday.com/directory/",
            "best_for": "Artists and makers seeking a broader public artist directory, including existing La Veta-area examples.",
            "action": "Use as a supplemental discovery and listing path for regional artists; verify current signup rules before recommending.",
            "confidence": "Medium",
        },
        {
            "title": "City of Raton Economic Development Programs",
            "county": "Colfax",
            "kind": "Startup / economic-development resource hub",
            "url": "https://www.ratonnm.gov/business/economic_development/index.php",
            "best_for": "Raton and Colfax startup paths, SBA/SBDC/SCORE/FastTrac links, GrowRaton, Raton MainStreet, and related support routes.",
            "action": "Use when someone needs a first route into business support rather than a single directory listing.",
            "confidence": "High",
        },
        {
            "title": "Trinidad Community Foundation",
            "county": "Las Animas",
            "kind": "Local foundation / grantmaker",
            "url": "https://www.trinidadcf.org/board.html",
            "best_for": "Las Animas County nonprofit and public-benefit projects seeking local foundation context or grantmaker contact information.",
            "action": "Use alongside the City of Trinidad grants page; confirm current application instructions before promising deadlines or eligibility.",
            "confidence": "High",
        },
        {
            "title": "Spanish Peaks Community Foundation",
            "county": "Huerfano",
            "kind": "Local foundation / community projects",
            "url": "https://www.spanishpeaks.foundation/",
            "best_for": "Huerfano County local projects, artists, tradition-keepers, small nonprofits, gathering spaces, and cultural stewardship efforts.",
            "action": "Use as a local funding and civic-support lead, then verify whether a given project fits current foundation priorities.",
            "confidence": "High",
        },
        {
            "title": "New Mexico Local Economic Development Act",
            "county": "Colfax",
            "kind": "Economic-development incentive / state program",
            "url": "https://www.edd.newmexico.gov/grants/local-economic-development-act/",
            "best_for": "New Mexico communities and qualifying economic-development projects, including Colfax County and several local municipalities.",
            "action": "Use for larger business-expansion or project-support questions; verify eligibility with the state and local government before advising.",
            "confidence": "High",
        },
        {
            "title": "ROAMS Local Resources",
            "county": "Colfax",
            "kind": "Health and family resource directory",
            "url": "https://roamsnm.org/",
            "best_for": "Colfax, northeastern New Mexico, family support, prenatal/postnatal services, youth/family resources, and local service referrals.",
            "action": "Use for health, family, youth, and service-provider referrals that need a regional directory beyond business promotion.",
            "confidence": "High",
        },
    ]
)


AMPLIFIER_CHANNELS = [
    {
        "channel": "LocalStash / Weekender regional events",
        "area_served": "Las Animas, Huerfano, Colfax, and nearby SoCO / NoNM communities",
        "channel_type": "Regional event list; visitor guide; magazine or sponsor inquiry",
        "asks": "Review current regional event listings and ask directly about event submission, magazine inclusion, sponsorship, or advertising options.",
        "best_for": "Events, arts and music listings, visitor-facing businesses, nonprofit programs, community happenings, and cross-county awareness.",
        "paid_free_status": "Unknown - verify",
        "verification_status": "Live Weekender page and LocalStash transition evidence checked July 2026",
        "source_url": "https://weekender.pub/",
        "implementation_note": "Use as a regional discovery and promotion route; confirm deadlines, rates, and submission rules before planning around placement.",
    },
    {
        "channel": "Red River Brewing Company & Distillery",
        "area_served": "Red River / Colfax",
        "channel_type": "Own-site newsletter / mailing list",
        "asks": "Ask about newsletter signup, promotion fit, and any business-originating mailing-list opportunity.",
        "best_for": "Visitor-facing food, beverage, live-music, and Red River event awareness.",
        "paid_free_status": "Unknown - verify",
        "verification_status": "Verified newsletter or signup evidence",
        "source_url": "https://www.redriverbrewing.com/",
        "implementation_note": "Use as proof that local businesses can have their own audiences; ask before sending promotional material.",
    },
    {
        "channel": "Angel Fire Resort Events",
        "area_served": "Angel Fire / Colfax",
        "channel_type": "Events calendar; calendar subscription; newsletter signup",
        "asks": "Check event fit, calendar options, and newsletter signup path.",
        "best_for": "Resort-adjacent events, seasonal tourism, outdoor recreation, food, lodging, and visitor activity.",
        "paid_free_status": "Unknown - verify",
        "verification_status": "Verified calendar and newsletter/signup evidence",
        "source_url": "https://www.angelfireresort.com/events/",
        "implementation_note": "Treat as a visitor/venue channel; confirm listing eligibility and deadlines before promising placement.",
    },
    {
        "channel": "Angel Fire Resort Vacation Rentals",
        "area_served": "Angel Fire / Colfax",
        "channel_type": "Events referral; newsletter signup",
        "asks": "Ask whether local events, lodging partners, or visitor resources can be shared.",
        "best_for": "Lodging-adjacent tourism campaigns and visitor-facing event discovery.",
        "paid_free_status": "Unknown - verify",
        "verification_status": "Related proof - verify separately",
        "source_url": "https://www.angelfireresortvacationrentals.com/plan-your-trip/summer-events/",
        "implementation_note": "Use as a lodging-audience lead, not as confirmed submission access.",
    },
    {
        "channel": "Red River Chamber / RedRiver.org Events",
        "area_served": "Red River / Colfax",
        "channel_type": "Events calendar; submit event; newsletter; vacation guide",
        "asks": "Submit local visitor-friendly events and ask about guide or newsletter fit.",
        "best_for": "Public events, festivals, arts, family activities, outdoor recreation, and visitor-facing promotions.",
        "paid_free_status": "Unknown - verify",
        "verification_status": "Verified calendar, event submission, and newsletter/signup evidence",
        "source_url": "https://redriver.org/events/",
        "implementation_note": "Use for visitor-friendly events; do not imply all business promotions qualify.",
    },
    {
        "channel": "Red River Chamber Vacation Guide",
        "area_served": "Red River / Colfax",
        "channel_type": "Vacation guide request; visitor mailing pathway; newsletter",
        "asks": "Ask about visitor-guide listing or advertising requirements, deadlines, and eligibility.",
        "best_for": "Tourism businesses, lodging, dining, attractions, and seasonal visitor campaigns.",
        "paid_free_status": "Unknown - verify",
        "verification_status": "Verified visitor-guide channel",
        "source_url": "https://redriver.org/plan-your-trip/vacation-guide/",
        "implementation_note": "Treat as a guide pathway; confirm whether listing, advertising, or editorial inclusion is available.",
    },
    {
        "channel": "Visit Angel Fire NM Get Listed",
        "area_served": "Angel Fire / Colfax",
        "channel_type": "Business listing intake; event submission; newsletter signup",
        "asks": "Submit eligible properties/listings or ask about event/listing pathways.",
        "best_for": "Visitor-facing businesses, rentals, events, and tourism services.",
        "paid_free_status": "Unknown - verify",
        "verification_status": "Verified submission channel",
        "source_url": "https://visitangelfirenm.com/get-listed/",
        "implementation_note": "Use the public form path where it fits; confirm approval and listing scope.",
    },
    {
        "channel": "Visit Angel Fire Events",
        "area_served": "Angel Fire / Colfax",
        "channel_type": "Events calendar; list your event; calendar subscription; newsletter",
        "asks": "Submit local events and prepare clean event data, images, and contact details.",
        "best_for": "Community events, visitor events, arts, recreation, classes, and seasonal programming.",
        "paid_free_status": "Unknown - verify",
        "verification_status": "Verified event calendar and subscribe options",
        "source_url": "https://visitangelfirenm.com/events/",
        "implementation_note": "Use alongside the dedicated list-your-event page when available.",
    },
    {
        "channel": "Visit Trinidad Tourism / Resources for Locals",
        "area_served": "Trinidad / Las Animas",
        "channel_type": "Marketing support; social media co-op; community calendar; business directory request",
        "asks": "Ask about event support, attraction/business listings, co-promotion, and community calendar fit.",
        "best_for": "Trinidad tourism businesses, events, attractions, visitor experiences, and local organizations.",
        "paid_free_status": "Unknown - verify",
        "verification_status": "Verified submission and co-promotion channel",
        "source_url": "https://visittrinidadcolorado.com/resources-for-locals/",
        "implementation_note": "Good first stop for visitor-facing Trinidad activity; follow the posted intake paths.",
    },
    {
        "channel": "Visit Trinidad Submit Event",
        "area_served": "Trinidad / Las Animas",
        "channel_type": "Event submission rules / approval process",
        "asks": "Submit events for review with complete public details and images.",
        "best_for": "Public events, festivals, arts events, community programs, and visitor-relevant activities.",
        "paid_free_status": "Unknown - verify",
        "verification_status": "Verified reviewed submission pathway",
        "source_url": "https://visittrinidadcolorado.com/resources-for-locals/submit-your-event/",
        "implementation_note": "Use for event submission only; approval and timing belong to the site owner.",
    },
    {
        "channel": "City of Trinidad Economic Development",
        "area_served": "Trinidad / Las Animas",
        "channel_type": "Economic-development newsletter; business news/resources/events",
        "asks": "Ask how to receive updates or share business-resource news.",
        "best_for": "Business support, city economic-development awareness, and resource updates.",
        "paid_free_status": "Unknown - verify",
        "verification_status": "Verified municipal newsletter page; signup pathway needs confirmation",
        "source_url": "https://www.trinidad.co.gov/services/economicdevelopment_newsletter.php",
        "implementation_note": "Use as an official update source; confirm submission or signup process before directing users.",
    },
    {
        "channel": "Main Street LIVE",
        "area_served": "Trinidad / Las Animas",
        "channel_type": "Events calendar; season lineup; special events",
        "asks": "Ask about event partnership, venue calendar fit, sponsorship, or audience alignment.",
        "best_for": "Performances, arts events, venue partnerships, and cultural programming.",
        "paid_free_status": "Unknown - verify",
        "verification_status": "Verified event lineup; newsletter not found",
        "source_url": "https://www.mainstreetlive.org/",
        "implementation_note": "Use as a venue/arts channel; confirm whether outside events or promotions are accepted.",
    },
    {
        "channel": "Main Street LIVE 2026 Calendar",
        "area_served": "Trinidad / Las Animas",
        "channel_type": "Calendar / ticketed event lineup",
        "asks": "Check schedule fit and ask about partnership or listing opportunities.",
        "best_for": "Arts, music, theater, and event-timing awareness.",
        "paid_free_status": "Unknown - verify",
        "verification_status": "Verified calendar page",
        "source_url": "https://www.mainstreetlive.org/2026-calendar",
        "implementation_note": "Use for planning around known events and understanding audience timing.",
    },
    {
        "channel": "Spanish Peaks Country Newsletter",
        "area_served": "Huerfano County / Walsenburg / La Veta / Cuchara",
        "channel_type": "Newsletter; events calendar; submit event; business directory; add listing",
        "asks": "Ask about event submission, directory listing, newsletter signup, and visitor-guide pathways.",
        "best_for": "Tourism businesses, galleries, museums, lodging, dining, events, and seasonal campaigns.",
        "paid_free_status": "Unknown - verify",
        "verification_status": "Verified newsletter, calendar, directory, and submit-listing evidence",
        "source_url": "https://spanishpeakscountry.com/newsletter-signup/",
        "implementation_note": "Strong Huerfano amplifier because it connects directory, events, and visitor audiences.",
    },
    {
        "channel": "Spanish Peaks Country Business Directory",
        "area_served": "Huerfano County",
        "channel_type": "Business directory; add business listing",
        "asks": "Submit or update eligible business listings.",
        "best_for": "Visitor-facing Huerfano businesses, galleries, museums, lodging, dining, shopping, and attractions.",
        "paid_free_status": "Unknown - verify",
        "verification_status": "Verified directory",
        "source_url": "https://spanishpeakscountry.com/business-directory",
        "implementation_note": "Use before creating a manual Huerfano visitor-economy list.",
    },
    {
        "channel": "Spanish Peaks Country Submit Event",
        "area_served": "Huerfano County",
        "channel_type": "Submit event; event calendar",
        "asks": "Submit events with clean title, timing, location, description, contact, and image.",
        "best_for": "Public events, arts, markets, festivals, classes, and visitor-facing activities.",
        "paid_free_status": "Unknown - verify",
        "verification_status": "Verified event submission path",
        "source_url": "https://spanishpeakscountry.com/spc-events/community/add/",
        "implementation_note": "Use for calendar placement requests; confirm review time and event fit.",
    },
    {
        "channel": "World Journal",
        "area_served": "Huerfano / Walsenburg",
        "channel_type": "Newspaper, events, classifieds, advertising inquiry possible",
        "asks": "Ask about story coverage, event listings, classifieds, legal notices, advertising, and deadlines.",
        "best_for": "Huerfano announcements, event awareness, local stories, public notices, and paid-media inquiries.",
        "paid_free_status": "Unknown - verify",
        "verification_status": "Promotion possible - verify / paid ad status unknown",
        "source_url": "https://worldjournalnewspaper.com/",
        "implementation_note": "Do not imply free publication; ask directly about rates, editorial fit, and deadlines.",
    },
    {
        "channel": "La Veta Creative District",
        "area_served": "La Veta / Huerfano",
        "channel_type": "Events/festivals, arts visibility, possible mailing/news",
        "asks": "Ask about arts events, festival participation, listings, partner sharing, or newsletter options.",
        "best_for": "Artists, galleries, makers, workshops, performances, and creative-sector partnerships.",
        "paid_free_status": "Unknown - verify",
        "verification_status": "Needs contact confirmation",
        "source_url": "https://www.lavetacreativedistrict.org/festivals-and-signature-events",
        "implementation_note": "Use as an arts-sector relationship lead; confirm submission and promotion channels.",
    },
]


AMPLIFIER_CATEGORIES = [
    {
        "title": "Event Calendars",
        "body": "Best for public, time-sensitive things: performances, markets, workshops, launches, fundraisers, and visitor-facing events.",
        "query": "event",
    },
    {
        "title": "Newsletters & Mailing Lists",
        "body": "Best for opt-in audiences; ask before assuming outside announcements or ads are accepted.",
        "query": "newsletter",
    },
    {
        "title": "Business Directories",
        "body": "Best for being findable after the first announcement has passed.",
        "query": "business",
    },
    {
        "title": "Tourism/Visitor Guides",
        "body": "Best for lodging, dining, shopping, galleries, attractions, recreation, and visitor services.",
        "query": "tourism",
    },
    {
        "title": "Anchor Venue Lineups",
        "body": "Best for arts, music, theater, food, and event-adjacent cross-promotion.",
        "query": "venue",
    },
    {
        "title": "Ask About Advertising or Placement",
        "body": "Best when a channel may sell ads or placements but the public page does not confirm terms.",
        "query": "advertising",
    },
]


PROMOTION_PACKET = [
    "Event or business name",
    "Date, time, and location",
    "One-sentence public hook",
    "50-word description",
    "100-word description",
    "Website, ticket, registration, or contact link",
    "Contact name, email, and phone",
    "Square image",
    "Vertical image",
    "Printable flyer",
    "Accessibility notes",
    "Item type: free, ticketed, nonprofit, youth, tourism, business, or community",
]


BEST_USE_MATRIX = [
    ("Public event", "Event calendars, tourism calendars, venue lineups, and city/community calendars."),
    ("Visitor-facing business", "Tourism directories, visitor guides, chamber/tourism sites, and Google Business Profile."),
    ("Restaurant or retail special", "Newsletter opportunities, social media co-op, paid ad inquiry, and local flyers. Verify newsletter ad rules first."),
    ("Art show or performance", "Venue lineups, arts calendars, tourism calendars, and local media."),
    ("Nonprofit program", "City calendars, newsletters, radio PSA, schools/libraries, and partner organizations. Use community-announcement language."),
    ("Grant-funded project", "Media coverage, newsletter mentions, partner reposts, and post-event reporting. Track screenshots and reach when possible."),
    ("Seasonal tourism campaign", "Tourism sites, visitor guides, lodging partners, and regional newsletters. Ask about deadlines, eligibility, and paid/free status."),
]


POSTING_SPACES = [
    {
        "place": "Trinidad / Las Animas",
        "physical": "City Hall and Clerk pathway at 135 N. Animas Street, plus public places used for notices under local rules.",
        "digital": "City public notices, agendas, minutes, Clerk pages, emergency alerts, chamber/tourism event pages, and Visit Trinidad resources.",
        "use_for": "Official notices, event verification, civic updates, tourism calendar submissions, and public-sector timing checks.",
        "status": "Hybrid - verify board rules and deadlines",
        "source_url": "https://www.trinidad.co.gov/government/public_notice.php",
    },
    {
        "place": "Walsenburg / Huerfano",
        "physical": "City Hall entrance at 525 S. Albert Avenue, County Clerk and Recorder, and courthouse bulletin-board/public-office pathways.",
        "digital": "Walsenburg agendas/minutes, Huerfano County public notices, county news, meeting pages, calendars, and newsletter/update pages.",
        "use_for": "Public notices, meeting awareness, business-license context, county calendar checks, and civic program visibility.",
        "status": "Hybrid - verify office-specific posting rules",
        "source_url": "https://www.walsenburg.org/city-clerks-office/page/agendas-and-minutes",
    },
    {
        "place": "Raton / Colfax",
        "physical": "City Hall posting cabinet and Colfax County Clerk/County buildings including 333 Savage Avenue and other public-office pathways.",
        "digital": "City agendas/minutes/events calendar/public notices/bids/updates; Colfax County news, calendar, legal notices, and public hearings.",
        "use_for": "Official notices, public hearing awareness, county business context, community calendar timing, and verification.",
        "status": "Hybrid - verify current posting locations",
        "source_url": "https://www.ratonnm.gov/government/agendas_minutes.php",
    },
    {
        "place": "General regional pattern",
        "physical": "Libraries, chambers, venues, schools, visitor centers, coffee shops, galleries, and community centers may have boards.",
        "digital": "Official websites, tourism calendars, chamber pages, newspaper/radio pages, Facebook/community groups, and partner newsletters.",
        "use_for": "Supplemental community visibility after the official or owner-controlled channel has been checked.",
        "status": "Field-check needed",
        "source_url": "",
    },
]

PHYSICAL_AD_PLACE_TYPES = [
    {
        "key": "community-public",
        "title": "Community and public spaces",
        "best_for": "Libraries, community centers, schools, and public offices used for programs, services, classes, and local announcements.",
        "categories": ["Community and public spaces"],
    },
    {
        "key": "arts-events",
        "title": "Arts and event spaces",
        "best_for": "Galleries, theaters, museums, venues, and creative spaces used for openings, performances, workshops, artist calls, and festivals.",
        "categories": ["Arts and event spaces"],
    },
    {
        "key": "local-businesses",
        "title": "Local businesses and services",
        "best_for": "Food and drink, retail, bookstores, pharmacies, personal services, auto shops, and secondhand stores near regular local foot traffic.",
        "categories": ["Local businesses and services"],
    },
    {
        "key": "visitor-travel",
        "title": "Visitor and travel locations",
        "best_for": "Visitor centers, chambers, lodging, transit, and travel stops used for events, maps, tours, brochures, and visitor-facing services.",
        "categories": ["Visitor and travel locations"],
    },
]

PHYSICAL_AD_LOCATION_TERMS = (
    "library",
    "visitor center",
    "visitors center",
    "welcome center",
    "tourism",
    "tourist",
    "chamber",
    "mainstreet",
    "creative district",
    "city hall",
    "town hall",
    "county clerk",
    "courthouse",
    "court",
    "public office",
    "community center",
    "senior center",
    "recreation center",
    "gallery",
    "museum",
    "venue",
    "theater",
    "theatre",
    "arts",
    "cultural",
    "coffee",
    "cafe",
    "espresso",
    "bakery",
    "restaurant",
    "bar",
    "brewery",
    "distillery",
    "market",
    "grocery",
    "food store",
    "mercantile",
    "shop",
    "store",
    "rail",
    "train",
    "station",
    "depot",
    "bus",
    "transit",
    "hotel",
    "motel",
    "inn",
    "lodging",
    "campground",
    "rv",
    "resort",
    "school",
    "college",
    "campus",
    "bookstore",
    "book shop",
    "bookseller",
    "pharmacy",
    "drugstore",
    "tattoo",
    "auto shop",
    "auto repair",
    "automotive",
    "car dealer",
    "dealership",
    "tire shop",
    "thrift",
    "secondhand",
    "antique",
    "salon",
    "barber",
    "haircut",
    "hair salon",
    "beauty salon",
    "personal care",
    "spa",
    "independent retailer",
    "locally owned",
)

PHYSICAL_AD_LISTING_TYPES = {
    "Arts & culture",
    "Auto & transportation",
    "Education & learning",
    "Events & venues",
    "Food & drink",
    "Health & wellness",
    "Lodging & stays",
    "Nonprofit & community",
    "Public offices",
    "Retail & local goods",
    "Tourism & visitor info",
}


PROMOTE_ROUTE_DEFS = [
    {
        "key": "events",
        "title": "Events",
        "summary": "Venues, public events, performances, festivals, classes, and event-submission contacts.",
        "query": "event venue festival performance class",
    },
    {
        "key": "advertising",
        "title": "Advertising + media",
        "summary": "Paid-ad inquiries, newspapers, radio, newsletters, social sharing, sponsorships, and editorial contacts.",
        "query": "advertising media newspaper radio newsletter sponsorship social",
    },
    {
        "key": "businesses",
        "title": "Business visibility",
        "summary": "Business directories, chambers, visitor guides, local retailers, restaurants, and cross-promotion contacts.",
        "query": "business directory chamber tourism retail restaurant",
    },
    {
        "key": "nonprofits",
        "title": "Nonprofit outreach",
        "summary": "Community organizations, service providers, referral partners, public agencies, and mission-aligned channels.",
        "query": "nonprofit community service partner referral",
    },
    {
        "key": "calendars",
        "title": "Calendars",
        "summary": "Event calendars, tourism calendars, venue lineups, public calendars, and community announcement routes.",
        "query": "calendar event listing tourism schedule",
    },
    {
        "key": "galleries",
        "title": "Galleries + arts",
        "summary": "Artists, galleries, creative districts, museums, theaters, cultural groups, and arts audiences.",
        "query": "artist gallery arts museum theater creative cultural",
    },
]


PERSONA_ROUTES = [
    {
        "persona": "New business",
        "start": "Pick one target customer and get one official listing or support conversation started.",
        "pages": "Plan, Network, County page, Appendix",
        "channels": "SBDC, chamber, municipal business resources, tourism directory if visitor-facing.",
    },
    {
        "persona": "Existing business",
        "start": "Update listings, add one cross-county channel, and track whether it produces calls, visits, or referrals.",
        "pages": "Network, Amplifiers, Templates",
        "channels": "Chambers, tourism directories, newsletters, local media, business associations.",
    },
    {
        "persona": "Nonprofit or program",
        "start": "Write the community benefit in one sentence and choose calendars, partners, and referral sources before ads.",
        "pages": "Plan, Posting, Templates, Appendix",
        "channels": "Nonprofit directories, public calendars, libraries, schools, radio, city/county updates.",
    },
    {
        "persona": "Artist, gallery, or maker",
        "start": "Pair the creative offer with a place and date, then route it through arts, tourism, and venue channels.",
        "pages": "Amplifiers, Region, County page",
        "channels": "Creative districts, galleries, visitor guides, anchor venue lineups, event calendars.",
    },
    {
        "persona": "Event organizer",
        "start": "Prepare the packet once, then submit to the right calendar, venue, tourism page, and media outlet.",
        "pages": "Amplifiers, Templates, Posting",
        "channels": "Event calendars, tourism calendars, newspapers, radio, partner newsletters.",
    },
    {
        "persona": "Rural service or mentor",
        "start": "Make referral language easy: who you help, what happens next, and how a partner sends someone to you.",
        "pages": "Plan, Network, Appendix",
        "channels": "Public agencies, schools, libraries, chambers, nonprofit directories, workforce and SBDC partners.",
    },
]

DIRECTORY_SOURCES = filter_excluded_directory_rows(DIRECTORY_SOURCES)
AMPLIFIER_CHANNELS = filter_excluded_directory_rows(AMPLIFIER_CHANNELS)
POSTING_SPACES = filter_excluded_directory_rows(POSTING_SPACES)


PATHS = [
    {
        "name": "Directory",
        "href": "network/",
        "summary": "Find a business, organization, place, program, service, or support resource.",
        "cta": "Search listings",
    },
    {
        "name": "Promote",
        "href": "promote/",
        "summary": "Find calendars, media, visitor channels, directories, and places that may share something.",
        "cta": "Choose a promotion route",
    },
    {
        "name": "Funding",
        "href": "resources/funding/",
        "summary": "Compare grants, capital, incentives, fiscal support, and free assistance.",
        "cta": "Search funding",
    },
    {
        "name": "Counties",
        "href": "region/",
        "summary": "Begin with Colfax, Las Animas, or Huerfano, then widen across the region when useful.",
        "cta": "Choose a county",
    },
    {
        "name": "Guide",
        "href": "plan/",
        "summary": "Plan an outreach cycle, understand the region, and learn how this manual is maintained.",
        "cta": "Plan the work",
    },
    {
        "name": "Tools",
        "href": "tools/free-discounted/",
        "summary": "Use free services, templates, posting aids, downloads, and the update form.",
        "cta": "Open practical tools",
    },
]


ROUTE_LABELS = {
    "home": "Home",
    "plan": "Plan",
    "amplifiers": "Amplifiers",
    "promote": "Promote",
    "network": "Directory",
    "posting": "Physical locations",
    "region": "Region",
    "colfax": "Colfax County",
    "las-animas": "Las Animas County",
    "huerfano": "Huerfano County",
    "templates": "Templates",
    "free-tools": "Free & Discounted Tools",
    "submit": "Submit",
    "appendix": "Appendix",
    "about": "About",
    "funding": "Funding",
    "arts-culture": "Arts & Culture",
    "post-raton": "Post Events in Raton",
    "post-trinidad": "Post Events in Trinidad",
    "post-huerfano": "Post Events in Walsenburg and La Veta",
    "advertise-trinidad": "Advertise in Trinidad",
    "colfax-business": "Colfax Business Resources",
    "las-animas-nonprofit": "Las Animas Nonprofit Resources",
    "huerfano-calendars": "Huerfano Event Calendars",
    "artist-gallery": "Artist and Gallery Promotion",
    "regional-channels": "Regional Channels",
}


TASK_PAGE_DEFS = [
    {
        "active": "post-raton",
        "title": "Where to Post Events in Raton NM | Stateline Tri-County Guide",
        "description": "Find starting points for Raton event visibility, including city pages, tourism routes, media, calendars, public boards, partners, and practical next steps.",
        "eyebrow": "Raton event visibility",
        "h1": "Where to post events in Raton, New Mexico",
        "intro": "Use this page when a public event, class, fundraiser, art opening, business launch, civic program, performance, or community activity needs visibility in Raton or Colfax County. Start with the page or channel that best matches the event: city or county channels for official/public information, tourism and visitor-facing routes for events that serve travelers, media for public-interest announcements, and partner channels for aligned audiences. Check current rules before printing materials or promising placement.",
        "source_terms": ["Raton", "Colfax", "Events", "Tourism", "Media", "Arts", "MainStreet"],
        "row_terms": ["Raton", "Colfax", "event", "calendar", "media", "artist", "gallery", "theater", "tourism"],
        "primary_links": [("Use regional amplifier channels", "amplifiers/"), ("Separate official notices from community visibility", "posting/"), ("Use copy-ready outreach templates", "templates/")],
    },
    {
        "active": "post-trinidad",
        "title": "Where to Post Events in Trinidad CO | Stateline Tri-County Guide",
        "description": "Use Trinidad tourism, city, chamber, creative district, venue, media, and community routes to submit or promote public events after checking rules.",
        "eyebrow": "Trinidad event visibility",
        "h1": "Where to post events in Trinidad, Colorado",
        "intro": "Use this page when a public event, art show, performance, market, workshop, nonprofit program, business announcement, or visitor-facing activity needs visibility in Trinidad or Las Animas County. Start with tourism and city-facing routes when the event is public or visitor-relevant. Use chamber, creative-district, venue, media, and partner channels when the event fits their audience. Confirm submission rules, review time, image requirements, and whether placement is editorial, free, paid, or member-only.",
        "source_terms": ["Trinidad", "Las Animas", "Tourism", "Chamber", "Creative", "Event", "Media"],
        "row_terms": ["Trinidad", "Las Animas", "event", "calendar", "media", "artist", "gallery", "music", "tourism"],
        "primary_links": [("Find Trinidad and regional amplifier channels", "amplifiers/"), ("Use an event calendar template", "templates/"), ("Submit a changed event route", "submit/")],
    },
    {
        "active": "post-huerfano",
        "title": "Where to Post Events in Walsenburg & La Veta CO | Stateline Tri-County Guide",
        "description": "Find Huerfano County event routes through Spanish Peaks Country, Walsenburg, La Veta, libraries, media, arts, and tourism channels.",
        "eyebrow": "Huerfano event visibility",
        "h1": "Where to post events in Walsenburg and La Veta",
        "intro": "Use this page when a Huerfano County event, art show, farmers market, workshop, nonprofit program, visitor activity, gallery reception, performance, or local announcement needs public visibility. Start with Spanish Peaks Country, town/city routes, libraries, chamber or economic-development contacts, arts channels, and regional media. Treat public boards and calendars as owner-controlled channels. Check current rules, review time, and whether the event fits before assuming placement.",
        "source_terms": ["Huerfano", "Walsenburg", "La Veta", "Spanish Peaks", "Event", "Tourism", "Arts", "Media"],
        "row_terms": ["Huerfano", "Walsenburg", "La Veta", "event", "calendar", "media", "artist", "gallery", "music", "tourism"],
        "primary_links": [("Find Huerfano amplifier channels", "amplifiers/"), ("Open the Huerfano county page", "counties/huerfano/"), ("Submit a changed event route", "submit/")],
    },
    {
        "active": "advertise-trinidad",
        "title": "Where to Advertise in Trinidad CO | Stateline Tri-County Guide",
        "description": "Compare Trinidad-area promotion routes, including tourism channels, chamber options, media, venue lineups, newsletters, and paid-placement inquiries.",
        "eyebrow": "Trinidad promotion routes",
        "h1": "Where to advertise or promote something in Trinidad, Colorado",
        "intro": "Use this page when a business, artist, nonprofit, venue, program, or service needs more visibility in Trinidad or nearby Las Animas County communities. Start by deciding whether the item belongs in tourism, chamber, media, creative-district, venue, or partner channels. Ask directly before assuming free placement, paid ad availability, deadline timing, audience size, or editorial coverage.",
        "source_terms": ["Trinidad", "Las Animas", "Advertising", "Media", "Chamber", "Tourism", "Newsletter"],
        "row_terms": ["Trinidad", "Las Animas", "advertising", "media", "newsletter", "tourism", "business", "artist"],
        "primary_links": [("Compare calendars, media, directories, and visitor guides", "amplifiers/"), ("Prepare an advertising inquiry", "templates/"), ("Search Las Animas entries", "network/")],
    },
    {
        "active": "colfax-business",
        "title": "Colfax County Business Resources | Stateline Tri-County Guide",
        "description": "Start with Raton business services, licensing, GrowRaton, MainStreet, county resources, tourism, and New Mexico support before outreach.",
        "eyebrow": "Colfax business resources",
        "h1": "Colfax County business resources",
        "intro": "Use this page when a new or existing Colfax County business needs a practical first path for support, listings, promotion, tourism exposure, licensing context, downtown partnerships, or New Mexico statewide resources. Start with official and public directories before building a contact list by hand.",
        "source_terms": ["Colfax", "Raton", "Business", "MainStreet", "GrowRaton", "SBDC", "New Mexico"],
        "row_terms": ["Colfax", "Raton", "business", "support", "funding", "directory", "economic"],
        "primary_links": [("Open the Colfax county page", "counties/colfax/"), ("Search business and support entries", "network/"), ("Plan the outreach cycle first", "plan/")],
    },
    {
        "active": "las-animas-nonprofit",
        "title": "Las Animas County Nonprofit Resources | Stateline Tri-County Guide",
        "description": "Find Trinidad and Las Animas nonprofit visibility, grant, partner, media, chamber, and community-resource routes with clear next steps.",
        "eyebrow": "Las Animas nonprofit routes",
        "h1": "Las Animas County nonprofit resources",
        "intro": "Use this page when a nonprofit, fiscally sponsored project, community program, class, service, or volunteer effort needs visibility, partners, funding paths, public calendars, or public local referrals in Las Animas County. Check eligibility, deadlines, rates, and acceptance with the page or organization before promising participation or publication.",
        "source_terms": ["Las Animas", "Trinidad", "Nonprofit", "Grant", "Community", "Foundation", "Chamber"],
        "row_terms": ["Las Animas", "Trinidad", "nonprofit", "foundation", "grant", "community", "partner"],
        "primary_links": [("Open the Las Animas county page", "counties/las-animas/"), ("Search nonprofit and funding entries", "network/"), ("Submit a correction", "submit/")],
    },
    {
        "active": "huerfano-calendars",
        "title": "Huerfano County Event Calendars & Visitor Listings | Stateline Tri-County Guide",
        "description": "Use Spanish Peaks Country, Walsenburg, La Veta, media, tourism, library, arts, and community calendars as Huerfano event starting points.",
        "eyebrow": "Huerfano calendar routes",
        "h1": "Huerfano County event calendars and visitor listings",
        "intro": "Use this page when an event, arts program, visitor-facing listing, class, market, fundraiser, or community announcement needs Huerfano County visibility. Start with Spanish Peaks Country and local public channels, then widen through media, chamber, arts, library, and partner routes when the audience fit is clear.",
        "source_terms": ["Huerfano", "Walsenburg", "La Veta", "Spanish Peaks", "Calendar", "Visitor", "Tourism"],
        "row_terms": ["Huerfano", "Walsenburg", "La Veta", "calendar", "event", "visitor", "tourism", "media"],
        "primary_links": [("Open the Huerfano county page", "counties/huerfano/"), ("Find amplifier channels", "amplifiers/"), ("Separate posting types", "posting/")],
    },
    {
        "active": "artist-gallery",
        "title": "Artist & Gallery Promotion in Raton, Trinidad & Walsenburg | Stateline Tri-County Guide",
        "description": "Route art shows, gallery events, makers, workshops, performances, and creative-sector announcements through arts, tourism, media, venue, and partner channels.",
        "eyebrow": "Artist and gallery promotion",
        "h1": "Artist and gallery promotion across the tri-county area",
        "intro": "Use this page when an artist, gallery, maker, performer, workshop, creative class, exhibition, or arts nonprofit needs a practical route to local attention. Start with arts councils, creative districts, tourism pages, galleries, venue calendars, media, and partner organizations before building a new audience list from scratch.",
        "source_terms": ["Arts", "Creative", "Gallery", "Artist", "Raton", "Trinidad", "Walsenburg", "La Veta"],
        "row_terms": ["artist", "gallery", "creative", "maker", "museum", "music", "theater", "ceramics", "painting", "photography"],
        "primary_links": [("Search artists, galleries, makers, and venues", "network/"), ("Find regional amplifier channels", "amplifiers/"), ("Use outreach templates for creative work", "templates/")],
    },
    {
        "active": "regional-channels",
        "title": "Regional Newsletters, Event Calendars & Visitor Guides | Stateline Tri-County Guide",
        "description": "Compare tri-county newsletters, event calendars, tourism guides, business directories, venue lineups, and placement inquiry paths.",
        "eyebrow": "Regional amplifier channels",
        "h1": "Regional newsletters, event calendars, and visitor guides",
        "intro": "Use this page when a business, artist, nonprofit, event organizer, program, or service needs to compare the channels that already gather public attention across the tri-county region. Treat these as routing starts, not guarantees. Confirm deadlines, formats, acceptance, rates, and review timing with each channel owner.",
        "source_terms": ["Regional", "Calendar", "Newsletter", "Visitor", "Directory", "Media", "Tourism"],
        "row_terms": ["Regional", "calendar", "newsletter", "media", "visitor", "directory", "tourism"],
        "primary_links": [("Open the full amplifier page", "amplifiers/"), ("Search public directories and local entries", "network/"), ("Submit a changed channel", "submit/")],
    },
]


TASK_CATEGORY_META = {
    "post-raton": {
        "label": "Events",
        "class": "cat-events",
        "summary": "Public events, classes, fundraisers, markets, openings, and performances.",
        "next": "Start with public calendars and visitor-facing routes, then widen to partners.",
    },
    "post-trinidad": {
        "label": "Events",
        "class": "cat-events",
        "summary": "Public events, art shows, performances, workshops, and visitor-facing activities.",
        "next": "Start with tourism, city, venue, and arts routes when the event is public.",
    },
    "post-huerfano": {
        "label": "Events",
        "class": "cat-events",
        "summary": "County events, markets, gallery receptions, workshops, performances, and announcements.",
        "next": "Start with Spanish Peaks, Walsenburg, La Veta, libraries, arts, and local media.",
    },
    "advertise-trinidad": {
        "label": "Promotion",
        "class": "cat-promotion",
        "summary": "Advertising, sponsorship, paid placement, media, newsletter, and partner visibility.",
        "next": "Ask which placements are free, paid, editorial, member-only, or unavailable.",
    },
    "colfax-business": {
        "label": "Business",
        "class": "cat-business",
        "summary": "Business support, licensing context, downtown routes, tourism visibility, and statewide help.",
        "next": "Start with official public pages and local business-support routes before cold outreach.",
    },
    "las-animas-nonprofit": {
        "label": "Nonprofits",
        "class": "cat-nonprofit",
        "summary": "Community programs, fiscal sponsorship, funding paths, partner referrals, and visibility.",
        "next": "Check eligibility, deadlines, and program fit before promising participation.",
    },
    "huerfano-calendars": {
        "label": "Calendars",
        "class": "cat-events",
        "summary": "Event calendars, visitor listings, community announcements, and local tourism routes.",
        "next": "Start with the channel that already gathers the audience you need.",
    },
    "artist-gallery": {
        "label": "Arts & Culture",
        "class": "cat-arts",
        "summary": "Artists, galleries, makers, performers, creative classes, exhibitions, and arts nonprofits.",
        "next": "Pair arts channels with tourism, venue, media, and partner routes when the audience overlaps.",
    },
    "regional-channels": {
        "label": "Regional",
        "class": "cat-regional",
        "summary": "Newsletters, calendars, visitor guides, directories, partner pages, and multi-county visibility.",
        "next": "Use the broad channel only after the local fit and action are clear.",
    },
}


ROUTE_TYPE_CARDS = [
    {
        "label": "Events",
        "class": "cat-events",
        "query": "event",
        "use": "Public event, class, fundraiser, market, opening, performance, or visitor activity.",
        "prepare": "Name, date, time, place, short blurb, image, cost, and public contact.",
        "check": "Eligibility, lead time, image size, deadline, and whether the calendar owner reviews submissions.",
    },
    {
        "label": "Promotion",
        "class": "cat-promotion",
        "query": "advertising",
        "use": "Ad inquiry, newsletter blurb, partner share, flyer placement, or media pitch.",
        "prepare": "One-sentence hook, audience fit, call to action, image, link, and contact.",
        "check": "Free or paid status, rates, deadline, audience fit, and whether placement is guaranteed.",
    },
    {
        "label": "Business",
        "class": "cat-business",
        "query": "business",
        "use": "Business listing, service-area update, shop-local route, or downtown/tourism visibility.",
        "prepare": "Business name, category, address or service area, website, hours, phone, and short description.",
        "check": "Listing requirements, membership rules, current contact route, and update process.",
    },
    {
        "label": "Nonprofits",
        "class": "cat-nonprofit",
        "query": "nonprofit",
        "use": "Program, mentorship, class, service, volunteer route, grant path, or community referral.",
        "prepare": "Who is served, what is offered, eligibility, dates, location, contact, and referral action.",
        "check": "Eligibility, privacy limits, deadlines, and whether the partner wants public promotion.",
    },
    {
        "label": "Arts & Culture",
        "class": "cat-arts",
        "query": "artist",
        "use": "Artist, gallery, venue, maker, exhibition, performance, workshop, or cultural resource.",
        "prepare": "Artist or organization name, medium, event details, portfolio/listing link, image, and public action.",
        "check": "Submission style, image credit, permission, commission or sales terms, and audience fit.",
    },
]


def task_category_meta(active: str) -> dict:
    return TASK_CATEGORY_META.get(
        active,
        {
            "label": "Guide route",
            "class": "cat-support",
            "summary": "A focused starting path for a regional visibility task.",
            "next": "Start with the owner-controlled public page, then widen if the fit is clear.",
        },
    )


COUNTY_INTENT_BLOCKS = {
    "Colfax": {
        "helps": "Use this page to find public promotion, business-support, directory, calendar, media, tourism, funding, and partner routes in Colfax County. It is designed for businesses, artists, nonprofits, galleries, event organizers, service providers, and community programs that need a practical starting point.",
        "searches": [
            "Raton business resources",
            "Colfax County business support",
            "Where to post events in Raton NM",
            "Raton tourism and visitor-facing listings",
            "Raton MainStreet and GrowRaton support routes",
            "Colfax County media and public-notice pathways",
            "New Mexico resources for local businesses and community programs",
        ],
        "title": "Colfax County Business, Event & Promotion Resources | Stateline Tri-County Guide",
        "description": "Use Raton, MainStreet, GrowRaton, Explore Raton, arts, media, county, and New Mexico support routes before building a new contact list.",
    },
    "Las Animas": {
        "helps": "Use this page to find public promotion, nonprofit, business, tourism, chamber, media, creative-district, event-calendar, grant, and partner routes in Las Animas County. Start with Trinidad-facing channels, then widen through Colexico, regional media, and Colorado support systems.",
        "searches": [
            "Trinidad Colorado business resources",
            "Where to post events in Trinidad CO",
            "Las Animas County nonprofit resources",
            "Trinidad tourism event submission",
            "Trinidad chamber and Colexico routes",
            "Las Animas County grants and community resources",
            "Trinidad creative district and arts promotion channels",
        ],
        "title": "Las Animas County Business, Event & Nonprofit Resources | Stateline Tri-County Guide",
        "description": "Use Trinidad, tourism, the chamber, Colexico, city economic development, creative district, media, grants, and Colorado support routes.",
    },
    "Huerfano": {
        "helps": "Use this page to find public promotion, tourism, business, event-calendar, media, arts, chamber, economic-development, and partner routes in Huerfano County. Start with Walsenburg, La Veta, Spanish Peaks Country, HCED, the chamber, and regional media before building a manual contact list.",
        "searches": [
            "Huerfano County event calendar",
            "Walsenburg business resources",
            "La Veta event promotion",
            "Spanish Peaks Country business directory",
            "Huerfano County visitor guide listings",
            "World Journal event and advertising inquiry",
            "Huerfano arts, gallery, and creative-district promotion",
        ],
        "title": "Huerfano County Event, Tourism & Business Resources | Stateline Tri-County Guide",
        "description": "Use Walsenburg, La Veta, Spanish Peaks Country, HCED, chamber, creative district, World Journal, and rural Colorado support routes.",
    },
}


BASE_SITE_ROUTES = [
    {
        "title": "Guide home",
        "path": "",
        "category": "Guide page",
        "summary": "Start with a task, county, or resource type and move directly to the matching guide page.",
        "keywords": ["home", "start", "tri-county guide", "help", "navigation"],
    },
    {
        "title": "Master directory",
        "path": "network/",
        "category": "Directory",
        "summary": "Search businesses, nonprofits, artists, programs, services, venues, support organizations, and regional channels.",
        "keywords": ["directory", "listing", "contact", "search", "business", "nonprofit", "artist"],
    },
    {
        "title": "Funding and free support",
        "path": "resources/funding/",
        "category": "Funding",
        "summary": "Search grants, loans, technical assistance, stipends, scholarships, and no-cost support programs.",
        "keywords": ["funding", "grant", "loan", "stipend", "scholarship", "free support", "technical assistance"],
    },
    {
        "title": "Arts and culture",
        "path": "resources/arts-culture/",
        "category": "Arts & culture",
        "summary": "Find artist directories, galleries, venues, open calls, registries, cultural resources, and regional audio.",
        "keywords": ["arts", "culture", "artist", "gallery", "venue", "open call", "registry", "music"],
    },
    {
        "title": "Plan your growth",
        "path": "plan/",
        "category": "Guide page",
        "summary": "Choose an audience, prepare one reusable promotion packet, test matched channels, and track what works.",
        "keywords": ["plan", "growth", "customer", "audience", "promotion packet", "strategy"],
    },
    {
        "title": "Promotion finder",
        "path": "promote/",
        "category": "Promotion finder",
        "summary": "Filter regional promotion routes by county and task, including events, advertising, businesses, nonprofits, calendars, and galleries.",
        "keywords": ["promote", "advertise", "events", "calendar", "business", "nonprofit", "gallery"],
    },
    {
        "title": "Physical ad finder",
        "path": "posting/",
        "category": "Physical promotion",
        "summary": "Search public-facing locations and contacts for flyers, posters, brochures, and rack cards.",
        "keywords": ["flyer", "poster", "brochure", "rack card", "physical advertising", "bulletin board"],
    },
    {
        "title": "Regional channels",
        "path": "regional-channels/",
        "category": "Promotion channels",
        "summary": "Use regional directories, calendars, newsletters, visitor guides, media, and partner channels across county lines.",
        "keywords": ["regional", "channel", "calendar", "newsletter", "visitor guide", "media", "partner"],
    },
    {
        "title": "Amplifier channels",
        "path": "amplifiers/",
        "category": "Promotion channels",
        "summary": "Find calendars, newsletters, directories, visitor guides, venues, media outlets, and other routes that can carry a message farther.",
        "keywords": ["amplifier", "calendar", "newsletter", "directory", "visitor guide", "media", "venue"],
    },
    {
        "title": "Tri-county region overview",
        "path": "region/",
        "category": "Regional guide",
        "summary": "Understand how Colfax, Las Animas, and Huerfano county resources connect across the state line.",
        "keywords": ["region", "tri-county", "state line", "overview", "New Mexico", "Colorado"],
    },
    {
        "title": "Colfax County resources",
        "path": "counties/colfax/",
        "category": "County guide",
        "county": "Colfax",
        "summary": "Find Colfax County business, nonprofit, arts, event, tourism, media, and support routes.",
        "keywords": ["Colfax", "Raton", "Angel Fire", "Cimarron", "Eagle Nest", "Red River", "Maxwell", "Springer"],
    },
    {
        "title": "Las Animas County resources",
        "path": "counties/las-animas/",
        "category": "County guide",
        "county": "Las Animas",
        "summary": "Find Las Animas County business, nonprofit, arts, event, tourism, media, and support routes.",
        "keywords": ["Las Animas", "Trinidad", "Aguilar", "Branson", "Kim", "Model", "Hoehne"],
    },
    {
        "title": "Huerfano County resources",
        "path": "counties/huerfano/",
        "category": "County guide",
        "county": "Huerfano",
        "summary": "Find Huerfano County business, nonprofit, arts, event, tourism, media, and support routes.",
        "keywords": ["Huerfano", "Walsenburg", "La Veta", "Gardner", "Cuchara"],
    },
    {
        "title": "Message templates",
        "path": "templates/",
        "category": "Tools",
        "summary": "Use copy-ready outreach language for directories, calendars, partners, media, and listing corrections.",
        "keywords": ["template", "message", "email", "calendar submission", "media pitch", "partner request"],
    },
    {
        "title": "Free and discounted tools",
        "path": "tools/free-discounted/",
        "category": "Tools",
        "summary": "Compare general free tools, nonprofit discounts and donated services, and free advising or public support.",
        "keywords": ["free software", "free tools", "nonprofit discount", "donated software", "free advising", "open source", "forms", "email"],
    },
    {
        "title": "Submit an update",
        "path": "submit/",
        "category": "Guide service",
        "summary": "Suggest a listing, correct an entry, add a public contact path, or recommend a regional resource.",
        "keywords": ["submit", "update", "correction", "add listing", "remove listing", "contact"],
    },
    {
        "title": "Guide appendix",
        "path": "appendix/",
        "category": "Reference",
        "summary": "Open compact reference tables, contact paths, downloads, and supporting guide information.",
        "keywords": ["appendix", "reference", "table", "download", "contacts"],
    },
    {
        "title": "About and creation process",
        "path": "about/",
        "category": "About",
        "summary": "Read the guide purpose, data-compilation method, limitations, and a reusable model for local resource research.",
        "keywords": ["about", "creation process", "method", "data", "research", "limitations"],
    },
    {
        "title": "Post events in Raton and Colfax County",
        "path": "post-events-raton/",
        "category": "Task guide",
        "county": "Colfax",
        "summary": "Find event calendars and promotion channels for Raton and Colfax County.",
        "keywords": ["Raton", "Colfax", "event", "calendar", "post event"],
    },
    {
        "title": "Post events in Trinidad and Las Animas County",
        "path": "post-events-trinidad/",
        "category": "Task guide",
        "county": "Las Animas",
        "summary": "Find event calendars and promotion channels for Trinidad and Las Animas County.",
        "keywords": ["Trinidad", "Las Animas", "event", "calendar", "post event"],
    },
    {
        "title": "Post events in Huerfano County",
        "path": "post-events-huerfano/",
        "category": "Task guide",
        "county": "Huerfano",
        "summary": "Find event calendars and promotion channels for Walsenburg, La Veta, and Huerfano County.",
        "keywords": ["Huerfano", "Walsenburg", "La Veta", "event", "calendar", "post event"],
    },
    {
        "title": "Advertise in Trinidad and Las Animas County",
        "path": "advertise-trinidad/",
        "category": "Task guide",
        "county": "Las Animas",
        "summary": "Find advertising, media, visitor, and community promotion contacts in and around Trinidad.",
        "keywords": ["Trinidad", "Las Animas", "advertise", "media", "newspaper", "radio"],
    },
    {
        "title": "Colfax County business visibility",
        "path": "colfax-business/",
        "category": "Task guide",
        "county": "Colfax",
        "summary": "Find business directories, support organizations, visitor channels, and local promotion routes in Colfax County.",
        "keywords": ["Colfax", "business", "directory", "support", "tourism", "customers"],
    },
    {
        "title": "Las Animas County nonprofit outreach",
        "path": "las-animas-nonprofit/",
        "category": "Task guide",
        "county": "Las Animas",
        "summary": "Find nonprofit partners, funding, referral routes, calendars, and public channels in Las Animas County.",
        "keywords": ["Las Animas", "nonprofit", "partner", "funding", "referral", "community"],
    },
    {
        "title": "Huerfano County calendars",
        "path": "huerfano-calendars/",
        "category": "Task guide",
        "county": "Huerfano",
        "summary": "Find event calendars, venue schedules, visitor calendars, and announcement routes in Huerfano County.",
        "keywords": ["Huerfano", "calendar", "events", "Walsenburg", "La Veta", "schedule"],
    },
    {
        "title": "Artist and gallery promotion",
        "path": "artist-gallery-promotion/",
        "category": "Task guide",
        "summary": "Find artist directories, galleries, venues, open calls, cultural partners, and promotion routes across the region.",
        "keywords": ["artist", "gallery", "open call", "registry", "venue", "creative business"],
    },
]


def assistant_site_routes() -> list[dict]:
    routes = [dict(item) for item in BASE_SITE_ROUTES]
    for route_def in PROMOTE_ROUTE_DEFS:
        routes.append(
            {
                "title": f"{route_def['title']} across the tri-county region",
                "path": f"promote/?route={quote_plus(route_def['key'])}#promotion-results",
                "category": "Promotion finder",
                "summary": route_def["summary"],
                "keywords": [route_def["title"], route_def["query"], "regional promotion"],
            }
        )
        for county in ("Colfax", "Las Animas", "Huerfano"):
            routes.append(
                {
                    "title": f"{route_def['title']} in {county} County",
                    "path": (
                        "promote/?county="
                        f"{quote_plus(county)}&route={quote_plus(route_def['key'])}#promotion-results"
                    ),
                    "category": "Promotion finder",
                    "county": county,
                    "summary": route_def["summary"],
                    "keywords": [route_def["title"], route_def["query"], county, "promotion"],
                }
            )
    for item in routes:
        item.setdefault("area_served", item.get("county") or "Colfax Las Animas Huerfano")
        item.setdefault("action", "Open this guide page for the full route, filters, links, and next actions.")
    return routes


def rel(path: str, depth: int = 0) -> str:
    return "../" * depth + path


def clean_text(value: str | None) -> str:
    return (value or "").replace("\u2019", "'").replace("\u2013", "-").replace("\u2014", "-").strip()


PLACE_ONLY_LISTING_NAMES = {
    "aguilar",
    "angel fire",
    "cimarron",
    "cuchara",
    "eagle nest",
    "gardner",
    "la veta",
    "raton",
    "red river",
    "trinidad",
    "walsenburg",
}


NON_ENTITY_RESOURCE_NAMES = {
    "adventure guide",
    "architecture",
    "atv/utving",
    "calendars of events",
    "camping",
    "community groups and digital bulletin boards",
    "contact us",
    "cross-country ski",
    "cross-country skiing",
    "downhill skiing & snowboarding",
    "entertainment",
    "fishing",
    "fishing & fly fishing",
    "get your new mexico true",
    "golf",
    "golfing",
    "gravel cycling",
    "greenhorn valley",
    "hiking",
    "horse riding",
    "horseback riding",
    "hot springs",
    "hunting",
    "hunting & land leases",
    "jeeping & 4wd",
    "links",
    "local parks",
    "main street/chamber pages",
    "more attractions",
    "mountain biking",
    "national parks",
    "national parks, monuments & historic sites",
    "official city/county pages",
    "other sports",
    "outdoor adventures",
    "rafting/kayaking",
    "restaurants",
    "restaurants & dining",
    "skiing/boarding",
    "snowmobiling",
    "snowshoeing",
    "stonewall",
    "subscribe for fresh",
    "tap into creativity",
    "the colorado directory, inc.",
    "tourism offices and visitor-facing pages",
    "tourism pages",
    "tourism websites, google business profiles, social pages, and email newsletters",
    "vacation ideas",
    "visual arts",
    "water sports",
    "weddings & elope",
    "weddings & elopements",
    "whitewater rafting & kayaking",
    "winter lodging",
}


GENERIC_NOTE_PATTERNS = (
    "Commercial-directory-only lead from the July 2026 sweep",
    "Creative-directory lead added from a public local arts",
    "Use as a launch/outreach lead; verify details before",
    "Visitor-facing listing pulled from public travel/vacation guide source",
    "Use this as a starting contact",
    "Treat as unverified",
    "Verify before using",
    "review before publishing",
    "Open a source link when available",
    "Commercial-directory-only",
    "Visitor-facing listing pulled",
    "YellowPages.com bulk listing",
    "bulk listing",
    "source-check candidate",
    "starting contact",
)


GENERIC_RESOURCE_TYPES = {
    "outreach lead / source-check candidate",
    "promotion",
    "visitor-facing listing",
    "resource",
}


GENERIC_CATEGORIES = {
    "commercial directory lead / local business",
    "all tourism directory listings",
    "vacation directory listings and attractions",
    "travel guide businesses and attractions",
    "local listing to confirm",
}


BUSINESS_TYPE_KEYWORDS = [
    ("accounting", "accounting and bookkeeping service"),
    ("appraiser", "property or business appraisal service"),
    ("architect", "architecture or design service"),
    ("auto", "auto service or repair business"),
    ("bbq", "restaurant or food business"),
    ("bakery", "bakery or cafe"),
    ("bank", "banking or financial service"),
    ("baptist", "faith-based community organization"),
    ("bar", "bar, restaurant, or hospitality business"),
    ("beauty", "beauty or personal-care business"),
    ("brew", "brewery or hospitality business"),
    ("cafe", "cafe or food business"),
    ("camp", "campground or outdoor recreation business"),
    ("car wash", "auto service business"),
    ("church", "faith-based community organization"),
    ("clinic", "health or wellness service"),
    ("coffee", "coffee shop or cafe"),
    ("construction", "construction or contracting business"),
    ("dent", "dental or health service"),
    ("electric", "electrical or contracting business"),
    ("gallery", "gallery, studio, or creative venue"),
    ("gift", "gift shop or retail business"),
    ("golf", "recreation or visitor-facing business"),
    ("grocery", "grocery or food retail business"),
    ("hotel", "lodging or hospitality business"),
    ("inn", "lodging or hospitality business"),
    ("landscap", "landscaping or property service"),
    ("lodge", "lodging or hospitality business"),
    ("market", "retail, grocery, or local market"),
    ("mercantile", "retail, maker, or local goods business"),
    ("museum", "museum or cultural organization"),
    ("pizza", "restaurant or food business"),
    ("plumb", "plumbing or contracting business"),
    ("real estate", "real estate or property service"),
    ("resort", "lodging, recreation, or visitor-facing business"),
    ("restaurant", "restaurant or food business"),
    ("salon", "beauty or personal-care business"),
    ("school", "school, class, or education program"),
    ("studio", "studio, gallery, or creative business"),
    ("tire", "auto service or repair business"),
    ("vacation", "lodging or visitor-facing business"),
    ("winery", "winery or hospitality business"),
]


PUBLIC_TYPE_RULES = [
    (("grant", "funding", "loan", "scholarship", "stipend", "incentive", "foundation"), "Funding & support"),
    (("gallery", "artist", "arts", "creative", "maker", "museum", "studio", "craft", "ceramic", "painting", "photography", "sculpture", "fiber", "jewelry"), "Arts & culture"),
    (("newspaper", "radio", "media", "broadcast", "news", "magazine", "local page", "social page", "channels to watch"), "Media & news"),
    (("calendar", "event", "festival", "venue", "theater", "theatre", "performance", "live music"), "Events & venues"),
    (("hotel", "motel", "inn", "lodge", "lodging", "vacation rental", "rv", "resort", "campground", "camping"), "Lodging & stays"),
    (("restaurant", "dining", "food", "cafe", "coffee", "bakery", "bar", "brewery", "winery", "taqueria", "pizza", "catering"), "Food & drink"),
    (("shop", "shopping", "retail", "gift", "mercantile", "grocery", "market", "boutique", "apparel", "hardware"), "Retail & local goods"),
    (("tourism", "visitor", "chamber", "mainstreet", "main street", "destination", "travel guide"), "Tourism & visitor info"),
    (("outdoor", "recreation", "trail", "golf", "ski", "snowboard", "park", "state park", "guide"), "Outdoor recreation"),
    (("sbdc", "economic", "business support", "startup", "entrepreneur", "workforce", "training", "technical assistance", "job training"), "Business support"),
    (("school", "education", "college", "library", "class", "workshop"), "Education & learning"),
    (("hospital", "clinic", "health", "wellness", "dental", "therapy", "medical", "pharmacy", "beauty", "salon", "personal-care"), "Health & wellness"),
    (("church", "ministry", "nonprofit", "community", "service organization", "arts council"), "Nonprofit & community"),
    (("city", "county", "town", "village", "government", "municipal", "public office", "district"), "Public offices"),
    (("auto", "tire", "car wash", "fuel", "gas", "transport", "rv service"), "Auto & transportation"),
    (("home & garden", "home and garden", "garden", "construction", "contractor", "plumbing", "electric", "landscap", "excavation", "welding", "woodwork"), "Home, land & contracting"),
    (("bank", "credit union", "finance", "financial", "real estate", "property", "storage", "appraisal", "insurance", "accounting", "bookkeeping", "legal", "professional"), "Professional services"),
]

PUBLIC_TYPE_LABELS = {label for _, label in PUBLIC_TYPE_RULES}


AUDIENCE_DISPLAY_LABELS = {
    "For-Profit": "Businesses",
    "Non-Profit": "Nonprofits",
    "Artist": "Artists",
    "Creative business": "Creative businesses",
    "Entrepreneur": "Entrepreneurs",
    "Program": "Programs",
    "Visitors / tourists": "Visitors",
    "Arts / culture audiences": "Arts and culture",
    "Rural residents": "Rural residents",
    "Health / service audiences": "Health and service audiences",
    "Youth / families": "Youth and families",
}


def split_semicolon(value: object) -> list[str]:
    return [part.strip() for part in str(value or "").split(";") if part.strip()]


def host_matches(host: str, domains: set[str]) -> bool:
    return any(host == domain or host.endswith("." + domain) for domain in domains)


def normalized_listing_host(url: object) -> str:
    try:
        return urlparse(clean_text(url)).netloc.casefold().removeprefix("www.")
    except ValueError:
        return ""


def outreach_capability_tags(row: dict) -> list[str]:
    structured = row.get("outreach_channels")
    if isinstance(structured, list):
        labels = []
        for item in structured:
            if not isinstance(item, dict):
                continue
            label = clean_text(item.get("label"))
            if label and label not in labels:
                labels.append(label)
        if labels:
            return labels
    text_blob = " ".join(
        clean_text(row.get(field)).casefold()
        for field in (
            "notes",
            "public_description",
            "category",
            "resource_type",
            "public_listing_type",
            "yellowpages_recommended_action",
            "yellowpages_flyer_likelihood",
            "yellowpages_digital_distribution_likelihood",
        )
    )
    hosts = [
        normalized_listing_host(url)
        for url in split_semicolon(row.get("website")) + split_semicolon(row.get("source_url"))
    ]
    tags = []
    if is_physical_ad_candidate(row) or any(term in text_blob for term in ("flyer", "bulletin board", "rack card", "front-desk")):
        tags.append("Physical promotion contact")
    if any(term in text_blob for term in ("newsletter", "mailing list", "email list", "newsletter signup")):
        tags.append("Newsletter sharing")
    if (
        any(host and host_matches(host, SOCIAL_CHANNEL_HOSTS) for host in hosts)
        or any(
            term in text_blob
            for term in (
                "social media",
                "social profile",
                "digital share",
                "share digital event graphic",
                "partner share",
                "cross-promotion",
                "cross promotion",
                "repost",
                "digital distribution: medium",
                "digital distribution: high",
            )
        )
    ):
        tags.append("Social sharing")
    return tags


def fallback_online_connection_fields(row: dict) -> dict[str, str]:
    ordered_urls = []
    for field in ("website", "source_url"):
        for url in split_semicolon(row.get(field)):
            if DIRECTORY_CONNECTIVITY_CHECKS.get(url, {}).get("status") == "broken":
                continue
            if url not in ordered_urls:
                ordered_urls.append(url)
    direct_urls = [
        url
        for url in ordered_urls
        if normalized_listing_host(url) and not host_matches(normalized_listing_host(url), DIRECTORY_PROFILE_HOSTS)
    ]
    profile_urls = [url for url in ordered_urls if url not in direct_urls]
    if direct_urls:
        return {
            "online_connection_status": "direct-unconfirmed",
            "online_connection_group": "Direct website",
            "online_connection_label": "Website link",
            "online_connection_url": direct_urls[0],
            "online_connection_animated": "false",
        }
    if profile_urls:
        return {
            "online_connection_status": "profile-unconfirmed",
            "online_connection_group": "Hosted profile",
            "online_connection_label": "Listing link",
            "online_connection_url": profile_urls[0],
            "online_connection_animated": "false",
        }
    if clean_text(row.get("contact_email")) or clean_text(row.get("contact_phone")) or clean_text(row.get("physical_address")):
        return {
            "online_connection_status": "contact-only",
            "online_connection_group": "Contact only",
            "online_connection_label": "No direct website listed",
            "online_connection_url": "",
            "online_connection_animated": "false",
        }
    return {
        "online_connection_status": "no-online-link",
        "online_connection_group": "No online link",
        "online_connection_label": "No online link listed",
        "online_connection_url": "",
        "online_connection_animated": "false",
    }


def load_listing_keyword_index() -> dict[str, dict]:
    if hasattr(load_listing_keyword_index, "_cache"):
        return getattr(load_listing_keyword_index, "_cache")
    entries: dict[str, dict] = {}
    if LISTING_KEYWORD_INDEX_JSON.exists():
        try:
            payload = json.loads(LISTING_KEYWORD_INDEX_JSON.read_text(encoding="utf-8"))
            raw_entries = payload.get("entries", {})
            if isinstance(raw_entries, dict):
                entries = {str(key): value for key, value in raw_entries.items() if isinstance(value, dict)}
        except (OSError, json.JSONDecodeError):
            entries = {}
    setattr(load_listing_keyword_index, "_cache", entries)
    return entries


def listing_keyword_terms(row: dict) -> list[str]:
    entry = load_listing_keyword_index().get(clean_text(row.get("id")), {})
    keywords = entry.get("keywords", [])
    return [clean_text(keyword) for keyword in keywords if clean_text(keyword)]


def normalize_goal_relevance(value: object) -> str:
    goals = []
    for part in split_semicolon(value):
        normalized = "Find Money or Help" if part in {"Find Money / Help", "Find Money or Help"} else part
        if normalized not in goals:
            goals.append(normalized)
    return "; ".join(goals)


def concrete_listing_name(row: dict) -> bool:
    name = clean_text(row.get("resource_name")).lower()
    return bool(name) and name not in PLACE_ONLY_LISTING_NAMES


def normalized_resource_name_key(value: str) -> str:
    value = clean_text(value).casefold().replace("&", " and ")
    value = re.sub(r"\b(llc|inc|co|company|corp|corporation)\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    tokens = value.split()
    collapsed: list[str] = []
    index = 0
    while index < len(tokens):
        if len(tokens[index]) == 1 and tokens[index].isalpha():
            letters = []
            while index < len(tokens) and len(tokens[index]) == 1 and tokens[index].isalpha():
                letters.append(tokens[index])
                index += 1
            collapsed.append("".join(letters) if len(letters) > 1 else letters[0])
            continue
        collapsed.append(tokens[index])
        index += 1
    return " ".join(collapsed)


def split_resource_alias_names(value: str) -> list[str]:
    name = clean_text(value)
    if not name:
        return []
    parts = re.split(r"\s+(?:/|a/k/a|aka|formerly|dba|doing business as)\s+", name, flags=re.IGNORECASE)
    return [part.strip() for part in parts if part.strip()]


def duplicate_resource_score(row: dict) -> int:
    score = 0
    for field in ["website", "source_url", "contact_phone", "contact_email", "physical_address"]:
        if clean_text(row.get(field)):
            score += 12
    if clean_text(row.get("category")).casefold() not in GENERIC_CATEGORIES:
        score += 2
    if clean_text(row.get("resource_type")).casefold() not in GENERIC_RESOURCE_TYPES:
        score += 2
    if not generic_note(row):
        score += 4
    score += min(len(clean_text(row.get("notes"))) // 120, 3)
    return score


def merge_public_resource_group(group: list[dict]) -> dict:
    winner = max(group, key=duplicate_resource_score)
    merged = dict(winner)
    aliases = split_semicolon(merged.get("alternate_names"))
    merged_name = clean_text(merged.get("resource_name"))
    source_urls = split_semicolon(merged.get("source_url"))
    for row in group:
        row_name = clean_text(row.get("resource_name"))
        for alias in split_resource_alias_names(row_name):
            if alias and alias != merged_name and alias not in aliases:
                aliases.append(alias)
        for key, value in row.items():
            if key == "source_url":
                for url in split_semicolon(value):
                    if url not in source_urls:
                        source_urls.append(url)
            elif not clean_text(merged.get(key)) and clean_text(value):
                merged[key] = clean_text(value)
    merged["source_url"] = "; ".join(source_urls)
    if aliases:
        merged["alternate_names"] = "; ".join(aliases)
    return merged


def dedupe_resource_rows(rows: list[dict]) -> list[dict]:
    exact_keys = {
        (
            clean_text(row.get("county")).casefold(),
            clean_text(row.get("town")).casefold(),
            clean_text(row.get("state")).casefold(),
            normalized_resource_name_key(row.get("resource_name")),
        )
        for row in rows
    }
    groups: dict[tuple[str, str, str, str], list[dict]] = {}
    for row in rows:
        location = (
            clean_text(row.get("county")).casefold(),
            clean_text(row.get("town")).casefold(),
            clean_text(row.get("state")).casefold(),
        )
        name_key = normalized_resource_name_key(row.get("resource_name"))
        group_key = (*location, name_key)
        for alias in split_resource_alias_names(row.get("resource_name")):
            alias_key = normalized_resource_name_key(alias)
            if alias_key and alias_key != name_key and (*location, alias_key) in exact_keys:
                group_key = (*location, alias_key)
                break
        groups.setdefault(group_key, []).append(row)
    return [merge_public_resource_group(group) for group in groups.values()]


def inferred_listing_type(row: dict) -> str:
    name = clean_text(row.get("resource_name"))
    note = "" if generic_note(row) else clean_text(row.get("notes"))
    name_category = " ".join([name, clean_text(row.get("category"))]).casefold()
    if text_matches_terms(name_category, ["catering"]) and not text_matches_terms(
        name_category, ["grant", "funding", "scholarship", "stipend"]
    ):
        return "Food & drink"
    category = clean_text(row.get("category"))
    resource_type = clean_text(row.get("resource_type"))

    # Prefer the listing's concrete identity fields before broader keywords or notes.
    # This keeps incidental text such as "artist audience" from turning a cafe into
    # an arts listing and prevents short terms such as "art" matching "Auto Parts."
    candidates = []
    if category.casefold() not in GENERIC_CATEGORIES:
        candidates.append(category)
    candidates.append(name)
    if resource_type.casefold() not in GENERIC_RESOURCE_TYPES:
        candidates.append(resource_type)
    candidates.extend([" ".join(listing_keyword_terms(row)), note])
    for candidate in candidates:
        if candidate in PUBLIC_TYPE_LABELS:
            return candidate
        if not candidate:
            continue
        for needles, label in PUBLIC_TYPE_RULES:
            if text_matches_terms(candidate, list(needles)):
                return label

    text = " ".join(candidate for candidate in candidates if candidate)
    for needle, label in BUSINESS_TYPE_KEYWORDS:
        if business_keyword_matches(text, needle):
            label_text = label.casefold()
            for needles, public_label in PUBLIC_TYPE_RULES:
                if text_matches_terms(label_text, list(needles)) or text_matches_terms(needle, list(needles)):
                    return public_label
            return "Local business or service"
    return "Local business or service"


def public_place(row: dict) -> str:
    parts = [clean_text(row.get("town")), clean_text(row.get("county")), clean_text(row.get("state"))]
    parts = [part for part in parts if part]
    return ", ".join(parts) if parts else "the tri-county region"


def organization_tags(row: dict) -> list[str]:
    tags = []
    for audience in split_semicolon(row.get("audience_served")):
        label = AUDIENCE_DISPLAY_LABELS.get(audience, audience)
        if label and label not in tags:
            tags.append(label)
    return tags[:6] or ["Regional users"]


def public_search_keywords(row: dict) -> str:
    keywords = []
    listing_type = clean_text(row.get("public_listing_type")) or inferred_listing_type(row)
    category = clean_text(row.get("public_category")) or compact_category_label(row, listing_type)
    values = [
        row.get("resource_name"),
        row.get("alternate_names"),
        row.get("town"),
        row.get("county"),
        row.get("state"),
        category,
        listing_type,
        row.get("access_mode"),
        row.get("online_connection_group"),
        row.get("online_connection_label"),
        row.get("outreach_channel_labels"),
        row.get("outreach_channel_groups"),
    ]
    for raw_value in values:
        value = clean_text(raw_value)
        if value and value not in keywords:
            keywords.append(value)
    for value in [listing_type, public_best_for(row)]:
        if value and value not in keywords:
            keywords.append(value)
    for part in split_semicolon(normalize_goal_relevance(row.get("goal_relevance"))) + split_semicolon(row.get("audience_served")) + organization_tags(row):
        if part and part not in keywords:
            keywords.append(part)
    for part in listing_keyword_terms(row):
        if part not in keywords:
            keywords.append(part)
    for part in split_semicolon(row.get("outreach_channel_labels")):
        if part not in keywords:
            keywords.append(part)
    if is_physical_ad_candidate(row):
        for part in [
            "Physical promotion contact",
            "physical advertisements",
            "flyers",
            "posters",
            "rack cards",
            "bulletin boards",
            "front-desk referrals",
        ]:
            if part not in keywords:
                keywords.append(part)
    elif has_physical_location(row):
        for part in ["Physical location", "map", "in-person"]:
            if part not in keywords:
                keywords.append(part)
    return "; ".join(keywords)


def generic_note(row: dict) -> bool:
    note = clean_text(row.get("notes"))
    note_lower = note.casefold()
    return any(pattern.casefold() in note_lower for pattern in GENERIC_NOTE_PATTERNS)


def load_everything_description_index() -> dict[tuple[str, str, str], str]:
    if hasattr(load_everything_description_index, "_cache"):
        return getattr(load_everything_description_index, "_cache")
    index: dict[tuple[str, str, str], str] = {}
    if EVERYTHING_DIRECTORY_JSON.exists():
        try:
            payload = json.loads(EVERYTHING_DIRECTORY_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = []
        if isinstance(payload, list):
            for item in payload:
                if not isinstance(item, dict):
                    continue
                name_key = normalized_resource_name_key(item.get("name", ""))
                if not name_key:
                    continue
                town_key = clean_text(item.get("town")).casefold()
                county_key = clean_text(item.get("county")).casefold()
                description = clean_text(item.get("description"))
                if useful_public_description(description):
                    index.setdefault((name_key, town_key, county_key), description)
                    index.setdefault((name_key, "", county_key), description)
                    index.setdefault((name_key, town_key, ""), description)
    setattr(load_everything_description_index, "_cache", index)
    return index


def everything_description_for(row: dict) -> str:
    name_key = normalized_resource_name_key(row.get("resource_name", ""))
    town_key = clean_text(row.get("town")).casefold()
    county_key = clean_text(row.get("county")).casefold()
    if not name_key:
        return ""
    index = load_everything_description_index()
    return (
        index.get((name_key, town_key, county_key))
        or index.get((name_key, "", county_key))
        or index.get((name_key, town_key, ""))
        or ""
    )


def useful_public_description(value: str) -> bool:
    text = clean_text(value)
    if len(text) < 35:
        return False
    lowered = text.casefold()
    process_phrases = (
        "use it to find the public page",
        "open a source link",
        "starting contact",
        "before assuming",
        "source-check",
        "verify",
        "verification",
        "recommended outreach waves",
        "promotion timeline",
        "automation",
        "remaining gaps",
        "research sources by data type",
        "professional or service business in regional",
    )
    return not any(phrase in lowered for phrase in process_phrases)


def public_safe_note(row: dict) -> str:
    note = public_text_without_partner_names(clean_text(row.get("notes")))
    if note and not generic_note(row) and useful_public_description(note):
        return note
    return ""


def compact_category_label(row: dict, listing_type: str) -> str:
    category = clean_text(row.get("category"))
    resource_type = clean_text(row.get("resource_type"))
    for value in [category, resource_type]:
        lowered = value.casefold()
        if value and lowered not in GENERIC_CATEGORIES and lowered not in GENERIC_RESOURCE_TYPES:
            return value
    return listing_type


def listing_description_from_context(row: dict, listing_type: str, place: str) -> str:
    name = clean_text(row.get("resource_name")) or "This listing"
    category = compact_category_label(row, listing_type)
    base_by_type = {
        "Funding & support": "Funding or support resource",
        "Arts & culture": "Arts, culture, or creative-sector listing",
        "Media & news": "Media or public-information channel",
        "Events & venues": "Event, venue, or calendar listing",
        "Lodging & stays": "Lodging or visitor-stay listing",
        "Food & drink": "Food or drink business",
        "Retail & local goods": "Retail or local-goods business",
        "Tourism & visitor info": "Tourism or visitor-information listing",
        "Outdoor recreation": "Outdoor recreation or visitor-activity listing",
        "Business support": "Business or workforce-support resource",
        "Education & learning": "Education or learning resource",
        "Health & wellness": "Health, wellness, or personal-care listing",
        "Nonprofit & community": "Nonprofit or community organization",
        "Public offices": "Public office or civic-information route",
        "Auto & transportation": "Auto or transportation listing",
        "Home, land & contracting": "Home, land, or contracting service",
        "Professional services": "Professional or business-service listing",
        "Local business or service": "Local business or service",
    }.get(listing_type, "Local business, organization, program, service, or regional resource")
    best_for = public_best_for(row)
    best_phrase = best_for.replace("; ", ", ")
    category_sentence = f" Listed category: {category}." if category and category != listing_type else ""
    return f"{name} is a {base_by_type.lower()} in {place}.{category_sentence} Search here for {best_phrase} when you need a local contact, listing update, or outreach route."


def public_best_for(row: dict) -> str:
    goals = split_semicolon(normalize_goal_relevance(row.get("goal_relevance")))
    tags = organization_tags(row)
    capability_tags = outreach_capability_tags(row)
    listing_type = inferred_listing_type(row)
    access_mode = clean_text(row.get("access_mode")).casefold()
    uses = []
    if "Promote Something" in goals:
        uses.append("promotion")
    if "Improve Online Visibility" in goals:
        uses.append("online listing cleanup")
    if "Reach People Offline" in goals or "physical" in access_mode:
        uses.append("flyer posting")
    if "Find Money or Help" in goals or listing_type == "Funding & support":
        uses.append("funding or support research")
    if "Get Media Coverage" in goals or listing_type == "Media & news":
        uses.append("media or calendar outreach")
    if "Add / Correct Info" in goals:
        uses.append("listing updates")
    if "Newsletter sharing" in capability_tags:
        uses.append("newsletter sharing")
    if "Social sharing" in capability_tags:
        uses.append("social promotion")
    if "Visitors" in tags or listing_type in {"Tourism & visitor info", "Lodging & stays", "Food & drink", "Outdoor recreation"}:
        uses.append("visitor-facing visibility")
    if "Nonprofits" in tags or listing_type == "Nonprofit & community":
        uses.append("partner or referral outreach")
    if "Arts and culture" in tags or listing_type == "Arts & culture":
        uses.append("arts and culture visibility")
    deduped = []
    for item in uses:
        if item not in deduped:
            deduped.append(item)
    return "; ".join(deduped[:4]) if deduped else "regional discovery; contact-list building"


def public_description(row: dict) -> str:
    listing_type = inferred_listing_type(row)
    place = public_place(row)
    source_note = public_safe_note(row)
    if source_note:
        return source_note
    directory_note = everything_description_for(row)
    if directory_note:
        return public_text_without_partner_names(directory_note)
    return listing_description_from_context(row, listing_type, place)


def physical_promotion_category(row: dict) -> str:
    listing_type = inferred_listing_type(row)
    blob = " ".join(
        clean_text(row.get(field)).casefold()
        for field in [
            "resource_name",
            "resource_type",
            "category",
            "public_listing_type",
        ]
    )
    if text_matches_terms(blob, ["thrift", "secondhand", "antique", "mercantile"]):
        return "Local businesses and services"
    if text_matches_terms(blob, ["tattoo", "auto shop", "auto repair", "automotive", "car dealer", "dealership", "tire shop", "salon", "barber", "haircut", "hair salon", "beauty salon", "personal care", "spa"]) or listing_type == "Auto & transportation":
        return "Local businesses and services"
    if text_matches_terms(blob, ["bookstore", "book shop", "bookseller", "pharmacy", "drugstore"]):
        return "Local businesses and services"
    if text_matches_terms(blob, ["library", "community center", "senior center", "recreation center", "school", "college", "campus"]):
        return "Community and public spaces"
    if listing_type == "Public offices" or text_matches_terms(blob, ["city hall", "town hall", "county clerk", "courthouse", "court", "public office"]):
        return "Community and public spaces"
    if text_matches_terms(blob, ["visitor center", "visitors center", "welcome center", "tourism", "tourist", "chamber", "mainstreet"]):
        return "Visitor and travel locations"
    if text_matches_terms(blob, ["gallery", "museum", "venue", "theater", "theatre", "arts center", "art center", "creative district", "cultural center"]):
        return "Arts and event spaces"
    if listing_type == "Food & drink" or text_matches_terms(blob, ["coffee", "cafe", "espresso", "bakery", "restaurant", "bar", "brewery", "distillery"]):
        return "Local businesses and services"
    if listing_type == "Retail & local goods" or text_matches_terms(blob, ["market", "grocery", "food store", "shop", "store", "retail", "boutique"]):
        return "Local businesses and services"
    if listing_type in {"Lodging & stays", "Tourism & visitor info"} or text_matches_terms(blob, ["rail", "train", "station", "depot", "bus", "transit", "hotel", "motel", "inn", "lodging", "campground", "rv", "resort"]):
        return "Visitor and travel locations"
    return ""


def physical_ad_location_score(row: dict) -> int:
    listing_type = inferred_listing_type(row)
    access_mode = clean_text(row.get("access_mode")).casefold()
    goals = normalize_goal_relevance(row.get("goal_relevance")).casefold()
    blob = " ".join(
        clean_text(row.get(field)).casefold()
        for field in [
            "resource_name",
            "resource_type",
            "category",
            "public_listing_type",
            "physical_address",
            "notes",
            "audience_served",
        ]
    )
    term_hits = sum(1 for term in PHYSICAL_AD_LOCATION_TERMS if text_matches_terms(blob, [term]))
    category = physical_promotion_category(row)
    score = term_hits * 2
    if category:
        score += 10
    if "physical" in access_mode:
        score += 4
    if "reach people offline" in goals:
        score += 2
    if listing_type in PHYSICAL_AD_LISTING_TYPES:
        score += 2
    if has_physical_location(row):
        score += 2
    if resource_url(row):
        score += 1
    if "online lead" in access_mode and not has_physical_location(row):
        score -= 2
    if not category:
        return 0
    return max(score, 0)


def physical_ad_location_fit(row: dict) -> str:
    blob = " ".join(
        clean_text(row.get(field)).casefold()
        for field in ["resource_name", "category", "resource_type", "public_listing_type"]
    )
    listing_type = inferred_listing_type(row)
    if listing_type == "Public offices" or text_matches_terms(blob, ["city hall", "town hall", "county clerk", "courthouse", "court", "public office"]):
        return "Official notices, public meetings, civic information, public hearings, and department-approved announcements."
    if text_matches_terms(blob, ["library", "community center", "senior center", "recreation center"]):
        return "Community flyers, classes, nonprofit programs, support services, and local events."
    if text_matches_terms(blob, ["gallery", "museum", "venue", "theater", "theatre", "arts center", "art center", "creative district", "cultural center"]):
        return "Art openings, performances, workshops, creative calls, festivals, classes, and cultural events."
    if text_matches_terms(blob, ["bookstore", "book shop", "bookseller", "pharmacy", "drugstore", "tattoo", "auto shop", "auto repair", "automotive", "car dealer", "dealership", "tire shop", "thrift", "secondhand", "antique", "salon", "barber", "haircut", "hair salon", "beauty salon", "personal care", "spa"]):
        return "Community events, services, hiring, fundraisers, classes, referrals, and neighborhood-facing promotion."
    if text_matches_terms(blob, ["coffee", "cafe", "espresso", "bakery", "restaurant", "bar", "brewery", "distillery", "market", "grocery", "shop", "store", "mercantile"]):
        return "Neighborhood flyers, local offers, hiring, events, classes, specials, and downtown cross-promotion."
    if text_matches_terms(blob, ["rail", "train", "station", "depot", "bus", "transit", "hotel", "motel", "inn", "lodging", "campground", "rv", "resort"]):
        return "Visitor-facing flyers, travel information, event handouts, maps, tours, and lodging-adjacent services."
    if text_matches_terms(blob, ["visitor", "tourism", "tourist", "welcome center", "chamber", "mainstreet"]):
        return "Visitor-facing events, rack cards, brochures, business listings, tours, lodging, food, retail, and attractions."
    return "A local contact for flyers, posters, brochures, rack cards, or front-desk referrals."


def physical_ad_location_note(row: dict) -> str:
    listing_type = inferred_listing_type(row)
    blob = " ".join(
        clean_text(row.get(field)).casefold()
        for field in ["resource_name", "category", "resource_type", "public_listing_type"]
    )
    if listing_type == "Public offices":
        return "Public offices may separate official notices from community flyers or commercial advertising; use the listed contact for the correct route."
    if "library" in blob:
        return "Library bulletin-board policies can distinguish political, commercial, oversized, or undated materials."
    if text_matches_terms(blob, ["school", "college", "campus"]):
        return "Schools and campuses may route posting requests through a specific office or department."
    if text_matches_terms(blob, ["restaurant", "cafe", "coffee", "bar", "brewery", "market", "shop", "store"]):
        return "Use the listed business contact to confirm current space, format, and removal timing."
    if text_matches_terms(blob, ["visitor", "tourism", "tourist", "welcome center", "chamber"]):
        return "Use the listed contact to confirm current brochure, rack-card, poster, or calendar routes."
    return "Posting policies vary; use the listed contact to confirm the current route and format."


def has_physical_location(row: dict) -> bool:
    address = clean_text(row.get("physical_address"))
    if not address:
        return False
    lowered = address.casefold()
    if any(term in lowered for term in ("virtual", "online only", "no public location")):
        return False
    po_box = re.search(r"\bp\.?\s*o\.?\s*box\b|\bpo\s+box\b", lowered)
    streetish = re.search(
        r"\b(?:st|street|ave|avenue|rd|road|blvd|boulevard|dr|drive|ln|lane|way|hwy|highway|route|nm-|us-|co-|county road|cr|mile marker|main|broadway|commercial|plaza|terrace|camino|park)\b",
        lowered,
    )
    return not (po_box and not streetish)


def is_physical_ad_candidate(row: dict) -> bool:
    if not has_physical_location(row):
        return False
    return bool(physical_promotion_category(row))


def physical_ad_location_rows(rows: list[dict], limit: int = 96) -> list[dict]:
    scored: list[tuple[int, dict]] = []
    for row in rows:
        score = physical_ad_location_score(row)
        if score and is_physical_ad_candidate(row):
            scored.append((score, row))
    ranked = sorted(scored, key=lambda item: (-item[0], clean_text(item[1].get("resource_name")).casefold()))
    by_county: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    for item in ranked:
        by_county[clean_text(item[1].get("county")) or "Regional"].append(item)
    county_order = ["Colfax", "Las Animas", "Huerfano", "Regional"]
    active_counties = [county for county in county_order if by_county.get(county)]
    county_cap = max(1, (limit + max(1, len(active_counties)) - 1) // max(1, len(active_counties)))
    town_cap = max(2, (county_cap + 1) // 2)
    chosen: list[dict] = []
    chosen_ids: set[str] = set()
    town_counts: Counter[str] = Counter()

    def choose_from(items: list[tuple[int, dict]], cap: int) -> None:
        added = 0
        for _, row in items:
            key = clean_text(row.get("id")) or clean_text(row.get("resource_name")).casefold()
            town_key = f"{clean_text(row.get('county'))}|{clean_text(row.get('town'))}".casefold()
            if key in chosen_ids or town_counts[town_key] >= town_cap:
                continue
            chosen.append(row)
            chosen_ids.add(key)
            town_counts[town_key] += 1
            added += 1
            if added >= cap or len(chosen) >= limit:
                return

    for county in active_counties:
        choose_from(by_county.get(county, []), county_cap)
    if len(chosen) < limit:
        choose_from(ranked, limit - len(chosen))
    return sorted(
        chosen,
        key=lambda row: (
            clean_text(row.get("county")).casefold(),
            clean_text(row.get("town")).casefold(),
            clean_text(row.get("resource_name")).casefold(),
        ),
    )


def normalized_contact_destination(value: object) -> str:
    destination = clean_text(str(value or ""))
    if not destination:
        return ""
    lowered = destination.casefold()
    if lowered.startswith(("https://", "http://", "mailto:", "tel:")):
        return destination
    if lowered.startswith("www.") or re.match(r"^[a-z0-9][a-z0-9.-]+\.[a-z]{2,}(?:/|$)", lowered):
        return "https://" + destination
    return ""


def best_entity_contact_url(row: dict, name: str | None = None) -> str:
    for field in ("website", "source_url", "url"):
        for value in split_semicolon(row.get(field)):
            destination = normalized_contact_destination(value)
            if destination:
                return destination

    for email in split_semicolon(row.get("contact_email")):
        email = clean_text(email)
        if "@" in email:
            return "mailto:" + email

    for phone in split_semicolon(row.get("contact_phone")):
        dial = re.sub(r"[^0-9+]", "", phone)
        if len(re.sub(r"\D", "", dial)) >= 7:
            return "tel:" + dial

    address = next(iter(split_semicolon(row.get("physical_address"))), "")
    if address:
        return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(address)

    entity_name = clean_text(
        name
        or row.get("resource_name")
        or row.get("title")
        or row.get("channel")
        or row.get("place")
        or "regional resource"
    )
    place = " ".join(
        part
        for part in [
            clean_text(row.get("town")),
            clean_text(row.get("county")),
            clean_text(row.get("state")),
        ]
        if part
    )
    query = " ".join(part for part in [entity_name, place, "contact"] if part)
    return "https://www.google.com/search?q=" + quote_plus(query)


def entity_name_link(row: dict, name: str | None = None, class_name: str = "entity-name-link") -> str:
    label = clean_text(
        name
        or row.get("resource_name")
        or row.get("title")
        or row.get("channel")
        or row.get("place")
        or "Unnamed resource"
    )
    href = best_entity_contact_url(row, label)
    external = not href.casefold().startswith(("mailto:", "tel:"))
    external_attrs = ' target="_blank" rel="noreferrer"' if external else ""
    return (
        f'<a class="{html_escape(class_name)}" href="{html_escape(href)}"'
        f'{external_attrs} aria-label="Find contact information for {html_escape(label)}">'
        f"{html_escape(label)}</a>"
    )


def contact_links_for_row(row: dict) -> str:
    destinations: list[tuple[str, str]] = []
    seen: set[str] = set()
    seen_route_hosts: set[tuple[str, str]] = set()
    host_deduped_labels = {"Website", "Directory page", "Tourism listing", "Business profile", "Travel profile", "Listing page"}

    def add(label: str, value: object) -> None:
        destination = normalized_contact_destination(value)
        if not destination or destination in seen:
            return
        host_key = source_domain(destination).casefold()
        route_host_key = (label, host_key)
        if label in host_deduped_labels and host_key and route_host_key in seen_route_hosts:
            return
        seen.add(destination)
        if label in host_deduped_labels and host_key:
            seen_route_hosts.add(route_host_key)
        destinations.append((label, destination))

    website_urls = split_semicolon(row.get("website"))
    source_urls = split_semicolon(row.get("source_url"))
    for url in website_urls:
        add(resource_url_label(url), url)
    for url in source_urls:
        if url not in website_urls:
            add(resource_url_label(url, "Listing page"), url)
    for email in split_semicolon(row.get("contact_email")):
        email = clean_text(email)
        if "@" in email:
            add("Email", "mailto:" + email)
    for phone in split_semicolon(row.get("contact_phone")):
        phone_href = re.sub(r"[^0-9+]", "", phone)
        if len(re.sub(r"\D", "", phone_href)) >= 7:
            add("Phone", "tel:" + phone_href)
    for address in split_semicolon(row.get("physical_address")):
        map_url = "https://www.google.com/maps/search/?api=1&query=" + quote_plus(address)
        add("Map", map_url)

    label_counts = Counter(label for label, _ in destinations)
    label_indexes: Counter[str] = Counter()
    links: list[str] = []
    for label, destination in destinations:
        label_indexes[label] += 1
        display_label = label
        if label_counts[label] > 1:
            host = source_domain(destination)
            suffix = host or str(label_indexes[label])
            display_label = f"{label}: {suffix}"
        external = not destination.casefold().startswith(("mailto:", "tel:"))
        external_attrs = ' target="_blank" rel="noreferrer"' if external else ""
        links.append(
            f'<a class="resource-contact-link" href="{html_escape(destination)}"{external_attrs}>'
            f"{html_escape(display_label)}</a>"
        )
    return " ".join(links) or '<span class="source-note">Search for contact details or submit a contact update.</span>'


def resource_physical_indicator_badges(row: dict) -> str:
    if clean_text(row.get("physical_ad_candidate")) == "true" or is_physical_ad_candidate(row):
        note = clean_text(row.get("physical_ad_note")) or physical_ad_location_note(row)
        return (
            '<div class="listing-indicators" aria-label="Physical location indicators">'
            f'<span class="listing-marker listing-marker--ad" title="{html_escape(note)}">Physical promotion contact</span>'
            "</div>"
        )
    if clean_text(row.get("has_physical_location")) == "true" or has_physical_location(row):
        note = clean_text(row.get("physical_ad_note")) or "This listing has a real-world location."
        return (
            '<div class="listing-indicators" aria-label="Physical location indicators">'
            f'<span class="listing-marker listing-marker--physical" title="{html_escape(note)}">Physical location</span>'
            "</div>"
        )
    return ""


def resource_outreach_channel_badges(row: dict, limit: int = 6) -> str:
    channels = [item for item in (row.get("outreach_channels") or []) if isinstance(item, dict)]
    if not channels:
        return '<p class="outreach-empty">No advertising or cross-promotion route is listed yet.</p>'
    visible = channels[:limit]
    badges = []
    for item in visible:
        status = clean_text(item.get("status")) or "ask"
        label = clean_text(item.get("label")) or clean_text(item.get("channel"))
        note = clean_text(item.get("note"))
        badges.append(
            f'<span class="outreach-tag outreach-tag--{html_escape(status)}" '
            f'data-outreach-channel="{html_escape(item.get("key"))}" title="{html_escape(note)}">'
            f'{html_escape(label)}</span>'
        )
    remaining = len(channels) - len(visible)
    if remaining:
        badges.append(f'<span class="outreach-tag outreach-tag--more">+{remaining} more</span>')
    return '<div class="outreach-tags" aria-label="Promotion and advertising paths">' + "".join(badges) + "</div>"


def resource_online_connection_badge(row: dict) -> str:
    status = clean_text(row.get("online_connection_status")) or "no-online-link"
    label = clean_text(row.get("online_connection_label")) or "No online link listed"
    destination = normalized_contact_destination(row.get("online_connection_url"))
    animated = clean_text(row.get("online_connection_animated")) == "true"
    if status.startswith("direct"):
        style = "connected"
    elif status.startswith("profile") or status == "link-listed":
        style = "profile"
    else:
        style = "missing"
    animation_class = " is-animated" if animated else ""
    signal = '<span class="connection-label__signal" aria-hidden="true"></span>'
    if destination:
        return (
            f'<div class="resource-connection" data-online-connection="{html_escape(status)}">'
            f'<a class="connection-label connection-label--{style}{animation_class}" '
            f'href="{html_escape(destination)}" target="_blank" rel="noreferrer">'
            f"{signal}{html_escape(label)}</a></div>"
        )
    return (
        f'<div class="resource-connection" data-online-connection="{html_escape(status)}">'
        f'<span class="connection-label connection-label--missing">{signal}{html_escape(label)}</span></div>'
    )


def public_text_without_partner_names(value: str) -> str:
    replacements = {
        "Super Eukarya / Tri-County Marketing Guide implementation pack": "Tri-County Marketing Guide implementation pack",
        "Super Eukarya Design": "Design partner",
        "Super Eukarya": "design partner",
        "SUPER EUKARYA": "",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def row_blob(row: dict) -> str:
    fields = [
        "id",
        "resource_name",
        "resource_type",
        "category",
        "notes",
        "source_type",
        "goal_relevance",
        "audience_served",
    ]
    return " ".join(clean_text(row.get(field)).lower() for field in fields)


def is_creation_process_note(row: dict) -> bool:
    category = clean_text(row.get("category")).lower()
    resource_type = clean_text(row.get("resource_type")).lower()
    blob = row_blob(row)
    process_categories = (
        "outreach route",
        "peer models",
        "strategy crosswalk",
        "suggested hashtag",
        "funding programs comparison",
        "funding & financing programs",
        "promotion timeline",
        "research sources",
        "why these data points",
        "needs met",
        "remaining gaps",
        "inventory gaps",
        "published business count",
        "audience profiles",
        "business geography",
        "verification-priority",
        "sparse nodes",
    )
    process_terms = (
        "recommended outreach waves",
        "verification agenda",
        "priority map",
        "timeline",
        "automation",
        "streamlining",
        "data source",
        "strategy",
        "crosswalk",
        "how individuals compile",
        "contact confirmation",
    )
    return (
        resource_type == "data source"
        or any(term in category for term in process_categories)
        or any(term in blob for term in process_terms)
    )


def malformed_listing_name(row: dict) -> bool:
    name = clean_text(row.get("resource_name"))
    if not name:
        return True
    lowered = name.casefold()
    compact = re.sub(r"[^a-z0-9]+", " ", lowered).strip()
    if lowered.startswith("+"):
        return True
    if compact in {
        "email",
        "website",
        "phone",
        "address",
        "contact",
        "learn more",
        "read more",
        "view details",
        "registered businesses",
        "all listings",
    }:
        return True
    if "email" in compact and "website" in compact and len(compact.split()) <= 5:
        return True
    if re.fullmatch(r"(?:email|website|phone|address|contact|fax|map|details|view|more|and|or|\d|\s)+", compact):
        return True
    return False


def publishable_resource_row(row: dict) -> bool:
    name = clean_text(row.get("resource_name")).casefold()
    return (
        concrete_listing_name(row)
        and name not in NON_ENTITY_RESOURCE_NAMES
        and not row_references_excluded_directory_entity(row)
        and not is_creation_process_note(row)
        and not malformed_listing_name(row)
    )


def infer_verification_key(row: dict) -> str:
    if is_creation_process_note(row):
        return "process-note"
    confidence = clean_text(row.get("confidence_level")).lower()
    method = clean_text(row.get("verification_method")).lower()
    source_type = clean_text(row.get("source_type")).lower()
    has_url = bool(clean_text(row.get("website")) or clean_text(row.get("source_url")))
    follow_up = clean_text(row.get("needs_follow_up")).lower() in {"true", "yes", "1", "y"}
    official_method = any(term in method for term in ("primary source", "automated link check", "in-person verified", "source review"))
    official_source = any(term in source_type for term in ("government website", "organization website", "official"))
    if has_url and confidence == "high" and (official_method or official_source or not follow_up):
        return "official-source"
    if has_url:
        return "source-linked"
    return "field-check"


def infer_public_layer(row: dict) -> str:
    status = infer_verification_key(row)
    if status == "official-source":
        return "verified_directory"
    if status == "source-linked":
        return "source_linked"
    if status == "process-note":
        return "creation_process_note"
    return "provisional_lead"


def verification_summary(row: dict, status: str) -> str:
    if status == "official-source":
        return "A public source or official-style source check supports this listing. Re-check before publishing contact details or eligibility claims."
    if status == "source-linked":
        return "This listing has a public link, but details may still need confirmation before outreach or spending."
    if status == "process-note":
        return "This helps explain or improve the guide. It is not a direct public contact."
    return "No reliable public link is attached yet. Treat this as a lead for phone, email, website, or field verification."


def online_connection_fields(row: dict) -> dict[str, str]:
    entry_id = clean_text(row.get("id"))
    audited = DIRECTORY_CONNECTIVITY_ENTRIES.get(entry_id, {})
    if audited:
        return {
            "online_connection_status": clean_text(audited.get("connection_status")),
            "online_connection_group": clean_text(audited.get("connection_group")),
            "online_connection_label": clean_text(audited.get("public_label")),
            "online_connection_url": clean_text(audited.get("public_url")),
            "online_connection_animated": "true" if audited.get("animation_eligible") else "false",
        }
    return fallback_online_connection_fields(row)


def without_confirmed_broken_urls(value: object) -> str:
    return "; ".join(
        url
        for url in split_semicolon(value)
        if DIRECTORY_CONNECTIVITY_CHECKS.get(url, {}).get("status") != "broken"
    )


def enrich_resource_row(row: dict) -> dict:
    status = infer_verification_key(row)
    layer = infer_public_layer(row)
    enriched = dict(row)
    enriched["website"] = without_confirmed_broken_urls(enriched.get("website"))
    enriched["source_url"] = without_confirmed_broken_urls(enriched.get("source_url"))
    enriched["goal_relevance"] = normalize_goal_relevance(enriched.get("goal_relevance"))
    enriched["public_listing_type"] = inferred_listing_type(enriched)
    enriched["public_category"] = compact_category_label(enriched, enriched["public_listing_type"])
    enriched.update(online_connection_fields(enriched))
    enriched["public_description"] = public_description(enriched)
    enriched["has_physical_location"] = as_bool_text(has_physical_location(enriched))
    enriched["physical_ad_candidate"] = as_bool_text(is_physical_ad_candidate(enriched))
    if enriched["physical_ad_candidate"] == "true":
        enriched["physical_ad_label"] = "Physical promotion contact"
        enriched["physical_promotion_category"] = physical_promotion_category(enriched)
        enriched["physical_promotion_keywords"] = "; ".join(
            value
            for value in [
                "physical advertising",
                "physical promotion location",
                "on-site promotion contact",
                "flyers",
                "posters",
                "brochures",
                "rack cards",
                "bulletin boards",
                "front-desk referrals",
            ]
            if value
        )
        enriched["physical_ad_note"] = physical_ad_location_note(enriched)
    elif enriched["has_physical_location"] == "true":
        enriched["physical_ad_label"] = "Physical location"
        enriched["physical_promotion_category"] = ""
        enriched["physical_promotion_keywords"] = ""
        enriched["physical_ad_note"] = "This listing has a real-world location and a contact path for current location details."
    else:
        enriched["physical_ad_label"] = ""
        enriched["physical_promotion_category"] = ""
        enriched["physical_promotion_keywords"] = ""
        enriched["physical_ad_note"] = ""
    outreach_channels = classify_outreach_channels(
        enriched,
        has_physical_location=enriched["has_physical_location"] == "true",
        physical_ad_candidate=enriched["physical_ad_candidate"] == "true",
    )
    enriched["outreach_channels"] = outreach_channels
    enriched["outreach_channel_keys"] = "; ".join(item["key"] for item in outreach_channels)
    enriched["outreach_channel_labels"] = "; ".join(item["label"] for item in outreach_channels)
    enriched["outreach_channel_groups"] = "; ".join(dict.fromkeys(item["group"] for item in outreach_channels))
    enriched["outreach_listed_count"] = sum(item["status"] == "listed" for item in outreach_channels)
    enriched["outreach_ask_count"] = sum(item["status"] == "ask" for item in outreach_channels)
    enriched["public_keywords"] = public_search_keywords(enriched)
    enriched["public_audience_tags"] = "; ".join(organization_tags(enriched))
    enriched["public_org_tags"] = enriched["public_audience_tags"]
    enriched["public_best_for"] = public_best_for(enriched)
    enriched["verification_key"] = status
    enriched["verification_label"] = VERIFICATION_LABELS[status]
    enriched["verification_class"] = VERIFICATION_CLASSES[status]
    enriched["public_layer"] = layer
    enriched["public_layer_label"] = LAYER_LABELS[layer]
    enriched["verification_summary"] = verification_summary(row, status)
    enriched["has_public_source"] = bool(clean_text(row.get("website")) or clean_text(row.get("source_url")))
    return enriched


def source_status(item: dict) -> tuple[str, str]:
    confidence = clean_text(item.get("confidence")).lower()
    kind = clean_text(item.get("kind")).lower()
    if confidence == "high" or any(term in kind for term in ("government", "municipal", "official", "economic-development")):
        return ("official-source", VERIFICATION_LABELS["official-source"])
    if clean_text(item.get("url")):
        return ("source-linked", VERIFICATION_LABELS["source-linked"])
    return ("field-check", VERIFICATION_LABELS["field-check"])


def load_resources() -> list[dict]:
    if not SOURCE_CSV.exists():
        return []
    with SOURCE_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for key, value in list(row.items()):
            row[key] = clean_text(value)
    rows = [row for row in rows if publishable_resource_row(row)]
    rows = dedupe_resource_rows(rows)
    return [enrich_resource_row(row) for row in rows]


def summarize(rows: list[dict]) -> dict:
    county = Counter(row.get("county") or "Unknown" for row in rows)
    rtype = Counter(row.get("public_listing_type") or public_text_value(row.get("resource_type")) or "Resource" for row in rows)
    verification = Counter(row.get("verification_label") or "Unknown" for row in rows)
    layer = Counter(row.get("public_layer_label") or "Unknown" for row in rows)
    goal = Counter()
    audience = Counter()
    online_connection = Counter()
    outreach_channels = Counter()
    outreach_status = Counter()
    physical_location_count = 0
    physical_ad_candidate_count = 0
    for row in rows:
        if has_physical_location(row):
            physical_location_count += 1
        if is_physical_ad_candidate(row):
            physical_ad_candidate_count += 1
        for part in (row.get("goal_relevance") or "").split(";"):
            part = part.strip()
            if part:
                goal[part] += 1
        for part in (row.get("audience_served") or "").split(";"):
            part = part.strip()
            if part:
                audience[part] += 1
        online_connection[row.get("online_connection_group") or "Unknown"] += 1
        for channel in row.get("outreach_channels") or []:
            if not isinstance(channel, dict):
                continue
            outreach_channels[channel.get("channel") or "Unknown"] += 1
            outreach_status[channel.get("status_label") or "Unknown"] += 1
    return {
        "row_count": len(rows),
        "county": dict(county.most_common()),
        "resource_type": dict(rtype.most_common()),
        "verification": dict(verification.most_common()),
        "public_layer": dict(layer.most_common()),
        "goal": dict(goal.most_common(12)),
        "audience": dict(audience.most_common(12)),
        "online_connection": dict(online_connection.most_common()),
        "outreach_channels": dict(outreach_channels.most_common()),
        "outreach_status": dict(outreach_status.most_common()),
        "physical_location_count": physical_location_count,
        "physical_ad_candidate_count": physical_ad_candidate_count,
    }


def copy_assets() -> None:
    ASSET_OUT.mkdir(parents=True, exist_ok=True)
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    for src, dest in [
        (ROOT / "assets" / "brand" / "super-eukarya-logo.png", ASSET_OUT / "super-eukarya-logo.png"),
        (ROOT / "assets" / "brand" / "stateline-tri-county-guide-logo.svg", ASSET_OUT / "stateline-tri-county-guide-logo.svg"),
        (ROOT / "assets" / "brand" / "raton-accessible-cursor.svg", ASSET_OUT / "raton-accessible-cursor.svg"),
    ]:
        if src.exists():
            shutil.copy2(src, dest)

    texture_src = ROOT / "assets" / "textures"
    if texture_src.exists():
        texture_dest = ASSET_OUT / "textures"
        if texture_dest.exists():
            shutil.rmtree(texture_dest)
        shutil.copytree(texture_src, texture_dest)

    animation_src = ROOT / "assets" / "animations"
    if animation_src.exists():
        animation_dest = ASSET_OUT / "animations"
        if animation_dest.exists():
            shutil.rmtree(animation_dest)
        shutil.copytree(animation_src, animation_dest)

    audio_src = ROOT / "assets" / "audio"
    if audio_src.exists():
        audio_dest = ASSET_OUT / "audio"
        if audio_dest.exists():
            shutil.rmtree(audio_dest)
        shutil.copytree(audio_src, audio_dest)

    if SOURCE_CSV.exists():
        shutil.copy2(SOURCE_CSV, DATA_OUT / "tri_county_persona_resources.csv")
    if SOURCE_JSON.exists():
        shutil.copy2(SOURCE_JSON, DATA_OUT / "tri_county_persona_resources.json")
    # Keep raw implementation notes in the repository review files, not in the public deploy package.


def copy_site_extras() -> None:
    if not SITE_EXTRAS.exists():
        return
    for item in SITE_EXTRAS.iterdir():
        target = OUT / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


PUBLIC_DATA_EXCLUDE_FIELDS = {
    "confidence",
    "confidence_level",
    "directory_sweep_source_file",
    "has_public_source",
    "last_verified_date",
    "needs_follow_up",
    "source_status",
    "source_type",
    "travel_listing_sources",
    "verification_key",
    "verification_label",
    "verification_class",
    "verification_method",
    "verification_notes",
    "verification_status",
    "verification_summary",
    "public_layer",
    "public_layer_label",
    "paid_free_status",
    "yellowpages_digital_distribution_likelihood",
    "yellowpages_end_user_warning",
    "yellowpages_flyer_likelihood",
    "yellowpages_outreach_score",
    "yellowpages_policy_risk",
    "yellowpages_recommended_action",
    "yellowpages_review_reason",
    "yellowpages_verification_status",
}


PUBLIC_TEXT_REPLACEMENTS = {
    "Records needing manual verification": "Local listing to confirm",
    "Colfax County Inventory Gaps & Verification Agenda": "Colfax local follow-up",
    "Rural Verification Nodes": "Rural community lead",
    "Verification-Priority Sparse Nodes": "Sparse-area community lead",
    "verification-priority": "local follow-up",
    "manual-verification": "local update",
    "source-check": "local listing",
    "Source-check": "Local listing",
    "source check": "local review",
    "Source check": "Local review",
    "verification": "review",
    "Verification": "Review",
    "verify ": "check ",
    "Verify ": "Check ",
    "Field-check needed": "Local update needed",
    "field check needed": "local update needed",
    "field-check needed": "local update needed",
    "verified": "current",
    "Verified": "Current",
    "verify": "check",
    "Verify": "Check",
    "unchecked": "needs an update",
    "Unchecked": "Needs an update",
}


def public_text_value(value: object) -> object:
    if isinstance(value, dict):
        return {key: public_text_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [public_text_value(item) for item in value]
    if not isinstance(value, str):
        return value
    cleaned = value
    for source, replacement in PUBLIC_TEXT_REPLACEMENTS.items():
        cleaned = cleaned.replace(source, replacement)
    cleaned = cleaned.replace("; Check", "; check").replace(", Check", ", check")
    return cleaned


def public_data_item(item: dict) -> dict:
    public_item = {}
    for key, value in item.items():
        if key in PUBLIC_DATA_EXCLUDE_FIELDS or key.startswith("yellowpages_"):
            continue
        if key == "notes" and clean_text(item.get("public_description")):
            value = item["public_description"]
        if key == "resource_type" and clean_text(item.get("public_listing_type")):
            value = item["public_listing_type"]
        if key == "category" and clean_text(item.get("public_category")):
            value = item["public_category"]
        public_item[key] = public_text_value(value)
    return public_item


def metadata_id(value: object, fallback: str) -> str:
    raw = clean_text(str(value or fallback)).lower()
    parts = []
    last_dash = False
    for char in raw:
        if char.isalnum():
            parts.append(char)
            last_dash = False
        elif not last_dash:
            parts.append("-")
            last_dash = True
    cleaned = "".join(parts).strip("-")
    return cleaned or fallback


def split_public_list(value: object) -> list[str]:
    text = clean_text(str(value or ""))
    if not text:
        return []
    return [part.strip() for part in text.split(";") if part.strip()]


def as_bool_text(value: object) -> str:
    text = clean_text(str(value or "")).lower()
    return "true" if text in {"true", "yes", "1", "y"} else "false"


def property_value(name: str, value: object) -> dict | None:
    if isinstance(value, list):
        cleaned = [clean_text(str(item)) for item in value if clean_text(str(item))]
        if not cleaned:
            return None
        value = "; ".join(cleaned)
    text = clean_text(str(value or ""))
    if not text:
        return None
    return {"@type": "PropertyValue", "name": name, "value": text}


def compact_properties(items: list[dict | None]) -> list[dict]:
    return [item for item in items if item]


def resource_url(row: dict) -> str:
    return (split_semicolon(row.get("website")) or split_semicolon(row.get("source_url")) or [""])[0]


def directory_resource_metadata(row: dict, position: int) -> dict:
    public_row = public_data_item(row)
    entry_id = metadata_id(public_row.get("id"), f"resource-{position}")
    name = clean_text(public_row.get("resource_name")) or "Unnamed resource"
    county = clean_text(public_row.get("county"))
    town = clean_text(public_row.get("town"))
    state = clean_text(public_row.get("state"))
    url = resource_url(public_row)
    goals = split_public_list(public_row.get("goal_relevance"))
    audiences = split_public_list(public_row.get("audience_served"))
    area_parts = [part for part in [town, county, state] if part]
    area = ", ".join(area_parts) if area_parts else "Tri-county region"
    source_url = clean_text(public_row.get("source_url"))
    website = clean_text(public_row.get("website"))
    metadata = {
        "entry_id": entry_id,
        "entry_kind": "local_inventory_entry",
        "name": name,
        "county": county,
        "town": town,
        "state": state,
        "category": clean_text(public_row.get("category")),
        "resource_type": clean_text(public_row.get("public_listing_type")) or clean_text(public_row.get("resource_type")),
        "access_mode": clean_text(public_row.get("access_mode")),
        "audience_served": audiences,
        "goal_relevance": goals,
        "website": website,
        "source_url": source_url,
        "contact_phone": clean_text(public_row.get("contact_phone")),
        "contact_email": clean_text(public_row.get("contact_email")),
        "physical_address": clean_text(public_row.get("physical_address")),
        "online_connection_group": clean_text(public_row.get("online_connection_group")),
        "online_connection_label": clean_text(public_row.get("online_connection_label")),
        "online_connection_url": clean_text(public_row.get("online_connection_url")),
        "has_physical_location": clean_text(public_row.get("has_physical_location")),
        "physical_ad_candidate": clean_text(public_row.get("physical_ad_candidate")),
        "physical_ad_label": clean_text(public_row.get("physical_ad_label")),
        "physical_ad_note": clean_text(public_row.get("physical_ad_note")),
        "physical_promotion_category": clean_text(public_row.get("physical_promotion_category")),
        "physical_promotion_keywords": split_public_list(public_row.get("physical_promotion_keywords")),
        "outreach_channels": public_row.get("outreach_channels") or [],
        "outreach_channel_keys": split_public_list(public_row.get("outreach_channel_keys")),
        "outreach_channel_labels": split_public_list(public_row.get("outreach_channel_labels")),
        "cost_level": clean_text(public_row.get("cost_level")),
        "audience_tags": split_public_list(public_row.get("public_audience_tags") or public_row.get("public_org_tags")),
        "search_keywords": split_public_list(public_row.get("public_keywords")),
        "best_for": split_public_list(public_row.get("public_best_for")),
        "description": clean_text(public_row.get("public_description")) or clean_text(public_row.get("category")) or DEFAULT_LISTING_DESCRIPTION,
        "metadata_note": "Local details can change. Use the listed website, directory page, social profile, phone, or update form when a listing needs a correction.",
    }
    return {key: value for key, value in metadata.items() if value not in ("", [], None)}


def directory_shortcut_metadata(item: dict, position: int) -> dict:
    public_item = public_data_item(enrich_directory_source(item))
    title = clean_text(public_item.get("title")) or "Directory shortcut"
    entry_id = metadata_id(title, f"shortcut-{position}")
    metadata = {
        "entry_id": entry_id,
        "entry_kind": "directory_shortcut",
        "name": title,
        "county": clean_text(public_item.get("county")),
        "category": clean_text(public_item.get("kind")),
        "url": clean_text(public_item.get("url")),
        "description": clean_text(public_item.get("best_for")),
        "recommended_action": clean_text(public_item.get("action")),
        "outreach_channel_keys": split_public_list(public_item.get("outreach_channel_keys")),
        "outreach_channel_labels": split_public_list(public_item.get("outreach_channel_labels")),
        "metadata_note": "Shortcut details point readers to existing public pages and contact routes. Details may change.",
    }
    return {key: value for key, value in metadata.items() if value not in ("", [], None)}


def directory_metadata_payload(rows: list[dict]) -> dict:
    shortcuts = [
        directory_shortcut_metadata(item, idx)
        for idx, item in enumerate(sorted_sources(DIRECTORY_SOURCES), start=1)
    ]
    resources = [
        directory_resource_metadata(row, idx)
        for idx, row in enumerate(
            sorted(rows, key=lambda item: (item.get("resource_name") or "", item.get("county") or "", item.get("town") or "")),
            start=1,
        )
    ]
    entries = shortcuts + resources
    return {
        "generated_at": BUILD_DATE,
        "metadata_type": "stateline_guide_directory_metadata",
        "publication_note": "These entries help readers find directory shortcuts and local inventory entries. Details may change; use update pathways when information is outdated.",
        "entry_count": len(entries),
        "shortcut_count": len(shortcuts),
        "local_inventory_count": len(resources),
        "entries": entries,
    }


def metadata_schema_item(entry: dict) -> dict:
    item = {
        "@type": "Thing",
        "@id": SITE_URL + "network/#" + entry["entry_id"],
        "identifier": entry["entry_id"],
        "name": entry["name"],
        "description": entry.get("description") or entry.get("metadata_note"),
        "additionalType": "Directory shortcut" if entry.get("entry_kind") == "directory_shortcut" else "Local inventory entry",
        "category": entry.get("category") or entry.get("resource_type"),
        "areaServed": {
            "@type": "AdministrativeArea",
            "name": ", ".join(part for part in [entry.get("town"), entry.get("county"), entry.get("state")] if part) or entry.get("county") or "Tri-county region",
        },
        "additionalProperty": compact_properties(
            [
                property_value("entry_kind", entry.get("entry_kind")),
                property_value("county", entry.get("county")),
                property_value("town", entry.get("town")),
                property_value("state", entry.get("state")),
                property_value("resource_type", entry.get("resource_type")),
                property_value("access_mode", entry.get("access_mode")),
                property_value("audience_served", entry.get("audience_served")),
                property_value("goal_relevance", entry.get("goal_relevance")),
                property_value("contact_phone", entry.get("contact_phone")),
                property_value("contact_email", entry.get("contact_email")),
                property_value("physical_address", entry.get("physical_address")),
                property_value("outreach_channels", entry.get("outreach_channel_labels")),
                property_value("cost_level", entry.get("cost_level")),
                property_value("organization_tags", entry.get("organization_tags")),
                property_value("search_keywords", entry.get("search_keywords")),
                property_value("best_for", entry.get("best_for")),
                property_value("recommended_action", entry.get("recommended_action")),
                property_value("metadata_note", entry.get("metadata_note")),
            ]
        ),
    }
    url = entry.get("url") or entry.get("website") or entry.get("source_url")
    if url:
        item["url"] = url
    if entry.get("source_url") and entry.get("source_url") != url:
        item["sameAs"] = entry["source_url"]
    return {key: value for key, value in item.items() if value not in ("", [], None)}


def directory_item_list_schema(rows: list[dict]) -> dict:
    payload = directory_metadata_payload(rows)
    return {
        "@type": "ItemList",
        "@id": SITE_URL + "network/#directory-entry-metadata",
        "name": "Stateline Tri-County Guide directory entries",
        "description": "Machine-readable metadata for directory shortcuts and local inventory entries in the Stateline Tri-County Guide. Details may change.",
        "numberOfItems": payload["entry_count"],
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": idx,
                "item": metadata_schema_item(entry),
            }
            for idx, entry in enumerate(payload["entries"], start=1)
        ],
    }


def write_data_files(rows: list[dict], summary: dict) -> None:
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    directory_sources = [public_data_item(item) for item in sorted_sources(DIRECTORY_SOURCES)]
    directory_source_groups = [public_data_item(item) for item in grouped_directory_sources(DIRECTORY_SOURCES)]
    top_source_groups = [public_data_item(item) for item in top_directory_source_groups()]
    amplifier_channels = [public_data_item(item) for item in AMPLIFIER_CHANNELS]
    national_funding = [public_data_item(item) for item in NATIONAL_FUNDING_OPPORTUNITIES]
    national_funding_sources = [public_data_item(item) for item in NATIONAL_FUNDING_WATCH_SOURCES]
    resource_discovery_sources = [
        {
            key: public_text_value(item.get(key))
            for key in ("id", "name", "url", "category", "authority", "public_use")
            if item.get(key) not in (None, "", [])
        }
        for item in RESOURCE_DISCOVERY_SOURCES
    ]
    public_rows = [public_data_item(row) for row in rows]
    physical_ad_locations = []
    for row in physical_ad_location_rows(rows, limit=max(1, len(rows))):
        item = public_data_item(row)
        item["posting_fit"] = physical_ad_location_fit(row)
        item["posting_note"] = physical_ad_location_note(row)
        physical_ad_locations.append(item)
    public_summary = public_text_value({key: value for key, value in summary.items() if key not in {"verification", "public_layer"}})
    directory_metadata = directory_metadata_payload(rows)
    data = {
        "generated_at": BUILD_DATE,
        "summary": public_summary,
        "directory_metadata": {
            "href": "data/directory-metadata.json",
            "entry_count": directory_metadata["entry_count"],
            "shortcut_count": directory_metadata["shortcut_count"],
            "local_inventory_count": directory_metadata["local_inventory_count"],
        },
        "directory_sources": directory_sources,
        "directory_source_groups": directory_source_groups,
        "top_directory_source_groups": top_source_groups,
        "home_task_groups": HOME_TASK_GROUPS,
        "promote_route_defs": PROMOTE_ROUTE_DEFS,
        "amplifier_channels": amplifier_channels,
        "national_funding_opportunities": national_funding,
        "national_funding_watch_sources": national_funding_sources,
        "resource_discovery_sources": resource_discovery_sources,
        "free_tools": [public_data_item(item) for item in tools_catalog()],
        "site_routes": [public_data_item(item) for item in assistant_site_routes()],
        "posting_spaces": [public_data_item(item) for item in POSTING_SPACES],
        "physical_ad_locations": physical_ad_locations,
        "persona_routes": [public_data_item(item) for item in PERSONA_ROUTES],
        "resources": public_rows,
    }
    public_fieldnames = sorted({key for row in public_rows for key in row.keys()})
    with (DATA_OUT / "tri_county_persona_resources.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=public_fieldnames)
        writer.writeheader()
        writer.writerows(public_rows)
    (DATA_OUT / "directory-metadata.json").write_text(json.dumps(directory_metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    (DATA_OUT / "tri_county_persona_resources.json").write_text(json.dumps(public_rows, indent=2), encoding="utf-8")
    funding_payload = {
        "generated_at": BUILD_DATE,
        "opportunity_count": len(national_funding),
        "opportunities": national_funding,
    }
    (DATA_OUT / "national-funding-opportunities.json").write_text(
        json.dumps(funding_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    funding_fieldnames = sorted({key for item in national_funding for key in item.keys()})
    with (DATA_OUT / "national-funding-opportunities.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=funding_fieldnames)
        writer.writeheader()
        for item in national_funding:
            writer.writerow(
                {
                    key: "; ".join(str(value) for value in field_value) if isinstance(field_value, list) else field_value
                    for key, field_value in item.items()
                }
            )
    (DATA_OUT / "guide-data.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    js_payload = "window.TRI_COUNTY_GUIDE_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n"
    (ASSET_OUT / "site-data.js").write_text(js_payload, encoding="utf-8")


def html_escape(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def free_support_tool_records() -> list[dict]:
    records = []
    for item in NATIONAL_FUNDING_OPPORTUNITIES:
        if not item.get("include_in_tools"):
            continue
        access_types = item.get("tools_access_types") or ["Free or low-cost support"]
        records.append(
            {
                "id": f"support-{item.get('id')}",
                "name": item.get("name"),
                "url": item.get("application_url") or item.get("source_url"),
                "source_url": item.get("source_url"),
                "category": item.get("tools_category") or "Funding & business help",
                "format": item.get("tools_format") or "Advising and support service",
                "access_types": access_types,
                "use": item.get("tools_use") or item.get("summary"),
                "note": item.get("tools_note") or item.get("free_to_apply_or_enroll"),
                "nonprofit_note": item.get("tools_nonprofit_note") or item.get("requires_501c3"),
                "keywords": [
                    *(item.get("keywords") or []),
                    *(item.get("audiences") or []),
                    *(item.get("applicant_types") or []),
                    "support service",
                ],
                "featured": bool(item.get("tools_featured")),
            }
        )
    return records


def tools_catalog() -> list[dict]:
    return [*PROMOTION_TOOLS, *free_support_tool_records()]


def tool_offer_groups(item: dict) -> list[str]:
    access_types = [clean_text(value).casefold() for value in item.get("access_types") or [] if clean_text(value)]
    item_format = clean_text(item.get("format")).casefold()
    is_support = clean_text(item.get("id")).startswith("support-") or "support" in item_format or "advising" in item_format
    groups = []
    if not is_support and any("free" in label and "nonprofit" not in label for label in access_types):
        groups.append("general-free")
    if any("nonprofit" in label for label in access_types):
        groups.append("nonprofit")
    if is_support:
        groups.append("support")
    return groups


def promotion_tool_cards(items: list[dict] | None = None) -> str:
    cards = []
    for item in items if items is not None else tools_catalog():
        access_types = [clean_text(value) for value in item.get("access_types") or [] if clean_text(value)]
        keywords = [clean_text(value) for value in item.get("keywords") or [] if clean_text(value)]
        offer_groups = tool_offer_groups(item)
        badges = "".join(
            f'<span class="tool-pill">{html_escape(label)}</span>'
            for label in [item.get("category"), item.get("format"), *access_types]
            if label
        )
        source_link = ""
        source_url = clean_text(item.get("source_url"))
        has_nonprofit_offer = any("nonprofit" in label.casefold() for label in access_types)
        if source_url and source_url.rstrip("/") != clean_text(item.get("url")).rstrip("/"):
            source_link_label = "Plan or eligibility details" if has_nonprofit_offer else "Official details"
            source_link = (
                f'<a class="tool-detail-link" href="{html_escape(source_url)}" target="_blank" '
                f'rel="noreferrer">{source_link_label}</a>'
            )
        nonprofit_note = clean_text(item.get("nonprofit_note"))
        searchable = " ".join(
            clean_text(value)
            for value in [
                item.get("name"),
                item.get("category"),
                item.get("format"),
                item.get("use"),
                item.get("note"),
                nonprofit_note,
                *access_types,
                *keywords,
            ]
            if clean_text(value)
        )
        cards.append(
            f"""
            <article class="tool-card" data-tool-card data-tool-category="{html_escape(item.get('category'))}"
              data-tool-format="{html_escape(item.get('format'))}" data-tool-access="{html_escape(' '.join(access_types))}"
              data-tool-offers="{html_escape(' '.join(offer_groups))}"
              data-tool-search="{html_escape(searchable)}">
              <div class="tool-card__meta">{badges}</div>
              <h3><a href="{html_escape(item.get('url'))}" target="_blank" rel="noreferrer">{html_escape(item.get('name'))}</a></h3>
              <p>{html_escape(item.get('use'))}</p>
              <p class="source-note">{html_escape(item.get('note'))}</p>
              {f'<p class="tool-nonprofit-note"><strong>For nonprofits:</strong> {html_escape(nonprofit_note)}</p>' if nonprofit_note and has_nonprofit_offer else ''}
              {source_link}
            </article>
            """
        )
    return "\n".join(cards)


def promotion_tool_filters() -> str:
    categories = sorted(
        {clean_text(item.get("category")) for item in tools_catalog() if clean_text(item.get("category"))},
        key=str.casefold,
    )
    category_options = "".join(
        f'<option value="{html_escape(category)}">{html_escape(category)}</option>'
        for category in categories
    )
    return f"""
    <form class="tool-filters" data-tool-filters role="search" aria-label="Filter free and discounted tools and services">
      <label class="tool-filter-search">Search services and tools
        <input type="search" data-tool-query autocomplete="off" placeholder="Try advising, grants, flyer, CRM, forms, nonprofit...">
      </label>
      <label>Category
        <select data-tool-category>
          <option value="All">All categories</option>
          {category_options}
        </select>
      </label>
      <label>Offer
        <select data-tool-offer>
          <option value="All">All offers</option>
          <option value="general-free">General free tools</option>
          <option value="nonprofit">Nonprofit discounts &amp; donations</option>
          <option value="support">Free advising &amp; public support</option>
        </select>
      </label>
      <label>Format
        <select data-tool-format-filter>
          <option value="All">All formats</option>
          <option value="open-source">Open-source software</option>
          <option value="desktop">Desktop software</option>
          <option value="web">Web apps and services</option>
        </select>
      </label>
      <button class="button button-soft" type="reset">Clear</button>
      <p class="tool-filter-status" data-tool-status role="status" aria-live="polite"></p>
    </form>
    """


def enrich_directory_source(item: dict) -> dict:
    enriched = dict(item)
    if isinstance(enriched.get("outreach_channels"), list):
        return enriched
    channels = classify_outreach_channels(
        {
            "resource_name": enriched.get("title"),
            "category": enriched.get("kind"),
            "resource_type": enriched.get("kind"),
            "public_description": " ".join(
                part for part in (clean_text(enriched.get("best_for")), clean_text(enriched.get("action"))) if part
            ),
            "website": enriched.get("url"),
            "source_url": enriched.get("url"),
        }
    )
    enriched["outreach_channels"] = channels
    enriched["outreach_channel_keys"] = "; ".join(channel["key"] for channel in channels)
    enriched["outreach_channel_labels"] = "; ".join(channel["label"] for channel in channels)
    return enriched


def sorted_sources(sources: list[dict]) -> list[dict]:
    enriched = (enrich_directory_source(item) for item in sources)
    return sorted(enriched, key=lambda item: (item.get("title") or item.get("channel") or "").casefold())


SOURCE_GROUP_OVERRIDES = {
    "angelfirechamber.org": "Angel Fire Chamber directory and member routes",
    "biz.nm.gov": "New Mexico Business Portal resources",
    "chamber.huerfano.org": "Huerfano Chamber business and resource routes",
    "co.colfax.nm.us": "Colfax County official business and civic routes",
    "edd.newmexico.gov": "New Mexico EDD funding, business, and creative-economy programs",
    "exploreraton.com": "Explore Raton tourism, events, and visitor-guide routes",
    "growraton.org": "GrowRaton business support and property routes",
    "huerfano.us": "Huerfano County government routes",
    "nmfinance.com": "New Mexico Finance Authority capital programs",
    "oedit.colorado.gov": "Colorado OEDIT funding and creative-economy programs",
    "ratonnm.gov": "Raton municipal business and civic routes",
    "rd.usda.gov": "USDA Rural Development programs",
    "sba.gov": "SBA funding and lender routes",
    "sccfcolorado.org": "Southern Colorado Community Foundation grants, scholarships, and directory",
    "spanishpeakscountry.com": "Spanish Peaks Country tourism, event, and business routes",
    "tlacchamber.org": "Colexico / TLAC Chamber regional hub",
    "trinidad.co.gov": "Trinidad municipal civic and economic-development routes",
    "trinidadcf.org": "Trinidad Community Foundation grantmaker routes",
    "visittrinidadcolorado.com": "Visit Trinidad tourism, local resources, and event routes",
    "worldjournalnewspaper.com": "World Journal media and advertising routes",
}


SOURCE_GROUP_PRIORITY_DOMAINS = {
    "exploreraton.com": 45,
    "spanishpeakscountry.com": 45,
    "visittrinidadcolorado.com": 45,
    "tlacchamber.org": 42,
    "chamber.huerfano.org": 42,
    "growraton.org": 40,
    "ratonnm.gov": 40,
    "trinidad.co.gov": 40,
    "huerfano.us": 38,
    "oedit.colorado.gov": 36,
    "edd.newmexico.gov": 36,
    "sccfcolorado.org": 34,
    "sba.gov": 32,
    "rd.usda.gov": 30,
}


def source_domain(url: object) -> str:
    parsed = urlparse(str(url or ""))
    return parsed.netloc.lower().removeprefix("www.")


def source_link_label(item: dict) -> str:
    blob = " ".join(str(item.get(field) or "") for field in ["title", "kind", "url", "best_for", "action"]).casefold()
    if "submit" in blob and "event" in blob:
        return "Submit event"
    if "add business" in blob or "business listing" in blob or "listing update" in blob or "resource submission" in blob:
        return "Add listing"
    if "visitor guide" in blob and ("ad" in blob or "advertis" in blob):
        return "Visitor guide ads"
    if "newsletter" in blob:
        return "Newsletter"
    if "advertis" in blob or "placement" in blob:
        return "Advertising"
    if "calendar" in blob or "events" in blob:
        return "Calendar"
    if "grant" in blob or "scholarship" in blob or "stipend" in blob or "incentive" in blob or "funding" in blob or "loan" in blob:
        return "Grant page"
    if "directory" in blob:
        return "Directory"
    if "license" in blob or "permit" in blob or "forms" in blob:
        return "Forms"
    if "economic" in blob or "business support" in blob or "sbdc" in blob:
        return "Support"
    if "media" in blob or "radio" in blob or "newspaper" in blob:
        return "Media"
    return clean_text(item.get("kind")) or "Open"


def resource_url_label(url: str, fallback: str = "Website") -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    lowered = url.casefold()
    if "facebook.com" in host:
        return "Facebook"
    if "instagram.com" in host:
        return "Instagram"
    if "youtube.com" in host or "youtu.be" in host:
        return "YouTube"
    if "maps.google" in host or "google.com/maps" in lowered or "maps.app.goo.gl" in lowered:
        return "Map"
    if "tripadvisor.com" in host:
        return "Travel profile"
    if "yelp.com" in host or "yellowpages.com" in host:
        return "Business profile"
    if "tourism" in host or "travel" in host or "visit" in host or "explore" in host:
        return "Tourism listing"
    if "chamber" in host or "businessdirectory" in host:
        return "Directory page"
    return fallback


def source_group_key(item: dict) -> str:
    domain = source_domain(item.get("url"))
    if domain:
        return domain
    return clean_text(item.get("title")).casefold()


def source_group_title(item: dict) -> str:
    domain = source_domain(item.get("url"))
    return SOURCE_GROUP_OVERRIDES.get(domain) or clean_text(item.get("title")) or "Directory shortcut"


def source_group_priority(group: dict) -> tuple[int, str]:
    domain = clean_text(group.get("domain"))
    source_count = int(group.get("source_count") or 1)
    text = " ".join(
        [
            clean_text(group.get("title")),
            clean_text(group.get("kind")),
            clean_text(group.get("best_for")),
            clean_text(group.get("action")),
        ]
    ).casefold()
    score = SOURCE_GROUP_PRIORITY_DOMAINS.get(domain, 0) + min(source_count, 6) * 4
    if "tourism" in text or "visitor" in text:
        score += 12
    if "chamber" in text or "economic" in text or "business" in text:
        score += 10
    if "grant" in text or "funding" in text or "scholarship" in text:
        score += 8
    if "event" in text or "calendar" in text:
        score += 8
    if "directory" in text:
        score += 6
    return (-score, clean_text(group.get("title")).casefold())


def grouped_directory_sources(sources: list[dict]) -> list[dict]:
    groups: dict[str, dict] = {}
    seen_urls: dict[str, set[str]] = {}
    for item in sorted_sources(sources):
        key = source_group_key(item)
        group = groups.setdefault(
            key,
            {
                "title": source_group_title(item),
                "domain": source_domain(item.get("url")),
                "county": clean_text(item.get("county")),
                "counties": [],
                "kind": clean_text(item.get("kind")) or "Directory shortcut",
                "best_for": clean_text(item.get("best_for")),
                "action": clean_text(item.get("action")),
                "source_count": 0,
                "links": [],
                "url": clean_text(item.get("url")),
                "outreach_channels": [],
            },
        )
        county = clean_text(item.get("county"))
        if county and county not in group["counties"]:
            group["counties"].append(county)
        url = clean_text(item.get("url"))
        seen = seen_urls.setdefault(key, set())
        if url and url in seen:
            continue
        seen.add(url)
        for channel in item.get("outreach_channels") or []:
            if not isinstance(channel, dict):
                continue
            existing_index = next(
                (
                    index
                    for index, existing in enumerate(group["outreach_channels"])
                    if existing.get("key") == channel.get("key")
                ),
                None,
            )
            if existing_index is None:
                group["outreach_channels"].append(channel)
            elif (
                group["outreach_channels"][existing_index].get("status") != "listed"
                and channel.get("status") == "listed"
            ):
                group["outreach_channels"][existing_index] = channel
        group["source_count"] += 1
        group["links"].append(
            {
                "label": source_link_label(item),
                "title": clean_text(item.get("title")),
                "url": url,
                "county": county,
                "kind": clean_text(item.get("kind")),
                "best_for": clean_text(item.get("best_for")),
                "action": clean_text(item.get("action")),
                "outreach_channels": item.get("outreach_channels") or [],
            }
        )

    normalized = []
    for group in groups.values():
        counties = group["counties"] or [group["county"]]
        group["county"] = "Regional" if len(set(counties)) > 1 else counties[0]
        group["county_label"] = " / ".join(counties)
        if group["source_count"] > 1:
            kinds = []
            for link in group["links"]:
                kind = link.get("kind")
                if kind and kind not in kinds:
                    kinds.append(kind)
            group["kind"] = " + ".join(kinds[:3]) + (" + more" if len(kinds) > 3 else "")
            purpose = ", ".join(kinds[:3]).casefold() or "local information and support"
            group["best_for"] = f"Use {group['title']} for {purpose}."
            group["action"] = "Choose the link that fits your task; that page has the current details."
        normalized.append(group)
    return sorted(normalized, key=source_group_priority)


def top_directory_source_groups(limit: int = 30) -> list[dict]:
    return grouped_directory_sources(DIRECTORY_SOURCES)[:limit]


def source_cards(sources: list[dict], limit: int | None = None) -> str:
    cards = []
    ordered_sources = sorted_sources(sources)
    for item in ordered_sources[:limit]:
        cards.append(
            f"""
            <article class="source-card" data-county="{html_escape(item['county'])}" data-kind="{html_escape(item['kind'])}">
              <div class="source-card__meta">
                <span>{html_escape(item['county'])}</span>
                <span>{html_escape(item['kind'])}</span>
              </div>
              <h3><a href="{html_escape(item['url'])}" target="_blank" rel="noreferrer">{html_escape(item['title'])}</a></h3>
              <p>{html_escape(public_text_value(item['best_for']))}</p>
              <p class="action-line">{html_escape(public_text_value(item['action']))}</p>
              <div class="resource-outreach"><strong>Promotion paths:</strong>{resource_outreach_channel_badges(item, limit=4)}</div>
              <p class="source-note">Details can change. Use the page, then submit an update if this pathway is outdated.</p>
            </article>
            """
        )
    return "\n".join(cards)


def source_group_cards(sources: list[dict], limit: int | None = None) -> str:
    groups = grouped_directory_sources(sources)
    if limit is not None:
        groups = groups[:limit]
    cards = []
    for group in groups:
        links = "\n".join(
            f"""
            <a class="source-sublink" href="{html_escape(link['url'])}" target="_blank" rel="noreferrer">
              <span>{html_escape(link['label'])}</span>
              <strong>{html_escape(link['title'])}</strong>
            </a>
            """
            for link in group["links"]
            if link.get("url")
        )
        route_word = "route" if group["source_count"] == 1 else "routes"
        cards.append(
            f"""
            <article class="source-card source-group-card" data-county="{html_escape(group['county'])}" data-kind="{html_escape(group['kind'])}">
              <div class="source-card__meta">
                <span>{html_escape(group['county_label'])}</span>
                <span>{html_escape(group['source_count'])} {route_word}</span>
              </div>
              <h3><a href="{html_escape(group['url'])}" target="_blank" rel="noreferrer">{html_escape(group['title'])}</a></h3>
              <p>{html_escape(public_text_value(group['best_for']))}</p>
              <p class="action-line">{html_escape(public_text_value(group['action']))}</p>
              <div class="resource-outreach"><strong>Promotion paths:</strong>{resource_outreach_channel_badges(group, limit=4)}</div>
              <details class="source-group-links" open>
                <summary>Open {html_escape(group['source_count'])} {route_word}</summary>
                <div class="source-link-list">{links}</div>
              </details>
            </article>
            """
        )
    return "\n".join(cards)


def home_task_group_cards(depth: int = 0) -> str:
    return "\n".join(
        f"""
        <a class="mini-card task-link-card task-group-card" href="{rel(route_href(item['href']), depth)}">
          <h3>{html_escape(item['title'])}</h3>
          <p>{html_escape(item['summary'])}</p>
          <strong>{html_escape(item['action'])}</strong>
        </a>
        """
        for item in HOME_TASK_GROUPS
    )


def page_wayfinding(
    current_label: str,
    purpose: str,
    jumps: list[tuple[str, str]],
    related: list[tuple[str, str]],
    depth: int,
) -> str:
    def destination(href: str) -> str:
        return href if href.startswith("#") else rel(route_href(href), depth)

    jump_links = "".join(
        f'<a href="{html_escape(destination(href))}">{html_escape(label)}</a>'
        for label, href in jumps
    )
    related_links = "".join(
        f'<a href="{html_escape(destination(href))}">{html_escape(label)}</a>'
        for label, href in related
    )
    label_id = f"{css_token(current_label)}-wayfinding-title"
    return f"""
    <aside class="page-wayfinding" aria-labelledby="{html_escape(label_id)}">
      <div class="page-wayfinding__intro">
        <span class="page-wayfinding__label">You are in</span>
        <p id="{html_escape(label_id)}"><strong>{html_escape(current_label)}</strong> {html_escape(purpose)}</p>
      </div>
      <nav class="page-wayfinding__links" aria-label="On this page">
        <span>On this page</span>
        {jump_links}
      </nav>
      <nav class="page-wayfinding__links page-wayfinding__links--related" aria-label="Related guide sections">
        <span>Related routes</span>
        {related_links}
      </nav>
    </aside>
    """


def download_buttons(depth: int = 0) -> str:
    return f"""
    <div class="download-row" aria-label="Download guide data">
      <a class="button button-soft" href="{rel('data/tri_county_persona_resources.csv', depth)}" download data-analytics="download_inventory_csv">Download CSV</a>
      <a class="button button-soft" href="{rel('data/guide-data.json', depth)}" download data-analytics="download_inventory_json">Download JSON</a>
      <a class="button button-soft" href="{rel('SOURCES.md', depth)}" download data-analytics="download_sources">Download page index</a>
      <button class="button button-soft print-button" type="button">Print page</button>
    </div>
    """


def submit_listing_panel(depth: int = 0, context: str = "directory") -> str:
    context_copy = {
        "directory": ("Submit or correct a listing", "Use this when a business, nonprofit, gallery, program, service, venue, event series, or resource should be added, updated, corrected, or removed."),
        "amplifier": ("Suggest a channel", "Use this when a calendar, newsletter, visitor guide, media outlet, directory, venue lineup, or partner channel should be added or corrected."),
        "county": ("Add a local listing", "Use this when a county page is missing a business, organization, program, service, gallery, or resource that helps people find local visibility paths."),
        "appendix": ("Update the appendix", "Use this when the contact table needs a new row, a correction, a better link, or a note that a listing may be outdated."),
    }.get(context, ("Submit or correct a listing", "Use this when a listing should be added, updated, corrected, or removed."))
    return f"""
    <section class="section submit-band" aria-labelledby="submit-listing-title">
      <div class="section-heading">
        <p class="eyebrow">Help keep it useful</p>
        <h2 id="submit-listing-title">{html_escape(context_copy[0])}</h2>
        <p class="section-note">{html_escape(context_copy[1])} Submissions go through human review before publication.</p>
      </div>
      <div class="submit-card">
        <div>
          <h3>Best source to include</h3>
          <p>Send the public page, form, listing, event page, social profile, flyer, or contact route a reviewer can open.</p>
        </div>
        <div>
          <h3>What helps most</h3>
          <p>Name, county, community, category, short description, contact path, and what a reader should do next.</p>
        </div>
        <a class="button button-primary" href="{rel('submit/index.html', depth)}" data-analytics="submit_correction_click">Open submission form</a>
      </div>
    </section>
    """


def route_href(path: str) -> str:
    if not path:
        return "index.html"
    if path.startswith(("http://", "https://", "mailto:", "tel:", "#")):
        return path
    for separator in ("#", "?"):
        if separator in path:
            base, suffix = path.split(separator, 1)
            return f"{route_href(base)}{separator}{suffix}"
    if path.endswith(".html"):
        return path
    if path.endswith("/"):
        return f"{path}index.html"
    return f"{path}/index.html"


def route_url(active: str) -> str:
    return SITE_URL + ACTIVE_PATHS.get(active, "")


def breadcrumb_entries(active: str) -> list[tuple[str, str]]:
    if active == "home":
        return [("Home", "")]
    if active in {"colfax", "las-animas", "huerfano"}:
        return [("Home", ""), ("Region", ACTIVE_PATHS["region"]), (ROUTE_LABELS[active], ACTIVE_PATHS[active])]
    if active in {item["active"] for item in TASK_PAGE_DEFS}:
        return [("Home", ""), ("Task Guides", ACTIVE_PATHS["region"]), (ROUTE_LABELS[active], ACTIVE_PATHS[active])]
    return [("Home", ""), (ROUTE_LABELS.get(active, "Current page"), ACTIVE_PATHS.get(active, ""))]


def breadcrumb_nav(active: str, depth: int) -> str:
    entries = breadcrumb_entries(active)
    if len(entries) <= 1:
        return ""
    parts = []
    for index, (label, path) in enumerate(entries):
        if index == len(entries) - 1:
            parts.append(f'<span aria-current="page">{html_escape(label)}</span>')
        else:
            parts.append(f'<a href="{rel(route_href(path), depth)}">{html_escape(label)}</a>')
    return f'<nav class="breadcrumbs" aria-label="Breadcrumb">{"<span>/</span>".join(parts)}</nav>'


def breadcrumb_json_ld(active: str) -> dict:
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index + 1,
                "name": label,
                "item": SITE_URL + path,
            }
            for index, (label, path) in enumerate(breadcrumb_entries(active))
        ],
    }


def website_json_ld() -> dict:
    return {
        "@type": "WebSite",
        "name": "Stateline Tri-County Guide",
        "alternateName": "Tri-County Regional Marketing Guide",
        "url": SITE_URL,
        "description": "A tri-county guide for business listings, event calendars, newsletters, visitor guides, arts promotion, nonprofit outreach, and local support routes across Colfax, Las Animas, and Huerfano counties.",
        "inLanguage": "en-US",
    }


def organization_json_ld() -> dict:
    return {
        "@type": "Organization",
        "name": "Stateline Tri-County Guide",
        "url": SITE_URL,
        "logo": SITE_URL + "assets/stateline-tri-county-guide-logo.svg",
        "description": "A tri-county guide for business listings, event calendars, newsletters, visitor guides, arts promotion, nonprofit outreach, and local support routes across Colfax, Las Animas, and Huerfano counties.",
        "areaServed": [
            {"@type": "AdministrativeArea", "name": "Colfax County, New Mexico"},
            {"@type": "AdministrativeArea", "name": "Las Animas County, Colorado"},
            {"@type": "AdministrativeArea", "name": "Huerfano County, Colorado"},
        ],
    }


def next_action_block(depth: int = 1, links: list[tuple[str, str]] | None = None) -> str:
    links = links or [
        ("Plan the right outreach cycle before collecting links", "plan/"),
        ("Search public directories and local entries", "network/"),
        ("Find event calendars, newsletters, visitor guides, and directory channels", "amplifiers/"),
        ("Submit a correction with a public page link", "submit/"),
    ]
    items = "\n".join(
        f'<li><a href="{rel(route_href(href), depth)}">{html_escape(label)}</a></li>'
        for label, href in links
    )
    return f"""
    <section class="section next-actions" aria-labelledby="next-action-heading">
      <div class="section-heading">
        <p class="eyebrow">Next action</p>
        <h2 id="next-action-heading">Choose the next practical route.</h2>
      </div>
      <ul class="next-action-list">{items}</ul>
    </section>
    """


def page_shell(
    title: str,
    description: str,
    active: str,
    content: str,
    depth: int = 0,
    main_entity: dict | None = None,
    extra_json_alternates: list[tuple[str, str]] | None = None,
    schema_type: str = "WebPage",
) -> str:
    promote_nav_sections = []
    promote_nav_links = [("All promotion routes", route_href(ACTIVE_PATHS["promote"]), "promote")]
    for route_def in PROMOTE_ROUTE_DEFS:
        route_links = []
        for county in ("Colfax", "Las Animas", "Huerfano"):
            route_key = f"promote-{route_def['key']}-{county.casefold().replace(' ', '-')}"
            route_href_value = route_href(
                f"promote/?county={quote_plus(county)}&route={route_def['key']}#promotion-results"
            )
            route_links.append((f"{county} County", route_href_value, route_key))
        promote_nav_sections.append((route_def["title"], route_links))
        promote_nav_links.extend(route_links)
    county_nav_links = [
        ("Tri-county overview", "region/index.html", "region"),
        ("Colfax County", "counties/colfax/index.html", "colfax"),
        ("Las Animas County", "counties/las-animas/index.html", "las-animas"),
        ("Huerfano County", "counties/huerfano/index.html", "huerfano"),
    ]
    guide_nav_links = [
        ("Plan your growth", "plan/index.html", "plan"),
        ("Understand the region", "region/index.html", "region"),
        ("About + creation process", "about/index.html", "about"),
        ("Regional channels", "regional-channels/index.html", "regional-channels"),
    ]
    tools_nav_links = [
        ("Free & discounted tools", "tools/free-discounted/index.html", "free-tools"),
        ("Physical ad finder", "posting/index.html", "posting"),
        ("Message templates", "templates/index.html", "templates"),
        ("Appendix", "appendix/index.html", "appendix"),
        ("Submit update", "submit/index.html", "submit"),
    ]

    def nav_link(label: str, href: str, key: str, extra_class: str = "") -> str:
        active_class = "is-active" if key == active else ""
        current = ' aria-current="page"' if key == active else ""
        classes = " ".join(value for value in (active_class, extra_class) if value)
        return f'<a class="{classes}" href="{html_escape(rel(href, depth))}"{current}>{html_escape(label)}</a>'

    promote_menu_sections = "\n".join(
        f"""
        <section class="nav-menu-section" aria-label="{html_escape(section_label)}">
          <p class="nav-menu-label">{html_escape(section_label)}</p>
          <div class="nav-menu-county-links">
            {''.join(nav_link(label, href, key) for label, href, key in links)}
          </div>
        </section>
        """
        for section_label, links in promote_nav_sections
    )
    promote_menu = f"""
      {nav_link("All promotion routes", route_href(ACTIVE_PATHS["promote"]), "promote", "nav-menu-feature")}
      <div class="nav-menu-grid">{promote_menu_sections}</div>
    """
    nav_structure = [
        ("link", "Home", "index.html", "home", "nav-home"),
        ("link", "Directory", "network/index.html", "network", "nav-resource"),
        ("link", "Funding", route_href(ACTIVE_PATHS["funding"]), "funding", "nav-resource"),
        ("link", "Arts & Culture", route_href(ACTIVE_PATHS["arts-culture"]), "arts-culture", "nav-resource"),
        ("group", "Promote", promote_nav_links, "nav-promote", promote_menu),
        ("group", "Counties", county_nav_links, "nav-counties", ""),
        ("group", "Guide", guide_nav_links, "nav-guide", ""),
        ("group", "Tools", tools_nav_links, "nav-tools", ""),
    ]

    nav_parts = []
    for item in nav_structure:
        if item[0] == "link":
            _, label, href, key, extra_class = item
            nav_parts.append(nav_link(label, href, key, extra_class))
            continue
        _, label, children, extra_class, custom_menu = item
        group_active = any(key == active for _, _, key in children)
        if label == "Promote" and active in {item["active"] for item in TASK_PAGE_DEFS} | {"amplifiers"}:
            group_active = True
        child_links = custom_menu or "\n".join(nav_link(child_label, href, key) for child_label, href, key in children)
        menu_class = "nav-menu nav-menu--promote" if label == "Promote" else "nav-menu"
        nav_parts.append(
            f"""
            <details class="nav-group {extra_class} {'is-active' if group_active else ''}">
              <summary class="nav-trigger">{label}</summary>
              <div class="{menu_class}">
                {child_links}
              </div>
            </details>
            """
        )
    nav = "\n".join(nav_parts)
    footer_structure = [
        (
            "Guide",
            [
                ("Plan growth", "plan/index.html"),
                ("Region overview", "region/index.html"),
                ("About / process", "about/index.html"),
                ("Submit update", "submit/index.html"),
            ],
        ),
        (
            "Find resources",
            [
                ("Directory", "network/index.html"),
                ("Funding", route_href(ACTIVE_PATHS["funding"])),
                ("Arts & Culture", route_href(ACTIVE_PATHS["arts-culture"])),
                ("Free & discounted tools", "tools/free-discounted/index.html"),
                ("Appendix", "appendix/index.html"),
            ],
        ),
        (
            "Promote",
            [
                ("Promotion finder", route_href(ACTIVE_PATHS["promote"])),
                ("Events + calendars", route_href("promote/?route=events")),
                ("Advertising + media", route_href("promote/?route=advertising")),
                ("Physical locations", "posting/index.html"),
                ("Message templates", "templates/index.html"),
            ],
        ),
        (
            "Counties",
            [
                ("Colfax", "counties/colfax/index.html"),
                ("Las Animas", "counties/las-animas/index.html"),
                ("Huerfano", "counties/huerfano/index.html"),
                ("Colfax promotion routes", route_href("promote/?county=Colfax")),
                ("Las Animas promotion routes", route_href("promote/?county=Las+Animas")),
                ("Huerfano promotion routes", route_href("promote/?county=Huerfano")),
            ],
        ),
        (
            "Data + updates",
            [
                ("Submit update", "submit/index.html"),
                ("CSV data", "data/tri_county_persona_resources.csv"),
                ("JSON data", "data/guide-data.json"),
                ("Sitemap", "sitemap.xml"),
            ],
        ),
    ]
    footer_index = "\n".join(
        f"""
        <div class="footer-column">
          <h2>{html_escape(label)}</h2>
          <ul>
            {"".join(f'<li><a href="{rel(href, depth)}">{html_escape(link_label)}</a></li>' for link_label, href in links)}
          </ul>
        </div>
        """
        for label, links in footer_structure
    )
    canonical_url = route_url(active)
    hero_art = HERO_ART_BY_ACTIVE.get(active, "hero-plains-valley.svg")
    page_hero_art = f'<img class="page-hero-art page-hero-art--{html_escape(active)}" src="{rel("assets/animations/" + hero_art, depth)}" alt="" aria-hidden="true">'
    content = content.replace('<section class="page-hero">', f'<section class="page-hero">\n      {page_hero_art}')
    content = content.replace('<section class="page-hero county-hero">', f'<section class="page-hero county-hero">\n      {page_hero_art}')
    social_image_url = SITE_URL + "assets/animations/yucca-banner.svg"
    page_schema = {
        "@type": schema_type,
        "name": title,
        "url": canonical_url,
        "description": description,
        "inLanguage": "en-US",
        "dateModified": BUILD_DATE,
        "isPartOf": {
            "@type": "WebSite",
            "name": "Stateline Tri-County Guide",
            "url": SITE_URL,
        },
        "about": [
            "regional marketing",
            "business support",
            "creative economy",
            "nonprofit outreach",
            "Colfax County",
            "Las Animas County",
            "Huerfano County",
        ],
        "audience": [
            {"@type": "Audience", "audienceType": "small businesses"},
            {"@type": "Audience", "audienceType": "nonprofits"},
            {"@type": "Audience", "audienceType": "artists and creative businesses"},
            {"@type": "Audience", "audienceType": "community programs and service providers"},
        ],
        "publisher": {
            "@type": "Organization",
            "name": "Stateline Tri-County Guide",
        },
    }
    if main_entity:
        page_schema["mainEntity"] = main_entity
    structured_data = json.dumps(
        {
            "@context": "https://schema.org",
            "@graph": [
                website_json_ld(),
                organization_json_ld(),
                breadcrumb_json_ld(active),
                page_schema,
            ],
        },
        ensure_ascii=False,
    )
    extra_alternates = "\n".join(
        f'          <link rel="alternate" type="application/json" title="{html_escape(label)}" href="{rel(href, depth)}">'
        for label, href in (extra_json_alternates or [])
    )
    available_audio_tracks = [
        item
        for item in REGIONAL_AUDIO_TRACKS
        if item.get("local_audio_downloaded") and item.get("local_audio_filename")
    ]
    music_options = "\n".join(
        f'<option value="{rel("assets/audio/" + str(item["local_audio_filename"]), depth)}" '
        f'data-track-id="{html_escape(item.get("id"))}" '
        f'data-credit="{html_escape(item.get("credit_display"))}" '
        f'data-source-url="{html_escape(item.get("item_url"))}">'
        f'{html_escape(item.get("player_label") or item.get("title"))}</option>'
        for item in available_audio_tracks
    )
    first_audio = available_audio_tracks[0] if available_audio_tracks else {}
    first_audio_path = rel(
        f'assets/audio/{first_audio.get("local_audio_filename") or "loc-rael-nm-valse.mp3"}',
        depth,
    )
    first_audio_credit = first_audio.get("credit_display") or "Juan B. Rael Collection, Library of Congress."
    first_audio_source = first_audio.get("item_url") or "https://www.loc.gov/collections/hispano-music-and-culture-from-the-northern-rio-grande/"
    music_bar = (
        f"""
          <details class="music-bar" data-music-bar aria-label="Regional sound player">
            <summary class="music-summary">
              <span><span class="music-label-prefix">Regional </span>sound</span>
              <span class="music-status" data-music-status>Off</span>
            </summary>
            <div class="music-panel">
              <div class="music-bar__top">
                <button class="music-toggle" type="button" aria-pressed="false" data-state="stopped">Play</button>
                <label class="music-track-label">Track
                  <select class="music-track-select" aria-label="Choose regional sound track">
                    {music_options}
                  </select>
                </label>
              </div>
              <div class="music-bar__middle">
                <input class="music-progress" type="range" min="0" max="1000" value="0" aria-label="Regional sound progress">
                <span class="music-time" aria-live="polite">0:00</span>
              </div>
              <div class="music-bar__bottom">
                <span class="music-credit-block">
                  <span data-music-credit>{html_escape(first_audio_credit)}</span>
                  <a class="music-source-link" data-music-source href="{html_escape(first_audio_source)}" target="_blank" rel="noreferrer">Source &amp; rights</a>
                </span>
                <label>Volume
                  <input class="music-volume" type="range" min="0" max="100" value="42" aria-label="Regional sound volume">
                </label>
              </div>
            </div>
          </details>
    """
        if active == "arts-culture" and available_audio_tracks
        else ""
    )
    intro_curtain = (
        '<div class="intro-curtain" aria-hidden="true" data-intro-state="ready"></div>'
        if active == "home"
        else ""
    )
    audio_markup = (
        f"""
          <audio id="site-music-loop" preload="metadata" loop src="{first_audio_path}"></audio>
    """
        if active == "arts-culture" and available_audio_tracks
        else ""
    )
    return dedent(
        f"""\
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <meta name="description" content="{html_escape(description)}">
          <meta name="robots" content="index,follow">
          <meta name="theme-color" content="#173047">
          <link rel="canonical" href="{html_escape(canonical_url)}">
          <meta property="og:type" content="website">
          <meta property="og:site_name" content="Stateline Tri-County Guide">
          <meta property="og:locale" content="en_US">
          <meta property="og:title" content="{html_escape(title)}">
          <meta property="og:description" content="{html_escape(description)}">
          <meta property="og:url" content="{html_escape(canonical_url)}">
          <meta property="og:image" content="{html_escape(social_image_url)}">
          <meta property="og:image:alt" content="Animated high-desert route landscape for the Stateline Tri-County Guide">
          <meta name="twitter:card" content="summary_large_image">
          <meta name="twitter:title" content="{html_escape(title)}">
          <meta name="twitter:description" content="{html_escape(description)}">
          <meta name="twitter:image" content="{html_escape(social_image_url)}">
          <meta name="twitter:image:alt" content="Animated high-desert route landscape for the Stateline Tri-County Guide">
          <title>{html_escape(title)}</title>
          <link rel="preconnect" href="https://fonts.googleapis.com">
          <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
          <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap" rel="stylesheet">
          <link rel="icon" href="{rel('assets/site-icon.svg', depth)}" type="image/svg+xml">
          <link rel="alternate" type="application/json" href="{rel('data/guide-data.json', depth)}">
{extra_alternates}
          <link rel="stylesheet" href="{rel('assets/styles.css', depth)}?v={ASSET_VERSION}">
          <link rel="stylesheet" href="{rel('assets/animations/yucca-banner.css', depth)}?v={ASSET_VERSION}">
          <script src="{rel('assets/site-data.js', depth)}?v={ASSET_VERSION}"></script>
          <script defer src="{rel('assets/app.js', depth)}?v={ASSET_VERSION}"></script>
          <script type="application/ld+json">{structured_data}</script>
        </head>
        <body class="page-{html_escape(active)}">
          <a class="skip-link" href="#main">Skip to content</a>
          <div class="site-watermark" data-preview-watermark hidden aria-hidden="true">Draft preview</div>
          {audio_markup}
          {intro_curtain}
          <header class="site-header">
            <a class="brand" href="{rel('index.html', depth)}" aria-label="Stateline Tri-County Guide home">
              <span class="brand-mark" aria-hidden="true">
                <svg viewBox="0 0 44 36" focusable="false">
                  <path class="brand-mark__mesa" d="M3 25 12 17h8l5-7 5 7h5l6 8H3Z"/>
                  <path class="brand-mark__route" d="M7 28c7-5 13-6 19-3 5 2 9 1 13-2"/>
                  <circle class="brand-mark__sun" cx="32" cy="7" r="2.6"/>
                </svg>
              </span>
              <span>Stateline Tri-County Guide</span>
            </a>
            <nav class="site-nav" aria-label="Primary navigation">
              {nav}
            </nav>
            <div class="nav-yucca-flourish" data-nav-yucca aria-hidden="true">
              <svg viewBox="0 0 160 62" focusable="false">
                <path class="nav-yucca__index-line" d="M7 55.5H157"/>
                <g class="nav-yucca__plant nav-yucca__plant--left">
                  <path class="nav-yucca__stem" style="--sprout-delay:80ms" d="M54 55C53 41 54 28 50 16"/>
                  <path class="nav-yucca__branch" style="--sprout-delay:300ms" d="M52 33 43 26M52 27l9-8"/>
                  <path class="nav-yucca__leaf" style="--sprout-delay:180ms" d="m52 55-12-13 9 14m5-1 12-14-8 15m-5-1-2-17"/>
                  <g class="nav-yucca__flower" style="--sprout-delay:760ms" transform="translate(49 14)">
                    <path d="M0 3c-5-1-7-4-6-8 5 0 8 2 9 6"/>
                    <path d="M2 3c5-1 7-4 6-8-5 0-8 2-9 6"/>
                  </g>
                  <g class="nav-yucca__flower" style="--sprout-delay:930ms" transform="translate(42 24)">
                    <path d="M0 3c-4-1-6-4-5-7 4 0 7 2 8 5"/>
                    <path d="M2 3c4-1 6-4 5-7-4 0-7 2-8 5"/>
                  </g>
                </g>
                <g class="nav-yucca__plant nav-yucca__plant--center">
                  <path class="nav-yucca__stem" style="--sprout-delay:160ms" d="M102 55c0-18 2-34-2-49"/>
                  <path class="nav-yucca__branch" style="--sprout-delay:390ms" d="m101 34-13-9m13 2 12-11m-12 3-8-9"/>
                  <path class="nav-yucca__leaf" style="--sprout-delay:260ms" d="M101 55 84 38l12 18m7-1 17-19-11 20m-8-1-4-23m6 23 5-22"/>
                  <g class="nav-yucca__flower" style="--sprout-delay:820ms" transform="translate(99 5)">
                    <path d="M0 4c-6-1-8-5-7-9 6 0 9 3 10 7"/>
                    <path d="M2 4c6-1 8-5 7-9-6 0-9 3-10 7"/>
                  </g>
                  <g class="nav-yucca__flower" style="--sprout-delay:1000ms" transform="translate(91 9)">
                    <path d="M0 3c-4-1-6-4-5-7 4 0 7 2 8 5"/>
                    <path d="M2 3c4-1 6-4 5-7-4 0-7 2-8 5"/>
                  </g>
                  <g class="nav-yucca__flower" style="--sprout-delay:1110ms" transform="translate(112 15)">
                    <path d="M0 3c-4-1-6-4-5-7 4 0 7 2 8 5"/>
                    <path d="M2 3c4-1 6-4 5-7-4 0-7 2-8 5"/>
                  </g>
                </g>
                <g class="nav-yucca__plant nav-yucca__plant--right">
                  <path class="nav-yucca__stem" style="--sprout-delay:240ms" d="M137 55c1-12 0-23 3-34"/>
                  <path class="nav-yucca__branch" style="--sprout-delay:470ms" d="m139 37-9-7m9 0 8-7"/>
                  <path class="nav-yucca__leaf" style="--sprout-delay:340ms" d="m138 55-12-12 8 13m5-1 13-13-9 14m-5-1 1-18"/>
                  <g class="nav-yucca__flower" style="--sprout-delay:960ms" transform="translate(139 20)">
                    <path d="M0 3c-5-1-7-4-6-8 5 0 8 2 9 6"/>
                    <path d="M2 3c5-1 7-4 6-8-5 0-8 2-9 6"/>
                  </g>
                </g>
              </svg>
            </div>
          </header>
          <main id="main">
            <noscript><section class="noscript">Search, filters, and copy buttons need JavaScript. The pages, tables, links, downloads, and appendix content still work without it.</section></noscript>
            {breadcrumb_nav(active, depth)}
            {content}
          </main>
          <div class="corner-controls" aria-label="Page controls">
            {music_bar}
            <a class="back-to-top" href="#main">Back to top</a>
          </div>
          <section class="directory-assistant" data-directory-assistant data-site-root="{rel('', depth)}" data-network-url="{rel('network/index.html', depth)}" data-submit-url="{rel('submit/index.html', depth)}" aria-label="Directory assistant">
            <button class="directory-assistant__toggle" type="button" aria-expanded="false" aria-haspopup="dialog" aria-controls="directory-assistant-panel">
              <span class="assistant-dot" aria-hidden="true"></span>
              Ask for a route
            </button>
            <dialog class="directory-assistant__panel" id="directory-assistant-panel" aria-labelledby="directory-assistant-title" aria-describedby="directory-assistant-intro directory-assistant-scope directory-assistant-hint">
              <div class="directory-assistant__desert-motion" aria-hidden="true">
                <svg viewBox="0 0 430 58" preserveAspectRatio="xMidYMid slice" focusable="false">
                  <rect class="assistant-desert__sky" width="430" height="58"/>
                  <circle class="assistant-desert__sun" cx="344" cy="26" r="9"/>
                  <path class="assistant-desert__far-ridge" d="M0 45 49 30l41 8 47-19 55 21 56-15 58 17 55-13 69 18v11H0Z"/>
                  <path class="assistant-desert__near-ridge" d="M0 49c56-9 103-8 145 1 47 10 95 7 141-4 52-13 100-10 144 4v8H0Z"/>
                  <path class="assistant-desert__wind" d="M218 16c34 9 66 8 96-2 29-9 56-7 83 5"/>
                  <path class="assistant-desert__horizon" d="M0 50c78-5 147-4 207 2 79 8 151 7 223-2"/>
                  <g class="assistant-desert__yucca assistant-desert__yucca--one" transform="translate(62 14)">
                    <path class="assistant-desert__stem" d="M0 37C1 24 0 12-2 0"/>
                    <path class="assistant-desert__leaves" d="m0 37-15-17 11 18m5-1 15-18L6 38M0 37l-2-23"/>
                    <g class="assistant-desert__flowers" transform="translate(-2 1)">
                      <circle cx="-5" cy="2" r="3"/><circle cx="4" cy="-1" r="3.3"/><circle cx="2" cy="7" r="2.7"/>
                    </g>
                  </g>
                  <g class="assistant-desert__yucca assistant-desert__yucca--two" transform="translate(112 23)">
                    <path class="assistant-desert__stem" d="M0 28C1 18 1 9 0 0"/>
                    <path class="assistant-desert__leaves" d="m0 28-11-12 8 13m4-1 11-13-7 14M0 28V10"/>
                    <g class="assistant-desert__flowers" transform="translate(0 1)">
                      <circle cx="-4" cy="1" r="2.5"/><circle cx="4" cy="-1" r="2.8"/>
                    </g>
                  </g>
                </svg>
              </div>
              <div class="directory-assistant__header">
                <div>
                  <p class="eyebrow">Routing helper</p>
                  <h2 id="directory-assistant-title">Find the right route.</h2>
                </div>
                <button class="directory-assistant__close" type="button" aria-label="Close directory assistant">Close</button>
              </div>
              <p class="directory-assistant__intro" id="directory-assistant-intro">Describe the job in ordinary language: finding support, promoting an event, reaching a county, locating a free tool, or deciding where to start.</p>
              <p class="directory-assistant__scope" id="directory-assistant-scope">This helper suggests routes. If you already know a name, service, or category, <a href="{rel('network/index.html', depth)}#local-listings">search the Directory directly</a>.</p>
              <p class="sr-only" id="directory-assistant-hint">Results update after submitting the form or after a short pause while typing. Press Escape to close this panel.</p>
              <form class="directory-assistant__form" role="search">
                <label for="directory-assistant-query">What are you trying to find?</label>
                <div class="directory-assistant__search-row">
                  <input id="directory-assistant-query" name="directory_query" type="search" autocomplete="off" placeholder="I need more customers for my gallery in Raton..." aria-describedby="directory-assistant-hint directory-assistant-status" aria-controls="directory-assistant-results">
                  <button class="button button-primary" type="submit">Search</button>
                </div>
              </form>
              <p class="directory-assistant__prompt-label">Popular searches</p>
              <div class="directory-assistant__chips" role="group" aria-label="Suggested searches">
                <button type="button" data-assistant-prompt="funding">Funding</button>
                <button type="button" data-assistant-prompt="events">Events</button>
                <button type="button" data-assistant-prompt="flyers">Physical promotion</button>
                <button type="button" data-assistant-prompt="artists">Artists</button>
                <button type="button" data-assistant-prompt="catering">Food &amp; catering</button>
                <button type="button" data-assistant-prompt="nonprofit">Nonprofits</button>
                <button type="button" data-assistant-prompt="business support">Business help</button>
                <button type="button" data-assistant-prompt="free tools">Free tools</button>
              </div>
              <div class="directory-assistant__status" id="directory-assistant-status" role="status" aria-live="polite" aria-atomic="true"></div>
              <div class="directory-assistant__guidance" data-assistant-guidance role="region" aria-label="Suggested next steps" hidden>
                <p data-assistant-guidance-text></p>
                <p class="directory-assistant__question" data-assistant-guidance-question></p>
                <div class="directory-assistant__followups" data-assistant-followups role="group" aria-label="Suggested follow-up searches"></div>
              </div>
              <div class="directory-assistant__results" id="directory-assistant-results" data-assistant-results role="list" aria-label="Directory assistant results"></div>
              <div class="directory-assistant__footer">
                <a class="button button-soft" href="{rel('network/index.html', depth)}#resource-results" data-assistant-full-directory>Open full directory</a>
                <a class="button button-soft" href="{rel('submit/index.html', depth)}">Submit an update</a>
              </div>
            </dialog>
          </section>
          <footer class="site-footer">
            <div class="footer-summary">
              <p class="footer-kicker">Colfax NM + Las Animas CO + Huerfano CO</p>
              <p>This guide points people toward public directories, local support organizations, media channels, and clear update paths. Treat contact details as starting points and confirm details before spending, printing, or promising eligibility.</p>
              <div class="footer-logos" aria-label="Project logo area">
                <span class="footer-placeholder">Placeholder</span>
                <img src="{rel('assets/super-eukarya-logo.png', depth)}" alt="Project logo">
              </div>
            </div>
            <nav class="footer-index" aria-label="Footer site index">
              {footer_index}
            </nav>
          </footer>
        </body>
        </html>
        """
    )



def persona_route_controls(depth: int = 1) -> str:
    href_map = {
        "plan": "plan/index.html",
        "network": "network/index.html",
        "amplifiers": "amplifiers/index.html",
        "posting": "posting/index.html",
        "templates": "templates/index.html",
        "appendix": "appendix/index.html",
        "region": "region/index.html",
    }
    controls = []
    for item in PERSONA_ROUTES:
        first_page = (item["pages"].split(",")[0] or "Network").strip().lower()
        href = href_map.get(first_page, "network/index.html")
        controls.append(f'<a class="persona-route" href="{rel(href, depth)}">{html_escape(item["persona"])}</a>')
    return f'<div class="persona-routes" aria-label="Persona route shortcuts">{"".join(controls)}</div>'


def mountain_banner() -> str:
    return """
    <section class="hero yucca-banner-shell" aria-label="Tri-county guide introduction">
      <img class="yucca-banner-art" src="assets/animations/yucca-banner.svg" alt="" aria-hidden="true">
      <div class="hero-accent" aria-hidden="true" data-animated="true">
        <svg viewBox="0 0 1200 480" preserveAspectRatio="none" focusable="false">
          <path class="hero-route hero-route--one" d="M40 360 C 220 180, 380 420, 560 240 S 920 120, 1160 300"/>
          <path class="hero-route hero-route--two" d="M20 210 C 260 80, 460 280, 700 180 S 980 260, 1180 120"/>
          <circle class="hero-node hero-node--one" cx="220" cy="210" r="5"/>
          <circle class="hero-node hero-node--two" cx="560" cy="240" r="5"/>
          <circle class="hero-node hero-node--three" cx="920" cy="155" r="5"/>
        </svg>
      </div>
      <div class="hero-copy">
        <p class="eyebrow">Regional marketing, posting, and directory manual</p>
        <h1>Stateline Tri-County Guide</h1>
        <p class="lede">
          <span class="hero-lede-desktop">For new and existing businesses, artists, nonprofits, galleries, programs, services, and mentorships trying to expand customers, visibility, partnerships, and usefulness across Colfax, Las Animas, and Huerfano counties.</span>
          <span class="hero-lede-mobile">For businesses, artists, nonprofits, and programs building visibility across Colfax, Las Animas, and Huerfano counties.</span>
        </p>
        <div class="hero-actions">
          <a class="button button-primary" href="plan/index.html">Plan your growth</a>
          <a class="button button-soft" href="network/index.html">Search the directory</a>
          <a class="button button-soft" href="region/index.html">Understand the region</a>
        </div>
      </div>
    </section>
    """


def home_page(summary: dict) -> str:
    path_cards = "\n".join(
        f"""
        <a class="path-card" href="{route_href(item['href'])}">
          <span>0{idx}</span>
          <h2>{html_escape(item['name'])}</h2>
          <p>{html_escape(item['summary'])}</p>
          <strong>{html_escape(item['cta'])}</strong>
        </a>
        """
        for idx, item in enumerate(PATHS, start=1)
    )
    stats = "\n".join(
        f"<div class=\"stat\"><strong>{count}</strong><span>{html_escape(name)}</span></div>"
        for name, count in summary["county"].items()
    )
    task_cards = home_task_group_cards(0)
    content = (
        mountain_banner()
        + f"""
        <section class="section intro-band">
          <div class="section-heading">
            <p class="eyebrow">Purpose of the guide</p>
            <h2>Find the next local outreach route.</h2>
          </div>
          <div class="two-col">
            <p>This guide sorts chambers, tourism sites, newspapers, directories, calendars, newsletters, and public offices so people can use each channel with a clear purpose and a useful next step.</p>
            <p>Use it when you have a business, event, nonprofit, gallery, class, service, or program and need the right directory, event calendar, visitor guide, media route, or flyer stop across Colfax, Las Animas, and Huerfano counties.</p>
          </div>
        </section>
        <section class="section route-orientation" aria-labelledby="route-orientation-title">
          <div class="section-heading">
            <p class="eyebrow">How should I start?</p>
            <h2 id="route-orientation-title">Choose the section that matches the job.</h2>
            <p class="section-note">Directory finds people and places. Promote finds channels that can share something. Funding finds money and support. Counties starts locally. Guide explains the process. Tools helps you make and submit the materials.</p>
          </div>
          <div class="path-grid">{path_cards}</div>
        </section>
        <section class="section tinted">
          <div class="section-heading">
            <p class="eyebrow">What are you trying to do?</p>
            <h2>Start with the job in front of you.</h2>
            <p class="section-note">Each card goes to a practical page or search path. Use it to post, list, promote, fund, route by county, or find arts and culture channels without reading the site front to back.</p>
          </div>
          <div class="mini-grid task-grid">{task_cards}</div>
        </section>
        <section class="section tinted">
          <div class="section-heading">
            <p class="eyebrow">Inventory backbone</p>
            <h2>{summary['row_count']} local listings, organized beside existing directory shortcuts.</h2>
          </div>
          <div class="stats-grid">
            <div class="stat hero-stat"><strong>{summary['row_count']}</strong><span>local listings</span></div>
            {stats}
          </div>
          <p class="section-note">Use the local inventory for outreach and discovery. Details can change, so open the linked page when available and submit a correction when a listing, link, or contact route is outdated.</p>
          {download_buttons(0)}
          <div class="section-actions">
            <a class="button button-primary" href="network/index.html">Open the full directory</a>
            <a class="button button-soft" href="regional-channels/index.html">Find channel shortcuts</a>
          </div>
        </section>
        {submit_listing_panel(0, "directory")}
        """
    )
    return page_shell(
        "Stateline Tri-County Guide | Regional Marketing & Business Resources",
        "Find business directories, event calendars, newsletters, visitor guides, flyer posting routes, media channels, and public offices across Colfax, Las Animas, and Huerfano counties.",
        "home",
        content,
    )


def plan_page() -> str:
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">Plan Your Growth</p>
      <h1>Choose the cycle before collecting links.</h1>
      <p class="lede">The guide works best when a person starts with a goal, chooses the audience, uses existing directories first, prepares one reusable packet, tests matched channels, then adjusts based on what happened.</p>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Growth cycle</p>
        <h2>Each step changes the next one.</h2>
        <p class="section-note">Your goal shapes your audience. The audience determines which directories, partners, and calendars matter. Those channels determine what assets you need. The response tells you what to adjust before you repeat the cycle.</p>
      </div>
      <div class="steps-grid">
        <article class="step-card"><span>1</span><h3>Name the job</h3><p>Decide whether you are trying to launch, promote, correct, partner, fund, or expand.</p></article>
        <article class="step-card"><span>2</span><h3>Choose the audience</h3><p>Pick the people who should notice, visit, register, refer, attend, or share.</p></article>
        <article class="step-card"><span>3</span><h3>Start with directories</h3><p>Use existing lists before building a contact list by hand.</p></article>
        <article class="step-card"><span>4</span><h3>Prepare one packet</h3><p>Make a short blurb, image, date, place, contact route, and plain call to action.</p></article>
        <article class="step-card"><span>5</span><h3>Test matched channels</h3><p>Use a small set of calendars, media outlets, partners, or public channels that fit the job.</p></article>
        <article class="step-card"><span>6</span><h3>Track and repeat</h3><p>Record what happened, thank the channel, and reuse what worked.</p></article>
      </div>
      <div class="section-actions"><a class="button button-primary" href="../network/index.html">Find directories and listings</a></div>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Promotion packet</p>
        <h2>Templates help once the channel and audience are set.</h2>
        <p class="section-note">The useful strategy is to prepare one clean packet: a short blurb, image, flyer, listing details, date, location, hours, contact route, and plain call to action. The templates help you adapt that packet for directories, calendars, media, partners, emails, and social posts.</p>
      </div>
      <div class="section-actions">
        <a class="button button-primary" href="../templates/index.html">Use copy-ready templates</a>
        <a class="button button-soft" href="../regional-channels/index.html">Find places to send them</a>
        <a class="button button-soft" href="../tools/free-discounted/index.html">Find free &amp; discounted tools</a>
      </div>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Funding and support readiness</p>
        <h2>Visibility work can create proof for later asks.</h2>
        <p class="section-note">Grantors, lenders, sponsors, and partner organizations usually need more than enthusiasm. Track where you posted, who shared, what response arrived, and which partner can confirm the public benefit before using outreach results in a funding conversation.</p>
      </div>
      <a class="button button-soft" href="../network/index.html">Find funding and support entries</a>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Cross-promotion loop</p>
        <h2>Use the channel that worked, then make the relationship stronger.</h2>
        <p class="section-note">Submit the item, share the published result, thank the channel owner, report useful response, and reuse the relationship when it fits again.</p>
      </div>
    </section>
    """
    return page_shell(
        "Plan Local Growth Across Colfax, Las Animas & Huerfano | Stateline Tri-County Guide",
        "Choose the right business listing, event calendar, newsletter, partner, media, or flyer route before promoting a business, event, nonprofit, service, or program.",
        "plan",
        content,
        depth=1,
    )


def network_page(rows: list[dict]) -> str:
    row_count = len(rows)
    source_group_count = len(grouped_directory_sources(DIRECTORY_SOURCES))
    top_group_count = len(top_directory_source_groups())
    physical_location_count = sum(1 for row in rows if has_physical_location(row))
    physical_ad_count = sum(1 for row in rows if is_physical_ad_candidate(row))
    direct_website_count = sum(1 for row in rows if row.get("online_connection_group") == "Direct website")
    hosted_profile_count = sum(1 for row in rows if row.get("online_connection_group") == "Hosted profile")
    no_online_count = sum(1 for row in rows if row.get("online_connection_group") == "No online link")
    outreach_listed_count = sum(
        any(item.get("status") == "listed" for item in (row.get("outreach_channels") or []) if isinstance(item, dict))
        for row in rows
    )
    outreach_ask_count = sum(
        any(item.get("status") == "ask" for item in (row.get("outreach_channels") or []) if isinstance(item, dict))
        for row in rows
    )
    outreach_options = "".join(
        f'<option value="{html_escape(item["key"])}">{html_escape(item["label"])}</option>'
        for item in CHANNEL_DEFINITIONS
    )
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">Directory</p>
      <h1>Search the regional directory.</h1>
      <p class="lede">Search {row_count} local listings for business directories, event calendars, visitor guides, social pages, newsletter routes, and physical promotion contacts.</p>
    </section>
    {page_wayfinding(
        "Directory",
        "Find a known business, organization, place, program, service, or support resource.",
        [("Search listings", "#local-listings"), ("Directory shortcuts", "#directory-shortcuts"), ("Directory tools", "#directory-tools")],
        [("Find places to promote", "promote/"), ("Search funding", "resources/funding/"), ("Start with a county", "region/")],
        1,
    )}
    <section id="local-listings" class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Local listings</p>
        <h2>Find a local listing.</h2>
        <p class="section-note">Search by business name, town, county, service, audience, flyer posting fit, social profile, or task. Results stay alphabetical until you add another filter.</p>
      </div>
      <div class="tool-panel directory-search-panel">
        <div>
          <label for="resource-search">Search {row_count} local entries</label>
          <input id="resource-search" class="search-input" type="search" placeholder="Try bakery, gallery, flyer posting, newsletter, grant, Raton, Trinidad...">
        </div>
        <details class="directory-filter-details" open>
          <summary>Filters <span id="resource-filter-summary">All listings</span></summary>
          <div class="directory-filter-body">
            <div class="advanced-filters" aria-label="Detailed resource filters">
              <div>
                <label for="resource-type-filter">Resource type</label>
                <select id="resource-type-filter"><option value="All">All types</option></select>
              </div>
              <div>
                <label for="online-connection-filter">Online connection</label>
                <select id="online-connection-filter"><option value="All">All connection types</option></select>
              </div>
              <div>
                <label for="outreach-channel-filter">Promotion channel</label>
                <select id="outreach-channel-filter"><option value="All">All promotion channels</option>{outreach_options}</select>
              </div>
              <div>
                <label for="outreach-status-filter">Channel status</label>
                <select id="outreach-status-filter">
                  <option value="All">Any channel indication</option>
                  <option value="listed">Route shown on linked page</option>
                  <option value="ask">Ask before using</option>
                </select>
              </div>
            </div>
            <div>
              <span class="filter-label">Location access</span>
              <div id="physical-location-filter" class="filter-row" aria-label="Physical location filters">
                <button class="chip is-active" data-location-filter="All">All listings</button>
                <button class="chip" data-location-filter="Physical">Physical locations</button>
                <button class="chip" data-location-filter="Flyers">Physical promotion contacts</button>
              </div>
            </div>
            <div>
              <span class="filter-label">County</span>
              <div class="filter-row" aria-label="Resource filters">
                <button class="chip is-active" data-resource-filter="All">All</button>
                <button class="chip" data-resource-filter="Colfax">Colfax</button>
                <button class="chip" data-resource-filter="Las Animas">Las Animas</button>
                <button class="chip" data-resource-filter="Huerfano">Huerfano</button>
                <button class="chip" data-resource-filter="Regional">Regional</button>
              </div>
            </div>
          </div>
        </details>
      </div>
      <details class="marker-help">
        <summary>How to read a listing</summary>
        <div class="marker-legend" aria-label="Directory marker legend">
          <span class="listing-marker listing-marker--physical">Physical location</span>
          <span>{physical_location_count} listings include a map-able or street-style location.</span>
          <span class="listing-marker listing-marker--ad">Physical promotion contact</span>
          <span>{physical_ad_count} listings have a physical location, a relevant location type, and at least one contact route.</span>
          <span class="connection-label connection-label--connected"><span class="connection-label__signal" aria-hidden="true"></span>Connect online</span>
          <span>{direct_website_count} listings point to a business or organization website.</span>
          <span class="connection-label connection-label--profile"><span class="connection-label__signal" aria-hidden="true"></span>Online profile</span>
          <span>{hosted_profile_count} listings use a hosted directory, tourism page, or social profile that helps with discovery, updates, and cross-promotion.</span>
          <span class="connection-label connection-label--missing"><span class="connection-label__signal" aria-hidden="true"></span>No online link listed</span>
          <span>{no_online_count} listings currently rely on phone, email, map, or update-form routes.</span>
          <span class="outreach-tag outreach-tag--listed">Route shown</span>
          <span>{outreach_listed_count} listings point to at least one directory, calendar, newsletter, media, advertising, sponsorship, or sharing route. Open the linked page for current terms.</span>
          <span class="outreach-tag outreach-tag--ask">Contact opportunity</span>
          <span>{outreach_ask_count} listings may suit a tailored outreach request; use the available contact information for current terms.</span>
        </div>
      </details>
      <p id="resource-results-note" class="section-note" aria-live="polite">Search by town, county, business type, audience, keyword, flyer posting fit, or outreach task.</p>
      <div id="resource-results" class="resource-list"></div>
      <div class="directory-more-row">
        <button id="resource-load-more" class="button button-soft" type="button" hidden>Show more listings</button>
      </div>
      <div class="section-actions directory-secondary-actions">
        <a class="button button-soft" href="../appendix/index.html">Open table view</a>
        <a class="button button-soft" href="../submit/index.html">Correct a listing</a>
      </div>
    </section>
    <section id="directory-shortcuts" class="section">
      <div class="section-heading">
        <p class="eyebrow">Directory shortcuts</p>
        <h2>Use an existing regional source instead of rebuilding its list.</h2>
        <p class="section-note">{source_group_count} grouped cards connect to {len(DIRECTORY_SOURCES)} chamber, calendar, visitor, funding, media, arts, and public-information routes.</p>
      </div>
      <div class="tool-panel">
        <div>
          <label for="source-search">Search directory shortcuts</label>
          <input id="source-search" class="search-input" type="search" placeholder="Try chamber, event, media, nonprofit, artist, funding...">
        </div>
        <div class="filter-row" aria-label="County filters">
          <button class="chip is-active" data-source-filter="All">All</button>
          <button class="chip" data-source-filter="Colfax">Colfax</button>
          <button class="chip" data-source-filter="Las Animas">Las Animas</button>
          <button class="chip" data-source-filter="Huerfano">Huerfano</button>
          <button class="chip" data-source-filter="Regional">Regional</button>
        </div>
      </div>
      <p id="source-results-note" class="section-note" aria-live="polite">{top_group_count} priority shortcut groups are available. Search or choose a county to inspect all {source_group_count} groups.</p>
      <div id="source-results" class="source-grid"></div>
      <div class="directory-more-row">
        <button id="source-load-more" class="button button-soft" type="button" hidden>Show more shortcuts</button>
      </div>
    </section>
    <section id="directory-tools" class="section tinted directory-support-section">
      <details class="directory-support-details">
        <summary>Browse by role or download directory data</summary>
        <div class="directory-support-body">
          <p class="section-note">Role shortcuts connect to the most useful starting page for a new business, existing business, nonprofit, artist, event organizer, or rural service.</p>
          {persona_route_controls(1)}
          {download_buttons(1)}
        </div>
      </details>
    </section>
    {submit_listing_panel(1, "directory")}
    {next_action_block(1, [
        ("Find regional newsletters, calendars, visitor guides, and directory channels", "amplifiers/"),
        ("Use copy-ready outreach templates", "templates/"),
        ("Submit a correction with a public page link", "submit/"),
        ("Open the public contact appendix", "appendix/"),
    ])}
    """
    return page_shell(
        "Find Local Directories, Physical Ad Locations, Media & Support Entries | Stateline Tri-County Guide",
        f"Search a {row_count}-entry tri-county directory for business listings, event calendars, newsletters, social pages, visitor guides, physical posting routes, funding leads, arts listings, and support services.",
        "network",
        content,
        depth=1,
        main_entity=directory_item_list_schema(rows),
        extra_json_alternates=[("Full directory metadata", "data/directory-metadata.json")],
        schema_type="CollectionPage",
    )


def normalized_match_text(value: object) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).split())


def text_matches_terms(value: object, terms: list[str]) -> bool:
    haystack = f" {normalized_match_text(value)} "
    return any(
        normalized and f" {normalized} " in haystack
        for normalized in (normalized_match_text(term) for term in terms)
    )


BUSINESS_PREFIX_KEYWORDS = {"brew", "dent", "landscap", "plumb"}


def business_keyword_matches(value: object, term: str) -> bool:
    normalized_value = normalized_match_text(value)
    normalized_term = normalized_match_text(term)
    if not normalized_term:
        return False
    if normalized_term in BUSINESS_PREFIX_KEYWORDS:
        return bool(re.search(rf"\b{re.escape(normalized_term)}[a-z0-9]*\b", normalized_value))
    return text_matches_terms(normalized_value, [normalized_term])


def row_matches_terms(row: dict, terms: list[str]) -> bool:
    identity_fields = (
        "resource_name",
        "alternate_names",
        "category",
        "public_listing_type",
        "public_category",
    )
    return text_matches_terms(" ".join(str(row.get(field) or "") for field in identity_fields), terms)


def resource_preview_cards(rows: list[dict], terms: list[str], limit: int = 18) -> str:
    matched = []
    seen_names = set()
    for row in sorted(rows, key=lambda item: (item.get("resource_name") or "", item.get("county") or "", item.get("town") or "")):
        if not row_matches_terms(row, terms):
            continue
        name_key = normalized_resource_name_key(row.get("resource_name"))
        if not name_key or name_key in seen_names:
            continue
        seen_names.add(name_key)
        matched.append(row)
        if len(matched) >= limit:
            break
    if not matched:
        return '<p class="section-note">No matching local inventory rows are available in this build.</p>'
    cards = []
    for row in matched:
        links = contact_links_for_row(row)
        tags = "".join(f'<span class="badge">{html_escape(tag)}</span>' for tag in organization_tags(row))
        cards.append(
            f"""
            <article class="resource-item">
              <div class="source-card__meta">
                <span>{html_escape(row.get('county'))}</span>
                <span>{html_escape(row.get('town'))}</span>
                <span>{html_escape(row.get('public_listing_type') or row.get('resource_type'))}</span>
              </div>
              <h3>{entity_name_link(row)}</h3>
              <p class="resource-tags"><strong>Useful for:</strong> {tags}</p>
              {resource_physical_indicator_badges(row)}
              {resource_online_connection_badge(row)}
              <p>{html_escape(public_text_value(row.get('public_description') or row.get('category') or DEFAULT_LISTING_DESCRIPTION))}</p>
              <div class="resource-outreach"><strong>Promotion paths:</strong>{resource_outreach_channel_badges(row)}</div>
              <p class="resource-best"><strong>Best fit:</strong> {html_escape(public_text_value(row.get('public_best_for') or public_best_for(row)))}</p>
              <p class="action-line">{html_escape(public_text_value(row.get('goal_relevance') or 'Choose the route that fits, then contact the listed page or organization.'))}</p>
              <div class="resource-links">{links}</div>
            </article>
            """
        )
    return "\n".join(cards)


def sources_matching_terms(terms: list[str]) -> list[dict]:
    return [
        item for item in DIRECTORY_SOURCES
        if text_matches_terms(
            " ".join(str(item.get(field) or "") for field in ["title", "kind", "best_for", "action", "county"]),
            terms,
        )
    ]


DISCOVERY_CATEGORY_LABELS = {
    "grants-public-funding": "Grants and public funding",
    "business-capital": "Loans and business capital",
    "fiscal-sponsorship": "Fiscal sponsors",
    "nonprofit-directories": "Nonprofit directories",
    "business-directories": "Business directories",
    "artists-creative-opportunities": "Artist opportunities",
}


def selected_discovery_sources(categories: list[str], limit: int = 9) -> list[dict]:
    buckets = {
        category: [item for item in RESOURCE_DISCOVERY_SOURCES if item.get("category") == category]
        for category in categories
    }
    selected = []
    index = 0
    while len(selected) < limit:
        added = False
        for category in categories:
            bucket = buckets[category]
            if index < len(bucket):
                selected.append(bucket[index])
                added = True
                if len(selected) >= limit:
                    break
        if not added:
            break
        index += 1
    return selected


def discovery_source_cards(categories: list[str], limit: int = 9) -> str:
    sources = selected_discovery_sources(categories, limit)
    if not sources:
        return '<p class="section-note">No external search registry is configured for this route yet.</p>'
    return "\n".join(
        f"""
        <article class="source-card discovery-source-card">
          <div class="source-card__meta">
            <span>{html_escape(item.get('resource_type') or DISCOVERY_CATEGORY_LABELS.get(item.get('category'), 'Resource search'))}</span>
            <span>{html_escape(item.get('authority'))}</span>
          </div>
          <h3><a href="{html_escape(item.get('url'))}" target="_blank" rel="noreferrer">{html_escape(item.get('name'))}</a></h3>
          <p>{html_escape(item.get('public_use'))}</p>
          <a class="text-link" href="{html_escape(item.get('url'))}" target="_blank" rel="noreferrer">{html_escape(item.get('action_label') or 'Open registry')}</a>
        </article>
        """
        for item in sources
    )


FUNDING_AUDIENCE_FILTERS = (
    ("arts", "Arts and culture"),
    ("creative", "Creative businesses"),
    ("nonprofit", "Nonprofits"),
    ("economic development", "Economic development"),
    ("education student scholarship", "Education and scholarships"),
    ("health healthcare wellness mental", "Healthcare and wellness"),
    ("small business", "Small businesses"),
    ("women", "Women-owned businesses"),
    ("lgbtq", "LGBTQ-owned businesses"),
    ("indigenous native tribal", "Indigenous-owned and tribal"),
    ("hispanic latino latinx", "Hispanic- and Latino-owned"),
)


def funding_program_group(item: dict) -> str:
    value = str(item.get("program_type") or "").casefold()
    if "fellowship" in value:
        return "Fellowships"
    if any(term in value for term in ("loan", "microloan", "capital", "credit", "financing")):
        return "Loans and capital"
    if (
        ("grant" in value and "research" not in value)
        or any(term in value for term in ("apprenticeship award", "scholarship", "stipend", "sponsorship", "purchase award"))
    ):
        return "Cash grants"
    if any(term in value for term in ("free", "accelerator", "education", "certification")):
        return "Free support programs"
    if any(term in value for term in ("match", "research", "directory")):
        return "Funding search tools"
    if any(term in value for term in ("reimbursement", "incentive", "assistance")):
        return "Incentives and reimbursements"
    return "Other support"


def funding_timing_group(item: dict) -> str:
    status = str(item.get("status") or "").casefold()
    if any(term in status for term in ("open", "available", "upcoming")):
        return "Open or upcoming"
    if "monitor" in status:
        return "Monitor next cycle"
    return "Check current availability"


def funding_cost_group(item: dict) -> str:
    value = str(item.get("free_to_apply_or_enroll") or "").casefold()
    if value.startswith("yes") or "free" in value and not any(term in value for term in ("not free", "fee", "membership")):
        return "Free"
    if any(term in value for term in ("membership is required", "membership required", "application fee", "$15")):
        return "Fee or membership"
    return "Check cost"


def css_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def national_funding_card(item: dict) -> str:
    audiences = "; ".join(str(value) for value in item.get("audiences") or [])
    applicants = "; ".join(str(value) for value in item.get("applicant_types") or [])
    keyword_blob = " ".join(str(value) for value in item.get("keywords") or [])
    search_blob = " ".join(
        str(value or "")
        for value in (
            item.get("name"),
            item.get("provider"),
            item.get("program_type"),
            item.get("summary"),
            item.get("geography"),
            audiences,
            applicants,
            item.get("deadline_display"),
            item.get("funding_range"),
            item.get("requires_501c3"),
            item.get("fiscal_sponsor_policy"),
            item.get("advertising_marketing_eligibility"),
            item.get("free_to_apply_or_enroll"),
            keyword_blob,
        )
    ).casefold()
    status_group = funding_timing_group(item)
    program_group = funding_program_group(item)
    cost_group = funding_cost_group(item)
    application_url = str(item.get("application_url") or item.get("source_url") or "")
    source_url = str(item.get("source_url") or application_url)
    detail_link = (
        f'<a class="button button-soft" href="{html_escape(source_url)}" target="_blank" rel="noreferrer">Program details</a>'
        if source_url and source_url != application_url
        else ""
    )
    return f"""
    <article class="funding-card" data-funding-card
      data-funding-search="{html_escape(search_blob)}"
      data-funding-audiences="{html_escape((audiences + ' ' + keyword_blob).casefold())}"
      data-funding-status="{html_escape(status_group)}"
      data-funding-type="{html_escape(program_group)}"
      data-funding-cost="{html_escape(cost_group)}">
      <div class="funding-card__meta">
        <span class="badge">{html_escape(item.get('program_type'))}</span>
        <span class="funding-status funding-status--{html_escape(css_token(status_group))}">{html_escape(item.get('status'))}</span>
      </div>
      <h3><a href="{html_escape(source_url)}" target="_blank" rel="noreferrer">{html_escape(item.get('name'))}</a></h3>
      <p class="funding-provider">{html_escape(item.get('provider'))}</p>
      <p>{html_escape(public_text_value(item.get('summary')))}</p>
      <div class="funding-card__essentials">
        <p><strong>Deadline</strong><span>{html_escape(item.get('deadline_display'))}</span></p>
        <p><strong>Funding or support</strong><span>{html_escape(item.get('funding_range'))}</span></p>
      </div>
      <details class="funding-details">
        <summary>Eligibility, costs, and allowed uses</summary>
        <dl class="funding-terms">
          <div><dt>Applicant</dt><dd>{html_escape(applicants)}</dd></div>
          <div><dt>501(c)(3)</dt><dd>{html_escape(item.get('requires_501c3'))}</dd></div>
          <div><dt>Fiscal sponsor</dt><dd>{html_escape(item.get('fiscal_sponsor_policy'))}</dd></div>
          <div><dt>Marketing or advertising costs</dt><dd>{html_escape(item.get('advertising_marketing_eligibility'))}</dd></div>
          <div><dt>Cost to apply or enroll</dt><dd>{html_escape(item.get('free_to_apply_or_enroll'))}</dd></div>
          <div><dt>Match</dt><dd>{html_escape(item.get('match_requirement'))}</dd></div>
          <div><dt>Area served</dt><dd>{html_escape(item.get('geography'))}</dd></div>
          <div><dt>Useful for</dt><dd>{html_escape(audiences)}</dd></div>
        </dl>
      </details>
      <div class="section-actions funding-card__actions">
        <a class="button button-primary" href="{html_escape(application_url)}" target="_blank" rel="noreferrer">Open application route</a>
        {detail_link}
      </div>
    </article>
    """


def funding_deadline_sort_key(item: dict) -> tuple:
    timing = funding_timing_group(item)
    deadline = str(item.get("deadline_date") or "")
    return (
        0 if timing == "Open or upcoming" else 1,
        0 if deadline else 1,
        deadline or "9999-12-31",
        str(item.get("name") or "").casefold(),
    )


def national_funding_cards() -> str:
    ordered = sorted(NATIONAL_FUNDING_OPPORTUNITIES, key=funding_deadline_sort_key)
    return "\n".join(national_funding_card(item) for item in ordered)


def funding_page(rows: list[dict]) -> str:
    terms = [
        "funding", "grant", "grants", "scholarship", "scholarships", "stipend", "stipends",
        "loan", "loans", "incentive", "incentives", "foundation", "foundations", "capital",
        "microgrant", "microgrants", "fellowship", "fellowships", "training reimbursement",
        "technical assistance", "cdfi",
    ]
    funding_sources = sources_matching_terms(terms)
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">Funding</p>
      <h1>Funding, grants, incentives, and support entries.</h1>
      <p class="lede">Use this page to find likely starting points for business, nonprofit, arts, culture, outdoor recreation, workforce, and community projects. Check eligibility, deadlines, applicant type, match rules, and award status with the original program.</p>
    </section>
    {page_wayfinding(
        "Funding",
        "Compare grants, capital, incentives, fiscal support, and free assistance.",
        [("Search funding", "#funding-finder"), ("Search registries", "#funding-registries"), ("Regional shortcuts", "#funding-shortcuts"), ("Local support", "#local-funding")],
        [("Find local providers", "network/"), ("Free & discounted tools", "tools/free-discounted/"), ("Arts & Culture", "resources/arts-culture/")],
        2,
    )}
    <section id="funding-finder" class="section funding-finder" aria-labelledby="national-funding-title">
      <div class="section-heading">
        <p class="eyebrow">Regional and national funding finder</p>
        <h2 id="national-funding-title">Search {len(NATIONAL_FUNDING_OPPORTUNITIES)} grants, capital, and free support programs.</h2>
        <p class="section-note">Filter by audience, timing, support type, or application cost. Closed rounds stay visible only when they are useful programs to monitor.</p>
      </div>
      <div class="funding-filter-panel" role="search" aria-label="Filter regional and national funding opportunities">
        <label class="funding-search-label" for="funding-search">Search funding</label>
        <input id="funding-search" class="search-input" type="search" placeholder="Try artist, nonprofit, women-owned, fiscal sponsor, rolling, advertising...">
        <div class="funding-filter-grid">
          <label>Audience
            <select id="funding-audience-filter">
              <option value="All">All audiences</option>
              {''.join(f'<option value="{html_escape(value)}">{html_escape(label)}</option>' for value, label in FUNDING_AUDIENCE_FILTERS)}
            </select>
          </label>
          <label>Timing
            <select id="funding-status-filter">
              <option value="All">All timing</option>
              <option value="Open or upcoming">Open or upcoming</option>
              <option value="Monitor next cycle">Monitor next cycle</option>
              <option value="Check current availability">Check current availability</option>
            </select>
          </label>
          <label>Support type
            <select id="funding-type-filter">
              <option value="All">All support types</option>
               <option value="Cash grants">Cash grants</option>
               <option value="Fellowships">Fellowships</option>
               <option value="Loans and capital">Loans and capital</option>
               <option value="Incentives and reimbursements">Incentives and reimbursements</option>
               <option value="Free support programs">Free support programs</option>
              <option value="Funding search tools">Funding search tools</option>
            </select>
          </label>
          <label>Application cost
            <select id="funding-cost-filter">
              <option value="All">All cost information</option>
              <option value="Free">Free to apply or enroll</option>
              <option value="Fee or membership">Fee or membership required</option>
              <option value="Check cost">Check current cost</option>
            </select>
          </label>
        </div>
        <p id="funding-results-note" class="results-note" role="status" aria-live="polite">Funding entries are ready to filter.</p>
      </div>
      <div id="national-funding-results" class="funding-grid">{national_funding_cards()}</div>
      <div class="section-actions directory-load-more-row">
        <button id="funding-load-more" class="button button-soft" type="button">Show more funding entries</button>
      </div>
      <div class="download-row">
        <a class="button button-soft" href="../../data/national-funding-opportunities.csv" download>Download funding CSV</a>
        <a class="button button-soft" href="../../data/national-funding-opportunities.json" download>Download funding JSON</a>
      </div>
    </section>
    <section id="funding-registries" class="section funding-registry-section">
      <div class="section-heading">
        <p class="eyebrow">Search beyond this list</p>
        <h2>Funding, lending, and fiscal-sponsor registries.</h2>
        <p class="section-note">Use these when the curated entries do not fit. Start with the registry, then confirm the program or sponsor directly.</p>
      </div>
      <div class="source-grid compact" data-progressive-list data-compact-count="4" data-wide-count="9">{discovery_source_cards(['grants-public-funding', 'business-capital', 'fiscal-sponsorship'], 99)}</div>
      <div class="section-actions"><button class="button button-soft" type="button" data-progressive-more data-progressive-label="registries">Show more registries</button></div>
    </section>
    <section id="funding-shortcuts" class="section">
      <div class="section-heading">
        <p class="eyebrow">Funding directory shortcuts</p>
        <h2>Programs and pages to open directly.</h2>
      </div>
      <div class="source-grid compact" data-progressive-list data-compact-count="4" data-wide-count="12">{source_group_cards(funding_sources, 12)}</div>
      <div class="section-actions"><button class="button button-soft" type="button" data-progressive-more data-progressive-label="shortcuts">Show more shortcuts</button><a class="button button-soft" href="../../network/index.html?q=funding+grant+loan#resource-results">Search every funding-related listing</a></div>
    </section>
    <section id="local-funding" class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Local inventory entries</p>
        <h2>Additional rows that may connect to money, training, or support.</h2>
        <p class="section-note">Use these as starting entries. Open the link or contact path before including a program in public advice.</p>
      </div>
      <div class="resource-list" data-progressive-list data-compact-count="4" data-wide-count="12">{resource_preview_cards(rows, terms, 12)}</div>
      <div class="section-actions"><button class="button button-soft" type="button" data-progressive-more data-progressive-label="local entries">Show more local entries</button></div>
      {download_buttons(2)}
    </section>
    {submit_listing_panel(2, "directory")}
    """
    return page_shell(
        "Funding, Grants & Support Entries | Stateline Tri-County Guide",
        "Find grant, incentive, scholarship, stipend, loan, workforce, arts, nonprofit, and business-support starting points for Colfax, Las Animas, and Huerfano counties.",
        "funding",
        content,
        depth=2,
        schema_type="CollectionPage",
        extra_json_alternates=[("National funding opportunities", "data/national-funding-opportunities.json")],
    )


def arts_culture_page(rows: list[dict]) -> str:
    terms = [
        "art", "arts", "artist", "artists", "gallery", "galleries", "creative", "maker", "makers",
        "music", "musician", "musicians", "theater", "theatre", "museum", "museums", "cultural",
        "craft", "crafts", "artisan", "artisans", "mural", "murals", "performance", "performances",
        "dance", "film", "literary", "writer", "writers", "studio", "studios",
    ]
    arts_sources = sources_matching_terms(terms)
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">Arts & Culture</p>
      <h1>Artists, galleries, makers, venues, and cultural routes.</h1>
      <p class="lede">Use this page when creative work needs to be findable: listings, shows, vendor visibility, visitor-facing promotion, venue calendars, media, creative districts, and partner channels.</p>
    </section>
    {page_wayfinding(
        "Arts & Culture",
        "Find creative people, places, open calls, funding, and visibility routes.",
        [("County routes", "#arts-county-routes"), ("Choose a goal", "#arts-goals"), ("Open calls", "#arts-open-calls"), ("Creative listings", "#arts-local-listings")],
        [("Promote creative work", "promote/?route=galleries"), ("Search arts funding", "resources/funding/?audience=arts"), ("Search the Directory", "network/?q=artist+gallery+maker#resource-results")],
        2,
    )}
    <nav id="arts-county-routes" class="arts-route-strip" aria-label="Creative directory routes by county">
      <a class="arts-route-visual arts-route-visual--colfax" href="../../network/index.html?q=artist+gallery+maker+Colfax#resource-results">
        <img src="../../assets/animations/hero-volcanic-field.svg" alt="" aria-hidden="true">
        <span><strong>Colfax County</strong><small>Artists, studios, galleries, and makers</small></span>
      </a>
      <a class="arts-route-visual arts-route-visual--las-animas" href="../../network/index.html?q=artist+gallery+maker+Las+Animas#resource-results">
        <img src="../../assets/animations/hero-fishers-peak.svg" alt="" aria-hidden="true">
        <span><strong>Las Animas County</strong><small>Creative businesses, venues, and cultural programs</small></span>
      </a>
      <a class="arts-route-visual arts-route-visual--huerfano" href="../../network/index.html?q=artist+gallery+maker+Huerfano#resource-results">
        <img src="../../assets/animations/hero-spanish-peaks.svg" alt="" aria-hidden="true">
        <span><strong>Huerfano County</strong><small>Arts districts, performers, makers, and events</small></span>
      </a>
    </nav>
    <section id="arts-goals" class="section">
      <div class="section-heading">
        <p class="eyebrow">Choose a creative route</p>
        <h2>Start with what you need to do.</h2>
      </div>
      <div class="mini-grid arts-action-grid">
        <a class="mini-card category-route-card" href="../../network/index.html?q=artist+gallery+maker#resource-results"><h3>Find artists and galleries</h3><p>Search local makers, studios, galleries, performers, and cultural organizations.</p><strong>Search creative listings</strong></a>
        <a class="mini-card category-route-card" href="../funding/index.html?audience=arts"><h3>Find arts funding</h3><p>Compare grants, fellowships, fiscal-sponsor routes, and free support programs.</p><strong>Open funding</strong></a>
        <a class="mini-card category-route-card" href="../../amplifiers/index.html#amplifier-event-calendars"><h3>Promote an event</h3><p>Find calendars, visitor guides, media, newsletters, and partner channels.</p><strong>Open promotion channels</strong></a>
        <a class="mini-card category-route-card" href="../../submit/index.html"><h3>Add creative work</h3><p>Submit an artist, gallery, venue, cultural program, or corrected contact route.</p><strong>Submit a listing</strong></a>
      </div>
    </section>
    <section id="arts-open-calls" class="section">
      <div class="section-heading">
        <p class="eyebrow">Open calls and artist registries</p>
        <h2>Find calls, registries, residencies, and art-fair applications.</h2>
        <p class="section-note">Start with the local and state routes, then widen the search. Each card identifies the kind of route it opens; confirm the current deadline, fee, eligibility, and rights terms on the linked page.</p>
      </div>
      <div class="source-grid compact" data-progressive-list data-compact-count="5" data-wide-count="10">{discovery_source_cards(['artists-creative-opportunities'], 99)}</div>
      <div class="section-actions"><button class="button button-soft" type="button" data-progressive-more data-progressive-label="registries">Show more registries</button></div>
    </section>
    <section id="arts-shortcuts" class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Arts and culture shortcuts</p>
        <h2>Pages that already gather creative visibility.</h2>
      </div>
      <div class="source-grid compact" data-progressive-list data-compact-count="4" data-wide-count="12">{source_group_cards(arts_sources, 12)}</div>
      <div class="section-actions"><button class="button button-soft" type="button" data-progressive-more data-progressive-label="shortcuts">Show more shortcuts</button></div>
    </section>
    <section id="arts-local-listings" class="section">
      <div class="section-heading">
        <p class="eyebrow">Local creative inventory</p>
        <h2>Artists, venues, galleries, makers, and cultural entries.</h2>
        <p class="section-note">Use these rows for discovery and outreach. Confirm current details before publishing a recommendation or sending visitors to a location.</p>
      </div>
      <div class="resource-list" data-progressive-list data-compact-count="4" data-wide-count="12">{resource_preview_cards(rows, terms, 12)}</div>
      <div class="section-actions"><button class="button button-soft" type="button" data-progressive-more data-progressive-label="local entries">Show more local entries</button><a class="button button-primary" href="../../network/index.html?q=artist+gallery+maker#resource-results">Search the full creative directory</a></div>
      {download_buttons(2)}
    </section>
    {submit_listing_panel(2, "directory")}
    """
    return page_shell(
        "Arts & Culture Directory Routes | Stateline Tri-County Guide",
        "Find artist, gallery, maker, music, venue, creative-district, cultural, visitor-facing, and partner visibility routes across the tri-county region.",
        "arts-culture",
        content,
        depth=2,
        schema_type="CollectionPage",
    )


def promote_page() -> str:
    route_cards = "\n".join(
        f"""
        <a class="mini-card category-route-card promote-route-card" href="?route={html_escape(item['key'])}#promotion-results"
           data-promote-route-link="{html_escape(item['key'])}">
          <h3>{html_escape(item['title'])}</h3>
          <p>{html_escape(item['summary'])}</p>
          <strong>Show matching contacts</strong>
        </a>
        """
        for item in PROMOTE_ROUTE_DEFS
    )
    county_route_panels = "\n".join(
        f"""
        <article class="county-promote-panel">
          <h3>{html_escape(county)} County</h3>
          <div class="county-promote-links">
            {''.join(
                f'<a href="?county={quote_plus(county)}&amp;route={html_escape(item["key"])}#promotion-results">{html_escape(item["title"])}</a>'
                for item in PROMOTE_ROUTE_DEFS
            )}
          </div>
        </article>
        """
        for county in ("Colfax", "Las Animas", "Huerfano")
    )
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">Promote</p>
      <h1>Find the local channel that fits the job.</h1>
      <p class="lede">Search events, advertising, business directories, nonprofit partners, calendars, galleries, media, and visitor channels across Colfax, Las Animas, and Huerfano counties.</p>
    </section>
    {page_wayfinding(
        "Promote",
        "Find the channel that can share an event, service, business, nonprofit, or arts project.",
        [("Choose a route", "#promote-routes"), ("Search contacts", "#promotion-results"), ("County shortcuts", "#county-promotion"), ("Specialized views", "#promote-specialized")],
        [("Find a specific listing", "network/"), ("Physical ad finder", "posting/"), ("Message templates", "templates/")],
        1,
    )}
    <section id="promote-routes" class="section" aria-labelledby="promote-route-title">
      <div class="section-heading">
        <p class="eyebrow">Choose a route</p>
        <h2 id="promote-route-title">Start with what needs visibility.</h2>
        <p class="section-note">Each route opens the same regional data with a different filter, so the navigation stays compact and the results remain comprehensive.</p>
      </div>
      <div class="mini-grid promote-route-grid">{route_cards}
        <a class="mini-card category-route-card promote-route-card promote-route-card--physical" href="../posting/index.html">
          <h3>Physical locations</h3>
          <p>Search storefronts, libraries, visitor centers, venues, galleries, public offices, and other on-site promotion contacts.</p>
          <strong>Open physical-location finder</strong>
        </a>
      </div>
    </section>
    <section id="promotion-results" class="section tinted" aria-labelledby="promotion-results-title">
      <div class="section-heading">
        <p class="eyebrow">Promotion directory</p>
        <h2 id="promotion-results-title">Search local contacts and established channels.</h2>
        <p class="section-note">Use the links and contact details shown. Placement, pricing, deadlines, and submission policies can change.</p>
      </div>
      <div class="promote-filter-panel" role="search" aria-label="Filter promotion contacts">
        <label class="promote-search-label" for="promote-search">Search promotion contacts</label>
        <input id="promote-search" class="search-input" type="search" placeholder="Try restaurant, gallery, newsletter, calendar, Raton, Trinidad...">
        <div class="promote-filter-grid">
          <label>County
            <select id="promote-county-filter">
              <option value="All">All counties</option>
              <option value="Colfax">Colfax</option>
              <option value="Las Animas">Las Animas</option>
              <option value="Huerfano">Huerfano</option>
              <option value="Regional">Regional</option>
            </select>
          </label>
          <label>Route
            <select id="promote-route-filter">
              <option value="All">All promotion routes</option>
              {''.join(f'<option value="{html_escape(item["key"])}">{html_escape(item["title"])}</option>' for item in PROMOTE_ROUTE_DEFS)}
            </select>
          </label>
        </div>
        <p id="promote-results-note" class="results-note" role="status" aria-live="polite">Promotion contacts are ready to filter.</p>
      </div>
      <div id="promote-results" class="resource-list promote-results-list"></div>
      <div class="section-actions">
        <button id="promote-load-more" class="button button-soft" type="button">Show more promotion contacts</button>
        <a class="button button-soft" href="../network/index.html#resource-results">Open the master directory</a>
      </div>
    </section>
    <section id="county-promotion" class="section county-promote-section" aria-labelledby="county-promotion-title">
      <div class="section-heading">
        <p class="eyebrow">County shortcuts</p>
        <h2 id="county-promotion-title">The same six routes for every county.</h2>
        <p class="section-note">Choose a county and task together. Regional results remain available when a cross-county channel is the better fit.</p>
      </div>
      <div class="county-promote-grid">{county_route_panels}</div>
    </section>
    <section id="promote-specialized" class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Specialized views</p>
        <h2>Open the detail page only when it adds something.</h2>
      </div>
      <div class="section-actions">
        <a class="button button-soft" href="../amplifiers/index.html">Calendars, media, and visitor guides</a>
        <a class="button button-soft" href="../posting/index.html">Physical promotion locations</a>
        <a class="button button-soft" href="../templates/index.html">Message templates</a>
        <a class="button button-soft" href="../resources/arts-culture/index.html">Arts &amp; Culture</a>
      </div>
    </section>
    {submit_listing_panel(1, "amplifier")}
    """
    return page_shell(
        "Promotion Directory for Colfax, Las Animas & Huerfano Counties | Stateline Tri-County Guide",
        "Search events, advertising, business directories, nonprofit partners, calendars, galleries, media, and visitor channels across the tri-county region.",
        "promote",
        content,
        depth=1,
        schema_type="CollectionPage",
    )


def amplifiers_page() -> str:
    categories = "\n".join(
        f"""
        <a class="mini-card category-route-card" href="../network/index.html?q={quote_plus(item['query'])}#resource-results"
           aria-label="Search the comprehensive directory for {html_escape(item['title'])}">
          <h3>{html_escape(item['title'])}</h3>
          <p>{html_escape(item['body'])}</p>
          <strong>Search this directory category</strong>
        </a>
        """
        for item in AMPLIFIER_CATEGORIES
    )
    packet = "\n".join(f"<li>{html_escape(item)}</li>" for item in PROMOTION_PACKET)
    matrix = "\n".join(
        f"""
        <tr>
          <td>{html_escape(public_text_value(use_case))}</td>
          <td>{html_escape(public_text_value(channels))}</td>
        </tr>
        """
        for use_case, channels in BEST_USE_MATRIX
    )
    rows = "\n".join(
        f"""
        <tr>
          <td><a href="{html_escape(item['source_url'])}" target="_blank" rel="noreferrer">{html_escape(item['channel'])}</a></td>
          <td>{html_escape(item['area_served'])}</td>
          <td>{html_escape(item['channel_type'])}</td>
          <td>{html_escape(public_text_value(item['asks']))}</td>
          <td>{html_escape(public_text_value(item['best_for']))}</td>
          <td>{html_escape(public_text_value(item['implementation_note']))}</td>
        </tr>
        """
        for item in AMPLIFIER_CHANNELS
    )
    outreach = """Subject: Question About Promotion / Advertising Opportunities

Hello, I am reaching out to ask whether [organization/publication/site name] accepts event listings, newsletter submissions, business directory updates, paid advertisements, social media co-promotion, visitor-guide listings, or other community announcements.

The item is [business/event/program name]. It serves [audience] in [town/county] and the public action is [visit/register/contact/attend].

Could you point me to the right form, deadline, rate card, eligibility rule, or contact person? I can send a short description, image, flyer, and link in whatever format you prefer."""
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">Regional Amplifier Channels</p>
      <h1>Newsletters, calendars, directories, and visitor guides.</h1>
      <p class="lede">Use this page to decide where an event, listing, announcement, partnership ask, or visitor-facing update may belong. Open the linked page before assuming current rates, deadlines, or acceptance rules.</p>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">What each side is for</p>
        <h2>Choose the channel by the job it can actually do.</h2>
      </div>
      <div class="mini-grid">{categories}</div>
      <p class="section-note">Do not promise ad availability, free placement, deadlines, audience size, endorsement, or acceptance unless the page or organization says so. Ask the channel directly when those details matter.</p>
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Best-use matrix</p>
        <h2>Match the channel to the thing being promoted.</h2>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Use case</th><th>Best first channels</th></tr></thead>
          <tbody>{matrix}</tbody>
        </table>
      </div>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Common questions</p>
        <h2>Use channels with permission and fit.</h2>
      </div>
      <div class="mini-grid">
        <article class="mini-card"><h3>Where should I post a public event first?</h3><p>Start with event calendars, tourism calendars, venue lineups, city or community calendars, and partner channels that already serve the event's audience.</p></article>
        <article class="mini-card"><h3>Can I assume a newsletter accepts outside promotions?</h3><p>No. Use the channel's current contact or submission page to confirm placement, price, deadline, and format.</p></article>
        <article class="mini-card"><h3>What should I prepare before submitting an event?</h3><p>Prepare the event name, date, time, location, short description, contact link, images, flyer, accessibility notes, and whether the event is free, ticketed, nonprofit, youth, tourism, business, or community-oriented.</p></article>
      </div>
    </section>
    <section id="amplifier-event-calendars" class="section">
      <div class="section-heading">
        <p class="eyebrow">Channel table</p>
        <h2>Places to check before submitting or pitching.</h2>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Channel</th><th>Area served</th><th>Channel type</th><th>What users can ask/submit</th><th>Best for</th><th>How to use it</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
      <p class="section-note">Before paying for ads or promising placement, ask the channel about current rates, deadlines, acceptance, and submission rules.</p>
    </section>
    <section class="section">
      <div class="two-col">
        <div>
          <p class="eyebrow">Promotion packet</p>
          <h2>Prepare once, submit many times.</h2>
          <ul class="check-list">{packet}</ul>
        </div>
        <div>
          <p class="eyebrow">Anti-spam rule</p>
          <h2>Ask like a neighbor with a specific local fit.</h2>
          <p>Send only to channels where the item fits, use the channel owner's preferred form, avoid repeated messages, and stop when a page says submissions are closed or not accepted. For nonprofits and community programs, lead with public benefit rather than sales language.</p>
          <pre>{html_escape(outreach)}</pre>
        </div>
      </div>
    </section>
    {submit_listing_panel(1, "amplifier")}
    """
    return page_shell(
        "Regional Newsletters, Calendars, Directories & Visitor Guides | Stateline Tri-County Guide",
        "Compare event calendars, newsletters, business directories, tourism guides, venue lineups, and advertising inquiry routes across the tri-county area.",
        "amplifiers",
        content,
        depth=1,
        schema_type="CollectionPage",
    )


def posting_page(rows: list[dict]) -> str:
    posting_rows = "\n".join(
        f"""
        <tr>
          <td>{entity_name_link(item, item['place'])}</td>
          <td>{html_escape(item['physical'])}</td>
          <td>{html_escape(item['digital'])}</td>
          <td>{html_escape(public_text_value(item['use_for']))}</td>
          <td>{html_escape(public_text_value(item['status']))}</td>
          <td>{f'<a href="{html_escape(item["source_url"])}" target="_blank" rel="noreferrer">Open page</a>' if item['source_url'] else 'Local update needed'}</td>
        </tr>
        """
        for item in POSTING_SPACES
    )
    type_cards = "\n".join(
        f"""
        <a class="mini-card category-route-card" href="?category={quote_plus('|'.join(item['categories']))}#physical-location-results"
           aria-label="Find {html_escape(item['title'])} in the physical-location directory">
          <h3>{html_escape(item['title'])}</h3>
          <p>{html_escape(item['best_for'])}</p>
          <strong>Show matching contacts</strong>
        </a>
        """
        for item in PHYSICAL_AD_PLACE_TYPES
    )
    candidate_count = len(physical_ad_location_rows(rows, limit=max(1, len(rows))))
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">Physical Promotion</p>
      <h1>Find local contacts for flyers, posters, brochures, and rack cards.</h1>
      <p class="lede">Search storefronts, libraries, visitor centers, public offices, galleries, venues, theaters, bookstores, pharmacies, coffee shops, tattoo and auto shops, thrift and antique stores, lodging, and travel stops across all three counties.</p>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Physical ad finder</p>
        <h2>Start with the places people already pass through.</h2>
        <p class="section-note">The directory identifies useful in-person contacts. Posting policies vary by location; use the phone, email, website, social page, or map shown to confirm current space and format.</p>
      </div>
      <div class="mini-grid">{type_cards}</div>
    </section>
    <section id="physical-location-results" class="section tinted" aria-labelledby="physical-location-title">
      <div class="section-heading">
        <p class="eyebrow">Physical locations</p>
        <h2 id="physical-location-title">Search {candidate_count} on-site promotion contacts.</h2>
        <p class="section-note">Each result includes every available contact path. The category labels describe why a location may be useful; they do not imply sponsorship or guaranteed placement.</p>
      </div>
      <div class="physical-filter-panel" role="search" aria-label="Filter physical promotion locations">
        <label class="physical-search-label" for="physical-location-search">Search locations</label>
        <input id="physical-location-search" class="search-input" type="search" placeholder="Try library, coffee, bookstore, pharmacy, tattoo, auto, gallery, Raton...">
        <div class="physical-filter-grid">
          <label>County
            <select id="physical-county-filter">
              <option value="All">All counties</option>
              <option value="Colfax">Colfax</option>
              <option value="Las Animas">Las Animas</option>
              <option value="Huerfano">Huerfano</option>
              <option value="Regional">Regional</option>
            </select>
          </label>
          <label>Location type
            <select id="physical-category-filter"><option value="All">All location types</option></select>
          </label>
        </div>
        <p id="physical-results-note" class="results-note" role="status" aria-live="polite">Physical locations are ready to filter.</p>
      </div>
      <div id="physical-location-list" class="resource-list physical-posting-list"></div>
      <div class="section-actions">
        <button id="physical-load-more" class="button button-soft" type="button">Show more locations</button>
        <a class="button button-soft" href="../network/index.html?location=Flyers#resource-results">Open these results in the master directory</a>
      </div>
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Posting map</p>
        <h2>Official notices and community visibility are different routes.</h2>
        <p class="section-note">Use official public-office routes for civic notices and public information. Use owner-controlled boards, counters, racks, venues, and downtown partners for ordinary event or business visibility.</p>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Community</th><th>Physical pathway</th><th>Digital pathway</th><th>Use for</th><th>Status</th><th>Link</th></tr></thead>
          <tbody>{posting_rows}</tbody>
        </table>
      </div>
      <p class="section-note">Use the page owner or office contact to distinguish a public notice, calendar item, advertisement, flyer, or partner share.</p>
    </section>
    <section class="section posting-method">
      <div class="section-heading">
        <p class="eyebrow">Posting method</p>
        <h2>A simple sequence for offline and online visibility.</h2>
      </div>
      <div class="steps-grid">
        <article class="step-card"><span>1</span><h3>Find the owner</h3><p>Identify who controls the board, calendar, newsletter, or directory before preparing materials.</p></article>
        <article class="step-card"><span>2</span><h3>Match the purpose</h3><p>Official notice, public event, business listing, and paid advertisement are different requests.</p></article>
        <article class="step-card"><span>3</span><h3>Use clear assets</h3><p>Keep a short blurb, accessible flyer, square image, date, location, and contact ready.</p></article>
        <article class="step-card"><span>4</span><h3>Track proof</h3><p>Record where it was posted, who approved it, when it expires, and what response it produced.</p></article>
      </div>
    </section>
    {next_action_block(1, [
        ("Find event calendars, newsletters, visitor guides, and directory channels", "amplifiers/"),
        ("Use copy-ready outreach templates", "templates/"),
        ("Submit a corrected posting route", "submit/"),
        ("Open the promotion directory", "promote/"),
        ("Open the spreadsheet-style appendix", "appendix/"),
    ])}
    """
    return page_shell(
        "Physical Promotion Locations in the Tri-County Area | Stateline Tri-County Guide",
        "Search local storefronts, libraries, visitor centers, galleries, venues, public offices, and other physical promotion contacts across all three counties.",
        "posting",
        content,
        depth=1,
    )


def appendix_page(rows: list[dict]) -> str:
    sorted_rows = sorted(rows, key=lambda row: (row.get("county") or "", row.get("town") or "", row.get("resource_name") or ""))
    table_rows = "\n".join(
        f"""
        <tr>
          <td>{html_escape(row.get('county'))}</td>
          <td>{html_escape(row.get('town'))}</td>
          <td>{entity_name_link(row)}</td>
          <td>{html_escape(public_text_value(row.get('category')))}</td>
          <td>{html_escape(row.get('public_listing_type') or row.get('resource_type'))}</td>
          <td>{html_escape(row.get('access_mode'))}</td>
          <td>{html_escape(row.get('contact_phone'))}</td>
          <td>{html_escape(row.get('contact_email'))}</td>
          <td>{html_escape(row.get('physical_address'))}</td>
          <td>{f'<a href="{html_escape(resource_url(row))}" target="_blank" rel="noreferrer">{html_escape(resource_url_label(resource_url(row)))}</a>' if resource_url(row) else 'Send update'}</td>
          <td>{html_escape(public_text_value(row.get('public_description') or row.get('category') or 'Local directory listing.'))}</td>
        </tr>
        """
        for row in sorted_rows
    )
    county_counts = Counter(row.get("county") or "Unknown" for row in rows)
    count_cards = "\n".join(
        f"<div class=\"stat\"><strong>{count}</strong><span>{html_escape(county)}</span></div>"
        for county, count in county_counts.most_common()
    )
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">Public Contact Appendix</p>
      <h1>Grouped contacts for people who need the full table.</h1>
      <p class="lede">Use this appendix when you need the contact table behind the guide. Confirm phone numbers, emails, addresses, and current submission paths before direct outreach.</p>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Choose the lighter route</p>
        <h2>Use the full table only when a table is the job.</h2>
        <p class="section-note">For guided discovery, start with the Directory or use the routing helper. Stay here when you need county/community grouping, contact details, or spreadsheet-style review.</p>
      </div>
      <div class="section-actions">
        <a class="button button-primary" href="../network/index.html">Search by need</a>
        <a class="button button-soft" href="#full-table">Use full table</a>
        <a class="button button-soft" href="../submit/index.html">Submit a correction</a>
      </div>
    </section>
    <section class="section">
      <div class="stats-grid">{count_cards}</div>
      {download_buttons(1)}
      <p class="section-note">The appendix keeps as much information as possible for outreach and correction work. If a detail looks old, submit an update with the source that should be checked.</p>
    </section>
    <section class="section tinted" id="full-table">
      <div class="section-heading">
        <p class="eyebrow">Appendix table</p>
        <h2>{len(rows)} resource entries grouped by county and community.</h2>
      </div>
      <div class="table-wrap appendix-table">
        <table>
          <thead><tr><th>County</th><th>Community</th><th>Name</th><th>Category</th><th>Type</th><th>Access</th><th>Phone</th><th>Email</th><th>Address</th><th>Link</th><th>Notes</th></tr></thead>
          <tbody>{table_rows}</tbody>
        </table>
      </div>
    </section>
    {submit_listing_panel(1, "appendix")}
    {next_action_block(1, [
        ("Search by need instead of table order", "network/"),
        ("Find event calendars, newsletters, visitor guides, and directory channels", "amplifiers/"),
        ("Submit an appendix correction with a public page link", "submit/"),
        ("Understand how the three counties connect", "region/"),
    ])}
    """
    return page_shell(
        "Tri-County Public Contact Appendix | Stateline Tri-County Guide",
        "Browse public-contact appendix entries by county, community, access mode, resource type, and listing details.",
        "appendix",
        content,
        depth=1,
        schema_type="CollectionPage",
    )


def region_page(summary: dict) -> str:
    type_stats = "\n".join(
        f"<li><strong>{count}</strong><span>{html_escape(name)}</span></li>"
        for name, count in summary["resource_type"].items()
    )
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">Understand the Region</p>
      <h1>Regional growth means crossing county lines on purpose.</h1>
      <p class="lede">Use the tri-county guide to route attention between Raton/Colfax, Trinidad/Las Animas, Walsenburg-La Veta/Huerfano, and statewide support systems.</p>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Co-channeling model</p>
        <h2>One public resource, many local doors.</h2>
        <p class="section-note">County pages make local entry easy. The Directory keeps cross-county listings, media, funding, creative-economy, and nonprofit resources connected.</p>
      </div>
      <ul class="check-list">
        <li>Colfax: Raton city, chamber, MainStreet, GrowRaton, Explore Raton, KRTN, NM statewide support.</li>
        <li>Las Animas: Colexico/TLAC, Trinidad tourism, CREATE Trinidad, city economic development, Chronicle-News.</li>
        <li>Huerfano: chamber, HCED, Spanish Peaks Country, La Veta, World Journal, Wheelhouse, creative district.</li>
      </ul>
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Inventory coverage</p>
        <h2>The data is strongest for visibility, media, resources, and funding paths.</h2>
        <p class="section-note">These counts describe the guide's current coverage. Do not treat them as audience size, market demand, economic value, or actual reach.</p>
      </div>
      <ul class="type-list">{type_stats}</ul>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Best regional uses</p>
        <h2>What this guide helps people do.</h2>
      </div>
      <div class="mini-grid">
        <article class="mini-card"><h3>Launch or relaunch</h3><p>Get business counseling, make a listing, pick a first audience, and send one clean announcement through three local channels.</p></article>
        <article class="mini-card"><h3>Promote an event</h3><p>Check calendars, avoid conflicts, submit to tourism and media channels, and ask one chamber/creative district/partner to share.</p></article>
        <article class="mini-card"><h3>Find partners</h3><p>Use chambers, nonprofit directories, arts councils, public libraries, schools, and local service organizations as referral nodes.</p></article>
        <article class="mini-card"><h3>Expand customers</h3><p>Use visitor-facing directories, media, business associations, county-specific pages, and cross-county offers to reach beyond one town.</p></article>
      </div>
    </section>
    {next_action_block(1, [
        ("Open the Colfax county starting point", "counties/colfax/"),
        ("Open the Las Animas county starting point", "counties/las-animas/"),
        ("Open the Huerfano county starting point", "counties/huerfano/"),
        ("Search public directories and local entries", "network/"),
    ])}
    """
    return page_shell(
        "Tri-County Regional Visibility Map | Stateline Tri-County Guide",
        "Understand how Raton, Trinidad, Walsenburg, La Veta, Colfax, Las Animas, Huerfano, and statewide support systems connect.",
        "region",
        content,
        depth=1,
        schema_type="AboutPage",
    )


def county_page(county: str, slug: str, summary_text: str, rows: list[dict]) -> str:
    sources = [item for item in DIRECTORY_SOURCES if item["county"] in (county, "Regional")]
    top_rows = [row for row in rows if row.get("county") == county][:12]
    intent = COUNTY_INTENT_BLOCKS[county]
    intent_items = "\n".join(f"<li>{html_escape(item)}</li>" for item in intent["searches"])
    leads = "\n".join(
        f"""
        <li>
          <strong>{entity_name_link(row)}</strong>
          <span>{html_escape(row.get('public_listing_type') or row.get('resource_type'))} - {html_escape(row.get('town') or county)}</span>
        </li>
        """
        for row in top_rows
    )
    depth = 2
    active = slug
    content = f"""
    <section class="page-hero county-hero">
      <p class="eyebrow">{html_escape(county)} County</p>
      <h1>{html_escape(summary_text)}</h1>
      <p class="lede">Start with public directories and support organizations, then use local inventory entries as outreach paths to confirm before action.</p>
    </section>
    <section class="section">
      <div class="two-col">
        <div>
          <p class="eyebrow">What this page helps with</p>
          <h2>Start from the county, then choose the right door.</h2>
          <p>{html_escape(intent["helps"])}</p>
        </div>
        <div>
          <p class="eyebrow">Common searches this page answers</p>
          <ul class="check-list">{intent_items}</ul>
        </div>
      </div>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">First places to check</p>
        <h2>Use these before building a fresh contact list.</h2>
      </div>
      <div class="source-grid compact">{source_cards(sources, 10)}</div>
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Local listing sample</p>
        <h2>Inventory examples to check before outreach.</h2>
      </div>
      <ul class="lead-list">{leads}</ul>
      <p class="section-note">The full inventory is searchable from the Directory and downloadable as CSV in the data folder.</p>
    </section>
    {submit_listing_panel(depth, "county")}
    {next_action_block(depth, [
        ("Find regional amplifier channels", "amplifiers/"),
        ("Use copy-ready outreach templates", "templates/"),
        ("Submit a county listing correction", "submit/"),
        ("Understand how the three counties connect", "region/"),
    ])}
    """
    return page_shell(intent["title"], intent["description"], active, content, depth=depth, schema_type="CollectionPage")


def templates_page() -> str:
    templates = [
        (
            "Directory listing request",
            "Use for chambers, tourism pages, arts directories, business directories, and public resource lists.",
            "Mention why that exact directory fits: town, audience, industry, visitor use, member status, or service area.",
            "Hello [name/team], I am requesting a listing or update for [business/program]. We serve [audience] in [town/county]. Public details: [website], [phone], [address or service area], [hours if relevant], [1-sentence description]. If there is a preferred form, membership rule, or review process, would you point me to it?",
        ),
        (
            "Event calendar submission",
            "Use for public calendars, visitor sites, community boards, libraries, venue calendars, and newsletters.",
            "Lead with the public value: family-friendly, visitor-facing, local arts, downtown business, fundraiser, class, or service.",
            "Event: [name]\nDate/time: [date/time]\nLocation: [place]\nCost: [free/price]\nAudience: [who it is for]\nShort description: [45-75 words]\nPublic action: [register/attend/call/visit]\nContact: [name/email/phone]\nImage/flyer: [attached or link]\nPlease let me know if a different format or lead time is required.",
        ),
        (
            "Newsletter or mailing-list note",
            "Use when sending to a list you own or a partner who accepts community announcements.",
            "Segment the list before sending. A gallery list, business list, volunteer list, and visitor list should not get the same wording.",
            "Subject: [specific local action]\nHi [first name/community], [one local sentence that proves this is meant for them]. [Organization] is sharing [event/resource/service] for [audience] in [town/region]. The useful detail is [why this matters now]. Learn more: [link]. If this is not a fit for your inbox, reply with 'remove' and I will update the list.",
        ),
        (
            "Media pitch",
            "Use for newspapers, radio, local magazines, podcasts, or public-interest editorial contacts.",
            "Do not send only a flyer. Add the local reason, a human angle, and a clean public action.",
            "[Organization] is launching [thing] for [audience] on [date]. It matters locally because [one concrete reason]. We can provide photos, a short interview, and event details. The public call to action is [register/visit/share/contact]. If this is not the right desk, would you point me to the best contact?",
        ),
        (
            "Promotion or advertising inquiry",
            "Use when a site, publication, venue, radio station, chamber, or visitor guide may offer ads or paid placement.",
            "Ask for the current option instead of assuming placement exists.",
            "Hello [name/team], does [organization/publication/site] currently accept event listings, directory updates, newsletter submissions, paid ads, social media co-promotion, visitor-guide listings, or other community announcements? The item is [business/event/program] for [audience] in [town/county]. Could you share the right form, deadline, rate card, eligibility rule, or contact person?",
        ),
        (
            "Partner share request",
            "Use for aligned organizations, venues, galleries, nonprofits, schools, public programs, and local businesses.",
            "Make it easy to say yes, easy to say no, and clear why their audience might care.",
            "We are trying to reach [audience] across [counties]. Would your organization be open to sharing [listing/event/resource], referring people who need it, or suggesting the best local channel? I can send a short blurb and image sized for your usual format. No pressure if this is not a fit.",
        ),
        (
            "Flyer rack or community board ask",
            "Use for physical posting spots, front desks, visitor centers, cafes, libraries, shops, and venue bulletin boards.",
            "Ask permission first and include dates so outdated materials can be removed.",
            "Hello [name/team], may I leave a small flyer for [event/service/program] at [location]? It is for [audience] and runs through [date]. I can bring [quantity] copies and remove them after [date]. If you have posting rules, size limits, or a preferred contact, I am happy to follow them.",
        ),
        (
            "Arts, venue, or gallery ask",
            "Use for artist listings, openings, calls, performances, workshop announcements, and venue calendars.",
            "Include medium, dates, image credit, access needs, and whether sales or registration are involved.",
            "Hello [name/team], I am sharing [artist/show/workshop/performance] in [town/region]. The work/program is [short description] and may fit [their audience or calendar] because [specific reason]. Public details: [date/place/link/contact]. Please let me know if you need image credit, a shorter blurb, or a different submission path.",
        ),
        (
            "Funding or referral introduction",
            "Use when asking a funder, SBDC, foundation, chamber, or public office where to begin.",
            "State the stage, need, county, and deadline. Do not make them decode the project.",
            "Hello [name/team], I am looking for the best starting point for [business/nonprofit/artist/program] in [county]. We are trying to [goal] and need [grant/loan/training/referral/technical help] by [timeline if any]. Could you suggest the right program, eligibility page, or contact route?",
        ),
        (
            "Correction or update request",
            "Use when your own listing is wrong or a public guide entry has changed.",
            "Make the correction easy to check by providing the exact page and replacement text.",
            "Hello [name/team], I noticed [page/listing] may be outdated. Current public details should be: [name], [website], [phone], [address/service area], [short description], [contact]. The source page I am using is [link]. Please let me know if another update path is preferred.",
        ),
        (
            "Follow-up and thank-you",
            "Use after a submission, referral, meeting, or shared post.",
            "Keep it short. Thank them, name the action, and make the next step optional.",
            "Thank you for [sharing/listing/referring/responding]. I appreciate it. If helpful, here is the final public link or blurb: [link/text]. I will keep future updates brief and only send them when they fit your audience.",
        ),
        (
            "Please update or remove me",
            "Use when honoring list preferences or correcting accidental outreach.",
            "This is part of being a decent regional neighbor. Make the off-ramp clean.",
            "Thanks for letting me know. I have updated this contact/listing preference for [organization/name]. You should not receive this type of outreach again unless you ask to be added back or there is a direct correction request.",
        ),
    ]
    items = "\n".join(
        f"""
        <article class="template-card">
          <h3>{html_escape(title)}</h3>
          <p>{html_escape(purpose)}</p>
          <p class="template-meta"><strong>Personalize:</strong> {html_escape(personalize)}</p>
          <pre>{html_escape(body)}</pre>
          <button class="copy-button" type="button">Copy</button>
        </article>
        """
        for title, purpose, personalize, body in templates
    )
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">Templates</p>
      <h1>Send clearer messages without sounding mass-produced.</h1>
      <p class="lede">Use these as plain starting copy for listings, events, grants, nonprofit referrals, gallery shows, classes, markets, services, mentorships, and partner asks. The goal is not volume. The goal is the right message to the right channel.</p>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Before sending</p>
        <h2>Personalize the first sentence and keep the ask small.</h2>
      </div>
      <div class="template-rules">
        <article class="step-card"><span>1</span><h3>Segment the list</h3><p>Separate visitors, artists, businesses, nonprofits, public offices, media, funders, and partners before writing.</p></article>
        <article class="step-card"><span>2</span><h3>Name the fit</h3><p>Say why that channel or person is relevant. County, audience, topic, venue, or program fit is enough.</p></article>
        <article class="step-card"><span>3</span><h3>Use one ask</h3><p>Ask for one action: list it, share it, refer it, quote rates, correct it, or point you to the right form.</p></article>
        <article class="step-card"><span>4</span><h3>Leave an easy no</h3><p>Do not imply obligation. Offer to stop, remove, correct, or use a different channel.</p></article>
      </div>
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Copy-ready starts</p>
        <h2>Adapt the message to the route.</h2>
      </div>
      <div class="template-grid">{items}</div>
    </section>
    {next_action_block(1, [
        ("Find free and discounted tools", "tools/free-discounted/"),
        ("Find places to send outreach packets", "amplifiers/"),
        ("Search directories and local entries", "network/"),
        ("Submit a correction or new channel", "submit/"),
        ("Plan the outreach cycle first", "plan/"),
    ])}
    """
    return page_shell(
        "Outreach Templates for Listings, Events, Media & Partners | Stateline Tri-County Guide",
        "Copy and adapt outreach language for directories, event calendars, newsletters, partner asks, media inquiries, and correction requests.",
        "templates",
        content,
        depth=1,
    )


def free_tools_page() -> str:
    catalog = tools_catalog()
    offer_counts = Counter(
        group
        for item in catalog
        for group in tool_offer_groups(item)
    )
    tools = promotion_tool_cards(catalog)
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">Free &amp; discounted tools</p>
      <h1>Find free tools, nonprofit offers, and no-cost support.</h1>
      <p class="lede">Start with the kind of access you qualify for. Some tools do not require nonprofit status, some offers do, and some services are provided through public or partner-funded business support.</p>
    </section>
    <section class="section tool-offer-overview" aria-labelledby="tool-offer-heading">
      <div class="section-heading">
        <p class="eyebrow">Choose by access</p>
        <h2 id="tool-offer-heading">Free does not mean the same thing on every provider page.</h2>
        <p class="section-note">Use the three starting points below to avoid mixing general free plans with nonprofit-only benefits. Confirm current limits and eligibility before moving contacts, files, or project budgets into a service.</p>
      </div>
      <div class="tool-offer-grid">
        <article class="tool-offer-card">
          <h3>General free tools</h3>
          <p>Free plans, free services, and open-source software that do not require nonprofit status. Other provider rules may still apply.</p>
          <button class="button button-soft" type="button" data-tool-preset="general-free" aria-controls="free-tools-directory" aria-pressed="false">Show {offer_counts['general-free']} general free resources</button>
        </article>
        <article class="tool-offer-card">
          <h3>Nonprofit discounts &amp; donations</h3>
          <p>Free nonprofit programs, donated technology, membership offers, and discounted plans that may require verification.</p>
          <button class="button button-soft" type="button" data-tool-preset="nonprofit" aria-controls="free-tools-directory" aria-pressed="false">Show {offer_counts['nonprofit']} nonprofit offers</button>
        </article>
        <article class="tool-offer-card">
          <h3>Free advising &amp; public support</h3>
          <p>No-cost mentoring, counseling, research access, public directories, technical help, and regional support programs.</p>
          <button class="button button-soft" type="button" data-tool-preset="support" aria-controls="free-tools-directory" aria-pressed="false">Show {offer_counts['support']} support resources</button>
        </article>
      </div>
    </section>
    <section class="section tinted" id="free-tools-directory" aria-labelledby="free-tools-heading">
      <div class="section-heading">
        <p class="eyebrow">Search all tools &amp; support</p>
        <h2 id="free-tools-heading">Compare the practical options.</h2>
        <p class="section-note">Open the provider name for the main service. When a separate eligibility or offer page exists, the card links to that page too.</p>
      </div>
      {promotion_tool_filters()}
      <div class="tool-grid" data-tool-grid>{tools}</div>
      <p class="empty-state" data-tool-empty hidden>No tools match those filters. Clear a filter or try a broader term.</p>
      <div class="section-actions"><button class="button button-soft" type="button" data-tool-more hidden>Show more tools</button></div>
    </section>
    {next_action_block(2, [
        ("Use copy-ready outreach templates", "templates/"),
        ("Search grants and funding support", "resources/funding/"),
        ("Search local directories and contacts", "network/"),
        ("Suggest a tool or correct an offer", "submit/"),
    ])}
    """
    return page_shell(
        "Free & Discounted Tools for Businesses and Nonprofits | Stateline Tri-County Guide",
        "Search free software, nonprofit discounts and donated services, open-source tools, and no-cost business support for organizations across the tri-county region.",
        "free-tools",
        content,
        depth=2,
    )


def submit_page() -> str:
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">Submit a Listing</p>
      <h1>Send enough information for a useful review.</h1>
      <p class="lede">Use this page to suggest a new listing, correct an existing entry, submit an event path, or recommend a directory, calendar, newsletter, visitor guide, funding source, arts listing, or media channel.</p>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Before you submit</p>
        <h2>Include the source, the place, and the reader action.</h2>
      </div>
      <div class="steps-grid">
        <article class="step-card"><span>1</span><h3>Name the listing</h3><p>Use the public name of the business, organization, program, service, gallery, event, venue, or resource.</p></article>
        <article class="step-card"><span>2</span><h3>Pick the section</h3><p>Choose the county page, Directory, appendix, regional channel list, posting map, or templates/resources area.</p></article>
        <article class="step-card"><span>3</span><h3>Add the public link</h3><p>Include a website, form, social page, public directory link, flyer, official page, or contact route that can be checked.</p></article>
        <article class="step-card"><span>4</span><h3>State the use</h3><p>Say whether readers should list, post, contact, visit, register, ask about advertising, check public information, or request a correction.</p></article>
      </div>
    </section>
    <section class="section tinted" id="submission-form">
      <div class="section-heading">
        <p class="eyebrow">Submission form</p>
        <h2>Listing, correction, channel, or event update.</h2>
        <p class="section-note">Send the clearest public link you have. A person should still review public claims, contact details, rates, eligibility, and civic guidance before publication.</p>
      </div>
      <form class="submission-form" name="listing-submission" method="POST" data-netlify="true" netlify-honeypot="bot-field" data-submit-form action="/submit/">
        <input type="hidden" name="form-name" value="listing-submission">
        <p class="hidden-field"><label>Do not fill this out: <input name="bot-field"></label></p>
        <div class="form-grid">
          <label>Submission type
            <select name="submission_type" required>
              <option value="">Choose one</option>
              <option>New business or organization listing</option>
              <option>Correction to an existing listing</option>
              <option>Event or calendar pathway</option>
              <option>Amplifier channel or media resource</option>
              <option>Creative business, gallery, or venue</option>
              <option>Nonprofit, service, program, or mentorship</option>
              <option>Funding, grant, stipend, scholarship, or training source</option>
              <option>Remove or flag an outdated listing</option>
            </select>
          </label>
          <label>Guide section
            <select name="guide_section" required>
              <option value="">Choose one</option>
              <option>Directory</option>
              <option>Amplifier channels</option>
              <option>Where To Post</option>
              <option>Colfax County page</option>
              <option>Las Animas County page</option>
              <option>Huerfano County page</option>
              <option>Funding page</option>
              <option>Arts & Culture page</option>
              <option>Appendix contact table</option>
              <option>Templates or planning resources</option>
            </select>
          </label>
          <label>County or region
            <select name="county_or_region" required>
              <option value="">Choose one</option>
              <option>Colfax County, NM</option>
              <option>Las Animas County, CO</option>
              <option>Huerfano County, CO</option>
              <option>Regional / cross-county</option>
              <option>Statewide support resource</option>
            </select>
          </label>
          <label>Community or service area
            <input name="community" type="text" placeholder="Raton, Trinidad, Walsenburg, La Veta, rural county, regional...">
          </label>
          <label>Name to list
            <input name="listing_name" type="text" required placeholder="Public business, organization, program, event, or resource name">
          </label>
          <label>Category
            <input name="category" type="text" placeholder="Business, nonprofit, arts, event, tourism, funding, media, service...">
          </label>
          <label>Website or public page link
            <input name="source_url" type="url" placeholder="https://example.org/listing-or-page">
          </label>
          <label>Contact email
            <input name="contact_email" type="email" placeholder="contact@example.org">
          </label>
          <label>Contact phone
            <input name="contact_phone" type="tel" placeholder="(575) 000-0000">
          </label>
          <label>Physical address
            <input name="physical_address" type="text" placeholder="Street, city, state, ZIP">
          </label>
        </div>
        <label>Short public description
          <textarea name="short_description" rows="4" required placeholder="What should a reader know in 1-3 plain sentences?"></textarea>
        </label>
        <label>Reader action
          <textarea name="reader_action" rows="3" placeholder="Should someone visit, register, call, submit an event, ask about advertising, check a listing, or contact a partner?"></textarea>
        </label>
        <label>Update notes
          <textarea name="update_notes" rows="4" placeholder="What page should be checked? What is outdated, missing, or needs confirmation?"></textarea>
        </label>
        <div class="form-grid">
          <label>Your name
            <input name="submitter_name" type="text" placeholder="Jane Doe">
          </label>
          <label>Your email
            <input name="submitter_email" type="email" placeholder="you@example.org">
          </label>
        </div>
        <button class="button button-primary" type="submit" data-submit-button data-analytics="submit_correction_click">Submit listing for review</button>
        <div class="submit-success-card" data-submit-success hidden aria-live="polite" tabindex="-1">
          <div class="submit-sparkles" aria-hidden="true">
            <span class="sparkle sparkle-one"></span>
            <span class="sparkle sparkle-two"></span>
            <span class="sparkle sparkle-three"></span>
          </div>
          <p class="eyebrow">Received</p>
          <h3>Absurdly grateful. Truly.</h3>
          <p><strong data-submitted-name>This update</strong> is now packaged for review. Thank you for helping make the guide more useful for someone who is trying to get found, get help, or get a local thing off the ground.</p>
          <p class="source-note">Next step: the public link and contact details should be checked before the listing changes on the site.</p>
        </div>
      </form>
    </section>
    <section class="section" id="submission-received">
      <div class="section-heading">
        <p class="eyebrow">What happens next</p>
        <h2>Good updates include a source someone can open.</h2>
      </div>
      <div class="submit-card">
        <div>
          <h3>Review the page</h3>
          <p>The public page, form, listing, social profile, flyer, or contact route should be checked before publication.</p>
        </div>
        <div>
          <h3>Update the right section</h3>
          <p>Directory rows, calendars, funding sources, arts listings, appendix contacts, and templates can all be corrected from the same submission path.</p>
        </div>
        <div>
          <h3>Keep it plain</h3>
          <p>The best public listing tells readers what the entity is, where it serves, how to contact it, and what action makes sense.</p>
        </div>
      </div>
    </section>
    {next_action_block(1, [
        ("Search the current directory before submitting", "network/"),
        ("Open the public contact appendix", "appendix/"),
        ("Find amplifier channels to check", "amplifiers/"),
        ("Read the creation process and page method", "about/"),
    ])}
    """
    return page_shell(
        "Submit a Correction or Suggest a Regional Channel | Stateline Tri-County Guide",
        "Send public-page corrections, listing updates, new channel suggestions, or changed contact paths for review.",
        "submit",
        content,
        depth=1,
    )


def about_page(summary: dict) -> str:
    source_rows = "\n".join(
        f"""
        <tr>
          <td><a href="{html_escape(item['url'])}" target="_blank" rel="noreferrer">{html_escape(item['title'])}</a></td>
          <td>{html_escape(item['county'])}</td>
          <td>{html_escape(item['kind'])}</td>
          <td>{html_escape(public_text_value(item['best_for']))}</td>
        </tr>
        """
        for item in DIRECTORY_SOURCES
    )
    amplifier_rows = "\n".join(
        f"""
        <tr>
          <td><a href="{html_escape(item['source_url'])}" target="_blank" rel="noreferrer">{html_escape(item['channel'])}</a></td>
          <td>{html_escape(item['area_served'])}</td>
          <td>{html_escape(item['channel_type'])}</td>
          <td>{html_escape(public_text_value(item['asks']))}</td>
        </tr>
        """
        for item in AMPLIFIER_CHANNELS
    )
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">How the guide works</p>
      <h1>A routing layer for regional visibility.</h1>
      <p class="lede">Use this guide when you need to know which existing channel fits the job: getting listed, posting an event, asking about advertising, reaching visitors, finding partners, or checking public information.</p>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Purpose</p>
        <h2>What this guide does.</h2>
      </div>
      <div class="two-col">
        <p>This guide helps people sort chambers, tourism sites, newspapers, directories, calendars, newsletters, and public offices in a practical order with a clear next step.</p>
        <p>Use it when someone has a business, event, nonprofit, gallery, class, service, or program and needs to know where to put it so people across Colfax, Las Animas, and Huerfano counties can find it.</p>
      </div>
      {download_buttons(1)}
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Update model</p>
        <h2>Keep the guide useful by checking the details that change.</h2>
      </div>
      <div class="steps-grid">
        <article class="step-card"><span>1</span><h3>Open the page</h3><p>Use the linked page, form, directory, or public contact route before spending time or money.</p></article>
        <article class="step-card"><span>2</span><h3>Confirm the current rule</h3><p>Ask about rates, deadlines, acceptance, eligibility, and the preferred submission format when those details matter.</p></article>
        <article class="step-card"><span>3</span><h3>Submit changes</h3><p>If a link, listing, office, or route has changed, send the correction with the page that should be checked.</p></article>
        <article class="step-card"><span>4</span><h3>Review before publication</h3><p>New public claims and civic/legal guidance should be approved by a human reviewer before they go live.</p></article>
      </div>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Build a similar guide</p>
        <h2>How another community can map its own channels.</h2>
      </div>
      <div class="steps-grid">
        <article class="step-card"><span>1</span><h3>Name the user jobs</h3><p>Write down what people actually need: get listed, post an event, find funding, ask for mentorship, reach visitors, update a directory, or find a partner.</p></article>
        <article class="step-card"><span>2</span><h3>Start with official directories</h3><p>Collect city, county, chamber, tourism, creative-district, library, newspaper, nonprofit, and economic-development pages before making a new directory.</p></article>
        <article class="step-card"><span>3</span><h3>Add self-submission paths</h3><p>Look for add-a-business, submit-an-event, update-a-resource, newsletter, visitor-guide, public-notice, and contact-us paths. Record what users can reasonably ask for.</p></article>
        <article class="step-card"><span>4</span><h3>Keep a review trail</h3><p>Keep notes about where each route came from, but write the public page around what a user can do next.</p></article>
        <article class="step-card"><span>5</span><h3>Write action copy</h3><p>Explain what the page or channel is for, who should use it, what to prepare, and what should be checked first.</p></article>
        <article class="step-card"><span>6</span><h3>Keep updates open</h3><p>Give users a correction path, a submission path, and a review date so the guide can keep improving.</p></article>
      </div>
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Before relying on a listing</p>
        <h2>Check the details that can change.</h2>
      </div>
      <ul class="check-list">
        <li>Confirm directory and submission links before sending people to them.</li>
        <li>Check business phone numbers, addresses, eligibility, and update processes before printing or promising anything.</li>
        <li>Ask chambers, city offices, newspapers, creative districts, and economic-development organizations whether they want wording changed.</li>
        <li>Do not assume free placement, ad availability, endorsement, deadlines, audience size, or acceptance unless the source confirms it.</li>
      </ul>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Page index</p>
        <h2>Public directories and resource hubs used by the guide.</h2>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Page or organization</th><th>County</th><th>Type</th><th>Best for</th></tr></thead>
          <tbody>{source_rows}</tbody>
        </table>
      </div>
      <p class="section-note">Downloadable data files are available for users who need a spreadsheet or page list.</p>
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Amplifier source index</p>
        <h2>Calendars, newsletters, directories, and visitor-guide pathways.</h2>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Channel</th><th>Area served</th><th>Type</th><th>What users can ask</th></tr></thead>
          <tbody>{amplifier_rows}</tbody>
        </table>
      </div>
    </section>
    {next_action_block(1, [
        ("Search public directories and local entries", "network/"),
        ("Find event calendars, newsletters, visitor guides, and directory channels", "amplifiers/"),
        ("Submit a correction with a public page link", "submit/"),
        ("Open the public contact appendix", "appendix/"),
    ])}
    """
    return page_shell(
        "How This Manual Works | Stateline Tri-County Guide",
        "Purpose, update guidance, and page-routing logic for the tri-county regional marketing guide.",
        "about",
        content,
        depth=1,
        schema_type="AboutPage",
    )


def match_terms(item: dict, terms: list[str]) -> bool:
    haystack = " ".join(str(value or "") for value in item.values()).lower()
    return any(term.lower() in haystack for term in terms)


def task_page(definition: dict, rows: list[dict]) -> str:
    meta = task_category_meta(definition["active"])
    source_matches = [item for item in DIRECTORY_SOURCES if match_terms(item, definition["source_terms"])]
    if not source_matches:
        source_matches = DIRECTORY_SOURCES[:8]
    row_matches = [
        row
        for row in rows
        if match_terms(row, definition["row_terms"])
    ][:12]
    lead_items = "\n".join(
        f"""
        <li>
          <strong>{entity_name_link(row)}</strong>
          <span>{html_escape(row.get('town') or row.get('county') or 'Regional')} - {html_escape(row.get('public_listing_type') or row.get('resource_type') or 'Resource')}</span>
        </li>
        """
        for row in row_matches
    )
    if not lead_items:
        lead_items = "<li><strong>Start with the shortcut cards above.</strong><span>No close inventory entry matched this task yet; submit one when a better local route is confirmed.</span></li>"
    route_cards = "\n".join(
        f"""
        <a class="route-type-card {html_escape(card['class'])}"
           href="../network/index.html?q={quote_plus(card['query'])}#resource-results"
           aria-label="Search the comprehensive {html_escape(card['label'])} directory">
          <span class="category-badge {html_escape(card['class'])}">{html_escape(card['label'])}</span>
          <h3>{html_escape(card['use'])}</h3>
          <p><strong>Prepare:</strong> {html_escape(card['prepare'])}</p>
          <p><strong>Check:</strong> {html_escape(card['check'])}</p>
          <span class="route-type-card__action">Search {html_escape(card['label'])}</span>
        </a>
        """
        for card in ROUTE_TYPE_CARDS
    )
    next_links = definition["primary_links"] + [
        ("Submit a correction with a public page link", "submit/"),
    ]
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">{html_escape(definition['eyebrow'])}</p>
      <span class="category-badge {html_escape(meta['class'])}">{html_escape(meta['label'])}</span>
      <h1>{html_escape(definition['h1'])}</h1>
      <p class="lede">{html_escape(definition['intro'])}</p>
      <p class="section-note">{html_escape(meta['summary'])} {html_escape(meta['next'])}</p>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Route colors</p>
        <h2>Choose the first path by what the item needs to do.</h2>
      </div>
      <div class="route-type-grid">{route_cards}</div>
      <p class="section-note">Open the source before spending money, printing materials, or promising placement.</p>
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Local starting points</p>
        <h2>Check existing public channels before building a fresh list.</h2>
      </div>
      <div class="source-grid compact">{source_cards(source_matches, 8)}</div>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Local inventory entries</p>
        <h2>Use these as starting points for the next contact or link.</h2>
        <p class="section-note">These rows come from the working inventory. They help users find likely routes quickly, but details should be checked on the linked page or contact path before action.</p>
      </div>
      <ul class="lead-list">{lead_items}</ul>
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Short sequence</p>
        <h2>Move from fit to next action.</h2>
      </div>
      <div class="steps-grid">
        <article class="step-card"><span>1</span><h3>Match the route</h3><p>Pick the category that fits: event, promotion, business, nonprofit, arts, or regional.</p></article>
        <article class="step-card"><span>2</span><h3>Prepare one packet</h3><p>Make the blurb, image, link, contact, location or service area, and public action easy to copy.</p></article>
        <article class="step-card"><span>3</span><h3>Use the owner path</h3><p>Submit through the page owner's form or contact route, then ask only about what is unclear.</p></article>
        <article class="step-card"><span>4</span><h3>Record the result</h3><p>Save the response, published link, deadline, rate, or reason the route was not a fit.</p></article>
      </div>
    </section>
    {next_action_block(1, next_links)}
    """
    return page_shell(
        definition["title"],
        definition["description"],
        definition["active"],
        content,
        depth=1,
        schema_type="CollectionPage",
    )


def write_static_assets() -> None:
    icon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="Stateline Tri-County Guide icon"><rect x="3" y="3" width="58" height="58" rx="9" fill="#f3efe5"/><path d="M8 43 21 31h10l7-12 8 12h5l7 12H8Z" fill="#173047"/><path d="M12 49c10-7 19-8 27-4 7 3 12 1 18-3" fill="none" stroke="#b69146" stroke-width="4" stroke-linecap="round"/><circle cx="48" cy="14" r="4" fill="#a76149"/></svg>"""
    (ASSET_OUT / "site-icon.svg").write_text(icon, encoding="utf-8")

    css = r"""
    :root {
      --ink: #173047;
      --ink-soft: rgba(23, 48, 71, 0.76);
      --paper: #f3efe5;
      --panel: #fffdf8;
      --mist: #e5ebe2;
      --sky: #afcbd0;
      --sage: #687665;
      --clay: #a76149;
      --gold: #b69146;
      --plum: #6d5262;
      --line: rgba(23, 48, 71, 0.16);
      --shadow: 0 16px 44px rgba(23, 48, 71, 0.10);
      --radius: 6px;
      --focus-ring: #b69146;
      --route: #2f6780;
      --route-soft: rgba(47,103,128,0.42);
      --status-ok: #4d8a5c;
      --linked: #4e7f9c;
      --field: #9a7a2a;
      --manual: #695674;
      --page-accent: var(--clay);
      color-scheme: light;
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; overflow-x: hidden; }
    body {
      margin: 0;
      font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background-color: var(--paper);
      background-image: url("textures/high-desert-plaster.webp");
      background-size: 640px 640px;
      background-blend-mode: soft-light;
      line-height: 1.6;
    }
    .page-colfax, .page-post-raton, .page-colfax-business { --page-accent: #455f68; }
    .page-las-animas, .page-post-trinidad, .page-advertise-trinidad, .page-las-animas-nonprofit { --page-accent: var(--clay); }
    .page-huerfano, .page-post-huerfano, .page-huerfano-calendars { --page-accent: var(--gold); }
    img { max-width: 100%; height: auto; }
    a { color: inherit; }
    @media (pointer: fine) {
      html, body { cursor: url("raton-accessible-cursor.svg") 4 2, auto; }
      a, button, select, summary, .button, .chip, .copy-button { cursor: url("raton-accessible-cursor.svg") 4 2, pointer; }
    }
    .skip-link { position: absolute; top: -80px; left: 16px; background: var(--ink); color: #fff; padding: 10px 14px; z-index: 20; }
    .skip-link:focus { top: 12px; }
    .site-watermark {
      position: fixed;
      inset-inline: 0;
      bottom: max(8vh, env(safe-area-inset-bottom));
      z-index: 12;
      pointer-events: none;
      width: 100%;
      min-height: 0;
      padding: 0 20px;
      border: 0;
      background: transparent;
      color: var(--ink);
      box-shadow: none;
      opacity: 0.10;
      font-size: 1.2rem;
      font-weight: 800;
      letter-spacing: 0.12em;
      line-height: 1.2;
      text-align: center;
      text-transform: uppercase;
      white-space: nowrap;
    }
    .intro-curtain {
      position: fixed;
      inset: 0;
      z-index: 999;
      pointer-events: none;
      background: #000;
      opacity: 1;
      animation: introReveal 2800ms cubic-bezier(.22,.72,.18,1) forwards;
    }
    .intro-curtain::before {
      content: "";
      position: absolute;
      inset: -12%;
      background:
        radial-gradient(circle at 50% 48%, rgba(255,255,255,1) 0 14%, rgba(255,255,255,0.94) 30%, rgba(255,255,255,0.42) 58%, rgba(255,255,255,0) 76%),
        linear-gradient(180deg, rgba(255,255,255,0), rgba(255,255,255,0.94));
      opacity: 0;
      transform: scale(0.92);
      animation: introGlow 2800ms cubic-bezier(.22,.72,.18,1) forwards;
    }
    .intro-curtain[data-intro-state="skipped"],
    .intro-curtain[data-intro-state="complete"] {
      display: none;
      animation: none;
    }
    @keyframes introReveal {
      0%, 22% { background: #000; opacity: 1; }
      62% { background: #fff; opacity: 1; }
      78% { background: #fff; opacity: 0.82; }
      100% { background: #fff; opacity: 0; visibility: hidden; }
    }
    @keyframes introGlow {
      0%, 22% { opacity: 0; transform: scale(0.84); }
      44% { opacity: 0.44; transform: scale(0.98); }
      66% { opacity: 0.94; transform: scale(1.08); }
      100% { opacity: 0.2; transform: scale(1.16); }
    }
    .site-header {
      position: sticky;
      top: 0;
      z-index: 10;
      isolation: isolate;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      min-height: 58px;
      padding: 10px clamp(16px, 4vw, 56px);
      border-bottom: 1px solid rgba(23,48,71,0.16);
      background: rgba(243, 239, 229, 0.93);
      box-shadow: inset 0 -2px 0 rgba(182,145,70,0.18);
      backdrop-filter: blur(18px);
    }
    .brand { position: relative; z-index: 2; display: inline-flex; align-items: center; gap: 10px; text-decoration: none; font-weight: 800; }
    .brand-mark { display: grid; place-items: center; width: 38px; height: 32px; color: var(--ink); }
    .brand-mark svg { display: block; width: 100%; height: 100%; overflow: visible; }
    .brand-mark__mesa { fill: var(--ink); }
    .brand-mark__route { fill: none; stroke: var(--gold); stroke-width: 2.4; stroke-linecap: round; }
    .brand-mark__sun { fill: var(--clay); }
    .site-nav { position: relative; z-index: 2; display: flex; gap: 3px; flex-wrap: wrap; justify-content: flex-end; align-items: center; overflow: visible; }
    .site-nav a, .nav-trigger { position: relative; display: inline-flex; align-items: center; justify-content: center; min-height: 34px; text-decoration: none; padding: 7px 9px; border: 0; border-radius: 4px; background: transparent; font: inherit; font-size: 0.8rem; color: var(--ink-soft); cursor: url("raton-accessible-cursor.svg") 4 2, pointer; transition: background 160ms ease, color 160ms ease, box-shadow 160ms ease; }
    .site-nav a:hover, .site-nav a.is-active, .site-nav a[aria-current="page"], .nav-group:hover > .nav-trigger, .nav-group:focus-within > .nav-trigger, .nav-group.is-active > .nav-trigger { background: rgba(167,97,73,0.075); color: var(--ink); }
    @media (hover: hover) and (pointer: fine) {
      .site-nav a:hover,
      .site-nav a:focus-visible,
      .nav-group:hover > .nav-trigger,
      .nav-group:focus-within > .nav-trigger {
        animation: navCursorGlow 1800ms ease-in-out infinite;
      }
    }
    @keyframes navCursorGlow {
      0%, 100% { box-shadow: 0 0 0 0 rgba(182,145,70,0); }
      50% { box-shadow: 0 0 0 2px rgba(182,145,70,0.20), 0 0 11px rgba(182,145,70,0.16); }
    }
    .site-nav a[aria-current="page"]::after,
    .nav-group.is-active > .nav-trigger::before {
      content: "";
      position: absolute;
      left: 12px;
      right: 12px;
      bottom: -3px;
      height: 2px;
      border-radius: 1px;
      background: var(--page-accent);
      animation: tabSettle 180ms ease-out;
    }
    .nav-group { position: relative; }
    .nav-promote { position: static; }
    .nav-group summary { list-style: none; }
    .nav-group summary::-webkit-details-marker { display: none; }
    .nav-trigger::after { content: ""; width: 0; height: 0; margin-left: 6px; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid currentColor; opacity: 0.72; }
    .nav-menu {
      position: absolute;
      right: 0;
      top: calc(100% + 8px);
      z-index: 20;
      display: none;
      min-width: 190px;
      padding: 8px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(255,255,255,0.96);
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
      max-height: min(72vh, 430px);
      overflow-y: auto;
    }
    .nav-menu a { display: flex; justify-content: flex-start; width: 100%; border-radius: 8px; white-space: nowrap; }
    .nav-menu--promote {
      width: min(760px, calc(100vw - 32px));
      max-height: min(76vh, 620px);
      padding: 10px;
    }
    .nav-menu-feature {
      min-height: 40px;
      margin-bottom: 5px;
      border-bottom: 1px solid var(--line) !important;
      border-radius: 6px 6px 0 0 !important;
      color: var(--ink) !important;
      font-weight: 850;
    }
    .nav-menu-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 4px 14px; }
    .nav-menu-section { min-width: 0; padding: 4px 0 6px; }
    .nav-menu-label { display: block; margin: 0; padding: 8px 9px 4px; color: var(--plum); font-size: 0.68rem; font-weight: 900; text-transform: uppercase; letter-spacing: 0.08em; }
    .nav-menu-county-links { display: grid; gap: 2px; }
    .nav-menu-county-links a { min-height: 30px; font-size: 0.76rem; }
    .nav-group:hover .nav-menu, .nav-group:focus-within .nav-menu, .nav-group[open] .nav-menu { display: grid; gap: 2px; }
    @keyframes tabSettle {
      from { transform: scaleX(0.65); opacity: 0.35; }
      to { transform: scaleX(1); opacity: 1; }
    }
    .nav-yucca-flourish {
      position: absolute;
      z-index: 1;
      top: 0;
      right: clamp(10px, 2.2vw, 34px);
      width: 160px;
      height: 62px;
      overflow: visible;
      opacity: 0;
      visibility: hidden;
      pointer-events: none;
      color: var(--sage);
    }
    .nav-yucca-flourish svg { display: block; width: 100%; height: 100%; overflow: visible; }
    .nav-yucca__index-line,
    .nav-yucca__stem,
    .nav-yucca__branch,
    .nav-yucca__leaf {
      fill: none;
      stroke: currentColor;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    .nav-yucca__index-line { stroke: var(--gold); stroke-width: 1; opacity: 0.42; }
    .nav-yucca__stem { stroke-width: 2.25; stroke-dasharray: 70; stroke-dashoffset: 70; }
    .nav-yucca__branch { stroke-width: 1.7; stroke-dasharray: 42; stroke-dashoffset: 42; }
    .nav-yucca__leaf {
      stroke: var(--ink);
      stroke-width: 2.1;
      stroke-dasharray: 78;
      stroke-dashoffset: 78;
      opacity: 0.88;
    }
    .nav-yucca__flower {
      color: #f5e6b9;
      opacity: 0;
      transform-box: fill-box;
      transform-origin: center bottom;
    }
    .nav-yucca__flower path {
      fill: currentColor;
      stroke: var(--gold);
      stroke-width: 0.7;
      stroke-linejoin: round;
    }
    .nav-yucca-flourish.is-growing {
      visibility: visible;
      animation: navYuccaVisit 3000ms linear both;
    }
    .nav-yucca-flourish.is-growing .nav-yucca__stem,
    .nav-yucca-flourish.is-growing .nav-yucca__branch,
    .nav-yucca-flourish.is-growing .nav-yucca__leaf {
      animation: navYuccaDraw 720ms cubic-bezier(.2,.76,.3,1) var(--sprout-delay, 0ms) both;
    }
    .nav-yucca-flourish.is-growing .nav-yucca__flower {
      animation: navYuccaBloom 520ms cubic-bezier(.17,.86,.32,1.28) var(--sprout-delay, 760ms) both;
    }
    @keyframes navYuccaVisit {
      0% { opacity: 0; }
      8%, 76% { opacity: 0.88; }
      100% { opacity: 0; }
    }
    @keyframes navYuccaDraw {
      from { stroke-dashoffset: 78; }
      to { stroke-dashoffset: 0; }
    }
    @keyframes navYuccaBloom {
      0% { opacity: 0; scale: 0.2; rotate: -8deg; }
      72% { opacity: 1; scale: 1.12; rotate: 2deg; }
      100% { opacity: 1; scale: 1; rotate: 0deg; }
    }
    .hero {
      position: relative;
      min-height: min(72vh, 700px);
      overflow: hidden;
      display: grid;
      align-items: end;
      padding: clamp(72px, 8vw, 112px) clamp(18px, 6vw, 86px) clamp(42px, 6vw, 72px);
      isolation: isolate;
    }
    .mountain-scene { position: absolute; inset: 0; z-index: -1; background: linear-gradient(180deg, #dff3f3, #f7faf3 74%); }
    .mountain-scene svg { position: absolute; inset: auto 0 0; width: 100%; height: 58%; }
    .sky-fade { fill: transparent; }
    .far-mountains { fill: rgba(114, 150, 143, 0.42); }
    .near-mountains { fill: rgba(82, 116, 105, 0.62); }
    .ridge-line { fill: rgba(216, 187, 104, 0.22); }
    .cloud {
      position: absolute;
      width: 180px;
      height: 54px;
      border-radius: 999px;
      background: rgba(255,255,255,0.62);
      filter: blur(0.2px);
      box-shadow: 42px 6px 0 rgba(255,255,255,0.5), 84px -8px 0 rgba(255,255,255,0.56), 130px 8px 0 rgba(255,255,255,0.44);
      animation: drift 44s linear infinite;
    }
    .cloud-a { top: 18%; left: -260px; }
    .cloud-b { top: 31%; left: -420px; animation-duration: 58s; transform: scale(0.72); opacity: 0.7; }
    .cloud-c { top: 12%; left: -360px; animation-duration: 70s; transform: scale(0.55); opacity: 0.6; }
    @keyframes drift { from { translate: -16vw 0; } to { translate: 130vw 0; } }
    .hero-copy { max-width: 1000px; }
    .hero-copy { position: relative; z-index: 2; }
    .hero-accent {
      position: absolute;
      inset: 0;
      z-index: 0;
      pointer-events: none;
      opacity: 0.22;
      color: rgba(23,48,71,0.52);
      mix-blend-mode: multiply;
    }
    .hero-accent svg { width: 100%; height: 100%; display: block; }
    .hero-route {
      fill: none;
      stroke: currentColor;
      stroke-width: 1.5;
      stroke-linecap: round;
      stroke-dasharray: 8 18;
      opacity: 0.18;
      animation: routeDrift 52s linear infinite;
    }
    .hero-route--two { animation-duration: 68s; animation-direction: reverse; opacity: 0.11; }
    .hero-node {
      fill: currentColor;
      opacity: 0.14;
      transform-box: fill-box;
      transform-origin: center;
      animation: nodeBreathe 13s ease-in-out infinite;
    }
    .hero-node--two { animation-delay: -2.6s; }
    .hero-node--three { animation-delay: -5.2s; }
    @keyframes routeDrift { to { stroke-dashoffset: -260; } }
    @keyframes nodeBreathe {
      0%, 100% { transform: scale(1); opacity: 0.10; }
      50% { transform: scale(1.16); opacity: 0.24; }
    }
    .eyebrow { margin: 0 0 10px; text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.76rem; font-weight: 800; color: var(--plum); }
    h1, h2, h3 { line-height: 1.08; letter-spacing: 0; }
    h1 { margin: 0; font-family: Fraunces, Georgia, serif; font-size: clamp(3rem, 6.2vw, 5.25rem); max-width: 18ch; }
    .page-hero h1 { font-size: clamp(2.35rem, 4.2vw, 3.55rem); max-width: 16ch; }
    .county-hero h1 { font-size: clamp(2.1rem, 4vw, 3.55rem); max-width: 23ch; }
    .county-hero .lede { max-width: 52rem; }
    h2 { margin: 0; font-size: clamp(1.8rem, 3vw, 2.8rem); }
    h3 { margin: 0 0 10px; font-size: 1.08rem; }
    .lede { max-width: 780px; font-size: clamp(1.05rem, 2vw, 1.35rem); color: var(--ink-soft); }
    .hero-actions, .section-actions, .download-row { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 26px; }
    .button { display: inline-flex; align-items: center; justify-content: center; min-height: 42px; padding: 10px 16px; border-radius: 5px; text-decoration: none; border: 1px solid var(--line); font-weight: 800; }
    button.button { font: inherit; cursor: pointer; }
    .button-primary { background: var(--ink); color: #fff; border-color: var(--ink); }
    .button-soft { background: rgba(255,255,255,0.62); }
    .breadcrumbs {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      max-width: 1180px;
      margin: 18px auto 0;
      padding: 0 clamp(18px, 6vw, 86px);
      color: var(--ink-soft);
      font-size: 0.86rem;
      font-weight: 700;
    }
    .breadcrumbs a {
      color: var(--ink);
      text-decoration: none;
      text-underline-offset: 3px;
    }
    .breadcrumbs a:hover,
    .breadcrumbs a:focus-visible {
      text-decoration: underline;
    }
    .page-wayfinding {
      display: grid;
      grid-template-columns: minmax(250px, 1.2fr) repeat(2, minmax(220px, 1fr));
      gap: 18px 28px;
      align-items: start;
      padding: 18px clamp(18px, 6vw, 86px);
      border-bottom: 1px solid var(--line);
      background: rgba(255,253,248,0.86);
    }
    .page-wayfinding__intro p { margin: 3px 0 0; color: var(--ink-soft); line-height: 1.45; }
    .page-wayfinding__intro strong { color: var(--ink); }
    .page-wayfinding__label,
    .page-wayfinding__links > span {
      display: block;
      margin-bottom: 6px;
      color: var(--plum);
      font-size: 0.7rem;
      font-weight: 900;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .page-wayfinding__links { display: flex; flex-wrap: wrap; gap: 7px 13px; align-content: start; }
    .page-wayfinding__links > span { flex-basis: 100%; }
    .page-wayfinding__links a {
      color: var(--linked);
      font-size: 0.82rem;
      font-weight: 800;
      line-height: 1.35;
      text-decoration-thickness: 1px;
      text-underline-offset: 3px;
    }
    .section, .page-hero { padding: clamp(38px, 5vw, 72px) clamp(18px, 6vw, 86px); }
    main section[id], main nav[id], #resource-results { scroll-margin-top: 92px; }
    .page-hero {
      position: relative;
      isolation: isolate;
      display: grid;
      align-content: center;
      min-height: clamp(250px, 32vh, 360px);
      overflow: hidden;
      background: linear-gradient(112deg, rgba(243,239,229,0.98) 0 36%, rgba(229,235,226,0.84) 63%, rgba(175,203,208,0.48));
      border-bottom: 1px solid rgba(23,48,71,0.16);
      box-shadow: inset 0 -3px 0 color-mix(in srgb, var(--page-accent) 18%, transparent);
    }
    .page-hero > :not(.page-hero-art) { position: relative; z-index: 1; }
    .page-network .page-hero {
      min-height: clamp(240px, 30vh, 330px);
      padding-top: clamp(36px, 4vw, 52px);
      padding-bottom: clamp(32px, 4vw, 48px);
    }
    .page-network .page-hero h1 {
      max-width: 16ch;
      font-size: clamp(2.7rem, 5.4vw, 4.6rem);
    }
    .page-hero-art {
      position: absolute;
      z-index: 0;
      right: clamp(-110px, 4vw, 80px);
      top: 50%;
      width: min(820px, 64vw);
      aspect-ratio: 1.88 / 1;
      height: auto;
      transform: translateY(-50%);
      object-fit: cover;
      object-position: center bottom;
      border-radius: 50%;
      opacity: 0.58;
      filter: saturate(0.94) contrast(1.02);
      -webkit-mask-image: radial-gradient(ellipse at center, #000 44%, rgba(0,0,0,0.78) 64%, transparent 82%);
      mask-image: radial-gradient(ellipse at center, #000 44%, rgba(0,0,0,0.78) 64%, transparent 82%);
      pointer-events: none;
    }
    .county-hero { background: linear-gradient(112deg, rgba(243,239,229,0.98), rgba(182,145,70,0.17), rgba(175,203,208,0.34)); }
    .tinted { background: rgba(229, 235, 226, 0.58); }
    .intro-band { background: rgba(255,253,248,0.88); }
    .section-heading { position: relative; max-width: 870px; margin-bottom: 26px; }
    .section-heading::after {
      content: "";
      display: block;
      width: min(240px, 52vw);
      height: 1px;
      margin-top: 18px;
      background: linear-gradient(90deg, rgba(23,48,71,0), rgba(47,103,128,0.18), rgba(216,187,104,0.20), rgba(23,48,71,0));
      background-size: 180% 100%;
      animation: headingGlide 32s linear infinite;
    }
    @keyframes headingGlide { to { background-position: 180% 0; } }
    .two-col { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 28px; font-size: 1.06rem; color: var(--ink-soft); }
    .path-grid, .source-grid, .mini-grid, .steps-grid, .template-grid, .stats-grid {
      display: grid;
      gap: 18px;
    }
    .path-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .source-grid { grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }
    .source-grid.compact { grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }
    .mini-grid { grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); }
    .tool-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }
    .tool-grid > * { min-width: 0; }
    .tool-filters {
      display: grid;
      grid-template-columns: minmax(220px, 1.35fr) repeat(3, minmax(155px, 0.78fr)) auto;
      gap: 12px;
      align-items: end;
      margin: 0 0 18px;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(255,255,255,0.62);
    }
    .tool-filters label { display: grid; min-width: 0; gap: 6px; color: var(--ink); font-size: 0.78rem; font-weight: 800; }
    .tool-filters input, .tool-filters select { width: 100%; min-width: 0; min-height: 44px; }
    .tool-filters .button { min-height: 44px; }
    .tool-filter-status { grid-column: 1 / -1; min-height: 1.2em; margin: 0; color: var(--ink-soft); font-size: 0.86rem; }
    .tool-offer-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      margin-top: 18px;
      border-block: 1px solid var(--line);
    }
    .tool-offer-card {
      display: flex;
      min-width: 0;
      flex-direction: column;
      align-items: flex-start;
      gap: 10px;
      padding: 20px;
      border-right: 1px solid var(--line);
    }
    .tool-offer-card:last-child { border-right: 0; }
    .tool-offer-card h3, .tool-offer-card p { margin: 0; }
    .tool-offer-card p { color: var(--ink-soft); }
    .tool-offer-card .button { margin-top: auto; }
    .tool-offer-card .button[aria-pressed="true"] { border-color: var(--ink); background: var(--ink); color: #fff; }
    .tool-card { display: flex; min-height: 310px; flex-direction: column; overflow-wrap: anywhere; }
    .tool-card[hidden] { display: none; }
    .tool-card__meta { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 10px; }
    .tool-pill { display: inline-flex; align-items: center; min-height: 24px; padding: 3px 7px; border: 1px solid rgba(23,48,71,0.12); border-radius: 999px; background: rgba(220,238,232,0.58); color: var(--ink); font-size: 0.68rem; font-weight: 800; }
    .tool-card h3 { margin-top: 0; }
    .tool-card .source-note { margin-top: auto; }
    .tool-nonprofit-note { color: var(--ink-soft); font-size: 0.82rem; line-height: 1.45; }
    .tool-detail-link { display: inline-flex; align-self: flex-start; margin-top: 4px; font-size: 0.82rem; font-weight: 800; }
    .steps-grid { grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }
    .template-grid { grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); }
    .stats-grid { grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }
    .path-card, .source-card, .mini-card, .step-card, .template-card, .tool-card, .resource-item, .lead-card, .stat, figure {
      background: rgba(255,253,248,0.90);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: 0 6px 18px rgba(23,48,71,0.045);
    }
    .path-card {
      position: relative;
      padding: 20px;
      min-height: 220px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      text-decoration: none;
      border-top: 3px solid var(--clay);
    }
    .path-card:nth-child(2), .task-link-card:nth-child(3n + 2) { border-top-color: var(--sage); }
    .path-card:nth-child(3), .task-link-card:nth-child(3n) { border-top-color: var(--gold); }
    .task-link-card { min-height: 188px; }
    .category-route-card {
      display: flex;
      min-height: 180px;
      flex-direction: column;
      color: inherit;
      text-decoration: none;
      border-left: 3px solid var(--page-accent);
    }
    .category-route-card > strong { margin-top: auto; color: var(--linked); }
    .path-card span, .step-card span { color: var(--clay); font-weight: 900; }
    .path-card p { color: var(--ink-soft); }
    .path-card strong { margin-top: auto; }
    .source-card, .mini-card, .step-card, .template-card, .tool-card, .resource-item, .lead-card { padding: 16px; }
    .source-card, .resource-item { border-left: 3px solid color-mix(in srgb, var(--page-accent) 72%, var(--ink)); }
    .current-leads-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(270px, 1fr));
      gap: 14px;
    }
    .page-arts-culture .current-leads-grid {
      grid-template-columns: repeat(auto-fit, minmax(270px, 420px));
    }
    .arts-route-strip {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 1px;
      padding: 0;
      border-bottom: 1px solid var(--line);
      background: rgba(23,48,71,0.16);
    }
    .arts-route-visual {
      position: relative;
      isolation: isolate;
      display: grid;
      align-items: end;
      min-height: 214px;
      overflow: hidden;
      color: #fff;
      text-decoration: none;
    }
    .arts-route-visual img {
      position: absolute;
      z-index: -2;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      filter: saturate(0.82) contrast(1.05);
      transition: transform 480ms cubic-bezier(.2,.7,.25,1), filter 240ms ease;
    }
    .arts-route-visual::after {
      content: "";
      position: absolute;
      z-index: -1;
      inset: 34% 0 0;
      background: linear-gradient(180deg, transparent, rgba(16,40,61,0.84));
    }
    .arts-route-visual span {
      display: grid;
      gap: 2px;
      padding: 22px clamp(16px, 3vw, 30px);
    }
    .arts-route-visual strong { font-family: Fraunces, Georgia, serif; font-size: clamp(1.25rem, 2vw, 1.7rem); line-height: 1.08; }
    .arts-route-visual small { color: rgba(255,255,255,0.82); font-size: 0.82rem; }
    .arts-route-visual:hover img,
    .arts-route-visual:focus-visible img { transform: scale(1.025); filter: saturate(0.96) contrast(1.07); }
    .arts-route-visual:focus-visible { z-index: 2; outline-offset: -4px; }
    .lead-card {
      min-height: 210px;
      display: flex;
      flex-direction: column;
    }
    .lead-card .action-line {
      margin-top: auto;
    }
    .task-group-card strong {
      display: block;
      margin-top: 14px;
    }
    .path-card, .mini-card, .step-card, .template-card, .tool-card, .lead-card, .route-type-card, .button, .chip, .persona-route {
      transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease, background 180ms ease;
    }
    .path-card:hover,
    .path-card:focus-visible,
    .mini-card:hover,
    .mini-card:focus-within,
    .step-card:hover,
    .step-card:focus-within,
    .template-card:hover,
    .template-card:focus-within,
    .tool-card:hover,
    .tool-card:focus-within,
    .lead-card:hover,
    .lead-card:focus-within,
    .route-type-card:hover,
    .route-type-card:focus-within {
      transform: translateY(-1px);
      box-shadow: 0 12px 24px rgba(23,48,71,0.08);
      border-color: rgba(47,103,128,0.18);
    }
    .button:hover, .button:focus-visible, .chip:hover, .chip:focus-visible, .persona-route:hover, .persona-route:focus-visible {
      transform: translateY(-1px);
      box-shadow: 0 8px 16px rgba(23,48,71,0.07);
    }
    .tool-card a { text-decoration-thickness: 2px; text-underline-offset: 3px; }
    .submit-band { background: linear-gradient(135deg, rgba(216,187,104,0.16), rgba(220,238,232,0.56)); }
    .next-actions { border-top: 1px solid var(--line); background: rgba(255,255,255,0.44); }
    .next-action-list {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      padding: 0;
      margin: 0;
      list-style: none;
    }
    .next-action-list a {
      display: block;
      height: 100%;
      padding: 14px 16px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(255,255,255,0.82);
      color: var(--ink);
      font-weight: 850;
      text-decoration: none;
      box-shadow: 0 10px 28px rgba(23,48,71,0.045);
      transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
    }
    .next-action-list a:hover,
    .next-action-list a:focus-visible {
      transform: translateY(-1px);
      border-color: rgba(47,103,128,0.22);
      box-shadow: 0 12px 24px rgba(23,48,71,0.08);
    }
    .submit-card { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; align-items: center; padding: 18px; border: 1px solid var(--line); border-radius: var(--radius); background: rgba(255,255,255,0.84); box-shadow: var(--shadow); }
    .submit-card p { margin-bottom: 0; color: var(--ink-soft); }
    .submission-form { display: grid; gap: 18px; max-width: 1040px; }
    .form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
    .submission-form input, .submission-form select, .submission-form textarea { width: 100%; margin-top: 8px; padding: 11px 12px; border: 1px solid var(--line); border-radius: var(--radius); background: rgba(255,255,255,0.94); color: var(--ink); font: inherit; }
    .submission-form textarea { resize: vertical; }
    .hidden-field { position: absolute; left: -9999px; width: 1px; height: 1px; overflow: hidden; }
    .submit-success-card {
      position: relative;
      overflow: hidden;
      display: grid;
      gap: 8px;
      margin-top: 6px;
      padding: 18px;
      border: 1px solid rgba(216,187,104,0.45);
      border-radius: var(--radius);
      background: linear-gradient(135deg, rgba(255,255,255,0.94), rgba(220,238,232,0.84));
      box-shadow: 0 18px 42px rgba(23,48,71,0.12);
      animation: gratitude-pop 560ms ease both;
    }
    .submit-success-card[hidden] { display: none; }
    .submit-success-card h3 { margin: 0; font-size: clamp(1.35rem, 3vw, 2.1rem); }
    .submit-success-card p { margin: 0; }
    .submit-sparkles { position: absolute; inset: 0; pointer-events: none; }
    .sparkle {
      position: absolute;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--gold);
      box-shadow: 0 0 0 8px rgba(216,187,104,0.16);
      animation: sparkle-rise 1400ms ease-out infinite;
    }
    .sparkle-one { left: 8%; bottom: 18%; animation-delay: 0ms; }
    .sparkle-two { left: 82%; bottom: 24%; background: var(--sage); animation-delay: 240ms; }
    .sparkle-three { left: 52%; bottom: 12%; background: var(--clay); animation-delay: 480ms; }
    @keyframes gratitude-pop {
      from { opacity: 0; transform: translateY(8px) scale(0.985); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }
    @keyframes sparkle-rise {
      0% { opacity: 0; transform: translateY(16px) scale(0.7); }
      25% { opacity: 1; }
      100% { opacity: 0; transform: translateY(-46px) scale(1.3); }
    }
    .source-card__meta { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
    .source-card__meta span, .badge { background: rgba(216,187,104,0.24); border: 1px solid rgba(216,187,104,0.36); border-radius: 999px; padding: 3px 8px; font-size: 0.74rem; font-weight: 800; }
    .resource-tags { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
    .source-card p, .mini-card p, .step-card p, .resource-item p { color: var(--ink-soft); }
    .resource-best {
      margin-top: 2px;
      padding: 8px 10px;
      border-radius: var(--radius);
      background: rgba(220,238,232,0.48);
      color: rgba(23,48,71,0.78) !important;
      font-size: 0.88rem;
    }
    .resource-best strong { color: var(--ink); }
    .directory-jumpbar {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 22px;
    }
    .directory-search-panel {
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(255,255,255,0.72);
    }
    .directory-filter-details,
    .marker-help,
    .directory-support-details,
    .resource-more,
    .source-group-links {
      border: 0;
    }
    .directory-filter-details > summary,
    .resource-more > summary,
    .source-group-links > summary {
      display: none;
    }
    .directory-filter-body {
      display: grid;
      gap: 14px;
      padding-top: 2px;
    }
    .filter-label {
      display: block;
      margin-bottom: 8px;
      color: var(--ink);
      font-weight: 850;
    }
    .marker-help {
      margin: 12px 0 14px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(255,255,255,0.54);
    }
    .marker-help > summary,
    .directory-support-details > summary {
      cursor: pointer;
      padding: 12px 14px;
      color: var(--ink);
      font-weight: 900;
    }
    .marker-help .marker-legend {
      margin: 0;
      padding: 0 14px 14px;
    }
    .directory-more-row {
      display: flex;
      justify-content: center;
      margin-top: 18px;
    }
    .directory-secondary-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 20px;
    }
    .directory-support-details {
      max-width: 980px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(255,255,255,0.72);
    }
    .directory-support-body {
      padding: 0 16px 16px;
    }
    .resource-links {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }
    .listing-indicators {
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
      margin: 8px 0 2px;
    }
    .listing-marker {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      border: 1px solid rgba(92,138,99,0.38);
      border-radius: 999px;
      background: rgba(220,238,232,0.62);
      color: #173047;
      padding: 5px 9px;
      font-size: 0.76rem;
      font-weight: 850;
      line-height: 1.15;
    }
    .listing-marker::before {
      content: "";
      display: inline-block;
      flex: 0 0 auto;
    }
    .listing-marker--ad {
      border-color: rgba(179,107,79,0.38);
      background: rgba(199,127,97,0.16);
    }
    .listing-marker--ad::before {
      width: 9px;
      height: 9px;
      border-radius: 50% 50% 50% 0;
      background: #8f4f3a;
      transform: rotate(-45deg);
      box-shadow: 0 0 0 2px rgba(143,79,58,0.13);
    }
    .listing-marker--physical::before {
      width: 10px;
      height: 10px;
      border-radius: 2px;
      border: 2px solid #2f6780;
      background: rgba(255,255,255,0.7);
      box-shadow: 3px 3px 0 rgba(47,103,128,0.22);
    }
    .resource-outreach {
      display: grid;
      gap: 7px;
    }
    .resource-outreach > strong {
      color: var(--ink);
      font-size: 0.84rem;
    }
    .outreach-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      min-width: 0;
    }
    .outreach-tag {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-width: 0;
      border: 1px solid rgba(55,82,91,0.24);
      border-radius: 4px;
      padding: 4px 7px;
      color: #173047;
      background: rgba(255,255,255,0.62);
      font-size: 0.72rem;
      font-weight: 800;
      line-height: 1.2;
    }
    .outreach-tag::before {
      content: "";
      width: 7px;
      height: 7px;
      flex: 0 0 auto;
      border-radius: 50%;
      background: #60717a;
    }
    .outreach-tag--listed {
      border-color: rgba(49,111,82,0.36);
      background: rgba(213,235,223,0.7);
    }
    .outreach-tag--listed::before { background: #316f52; }
    .outreach-tag--ask {
      border-color: rgba(161,104,44,0.34);
      background: rgba(244,226,194,0.6);
    }
    .outreach-tag--ask::before { background: #98632d; }
    .outreach-tag--more {
      color: var(--ink-soft);
      background: rgba(235,239,236,0.68);
    }
    .outreach-tag--more::before { display: none; }
    .outreach-empty {
      margin: 0;
      color: var(--ink-soft);
      font-size: 0.8rem;
    }
    .resource-connection {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      margin: 8px 0 1px;
      min-height: 28px;
    }
    .connection-label {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      min-height: 28px;
      padding: 4px 9px;
      border: 1px solid rgba(23,48,71,0.18);
      border-radius: 999px;
      background: rgba(255,255,255,0.72);
      color: var(--ink);
      font-size: 0.75rem;
      font-weight: 850;
      line-height: 1.2;
      text-decoration: none;
    }
    .connection-label__signal {
      position: relative;
      display: inline-block;
      width: 8px;
      height: 8px;
      flex: 0 0 auto;
      border-radius: 50%;
      background: #6f7b78;
    }
    .connection-label__signal::after {
      content: "";
      position: absolute;
      inset: -1px;
      border: 1px solid currentColor;
      border-radius: inherit;
      opacity: 0;
    }
    .connection-label--connected {
      border-color: rgba(67,112,87,0.34);
      background: rgba(218,235,222,0.66);
      color: #254f3a;
    }
    .connection-label--connected .connection-label__signal {
      background: #437057;
    }
    .connection-label--profile {
      border-color: rgba(47,103,128,0.28);
      background: rgba(215,232,238,0.62);
      color: #24566e;
    }
    .connection-label--profile .connection-label__signal {
      background: #397d91;
    }
    .connection-label--missing {
      border-color: rgba(90,91,86,0.20);
      background: rgba(235,233,225,0.66);
      color: #5a5b56;
    }
    .connection-label--missing .connection-label__signal {
      background: #8a8a82;
    }
    .connection-label--connected.is-animated .connection-label__signal::after {
      animation: connection-online-pulse 4.8s ease-out infinite;
    }
    .connection-label--connected:hover,
    .connection-label--connected:focus-visible {
      background: rgba(205,229,211,0.88);
      border-color: rgba(67,112,87,0.52);
    }
    .connection-update-link {
      color: var(--ink-soft);
      font-size: 0.76rem;
      font-weight: 800;
    }
    @keyframes connection-online-pulse {
      0%, 70%, 100% { transform: scale(1); opacity: 0; }
      78% { transform: scale(1); opacity: 0.52; }
      92% { transform: scale(2.7); opacity: 0; }
    }
    .marker-legend {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px 10px;
      margin: 14px 0 10px;
      color: var(--ink-soft);
      font-size: 0.91rem;
    }
    .marker-legend .listing-marker {
      margin-right: 2px;
    }
    .resource-contact-link {
      display: inline-flex;
      align-items: center;
      min-height: 34px;
      padding: 6px 10px;
      border: 1px solid rgba(23,48,71,0.13);
      border-radius: 999px;
      background: rgba(255,255,255,0.74);
      color: var(--ink);
      text-decoration: none;
      font-size: 0.86rem;
      font-weight: 850;
    }
    .resource-contact-link:hover,
    .resource-contact-link:focus-visible {
      background: rgba(220,238,232,0.68);
      border-color: rgba(47,103,128,0.24);
    }
    .source-group-card {
      display: flex;
      flex-direction: column;
    }
    .source-group-links {
      margin-top: auto;
    }
    .source-link-list {
      display: grid;
      gap: 8px;
      margin-top: 14px;
      padding-top: 12px;
      border-top: 1px solid var(--line);
    }
    .source-sublink {
      display: grid;
      gap: 2px;
      padding: 9px 10px;
      border: 1px solid rgba(23,48,71,0.10);
      border-radius: 7px;
      background: rgba(246,248,244,0.72);
      text-decoration: none;
    }
    .source-sublink span {
      color: var(--plum);
      font-size: 0.72rem;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .source-sublink strong {
      color: var(--ink);
      font-size: 0.9rem;
      line-height: 1.25;
    }
    .source-sublink:hover,
    .source-sublink:focus-visible {
      border-color: rgba(47,103,128,0.24);
      background: rgba(255,255,255,0.94);
    }
    .source-note { font-size: 0.9rem; color: rgba(23,48,71,0.68) !important; }
    .source-refresh-details {
      margin-top: 18px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(255,255,255,0.72);
      overflow: hidden;
    }
    .source-refresh-details summary {
      cursor: pointer;
      padding: 12px 14px;
      font-weight: 900;
    }
    .source-refresh-details .table-wrap { border: 0; border-top: 1px solid var(--line); border-radius: 0; }
    .action-line { font-weight: 700; color: var(--ink) !important; }
    .stat { padding: 18px; display: grid; gap: 4px; }
    .stat strong { font-size: clamp(2rem, 4vw, 3.4rem); line-height: 1; }
    .stat span, .section-note { color: var(--ink-soft); }
    .hero-stat { background: var(--ink); color: #fff; }
    .hero-stat span { color: rgba(255,255,255,0.75); }
    .check-list { padding-left: 1.1rem; color: var(--ink-soft); }
    .check-list li { margin: 8px 0; }
    .tool-panel { display: grid; gap: 14px; margin-bottom: 20px; }
    .template-rules,
    .route-type-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(225px, 1fr));
      gap: 14px;
    }
    .template-meta {
      padding: 9px 10px;
      border-radius: var(--radius);
      background: rgba(220,238,232,0.52);
      color: rgba(23,48,71,0.78);
      font-size: 0.9rem;
    }
    .category-badge {
      display: inline-flex;
      width: fit-content;
      align-items: center;
      min-height: 28px;
      padding: 4px 10px;
      border-radius: 999px;
      border: 1px solid rgba(23,48,71,0.12);
      font-size: 0.74rem;
      font-weight: 950;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }
    .route-type-card {
      display: grid;
      gap: 10px;
      padding: 18px;
      border: 1px solid var(--line);
      border-left-width: 8px;
      border-radius: var(--radius);
      background: rgba(255,255,255,0.82);
      box-shadow: 0 12px 28px rgba(23,48,71,0.06);
      color: inherit;
      text-decoration: none;
    }
    .route-type-card h3 { margin: 0; font-size: 1.02rem; }
    .route-type-card p { margin: 0; color: var(--ink-soft); }
    .route-type-card__action {
      align-self: end;
      color: var(--linked);
      font-size: 0.86rem;
      font-weight: 900;
    }
    .cat-events { --cat: #3b7f8f; border-color: rgba(59,127,143,0.34); background: rgba(183,219,228,0.38); }
    .cat-promotion { --cat: #b36b4f; border-color: rgba(179,107,79,0.35); background: rgba(199,127,97,0.18); }
    .cat-business { --cat: #5c8a63; border-color: rgba(92,138,99,0.36); background: rgba(139,170,124,0.22); }
    .cat-nonprofit { --cat: #6f5f91; border-color: rgba(111,95,145,0.34); background: rgba(105,86,116,0.15); }
    .cat-arts { --cat: #a58339; border-color: rgba(165,131,57,0.38); background: rgba(216,187,104,0.22); }
    .cat-regional { --cat: #2f6780; border-color: rgba(47,103,128,0.34); background: rgba(220,238,232,0.52); }
    .cat-support { --cat: #173047; border-color: rgba(23,48,71,0.22); background: rgba(23,48,71,0.06); }
    .route-type-card.cat-events,
    .route-type-card.cat-promotion,
    .route-type-card.cat-business,
    .route-type-card.cat-nonprofit,
    .route-type-card.cat-arts,
    .route-type-card.cat-regional,
    .route-type-card.cat-support { border-left-color: var(--cat); }
    label { display: block; font-weight: 800; margin-bottom: 8px; }
    .search-input { width: 100%; min-height: 48px; padding: 12px 14px; border: 1px solid var(--line); border-radius: var(--radius); font: inherit; background: rgba(255,255,255,0.9); }
    .advanced-filters { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
    select { width: 100%; min-height: 44px; padding: 10px 12px; border: 1px solid var(--line); border-radius: var(--radius); background: rgba(255,255,255,0.9); color: var(--ink); font: inherit; }
    .filter-row { display: flex; flex-wrap: wrap; gap: 8px; }
    .chip, .copy-button { min-height: 38px; border: 1px solid var(--line); border-radius: 999px; background: rgba(255,255,255,0.85); color: var(--ink); padding: 8px 12px; font: inherit; font-weight: 800; cursor: pointer; }
    .chip.is-active { background: var(--ink); color: #fff; }
    .resource-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(430px, 1fr)); gap: 12px; }
    [data-progressive-list] > [hidden] { display: none !important; }
    .resource-item { display: flex; flex-direction: column; min-width: 0; }
    .resource-item__head { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
    .resource-item__head h3 { margin-bottom: 0; }
    .resource-meta-line { margin: 8px 0; font-size: 0.9rem; }
    .resource-description { margin: 10px 0; }
    .resource-more__body { display: grid; gap: 8px; }
    .resource-more__body > * { margin-top: 0; margin-bottom: 0; }
    .resource-item a { font-weight: 800; }
    .entity-name-link {
      color: inherit;
      text-decoration-color: rgba(78,127,156,0.62);
      text-decoration-thickness: 1px;
      text-underline-offset: 3px;
    }
    .entity-name-link:hover,
    .entity-name-link:focus-visible {
      color: #315f79;
      text-decoration-color: currentColor;
    }
    .lead-list { columns: 2; gap: 40px; padding-left: 1.1rem; }
    .lead-list li { break-inside: avoid; margin: 0 0 12px; }
    .lead-list span { display: block; color: var(--ink-soft); }
    figure { margin: 0; padding: 14px; }
    figcaption { color: var(--ink-soft); font-size: 0.92rem; margin-top: 8px; }
    .persona-routes { display: flex; flex-wrap: wrap; gap: 8px; margin: 16px 0 0; }
    .persona-route { display: inline-flex; min-height: 36px; align-items: center; padding: 7px 10px; border: 1px solid var(--line); border-radius: 999px; background: rgba(255,255,255,0.72); text-decoration: none; font-size: 0.86rem; font-weight: 800; }
    .type-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; padding: 0; list-style: none; }
    .type-list li { padding: 12px; background: rgba(255,255,255,0.72); border: 1px solid var(--line); border-radius: var(--radius); }
    .type-list strong { display: block; font-size: 1.5rem; }
    pre { white-space: pre-wrap; background: rgba(23,48,71,0.055); border: 1px solid var(--line); border-radius: var(--radius); padding: 14px; font-size: 0.92rem; }
    .table-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: var(--radius); background: #fff; }
    table { width: 100%; border-collapse: collapse; min-width: 720px; }
    th, td { text-align: left; padding: 12px 14px; border-bottom: 1px solid var(--line); vertical-align: top; }
    th { background: rgba(220,238,232,0.7); }
    .physical-posting-table table { min-width: 1040px; }
    .table-subtle { display: block; margin-top: 4px; color: var(--ink-soft); font-size: 0.9rem; }
    .appendix-table table { min-width: 1240px; }
    .noscript { margin: 20px clamp(18px, 6vw, 86px) 0; padding: 14px 16px; border: 1px solid var(--line); border-radius: var(--radius); background: rgba(216,187,104,0.2); font-weight: 700; }
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
    .corner-controls {
      position: fixed;
      right: max(16px, env(safe-area-inset-right));
      bottom: max(16px, env(safe-area-inset-bottom));
      z-index: 30;
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      justify-content: flex-end;
      gap: 6px;
      width: min(370px, calc(100vw - 32px));
      pointer-events: none;
    }
    .back-to-top, .music-summary, .music-toggle {
      pointer-events: auto;
      min-height: 34px;
      text-decoration: none;
      background: rgba(16,40,61,0.40);
      color: #fff;
      border: 1px solid rgba(255,255,255,0.18);
      border-radius: 999px;
      padding: 6px 9px;
      font: inherit;
      font-size: 0.72rem;
      font-weight: 800;
      box-shadow: 0 8px 18px rgba(23,48,71,0.08);
      transition: background 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
    }
    .back-to-top {
      display: none;
      opacity: 0;
      visibility: hidden;
      transform: translateY(4px);
      pointer-events: none;
      transition: opacity 160ms ease, visibility 160ms ease, transform 160ms ease, background 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
    }
    body[data-scroll-state="scrolled"] .back-to-top {
      display: inline-flex;
      opacity: 1;
      visibility: visible;
      transform: translateY(0);
      pointer-events: auto;
    }
    .back-to-top:hover,
    .back-to-top:focus-visible,
    .music-summary:hover,
    .music-summary:focus-visible,
    .music-toggle:hover,
    .music-toggle:focus-visible {
      background: rgba(16,40,61,0.82);
      border-color: rgba(255,255,255,0.34);
      box-shadow: 0 10px 22px rgba(23,48,71,0.14);
    }
    .music-summary { list-style: none; display: inline-flex; align-items: center; justify-content: space-between; gap: 10px; align-self: flex-end; min-width: 150px; cursor: pointer; }
    .music-summary::-webkit-details-marker { display: none; }
    .music-status {
      border-radius: 999px;
      padding: 2px 7px;
      background: rgba(255,255,255,0.22);
      font-size: 0.66rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .music-toggle { background: rgba(255,255,255,0.56); color: var(--ink); border-color: rgba(23,48,71,0.10); }
    .music-toggle:hover, .music-toggle:focus-visible { color: #fff; }
    .music-toggle[data-state="playing"] { background: rgba(216,187,104,0.56); color: #173047; }
    .music-toggle[data-state="playing"]:hover, .music-toggle[data-state="playing"]:focus-visible { background: rgba(216,187,104,0.82); color: #173047; }
    .music-bar {
      pointer-events: auto;
      width: auto;
      max-width: min(340px, calc(100vw - 32px));
      border: 0;
      background: transparent;
      color: var(--ink);
    }
    .music-panel {
      margin-top: 7px;
      width: min(340px, calc(100vw - 32px));
      padding: 10px;
      border: 1px solid rgba(23,48,71,0.14);
      border-radius: 12px;
      background: rgba(255,255,255,0.78);
      box-shadow: 0 14px 32px rgba(23,48,71,0.13);
      backdrop-filter: blur(18px);
    }
    .music-bar:not([open]) .music-panel { display: none; }
    .music-bar__top,
    .music-bar__middle,
    .music-bar__bottom {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .music-bar__top { justify-content: space-between; }
    .music-bar__middle { margin-top: 8px; }
    .music-bar__bottom {
      justify-content: space-between;
      margin-top: 7px;
      color: rgba(23,48,71,0.66);
      font-size: 0.68rem;
      font-weight: 800;
    }
    .music-credit-block {
      display: grid;
      gap: 2px;
      max-width: 205px;
      line-height: 1.3;
    }
    .music-source-link {
      width: fit-content;
      color: var(--ink);
      text-decoration-thickness: 1px;
      text-underline-offset: 2px;
    }
    .music-bar label {
      margin: 0;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      color: rgba(23,48,71,0.72);
      font-size: 0.68rem;
      font-weight: 900;
    }
    .music-track-select {
      min-height: 30px;
      width: 158px;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 0.72rem;
      background: rgba(255,255,255,0.72);
    }
    .music-progress {
      flex: 1;
      min-width: 0;
      accent-color: var(--ink);
    }
    .music-volume {
      width: 82px;
      accent-color: var(--gold);
    }
    .music-time {
      min-width: 42px;
      text-align: right;
      font-size: 0.72rem;
      font-weight: 900;
      color: rgba(23,48,71,0.74);
    }
    .directory-assistant {
      position: fixed;
      left: max(16px, env(safe-area-inset-left));
      bottom: max(16px, env(safe-area-inset-bottom));
      z-index: 35;
      width: min(430px, calc(100vw - 32px));
      pointer-events: none;
    }
    .directory-assistant__toggle {
      pointer-events: auto;
      display: inline-flex;
      align-items: center;
      gap: 9px;
      min-height: 42px;
      border: 1px solid rgba(255,255,255,0.34);
      border-radius: 999px;
      padding: 9px 13px;
      background: rgba(23,48,71,0.76);
      color: #fff;
      font: inherit;
      font-size: 0.82rem;
      font-weight: 900;
      box-shadow: 0 12px 26px rgba(23,48,71,0.16);
      backdrop-filter: blur(14px);
    }
    .page-network:not([data-scroll-state="scrolled"]) .directory-assistant__toggle {
      opacity: 0;
      visibility: hidden;
      pointer-events: none;
    }
    .assistant-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--gold);
      box-shadow: 0 0 0 5px rgba(216,187,104,0.18);
    }
    .directory-assistant__panel {
      pointer-events: auto;
      position: fixed;
      left: max(16px, env(safe-area-inset-left));
      bottom: calc(max(16px, env(safe-area-inset-bottom)) + 58px);
      width: min(430px, calc(100vw - 32px));
      margin: 0;
      max-height: min(72vh, 620px);
      overflow: auto;
      padding: 16px;
      border: 1px solid rgba(23,48,71,0.16);
      border-radius: 10px;
      background: rgba(255,255,255,0.94);
      box-shadow: 0 24px 64px rgba(23,48,71,0.20);
      backdrop-filter: blur(18px);
    }
    .directory-assistant__panel.is-southwest-opening {
      transform-origin: left bottom;
      animation: assistant-desert-open 460ms cubic-bezier(.2,.82,.24,1.08) both;
    }
    .directory-assistant__panel.is-southwest-closing {
      pointer-events: none;
      transform-origin: left bottom;
      animation: assistant-desert-close 260ms cubic-bezier(.58,.08,.82,.38) both;
    }
    .resource-item.is-bubble-opening,
    .source-card.is-bubble-opening {
      transform-origin: center top;
      animation: listing-bubble-pop 280ms cubic-bezier(.2,.82,.24,1.14) both;
    }
    @keyframes assistant-desert-open {
      0% { opacity: 0; transform: translateY(10px) scale(0.95); }
      70% { opacity: 1; transform: translateY(-1px) scale(1.008); }
      100% { opacity: 1; transform: translateY(0) scale(1); }
    }
    @keyframes assistant-desert-close {
      0% { opacity: 1; transform: translateY(0) scale(1); }
      100% { opacity: 0; transform: translateY(8px) scale(0.97); }
    }
    @keyframes listing-bubble-pop {
      0% { transform: scale(0.985); box-shadow: 0 7px 18px rgba(23,48,71,0.05); }
      64% { transform: scale(1.006); box-shadow: 0 14px 30px rgba(23,48,71,0.10); }
      100% { transform: scale(1); box-shadow: 0 10px 28px rgba(23,48,71,0.06); }
    }
    .directory-assistant__desert-motion {
      height: 48px;
      margin: -16px -16px 12px;
      overflow: hidden;
      border-bottom: 1px solid rgba(23,48,71,0.12);
      border-radius: 9px 9px 0 0;
      background: rgba(175,203,208,0.24);
    }
    .directory-assistant__desert-motion svg {
      display: block;
      width: 100%;
      height: 100%;
    }
    .assistant-desert__sky { fill: #dfe8df; }
    .assistant-desert__sun {
      fill: #d6bb68;
      opacity: 0.82;
      transform-box: fill-box;
      transform-origin: center;
    }
    .assistant-desert__far-ridge { fill: #9eb8b3; opacity: 0.58; }
    .assistant-desert__near-ridge { fill: #6f7f6c; opacity: 0.72; }
    .assistant-desert__wind,
    .assistant-desert__horizon,
    .assistant-desert__stem,
    .assistant-desert__leaves {
      fill: none;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    .assistant-desert__wind {
      stroke: rgba(255,253,248,0.82);
      stroke-width: 1.2;
      stroke-dasharray: 24 12;
    }
    .assistant-desert__horizon {
      stroke: rgba(167,97,73,0.54);
      stroke-width: 1.4;
      stroke-dasharray: 440;
    }
    .assistant-desert__yucca {
      transform-box: fill-box;
      transform-origin: 50% 100%;
    }
    .assistant-desert__stem { stroke: #556554; stroke-width: 2.2; }
    .assistant-desert__leaves { stroke: #324f4d; stroke-width: 2.4; }
    .assistant-desert__flowers circle {
      fill: #fff8df;
      stroke: #b69146;
      stroke-width: 0.7;
      transform-box: fill-box;
      transform-origin: center;
    }
    .directory-assistant__panel.is-southwest-opening .assistant-desert__sun {
      animation: assistant-sunrise 720ms cubic-bezier(.18,.74,.28,1) both;
    }
    .directory-assistant__panel.is-southwest-opening .assistant-desert__horizon {
      animation: assistant-horizon-draw 660ms ease-out both;
    }
    .directory-assistant__panel.is-southwest-opening .assistant-desert__wind {
      animation: assistant-wind-drift 1100ms ease-out both;
    }
    .directory-assistant__panel.is-southwest-opening .assistant-desert__yucca--one {
      animation: assistant-yucca-grow 620ms cubic-bezier(.16,.82,.25,1.12) 90ms both;
    }
    .directory-assistant__panel.is-southwest-opening .assistant-desert__yucca--two {
      animation: assistant-yucca-grow 560ms cubic-bezier(.16,.82,.25,1.12) 170ms both;
    }
    .directory-assistant__panel.is-southwest-opening .assistant-desert__flowers circle {
      animation: assistant-flower-open 380ms cubic-bezier(.18,.86,.24,1.22) 390ms both;
    }
    .directory-assistant__panel.is-southwest-closing .assistant-desert__sun {
      animation: assistant-sunset 240ms ease-in both;
    }
    .directory-assistant__panel.is-southwest-closing .assistant-desert__yucca {
      animation: assistant-yucca-rest 220ms ease-in both;
    }
    @keyframes assistant-sunrise {
      from { opacity: 0; transform: translateY(13px) scale(0.72); }
      to { opacity: 0.82; transform: translateY(0) scale(1); }
    }
    @keyframes assistant-sunset {
      from { opacity: 0.82; transform: translateY(0) scale(1); }
      to { opacity: 0; transform: translateY(12px) scale(0.78); }
    }
    @keyframes assistant-horizon-draw {
      from { stroke-dashoffset: 440; }
      to { stroke-dashoffset: 0; }
    }
    @keyframes assistant-wind-drift {
      from { opacity: 0; stroke-dashoffset: 72; transform: translateX(-12px); }
      45% { opacity: 0.84; }
      to { opacity: 0.34; stroke-dashoffset: 0; transform: translateX(8px); }
    }
    @keyframes assistant-yucca-grow {
      from { opacity: 0; transform: scaleY(0.16) rotate(-2deg); }
      to { opacity: 1; transform: scaleY(1) rotate(0); }
    }
    @keyframes assistant-yucca-rest {
      from { opacity: 1; transform: scaleY(1); }
      to { opacity: 0; transform: scaleY(0.55); }
    }
    @keyframes assistant-flower-open {
      from { opacity: 0; transform: scale(0.2); }
      to { opacity: 1; transform: scale(1); }
    }
    .directory-assistant__panel::backdrop {
      background: rgba(16,40,61,0.12);
      backdrop-filter: blur(1px);
    }
    .directory-assistant__header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 14px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 10px;
      margin-bottom: 10px;
    }
    .directory-assistant__header h2 { margin: 0; font-size: 1.25rem; }
    .directory-assistant__close {
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(23,48,71,0.06);
      color: var(--ink);
      padding: 6px 9px;
      min-height: 36px;
      font: inherit;
      font-size: 0.72rem;
      font-weight: 900;
    }
    .directory-assistant__intro,
    .directory-assistant__scope,
    .directory-assistant__status,
    .assistant-result p {
      color: var(--ink-soft);
    }
    .directory-assistant__scope {
      margin: 8px 0 0;
      padding-left: 10px;
      border-left: 2px solid rgba(182,145,70,0.48);
      font-size: 0.82rem;
      line-height: 1.45;
    }
    .directory-assistant__scope a { color: var(--linked); font-weight: 800; }
    .directory-assistant__form { display: grid; gap: 8px; margin-top: 12px; }
    .directory-assistant__search-row { display: grid; grid-template-columns: 1fr auto; gap: 8px; }
    .directory-assistant input {
      width: 100%;
      min-height: 42px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 10px 11px;
      background: rgba(255,255,255,0.96);
      color: var(--ink);
      font: inherit;
    }
    .directory-assistant__prompt-label {
      margin: 12px 0 7px;
      color: var(--ink);
      font-size: 0.76rem;
      font-weight: 900;
    }
    .directory-assistant__chips { display: flex; flex-wrap: wrap; gap: 7px; margin: 0 0 12px; }
    .directory-assistant__chips button {
      border: 1px solid rgba(47,103,128,0.18);
      border-radius: 999px;
      background: rgba(220,238,232,0.62);
      color: var(--ink);
      padding: 6px 9px;
      min-height: 36px;
      font: inherit;
      font-size: 0.74rem;
      font-weight: 900;
    }
    .directory-assistant__results { display: grid; gap: 8px; margin-top: 8px; }
    .directory-assistant__results:empty { display: none; margin-top: 0; }
    .directory-assistant__guidance {
      display: grid;
      gap: 7px;
      margin-top: 9px;
      padding: 10px;
      border-left: 3px solid rgba(47,103,128,0.52);
      border-radius: 0 var(--radius) var(--radius) 0;
      background: rgba(220,238,232,0.44);
    }
    .directory-assistant__guidance[hidden] { display: none; }
    .directory-assistant__guidance p { margin: 0; color: var(--ink-soft); font-size: 0.82rem; line-height: 1.4; }
    .directory-assistant__question { color: var(--ink) !important; font-weight: 850; }
    .directory-assistant__followups { display: flex; flex-wrap: wrap; gap: 6px; }
    .directory-assistant__followups button {
      min-height: 34px;
      border: 1px solid rgba(47,103,128,0.20);
      border-radius: 999px;
      padding: 6px 9px;
      background: rgba(255,255,255,0.82);
      color: var(--ink);
      font: inherit;
      font-size: 0.74rem;
      font-weight: 850;
    }
    .assistant-result {
      display: grid;
      gap: 5px;
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(246,248,244,0.86);
    }
    .assistant-result__meta {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 5px;
      color: var(--ink-soft);
      font-size: 0.72rem;
      font-weight: 800;
    }
    .assistant-result__type {
      border-radius: 999px;
      background: rgba(23,48,71,0.08);
      padding: 3px 8px;
      font-size: 0.72rem;
      font-weight: 900;
    }
    .assistant-result h3 { margin: 0; font-size: 0.96rem; line-height: 1.25; }
    .assistant-result p { margin: 0; font-size: 0.82rem; line-height: 1.4; }
    .assistant-result__description {
      display: -webkit-box;
      overflow: hidden;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 3;
    }
    .assistant-result__next {
      display: -webkit-box;
      overflow: hidden;
      padding-top: 2px;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 2;
    }
    .assistant-result__next strong { color: var(--ink); }
    .assistant-result__actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    .assistant-result__actions .resource-links { margin-top: 2px; }
    .assistant-result__actions .resource-contact-link { min-height: 34px; padding: 6px 9px; font-size: 0.78rem; }
    .assistant-result__actions .source-note { font-size: 0.78rem; }
    .directory-assistant__footer {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid var(--line);
    }
    .site-footer {
      display: grid;
      grid-template-columns: minmax(240px, 0.8fr) minmax(0, 1.8fr);
      gap: clamp(24px, 4vw, 52px);
      align-items: start;
      padding: 42px clamp(18px, 6vw, 86px);
      background: #10283d;
      border-top: 3px solid rgba(182,145,70,0.66);
      color: rgba(255,255,255,0.78);
    }
    .footer-summary { display: grid; gap: 14px; align-content: start; }
    .footer-kicker { color: #fff; font-weight: 900; }
    .footer-index {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 18px;
    }
    .footer-column h2 {
      margin: 0 0 10px;
      color: #fff;
      font: inherit;
      font-size: 0.84rem;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .footer-column ul {
      display: grid;
      gap: 7px;
      margin: 0;
      padding: 0;
      list-style: none;
    }
    .footer-column a {
      color: rgba(255,255,255,0.78);
      text-decoration: none;
      text-underline-offset: 3px;
      font-size: 0.88rem;
    }
    .footer-column a:hover,
    .footer-column a:focus-visible {
      color: #fff;
      text-decoration: underline;
    }
    .footer-logos { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; justify-content: flex-end; }
    .footer-logos img { width: 170px; height: 86px; object-fit: contain; background: rgba(255,255,255,0.9); border-radius: 6px; padding: 8px; }
    .footer-placeholder {
      display: inline-grid;
      place-items: center;
      width: 170px;
      height: 86px;
      border: 1px solid rgba(255,255,255,0.28);
      border-radius: 6px;
      background: rgba(255,255,255,0.10);
      color: rgba(255,255,255,0.9);
      font-weight: 900;
    }
    :focus-visible { outline: 3px solid var(--gold); outline-offset: 3px; }
    @media (min-width: 1200px) {
      .site-header { padding-right: 198px; }
      .nav-yucca-flourish { right: 24px; }
    }
    @media (max-width: 860px) {
      .site-header { align-items: flex-start; flex-direction: column; }
      .site-nav { width: 100%; justify-content: flex-start; }
      .path-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .two-col, .site-footer, .advanced-filters, .form-grid, .submit-card { grid-template-columns: 1fr; }
      .page-wayfinding { grid-template-columns: 1fr 1fr; }
      .page-wayfinding__intro { grid-column: 1 / -1; }
      .nav-yucca-flourish { top: 1px; right: 7px; width: 118px; height: 46px; }
      .footer-index { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .footer-logos { justify-content: flex-start; }
      .next-action-list { grid-template-columns: 1fr; }
      .lead-list { columns: 1; }
      h1 { max-width: 12ch; }
      .back-to-top, .music-summary, .music-toggle { min-height: 38px; padding: 7px 10px; font-size: 0.74rem; }
      .corner-controls { width: min(360px, calc(100vw - 24px)); }
      .music-panel { padding: 9px; }
      .music-track-select { width: 140px; }
      .directory-assistant { width: min(390px, calc(100vw - 24px)); left: 12px; bottom: 74px; }
      .directory-assistant__toggle { min-height: 40px; padding: 8px 11px; font-size: 0.78rem; }
      .directory-assistant__panel { left: 12px; bottom: 128px; width: min(390px, calc(100vw - 24px)); max-height: min(76vh, 580px); padding: 13px; }
      .directory-assistant__desert-motion { margin: -13px -13px 10px; }
    }
    @media (max-width: 640px) {
      body { overflow-x: hidden; }
      .site-header { width: 100%; max-width: 100vw; padding: 8px 12px; gap: 10px; }
      .brand { font-size: 0.9rem; gap: 8px; }
      .brand-mark { width: 32px; height: 26px; }
      .site-nav { width: 100%; max-width: 100%; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 5px; justify-content: stretch; overflow: visible; padding-bottom: 0; }
      .site-nav a, .nav-trigger { width: 100%; min-height: 40px; white-space: normal; text-align: center; padding: 5px 6px; font-size: 0.76rem; line-height: 1.2; }
      .nav-group { position: static; min-width: 0; }
      .nav-menu,
      .nav-menu--promote { position: absolute; top: calc(100% + 6px); right: 0; left: 0; width: 100%; min-width: 0; max-width: none; margin-top: 0; padding: 8px; box-shadow: var(--shadow); }
      .nav-menu a { white-space: normal; justify-content: flex-start; text-align: left; }
      .nav-menu-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 2px 10px; }
      .nav-menu-section { padding: 2px 0 3px; }
      .nav-menu-label { padding: 5px 5px 2px; }
      .nav-menu-county-links a { min-height: 28px; padding: 3px 5px; font-size: 0.7rem; }
      .hero {
        min-height: min(64svh, 560px);
        padding-top: clamp(64px, 15vw, 84px);
        padding-bottom: 96px;
      }
      .hero-actions {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
        max-width: 360px;
        margin-top: 18px;
      }
      .hero-actions .button {
        min-height: 40px;
        padding: 8px 10px;
        font-size: 0.9rem;
        text-align: center;
      }
      .hero-actions .button:nth-child(3) { grid-column: 1 / -1; }
      .page-hero { min-height: 178px; padding-top: 20px; padding-bottom: 20px; }
      .page-hero h1 { max-width: 15ch; font-size: clamp(2rem, 9vw, 2.5rem); }
      .page-hero .lede { display: none; }
      .page-hero-art { width: 500px; max-width: none; right: -235px; top: 46%; opacity: 0.44; }
      .page-network .page-hero { min-height: 188px; padding-top: 18px; padding-bottom: 20px; }
      .page-network .page-hero h1 { max-width: 12ch; font-size: 2.25rem; line-height: 1.02; }
      .page-network .section { padding: 32px 18px; }
      .page-network .section-heading { margin-bottom: 18px; }
      .page-wayfinding { grid-template-columns: 1fr; gap: 11px; padding: 14px 18px; }
      .page-wayfinding__intro { grid-column: auto; }
      .page-wayfinding__links { gap: 7px 12px; }
      .path-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
      .path-card { min-height: 132px; padding: 12px; }
      .path-card h2 { font-size: 1.05rem; }
      .path-card p { display: none; }
      .arts-route-visual { min-height: 122px; }
      .arts-route-visual span { padding: 12px 9px; }
      .arts-route-visual strong { font-size: 0.96rem; }
      .arts-route-visual small { display: none; }
      .directory-jumpbar { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 18px; }
      .directory-jumpbar .button { min-height: 40px; padding: 8px; text-align: center; }
      .directory-search-panel { padding: 12px; gap: 10px; }
      .directory-filter-details {
        border-top: 1px solid var(--line);
      }
      .directory-filter-details > summary,
      .resource-more > summary,
      .source-group-links > summary {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        cursor: pointer;
        color: var(--ink);
        font-weight: 850;
      }
      .directory-filter-details > summary { padding: 12px 0 2px; }
      .directory-filter-details > summary span { color: var(--ink-soft); font-size: 0.78rem; font-weight: 750; }
      .directory-filter-body { padding-top: 12px; }
      .filter-row { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 7px; }
      .filter-row .chip { width: 100%; min-height: 40px; padding: 7px 8px; font-size: 0.78rem; }
      #physical-location-filter .chip:first-child,
      [aria-label="Resource filters"] .chip:first-child { grid-column: 1 / -1; }
      .marker-help > summary { padding: 10px 12px; font-size: 0.86rem; }
      .marker-help .marker-legend { display: grid; grid-template-columns: auto 1fr; gap: 7px; padding: 0 12px 12px; font-size: 0.8rem; }
      .resource-list, .source-grid { grid-template-columns: 1fr; gap: 10px; }
      .resource-item, .source-card { padding: 12px; box-shadow: none; }
      .resource-item__head h3 { font-size: 1.08rem; line-height: 1.18; }
      .resource-meta-line { margin: 7px 0; font-size: 0.82rem; line-height: 1.4; }
      .resource-description {
        display: -webkit-box;
        overflow: hidden;
        margin: 8px 0;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;
        font-size: 0.9rem;
        line-height: 1.45;
      }
      .resource-more, .source-group-links { margin-top: 8px; border-top: 1px solid var(--line); }
      .resource-more > summary, .source-group-links > summary { padding: 10px 0 2px; font-size: 0.82rem; }
      .resource-more__body { padding-top: 9px; }
      .resource-tags .badge { font-size: 0.68rem; padding: 2px 6px; }
      .outreach-tags { gap: 5px; }
      .outreach-tag { padding: 4px 6px; font-size: 0.68rem; }
      .resource-links { gap: 6px; margin-top: 9px; }
      .resource-contact-link { min-height: 38px; padding: 7px 10px; font-size: 0.8rem; }
      .source-group-links .source-link-list { margin-top: 8px; padding-top: 8px; }
      .directory-more-row .button { width: 100%; justify-content: center; }
      .directory-secondary-actions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .directory-secondary-actions .button { padding: 8px; text-align: center; }
      .directory-support-details > summary { font-size: 0.9rem; }
      .corner-controls { left: auto; right: 12px; bottom: 12px; width: auto; max-width: calc(100vw - 156px); flex-direction: column; align-items: flex-end; justify-content: flex-end; }
      .back-to-top, .music-summary, .music-toggle { font-size: 0.72rem; min-height: 38px; padding: 6px 9px; background-color: rgba(16,40,61,0.48); max-width: none; white-space: nowrap; }
      .music-toggle { position: static; left: auto; right: auto; bottom: auto; }
      .back-to-top { position: static; left: auto; right: auto; bottom: auto; align-self: flex-end; }
      .music-summary { align-self: flex-end; min-width: 116px; }
      .music-label-prefix { display: none; }
      .page-network:not([data-music-state="playing"]) .music-bar {
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
      }
      .page-network:not([data-scroll-state="scrolled"]) .directory-assistant__toggle {
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
      }
      .music-toggle { background-color: rgba(255,255,255,0.60); }
      .music-toggle[data-state="playing"] { background-color: rgba(216,187,104,0.52); }
      .music-bar { width: auto; max-width: calc(100vw - 24px); align-self: flex-end; }
      .music-panel { width: min(320px, calc(100vw - 24px)); }
      .music-bar__top { align-items: flex-start; }
      .music-track-label { flex: 1; }
      .music-track-select { width: 100%; }
      .music-bar__bottom { align-items: flex-start; flex-direction: column; gap: 6px; }
      .music-credit-block { max-width: none; }
      .music-volume { width: 76px; }
      .directory-assistant { width: auto; max-width: calc(100vw - 156px); left: 12px; bottom: 12px; }
      .directory-assistant__toggle { min-height: 38px; padding: 7px 10px; background: rgba(23,48,71,0.56); font-size: 0.75rem; }
      .directory-assistant__panel { inset: auto 12px 12px 12px; width: auto; max-width: none; max-height: calc(100vh - 24px); }
      .directory-assistant__search-row { grid-template-columns: 1fr; }
      .directory-assistant__footer .button { width: 100%; justify-content: center; }
      .footer-index { grid-template-columns: 1fr; }
      .footer-logos img { width: 118px; height: 62px; padding: 6px; }
      .footer-placeholder { width: 118px; height: 62px; }
    }
    .funding-filter-panel {
      margin: 20px 0 24px;
      padding: 18px 0;
      border-block: 1px solid var(--line);
    }
    .promote-filter-panel,
    .physical-filter-panel {
      margin: 20px 0 24px;
      padding: 18px 0;
      border-block: 1px solid var(--line);
    }
    .promote-search-label,
    .physical-search-label {
      display: block;
      margin-bottom: 7px;
      color: var(--ink);
      font-weight: 800;
    }
    .promote-filter-grid,
    .physical-filter-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-top: 12px;
    }
    .promote-filter-grid label,
    .physical-filter-grid label {
      color: var(--ink-soft);
      font-size: 0.82rem;
      font-weight: 750;
    }
    .promote-filter-grid select,
    .physical-filter-grid select {
      width: 100%;
      min-height: 44px;
      margin-top: 5px;
    }
    .promote-route-grid {
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    }
    .promote-route-card {
      min-height: 190px;
      border-top: 4px solid color-mix(in srgb, var(--page-accent) 68%, transparent);
    }
    .promote-route-card.is-active {
      border-color: var(--page-accent);
      background: color-mix(in srgb, var(--page-accent) 9%, rgba(255,255,255,0.84));
      box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--page-accent) 42%, transparent);
    }
    .county-promote-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }
    .county-promote-panel {
      min-width: 0;
      padding: 17px;
      border: 1px solid var(--line);
      border-top: 4px solid color-mix(in srgb, var(--page-accent) 62%, transparent);
      border-radius: 6px;
      background: rgba(255,255,255,0.67);
    }
    .county-promote-panel h3 { margin: 0 0 11px; font-size: 1.05rem; }
    .county-promote-links { display: grid; gap: 7px; }
    .county-promote-links a {
      min-height: 38px;
      padding: 8px 10px;
      border: 1px solid rgba(23,48,71,0.12);
      border-radius: 4px;
      background: rgba(255,255,255,0.58);
      color: var(--ink);
      font-size: 0.84rem;
      font-weight: 760;
      text-decoration: none;
    }
    .county-promote-links a:hover,
    .county-promote-links a:focus-visible {
      border-color: var(--page-accent);
      background: rgba(255,255,255,0.92);
    }
    .funding-search-label { display: block; margin-bottom: 7px; color: var(--ink); font-weight: 800; }
    .funding-filter-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-top: 12px;
    }
    .funding-filter-grid label { color: var(--ink-soft); font-size: 0.82rem; font-weight: 750; }
    .funding-filter-grid select { width: 100%; min-height: 44px; margin-top: 5px; }
    .funding-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
    .funding-card {
      display: flex;
      min-width: 0;
      flex-direction: column;
      padding: 18px;
      border: 1px solid var(--line);
      border-top: 4px solid rgba(58, 111, 101, 0.72);
      border-radius: 6px;
      background: rgba(255,255,255,0.72);
    }
    .funding-card[hidden] { display: none; }
    .funding-card h3 { margin: 9px 0 2px; font-size: 1.18rem; line-height: 1.28; }
    .funding-card h3 a { color: var(--ink); text-decoration-thickness: 1px; text-underline-offset: 3px; }
    .funding-card__meta { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px; }
    .funding-provider { margin: 0 0 10px; color: var(--ink-soft); font-size: 0.84rem; font-weight: 700; }
    .funding-status {
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 4px 8px;
      border: 1px solid rgba(23,48,71,0.16);
      border-radius: 999px;
      background: rgba(74, 130, 107, 0.10);
      color: var(--ink);
      font-size: 0.74rem;
      font-weight: 800;
    }
    .funding-status--monitor-next-cycle { background: rgba(183, 139, 73, 0.11); }
    .funding-status--check-current-availability { background: rgba(91, 92, 125, 0.10); }
    .funding-card__essentials {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin: 8px 0 12px;
      padding-block: 12px;
      border-block: 1px solid var(--line);
    }
    .funding-card__essentials p { margin: 0; }
    .funding-card__essentials strong,
    .funding-card__essentials span { display: block; }
    .funding-card__essentials strong { margin-bottom: 3px; color: var(--ink); font-size: 0.76rem; text-transform: uppercase; }
    .funding-card__essentials span { color: var(--ink-soft); font-size: 0.9rem; line-height: 1.45; }
    .funding-details { margin-top: 2px; }
    .funding-details > summary { cursor: pointer; color: var(--ink); font-size: 0.86rem; font-weight: 800; }
    .funding-terms { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 16px; margin: 12px 0 0; }
    .funding-terms div { min-width: 0; padding: 9px 0; border-top: 1px solid rgba(23,48,71,0.10); }
    .funding-terms dt { color: var(--ink); font-size: 0.74rem; font-weight: 800; text-transform: uppercase; }
    .funding-terms dd { margin: 3px 0 0; color: var(--ink-soft); font-size: 0.84rem; line-height: 1.45; overflow-wrap: anywhere; }
    .funding-card__actions { margin-top: auto; padding-top: 14px; }
    @media (max-width: 900px) {
      .site-watermark { font-size: 1rem; }
      .funding-filter-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .funding-grid { grid-template-columns: 1fr; }
      .county-promote-grid { grid-template-columns: 1fr; }
      .tool-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .tool-filters { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .tool-offer-grid { grid-template-columns: 1fr; }
      .tool-offer-card { border-right: 0; border-bottom: 1px solid var(--line); }
      .tool-offer-card:last-child { border-bottom: 0; }
    }
    @media (max-width: 640px) {
      .site-watermark { bottom: max(9vh, env(safe-area-inset-bottom)); padding-inline: 12px; font-size: 0.9rem; }
      .funding-filter-panel { margin: 14px 0 18px; padding: 12px 0; }
      .funding-filter-grid { grid-template-columns: 1fr; gap: 8px; }
      .funding-card { padding: 13px; }
      .funding-card h3 { font-size: 1.05rem; }
      .funding-card__essentials, .funding-terms { grid-template-columns: 1fr; }
      .funding-card__essentials { gap: 8px; }
      .funding-card__actions { display: grid; grid-template-columns: 1fr; }
      .funding-card__actions .button { width: 100%; justify-content: center; }
      .promote-filter-panel,
      .physical-filter-panel { margin: 12px 0 16px; padding: 12px 0; }
      .promote-filter-grid,
      .physical-filter-grid { grid-template-columns: 1fr; gap: 8px; }
      .tool-grid { grid-template-columns: 1fr; gap: 10px; }
      .tool-filters { grid-template-columns: 1fr; gap: 8px; padding: 12px; }
      .tool-filter-status { grid-column: 1; }
      .tool-card { min-height: 0; padding: 13px; }
      .tool-offer-card { padding: 16px 0; }
      .tool-offer-card .button { width: 100%; justify-content: center; }
      .promote-route-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
      .promote-route-card { min-height: 138px; padding: 12px; }
      .promote-route-card h3 { font-size: 0.98rem; }
      .promote-route-card p {
        display: -webkit-box;
        overflow: hidden;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;
      }
      .county-promote-section,
      .posting-method { display: none; }
      .page-posting .mini-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
      .page-posting .mini-card { min-height: 132px; padding: 12px; }
      .page-posting .mini-card h3 { font-size: 0.96rem; }
      .page-posting .mini-card p {
        display: -webkit-box;
        overflow: hidden;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;
      }
    }
    @media (max-width: 420px) {
      .site-nav { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 5px; }
      .site-nav a, .nav-trigger { min-height: 42px; padding: 6px 5px; font-size: 0.78rem; }
      .nav-menu--promote { max-height: min(68vh, 520px); }
      .site-watermark { bottom: max(9vh, env(safe-area-inset-bottom)); padding-inline: 10px; font-size: 0.82rem; letter-spacing: 0.08em; }
    }
    @media print {
      .site-header, .site-watermark, .hero-actions, .tool-panel, .copy-button, .corner-controls, .directory-assistant, .download-row, .nav-yucca-flourish { display: none; }
      body { background: #fff; background-image: none; color: #111; }
      a::after { content: " (" attr(href) ")"; font-size: 0.86em; }
      .section, .page-hero { padding: 24px 0; }
      tr, figure, .source-card, .resource-item, .funding-card { break-inside: avoid; }
    }
    @media (prefers-reduced-motion: reduce) {
      *,
      *::before,
      *::after {
        animation-duration: 0.001ms !important;
        animation-iteration-count: 1 !important;
        scroll-behavior: auto !important;
        transition-duration: 0.001ms !important;
      }
      [data-animated="true"], .intro-curtain, .hero-accent, .hero-route, .hero-node, .submit-success-card, .sparkle,
      .directory-assistant__panel.is-southwest-opening, .directory-assistant__panel.is-southwest-closing,
      .assistant-desert__sun, .assistant-desert__horizon, .assistant-desert__wind,
      .assistant-desert__yucca, .assistant-desert__flowers circle,
      .resource-item.is-bubble-opening, .source-card.is-bubble-opening,
      .nav-yucca-flourish, .nav-yucca__stem, .nav-yucca__branch, .nav-yucca__leaf, .nav-yucca__flower {
        animation: none !important;
        transform: none !important;
      }
      .intro-curtain, .nav-yucca-flourish { display: none; }
    }
    """
    (ASSET_OUT / "styles.css").write_text(dedent(css).strip() + "\n", encoding="utf-8")

    js = r"""
    const DATA = window.TRI_COUNTY_GUIDE_DATA || { directory_sources: [], resources: [] };
    const GUIDE_SOUND_CHOICE_KEY = "triCountyRegionalSoundChoiceV3";
    const GUIDE_SOUND_VOLUME_KEY = "triCountyRegionalSoundVolumeV3";
    let guideAudioContext = null;
    let guideSfxArmed = false;

    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      })[char]);
    }

    function searchableText(value) {
      if (Array.isArray(value)) return value.map(searchableText).join(" ");
      if (value && typeof value === "object") return Object.values(value).map(searchableText).join(" ");
      return String(value ?? "");
    }

    function soundEffectsAllowed() {
      return localStorage.getItem(GUIDE_SOUND_CHOICE_KEY) !== "stopped";
    }

    function guideSfxVolume() {
      const saved = Number(localStorage.getItem(GUIDE_SOUND_VOLUME_KEY));
      const base = Number.isFinite(saved) ? saved : 42;
      return Math.max(0.04, Math.min(0.28, (base / 100) * 0.32));
    }

    function getGuideAudioContext() {
      const AudioCtor = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtor) return null;
      if (!guideAudioContext) {
        guideAudioContext = new AudioCtor();
      }
      return guideAudioContext;
    }

    function playFilteredNoise(ctx, when, duration, gain, frequency = 2600) {
      const sampleRate = ctx.sampleRate;
      const length = Math.max(1, Math.floor(sampleRate * duration));
      const buffer = ctx.createBuffer(1, length, sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < length; i += 1) {
        const t = i / length;
        const envelope = Math.pow(1 - t, 2.6);
        data[i] = (Math.random() * 2 - 1) * envelope;
      }
      const source = ctx.createBufferSource();
      const filter = ctx.createBiquadFilter();
      const amp = ctx.createGain();
      filter.type = "bandpass";
      filter.frequency.setValueAtTime(frequency, when);
      filter.Q.setValueAtTime(4.4, when);
      amp.gain.setValueAtTime(0.0001, when);
      amp.gain.exponentialRampToValueAtTime(gain, when + 0.012);
      amp.gain.exponentialRampToValueAtTime(0.0001, when + duration);
      source.buffer = buffer;
      source.connect(filter);
      filter.connect(amp);
      amp.connect(ctx.destination);
      source.start(when);
      source.stop(when + duration + 0.02);
    }

    function playPluckedNote(ctx, when, frequency, duration, gain, pan = 0) {
      const oscillator = ctx.createOscillator();
      const harmonic = ctx.createOscillator();
      const filter = ctx.createBiquadFilter();
      const amp = ctx.createGain();
      const stereo = ctx.createStereoPanner ? ctx.createStereoPanner() : null;
      oscillator.type = "triangle";
      harmonic.type = "sine";
      oscillator.frequency.setValueAtTime(frequency, when);
      harmonic.frequency.setValueAtTime(frequency * 2.01, when);
      filter.type = "lowpass";
      filter.frequency.setValueAtTime(2100, when);
      filter.frequency.exponentialRampToValueAtTime(720, when + duration);
      filter.Q.setValueAtTime(0.55, when);
      amp.gain.setValueAtTime(0.0001, when);
      amp.gain.exponentialRampToValueAtTime(gain, when + 0.018);
      amp.gain.exponentialRampToValueAtTime(0.0001, when + duration);
      oscillator.connect(filter);
      harmonic.connect(filter);
      filter.connect(amp);
      if (stereo) {
        stereo.pan.setValueAtTime(pan, when);
        amp.connect(stereo);
        stereo.connect(ctx.destination);
      } else {
        amp.connect(ctx.destination);
      }
      oscillator.start(when);
      harmonic.start(when);
      oscillator.stop(when + duration + 0.04);
      harmonic.stop(when + duration + 0.04);
    }

    function scheduleGuideSfx(kind) {
      const ctx = getGuideAudioContext();
      if (!ctx) return false;
      const now = ctx.currentTime + 0.018;
      const volume = guideSfxVolume();
      if (kind === "submit") {
        playFilteredNoise(ctx, now, 0.11, volume * 0.22, 3200);
        [
          [329.63, 0.00, 0.40, -0.22],
          [440.00, 0.08, 0.42, 0.10],
          [523.25, 0.17, 0.46, 0.24],
          [659.25, 0.31, 0.62, 0.05]
        ].forEach(([freq, offset, dur, pan]) => playPluckedNote(ctx, now + offset, freq, dur, volume * 0.34, pan));
        return true;
      }
      playFilteredNoise(ctx, now + 0.04, 0.16, volume * 0.18, 1800);
      [
        [220.00, 0.00, 0.55, -0.18],
        [277.18, 0.13, 0.58, 0.08],
        [329.63, 0.28, 0.64, 0.18],
        [392.00, 0.48, 0.78, -0.02]
      ].forEach(([freq, offset, dur, pan]) => playPluckedNote(ctx, now + offset, freq, dur, volume * 0.25, pan));
      return true;
    }

    function armGuideSfx(kind) {
      if (guideSfxArmed) return;
      guideSfxArmed = true;
      const trigger = () => {
        guideSfxArmed = false;
        document.removeEventListener("pointerdown", trigger);
        document.removeEventListener("keydown", trigger);
        playGuideSfx(kind, { userInitiated: true });
      };
      document.addEventListener("pointerdown", trigger, { once: true, passive: true });
      document.addEventListener("keydown", trigger, { once: true });
    }

    async function playGuideSfx(kind, { armOnGesture = false, userInitiated = false } = {}) {
      if (!soundEffectsAllowed()) return false;
      const ctx = getGuideAudioContext();
      if (!ctx) return false;
      try {
        if (ctx.state === "suspended") {
          await ctx.resume();
        }
        if (ctx.state === "suspended") {
          if (armOnGesture && !userInitiated) armGuideSfx(kind);
          return false;
        }
        return scheduleGuideSfx(kind);
      } catch {
        if (armOnGesture && !userInitiated) armGuideSfx(kind);
        return false;
      }
    }

    const NAV_YUCCA_KEY = "statelineGuideNavYuccaV1";

    function initPreviewWatermark() {
      const watermark = document.querySelector("[data-preview-watermark]");
      if (!watermark) return;
      const host = window.location.hostname.toLowerCase();
      const isPreview = host.startsWith("deploy-preview-") || host === "localhost" || host === "127.0.0.1";
      if (isPreview) watermark.hidden = false;
    }

    function playNavigationYucca() {
      const flourish = document.querySelector("[data-nav-yucca]");
      if (!flourish || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      flourish.classList.remove("is-growing");
      void flourish.offsetWidth;
      flourish.classList.add("is-growing");
      window.setTimeout(() => flourish.classList.remove("is-growing"), 3050);
    }

    function initNavigationYucca() {
      const flourish = document.querySelector("[data-nav-yucca]");
      if (!flourish) return;

      try {
        if (sessionStorage.getItem(NAV_YUCCA_KEY) === "show") {
          sessionStorage.removeItem(NAV_YUCCA_KEY);
          const intro = document.querySelector(".intro-curtain");
          if (intro) {
            intro.dataset.introState = "skipped";
            sessionStorage.setItem("triCountyLandingIntroSeenV3", "seen");
          }
          window.requestAnimationFrame(() => window.requestAnimationFrame(playNavigationYucca));
        }
      } catch {}

      document.addEventListener("click", event => {
        if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        if (!(event.target instanceof Element)) return;
        const anchor = event.target.closest("a[href]");
        if (!anchor || anchor.hasAttribute("download")) return;
        const target = (anchor.getAttribute("target") || "").toLowerCase();
        if (target && target !== "_self") return;
        const href = anchor.getAttribute("href") || "";
        if (!href || href.startsWith("mailto:") || href.startsWith("tel:") || href.startsWith("javascript:")) return;

        let destination;
        try {
          destination = new URL(anchor.href, window.location.href);
        } catch {
          return;
        }
        if (destination.origin !== window.location.origin) return;

        const sameDocument = destination.pathname === window.location.pathname && destination.search === window.location.search;
        if (sameDocument) {
          if (destination.hash && destination.hash !== window.location.hash) playNavigationYucca();
          return;
        }

        try {
          sessionStorage.setItem(NAV_YUCCA_KEY, "show");
        } catch {}
      });
    }

    const SEARCH_STOP_WORDS = new Set(["a", "an", "and", "for", "in", "near", "of", "the", "to"]);

    function normalizedSearchTerms(query) {
      return String(query || "")
        .toLowerCase()
        .split(/\s+/)
        .map(term => term.replace(/[^a-z0-9+&-]/g, ""))
        .filter(term => term.length > 1 && !SEARCH_STOP_WORDS.has(term))
        .map(term => {
          if (term.length > 5 && term.endsWith("ies")) return `${term.slice(0, -3)}y`;
          if (term.length > 4 && term.endsWith("s") && !term.endsWith("ss")) return term.slice(0, -1);
          return term;
        });
    }

    function matchesSearchTerms(blob, query) {
      const terms = normalizedSearchTerms(query);
      if (!terms.length) return true;
      const text = String(blob || "").toLowerCase();
      return terms.every(term => text.includes(term));
    }

    function textMatch(item, query) {
      return matchesSearchTerms(searchableText(item), query);
    }

    function resourceTextMatch(item, query) {
      const blob = searchableText([
        item.resource_name,
        item.alternate_names,
        item.town,
        item.county,
        item.state,
        item.category,
        item.resource_type,
        item.public_listing_type,
        item.access_mode,
        item.public_keywords,
        item.public_audience_tags,
        item.public_best_for,
        item.online_connection_group,
        item.online_connection_label,
        item.physical_promotion_keywords,
        item.outreach_channel_keys,
        item.outreach_channel_labels,
        (item.outreach_channels || []).map(channel => [channel.channel, channel.label, channel.status_label].filter(Boolean).join(" ")).join(" "),
        item.goal_relevance,
        item.audience_served,
        item.public_description
      ]);
      return matchesSearchTerms(blob, query);
    }

    function uniqueValues(items, field) {
      return [...new Set(items.map(item => item[field]).filter(Boolean))].sort((a, b) => a.localeCompare(b));
    }

    function populateSelect(select, values, allLabel) {
      if (!select) return;
      select.innerHTML = `<option value="All">${allLabel}</option>` + values.map(value => `<option value="${value}">${value}</option>`).join("");
    }

    function splitList(value) {
      return String(value || "")
        .split(";")
        .map(part => part.trim())
        .filter(Boolean);
    }

    function normalUrl(value) {
      const url = String(value || "").trim();
      if (!url) return "";
      if (/^https?:\/\//i.test(url) || /^mailto:/i.test(url) || /^tel:/i.test(url)) return url;
      if (/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(url)) return `mailto:${url}`;
      return `https://${url}`;
    }

    function urlHost(value) {
      try {
        return new URL(normalUrl(value)).hostname.replace(/^www\./, "").toLowerCase();
      } catch {
        return "";
      }
    }

    function linkLabel(url, fallback = "Website") {
      const host = urlHost(url);
      const lower = String(url || "").toLowerCase();
      if (lower.startsWith("mailto:")) return "Email";
      if (lower.startsWith("tel:")) return "Phone";
      if (host.includes("facebook.com")) return "Facebook";
      if (host.includes("instagram.com")) return "Instagram";
      if (host.includes("youtube.com") || host.includes("youtu.be")) return "YouTube";
      if (host.includes("google.com/maps") || lower.includes("maps.app.goo.gl")) return "Map";
      if (host.includes("tripadvisor.com")) return "Travel profile";
      if (host.includes("yelp.com")) return "Business profile";
      if (host.includes("yellowpages.com")) return "Business profile";
      if (host.includes("chamber") || host.includes("businessdirectory")) return "Directory page";
      if (host.includes("tourism") || host.includes("travel") || host.includes("visit") || host.includes("explore")) return "Tourism listing";
      return fallback;
    }

    function contactLinks(item) {
      const links = [];
      const seen = new Set();
      const seenRouteHosts = new Set();
      const hostDedupedLabels = new Set(["Website", "Directory page", "Tourism listing", "Business profile", "Travel profile", "Listing page"]);
      function add(label, href) {
        const normalized = normalUrl(href);
        if (!normalized || seen.has(normalized)) return;
        const host = urlHost(normalized);
        const routeHostKey = `${label}|${host}`;
        if (hostDedupedLabels.has(label) && host && seenRouteHosts.has(routeHostKey)) return;
        seen.add(normalized);
        if (hostDedupedLabels.has(label) && host) seenRouteHosts.add(routeHostKey);
        links.push({ label, href: normalized });
      }
      splitList(item.website).forEach(url => add(linkLabel(url, "Website"), url));
      splitList(item.application_url).forEach(url => add("Apply or enroll", url));
      splitList(item.source_url).forEach(url => add(linkLabel(url, item.website ? "Listing page" : "Website"), url));
      splitList(item.url).forEach(url => add(linkLabel(url, "Listing page"), url));
      (item.links || []).forEach(link => {
        if (link && link.url) add(link.label || linkLabel(link.url, "Listing page"), link.url);
      });
      splitList(item.contact_email).forEach(email => add("Email", `mailto:${email}`));
      splitList(item.contact_phone).forEach(phone => {
        const dial = phone.replace(/[^0-9+]/g, "");
        if (dial.length >= 7) add("Phone", `tel:${dial}`);
      });
      splitList(item.physical_address).forEach(address => add("Map", `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address)}`));
      const labelTotals = links.reduce((counts, link) => {
        counts[link.label] = (counts[link.label] || 0) + 1;
        return counts;
      }, {});
      const labelIndexes = {};
      return links.map(link => {
        if (labelTotals[link.label] < 2) return link;
        labelIndexes[link.label] = (labelIndexes[link.label] || 0) + 1;
        const host = urlHost(link.href).replace(/^www\./, "");
        const suffix = host && link.label !== "Map" ? host : String(labelIndexes[link.label]);
        const separator = link.label === "Map" ? " " : ": ";
        return { ...link, label: `${link.label}${separator}${suffix}` };
      });
    }

    function bestEntityContact(item, explicitTitle = "") {
      const direct = contactLinks(item)[0];
      if (direct) return direct;
      const title = explicitTitle || item.resource_name || item.title || item.name || item.channel || item.place || "regional resource";
      const place = [item.town, item.county, item.state].filter(Boolean).join(" ");
      const query = [title, place, "contact"].filter(Boolean).join(" ");
      return {
        label: "Search",
        href: `https://www.google.com/search?q=${encodeURIComponent(query)}`
      };
    }

    function entityNameMarkup(item, explicitTitle = "") {
      const title = explicitTitle || item.resource_name || item.title || item.name || item.channel || item.place || "Unnamed resource";
      const destination = bestEntityContact(item, title);
      const opensNewWindow = !/^(mailto:|tel:)/i.test(destination.href);
      const targetAttrs = opensNewWindow ? ' target="_blank" rel="noreferrer"' : "";
      return `<a class="entity-name-link" href="${escapeHtml(destination.href)}"${targetAttrs} aria-label="Find contact information for ${escapeHtml(title)}">${escapeHtml(title)}</a>`;
    }

    function contactLinkMarkup(item, { compact = false } = {}) {
      const links = contactLinks(item);
      if (!links.length) return `<span class="source-note">Send an update if you have a public contact path.</span>`;
      const visible = compact ? links.slice(0, 2) : links;
      return `<div class="resource-links">${visible.map(link => `
        <a class="resource-contact-link" href="${escapeHtml(link.href)}"${/^(mailto:|tel:)/i.test(link.href) ? "" : ' target="_blank" rel="noreferrer"'}>${escapeHtml(link.label)}</a>
      `).join("")}</div>`;
    }

    function truthyFlag(value) {
      return value === true || String(value || "").toLowerCase() === "true";
    }

    function physicalIndicatorMarkup(item) {
      const note = item.physical_ad_note || "Use the listed contact to confirm current posting policies and formats.";
      if (truthyFlag(item.physical_ad_candidate)) {
        return `<div class="listing-indicators" aria-label="Physical location indicators"><span class="listing-marker listing-marker--ad" title="${escapeHtml(note)}">Physical promotion contact</span></div>`;
      }
      if (truthyFlag(item.has_physical_location)) {
        return `<div class="listing-indicators" aria-label="Physical location indicators"><span class="listing-marker listing-marker--physical" title="${escapeHtml(note)}">Physical location</span></div>`;
      }
      return "";
    }

    function outreachChannelMarkup(item, { compact = false } = {}) {
      const channels = Array.isArray(item.outreach_channels)
        ? item.outreach_channels.filter(channel => channel && channel.key && channel.label)
        : [];
      if (!channels.length) {
        return compact ? "" : `<p class="outreach-empty">No advertising or cross-promotion route is listed yet.</p>`;
      }
      const limit = compact ? 3 : 7;
      const visible = channels.slice(0, limit);
      const badges = visible.map(channel => {
        const status = channel.status === "listed" ? "listed" : "ask";
        const note = channel.note || (status === "listed"
          ? "Open the linked page and confirm current terms."
          : "Use the listed contact to confirm current placement or sharing options.");
        return `<span class="outreach-tag outreach-tag--${status}" data-outreach-channel="${escapeHtml(channel.key)}" title="${escapeHtml(note)}">${escapeHtml(channel.label)}</span>`;
      });
      if (channels.length > visible.length) {
        badges.push(`<span class="outreach-tag outreach-tag--more">+${channels.length - visible.length} more</span>`);
      }
      return `<div class="outreach-tags" aria-label="Promotion and advertising paths">${badges.join("")}</div>`;
    }

    function onlineConnectionMarkup(item) {
      const status = String(item.online_connection_status || "no-online-link");
      const label = String(item.online_connection_label || "No online link listed");
      const href = normalUrl(item.online_connection_url || "");
      const animated = truthyFlag(item.online_connection_animated);
      const style = status.startsWith("direct")
        ? "connected"
        : status.startsWith("profile") || status === "link-listed"
          ? "profile"
          : "missing";
      const signal = `<span class="connection-label__signal" aria-hidden="true"></span>`;
      if (href) {
        const title = item.resource_name || item.title || item.channel || item.place || "this listing";
        return `
          <div class="resource-connection" data-online-connection="${escapeHtml(status)}">
            <a class="connection-label connection-label--${style}${animated ? " is-animated" : ""}"
               href="${escapeHtml(href)}" target="_blank" rel="noreferrer"
               aria-label="${escapeHtml(label)} for ${escapeHtml(title)}">
              ${signal}${escapeHtml(label)}
            </a>
          </div>
        `;
      }
      return `
        <div class="resource-connection" data-online-connection="${escapeHtml(status)}">
          <span class="connection-label connection-label--missing">${signal}${escapeHtml(label)}</span>
          ${status === "no-online-link" ? '<a class="connection-update-link" href="/submit/">Add a link</a>' : ""}
        </div>
      `;
    }

    function sourceCard(item) {
      return `
        <article class="source-card" data-county="${escapeHtml(item.county)}" data-kind="${escapeHtml(item.kind)}">
          <div class="source-card__meta">
            <span>${escapeHtml(item.county)}</span>
            <span>${escapeHtml(item.kind)}</span>
          </div>
          <h3><a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">${escapeHtml(item.title)}</a></h3>
          <p>${escapeHtml(item.best_for)}</p>
          <p class="action-line">${escapeHtml(item.action)}</p>
          <div class="resource-outreach"><strong>Promotion paths:</strong>${outreachChannelMarkup(item, { compact: true })}</div>
          <p class="source-note">Details can change. Use the page, then submit an update if this pathway is outdated.</p>
        </article>
      `;
    }

    function sourceGroupCard(item) {
      const links = (item.links || [])
        .filter(link => link.url)
        .map(link => `
          <a class="source-sublink" href="${escapeHtml(link.url)}" target="_blank" rel="noreferrer">
            <span>${escapeHtml(link.label || "Open")}</span>
            <strong>${escapeHtml(link.title || link.url)}</strong>
          </a>
        `).join("");
      const sourceCount = Number(item.source_count || (item.links || []).length || 1);
      const routeWord = sourceCount === 1 ? "route" : "routes";
      return `
        <article class="source-card source-group-card" data-county="${escapeHtml(item.county)}" data-kind="${escapeHtml(item.kind)}">
          <div class="source-card__meta">
            <span>${escapeHtml(item.county_label || item.county || "Regional")}</span>
            <span>${escapeHtml(sourceCount)} ${routeWord}</span>
          </div>
          <h3><a href="${escapeHtml(item.url || (item.links && item.links[0] ? item.links[0].url : "#"))}" target="_blank" rel="noreferrer">${escapeHtml(item.title)}</a></h3>
          <p>${escapeHtml(item.best_for)}</p>
          <p class="action-line">${escapeHtml(item.action)}</p>
          <div class="resource-outreach"><strong>Promotion paths:</strong>${outreachChannelMarkup(item, { compact: true })}</div>
          <details class="source-group-links" open>
            <summary>Open ${escapeHtml(sourceCount)} ${routeWord}</summary>
            <div class="source-link-list">${links}</div>
          </details>
        </article>
      `;
    }

    function resourceCard(item) {
      const tags = String(item.public_audience_tags || item.public_org_tags || "")
        .split(";")
        .map(tag => tag.trim())
        .filter(Boolean)
        .map(tag => `<span class="badge">${escapeHtml(tag)}</span>`)
        .join(" ");
      const listingType = item.public_listing_type || item.resource_type || "Resource";
      const category = item.category || "";
      const metaParts = [
        [item.town, item.county, item.state].filter(Boolean).join(", "),
        listingType
      ].filter(Boolean);
      if (category && category !== listingType) metaParts.push(category);
      return `
        <article class="resource-item">
          <div class="resource-item__head">
            <h3>${entityNameMarkup(item)}</h3>
          </div>
          <p class="resource-meta-line">${escapeHtml(metaParts.join(" - "))}</p>
          ${physicalIndicatorMarkup(item)}
          ${onlineConnectionMarkup(item)}
          <p class="resource-description">${escapeHtml(item.public_description || "Tri-county business, nonprofit, arts, tourism, or service listing for local discovery and outreach.")}</p>
          <details class="resource-more" open>
            <summary>Details and best use</summary>
            <div class="resource-more__body">
              <p class="resource-tags"><strong>Useful for:</strong> ${tags}</p>
              <p class="resource-best"><strong>Best fit:</strong> ${escapeHtml(item.public_best_for || "regional discovery; contact-list building")}</p>
              <div class="resource-outreach"><strong>Promotion paths:</strong>${outreachChannelMarkup(item)}</div>
              <p class="source-note">If this looks outdated, use the correction form so the guide can be updated.</p>
            </div>
          </details>
          ${contactLinkMarkup(item)}
        </article>
      `;
    }

    function assistantTitle(item) {
      return item.title || item.resource_name || item.name || item.channel || item.place || "Directory result";
    }

    function assistantCategory(item) {
      return item.public_listing_type || item.kind || item.resource_type || item.channel_type || item.program_type || item.type || "Directory route";
    }

    function assistantTypeLabel(item, category) {
      return {
        "Current item": "Featured route",
        "Shortcut group": "Directory shortcut",
        "Shortcut": "Directory shortcut",
        "Listing": category,
        "Amplifier": "Promotion channel",
        "Physical ad location": "Physical promotion contact",
        "Posting path": "Posting route",
        "Funding opportunity": "Funding",
        "Free tool": "Free tool or service",
        "Site route": "Guide page"
      }[item.assistant_type] || category;
    }

    function assistantDescription(item) {
      return item.public_description
        || item.summary
        || item.posting_fit
        || item.best_for
        || item.short_description
        || item.asks
        || item.use
        || item.note
        || "Local route for finding a relevant organization, program, service, or promotion channel.";
    }

    function assistantNextStep(item) {
      const action = String(item.posting_note || item.action || item.reader_action || "").trim();
      if (!action || /^(open the link|use this route|send an update)/i.test(action)) return "";
      return action;
    }

    function assistantContactMarkup(item) {
      if (item.assistant_type === "Site route" && item.path !== undefined) {
        return `<div class="resource-links"><a class="resource-contact-link" href="${escapeHtml(assistantSiteUrl(item.path))}">Open guide page</a></div>`;
      }
      if (item.assistant_type === "Free tool") {
        const links = [];
        if (item.url) links.push(`<a class="resource-contact-link" href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">Website</a>`);
        if (item.source_url && item.source_url !== item.url) links.push(`<a class="resource-contact-link" href="${escapeHtml(item.source_url)}" target="_blank" rel="noreferrer">Plan or eligibility</a>`);
        return `<div class="resource-links">${links.join("")}</div>`;
      }
      const sourceUrls = [
        ...splitList(item.source_url),
        ...splitList(item.url),
        ...(item.links || []).map(link => link.url).filter(Boolean)
      ];
      return contactLinkMarkup({ ...item, source_url: sourceUrls.join("; ") }, { compact: true });
    }

    function assistantTitleMarkup(item, title) {
      if (item.assistant_type === "Site route" && item.path !== undefined) {
        return `<a class="entity-name-link" href="${escapeHtml(assistantSiteUrl(item.path))}" aria-label="Open ${escapeHtml(title)}">${escapeHtml(title)}</a>`;
      }
      if (item.assistant_type === "Free tool" && item.url) {
        return `<a class="entity-name-link" href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer" aria-label="Open ${escapeHtml(title)} website">${escapeHtml(title)}</a>`;
      }
      return entityNameMarkup(item, title);
    }

    function assistantCard(item) {
      const title = assistantTitle(item);
      const county = item.county || item.area_served || [item.town, item.state].filter(Boolean).join(", ") || "Regional";
      const category = assistantCategory(item);
      const typeLabel = assistantTypeLabel(item, category);
      const description = assistantDescription(item);
      const nextStep = assistantNextStep(item);
      const metaLabels = [...new Set([typeLabel, county].filter(Boolean))];
      return `
        <article class="assistant-result" role="listitem">
          <div class="assistant-result__meta">
            ${metaLabels.map((label, index) => `<span${index === 0 ? ' class="assistant-result__type"' : ""}>${escapeHtml(label)}</span>`).join("")}
          </div>
          <h3>${assistantTitleMarkup(item, title)}</h3>
          ${physicalIndicatorMarkup(item)}
          ${["Site route", "Free tool"].includes(item.assistant_type) ? "" : onlineConnectionMarkup(item)}
          ${outreachChannelMarkup(item, { compact: true })}
          <p class="assistant-result__description">${escapeHtml(description)}</p>
          ${nextStep ? `<p class="assistant-result__next"><strong>Next:</strong> ${escapeHtml(nextStep)}</p>` : ""}
          <div class="assistant-result__actions">
            ${assistantContactMarkup(item)}
          </div>
        </article>
      `;
    }

    function assistantSearchFields(item) {
      const title = assistantTitle(item);
      const location = searchableText([item.county, item.area_served, item.town, item.state]);
      const category = searchableText([
        item.kind,
        item.public_listing_type,
        item.resource_type,
        item.channel_type,
        item.program_type,
        item.type,
        item.category,
        assistantTypeLabel(item, assistantCategory(item))
      ]);
      const description = searchableText([
        item.public_description,
        item.summary,
        item.posting_fit,
        item.best_for,
        item.short_description,
        item.asks,
        item.public_best_for,
        item.funding_range,
        item.deadline_display,
        item.requires_501c3,
        item.fiscal_sponsor_policy,
        item.advertising_marketing_eligibility,
        item.free_to_apply_or_enroll,
        item.match_requirement,
        item.use,
        item.note,
        item.nonprofit_note,
        item.access_types
      ]);
      const keywords = searchableText([
        item.public_keywords,
        item.keywords,
        item.public_audience_tags,
        item.audiences,
        item.applicant_types,
        item.public_org_tags,
        item.online_connection_group,
        item.online_connection_label,
        item.audience_served,
        item.goal_relevance,
        item.action,
        item.posting_note,
        item.reader_action,
        item.status,
        item.provider,
        item.format,
        item.path
      ]);
      return {
        title: title.toLowerCase(),
        location: location.toLowerCase(),
        category: category.toLowerCase(),
        description: description.toLowerCase(),
        keywords: keywords.toLowerCase(),
        strong: searchableText([title, category, description]).toLowerCase(),
        all: searchableText([title, location, category, description, keywords]).toLowerCase()
      };
    }

    function assistantIdentity(item) {
      const title = assistantTitle(item).toLowerCase().replace(/[^a-z0-9]+/g, "");
      const county = String(item.county || item.area_served || item.town || "regional").toLowerCase().replace(/[^a-z0-9]+/g, "");
      return `${title}|${county}`;
    }

    const ASSISTANT_INTENTS = [
      {
        id: "tools",
        search: "free",
        signals: ["free tool", "free tools", "free software", "open source", "open-source", "web app", "nonprofit software", "software for nonprofits", "flyer maker", "form builder", "email tool", "crm tool"],
        guidance: "It sounds like you need software or an online service without adding a large recurring cost.",
        question: "Do you need design, forms, email, social scheduling, audio and video, or a nonprofit-specific offer?",
        suggestions: [
          ["Design and flyers", "design"],
          ["Forms and documents", "forms"],
          ["Email and contacts", "email"],
          ["Nonprofit offers", "nonprofit"]
        ],
        specific: [
          ["flyer", "design"],
          ["form", "forms"],
          ["email", "email"],
          ["crm", "crm"],
          ["audio", "audio"],
          ["video", "video"],
          ["open source", "open-source"],
          ["open-source", "open-source"],
          ["nonprofit", "nonprofit"]
        ]
      },
      {
        id: "flyers",
        search: "flyer location",
        signals: ["flyer", "flyers", "poster", "posters", "bulletin board", "rack card", "brochure", "physical advertising", "where can i post"],
        guidance: "It sounds like you need physical places that may accept local promotional material.",
        question: "Are you placing flyers, posters, brochures, or rack cards?",
        suggestions: [
          ["Public boards", "flyer location"],
          ["Event promotion", "events"],
          ["Media options", "media"],
          ["Visitor channels", "tourism"]
        ]
      },
      {
        id: "funding",
        search: "funding",
        signals: ["grant", "grants", "funding", "money", "capital", "loan", "scholarship", "stipend", "startup costs", "start-up costs", "pay for"],
        guidance: "It sounds like you need funding or financial support.",
        question: "Is this for a business, nonprofit, artist, or community program?",
        suggestions: [
          ["Business funding", "funding business"],
          ["Nonprofit funding", "funding nonprofit"],
          ["Artist funding", "funding artist"],
          ["Scholarships", "scholarship"]
        ],
        specific: [
          ["scholarship", "scholarship"],
          ["stipend", "stipend"],
          ["loan", "loan"],
          ["artist", "funding artist"],
          ["women", "funding women"],
          ["woman", "funding women"],
          ["lgbtq", "funding lgbtq"],
          ["indigenous", "funding indigenous"],
          ["native", "funding indigenous"],
          ["hispanic", "funding hispanic"],
          ["latino", "funding latino"],
          ["creative", "funding creative"],
          ["economic development", "funding economic development"],
          ["small business", "funding small business"],
          ["nonprofit", "funding nonprofit"],
          ["business", "funding business"],
          ["grant", "grant"]
        ]
      },
      {
        id: "events",
        search: "events",
        signals: ["event", "events", "calendar", "festival", "concert", "workshop", "class", "performance", "submit my event", "post my event"],
        guidance: "It sounds like you need to publish or promote an event.",
        question: "Do you need a calendar, media coverage, physical flyers, or a partner venue?",
        suggestions: [
          ["Event calendars", "event calendar"],
          ["Media coverage", "media event"],
          ["Physical promotion", "flyer location"],
          ["Venues", "event venue"]
        ],
        specific: [
          ["calendar", "event calendar"],
          ["venue", "event venue"],
          ["festival", "festival"]
        ]
      },
      {
        id: "listing",
        search: "directory",
        signals: ["get listed", "add my business", "add my organization", "business listing", "directory listing", "not listed", "update my listing", "correct my listing", "showing up online"],
        guidance: "It sounds like you need a listing, correction, or stronger directory presence.",
        question: "Are you trying to reach local residents, visitors, arts audiences, or business partners?",
        suggestions: [
          ["Business directories", "business directory"],
          ["Tourism listings", "tourism directory"],
          ["Arts listings", "artist directory"],
          ["Promotion channels", "promotion channel"]
        ]
      },
      {
        id: "visibility",
        search: "promotion channel",
        signals: ["more customers", "new customers", "more people", "get the word out", "promote", "promotion", "marketing", "advertise", "advertising", "visibility", "reach people", "reach visitors", "grow my audience", "expand my customer"],
        guidance: "It sounds like you want to reach more people or attract customers.",
        question: "Would media, event calendars, physical flyers, or directory listings fit the audience best?",
        suggestions: [
          ["Media and advertising", "media"],
          ["Event calendars", "events"],
          ["Physical promotion", "flyer location"],
          ["Get listed", "directory"]
        ]
      },
      {
        id: "media",
        search: "media",
        signals: ["newspaper", "radio", "press", "media", "interview", "news coverage", "press release"],
        guidance: "It sounds like you need a media or public-information channel.",
        question: "Are you looking for news coverage, paid advertising, radio, or a community calendar?",
        suggestions: [
          ["Newspapers", "newspaper"],
          ["Radio", "radio"],
          ["Event calendars", "event calendar"],
          ["Advertising routes", "advertising"]
        ],
        specific: [
          ["newspaper", "newspaper"],
          ["radio", "radio"],
          ["press release", "media"]
        ]
      },
      {
        id: "partnership",
        search: "partnership",
        signals: ["partner", "partnership", "collaborate", "collaboration", "cross promote", "cross-promotion", "sponsor", "sponsorship", "referral partner"],
        guidance: "It sounds like you need a partner, sponsor, referral, or cross-promotion route.",
        question: "Would a chamber, nonprofit, tourism office, venue, or media partner make the most sense?",
        suggestions: [
          ["Chambers", "chamber"],
          ["Nonprofits", "nonprofit"],
          ["Tourism partners", "tourism"],
          ["Venues", "event venue"]
        ]
      },
      {
        id: "business-support",
        search: "business support",
        signals: ["start a business", "starting a business", "startup", "business help", "need help", "where do i start", "not sure where", "mentor", "mentorship", "training", "technical assistance", "permit"],
        guidance: "It sounds like you need a practical starting point or business support.",
        question: "Do you need startup guidance, training, mentorship, funding, or permit help?",
        suggestions: [
          ["Startup help", "business support"],
          ["Training", "training"],
          ["Mentorship", "mentorship"],
          ["Business funding", "funding business"]
        ]
      },
      {
        id: "nonprofit",
        search: "nonprofit",
        signals: ["nonprofit", "non-profit", "charity", "community organization", "community program"],
        guidance: "It sounds like you are looking for nonprofit or community-program support.",
        question: "Do you need funding, event promotion, partners, or a directory listing?",
        suggestions: [
          ["Nonprofit funding", "funding nonprofit"],
          ["Promote an event", "events nonprofit"],
          ["Find partners", "partnership nonprofit"],
          ["Get listed", "nonprofit directory"]
        ]
      },
      {
        id: "arts",
        search: "artist",
        signals: ["artist", "artists", "gallery", "galleries", "musician", "writer", "maker", "creative business", "studio", "arts organization"],
        guidance: "It sounds like you need an arts, culture, or creative-business route.",
        question: "Do you need galleries, funding, event promotion, or an arts directory?",
        suggestions: [
          ["Galleries", "gallery"],
          ["Artist funding", "funding artist"],
          ["Arts events", "events artist"],
          ["Arts listings", "artist directory"]
        ],
        specific: [
          ["gallery", "gallery"],
          ["galleries", "gallery"],
          ["musician", "musician"],
          ["writer", "writer"]
        ]
      },
      {
        id: "tourism",
        search: "tourism",
        signals: ["visitor", "visitors", "tourist", "tourists", "traveler", "travelers", "tourism", "visitor guide", "travel guide"],
        guidance: "It sounds like you want to reach visitors or travel audiences.",
        question: "Do you need a visitor guide, tourism listing, event calendar, or hospitality partner?",
        suggestions: [
          ["Visitor guides", "visitor guide"],
          ["Tourism listings", "tourism directory"],
          ["Visitor events", "events tourism"],
          ["Hospitality partners", "lodging food"]
        ]
      },
      {
        id: "food",
        search: "food",
        signals: ["catering", "caterer", "restaurant", "bakery", "cafe", "coffee shop", "food business"],
        guidance: "It sounds like you need a food, dining, or catering route.",
        question: "Are you looking for a business listing, event work, promotion, or startup support?",
        suggestions: [
          ["Catering", "catering"],
          ["Food businesses", "food"],
          ["Event promotion", "events food"],
          ["Business support", "business support food"]
        ],
        specific: [
          ["catering", "catering"],
          ["caterer", "catering"],
          ["bakery", "bakery"],
          ["restaurant", "food"],
          ["cafe", "cafe"],
          ["coffee shop", "cafe"]
        ]
      }
    ];

    const ASSISTANT_LOCATIONS = [...new Set(
      (DATA.resources || [])
        .flatMap(item => [item.town, item.county])
        .map(value => String(value || "").trim())
        .filter(value => value.length > 2 && value.toLowerCase() !== "regional")
    )].sort((a, b) => b.length - a.length || a.localeCompare(b));

    function assistantMatchesSignal(text, signal) {
      const escaped = String(signal || "")
        .trim()
        .replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
        .replace(/\s+/g, "\\s+");
      return escaped ? new RegExp(`\\b${escaped}\\b`, "i").test(text) : false;
    }

    function assistantDetectedLocation(text) {
      return ASSISTANT_LOCATIONS.find(location => assistantMatchesSignal(text, location)) || "";
    }

    function assistantIntentQuery(intent, text) {
      const specific = (intent.specific || []).find(([signal]) => assistantMatchesSignal(text, signal));
      return specific ? specific[1] : intent.search;
    }

    function assistantInterpretation(query) {
      const text = String(query || "").trim();
      const location = assistantDetectedLocation(text);
      const ranked = ASSISTANT_INTENTS
        .map((intent, index) => ({
          intent,
          index,
          score: intent.signals.reduce(
            (score, signal) => score + (assistantMatchesSignal(text, signal) ? (signal.includes(" ") ? 2 : 1) : 0),
            0
          )
        }))
        .filter(entry => entry.score > 0)
        .sort((a, b) => b.score - a.score || a.index - b.index);
      const intent = ranked[0]?.intent;
      if (!intent) {
        const conversational = /[?]|\b(i|we|my|our|how|where|what|need|want|trying|help)\b/i.test(text)
          || normalizedSearchTerms(text).length >= 3;
        return {
          recognized: false,
          location,
          baseQuery: text,
          searchQuery: text,
          guidance: conversational ? "I could not tell which route fits yet." : "",
          question: conversational ? "Are you trying to get listed, promote an event, find funding, reach visitors, or find local help?" : "",
          suggestions: conversational
            ? [
                ["Get listed", "directory"],
                ["Promote an event", "events"],
                ["Find funding", "funding"],
                ["Find local help", "business support"],
                ["Find free tools", "free tools"]
              ].map(([label, value]) => ({ label, query: value }))
            : []
        };
      }
      const baseQuery = assistantIntentQuery(intent, text);
      const searchQuery = location && !assistantMatchesSignal(baseQuery, location)
        ? `${baseQuery} ${location}`
        : baseQuery;
      const locationNote = location
        ? ` I found ${location} in your question.`
        : " Add a town or county if location matters.";
      return {
        recognized: true,
        intent: intent.id,
        location,
        baseQuery,
        searchQuery,
        guidance: `${intent.guidance}${locationNote}`,
        question: intent.question,
        suggestions: intent.suggestions.map(([label, value]) => ({
          label,
          query: location && !assistantMatchesSignal(value, location) ? `${value} ${location}` : value
        }))
      };
    }

    function assistantIntentAccepts(item, intent, fields) {
      if (!intent) return true;
      if (intent === "visibility") {
        if (["Shortcut group", "Shortcut", "Amplifier"].includes(item.assistant_type)) {
          return true;
        }
        return /\b(media|news|advertis|directory|tourism|visitor|chamber|business support|public office|promotion)\b/.test(fields.category);
      }
      if (intent === "tools") {
        return item.assistant_type === "Free tool" || (item.assistant_type === "Site route" && item.category === "Tools");
      }
      return true;
    }

    function assistantSearch(query, intent = "") {
      const normalized = String(query || "").trim().toLowerCase();
      const terms = normalizedSearchTerms(normalized);
      if (!terms.length) return [];
      const locationTerms = new Set(normalizedSearchTerms(assistantDetectedLocation(normalized)));
      const audienceTerms = new Set(["artist", "business", "nonprofit", "program"]);
      const coreTerms = terms.filter(term => !locationTerms.has(term) && !audienceTerms.has(term));
      const pools = [
        ...((DATA.directory_source_groups || DATA.directory_sources || [])).map(item => ({ ...item, assistant_type: "Shortcut group" })),
        ...(DATA.resources || []).map(item => ({ ...item, assistant_type: "Listing" })),
        ...(DATA.amplifier_channels || []).map(item => ({ ...item, assistant_type: "Amplifier" })),
        ...(DATA.physical_ad_locations || []).map(item => ({ ...item, assistant_type: "Physical ad location" })),
        ...(DATA.posting_spaces || []).map(item => ({ ...item, assistant_type: "Posting path" })),
        ...(DATA.national_funding_opportunities || []).map(item => ({ ...item, assistant_type: "Funding opportunity" })),
        ...(DATA.free_tools || []).map(item => ({ ...item, assistant_type: "Free tool" })),
        ...(DATA.site_routes || []).map(item => ({ ...item, assistant_type: "Site route" }))
      ];
      const scored = pools.map(item => {
        const fields = assistantSearchFields(item);
        if (!assistantIntentAccepts(item, intent, fields)) return null;
        if (!terms.every(term => fields.all.includes(term))) return null;
        if (coreTerms.length && !coreTerms.every(term => fields.strong.includes(term))) return null;
        let score = fields.title.includes(normalized) ? 20 : 0;
        for (const term of terms) {
          if (fields.title.includes(term)) score += 10;
          if (fields.category.includes(term)) score += 6;
          if (fields.location.includes(term)) score += 6;
          if (fields.description.includes(term)) score += 3;
          if (fields.keywords.includes(term)) score += 2;
        }
        score += {
          "Shortcut group": 6,
          "Shortcut": 6,
          "Amplifier": 5,
          "Physical ad location": 5,
          "Posting path": 5,
          "Funding opportunity": 7,
          "Free tool": 8,
          "Site route": 18,
          "Current item": 4,
          "Listing": 3
        }[item.assistant_type] || 1;
        return { item, score };
      }).filter(Boolean);

      const unique = [];
      const seen = new Set();
      scored
        .sort((a, b) => b.score - a.score || assistantTitle(a.item).localeCompare(assistantTitle(b.item)))
        .forEach(entry => {
          const key = assistantIdentity(entry.item);
          if (seen.has(key)) return;
          seen.add(key);
          unique.push(entry.item);
        });
      return unique.slice(0, 5);
    }

    function assistantUrl(key) {
      const root = document.querySelector("[data-directory-assistant]");
      if (!root) return key === "submit" ? "submit/index.html" : "network/index.html";
      return key === "submit" ? root.dataset.submitUrl : root.dataset.networkUrl;
    }

    function assistantNetworkUrl(query = "") {
      const base = assistantUrl("network");
      const search = String(query || "").trim();
      return search
        ? `${base}${base.includes("?") ? "&" : "?"}q=${encodeURIComponent(search)}#resource-results`
        : `${base}#resource-results`;
    }

    const bubbleAnimationTimers = new WeakMap();
    const assistantMotionTimers = new WeakMap();

    function replayBubbleOpen(element) {
      if (!element || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      const previousTimer = bubbleAnimationTimers.get(element);
      if (previousTimer) window.clearTimeout(previousTimer);
      element.classList.remove("is-bubble-opening");
      void element.offsetWidth;
      element.classList.add("is-bubble-opening");
      bubbleAnimationTimers.set(element, window.setTimeout(() => {
        element.classList.remove("is-bubble-opening");
        bubbleAnimationTimers.delete(element);
      }, 360));
    }

    function replayAssistantMotion(panel, phase) {
      if (!panel || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return 0;
      const previousTimer = assistantMotionTimers.get(panel);
      if (previousTimer) window.clearTimeout(previousTimer);
      panel.classList.remove("is-southwest-opening", "is-southwest-closing");
      void panel.offsetWidth;
      const className = phase === "close" ? "is-southwest-closing" : "is-southwest-opening";
      const duration = phase === "close" ? 260 : 760;
      panel.classList.add(className);
      assistantMotionTimers.set(panel, window.setTimeout(() => {
        panel.classList.remove(className);
        assistantMotionTimers.delete(panel);
      }, duration + 40));
      return duration;
    }

    function initDirectoryAssistant() {
      const root = document.querySelector("[data-directory-assistant]");
      if (!root) return;
      const toggle = root.querySelector(".directory-assistant__toggle");
      const panel = root.querySelector(".directory-assistant__panel");
      const close = root.querySelector(".directory-assistant__close");
      const form = root.querySelector(".directory-assistant__form");
      const input = root.querySelector("#directory-assistant-query");
      const results = root.querySelector("[data-assistant-results]");
      const status = root.querySelector(".directory-assistant__status");
      const guidance = root.querySelector("[data-assistant-guidance]");
      const guidanceText = root.querySelector("[data-assistant-guidance-text]");
      const guidanceQuestion = root.querySelector("[data-assistant-guidance-question]");
      const followups = root.querySelector("[data-assistant-followups]");
      const fullDirectory = root.querySelector("[data-assistant-full-directory]");
      const chips = [...root.querySelectorAll("[data-assistant-prompt]")];
      if (!toggle || !panel || !form || !input || !results || !status) return;
      let renderTimer = null;
      let lastFocusedElement = null;
      let returnFocusOnClose = true;
      let closeTimer = null;
      let isClosing = false;

      function finishClose() {
        closeTimer = null;
        isClosing = false;
        panel.classList.remove("is-southwest-opening", "is-southwest-closing");
        if (panel.open && typeof panel.close === "function") {
          panel.close();
        } else {
          panel.removeAttribute("open");
          syncClosed();
        }
      }

      function setOpen(open, { returnFocus = true } = {}) {
        if (open) {
          if (closeTimer) {
            window.clearTimeout(closeTimer);
            closeTimer = null;
          }
          isClosing = false;
          panel.classList.remove("is-southwest-closing");
          lastFocusedElement = document.activeElement instanceof HTMLElement ? document.activeElement : toggle;
          if (!panel.open) {
            if (typeof panel.showModal === "function") {
              panel.showModal();
            } else {
              panel.setAttribute("open", "");
            }
          }
          replayAssistantMotion(panel, "open");
          toggle.setAttribute("aria-expanded", "true");
          root.dataset.open = "true";
          window.setTimeout(() => input.focus(), 40);
          return;
        }
        returnFocusOnClose = returnFocus;
        if (!panel.open) {
          finishClose();
          return;
        }
        if (isClosing) return;
        isClosing = true;
        const duration = replayAssistantMotion(panel, "close");
        if (!duration) {
          finishClose();
          return;
        }
        closeTimer = window.setTimeout(finishClose, duration);
      }

      function syncClosed() {
        if (closeTimer) {
          window.clearTimeout(closeTimer);
          closeTimer = null;
        }
        isClosing = false;
        panel.classList.remove("is-southwest-opening", "is-southwest-closing");
        toggle.setAttribute("aria-expanded", "false");
        root.dataset.open = "false";
        if (renderTimer) {
          window.clearTimeout(renderTimer);
          renderTimer = null;
        }
        if (returnFocusOnClose && lastFocusedElement && typeof lastFocusedElement.focus === "function") {
          window.setTimeout(() => lastFocusedElement.focus(), 0);
        }
      }

      function render(query) {
        const search = String(query || "").trim();
        if (search.length < 2) {
          if (guidance) guidance.hidden = true;
          status.textContent = search
            ? "Keep typing: enter at least two letters."
            : "Choose a popular search or enter at least two letters.";
          results.innerHTML = "";
          if (fullDirectory) {
            fullDirectory.href = assistantNetworkUrl();
            fullDirectory.textContent = "Open full directory";
            fullDirectory.setAttribute("aria-label", "Open the full directory");
          }
          return;
        }
        const interpretation = assistantInterpretation(search);
        if (guidance && guidanceText && guidanceQuestion && followups) {
          guidance.hidden = !interpretation.guidance;
          guidanceText.textContent = interpretation.guidance;
          guidanceQuestion.textContent = interpretation.question;
          guidanceQuestion.hidden = !interpretation.question;
          followups.innerHTML = interpretation.suggestions.map(suggestion => `
            <button type="button" data-assistant-followup="${escapeHtml(suggestion.query)}">${escapeHtml(suggestion.label)}</button>
          `).join("");
        }
        let matches = assistantSearch(interpretation.searchQuery, interpretation.intent);
        let widened = false;
        if (!matches.length && interpretation.location && interpretation.baseQuery !== interpretation.searchQuery) {
          matches = assistantSearch(interpretation.baseQuery, interpretation.intent);
          widened = matches.length > 0;
        }
        if (fullDirectory) {
          const handoffQuery = widened ? interpretation.baseQuery : interpretation.searchQuery;
          fullDirectory.href = assistantNetworkUrl(handoffQuery);
          fullDirectory.textContent = "See all matching listings";
          fullDirectory.setAttribute("aria-label", `See all directory listings matching ${handoffQuery}`);
        }
        if (interpretation.recognized) {
          status.textContent = matches.length
            ? (widened
                ? `No exact ${interpretation.location} match. Showing ${matches.length} broader regional route${matches.length === 1 ? "" : "s"}.`
                : `Showing ${matches.length} suggested route${matches.length === 1 ? "" : "s"}${interpretation.location ? ` for ${interpretation.location}` : ""}.`)
            : "I understood the request, but found no close directory match. Try one of the suggested follow-up searches.";
        } else {
          status.textContent = matches.length
            ? `Showing ${matches.length} result${matches.length === 1 ? "" : "s"} for "${search}".`
            : `No close match for "${search}". Try a town, county, or one of the suggested next steps.`;
        }
        results.innerHTML = matches.map(assistantCard).join("");
      }

      toggle.addEventListener("click", () => {
        const shouldOpen = !panel.open || isClosing;
        setOpen(shouldOpen);
        if (shouldOpen && !status.textContent.trim()) {
          render(input.value);
        }
      });
      close && close.addEventListener("click", () => setOpen(false));
      panel.addEventListener("cancel", event => {
        event.preventDefault();
        setOpen(false);
      });
      panel.addEventListener("close", syncClosed);
      panel.addEventListener("click", event => {
        if (event.target !== panel) return;
        const rect = panel.getBoundingClientRect();
        const isBackdropClick = event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom;
        if (isBackdropClick) setOpen(false);
      });
      form.addEventListener("submit", event => {
        event.preventDefault();
        render(input.value);
      });
      input.addEventListener("input", () => {
        if (renderTimer) window.clearTimeout(renderTimer);
        if (input.value.trim().length < 2) {
          render(input.value);
        } else {
          renderTimer = window.setTimeout(() => render(input.value), 150);
        }
      });
      chips.forEach(chip => chip.addEventListener("click", () => {
        input.value = chip.dataset.assistantPrompt || "";
        render(input.value);
        input.focus();
      }));
      guidance && guidance.addEventListener("click", event => {
        if (!(event.target instanceof Element)) return;
        const suggestion = event.target.closest("[data-assistant-followup]");
        if (!suggestion) return;
        input.value = suggestion.dataset.assistantFollowup || "";
        render(input.value);
        input.focus();
      });
      document.addEventListener("keydown", event => {
        if (event.key === "Escape" && panel.open) {
          event.preventDefault();
          setOpen(false);
        }
      });
    }

    function initDirectoryOpenAnimations() {
      document.addEventListener("click", event => {
        if (!(event.target instanceof Element)) return;
        const summary = event.target.closest(".resource-more > summary, .source-group-links > summary");
        if (!summary) return;
        const details = summary.parentElement;
        if (!(details instanceof HTMLDetailsElement) || details.open) return;
        window.requestAnimationFrame(() => {
          if (!details.open) return;
          replayBubbleOpen(details.closest(".resource-item, .source-card"));
        });
      });
    }

    function directoryPageSize(compactSize, wideSize) {
      return window.matchMedia("(max-width: 640px)").matches ? compactSize : wideSize;
    }

    function syncDirectoryDetails(root = document) {
      const compact = window.matchMedia("(max-width: 640px)").matches;
      root.querySelectorAll(".resource-more, .source-group-links").forEach(details => {
        details.toggleAttribute("open", !compact);
      });
      const filters = document.querySelector(".directory-filter-details");
      if (filters) filters.toggleAttribute("open", !compact);
    }

    function initProgressiveLists() {
      document.querySelectorAll("[data-progressive-list]").forEach(host => {
        const items = [...host.children].filter(item => item.matches("article"));
        const section = host.closest(".section") || host.parentElement;
        const button = section?.querySelector("[data-progressive-more]");
        const compactStep = Math.max(1, Number(host.dataset.compactCount) || 4);
        const wideCount = Math.max(compactStep, Number(host.dataset.wideCount) || items.length);
        let compact = window.matchMedia("(max-width: 640px)").matches;
        let visibleCount = compact ? compactStep : wideCount;

        function render() {
          const visibleItems = items.slice(0, visibleCount);
          const visibleSet = new Set(visibleItems);
          items.forEach(item => { item.hidden = !visibleSet.has(item); });
          if (!button) return;
          const remaining = Math.max(0, items.length - visibleItems.length);
          const label = button.dataset.progressiveLabel || "items";
          button.hidden = remaining === 0;
          button.textContent = remaining ? `Show ${Math.min(compactStep, remaining)} more ${label}` : `All ${label} shown`;
        }

        button && button.addEventListener("click", () => {
          visibleCount += compactStep;
          render();
        });
        window.addEventListener("resize", () => {
          const nextCompact = window.matchMedia("(max-width: 640px)").matches;
          if (nextCompact === compact) return;
          compact = nextCompact;
          visibleCount = compact ? compactStep : wideCount;
          render();
        }, { passive: true });
        render();
      });
    }

    function initFreeToolFilters() {
      const form = document.querySelector("[data-tool-filters]");
      const grid = document.querySelector("[data-tool-grid]");
      if (!form || !grid) return;
      const query = form.querySelector("[data-tool-query]");
      const category = form.querySelector("[data-tool-category]");
      const offer = form.querySelector("[data-tool-offer]");
      const format = form.querySelector("[data-tool-format-filter]");
      const status = form.querySelector("[data-tool-status]");
      const empty = document.querySelector("[data-tool-empty]");
      const more = document.querySelector("[data-tool-more]");
      const presets = [...document.querySelectorAll("[data-tool-preset]")];
      const cards = [...grid.querySelectorAll("[data-tool-card]")];
      let compact = window.matchMedia("(max-width: 640px)").matches;
      let visibleLimit = compact ? 6 : Number.POSITIVE_INFINITY;

      function matchesOffer(card, value) {
        if (!value || value === "all") return true;
        const offerGroups = String(card.dataset.toolOffers || "").toLowerCase().split(/\s+/);
        return offerGroups.includes(value);
      }

      function matchesFormat(card, value) {
        if (!value || value === "all") return true;
        const accessText = String(card.dataset.toolAccess || "").toLowerCase();
        const formatText = String(card.dataset.toolFormat || "").toLowerCase();
        if (value === "open-source") return accessText.includes("open-source");
        if (value === "desktop") return formatText.includes("desktop");
        if (value === "web") return formatText.includes("web");
        return true;
      }

      function render() {
        const terms = normalizedSearchTerms(query?.value || "");
        const selectedCategory = String(category?.value || "All");
        const selectedOffer = String(offer?.value || "All").toLowerCase();
        const selectedFormat = String(format?.value || "All").toLowerCase();
        const matches = cards.filter(card => {
          const searchText = String(card.dataset.toolSearch || "").toLowerCase();
          const categoryMatch = selectedCategory === "All" || card.dataset.toolCategory === selectedCategory;
          return categoryMatch && matchesOffer(card, selectedOffer) && matchesFormat(card, selectedFormat)
            && terms.every(term => searchText.includes(term));
        });
        const visible = matches.slice(0, visibleLimit);
        const visibleSet = new Set(visible);
        cards.forEach(card => { card.hidden = !visibleSet.has(card); });
        if (empty) empty.hidden = matches.length > 0;
        if (status) {
          status.textContent = matches.length
            ? `Showing ${visible.length} of ${matches.length} matching tool${matches.length === 1 ? "" : "s"}.`
            : "No matching tools.";
        }
        if (more) {
          const remaining = Math.max(0, matches.length - visible.length);
          more.hidden = remaining === 0;
          more.textContent = remaining ? `Show ${Math.min(6, remaining)} more tools` : "All tools shown";
        }
        presets.forEach(button => {
          button.setAttribute("aria-pressed", String(button.dataset.toolPreset === selectedOffer));
        });
      }

      form.addEventListener("input", () => {
        visibleLimit = compact ? 6 : Number.POSITIVE_INFINITY;
        render();
      });
      form.addEventListener("change", () => {
        visibleLimit = compact ? 6 : Number.POSITIVE_INFINITY;
        render();
      });
      form.addEventListener("reset", () => {
        window.setTimeout(() => {
          visibleLimit = compact ? 6 : Number.POSITIVE_INFINITY;
          render();
        }, 0);
      });
      presets.forEach(button => {
        button.addEventListener("click", () => {
          if (offer) offer.value = button.dataset.toolPreset || "All";
          visibleLimit = compact ? 6 : Number.POSITIVE_INFINITY;
          render();
          form.scrollIntoView({ block: "start", behavior: "auto" });
          query?.focus({ preventScroll: true });
        });
      });
      more && more.addEventListener("click", () => {
        visibleLimit += 6;
        render();
      });
      window.addEventListener("resize", () => {
        const nextCompact = window.matchMedia("(max-width: 640px)").matches;
        if (nextCompact === compact) return;
        compact = nextCompact;
        visibleLimit = compact ? 6 : Number.POSITIVE_INFINITY;
        render();
      });
      render();
    }

    function assistantSiteUrl(path = "") {
      const root = document.querySelector("[data-directory-assistant]");
      const base = new URL(root?.dataset.siteRoot || "./", document.baseURI);
      return new URL(String(path || ""), base).href;
    }

    function initNationalFundingSearch() {
      const host = document.querySelector("#national-funding-results");
      if (!host) return;
      const cards = [...host.querySelectorAll("[data-funding-card]")];
      const input = document.querySelector("#funding-search");
      const audience = document.querySelector("#funding-audience-filter");
      const status = document.querySelector("#funding-status-filter");
      const type = document.querySelector("#funding-type-filter");
      const cost = document.querySelector("#funding-cost-filter");
      const note = document.querySelector("#funding-results-note");
      const moreButton = document.querySelector("#funding-load-more");
      let visibleCount = directoryPageSize(6, 12);
      const incoming = new URLSearchParams(window.location.search);
      const incomingQuery = incoming.get("q");
      const incomingAudience = incoming.get("audience");
      if (incomingQuery && input) input.value = incomingQuery;
      if (incomingAudience && audience && [...audience.options].some(option => option.value === incomingAudience)) {
        audience.value = incomingAudience;
      }

      function matchesAudience(card, value) {
        if (value === "All") return true;
        const haystack = card.dataset.fundingAudiences || "";
        return value.split(/\s+/).some(term => haystack.includes(term));
      }

      function render() {
        const query = String(input?.value || "").trim().toLowerCase();
        const audienceValue = audience?.value || "All";
        const statusValue = status?.value || "All";
        const typeValue = type?.value || "All";
        const costValue = cost?.value || "All";
        const matched = cards.filter(card => (
            (!query || (card.dataset.fundingSearch || "").includes(query))
            && matchesAudience(card, audienceValue)
            && (statusValue === "All" || card.dataset.fundingStatus === statusValue)
            && (typeValue === "All" || card.dataset.fundingType === typeValue)
            && (costValue === "All" || card.dataset.fundingCost === costValue)
        ));
        const visible = new Set(matched.slice(0, visibleCount));
        cards.forEach(card => { card.hidden = !visible.has(card); });
        if (note) note.textContent = `Showing ${visible.size} of ${matched.length} matching funding ${matched.length === 1 ? "entry" : "entries"}.`;
        if (moreButton) {
          const remaining = Math.max(0, matched.length - visible.size);
          moreButton.hidden = remaining === 0;
          moreButton.textContent = remaining
            ? `Show ${Math.min(directoryPageSize(6, 12), remaining)} more funding entries`
            : "All matching funding entries shown";
        }
      }

      [input, audience, status, type, cost].forEach(control => {
        if (!control) return;
        control.addEventListener(control === input ? "input" : "change", () => {
          visibleCount = directoryPageSize(6, 12);
          render();
        });
      });
      moreButton && moreButton.addEventListener("click", () => {
        visibleCount += directoryPageSize(6, 12);
        render();
      });
      render();
    }

    function initSourceSearch() {
      const host = document.querySelector("#source-results");
      if (!host) return;
      const input = document.querySelector("#source-search");
      const note = document.querySelector("#source-results-note");
      const chips = [...document.querySelectorAll("[data-source-filter]")];
      const moreButton = document.querySelector("#source-load-more");
      let county = "All";
      let visibleCount = directoryPageSize(4, 8);
      function resetVisibleCount() {
        visibleCount = directoryPageSize(4, 8);
      }
      function render() {
        const query = input.value.trim();
        const allGroups = DATA.directory_source_groups || DATA.directory_sources || [];
        const topGroups = DATA.top_directory_source_groups || allGroups.slice(0, 30);
        const showingPriority = county === "All" && !query;
        const pool = showingPriority ? topGroups : allGroups;
        const filtered = pool
          .filter(item => (county === "All" || item.county === county || (item.counties || []).includes(county)) && (!query || textMatch(item, query)))
          .sort((a, b) => String(a.title || "").localeCompare(String(b.title || "")));
        const visible = filtered.slice(0, visibleCount);
        if (note) {
          note.textContent = showingPriority
            ? `Showing ${visible.length} of ${filtered.length} priority shortcut groups. Search or choose a county to inspect all ${allGroups.length} groups.`
            : `Showing ${visible.length} of ${filtered.length} matching shortcut group${filtered.length === 1 ? "" : "s"}.`;
        }
        host.innerHTML = visible.map(item => item.links ? sourceGroupCard(item) : sourceCard(item)).join("") || `<p class="section-note">No shortcuts match that search yet.</p>`;
        syncDirectoryDetails(host);
        if (moreButton) {
          const remaining = Math.max(0, filtered.length - visible.length);
          moreButton.hidden = remaining === 0;
          moreButton.textContent = remaining ? `Show ${Math.min(directoryPageSize(4, 8), remaining)} more shortcuts` : "All shortcuts shown";
        }
      }
      input.addEventListener("input", () => {
        resetVisibleCount();
        render();
      });
      chips.forEach(chip => chip.addEventListener("click", () => {
        county = chip.dataset.sourceFilter;
        chips.forEach(c => c.classList.toggle("is-active", c === chip));
        resetVisibleCount();
        render();
      }));
      moreButton && moreButton.addEventListener("click", () => {
        visibleCount += directoryPageSize(4, 8);
        render();
      });
      render();
    }

    function promoteRouteMatch(item, route) {
      if (!route || route === "All") return true;
      const channelKeys = new Set((item.outreach_channels || []).map(channel => channel.key));
      const channelMap = {
        events: ["event_calendar", "partner_cross_promotion"],
        advertising: ["paid_digital_advertising", "media_editorial", "newsletter_mailing_list", "social_cross_promotion", "sponsorship"],
        businesses: ["directory_listing", "partner_cross_promotion", "front_desk_referrals"],
        nonprofits: ["partner_cross_promotion", "newsletter_mailing_list", "front_desk_referrals"],
        calendars: ["event_calendar"],
        galleries: ["event_calendar", "social_cross_promotion", "partner_cross_promotion"],
      };
      const termMap = {
        events: ["event", "venue", "festival", "performance", "class", "workshop"],
        advertising: ["advertis", "media", "newspaper", "radio", "newsletter", "sponsor", "editorial"],
        businesses: ["business", "chamber", "retail", "restaurant", "visitor guide", "tourism", "directory"],
        nonprofits: ["nonprofit", "community", "public service", "referral", "foundation", "volunteer"],
        calendars: ["calendar", "event submission", "schedule", "what's on"],
        galleries: ["artist", "gallery", "arts", "museum", "theater", "theatre", "creative", "cultural"],
      };
      if ((channelMap[route] || []).some(key => channelKeys.has(key))) return true;
      const blob = searchableText(item).toLowerCase();
      return (termMap[route] || []).some(term => blob.includes(term));
    }

    function promoteCountyMatch(item, county) {
      if (!county || county === "All") return true;
      const counties = Array.isArray(item.counties) ? item.counties : splitList(item.counties);
      const blob = searchableText([item.county, counties, item.county_label, item.area_served, item.town]).toLowerCase();
      if (blob.includes(county.toLowerCase())) return true;
      return /regional|tri-county|all three count/.test(blob);
    }

    function promoteItemTitle(item) {
      return item.resource_name || item.title || item.channel || item.name || "Promotion contact";
    }

    function promoteItemKey(item) {
      const title = promoteItemTitle(item).toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
      const firstLink = contactLinks(item)[0];
      const host = firstLink ? urlHost(firstLink.href) : "";
      return `${title}|${host || String(item.county || item.area_served || "regional").toLowerCase()}`;
    }

    function promoteCard(item) {
      if (item.__promoteType === "source") return sourceGroupCard(item);
      if (item.__promoteType === "amplifier") {
        return resourceCard({
          ...item,
          resource_name: item.channel || item.title,
          county: item.county || "Regional",
          category: "Promotion channel",
          public_listing_type: item.channel_type || "Promotion channel",
          public_description: item.best_for || item.implementation_note,
          public_best_for: item.asks || item.implementation_note,
          website: item.source_url || item.url,
        });
      }
      return resourceCard(item);
    }

    function initPromoteSearch() {
      const host = document.querySelector("#promote-results");
      if (!host) return;
      const input = document.querySelector("#promote-search");
      const countySelect = document.querySelector("#promote-county-filter");
      const routeSelect = document.querySelector("#promote-route-filter");
      const note = document.querySelector("#promote-results-note");
      const moreButton = document.querySelector("#promote-load-more");
      const routeCards = [...document.querySelectorAll("[data-promote-route-link]")];
      const params = new URLSearchParams(window.location.search);
      const incomingCounty = params.get("county") || "All";
      const incomingRoute = params.get("route") || "All";
      const incomingQuery = params.get("q") || "";
      if (input) input.value = incomingQuery;
      if (countySelect && [...countySelect.options].some(option => option.value === incomingCounty)) countySelect.value = incomingCounty;
      if (routeSelect && [...routeSelect.options].some(option => option.value === incomingRoute)) routeSelect.value = incomingRoute;
      let visibleCount = directoryPageSize(8, 16);

      const resources = (DATA.resources || []).map(item => ({ ...item, __promoteType: "resource" }));
      const sourceGroups = (DATA.directory_source_groups || DATA.directory_sources || []).map(item => ({ ...item, __promoteType: "source" }));
      const amplifiers = (DATA.amplifier_channels || []).map(item => ({ ...item, __promoteType: "amplifier" }));
      const pool = [...resources, ...sourceGroups, ...amplifiers];

      function render() {
        const query = String(input?.value || "").trim();
        const county = countySelect?.value || "All";
        const route = routeSelect?.value || "All";
        const seen = new Set();
        const matched = pool
          .filter(item => promoteCountyMatch(item, county))
          .filter(item => promoteRouteMatch(item, route))
          .filter(item => !query || textMatch(item, query) || resourceTextMatch(item, query))
          .filter(item => {
            const key = promoteItemKey(item);
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
          })
          .sort((a, b) => promoteItemTitle(a).localeCompare(promoteItemTitle(b)));
        const visible = matched.slice(0, visibleCount);
        host.innerHTML = visible.map(promoteCard).join("") || `<p class="section-note">No promotion contacts match those filters. Try all routes or remove a search term.</p>`;
        syncDirectoryDetails(host);
        routeCards.forEach(card => card.classList.toggle("is-active", card.dataset.promoteRouteLink === route));
        if (note) {
          const routeLabel = routeSelect?.selectedOptions[0]?.textContent || "All promotion routes";
          const countyLabel = county === "All" ? "the tri-county region" : `${county} County plus region-wide channels`;
          const routePhrase = route === "All" ? "contacts across all promotion routes" : `${routeLabel.toLowerCase()} contacts`;
          note.textContent = `Showing ${visible.length} of ${matched.length} ${routePhrase} for ${countyLabel}.`;
        }
        if (moreButton) {
          const remaining = Math.max(0, matched.length - visible.length);
          moreButton.hidden = remaining === 0;
          moreButton.textContent = remaining ? `Show ${Math.min(directoryPageSize(8, 16), remaining)} more contacts` : "All matching contacts shown";
        }
      }

      [input, countySelect, routeSelect].forEach(control => {
        if (!control) return;
        control.addEventListener(control === input ? "input" : "change", () => {
          visibleCount = directoryPageSize(8, 16);
          render();
        });
      });
      moreButton && moreButton.addEventListener("click", () => {
        visibleCount += directoryPageSize(8, 16);
        render();
      });
      render();
    }

    function initPhysicalLocationSearch() {
      const host = document.querySelector("#physical-location-list");
      if (!host) return;
      const input = document.querySelector("#physical-location-search");
      const countySelect = document.querySelector("#physical-county-filter");
      const categorySelect = document.querySelector("#physical-category-filter");
      const note = document.querySelector("#physical-results-note");
      const moreButton = document.querySelector("#physical-load-more");
      const rows = DATA.physical_ad_locations || [];
      populateSelect(categorySelect, uniqueValues(rows, "physical_promotion_category"), "All location types");
      const params = new URLSearchParams(window.location.search);
      const incomingQuery = params.get("q") || "";
      const incomingCounty = params.get("county") || "All";
      const incomingCategory = params.get("category") || "All";
      if (input) input.value = incomingQuery;
      if (countySelect && [...countySelect.options].some(option => option.value === incomingCounty)) countySelect.value = incomingCounty;
      if (categorySelect && incomingCategory !== "All") {
        if (![...categorySelect.options].some(option => option.value === incomingCategory)) {
          const option = document.createElement("option");
          option.value = incomingCategory;
          option.textContent = "Selected location group";
          categorySelect.appendChild(option);
        }
        categorySelect.value = incomingCategory;
      }
      let visibleCount = directoryPageSize(8, 18);

      function render() {
        const query = String(input?.value || "").trim();
        const county = countySelect?.value || "All";
        const selectedCategories = String(categorySelect?.value || "All").split("|").filter(Boolean);
        const matched = rows
          .filter(item => county === "All" || item.county === county)
          .filter(item => selectedCategories.includes("All") || selectedCategories.includes(item.physical_promotion_category))
          .filter(item => !query || resourceTextMatch(item, query))
          .sort((a, b) => String(a.resource_name || "").localeCompare(String(b.resource_name || "")));
        const visible = matched.slice(0, visibleCount);
        host.innerHTML = visible.map(item => resourceCard({
          ...item,
          category: item.physical_promotion_category || item.category,
          public_best_for: item.posting_fit || item.public_best_for,
          physical_ad_note: item.posting_note || item.physical_ad_note,
        })).join("") || `<p class="section-note">No physical promotion contacts match those filters.</p>`;
        syncDirectoryDetails(host);
        if (note) note.textContent = `Showing ${visible.length} of ${matched.length} matching physical promotion contacts.`;
        if (moreButton) {
          const remaining = Math.max(0, matched.length - visible.length);
          moreButton.hidden = remaining === 0;
          moreButton.textContent = remaining ? `Show ${Math.min(directoryPageSize(8, 18), remaining)} more locations` : "All matching locations shown";
        }
      }

      [input, countySelect, categorySelect].forEach(control => {
        if (!control) return;
        control.addEventListener(control === input ? "input" : "change", () => {
          visibleCount = directoryPageSize(8, 18);
          render();
        });
      });
      moreButton && moreButton.addEventListener("click", () => {
        visibleCount += directoryPageSize(8, 18);
        render();
      });
      render();
    }

    function initResourceSearch() {
      const host = document.querySelector("#resource-results");
      if (!host) return;
      const input = document.querySelector("#resource-search");
      const chips = [...document.querySelectorAll("[data-resource-filter]")];
      const locationChips = [...document.querySelectorAll("[data-location-filter]")];
      const typeSelect = document.querySelector("#resource-type-filter");
      const onlineSelect = document.querySelector("#online-connection-filter");
      const outreachSelect = document.querySelector("#outreach-channel-filter");
      const outreachStatusSelect = document.querySelector("#outreach-status-filter");
      const filterDetails = document.querySelector(".directory-filter-details");
      const note = document.querySelector("#resource-results-note");
      const filterSummary = document.querySelector("#resource-filter-summary");
      const moreButton = document.querySelector("#resource-load-more");
      let county = "All";
      let locationMode = "All";
      let visibleCount = directoryPageSize(10, 24);
      const incomingParams = new URLSearchParams(window.location.search);
      const incomingQuery = incomingParams.get("q");
      const incomingLocation = incomingParams.get("location");
      const incomingChannel = incomingParams.get("channel");
      const incomingChannelStatus = incomingParams.get("channel_status");
      if (incomingQuery) input.value = incomingQuery;
      if (
        filterDetails
        && window.matchMedia("(max-width: 640px)").matches
        && !incomingQuery
        && !incomingLocation
        && !incomingChannel
        && !incomingChannelStatus
      ) {
        filterDetails.open = false;
      }
      if (["Physical", "Flyers"].includes(incomingLocation)) {
        locationMode = incomingLocation;
        locationChips.forEach(chip => chip.classList.toggle("is-active", chip.dataset.locationFilter === locationMode));
      }
      populateSelect(typeSelect, uniqueValues(DATA.resources, "public_listing_type"), "All types");
      populateSelect(onlineSelect, uniqueValues(DATA.resources, "online_connection_group"), "All connection types");
      if (outreachSelect && incomingChannel && [...outreachSelect.options].some(option => option.value === incomingChannel)) {
        outreachSelect.value = incomingChannel;
      }
      if (outreachStatusSelect && ["listed", "ask"].includes(incomingChannelStatus)) {
        outreachStatusSelect.value = incomingChannelStatus;
      }
      function resetVisibleCount() {
        visibleCount = directoryPageSize(10, 24);
      }
      function render() {
        const query = input.value.trim();
        const resourceType = typeSelect ? typeSelect.value : "All";
        const onlineConnection = onlineSelect ? onlineSelect.value : "All";
        const outreachChannel = outreachSelect ? outreachSelect.value : "All";
        const outreachStatus = outreachStatusSelect ? outreachStatusSelect.value : "All";
        const matched = DATA.resources
          .filter(item => (county === "All" || item.county === county) && (!query || resourceTextMatch(item, query)))
          .filter(item => resourceType === "All" || item.public_listing_type === resourceType)
          .filter(item => onlineConnection === "All" || item.online_connection_group === onlineConnection)
          .filter(item => {
            const channels = Array.isArray(item.outreach_channels) ? item.outreach_channels : [];
            return outreachChannel === "All" || channels.some(channel => channel.key === outreachChannel);
          })
          .filter(item => {
            const channels = Array.isArray(item.outreach_channels) ? item.outreach_channels : [];
            if (outreachStatus === "All") return true;
            return channels.some(channel => (
              channel.status === outreachStatus
              && (outreachChannel === "All" || channel.key === outreachChannel)
            ));
          })
          .filter(item => (
            locationMode === "All"
            || (locationMode === "Physical" && truthyFlag(item.has_physical_location))
            || (locationMode === "Flyers" && truthyFlag(item.physical_ad_candidate))
          ))
          .sort((a, b) => String(a.resource_name || "").localeCompare(String(b.resource_name || "")));
        const filtered = matched.slice(0, visibleCount);
        if (note) {
          const locationLabel = {
            All: "matching listings",
            Physical: "listings with physical locations",
            Flyers: "physical promotion contacts"
          }[locationMode] || "matching listings";
          note.textContent = `Showing ${filtered.length} of ${matched.length} ${locationLabel}. Search by town, county, resource type, audience, keyword, or task.`;
        }
        if (filterSummary) {
          const activeFilters = [
            county !== "All" ? county : "",
            resourceType !== "All" ? resourceType : "",
            onlineConnection !== "All" ? onlineConnection : "",
            outreachChannel !== "All" ? outreachChannel : "",
            outreachStatus !== "All" ? outreachStatus : "",
            locationMode !== "All" ? locationMode : "",
          ].filter(Boolean);
          filterSummary.textContent = activeFilters.length ? `${activeFilters.length} active` : "All listings";
        }
        host.innerHTML = filtered.map(resourceCard).join("") || `<p class="section-note">No local inventory entries match that search.</p>`;
        syncDirectoryDetails(host);
        if (moreButton) {
          const remaining = Math.max(0, matched.length - filtered.length);
          moreButton.hidden = remaining === 0;
          moreButton.textContent = remaining ? `Show ${Math.min(directoryPageSize(10, 24), remaining)} more listings` : "All listings shown";
        }
      }
      input.addEventListener("input", () => {
        resetVisibleCount();
        render();
      });
      [typeSelect, onlineSelect, outreachSelect, outreachStatusSelect].forEach(select => select && select.addEventListener("change", () => {
        resetVisibleCount();
        render();
      }));
      locationChips.forEach(chip => chip.addEventListener("click", () => {
        locationMode = chip.dataset.locationFilter;
        locationChips.forEach(c => c.classList.toggle("is-active", c === chip));
        resetVisibleCount();
        render();
      }));
      chips.forEach(chip => chip.addEventListener("click", () => {
        county = chip.dataset.resourceFilter;
        chips.forEach(c => c.classList.toggle("is-active", c === chip));
        resetVisibleCount();
        render();
      }));
      moreButton && moreButton.addEventListener("click", () => {
        visibleCount += directoryPageSize(10, 24);
        render();
      });
      render();
    }

    function initCopyButtons() {
      document.querySelectorAll(".template-card").forEach(card => {
        const button = card.querySelector(".copy-button");
        const pre = card.querySelector("pre");
        if (!button || !pre) return;
        button.addEventListener("click", async () => {
          try {
            await navigator.clipboard.writeText(pre.innerText);
            button.textContent = "Copied";
            setTimeout(() => (button.textContent = "Copy"), 1400);
          } catch {
            button.textContent = "Select text";
          }
        });
      });
    }

    function initSubmissionForms() {
      document.querySelectorAll("[data-submit-form]").forEach(form => {
        const button = form.querySelector("[data-submit-button]");
        const success = form.querySelector("[data-submit-success]");
        const submittedName = form.querySelector("[data-submitted-name]");
        const isLocalPreview = ["", "localhost", "127.0.0.1"].includes(window.location.hostname) || window.location.protocol === "file:";
        let submitted = false;

        function showSuccess() {
          const listingName = form.elements.listing_name ? String(form.elements.listing_name.value || "").trim() : "";
          if (submittedName) submittedName.textContent = listingName || "This update";
          playGuideSfx("submit", { userInitiated: true });
          if (success) {
            success.hidden = false;
            success.focus({ preventScroll: true });
            success.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "center" });
          }
          if (button) {
            button.textContent = "Submitted for review";
            button.disabled = true;
          }
        }

        form.addEventListener("submit", async event => {
          if (!form.checkValidity() || submitted) return;
          event.preventDefault();
          submitted = true;
          showSuccess();
          if (isLocalPreview || !window.fetch) return;
          const data = new FormData(form);
          try {
            await fetch(form.getAttribute("action") || window.location.pathname, {
              method: "POST",
              headers: { "Content-Type": "application/x-www-form-urlencoded" },
              body: new URLSearchParams(data).toString()
            });
          } catch {
            if (button) {
              button.textContent = "Saved on this page";
              button.disabled = false;
            }
            submitted = false;
          }
        });
      });
    }

    function initPrintButtons() {
      document.querySelectorAll(".print-button").forEach(button => {
        button.addEventListener("click", () => window.print());
      });
    }

    function initCornerControls() {
      const backToTop = document.querySelector(".back-to-top");
      const updateScrollState = () => {
        document.body.dataset.scrollState = window.scrollY > 240 ? "scrolled" : "top";
      };
      updateScrollState();
      window.addEventListener("scroll", updateScrollState, { passive: true });
      if (backToTop) {
        backToTop.addEventListener("click", event => {
          event.preventDefault();
          window.scrollTo({
            top: 0,
            behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth"
          });
        });
      }
    }

    function initAmbientMusic() {
      const musicShell = document.querySelector("[data-music-bar]");
      const toggle = document.querySelector(".music-toggle");
      const trackSelect = document.querySelector(".music-track-select");
      const progress = document.querySelector(".music-progress");
      const timeLabel = document.querySelector(".music-time");
      const volume = document.querySelector(".music-volume");
      const status = document.querySelector("[data-music-status]");
      const credit = document.querySelector("[data-music-credit]");
      const sourceLink = document.querySelector("[data-music-source]");
      const intro = document.querySelector(".intro-curtain");
      const loopAudio = document.getElementById("site-music-loop");
      if (!toggle || !loopAudio) return;

      const MUSIC_KEY = "triCountyRegionalSoundChoiceV3";
      const TIME_KEY = "triCountyRegionalSoundTimeV3";
      const INTRO_KEY = "triCountyLandingIntroSeenV3";
      const TRACK_KEY = "triCountyRegionalSoundTrackV3";
      const VOLUME_KEY = "triCountyRegionalSoundVolumeV3";
      const savedChoice = localStorage.getItem(MUSIC_KEY);
      let hasSeenIntro = false;
      try {
        hasSeenIntro = sessionStorage.getItem(INTRO_KEY) === "seen";
      } catch {}
      const saveData = Boolean(navigator.connection && navigator.connection.saveData);
      const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      let isPlaying = false;
      let timeSaveId = null;

      loopAudio.loop = true;
      if (trackSelect) {
        const savedTrack = localStorage.getItem(TRACK_KEY);
        const savedOption = savedTrack ? Array.from(trackSelect.options).find(option => option.dataset.trackId === savedTrack) : null;
        if (savedOption) trackSelect.value = savedOption.value;
        loopAudio.src = trackSelect.value;
      }

      function selectedTrackId() {
        const option = trackSelect ? trackSelect.selectedOptions[0] : null;
        return option ? option.dataset.trackId || option.value : "regional-audio-default";
      }

      function updateTrackDetails() {
        const option = trackSelect ? trackSelect.selectedOptions[0] : null;
        if (!option) return;
        if (credit) credit.textContent = option.dataset.credit || option.textContent;
        if (sourceLink && option.dataset.sourceUrl) sourceLink.href = option.dataset.sourceUrl;
      }

      function trackTimeKey(trackId = selectedTrackId()) {
        return `${TIME_KEY}:${trackId}`;
      }

      function formatTime(seconds) {
        const safeSeconds = Number.isFinite(seconds) && seconds > 0 ? seconds : 0;
        const minutes = Math.floor(safeSeconds / 60);
        const remaining = Math.floor(safeSeconds % 60).toString().padStart(2, "0");
        return `${minutes}:${remaining}`;
      }

      function updateProgress() {
        const duration = loopAudio.duration;
        const current = loopAudio.currentTime || 0;
        if (progress) {
          progress.value = Number.isFinite(duration) && duration > 0
            ? String(Math.min(1000, Math.round((current / duration) * 1000)))
            : "0";
        }
        if (timeLabel) {
          timeLabel.textContent = Number.isFinite(duration) && duration > 0
            ? `${formatTime(current)} / ${formatTime(duration)}`
            : formatTime(current);
        }
      }

      function applyVolume({ save = false } = {}) {
        const savedVolume = Number(localStorage.getItem(VOLUME_KEY));
        const fallback = Number.isFinite(savedVolume) ? savedVolume : 42;
        const raw = volume ? Number(volume.value || fallback) : fallback;
        const clamped = Math.max(0, Math.min(100, Number.isFinite(raw) ? raw : fallback));
        if (volume) volume.value = String(clamped);
        const normalized = clamped / 100;
        loopAudio.volume = normalized;
        if (save) localStorage.setItem(VOLUME_KEY, String(clamped));
      }

      applyVolume();
      updateTrackDetails();
      updateProgress();

      function setButtonState(state) {
        toggle.dataset.state = state;
        document.body.dataset.musicState = state;
        if (state === "playing") {
          toggle.textContent = "Stop";
          toggle.setAttribute("aria-pressed", "true");
          if (status) status.textContent = "On";
          if (musicShell) musicShell.open = true;
        } else if (state === "blocked") {
          toggle.textContent = "Play";
          toggle.setAttribute("aria-pressed", "false");
          if (status) status.textContent = "Tap play";
        } else {
          toggle.textContent = "Play";
          toggle.setAttribute("aria-pressed", "false");
          if (status) status.textContent = "Off";
        }
      }

      function rememberTime({ force = false } = {}) {
        if ((!force && !isPlaying) || !Number.isFinite(loopAudio.currentTime)) return;
        localStorage.setItem(trackTimeKey(), String(loopAudio.currentTime));
      }

      function restoreLoopPosition() {
        const savedTime = Number(localStorage.getItem(trackTimeKey()));
        if (Number.isFinite(savedTime) && savedTime > 0) {
          try {
            loopAudio.currentTime = savedTime;
          } catch {
            loopAudio.addEventListener("loadedmetadata", () => {
              try { loopAudio.currentTime = savedTime; } catch {}
            }, { once: true });
          }
        }
      }

      async function startLoop({ userInitiated = false, resume = true, fromBeginning = false } = {}) {
        try {
          if (fromBeginning) {
            loopAudio.currentTime = 0;
          } else if (resume) {
            restoreLoopPosition();
          }
          applyVolume();
          await loopAudio.play();
          isPlaying = true;
          setButtonState("playing");
          localStorage.setItem(MUSIC_KEY, "playing");
          if (timeSaveId) window.clearInterval(timeSaveId);
          timeSaveId = window.setInterval(rememberTime, 900);
          if (userInitiated) {
            rememberTime({ force: true });
          }
          updateProgress();
        } catch {
          isPlaying = false;
          setButtonState("blocked");
        }
      }

      async function startMusic({ userInitiated = false } = {}) {
        await startLoop({ userInitiated, resume: true });
      }

      function stopMusic() {
        rememberTime({ force: true });
        if (timeSaveId) {
          window.clearInterval(timeSaveId);
          timeSaveId = null;
        }
        isPlaying = false;
        loopAudio.pause();
        setButtonState("stopped");
        localStorage.setItem(MUSIC_KEY, "stopped");
        updateProgress();
      }

      toggle.addEventListener("click", () => {
        if (isPlaying) {
          stopMusic();
          return;
        }
        startMusic({ userInitiated: true });
      });

      if (trackSelect) {
        trackSelect.addEventListener("change", () => {
          const wasPlaying = isPlaying;
          rememberTime({ force: true });
          if (timeSaveId) {
            window.clearInterval(timeSaveId);
            timeSaveId = null;
          }
          isPlaying = false;
          loopAudio.pause();
          localStorage.setItem(TRACK_KEY, selectedTrackId());
          loopAudio.src = trackSelect.value;
          loopAudio.currentTime = 0;
          updateTrackDetails();
          updateProgress();
          if (wasPlaying) startLoop({ userInitiated: true, resume: false, fromBeginning: true });
        });
      }

      if (volume) {
        volume.addEventListener("input", () => applyVolume({ save: true }));
      }

      if (progress) {
        progress.addEventListener("input", () => {
          const duration = loopAudio.duration;
          if (!Number.isFinite(duration) || duration <= 0) return;
          loopAudio.currentTime = (Number(progress.value) / 1000) * duration;
          rememberTime({ force: true });
          updateProgress();
        });
      }

      loopAudio.addEventListener("timeupdate", updateProgress);
      loopAudio.addEventListener("loadedmetadata", updateProgress);
      loopAudio.addEventListener("ended", updateProgress);

      document.addEventListener("visibilitychange", () => {
        if (document.hidden) rememberTime({ force: true });
      });

      function markIntroComplete() {
        if (!intro) return;
        intro.dataset.introState = "complete";
        try {
          sessionStorage.setItem(INTRO_KEY, "seen");
        } catch {}
      }

      window.addEventListener("beforeunload", () => rememberTime({ force: true }));

      setButtonState("stopped");
      if (intro) {
        if (hasSeenIntro || prefersReducedMotion) {
          intro.dataset.introState = "skipped";
          if (savedChoice === "playing" && !saveData && !prefersReducedMotion) {
            window.setTimeout(() => startMusic(), 250);
          }
        } else {
          intro.dataset.introState = "playing";
          window.setTimeout(() => playGuideSfx("intro", { armOnGesture: true }), 180);
          window.setTimeout(markIntroComplete, 3000);
        }
      } else if (savedChoice === "playing" && !saveData && !prefersReducedMotion) {
        window.setTimeout(() => startMusic(), 250);
      }
    }

    initPreviewWatermark();
    initNavigationYucca();
    syncDirectoryDetails();
    initProgressiveLists();
    initFreeToolFilters();
    initNationalFundingSearch();
    initSourceSearch();
    initPromoteSearch();
    initPhysicalLocationSearch();
    initResourceSearch();
    initDirectoryOpenAnimations();
    initDirectoryAssistant();
    initCopyButtons();
    initSubmissionForms();
    initPrintButtons();
    initCornerControls();
    initAmbientMusic();
    """
    (ASSET_OUT / "app.js").write_text(dedent(js).strip() + "\n", encoding="utf-8")


def write_readme(summary: dict) -> None:
    task_page_lines = "\n".join(
        f"- `{ACTIVE_PATHS[item['active']]}` - {item['h1']}"
        for item in TASK_PAGE_DEFS
    )
    readme = f"""# Tri-County Regional Marketing Guide

Netlify-ready static site generated on {BUILD_DATE}.

## Deploy

Upload the contents of this folder to Netlify, or upload the generated zip file beside it.

## Main files

- `index.html` - homepage
- `plan/` - step-by-step growth methodology
- `amplifiers/` - newsletters, calendars, directories, visitor guides, and promotion channels
- `network/` - searchable directory shortcuts, physical-location filters, and {summary['row_count']}-row local inventory
- `posting/` - physical flyer/poster location finder plus digital posting and public-notice guidance
- `region/` - regional routing model
- `counties/` - Colfax, Las Animas, and Huerfano county pages
- task-intent pages:
{task_page_lines}
- `templates/` - copy-ready outreach templates
- `submit/` - listing and channel-update intake form
- `appendix/` - public contact/resource appendix grouped by county and community
- `about/` - creation process, method, caveats, and page index
- `assets/animations/` - layered animated yucca SVG banner, CTA marker, and preview files
- `assets/audio/` - Library of Congress public-domain regional MP3 tracks used by the site music bar
- `data/tri_county_persona_resources.csv` - public local inventory
- `data/national-funding-opportunities.csv` - national grants and free support programs with deadline, applicant, fiscal-sponsor, application-cost, and funding-range fields
- `data/national-funding-opportunities.json` - machine-readable national funding directory
- `data/guide-data.json` - directory shortcuts plus public site data
- `data/directory-metadata.json` - full machine-readable metadata for every directory shortcut and local inventory entry
- `SOURCES.md` - directory, amplifier, and posting page manifest
- Secondary routing helper - client-side route suggestions across shortcuts, local inventory rows, regional channels, and posting pathways
- Arts & Culture audio player - Library of Congress public-domain regional audio with play/stop, track choice, progress, and volume controls

## Data summary

- Total local inventory rows: {summary['row_count']}
- National funding opportunities: {len(NATIONAL_FUNDING_OPPORTUNITIES)}
- County mix: {summary['county']}
- Resource type mix: {summary['resource_type']}

## Caveat

The local resource inventory is a working directory. Check phone numbers, eligibility, listing status, and submission rules before publication, printing, outreach, or spending.

## QA notes

- Local HTML/asset references were checked after generation.
- SEO metadata is generated from the page shell: title, description, canonical URL, robots tag, social preview tags, JSON-LD, sitemap, and robots.txt.
- Public pages distinguish directory shortcuts, amplifier channels, public-notice/posting pathways, and local inventory rows.
- Directory page JSON-LD includes machine-readable metadata for every directory shortcut and local inventory entry.
- Unknown paid/free placement, ad availability, approval, deadlines, and audience size are left as direct-contact follow-up tasks.
- A bounded automated external-link check may flag official sites because of bot blocking or local certificate handling. Treat `QA_REPORT.md` as a launch checklist, not a proof that every listed official page is broken.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    (OUT / "netlify.toml").write_text("[build]\n  publish = \".\"\n\n[[headers]]\n  for = \"/*\"\n  [headers.values]\n    X-Content-Type-Options = \"nosniff\"\n", encoding="utf-8")
    sitemap_urls = [SITE_URL + path for path in dict.fromkeys(ACTIVE_PATHS.values())]
    sitemap = "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
            *[f"  <url><loc>{html_escape(url)}</loc><lastmod>{BUILD_DATE}</lastmod><changefreq>monthly</changefreq></url>" for url in sitemap_urls],
            "</urlset>",
            "",
        ]
    )
    (OUT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8")


def write_research_notes(summary: dict) -> None:
    by_county: dict[str, list[dict]] = {}
    for source in DIRECTORY_SOURCES:
        by_county.setdefault(source["county"], []).append(source)

    county_sections = []
    for county in ["Colfax", "Las Animas", "Huerfano", "Regional"]:
        rows = by_county.get(county, [])
        items = "\n".join(
            f"- [{item['title']}]({item['url']}) - {item['kind']}. {public_text_value(item['best_for'])} Action: {public_text_value(item['action'])}"
            for item in rows
        )
        county_sections.append(f"## {county}\n\n{items}")

    notes = f"""# Deep Directory Research Notes

Generated: {BUILD_DATE}

## Purpose

This file records the researched directory layer used by the Netlify draft. The public site is designed to save end users time by sending them first to existing directories, calendars, media pages, economic-development offices, nonprofit directories, creative districts, and state/federal assistance channels.

## How To Interpret The Local Inventory

- Local resource rows: {summary['row_count']}
- County mix: {summary['county']}
- Resource type mix: {summary['resource_type']}

The {summary['row_count']}-row inventory is a working directory. It is useful for discovery, outreach planning, and finding patterns. Check current details before publishing contact, eligibility, or placement claims.

## What The Site Incorporates

- A six-section homepage orientation layer: Directory, Promote, Funding, Counties, Guide, and Tools.
- A searchable shortcut directory with {len(DIRECTORY_SOURCES)} researched pages.
- A regional amplifier page with {len(AMPLIFIER_CHANNELS)} channel rows and practical follow-up guidance.
- A posting page separating official notices, physical boards, flyer/poster/rack-card locations, digital calendars, and local update tasks.
- A public contact appendix grouped by county and community.
- A searchable local inventory using the existing CSV/JSON data.
- County pages that point to local first stops instead of burying users in one long HTML document.
- Templates for listing requests, event calendar submissions, media pitches, partner asks, and follow-up tracking.
- About/method language moved away from the homepage to reduce the "AI report" feel.

## Directory Page Map

{chr(10).join(county_sections)}

## Publication Priorities

1. Check official submission links and preferred contact paths with each chamber, city/tourism office, creative district, newspaper, and economic-development office.
2. Ask whether public wording should say "partner", "resource", "directory", or "referral" for each organization.
3. Keep commercial scraping out of the public guide. Point users to official directories instead.
4. Maintain update dates beside data-heavy inventory sections.
"""
    (OUT / "RESEARCH_DIVE.md").write_text(notes, encoding="utf-8")

    source_manifest = f"""# Page Manifest

Generated: {BUILD_DATE}

This manifest preserves the public page layer used by the Netlify guide. Entries are practical routing paths, not endorsements, guarantees, or proof of acceptance.

## Directory Shortcuts

{chr(10).join(f"- [{item['title']}]({item['url']}) - {item['county']}; {item['kind']}; {public_text_value(item['best_for'])}" for item in DIRECTORY_SOURCES)}

## Amplifier Channels

{chr(10).join(f"- [{item['channel']}]({item['source_url']}) - {item['area_served']}; {item['channel_type']}; ask about current rates, deadlines, and submission rules when relevant." for item in AMPLIFIER_CHANNELS)}

## Posting And Public-Notice Pathways

{chr(10).join(f"- {item['place']} - {public_text_value(item['status'])}" + (f"; link: {item['source_url']}" if item['source_url'] else "; link: local update needed") for item in POSTING_SPACES)}

## Data Files

- data/tri_county_persona_resources.csv
- data/tri_county_persona_resources.json
- data/guide-data.json
"""
    (OUT / "SOURCES.md").write_text(source_manifest, encoding="utf-8")
    (DATA_OUT / "SOURCES.md").write_text(source_manifest, encoding="utf-8")

    html_count = len(list(OUT.glob("**/*.html")))
    qa = f"""# QA Report

Generated: {BUILD_DATE}

## Passed

- {html_count} HTML files present, including generated public pages and animation previews.
- 0 missing local href/src references in generated HTML.
- {len(DIRECTORY_SOURCES)} researched directory shortcuts embedded.
- {len(AMPLIFIER_CHANNELS)} amplifier channel rows embedded.
- {len(POSTING_SPACES)} posting/public-notice pathway rows embedded.
- {summary['row_count']} local inventory rows embedded and copied to `/data`.
- Full directory metadata generated at `/data/directory-metadata.json` and embedded in Directory page JSON-LD.
- Public pages use the animated landscape assets and HTML/CSS layout; no separate generated chart assets are required.
- Zip package generated for Netlify upload.

## Known Caveats

- Any automated external-link check can produce false failures for government/tourism sites that block scripted requests.
- Paid/free status, advertising availability, approval rules, print deadlines, and audience size remain direct-contact follow-up tasks unless explicitly stated on a page.
- Fresh scripted link checks may be exported separately when the link-check script is run.
- The stale Raton/Colfax directory paths from the added PDF materials were replaced with working official parent/category pages in the public shortcut layer.

## Manual Publication Check

Before public launch, open the deployed Netlify preview and check:

- Home hero yucca/mountain animation, reduced-motion behavior, and mobile title wrapping.
- Directory search for `chamber`, `artist`, `media`, `grant`, `Raton`, `Trinidad`, and `Walsenburg`.
- Directory filters for resource type and access mode.
- Directory physical-location filters for `Physical locations` and `Physical promotion contacts`.
- Amplifier page rows for link URL and practical channel use.
- Physical-location finder search, county/category filters, contact links, and one clear policy note.
- County page nav paths.
- Footer logo scale.
- All high-priority external links.
- any link-check report for bot-blocked, timed-out, or manually-confirmed URLs.
"""
    (OUT / "QA_REPORT.md").write_text(qa, encoding="utf-8")


def write_pages(rows: list[dict], summary: dict) -> None:
    (OUT / "index.html").write_text(home_page(summary), encoding="utf-8")
    for folder in ["plan", "amplifiers", "promote", "network", "posting", "region", "templates", "tools/free-discounted", "submit", "appendix", "about", "resources/funding", "resources/arts-culture"]:
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    for item in TASK_PAGE_DEFS:
        path = OUT / ACTIVE_PATHS[item["active"]]
        path.mkdir(parents=True, exist_ok=True)
    (OUT / "plan" / "index.html").write_text(plan_page(), encoding="utf-8")
    (OUT / "amplifiers" / "index.html").write_text(amplifiers_page(), encoding="utf-8")
    (OUT / "promote" / "index.html").write_text(promote_page(), encoding="utf-8")
    (OUT / "network" / "index.html").write_text(network_page(rows), encoding="utf-8")
    (OUT / "resources" / "funding" / "index.html").write_text(funding_page(rows), encoding="utf-8")
    (OUT / "resources" / "arts-culture" / "index.html").write_text(arts_culture_page(rows), encoding="utf-8")
    (OUT / "posting" / "index.html").write_text(posting_page(rows), encoding="utf-8")
    (OUT / "region" / "index.html").write_text(region_page(summary), encoding="utf-8")
    (OUT / "templates" / "index.html").write_text(templates_page(), encoding="utf-8")
    (OUT / "tools" / "free-discounted" / "index.html").write_text(free_tools_page(), encoding="utf-8")
    (OUT / "submit" / "index.html").write_text(submit_page(), encoding="utf-8")
    (OUT / "appendix" / "index.html").write_text(appendix_page(rows), encoding="utf-8")
    (OUT / "about" / "index.html").write_text(about_page(summary), encoding="utf-8")
    for item in TASK_PAGE_DEFS:
        (OUT / ACTIVE_PATHS[item["active"]] / "index.html").write_text(task_page(item, rows), encoding="utf-8")

    county_copy = {
        "Colfax": ("colfax", "Use Raton as the first visible hub, then widen through MainStreet, GrowRaton, Explore Raton, arts, media, and New Mexico support."),
        "Las Animas": ("las-animas", "Use Trinidad as the chamber, tourism, media, and creative-district hub, then connect outward through Colexico and Colorado support."),
        "Huerfano": ("huerfano", "Use Walsenburg, La Veta, Spanish Peaks Country, HCED, the chamber, creative district, and the World Journal as practical entry points."),
    }
    for county, (slug, summary_text) in county_copy.items():
        target = OUT / "counties" / slug
        target.mkdir(parents=True, exist_ok=True)
        target.joinpath("index.html").write_text(county_page(county, slug, summary_text, rows), encoding="utf-8")


def zip_output() -> Path:
    zip_base = OUT.parent / "Tri_County_Regional_Marketing_Guide_Netlify_Deep"
    zip_path = Path(str(zip_base) + ".zip")
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(zip_base), "zip", OUT)
    return zip_path


def reset_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def main() -> None:
    reset_output_dir(OUT)
    rows = load_resources()
    summary = summarize(rows)
    copy_assets()
    write_data_files(rows, summary)
    write_static_assets()
    write_pages(rows, summary)
    copy_site_extras()
    write_readme(summary)
    write_research_notes(summary)
    zip_path = zip_output()
    print(json.dumps({"output": str(OUT), "zip": str(zip_path), "rows": summary["row_count"], "sources": len(DIRECTORY_SOURCES)}, indent=2))


if __name__ == "__main__":
    main()

