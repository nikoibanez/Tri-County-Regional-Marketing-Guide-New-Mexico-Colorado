from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "tri_county_persona_resources.csv"
JSON_PATH = ROOT / "data" / "tri_county_persona_resources.json"
REVIEW_PATH = ROOT / "review" / "DIGITAL_ONLY_CREATIVE_DIRECTORY_EXPANSION_20260627.md"
TODAY = "2026-06-27"


FIELDNAMES = [
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


DEFAULT_NOTES = (
    "Digital/source-linked creative lead added from a public online directory, official creative-district page, "
    "state creative-economy source, or artist application page. Confirm current activity, eligibility, service area, "
    "contact route, listing rules, fees, and deadlines at the source before outreach, spending, printing, or promising placement."
)
DEFAULT_AUDIENCE = "Artist; Creative business; Arts / culture audiences; For-Profit; Non-Profit; Program; Visitors / tourists"
DEFAULT_GOALS = "Improve Online Visibility; Add / Correct Info; Promote Something; Find Money or Help; Start Something; Track Results"


def slug(value: str, limit: int = 86) -> str:
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:limit].rstrip("-")


def row(
    name: str,
    category: str,
    town: str,
    county: str,
    state: str,
    *,
    website: str = "",
    source_url: str,
    source_type: str,
    phone: str = "",
    email: str = "",
    address: str = "",
    resource_type: str = "Digital creative directory / source-linked lead",
    access_mode: str = "Online",
    audience: str = DEFAULT_AUDIENCE,
    cost_level: str = "Unknown / verify",
    goals: str = DEFAULT_GOALS,
    notes: str = DEFAULT_NOTES,
    confidence: str = "Medium",
    verification: str = "Source-linked public web review",
    follow_up: str = "true",
    row_id: str | None = None,
) -> dict[str, str]:
    return {
        "id": row_id or slug(f"{name}-{town}-{county}-{category}"),
        "resource_name": name,
        "category": category,
        "town": town,
        "county": county,
        "state": state,
        "website": website,
        "contact_email": email,
        "contact_phone": phone,
        "physical_address": address,
        "source_url": source_url,
        "source_type": source_type,
        "last_verified_date": TODAY,
        "verification_method": verification,
        "confidence_level": confidence,
        "notes": notes,
        "needs_follow_up": follow_up,
        "resource_type": resource_type,
        "audience_served": audience,
        "cost_level": cost_level,
        "access_mode": access_mode,
        "goal_relevance": goals,
    }


