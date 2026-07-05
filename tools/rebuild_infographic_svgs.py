from __future__ import annotations

from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SVG_DIR = ROOT / "assets" / "super_eukarya_vector_package" / "assets"
BRAND_DIR = ROOT / "assets" / "brand"

INK = "#142B44"
INK_SOFT = "#4A5563"
PAPER = "#F7F3EA"
CREAM = "#FFFFFF"
GOLD = "#B9A36A"
LINE = "#DED6C6"
TEAL = "#5BAEAD"
BLUE = "#6F8FC9"
GREEN = "#6CB894"
CLAY = "#D48964"
PLUM = "#695674"
RATON_DARK = "#502020"
RATON_GOLD = "#C9933A"


def text(x: float, y: float, value: str, cls: str, anchor: str = "middle") -> str:
    return f'<text x="{x:g}" y="{y:g}" text-anchor="{anchor}" class="{cls}">{escape(value)}</text>'


def lines(x: float, y: float, values: list[str], cls: str, anchor: str = "middle", step: int = 18) -> str:
    return "\n".join(text(x, y + i * step, value, cls, anchor) for i, value in enumerate(values))


def card(
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    desc: list[str],
    color: str,
    title_size: str = "card-title",
    body_size: str = "card-body",
) -> str:
    total = 22 + 10 + len(desc) * 17
    start = y + (h - total) / 2 + 20
    body_start = start + 30
    return f"""
<g>
  <rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="18" class="card"/>
  <rect x="{x + 18:g}" y="{y + 18:g}" width="34" height="8" rx="4" fill="{color}"/>
  {text(x + w / 2, start, title, title_size)}
  {lines(x + w / 2, body_start, desc, body_size)}
</g>"""


