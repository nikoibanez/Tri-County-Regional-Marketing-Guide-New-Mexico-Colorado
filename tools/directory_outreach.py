from __future__ import annotations

import re
from urllib.parse import urlparse


CHANNEL_DEFINITIONS = (
    {
        "key": "physical_flyers",
        "label": "Flyers and posters",
        "group": "Physical",
        "listed_label": "Flyer/poster route",
        "ask_label": "Flyer/poster contact",
    },
    {
        "key": "physical_brochures",
        "label": "Brochures and rack cards",
        "group": "Physical",
        "listed_label": "Brochure/rack-card route",
        "ask_label": "Brochure/rack-card contact",
    },
    {
        "key": "physical_bulletin_board",
        "label": "Bulletin boards",
        "group": "Physical",
        "listed_label": "Bulletin-board route",
        "ask_label": "Bulletin-board contact",
    },
    {
        "key": "front_desk_referrals",
        "label": "Front-desk referrals",
        "group": "Physical",
        "listed_label": "Front-desk referral route",
        "ask_label": "Front-desk referral contact",
    },
    {
        "key": "directory_listing",
        "label": "Directory profiles and listings",
        "group": "Digital",
        "listed_label": "Existing directory profile",
        "ask_label": "Directory listing contact",
    },
    {
        "key": "event_calendar",
        "label": "Event calendars",
        "group": "Digital",
        "listed_label": "Event/calendar route",
        "ask_label": "Event calendar contact",
    },
    {
        "key": "social_cross_promotion",
        "label": "Social cross-promotion",
        "group": "Digital",
        "listed_label": "Social-sharing route",
        "ask_label": "Social-sharing contact",
    },
    {
        "key": "newsletter_mailing_list",
        "label": "Newsletters and mailing lists",
        "group": "Digital",
        "listed_label": "Newsletter/mailing-list route",
        "ask_label": "Newsletter contact",
    },
    {
        "key": "paid_digital_advertising",
        "label": "Paid digital advertising",
        "group": "Digital",
        "listed_label": "Advertising inquiry route",
        "ask_label": "Digital advertising contact",
    },
    {
        "key": "media_editorial",
        "label": "Media and editorial coverage",
        "group": "Digital",
        "listed_label": "Media/editorial route",
        "ask_label": "Pitch a story or announcement",
    },
    {
        "key": "sponsorship",
        "label": "Sponsorships",
        "group": "Digital",
        "listed_label": "Sponsorship inquiry route",
        "ask_label": "Sponsorship contact",
    },
    {
        "key": "partner_cross_promotion",
        "label": "Partner cross-promotion",
        "group": "Digital",
        "listed_label": "Partner-sharing route",
        "ask_label": "Cross-promotion contact",
    },
)

CHANNELS_BY_KEY = {item["key"]: item for item in CHANNEL_DEFINITIONS}
STATUS_PRIORITY = {"not_indicated": 0, "ask": 1, "listed": 2}

SOCIAL_HOSTS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "tiktok.com",
    "youtube.com",
    "youtu.be",
}

PARTNER_FRIENDLY_TYPES = {
    "Arts & culture",
    "Business support",
    "Education & learning",
    "Events & venues",
    "Food & drink",
    "Health & wellness",
    "Local business or service",
    "Lodging & stays",
    "Media & news",
    "Nonprofit & community",
    "Outdoor recreation",
    "Retail & local goods",
    "Tourism & visitor info",
}

CALENDAR_FRIENDLY_TYPES = {
    "Arts & culture",
    "Business support",
    "Events & venues",
    "Media & news",
    "Nonprofit & community",
    "Public offices",
    "Tourism & visitor info",
}

NEWSLETTER_FRIENDLY_TYPES = {
    "Arts & culture",
    "Business support",
    "Education & learning",
    "Funding & support",
    "Media & news",
    "Nonprofit & community",
    "Public offices",
    "Tourism & visitor info",
}


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def split_values(value: object) -> list[str]:
    if isinstance(value, list):
        return [clean(item) for item in value if clean(item)]
    return [part.strip() for part in str(value or "").split(";") if part.strip()]


def url_host(value: object) -> str:
    try:
        return urlparse(clean(value)).netloc.casefold().removeprefix("www.")
    except ValueError:
        return ""


def host_matches(host: str, domains: set[str]) -> bool:
    return any(host == domain or host.endswith("." + domain) for domain in domains)


def contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def source_specific_note(value: object) -> str:
    """Exclude guide-generated and commercial-sweep guidance from route claims."""

    note = clean(value).casefold()
    generated_markers = (
        "search here for",
        "it is useful for",
        "it is relevant for",
        "can help users find",
        "visitor-facing listing pulled",
        "commercial-directory-only lead",
        "treat as unverified",
        "verify current details",
        "recommended outreach",
        "starting contact",
        "before assuming",
        "use it to ask about",
        "use it when planning",
        "do not assume",
        "ask office/admin",
        "use only for direct partnership",
        "may share mission-aligned",
    )
    if any(marker in note for marker in generated_markers):
        return ""
    return note


def classify_outreach_channels(
    row: dict,
    *,
    has_physical_location: bool = False,
    physical_ad_candidate: bool = False,
) -> list[dict]:
    """Return actionable outreach routes without asserting unverified acceptance."""

    name = clean(row.get("resource_name") or row.get("title") or row.get("channel")).casefold()
    listing_type = clean(row.get("public_listing_type") or row.get("resource_type"))
    identity_text = " ".join(
        clean(row.get(field)).casefold()
        for field in ("resource_name", "category", "resource_type", "source_type")
    )
    explicit_text = " ".join(
        part
        for part in (
            source_specific_note(row.get("notes")),
            source_specific_note(row.get("public_description")),
            clean(row.get("source_type")).casefold(),
            clean(row.get("category")).casefold(),
            clean(row.get("resource_type")).casefold(),
        )
        if part
    )
    recommendation_text = " ".join(
        clean(row.get(field)).casefold()
        for field in (
            "yellowpages_recommended_action",
            "yellowpages_flyer_likelihood",
            "yellowpages_digital_distribution_likelihood",
        )
    )
    urls = []
    for field in ("website", "source_url", "url"):
        for value in split_values(row.get(field)):
            if value not in urls:
                urls.append(value)
    url_text = " ".join(url.casefold() for url in urls)
    hosts = {url_host(url) for url in urls if url_host(url)}
    has_reachable_route = bool(
        urls
        or clean(row.get("contact_email"))
        or clean(row.get("contact_phone"))
        or has_physical_location
    )
    public_facing_signal = contains_any(
        identity_text,
        (
            "visitor center",
            "welcome center",
            "community center",
            "library",
            "museum",
            "gallery",
            "arts center",
            "theater",
            "theatre",
            "venue",
            "hotel",
            "motel",
            "lodge",
            "lodging",
            "restaurant",
            "cafe",
            "coffee",
            "market",
            "store",
            "shop",
            "chamber",
        ),
    )
    visitor_signal = contains_any(
        identity_text,
        (
            "visitor center",
            "welcome center",
            "tourism office",
            "tourism board",
            "destination marketing",
            "chamber",
            "hotel",
            "motel",
            "lodge",
            "lodging",
            "museum",
            "gallery",
            "campground",
            "rv park",
        ),
    )
    community_signal = contains_any(
        identity_text,
        (
            "library",
            "community center",
            "senior center",
            "recreation center",
            "city hall",
            "town hall",
            "county government",
            "public office",
            "college",
            "school",
            "church",
            "nonprofit",
            "foundation",
        ),
    )
    calendar_signal = contains_any(
        identity_text,
        (
            "event",
            "calendar",
            "festival",
            "fair board",
            "venue",
            "theater",
            "theatre",
            "library",
            "community center",
            "visitor center",
            "tourism board",
            "chamber",
            "newspaper",
            "radio",
            "magazine",
        ),
    )
    member_communication_signal = contains_any(
        identity_text,
        (
            "chamber",
            "association",
            "alliance",
            "council",
            "district",
            "foundation",
            "nonprofit",
            "library",
            "visitor center",
            "tourism board",
            "economic development",
            "newspaper",
            "radio",
            "magazine",
        ),
    )
    sponsorship_signal = contains_any(
        identity_text,
        (
            "event",
            "festival",
            "fair board",
            "venue",
            "theater",
            "theatre",
            "newspaper",
            "radio",
            "magazine",
            "visitor center",
            "tourism board",
            "chamber",
        ),
    )
    media_signal = contains_any(
        identity_text,
        ("media", "newspaper", "radio", "magazine", "broadcast", "advertising"),
    )
    partnership_signal = contains_any(
        identity_text,
        (
            "chamber",
            "association",
            "alliance",
            "network",
            "council",
            "district",
            "nonprofit",
            "foundation",
            "economic development",
            "visitor center",
            "tourism board",
            "arts center",
            "gallery",
            "museum",
            "event",
            "venue",
            "media",
            "newspaper",
            "radio",
            "magazine",
        ),
    )
    results: dict[str, dict] = {}

    def add(key: str, status: str, evidence: str) -> None:
        definition = CHANNELS_BY_KEY[key]
        existing = results.get(key)
        if existing and STATUS_PRIORITY[existing["status"]] > STATUS_PRIORITY[status]:
            return
        if existing and STATUS_PRIORITY[existing["status"]] == STATUS_PRIORITY[status]:
            evidence_values = existing.setdefault("evidence", [])
            if evidence and evidence not in evidence_values:
                evidence_values.append(evidence)
            return
        results[key] = {
            "key": key,
            "label": definition["listed_label"] if status == "listed" else definition["ask_label"],
            "channel": definition["label"],
            "group": definition["group"],
            "status": status,
            "status_label": "Listed route" if status == "listed" else "Contact opportunity",
            "note": (
                "The listing information identifies this route. Confirm current eligibility, pricing, deadlines, and acceptance rules."
                if status == "listed"
                else "This may be a useful outreach contact, but the guide does not imply that placement or sharing is available."
            ),
            "evidence": [evidence] if evidence else [],
        }

    # A location can be a useful place to ask, but an address never proves posting permission.
    if physical_ad_candidate:
        add("physical_flyers", "ask", "Physical location and listing type suggest an owner-approved flyer inquiry may fit.")
    if has_physical_location and (
        public_facing_signal or listing_type in {"Food & drink", "Lodging & stays", "Retail & local goods"}
    ):
        add("front_desk_referrals", "ask", "A public-facing physical location may support direct referral or counter-card outreach.")
    if has_physical_location and visitor_signal:
        add("physical_brochures", "ask", "Visitor-facing locations may have owner-controlled brochure or rack-card space.")
    if has_physical_location and community_signal:
        add("physical_bulletin_board", "ask", "Community-serving locations may have a staff-controlled bulletin board.")

    if matches_any(
        explicit_text,
        (
            r"\baccepts?\b.{0,40}\b(?:flyers?|posters?)\b",
            r"\b(?:flyers?|posters?)\b.{0,40}\b(?:accepted|permitted|welcome)\b",
            r"\b(?:display|post)\b.{0,24}\b(?:flyers?|posters?)\b",
        ),
    ):
        add("physical_flyers", "listed", "Listing text names flyer or poster placement.")
    if matches_any(
        explicit_text,
        (
            r"\b(?:accepts?|displays?|stocks?)\b.{0,40}\b(?:brochures?|rack cards?)\b",
            r"\b(?:brochures?|rack cards?)\b.{0,40}\b(?:accepted|available|displayed|welcome)\b",
        ),
    ):
        add("physical_brochures", "listed", "Listing text names brochures or rack cards.")
    if matches_any(
        explicit_text,
        (
            r"\b(?:has|maintains|offers|provides)\b.{0,40}\b(?:bulletin|community) board\b",
            r"\b(?:bulletin|community) board\b.{0,40}\b(?:available|open|accepts)\b",
        ),
    ):
        add("physical_bulletin_board", "listed", "Listing text names a bulletin or community board.")
    elif has_physical_location and contains_any(recommendation_text, ("bulletin board", "community board")):
        add("physical_bulletin_board", "ask", "Existing outreach notes suggest asking staff about a community board.")

    directory_signal = contains_any(
        explicit_text + " " + url_text,
        (
            "business directory",
            "member directory",
            "nonprofit directory",
            "artist directory",
            "visitor listing",
            "directory listing",
            "add listing",
            "add business",
            "get listed",
            "business profile",
            "/business-directory/listing/",
            "/membership-directory/",
            "/listing/",
        ),
    ) or any(re.search(r"/(?:business|member)/[^/?#]+/?$", url.casefold()) for url in urls)
    if directory_signal:
        add("directory_listing", "listed", "A linked page or listing field identifies a directory/profile route.")
    elif contains_any(identity_text, ("chamber", "tourism board", "visitor center", "business alliance", "economic development")):
        add("directory_listing", "ask", "Business-support and visitor organizations may maintain listings or referral lists.")

    calendar_listed = contains_any(
        explicit_text + " " + url_text,
        (
            "submit event",
            "submit your event",
            "list your event",
            "event submission",
            "community calendar",
            "event calendar",
            "events calendar",
            "calendar submission",
            "/submit-event",
            "/submit-an-event",
            "/events/submit",
        ),
    )
    if calendar_listed:
        add("event_calendar", "listed", "A linked page or listing field identifies an event-calendar route.")
    elif calendar_signal and has_reachable_route:
        add("event_calendar", "ask", "The organization publishes events or serves audiences that may use a calendar.")

    has_social_profile = any(host_matches(host, SOCIAL_HOSTS) for host in hosts)
    social_listed = contains_any(
        explicit_text,
        (
            "social media co-op",
            "social media cross-promotion",
            "partner repost",
            "accepts social media submissions",
            "shares partner posts",
        ),
    )
    if social_listed:
        add("social_cross_promotion", "listed", "Listing text identifies coordinated social sharing or cross-promotion.")
    elif has_social_profile or (
        contains_any(recommendation_text, ("digital distribution: medium", "digital distribution: high")) and urls
    ):
        add("social_cross_promotion", "ask", "A public social profile provides a direct place to ask about sharing.")

    newsletter_listed = contains_any(
        explicit_text + " " + url_text,
        ("newsletter signup", "newsletter sign-up", "email newsletter", "mailing list", "/newsletter", "/subscribe"),
    )
    if newsletter_listed:
        add("newsletter_mailing_list", "listed", "A linked page or listing field identifies a newsletter or mailing-list route.")
    elif contains_any(recommendation_text, ("newsletter", "mailing list")) or (
        member_communication_signal and has_reachable_route
    ):
        add("newsletter_mailing_list", "ask", "This organization may communicate with members, residents, supporters, or visitors by email.")

    advertising_listed = contains_any(
        explicit_text + " " + url_text,
        (
            "advertising inquiry",
            "advertising rates",
            "advertise with",
            "digital advertising",
            "paid advertising",
            "media kit",
            "rate sheet",
            "radio advertising",
            "print advertising",
            "/advertising",
            "/advertise",
        ),
    )
    if advertising_listed:
        add("paid_digital_advertising", "listed", "A linked page or listing field identifies an advertising inquiry route.")
    elif (listing_type == "Media & news" or media_signal) and has_reachable_route:
        add("paid_digital_advertising", "ask", "Media organizations are reasonable contacts for current advertising options and rates.")

    editorial_listed = contains_any(
        explicit_text + " " + url_text,
        (
            "submit news",
            "submit a story",
            "story submission",
            "press release",
            "editorial submission",
            "community announcement",
            "public service announcement",
            "public announcements",
        ),
    )
    if editorial_listed:
        add("media_editorial", "listed", "A linked page or listing field identifies a story, announcement, or editorial route.")
    elif (listing_type == "Media & news" or media_signal) and has_reachable_route:
        add("media_editorial", "ask", "The listing is a media organization that may consider relevant stories or announcements.")

    sponsorship_listed = contains_any(
        explicit_text + " " + url_text,
        ("sponsorship inquiry", "sponsor opportunity", "sponsorship opportunities", "become a sponsor", "underwriting", "/sponsor"),
    )
    if sponsorship_listed:
        add("sponsorship", "listed", "A linked page or listing field identifies a sponsorship or underwriting route.")
    elif contains_any(recommendation_text, ("sponsorship", "underwriting")) or (
        sponsorship_signal and has_reachable_route
    ):
        add("sponsorship", "ask", "Events, media, and visitor organizations may have current sponsorship options.")

    partnership_listed = contains_any(
        explicit_text,
        (
            "offers cross-promotion",
            "cross-promotion program",
            "partner sharing program",
            "marketing co-op",
            "referral partner program",
        ),
    )
    if partnership_listed:
        add("partner_cross_promotion", "listed", "Listing text identifies partner sharing, referrals, or cross-promotion.")
    elif (
        contains_any(recommendation_text, ("partnership", "referral", "cross-promotion", "cross promotion"))
        or partnership_signal
        or has_social_profile
    ) and has_reachable_route:
        add("partner_cross_promotion", "ask", "The listing has a reachable public or physical presence for a tailored partnership inquiry.")

    return [results[key] for key in CHANNELS_BY_KEY if key in results]


def channel_status_map(channels: list[dict]) -> dict[str, str]:
    statuses = {definition["key"]: "not_indicated" for definition in CHANNEL_DEFINITIONS}
    for item in channels:
        key = clean(item.get("key"))
        status = clean(item.get("status"))
        if key in statuses and status in STATUS_PRIORITY:
            statuses[key] = status
    return statuses
