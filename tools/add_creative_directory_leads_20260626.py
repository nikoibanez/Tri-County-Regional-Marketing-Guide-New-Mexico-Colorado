from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "tri_county_persona_resources.csv"
JSON_PATH = ROOT / "data" / "tri_county_persona_resources.json"
REVIEW_PATH = ROOT / "review" / "CREATIVE_DIRECTORY_EXPANSION_20260626.md"
TODAY = "2026-06-26"


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
    "Creative-directory lead added from a public local arts, tourism, chamber, creative-district, "
    "or maker directory. Open the source and confirm current hours, contact route, listing status, "
    "submission path, and availability before outreach, spending, printing, or promising placement."
)
DEFAULT_AUDIENCE = "Artist; Arts / culture audiences; For-Profit; Non-Profit; Program; Visitors / tourists"
DEFAULT_GOALS = "Start Something; Promote Something; Get Media Coverage; Reach People Offline; Improve Online Visibility; Add / Correct Info"

DROP_DUPLICATE_IDS = {
    "the-bakery-and-cafe-angel-fire-colfax-bakery-cafe",
    "taty-the-bump-colfax-cafe-bistro",
    "crafted-in-colorado-huerfano-creative-retail-local-goods",
    "la-veta-mercantile-huerfano-gallery-venue-creative-retail",
    "a-r-mitchell-museum-of-western-art-las-animas-museum-gallery",
    "brick-road-bakery-las-animas-bakery",
    "kathy-hill-s-studio-gallery-huerfano-arts-gallery",
}


def slug(value: str, limit: int = 74) -> str:
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
    resource_type: str = "Creative / Artist",
    access_mode: str = "Online + Physical",
    audience: str = DEFAULT_AUDIENCE,
    cost_level: str = "Unknown / verify",
    goals: str = DEFAULT_GOALS,
    notes: str = DEFAULT_NOTES,
    confidence: str = "Medium",
    follow_up: str = "true",
    row_id: str | None = None,
) -> dict[str, str]:
    return {
        "id": row_id or slug(f"{name}-{county}-{category}"),
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
        "verification_method": "Source-linked public directory review",
        "confidence_level": confidence,
        "notes": notes,
        "needs_follow_up": follow_up,
        "resource_type": resource_type,
        "audience_served": audience,
        "cost_level": cost_level,
        "access_mode": access_mode,
        "goal_relevance": goals,
    }


ANGEL_FIRE_ARTS = "https://angelfirechamber.org/business/category/artists-galleries-studios/"
ANGEL_FIRE_CULTURE = "https://angelfirechamber.org/visitor/arts-and-culture/"
EXPLORE_RATON_ARTS = "https://www.exploreraton.com/arts-culture"
RATON_ARTS = "https://www.ratonarts.org/"
RATON_OLD_PASS = "https://www.ratonnm.gov/business_detail_T7_R18.php"
TRINIDAD_COMMUNITY = "https://www.trinidadcreativedistrict.org/arts-in-the-trinidad-colorado-community"
TRINIDAD_SHOP = "https://visittrinidadcolorado.com/shop/"
TRINIDAD_VISUAL_ARTS = "https://visittrinidadcolorado.com/arts-culture/visual-arts/"
SPANISH_PEAKS_GALLERIES = "https://spanishpeakscountry.com/business-directory/categories/galleries"
SPANISH_PEAKS_DIRECTORY = "https://spanishpeakscountry.com/business-directory"
LA_VETA_CREATIVE_SPACES = "https://www.lavetacreativedistrict.org/creative-spaces"
LA_VETA_ARTISTS = "https://www.lavetacreativedistrict.org/artists"
WALSENBURG_MERCANTILE_VENDORS = "https://www.walsenburgmercantile.com/meet-our-vendors"


