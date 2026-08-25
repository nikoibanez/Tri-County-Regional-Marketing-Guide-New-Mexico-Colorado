from __future__ import annotations

import re
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "animations"


STYLE_TEMPLATE = """
  .sun-glow { animation: geo-sun 30s ease-in-out infinite alternate; }
  .cloud-bank { animation: geo-clouds 108s linear infinite; }
  .far-range,
  .mid-range {
    transform-box: fill-box;
    transform-origin: 50% 100%;
  }
  .far-range { animation: geo-far 52s ease-in-out infinite alternate; }
  .mid-range { animation: geo-mid 44s ease-in-out infinite alternate; }
  .near-feature { animation: geo-near 38s ease-in-out infinite alternate; }
  .plains-layer {
    transform-box: fill-box;
    transform-origin: 50% 100%;
    animation: geo-plains 48s ease-in-out infinite alternate;
  }
  .wind-line {
    fill: none;
    stroke: __WIND_LIGHT__;
    opacity: 0.42;
    stroke-width: 1.4;
    stroke-linecap: round;
    stroke-dasharray: 210 90;
    animation: geo-wind 28s linear infinite;
  }
  .wind-line.thin { stroke-width: 0.9; opacity: 0.28; animation-duration: 34s; }
  .wind-line.gold { stroke: __WIND_ACCENT__; opacity: 0.30; animation-duration: 31s; }
  .yucca-sway {
    transform-box: fill-box;
    transform-origin: 50% 100%;
    animation: geo-yucca 10.5s ease-in-out infinite alternate;
  }
  .yucca-sway.slow { animation-duration: 13s; animation-delay: -1.2s; }
  .leaf-sway {
    transform-box: fill-box;
    transform-origin: 50% 100%;
    animation: geo-leaf 12s ease-in-out infinite alternate;
  }
  .blossom {
    transform-box: fill-box;
    transform-origin: 50% 18%;
    animation: geo-blossom 9s ease-in-out infinite alternate;
  }
  .blossom.d2 { animation-delay: -1.6s; }
  .blossom.d3 { animation-delay: -3.1s; }
  .seed {
    transform-box: fill-box;
    transform-origin: 0 0;
    animation: geo-seed 24s ease-in-out infinite;
  }
  .seed.s2 { animation-delay: -4s; }
  .seed.s3 { animation-delay: -8s; }
  @keyframes geo-sun {
    from { transform: translate(-3px, 1px) scale(0.99); opacity: 0.54; }
    to { transform: translate(4px, -2px) scale(1.01); opacity: 0.68; }
  }
  @keyframes geo-clouds {
    from { transform: translateX(-220px); }
    to { transform: translateX(1700px); }
  }
  @keyframes geo-far {
    from { transform: translateX(-2px) scaleX(1.014); }
    to { transform: translateX(2px) scaleX(1.018); }
  }
  @keyframes geo-mid {
    from { transform: translateX(2px) scaleX(1.018); }
    to { transform: translateX(-2px) scaleX(1.014); }
  }
  @keyframes geo-near {
    from { transform: translateX(-3px) translateY(0.5px); }
    to { transform: translateX(3px) translateY(-0.5px); }
  }
  @keyframes geo-plains {
    from { transform: translateX(-2px) scaleX(1.012); }
    to { transform: translateX(2px) translateY(-1px) scaleX(1.016); }
  }
  @keyframes geo-wind {
    from { stroke-dashoffset: 180; transform: translateX(-18px); }
    to { stroke-dashoffset: -180; transform: translateX(26px); }
  }
  @keyframes geo-yucca {
    from { transform: rotate(-0.8deg) translateX(-1px); }
    to { transform: rotate(1.1deg) translateX(1.5px); }
  }
  @keyframes geo-leaf {
    from { transform: rotate(-0.45deg); }
    to { transform: rotate(0.75deg); }
  }
  @keyframes geo-blossom {
    from { transform: rotate(-1.2deg) translateY(0); }
    to { transform: rotate(1deg) translateY(1px); }
  }
  @keyframes geo-seed {
    0%, 100% { transform: translate(0, 0) rotate(-3deg); opacity: 0.54; }
    50% { transform: translate(14px, 4px) rotate(4deg); opacity: 0.36; }
  }
  @media (prefers-reduced-motion: reduce) {
    .sun-glow,
    .cloud-bank,
    .far-range,
    .mid-range,
    .near-feature,
    .plains-layer,
    .wind-line,
    .yucca-sway,
    .leaf-sway,
    .blossom,
    .seed {
      animation: none !important;
    }
  }
"""


