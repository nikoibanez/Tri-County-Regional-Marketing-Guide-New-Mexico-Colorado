from __future__ import annotations

import hashlib
import html
import json
import os
import re
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None


WORKSPACE = Path.cwd()
DOWNLOADS = Path.home() / "Downloads"
OUT_DIR = DOWNLOADS / "tri_county_reaudit"
OUT_DIR.mkdir(parents=True, exist_ok=True)


UPLOADS = [
    ("roadmap_pdf", "Implementation roadmap and agentic prompts", DOWNLOADS / "Implementation_Roadmap_and_Agentic_AI_Prompts_for_Regional_Guide_Transformation.pdf", "source-method"),
    ("colfax_integrated_html", "Colfax integrated/current mirror", DOWNLOADS / "tri_county_guide_colfax_inventory_integrated.html", "guide-html"),
    ("las_animas_pdf", "Las Animas outreach inventory", DOWNLOADS / "Las Animas County Outreach and Visibility Inventory.pdf", "county-source"),
    ("huerfano_pdf", "Huerfano outreach inventory", DOWNLOADS / "Huerfano County Business Inventory and Outreach Targets Report.pdf", "county-source"),
    ("agentic_brief_pdf", "Agentic landing-site brief", DOWNLOADS / "agentic_ai_landing_site_implementation_brief.pdf", "source-method"),
    ("agentic_brief_txt", "Agentic landing-site brief extracted text", DOWNLOADS / "agentic_ai_landing_site_implementation_brief_extracted.txt", "source-method"),
    ("super_eukarya_zip", "Super Eukarya visuals package", DOWNLOADS / "super_eukarya_site_visuals_and_codex_notes.zip", "visual-assets"),
    ("download_package_zip", "Current guide download package", DOWNLOADS / "Tri_County_Regional_Marketing_Guide_Download_Package.zip", "distribution"),
    ("current_interactive_html", "Current interactive guide", DOWNLOADS / "Tri_County_Regional_Marketing_Guide_Interactive.html", "guide-html"),
    ("pre_persona_backup_html", "Pre-persona backup", DOWNLOADS / "tri_county_guide_colfax_inventory_integrated.backup_before_persona_20260619.html", "guide-html"),
    ("attachments_zip", "Giant attachments bundle", DOWNLOADS / "attachments.zip", "bundle"),
    ("send_html", "SEND draft", DOWNLOADS / "Tri_County_Regional_Marketing_Guide_Interactive_SEND (1).html", "guide-html"),
]

DERIVED = [
    ("persona_json", "456-resource JSON", DOWNLOADS / "tri_county_persona_resources.json", "structured-data"),
    ("persona_csv", "456-resource CSV", DOWNLOADS / "tri_county_persona_resources.csv", "structured-data"),
    ("validation_report", "Validation report", DOWNLOADS / "Validation_Report.md", "qa"),
    ("juxtaposition_html", "Version juxtaposition", DOWNLOADS / "Tri_County_Guide_Version_Juxtaposition.html", "review-artifact"),
    ("attachment_audit_md", "Attachment incorporation audit", DOWNLOADS / "Tri_County_Attachments_Incorporation_Audit.md", "review-artifact"),
]

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
    "currently",
]

MOJIBAKE_MARKERS = ["â€™", "â€“", "â€œ", "â€", "Â", "Ã", "ã€", "�", "ﬁ", "ﬃ"]


def fs_path(path: Path) -> str:
    resolved = str(path.resolve())
    if os.name == "nt" and not resolved.startswith("\\\\?\\"):
        return "\\\\?\\" + resolved
    return resolved


def read_bytes(path: Path) -> bytes:
    with open(fs_path(path), "rb") as handle:
        return handle.read()


def read_text(path: Path) -> str:
    with open(fs_path(path), "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def size(path: Path) -> int:
    return os.stat(fs_path(path)).st_size


def sha16(path: Path) -> str:
    return hashlib.sha256(read_bytes(path)).hexdigest()[:16]


def clean_html(source: str) -> str:
    no_script = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", source, flags=re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", no_script))).strip()


