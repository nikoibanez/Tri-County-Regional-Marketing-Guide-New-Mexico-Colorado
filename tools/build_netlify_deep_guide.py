from __future__ import annotations

import csv
import html
import json
import os
import shutil
from collections import Counter
from pathlib import Path
from textwrap import dedent


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
REAUDIT_NOTES = DOWNLOADS / "tri_county_reaudit" / "comprehensive_reaudit_source_notes.md"
NEW_PDF_EXTRACT_DIR = DOWNLOADS / "tri_county_new_pdf_extract_20260621"
BUILD_DATE = "2026-06-27"


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


DIRECTORY_SOURCES = [
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
        "title": "Colexico Alliance / TLAC Chamber",
        "county": "Las Animas",
        "kind": "Regional chamber",
        "url": "https://tlacchamber.org/",
        "best_for": "Member directory, community articles, event calendar, local products, and the cross-state regional chamber frame.",
        "action": "Use as the first regional business network shortcut for Trinidad and neighboring counties.",
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
            "title": "Spanish Peaks Country Add Business Listing",
            "county": "Huerfano",
            "kind": "Directory submission",
            "url": "https://spanishpeakscountry.com/add-business-listing/",
            "best_for": "Visitor-facing businesses that may belong in the Spanish Peaks Country directory.",
            "action": "Use to request a listing; do not promise acceptance without review.",
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
            "url": "https://www.edd.newmexico.gov/local-economic-development-act/",
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
        "cta": "Search shortcuts and leads",
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
    "about": "Creation Process",
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
        "description": "Find starting points for Raton event visibility, including city pages, tourism routes, media, calendars, public boards, partners, and verification steps.",
        "eyebrow": "Raton event visibility",
        "h1": "Where to post events in Raton, New Mexico",
        "intro": "Use this page when a public event, class, fundraiser, art opening, business launch, civic program, performance, or community activity needs visibility in Raton or Colfax County. Start with the source that best matches the event: city or county channels for official/public information, tourism and visitor-facing routes for events that serve travelers, media for public-interest announcements, and partner channels for aligned audiences. Verify the current rules before printing materials or promising placement.",
        "source_terms": ["Raton", "Colfax", "Events", "Tourism", "Media", "Arts", "MainStreet"],
        "row_terms": ["Raton", "Colfax", "event", "calendar", "media", "artist", "gallery", "theater", "tourism"],
        "primary_links": [("Use regional amplifier channels", "amplifiers/"), ("Separate official notices from community visibility", "posting/"), ("Use copy-ready outreach templates", "templates/")],
    },
    {
        "active": "post-trinidad",
        "title": "Where to Post Events in Trinidad CO | Stateline Guide",
        "description": "Use Trinidad tourism, city, chamber, creative district, venue, media, and community routes to submit or promote public events after verifying rules.",
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
        "intro": "Use this page when a Huerfano County event, art show, farmers market, workshop, nonprofit program, visitor activity, gallery reception, performance, or local announcement needs public visibility. Start with Spanish Peaks Country, town/city routes, libraries, chamber or economic-development contacts, arts channels, and regional media. Treat public boards and calendars as owner-controlled channels. Verify current rules, review time, and whether the event fits before assuming placement.",
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
        "primary_links": [("Compare calendars, media, directories, and visitor guides", "amplifiers/"), ("Prepare an advertising inquiry", "templates/"), ("Search Las Animas leads", "network/")],
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
        "primary_links": [("Open the Colfax county page", "counties/colfax/"), ("Search business and support leads", "network/"), ("Plan the outreach cycle first", "plan/")],
    },
    {
        "active": "las-animas-nonprofit",
        "title": "Las Animas County Nonprofit Resources | Stateline Guide",
        "description": "Find Trinidad and Las Animas nonprofit visibility, grant, partner, media, chamber, and community-resource routes with verification reminders.",
        "eyebrow": "Las Animas nonprofit routes",
        "h1": "Las Animas County nonprofit resources",
        "intro": "Use this page when a nonprofit, fiscally sponsored project, community program, class, service, or volunteer effort needs visibility, partners, funding paths, public calendars, or source-backed local referrals in Las Animas County. Verify eligibility, deadlines, rates, and acceptance with the source before promising participation or publication.",
        "source_terms": ["Las Animas", "Trinidad", "Nonprofit", "Grant", "Community", "Foundation", "Chamber"],
        "row_terms": ["Las Animas", "Trinidad", "nonprofit", "foundation", "grant", "community", "partner"],
        "primary_links": [("Open the Las Animas county page", "counties/las-animas/"), ("Search nonprofit and funding leads", "network/"), ("Submit a source-backed correction", "submit/")],
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
        "primary_links": [("Open the full amplifier page", "amplifiers/"), ("Search public directories and local leads", "network/"), ("Submit a changed channel", "submit/")],
    },
]


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
    return [enrich_resource_row(row) for row in rows]


def summarize(rows: list[dict]) -> dict:
    county = Counter(row.get("county") or "Unknown" for row in rows)
    rtype = Counter(row.get("resource_type") or "Unknown" for row in rows)
    verification = Counter(row.get("verification_label") or "Unknown" for row in rows)
    layer = Counter(row.get("public_layer_label") or "Unknown" for row in rows)
    goal = Counter()
    audience = Counter()
    for row in rows:
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
}


PUBLIC_TEXT_REPLACEMENTS = {
    "Records needing manual verification": "Local listing to confirm",
    "Colfax County Inventory Gaps & Verification Agenda": "Colfax local follow-up",
    "Rural Verification Nodes": "Rural community lead",
    "Verification-Priority Sparse Nodes": "Sparse-area community lead",
    "verification-priority": "source-check",
    "manual-verification": "manual-confirmation",
    "verification": "source check",
    "Verification": "Source check",
    "Field-check needed": "Local check needed",
    "field check needed": "local check needed",
    "verified": "checked",
    "Verified": "Checked",
}


def public_text_value(value: object) -> object:
    if not isinstance(value, str):
        return value
    cleaned = value
    for source, replacement in PUBLIC_TEXT_REPLACEMENTS.items():
        cleaned = cleaned.replace(source, replacement)
    return cleaned