def style_for(variant: dict[str, str]) -> str:
    return (
        STYLE_TEMPLATE.replace("__WIND_LIGHT__", variant["wind_light"])
        .replace("__WIND_ACCENT__", variant["wind_accent"])
    )


def common_defs(variant: dict[str, str]) -> str:
    return f"""
  <linearGradient id="yuccaLeaf" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{variant['leaf_dark']}"/>
    <stop offset="0.48" stop-color="{variant['leaf_mid']}"/>
    <stop offset="1" stop-color="{variant['leaf_light']}"/>
  </linearGradient>
  <linearGradient id="flower" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{variant['flower_top']}"/>
    <stop offset="0.62" stop-color="{variant['flower_mid']}"/>
    <stop offset="1" stop-color="{variant['flower_base']}"/>
  </linearGradient>
  <filter id="softShadow" x="-20%" y="-20%" width="140%" height="150%">
    <feDropShadow dx="0" dy="14" stdDeviation="14" flood-color="{variant['shadow']}" flood-opacity="0.13"/>
  </filter>
"""


def yucca(side: str, variant: dict[str, str]) -> str:
    if side == "left":
        transform = "translate(42 344) scale(0.62)"
    elif side == "both":
        return yucca("left", variant) + yucca("right", variant)
    else:
        transform = "translate(1212 330) scale(0.58)"
    return f"""
    <g filter="url(#softShadow)" opacity="0.88" transform="{transform}">
      <g class="leaf-sway">
        <path d="M150 520l62-260 30 270z" fill="url(#yuccaLeaf)"/>
        <path d="M148 524l-66-220 120 222z" fill="{variant['leaf_dark']}" opacity="0.9"/>
        <path d="M178 520l148-194-80 204z" fill="{variant['leaf_mid']}"/>
        <path d="M190 523l214-120-148 130z" fill="{variant['leaf_secondary']}"/>
        <path d="M116 526L0 370l168 154z" fill="{variant['leaf_dark']}" opacity="0.88"/>
        <path d="M206 526l58-158 10 164z" fill="{variant['leaf_light']}"/>
      </g>
      <g class="yucca-sway slow" transform="translate(202 54)">
        <path d="M0 430C24 320 36 213 24 0" fill="none" stroke="{variant['stem']}" stroke-width="10" stroke-linecap="round"/>
        <path d="M24 58c24-24 52-42 82-55" fill="none" stroke="{variant['branch']}" stroke-width="7" stroke-linecap="round"/>
        <path d="M24 114c-25-25-48-39-75-49" fill="none" stroke="{variant['branch']}" stroke-width="7" stroke-linecap="round"/>
        <path d="M30 186c34-24 65-37 104-43" fill="none" stroke="{variant['branch']}" stroke-width="7" stroke-linecap="round"/>
        <path d="M26 252c-28-22-59-38-94-46" fill="none" stroke="{variant['branch']}" stroke-width="7" stroke-linecap="round"/>
        <g class="blossom"><ellipse cx="112" cy="4" rx="17" ry="33" fill="url(#flower)" transform="rotate(25 112 4)"/><ellipse cx="88" cy="8" rx="15" ry="30" fill="url(#flower)" transform="rotate(-12 88 8)"/></g>
        <g class="blossom d2"><ellipse cx="-54" cy="68" rx="17" ry="34" fill="url(#flower)" transform="rotate(-24 -54 68)"/><ellipse cx="-26" cy="76" rx="15" ry="29" fill="url(#flower)" transform="rotate(12 -26 76)"/></g>
        <g class="blossom d3"><ellipse cx="132" cy="144" rx="15" ry="32" fill="url(#flower)" transform="rotate(26 132 144)"/><ellipse cx="104" cy="151" rx="14" ry="28" fill="url(#flower)" transform="rotate(-10 104 151)"/></g>
      </g>
    </g>
    """


HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}")