NM_CREATIVE_RESOURCE = "https://www.edd.newmexico.gov/divisions-and-offices/creative-industries/creative-industries-resource-center/"
NM_CREATIVE_GRANTS = "https://www.edd.newmexico.gov/grants/cid-grants/"
NM_CREATIVE_SUBMITTABLE = "https://creativeindustriesdivision.submittable.com/submit"
NM_CREATIVECON_PRESS = "https://www.edd.newmexico.gov/press-releases/state-launches-nm-creativecon-series-to-boost-creative-economy/"
CREATIVE_NM = "https://www.creativenewmexico.org/"
STARTUPSPACE_NM_RESOURCE = "https://www.startupspace.app/resource?page=62"
STARTUPSPACE_CREATIVE_SEARCH = "https://startupspace.app/resource?comm_interest_search%5B0%5D=750&feature_button_show_hide=show&filter_show_hide=show&gray_button_show_hide=show&group_id=NTc5&is_search=1&map_list_type=list&map_view=hide&page=16&resource_type_selection=view_all_resource&search_latitude=34.9727305&search_location=New+Mexico%2C+USA&search_longitude=-105.0323635&search_radius=200"
CO_CREATIVE_INDUSTRIES = "https://oedit.colorado.gov/colorado-creative-industries"
CO_CREATIVE_DISTRICTS = "https://oedit.colorado.gov/colorado-creative-districts"
CALL_YOURSELF_CREATIVE = "https://callyourselfcreative.org/partners"
ARTS_IN_SOCIETY = "https://www.redlineart.org/ais-apply-for-a-grant"
LA_VETA_ARTISTS = "https://www.lavetacreativedistrict.org/artists"
LA_VETA_AID = "https://www.lavetacreativedistrict.org/aid-for-artists"
KENNY_SCHNEIDER = "https://www.lavetacreativedistrict.org/artists/kenny-schneider"
WALSENBURG_MAKERS = "https://www.walsenburgmercantile.com/meet-our-vendors"
TRINIDAD_COMMUNITY = "https://www.trinidadcreativedistrict.org/arts-in-the-trinidad-colorado-community"
TRINIDAD_ABOUT = "https://www.trinidadcreativedistrict.org/about"
TRINIDAD_SPACE = "https://www.trinidadcreativedistrict.org/space-to-create"
TRINIDAD_GET_LIT_2026 = "https://www.trinidadcreativedistrict.org/copy-of-2025-get-lit-literary-festival"
TRINIDAD_ZAPP_2026 = "https://www.zapplication.org/event-info.php?ID=14415"
TRINIDAD_VISUAL_ARTS = "https://visittrinidadcolorado.com/arts-culture/visual-arts/"
TRINIDAD_CAMPAIGNS = "https://app.seemylegacy.com/community/2682/campaign/7906"
ANGEL_FIRE_ARTS_DIRECTORY = "https://angelfirechamber.org/business/category/artists-galleries-studios/"
ANGEL_FIRE_CATERING = "https://visitangelfirenm.com/catering/"
TAOS_ANGEL_FIRE_GALLERIES = "https://taos.org/places/category/art-galleries/angel-fire/"
RATON_CITY_ARTS = "https://www.ratonnm.gov/community/arts/index.php"
EXPLORE_RATON_ARTS = "https://www.exploreraton.com/arts-culture"
EXPLORE_RATON_SHOP = "https://www.exploreraton.com/shop"
RATON_ARTS_VISUAL = "https://www.ratonarts.org/visual-arts"
SPANISH_PEAKS_GALLERIES = "https://spanishpeakscountry.com/business-directory/categories/galleries"
SPANISH_PEAKS_ARTS = "https://spanishpeaksarts.org/"
NM_ARTIST_DIRECTORY = "https://www.newmexicoartistdirectory.com/"