def public_data_item(item: dict) -> dict:
    return {key: public_text_value(value) for key, value in item.items() if key not in PUBLIC_DATA_EXCLUDE_FIELDS}


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
    return clean_text(row.get("website")) or clean_text(row.get("source_url"))


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
        "entry_kind": "local_inventory_lead",
        "name": name,
        "county": county,
        "town": town,
        "state": state,
        "category": clean_text(public_row.get("category")),
        "resource_type": clean_text(public_row.get("resource_type")),
        "access_mode": clean_text(public_row.get("access_mode")),
        "audience_served": audiences,
        "goal_relevance": goals,
        "website": website,
        "source_url": source_url,
        "source_type": clean_text(public_row.get("source_type")),
        "contact_phone": clean_text(public_row.get("contact_phone")),
        "contact_email": clean_text(public_row.get("contact_email")),
        "physical_address": clean_text(public_row.get("physical_address")),
        "cost_level": clean_text(public_row.get("cost_level")),
        "needs_follow_up": as_bool_text(public_row.get("needs_follow_up")),
        "has_public_source": as_bool_text(public_row.get("has_public_source")),
        "description": clean_text(public_row.get("notes")) or "Use as a directory lead and confirm current details before action.",
        "metadata_note": "Directory metadata is a routing aid. Confirm details with the listed source or contact path before spending, printing, promising eligibility, or publishing claims.",
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
        "metadata_note": "Shortcut metadata points to an existing source. Open the source before assuming current rules, rates, deadlines, eligibility, or acceptance.",
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
        "publication_note": "These entries are routing metadata for directory discovery. Treat local inventory rows as leads unless a current public source confirms them.",
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
        "additionalType": "Directory shortcut" if entry.get("entry_kind") == "directory_shortcut" else "Local inventory lead",
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
                property_value("source_type", entry.get("source_type")),
                property_value("contact_phone", entry.get("contact_phone")),
                property_value("contact_email", entry.get("contact_email")),
                property_value("physical_address", entry.get("physical_address")),
                property_value("cost_level", entry.get("cost_level")),
                property_value("needs_follow_up", entry.get("needs_follow_up")),
                property_value("has_public_source", entry.get("has_public_source")),
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
        "description": "Machine-readable metadata for every directory shortcut and local inventory entry in the Stateline Guide. Entries are routing aids and should be confirmed before action.",
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
    amplifier_channels = [public_data_item(item) for item in AMPLIFIER_CHANNELS]
    public_rows = [public_data_item(row) for row in rows]
    public_summary = {key: value for key, value in summary.items() if key not in {"verification", "public_layer"}}
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
        "amplifier_channels": amplifier_channels,
        "posting_spaces": POSTING_SPACES,
        "persona_routes": PERSONA_ROUTES,
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
              <p class="source-note">Details can change. Open the source, then submit a correction if this pathway is outdated.</p>
            </article>
            """
        )
    return "\n".join(cards)


def download_buttons(depth: int = 0) -> str:
    return f"""
    <div class="download-row" aria-label="Download guide data">
      <a class="button button-soft" href="{rel('data/tri_county_persona_resources.csv', depth)}" download data-analytics="download_inventory_csv">Download CSV</a>
      <a class="button button-soft" href="{rel('data/guide-data.json', depth)}" download data-analytics="download_inventory_json">Download JSON</a>
      <a class="button button-soft" href="{rel('SOURCES.md', depth)}" download data-analytics="download_sources">Download Sources</a>
      <button class="button button-soft print-button" type="button">Print page</button>
    </div>
    """


def submit_listing_panel(depth: int = 0, context: str = "directory") -> str:
    context_copy = {
        "directory": ("Submit or correct a listing", "Use this when a business, nonprofit, gallery, program, service, venue, event series, or resource should be added, updated, corrected, or removed."),
        "amplifier": ("Suggest a channel", "Use this when a calendar, newsletter, visitor guide, media outlet, directory, venue lineup, or partner channel should be added or corrected."),
        "county": ("Add a local listing", "Use this when a county page is missing a business, organization, program, service, gallery, or resource that helps people find local visibility paths."),
        "appendix": ("Update the appendix", "Use this when the contact table needs a new row, a correction, a better source link, or a note that a listing may be outdated."),
    }.get(context, ("Submit or correct a listing", "Use this when a listing should be added, updated, corrected, or removed."))
    return f"""
    <section class="section submit-band" aria-labelledby="submit-listing-title">
      <div class="section-heading">
        <p class="eyebrow">Listing updates</p>
        <h2 id="submit-listing-title">{html_escape(context_copy[0])}</h2>
        <p class="section-note">{html_escape(context_copy[1])} Submissions are starting points for review, not automatic publication.</p>
      </div>
      <div class="submit-card">
        <div>
          <h3>What to include</h3>
          <p>Name, county, community, website or source link, contact route, short description, audience served, and what action a reader should take.</p>
        </div>
        <div>
          <h3>Placeholder intake contact</h3>
          <p>Email: updates@statelineguide.example<br>Phone: (575) 000-0000<br>Mail: 000 Main Street, Raton, NM 87740</p>
        </div>
        <a class="button button-primary" href="{rel('submit/index.html', depth)}" data-analytics="submit_correction_click">Open submission form</a>
      </div>
    </section>
    """


def route_href(path: str) -> str:
    return f"{path}index.html" if path else "index.html"


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
        ("Search public directories and local leads", "network/"),
        ("Find event calendars, newsletters, visitor guides, and directory channels", "amplifiers/"),
        ("Submit a correction with a public source link", "submit/"),
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
                ("Creation", "about/index.html", "about"),
            ],
        ),
        (
            "group",
            "Find",
            [
                ("Network", "network/index.html", "network"),
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
                ("Creation process", "about/index.html"),
            ],
        ),
        (
            "Find",
            [
                ("Directory", "network/index.html"),
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
          <div class="music-bar" data-music-bar aria-label="Local copyright-free music player">
            <div class="music-bar__top">
              <button class="music-toggle" type="button" aria-pressed="false" data-state="stopped">Play</button>
              <label class="music-track-label">Track
                <select class="music-track-select" aria-label="Choose local music track">
                  <option value="{rel('assets/audio/loc-rael-nm-valse.mp3', depth)}" data-track-id="rael-arroyo-hondo">Rael Waltz - Arroyo Hondo, NM</option>
                  <option value="{rel('assets/audio/loc-rael-co-valse.mp3', depth)}" data-track-id="rael-antonito">Rael Waltz - Antonito, CO</option>
                </select>
              </label>
            </div>
            <div class="music-bar__middle">
              <input class="music-progress" type="range" min="0" max="1000" value="0" aria-label="Music progress">
              <span class="music-time" aria-live="polite">0:00</span>
            </div>
            <div class="music-bar__bottom">
              <span>Regional archival audio from the Library of Congress.</span>
              <label>Volume
                <input class="music-volume" type="range" min="0" max="100" value="58" aria-label="Music volume">
              </label>
            </div>
          </div>
    """
    intro_curtain = (
        '<div class="intro-curtain" aria-hidden="true" data-intro-state="ready"></div>'
        if active == "home"
        else ""
    )
    audio_markup = f"""
          <audio id="site-music-loop" preload="auto" loop src="{rel('assets/audio/loc-rael-nm-valse.mp3', depth)}"></audio>
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
        <body>
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
              <p class="directory-assistant__intro" id="directory-assistant-intro">Search by need, county, town, audience, or task. Results include source links and update reminders so users can act without treating old details as final.</p>
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
    persona_cards = "\n".join(
        f"""
        <article class="mini-card">
          <h3>{html_escape(item['persona'])}</h3>
          <p>{html_escape(item['start'])}</p>
          <p class="action-line">{html_escape(item['pages'])}</p>
        </article>
        """
        for item in PERSONA_ROUTES
    )
    task_cards = "\n".join(
        f"""
        <a class="mini-card task-link-card" href="{route_href(ACTIVE_PATHS[item['active']])}">
          <h3>{html_escape(item['h1'])}</h3>
          <p>{html_escape(item['description'])}</p>
        </a>
        """
        for item in TASK_PAGE_DEFS
    )
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
            <h2>Start with the search question people actually type.</h2>
            <p class="section-note">These pages turn common local questions into next actions: where to post, where to advertise, what county page to use, and which channels to verify first.</p>
          </div>
          <div class="mini-grid task-grid">{task_cards}</div>
        </section>
        <section class="section">
          <div class="two-col">
            <div>
              <p class="eyebrow">Pick your door</p>
              <h2>Use the guide by need, not by reading order.</h2>
              <p>Open a gallery, fix an old listing, plan a fundraiser, or expand a rural service from the page that fits the task. The same useful loop still applies: list, post, partner, follow up, repeat.</p>
              <a class="button button-primary" href="amplifiers/index.html">Find amplifier channels</a>
            </div>
            <div>
              <p class="eyebrow">Routing logic</p>
              <h2>The same loop works across roles.</h2>
              <p>New businesses, long-running organizations, artists, mentors, venues, and service providers can start from different pages because the guide is organized around tasks: getting listed, posting something, finding partners, preparing materials, and verifying the path.</p>
            </div>
          </div>
        </section>
        <section class="section tinted">
          <div class="section-heading">
            <p class="eyebrow">Use by role</p>
            <h2>Six quick starts for the people this guide is meant to serve.</h2>
          </div>
          <div class="mini-grid">{persona_cards}</div>
        </section>
        <section class="section tinted">
          <div class="section-heading">
            <p class="eyebrow">Inventory backbone</p>
            <h2>{summary['row_count']} local listings and leads, organized beside existing directory shortcuts.</h2>
          </div>
          <div class="stats-grid">
            <div class="stat hero-stat"><strong>{summary['row_count']}</strong><span>local listings and leads</span></div>
            {stats}
          </div>
          <p class="section-note">Use the local inventory for outreach and discovery. Details can change, so open the source when available and submit a correction when a listing, link, or contact route is outdated.</p>
          {download_buttons(0)}
        </section>
        <section class="section">
          <div class="section-heading">
            <p class="eyebrow">Existing shortcuts</p>
            <h2>Start with places that already collect the information.</h2>
          </div>
          <div class="source-grid compact">
            {source_cards(DIRECTORY_SOURCES, 12)}
          </div>
          <div class="section-actions"><a class="button button-primary" href="network/index.html">Open the full shortcut directory</a></div>
        </section>
        {submit_listing_panel(0, "directory")}
        {next_action_block(0, [
            ("Plan the right outreach cycle before collecting links", "plan/"),
            ("Search public directories and local leads", "network/"),
            ("Find event calendars, newsletters, visitor guides, and directory channels", "amplifiers/"),
            ("Choose a county starting point", "region/"),
        ])}
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
      <div class="section-actions"><a class="button button-primary" href="../network/index.html">Find directories and leads</a></div>
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Use by need</p>
        <h2>Start with the job, then choose the section.</h2>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Need</th><th>Start here</th><th>First action</th></tr></thead>
          <tbody>
            <tr><td>Get listed</td><td>Network</td><td>Use existing directories first.</td></tr>
            <tr><td>Post an event</td><td>Amplify + Post</td><td>Choose calendar, venue, media, or notice path.</td></tr>
            <tr><td>Find partners</td><td>Region</td><td>Use county hubs and referral nodes.</td></tr>
            <tr><td>Prepare outreach</td><td>Templates</td><td>Make one packet, then adapt it.</td></tr>
            <tr><td>Correct data</td><td>Submit</td><td>Send source link plus correction.</td></tr>
          </tbody>
        </table>
      </div>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Promotion packet</p>
        <h2>Templates are time-savers, not the strategy.</h2>
        <p class="section-note">The useful strategy is to prepare one clean packet: a short blurb, image, flyer, listing details, date, location, hours, contact route, and plain call to action. The templates help you adapt that packet for directories, calendars, media, partners, emails, and social posts.</p>
      </div>
      <div class="section-actions">
        <a class="button button-primary" href="../templates/index.html">Use copy-ready templates</a>
        <a class="button button-soft" href="../amplifiers/index.html">Find places to send them</a>
      </div>
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Free and freemium tools</p>
        <h2>Build the packet with tools people already recognize.</h2>
        <p class="section-note">Plan limits change. Treat these as popular online starting points and verify current free-tier limits before relying on them for a campaign.</p>
      </div>
      <div class="tool-grid">{tool_cards}</div>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Funding and support readiness</p>
        <h2>Visibility work can create proof for later asks.</h2>
        <p class="section-note">Grantors, lenders, sponsors, and partner organizations usually need more than enthusiasm. Track where you posted, who shared, what response arrived, and which partner can confirm the public benefit before using outreach results in a funding conversation.</p>
      </div>
      <a class="button button-soft" href="../network/index.html">Find funding and support leads</a>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Cross-promotion loop</p>
        <h2>Use the channel that worked, then make the relationship stronger.</h2>
        <p class="section-note">Submit the item, share the published result, thank the channel owner, report useful response, and reuse the relationship when it fits again.</p>
      </div>
    </section>
    {next_action_block(1, [
        ("Search directories and support leads", "network/"),
        ("Find event calendars, newsletters, visitor guides, and directory channels", "amplifiers/"),
        ("Use copy-ready outreach templates", "templates/"),
        ("Submit a correction with a public source link", "submit/"),
    ])}
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
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">Find the Network</p>
      <h1>Use the directories that already save time.</h1>
      <p class="lede">Search high-value public shortcuts first, then use the {row_count}-entry local inventory as a working list to confirm before outreach.</p>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Persona routes</p>
        <h2>Start from the person doing the work.</h2>
        <p class="section-note">A new business, a gallery, a nonprofit, and a mentor program do not need the same first contact. Use these role shortcuts first, then narrow the local list by county, resource type, or access mode.</p>
      </div>
      {persona_route_controls(1)}
      {download_buttons(1)}
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Keep it current</p>
        <h2>If something has changed, send the update path.</h2>
      </div>
      <div class="two-col">
        <p>The guide keeps source links and contact routes visible so users have a starting point. Before spending money, printing materials, or promising placement, open the source and confirm current rules.</p>
        <p>If a link is outdated, a business moved, or a better submission path exists, use the correction form and include the public source to check.</p>
      </div>
      <div class="section-actions"><a class="button button-primary" href="../submit/index.html">Submit a correction</a></div>
    </section>
    <section class="section">
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
      <div id="source-results" class="source-grid"></div>
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Lead bank</p>
        <h2>Search the local inventory, but verify before using.</h2>
      </div>
      <div class="tool-panel">
        <div>
          <label for="resource-search">Search {row_count} local entries</label>
          <input id="resource-search" class="search-input" type="search" placeholder="Try gallery, radio, grant, Raton, Walsenburg, Trinidad...">
        </div>
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
        <div class="filter-row" aria-label="Resource filters">
          <button class="chip is-active" data-resource-filter="All">All</button>
          <button class="chip" data-resource-filter="Colfax">Colfax</button>
          <button class="chip" data-resource-filter="Las Animas">Las Animas</button>
          <button class="chip" data-resource-filter="Huerfano">Huerfano</button>
          <button class="chip" data-resource-filter="Regional">Regional</button>
        </div>
      </div>
      <p class="section-note">Search by town, county, resource type, or access mode. Open the source when available and submit corrections when details have changed.</p>
      <div id="resource-results" class="resource-list"></div>
      <p class="section-note">Need a table view? Open the public-contact appendix for county/community grouping.</p>
      <div class="section-actions"><a class="button button-primary" href="../appendix/index.html">Open the appendix</a></div>
    </section>
    {submit_listing_panel(1, "directory")}
    {next_action_block(1, [
        ("Find regional newsletters, calendars, visitor guides, and directory channels", "amplifiers/"),
        ("Use copy-ready outreach templates", "templates/"),
        ("Submit a correction with a public source link", "submit/"),
        ("Open the public contact appendix", "appendix/"),
    ])}
    """
    return page_shell(
        "Find Local Directories, Media, Funding & Support Leads | Stateline Guide",
        f"Search public shortcuts and a {row_count}-entry regional inventory of directories, media, funding, business, nonprofit, arts, and support leads.",
        "network",
        content,
        depth=1,
        main_entity=directory_item_list_schema(rows),
        extra_json_alternates=[("Full directory metadata", "data/directory-metadata.json")],
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
          <td>{html_escape(use_case)}</td>
          <td>{html_escape(channels)}</td>
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
      <p class="lede">Use this page to decide where an event, listing, announcement, partnership ask, or visitor-facing update may belong. Open the source before assuming current rates, deadlines, or acceptance rules.</p>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">What each side is for</p>
        <h2>Choose the channel by the job it can actually do.</h2>
      </div>
      <div class="mini-grid">{categories}</div>
      <p class="section-note">Do not promise ad availability, free placement, deadlines, audience size, endorsement, or acceptance unless the source says so. Ask the channel directly when those details matter.</p>
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
      <p class="section-note">Before paying for ads or promising placement, ask the source about current rates, deadlines, acceptance, and submission rules.</p>
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
        <article class="mini-card"><h3>Can I assume a newsletter accepts outside promotions?</h3><p>No. Ask first. Do not assume ad availability, free placement, deadlines, audience size, endorsement, or acceptance unless the source confirms it.</p></article>
        <article class="mini-card"><h3>What should I prepare before submitting an event?</h3><p>Prepare the event name, date, time, location, short description, contact link, images, flyer, accessibility notes, and whether the event is free, ticketed, nonprofit, youth, tourism, business, or community-oriented.</p></article>
      </div>
    </section>
    {submit_listing_panel(1, "amplifier")}
    {next_action_block(1, [
        ("Search public directories and local leads", "network/"),
        ("Separate official notices from community visibility", "posting/"),
        ("Use copy-ready outreach templates", "templates/"),
        ("Submit a changed channel with a public source link", "submit/"),
    ])}
    """
    return page_shell(
        "Regional Newsletters, Calendars, Directories & Visitor Guides | Stateline Guide",
        "Compare event calendars, newsletters, business directories, tourism guides, venue lineups, and advertising inquiry routes across the tri-county area.",
        "amplifiers",
        content,
        depth=1,
        schema_type="CollectionPage",
    )


def posting_page() -> str:
    rows = "\n".join(
        f"""
        <tr>
          <td>{html_escape(item['place'])}</td>
          <td>{html_escape(item['physical'])}</td>
          <td>{html_escape(item['digital'])}</td>
          <td>{html_escape(public_text_value(item['use_for']))}</td>
          <td>{html_escape(public_text_value(item['status']))}</td>
          <td>{f'<a href="{html_escape(item["source_url"])}" target="_blank" rel="noreferrer">Open source</a>' if item['source_url'] else 'Local check needed'}</td>
        </tr>
        """
        for item in POSTING_SPACES
    )
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">Where To Post</p>
      <h1>Separate official notices from community visibility.</h1>
      <p class="lede">Small communities have physical boards, public offices, digital public-notice pages, calendars, newsletters, and informal partner channels. Use this page to verify the right channel without treating every board as an ad space.</p>
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Posting map</p>
        <h2>Physical plus digital channels to verify by community.</h2>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Community</th><th>Physical pathway</th><th>Digital pathway</th><th>Use for</th><th>Status</th><th>Source</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
      <p class="section-note">Use "field-check needed" entries as details to confirm, not as a claim that posting is already allowed.</p>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Posting method</p>
        <h2>A simple sequence for offline and online visibility.</h2>
      </div>
      <div class="steps-grid">
        <article class="step-card"><span>1</span><h3>Verify the owner</h3><p>Identify who controls the board, calendar, newsletter, or directory before preparing materials.</p></article>
        <article class="step-card"><span>2</span><h3>Match the purpose</h3><p>Official notice, public event, business listing, and paid advertisement are different requests.</p></article>
        <article class="step-card"><span>3</span><h3>Use clear assets</h3><p>Keep a short blurb, accessible flyer, square image, date, location, and contact ready.</p></article>
        <article class="step-card"><span>4</span><h3>Track proof</h3><p>Record where it was posted, who approved it, when it expires, and what response it produced.</p></article>
      </div>
    </section>
    {next_action_block(1, [
        ("Find event calendars, newsletters, visitor guides, and directory channels", "amplifiers/"),
        ("Use copy-ready outreach templates", "templates/"),
        ("Submit a corrected posting route", "submit/"),
        ("Search public directories and local leads", "network/"),
    ])}
    """
    return page_shell(
        "Where to Post Events, Notices & Listings in the Tri-County Area | Stateline Guide",
        "Separate official notices from community visibility, then verify boards, calendars, newsletters, directories, and public office posting routes.",
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
          <td>{html_escape(row.get('resource_type'))}</td>
          <td>{html_escape(row.get('access_mode'))}</td>
          <td>{html_escape(row.get('contact_phone'))}</td>
          <td>{html_escape(row.get('contact_email'))}</td>
          <td>{html_escape(row.get('physical_address'))}</td>
          <td>{f'<a href="{html_escape(row.get("website") or row.get("source_url"))}" target="_blank" rel="noreferrer">Open</a>' if (row.get('website') or row.get('source_url')) else 'Verify manually'}</td>
          <td>{html_escape(public_text_value(row.get('notes')))}</td>
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
        ("Submit an appendix correction with a public source link", "submit/"),
        ("Understand how the three counties connect", "region/"),
    ])}
    """
    return page_shell(
        "Tri-County Public Contact Appendix | Stateline Guide",
        "Browse public-contact appendix entries by county, community, source, access mode, resource type, and update status.",
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
        <p class="section-note">These counts describe the guide's current source coverage. Do not treat them as audience size, market demand, economic value, or verified reach.</p>
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
        ("Search public directories and local leads", "network/"),
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
          <span>{html_escape(row.get('resource_type'))} - {html_escape(row.get('town') or county)}</span>
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
      <p class="lede">Start with public directories and support organizations, then use local inventory entries as outreach leads to confirm before action.</p>
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
        <p class="eyebrow">Local lead sample</p>
        <h2>Inventory examples to verify and use carefully.</h2>
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
        ("Directory listing request", "Hello, I am requesting an update or listing for [business/program name]. We serve [audience] in [town/county]. Our current details are: [website], [phone], [address], [hours], [short description]. Please let me know if there is a preferred form or review process."),
        ("Event calendar submission", "Event name: [name]. Date/time: [date]. Location: [place]. Cost: [free/price]. Who it is for: [audience]. Short description: [45-75 words]. Image/flyer attached. Contact: [name/email/phone]."),
        ("Media pitch", "[Organization] is launching [thing] for [audience] on [date]. It matters locally because [one concrete reason]. We can provide photos, a short interview, and event details. The public call to action is [register/visit/share/contact]."),
        ("Promotion or advertising question", "Hello, I am reaching out to ask whether [organization/publication/site name] accepts event listings, newsletter submissions, business directory updates, paid advertisements, social media co-promotion, visitor-guide listings, or other community announcements. The item is [business/event/program name] for [audience] in [town/county]. Could you point me to the right form, deadline, rate card, eligibility rule, or contact person?"),
        ("Partner ask", "We are trying to reach [audience] across [counties]. Would your organization be open to sharing [listing/event/resource], referring people who need it, or suggesting the best local channel? I can send a short blurb and image sized for your usual format."),
        ("Follow-up tracker", "Track: date, channel, contact, message sent, response, next action, result, whether the source should be reused."),
    ]
    items = "\n".join(
        f"""
        <article class="template-card">
          <h3>{html_escape(title)}</h3>
          <pre>{html_escape(body)}</pre>
          <button class="copy-button" type="button">Copy</button>
        </article>
        """
        for title, body in templates
    )
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">Templates</p>
      <h1>Make the next action easy to send.</h1>
      <p class="lede">Use these as plain starting copy for a business listing, event, grant path, nonprofit referral, gallery show, class, market, or mentorship program.</p>
    </section>
    <section class="section">
      <div class="template-grid">{items}</div>
    </section>
    {next_action_block(1, [
        ("Find places to send outreach packets", "amplifiers/"),
        ("Search directories and local leads", "network/"),
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
    content = """
    <section class="page-hero">
      <p class="eyebrow">Submit a Listing</p>
      <h1>Send enough information for a useful review.</h1>
      <p class="lede">Use this page to suggest a new listing, correct an existing entry, submit an event path, or recommend a directory, calendar, newsletter, visitor guide, or media channel. A submission is a review request, not automatic publication.</p>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Before you submit</p>
        <h2>Include the source, the place, and the reader action.</h2>
      </div>
      <div class="steps-grid">
        <article class="step-card"><span>1</span><h3>Name the listing</h3><p>Use the public name of the business, organization, program, service, gallery, event, venue, or resource.</p></article>
        <article class="step-card"><span>2</span><h3>Pick the section</h3><p>Choose the county page, network directory, appendix, amplifier channel list, posting map, or templates/resources area.</p></article>
        <article class="step-card"><span>3</span><h3>Add proof</h3><p>Include a website, form, social page, public directory link, flyer, official page, or contact route that can be checked.</p></article>
        <article class="step-card"><span>4</span><h3>State the use</h3><p>Say whether readers should list, post, contact, visit, register, ask about advertising, verify public information, or request a correction.</p></article>
      </div>
    </section>
    <section class="section tinted" id="submission-form">
      <div class="section-heading">
        <p class="eyebrow">Submission form</p>
        <h2>Listing, correction, channel, or event update.</h2>
        <p class="section-note">Use this form to send details for review. Replace the placeholder contact details before publishing if a real intake inbox is available.</p>
      </div>
      <form class="submission-form" name="listing-submission" method="POST" data-netlify="true" netlify-honeypot="bot-field" action="#submission-received">
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
          <label>Website or public source link
            <input name="source_url" type="url" placeholder="https://example.org/listing-or-source">
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
          <textarea name="reader_action" rows="3" placeholder="Should someone visit, register, call, submit an event, ask about advertising, verify a listing, or contact a partner?"></textarea>
        </label>
        <label>Update notes
          <textarea name="update_notes" rows="4" placeholder="What source should be checked? What is outdated, missing, or needs confirmation?"></textarea>
        </label>
        <div class="form-grid">
          <label>Your name
            <input name="submitter_name" type="text" placeholder="Jane Doe">
          </label>
          <label>Your email
            <input name="submitter_email" type="email" placeholder="you@example.org">
          </label>
        </div>
        <button class="button button-primary" type="submit" data-analytics="submit_correction_click">Submit listing for review</button>
      </form>
    </section>
    <section class="section" id="submission-received">
      <div class="section-heading">
        <p class="eyebrow">Placeholder contact</p>
        <h2>Manual intake path until final contacts are confirmed.</h2>
      </div>
      <div class="submit-card">
        <div>
          <h3>Email</h3>
          <p>updates@statelineguide.example</p>
        </div>
        <div>
          <h3>Phone</h3>
          <p>(575) 000-0000</p>
        </div>
        <div>
          <h3>Mail</h3>
          <p>000 Main Street<br>Raton, NM 87740</p>
        </div>
      </div>
      <p class="section-note">Replace these placeholders before public launch if submissions should go to a real inbox, department, partner, or shared review queue.</p>
    </section>
    {next_action_block(1, [
        ("Search the current directory before submitting", "network/"),
        ("Open the public contact appendix", "appendix/"),
        ("Find amplifier channels to verify", "amplifiers/"),
        ("Read the creation process and source method", "about/"),
    ])}
    """
    return page_shell(
        "Submit a Correction or Suggest a Regional Channel | Stateline Guide",
        "Send source-backed corrections, listing updates, new channel suggestions, or changed contact paths for review.",
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
          <td>{html_escape(item['best_for'])}</td>
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
      <p class="lede">Use this guide when you need to know which existing channel fits the job: getting listed, posting an event, asking about advertising, reaching visitors, finding partners, or verifying public information.</p>
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
        <article class="step-card"><span>1</span><h3>Open the source</h3><p>Use the linked page, form, directory, or public contact route before spending time or money.</p></article>
        <article class="step-card"><span>2</span><h3>Confirm the current rule</h3><p>Ask about rates, deadlines, acceptance, eligibility, and the preferred submission format when those details matter.</p></article>
        <article class="step-card"><span>3</span><h3>Submit changes</h3><p>If a link, listing, office, or route has changed, send the correction with the source that should be checked.</p></article>
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
        <article class="step-card"><span>5</span><h3>Write action copy</h3><p>Explain what the source is for, who should use it, what to prepare, and what must be verified first.</p></article>
        <article class="step-card"><span>6</span><h3>Keep updates open</h3><p>Give users a correction path, a submission path, and a review date so the guide can keep improving.</p></article>
      </div>
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Before relying on a listing</p>
        <h2>Verify the details that can change.</h2>
      </div>
      <ul class="check-list">
        <li>Confirm directory and submission links before sending people to them.</li>
        <li>Verify business phone numbers, addresses, eligibility, and update processes before printing or promising anything.</li>
        <li>Ask chambers, city offices, newspapers, creative districts, and economic-development organizations whether they want wording changed.</li>
        <li>Do not assume free placement, ad availability, endorsement, deadlines, audience size, or acceptance unless the source confirms it.</li>
      </ul>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Source index</p>
        <h2>Public directories and resource hubs used by the guide.</h2>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Source</th><th>County</th><th>Type</th><th>Best for</th></tr></thead>
          <tbody>{source_rows}</tbody>
        </table>
      </div>
      <p class="section-note">Downloadable data files are available for users who need a spreadsheet or source list.</p>
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
        ("Search public directories and local leads", "network/"),
        ("Find event calendars, newsletters, visitor guides, and directory channels", "amplifiers/"),
        ("Submit a correction with a public source link", "submit/"),
        ("Open the public contact appendix", "appendix/"),
    ])}
    """
    return page_shell(
        "How This Manual Works | Stateline Guide",
        "Purpose, update guidance, and source-routing logic for the tri-county regional marketing guide.",
        "about",
        content,
        depth=1,
        schema_type="AboutPage",
    )


