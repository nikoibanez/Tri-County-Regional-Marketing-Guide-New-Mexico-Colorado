from __future__ import annotations

import argparse
import json
import os
import time
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SITE = ROOT / "dist" / "tri-county-netlify-guide-deep"
DEFAULT_OUT_DIR = ROOT / "review" / "maintenance"
DEFAULT_PATHS = (
    "",
    "network/",
    "resources/funding/",
    "resources/arts-culture/",
    "posting/",
    "submit/",
    "about/",
    "data/guide-data.json",
    "sitemap.xml",
    "robots.txt",
)


def local_fetch(site: Path, route: str) -> tuple[bool, str, str]:
    target = site / route
    if route.endswith("/") or target.is_dir():
        target = target / "index.html"
    if not route:
        target = site / "index.html"
    if not target.exists():
        return False, "", f"Missing file: {target}"
    return True, target.read_text(encoding="utf-8", errors="replace"), ""


def remote_fetch(base_url: str, route: str, timeout: int) -> tuple[bool, str, str]:
    url = urljoin(base_url.rstrip("/") + "/", route)
    request = Request(
        url,
        headers={"User-Agent": "StatelineGuideSmokeTest/1.0 (+https://statelineguide.org)"},
        method="GET",
    )
    for attempt in range(2):
        try:
            with urlopen(request, timeout=timeout) as response:
                body = response.read(3_000_000).decode(response.headers.get_content_charset() or "utf-8", errors="replace")
                status = getattr(response, "status", 200)
                return 200 <= status < 400, body, "" if status < 400 else f"HTTP {status}"
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            if attempt == 0:
                time.sleep(1)
                continue
            return False, "", str(exc)
    return False, "", "Unknown fetch failure."


def validate_body(route: str, body: str) -> str:
    suffix = Path(route).suffix.casefold()
    if suffix == ".json":
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            return f"Invalid JSON: {exc}"
        if not isinstance(payload, dict):
            return "Expected a JSON object."
        return ""
    if suffix == ".xml":
        return "" if "<urlset" in body and "<loc>" in body else "Sitemap XML is missing urlset or loc elements."
    if suffix == ".txt":
        return "" if "Sitemap:" in body else "robots.txt is missing the Sitemap directive."
    lowered = body.casefold()
    required = ("<title>", "<main", "</html>")
    missing = [marker for marker in required if marker not in lowered]
    return f"HTML is missing: {', '.join(missing)}" if missing else ""


def run_smoke(site: Path, base_url: str, timeout: int, paths: tuple[str, ...] = DEFAULT_PATHS) -> dict:
    results = []
    for route in paths:
        ok, body, error = remote_fetch(base_url, route, timeout) if base_url else local_fetch(site, route)
        if ok:
            error = validate_body(route, body)
            ok = not error
        results.append({"route": "/" + route, "ok": ok, "error": error})
    return {
        "generated_at": date.today().isoformat(),
        "target": base_url or str(site),
        "mode": "live" if base_url else "local",
        "status": "pass" if all(item["ok"] for item in results) else "fail",
        "checked": len(results),
        "failed": sum(1 for item in results if not item["ok"]),
        "results": results,
    }


def write_markdown(payload: dict, path: Path) -> None:
    lines = [
        "# Site Smoke Test",
        "",
        f"Generated: {payload['generated_at']}",
        f"Target: {payload['target']}",
        f"Mode: {payload['mode']}",
        f"Status: **{payload['status'].upper()}**",
        "",
        "| Route | Result | Detail |",
        "| --- | --- | --- |",
    ]
    for item in payload["results"]:
        detail = (item["error"] or "Loaded and passed content checks.").replace("|", "\\|")
        lines.append(f"| `{item['route']}` | {'PASS' if item['ok'] else 'FAIL'} | {detail} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test the generated site locally or at its configured public URL.")
    parser.add_argument("--site", type=Path, default=DEFAULT_SITE)
    parser.add_argument("--base-url", default=os.environ.get("PUBLIC_SITE_ORIGIN", ""))
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    payload = run_smoke(args.site, args.base_url.strip(), args.timeout)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    prefix = "live" if payload["mode"] == "live" else "local"
    json_path = args.out_dir / f"{prefix}-smoke-test-latest.json"
    md_path = args.out_dir / f"{prefix}-smoke-test-latest.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(payload, md_path)
    print(json.dumps({"status": payload["status"], "checked": payload["checked"], "failed": payload["failed"]}, indent=2))
    if payload["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