ENTRIES: list[dict[str, str]] = [
    row(
        "Raton Arts & Cultural District",
        "Creative district / arts hub",
        "Raton",
        "Colfax",
        "NM",
        website="https://www.nmartsandculturaldistricts.org/raton/",
        source_url="https://www.nmartsandculturaldistricts.org/raton/",
        source_type="State arts directory",
    ),
    row(
        "Raton Arts & Humanities Council / Old Pass Gallery",
        "Gallery / arts council",
        "Raton",
        "Colfax",
        "NM",
        website=RATON_ARTS,
        source_url=RATON_OLD_PASS,
        source_type="Organization and municipal source",
        phone="(575) 445-2052",
        address="145 S. First St., Raton, NM 87740",
        row_id="old-pass-gallery-raton-arts-humanities-council-colfax-arts-culture",
    ),
    row(
        "Old Pass Gallery",
        "Gallery / local-regional artist retail",
        "Raton",
        "Colfax",
        "NM",
        website=RATON_ARTS,
        source_url=RATON_OLD_PASS,
        source_type="Organization and municipal source",
        phone="(575) 445-2052",
        address="145 S. First St., Raton, NM 87740",
        row_id="old-pass-gallery-colfax-arts-culture",
    ),
    row(
        "Carl Swanson Gallery",
        "Painter / gallery",
        "Raton",
        "Colfax",
        "NM",
        website="https://carlswansongallery.com",
        source_url=EXPLORE_RATON_ARTS,
        source_type="Tourism arts page",
        address="210 S. 1st St., Raton, NM",
    ),
    row(
        "El Raton Media Works",
        "Film / media production support",
        "Raton",
        "Colfax",
        "NM",
        website="https://www.elratonmediaworks.org",
        source_url=EXPLORE_RATON_ARTS,
        source_type="Tourism arts page",
        resource_type="Media / Creative",
    ),
    row(
        "The Isabel Castillo School for the Performing Arts",
        "Performing arts / rentable studio theater",
        "Raton",
        "Colfax",
        "NM",
        website="https://www.facebook.com",
        source_url=EXPLORE_RATON_ARTS,
        source_type="Tourism arts page",
        resource_type="Creative education / venue",
    ),
    row(
        "The Shuler Theater",
        "Performing arts venue",
        "Raton",
        "Colfax",
        "NM",
        website="https://shulertheater.com",
        source_url=EXPLORE_RATON_ARTS,
        source_type="Tourism arts page",
        resource_type="Venue / Performing Arts",
    ),
    row(
        "Eagle Nest Mercantile",
        "Gift boutique / art gallery / maker retail",
        "Eagle Nest",
        "Colfax",
        "NM",
        website="https://www.eaglenestmercantile.com",
        source_url=ANGEL_FIRE_ARTS,
        source_type="Chamber directory",
        phone="(575) 312-9801",
        address="170 E. Therma Drive, Eagle Nest, NM",
        row_id="eagle-nest-mercantile-colfax-retail",
    ),
    row(
        "Art Up Northern New Mexico",
        "Arts nonprofit / artist membership organization",
        "Angel Fire",
        "Colfax",
        "NM",
        website="https://artup-nnm.org",
        source_url=ANGEL_FIRE_ARTS,
        source_type="Chamber directory",
        resource_type="Creative nonprofit / Artist support",
    ),
    row(
        "J. Binford-Bell Studio & Gallery",
        "Artist studio / gallery",
        "Angel Fire",
        "Colfax",
        "NM",
        website="https://binford-bellstudio.blogspot.com",
        source_url=ANGEL_FIRE_ARTS,
        source_type="Chamber directory",
    ),
    row(
        "Enchanted Circle Pottery",
        "Pottery / ceramics studio",
        "Angel Fire corridor",
        "Regional",
        "NM",
        website="https://www.enchantedcirclepottery.com",
        source_url=ANGEL_FIRE_ARTS,
        source_type="Chamber directory",
        address="26871 East U.S. Highway 64, Taos Canyon, NM",
        notes=(
            "Regional creative lead from the Angel Fire Chamber arts category; confirm whether the user's project needs a Colfax-only listing or an Enchanted Circle referral before outreach."
        ),
    ),
    row(
        "The Bakery & Cafe @ Angel Fire",
        "Bakery / cafe",
        "Angel Fire",
        "Colfax",
        "NM",
        website="https://thebakeryatangelfire.com/",
        source_url="https://angelfirechamber.org/business/the-bakery-cafe-angel-fire/",
        source_type="Chamber directory",
        phone="575-377-1525",
        address="3420 Mountain View Blvd., Angel Fire, NM 87710",
        resource_type="Food / Creative Business",
        audience="For-Profit; Program; Visitors / tourists; Arts / culture audiences",
        row_id="the-bakery-cafe-colfax-food-beverage",
    ),
    row(
        "Taty @ the Bump",
        "Cafe / bistro",
        "Angel Fire",
        "Colfax",
        "NM",
        website="https://www.facebook.com/taty.bistro",
        source_url=ANGEL_FIRE_ARTS,
        source_type="Chamber directory",
        resource_type="Food / Creative Business",
        audience="For-Profit; Program; Visitors / tourists; Arts / culture audiences",
        row_id="taty-at-the-bump-colfax-food-beverage",
    ),
    row(
        "Corazon Gallery",
        "Nonprofit gallery / local artist venue",
        "Trinidad",
        "Las Animas",
        "CO",
        website="https://www.corazongallery.org/",
        source_url=TRINIDAD_COMMUNITY,
        source_type="Creative district directory",
        phone="719-846-0207",
        address="149 E. Main St. Suite 1, Trinidad, CO 81082",
    ),
    row(
        "The Commons @ Space to Create",
        "Exhibition space / rentable arts venue",
        "Trinidad",
        "Las Animas",
        "CO",
        website="https://www.trinidadcreativedistrict.org/the-commons",
        source_url=TRINIDAD_COMMUNITY,
        source_type="Creative district directory",
        address="218 W. Main St., Trinidad, CO",
        resource_type="Venue / Creative Space",
    ),
    row(
        "East Street School",
        "Creative community / gallery / class space",
        "Trinidad",
        "Las Animas",
        "CO",
        website="https://www.eaststreetschool.com/programs",
        source_url=TRINIDAD_COMMUNITY,
        source_type="Creative district directory",
        address="210 East Street, Trinidad, CO",
        resource_type="Creative education / venue",
    ),
    row(
        "Doug and Lori Holdread's Art Gallery",
        "Artist gallery",
        "Trinidad",
        "Las Animas",
        "CO",
        website="https://dougandlori.art/",
        source_url=TRINIDAD_COMMUNITY,
        source_type="Creative district directory",
        phone="719-680-7095",
        address="149 E. Main St., Trinidad, CO",
    ),
    row(
        "A.R. Mitchell Museum of Western Art",
        "Museum / gallery",
        "Trinidad",
        "Las Animas",
        "CO",
        website="https://www.armitchellmuseum.com",
        source_url=TRINIDAD_COMMUNITY,
        source_type="Creative district directory",
        address="150 E. Main St., Trinidad, CO",
        resource_type="Museum / Creative",
        row_id="a-r-mitchell-museum-of-western-art-las-animas-museum-arts",
    ),
    row(
        "Marketplace Gallery",
        "Multi-artist gallery",
        "Trinidad",
        "Las Animas",
        "CO",
        website="https://www.marketplacegallery.net",
        source_url=TRINIDAD_COMMUNITY,
        source_type="Creative district directory",
        address="149 E. Main St. #8, Trinidad, CO",
    ),
    row(
        "Tabula Rasa Gallery and Art Supply",
        "Printmaking studio / gallery / art supply",
        "Trinidad",
        "Las Animas",
        "CO",
        website="https://www.tabularasa.gallery",
        source_url=TRINIDAD_COMMUNITY,
        source_type="Creative district directory",
        address="1300 E. Main St., Trinidad, CO",
        resource_type="Creative retail / Artist supply",
    ),
    row(
        "Pack Mule Mercantile",
        "Handmade goods / vintage / art retail",
        "Trinidad",
        "Las Animas",
        "CO",
        website="https://www.facebook.com",
        source_url=TRINIDAD_COMMUNITY,
        source_type="Creative district directory",
        address="130 E. Main St., Trinidad, CO",
        resource_type="Maker retail / Creative business",
    ),
    row(
        "221B Gallery",
        "Experimental / multi-disciplinary gallery",
        "Trinidad",
        "Las Animas",
        "CO",
        website="https://pug-okra-fbcs.squarespace.com",
        source_url=TRINIDAD_COMMUNITY,
        source_type="Creative district directory",
        address="221 Nona Ave, Trinidad, CO 81082",
    ),
    row(
        "Lucky Blue Tattoo",
        "Tattoo / tooth gem studio",
        "Trinidad",
        "Las Animas",
        "CO",
        website="https://www.luckybluetattootrinidad.com/",
        source_url="https://www.luckybluetattootrinidad.com/",
        source_type="Business website",
        phone="(719) 497-9092",
        address="443 North Commercial Street Suite B, Trinidad, CO 81082",
        resource_type="Tattoo / Body art",
        audience="Artist; For-Profit; Program; Visitors / tourists",
    ),
    row(
        "Brick City Tattoo",
        "Tattoo studio",
        "Trinidad",
        "Las Animas",
        "CO",
        website="https://www.facebook.com/Brickcitytattooparlor/",
        source_url=TRINIDAD_SHOP,
        source_type="Tourism business directory",
        phone="719-846-3129",
        address="500 W. Main St., Trinidad, CO 81082",
        resource_type="Tattoo / Body art",
        audience="Artist; For-Profit; Program; Visitors / tourists",
    ),
    row(
        "Brick Road Bakery",
        "Bakery",
        "Trinidad",
        "Las Animas",
        "CO",
        website="",
        source_url=TRINIDAD_SHOP,
        source_type="Tourism business directory",
        phone="719-680-3701",
        address="132 N. Commercial St. Ste. A, Trinidad, CO 81082",
        resource_type="Food / Creative Business",
        audience="For-Profit; Program; Visitors / tourists; Arts / culture audiences",
        row_id="brick-road-bakery-las-animas-bakery-cafe",
    ),
    row(
        "Curly's Beads and Gift Shop",
        "Beads / gift shop / creative retail",
        "Trinidad",
        "Las Animas",
        "CO",
        website="",
        source_url=TRINIDAD_SHOP,
        source_type="Tourism business directory",
        phone="719-846-8647",
        address="131 N. Commercial St., Trinidad, CO 81082",
        resource_type="Creative retail / Maker supply",
    ),
    row(
        "Frank Images",
        "Photography / image business",
        "Trinidad",
        "Las Animas",
        "CO",
        website="",
        source_url=TRINIDAD_SHOP,
        source_type="Tourism business directory",
        phone="719-846-3685",
        address="234 N. Commercial St., Trinidad, CO 81082",
        resource_type="Photography / Creative",
    ),
    row(
        "Mt. Carmel Wellness & Community Center",
        "Community classes / wellness / creative programs",
        "Trinidad",
        "Las Animas",
        "CO",
        website="https://www.mtcarmelcenter.org/wellness-programs",
        source_url=TRINIDAD_COMMUNITY,
        source_type="Creative district community directory",
        address="911 Robinson Avenue, Trinidad, CO",
        resource_type="Creative education / community programs",
    ),
    row(
        "Heritage School at Trinidad State",
        "Creative classes / heritage skills",
        "Trinidad",
        "Las Animas",
        "CO",
        website="https://www.facebook.com/southernrockiesheritageschool",
        source_url=TRINIDAD_COMMUNITY,
        source_type="Creative district community directory",
        resource_type="Creative education / community programs",
    ),
    row(
        "Trinidad State Collaboratory",
        "Community maker space / small business incubator",
        "Trinidad",
        "Las Animas",
        "CO",
        website="https://trinidadstate.edu/collaboratory/index.html",
        source_url=TRINIDAD_COMMUNITY,
        source_type="Creative district community directory",
        address="Trinidad Campus, Berg Building, Trinidad, CO",
        resource_type="Maker space / Creative business support",
    ),
    row(
        "Main Street LIVE",
        "Performing arts venue",
        "Trinidad",
        "Las Animas",
        "CO",
        website="https://www.mainstreetlive.org/",
        source_url=TRINIDAD_COMMUNITY,
        source_type="Creative district community directory",
        phone="719-846-4765",
        address="131 W. Main St., Trinidad, CO",
        resource_type="Venue / Performing Arts",
        row_id="main-street-live-las-animas-performance-venue",
    ),
    row(
        "Trinidad Lounge",
        "Live music venue",
        "Trinidad",
        "Las Animas",
        "CO",
        website="https://dadlounge.com/",
        source_url=TRINIDAD_COMMUNITY,
        source_type="Creative district community directory",
        address="421 N. Commercial St., Trinidad, CO",
        resource_type="Venue / Live Music",
    ),
    row(
        "The Well Hotel & Taproom",
        "Live music venue / hotel taproom",
        "Trinidad",
        "Las Animas",
        "CO",
        website="https://wellhoteltrinidad.com/events/",
        source_url=TRINIDAD_COMMUNITY,
        source_type="Creative district community directory",
        phone="719-422-8030",
        address="155 E. Main Street, Trinidad, CO",
        resource_type="Venue / Live Music",
        row_id="the-well-hotel-taproom-las-animas-boutique-hotel-taproom",
    ),
    row(
        "The Royal Tavern",
        "Live music / karaoke venue",
        "Trinidad",
        "Las Animas",
        "CO",
        website="https://theroyaltavern.simdif.com/upcoming_events%C2%A0.html",
        source_url=TRINIDAD_COMMUNITY,
        source_type="Creative district community directory",
        address="1906 N. Linden Ave, Trinidad, CO",
        resource_type="Venue / Live Music",
    ),
    row(
        "Trinidad Colorado Music Scene",
        "Live music community page",
        "Trinidad",
        "Las Animas",
        "CO",
        website="https://www.facebook.com/trinidadcoloradomusicscene/",
        source_url=TRINIDAD_COMMUNITY,
        source_type="Creative district community directory",
        resource_type="Creative community / Music",
        access_mode="Online",
    ),
    row(
        "La Veta Creative District creative spaces",
        "Creative spaces directory",
        "La Veta",
        "Huerfano",
        "CO",
        website=LA_VETA_CREATIVE_SPACES,
        source_url=LA_VETA_CREATIVE_SPACES,
        source_type="Creative district directory",
        resource_type="Creative directory",
        notes="Use this directory page as the maintained source for La Veta creative spaces; confirm each listed venue before outreach.",
    ),
    row(
        "La Veta Mercantile",
        "Gallery / venue / creative retail",
        "La Veta",
        "Huerfano",
        "CO",
        website="https://www.facebook.com/lavetamercantile",
        source_url=SPANISH_PEAKS_GALLERIES,
        source_type="Tourism business directory",
        phone="719-742-3387",
        address="300 S. Main St., La Veta, CO",
        row_id="la-veta-mercantile-huerfano-retail",
    ),
    row(
        "Walsenburg Studio",
        "Art studio / gallery",
        "Walsenburg",
        "Huerfano",
        "CO",
        website="https://www.walsenburgstudio.com/",
        source_url=SPANISH_PEAKS_GALLERIES,
        source_type="Tourism business directory",
        address="728 Main St., Walsenburg, CO",
    ),
    row(
        "Museum of Friends",
        "Contemporary art museum / gallery",
        "Walsenburg",
        "Huerfano",
        "CO",
        website="https://www.museumoffriends.org/",
        source_url=SPANISH_PEAKS_GALLERIES,
        source_type="Tourism business directory",
        address="600 Main St., Walsenburg, CO 81089",
        resource_type="Museum / Creative",
    ),
    row(
        "Kathy Hills Studio Gallery / Spanish Peaks Art",
        "Painter / studio gallery",
        "La Veta",
        "Huerfano",
        "CO",
        website="https://kathywhill.com/",
        source_url=SPANISH_PEAKS_GALLERIES,
        source_type="Tourism and creative district directory",
        address="133 East Virginia Street, La Veta, CO",
    ),
    row(
        "Artisans on Main",
        "Local-regional artist gallery / maker retail",
        "La Veta",
        "Huerfano",
        "CO",
        website="https://www.artisansonmain.art/",
        source_url=SPANISH_PEAKS_GALLERIES,
        source_type="Tourism and creative district directory",
        address="210 South Main Street, La Veta, CO",
        row_id="artisans-on-main-llc-huerfano-retail-arts",
    ),
    row(
        "Spanish Peaks Arts Council / SPACe Gallery",
        "Arts council / gallery / workshops",
        "La Veta",
        "Huerfano",
        "CO",
        website="https://spanishpeaksarts.org/",
        source_url=SPANISH_PEAKS_GALLERIES,
        source_type="Tourism and creative district directory",
        address="132 W. Ryus Ave, La Veta, CO 81055",
        row_id="spanish-peaks-arts-council-space-gallery-huerfano-arts-culture",
        resource_type="Creative nonprofit / Gallery",
    ),
    row(
        "Shalawalla Gallery, Gift Shop, & School",
        "Gallery / gift shop / school",
        "La Veta",
        "Huerfano",
        "CO",
        website="https://www.shalawalla.com/",
        source_url=SPANISH_PEAKS_GALLERIES,
        source_type="Tourism and creative district directory",
        address="115 W. Ryus Ave, La Veta, CO 81055",
        row_id="shalawalla-huerfano-retail",
    ),
    row(
        "Judith Baker Montano",
        "Fiber art / creative studio",
        "La Veta",
        "Huerfano",
        "CO",
        website="https://www.judithbakermontano.com",
        source_url=LA_VETA_CREATIVE_SPACES,
        source_type="Creative district directory",
    ),
    row(
        "Crafted in Colorado",
        "Creative retail / local goods",
        "La Veta",
        "Huerfano",
        "CO",
        website="https://www.craftedincolorado.com",
        source_url=LA_VETA_CREATIVE_SPACES,
        source_type="Creative district directory",
        resource_type="Maker retail / Creative business",
        row_id="crafted-in-colorado-huerfano-retail-maker",
    ),
    row(
        "Estelle Center for Creative Arts",
        "Creative arts center",
        "La Veta",
        "Huerfano",
        "CO",
        website="https://estellecreativearts.com",
        source_url=LA_VETA_CREATIVE_SPACES,
        source_type="Creative district directory",
        resource_type="Creative education / venue",
    ),
    row(
        "Francisco Center for the Performing Arts",
        "Performing arts venue",
        "La Veta",
        "Huerfano",
        "CO",
        website="https://www.lavetatheaterweb.org",
        source_url=LA_VETA_CREATIVE_SPACES,
        source_type="Creative district directory",
        resource_type="Venue / Performing Arts",
    ),
    row(
        "La Veta School of the Arts",
        "Creative education",
        "La Veta",
        "Huerfano",
        "CO",
        website="https://thelvsa.org",
        source_url=LA_VETA_CREATIVE_SPACES,
        source_type="Creative district directory",
        resource_type="Creative education / venue",
    ),
    row(
        "Nicole Copel Ceramics",
        "Ceramics / pottery artist",
        "La Veta",
        "Huerfano",
        "CO",
        website="https://www.nicolecopelceramics.com",
        source_url=LA_VETA_CREATIVE_SPACES,
        source_type="Creative district directory",
    ),
    row(
        "Grasshopper Studio / Grasshopper Co.",
        "Stained glass / creative studio",
        "La Veta",
        "Huerfano",
        "CO",
        source_url=LA_VETA_CREATIVE_SPACES,
        source_type="Creative district directory",
    ),
    row(
        "H's Place",
        "Creative space / local business",
        "La Veta",
        "Huerfano",
        "CO",
        website="https://www.facebook.com",
        source_url=LA_VETA_CREATIVE_SPACES,
        source_type="Creative district directory",
        resource_type="Creative / Local Business",
    ),
    row(
        "Huajatolla Heritage Foundation",
        "Heritage / culture organization",
        "La Veta",
        "Huerfano",
        "CO",
        website="https://www.hhfoundation.org",
        source_url=LA_VETA_CREATIVE_SPACES,
        source_type="Creative district directory",
        resource_type="Heritage / Creative",
    ),
    row(
        "Silvershoe",
        "Creative retail / local goods",
        "La Veta",
        "Huerfano",
        "CO",
        website="https://www.facebook.com",
        source_url=LA_VETA_CREATIVE_SPACES,
        source_type="Creative district directory",
        resource_type="Maker retail / Creative business",
        row_id="silvershoe-huerfano-retail",
    ),
    row(
        "Two Mountain Treasures",
        "Creative retail / local goods",
        "La Veta",
        "Huerfano",
        "CO",
        source_url=LA_VETA_CREATIVE_SPACES,
        source_type="Creative district directory",
        resource_type="Maker retail / Creative business",
        row_id="two-mountain-treasures-huerfano-retail",
    ),
    row(
        "Lighthouse Coffee & His Majesty's Bakery",
        "Bakery / coffee",
        "Walsenburg",
        "Huerfano",
        "CO",
        website="",
        source_url=SPANISH_PEAKS_DIRECTORY,
        source_type="Tourism business directory",
        phone="(719) 890-0775",
        address="1000 Main St., Walsenburg, CO 81089",
        resource_type="Food / Creative Business",
        audience="For-Profit; Program; Visitors / tourists; Arts / culture audiences",
    ),
    row(
        "Cuchara Mountain Mercantile",
        "Gift shop / venue / dining",
        "Cuchara",
        "Huerfano",
        "CO",
        website="https://cucharamountainmercantile.com/",
        source_url=SPANISH_PEAKS_DIRECTORY,
        source_type="Tourism business directory",
        address="1120 Panadero Avenue, La Veta, CO",
        resource_type="Maker retail / Creative business",
    ),
    row(
        "Walsenburg Mercantile makers directory",
        "Local makers / artists / entrepreneurs directory",
        "Walsenburg",
        "Huerfano",
        "CO",
        website="https://www.walsenburgmercantile.com/",
        source_url=WALSENBURG_MERCANTILE_VENDORS,
        source_type="Business vendor directory",
        phone="(719) 890-1240",
        email="MercantileWalsenburg@gmail.com",
        address="408 Russell Avenue, Walsenburg, CO 81089",
        resource_type="Maker marketplace / Creative directory",
        notes="Use the vendor page as a maintained local maker directory; confirm individual vendor status before outreach.",
    ),
]