ENTRIES: list[dict[str, str]] = [
    row(
        "New Mexico Creative Industries Resource Center",
        "Statewide creative resource directory",
        "Regional",
        "Regional",
        "NM",
        website=NM_CREATIVE_RESOURCE,
        source_url=NM_CREATIVE_RESOURCE,
        source_type="Official state creative-economy directory",
        resource_type="Creative directory / listing path",
        notes=(
            "Official New Mexico creative-economy resource directory and listing-update path. Use for Colfax/Raton-area creative businesses, spaces, and support organizations, then confirm each listing at the source."
        ),
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "NM Creative Industries Submit or Update a Resource Listing",
        "Creative listing submission path",
        "Regional",
        "Regional",
        "NM",
        website=NM_CREATIVE_RESOURCE,
        source_url=NM_CREATIVE_RESOURCE,
        source_type="Official state submission/update path",
        resource_type="Creative listing update path",
        notes="Use this source to submit or update a New Mexico creative business, creative venture, or creative-economy resource listing; confirm current form requirements before submission.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "NM Creative Industries Grant Opportunities",
        "Creative grants and public development opportunities",
        "Regional",
        "Regional",
        "NM",
        website=NM_CREATIVE_GRANTS,
        source_url=NM_CREATIVE_GRANTS,
        source_type="Official state grants page",
        resource_type="Grant / funding resource",
        notes="Official Creative Industries Division grant page. Verify current rounds, eligibility, deadlines, and whether a program applies to an individual, business, nonprofit, public entity, or support organization.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "Creative Industries Division Grant Portal",
        "Creative grants portal",
        "Regional",
        "Regional",
        "NM",
        website=NM_CREATIVE_SUBMITTABLE,
        source_url=NM_CREATIVE_SUBMITTABLE,
        source_type="Official grant portal",
        resource_type="Grant application portal",
        notes="Portal only shows grant programs currently accepting applications. Check the CID grants page for program details before applying.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "Creative New Mexico",
        "Statewide creative advocacy and resource organization",
        "Regional",
        "Regional",
        "NM",
        website=CREATIVE_NM,
        source_url=CREATIVE_NM,
        source_type="Creative-sector organization website",
        resource_type="Creative support organization",
        notes="Statewide organization connecting, promoting, and advocating for creative individuals, organizations, industries, and communities. Confirm current programs, workshops, grant links, and membership paths.",
        confidence="Medium",
    ),
    row(
        "New Mexico Artist Directory",
        "Statewide artist studios, galleries, and media directory",
        "Regional",
        "Regional",
        "NM",
        website=NM_ARTIST_DIRECTORY,
        source_url=NM_ARTIST_DIRECTORY,
        source_type="Statewide artist directory",
        resource_type="Digital artist directory",
        notes="Statewide artist directory with regional, gallery, media, studio-tour, class, workshop, and art-service browsing. Use as a broader New Mexico discovery source for Colfax-area artists, then verify each profile at the source.",
        confidence="Medium",
    ),
    row(
        "Angel Fire Chamber Artists, Galleries, and Studios Directory",
        "Chamber arts category directory",
        "Angel Fire",
        "Colfax",
        "NM",
        website=ANGEL_FIRE_ARTS_DIRECTORY,
        source_url=ANGEL_FIRE_ARTS_DIRECTORY,
        source_type="Chamber member directory category",
        resource_type="Digital artist directory",
        notes="Angel Fire Chamber arts category listing artists, galleries, studios, creative nonprofits, maker retail, and related businesses. Confirm current membership and contact route before outreach.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "Art Up Northern New Mexico",
        "Arts nonprofit / artist membership organization",
        "Angel Fire",
        "Colfax",
        "NM",
        website="https://artup-nnm.org",
        source_url="https://angelfirechamber.org/business/art-up-northern-new-mexico/",
        source_type="Chamber member directory profile",
        phone="575-224-1180",
        address="P.O. Box 712, Angel Fire, NM 87710",
        resource_type="Creative nonprofit / Artist support",
        notes="Chamber profile describes Art Up Northern New Mexico as a nonprofit promoting creative arts through programs, membership, shows, volunteers, and donations. Confirm current programs and listing paths before outreach.",
        confidence="High",
        verification="Official source checked",
        row_id="art-up-northern-new-mexico-colfax-arts-nonprofit-artist-membership-organiz",
    ),
    row(
        "Visit Angel Fire Catering and Event-Service Directory",
        "Catering and event-service listing directory",
        "Angel Fire",
        "Colfax",
        "NM",
        website=ANGEL_FIRE_CATERING,
        source_url=ANGEL_FIRE_CATERING,
        source_type="Official visitor directory category",
        resource_type="Digital creative service directory",
        notes="Visit Angel Fire catering page lists local catering and event-service options. Use for food, hospitality, event, and creative-service routing, then verify current availability and terms with each listing.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "Taos.org Angel Fire Art Galleries Directory",
        "Regional visitor art-gallery directory",
        "Angel Fire",
        "Colfax",
        "NM",
        website=TAOS_ANGEL_FIRE_GALLERIES,
        source_url=TAOS_ANGEL_FIRE_GALLERIES,
        source_type="Regional visitor directory category",
        resource_type="Digital gallery directory",
        notes="Regional visitor directory category for Angel Fire art galleries. Use as a secondary cross-check for Angel Fire-area gallery discovery and confirm each listing directly.",
        confidence="Medium",
    ),
    row(
        "City of Raton Arts Page",
        "Municipal arts page and related arts links",
        "Raton",
        "Colfax",
        "NM",
        website=RATON_CITY_ARTS,
        source_url=RATON_CITY_ARTS,
        source_type="Municipal arts page",
        resource_type="Digital arts directory",
        notes="City page groups Old Pass Gallery, Raton Arts and Cultural District, The Raton Museum, Santa Fe Trail School for the Performing Arts, and Shuler Theater. Verify current pages and contacts before outreach.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "Explore Raton Arts and Culture Page",
        "Visitor-facing arts and culture route",
        "Raton",
        "Colfax",
        "NM",
        website=EXPLORE_RATON_ARTS,
        source_url=EXPLORE_RATON_ARTS,
        source_type="Tourism arts page",
        resource_type="Digital arts directory",
        notes="Explore Raton arts page links cultural venues, galleries, film resources, local art news, Old Pass Gallery, and performing arts routes. Verify current links before publication or outreach.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "Explore Raton Shop Local Directory",
        "Visitor-facing shopping and creative goods directory",
        "Raton",
        "Colfax",
        "NM",
        website=EXPLORE_RATON_SHOP,
        source_url=EXPLORE_RATON_SHOP,
        source_type="Tourism shopping directory",
        resource_type="Digital creative retail directory",
        notes="Explore Raton shop page lists gift shops, arts and crafts, sweets, local goods, and visitor-facing retail. Treat as a discovery source and verify each listing before outreach.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "Raton Arts and Humanities Council Visual Arts Calendar",
        "Visual arts calendar and gallery program route",
        "Raton",
        "Colfax",
        "NM",
        website=RATON_ARTS_VISUAL,
        source_url=RATON_ARTS_VISUAL,
        source_type="Arts organization calendar page",
        resource_type="Digital arts calendar",
        notes="Raton Arts and Humanities Council visual arts page provides a calendar route for Old Pass Gallery programming. Verify current show dates and submission/contact process directly.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "NM CreativeCon / Creative Industries Event Series",
        "Creative entrepreneurship training and networking series",
        "Raton",
        "Colfax",
        "NM",
        website=NM_CREATIVECON_PRESS,
        source_url=NM_CREATIVECON_PRESS,
        source_type="Official state press release",
        resource_type="Creative entrepreneurship program",
        access_mode="Online + Event / verify",
        notes="The 2026 Raton event was listed as part of the statewide NM CreativeCon series. Treat this as a program/source lead and verify future dates before presenting it as an active event.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "Startup Space Creative Assets Directory - Northeast New Mexico Search",
        "Digital creative assets directory",
        "Regional",
        "Colfax",
        "NM",
        website=STARTUPSPACE_CREATIVE_SEARCH,
        source_url=STARTUPSPACE_CREATIVE_SEARCH,
        source_type="Digital directory search result",
        resource_type="Digital creative directory / source-linked lead",
        notes="Startup Space/NM creative-resource directory search surface for creative assets near northeastern New Mexico. Listings can change and may be difficult for scripted tools to inspect; verify each listing manually.",
        confidence="Medium",
    ),
    row(
        "LK Creative",
        "Freelance graphic design / online resource",
        "Angel Fire",
        "Colfax",
        "NM",
        website=STARTUPSPACE_NM_RESOURCE,
        source_url=STARTUPSPACE_NM_RESOURCE,
        source_type="Startup Space digital listing",
        resource_type="Creative business / source-linked lead",
        notes="Search result identifies LK Creative as an online resource for freelance graphic design in Angel Fire. Confirm current contact, service area, and active status before outreach.",
        confidence="Low",
        verification="Search-result source linked; needs manual verification",
    ),
    row(
        "Meditating Monkey Art Emporium",
        "Creative retail / artist gathering space",
        "Raton",
        "Colfax",
        "NM",
        website=STARTUPSPACE_CREATIVE_SEARCH,
        source_url=STARTUPSPACE_CREATIVE_SEARCH,
        source_type="Startup Space digital listing",
        resource_type="Creative business / source-linked lead",
        access_mode="Online + Physical / verify",
        notes="Digital listing/search snippets identify a Raton creative/art emporium. Confirm current activity, address, contact route, and listing status before publication or outreach.",
        confidence="Low",
        verification="Search-result source linked; needs manual verification",
    ),
    row(
        "Colorado Creative Industries",
        "Statewide arts funding and creative-sector support",
        "Regional",
        "Regional",
        "CO",
        website=CO_CREATIVE_INDUSTRIES,
        source_url=CO_CREATIVE_INDUSTRIES,
        source_type="Official state creative agency page",
        resource_type="Grant / funding resource",
        notes="Colorado Creative Industries provides funding, support, and recognition for artists, creative businesses, and organizations. Verify current program rules and deadlines before applying.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "Colorado Creative Districts",
        "Certified creative district directory and program",
        "Regional",
        "Regional",
        "CO",
        website=CO_CREATIVE_DISTRICTS,
        source_url=CO_CREATIVE_DISTRICTS,
        source_type="Official state creative district page",
        resource_type="Creative district directory",
        notes="Official Colorado Creative Districts program source. Use to understand certified districts and cross-check La Veta and Trinidad creative-district context.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "Call Yourself Creative Certified District Partners",
        "Creative district partner contact list",
        "Regional",
        "Regional",
        "CO",
        website=CALL_YOURSELF_CREATIVE,
        source_url=CALL_YOURSELF_CREATIVE,
        source_type="Creative district partner directory",
        resource_type="Creative district directory",
        notes="Partner list for Colorado certified creative districts. Use as a contact-routing source for district-to-district questions, then confirm details with the listed organization.",
        confidence="Medium",
    ),
    row(
        "Arts in Society Colorado Grant",
        "Colorado artist and nonprofit grant",
        "Regional",
        "Regional",
        "CO",
        website=ARTS_IN_SOCIETY,
        source_url=ARTS_IN_SOCIETY,
        source_type="Grant program page",
        resource_type="Grant / funding resource",
        notes="Colorado grant program for nonprofits, individuals, and eligible partners. Confirm cycle status, eligibility, and application requirements before sharing as an active opportunity.",
        confidence="Medium",
    ),
    row(
        "Spanish Peaks Country Galleries Directory",
        "Visitor-facing gallery directory",
        "La Veta / Walsenburg",
        "Huerfano",
        "CO",
        website=SPANISH_PEAKS_GALLERIES,
        source_url=SPANISH_PEAKS_GALLERIES,
        source_type="Tourism business directory category",
        resource_type="Digital gallery directory",
        notes="Spanish Peaks Country galleries category lists Huerfano-area galleries, museums, creative retail, and shopping routes. Use as a first Huerfano gallery discovery path, then verify each listing.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "Spanish Peaks Arts Council Online Shows and Member Routes",
        "Arts council, gallery, member artist, and exhibition route",
        "La Veta",
        "Huerfano",
        "CO",
        website=SPANISH_PEAKS_ARTS,
        source_url=SPANISH_PEAKS_ARTS,
        source_type="Arts organization website",
        resource_type="Digital arts calendar / artist route",
        notes="Spanish Peaks Arts Council site links member artists, joining SPACe, exhibitions, workshops, and art events. Verify current show dates, member listing rules, and contact route before publication.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "La Veta Creative District Creatives Directory",
        "Digital local artist directory",
        "La Veta",
        "Huerfano",
        "CO",
        website=LA_VETA_ARTISTS,
        source_url=LA_VETA_ARTISTS,
        source_type="Official creative district directory",
        resource_type="Digital artist directory",
        notes="Official La Veta Creative District creatives directory. Use as the first source for La Veta-area artist discovery, then open each artist profile before contact.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "La Veta Creative District Aid for Artists",
        "Artist funding and emergency-resource list",
        "La Veta",
        "Huerfano",
        "CO",
        website=LA_VETA_AID,
        source_url=LA_VETA_AID,
        source_type="Official creative district resource page",
        resource_type="Grant / funding resource",
        notes="La Veta Creative District artist-aid page points creatives toward grants, relief, and support resources. Verify current program status because some relief funds or deadlines may have changed.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "Kenny Schneider / Kenetics",
        "Digital photography / painting / public art profile",
        "La Veta",
        "Huerfano",
        "CO",
        website="https://kenetics.wixsite.com/kenetics-1",
        source_url=KENNY_SCHNEIDER,
        source_type="Official creative district artist profile",
        phone="719-330-8479",
        email="kenetics@centurytel.net",
        address="PO Box 542, La Veta, CO 81055",
        resource_type="Creative business / artist profile",
        access_mode="Online + Local / verify",
        notes="Artist profile includes painting, drawing, graphics, film, video, public art, digital photography, and sculpture. Confirm preferred contact route and current project status before outreach.",
        confidence="High",
        verification="Official source checked",
        row_id="kenny-schneider-kenetics-huerfano-mixed-media-artist",
    ),
    row(
        "Walsenburg Mercantile Meet Our Makers Directory",
        "Digital maker and vendor directory",
        "Walsenburg",
        "Huerfano",
        "CO",
        website=WALSENBURG_MAKERS,
        source_url=WALSENBURG_MAKERS,
        source_type="Local business maker directory",
        resource_type="Digital maker directory",
        access_mode="Online + Physical / verify",
        notes="Public vendor/maker directory for local artisans, creators, and small businesses showcased by Walsenburg Mercantile. Confirm each maker before direct outreach.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "CREATE Trinidad Arts in the Community Directory",
        "Digital arts, gallery, class, music, and venue directory",
        "Trinidad",
        "Las Animas",
        "CO",
        website=TRINIDAD_COMMUNITY,
        source_url=TRINIDAD_COMMUNITY,
        source_type="Official creative district community directory",
        resource_type="Digital arts directory",
        notes="CREATE Trinidad's arts-in-the-community page groups galleries, classes, venues, music, museums, and creative opportunities. Confirm each listing with the linked source before outreach.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "CREATE Trinidad / Corazon de Trinidad Creative District",
        "Creative district organization and resource hub",
        "Trinidad",
        "Las Animas",
        "CO",
        website=TRINIDAD_ABOUT,
        source_url=TRINIDAD_ABOUT,
        source_type="Official creative district organization page",
        resource_type="Creative support organization",
        email="trinidadcreativedistrict@gmail.com",
        phone="(719) 846-9843",
        notes="Official creative district source describing support for artists, creative entrepreneurs, nonprofit cultural organizations, and creative initiatives. Confirm current staff/contact paths before formal requests.",
        confidence="High",
        verification="Official source checked",
        row_id="create-trinidad-las-animas-creative-district-cultural-hub",
    ),
    row(
        "Trinidad Space to Create Digital Resource Page",
        "Creative workspace and affordable creative-sector housing resource",
        "Trinidad",
        "Las Animas",
        "CO",
        website=TRINIDAD_SPACE,
        source_url=TRINIDAD_SPACE,
        source_type="Official creative district resource page",
        resource_type="Creative workspace / housing resource",
        access_mode="Online + Physical / verify",
        notes="Digital resource page for Trinidad Space to Create and related Commons information. Verify active availability, rental terms, and residential opportunity details at the source.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "Visit Trinidad Visual Arts Page",
        "Visitor-facing visual arts and gallery route",
        "Trinidad",
        "Las Animas",
        "CO",
        website=TRINIDAD_VISUAL_ARTS,
        source_url=TRINIDAD_VISUAL_ARTS,
        source_type="Tourism visual arts page",
        resource_type="Digital arts directory",
        notes="Visit Trinidad visual arts page routes users to galleries, Space to Create, public art, shopping, and arts itinerary paths. Verify each linked route before outreach.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "CREATE Trinidad Campaigns and Registration Portal",
        "Creative grant, ticketing, sponsorship, and volunteer portal",
        "Trinidad",
        "Las Animas",
        "CO",
        website=TRINIDAD_CAMPAIGNS,
        source_url=TRINIDAD_CAMPAIGNS,
        source_type="Creative district campaigns portal",
        resource_type="Grant / registration portal",
        access_mode="Online",
        notes="CREATE Trinidad portal lists current campaigns, including Creative Impact Grants and GET LIT ticketing when active. Dates, eligibility, ticketing, sponsorship, and grant requirements are time-sensitive and must be verified before use.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "2026 GET LIT Literary Festival and Trinidad Art Festival",
        "Writer, artist, festival, and sponsorship pathway",
        "Trinidad",
        "Las Animas",
        "CO",
        website=TRINIDAD_GET_LIT_2026,
        source_url=TRINIDAD_GET_LIT_2026,
        source_type="Official creative district event page",
        resource_type="Creative event / artist opportunity",
        access_mode="Online + Event / verify",
        notes="Official 2026 GET LIT and Trinidad Art Festival page. Dates and application paths are event-specific; verify before sharing, applying, sponsoring, or promoting.",
        confidence="High",
        verification="Official source checked",
    ),
    row(
        "Trinidad Art Fest 2026 ZAPP Artist Application",
        "Juried artist application portal",
        "Trinidad",
        "Las Animas",
        "CO",
        website=TRINIDAD_ZAPP_2026,
        source_url=TRINIDAD_ZAPP_2026,
        source_type="Artist application portal",
        resource_type="Artist application path",
        access_mode="Online",
        notes="ZAPP listing for Trinidad Art Fest 2026. Fees, deadlines, image requirements, and eligibility are time-sensitive; verify directly in the portal before applying.",
        confidence="Medium",
    ),
]