def text_stats(text: str) -> dict:
    return {
        "words": len(text.split()),
        "report_marker_count": sum(len(re.findall(re.escape(marker), text, flags=re.I)) for marker in REPORT_MARKERS),
        "mojibake_marker_count": sum(text.count(marker) for marker in MOJIBAKE_MARKERS),
    }


def headings_from_html(source: str) -> list[str]:
    markup = re.sub(r"<script[\s\S]*?</script>", " ", source, flags=re.I)
    headings = []
    for tag in ("h1", "h2", "h3"):
        for match in re.finditer(fr"<{tag}\b[^>]*>([\s\S]*?)</{tag}>", markup, flags=re.I):
            text = clean_html(match.group(1))
            if text:
                headings.append(text)
    return headings


def pdf_text(path: Path) -> tuple[int | None, str, str]:
    if PdfReader is None:
        return None, "", "PDF extraction unavailable"
    reader = PdfReader(fs_path(path))
    text = ""
    for page in reader.pages[:5]:
        text += (page.extract_text() or "") + "\n"
    meta = reader.metadata or {}
    return len(reader.pages), str(meta.get("/Title", "")), re.sub(r"\s+", " ", text).strip()


def classify_decision(key: str, role: str, path: Path, stats: dict) -> tuple[str, str]:
    name = path.name.lower()
    if role == "bundle":
        return "harvest-and-rebuild", "Use as source ecosystem; do not publish raw."
    if role == "distribution":
        return "reference-current-package", "Use for current asset parity and download expectations."
    if role == "visual-assets":
        return "keep-assets", "Use refined SVG/logo principles; avoid over-illustrating."
    if role == "structured-data":
        return "keep-as-data-source", "Use as the directory/data backbone."
    if role == "county-source":
        return "keep-as-source", "Use for county content, then rewrite public copy."
    if role == "source-method":
        return "use-internally", "Use for method and architecture; do not expose as public copy."
    if "send" in name:
        return "archive", "Earlier draft; keep only for lineage."
    if "backup" in name:
        return "archive-with-lessons", "Transitional draft; keep structure lessons only."
    if "interactive" in name or "integrated" in name:
        return "mine-for-content", "Use content/data but split into multi-page site."
    if role == "review-artifact":
        return "internal-only", "Review support artifact, not final public site."
    return "review", "Review before incorporation."


