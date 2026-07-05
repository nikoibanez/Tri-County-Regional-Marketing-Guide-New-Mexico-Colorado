from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets" / "super_eukarya_vector_package" / "assets"
OUT = ROOT / "dist" / "super_eukarya_refined_contact_sheet.html"

FILES = [
    "se_system_map.svg",
    "se_persona_finder_diagram.svg",
    "se_tri_county_route_nodes.svg",
    "se_visibility_stack.svg",
    "se_accessibility_contrast.svg",
    "se_bulletin_media_network.svg",
    "se_funding_pipeline.svg",
    "se_cross_promotion_loop.svg",
]


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cards = []
    for filename in FILES:
        svg = (ASSET_DIR / filename).read_text(encoding="utf-8")
        cards.append(
            f"""<article>
<div class="art">{svg}</div>
<h2>{filename}</h2>
</article>"""
        )
    OUT.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Super Eukarya Refined SVG Contact Sheet</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 24px; font-family: Arial, sans-serif; background: #F4F1EA; color: #0B1F3B; }}
  main {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; max-width: 1400px; margin: 0 auto; }}
  article {{ background: #fff; border: 1px solid #D8D3C8; border-radius: 8px; overflow: hidden; }}
  .art {{ aspect-ratio: 5 / 3; background: #F4F1EA; }}
  svg {{ display: block; width: 100%; height: 100%; }}
  h1 {{ max-width: 1400px; margin: 0 auto 20px; font-size: 28px; }}
  h2 {{ margin: 0; padding: 10px 12px; font-size: 14px; background: #0B1F3B; color: #F4F1EA; letter-spacing: 0; }}
</style>
</head>
<body>
<h1>Super Eukarya Refined SVG Contact Sheet</h1>
<main>
{''.join(cards)}
</main>
</body>
</html>
""",
        encoding="utf-8",
    )
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
