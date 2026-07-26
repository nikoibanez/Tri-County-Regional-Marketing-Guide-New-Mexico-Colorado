from __future__ import annotations

import argparse
import json
import os
import shutil
import ssl
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "data" / "update-source-registry.json"
DEFAULT_OUT_DIR = ROOT / "review" / "update-audits"
PUBLIC_SITE_ORIGIN = (os.environ.get("PUBLIC_SITE_ORIGIN") or "https://newmexicocoloradoguide.netlify.app").rstrip("/")
CONFIRMED_BROKEN_STATUSES = {"broken", "invalid_url", "missing_url"}
BROWSER_CHECK_STATUSES = {"error", "http_error", "network_error", "timeout"}
SCRIPT_LIMIT_STATUSES = {"access_blocked", "tls_error"}
FIELD_CHECK_STATUSES = {"field_check"}


def check_url(url: str, timeout: int) -> dict:
    if not url:
        return {"status": "missing_url", "status_code": None, "final_url": "", "error": "No source URL is attached."}
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {"status": "invalid_url", "status_code": None, "final_url": url, "error": "URL must include an http(s) scheme and host."}

    context = ssl.create_default_context()
    headers = {
        "User-Agent": f"TriCountyGuideSourceAudit/1.2 (+{PUBLIC_SITE_ORIGIN}/about/)",
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
            if method == "HEAD":
                continue
            if exc.code in {401, 403, 406, 429}:
                status = "access_blocked"
            elif exc.code in {404, 410}:
                status = "broken"
            else:
                status = "http_error"
            return {"status": status, "status_code": exc.code, "final_url": url, "error": str(exc)}
        except TimeoutError as exc:
            return {"status": "timeout", "status_code": None, "final_url": url, "error": str(exc)}
        except URLError as exc:
            reason_value = getattr(exc, "reason", exc)
            reason = str(reason_value)
            status = "tls_error" if isinstance(reason_value, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in reason else "network_error"
            return {"status": status, "status_code": None, "final_url": url, "error": reason}
        except Exception as exc:
            return {"status": "error", "status_code": None, "final_url": url, "error": str(exc)}

    return {"status": "error", "status_code": None, "final_url": url, "error": "Unable to complete URL check."}


def check_record(record: dict, timeout: int) -> dict:
    url = str(record.get("url") or "").strip()
    if not url and (record.get("check_mode") == "field" or record.get("source_group") == "posting_spaces"):
        return {
            "status": "field_check",
            "status_code": None,
            "final_url": "",
            "error": "Offline or physical-location guidance; no web URL is expected.",
        }
    return check_url(url, timeout)


def summarize(results: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for result in results:
        counts[result["check"]["status"]] = counts.get(result["check"]["status"], 0) + 1
    return {
        "checked": len(results),
        "web_checked": sum(1 for item in results if item["check"]["status"] not in FIELD_CHECK_STATUSES),
        "counts": dict(sorted(counts.items())),
        "confirmed_broken": sum(1 for item in results if item["check"]["status"] in CONFIRMED_BROKEN_STATUSES),
        "needs_attention": sum(1 for item in results if item["check"]["status"] in CONFIRMED_BROKEN_STATUSES),
        "browser_check_needed": sum(1 for item in results if item["check"]["status"] in BROWSER_CHECK_STATUSES),
        "script_access_limited": sum(1 for item in results if item["check"]["status"] in SCRIPT_LIMIT_STATUSES),
        "field_checks": sum(1 for item in results if item["check"]["status"] in FIELD_CHECK_STATUSES),
        "human_approval_required": sum(1 for item in results if item["record"]["review_level"] == "human_approval_required"),
    }


def write_markdown(payload: dict, path: Path) -> None:
    lines = [
        "# Update Source Audit",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "This report separates confirmed link failures from pages that merely block or confuse scripted checks.",
        "",
        "## Summary",
        "",
        f"- Records checked: {payload['summary']['checked']}",
        f"- Web sources checked: {payload['summary']['web_checked']}",
        f"- Confirmed broken or missing: {payload['summary']['confirmed_broken']}",
        f"- Normal-browser confirmation required: {payload['summary']['browser_check_needed']}",
        f"- Script-access limitations (not broken): {payload['summary']['script_access_limited']}",
        f"- Offline field-check records: {payload['summary']['field_checks']}",
        f"- Human approval required: {payload['summary']['human_approval_required']}",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in payload["summary"]["counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Confirmed Broken Or Missing", ""])
    broken = [item for item in payload["results"] if item["check"]["status"] in CONFIRMED_BROKEN_STATUSES]
    if not broken:
        lines.append("No checked web source is confirmed broken or missing.")
    else:
        for item in broken:
            record = item["record"]
            check = item["check"]
            url = record.get("url") or ""
            linked = f"[{record['title']}]({url})" if url else record["title"]
            lines.append(f"- {linked} - {record['county']}; {record['update_domain']}; {check['status']}; {check.get('error', '')}")

    lines.extend(["", "## Normal-Browser Confirmation Required", ""])
    browser_checks = [item for item in payload["results"] if item["check"]["status"] in BROWSER_CHECK_STATUSES]
    if not browser_checks:
        lines.append("No inconclusive network or server response is waiting on a normal-browser confirmation.")
    else:
        lines.append("These pages are not classified as broken. A timeout, network problem, or temporary server response prevented a conclusive scripted check.")
        lines.append("")
        for item in browser_checks:
            record = item["record"]
            check = item["check"]
            url = record.get("url") or ""
            linked = f"[{record['title']}]({url})" if url else record["title"]
            lines.append(f"- {linked} - {record['county']}; {record['update_domain']}; {check['status']}; {check.get('error', '')}")

    lines.extend(["", "## Script Access Limitations (Not Broken)", ""])
    script_limits = [item for item in payload["results"] if item["check"]["status"] in SCRIPT_LIMIT_STATUSES]
    if not script_limits:
        lines.append("No checked source blocked scripted access or exposed a local TLS-checker limitation.")
    else:
        lines.append("These are informational results, not broken-link findings. The page blocked scripted access or the local certificate checker could not validate its chain.")
        lines.append("")
        for item in script_limits:
            record = item["record"]
            check = item["check"]
            url = record.get("url") or ""
            linked = f"[{record['title']}]({url})" if url else record["title"]
            lines.append(f"- {linked} - {record['county']}; {record['update_domain']}; {check['status']}; {check.get('error', '')}")

    lines.extend(["", "## Offline Field Checks", ""])
    field_checks = [item for item in payload["results"] if item["check"]["status"] in FIELD_CHECK_STATUSES]
    if not field_checks:
        lines.append("No offline field-check record was included.")
    else:
        for item in field_checks:
            record = item["record"]
            lines.append(f"- {record['title']} - {record['county']}; {record['category']}; verify the physical or offline pathway locally.")

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


def update_registry_state(registry: dict, results: list[dict], registry_path: Path) -> int:
    checked_by_id = {
        item["record"].get("id"): item["check"]
        for item in results
        if item["record"].get("id") and item["check"].get("status") != "not_checked"
    }
    today = date.today()
    updated = 0
    for record in registry.get("records", []):
        check = checked_by_id.get(record.get("id"))
        if not check:
            continue
        record["last_checked"] = today.isoformat()
        record["next_check"] = (today + timedelta(days=int(record.get("cadence_days") or 30))).isoformat()
        record["last_check_status"] = check.get("status", "")
        record["last_status_code"] = check.get("status_code")
        updated += 1
    if updated:
        registry["maintenance_updated_at"] = today.isoformat()
        registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Tri-County Guide monitored source URLs.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--timeout", type=int, default=12)
    parser.add_argument("--limit", type=int, default=0, help="Limit records checked. 0 checks all records.")
    parser.add_argument("--domain", action="append", default=[], help="Only check records with this update_domain. Can be repeated or comma-separated.")
    parser.add_argument("--no-network", action="store_true", help="Generate a due report without checking URLs.")
    parser.add_argument("--no-update-registry", action="store_true", help="Do not persist last-checked status and next-check dates.")
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
            check = check_record(record, args.timeout)
        results.append({"record": record, "check": check})

    payload = {
        "generated_at": date.today().isoformat(),
        "registry": str(args.registry),
        "summary": summarize(results),
        "results": results,
    }

    state_updates = 0
    if not args.no_network and not args.no_update_registry:
        state_updates = update_registry_state(registry, results, args.registry)
    payload["registry_state_updates"] = state_updates

    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / f"update-audit-{date.today().isoformat()}.json"
    md_path = args.out_dir / f"update-audit-{date.today().isoformat()}.md"
    latest_md = args.out_dir / "update-audit-latest.md"
    latest_json = args.out_dir / "update-audit-latest.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(payload, md_path)
    shutil.copy2(md_path, latest_md)
    shutil.copy2(json_path, latest_json)
    print(
        json.dumps(
            {"json": str(json_path), "markdown": str(md_path), "summary": payload["summary"], "registry_state_updates": state_updates},
            indent=2,
        )
    )

    if args.fail_on_broken and payload["summary"]["confirmed_broken"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