def branded_geometry(fragment: str, variant: dict[str, str]) -> str:
    """Map legacy scene-specific fills to the assigned public brand family."""

    def replacement(match: re.Match[str]) -> str:
        value = match.group(0)
        red, green, blue = (int(value[index : index + 2], 16) for index in (1, 3, 5))
        luminance = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255
        if luminance > 0.86:
            return variant["flower_mid"]
        if red > green * 1.2 and red > blue * 1.2:
            return variant["warm"]
        if luminance < 0.24:
            return variant["ridge_shadow"]
        if luminance < 0.44:
            return variant["near_a"]
        if luminance < 0.68:
            return variant["near_b"]
        return variant["plain_a"]

    return HEX_COLOR.sub(replacement, fragment)


def svg_for(variant: dict[str, str]) -> str:
    far = branded_geometry(variant["far"], variant)
    mid = branded_geometry(variant["mid"], variant)
    feature = branded_geometry(variant["feature"], variant)
    return dedent(
        f"""\
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 720" role="img" aria-labelledby="title desc" data-brand-palette="{variant['brand']}" data-edge-overscan="true">
          <title id="title">{variant['title']}</title>
          <desc id="desc">{variant['desc']}</desc>
          <defs>
            <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stop-color="{variant['sky_top']}"/>
              <stop offset="0.58" stop-color="{variant['sky_mid']}"/>
              <stop offset="1" stop-color="{variant['sky_bottom']}"/>
            </linearGradient>
            <radialGradient id="sunwash" cx="{variant['sun_x']}" cy="{variant['sun_y']}" r="0.42">
              <stop offset="0" stop-color="{variant['flower_mid']}" stop-opacity="0.9"/>
              <stop offset="0.52" stop-color="{variant['warm']}" stop-opacity="0.28"/>
              <stop offset="1" stop-color="{variant['sky_highlight']}" stop-opacity="0"/>
            </radialGradient>
            <linearGradient id="farTone" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stop-color="{variant['far_a']}" stop-opacity="0.70"/>
              <stop offset="1" stop-color="{variant['far_b']}" stop-opacity="0.68"/>
            </linearGradient>
            <linearGradient id="nearTone" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stop-color="{variant['near_a']}"/>
              <stop offset="1" stop-color="{variant['near_b']}"/>
            </linearGradient>
            {common_defs(variant)}
            <style>{style_for(variant)}</style>
          </defs>
          <rect width="1600" height="720" fill="url(#sky)"/>
          <rect width="1600" height="720" fill="url(#sunwash)" class="sun-glow"/>
          <g class="cloud-bank" opacity="0.42">
            <path d="M-160 162c22-39 76-46 104-20 22-44 90-56 122-18 24-18 68-17 92 3 32 27 16 68-42 68h-276z" fill="{variant['sky_bottom']}"/>
            <path d="M-520 238c16-30 54-37 76-16 15-34 64-46 89-18 18-14 54-13 72 4 25 23 14 54-30 54h-207z" fill="{variant['sky_bottom']}" opacity="0.78"/>
          </g>
          <path class="wind-line thin" d="{variant['wind1']}"/>
          <path class="wind-line" d="{variant['wind2']}"/>
          <path class="wind-line gold" d="{variant['wind3']}"/>
          <g class="far-range">{far}</g>
          <g class="mid-range">{mid}</g>
          <g class="near-feature">{feature}</g>
          <g id="plains" class="plains-layer" opacity="0.95">
            <path d="{variant['plain1']}" fill="{variant['plain_a']}" opacity="0.34"/>
            <path d="{variant['plain2']}" fill="{variant['plain_b']}" opacity="0.32"/>
            <path d="M0 680c250-34 465-34 642 0 190 36 336 38 528 3 170-31 316-22 430 22v15H0z" fill="{variant['ridge_shadow']}" opacity="0.10"/>
          </g>
          {yucca(variant['yucca'], variant)}
          <g opacity="0.72">
            <path class="seed" d="M545 238c34-18 54-14 78 14-32 18-57 12-78-14z" fill="{variant['flower_top']}"/>
            <path class="seed s2" d="M884 154c26-13 43-9 62 12-26 15-45 10-62-12z" fill="{variant['flower_top']}"/>
            <path class="seed s3" d="M1016 312c28-16 47-11 68 13-29 16-50 11-68-13z" fill="{variant['flower_top']}"/>
          </g>
        </svg>
        """
    )