def stage(title: str, subtitle: str, body: str, desc: str, height: int = 720) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}" role="img" aria-labelledby="title desc" shape-rendering="geometricPrecision">
<title id="title">{escape(title)}</title>
<desc id="desc">{escape(desc)}</desc>
<defs>
<style>
  .title {{ font: 800 38px Arial, sans-serif; fill: {INK}; letter-spacing: 0; }}
  .subtitle {{ font: 700 16px Arial, sans-serif; fill: #736646; letter-spacing: 0; }}
  .card-title {{ font: 800 19px Arial, sans-serif; fill: {INK}; letter-spacing: 0; }}
  .card-title-sm {{ font: 800 16px Arial, sans-serif; fill: {INK}; letter-spacing: 0; }}
  .card-body {{ font: 600 14px Arial, sans-serif; fill: {INK_SOFT}; letter-spacing: 0; }}
  .card-body-sm {{ font: 600 13px Arial, sans-serif; fill: {INK_SOFT}; letter-spacing: 0; }}
  .invert-title {{ font: 800 22px Arial, sans-serif; fill: {PAPER}; letter-spacing: 0; }}
  .invert-body {{ font: 600 14px Arial, sans-serif; fill: {PAPER}; opacity: .86; letter-spacing: 0; }}
  .micro {{ font: 700 12px Arial, sans-serif; fill: #736646; letter-spacing: 0; }}
  .card {{ fill: {CREAM}; stroke: {LINE}; stroke-width: 2; vector-effect: non-scaling-stroke; }}
  .soft {{ fill: {CREAM}; opacity: .68; stroke: {LINE}; stroke-width: 1.6; vector-effect: non-scaling-stroke; }}
  .line {{ fill: none; stroke: {GOLD}; stroke-width: 4; stroke-linecap: round; stroke-linejoin: round; vector-effect: non-scaling-stroke; }}
  .line-soft {{ fill: none; stroke: {INK}; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; opacity: .22; vector-effect: non-scaling-stroke; }}
</style>
<marker id="arrow" markerWidth="14" markerHeight="14" refX="10" refY="7" orient="auto">
  <path d="M2 2 L11 7 L2 12 Z" fill="{GOLD}"/>
</marker>
</defs>
<rect width="1200" height="{height}" fill="{PAPER}"/>
<text x="72" y="80" class="title">{escape(title)}</text>
<text x="74" y="116" class="subtitle">{escape(subtitle)}</text>
<line x1="72" y1="148" x2="1128" y2="148" stroke="{GOLD}" stroke-width="3" stroke-linecap="round"/>
{body}
</svg>
"""


def system_map() -> str:
    body = f"""
<path d="M600 348 L600 226 M600 348 L854 286 M600 348 L854 494 M600 348 L600 596 M600 348 L346 494 M600 348 L346 286" class="line-soft"/>
<circle cx="600" cy="348" r="78" fill="{INK}"/>
{text(600, 338, "Regional core", "invert-title")}
{lines(600, 366, ["Shared sources", "and follow-up"], "invert-body")}
{card(486, 180, 228, 100, "Start with need", ["Name the audience", "before the channel."], GREEN)}
{card(742, 240, 228, 100, "Find source", ["Use directories, maps,", "calendars, and offices."], TEAL)}
{card(742, 448, 228, 100, "Choose channel", ["Match public, media,", "partner, or social routes."], BLUE)}
{card(486, 572, 228, 100, "Track response", ["Record who answered", "and what changed."], GOLD)}
{card(230, 448, 228, 100, "Update packet", ["Improve the blurb,", "image, link, or ask."], CLAY)}
{card(230, 240, 228, 100, "Build trust", ["Confirm details before", "posting or spending."], PLUM)}
<path d="M208 652 C380 610 820 610 992 652" class="line"/>
{text(600, 684, "Use this map to move from a local idea to a repeatable outreach path.", "micro")}
"""
    return stage(
        "Regional Outreach System",
        "Use this to connect needs, sources, channels, and follow-up.",
        body,
        "A regional outreach system map with centered boxes for need, source, channel, tracking, packet updates, and trust.",
    )


def growth_cycle() -> str:
    body = f"""
<path d="M600 212 C822 212 990 330 990 398 C990 466 822 584 600 584 C378 584 210 466 210 398 C210 330 378 212 600 212" class="line" marker-end="url(#arrow)" opacity=".48"/>
{card(486, 176, 228, 100, "Define goal", ["Pick customers, partners,", "funding, trust, or visits."], GREEN)}
{card(762, 252, 228, 100, "Name audience", ["Decide who needs to", "notice or respond."], BLUE)}
{card(762, 448, 228, 100, "Check sources", ["Start with existing", "directories and calendars."], TEAL)}
{card(486, 572, 228, 100, "Build packet", ["Prepare one reusable", "blurb, image, and ask."], GOLD)}
{card(210, 448, 228, 100, "Send through", ["Submit to matched", "media and partner routes."], CLAY)}
{card(210, 252, 228, 100, "Track reply", ["Log where it went", "and what came back."], PLUM)}
<rect x="462" y="338" width="276" height="112" rx="22" fill="{INK}"/>
{text(600, 384, "Refine and repeat", "invert-title")}
{lines(600, 414, ["The response changes", "the next cycle."], "invert-body")}
"""
    return stage(
        "Growth Cycle",
        "Use this to turn promotion from a one-time task into a repeatable loop.",
        body,
        "A six-step growth cycle with centered boxes and descriptions for goals, audience, sources, packets, channels, and replies.",
    )


def need_matrix() -> str:
    items = [
        (72, 184, "New business", ["Claim core listings;", "ask one support office."], GREEN),
        (428, 184, "Existing business", ["Update stale profiles;", "reach nearby counties."], BLUE),
        (784, 184, "Nonprofit program", ["Lead with benefit;", "show referral path."], TEAL),
        (72, 396, "Artist or gallery", ["Connect work to place,", "date, and visitor path."], CLAY),
        (428, 396, "Event organizer", ["Make one clean packet;", "submit to calendars."], GOLD),
        (784, 396, "Rural service", ["Make referrals easy;", "state area and next step."], PLUM),
    ]
    body = "\n".join(card(x, y, 344, 156, title, desc + ["Open the matched page."], color) for x, y, title, desc, color in items)
    body += f"""
<rect x="238" y="644" width="724" height="34" rx="17" class="soft"/>
{text(600, 666, "Each box tells the reader what to do first, then where to go next.", "micro")}
"""
    return stage(
        "Use by Need",
        "Use this to choose the right section without reading the guide in order.",
        body,
        "A use-by-need matrix with centered cards for new businesses, existing businesses, nonprofits, artists, events, and rural services.",
    )


def visibility_stack() -> str:
    rows = [
        ("1", "Website or listing", "Stable facts people can verify later.", GREEN),
        ("2", "Google or maps", "Hours, photos, phone, and directions.", BLUE),
        ("3", "Social post", "Short update people can share quickly.", TEAL),
        ("4", "Calendar or event", "Date, place, registration, and cost.", GOLD),
        ("5", "Flyer or handout", "Readable offline copy for boards.", CLAY),
        ("6", "Partner referral", "Plain language others can reuse.", PLUM),
    ]
    parts = []
    y = 182
    for number, title, desc, color in rows:
        parts.append(f"""
<g>
  <rect x="166" y="{y}" width="868" height="66" rx="14" class="card"/>
  <circle cx="205" cy="{y + 33}" r="18" fill="{color}"/>
  {text(205, y + 39, number, "invert-body")}
  {text(408, y + 31, title, "card-title", "start")}
  {text(408, y + 53, desc, "card-body", "start")}
</g>""")
        y += 78
    parts.append(f'<path d="M141 230 L141 620" class="line" marker-end="url(#arrow)"/>')
    return stage(
        "Visibility Stack",
        "Use this to build one promotion packet that can travel through many channels.",
        "\n".join(parts),
        "A visibility stack with six horizontal cards, each containing a title and short description.",
    )


def cross_promotion() -> str:
    items = [
        (486, 178, "Identify partner", ["Find a nearby business,", "venue, program, or office."], GREEN),
        (762, 286, "Share asset", ["Send one blurb, image,", "date, link, and ask."], BLUE),
        (762, 500, "Publish or tag", ["Make the exchange", "visible and easy to share."], TEAL),
        (486, 584, "Thank and recap", ["Report the result and", "credit the partner."], GOLD),
        (210, 500, "Log outcome", ["Track visits, replies,", "sales, or signups."], CLAY),
        (210, 286, "Repeat better", ["Use what worked in", "the next small cycle."], PLUM),
    ]
    body = '<path d="M600 262 C770 262 900 350 900 430 C900 510 770 598 600 598 C430 598 300 510 300 430 C300 350 430 262 600 262" class="line" marker-end="url(#arrow)" opacity=".55"/>'
    body += "\n".join(card(x, y, 228, 98, title, desc, color, "card-title-sm", "card-body-sm") for x, y, title, desc, color in items)
    body += f"""
<rect x="472" y="372" width="256" height="92" rx="20" fill="{INK}"/>
{text(600, 408, "Follow-up log", "invert-title")}
{lines(600, 436, ["Keep the relationship", "visible and useful."], "invert-body")}
"""
    return stage(
        "Cross-Promotion Loop",
        "Use this to make collaboration a repeatable exchange, not a one-off favor.",
        body,
        "A cross-promotion loop with six centered steps and a central follow-up log.",
    )


def persona_finder() -> str:
    body = f"""
<path d="M244 384 H956" class="line" marker-end="url(#arrow)" opacity=".55"/>
{card(92, 272, 228, 160, "Who are you?", ["Business, artist,", "nonprofit, mentor,", "or event organizer."], GREEN)}
{card(356, 272, 228, 160, "What is needed?", ["Visibility, partners,", "funding, posting,", "or directory help."], BLUE)}
{card(620, 272, 228, 160, "Where first?", ["Choose county,", "community, or", "cross-county route."], TEAL)}
{card(884, 272, 228, 160, "What is trusted?", ["Prioritize official,", "linked, or field-check", "sources."], GOLD)}
<rect x="256" y="526" width="688" height="54" rx="27" class="soft"/>
{text(600, 560, "Use filters to turn a large lead bank into a short, relevant action list.", "micro")}
"""
    return stage(
        "Persona Finder",
        "Use this to filter the guide by the person doing the work.",
        body,
        "A persona finder flow with four centered cards for role, need, place, and source confidence.",
    )


def bulletin_network() -> str:
    items = [
        (72, 196, "Official notice", ["City or county page", "for civic information."], INK),
        (428, 196, "Public board", ["Physical posting route", "that needs permission."], GOLD),
        (784, 196, "Community calendar", ["Event details with date,", "location, and link."], GREEN),
        (72, 430, "Local media", ["Radio or newspaper", "for public reach."], BLUE),
        (428, 430, "Partner share", ["Chamber, library, school,", "district, or nonprofit."], TEAL),
        (784, 430, "Digital post", ["Social or email copy", "for quick sharing."], CLAY),
    ]
    body = "\n".join(card(x, y, 344, 146, title, desc, color) for x, y, title, desc, color in items)
    body += f"""
<path d="M244 370 H956" class="line" marker-end="url(#arrow)" opacity=".5"/>
{text(600, 386, "Verify rules before posting; choose the channel that matches the request.", "micro")}
"""
    return stage(
        "Bulletin and Media Network",
        "Use this to separate civic posting, community promotion, and media outreach.",
        body,
        "A bulletin and media network diagram with six centered cards and descriptions for posting paths.",
    )


def accessibility_contrast() -> str:
    body = f"""
<rect x="88" y="196" width="304" height="170" rx="20" fill="{PAPER}" stroke="{LINE}" stroke-width="2"/>
{text(240, 254, "Dark on cream", "card-title")}
{lines(240, 288, ["Use for body text,", "captions, and lists."], "card-body")}
<rect x="124" y="318" width="232" height="28" rx="14" fill="{RATON_DARK}"/>
{text(240, 338, "High contrast", "invert-body")}

<rect x="448" y="196" width="304" height="170" rx="20" fill="{INK}" stroke="{LINE}" stroke-width="2"/>
{text(600, 254, "Cream on navy", "invert-title")}
{lines(600, 288, ["Use for buttons,", "headers, and footer."], "invert-body")}
<rect x="484" y="318" width="232" height="28" rx="14" fill="{PAPER}"/>
{text(600, 338, "Readable accent", "card-body")}

<rect x="808" y="196" width="304" height="170" rx="20" fill="{RATON_DARK}" stroke="{LINE}" stroke-width="2"/>
{text(960, 254, "Cream on Raton dark", "invert-title")}
{lines(960, 288, ["Use for cursor,", "icons, and badges."], "invert-body")}
<rect x="844" y="318" width="232" height="28" rx="14" fill="{RATON_GOLD}"/>
{text(960, 338, "Accent only", "card-body")}

{card(144, 452, 256, 118, "Keep type large", ["Avoid tiny text over", "busy images."], GREEN)}
{card(472, 452, 256, 118, "Use plain labels", ["Readers scan faster", "with direct wording."], BLUE)}
{card(800, 452, 256, 118, "Check before print", ["Test flyers on paper", "and mobile screens."], GOLD)}
"""
    return stage(
        "Accessible Contrast",
        "Use this to keep flyers, listings, and guide graphics readable.",
        body,
        "An accessibility contrast guide with centered cards for color pairings and legibility practices.",
    )


def route_nodes() -> str:
    body = f"""
<path d="M600 352 L290 252 M600 352 L910 252 M600 352 L290 520 M600 352 L910 520" class="line-soft"/>
<rect x="462" y="290" width="276" height="124" rx="24" fill="{INK}"/>
{text(600, 338, "Stateline core", "invert-title")}
{lines(600, 368, ["Network page plus", "county entry points."], "invert-body")}
{card(112, 188, 300, 138, "Colfax / Raton", ["Start with city, chamber,", "MainStreet, media, and NM tools."], BLUE)}
{card(788, 188, 300, 138, "Las Animas / Trinidad", ["Start with county, city,", "tourism, arts, and media."], GREEN)}
{card(112, 456, 300, 138, "Huerfano / Walsenburg", ["Start with chamber, HCED,", "tourism, arts, and news."], CLAY)}
{card(788, 456, 300, 138, "Cross-county partners", ["Use directories, funders,", "creative and nonprofit hubs."], GOLD)}
"""
    return stage(
        "Tri-County Route Nodes",
        "Use this to choose a local door while keeping cross-county options visible.",
        body,
        "A tri-county route-node diagram with centered county and cross-county resource cards.",
    )


def funding_pipeline() -> str:
    items = [
        (74, "Define need", ["What money or help", "is actually needed?"], GREEN),
        (250, "Gather proof", ["Budget, timeline,", "impact, and records."], BLUE),
        (426, "Check fit", ["Eligibility, geography,", "and deadline."], TEAL),
        (602, "Ask support", ["SBDC, EDD, chamber,", "or fiscal partner."], GOLD),
        (778, "Apply cleanly", ["Use complete forms", "and plain outcomes."], CLAY),
        (954, "Track result", ["Note decision, date,", "and next attempt."], PLUM),
    ]
    body = '<path d="M112 410 H1088" class="line" marker-end="url(#arrow)" opacity=".58"/>'
    body += "\n".join(card(x, 250, 158, 160, title, desc, color, "card-title-sm", "card-body-sm") for x, title, desc, color in items)
    body += f"""
<rect x="238" y="522" width="724" height="52" rx="26" class="soft"/>
{text(600, 555, "Use this only after verifying current eligibility, deadlines, and contact paths.", "micro")}
"""
    return stage(
        "Funding Readiness Pipeline",
        "Use this to prepare before treating any grant or loan as a fit.",
        body,
        "A funding readiness pipeline with six centered cards for need, proof, fit, support, application, and tracking.",
    )


def write_cursor() -> None:
    BRAND_DIR.mkdir(parents=True, exist_ok=True)
    cursor = f"""<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32" role="img" aria-label="Raton color accessible cursor">
<path d="M5 3 L24 17 L16 19 L20 28 L15 30 L11 21 L5 27 Z" fill="{RATON_DARK}" fill-opacity=".78" stroke="{PAPER}" stroke-opacity=".88" stroke-width="1.35" stroke-linejoin="round"/>
<path d="M8 7 L19 16 L14 17 L17 25" fill="none" stroke="{RATON_GOLD}" stroke-opacity=".82" stroke-width="1.05" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""
    (BRAND_DIR / "raton-accessible-cursor.svg").write_text(cursor, encoding="utf-8")


def main() -> None:
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "se_system_map.svg": system_map(),
        "se_growth_cycle.svg": growth_cycle(),
        "se_need_tool_matrix.svg": need_matrix(),
        "se_visibility_stack.svg": visibility_stack(),
        "se_cross_promotion_loop.svg": cross_promotion(),
        "se_persona_finder_diagram.svg": persona_finder(),
        "se_bulletin_media_network.svg": bulletin_network(),
        "se_accessibility_contrast.svg": accessibility_contrast(),
        "se_tri_county_route_nodes.svg": route_nodes(),
        "se_funding_pipeline.svg": funding_pipeline(),
    }
    for name, svg in outputs.items():
        (SVG_DIR / name).write_text(svg, encoding="utf-8")
    write_cursor()
    print(f"rewrote {len(outputs)} infographics and 1 cursor asset")


if __name__ == "__main__":
    main()
