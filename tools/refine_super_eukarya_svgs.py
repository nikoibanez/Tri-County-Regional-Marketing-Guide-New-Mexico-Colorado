from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets" / "super_eukarya_vector_package" / "assets"

NAVY = "#142B44"
CREAM = "#F7F3EA"
GOLD = "#B9A36A"
TEAL = "#5BAEAD"
BLUE = "#6F8FC9"
ORANGE = "#D48964"
GREEN = "#6CB894"
RED = "#A95656"
LINE = "#DED6C6"
INK_2 = "#4A5563"
WHITE = "#FFFFFF"


STYLE = f"""
<style>
  .se-title {{ font: 800 38px Arial, sans-serif; letter-spacing: 0; fill: {NAVY}; }}
  .se-kicker {{ font: 700 14px Arial, sans-serif; letter-spacing: 0; fill: #736646; }}
  .se-label {{ font: 700 18px Arial, sans-serif; letter-spacing: 0; fill: {NAVY}; }}
  .se-label-sm {{ font: 700 15px Arial, sans-serif; letter-spacing: 0; fill: {NAVY}; }}
  .se-micro {{ font: 600 13px Arial, sans-serif; letter-spacing: 0; fill: {INK_2}; }}
  .se-invert {{ fill: {CREAM}; }}
  .se-line {{ stroke: {NAVY}; stroke-width: 3; fill: none; stroke-linecap: round; stroke-linejoin: round; vector-effect: non-scaling-stroke; }}
  .se-line-soft {{ stroke: {NAVY}; stroke-width: 2.5; fill: none; stroke-linecap: round; stroke-linejoin: round; opacity: .26; vector-effect: non-scaling-stroke; }}
  .se-line-gold {{ stroke: {GOLD}; stroke-width: 3; fill: none; stroke-linecap: round; stroke-linejoin: round; vector-effect: non-scaling-stroke; }}
  .se-panel {{ fill: {WHITE}; stroke: {LINE}; stroke-width: 2; vector-effect: non-scaling-stroke; }}
  .se-soft {{ fill: {WHITE}; opacity: .58; }}
  .se-hairline {{ stroke: {LINE}; stroke-width: 1.5; vector-effect: non-scaling-stroke; }}
</style>""".strip()


