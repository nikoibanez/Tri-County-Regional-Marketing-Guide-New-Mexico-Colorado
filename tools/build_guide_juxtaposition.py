from __future__ import annotations

import hashlib
import html
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - only used when bundled PDF support is absent.
    PdfReader = None


DOWNLOADS = Path.home() / "Downloads"
OUTPUT = DOWNLOADS / "Tri_County_Guide_Version_Juxtaposition.html"


@dataclass(frozen=True)
class FileRef:
    key: str
    label: str
    path: Path
    role: str
    kind: str
    preview: bool = False


FILES = [
    FileRef(
        "current",
        "Current interactive guide",
        DOWNLOADS / "Tri_County_Regional_Marketing_Guide_Interactive.html",
        "Working/public HTML",
        "HTML",
        True,
    ),
    FileRef(
        "colfax_alias",
        "Colfax integrated guide",
        DOWNLOADS / "tri_county_guide_colfax_inventory_integrated.html",
        "Byte-identical mirror of current guide",
        "HTML",
        False,
    ),
    FileRef(
        "backup",
        "Pre-persona backup",
        DOWNLOADS / "tri_county_guide_colfax_inventory_integrated.backup_before_persona_20260619.html",
        "Historical HTML snapshot",
        "HTML",
        True,
    ),
    FileRef(
        "send",
        "SEND draft",
        DOWNLOADS / "Tri_County_Regional_Marketing_Guide_Interactive_SEND (1).html",
        "Earlier share/send draft",
        "HTML",
        True,
    ),
    FileRef(
        "package",
        "Download package",
        DOWNLOADS / "Tri_County_Regional_Marketing_Guide_Download_Package.zip",
        "Distribution bundle",
        "ZIP",
    ),
    FileRef(
        "visuals",
        "Super Eukarya visuals package",
        DOWNLOADS / "super_eukarya_site_visuals_and_codex_notes.zip",
        "Design/source asset package",
        "ZIP",
    ),
    FileRef(
        "brief",
        "Agentic AI implementation brief",
        DOWNLOADS / "agentic_ai_landing_site_implementation_brief.pdf",
        "Method/source PDF",
        "PDF",
    ),
    FileRef(
        "huerfano",
        "Huerfano outreach inventory",
        DOWNLOADS / "Huerfano County Business Inventory and Outreach Targets Report.pdf",
        "County source PDF",
        "PDF",
    ),
]


