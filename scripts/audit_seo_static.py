from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "dist" / "tri-county-netlify-guide-deep"
ALLOWED_PAGE_TYPES = {"WebPage", "CollectionPage", "AboutPage"}


REQUIRED_HTML_MARKERS = {
    "title": r"<title>[^<]+</title>",
    "description": r'<meta name="description" content="[^"]+">',
    "robots": r'<meta name="robots" content="index,follow">',
    "canonical": r'<link rel="canonical" href="https://[^"]+">',
    "og_title": r'<meta property="og:title" content="[^"]+">',
    "og_description": r'<meta property="og:description" content="[^"]+">',
    "structured_data": r'<script type="application/ld\+json">',
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def json_ld_nodes(payload: dict) -> list[dict]:
    graph = payload.get("@graph")
    if isinstance(graph, list):
        return [node for node in graph if isinstance(node, dict)]
    return [payload]


def main() -> None:
    if not SITE.exists():
        fail(f"site folder not found: {SITE}")

    html_files = sorted(path for path in SITE.glob("**/*.html") if "assets" not in path.relative_to(SITE).parts)
    if not html_files:
        fail("no generated HTML files found")

    failures: list[str] = []
    for path in html_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(SITE)
        h1_count = len(re.findall(r"<h1\b", text, flags=re.I))
        if h1_count != 1:
            failures.append(f"{rel}: expected exactly one h1, found {h1_count}")
        if "FAQPage" in text:
            failures.append(f"{rel}: FAQPage structured data should not be present")
        if re.search(r'<meta name="robots" content="[^"]*noindex', text, flags=re.I):
            failures.append(f"{rel}: page is marked noindex")
        for name, pattern in REQUIRED_HTML_MARKERS.items():
            if not re.search(pattern, text):
                failures.append(f"{rel}: missing {name}")
        json_ld_matches = re.findall(r'<script type="application/ld\+json">(.+?)</script>', text, flags=re.S)
        if len(json_ld_matches) != 1:
            failures.append(f"{rel}: expected one JSON-LD script, found {len(json_ld_matches)}")
        for match in json_ld_matches:
            try:
                payload = json.loads(match)
            except json.JSONDecodeError as exc:
                failures.append(f"{rel}: invalid JSON-LD ({exc})")
                continue
            nodes = json_ld_nodes(payload)
            node_types = set()
            for node in nodes:
                value = node.get("@type")
                if isinstance(value, list):
                    node_types.update(str(item) for item in value)
                elif value:
                    node_types.add(str(value))
            if "FAQPage" in node_types:
                failures.append(f"{rel}: FAQPage JSON-LD is present")
            page_nodes = [node for node in nodes if node.get("@type") in ALLOWED_PAGE_TYPES]
            if not page_nodes:
                failures.append(f"{rel}: missing WebPage/CollectionPage/AboutPage JSON-LD node")
                continue
            if "WebSite" not in node_types:
                failures.append(f"{rel}: missing WebSite JSON-LD node")
            if "Organization" not in node_types:
                failures.append(f"{rel}: missing Organization JSON-LD node")
            if "BreadcrumbList" not in node_types:
                failures.append(f"{rel}: missing BreadcrumbList JSON-LD node")
            page_node = page_nodes[0]
            if not page_node.get("url") or not page_node.get("name") or not page_node.get("description"):
                failures.append(f"{rel}: page JSON-LD missing url, name, or description")
            if str(rel).replace("\\", "/") == "network/index.html":
                main_entity = page_node.get("mainEntity") or {}
                item_list = main_entity.get("itemListElement") or []
                if main_entity.get("@type") != "ItemList":
                    failures.append(f"{rel}: network JSON-LD mainEntity is not ItemList")
                if not item_list:
                    failures.append(f"{rel}: network JSON-LD ItemList is empty")
                metadata_path = SITE / "data" / "directory-metadata.json"
                if not metadata_path.exists():
                    failures.append("data/directory-metadata.json missing")
                else:
                    try:
                        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                    except json.JSONDecodeError as exc:
                        failures.append(f"data/directory-metadata.json invalid JSON ({exc})")
                    else:
                        expected_count = metadata.get("entry_count")
                        if main_entity.get("numberOfItems") != expected_count:
                            failures.append(f"{rel}: JSON-LD numberOfItems does not match directory metadata")
                        if len(item_list) != expected_count:
                            failures.append(f"{rel}: JSON-LD itemListElement count does not match directory metadata")
                        if expected_count != len(metadata.get("entries") or []):
                            failures.append("data/directory-metadata.json entry_count does not match entries length")

    sitemap = SITE / "sitemap.xml"
    robots = SITE / "robots.txt"
    if not sitemap.exists():
        failures.append("sitemap.xml missing")
    if not robots.exists():
        failures.append("robots.txt missing")
    if sitemap.exists():
        sitemap_text = sitemap.read_text(encoding="utf-8", errors="ignore")
        if "<loc>https://" not in sitemap_text or "<lastmod>" not in sitemap_text:
            failures.append("sitemap.xml missing loc or lastmod")
    if robots.exists() and "Sitemap:" not in robots.read_text(encoding="utf-8", errors="ignore"):
        failures.append("robots.txt missing Sitemap directive")

    if failures:
        for item in failures:
            print(f"FAIL: {item}")
        sys.exit(1)

    print(f"SEO static audit passed for {len(html_files)} HTML files.")


if __name__ == "__main__":
    main()