BASE = {
    "sun_x": "0.72",
    "sun_y": "0.34",
    "wind1": "M515 126c168 48 292 50 436 2 126-42 236-38 364 7",
    "wind2": "M356 178c190 76 384 80 566 20 192-63 342-45 536 24",
    "wind3": "M660 246c142 30 288 20 422-28 102-37 192-24 286 22",
    "plain1": "M0 542c155-30 300-28 438 8 122 31 265 36 426 10 182-30 355-18 520 42 85 31 155 37 216 18v100H0z",
    "plain2": "M0 626c184-22 324-23 446-5 176 26 318 17 460-28 188-58 388-46 694 40v87H0z",
    "yucca": "right",
}


# These animation-only palettes are derived from the current official websites
# and logo assets for the City of Raton, Explore Raton, and Raton MainStreet.
# Keep them distinct so future landscape variants remain related without
# flattening the three public identities into one generic Southwest palette.
BRAND_PALETTES = {
    "city-of-raton": {
        "sky_top": "#bfe9e8",
        "sky_mid": "#eeedd6",
        "sky_bottom": "#f8f7ed",
        "sky_highlight": "#ffffff",
        "warm": "#772816",
        "far_a": "#21bdc5",
        "far_b": "#b3b078",
        "near_a": "#147176",
        "near_b": "#4a221a",
        "plain_a": "#b3b078",
        "plain_b": "#8e9166",
        "ridge_shadow": "#4a221a",
        "leaf_dark": "#174d51",
        "leaf_mid": "#147176",
        "leaf_secondary": "#2b6767",
        "leaf_light": "#b3b078",
        "stem": "#58642f",
        "branch": "#716f35",
        "flower_top": "#ffffff",
        "flower_mid": "#eeedd6",
        "flower_base": "#b3b078",
        "shadow": "#4a221a",
        "wind_light": "#ffffff",
        "wind_accent": "#21bdc5",
    },
    "explore-raton": {
        "sky_top": "#aae8ec",
        "sky_mid": "#dfe6e9",
        "sky_bottom": "#eeedd6",
        "sky_highlight": "#ffffff",
        "warm": "#d97345",
        "far_a": "#21bdc5",
        "far_b": "#775751",
        "near_a": "#2b5672",
        "near_b": "#772816",
        "plain_a": "#d97345",
        "plain_b": "#7ed4d8",
        "ridge_shadow": "#22495a",
        "leaf_dark": "#22495a",
        "leaf_mid": "#2b5672",
        "leaf_secondary": "#147176",
        "leaf_light": "#21bdc5",
        "stem": "#4a5f4a",
        "branch": "#65714e",
        "flower_top": "#ffffff",
        "flower_mid": "#eeedd6",
        "flower_base": "#d97345",
        "shadow": "#22495a",
        "wind_light": "#aae8ec",
        "wind_accent": "#d97345",
    },
    "raton-mainstreet": {
        "sky_top": "#c8d5dc",
        "sky_mid": "#f3f5f8",
        "sky_bottom": "#ffffff",
        "sky_highlight": "#ffffff",
        "warm": "#a06393",
        "far_a": "#a06393",
        "far_b": "#716c2c",
        "near_a": "#6c1c5b",
        "near_b": "#2a2a2a",
        "plain_a": "#716c2c",
        "plain_b": "#c8d5dc",
        "ridge_shadow": "#2a2a2a",
        "leaf_dark": "#3f2b3a",
        "leaf_mid": "#6c1c5b",
        "leaf_secondary": "#59602e",
        "leaf_light": "#716c2c",
        "stem": "#5b5931",
        "branch": "#716c2c",
        "flower_top": "#ffffff",
        "flower_mid": "#f3f5f8",
        "flower_base": "#a06393",
        "shadow": "#2a2a2a",
        "wind_light": "#c8d5dc",
        "wind_accent": "#a06393",
    },
}