FEATURE_PATTERNS = {
    "Animated mountain banner": "mountain-banner",
    "Footer brand/logo block": "guide-brand-footer",
    "Embedded PNG logos": "data:image/png",
    "Inline SVG figures": "<svg",
    "Persona/task routing": "persona",
    "Huerfano content": "Huerfano",
    "Las Animas content": "Las Animas",
    "Colfax content": "Colfax",
    "Templates section": "templates",
    "Validation language": "Validation",
}


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def file_meta(path: Path) -> dict:
    raw = path.read_bytes()
    stat = path.stat()
    return {
        "bytes": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def html_metrics(path: Path) -> dict:
    source = path.read_text(encoding="utf-8", errors="replace")
    body_text = clean_text(source)
    headings: list[tuple[str, str]] = []
    for tag in ("h1", "h2", "h3"):
        for match in re.finditer(fr"<{tag}\b[^>]*>([\s\S]*?)</{tag}>", source, flags=re.I):
            heading = clean_text(match.group(1))
            if heading:
                headings.append((tag, heading))

    features = {}
    for label, marker in FEATURE_PATTERNS.items():
        haystack = source.lower() if marker.startswith("<") else source
        needle = marker.lower() if marker.startswith("<") else marker
        features[label] = haystack.count(needle)

    return {
        "chars": len(source),
        "word_count": len(body_text.split()),
        "headings": headings,
        "heading_count": len(headings),
        "h2": [text for tag, text in headings if tag == "h2"],
        "ids": sorted(set(re.findall(r'id="([^"]+)"', source))),
        "svg_count": source.lower().count("<svg"),
        "img_count": source.lower().count("<img"),
        "table_count": source.lower().count("<table"),
        "feature_counts": features,
    }


def zip_summary(path: Path) -> list[dict]:
    with zipfile.ZipFile(path) as archive:
        return [
            {
                "name": item.filename,
                "bytes": item.file_size,
                "compressed": item.compress_size,
            }
            for item in sorted(archive.infolist(), key=lambda item: item.filename.lower())
        ]


def pdf_summary(path: Path) -> dict:
    if PdfReader is None:
        return {"pages": None, "title": "", "snippet": "PDF extraction support was not available."}

    reader = PdfReader(str(path))
    text = ""
    for page in reader.pages[:3]:
        try:
            text += (page.extract_text() or "") + "\n"
        except Exception as exc:
            text += f"[extract error: {exc}]\n"
    text = re.sub(r"\s+", " ", text).strip()
    meta = reader.metadata or {}
    return {
        "pages": len(reader.pages),
        "title": str(meta.get("/Title", "")),
        "author": str(meta.get("/Author", "")),
        "snippet": text[:950],
    }


def pct_delta(new: int, old: int) -> str:
    if old == 0:
        return "n/a"
    change = ((new - old) / old) * 100
    return f"{change:+.1f}%"


def html_escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def format_bytes(value: int) -> str:
    if value >= 1024 * 1024:
        return f"{value / (1024 * 1024):.2f} MB"
    if value >= 1024:
        return f"{value / 1024:.1f} KB"
    return f"{value} B"


def local_href(path: Path) -> str:
    return quote(path.name)


def build() -> None:
    records = []
    for ref in FILES:
        if not ref.path.exists():
            records.append({"ref": ref, "exists": False})
            continue

        record = {"ref": ref, "exists": True, "meta": file_meta(ref.path)}
        if ref.kind == "HTML":
            record["html"] = html_metrics(ref.path)
        elif ref.kind == "ZIP":
            record["zip"] = zip_summary(ref.path)
        elif ref.kind == "PDF":
            record["pdf"] = pdf_summary(ref.path)
        records.append(record)

    html_records = [record for record in records if record.get("exists") and record["ref"].kind == "HTML"]
    current = next(record for record in html_records if record["ref"].key == "current")
    backup = next(record for record in html_records if record["ref"].key == "backup")
    send = next(record for record in html_records if record["ref"].key == "send")
    colfax = next(record for record in html_records if record["ref"].key == "colfax_alias")

    h2_current = set(current["html"]["h2"])
    h2_backup = set(backup["html"]["h2"])
    h2_send = set(send["html"]["h2"])

    additions_since_send = sorted(h2_current - h2_send)
    additions_since_backup = sorted(h2_current - h2_backup)
    dropped_since_send = sorted(h2_send - h2_current)
    duplicate_current = current["meta"]["sha256"] == colfax["meta"]["sha256"]

    rows = []
    for record in records:
        ref = record["ref"]
        if not record["exists"]:
            rows.append(
                f"<tr><td>{html_escape(ref.label)}</td><td>{html_escape(ref.kind)}</td><td colspan='6'>Missing at {html_escape(ref.path)}</td></tr>"
            )
            continue

        meta = record["meta"]
        html_bits = ""
        if "html" in record:
            metrics = record["html"]
            html_bits = (
                f"{metrics['word_count']:,} words; "
                f"{metrics['heading_count']} headings; "
                f"{metrics['svg_count']} SVG; {metrics['img_count']} images; "
                f"{metrics['table_count']} tables"
            )
        elif "zip" in record:
            html_bits = f"{len(record['zip'])} files in package"
        elif "pdf" in record:
            pdf = record["pdf"]
            html_bits = f"{pdf.get('pages') or 'unknown'} pages; {html_escape(pdf.get('title') or ref.label)}"

        rows.append(
            "<tr>"
            f"<td><a href='{local_href(ref.path)}'>{html_escape(ref.label)}</a><span>{html_escape(ref.role)}</span></td>"
            f"<td>{html_escape(ref.kind)}</td>"
            f"<td>{format_bytes(meta['bytes'])}</td>"
            f"<td>{html_escape(meta['modified'])}</td>"
            f"<td>{html_escape(html_bits)}</td>"
            f"<td><code>{html_escape(meta['sha256'][:16])}</code></td>"
            "</tr>"
        )

    feature_rows = []
    html_order = [send, backup, current]
    for feature in FEATURE_PATTERNS:
        cells = []
        for record in html_order:
            count = record["html"]["feature_counts"][feature]
            cells.append("<td class='yes'>yes</td>" if count else "<td class='no'>no</td>")
        feature_rows.append(f"<tr><td>{html_escape(feature)}</td>{''.join(cells)}</tr>")

    preview_cards = []
    for record in [send, backup, current]:
        ref = record["ref"]
        meta = record["meta"]
        metrics = record["html"]
        preview_cards.append(
            "<section class='preview-panel'>"
            f"<div class='preview-head'><h3>{html_escape(ref.label)}</h3>"
            f"<p>{html_escape(ref.role)} · {format_bytes(meta['bytes'])} · {metrics['word_count']:,} words</p></div>"
            f"<iframe title='{html_escape(ref.label)} preview' src='{local_href(ref.path)}#top' loading='lazy'></iframe>"
            f"<a class='open-link' href='{local_href(ref.path)}'>Open full version</a>"
            "</section>"
        )

    zip_sections = []
    for record in records:
        if "zip" not in record:
            continue
        items = "\n".join(
            f"<tr><td>{html_escape(item['name'])}</td><td>{format_bytes(item['bytes'])}</td><td>{format_bytes(item['compressed'])}</td></tr>"
            for item in record["zip"]
        )
        zip_sections.append(
            f"<section><h3>{html_escape(record['ref'].label)}</h3>"
            f"<p>{html_escape(record['ref'].role)}.</p>"
            "<div class='table-wrap'><table><thead><tr><th>Package entry</th><th>Bytes</th><th>Compressed</th></tr></thead>"
            f"<tbody>{items}</tbody></table></div></section>"
        )

    pdf_sections = []
    for record in records:
        if "pdf" not in record:
            continue
        pdf = record["pdf"]
        pdf_sections.append(
            "<section class='source-note'>"
            f"<h3>{html_escape(record['ref'].label)}</h3>"
            f"<p><strong>{html_escape(pdf.get('title') or record['ref'].label)}</strong>"
            f"{' · ' + html_escape(pdf.get('author')) if pdf.get('author') else ''}"
            f" · {html_escape(pdf.get('pages') or 'unknown')} pages</p>"
            f"<p>{html_escape(pdf.get('snippet', ''))}</p>"
            f"<a class='open-link' href='{local_href(record['ref'].path)}'>Open source PDF</a>"
            "</section>"
        )

    current_words = current["html"]["word_count"]
    send_words = send["html"]["word_count"]
    backup_words = backup["html"]["word_count"]

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "duplicate_current_colfax": duplicate_current,
        "current_sha256": current["meta"]["sha256"],
        "records": [
            {
                "key": record["ref"].key,
                "label": record["ref"].label,
                "path": str(record["ref"].path),
                "exists": record["exists"],
                "meta": record.get("meta"),
            }
            for record in records
        ],
    }

    html_out = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Tri-County Guide Version Juxtaposition</title>
