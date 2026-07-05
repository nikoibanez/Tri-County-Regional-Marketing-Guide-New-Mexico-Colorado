from __future__ import annotations

import argparse
import json
import shutil
import ssl
import time
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "data" / "update-source-registry.json"
DEFAULT_OUT_DIR = ROOT / "review" / "update-audits"


def check_url(url: str, timeout: int) -> dict:
    if not url:
        return {"status": "missing_url", "status_code": None, "final_url": "", "error": "No source URL is attached."}

    context = ssl.create_default_context()
    headers = {
        "User-Agent": "TriCountyGuideSourceAudit/1.0 (+https://wonderful-kashata-6ed008.netlify.app/)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    for method in ("HEAD", "GET"):
        request = Request(url, headers=headers, method=method)
        started = time.monotonic()
        try:
            with urlopen(request, timeout=timeout, context=context) as response:
                elapsed_ms = round((time.monotonic() - started) * 1000)
                code = getattr(response, "status", None)
                final_url = response.geturl()
                status = "ok"
                if final_url and final_url.rstrip("/") != url.rstrip("/"):
                    status = "redirect"
                return {"status": status, "status_code": code, "final_url": final_url, "elapsed_ms": elapsed_ms, "error": ""}
        except HTTPError as exc:
            if method == "HEAD" and exc.code in {403, 405, 406, 429, 500, 501}:
                continue
            status = "manual_review" if exc.code in {401, 403, 406, 429} else "http_error"
            return {"status": status, "status_code": exc.code, "final_url": url, "error": str(exc)}
        except TimeoutError as exc:
            return {"status": "timeout", "status_code": None, "final_url": url, "error": str(exc)}
        except URLError as exc:
            reason = str(getattr(exc, "reason", exc))
            return {"status": "network_error", "status_code": None, "final_url": url, "error": reason}
        except Exception as exc:
            return {"status": "error", "status_code": None, "final_url": url, "error": str(exc)}

    return {"status": "error", "status_code": None, "final_url": url, "error": "Unable to complete URL check."}


def summarize(results: list[dict]) -> dict:
    counts: dict[str, int] = {}
    attention_statuses = {"error", "http_error", "manual_review", "missing_url", "network_error", "timeout"}
    for result in results:
        counts[result["check"]["status"]] = counts.get(result["check"]["status"], 0) + 1
    return {
        "checked": len(results),
        "counts": dict(sorted(counts.items())),
        "needs_attention": sum(1 for item in results if item["check"]["status"] in attention_statuses),
        "human_approval_required": sum(1 for item in results if item["record"]["review_level"] == "human_approval_required"),
    }


def write_markdown(payload: dict, path: Path) -> None:
    lines = [
        "# Update Source Audit",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "This report is a review queue. A failure here does not automatically mean a public source is invalid; some official sites block scripted checks.",
        "",
        "## Summary",
        "",
        f"- Checked: {payload['summary']['checked']}",
        f"- Needs attention: {payload['summary']['needs_attention']}",
        f"- Human approval required: {payload['summary']['human_approval_required']}",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in payload["summary"]["counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Needs Attention", ""])
    attention = [item for item in payload["results"] if item["check"]["status"] in {"error", "http_error", "manual_review", "missing_url", "network_error", "timeout"}]
    if not attention:
        lines.append("No checked sources need attention.")
    else:
        for item in attention:
            record = item["record"]
            check = item["check"]
            url = record.get("url") or ""
            linked = f"[{record['title']}]({url})" if url else record["title"]
            lines.append(f"- {linked} - {record['county']}; {record['update_domain']}; {check['status']}; {check.get('error', '')}")

    lines.extend(["", "## Human Approval Required", ""])
    high_risk = [item for item in payload["results"] if item["record"]["review_level"] == "human_approval_required"]
    if not high_risk:
        lines.append("No checked records are marked human approval required.")
    else:
        for item in high_risk:
            record = item["record"]
            url = record.get("url") or ""
            linked = f"[{record['title']}]({url})" if url else record["title"]
            lines.append(f"- {linked} - {record['county']}; {record['category']}; {record['public_claim_boundary']}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Tri-County Guide monitored source URLs.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--timeout", type=int, default=12)
    parser.add_argument("--limit", type=int, default=0, help="Limit records checked. 0 checks all records.")
    parser.add_argument("--domain", action="append", default=[], help="Only check records with this update_domain. Can be repeated or comma-separated.")
    parser.add_argument("--no-network", action="store_true", help="Generate a due report without checking URLs.")
    parser.add_argument("--fail-on-broken", action="store_true", help="Exit nonzero if checked sources need attention.")
    args = parser.parse_args()

    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    records = registry.get("records", [])
    if args.domain:
        domains = {part.strip() for value in args.domain for part in value.split(",") if part.strip()}
        records = [record for record in records if record.get("update_domain") in domains]
    if args.limit > 0:
        records = records[: args.limit]

    results = []
    for record in records:
        if args.no_network:
            check = {"status": "not_checked", "status_code": None, "final_url": record.get("url", ""), "error": "Network checks were disabled."}
        else:
            check = check_url(record.get("url", ""), args.timeout)
        results.append({"record": record, "check": check})

    payload = {
        "generated_at": date.today().isoformat(),
        "registry": str(args.registry),
        "summary": summarize(results),
        "results": results,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / f"update-audit-{date.today().isoformat()}.json"
    md_path = args.out_dir / f"update-audit-{date.today().isoformat()}.md"
    latest_md = args.out_dir / "update-audit-latest.md"
    latest_json = args.out_dir / "update-audit-latest.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(payload, md_path)
    shutil.copy2(md_path, latest_md)
    shutil.copy2(json_path, latest_json)
    print(json.dumps({"json": str(json_path), "markdown": str(md_path), "summary": payload["summary"]}, indent=2))

    if args.fail_on_broken and payload["summary"]["needs_attention"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
