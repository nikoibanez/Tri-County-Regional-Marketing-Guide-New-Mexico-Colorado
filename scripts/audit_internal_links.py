from __future__ import annotations

import argparse
import json
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SITE = ROOT / "dist" / "tri-county-netlify-guide-deep"
DEFAULT_OUT_DIR = ROOT / "review" / "maintenance"
SKIP_SCHEMES = {"data", "javascript", "mailto", "sms", "tel"}


class ReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[tuple[str, str]] = []
        self.ids: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.casefold(): value or "" for name, value in attrs}
        element_id = values.get("id")
        if element_id:
            self.ids.append(element_id)
        if tag.casefold() == "a" and values.get("name"):
            self.ids.append(values["name"])
        for attribute in ("href", "src"):
            value = values.get(attribute)
            if value:
                self.references.append((attribute, value))


def parse_html(path: Path) -> ReferenceParser:
    parser = ReferenceParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    return parser


def target_for(site: Path, source: Path, value: str) -> tuple[Path | None, str]:
    parsed = urlsplit(value)
    if parsed.scheme.casefold() in SKIP_SCHEMES or parsed.scheme or parsed.netloc:
        return None, ""
    raw_path = unquote(parsed.path)
    if raw_path:
        target = site / raw_path.lstrip("/") if raw_path.startswith("/") else source.parent / raw_path
    else:
        target = source
    target = target.resolve()
    try:
        target.relative_to(site.resolve())
    except ValueError:
        return target, parsed.fragment
    if raw_path.endswith("/") or target.is_dir():
        target = target / "index.html"
    return target, parsed.fragment


def audit_site(site: Path) -> dict:
    site = site.resolve()
    html_files = sorted(site.rglob("*.html")) if site.exists() else []
    parsers = {path.resolve(): parse_html(path) for path in html_files}
    missing_targets: list[dict[str, str]] = []
    missing_anchors: list[dict[str, str]] = []
    outside_site: list[dict[str, str]] = []
    duplicate_ids: list[dict[str, object]] = []
    checked = 0

    for source, parser in parsers.items():
        seen: set[str] = set()
        duplicates: set[str] = set()
        for element_id in parser.ids:
            if element_id in seen:
                duplicates.add(element_id)
            seen.add(element_id)
        if duplicates:
            duplicate_ids.append({"page": str(source.relative_to(site)), "ids": sorted(duplicates)})

        for attribute, value in parser.references:
            target, fragment = target_for(site, source, value)
            if target is None:
                continue
            checked += 1
            try:
                relative_target = target.relative_to(site)
            except ValueError:
                outside_site.append({"page": str(source.relative_to(site)), "attribute": attribute, "value": value})
                continue
            if not target.exists():
                missing_targets.append(
                    {
                        "page": str(source.relative_to(site)),
                        "attribute": attribute,
                        "value": value,
                        "target": str(relative_target),
                    }
                )
                continue
            if fragment and target.suffix.casefold() in {".html", ".htm"}:
                target_parser = parsers.get(target.resolve()) or parse_html(target)
                if fragment not in set(target_parser.ids):
                    missing_anchors.append(
                        {
                            "page": str(source.relative_to(site)),
                            "value": value,
                            "target": str(relative_target),
                            "fragment": fragment,
                        }
                    )

    blocking_count = len(missing_targets) + len(missing_anchors) + len(outside_site) + len(duplicate_ids)
    return {
        "generated_at": date.today().isoformat(),
        "site": str(site),
        "status": "pass" if not blocking_count and html_files else "fail",
        "summary": {
            "html_files": len(html_files),
            "local_references_checked": checked,
            "missing_targets": len(missing_targets),
            "missing_anchors": len(missing_anchors),
            "outside_site_targets": len(outside_site),
            "pages_with_duplicate_ids": len(duplicate_ids),
        },
        "missing_targets": missing_targets,
        "missing_anchors": missing_anchors,
        "outside_site_targets": outside_site,
        "duplicate_ids": duplicate_ids,
    }


def write_markdown(payload: dict, path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# Internal Link Audit",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        f"Status: **{payload['status'].upper()}**",
        "",
        f"- HTML files: {summary['html_files']}",
        f"- Local references checked: {summary['local_references_checked']}",
        f"- Missing targets: {summary['missing_targets']}",
        f"- Missing anchors: {summary['missing_anchors']}",
        f"- Targets escaping the publish directory: {summary['outside_site_targets']}",
        f"- Pages with duplicate IDs: {summary['pages_with_duplicate_ids']}",
        "",
        "## Findings",
        "",
    ]
    findings: list[str] = []
    for item in payload["missing_targets"]:
        findings.append(f"Missing target: `{item['page']}` -> `{item['value']}`")
    for item in payload["missing_anchors"]:
        findings.append(f"Missing anchor: `{item['page']}` -> `{item['value']}`")
    for item in payload["outside_site_targets"]:
        findings.append(f"Outside publish directory: `{item['page']}` -> `{item['value']}`")
    for item in payload["duplicate_ids"]:
        findings.append(f"Duplicate IDs in `{item['page']}`: {', '.join(item['ids'])}")
    lines.extend(f"- {item}" for item in findings or ["None."])
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check generated HTML for broken local links, anchors, assets, and duplicate IDs.")
    parser.add_argument("--site", type=Path, default=DEFAULT_SITE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--fail-on-broken", action="store_true")
    args = parser.parse_args()

    payload = audit_site(args.site)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "internal-link-audit-latest.json"
    md_path = args.out_dir / "internal-link-audit-latest.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(payload, md_path)
    print(json.dumps({"status": payload["status"], "summary": payload["summary"]}, indent=2))

    if args.fail_on_broken and payload["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