def read_rows() -> list[dict[str, str]]:
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [{field: row.get(field, "") for field in FIELDNAMES} for row in reader]


def write_rows(rows: list[dict[str, str]]) -> None:
    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        for item in rows:
            writer.writerow({field: item.get(field, "") for field in FIELDNAMES})
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    rows = read_rows()
    before_count = len(rows)
    index = {item["id"]: item for item in rows}
    added: list[str] = []
    updated: list[str] = []
    for entry in ENTRIES:
        current = index.get(entry["id"])
        if current:
            current.update({field: entry.get(field, "") for field in FIELDNAMES})
            updated.append(entry["id"])
        else:
            rows.append(entry)
            index[entry["id"]] = entry
            added.append(entry["id"])

    rows.sort(key=lambda item: (item.get("county", ""), item.get("town", ""), item.get("resource_name", "")))
    write_rows(rows)

    by_county = Counter(entry["county"] for entry in ENTRIES)
    by_type = Counter(entry["resource_type"] for entry in ENTRIES)
    source_rows = "\n".join(
        f"- {entry['resource_name']} - {entry['town']}, {entry['county']} - {entry['source_url']}"
        for entry in ENTRIES
    )
    review = f"""# Digital-Only Creative Directory Expansion - {TODAY}

## Summary

- Rows before: {before_count}
- Rows after: {len(rows)}
- New rows added: {len(added)}
- Existing rows updated: {len(updated)}
- Digital/source-linked creative entries processed: {len(ENTRIES)}

## County Mix

{chr(10).join(f"- {county}: {count}" for county, count in by_county.most_common())}

## Resource-Type Mix

{chr(10).join(f"- {rtype}: {count}" for rtype, count in by_type.most_common())}

## Method

Searched current public web sources for online-only or digital-first creative listings, artist application portals, creative-district directories, creative-economy resource centers, and source-linked listings across Raton, Angel Fire, Colfax County, Trinidad, Las Animas County, La Veta, Walsenburg, Huerfano County, and regional New Mexico/Colorado creative-support systems.

Official creative-district, state agency, and organization pages were added as higher-confidence rows. Startup Space/search-result-only leads were retained as lower-confidence source-linked leads requiring manual confirmation.

No row should be read as proof of grant eligibility, ad availability, acceptance into an event, active business status, endorsement, deadline, fee, or service availability without checking the source.

## Entries Processed

{source_rows}
"""
    REVIEW_PATH.write_text(review, encoding="utf-8")

    print(
        json.dumps(
            {
                "rows_before": before_count,
                "rows_after": len(rows),
                "added": len(added),
                "updated": len(updated),
                "processed": len(ENTRIES),
                "review": str(REVIEW_PATH),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