LA_VETA_ARTIST_DIRECTORY_ROWS = [
    ("Shawn Bridges / Shawn K. Bridges Art", "Painting / artist", ""),
    ("Lyle Clift", "Sculpture / independent artist", ""),
    ("Sandy Dolak", "Fiber Arts / independent artist", ""),
    ("Cathy Fowler", "Sculpture / independent artist", ""),
    ("Bob Hoffman / Artisans on Main", "Woodworking / artist", ""),
    ("Jennifer Peterson / Estelle Center for Creative Arts", "Fiber Arts / artist", ""),
    ("Anjillee Schwarz / Grasshopper Co.", "Stained glass / artist", ""),
    ("Wayne Stewart Fine Art", "Painting / artist", ""),
    ("Maria Battista", "Sculpture / independent artist", ""),
    ("Nancy Carroll / Artisans on Main", "Photography / artist", ""),
    ("Beth Evans / Shalawalla Studio & Gallery", "Batik / artist", ""),
    ("Cathryn Gladyshev", "Painting / independent artist", ""),
    ("Kate McCabe / Artisans on Main", "Painting / artist", ""),
    ("Steve Riley Limited Editions", "Photography / artist", ""),
    ("Mary Scott / Nevermore Fiber Fabrications", "Fiber Arts / artist", ""),
    ("Gary Alan Weston Studios", "Recycled art / artist", ""),
    ("Lynn Bower Andrews / SPACe Gallery", "Painting / artist", ""),
    ("Jolynn Chappell / Nature Canyon Arts", "Sculpture / artist", ""),
    ("Heather Curtis", "Photography / independent artist", ""),
    ("Jonathan Evans / Shalawalla Studio & Gallery", "Batik / artist", ""),
    ("Marta Moore Art", "Painting / artist", ""),
    ("Kenny Schneider / Kenetics", "Mixed media / artist", ""),
    ("Arthur Short Bull", "Painting / artist", ""),
    ("Peggy Zehring / La Veta School of the Arts", "Painting / art teacher", ""),
]

