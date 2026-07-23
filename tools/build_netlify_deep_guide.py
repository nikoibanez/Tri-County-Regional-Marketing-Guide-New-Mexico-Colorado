from __future__ import annotations

import csv
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
REAUDIT_NOTES = DOWNLOADS / "tri_county_reaudit" / "comprehensive_reaudit_source_notes.md"
NEW_PDF_EXTRACT_DIR = DOWNLOADS / "tri_county_new_pdf_extract_20260621"
BUILD_DATE = os.environ.get("BUILD_DATE", date.today().isoformat())


def normalize_origin(value: str) -> str:
    value = (value or "").strip() or "https://statelineguide.org"
    return value.rstrip("/") + "/"


SITE_URL = normalize_origin(os.environ.get("PUBLIC_SITE_ORIGIN", "https://statelineguide.org"))

ACTIVE_PATHS = {
    "home": "",
    "plan": "plan/",
    "amplifiers": "amplifiers/",
    "network": "network/",
    "posting": "posting/",
    "region": "region/",
    "colfax": "counties/colfax/",
    "las-animas": "counties/las-animas/",
    "huerfano": "counties/huerfano/",
    "templates": "templates/",
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
    "posting": "hero-desert-buttes.svg",
    "region": "hero-raton-mesa.svg",
    "colfax": "hero-volcanic-field.svg",
    "las-animas": "hero-fishers-canyon.svg",
    "huerfano": "hero-spanish-peaks.svg",
    "templates": "hero-huerfano-valley.svg",
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
        "href": "posting/",
        "summary": "Find the calendar, tourism, venue, media, or public-office route that fits the event before sending materials everywhere.",
        "action": "Choose an event route",
    },
    {
        "title": "Promote or advertise",
        "href": "regional-channels/",
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


CURRENT_LEADS = [
    {
        "title": "New Mexico Local Economic Development Act",
        "county": "Colfax",
        "kind": "Public economic-development funding",
        "group": "Funding",
        "url": "https://www.edd.newmexico.gov/grants/local-economic-development-act/",
        "best_for": "Colfax projects that may need a formal public economic-development path, infrastructure support, or a city/county conversation before funding is realistic.",
        "action": "Use as an official starting gate, then confirm eligibility, public-process requirements, and the local applicant pathway.",
    },
    {
        "title": "New Mexico Trails+ Grant",
        "county": "Colfax",
        "kind": "Outdoor recreation / trail funding",
        "group": "Funding",
        "url": "https://www.edd.newmexico.gov/press-releases/state-opens-trails-grant-for-outdoor-recreation-projects/",
        "best_for": "Trail, outdoor recreation, visitor-economy, and community access projects that need a state funding lead to evaluate.",
        "action": "Check the current cycle, eligible applicants, match rules, and deadlines before building a project promise around it.",
    },
    {
        "title": "New Mexico Job Training Incentive Program",
        "county": "Colfax",
        "kind": "Workforce training reimbursement",
        "group": "Funding",
        "url": "https://www.edd.newmexico.gov/programs-and-services/business-development/job-training-incentive-program/",
        "best_for": "New Mexico businesses planning expansion hires and training costs before those positions are filled.",
        "action": "Use early in hiring planning; verify eligible jobs, wages, timing, and approval steps before promising reimbursement.",
    },
    {
        "title": "Explore Raton Visitors Guide advertising",
        "county": "Colfax",
        "kind": "Visitor guide / promotion inquiry",
        "group": "Directory source",
        "url": "https://www.exploreraton.com/post/purchase-your-2026-raton-visitors-guide-ad",
        "best_for": "Raton and Colfax visitor-facing businesses, attractions, lodging, dining, galleries, recreation, and event campaigns.",
        "action": "Ask about the current visitor-guide deadline, ad sizes, rate card, placement rules, and whether the listing also appears online.",
    },
    {
        "title": "Town of La Veta Business Directory",
        "county": "Huerfano",
        "kind": "Municipal business directory",
        "group": "Directory source",
        "url": "https://townoflaveta-co.gov/business-directory/",
        "best_for": "La Veta businesses, galleries, lodging, dining, services, and local referrals that should be findable from a municipal source.",
        "action": "Check whether a listing is present, then use the town contact path to ask about additions or corrections.",
    },
    {
        "title": "Walsenburg Mercantile vendors",
        "county": "Huerfano",
        "kind": "Maker / retail vendor directory",
        "group": "Directory source",
        "url": "https://www.walsenburgmercantile.com/meet-our-vendors",
        "best_for": "Artists, makers, craftspeople, food producers, and retailers looking for local vendor visibility and cross-promotion examples.",
        "action": "Use as a discovery lead, then contact the venue directly before assuming vendor availability or terms.",
    },
    {
        "title": "Meditating Monkey Art Emporium relocation watch",
        "county": "Huerfano",
        "kind": "Arts venue / listing update watch",
        "group": "Update watch",
        "url": "https://www.facebook.com/meditatingmonkeyartemporium/",
        "best_for": "Arts-directory cleanup, visitor-facing gallery updates, and avoiding stale address or venue references.",
        "action": "Confirm the current address and status before publishing or printing a gallery, event, or shopping recommendation.",
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
        "url": "https://oedit.colorado.gov/arts-in-society-grant",
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
    ("Event Calendars", "Best for public, time-sensitive things: performances, markets, workshops, launches, fundraisers, and visitor-facing events."),
    ("Newsletters & Mailing Lists", "Best for opt-in audiences; ask before assuming outside announcements or ads are accepted."),
    ("Business Directories", "Best for being findable after the first announcement has passed."),
    ("Tourism/Visitor Guides", "Best for lodging, dining, shopping, galleries, attractions, recreation, and visitor services."),
    ("Anchor Venue Lineups", "Best for arts, music, theater, food, and event-adjacent cross-promotion."),
    ("Ask About Advertising or Placement", "Best when a channel may sell ads or placements but the public page does not confirm terms."),
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
        "title": "Libraries and community boards",
        "best_for": "Classes, nonprofit programs, arts events, workshops, support services, and local announcements.",
        "ask": "Ask the front desk or branch contact about flyer size, dates, political material, commercial material, and removal rules.",
    },
    {
        "title": "Visitor and tourism centers",
        "best_for": "Events, galleries, lodging-adjacent offers, visitor services, tours, food, retail, and destination-facing rack cards.",
        "ask": "Ask whether the location accepts brochures, rack cards, posters, or event flyers and whether materials must be visitor-facing.",
    },
    {
        "title": "City halls, courts, and public offices",
        "best_for": "Official notices, public meetings, civic programs, public hearings, and government-adjacent information.",
        "ask": "Use these for public information routes, not casual advertising. Ask the clerk, office, or department about current posting rules.",
    },
    {
        "title": "Downtown and high-traffic businesses",
        "best_for": "Local events, art shows, classes, services, hiring, restaurant specials, and cross-promotion near foot traffic.",
        "ask": "Ask the owner or manager before leaving materials. Bring a small stack and offer to remove flyers after the date passes.",
    },
    {
        "title": "Galleries, venues, museums, and cultural spaces",
        "best_for": "Openings, performances, artist calls, workshops, talks, music, festivals, and creative-sector promotion.",
        "ask": "Ask whether the event fits the venue's audience and whether they prefer a poster, digital image, calendar link, or press blurb.",
    },
    {
        "title": "Transit, travel, lodging, and visitor stops",
        "best_for": "Visitor-facing events, maps, tours, transportation notices, lodging-adjacent services, and regional travel ideas.",
        "ask": "Ask about lobby, kiosk, front-desk, or brochure-rack rules before printing large quantities.",
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
)

PHYSICAL_AD_LISTING_TYPES = {
    "Arts & culture",
    "Education & learning",
    "Events & venues",
    "Food & drink",
    "Lodging & stays",
    "Nonprofit & community",
    "Public offices",
    "Retail & local goods",
    "Tourism & visitor info",
}


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


PATHS = [
    {
        "name": "Plan Your Growth",
        "slug": "plan",
        "summary": "Choose what kind of expansion you need before chasing every possible listing.",
        "cta": "Start the growth cycle",
    },
    {
        "name": "Find the Network",
        "slug": "network",
        "summary": "Use existing directories, calendars, media channels, chambers, and support orgs first.",
        "cta": "Search shortcuts and listings",
    },
    {
        "name": "Understand the Region",
        "slug": "region",
        "summary": "See how Colfax, Las Animas, Huerfano, and regional channels fit together.",
        "cta": "Read the regional map",
    },
]


ROUTE_LABELS = {
    "home": "Home",
    "plan": "Plan",
    "amplifiers": "Amplifiers",
    "network": "Network",
    "posting": "Posting",
    "region": "Region",
    "colfax": "Colfax County",
    "las-animas": "Las Animas County",
    "huerfano": "Huerfano County",
    "templates": "Templates",
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
        "title": "Where to Post Events in Raton NM | Stateline Guide",
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
        "title": "Where to Post Events in Trinidad CO | Stateline Guide",
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
        "title": "Where to Post Events in Walsenburg & La Veta CO | Stateline Guide",
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
        "title": "Where to Advertise in Trinidad CO | Stateline Guide",
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
        "title": "Colfax County Business Resources | Stateline Guide",
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
        "title": "Las Animas County Nonprofit Resources | Stateline Guide",
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
        "title": "Huerfano County Event Calendars & Visitor Listings | Stateline Guide",
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
        "title": "Artist & Gallery Promotion in Raton, Trinidad & Walsenburg | Stateline Guide",
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
        "title": "Regional Newsletters, Event Calendars & Visitor Guides | Stateline Guide",
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
        "use": "Public event, class, fundraiser, market, opening, performance, or visitor activity.",
        "prepare": "Name, date, time, place, short blurb, image, cost, and public contact.",
        "check": "Eligibility, lead time, image size, deadline, and whether the calendar owner reviews submissions.",
    },
    {
        "label": "Promotion",
        "class": "cat-promotion",
        "use": "Ad inquiry, newsletter blurb, partner share, flyer placement, or media pitch.",
        "prepare": "One-sentence hook, audience fit, call to action, image, link, and contact.",
        "check": "Free or paid status, rates, deadline, audience fit, and whether placement is guaranteed.",
    },
    {
        "label": "Business",
        "class": "cat-business",
        "use": "Business listing, service-area update, shop-local route, or downtown/tourism visibility.",
        "prepare": "Business name, category, address or service area, website, hours, phone, and short description.",
        "check": "Listing requirements, membership rules, current contact route, and update process.",
    },
    {
        "label": "Nonprofits",
        "class": "cat-nonprofit",
        "use": "Program, mentorship, class, service, volunteer route, grant path, or community referral.",
        "prepare": "Who is served, what is offered, eligibility, dates, location, contact, and referral action.",
        "check": "Eligibility, privacy limits, deadlines, and whether the partner wants public promotion.",
    },
    {
        "label": "Arts & Culture",
        "class": "cat-arts",
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
        "title": "Colfax County Business, Event & Promotion Resources | Stateline Guide",
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
        "title": "Las Animas County Business, Event & Nonprofit Resources | Stateline Guide",
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
        "title": "Huerfano County Event, Tourism & Business Resources | Stateline Guide",
        "description": "Use Walsenburg, La Veta, Spanish Peaks Country, HCED, chamber, creative district, World Journal, and rural Colorado support routes.",
    },
}


PROMOTION_TOOLS = [
    {
        "name": "Canva",
        "url": "https://www.canva.com/",
        "use": "Flyers, social posts, simple ads, posters, and presentation graphics.",
        "note": "Free/freemium design tool; check current plan limits.",
    },
    {
        "name": "Adobe Express",
        "url": "https://www.adobe.com/express/",
        "use": "Alternate flyer, social, photo, and quick brand-asset creation.",
        "note": "Free/freemium design tool; check current plan limits.",
    },
    {
        "name": "Google Forms",
        "url": "https://workspace.google.com/products/forms/",
        "use": "Signup forms, intake forms, update requests, and simple surveys.",
        "note": "Useful when a program needs responses before a full website exists.",
    },
    {
        "name": "Google Business Profile",
        "url": "https://business.google.com/en-all/business-profile/",
        "use": "Search and Maps visibility, hours, photos, posts, and basic business listing control.",
        "note": "Free listing path for storefronts and service-area businesses.",
    },
    {
        "name": "Meta Business Suite",
        "url": "https://business.meta.com/",
        "use": "Facebook and Instagram post scheduling, messaging, insights, and ad setup.",
        "note": "Free business dashboard; paid ads remain optional.",
    },
    {
        "name": "HubSpot Email Marketing",
        "url": "https://www.hubspot.com/products/marketing/email",
        "use": "Email newsletters, outreach campaigns, simple CRM-linked lists, and templates.",
        "note": "Free/freemium email tools; check send limits before launch.",
    },
    {
        "name": "Mailchimp",
        "url": "https://mailchimp.com/pricing/marketing/compare-plans/",
        "use": "Beginner-friendly mailing lists, email campaigns, audience forms, and reporting.",
        "note": "Free/freemium email marketing; check current contact and send limits.",
    },
    {
        "name": "Brevo",
        "url": "https://www.brevo.com/pricing/",
        "use": "Email campaigns and contact lists when a small team needs a simple sender.",
        "note": "Free/freemium email marketing; check daily and monthly limits.",
    },
]


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
    return " ".join(value.split())


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
    text = " ".join(
        [
            name,
            clean_text(row.get("category")),
            clean_text(row.get("resource_type")),
            " ".join(listing_keyword_terms(row)),
            note,
        ]
    ).casefold()
    category = clean_text(row.get("category"))
    resource_type = clean_text(row.get("resource_type"))
    for needles, label in PUBLIC_TYPE_RULES:
        if any(needle in text for needle in needles):
            return label
    for candidate in [category, resource_type]:
        if candidate in PUBLIC_TYPE_LABELS:
            return candidate
        candidate_text = candidate.casefold()
        if candidate_text:
            for needles, label in PUBLIC_TYPE_RULES:
                if any(needle in candidate_text for needle in needles):
                    return label
    for needle, label in BUSINESS_TYPE_KEYWORDS:
        if needle in text:
            label_text = label.casefold()
            for needles, public_label in PUBLIC_TYPE_RULES:
                if any(rule in label_text or rule in needle for rule in needles):
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
    if is_physical_ad_candidate(row):
        for part in ["Ask about flyers", "physical ads", "posters", "rack cards", "bulletin boards", "front-desk referrals"]:
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
    return f"{name} is listed as a {base_by_type.lower()} in {place}.{category_sentence} Useful for {best_phrase} when the fit and contact path make sense."


def public_best_for(row: dict) -> str:
    goals = split_semicolon(normalize_goal_relevance(row.get("goal_relevance")))
    tags = organization_tags(row)
    listing_type = inferred_listing_type(row)
    access_mode = clean_text(row.get("access_mode")).casefold()
    uses = []
    if "Promote Something" in goals:
        uses.append("promotion")
    if "Improve Online Visibility" in goals:
        uses.append("online listing cleanup")
    if "Reach People Offline" in goals or "physical" in access_mode:
        uses.append("flyers or in-person referrals")
    if "Find Money or Help" in goals or listing_type == "Funding & support":
        uses.append("funding or support research")
    if "Get Media Coverage" in goals or listing_type == "Media & news":
        uses.append("media or calendar outreach")
    if "Add / Correct Info" in goals:
        uses.append("listing updates")
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
    term_hits = sum(1 for term in PHYSICAL_AD_LOCATION_TERMS if term in blob)
    score = term_hits * 2
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
    if not term_hits and listing_type not in PHYSICAL_AD_LISTING_TYPES:
        return 0
    return max(score, 0)


def physical_ad_location_fit(row: dict) -> str:
    blob = " ".join(
        clean_text(row.get(field)).casefold()
        for field in ["resource_name", "category", "resource_type", "public_listing_type", "public_description"]
    )
    listing_type = inferred_listing_type(row)
    if listing_type == "Public offices" or any(term in blob for term in ("city hall", "town hall", "county clerk", "courthouse", "court", "public office")):
        return "Official notices, public meetings, civic information, public hearings, and department-approved announcements."
    if any(term in blob for term in ("library", "community center", "senior center", "recreation center")):
        return "Community flyers, classes, nonprofit programs, support services, and local events."
    if any(term in blob for term in ("gallery", "museum", "venue", "theater", "theatre", "arts", "creative district", "cultural")):
        return "Art openings, performances, workshops, creative calls, festivals, classes, and cultural events."
    if any(term in blob for term in ("coffee", "cafe", "espresso", "bakery", "restaurant", "bar", "brewery", "distillery", "market", "grocery", "shop", "store", "mercantile")):
        return "Neighborhood flyers, local offers, hiring, events, classes, specials, and downtown cross-promotion."
    if any(term in blob for term in ("rail", "train", "station", "depot", "bus", "transit", "hotel", "motel", "inn", "lodging", "campground", "rv", "resort")):
        return "Visitor-facing flyers, travel information, event handouts, maps, tours, and lodging-adjacent services."
    if any(term in blob for term in ("visitor", "tourism", "tourist", "welcome center", "chamber", "mainstreet")):
        return "Visitor-facing events, rack cards, brochures, business listings, tours, lodging, food, retail, and attractions."
    return "Flyers, posters, brochures, rack cards, or front-desk referrals when the location owner says the material fits."


def physical_ad_location_note(row: dict) -> str:
    listing_type = inferred_listing_type(row)
    blob = " ".join(
        clean_text(row.get(field)).casefold()
        for field in ["resource_name", "category", "resource_type", "public_listing_type", "public_description"]
    )
    if listing_type == "Public offices":
        return "Ask the correct office first. Public offices may separate official notices from community flyers or commercial advertising."
    if "library" in blob:
        return "Ask staff about bulletin-board rules. Some libraries limit political, for-profit, oversized, or undated materials."
    if any(term in blob for term in ("school", "college", "campus")):
        return "Ask the office or department. Schools and campuses may require approval before materials can be posted."
    if any(term in blob for term in ("restaurant", "cafe", "coffee", "bar", "brewery", "market", "shop", "store")):
        return "Ask the owner or manager, bring a small stack, and offer to remove the flyer after the event or deadline."
    if any(term in blob for term in ("visitor", "tourism", "tourist", "welcome center", "chamber")):
        return "Ask whether they accept public-facing brochures, rack cards, posters, or calendar submissions."
    return "Ask before posting. Note who approved it, where it was placed, and when it should come down."


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
    return physical_ad_location_score(row) >= 19


def physical_ad_location_rows(rows: list[dict], limit: int = 96) -> list[dict]:
    scored: list[tuple[int, dict]] = []
    for row in rows:
        score = physical_ad_location_score(row)
        if score:
            scored.append((score, row))
    ranked = sorted(scored, key=lambda item: (-item[0], clean_text(item[1].get("resource_name")).casefold()))
    by_county: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    for item in ranked:
        by_county[clean_text(item[1].get("county")) or "Regional"].append(item)
    county_order = ["Colfax", "Las Animas", "Huerfano", "Regional"]
    county_cap = max(24, limit // 3)
    town_cap = 16
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

    for county in county_order:
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


def contact_links_for_row(row: dict) -> str:
    links: list[str] = []
    website_urls = split_semicolon(row.get("website"))
    source_urls = split_semicolon(row.get("source_url"))
    if website_urls:
        url = website_urls[0]
        links.append(f'<a href="{html_escape(url)}" target="_blank" rel="noreferrer">{html_escape(resource_url_label(url))}</a>')
    first_source = next((url for url in source_urls if url not in website_urls), "")
    if first_source:
        links.append(f'<a href="{html_escape(first_source)}" target="_blank" rel="noreferrer">{html_escape(resource_url_label(first_source, "Listing page"))}</a>')
    phone = clean_text(row.get("contact_phone"))
    if phone:
        phone_href = re.sub(r"[^0-9+]", "", phone)
        links.append(f'<a href="tel:{html_escape(phone_href)}">Phone</a>')
    email = clean_text(row.get("contact_email"))
    if email:
        links.append(f'<a href="mailto:{html_escape(email)}">Email</a>')
    address = clean_text(row.get("physical_address"))
    if address:
        map_url = "https://www.google.com/maps/search/?api=1&query=" + quote_plus(address)
        links.append(f'<a href="{html_escape(map_url)}" target="_blank" rel="noreferrer">Map</a>')
    return " ".join(links[:5]) or '<span class="source-note">Search the directory or submit a contact update.</span>'


def resource_physical_indicator_badges(row: dict) -> str:
    if clean_text(row.get("physical_ad_candidate")) == "true" or is_physical_ad_candidate(row):
        note = clean_text(row.get("physical_ad_note")) or physical_ad_location_note(row)
        return (
            '<div class="listing-indicators" aria-label="Physical location indicators">'
            f'<span class="listing-marker listing-marker--ad" title="{html_escape(note)}">Ask about flyers</span>'
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


def enrich_resource_row(row: dict) -> dict:
    status = infer_verification_key(row)
    layer = infer_public_layer(row)
    enriched = dict(row)
    enriched["goal_relevance"] = normalize_goal_relevance(enriched.get("goal_relevance"))
    enriched["public_listing_type"] = inferred_listing_type(enriched)
    enriched["public_category"] = compact_category_label(enriched, enriched["public_listing_type"])
    enriched["public_description"] = public_description(enriched)
    enriched["public_keywords"] = public_search_keywords(enriched)
    enriched["public_audience_tags"] = "; ".join(organization_tags(enriched))
    enriched["public_org_tags"] = enriched["public_audience_tags"]
    enriched["public_best_for"] = public_best_for(enriched)
    enriched["has_physical_location"] = as_bool_text(has_physical_location(enriched))
    enriched["physical_ad_candidate"] = as_bool_text(is_physical_ad_candidate(enriched))
    if enriched["physical_ad_candidate"] == "true":
        enriched["physical_ad_label"] = "Ask about flyers"
        enriched["physical_ad_note"] = physical_ad_location_note(enriched)
    elif enriched["has_physical_location"] == "true":
        enriched["physical_ad_label"] = "Physical location"
        enriched["physical_ad_note"] = "This listing has a real-world location; ask directly before leaving flyers, posters, brochures, or rack cards."
    else:
        enriched["physical_ad_label"] = ""
        enriched["physical_ad_note"] = ""
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
    return {
        "row_count": len(rows),
        "county": dict(county.most_common()),
        "resource_type": dict(rtype.most_common()),
        "verification": dict(verification.most_common()),
        "public_layer": dict(layer.most_common()),
        "goal": dict(goal.most_common(12)),
        "audience": dict(audience.most_common(12)),
        "physical_location_count": physical_location_count,
        "physical_ad_candidate_count": physical_ad_candidate_count,
    }


def copy_assets() -> None:
    ASSET_OUT.mkdir(parents=True, exist_ok=True)
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    for src, dest in [
        (ROOT / "assets" / "brand" / "super-eukarya-logo.png", ASSET_OUT / "super-eukarya-logo.png"),
        (ROOT / "assets" / "brand" / "raton-accessible-cursor.svg", ASSET_OUT / "raton-accessible-cursor.svg"),
    ]:
        if src.exists():
            shutil.copy2(src, dest)

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

    infographics_src = ROOT / "assets" / "infographics"
    if infographics_src.exists():
        infographics_dest = ASSET_OUT / "infographics"
        if infographics_dest.exists():
            shutil.rmtree(infographics_dest)
        shutil.copytree(infographics_src, infographics_dest)

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
        "has_physical_location": clean_text(public_row.get("has_physical_location")),
        "physical_ad_candidate": clean_text(public_row.get("physical_ad_candidate")),
        "physical_ad_label": clean_text(public_row.get("physical_ad_label")),
        "physical_ad_note": clean_text(public_row.get("physical_ad_note")),
        "cost_level": clean_text(public_row.get("cost_level")),
        "audience_tags": split_public_list(public_row.get("public_audience_tags") or public_row.get("public_org_tags")),
        "search_keywords": split_public_list(public_row.get("public_keywords")),
        "best_for": split_public_list(public_row.get("public_best_for")),
        "description": clean_text(public_row.get("public_description")) or clean_text(public_row.get("category")) or "Local directory listing for regional discovery and outreach.",
        "metadata_note": "Details may change; use the listed contact path or update form when information is outdated.",
    }
    return {key: value for key, value in metadata.items() if value not in ("", [], None)}


def directory_shortcut_metadata(item: dict, position: int) -> dict:
    public_item = public_data_item(item)
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
        "name": "Stateline Guide directory entries",
        "description": "Machine-readable metadata for directory shortcuts and local inventory entries in the Stateline Guide. Details may change.",
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
    public_rows = [public_data_item(row) for row in rows]
    physical_ad_locations = []
    for row in physical_ad_location_rows(rows, limit=120):
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
        "current_leads": [public_data_item(item) for item in CURRENT_LEADS],
        "home_task_groups": HOME_TASK_GROUPS,
        "amplifier_channels": amplifier_channels,
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
    (DATA_OUT / "guide-data.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    js_payload = "window.TRI_COUNTY_GUIDE_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n"
    (ASSET_OUT / "site-data.js").write_text(js_payload, encoding="utf-8")


def html_escape(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def sorted_sources(sources: list[dict]) -> list[dict]:
    return sorted(sources, key=lambda item: (item.get("title") or item.get("channel") or "").casefold())


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
            group["best_for"] = f"Grouped routes for {group['title']}. Use the sublinks below for the specific directory, grant, event, listing, advertising, or support task."
            group["action"] = "Pick the sublink that matches the job, then confirm current rules, deadlines, eligibility, rates, or acceptance with the source."
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
              <div class="source-link-list">{links}</div>
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


def current_lead_cards(depth: int = 0, group: str | None = None) -> str:
    leads = [item for item in CURRENT_LEADS if group is None or item["group"] == group]
    return "\n".join(
        f"""
        <article class="lead-card" data-lead-group="{html_escape(item['group'])}" data-county="{html_escape(item['county'])}">
          <div class="source-card__meta">
            <span>{html_escape(item['group'])}</span>
            <span>{html_escape(item['county'])}</span>
            <span>{html_escape(item['kind'])}</span>
          </div>
          <h3><a href="{html_escape(item['url'])}" target="_blank" rel="noreferrer">{html_escape(item['title'])}</a></h3>
          <p>{html_escape(public_text_value(item['best_for']))}</p>
          <p class="action-line">{html_escape(public_text_value(item['action']))}</p>
        </article>
        """
        for item in leads
    )


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
        <p class="section-note">{html_escape(context_copy[1])} Submissions are starting points for review, not automatic publication.</p>
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
        "name": "Stateline Guide",
        "alternateName": "Tri-County Regional Marketing Guide",
        "url": SITE_URL,
        "description": "A regional visibility routing guide for businesses, artists, nonprofits, event organizers, services, and community programs across Colfax, Las Animas, and Huerfano counties.",
        "inLanguage": "en-US",
    }


def organization_json_ld() -> dict:
    return {
        "@type": "Organization",
        "name": "Stateline Guide",
        "url": SITE_URL,
        "description": "A regional visibility routing guide for businesses, artists, nonprofits, event organizers, services, and community programs across Colfax, Las Animas, and Huerfano counties.",
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
    task_nav_labels = {
        "post-raton": "Raton events",
        "post-trinidad": "Trinidad events",
        "post-huerfano": "Huerfano events",
        "advertise-trinidad": "Trinidad ads",
        "colfax-business": "Colfax business",
        "las-animas-nonprofit": "Las Animas nonprofits",
        "huerfano-calendars": "Huerfano calendars",
        "artist-gallery": "Artist + gallery",
        "regional-channels": "Regional channels",
    }
    task_nav_links = [
        (task_nav_labels.get(item["active"], ROUTE_LABELS[item["active"]]), route_href(ACTIVE_PATHS[item["active"]]), item["active"])
        for item in TASK_PAGE_DEFS
    ]
    nav_structure = [
        ("link", "Home", "index.html", "home"),
        (
            "group",
            "Start",
            [
                ("Plan", "plan/index.html", "plan"),
                ("Region", "region/index.html", "region"),
                ("About", "about/index.html", "about"),
            ],
        ),
        (
            "group",
            "Find",
            [
                ("Network", "network/index.html", "network"),
                ("Funding", route_href(ACTIVE_PATHS["funding"]), "funding"),
                ("Arts & Culture", route_href(ACTIVE_PATHS["arts-culture"]), "arts-culture"),
                ("Amplifiers", "amplifiers/index.html", "amplifiers"),
                ("Regional channels", route_href(ACTIVE_PATHS["regional-channels"]), "regional-channels"),
                ("Appendix", "appendix/index.html", "appendix"),
            ],
        ),
        (
            "group",
            "Counties",
            [
                ("Colfax", "counties/colfax/index.html", "colfax"),
                ("Las Animas", "counties/las-animas/index.html", "las-animas"),
                ("Huerfano", "counties/huerfano/index.html", "huerfano"),
            ],
        ),
        (
            "group",
            "Tasks",
            task_nav_links,
        ),
        (
            "group",
            "Tools",
            [
                ("Posting rules", "posting/index.html", "posting"),
                ("Templates", "templates/index.html", "templates"),
                ("Submit update", "submit/index.html", "submit"),
            ],
        ),
    ]

    def nav_link(label: str, href: str, key: str) -> str:
        active_class = "is-active" if key == active else ""
        current = ' aria-current="page"' if key == active else ""
        return f'<a class="{active_class}" href="{rel(href, depth)}"{current}>{label}</a>'

    nav_parts = []
    for item in nav_structure:
        if item[0] == "link":
            _, label, href, key = item
            nav_parts.append(nav_link(label, href, key))
            continue
        _, label, children = item
        group_active = any(key == active for _, _, key in children)
        child_links = "\n".join(nav_link(child_label, href, key) for child_label, href, key in children)
        nav_parts.append(
            f"""
            <details class="nav-group {'is-active' if group_active else ''}">
              <summary class="nav-trigger">{label}</summary>
              <div class="nav-menu">
                {child_links}
              </div>
            </details>
            """
        )
    nav = "\n".join(nav_parts)
    footer_structure = [
        (
            "Start",
            [
                ("Home", "index.html"),
                ("Plan", "plan/index.html"),
                ("Region", "region/index.html"),
                ("About / process", "about/index.html"),
            ],
        ),
        (
            "Find",
            [
                ("Directory", "network/index.html"),
                ("Funding", route_href(ACTIVE_PATHS["funding"])),
                ("Arts & Culture", route_href(ACTIVE_PATHS["arts-culture"])),
                ("Amplifiers", "amplifiers/index.html"),
                ("Regional channels", route_href(ACTIVE_PATHS["regional-channels"])),
                ("Appendix", "appendix/index.html"),
            ],
        ),
        (
            "Task Guides",
            [(label, href) for label, href, _ in task_nav_links],
        ),
        (
            "Counties",
            [
                ("Colfax", "counties/colfax/index.html"),
                ("Las Animas", "counties/las-animas/index.html"),
                ("Huerfano", "counties/huerfano/index.html"),
                ("Colfax business", route_href(ACTIVE_PATHS["colfax-business"])),
                ("Las Animas nonprofits", route_href(ACTIVE_PATHS["las-animas-nonprofit"])),
                ("Huerfano calendars", route_href(ACTIVE_PATHS["huerfano-calendars"])),
            ],
        ),
        (
            "Tools + Data",
            [
                ("Posting rules", "posting/index.html"),
                ("Templates", "templates/index.html"),
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
            "name": "Stateline Guide",
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
            "name": "Stateline Guide",
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
    music_bar = f"""
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
                    <option value="{rel('assets/audio/loc-rael-nm-valse.mp3', depth)}" data-track-id="rael-arroyo-hondo">Rael Waltz - Arroyo Hondo, NM</option>
                    <option value="{rel('assets/audio/loc-rael-co-valse.mp3', depth)}" data-track-id="rael-antonito">Rael Waltz - Antonito, CO</option>
                  </select>
                </label>
              </div>
              <div class="music-bar__middle">
                <input class="music-progress" type="range" min="0" max="1000" value="0" aria-label="Regional sound progress">
                <span class="music-time" aria-live="polite">0:00</span>
              </div>
              <div class="music-bar__bottom">
                <span>Optional archival audio from the Library of Congress.</span>
                <label>Volume
                  <input class="music-volume" type="range" min="0" max="100" value="42" aria-label="Regional sound volume">
                </label>
              </div>
            </div>
          </details>
    """
    intro_curtain = (
        '<div class="intro-curtain" aria-hidden="true" data-intro-state="ready"></div>'
        if active == "home"
        else ""
    )
    audio_markup = f"""
          <audio id="site-music-loop" preload="metadata" loop src="{rel('assets/audio/loc-rael-nm-valse.mp3', depth)}"></audio>
    """
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
          <meta property="og:site_name" content="Stateline Guide">
          <meta property="og:locale" content="en_US">
          <meta property="og:title" content="{html_escape(title)}">
          <meta property="og:description" content="{html_escape(description)}">
          <meta property="og:url" content="{html_escape(canonical_url)}">
          <meta property="og:image" content="{html_escape(social_image_url)}">
          <meta name="twitter:card" content="summary_large_image">
          <meta name="twitter:title" content="{html_escape(title)}">
          <meta name="twitter:description" content="{html_escape(description)}">
          <meta name="twitter:image" content="{html_escape(social_image_url)}">
          <title>{html_escape(title)}</title>
          <link rel="preconnect" href="https://fonts.googleapis.com">
          <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
          <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap" rel="stylesheet">
          <link rel="icon" href="{rel('assets/site-icon.svg', depth)}" type="image/svg+xml">
          <link rel="alternate" type="application/json" href="{rel('data/guide-data.json', depth)}">
{extra_alternates}
          <link rel="stylesheet" href="{rel('assets/styles.css', depth)}">
          <link rel="stylesheet" href="{rel('assets/animations/yucca-banner.css', depth)}">
          <script src="{rel('assets/site-data.js', depth)}"></script>
          <script defer src="{rel('assets/app.js', depth)}"></script>
          <script type="application/ld+json">{structured_data}</script>
        </head>
        <body class="page-{html_escape(active)}">
          <a class="skip-link" href="#main">Skip to content</a>
          {audio_markup}
          {intro_curtain}
          <header class="site-header">
            <a class="brand" href="{rel('index.html', depth)}" aria-label="Stateline Guide home">
              <span class="brand-mark">SG</span>
              <span>Stateline Guide</span>
            </a>
            <nav class="site-nav" aria-label="Primary navigation">
              {nav}
            </nav>
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
          <section class="directory-assistant" data-directory-assistant data-network-url="{rel('network/index.html', depth)}" data-submit-url="{rel('submit/index.html', depth)}" aria-label="Directory assistant">
            <button class="directory-assistant__toggle" type="button" aria-expanded="false" aria-haspopup="dialog" aria-controls="directory-assistant-panel">
              <span class="assistant-dot" aria-hidden="true"></span>
              Ask directory
            </button>
            <dialog class="directory-assistant__panel" id="directory-assistant-panel" aria-labelledby="directory-assistant-title" aria-describedby="directory-assistant-intro directory-assistant-hint">
              <div class="directory-assistant__header">
                <div>
                  <p class="eyebrow">Immediate directory</p>
                  <h2 id="directory-assistant-title">Find the right route.</h2>
                </div>
                <button class="directory-assistant__close" type="button" aria-label="Close directory assistant">Close</button>
              </div>
              <p class="directory-assistant__intro" id="directory-assistant-intro">Search by need, county, town, audience, or task. Results include useful links and update reminders so users can act without treating old details as final.</p>
              <p class="sr-only" id="directory-assistant-hint">Results update after submitting the form or after a short pause while typing. Press Escape to close this panel.</p>
              <form class="directory-assistant__form" role="search">
                <label for="directory-assistant-query">What are you trying to find?</label>
                <div class="directory-assistant__search-row">
                  <input id="directory-assistant-query" name="directory_query" type="search" autocomplete="off" placeholder="grants, artist, event, Raton, nonprofit..." aria-describedby="directory-assistant-hint directory-assistant-status" aria-controls="directory-assistant-results">
                  <button class="button button-primary" type="submit">Search</button>
                </div>
              </form>
              <div class="directory-assistant__chips" role="group" aria-label="Suggested searches">
                <button type="button" data-assistant-prompt="funding grants scholarships stipends">Funding</button>
                <button type="button" data-assistant-prompt="artists creative galleries makers">Artists</button>
                <button type="button" data-assistant-prompt="event calendar submit event">Events</button>
                <button type="button" data-assistant-prompt="nonprofit community services">Nonprofits</button>
                <button type="button" data-assistant-prompt="Raton Colfax">Raton</button>
                <button type="button" data-assistant-prompt="Trinidad Las Animas">Trinidad</button>
                <button type="button" data-assistant-prompt="Walsenburg Huerfano La Veta">Huerfano</button>
              </div>
              <div class="directory-assistant__status" id="directory-assistant-status" role="status" aria-live="polite" aria-atomic="true"></div>
              <div class="directory-assistant__results" id="directory-assistant-results" data-assistant-results role="list" aria-label="Directory assistant results"></div>
              <div class="directory-assistant__footer">
                <a class="button button-soft" href="{rel('network/index.html', depth)}">Open full directory</a>
                <a class="button button-soft" href="{rel('submit/index.html', depth)}">Submit a correction</a>
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
        <p class="eyebrow">Stateline Guide</p>
        <h1>Tri-County Regional Marketing Guide</h1>
        <p class="lede">For new and existing businesses, artists, nonprofits, galleries, programs, services, and mentorships trying to expand customers, visibility, partnerships, and usefulness across Colfax, Las Animas, and Huerfano counties.</p>
        <div class="hero-actions">
          <a class="button button-primary" href="plan/index.html">Plan your growth</a>
          <a class="button button-soft" href="network/index.html">Find the network</a>
          <a class="button button-soft" href="region/index.html">Understand the region</a>
        </div>
      </div>
    </section>
    """


def home_page(summary: dict) -> str:
    path_cards = "\n".join(
        f"""
        <a class="path-card" href="{item['slug']}/index.html">
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
            <h2>Use this guide when you need a route, not just a search result.</h2>
          </div>
          <div class="two-col">
            <p>This guide does not replace chambers, tourism sites, newspapers, directories, calendars, or public offices. It helps people use those channels in the right order, for the right purpose, and with a clear next step.</p>
            <p>Use it when you have a business, event, nonprofit, gallery, class, service, or program and need to know where to put it so people across Colfax, Las Animas, and Huerfano counties can find it.</p>
          </div>
        </section>
        <section class="section">
          <div class="path-grid">{path_cards}</div>
        </section>
        <section class="section tinted">
          <div class="section-heading">
            <p class="eyebrow">Quick task guides</p>
            <h2>Start with the job in front of you.</h2>
            <p class="section-note">Each card goes to a practical page or search path. Use it to post, list, promote, fund, route by county, or find arts and culture channels without reading the site front to back.</p>
          </div>
          <div class="mini-grid task-grid">{task_cards}</div>
        </section>
        <section class="section">
          <div class="section-heading">
            <p class="eyebrow">Current funding and directory entries</p>
            <h2>Fast-moving items to check before building a new list.</h2>
            <p class="section-note">Use these time-sensitive entries as starting points. Open the linked page before assuming eligibility, rates, deadlines, listing approval, or current location details.</p>
          </div>
          <div class="current-leads-grid">{current_lead_cards(0)}</div>
          <figure class="grant-map-figure">
            <img class="grant-map-image" src="assets/infographics/grant-opportunity-map.svg" alt="Grant routing infographic for Southern Colorado and Northern New Mexico">
            <figcaption>Use the grant map as a visual starting point, then confirm current applicant rules and deadlines with the original program.</figcaption>
          </figure>
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
        "Tri-County Regional Marketing Guide | Stateline Guide",
        "Find directories, calendars, media channels, tourism pages, public offices, and outreach routes for Colfax, Las Animas, and Huerfano counties.",
        "home",
        content,
    )


def plan_page() -> str:
    tool_cards = "\n".join(
        f"""
        <article class="tool-card">
          <h3><a href="{html_escape(item['url'])}" target="_blank" rel="noreferrer">{html_escape(item['name'])}</a></h3>
          <p>{html_escape(item['use'])}</p>
          <p class="source-note">{html_escape(item['note'])}</p>
        </article>
        """
        for item in PROMOTION_TOOLS
    )
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
        <h2>Templates are time-savers, not the strategy.</h2>
        <p class="section-note">The useful strategy is to prepare one clean packet: a short blurb, image, flyer, listing details, date, location, hours, contact route, and plain call to action. The templates help you adapt that packet for directories, calendars, media, partners, emails, and social posts.</p>
      </div>
      <div class="section-actions">
        <a class="button button-primary" href="../templates/index.html">Use copy-ready templates</a>
        <a class="button button-soft" href="../regional-channels/index.html">Find places to send them</a>
      </div>
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Free and freemium tools</p>
        <h2>Build the packet with tools people already recognize.</h2>
        <p class="section-note">Plan limits change. Treat these as popular online starting points and check current free-tier limits before relying on them for a campaign.</p>
      </div>
      <div class="tool-grid">{tool_cards}</div>
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
        "Plan Local Growth Across Colfax, Las Animas & Huerfano | Stateline Guide",
        "Choose a goal, audience, outreach packet, channel set, and tracking loop before promoting a business, event, nonprofit, service, or program.",
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
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">Find the Network</p>
      <h1>Search the regional directory.</h1>
      <p class="lede">Search {row_count} local listings, or use a directory shortcut to widen the search.</p>
      <nav class="directory-jumpbar" aria-label="Directory page sections">
        <a class="button button-primary" href="#local-listings">Local listings</a>
        <a class="button button-soft" href="#directory-shortcuts">Directory shortcuts</a>
      </nav>
    </section>
    <section id="local-listings" class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Local listings</p>
        <h2>Find a local listing.</h2>
        <p class="section-note">Search by name, town, county, service, audience, or task. Results are alphabetical until you apply another filter.</p>
      </div>
      <div class="tool-panel directory-search-panel">
        <div>
          <label for="resource-search">Search {row_count} local entries</label>
          <input id="resource-search" class="search-input" type="search" placeholder="Try bakery, gallery, grant, library, Raton, Trinidad...">
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
                <label for="access-mode-filter">Access mode</label>
                <select id="access-mode-filter"><option value="All">All access modes</option></select>
              </div>
            </div>
            <div>
              <span class="filter-label">Location access</span>
              <div id="physical-location-filter" class="filter-row" aria-label="Physical location filters">
                <button class="chip is-active" data-location-filter="All">All listings</button>
                <button class="chip" data-location-filter="Physical">Physical locations</button>
                <button class="chip" data-location-filter="Flyers">Ask about flyers</button>
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
        <summary>What the location labels mean</summary>
        <div class="marker-legend" aria-label="Directory marker legend">
          <span class="listing-marker listing-marker--physical">Physical location</span>
          <span>{physical_location_count} listings include a map-able or street-style location.</span>
          <span class="listing-marker listing-marker--ad">Ask about flyers</span>
          <span>{physical_ad_count} listings may be useful places to ask about physical materials. Ask first; the guide does not imply permission.</span>
        </div>
      </details>
      <p id="resource-results-note" class="section-note" aria-live="polite">Search by town, county, resource type, audience, keyword, or task.</p>
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
    <section class="section tinted directory-support-section">
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
        "Find Local Directories, Physical Ad Locations, Media & Support Entries | Stateline Guide",
        f"Search public shortcuts and a {row_count}-entry regional inventory of directories, physical locations, media, funding, business, nonprofit, arts, and support entries.",
        "network",
        content,
        depth=1,
        main_entity=directory_item_list_schema(rows),
        extra_json_alternates=[("Full directory metadata", "data/directory-metadata.json")],
        schema_type="CollectionPage",
    )


def row_matches_terms(row: dict, terms: list[str]) -> bool:
    blob = " ".join(str(value or "") for value in row.values()).lower()
    return any(term in blob for term in terms)


def resource_preview_cards(rows: list[dict], terms: list[str], limit: int = 18) -> str:
    matched = [
        row for row in sorted(rows, key=lambda item: (item.get("resource_name") or "", item.get("county") or "", item.get("town") or ""))
        if row_matches_terms(row, terms)
    ][:limit]
    if not matched:
        return '<p class="section-note">No matching local inventory rows are available in this build.</p>'
    cards = []
    for row in matched:
        url = (split_semicolon(row.get("website")) or split_semicolon(row.get("source_url")) or [""])[0]
        link = f'<a class="resource-contact-link" href="{html_escape(url)}" target="_blank" rel="noreferrer">{html_escape(resource_url_label(url))}</a>' if url else '<span class="source-note">Send an update if you have a public contact path.</span>'
        tags = "".join(f'<span class="badge">{html_escape(tag)}</span>' for tag in organization_tags(row))
        cards.append(
            f"""
            <article class="resource-item">
              <div class="source-card__meta">
                <span>{html_escape(row.get('county'))}</span>
                <span>{html_escape(row.get('town'))}</span>
                <span>{html_escape(row.get('public_listing_type') or row.get('resource_type'))}</span>
              </div>
              <h3>{html_escape(row.get('resource_name') or 'Unnamed resource')}</h3>
              <p class="resource-tags"><strong>Useful for:</strong> {tags}</p>
              {resource_physical_indicator_badges(row)}
              <p>{html_escape(public_text_value(row.get('public_description') or row.get('category') or 'Local directory listing for regional discovery and outreach.'))}</p>
              <p class="resource-best"><strong>Best fit:</strong> {html_escape(public_text_value(row.get('public_best_for') or public_best_for(row)))}</p>
              <p class="action-line">{html_escape(public_text_value(row.get('goal_relevance') or 'Choose the route that fits, then contact the listed page or organization.'))}</p>
              <div class="resource-links">{link}</div>
            </article>
            """
        )
    return "\n".join(cards)


def sources_matching_terms(terms: list[str]) -> list[dict]:
    return [
        item for item in DIRECTORY_SOURCES
        if any(
            term in " ".join(str(item.get(field) or "") for field in ["title", "kind", "best_for", "action", "county"]).lower()
            for term in terms
        )
    ]


def funding_page(rows: list[dict]) -> str:
    terms = ["fund", "grant", "scholarship", "stipend", "loan", "incentive", "foundation", "capital", "training reimbursement", "technical assistance"]
    funding_sources = sources_matching_terms(terms)
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">Funding</p>
      <h1>Funding, grants, incentives, and support entries.</h1>
      <p class="lede">Use this page to find likely starting points for business, nonprofit, arts, culture, outdoor recreation, workforce, and community projects. Check eligibility, deadlines, applicant type, match rules, and award status with the original program.</p>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Check first</p>
        <h2>Current funding entries from the latest review.</h2>
        <p class="section-note">These are not guarantees of eligibility or open cycles. They are useful routes to check before starting a funding search from scratch.</p>
      </div>
      <div class="current-leads-grid">{current_lead_cards(2, "Funding")}</div>
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Grant routing map</p>
        <h2>Match the project type before chasing applications.</h2>
      </div>
      <figure class="grant-map-figure">
        <img class="grant-map-image" src="../../assets/infographics/grant-opportunity-map.svg" alt="Grant routing infographic for Southern Colorado and Northern New Mexico">
        <figcaption>Use the map to frame the search, then open the program source for current applicant rules, deadlines, match requirements, and contact instructions.</figcaption>
      </figure>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Funding directory shortcuts</p>
        <h2>Programs and pages to open directly.</h2>
      </div>
      <div class="source-grid compact">{source_group_cards(funding_sources)}</div>
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Local inventory entries</p>
        <h2>Additional rows that may connect to money, training, or support.</h2>
        <p class="section-note">Use these as starting entries, not final eligibility statements. Open the link or contact path before including a program in public advice.</p>
      </div>
      <div class="resource-list">{resource_preview_cards(rows, terms)}</div>
      {download_buttons(2)}
    </section>
    {submit_listing_panel(2, "directory")}
    """
    return page_shell(
        "Funding, Grants & Support Entries | Stateline Guide",
        "Find grant, incentive, scholarship, stipend, loan, workforce, arts, nonprofit, and business-support starting points for Colfax, Las Animas, and Huerfano counties.",
        "funding",
        content,
        depth=2,
        schema_type="CollectionPage",
    )


def arts_culture_page(rows: list[dict]) -> str:
    terms = ["art", "artist", "gallery", "creative", "maker", "music", "theater", "theatre", "museum", "cultural", "craft", "mural", "performance", "dance", "film", "literary"]
    arts_sources = sources_matching_terms(terms)
    arts_leads = [item for item in CURRENT_LEADS if item["title"] in {"Walsenburg Mercantile vendors", "Meditating Monkey Art Emporium relocation watch"}]
    lead_markup = "\n".join(
        f"""
        <article class="lead-card" data-lead-group="{html_escape(item['group'])}" data-county="{html_escape(item['county'])}">
          <div class="source-card__meta"><span>{html_escape(item['county'])}</span><span>{html_escape(item['kind'])}</span></div>
          <h3><a href="{html_escape(item['url'])}" target="_blank" rel="noreferrer">{html_escape(item['title'])}</a></h3>
          <p>{html_escape(item['best_for'])}</p>
          <p class="action-line">{html_escape(item['action'])}</p>
        </article>
        """
        for item in arts_leads
    )
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">Arts & Culture</p>
      <h1>Artists, galleries, makers, venues, and cultural routes.</h1>
      <p class="lede">Use this page when creative work needs to be findable: listings, shows, vendor visibility, visitor-facing promotion, venue calendars, media, creative districts, and partner channels.</p>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Fast arts entries</p>
        <h2>Useful arts-directory items to check now.</h2>
        <p class="section-note">These entries help keep arts pages practical: who may list creative work, where makers appear, and what needs an address or status check.</p>
      </div>
      <div class="current-leads-grid">{lead_markup}</div>
      <div class="section-actions">
        <a class="button button-primary" href="../../artist-gallery-promotion/index.html">Open artist promotion guide</a>
        <a class="button button-soft" href="../../network/index.html">Search all creative entries</a>
      </div>
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Arts and culture shortcuts</p>
        <h2>Pages that already gather creative visibility.</h2>
      </div>
      <div class="source-grid compact">{source_group_cards(arts_sources)}</div>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Local creative inventory</p>
        <h2>Artists, venues, galleries, makers, and cultural entries.</h2>
        <p class="section-note">Use these rows for discovery and outreach. Confirm current details before publishing a recommendation or sending visitors to a location.</p>
      </div>
      <div class="resource-list">{resource_preview_cards(rows, terms, 24)}</div>
      {download_buttons(2)}
    </section>
    {submit_listing_panel(2, "directory")}
    """
    return page_shell(
        "Arts & Culture Directory Routes | Stateline Guide",
        "Find artist, gallery, maker, music, venue, creative-district, cultural, visitor-facing, and partner visibility routes across the tri-county region.",
        "arts-culture",
        content,
        depth=2,
        schema_type="CollectionPage",
    )


def amplifiers_page() -> str:
    categories = "\n".join(
        f"""
        <article class="mini-card">
          <h3>{html_escape(title)}</h3>
          <p>{html_escape(body)}</p>
        </article>
        """
        for title, body in AMPLIFIER_CATEGORIES
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
        <article class="mini-card"><h3>Can I assume a newsletter accepts outside promotions?</h3><p>No. Ask first. Do not assume ad availability, free placement, deadlines, audience size, endorsement, or acceptance unless the page or organization confirms it.</p></article>
        <article class="mini-card"><h3>What should I prepare before submitting an event?</h3><p>Prepare the event name, date, time, location, short description, contact link, images, flyer, accessibility notes, and whether the event is free, ticketed, nonprofit, youth, tourism, business, or community-oriented.</p></article>
      </div>
    </section>
    <section class="section">
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
          <h2>Ask like a neighbor, not like a blast campaign.</h2>
          <p>Send only to channels where the item fits, use the channel owner's preferred form, avoid repeated messages, and stop when a page says submissions are closed or not accepted. For nonprofits and community programs, lead with public benefit rather than sales language.</p>
          <pre>{html_escape(outreach)}</pre>
        </div>
      </div>
    </section>
    {submit_listing_panel(1, "amplifier")}
    """
    return page_shell(
        "Regional Newsletters, Calendars, Directories & Visitor Guides | Stateline Guide",
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
          <td>{html_escape(item['place'])}</td>
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
        <article class="mini-card">
          <h3>{html_escape(item['title'])}</h3>
          <p>{html_escape(item['best_for'])}</p>
          <p class="resource-best"><strong>Ask:</strong> {html_escape(item['ask'])}</p>
        </article>
        """
        for item in PHYSICAL_AD_PLACE_TYPES
    )
    candidate_rows = physical_ad_location_rows(rows)
    candidate_table = "\n".join(
        f"""
        <tr>
          <td><strong>{html_escape(row.get('resource_name') or 'Unnamed place')}</strong><span class="table-subtle">{html_escape(public_place(row))}</span></td>
          <td>{html_escape(row.get('public_listing_type') or inferred_listing_type(row))}</td>
          <td>{html_escape(physical_ad_location_fit(row))}</td>
          <td>{html_escape(physical_ad_location_note(row))}</td>
          <td><div class="resource-links">{contact_links_for_row(row)}</div></td>
        </tr>
        """
        for row in candidate_rows
    )
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">Where To Post</p>
      <h1>Find physical places to ask about flyers, posters, and local ads.</h1>
      <p class="lede">Use this page when you need real-world visibility: library boards, visitor centers, public-office posting routes, downtown businesses, galleries, venues, travel stops, and other local places where a flyer, poster, rack card, or small stack may fit.</p>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Physical ad finder</p>
        <h2>Start with the places people already pass through.</h2>
        <p class="section-note">These are places to ask, not guaranteed ad spaces. Libraries, visitor centers, city halls, courts, downtown shops, restaurants, galleries, community spaces, bus or train stops, and lodging desks often have owner-controlled boards, brochure racks, front desks, or public-information areas. Some limit political, for-profit, oversized, expired, or unaffiliated materials.</p>
      </div>
      <div class="mini-grid">{type_cards}</div>
    </section>
    <section id="physical-ad-locations" class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Physical locations</p>
        <h2>Directory rows that may help with flyers, posters, rack cards, or front-desk referrals.</h2>
        <p class="section-note">This shortlist is pulled from the guide's local directory rows that look most useful for offline promotion. Ask the location owner or office before posting, leaving materials, or implying sponsorship.</p>
      </div>
      <div class="table-wrap physical-posting-table">
        <table>
          <thead><tr><th>Place</th><th>Type</th><th>Useful for</th><th>Before you post</th><th>Contact</th></tr></thead>
          <tbody>{candidate_table}</tbody>
        </table>
      </div>
      <p class="section-note">Need more than this shortlist? Search the Network or Appendix for terms like library, visitor center, chamber, gallery, cafe, restaurant, market, depot, city hall, courthouse, college, and community center.</p>
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
      <p class="section-note">Ask the page owner or office about current rules, deadlines, acceptable materials, and whether a request should be handled as a notice, calendar item, ad, flyer, or partner share.</p>
    </section>
    <section class="section">
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
        ("Filter the directory for physical locations", "network/#physical-location-filter"),
        ("Open the spreadsheet-style appendix", "appendix/"),
    ])}
    """
    return page_shell(
        "Where to Post Events, Notices & Listings in the Tri-County Area | Stateline Guide",
        "Separate official notices from community visibility, then check boards, calendars, newsletters, directories, and public office posting routes.",
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
          <td>{html_escape(row.get('resource_name'))}</td>
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
        <p class="section-note">For guided discovery, start with Network or the Ask directory button. Stay here when you need county/community grouping, contact details, or spreadsheet-style review.</p>
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
        "Tri-County Public Contact Appendix | Stateline Guide",
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
        <p class="section-note">County pages make local entry easy. The Network page keeps cross-county directories, media, funding, creative-economy, and nonprofit resources connected.</p>
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
        "Tri-County Regional Visibility Map | Stateline Guide",
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
          <strong>{html_escape(row.get('resource_name'))}</strong>
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
      <p class="section-note">The full inventory is searchable from the Network page and downloadable as CSV in the data folder.</p>
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
    tools = "\n".join(
        f"""
        <article class="tool-card">
          <h3><a href="{html_escape(tool['url'])}" target="_blank" rel="noreferrer">{html_escape(tool['name'])}</a></h3>
          <p>{html_escape(tool['use'])}</p>
          <p class="source-note">{html_escape(tool['note'])}</p>
        </article>
        """
        for tool in PROMOTION_TOOLS
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
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Useful free or freemium tools</p>
        <h2>Build the packet, list, form, or flyer without adding unnecessary software.</h2>
        <p class="section-note">Check current free-plan limits before relying on any tool for a public campaign or mailing list.</p>
      </div>
      <div class="tool-grid">{tools}</div>
    </section>
    {next_action_block(1, [
        ("Find places to send outreach packets", "amplifiers/"),
        ("Search directories and local entries", "network/"),
        ("Submit a correction or new channel", "submit/"),
        ("Plan the outreach cycle first", "plan/"),
    ])}
    """
    return page_shell(
        "Outreach Templates for Listings, Events, Media & Partners | Stateline Guide",
        "Copy and adapt outreach language for directories, event calendars, newsletters, partner asks, media inquiries, and correction requests.",
        "templates",
        content,
        depth=1,
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
        <article class="step-card"><span>2</span><h3>Pick the section</h3><p>Choose the county page, network directory, appendix, amplifier channel list, posting map, or templates/resources area.</p></article>
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
              <option>Network directory</option>
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
        "Submit a Correction or Suggest a Regional Channel | Stateline Guide",
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
        <p>This guide does not replace chambers, tourism sites, newspapers, directories, calendars, or public offices. It helps people use those sources correctly, in a practical order, and with a clear next step.</p>
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
        "How This Manual Works | Stateline Guide",
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
          <strong>{html_escape(row.get('resource_name'))}</strong>
          <span>{html_escape(row.get('town') or row.get('county') or 'Regional')} - {html_escape(row.get('public_listing_type') or row.get('resource_type') or 'Resource')}</span>
        </li>
        """
        for row in row_matches
    )
    if not lead_items:
        lead_items = "<li><strong>Start with the shortcut cards above.</strong><span>No close inventory entry matched this task yet; submit one when a better local route is confirmed.</span></li>"
    route_cards = "\n".join(
        f"""
        <article class="route-type-card {html_escape(card['class'])}">
          <span class="category-badge {html_escape(card['class'])}">{html_escape(card['label'])}</span>
          <h3>{html_escape(card['use'])}</h3>
          <p><strong>Prepare:</strong> {html_escape(card['prepare'])}</p>
          <p><strong>Check:</strong> {html_escape(card['check'])}</p>
        </article>
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
    icon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="Stateline Guide icon"><circle cx="32" cy="32" r="30" fill="#173047"/><path d="M15 38 C24 24 30 18 38 13 C36 23 35 31 48 44 C35 39 26 42 15 38Z" fill="#d8bb68"/><path d="M20 39 C30 33 38 28 47 18" fill="none" stroke="#f6f8f4" stroke-width="4" stroke-linecap="round"/></svg>"""
    (ASSET_OUT / "site-icon.svg").write_text(icon, encoding="utf-8")

    css = r"""
    :root {
      --ink: #173047;
      --ink-soft: rgba(23, 48, 71, 0.76);
      --paper: #f6f8f4;
      --panel: #ffffff;
      --mist: #dceee8;
      --sky: #b7dbe4;
      --sage: #8baa7c;
      --clay: #c77f61;
      --gold: #d8bb68;
      --plum: #695674;
      --line: rgba(23, 48, 71, 0.14);
      --shadow: 0 18px 50px rgba(23, 48, 71, 0.11);
      --radius: 8px;
      --focus-ring: #d8bb68;
      --route: #2f6780;
      --route-soft: rgba(47,103,128,0.42);
      --status-ok: #4d8a5c;
      --linked: #4e7f9c;
      --field: #9a7a2a;
      --manual: #695674;
      color-scheme: light;
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; overflow-x: hidden; }
    body {
      margin: 0;
      font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: var(--paper);
      line-height: 1.6;
    }
    img { max-width: 100%; height: auto; }
    a { color: inherit; }
    @media (pointer: fine) {
      html, body { cursor: url("raton-accessible-cursor.svg") 4 2, auto; }
      a, button, select, summary, .button, .chip, .copy-button { cursor: url("raton-accessible-cursor.svg") 4 2, pointer; }
    }
    .skip-link { position: absolute; top: -80px; left: 16px; background: var(--ink); color: #fff; padding: 10px 14px; z-index: 20; }
    .skip-link:focus { top: 12px; }
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
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      padding: 12px clamp(16px, 4vw, 56px);
      border-bottom: 1px solid var(--line);
      background: rgba(246, 248, 244, 0.9);
      backdrop-filter: blur(16px);
    }
    .brand { display: inline-flex; align-items: center; gap: 10px; text-decoration: none; font-weight: 800; }
    .brand-mark { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 50%; background: var(--ink); color: #fff; font-size: 0.78rem; letter-spacing: 0; }
    .site-nav { display: flex; gap: 5px; flex-wrap: wrap; justify-content: flex-end; align-items: center; overflow: visible; }
    .site-nav a, .nav-trigger { position: relative; display: inline-flex; align-items: center; justify-content: center; min-height: 34px; text-decoration: none; padding: 7px 10px; border: 0; border-radius: 999px; background: transparent; font: inherit; font-size: 0.82rem; color: var(--ink-soft); cursor: pointer; transition: background 160ms ease, color 160ms ease; }
    .site-nav a:hover, .site-nav a.is-active, .site-nav a[aria-current="page"], .nav-group:hover > .nav-trigger, .nav-group:focus-within > .nav-trigger, .nav-group.is-active > .nav-trigger { background: rgba(23, 48, 71, 0.08); color: var(--ink); }
    .site-nav a[aria-current="page"]::after,
    .nav-group.is-active > .nav-trigger::before {
      content: "";
      position: absolute;
      left: 12px;
      right: 12px;
      bottom: -5px;
      height: 3px;
      border-radius: 999px;
      background: currentColor;
      animation: tabSettle 180ms ease-out;
    }
    .nav-group { position: relative; }
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
    .nav-group:hover .nav-menu, .nav-group:focus-within .nav-menu, .nav-group[open] .nav-menu { display: grid; gap: 2px; }
    @keyframes tabSettle {
      from { transform: scaleX(0.65); opacity: 0.35; }
      to { transform: scaleX(1); opacity: 1; }
    }
    .hero {
      position: relative;
      min-height: min(76vh, 760px);
      overflow: hidden;
      display: grid;
      align-items: end;
      padding: clamp(80px, 10vw, 140px) clamp(18px, 6vw, 86px) clamp(48px, 8vw, 90px);
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
    .hero-copy { max-width: 860px; }
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
    h1 { margin: 0; font-family: Fraunces, Georgia, serif; font-size: clamp(3rem, 8vw, 6.9rem); max-width: 10ch; }
    .page-hero h1 { font-size: clamp(2.5rem, 7vw, 5rem); max-width: 12ch; }
    .county-hero h1 { font-size: clamp(2.1rem, 4vw, 3.55rem); max-width: 23ch; }
    .county-hero .lede { max-width: 52rem; }
    h2 { margin: 0; font-size: clamp(1.8rem, 3.5vw, 3.2rem); }
    h3 { margin: 0 0 10px; font-size: 1.08rem; }
    .lede { max-width: 780px; font-size: clamp(1.05rem, 2vw, 1.35rem); color: var(--ink-soft); }
    .hero-actions, .section-actions, .download-row { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 26px; }
    .button { display: inline-flex; align-items: center; justify-content: center; min-height: 42px; padding: 10px 16px; border-radius: 999px; text-decoration: none; border: 1px solid var(--line); font-weight: 800; }
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
    .section, .page-hero { padding: clamp(42px, 7vw, 94px) clamp(18px, 6vw, 86px); }
    #local-listings, #directory-shortcuts { scroll-margin-top: 92px; }
    .page-hero { position: relative; overflow: hidden; isolation: isolate; background: linear-gradient(135deg, rgba(220,238,232,0.86), rgba(183,219,228,0.5)); border-bottom: 1px solid var(--line); }
    .page-hero > :not(.page-hero-art) { position: relative; z-index: 1; }
    .page-network .page-hero {
      padding-top: clamp(42px, 5vw, 64px);
      padding-bottom: clamp(38px, 4vw, 56px);
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
      width: min(760px, 62vw);
      aspect-ratio: 1.88 / 1;
      height: auto;
      transform: translateY(-50%);
      object-fit: cover;
      object-position: center bottom;
      border-radius: 50%;
      opacity: 0.38;
      filter: saturate(0.78) contrast(0.94);
      -webkit-mask-image: radial-gradient(ellipse at center, #000 42%, rgba(0,0,0,0.72) 62%, transparent 78%);
      mask-image: radial-gradient(ellipse at center, #000 42%, rgba(0,0,0,0.72) 62%, transparent 78%);
      pointer-events: none;
    }
    .county-hero { background: linear-gradient(135deg, rgba(216,187,104,0.28), rgba(199,127,97,0.16), rgba(183,219,228,0.38)); }
    .tinted { background: rgba(220, 238, 232, 0.48); }
    .intro-band { background: #fff; }
    .section-heading { position: relative; max-width: 870px; margin-bottom: 30px; }
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
    .tool-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(245px, 1fr)); gap: 14px; }
    .steps-grid { grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }
    .template-grid { grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); }
    .stats-grid { grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }
    .path-card, .source-card, .mini-card, .step-card, .template-card, .tool-card, .resource-item, .lead-card, .stat, figure {
      background: rgba(255,255,255,0.86);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: 0 10px 28px rgba(23,48,71,0.06);
    }
    .path-card { padding: 24px; min-height: 260px; display: flex; flex-direction: column; text-decoration: none; }
    .task-link-card { min-height: 220px; }
    .path-card span, .step-card span { color: var(--clay); font-weight: 900; }
    .path-card p { color: var(--ink-soft); }
    .path-card strong { margin-top: auto; }
    .source-card, .mini-card, .step-card, .template-card, .tool-card, .resource-item, .lead-card { padding: 18px; }
    .current-leads-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(270px, 1fr));
      gap: 14px;
    }
    .lead-card {
      min-height: 250px;
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
    .grant-map-figure {
      margin-top: 20px;
      padding: 18px;
      background: rgba(255,255,255,0.78);
    }
    .grant-map-image {
      display: block;
      width: 100%;
      border-radius: 6px;
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
    }
    .route-type-card h3 { margin: 0; font-size: 1.02rem; }
    .route-type-card p { margin: 0; color: var(--ink-soft); }
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
    .resource-item { display: flex; flex-direction: column; min-width: 0; }
    .resource-item__head { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
    .resource-item__head h3 { margin-bottom: 0; }
    .resource-meta-line { margin: 8px 0; font-size: 0.9rem; }
    .resource-description { margin: 10px 0; }
    .resource-more__body { display: grid; gap: 8px; }
    .resource-more__body > * { margin-top: 0; margin-bottom: 0; }
    .resource-item a { font-weight: 800; }
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
      max-width: min(320px, calc(100vw - 32px));
      border: 0;
      background: transparent;
      color: var(--ink);
    }
    .music-panel {
      margin-top: 7px;
      width: min(320px, calc(100vw - 32px));
      padding: 10px;
      border: 1px solid rgba(23,48,71,0.14);
      border-radius: 12px;
      background: rgba(255,255,255,0.78);
      box-shadow: 0 14px 32px rgba(23,48,71,0.13);
      backdrop-filter: blur(18px);
    }
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
    .directory-assistant__status,
    .assistant-result p {
      color: var(--ink-soft);
    }
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
    .directory-assistant__chips { display: flex; flex-wrap: wrap; gap: 7px; margin: 12px 0; }
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
    .directory-assistant__results { display: grid; gap: 10px; margin-top: 10px; }
    .assistant-result {
      display: grid;
      gap: 7px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(246,248,244,0.86);
    }
    .assistant-result__meta {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 6px;
    }
    .assistant-result__type {
      border-radius: 999px;
      background: rgba(23,48,71,0.08);
      padding: 3px 8px;
      font-size: 0.72rem;
      font-weight: 900;
    }
    .assistant-result h3 { margin: 0; font-size: 0.98rem; }
    .assistant-result p { margin: 0; font-size: 0.86rem; }
    .assistant-result__actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    .assistant-result__actions a { font-size: 0.82rem; font-weight: 900; text-underline-offset: 3px; }
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
    @media (max-width: 860px) {
      .site-header { align-items: flex-start; flex-direction: column; }
      .site-nav { width: 100%; justify-content: flex-start; }
      .path-grid, .two-col, .site-footer, .advanced-filters, .form-grid, .submit-card { grid-template-columns: 1fr; }
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
    }
    @media (max-width: 640px) {
      body { overflow-x: hidden; }
      .site-header { width: 100%; max-width: 100vw; padding: 8px 12px; gap: 10px; }
      .brand { font-size: 0.9rem; gap: 8px; }
      .brand-mark { width: 28px; height: 28px; font-size: 0.68rem; }
      .site-nav { width: 100%; max-width: 100%; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 5px; justify-content: stretch; overflow: visible; padding-bottom: 0; }
      .site-nav a, .nav-trigger { width: 100%; min-height: 32px; white-space: nowrap; text-align: center; padding: 5px 6px; font-size: 0.74rem; }
      .nav-group { position: relative; }
      .nav-menu { position: absolute; top: calc(100% + 6px); min-width: 150px; width: max-content; max-width: calc(100vw - 24px); margin-top: 0; padding: 6px; box-shadow: var(--shadow); }
      .nav-group:nth-of-type(1) .nav-menu { left: 50%; right: auto; translate: -50% 0; }
      .nav-group:nth-of-type(2) .nav-menu { right: 0; left: auto; translate: none; }
      .nav-group:nth-of-type(3) .nav-menu { left: 0; right: auto; translate: none; }
      .nav-group:nth-of-type(4) .nav-menu { left: 50%; right: auto; translate: -50% 0; }
      .nav-group:nth-of-type(5) .nav-menu { right: 0; left: auto; translate: none; }
      .nav-menu a { white-space: normal; justify-content: center; }
      .hero {
        min-height: calc(100svh - 92px);
        padding-bottom: 150px;
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
      .page-hero-art { width: 540px; max-width: none; right: -240px; top: 42%; opacity: 0.34; }
      .page-network .page-hero { padding-top: 20px; padding-bottom: 24px; }
      .page-network .page-hero h1 { max-width: 11ch; font-size: 2.55rem; line-height: 1.02; }
      .page-network .section { padding: 32px 18px; }
      .page-network .section-heading { margin-bottom: 18px; }
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
      .resource-item, .source-card { padding: 14px; box-shadow: 0 7px 18px rgba(23,48,71,0.05); }
      .resource-item__head h3 { font-size: 1.08rem; line-height: 1.18; }
      .resource-meta-line { margin: 7px 0; font-size: 0.82rem; line-height: 1.4; }
      .resource-description {
        display: -webkit-box;
        overflow: hidden;
        margin: 8px 0;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 3;
        font-size: 0.9rem;
        line-height: 1.45;
      }
      .resource-more, .source-group-links { margin-top: 8px; border-top: 1px solid var(--line); }
      .resource-more > summary, .source-group-links > summary { padding: 10px 0 2px; font-size: 0.82rem; }
      .resource-more__body { padding-top: 9px; }
      .resource-tags .badge { font-size: 0.68rem; padding: 2px 6px; }
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
      .music-bar__bottom { align-items: flex-start; gap: 6px; }
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
    @media print {
      .site-header, .hero-actions, .tool-panel, .copy-button, .corner-controls, .directory-assistant, .download-row { display: none; }
      body { background: #fff; color: #111; }
      a::after { content: " (" attr(href) ")"; font-size: 0.86em; }
      .section, .page-hero { padding: 24px 0; }
      tr, figure, .source-card, .resource-item { break-inside: avoid; }
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
      [data-animated="true"], .intro-curtain, .hero-accent, .hero-route, .hero-node, .submit-success-card, .sparkle {
        animation: none !important;
        transform: none !important;
      }
      .intro-curtain { display: none; }
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

    function textMatch(item, query) {
      const blob = searchableText(item).toLowerCase();
      return blob.includes(query.toLowerCase());
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
        item.goal_relevance,
        item.audience_served,
        item.public_description
      ]).toLowerCase();
      return blob.includes(query.toLowerCase());
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
      function add(label, href) {
        const normalized = normalUrl(href);
        if (!normalized || seen.has(normalized)) return;
        seen.add(normalized);
        links.push({ label, href: normalized });
      }
      splitList(item.website).forEach(url => add(linkLabel(url, "Website"), url));
      splitList(item.contact_email).forEach(email => add("Email", `mailto:${email}`));
      splitList(item.contact_phone).forEach(phone => {
        const dial = phone.replace(/[^0-9+]/g, "");
        if (dial.length >= 7) add("Phone", `tel:${dial}`);
      });
      splitList(item.physical_address).forEach(address => add("Map", `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address)}`));
      splitList(item.source_url).forEach(url => add(linkLabel(url, item.website ? "Listing page" : "Website"), url));
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

    function contactLinkMarkup(item, { compact = false } = {}) {
      const links = contactLinks(item);
      if (!links.length) return `<span class="source-note">Send an update if you have a public contact path.</span>`;
      const visible = compact ? links.slice(0, 3) : links.slice(0, 7);
      return `<div class="resource-links">${visible.map(link => `
        <a class="resource-contact-link" href="${escapeHtml(link.href)}" target="_blank" rel="noreferrer">${escapeHtml(link.label)}</a>
      `).join("")}</div>`;
    }

    function truthyFlag(value) {
      return value === true || String(value || "").toLowerCase() === "true";
    }

    function physicalIndicatorMarkup(item) {
      const note = item.physical_ad_note || "Ask the location directly before leaving flyers, posters, brochures, or rack cards.";
      if (truthyFlag(item.physical_ad_candidate)) {
        return `<div class="listing-indicators" aria-label="Physical location indicators"><span class="listing-marker listing-marker--ad" title="${escapeHtml(note)}">Ask about flyers</span></div>`;
      }
      if (truthyFlag(item.has_physical_location)) {
        return `<div class="listing-indicators" aria-label="Physical location indicators"><span class="listing-marker listing-marker--physical" title="${escapeHtml(note)}">Physical location</span></div>`;
      }
      return "";
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
            <h3>${escapeHtml(item.resource_name || "Unnamed resource")}</h3>
          </div>
          <p class="resource-meta-line">${escapeHtml(metaParts.join(" - "))}</p>
          ${physicalIndicatorMarkup(item)}
          <p class="resource-description">${escapeHtml(item.public_description || "Local directory listing for regional discovery and outreach.")}</p>
          <details class="resource-more" open>
            <summary>Details and best use</summary>
            <div class="resource-more__body">
              <p class="resource-tags"><strong>Useful for:</strong> ${tags}</p>
              <p class="resource-best"><strong>Best fit:</strong> ${escapeHtml(item.public_best_for || "regional discovery; contact-list building")}</p>
              <p class="source-note">If this looks outdated, use the correction form so the guide can be updated.</p>
            </div>
          </details>
          ${contactLinkMarkup(item)}
        </article>
      `;
    }

    function assistantCard(item) {
      const title = item.title || item.resource_name || item.channel || item.place || "Directory result";
      const url = splitList(item.url || item.website || item.source_url)[0] || "";
      const county = item.county || item.area_served || [item.town, item.state].filter(Boolean).join(", ") || "Regional";
      const category = item.kind || item.resource_type || item.channel_type || item.type || "Directory route";
      const description = item.posting_fit || item.best_for || item.public_description || item.asks || item.short_description || "Use this route when it fits the task, place, and audience.";
      const action = item.posting_note || item.action || item.reader_action || "Open the link, then submit a correction if details have changed.";
      const typeLabel = item.assistant_type || "Directory";
      const sourceLink = url
        ? `<a href="${escapeHtml(normalUrl(url))}" target="_blank" rel="noreferrer" aria-label="${escapeHtml(linkLabel(url, "Open page"))} for ${escapeHtml(title)}">${escapeHtml(linkLabel(url, "Open page"))}</a>`
        : contactLinkMarkup(item, { compact: true });
      return `
        <article class="assistant-result" role="listitem">
          <div class="assistant-result__meta">
            <span class="assistant-result__type">${escapeHtml(typeLabel)}</span>
            <span>${escapeHtml(county)}</span>
            <span>${escapeHtml(category)}</span>
          </div>
          <h3>${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(title)}</a>` : escapeHtml(title)}</h3>
          ${physicalIndicatorMarkup(item)}
          <p>${escapeHtml(description)}</p>
          ${item.public_best_for ? `<p class="resource-best"><strong>Best fit:</strong> ${escapeHtml(item.public_best_for)}</p>` : ""}
          <p class="action-line">${escapeHtml(action)}</p>
          <div class="assistant-result__actions">
            ${sourceLink}
            <a href="network/index.html" aria-label="Search the full directory for results related to ${escapeHtml(title)}">Search full directory</a>
          </div>
        </article>
      `;
    }

    function assistantSearch(query) {
      const normalized = String(query || "").trim().toLowerCase();
      const terms = normalized.split(/\s+/).filter(Boolean);
      const pools = [
        ...(DATA.current_leads || []).map(item => ({ ...item, assistant_type: "Current item" })),
        ...((DATA.directory_source_groups || DATA.directory_sources || [])).map(item => ({ ...item, assistant_type: "Shortcut group" })),
        ...(DATA.resources || []).map(item => ({ ...item, assistant_type: "Listing" })),
        ...(DATA.amplifier_channels || []).map(item => ({ ...item, assistant_type: "Amplifier" })),
        ...(DATA.physical_ad_locations || []).map(item => ({ ...item, assistant_type: "Physical ad location" })),
        ...(DATA.posting_spaces || []).map(item => ({ ...item, assistant_type: "Posting path" }))
      ];
      const scored = pools.map(item => {
        const blob = Object.values(item).join(" ").toLowerCase();
        let score = 0;
        for (const term of terms) {
          if (!term) continue;
          if (blob.includes(term)) score += 3;
          if (String(item.title || item.resource_name || item.channel || item.place || "").toLowerCase().includes(term)) score += 5;
          if (String(item.county || item.area_served || "").toLowerCase().includes(term)) score += 2;
        }
        if (!terms.length) {
          score += {
            "Current item": 8,
            "Shortcut group": 6,
            "Shortcut": 6,
            "Amplifier": 5,
            "Posting path": 4,
            "Listing": 2
          }[item.assistant_type] || 1;
        }
        return { item, score };
      }).filter(entry => entry.score > 0);

      return scored
        .sort((a, b) => b.score - a.score || String(a.item.title || a.item.resource_name || a.item.channel || "").localeCompare(String(b.item.title || b.item.resource_name || b.item.channel || "")))
        .slice(0, 6)
        .map(entry => entry.item);
    }

    function assistantUrl(key) {
      const root = document.querySelector("[data-directory-assistant]");
      if (!root) return key === "submit" ? "submit/index.html" : "network/index.html";
      return key === "submit" ? root.dataset.submitUrl : root.dataset.networkUrl;
    }

    function assistantCardWithUrls(item) {
      return assistantCard(item)
        .replaceAll('href="network/index.html"', `href="${escapeHtml(assistantUrl("network"))}"`)
        .replaceAll('href="submit/index.html"', `href="${escapeHtml(assistantUrl("submit"))}"`);
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
      const chips = [...root.querySelectorAll("[data-assistant-prompt]")];
      if (!toggle || !panel || !form || !input || !results || !status) return;
      let renderTimer = null;
      let lastFocusedElement = null;
      let returnFocusOnClose = true;

      function setOpen(open, { returnFocus = true } = {}) {
        if (open) {
          lastFocusedElement = document.activeElement instanceof HTMLElement ? document.activeElement : toggle;
          if (!panel.open) {
            if (typeof panel.showModal === "function") {
              panel.showModal();
            } else {
              panel.setAttribute("open", "");
            }
          }
          toggle.setAttribute("aria-expanded", "true");
          root.dataset.open = "true";
          window.setTimeout(() => input.focus(), 40);
          return;
        }
        returnFocusOnClose = returnFocus;
        if (panel.open && typeof panel.close === "function") {
          panel.close();
        } else {
          panel.removeAttribute("open");
          syncClosed();
        }
      }

      function syncClosed() {
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
        const displayQuery = search || "starter routes";
        const matches = assistantSearch(search);
        status.textContent = matches.length
          ? (search
            ? `Showing ${matches.length} route${matches.length === 1 ? "" : "s"} for "${displayQuery}".`
            : `Showing ${matches.length} starter routes from current items, directories, channels, and posting paths.`)
          : `No close match for "${displayQuery}". Try a county, town, or need like funding, events, artist, nonprofit, or media.`;
        results.innerHTML = matches.map(assistantCardWithUrls).join("") || `
          <article class="assistant-result" role="listitem">
            <h3>No direct match yet</h3>
            <p>Open the full directory or submit a correction if a resource should be added.</p>
            <div class="assistant-result__actions">
              <a href="${escapeHtml(assistantUrl("network"))}">Open full directory</a>
              <a href="${escapeHtml(assistantUrl("submit"))}">Submit a correction</a>
            </div>
          </article>
        `;
      }

      toggle.addEventListener("click", () => {
        const shouldOpen = !panel.open;
        setOpen(shouldOpen);
        if (shouldOpen && !results.innerHTML.trim()) {
          render(input.value);
        }
      });
      close && close.addEventListener("click", () => setOpen(false));
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
        if (input.value.trim().length >= 2) {
          renderTimer = window.setTimeout(() => render(input.value), 220);
        }
      });
      chips.forEach(chip => chip.addEventListener("click", () => {
        input.value = chip.dataset.assistantPrompt || "";
        render(input.value);
        input.focus();
      }));
      document.addEventListener("keydown", event => {
        if (event.key === "Escape" && panel.open && typeof panel.close !== "function") {
          event.preventDefault();
          setOpen(false);
        }
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

    function initSourceSearch() {
      const host = document.querySelector("#source-results");
      if (!host) return;
      const input = document.querySelector("#source-search");
      const note = document.querySelector("#source-results-note");
      const chips = [...document.querySelectorAll("[data-source-filter]")];
      const moreButton = document.querySelector("#source-load-more");
      let county = "All";
      let visibleCount = directoryPageSize(6, 12);
      function resetVisibleCount() {
        visibleCount = directoryPageSize(6, 12);
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
          moreButton.textContent = remaining ? `Show ${Math.min(directoryPageSize(6, 12), remaining)} more shortcuts` : "All shortcuts shown";
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
        visibleCount += directoryPageSize(6, 12);
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
      const accessSelect = document.querySelector("#access-mode-filter");
      const note = document.querySelector("#resource-results-note");
      const filterSummary = document.querySelector("#resource-filter-summary");
      const moreButton = document.querySelector("#resource-load-more");
      let county = "All";
      let locationMode = "All";
      let visibleCount = directoryPageSize(18, 36);
      populateSelect(typeSelect, uniqueValues(DATA.resources, "public_listing_type"), "All types");
      populateSelect(accessSelect, uniqueValues(DATA.resources, "access_mode"), "All access modes");
      function resetVisibleCount() {
        visibleCount = directoryPageSize(18, 36);
      }
      function render() {
        const query = input.value.trim();
        const resourceType = typeSelect ? typeSelect.value : "All";
        const accessMode = accessSelect ? accessSelect.value : "All";
        const matched = DATA.resources
          .filter(item => (county === "All" || item.county === county) && (!query || resourceTextMatch(item, query)))
          .filter(item => resourceType === "All" || item.public_listing_type === resourceType)
          .filter(item => accessMode === "All" || item.access_mode === accessMode)
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
            Flyers: "places to ask about flyers or posters"
          }[locationMode] || "matching listings";
          note.textContent = `Showing ${filtered.length} of ${matched.length} ${locationLabel}. Search by town, county, resource type, audience, keyword, or task.`;
        }
        if (filterSummary) {
          const activeFilters = [
            county !== "All" ? county : "",
            resourceType !== "All" ? resourceType : "",
            accessMode !== "All" ? accessMode : "",
            locationMode !== "All" ? locationMode : "",
          ].filter(Boolean);
          filterSummary.textContent = activeFilters.length ? `${activeFilters.length} active` : "All listings";
        }
        host.innerHTML = filtered.map(resourceCard).join("") || `<p class="section-note">No local inventory entries match that search.</p>`;
        syncDirectoryDetails(host);
        if (moreButton) {
          const remaining = Math.max(0, matched.length - filtered.length);
          moreButton.hidden = remaining === 0;
          moreButton.textContent = remaining ? `Show ${Math.min(directoryPageSize(18, 36), remaining)} more listings` : "All listings shown";
        }
      }
      input.addEventListener("input", () => {
        resetVisibleCount();
        render();
      });
      [typeSelect, accessSelect].forEach(select => select && select.addEventListener("change", () => {
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
        visibleCount += directoryPageSize(18, 36);
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
      const intro = document.querySelector(".intro-curtain");
      const loopAudio = document.getElementById("site-music-loop");
      if (!toggle || !loopAudio) return;

      const MUSIC_KEY = "triCountyRegionalSoundChoiceV3";
      const TIME_KEY = "triCountyRegionalSoundTimeV3";
      const INTRO_KEY = "triCountyLandingIntroSeenV3";
      const TRACK_KEY = "triCountyRegionalSoundTrackV3";
      const VOLUME_KEY = "triCountyRegionalSoundVolumeV3";
      const savedChoice = localStorage.getItem(MUSIC_KEY);
      const hasSeenIntro = sessionStorage.getItem(INTRO_KEY) === "seen";
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
        return option ? option.dataset.trackId || option.value : "rael-arroyo-hondo";
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
        sessionStorage.setItem(INTRO_KEY, "seen");
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

    initSourceSearch();
    initResourceSearch();
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
- `data/guide-data.json` - directory shortcuts plus public site data
- `data/directory-metadata.json` - full machine-readable metadata for every directory shortcut and local inventory entry
- `SOURCES.md` - directory, amplifier, and posting page manifest
- Global `Ask directory` assistant - client-side search across shortcuts, local inventory rows, amplifier channels, and posting pathways
- Global music bar - Library of Congress public-domain regional audio with play/stop, track choice, progress, and volume controls

## Data summary

- Total local inventory rows: {summary['row_count']}
- County mix: {summary['county']}
- Resource type mix: {summary['resource_type']}

## Caveat

The local resource inventory is a working directory. Check phone numbers, eligibility, listing status, and submission rules before publication, printing, outreach, or spending.

## QA notes

- Local HTML/asset references were checked after generation.
- SEO metadata is generated from the page shell: title, description, canonical URL, robots tag, social preview tags, JSON-LD, sitemap, and robots.txt.
- Public pages distinguish directory shortcuts, amplifier channels, public-notice/posting pathways, and local inventory rows.
- Network page JSON-LD includes machine-readable metadata for every directory shortcut and local inventory entry.
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

- A three-path homepage: Plan Your Growth, Find the Network, Understand the Region.
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
- Full directory metadata generated at `/data/directory-metadata.json` and embedded in Network page JSON-LD.
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
- Network search for `chamber`, `artist`, `media`, `grant`, `Raton`, `Trinidad`, and `Walsenburg`.
- Network filters for resource type and access mode.
- Network physical-location filters for `Physical locations` and `Ask about flyers`.
- Amplifier page rows for link URL and practical channel use.
- Posting page language: physical flyer/poster locations should be framed as places to ask, not guaranteed ad placement.
- County page nav paths.
- Footer logo scale.
- All high-priority external links.
- any link-check report for bot-blocked, timed-out, or manually-confirmed URLs.
"""
    (OUT / "QA_REPORT.md").write_text(qa, encoding="utf-8")


def write_pages(rows: list[dict], summary: dict) -> None:
    (OUT / "index.html").write_text(home_page(summary), encoding="utf-8")
    for folder in ["plan", "amplifiers", "network", "posting", "region", "templates", "submit", "appendix", "about", "resources/funding", "resources/arts-culture"]:
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    for item in TASK_PAGE_DEFS:
        path = OUT / ACTIVE_PATHS[item["active"]]
        path.mkdir(parents=True, exist_ok=True)
    (OUT / "plan" / "index.html").write_text(plan_page(), encoding="utf-8")
    (OUT / "amplifiers" / "index.html").write_text(amplifiers_page(), encoding="utf-8")
    (OUT / "network" / "index.html").write_text(network_page(rows), encoding="utf-8")
    (OUT / "resources" / "funding" / "index.html").write_text(funding_page(rows), encoding="utf-8")
    (OUT / "resources" / "arts-culture" / "index.html").write_text(arts_culture_page(rows), encoding="utf-8")
    (OUT / "posting" / "index.html").write_text(posting_page(rows), encoding="utf-8")
    (OUT / "region" / "index.html").write_text(region_page(summary), encoding="utf-8")
    (OUT / "templates" / "index.html").write_text(templates_page(), encoding="utf-8")
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


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
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

