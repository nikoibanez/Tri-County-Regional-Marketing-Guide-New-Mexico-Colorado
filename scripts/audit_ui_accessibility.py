from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "dist" / "tri-county-netlify-guide-deep"
REVIEW = ROOT / "review"


def check(condition: bool, label: str, detail: str, rows: list[tuple[str, str, str]]) -> None:
    rows.append(("PASS" if condition else "FAIL", label, detail))


def attribute_has_idrefs(document: str, attribute: str, expected: set[str]) -> bool:
    match = re.search(rf'\b{re.escape(attribute)}="([^"]+)"', document)
    return bool(match and expected.issubset(set(match.group(1).split())))


def main() -> int:
    html_files = sorted(SITE.rglob("*.html"))
    failures = 0
    rows: list[tuple[str, str, str]] = []

    index = (SITE / "index.html").read_text(encoding="utf-8")
    arts_page_path = SITE / "resources" / "arts-culture" / "index.html"
    arts_page = arts_page_path.read_text(encoding="utf-8")
    tools_page = (SITE / "tools" / "free-discounted" / "index.html").read_text(encoding="utf-8")
    app_js = (SITE / "assets" / "app.js").read_text(encoding="utf-8")
    styles = (SITE / "assets" / "styles.css").read_text(encoding="utf-8")
    guide_data = json.loads((SITE / "data" / "guide-data.json").read_text(encoding="utf-8"))

    check(bool(html_files), "generated pages exist", f"{len(html_files)} HTML files found", rows)
    check('href="#main"' in index and 'id="main"' in index, "skip link target", "Homepage includes a skip link target", rows)
    check("<dialog" in index and 'id="directory-assistant-panel"' in index, "native assistant dialog", "Assistant uses native dialog markup", rows)
    check('aria-haspopup="dialog"' in index, "assistant opener semantics", "Ask directory button announces a dialog", rows)
    check('aria-labelledby="directory-assistant-title"' in index, "assistant title link", "Dialog is tied to a visible title", rows)
    check(
        attribute_has_idrefs(
            index,
            "aria-describedby",
            {"directory-assistant-intro", "directory-assistant-scope", "directory-assistant-hint"},
        ),
        "assistant description link",
        "Dialog is tied to its visible scope and screen-reader instructions",
        rows,
    )
    check('aria-controls="directory-assistant-results"' in index, "assistant result control", "Search input controls the results region", rows)
    check('role="status"' in index and 'aria-live="polite"' in index, "assistant live status", "Result counts are announced politely", rows)
    check('role="list"' in index and 'role="listitem"' in app_js, "assistant result structure", "Results are exposed as list/listitem content", rows)
    check("showModal" in app_js and "focusableSelector" not in app_js, "native focus management", "Uses dialog showModal instead of a custom focus trap", rows)
    check(
        'data-site-root=' in index and "...(DATA.site_routes || [])" in app_js,
        "assistant guide-page routing",
        f"Assistant indexes {len(guide_data.get('site_routes') or [])} internal routes with a page-relative root",
        rows,
    )
    check(
        'data-tool-query' in tools_page
        and 'data-tool-category' in tools_page
        and 'data-tool-offer' in tools_page
        and 'data-tool-format-filter' in tools_page
        and 'data-tool-status role="status" aria-live="polite"' in tools_page,
        "free-tool filter semantics",
        "Tool search, category, offer, and format controls are labelled and report results politely",
        rows,
    )
    check(
        tools_page.count("data-tool-card") == len(guide_data.get("free_tools") or []) >= 20,
        "structured free-tool inventory",
        f"Rendered {tools_page.count('data-tool-card')} cards from {len(guide_data.get('free_tools') or [])} structured tool records",
        rows,
    )
    check(
        'data-preview-watermark hidden aria-hidden="true">Draft preview</div>' in index
        and "opacity: 0.10;" in styles
        and "background: transparent;" in styles
        and "bottom: max(8vh, env(safe-area-inset-bottom));" in styles,
        "non-obstructive preview watermark",
        "Preview text is decorative, pointer-transparent, 90% transparent, and positioned in the lowest viewport band",
        rows,
    )
    check(
        "@media (max-width: 900px)" in styles
        and "@media (max-width: 640px)" in styles
        and ".tool-offer-grid { grid-template-columns: 1fr; }" in styles
        and "visibleLimit = compact ? 6" in app_js,
        "responsive tool reflow",
        "Tool categories and controls stack at tablet/mobile widths and the mobile list starts with six items",
        rows,
    )
    check(":focus-visible" in styles, "visible keyboard focus", "Generated controls retain visible focus styles", rows)
    check("@media (prefers-reduced-motion: reduce)" in styles, "reduced motion", "Decorative motion can be disabled by user preference", rows)
    all_html = "\n".join(html_file.read_text(encoding="utf-8") for html_file in html_files)
    generated_music_ref = re.search(r"stateline-[^\"']+\.mp3", all_html + app_js, re.IGNORECASE)
    check(not generated_music_ref, "generated music removed", "No generated music files are referenced by active pages/scripts", rows)
    non_arts_music_pages = [
        str(html_file.relative_to(SITE))
        for html_file in html_files
        if html_file != arts_page_path and 'data-music-bar' in html_file.read_text(encoding="utf-8")
    ]
    check(
        not non_arts_music_pages,
        "regional audio scope",
        "Music controls appear only on Arts & Culture" if not non_arts_music_pages else ", ".join(non_arts_music_pages),
        rows,
    )
    audio_manifest = json.loads((ROOT / "data" / "regional_audio_manifest.json").read_text(encoding="utf-8"))
    audio_tracks = [
        item
        for item in audio_manifest
        if item.get("local_audio_downloaded") and item.get("local_audio_filename")
    ]
    missing_audio = [
        item["local_audio_filename"]
        for item in audio_tracks
        if not (ROOT / "assets" / "audio" / item["local_audio_filename"]).exists()
        or not (SITE / "assets" / "audio" / item["local_audio_filename"]).exists()
    ]
    check(
        len(audio_tracks) >= 6
        and not missing_audio
        and all(item["local_audio_filename"] in arts_page for item in audio_tracks),
        "regional audio present",
        f"Arts & Culture references {len(audio_tracks)} manifest-backed LOC tracks"
        if not missing_audio
        else f"Missing audio: {', '.join(missing_audio)}",
        rows,
    )
    check(
        all(item.get("item_url") and item.get("license_status") and item.get("credit_line") for item in audio_tracks),
        "regional audio source trail",
        "Every player track includes an item page, rights note, and credit line",
        rows,
    )
    check(".sr-only" in styles, "screen-reader utility", "Screen-reader-only helper exists", rows)

    images_without_alt: list[str] = []
    for html_file in html_files:
        text = html_file.read_text(encoding="utf-8")
        for match in re.finditer(r"<img\b[^>]*>", text, re.IGNORECASE):
            if not re.search(r"\balt\s*=", match.group(0), re.IGNORECASE):
                images_without_alt.append(str(html_file.relative_to(SITE)))
                break
    check(not images_without_alt, "image alt attributes", "All generated pages give img elements alt attributes" if not images_without_alt else ", ".join(images_without_alt), rows)

    failures = sum(1 for status, _, _ in rows if status == "FAIL")
    REVIEW.mkdir(exist_ok=True)
    report = REVIEW / f"UI_ACCESSIBILITY_STATIC_AUDIT_{date.today():%Y%m%d}.md"
    lines = [
        "# UI Accessibility Static Audit",
        "",
        f"Date: {date.today():%Y-%m-%d}",
        "",
        "This no-dependency audit checks generated static files for accessibility regressions that are easy to break during generator edits. It does not replace browser, keyboard, or screen-reader QA.",
        "",
        "| Status | Check | Detail |",
        "| --- | --- | --- |",
    ]
    for status, label, detail in rows:
        safe_detail = detail.replace("|", "\\|")
        lines.append(f"| {status} | {label} | {safe_detail} |")
    lines.extend(["", f"Failures: {failures}", ""])
    report.write_text("\n".join(lines), encoding="utf-8")
    print(report)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
