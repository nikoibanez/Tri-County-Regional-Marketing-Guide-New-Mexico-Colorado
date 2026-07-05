from __future__ import annotations

from datetime import date
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "dist" / "tri-county-netlify-guide-deep"
REVIEW = ROOT / "review"


def check(condition: bool, label: str, detail: str, rows: list[tuple[str, str, str]]) -> None:
    rows.append(("PASS" if condition else "FAIL", label, detail))


def main() -> int:
    html_files = sorted(SITE.rglob("*.html"))
    failures = 0
    rows: list[tuple[str, str, str]] = []

    index = (SITE / "index.html").read_text(encoding="utf-8")
    app_js = (SITE / "assets" / "app.js").read_text(encoding="utf-8")
    styles = (SITE / "assets" / "styles.css").read_text(encoding="utf-8")

    check(bool(html_files), "generated pages exist", f"{len(html_files)} HTML files found", rows)
    check('href="#main"' in index and 'id="main"' in index, "skip link target", "Homepage includes a skip link target", rows)
    check("<dialog" in index and 'id="directory-assistant-panel"' in index, "native assistant dialog", "Assistant uses native dialog markup", rows)
    check('aria-haspopup="dialog"' in index, "assistant opener semantics", "Ask directory button announces a dialog", rows)
    check('aria-labelledby="directory-assistant-title"' in index, "assistant title link", "Dialog is tied to a visible title", rows)
    check('aria-describedby="directory-assistant-intro directory-assistant-hint"' in index, "assistant description link", "Dialog has visible and screen-reader instructions", rows)
    check('aria-controls="directory-assistant-results"' in index, "assistant result control", "Search input controls the results region", rows)
    check('role="status"' in index and 'aria-live="polite"' in index, "assistant live status", "Result counts are announced politely", rows)
    check('role="list"' in index and 'role="listitem"' in app_js, "assistant result structure", "Results are exposed as list/listitem content", rows)
    check("showModal" in app_js and "focusableSelector" not in app_js, "native focus management", "Uses dialog showModal instead of a custom focus trap", rows)
    check("stateline-" not in index and "stateline-" not in app_js, "generated music removed", "No generated music files are referenced by active pages/scripts", rows)
    check("loc-rael-nm-valse.mp3" in index and "loc-rael-co-valse.mp3" in index, "regional audio present", "Music bar references only LOC regional tracks", rows)
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
