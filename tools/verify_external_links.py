from __future__ import annotations

import argparse
import json
import ssl
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


USER_AGENT = "TriCountyGuideLinkAudit/2026.06 (+https://wonderful-kashata-6ed008.netlify.app/)"


def collect_urls(data: dict) -> tuple[dict[str, list[dict]], Counter]:
    urls: dict[str, list[dict]] = {}
    manual_counts: Counter = Counter()

    def add(url: str, source_type: str, label: str, extra: dict | None = None) -> None:
        if not url:
            manual_counts[source_type] += 1
            return
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            manual_counts[f"{source_type}:non_http"] += 1
            return
        urls.setdefault(url, []).append({"source_type": source_type, "label": label, **(extra or {})})

    for item in data.get("directory_sources", []):
        add(item.get("url", ""), "directory_source", item.get("title", ""), {"county": item.get("county"), "status": item.get("verification_label")})

    for item in data.get("amplifier_channels", []):
        add(item.get("source_url", ""), "amplifier_channel", item.get("channel", ""), {"area_served": item.get("area_served"), "status": item.get("verification_status")})

    for item in data.get("posting_spaces", []):
        add(item.get("source_url", ""), "posting_space", item.get("place", ""), {"status": item.get("status")})

    for item in data.get("resources", []):
        add(item.get("website") or item.get("source_url") or "", "resource_row", item.get("resource_name", ""), {"county": item.get("county"), "status": item.get("verification_label")})

    return urls, manual_counts


def check_url(url: str, timeout: int = 12) -> dict:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return {"url": url, "ok": False, "status": "invalid_url", "error": "missing scheme or host"}

    context = ssl.create_default_context()
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8"})
    try:
        with urlopen(request, timeout=timeout, context=context) as response:
            status_code = getattr(response, "status", None) or response.getcode()
            final_url = response.geturl()
            ok = 200 <= status_code < 400
            return {"url": url, "ok": ok, "status": "ok" if ok else "http_error", "status_code": status_code, "final_url": final_url}
    except HTTPError as exc:
        return {"url": url, "ok": 200 <= exc.code < 400, "status": "http_error", "status_code": exc.code, "error": str(exc)}
    except URLError as exc:
        return {"url": url, "ok": False, "status": "url_error", "error": str(exc.reason)}
    except TimeoutError as exc:
        return {"url": url, "ok": False, "status": "timeout", "error": str(exc)}
    except Exception as exc:
        return {"url": url, "ok": False, "status": exc.__class__.__name__, "error": str(exc)}


def write_markdown(report: dict, output_path: Path) -> None:
    failed = [item for item in report["checks"] if not item.get("ok")]
    ok_count = report["summary"]["ok"]
    checked = report["summary"]["checked"]
    lines = [
        "# Live Link Verification",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Unique URL-bearing listings checked: {checked}",
        f"- OK or redirected successfully: {ok_count}",
        f"- Needs normal-browser/manual confirmation: {len(failed)}",
        f"- Rows without a public URL, routed to field-check/manual verification: {sum(report['manual_counts'].values())}",
        "",
        "Automated checks confirm whether a URL responded to scripted access. They do not prove ad availability, directory acceptance, rates, deadlines, eligibility, or current contact accuracy.",
        "",
        "## Manual Field-Check Counts",
        "",
    ]
    for key, value in sorted(report["manual_counts"].items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## URLs Needing Manual Confirmation", ""])
    if failed:
        for item in failed:
            refs = "; ".join(f"{ref.get('source_type')}: {ref.get('label')}" for ref in item.get("references", [])[:3])
            lines.append(f"- {item['url']} - {item.get('status')} {item.get('status_code', '')} {item.get('error', '')}".rstrip())
            if refs:
                lines.append(f"  - Referenced by: {refs}")
    else:
        lines.append("- None from this scripted sweep.")
    lines.extend(["", "## Checked URLs", ""])
    for item in report["checks"]:
        label = "OK" if item.get("ok") else "CHECK"
        status_code = item.get("status_code", "")
        lines.append(f"- {label}: {item['url']} {status_code}".rstrip())
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check URL-bearing listings in generated tri-county guide data.")
    parser.add_argument("--data", required=True, type=Path, help="Path to generated data/guide-data.json")
    parser.add_argument("--json-out", required=True, type=Path)
    parser.add_argument("--md-out", required=True, type=Path)
    args = parser.parse_args()

    data = json.loads(args.data.read_text(encoding="utf-8"))
    urls, manual_counts = collect_urls(data)
    checks = []
    for url, refs in sorted(urls.items()):
        result = check_url(url)
        result["references"] = refs
        checks.append(result)

    summary = Counter("ok" if item.get("ok") else item.get("status", "failed") for item in checks)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "checked": len(checks),
            "ok": summary.get("ok", 0),
            "needs_manual_confirmation": len(checks) - summary.get("ok", 0),
            "by_status": dict(summary),
        },
        "manual_counts": dict(manual_counts),
        "checks": checks,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report, args.md_out)
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