for artist_name, artist_category, artist_row_id in LA_VETA_ARTIST_DIRECTORY_ROWS:
    ENTRIES.append(
        row(
            artist_name,
            artist_category,
            "La Veta",
            "Huerfano",
            "CO",
            source_url=LA_VETA_ARTISTS,
            source_type="Creative district artist directory",
            resource_type="Creative / Artist",
            access_mode="Online + Local / verify",
            notes=(
                "Individual artist lead listed by the La Veta Creative District artist directory. "
                "Confirm current practice, contact route, representation, and permission before outreach or publication."
            ),
            row_id=artist_row_id or None,
        )
    )


WALSENBURG_MAKERS = [
    ("2K Design", "Design / maker vendor"),
    ("Andreatta Beef", "Local food producer / vendor"),
    ("Bob Bader Custom Wood Products", "Woodworking / maker vendor"),
    ("Centennial Cuts", "Local food / maker vendor"),
    ("Colorado Crunch", "Local food product / maker vendor"),
    ("Customization By Elizabeth", "Custom goods / maker vendor"),
    ("Donovans Creations", "Maker vendor"),
    ("Eves Crafts and Creations", "Crafts / maker vendor"),
    ("Fox Canyon Knives", "Knives / metal craft vendor"),
    ("Ink By Bink", "Visual-art / design vendor"),
    ("Lisa Lynn - Wildlife Artist", "Wildlife artist"),
    ("Mimi's Merch", "Merchandise / maker vendor"),
    ("Mountain View Sanctuary", "Local goods / vendor"),
    ("SOCO Chili", "Local food product / maker vendor"),
    ("Silver Mountain Pottery", "Pottery / ceramics vendor"),
    ("Southern Colorado Crafts", "Crafts / maker vendor"),
    ("Suzy's Salsa", "Local food product / maker vendor"),
    ("3rd Times A Charm", "Maker vendor"),
    ("Artist Vicky De Taos", "Artist vendor"),
    ("Boonelicious LLC", "Food / local treat vendor"),
    ("Centennial Jewelry", "Jewelry vendor"),
    ("CostaCustoms", "Custom goods / maker vendor"),
    ("DeWitt Enterprises", "Local maker / vendor"),
    ("Dreaming Frog", "Maker vendor"),
    ("Fancy", "Local maker / vendor"),
    ("Heart Song", "Local maker / vendor"),
    ("JC CREATIONS", "Creative goods vendor"),
    ("Mallory's Treehouse", "Local maker / vendor"),
    ("Moon Mountain Studio", "Studio / maker vendor"),
    ("Nickell Designs", "Design / maker vendor"),
    ("Scotty B's Custom T's", "Custom apparel / maker vendor"),
    ("Simply Gray Boutique", "Boutique / creative retail vendor"),
    ("Stardust Farm & Flowers", "Flowers / local goods vendor"),
    ("Too Cool Chicks", "Local maker / vendor"),
    ("719 Tines", "Local maker / vendor"),
    ("Between the Knotted Lines", "Fiber / textile vendor"),
    ("Borrowed Blooms", "Floral / local goods vendor"),
    ("Chae Organics", "Body care / local goods vendor"),
    ("Cowgirl Style", "Local goods / maker vendor"),
    ("Desert Salt Rainbow Woman", "Local maker / vendor"),
    ("E-Z P-Z Woodworking Art", "Woodworking / art vendor"),
    ("Flamingo Book Club", "Book / literary vendor"),
    ("Hearts & Crafts", "Crafts / maker vendor"),
    ("JV Jungle Cuts", "Local maker / vendor"),
    ("Mike Snoddy", "Local maker / vendor"),
    ("Mountain Bubbles", "Body care / local goods vendor"),
    ("Odie Art", "Artist vendor"),
    ("Scrap Happy", "Recycled craft / maker vendor"),
    ("Simply Stitchz", "Fiber / textile vendor"),
    ("Studio Katie", "Studio / artist vendor"),
    ("Two Hare Trading", "Local goods / maker vendor"),
    ("Amber Schalla Silver", "Silver / jewelry vendor"),
    ("Blue Hemp Honey", "Local food product / maker vendor"),
    ("Botanical Creations", "Botanical goods / maker vendor"),
    ("Chollafire", "Local maker / vendor"),
    ("Craftsman Cottage Artisans", "Artisans / maker vendor"),
    ("Designs By Dustbunny", "Design / maker vendor"),
    ("Ecozoica Apothecary", "Apothecary / local goods vendor"),
    ("Flyda", "Local maker / vendor"),
    ("Huerfano County Historical Society", "Heritage / local history vendor"),
    ("Kissed By Katie", "Local maker / vendor"),
    ("Mimi's Creations", "Creative goods vendor"),
    ("Mountain Escapes", "Local goods / vendor"),
    ("Redhyl Welding", "Welding / metal craft vendor"),
    ("Second Chance", "Local goods / vendor"),
    ("Sofia Sugar Shack", "Sweets / local treat vendor"),
    ("Sunrise Mesa Design", "Design / maker vendor"),
    ("Vanishing Horizons", "Creative goods vendor"),
]

