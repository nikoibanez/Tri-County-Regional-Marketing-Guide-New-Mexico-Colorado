from __future__ import annotations

import hashlib
import html
import json
import os
import re
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None


ROOT = Path("review/attachments_20260620")
DOWNLOADS = Path.home() / "Downloads"
REPORT_PATH = DOWNLOADS / "Tri_County_Attachments_Incorporation_Audit.md"


REPORT_MARKERS = [
    "evidence",
    "verification",
    "not completed",
    "not implemented",
    "roadmap implementation",
    "constraints applied",
    "report",
    "objective",
    "why it matters",
    "why it needs checking",
    "no explicit",
    "best treated",
    "should",
]

MOJIBAKE_MARKERS = ["â€™", "â€“", "â€œ", "â€", "Â", "Ã", "ã€", "�"]


@dataclass
class HtmlAudit:
    rel: str
    bytes: int
    words: int
    headings: list[str]
    ids: set[str]
    internal_links: list[str]
    missing_anchors: list[str]
    asset_refs: list[str]
    missing_assets: list[str]
    report_markers: dict[str, int]
    mojibake: int
    sha: str


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def fs_path(path: Path) -> str:
    resolved = str(path.resolve())
    if os.name == "nt" and not resolved.startswith("\\\\?\\"):
        return "\\\\?\\" + resolved
    return resolved