def audit_file(key: str, label: str, path: Path, role: str) -> dict:
    row = {
        "key": key,
        "label": label,
        "path": str(path),
        "role": role,
        "exists": path.exists(),
        "extension": path.suffix.lower().lstrip(".") or "none",
    }
    if not path.exists():
        row["decision"] = "missing"
        row["decision_note"] = "File was named in the thread but not found at the expected path."
        return row

    row["bytes"] = size(path)
    row["sha16"] = sha16(path)
    row["modified"] = datetime.fromtimestamp(os.stat(fs_path(path)).st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    ext = row["extension"]
    text = ""
    headings: list[str] = []

    if ext in {"html", "htm"}:
        source = read_text(path)
        text = clean_html(source)
        headings = headings_from_html(source)
        ids = set(re.findall(r'id="([^"]+)"', re.sub(r"<script[\s\S]*?</script>", " ", source, flags=re.I)))
        hrefs = re.findall(r'href="([^"]+)"', re.sub(r"<script[\s\S]*?</script>", " ", source, flags=re.I))
        row["missing_anchors"] = sorted(set(h[1:] for h in hrefs if h.startswith("#") and len(h) > 1) - ids)
        row["svg_count"] = source.lower().count("<svg")
        row["img_count"] = source.lower().count("<img")
        row["table_count"] = source.lower().count("<table")
    elif ext in {"md", "txt", "csv", "json", "toml", "svg"}:
        text = read_text(path)
        headings = [line.strip() for line in text.splitlines() if line.lstrip().startswith("#")]
        if ext == "zip":
            row["zip_entries"] = None
    elif ext == "pdf":
        pages, title, text = pdf_text(path)
        row["pages"] = pages
        row["pdf_title"] = title
    elif ext == "zip":
        with zipfile.ZipFile(fs_path(path)) as zf:
            infos = zf.infolist()
            row["zip_entries"] = len(infos)
            row["zip_top_entries"] = [item.filename for item in sorted(infos, key=lambda i: i.filename.lower())[:20]]

    stats = text_stats(text)
    row.update(stats)
    row["heading_count"] = len(headings)
    row["first_headings"] = headings[:8]
    row["snippet"] = re.sub(r"\s+", " ", text).strip()[:500]
    row["decision"], row["decision_note"] = classify_decision(key, role, path, row)
    return row


def dataset_summary() -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    path = DOWNLOADS / "tri_county_persona_resources.json"
    if not path.exists():
        return [], [], [], []
    rows = json.loads(read_text(path))
    county_rows = [{"county": k, "resources": v} for k, v in Counter(row.get("County", "") for row in rows).most_common()]
    type_rows = [{"resource_type": k, "resources": v} for k, v in Counter(row.get("Resource_Type", "") for row in rows).most_common()]
    persona_rows = [{"primary_persona": k, "resources": v} for k, v in Counter(row.get("Primary_Persona", "") for row in rows).most_common()]
    source_rows = [{"source_section": k, "resources": v} for k, v in Counter(row.get("Source_Section", "") for row in rows).most_common(15)]
    return county_rows, type_rows, persona_rows, source_rows


def build() -> None:
    file_rows = [audit_file(*item) for item in UPLOADS + DERIVED]

    county_rows, type_rows, persona_rows, source_rows = dataset_summary()

    self_audit = [
        {
            "prior_gap": "Scope was too narrow",
            "evidence": "The previous audit centered on attachments.zip and only loosely referenced earlier uploads.",
            "correction": "This pass inventories the PDFs, HTML drafts, ZIPs, extracted text, generated package, dataset files, and review artifacts named across the thread.",
            "severity": "High",
        },
        {
            "prior_gap": "Technical false positives were possible",
            "evidence": "The first attachment audit initially counted JavaScript template strings and long-path nested assets incorrectly.",
            "correction": "The audit script now strips script blocks for anchor checks, reads long paths safely, and verifies script/css asset references separately.",
            "severity": "Medium",
        },
        {
            "prior_gap": "External benchmark research was too light",
            "evidence": "Earlier recommendations cited general guide patterns but did not preserve a structured benchmark table.",
            "correction": "This pass adds a benchmark source table for regional resource-center patterns, local economic-development examples, and state-level growth supports.",
            "severity": "High",
        },
        {
            "prior_gap": "No Data Analytics artifact",
            "evidence": "The prior handoff was a local Markdown audit and chat summary.",
            "correction": "This pass creates a Data Analytics report artifact with source-backed tables and charts.",
            "severity": "High",
        },
        {
            "prior_gap": "Implementation architecture remained high-level",
            "evidence": "The prior output named pages but did not fully connect content sources to page jobs and channel roles.",
            "correction": "This pass maps source materials to the multi-page Netlify structure and the co-channeling model.",
            "severity": "Medium",
        },
    ]

    benchmark_rows = [
        {
            "source": "New Mexico EDD Business Development",
            "url": "https://www.edd.newmexico.gov/programs-and-services/business-development/",
            "pattern": "Plan / Start / Grow pathing plus resource map, funding, training, business retention and expansion.",
            "site_implication": "Use action verbs and life-cycle paths; keep state programs under Find the Network and Understand the Region.",
        },
        {
            "source": "Trinidad & Las Animas County Chamber / Colexico Alliance",
            "url": "https://tlacchamber.org/",
            "pattern": "Frames a cross-state regional approach across Las Animas, Huerfano, and Colfax counties.",
            "site_implication": "Make regional connection the site thesis; acknowledge chambers as partners/nodes, not owners.",
        },
        {
            "source": "Huerfano County Chamber",
            "url": "https://www.chamber.huerfano.org/",
            "pattern": "Uses networking, education, promotion, advocacy, collaboration, events, and exposure as member benefits.",
            "site_implication": "Turn resource listings into practical visibility routes and event/promotion channels.",
        },
        {
            "source": "NMSBDC",
            "url": "https://www.nmsbdc.org/",
            "pattern": "Start, grow, succeed; counseling and training CTAs are immediate.",
            "site_implication": "Each page needs a clear CTA: get counseling, find training, prepare outreach, choose where to post.",
        },
        {
            "source": "CRCOG Municipal and Small Business Resource Center",
            "url": "https://crcogct.gov/regional-planning-and-development/economic-development/municipal-and-small-business-resource-center/",
            "pattern": "Audience is small businesses, entrepreneurs, and anyone expanding an existing business; resources grouped by business planning, training, capital, growth.",
            "site_implication": "Homepage should explicitly serve both new and existing businesses, then route by job to be done.",
        },
        {
            "source": "Douglas County Economic Development Resources",
            "url": "https://www.cdrpa.org/economic-development-resources",
            "pattern": "County connects entrepreneurs and employers to local stakeholders, regional organizations, and state/federal agencies.",
            "site_implication": "The guide should be a connector across organizations and county lines, not a substitute for those organizations.",
        },
        {
            "source": "City of Raton Economic Development",
            "url": "https://www.ratonnm.gov/business/economic_development/index.php",
            "pattern": "Economic development page lists local business support, resources, organizations, and startup help.",
            "site_implication": "Colfax/Raton pages should be channel hubs with city, GrowRaton, MainStreet, CCI, and media paths.",
        },
        {
            "source": "GrowRaton Economic Development",
            "url": "https://www.growraton.org/economic-development-overview/",
            "pattern": "Speaks to entrepreneurs and established businesses and names current/future economy categories.",
            "site_implication": "Use local economic sectors as context for audience/customer expansion, not as abstract demographics.",
        },
    ]

    channel_rows = [
        {"channel": "Advice / playbooks", "public_label": "Plan Your Growth", "primary_sources": "Agentic brief, small index.html, current guide templates", "job": "Help users choose next steps for customers, partners, funding, promotion, and launch/expansion."},
        {"channel": "Resource directory", "public_label": "Find the Network", "primary_sources": "456-resource dataset, county PDFs, regional business research, state/local sources", "job": "Let users find chambers, agencies, media, business anchors, arts orgs, training, funding, and posting channels."},
        {"channel": "Local data/context", "public_label": "Understand the Region", "primary_sources": "Demographic sections, posting matrix, directory feature matrix, county source PDFs", "job": "Show where to promote, who to reach, what channels fit each county, and which regional patterns matter."},
        {"channel": "County hubs", "public_label": "County Pages", "primary_sources": "Colfax, Las Animas, Huerfano inventories plus local official websites", "job": "Give each county its own practical entry point without fragmenting the regional mission."},
        {"channel": "Templates", "public_label": "Use the Templates", "primary_sources": "Current guide templates and implementation packs", "job": "Turn learning into copy-ready posts, emails, outreach scripts, and intake/update checklists."},
        {"channel": "Methods", "public_label": "About This Guide", "primary_sources": "Roadmap PDF, implementation status, validation report", "job": "Hold verification, limitations, update cadence, and attribution away from the main user journey."},
    ]

    page_rows = [
        {"page": "/", "title": "Grow Your Work Across the Tri-County Region", "cta": "Choose the kind of help you need", "incorporate": "Small index homepage concept; animated mountain banner; three path cards; regional thesis."},
        {"page": "/plan/", "title": "Plan Your Growth", "cta": "Pick a goal and follow the next steps", "incorporate": "Advice/playbooks from agentic brief and current guide templates."},
        {"page": "/network/", "title": "Find the Network", "cta": "Search resources by county, goal, type, and audience", "incorporate": "456-resource dataset plus county inventories and state supports."},
        {"page": "/region/", "title": "Understand the Region", "cta": "Use local signals before choosing outreach channels", "incorporate": "Posting spaces, county matrix, directory feature matrix, business/research notes."},
        {"page": "/counties/colfax/", "title": "Colfax County and Raton", "cta": "Find Colfax contacts, media, business anchors, and startup supports", "incorporate": "Raton/Colfax inventory, Raton economic-development sources, GrowRaton."},
        {"page": "/counties/las-animas/", "title": "Las Animas County and Trinidad", "cta": "Find Trinidad/Las Animas promotion and partner channels", "incorporate": "Las Animas PDF, Trinidad chamber/Colexico source, posting spaces."},
        {"page": "/counties/huerfano/", "title": "Huerfano County, Walsenburg, and La Veta", "cta": "Find Huerfano promotion, incubator, chamber, and partner channels", "incorporate": "Huerfano PDF, Huerfano Chamber, Wheelhouse/incubator context."},
        {"page": "/templates/", "title": "Templates You Can Use", "cta": "Copy, adapt, and send", "incorporate": "Outreach scripts, public posting checklist, referral blurbs, intake correction form."},
        {"page": "/about/", "title": "About This Guide", "cta": "See scope, update rules, and how to suggest corrections", "incorporate": "Validation report, method notes, verification/caveat language."},
    ]

    decision_counts = [{"decision": k, "files": v} for k, v in Counter(row.get("decision", "missing") for row in file_rows).most_common()]
    role_counts = [{"role": k, "files": v} for k, v in Counter(row.get("role", "") for row in file_rows).most_common()]

    output = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "file_rows": file_rows,
        "self_audit": self_audit,
        "benchmark_rows": benchmark_rows,
        "channel_rows": channel_rows,
        "page_rows": page_rows,
        "decision_counts": decision_counts,
        "role_counts": role_counts,
        "resource_by_county": county_rows,
        "resource_by_type": type_rows,
        "resource_by_persona": persona_rows,
        "resource_by_source": source_rows,
    }

    (OUT_DIR / "comprehensive_reaudit_data.json").write_text(json.dumps(output, indent=2), encoding="utf-8")

    lines = ["# Comprehensive Upload Re-Audit Source Notes", "", f"Generated: {output['generated_at']}", ""]
    lines.append("## Self-Audit Corrections")
    for row in self_audit:
        lines.append(f"- **{row['prior_gap']} ({row['severity']}):** {row['correction']}")
    lines.append("")
    lines.append("## Uploaded / Generated File Inventory")
    for row in file_rows:
        exists = "found" if row["exists"] else "missing"
        lines.append(f"- `{row['label']}` ({row['role']}, {exists}): {row.get('decision', 'missing')} — {row.get('decision_note', '')}")
    lines.append("")
    lines.append("## Dataset Summary")
    lines.append(f"- Resource rows: {sum(r['resources'] for r in county_rows) if county_rows else 0}")
    lines.append("- County mix: " + ", ".join(f"{r['county']} {r['resources']}" for r in county_rows))
    lines.append("- Type mix: " + ", ".join(f"{r['resource_type']} {r['resources']}" for r in type_rows))
    lines.append("")
    lines.append("## Benchmark Research Sources")
    for row in benchmark_rows:
        lines.append(f"- [{row['source']}]({row['url']}): {row['pattern']} Implication: {row['site_implication']}")
    lines.append("")
    lines.append("## Recommended Co-Channel Model")
    for row in channel_rows:
        lines.append(f"- **{row['public_label']}**: {row['job']} Sources: {row['primary_sources']}.")
    (OUT_DIR / "comprehensive_reaudit_source_notes.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(OUT_DIR / "comprehensive_reaudit_data.json")
    print(OUT_DIR / "comprehensive_reaudit_source_notes.md")


if __name__ == "__main__":
    build()