<style>
:root {{
  --ink: #172332;
  --muted: #5f6975;
  --paper: #f8f5ed;
  --panel: rgba(255,255,255,.78);
  --line: rgba(23,35,50,.14);
  --blue: #617cae;
  --teal: #5faaa8;
  --gold: #b4a066;
  --rose: #bf7767;
  --shadow: 0 18px 48px rgba(30, 43, 58, .12);
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--ink);
  background:
    linear-gradient(180deg, rgba(97,124,174,.12), transparent 28rem),
    radial-gradient(circle at 18% 12%, rgba(95,170,168,.18), transparent 24rem),
    var(--paper);
  letter-spacing: 0;
}}
a {{ color: #335f93; text-decoration-thickness: .08em; text-underline-offset: .2em; }}
a, strong, code {{ overflow-wrap: anywhere; word-break: break-word; }}
header, main {{ width: min(1180px, calc(100% - 32px)); margin: 0 auto; }}
header {{ padding: 42px 0 18px; }}
.eyebrow {{ color: var(--blue); font-size: 12px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }}
h1 {{ margin: 10px 0 12px; font-size: clamp(32px, 5vw, 64px); line-height: .98; letter-spacing: 0; max-width: 980px; }}
h2 {{ margin: 0 0 14px; font-size: clamp(24px, 3vw, 36px); letter-spacing: 0; }}
h3 {{ margin: 0 0 8px; font-size: 18px; letter-spacing: 0; }}
p {{ line-height: 1.55; }}
.lead {{ max-width: 900px; color: var(--muted); font-size: 18px; }}
.summary-grid, .preview-grid, .source-grid {{ display: grid; gap: 16px; }}
.summary-grid {{ grid-template-columns: repeat(4, minmax(0, 1fr)); margin: 28px 0; }}
.metric, section, .preview-panel {{
  background: var(--panel);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  backdrop-filter: blur(10px);
  border-radius: 8px;
  min-width: 0;
}}
.metric {{ padding: 18px; }}
.metric strong {{ display: block; font-size: 26px; margin-bottom: 4px; }}
.metric span {{ color: var(--muted); font-size: 13px; }}
section {{ padding: 22px; margin: 18px 0; }}
.callout {{ border-left: 5px solid rgba(95,170,168,.72); }}
.lineage {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-top: 16px; }}
.stage {{ padding: 16px; border: 1px solid var(--line); background: rgba(255,255,255,.52); border-radius: 8px; }}
.stage b {{ display: block; margin-bottom: 4px; }}
.stage small {{ color: var(--muted); }}
.table-wrap {{ overflow-x: auto; overflow-y: hidden; max-width: 100%; border: 1px solid var(--line); border-radius: 8px; background: rgba(255,255,255,.55); contain: inline-size; }}
table {{ width: 100%; border-collapse: collapse; min-width: 760px; }}
th, td {{ padding: 12px 14px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
th {{ font-size: 12px; text-transform: uppercase; color: var(--muted); background: rgba(255,255,255,.44); }}
td span {{ display: block; color: var(--muted); font-size: 12px; margin-top: 2px; }}
code {{ font-family: "SFMono-Regular", Consolas, monospace; font-size: 12px; color: #4a5460; }}
.yes {{ color: #236f61; font-weight: 800; }}
.no {{ color: #8c4e44; font-weight: 800; }}
.preview-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
.preview-panel {{ overflow: hidden; padding: 0; margin: 0; }}
.preview-head {{ padding: 16px 16px 12px; border-bottom: 1px solid var(--line); min-height: 96px; }}
.preview-head p {{ margin: 0; color: var(--muted); font-size: 13px; }}
iframe {{ width: 100%; height: 520px; border: 0; background: white; display: block; }}
.open-link {{ display: inline-block; margin: 13px 16px 16px; font-weight: 700; }}
.diff-list {{ columns: 2 320px; padding-left: 18px; }}
.diff-list li {{ break-inside: avoid; margin: 0 0 8px; }}
.source-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
.source-note {{ margin: 0; }}
footer {{ width: min(1180px, calc(100% - 32px)); margin: 30px auto; color: var(--muted); font-size: 13px; }}
@media (max-width: 950px) {{
  .summary-grid, .preview-grid, .source-grid, .lineage {{ grid-template-columns: 1fr; }}
  iframe {{ height: 440px; }}
}}
@media (max-width: 520px) {{
  header, main, footer {{ width: min(100% - 20px, 1180px); }}
  section {{ padding: 18px; }}
  table {{ min-width: 640px; }}
}}
</style>
</head>
<body>
<header>
  <div class="eyebrow">Tri-County Guide · Version Juxtaposition</div>
  <h1>Three real guide states, one current public package.</h1>
  <p class="lead">This page compares the guide files in Downloads, separates finished HTML versions from source/input files, and makes the lineage visible without relying on filenames alone.</p>
  <div class="summary-grid">
    <div class="metric"><strong>{current_words:,}</strong><span>words in current guide</span></div>
    <div class="metric"><strong>{pct_delta(current_words, send_words)}</strong><span>word-count change from SEND draft</span></div>
    <div class="metric"><strong>{current['html']['svg_count']}</strong><span>inline SVG/animated figure surfaces in current guide</span></div>
    <div class="metric"><strong>{'yes' if duplicate_current else 'no'}</strong><span>current and Colfax-integrated files are byte-identical</span></div>
  </div>
</header>
<main>
  <section class="callout">
    <h2>Bottom Line</h2>
    <p><strong>The current public guide is <a href="{local_href(current['ref'].path)}">Tri_County_Regional_Marketing_Guide_Interactive.html</a>.</strong> The file named <a href="{local_href(colfax['ref'].path)}">tri_county_guide_colfax_inventory_integrated.html</a> is currently an exact byte-for-byte mirror of it, with the same SHA-256 hash.</p>
    <p>The older SEND draft is the leanest version; the pre-persona backup is the transitional version; the current build is the distributable version with softened visuals, the animated mountain/cloud banner, embedded footer logos, full source-backed persona resources, and packaged CSV/JSON/validation files.</p>
  </section>

  <section>
    <h2>Lineage</h2>
    <div class="lineage">
      <div class="stage"><b>1. SEND draft</b><small>Early shareable HTML · {send_words:,} words · {send['html']['heading_count']} headings</small><p>Core guide content, county/resource sections, and tables, but no refined SVG system or current landing treatment.</p></div>
      <div class="stage"><b>2. Pre-persona backup</b><small>Transitional HTML · {backup_words:,} words · {pct_delta(backup_words, send_words)} from SEND</small><p>Adds the utilitarian/persona routing frame, implementation-method sections, and early SVG figures.</p></div>
      <div class="stage"><b>3. Current interactive guide</b><small>Public/distribution HTML · {current_words:,} words · {pct_delta(current_words, backup_words)} from backup</small><p>Adds the gentler visual system, animated banner, footer logos, refreshed SVGs, and packaged download assets.</p></div>
    </div>
  </section>

  <section>
    <h2>File Matrix</h2>
    <div class="table-wrap">
      <table>
        <thead><tr><th>File</th><th>Kind</th><th>Size</th><th>Modified</th><th>What it contains</th><th>SHA-256 prefix</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2>Feature Juxtaposition</h2>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Feature marker</th><th>SEND draft</th><th>Pre-persona backup</th><th>Current guide</th></tr></thead>
        <tbody>{''.join(feature_rows)}</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2>Headings Added Since SEND</h2>
    <p>These are the most visible structural additions present in the current guide but absent from the SEND draft.</p>
    <ul class="diff-list">{''.join(f'<li>{html_escape(item)}</li>' for item in additions_since_send[:36])}</ul>
  </section>

  <section>
    <h2>Headings Added After Backup</h2>
    <p>This is intentionally small: the last stage was mainly visual packaging and distribution polish, not a wholesale content rewrite.</p>
    <ul>{''.join(f'<li>{html_escape(item)}</li>' for item in additions_since_backup) or '<li>No major new H2 heading labels detected.</li>'}</ul>
  </section>

  <section>
    <h2>Headings Dropped Since SEND</h2>
    <p>These SEND-era H2 labels are not present as H2 labels in the current guide. Some content may have been renamed, merged, or moved under newer structure.</p>
    <ul class="diff-list">{''.join(f'<li>{html_escape(item)}</li>' for item in dropped_since_send[:36]) or '<li>No dropped H2 labels detected.</li>'}</ul>
  </section>

  <section>
    <h2>Side-by-Side Previews</h2>
    <div class="preview-grid">{''.join(preview_cards)}</div>
  </section>

  <section>
    <h2>Distribution Packages</h2>
    {''.join(zip_sections)}
  </section>

  <section>
    <h2>Source Documents</h2>
    <div class="source-grid">{''.join(pdf_sections)}</div>
  </section>
</main>
<footer>
  Generated {html_escape(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}. Raw comparison manifest:
  <script type="application/json" id="comparison-data">{html_escape(json.dumps(payload, indent=2))}</script>
</footer>
</body>
</html>
"""

    OUTPUT.write_text(html_out, encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    build()