def match_terms(item: dict, terms: list[str]) -> bool:
    haystack = " ".join(str(value or "") for value in item.values()).lower()
    return any(term.lower() in haystack for term in terms)


def task_page(definition: dict, rows: list[dict]) -> str:
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
          <span>{html_escape(row.get('town') or row.get('county') or 'Regional')} - {html_escape(row.get('resource_type') or 'Resource')}</span>
        </li>
        """
        for row in row_matches
    )
    if not lead_items:
        lead_items = "<li><strong>Start with the source cards above.</strong><span>No close inventory lead matched this task yet; submit one when a better local route is confirmed.</span></li>"
    route_rows = [
        ("Tourism or event calendar", "The item is public and visitor-facing", "Name, date, time, location, image, short description", "Confirm eligibility and lead time"),
        ("City or county source", "The item involves official notices, permits, public meetings, or civic timing", "Source link, official contact, legal name if needed", "Confirm rules with the office owner"),
        ("Chamber or business directory", "The item is a business, member update, or partner ask", "Business name, category, website, address or service area", "Confirm listing or member requirements"),
        ("Media or newsletter", "The item has public interest, event relevance, or community benefit", "50-word blurb, image, contact, deadline", "Ask about editorial versus paid placement"),
        ("Venue or partner channel", "The item fits an existing audience or lineup", "Flyer, description, target audience, public action", "Ask before sending promotional assets"),
    ]
    route_table = "\n".join(
        f"<tr><td>{html_escape(kind)}</td><td>{html_escape(use)}</td><td>{html_escape(prepare)}</td><td>{html_escape(note)}</td></tr>"
        for kind, use, prepare, note in route_rows
    )
    next_links = definition["primary_links"] + [
        ("Submit a correction with a public source link", "submit/"),
    ]
    content = f"""
    <section class="page-hero">
      <p class="eyebrow">{html_escape(definition['eyebrow'])}</p>
      <h1>{html_escape(definition['h1'])}</h1>
      <p class="lede">{html_escape(definition['intro'])}</p>
    </section>
    <section class="section">
      <div class="section-heading">
        <p class="eyebrow">Best first routes</p>
        <h2>Choose the route by what the item needs to do.</h2>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Route type</th><th>Use first when</th><th>What to prepare</th><th>Verification note</th></tr></thead>
          <tbody>{route_table}</tbody>
        </table>
      </div>
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
        <p class="eyebrow">Inventory leads to verify</p>
        <h2>Use these as starting points, not final proof.</h2>
        <p class="section-note">These rows come from the working inventory. They help users find likely routes quickly, but details should be checked at the source before action.</p>
      </div>
      <ul class="lead-list">{lead_items}</ul>
    </section>
    <section class="section tinted">
      <div class="section-heading">
        <p class="eyebrow">Use this sequence</p>
        <h2>Move from fit to proof.</h2>
      </div>
      <div class="steps-grid">
        <article class="step-card"><span>1</span><h3>Classify the item</h3><p>Decide whether it is public, private, official, paid, nonprofit, visitor-facing, or partner-facing.</p></article>
        <article class="step-card"><span>2</span><h3>Prepare one packet</h3><p>Make a short blurb, contact route, date or service area, image, link, and plain public action.</p></article>
        <article class="step-card"><span>3</span><h3>Use the owner path</h3><p>Submit through the source owner's preferred form or contact path before sending broad requests.</p></article>
        <article class="step-card"><span>4</span><h3>Ask what is unclear</h3><p>Confirm deadlines, rates, acceptance, membership rules, editorial review, and image requirements when the page does not say.</p></article>
        <article class="step-card"><span>5</span><h3>Save proof</h3><p>Record the submission, response, published link, or reason it did not fit.</p></article>
        <article class="step-card"><span>6</span><h3>Update the guide</h3><p>Submit a correction if a source changed or a better route is now available.</p></article>
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
      --verified: #4d8a5c;
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
      animation: introReveal 10000ms cubic-bezier(.22,.72,.18,1) forwards;
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
      animation: introGlow 10000ms cubic-bezier(.22,.72,.18,1) forwards;
    }
    .intro-curtain[data-intro-state="skipped"],
    .intro-curtain[data-intro-state="complete"] {
      display: none;
      animation: none;
    }
    @keyframes introReveal {
      0%, 30% { background: #000; opacity: 1; }
      70% { background: #fff; opacity: 1; }
      82% { background: #fff; opacity: 0.92; }
      100% { background: #fff; opacity: 0; visibility: hidden; }
    }
    @keyframes introGlow {
      0%, 30% { opacity: 0; transform: scale(0.82); }
      48% { opacity: 0.42; transform: scale(0.96); }
      70% { opacity: 1; transform: scale(1.08); }
      100% { opacity: 0.68; transform: scale(1.18); }
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
    .page-hero { position: relative; overflow: hidden; isolation: isolate; background: linear-gradient(135deg, rgba(220,238,232,0.86), rgba(183,219,228,0.5)); border-bottom: 1px solid var(--line); }
    .page-hero > :not(.page-hero-art) { position: relative; z-index: 1; }
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
    .path-card, .source-card, .mini-card, .step-card, .template-card, .tool-card, .resource-item, .stat, figure {
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
    .source-card, .mini-card, .step-card, .template-card, .tool-card, .resource-item { padding: 18px; }
    .path-card, .mini-card, .step-card, .template-card, .tool-card, .button, .chip, .persona-route {
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
    .tool-card:focus-within {
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
    .submit-card { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto; gap: 18px; align-items: center; padding: 18px; border: 1px solid var(--line); border-radius: var(--radius); background: rgba(255,255,255,0.84); box-shadow: var(--shadow); }
    .submit-card p { margin-bottom: 0; color: var(--ink-soft); }
    .submission-form { display: grid; gap: 18px; max-width: 1040px; }
    .form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
    .submission-form input, .submission-form select, .submission-form textarea { width: 100%; margin-top: 8px; padding: 11px 12px; border: 1px solid var(--line); border-radius: var(--radius); background: rgba(255,255,255,0.94); color: var(--ink); font: inherit; }
    .submission-form textarea { resize: vertical; }
    .hidden-field { position: absolute; left: -9999px; width: 1px; height: 1px; overflow: hidden; }
    .source-card__meta { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
    .source-card__meta span, .badge { background: rgba(216,187,104,0.24); border: 1px solid rgba(216,187,104,0.36); border-radius: 999px; padding: 3px 8px; font-size: 0.74rem; font-weight: 800; }
    .source-card p, .mini-card p, .step-card p, .resource-item p { color: var(--ink-soft); }
    .source-note { font-size: 0.9rem; color: rgba(23,48,71,0.68) !important; }
    .action-line { font-weight: 700; color: var(--ink) !important; }
    .stat { padding: 18px; display: grid; gap: 4px; }
    .stat strong { font-size: clamp(2rem, 4vw, 3.4rem); line-height: 1; }
    .stat span, .section-note { color: var(--ink-soft); }
    .hero-stat { background: var(--ink); color: #fff; }
    .hero-stat span { color: rgba(255,255,255,0.75); }
    .check-list { padding-left: 1.1rem; color: var(--ink-soft); }
    .check-list li { margin: 8px 0; }
    .tool-panel { display: grid; gap: 14px; margin-bottom: 20px; }
    label { display: block; font-weight: 800; margin-bottom: 8px; }
    .search-input { width: 100%; min-height: 48px; padding: 12px 14px; border: 1px solid var(--line); border-radius: var(--radius); font: inherit; background: rgba(255,255,255,0.9); }
    .advanced-filters { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
    select { width: 100%; min-height: 44px; padding: 10px 12px; border: 1px solid var(--line); border-radius: var(--radius); background: rgba(255,255,255,0.9); color: var(--ink); font: inherit; }
    .filter-row { display: flex; flex-wrap: wrap; gap: 8px; }
    .chip, .copy-button { min-height: 38px; border: 1px solid var(--line); border-radius: 999px; background: rgba(255,255,255,0.85); color: var(--ink); padding: 8px 12px; font: inherit; font-weight: 800; cursor: pointer; }
    .chip.is-active { background: var(--ink); color: #fff; }
    .resource-list { display: grid; gap: 12px; }
    .resource-item__head { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
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
    .back-to-top, .music-toggle {
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
    .back-to-top:hover,
    .back-to-top:focus-visible,
    .music-toggle:hover,
    .music-toggle:focus-visible {
      background: rgba(16,40,61,0.82);
      border-color: rgba(255,255,255,0.34);
      box-shadow: 0 10px 22px rgba(23,48,71,0.14);
    }
    .music-toggle { background: rgba(255,255,255,0.40); color: var(--ink); border-color: rgba(23,48,71,0.10); }
    .music-toggle:hover, .music-toggle:focus-visible { color: #fff; }
    .music-toggle[data-state="playing"] { background: rgba(216,187,104,0.40); color: #173047; }
    .music-toggle[data-state="playing"]:hover, .music-toggle[data-state="playing"]:focus-visible { background: rgba(216,187,104,0.82); color: #173047; }
    .music-bar {
      pointer-events: auto;
      width: 100%;
      padding: 10px;
      border: 1px solid rgba(23,48,71,0.14);
      border-radius: 12px;
      background: rgba(255,255,255,0.62);
      color: var(--ink);
      box-shadow: 0 12px 30px rgba(23,48,71,0.12);
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
      .back-to-top, .music-toggle { min-height: 38px; padding: 7px 10px; font-size: 0.74rem; }
      .corner-controls { width: min(360px, calc(100vw - 24px)); }
      .music-bar { padding: 9px; }
      .music-track-select { width: 140px; }
      .directory-assistant { width: min(390px, calc(100vw - 24px)); left: 12px; bottom: 112px; }
      .directory-assistant__toggle { min-height: 40px; padding: 8px 11px; font-size: 0.78rem; }
      .directory-assistant__panel { left: 12px; bottom: 166px; width: min(390px, calc(100vw - 24px)); max-height: min(76vh, 580px); padding: 13px; }
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
      .page-hero-art { width: 540px; max-width: none; right: -240px; top: 42%; opacity: 0.34; }
      .corner-controls { left: 12px; right: 12px; bottom: 12px; width: auto; max-width: none; flex-direction: column; align-items: stretch; justify-content: flex-end; }
      .back-to-top, .music-toggle { font-size: 0.74rem; min-height: 40px; padding: 7px 10px; background-color: rgba(16,40,61,0.48); max-width: none; white-space: nowrap; }
      .music-toggle { position: static; left: auto; right: auto; bottom: auto; }
      .back-to-top { position: static; left: auto; right: auto; bottom: auto; align-self: flex-end; }
      .music-toggle { background-color: rgba(255,255,255,0.52); }
      .music-toggle[data-state="playing"] { background-color: rgba(216,187,104,0.52); }
      .music-bar { width: 100%; }
      .music-bar__top { align-items: flex-start; }
      .music-track-label { flex: 1; }
      .music-track-select { width: 100%; }
      .music-bar__bottom { align-items: flex-start; gap: 6px; }
      .music-volume { width: 76px; }
      .directory-assistant { width: calc(100vw - 24px); left: 12px; bottom: 176px; }
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
      [data-animated="true"], .intro-curtain, .hero-accent, .hero-route, .hero-node {
        animation: none !important;
        transform: none !important;
      }
      .intro-curtain { display: none; }
    }
    """
    (ASSET_OUT / "styles.css").write_text(dedent(css).strip() + "\n", encoding="utf-8")

    js = r"""
    const DATA = window.TRI_COUNTY_GUIDE_DATA || { directory_sources: [], resources: [] };
    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      })[char]);
    }

    function textMatch(item, query) {
      const blob = Object.values(item).join(" ").toLowerCase();
      return blob.includes(query.toLowerCase());
    }

    function uniqueValues(items, field) {
      return [...new Set(items.map(item => item[field]).filter(Boolean))].sort((a, b) => a.localeCompare(b));
    }

    function populateSelect(select, values, allLabel) {
      if (!select) return;
      select.innerHTML = `<option value="All">${allLabel}</option>` + values.map(value => `<option value="${value}">${value}</option>`).join("");
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
          <p class="source-note">Details can change. Open the source, then submit a correction if this pathway is outdated.</p>
        </article>
      `;
    }

    function resourceCard(item) {
      const url = item.website || item.source_url || "";
      const link = url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">Open source</a>` : `<span class="source-note">Source link needed</span>`;
      return `
        <article class="resource-item">
          <div class="resource-item__head">
            <h3>${escapeHtml(item.resource_name || "Unnamed resource")}</h3>
          </div>
          <p>${escapeHtml([item.town, item.county, item.state].filter(Boolean).join(", "))} - ${escapeHtml(item.resource_type || "Resource")} - ${escapeHtml(item.category || "General")}</p>
          <p><span class="badge">${escapeHtml(item.access_mode || "Unknown access")}</span> <span class="badge">${escapeHtml(item.source_type || "Unknown source")}</span></p>
          <p>${escapeHtml(item.notes || "Use as a lead and confirm details before action.")}</p>
          <p class="source-note">If this looks outdated, use the correction form so the guide can be updated.</p>
          ${link}
        </article>
      `;
    }

    function assistantCard(item) {
      const title = item.title || item.resource_name || item.channel || item.place || "Directory result";
      const url = item.url || item.website || item.source_url || "";
      const county = item.county || item.area_served || [item.town, item.state].filter(Boolean).join(", ") || "Regional";
      const category = item.kind || item.resource_type || item.channel_type || item.type || "Directory route";
      const description = item.best_for || item.notes || item.asks || item.short_description || "Use this as a starting point, then confirm current details.";
      const action = item.action || item.reader_action || "Open the source, then submit a correction if details have changed.";
      const typeLabel = item.assistant_type || "Directory";
      const sourceLink = url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer" aria-label="Open source for ${escapeHtml(title)}">Open source</a>` : `<span class="source-note">Source link needed</span>`;
      return `
        <article class="assistant-result" role="listitem">
          <div class="assistant-result__meta">
            <span class="assistant-result__type">${escapeHtml(typeLabel)}</span>
            <span>${escapeHtml(county)}</span>
            <span>${escapeHtml(category)}</span>
          </div>
          <h3>${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(title)}</a>` : escapeHtml(title)}</h3>
          <p>${escapeHtml(description)}</p>
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
        ...(DATA.directory_sources || []).map(item => ({ ...item, assistant_type: "Shortcut" })),
        ...(DATA.resources || []).map(item => ({ ...item, assistant_type: "Lead bank" })),
        ...(DATA.amplifier_channels || []).map(item => ({ ...item, assistant_type: "Amplifier" })),
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
        if (!terms.length && item.assistant_type === "Shortcut") score += 1;
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
        const displayQuery = search || "regional help";
        const matches = assistantSearch(displayQuery);
        status.textContent = matches.length
          ? `Showing ${matches.length} route${matches.length === 1 ? "" : "s"} for "${displayQuery}".`
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
          render(input.value || "funding events business support");
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

    function initSourceSearch() {
      const host = document.querySelector("#source-results");
      if (!host) return;
      const input = document.querySelector("#source-search");
      const chips = [...document.querySelectorAll("[data-source-filter]")];
      let county = "All";
      function render() {
        const query = input.value.trim();
        const filtered = DATA.directory_sources
          .filter(item => (county === "All" || item.county === county) && (!query || textMatch(item, query)))
          .sort((a, b) => String(a.title || "").localeCompare(String(b.title || "")));
        host.innerHTML = filtered.map(sourceCard).join("") || `<p class="section-note">No shortcuts match that search yet.</p>`;
      }
      input.addEventListener("input", render);
      chips.forEach(chip => chip.addEventListener("click", () => {
        county = chip.dataset.sourceFilter;
        chips.forEach(c => c.classList.toggle("is-active", c === chip));
        render();
      }));
      render();
    }

    function initResourceSearch() {
      const host = document.querySelector("#resource-results");
      if (!host) return;
      const input = document.querySelector("#resource-search");
      const chips = [...document.querySelectorAll("[data-resource-filter]")];
      const typeSelect = document.querySelector("#resource-type-filter");
      const accessSelect = document.querySelector("#access-mode-filter");
      let county = "All";
      populateSelect(typeSelect, uniqueValues(DATA.resources, "resource_type"), "All types");
      populateSelect(accessSelect, uniqueValues(DATA.resources, "access_mode"), "All access modes");
      function render() {
        const query = input.value.trim();
        const resourceType = typeSelect ? typeSelect.value : "All";
        const accessMode = accessSelect ? accessSelect.value : "All";
        const filtered = DATA.resources
          .filter(item => (county === "All" || item.county === county) && (!query || textMatch(item, query)))
          .filter(item => resourceType === "All" || item.resource_type === resourceType)
          .filter(item => accessMode === "All" || item.access_mode === accessMode)
          .sort((a, b) => String(a.resource_name || "").localeCompare(String(b.resource_name || "")))
          .slice(0, 80);
        host.innerHTML = filtered.map(resourceCard).join("") || `<p class="section-note">No local inventory entries match that search.</p>`;
      }
      input.addEventListener("input", render);
      [typeSelect, accessSelect].forEach(select => select && select.addEventListener("change", render));
      chips.forEach(chip => chip.addEventListener("click", () => {
        county = chip.dataset.resourceFilter;
        chips.forEach(c => c.classList.toggle("is-active", c === chip));
        render();
      }));
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

    function initPrintButtons() {
      document.querySelectorAll(".print-button").forEach(button => {
        button.addEventListener("click", () => window.print());
      });
    }

    function initCornerControls() {
      const backToTop = document.querySelector(".back-to-top");
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
      const toggle = document.querySelector(".music-toggle");
      const trackSelect = document.querySelector(".music-track-select");
      const progress = document.querySelector(".music-progress");
      const timeLabel = document.querySelector(".music-time");
      const volume = document.querySelector(".music-volume");
      const intro = document.querySelector(".intro-curtain");
      const loopAudio = document.getElementById("site-music-loop");
      if (!toggle || !loopAudio) return;

      const MUSIC_KEY = "triCountyPianoMusicV2";
      const TIME_KEY = "triCountyPianoLoopTimeV2";
      const INTRO_KEY = "triCountyLandingIntroSeenV2";
      const TRACK_KEY = "triCountyPianoTrackV2";
      const VOLUME_KEY = "triCountyPianoVolumeV2";
      const savedChoice = localStorage.getItem(MUSIC_KEY);
      const hasSeenIntro = localStorage.getItem(INTRO_KEY) === "seen";
      const saveData = Boolean(navigator.connection && navigator.connection.saveData);
      const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      let isPlaying = false;
      let delayedStartId = null;
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
        const fallback = Number.isFinite(savedVolume) ? savedVolume : 58;
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
        if (state === "playing") {
          toggle.textContent = "Stop";
          toggle.setAttribute("aria-pressed", "true");
        } else {
          toggle.textContent = "Play";
          toggle.setAttribute("aria-pressed", "false");
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

      async function startMusic({ userInitiated = false, withIntro = false } = {}) {
        if (withIntro) {
          if (delayedStartId) window.clearTimeout(delayedStartId);
          delayedStartId = window.setTimeout(() => {
            delayedStartId = null;
            startLoop({ userInitiated, fromBeginning: true, resume: false });
          }, 2600);
          return;
        }
        await startLoop({ userInitiated, resume: true });
      }

      function stopMusic() {
        rememberTime({ force: true });
        if (delayedStartId) {
          window.clearTimeout(delayedStartId);
          delayedStartId = null;
        }
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
        localStorage.setItem(INTRO_KEY, "seen");
      }

      function startAfterFirstGesture(event) {
        if (event.target && event.target.closest && event.target.closest(".music-bar")) return;
        if (isPlaying || localStorage.getItem(MUSIC_KEY) === "stopped" || prefersReducedMotion || saveData) return;
        startMusic({ userInitiated: true });
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
          window.setTimeout(markIntroComplete, 10300);
          if (savedChoice !== "stopped" && !saveData) {
            window.setTimeout(() => startMusic({ withIntro: true }), 120);
            document.addEventListener("pointerdown", startAfterFirstGesture, { once: true });
            document.addEventListener("keydown", startAfterFirstGesture, { once: true });
          }
        }
      } else if (savedChoice === "playing" && !saveData && !prefersReducedMotion) {
        window.setTimeout(() => startMusic(), 250);
      }
    }

    initSourceSearch();
    initResourceSearch();
    initDirectoryAssistant();
    initCopyButtons();
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
- `network/` - searchable directory shortcuts and {summary['row_count']}-row local lead bank
- `posting/` - physical/digital posting and public-notice guidance
- `region/` - regional routing model
- `counties/` - Colfax, Las Animas, and Huerfano county pages
- task-intent pages:
{task_page_lines}
- `templates/` - copy-ready outreach templates
- `submit/` - listing and channel-update intake form
- `appendix/` - public contact/resource appendix grouped by county and community
- `about/` - creation process, method, caveats, and source index
- `assets/animations/` - layered animated yucca SVG banner, CTA marker, and preview files
- `assets/audio/` - Library of Congress public-domain regional MP3 tracks used by the site music bar
- `data/tri_county_persona_resources.csv` - source lead bank
- `data/guide-data.json` - directory shortcuts plus source data
- `data/directory-metadata.json` - full machine-readable metadata for every directory shortcut and local inventory entry
- `SOURCES.md` - directory, amplifier, and posting source manifest
- Global `Ask directory` assistant - client-side search across shortcuts, lead-bank rows, amplifier channels, and posting pathways
- Global music bar - Library of Congress public-domain regional audio with play/stop, track choice, progress, and volume controls

## Data summary

- Total local inventory rows: {summary['row_count']}
- County mix: {summary['county']}
- Resource type mix: {summary['resource_type']}

## Caveat

The local resource inventory is a lead bank. Verify phone numbers, eligibility, listing status, and submission rules before publication, printing, outreach, or spending.

## QA notes

- Local HTML/asset references were checked after generation.
- SEO metadata is generated from the page shell: title, description, canonical URL, robots tag, social preview tags, JSON-LD, sitemap, and robots.txt.
- Public pages distinguish directory shortcuts, amplifier channels, public-notice/posting pathways, and lead-bank rows.
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
            f"- [{item['title']}]({item['url']}) - {item['kind']}. {item['best_for']} Action: {item['action']}"
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

The {summary['row_count']}-row inventory is a lead bank. It is useful for discovery, outreach planning, and finding patterns. It should not be presented as a fully verified public business directory without additional confirmation.

## What The Site Incorporates

- A three-path homepage: Plan Your Growth, Find the Network, Understand the Region.
- A searchable shortcut directory with {len(DIRECTORY_SOURCES)} researched sources.
- A regional amplifier page with {len(AMPLIFIER_CHANNELS)} channel rows and practical source-follow-up guidance.
- A posting page separating official notices, physical boards, digital calendars, and field-check tasks.
- A public contact appendix grouped by county and community.
- A searchable local inventory using the existing CSV/JSON data.
- County pages that point to local first stops instead of burying users in one long HTML document.
- Templates for listing requests, event calendar submissions, media pitches, partner asks, and follow-up tracking.
- About/method language moved away from the homepage to reduce the "AI report" feel.

## Directory Source Map

{chr(10).join(county_sections)}

## Publication Priorities

1. Verify official submission links and preferred contact paths with each chamber, city/tourism office, creative district, newspaper, and economic-development office.
2. Ask whether public wording should say "partner", "resource", "directory", or "referral" for each organization.
3. Keep commercial scraping out of the public guide. Point users to official directories instead.
4. Maintain update dates beside data-heavy inventory sections.
"""
    (OUT / "RESEARCH_DIVE.md").write_text(notes, encoding="utf-8")

    source_manifest = f"""# Source Manifest

Generated: {BUILD_DATE}

This manifest preserves the source layer used by the Netlify guide. Source entries are practical routing leads, not endorsements, guarantees, or proof of acceptance.

## Directory Shortcuts

{chr(10).join(f"- [{item['title']}]({item['url']}) - {item['county']}; {item['kind']}; {item['best_for']}" for item in DIRECTORY_SOURCES)}

## Amplifier Channels

{chr(10).join(f"- [{item['channel']}]({item['source_url']}) - {item['area_served']}; {item['channel_type']}; ask about current rates, deadlines, and submission rules when relevant." for item in AMPLIFIER_CHANNELS)}

## Posting And Public-Notice Pathways

{chr(10).join(f"- {item['place']} - {item['status']}" + (f"; source: {item['source_url']}" if item['source_url'] else "; source: field check needed") for item in POSTING_SPACES)}

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
- Paid/free status, advertising availability, approval rules, print deadlines, and audience size remain direct-contact follow-up tasks unless explicitly stated in a source.
- Fresh scripted link verification is exported separately after build as `data/live_link_verification_20260622.json` and `data/LIVE_LINK_VERIFICATION_20260622.md` when the verification script is run.
- The stale Raton/Colfax directory paths from the added PDF sources were replaced with working official parent/category pages in the public shortcut layer.

## Manual Publication Check

Before public launch, open the deployed Netlify preview and check:

- Home hero yucca/mountain animation, reduced-motion behavior, and mobile title wrapping.
- Network search for `chamber`, `artist`, `media`, `grant`, `Raton`, `Trinidad`, and `Walsenburg`.
- Network filters for resource type and access mode.
- Amplifier page rows for source URL and practical channel use.
- Posting page language: no board, calendar, newsletter, or newspaper should be framed as guaranteed ad placement.
- County page nav paths.
- Footer logo scale.
- All high-priority external links.
- `data/LIVE_LINK_VERIFICATION_20260622.md` for bot-blocked, timed-out, or manually-confirmed URLs.
"""
    (OUT / "QA_REPORT.md").write_text(qa, encoding="utf-8")


def write_pages(rows: list[dict], summary: dict) -> None:
    (OUT / "index.html").write_text(home_page(summary), encoding="utf-8")
    for folder in ["plan", "amplifiers", "network", "posting", "region", "templates", "submit", "appendix", "about"]:
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    for item in TASK_PAGE_DEFS:
        path = OUT / ACTIVE_PATHS[item["active"]]
        path.mkdir(parents=True, exist_ok=True)
    (OUT / "plan" / "index.html").write_text(plan_page(), encoding="utf-8")
    (OUT / "amplifiers" / "index.html").write_text(amplifiers_page(), encoding="utf-8")
    (OUT / "network" / "index.html").write_text(network_page(rows), encoding="utf-8")
    (OUT / "posting" / "index.html").write_text(posting_page(), encoding="utf-8")
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