def svg(title: str, desc: str, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720" role="img" aria-labelledby="title desc" shape-rendering="geometricPrecision">
<title id="title">{title}</title>
<desc id="desc">{desc}</desc>
<rect width="1200" height="720" fill="{CREAM}"/>
<g opacity=".14">
  <line x1="72" y1="252" x2="1128" y2="252" class="se-hairline"/>
  <line x1="72" y1="438" x2="1128" y2="438" class="se-hairline"/>
  <line x1="352" y1="176" x2="352" y2="632" class="se-hairline"/>
  <line x1="848" y1="176" x2="848" y2="632" class="se-hairline"/>
</g>
<defs>
{STYLE}
</defs>
{heading(title, desc)}
{body}
</svg>
"""


def heading(title: str, desc: str) -> str:
    kicker = desc.split(".")[0]
    return f"""<text x="72" y="84" class="se-title">{title}</text>
<text x="74" y="118" class="se-kicker">{kicker}</text>
<line x1="72" y1="150" x2="1128" y2="150" stroke="{GOLD}" stroke-width="3" stroke-linecap="round"/>
<rect x="986" y="70" width="142" height="46" rx="23" fill="{WHITE}" opacity=".72" stroke="{LINE}"/>
<text x="1057" y="99" text-anchor="middle" class="se-kicker">SUPER EUKARYA</text>"""


def tspan_lines(lines: list[str], x: int, y: int, size_class: str = "se-label", dy: int = 22, anchor: str = "middle") -> str:
    out = [f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="{size_class}">']
    first = True
    for line in lines:
        out.append(f'<tspan x="{x}" dy="{0 if first else dy}">{line}</tspan>')
        first = False
    out.append("</text>")
    return "".join(out)


def node(x: int, y: int, r: int, color: str, label: list[str], invert: bool = False) -> str:
    fill = color if invert else WHITE
    text_class = "se-label-sm se-invert" if invert else "se-label-sm"
    stroke = color
    text_y = y - (8 if len(label) > 1 else -5)
    return f"""<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="4"/>
{tspan_lines(label, x, text_y, text_class, 18)}"""


def label_box(x: int, y: int, w: int, h: int, label: list[str], color: str = NAVY) -> str:
    cx = x + w // 2
    ty = y + h // 2 - (8 if len(label) > 1 else -5)
    return f"""<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" class="se-panel"/>
<rect x="{x}" y="{y}" width="8" height="{h}" rx="4" fill="{color}"/>
{tspan_lines(label, cx, ty, "se-label-sm", 18)}"""


def system_map() -> str:
    connectors = "\n".join(
        f'<line x1="600" y1="380" x2="{x}" y2="{y}" class="se-line-soft"/>'
        for x, y in [(600, 220), (845, 300), (845, 500), (600, 572), (355, 500), (355, 300)]
    )
    body = f"""<g>
{connectors}
<circle cx="600" cy="380" r="86" fill="{NAVY}"/>
{tspan_lines(["Regional", "Core"], 600, 366, "se-label se-invert", 24)}
<text x="600" y="414" text-anchor="middle" class="se-kicker">ROUTES + TRUST</text>
{node(600, 220, 58, GOLD, ["Funding"])}
{node(845, 300, 58, TEAL, ["Tourism"])}
{node(845, 500, 58, BLUE, ["Las", "Animas"])}
{node(600, 572, 58, GOLD, ["Media"])}
{node(355, 500, 58, TEAL, ["Huerfano"])}
{node(355, 300, 58, BLUE, ["Colfax"])}
<path d="M172 628 C360 585, 842 585, 1028 628" class="se-line-gold"/>
<text x="600" y="666" text-anchor="middle" class="se-micro">Shared calendars, radio, flyers, storefronts, source checks, and partner referrals.</text>
</g>"""
    return svg("Regional Outreach System", "01 / Visibility + Infrastructure + Growth. Clean hub-and-node system map.", body)


def persona_finder() -> str:
    cards = [
        (90, TEAL, "Artist"),
        (300, BLUE, "Nonprofit"),
        (510, GREEN, "Program"),
        (720, ORANGE, "Business"),
        (930, NAVY, "Civic"),
    ]
    card_markup = []
    for x, color, label in cards:
        card_markup.append(f'<rect x="{x}" y="236" width="180" height="96" rx="14" fill="{color}"/>')
        card_markup.append(f'<text x="{x + 90}" y="294" text-anchor="middle" class="se-label se-invert">{label}</text>')
        card_markup.append(f'<path d="M{x + 90} 332 C{x + 90} 392, 600 398, 600 466" class="se-line-soft"/>')
    body = f"""<g>
{"".join(card_markup)}
<rect x="388" y="456" width="424" height="124" rx="18" fill="{GOLD}" stroke="{NAVY}" stroke-width="3"/>
{tspan_lines(["Action Module", "Source + checklist + next step"], 600, 494, "se-label", 26)}
<g>
  <circle cx="430" cy="632" r="8" fill="{TEAL}"/>
  <circle cx="520" cy="632" r="8" fill="{BLUE}"/>
  <circle cx="610" cy="632" r="8" fill="{GREEN}"/>
  <circle cx="700" cy="632" r="8" fill="{ORANGE}"/>
  <circle cx="790" cy="632" r="8" fill="{NAVY}"/>
</g>
<text x="600" y="666" text-anchor="middle" class="se-micro">Equal filter inputs; one practical output per resource record.</text>
</g>"""
    return svg("Persona Finder Flow", "02 / Filter + Match + Action. Refined persona-to-action diagram.", body)


def route_nodes() -> str:
    body = f"""<g>
<path d="M196 610 C248 520, 306 452, 392 395 C488 330, 558 318, 640 280 C738 234, 836 185, 1010 128" class="se-line"/>
<path d="M392 395 C510 462, 652 472, 812 420" class="se-line-gold"/>
<circle cx="196" cy="610" r="22" fill="{NAVY}"/>
<circle cx="392" cy="395" r="22" fill="{TEAL}"/>
<circle cx="500" cy="335" r="22" fill="{GREEN}"/>
<circle cx="640" cy="280" r="22" fill="{ORANGE}"/>
<circle cx="812" cy="420" r="22" fill="{BLUE}"/>
<circle cx="1010" cy="128" r="22" fill="{GOLD}" stroke="{NAVY}" stroke-width="3"/>
<line x1="196" y1="610" x2="286" y2="580" class="se-line-soft"/>
<line x1="392" y1="395" x2="292" y2="384" class="se-line-soft"/>
<line x1="500" y1="335" x2="512" y2="245" class="se-line-soft"/>
<line x1="640" y1="280" x2="720" y2="236" class="se-line-soft"/>
<line x1="812" y1="420" x2="884" y2="456" class="se-line-soft"/>
<line x1="1010" y1="128" x2="914" y2="200" class="se-line-soft"/>
{label_box(286, 552, 176, 64, ["Walsenburg"], NAVY)}
{label_box(126, 356, 166, 64, ["La Veta"], TEAL)}
{label_box(452, 214, 164, 64, ["Cuchara"], GREEN)}
{label_box(720, 206, 164, 64, ["Trinidad"], ORANGE)}
{label_box(884, 430, 142, 64, ["Raton"], BLUE)}
{label_box(746, 176, 168, 76, ["Angel Fire", "Eagle Nest"], GOLD)}
<text x="600" y="666" text-anchor="middle" class="se-micro">Route logic: hub towns first, then corridor nodes and seasonal verification passes.</text>
</g>"""
    return svg("Tri-County Route Nodes", "03 / I-25 + Highway Corridors + Visitor Routes. Clean outreach geography graphic.", body)


def visibility_stack() -> str:
    labels = [
        ("01", "Website + Search", NAVY),
        ("02", "Google Business Profile", BLUE),
        ("03", "Tourism + City Calendars", TEAL),
        ("04", "Radio + Newspaper", GREEN),
        ("05", "Flyers + Bulletin Boards", ORANGE),
        ("06", "Partner Posts + Storefronts", GOLD),
    ]
    rows = []
    y = 208
    for idx, label, color in labels:
        text_fill = NAVY if color == GOLD else CREAM
        rows.append(f'<circle cx="176" cy="{y + 28}" r="15" fill="{color}" stroke="{NAVY if color == GOLD else color}" stroke-width="2"/>')
        rows.append(f'<rect x="220" y="{y}" width="760" height="56" rx="10" fill="{color}"/>')
        rows.append(f'<text x="256" y="{y + 36}" class="se-label-sm" fill="{text_fill}">{idx}</text>')
        rows.append(f'<text x="330" y="{y + 36}" class="se-label" fill="{text_fill}">{label}</text>')
        y += 70
    body = f"""<g>
<path d="M176 236 V586" class="se-line-gold"/>
{"".join(rows)}
<rect x="220" y="638" width="760" height="30" rx="15" fill="{WHITE}" opacity=".72" stroke="{LINE}"/>
<text x="600" y="659" text-anchor="middle" class="se-micro">Use the stack together: online proof, public calendars, local media, physical routes, and partner reminders.</text>
</g>"""
    return svg("Visibility Stack", "04 / Digital + Physical Channels. Proportionally spaced promotion stack.", body)


def accessibility_contrast() -> str:
    swatches = [
        (104, NAVY, CREAM, "Navy / Cream"),
        (364, CREAM, NAVY, "Cream / Navy"),
        (624, TEAL, CREAM, "Teal / Cream"),
        (884, GOLD, NAVY, "Gold / Navy"),
    ]
    out = []
    for x, bg, fg, label in swatches:
        out.append(f'<rect x="{x}" y="226" width="212" height="148" rx="14" fill="{bg}" stroke="{NAVY if bg == CREAM else bg}" stroke-width="3"/>')
        out.append(f'<text x="{x + 106}" y="286" text-anchor="middle" font-family="Arial, sans-serif" font-size="40" font-weight="900" fill="{fg}">Aa</text>')
        out.append(f'<text x="{x + 106}" y="330" text-anchor="middle" class="se-label-sm" fill="{fg}">{label}</text>')
    principles = [
        (126, "Visible focus"),
        (356, "Plain labels"),
        (586, "Keyboard path"),
        (816, "Useful alt text"),
    ]
    for x, label in principles:
        out.append(f'<rect x="{x}" y="456" width="258" height="66" rx="33" fill="{WHITE}" stroke="{LINE}" stroke-width="2"/>')
        out.append(f'<circle cx="{x + 36}" cy="489" r="12" fill="{GOLD}"/>')
        out.append(f'<text x="{x + 64}" y="496" class="se-label-sm">{label}</text>')
    body = f"""<g>
{"".join(out)}
<path d="M126 584 H1074" class="se-line-gold"/>
<text x="600" y="628" text-anchor="middle" class="se-label-sm">Accessibility is infrastructure, not a final checkbox.</text>
</g>"""
    return svg("Accessibility As System", "05 / Contrast + Labels + Keyboard + Alt Text. Balanced accessibility diagram.", body)


def media_network() -> str:
    positions = [
        (600, 208, GOLD, ["Calendars"]),
        (855, 300, GREEN, ["Partners"]),
        (855, 500, TEAL, ["Social"]),
        (600, 586, ORANGE, ["Flyer", "Boards"]),
        (345, 500, BLUE, ["News"]),
        (345, 300, GOLD, ["Radio"]),
    ]
    out = ['<circle cx="600" cy="400" r="214" fill="none" stroke="#D8D3C8" stroke-width="2"/>']
    for x, y, color, label in positions:
        out.append(f'<line x1="600" y1="400" x2="{x}" y2="{y}" class="se-line-soft"/>')
    out.append(f'<circle cx="600" cy="400" r="76" fill="{NAVY}"/>')
    out.append(tspan_lines(["Event", "Packet"], 600, 386, "se-label se-invert", 24))
    for x, y, color, label in positions:
        out.append(node(x, y, 54, color, label))
    body = f"""<g>
{"".join(out)}
<text x="600" y="666" text-anchor="middle" class="se-micro">A reusable packet can move through radio, news, calendars, flyer boards, social posts, and partner networks.</text>
</g>"""
    return svg("Local Media Network", "06 / Radio + News + Boards + Social + Partners. Symmetric media diagram.", body)


def funding_pipeline() -> str:
    steps = [
        (110, TEAL, "Idea", "scope + need"),
        (365, BLUE, "Budget", "quotes + match"),
        (620, ORANGE, "Apply", "forms + proof"),
        (875, GREEN, "Report", "metrics + media"),
    ]
    out = []
    for x, color, title, sub in steps:
        out.append(f'<rect x="{x}" y="284" width="215" height="124" rx="16" fill="{color}"/>')
        out.append(f'<text x="{x + 107}" y="336" text-anchor="middle" class="se-label se-invert">{title}</text>')
        out.append(f'<text x="{x + 107}" y="374" text-anchor="middle" class="se-micro" fill="{CREAM}">{sub}</text>')
    for x in [325, 580, 835]:
        out.append(f'<path d="M{x} 346 H{x + 40}" class="se-line-gold"/>')
        out.append(f'<path d="M{x + 40} 346 l-12 -8 M{x + 40} 346 l-12 8" class="se-line-gold"/>')
    body = f"""<g>
{"".join(out)}
<rect x="164" y="502" width="872" height="78" rx="18" class="se-panel"/>
<text x="600" y="535" text-anchor="middle" class="se-label-sm">Do not start with the application.</text>
<text x="600" y="562" text-anchor="middle" class="se-micro">Start with fit, public need, budget reality, source evidence, and reporting capacity.</text>
</g>"""
    return svg("Funding Readiness Pipeline", "07 / Idea + Evidence + Application + Reporting. Clean funding process graphic.", body)


def cross_promotion_loop() -> str:
    marker = f"""<marker id="se-loop-arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">
  <path d="M0 0 L10 5 L0 10 z" fill="{GOLD}"/>
</marker>"""
    points = [
        (600, 214, NAVY, "Lodge"),
        (760, 330, TEAL, "Dine"),
        (698, 520, BLUE, "Retail"),
        (502, 520, ORANGE, "Event"),
        (440, 330, GOLD, "Recap"),
    ]
    arcs = [
        "M648 222 C700 240, 742 276, 764 324",
        "M752 382 C738 438, 720 482, 704 514",
        "M648 544 C586 570, 542 562, 508 526",
        "M458 486 C422 438, 420 382, 438 336",
        "M472 288 C504 240, 548 216, 594 214",
    ]
    out = [f"<defs>{marker}</defs>"]
    out.append(f'<circle cx="600" cy="382" r="198" fill="{WHITE}" opacity=".46" stroke="{LINE}" stroke-width="2"/>')
    for d in arcs:
        out.append(f'<path d="{d}" class="se-line-gold" marker-end="url(#se-loop-arrow)"/>')
    for x, y, color, label in points:
        invert = color != GOLD
        out.append(node(x, y, 52, color, [label], invert=invert))
    out.append(f'<rect x="470" y="348" width="260" height="78" rx="16" class="se-panel"/>')
    out.append(tspan_lines(["Follow-up", "Log"], 600, 374, "se-label-sm", 20))
    body = f"""<g>
{"".join(out)}
<text x="600" y="666" text-anchor="middle" class="se-micro">Ask, share, display, attend, recap, correct the directory, and repeat with better local knowledge.</text>
</g>"""
    return svg("Cross-Promotion Loop", "08 / Lodging + Dining + Retail + Event + Recap. Refined partner loop.", body)


ASSETS = {
    "se_system_map.svg": system_map,
    "se_persona_finder_diagram.svg": persona_finder,
    "se_tri_county_route_nodes.svg": route_nodes,
    "se_visibility_stack.svg": visibility_stack,
    "se_accessibility_contrast.svg": accessibility_contrast,
    "se_bulletin_media_network.svg": media_network,
    "se_funding_pipeline.svg": funding_pipeline,
    "se_cross_promotion_loop.svg": cross_promotion_loop,
}


def main() -> int:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for filename, builder in ASSETS.items():
        path = ASSET_DIR / filename
        path.write_text(builder(), encoding="utf-8")
    print(f"Wrote {len(ASSETS)} refined SVG assets to {ASSET_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