def read_text(path: Path) -> str:
    with open(fs_path(path), "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def read_bytes(path: Path) -> bytes:
    with open(fs_path(path), "rb") as handle:
        return handle.read()


def file_size(path: Path) -> int:
    return os.stat(fs_path(path)).st_size


def file_exists(path: Path) -> bool:
    return os.path.exists(fs_path(path))


def clean_text(source: str) -> str:
    source = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", source, flags=re.I)
    source = re.sub(r"<[^>]+>", " ", source)
    return re.sub(r"\s+", " ", html.unescape(source)).strip()


def hash_file(path: Path) -> str:
    return hashlib.sha256(read_bytes(path)).hexdigest()


def audit_html(path: Path) -> HtmlAudit:
    source = read_text(path)
    markup = re.sub(r"<script[\s\S]*?</script>", " ", source, flags=re.I)
    text = clean_text(source)
    headings = []
    for tag in ("h1", "h2", "h3"):
        for match in re.finditer(fr"<{tag}\b[^>]*>([\s\S]*?)</{tag}>", markup, flags=re.I):
            title = clean_text(match.group(1))
            if title:
                headings.append(title)
    ids = set(re.findall(r'id="([^"]+)"', markup))
    hrefs = re.findall(r'href="([^"]+)"', markup)
    internal = [item[1:] for item in hrefs if item.startswith("#") and len(item) > 1]
    asset_refs = re.findall(r'(?:href|src)="([^"#][^"]*\.(?:css|js|png|jpg|jpeg|svg|webp|ico))"', markup, flags=re.I)
    asset_refs.extend(re.findall(r'<script\b[^>]*\bsrc="([^"#][^"]*\.js)"', source, flags=re.I))
    missing_assets = []
    for asset in asset_refs:
        if asset.startswith(("http://", "https://", "data:")):
            continue
        if not file_exists(path.parent / asset):
            missing_assets.append(asset)
    report_markers = {marker: len(re.findall(re.escape(marker), text, flags=re.I)) for marker in REPORT_MARKERS}
    mojibake = sum(text.count(marker) for marker in MOJIBAKE_MARKERS)
    return HtmlAudit(
        rel=rel(path),
        bytes=file_size(path),
        words=len(text.split()),
        headings=headings,
        ids=ids,
        internal_links=internal,
        missing_anchors=sorted(set(internal) - ids),
        asset_refs=asset_refs,
        missing_assets=sorted(set(missing_assets)),
        report_markers=report_markers,
        mojibake=mojibake,
        sha=hash_file(path)[:16],
    )


def md_outline(path: Path) -> dict:
    text = read_text(path)
    headings = [line.strip() for line in text.splitlines() if line.lstrip().startswith("#")]
    links = re.findall(r"https?://[^\s)>\]]+", text)
    tables = text.count("\n|")
    report_score = sum(len(re.findall(re.escape(marker), text, flags=re.I)) for marker in REPORT_MARKERS)
    mojibake = sum(text.count(marker) for marker in MOJIBAKE_MARKERS)
    return {
        "rel": rel(path),
        "bytes": file_size(path),
        "headings": headings[:18],
        "links": len(links),
        "tables": tables,
        "report_score": report_score,
        "mojibake": mojibake,
        "sha": hash_file(path)[:16],
        "snippet": re.sub(r"\s+", " ", text).strip()[:420],
    }


def pdf_outline(path: Path) -> dict:
    if PdfReader is None:
        return {"rel": rel(path), "pages": None, "snippet": "pypdf not available"}
    try:
        reader = PdfReader(fs_path(path))
    except FileNotFoundError:
        # Windows long paths can fail in very deep workspaces. Copying is overkill for
        # this report; the filename itself is enough if extraction fails.
        return {"rel": rel(path), "pages": None, "snippet": "Could not open due to path length/encoding."}
    text = ""
    for page in reader.pages[:4]:
        text += (page.extract_text() or "") + "\n"
    text = re.sub(r"\s+", " ", text).strip()
    meta = reader.metadata or {}
    return {
        "rel": rel(path),
        "bytes": file_size(path),
        "pages": len(reader.pages),
        "title": str(meta.get("/Title", "")),
        "author": str(meta.get("/Author", "")),
        "snippet": text[:600],
        "sha": hash_file(path)[:16],
    }


def svg_outline(path: Path) -> dict:
    source = read_text(path)
    view_box = re.search(r'viewBox="([^"]+)"', source)
    colors = Counter(re.findall(r"#[0-9a-fA-F]{3,8}", source))
    return {
        "rel": rel(path),
        "bytes": file_size(path),
        "viewBox": view_box.group(1) if view_box else "",
        "colors": [color for color, _ in colors.most_common(8)],
        "sha": hash_file(path)[:16],
    }


def zip_outline(path: Path) -> dict:
    with zipfile.ZipFile(fs_path(path)) as zf:
        entries = sorted(zf.infolist(), key=lambda item: item.filename.lower())
        return {
            "rel": rel(path),
            "bytes": file_size(path),
            "entries": [{"name": item.filename, "bytes": item.file_size} for item in entries[:40]],
            "entry_count": len(entries),
            "sha": hash_file(path)[:16],
        }


def resource_dataset_summary() -> dict:
    dataset = DOWNLOADS / "tri_county_persona_resources.json"
    if not dataset.exists():
        return {"exists": False}
    rows = json.loads(dataset.read_text(encoding="utf-8"))
    return {
        "exists": True,
        "rows": len(rows),
        "counties": Counter(row.get("County", "") for row in rows).most_common(),
        "types": Counter(row.get("Resource_Type", "") for row in rows).most_common(),
        "personas": Counter(row.get("Primary_Persona", "") for row in rows).most_common(),
        "sections": Counter(row.get("Source_Section", "") for row in rows).most_common(12),
    }


def table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    out = []
    for idx, row in enumerate(rows):
        out.append("| " + " | ".join(str(value).ljust(widths[i]) for i, value in enumerate(row)) + " |")
        if idx == 0:
            out.append("| " + " | ".join("-" * widths[i] for i in range(len(row))) + " |")
    return "\n".join(out)


def main() -> None:
    htmls = [audit_html(path) for path in sorted(ROOT.rglob("*.html"))]
    markdowns = [md_outline(path) for path in sorted(ROOT.rglob("*.md"))]
    pdfs = [pdf_outline(path) for path in sorted(ROOT.rglob("*.pdf"))]
    svgs = [svg_outline(path) for path in sorted(ROOT.rglob("*.svg"))]
    zips = [zip_outline(path) for path in sorted(ROOT.rglob("*.zip"))]
    tomls = [path for path in sorted(ROOT.rglob("*.toml"))]
    jsons = [path for path in sorted(ROOT.rglob("*.json"))]
    resources = resource_dataset_summary()

    lines: list[str] = []
    lines.append("# Tri-County Attachment Bundle Incorporation Audit")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Bundle reviewed: `{ROOT}`")
    lines.append("")
    lines.append("## Executive Read")
    lines.append("")
    lines.append("- The attachment bundle contains two different public-site instincts: a small three-path homepage concept and a large single-file guide/deploy draft.")
    lines.append("- The small `index.html` has the best public-facing information architecture, but it references missing `styles.css` and `script.js`, so it is not deploy-ready as-is.")
    lines.append("- The nested Netlify upload is technically closer to deployable, but it preserves too much long-report structure, has mojibake/encoding artifacts, and reads less like a polished regional growth site.")
    lines.append("- The best next draft should combine the small draft's three-path structure with the current 456-resource dataset and the refined visual system from the latest guide.")
    lines.append("- Public pages should remove internal research/status language and move methodology, verification, and caveats to an About/Method page.")
    lines.append("")
    lines.append("## HTML Files")
    html_rows = [["File", "Bytes", "Words", "Headings", "Missing assets", "Missing anchors", "Report markers", "Mojibake"]]
    for item in htmls:
        html_rows.append(
            [
                item.rel,
                f"{item.bytes:,}",
                f"{item.words:,}",
                str(len(item.headings)),
                ", ".join(item.missing_assets) or "-",
                ", ".join(item.missing_anchors) or "-",
                str(sum(item.report_markers.values())),
                str(item.mojibake),
            ]
        )
    lines.append(table(html_rows))
    lines.append("")
    for item in htmls:
        lines.append(f"### {item.rel}")
        lines.append("")
        lines.append(f"- SHA-256 prefix: `{item.sha}`")
        lines.append(f"- First headings: {', '.join('`' + h[:90] + '`' for h in item.headings[:10])}")
        if item.missing_assets:
            lines.append(f"- Technical issue: references missing assets: {', '.join('`' + a + '`' for a in item.missing_assets)}.")
        if item.missing_anchors:
            lines.append(f"- Technical issue: missing internal anchor targets: {', '.join('`' + a + '`' for a in item.missing_anchors)}.")
        if item.mojibake:
            lines.append(f"- Encoding issue: {item.mojibake} mojibake markers found.")
        top_markers = [(k, v) for k, v in item.report_markers.items() if v]
        if top_markers:
            lines.append("- Public-voice risk markers: " + ", ".join(f"`{k}` {v}" for k, v in top_markers[:10]) + ".")
        lines.append("")

    lines.append("## Markdown Notes")
    md_rows = [["File", "Bytes", "Headings", "Links", "Tables", "Report score", "Mojibake", "Use"]]
    for item in markdowns:
        use = "public source"
        name = item["rel"]
        if "Implementation_Status" in name or name.endswith("agents.md"):
            use = "internal only"
        elif "directory_feature" in name or "posting" in name or "regional_business" in name:
            use = "rewrite into public pages"
        elif "raton_businesses" in name:
            use = "data cleanup source"
        md_rows.append([name, f"{item['bytes']:,}", str(len(item["headings"])), str(item["links"]), str(item["tables"]), str(item["report_score"]), str(item["mojibake"]), use])
    lines.append(table(md_rows))
    lines.append("")
    for item in markdowns:
        lines.append(f"### {item['rel']}")
        lines.append("")
        if item["headings"]:
            lines.append("- Outline: " + "; ".join(f"`{heading}`" for heading in item["headings"][:10]))
        lines.append(f"- Snippet: {item['snippet']}")
        lines.append("")

    lines.append("## PDFs")
    pdf_rows = [["File", "Bytes", "Pages", "Title", "Use"]]
    for item in pdfs:
        use = "implementation/source pack"
        if "Regional_Directory" in item["rel"]:
            use = "raw directory source; rewrite before public use"
        pdf_rows.append([item["rel"], f"{item.get('bytes', 0):,}", str(item.get("pages", "-")), item.get("title", "")[:60], use])
    lines.append(table(pdf_rows))
    lines.append("")
    for item in pdfs:
        lines.append(f"### {item['rel']}")
        lines.append("")
        lines.append(f"- Snippet: {item.get('snippet', '')}")
        lines.append("")

    lines.append("## SVG Assets")
    lines.append("")
    lines.append(f"- SVG files found: {len(svgs)}.")
    svg_groups = Counter(Path(item["rel"]).name for item in svgs)
    duplicates = [name for name, count in svg_groups.items() if count > 1]
    lines.append(f"- Duplicate SVG asset names across root/nested packages: {', '.join('`' + name + '`' for name in duplicates) or 'none'}.")
    lines.append("- Recommendation: keep the latest refined SVG set, but use them as supporting illustrations, not as section filler.")
    lines.append("")

    lines.append("## ZIP Packages")
    zip_rows = [["File", "Bytes", "Entries", "Use"]]
    for item in zips:
        use = "source package"
        if "netlify-upload" in item["rel"]:
            use = "deployment draft; harvest structure/assets"
        elif "super_eukarya" in item["rel"]:
            use = "visual asset package"
        zip_rows.append([item["rel"], f"{item['bytes']:,}", str(item["entry_count"]), use])
    lines.append(table(zip_rows))
    lines.append("")

    lines.append("## Deployment Configs")
    lines.append("")
    for path in tomls:
        text = read_text(path).strip()
        lines.append(f"### {rel(path)}")
        lines.append("```toml")
        lines.append(text[:1200])
        lines.append("```")
        lines.append("")

    lines.append("## JSON/Manifest Files")
    lines.append("")
    for path in jsons:
        try:
            data = json.loads(read_text(path))
            descriptor = list(data.keys()) if isinstance(data, dict) else f"{len(data)} rows"
        except Exception as exc:
            descriptor = f"unreadable JSON: {exc}"
        lines.append(f"- `{rel(path)}`: {descriptor}")
    lines.append("")

    lines.append("## Current 456-Resource Dataset Available Outside ZIP")
    lines.append("")
    if resources["exists"]:
        lines.append(f"- Rows: {resources['rows']}")
        lines.append("- Counties: " + ", ".join(f"{name or 'blank'} {count}" for name, count in resources["counties"]))
        lines.append("- Resource types: " + ", ".join(f"{name or 'blank'} {count}" for name, count in resources["types"]))
        lines.append("- Primary personas: " + ", ".join(f"{name or 'blank'} {count}" for name, count in resources["personas"]))
        lines.append("- Major source sections: " + ", ".join(f"{name} {count}" for name, count in resources["sections"]))
    else:
        lines.append("- Dataset not found.")
    lines.append("")

    lines.append("## Incorporation Plan")
    lines.append("")
    lines.append("### Keep")
    lines.append("")
    lines.append("- The three-path homepage instinct from the small `index.html`: users should choose what they are trying to do before seeing the full inventory.")
    lines.append("- The regional-business, posting-space, county-matrix, and directory-feature markdown notes as content sources.")
    lines.append("- The refined SVG visual system and the gentler color direction, with fewer diagrams per page.")
    lines.append("- The 456-resource dataset from the latest guide as the working directory/data source.")
    lines.append("- The Netlify static-site assumption: no backend is needed for the next polished draft.")
    lines.append("")
    lines.append("### Rewrite")
    lines.append("")
    lines.append("- Replace `Advice / Resources / Data` with public-facing path labels such as `Plan Your Growth`, `Find the Network`, and `Understand the Region`.")
    lines.append("- Rewrite research-note language into action copy. Example: `No explicit newsletter evidence found` becomes `Best used as a directory listing, not a newsletter channel.`")
    lines.append("- Turn business examples into local navigation cues: `where to find customers`, `where to post`, `who can amplify`, `who can mentor`, `where creative work fits`.")
    lines.append("- Convert the directory into multi-page browsing plus one searchable/filterable directory page.")
    lines.append("")
    lines.append("### Do Not Publish As Main Copy")
    lines.append("")
    lines.append("- `Tri-County_Regional_Guide_Implementation_Status.md` and `agents.md`; keep them internal.")
    lines.append("- Any `not completed`, `evidence`, `verification`, or `roadmap` copy on public pages.")
    lines.append("- Mojibake-affected text from `raton_businesses.md` or the nested guide until encoding is cleaned.")
    lines.append("- The outer small `index.html` as-is, because it references missing CSS/JS.")
    lines.append("")
    lines.append("### Next Draft Shape")
    lines.append("")
    lines.append("```text")
    lines.append("/")
    lines.append("  index.html                  Home: regional connection + three paths")
    lines.append("/plan/")
    lines.append("  index.html                  Growth/advice playbooks")
    lines.append("/network/")
    lines.append("  index.html                  Searchable resources and partners")
    lines.append("/region/")
    lines.append("  index.html                  County signals, posting channels, local data")
    lines.append("/counties/")
    lines.append("  colfax.html")
    lines.append("  las-animas.html")
    lines.append("  huerfano.html")
    lines.append("/templates/")
    lines.append("  index.html                  Outreach scripts, posting checklist, referral blurbs")
    lines.append("/about/")
    lines.append("  index.html                  Scope, method, update/verification rules")
    lines.append("/assets/")
    lines.append("  css/site.css")
    lines.append("  js/site.js")
    lines.append("  svg/")
    lines.append("/data/")
    lines.append("  resources.json")
    lines.append("```")
    lines.append("")
    lines.append("## Open Clarifications Before Build")
    lines.append("")
    lines.append("1. Final site name: `Tri-County Regional Marketing Guide`, `Tri-County Growth Guide`, or another title.")
    lines.append("2. Path labels: use the warmer labels above or keep literal `Advice / Resources / Data`.")
    lines.append("3. Public credit posture: whether to show Raton/Super Eukarya logos only in the footer or on About as well.")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(REPORT_PATH)


if __name__ == "__main__":
    main()