VARIANTS = [
    {
        **BASE,
        "file": "hero-plains-valley.svg",
        "brand": "explore-raton",
        "title": "Animated high plains valley and yucca flowers",
        "desc": "A soft animated high plains valley with long ridges, yucca flowers, drifting clouds, and wind lines.",
        "far": '<path d="M0 430l140-70 142 36 174-102 144 92 142-62 156 96 138-72 152 84 196-116 176 120v284H0z" fill="url(#farTone)" opacity="0.62"/>',
        "mid": '<path d="M0 500c190-74 356-84 516-30 155 52 282 42 424-28 170-84 348-78 660 52v226H0z" fill="url(#nearTone)" opacity="0.58"/>',
        "feature": '<path d="M160 548c190-28 353-22 490 16 172 48 338 32 530-34 132-45 260-48 386-9v76c-188-34-345-26-510 22-178 52-344 54-504 8-146-42-330-40-552 14v-58c48-14 101-26 160-35z" fill="#e7ca8a" opacity="0.46"/>',
    },
    {
        **BASE,
        "file": "hero-fishers-peak.svg",
        "brand": "city-of-raton",
        "title": "Animated Fishers Peak mesa and yucca flowers",
        "desc": "A stylized Fishers Peak-inspired flat-topped mesa near Trinidad with foothills, plains, yucca flowers, and wind lines.",
        "far": '<path d="M0 438l160-72 164 28 170-88 146 84 158-66 146 78 196-94 198 116 262-78v374H0z" fill="url(#farTone)" opacity="0.58"/>',
        "mid": '<path d="M0 500c140-54 302-70 486-48 208 25 374-11 548-78 190-74 360-72 566 4v342H0z" fill="url(#nearTone)" opacity="0.54"/>',
        "feature": '<path d="M410 432l116-70h472l126 72-56 74H470z" fill="#2d4d56" opacity="0.88"/><path d="M526 362h472l36 20-514 10z" fill="#243d46" opacity="0.82"/><path d="M470 508h598l-68 74H414z" fill="#9b795e" opacity="0.62"/><path d="M614 395l-74 100M768 390l-46 116M930 392l52 110" stroke="#e7c89a" stroke-width="7" stroke-linecap="round" opacity="0.22"/>',
    },
    {
        **BASE,
        "file": "hero-garden-gods.svg",
        "brand": "raton-mainstreet",
        "title": "Animated Garden of the Gods sandstone fins and yucca flowers",
        "desc": "A Garden of the Gods-inspired animated scene with tilted red sandstone fins, pale distant peaks, yucca flowers, and wind lines.",
        "yucca": "both",
        "far": '<path d="M0 430l142-68 160 36 210-114 116 98 180-82 134 94 144-88 128 92 138-70 248 114v278H0z" fill="url(#farTone)" opacity="0.50"/><path d="M920 378l86-92 76 92z" fill="#f5f1e2" opacity="0.48"/>',
        "mid": '<path d="M0 522c160-48 306-58 438-28 122 28 256 19 402-24 210-61 442-42 760 52v198H0z" fill="#d7a66f" opacity="0.34"/>',
        "feature": '<path d="M470 548l92-252 44 262z" fill="#c05d3d" opacity="0.90"/><path d="M570 566l138-330 56 342z" fill="#a94d3d" opacity="0.92"/><path d="M724 580l124-278 58 286z" fill="#dd8b5d" opacity="0.88"/><path d="M876 574l92-244 48 252z" fill="#b55742" opacity="0.88"/><path d="M1038 566l74-184 40 190z" fill="#d7895d" opacity="0.82"/><path d="M520 364l34 178M646 306l44 230M790 356l36 192M936 398l28 150" stroke="#f5c891" stroke-width="6" stroke-linecap="round" opacity="0.28"/>',
    },
    {
        **BASE,
        "file": "hero-desert-buttes.svg",
        "brand": "explore-raton",
        "title": "Animated desert buttes, arroyos, and yucca flowers",
        "desc": "A dry animated butte and arroyo scene with layered desert mesas, yucca flowers, drifting clouds, and wind lines.",
        "far": '<path d="M0 444h164l52-48h184l36 46h204l64-82h256l48 80h240l78-54h274v334H0z" fill="url(#farTone)" opacity="0.58"/>',
        "mid": '<path d="M0 520h330l46-70h168l42 70h246l76-92h232l62 92h398v200H0z" fill="url(#nearTone)" opacity="0.58"/>',
        "feature": '<path d="M300 584c190-54 388-52 594 4 162 44 337 45 536 2v62c-212 50-399 46-564-4-204-62-404-60-600 6z" fill="#d8a46e" opacity="0.42"/><path d="M760 600c-126-18-234-12-326 18 90 18 181 23 274 16 84-6 165-2 242 14-54-26-118-42-190-48z" fill="#8a6f5d" opacity="0.24"/>',
    },
    {
        **BASE,
        "file": "hero-raton-mesa.svg",
        "brand": "city-of-raton",
        "title": "Animated Raton Mesa country and yucca flowers",
        "desc": "A Raton Mesa-inspired animated plateau with volcanic caprock, grassland folds, yucca flowers, and wind lines.",
        "far": '<path d="M0 436l150-56 184 28 160-64 170 62 158-60 162 64 174-72 156 76 286-54v360H0z" fill="url(#farTone)" opacity="0.56"/>',
        "mid": '<path d="M0 498h280l56-46h360l62 46h332l76-54h434v222H0z" fill="url(#nearTone)" opacity="0.58"/>',
        "feature": '<path d="M338 490h820l94 78H258z" fill="#314c52" opacity="0.74"/><path d="M258 568h994v64H258z" fill="#b08a5f" opacity="0.36"/><path d="M388 523h696" stroke="#d8bb68" stroke-width="8" stroke-linecap="round" opacity="0.24"/>',
    },
    {
        **BASE,
        "file": "hero-volcanic-field.svg",
        "brand": "explore-raton",
        "title": "Animated Raton-Clayton volcanic field and yucca flowers",
        "desc": "A Raton-Clayton volcanic field-inspired animated scene with cinder cones, basalt ridges, plains, yucca flowers, and wind lines.",
        "far": '<path d="M0 438l150-54 162 44 192-104 136 84 182-74 140 76 154-60 138 72 346-80v378H0z" fill="url(#farTone)" opacity="0.54"/>',
        "mid": '<path d="M0 520c132-72 246-92 342-60 96 32 182 16 258-50 120-102 250-96 380 20 94 84 200 98 318 44 108-50 208-58 302-20v266H0z" fill="url(#nearTone)" opacity="0.52"/>',
        "feature": '<path d="M606 540l154-176 170 176z" fill="#263e48" opacity="0.84"/><path d="M706 420c42-28 83-28 126 0-39 18-82 18-126 0z" fill="#1d3039" opacity="0.86"/><path d="M324 574l94-118 110 118zM1010 584l84-96 98 96z" fill="#6f6356" opacity="0.56"/><path d="M760 390l-38 126M812 394l34 120" stroke="#d8bb68" stroke-width="5" opacity="0.22"/>',
    },
    {
        **BASE,
        "file": "hero-fishers-canyon.svg",
        "brand": "city-of-raton",
        "title": "Animated Fishers Peak canyon and mesa slopes",
        "desc": "A Fishers Peak country-inspired animated canyon scene with a broad mesa profile, shaded draws, yucca flowers, and wind lines.",
        "yucca": "left",
        "far": '<path d="M0 432l166-58 160 34 184-90 128 72 176-60 156 70 192-82 138 76 300-56v382H0z" fill="url(#farTone)" opacity="0.55"/>',
        "mid": '<path d="M0 504c180-70 362-82 548-36 156 38 296 12 420-76 146-104 330-102 632-14v342H0z" fill="url(#nearTone)" opacity="0.53"/>',
        "feature": '<path d="M520 424h438l130 80H420z" fill="#253f49" opacity="0.82"/><path d="M420 504h668l-126 130H514z" fill="#aa7e58" opacity="0.46"/><path d="M666 524c70 42 110 82 120 120M842 520c-70 52-110 92-132 130" stroke="#5b4b48" stroke-width="12" stroke-linecap="round" opacity="0.20"/>',
    },
    {
        **BASE,
        "file": "hero-spanish-peaks.svg",
        "brand": "raton-mainstreet",
        "title": "Animated Spanish Peaks and radial dike country",
        "desc": "A Spanish Peaks-inspired animated scene with twin peaks, radial dike lines, valleys, yucca flowers, and wind lines.",
        "far": '<path d="M0 442l138-56 166 38 182-94 128 80 162-64 146 82 160-68 148 78 370-84v366H0z" fill="url(#farTone)" opacity="0.52"/>',
        "mid": '<path d="M0 522l250-86 176 54 234-190 154 168 104-72 164 104 180-222 338 240v202H0z" fill="url(#nearTone)" opacity="0.62"/>',
        "feature": '<path d="M660 304l94 168 96-126 80 142 140-212 186 278H500z" fill="#3f6575" opacity="0.44"/><path d="M760 422l-278 176M822 438l-174 190M930 438l224 178M1028 448l338 150" stroke="#705c55" stroke-width="8" stroke-linecap="round" opacity="0.22"/>',
    },
    {
        **BASE,
        "file": "hero-huerfano-valley.svg",
        "brand": "city-of-raton",
        "title": "Animated Huerfano valley, foothills, and yucca flowers",
        "desc": "A Huerfano County-inspired animated valley with foothills, grassland, distant peaks, yucca flowers, and wind lines.",
        "far": '<path d="M0 430l148-74 158 42 190-118 126 100 166-84 146 92 174-92 132 104 360-68v388H0z" fill="url(#farTone)" opacity="0.55"/>',
        "mid": '<path d="M0 520c126-42 256-50 390-24 154 30 300 14 438-50 178-83 356-72 534 32 82 48 162 60 238 36v206H0z" fill="url(#nearTone)" opacity="0.46"/>',
        "feature": '<path d="M232 590c186-74 380-76 582-4 170 60 354 54 552-18 88-32 166-38 234-20v78c-164-32-316-14-456 44-182 75-358 75-528 0-156-68-362-52-616 48v-62c72-28 150-50 232-66z" fill="#a6a878" opacity="0.36"/>',
    },
    {
        **BASE,
        "file": "hero-archive-ridges.svg",
        "brand": "raton-mainstreet",
        "title": "Animated layered ridges and public source paths",
        "desc": "An animated layered ridge scene with a subtle path motif for templates, sources, and guide maintenance pages.",
        "far": '<path d="M0 434l120-46 128 26 160-68 156 76 148-52 180 70 162-60 182 76 364-82v346H0z" fill="url(#farTone)" opacity="0.54"/>',
        "mid": '<path d="M0 510c182-64 360-72 534-24 144 39 282 24 414-44 204-104 422-84 652 48v230H0z" fill="url(#nearTone)" opacity="0.44"/>',
        "feature": '<path d="M380 602c160-76 304-76 432 0 106 62 230 72 372 30 104-30 216-18 336 36" fill="none" stroke="#d8bb68" stroke-width="18" stroke-linecap="round" opacity="0.24"/><path d="M420 590c154-56 296-46 428 28 114 64 240 70 378 18 86-32 182-20 288 36" fill="none" stroke="#173047" stroke-width="5" stroke-linecap="round" stroke-dasharray="18 20" opacity="0.18"/>',
    },
    {
        **BASE,
        "file": "hero-canyon-submit.svg",
        "brand": "explore-raton",
        "title": "Animated canyon pass and submission route",
        "desc": "An animated canyon-pass scene with buttes, a soft route line, yucca flowers, and wind lines for submission pages.",
        "yucca": "left",
        "far": '<path d="M0 446h198l48-42h172l38 42h220l70-74h260l56 74h232l68-44h238v274H0z" fill="url(#farTone)" opacity="0.56"/>',
        "mid": '<path d="M0 520h330l44-64h176l40 64h232l78-84h232l58 84h410v200H0z" fill="url(#nearTone)" opacity="0.52"/>',
        "feature": '<path d="M510 626c88-92 190-142 306-150 128-9 250 36 366 136" fill="none" stroke="#fff8dc" stroke-width="22" stroke-linecap="round" opacity="0.20"/><path d="M510 626c88-92 190-142 306-150 128-9 250 36 366 136" fill="none" stroke="#173047" stroke-width="5" stroke-linecap="round" stroke-dasharray="14 18" opacity="0.18"/>',
    },
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for source_variant in VARIANTS:
        variant = {**source_variant, **BRAND_PALETTES[source_variant["brand"]]}
        (OUT / variant["file"]).write_text(svg_for(variant), encoding="utf-8")


if __name__ == "__main__":
    main()