for maker_name, maker_category in WALSENBURG_MAKERS:
    ENTRIES.append(
        row(
            maker_name,
            maker_category,
            "Walsenburg",
            "Huerfano",
            "CO",
            source_url=WALSENBURG_MERCANTILE_VENDORS,
            website="",
            source_type="Business vendor directory",
            address="408 Russell Avenue, Walsenburg, CO 81089",
            resource_type="Maker / Artist Vendor",
            access_mode="Physical",
            cost_level="Unknown / verify",
            notes=(
                "Individual maker/vendor lead listed by Walsenburg Mercantile. Confirm current vendor status, products, contact route, and permission before direct outreach or publication."
            ),
        )
    )


def read_rows() -> list[dict[str, str]]:
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(rows: list[dict[str, str]]) -> None:
    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for item in rows:
            writer.writerow({field: item.get(field, "") for field in FIELDNAMES})
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    raw_rows = read_rows()
    before_count = len(raw_rows)
    rows = [row for row in raw_rows if row.get("id") not in DROP_DUPLICATE_IDS]
    dropped_duplicate_count = before_count - len(rows)
    index = {item["id"]: item for item in rows}
    added = []
    updated = []
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
    review = f"""# Creative Directory Expansion - {TODAY}

## Summary

- Rows before: {before_count}
- Rows after: {len(rows)}
- New rows added: {len(added)}
- Existing rows updated: {len(updated)}
- Duplicate rows folded into existing stable IDs: {dropped_duplicate_count}
- Total creative entries processed in this pass: {len(ENTRIES)}

## County Mix

{chr(10).join(f"- {county}: {count}" for county, count in by_county.most_common())}

## Resource-Type Mix

{chr(10).join(f"- {rtype}: {count}" for rtype, count in by_type.most_common())}

## Method

Searched current public/local source pages for artist, gallery, maker, tattoo, bakery, creative retail, performing arts, creative-space, and artisan leads across Raton, Angel Fire, Eagle Nest, Trinidad, La Veta, Walsenburg, Cuchara, and surrounding tri-county corridors. Smaller municipalities were included in the search intent, but rows were only added where a public source provided a usable lead.

All new individual entries are source-linked leads or local-check leads. They should be confirmed before direct outreach, publication as active businesses, or any claim about rates, eligibility, event acceptance, or availability.

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
                "dropped_duplicates": dropped_duplicate_count,
                "processed": len(ENTRIES),
                "review": str(REVIEW_PATH),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
