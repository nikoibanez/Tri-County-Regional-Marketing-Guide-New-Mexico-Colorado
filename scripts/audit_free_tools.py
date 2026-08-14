from __future__ import annotations

import argparse
import hashlib
import json
import re
import ssl
import time
from datetime import date, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from audit_resource_discovery_sources import parse_page


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "free-tools.json"
DEFAULT_STATE = ROOT / "data" / "free-tools-state.json"
DEFAULT_OUT_DIR = ROOT / "review" / "free-tools"
MAX_RESPONSE_BYTES = 2_000_000
BLOCKED_STATUSES = {401, 403, 406, 429}
BROKEN_STATUSES = {404, 410}


def clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalized_url(value: object) -> str:
    url = clean_text(value)
    try:
        parsed = urlparse(url)
    except ValueError:
        return ""
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return parsed._replace(fragment="").geturl()


def load_json(path: Path, fallback: dict) -> dict:
    if not path.exists():
        return fallback
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return fallback
    return payload if isinstance(payload, dict) else fallback


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    tools = payload.get("tools") if isinstance(payload.get("tools"), list) else []
    if not tools:
        return ["No free tools are configured."]
    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    required = ("id", "name", "url", "source_url", "category", "format", "use", "note")
    for index, tool in enumerate(tools, start=1):
        if not isinstance(tool, dict):
            errors.append(f"Tool row {index} is not an object.")
            continue
        missing = [field for field in required if not clean_text(tool.get(field))]
        if missing:
            errors.append(f"Tool row {index} is missing: {', '.join(missing)}.")
        tool_id = clean_text(tool.get("id"))
        name_key = clean_text(tool.get("name")).casefold()
        if tool_id in seen_ids:
            errors.append(f"Duplicate tool id: {tool_id}.")
        if name_key in seen_names:
            errors.append(f"Duplicate tool name: {tool.get('name')}.")
        seen_ids.add(tool_id)
        seen_names.add(name_key)
        for field in ("url", "source_url"):
            if clean_text(tool.get(field)) and not normalized_url(tool.get(field)):
                errors.append(f"{tool.get('name') or tool_id}: {field} is not an http(s) URL.")
        access_types = tool.get("access_types") if isinstance(tool.get("access_types"), list) else []
        if not any(clean_text(value) for value in access_types):
            errors.append(f"{tool.get('name') or tool_id}: access_types must contain at least one label.")
    return errors


def page_hash(text: str, links: list[tuple[str, str]]) -> str:
    link_payload = "\n".join(f"{clean_text(label)}|{clean_text(url)}" for label, url in links)
    payload = f"{clean_text(text)}\n{link_payload}".casefold()
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def review_signal_hash(text: str, terms: list[str], candidates: list[dict] | None = None) -> str:
    if candidates is not None:
        payload = "\n".join(sorted(clean_text(item.get("url")) for item in candidates if clean_text(item.get("url"))))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
    normalized = clean_text(text).casefold()
    present_terms = sorted({term for term in terms if term in normalized})
    payload = "\n".join(present_terms) if present_terms else "expected terms not found"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def fetch_page(url: str, timeout: int) -> dict:
    if not normalized_url(url):
        return {"status": "invalid_url", "status_code": None, "final_url": url, "error": "Invalid URL."}
    request = Request(
        url,
        headers={
            "User-Agent": "StatelineGuideFreeToolsAudit/1.0 (+https://newmexicocoloradoguide.netlify.app/about/)",
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.7",
        },
        method="GET",
    )
    started = time.monotonic()
    try:
        with urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
            raw = response.read(MAX_RESPONSE_BYTES)
            encoding = response.headers.get_content_charset() or "utf-8"
            text, links = parse_page(raw.decode(encoding, errors="replace"))
            return {
                "status": "ok",
                "status_code": getattr(response, "status", None),
                "final_url": response.geturl(),
                "elapsed_ms": round((time.monotonic() - started) * 1000),
                "content_hash": page_hash(text, links),
                "text": text,
                "links": links,
                "text_length": len(text),
                "link_count": len(links),
                "error": "",
            }
    except HTTPError as exc:
        status = "access_blocked" if exc.code in BLOCKED_STATUSES else "broken" if exc.code in BROKEN_STATUSES else "http_error"
        return {"status": status, "status_code": exc.code, "final_url": url, "error": str(exc)}
    except TimeoutError as exc:
        return {"status": "timeout", "status_code": None, "final_url": url, "error": str(exc)}
    except URLError as exc:
        reason = getattr(exc, "reason", exc)
        message = str(reason)
        status = "tls_error" if isinstance(reason, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in message else "network_error"
        return {"status": status, "status_code": None, "final_url": url, "error": message}
    except Exception as exc:  # pragma: no cover - defensive network boundary
        return {"status": "error", "status_code": None, "final_url": url, "error": str(exc)}


def watch_records(payload: dict) -> list[dict]:
    records = []
    for tool in payload.get("tools") or []:
        if not isinstance(tool, dict):
            continue
        records.append(
            {
                "id": f"tool:{clean_text(tool.get('id'))}",
                "kind": "tool",
                "name": clean_text(tool.get("name")),
                "url": clean_text(tool.get("source_url") or tool.get("url")),
                "watch_terms": [clean_text(value).casefold() for value in tool.get("watch_terms") or [] if clean_text(value)],
            }
        )
    for source in payload.get("discovery_sources") or []:
        if not isinstance(source, dict):
            continue
        records.append(
            {
                "id": f"discovery:{clean_text(source.get('id'))}",
                "kind": "discovery",
                "name": clean_text(source.get("name")),
                "url": clean_text(source.get("url")),
                "candidate_terms": [clean_text(value).casefold() for value in source.get("candidate_terms") or [] if clean_text(value)],
            }
        )
    return records


def candidate_links(record: dict, final_url: str, links: list[tuple[str, str]], known_urls: set[str], limit: int = 16) -> list[dict]:
    terms = record.get("candidate_terms") or []
    if not terms:
        return []
    candidates: list[dict] = []
    seen: set[str] = set()
    for label, href in links:
        absolute = normalized_url(urljoin(final_url, clean_text(href)))
        if not absolute or absolute in seen or absolute in known_urls:
            continue
        parsed = urlparse(absolute)
        if any(token in parsed.path.casefold() for token in ("privacy", "terms", "login", "signin", "account", "contact", "support")):
            continue
        blob = f"{clean_text(label)} {parsed.path.replace('-', ' ').replace('_', ' ')}".casefold()
        matched = [term for term in terms if term in blob]
        if not matched:
            continue
        seen.add(absolute)
        candidates.append(
            {
                "title": clean_text(label) or parsed.path.rstrip("/").split("/")[-1] or parsed.netloc,
                "url": absolute,
                "matched_terms": sorted(set(matched)),
                "score": len(matched),
            }
        )
    return sorted(candidates, key=lambda item: (-item["score"], item["title"].casefold(), item["url"]))[:limit]


def audit(payload: dict, previous_state: dict, timeout: int, no_network: bool = False) -> tuple[list[dict], dict, dict]:
    records = watch_records(payload)
    previous = previous_state.get("pages") if isinstance(previous_state.get("pages"), dict) else {}
    state_pages = dict(previous)
    known_urls = {
        normalized_url(value)
        for tool in payload.get("tools") or []
        if isinstance(tool, dict)
        for value in (tool.get("url"), tool.get("source_url"))
        if normalized_url(value)
    }
    checked_at = datetime.now().astimezone().isoformat(timespec="seconds")
    results = []
    for record in records:
        prior = previous.get(record["id"]) if isinstance(previous.get(record["id"]), dict) else {}
        check = (
            {"status": "not_checked", "status_code": None, "final_url": record["url"], "error": "Network checks disabled."}
            if no_network
            else fetch_page(record["url"], timeout)
        )
        prior_hash = clean_text(prior.get("content_hash"))
        current_hash = ""
        change_status = "not_checked"
        term_hits: list[str] = []
        candidates: list[dict] = []
        new_candidates: list[dict] = []
        term_review = False
        new_term_review = False
        new_failure = False
        if check.get("status") == "ok":
            page_text = clean_text(check.get("text")).casefold()
            term_hits = [term for term in record.get("watch_terms") or [] if term in page_text]
            term_review = bool(record.get("watch_terms")) and not term_hits
            new_term_review = term_review and not bool(prior.get("term_review"))
            if record["kind"] == "discovery":
                candidates = candidate_links(record, clean_text(check.get("final_url")), check.get("links") or [], known_urls)
                prior_candidates = {clean_text(value) for value in prior.get("candidate_urls") or [] if clean_text(value)}
                new_candidates = [candidate for candidate in candidates if candidate["url"] not in prior_candidates]
            current_hash = review_signal_hash(
                page_text,
                record.get("watch_terms") or [],
                candidates if record["kind"] == "discovery" else None,
            )
            change_status = "new_baseline" if not prior_hash else "changed" if current_hash != prior_hash else "unchanged"
            state_pages[record["id"]] = {
                "kind": record["kind"],
                "name": record["name"],
                "url": record["url"],
                "last_checked": checked_at,
                "last_status": "ok",
                "status_code": check.get("status_code"),
                "content_hash": current_hash,
                "source_content_hash": check.get("content_hash", ""),
                "text_length": check.get("text_length", 0),
                "link_count": check.get("link_count", 0),
                "term_review": term_review,
                "candidate_urls": sorted(candidate["url"] for candidate in candidates),
            }
        elif not no_network:
            new_failure = check.get("status") != prior.get("last_status")
            retained = dict(prior)
            retained.update(
                {
                    "kind": record["kind"],
                    "name": record["name"],
                    "url": record["url"],
                    "last_checked": checked_at,
                    "last_status": check.get("status", "error"),
                    "status_code": check.get("status_code"),
                    "last_error": check.get("error", ""),
                }
            )
            state_pages[record["id"]] = retained
            change_status = "check_failed"
        results.append(
            {
                "record": record,
                "check": {key: value for key, value in check.items() if key not in {"text", "links"}},
                "change_status": change_status,
                "term_hits": term_hits,
                "term_review": term_review,
                "new_term_review": new_term_review,
                "new_failure": new_failure,
                "candidate_count": len(candidates),
                "candidates": new_candidates,
            }
        )
    summary = {
        "tools_configured": len(payload.get("tools") or []),
        "discovery_sources": len(payload.get("discovery_sources") or []),
        "checked_ok": sum(item["check"].get("status") == "ok" for item in results),
        "changed": sum(item["change_status"] == "changed" for item in results),
        "new_baselines": sum(item["change_status"] == "new_baseline" for item in results),
        "unchanged": sum(item["change_status"] == "unchanged" for item in results),
        "failed": sum(item["change_status"] == "check_failed" for item in results),
        "new_failures": sum(bool(item["new_failure"]) for item in results),
        "automation_blocked": sum(item["check"].get("status") in {"access_blocked", "tls_error"} for item in results),
        "term_reviews": sum(bool(item["term_review"]) for item in results),
        "new_term_reviews": sum(bool(item["new_term_review"]) for item in results),
        "candidate_links": sum(len(item["candidates"]) for item in results),
        "candidate_links_seen": sum(int(item["candidate_count"]) for item in results),
    }
    summary["review_count"] = summary["changed"] + summary["new_baselines"] + summary["new_failures"] + summary["new_term_reviews"] + summary["candidate_links"]
    state = {
        "schema_version": 1,
        "updated_at": previous_state.get("updated_at") if no_network else checked_at,
        "pages": state_pages,
    }
    return results, summary, state


def markdown_report(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# Monthly Free Tools Review",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "This is a review queue. It does not change public pricing, eligibility, or tool recommendations automatically.",
        "",
        "## Summary",
        "",
        f"- Public tools configured: {summary['tools_configured']}",
        f"- Discovery pages configured: {summary['discovery_sources']}",
        f"- Pages checked successfully: {summary['checked_ok']}",
        f"- Changed pages: {summary['changed']}",
        f"- New baselines: {summary['new_baselines']}",
        f"- Failed checks: {summary['failed']} ({summary['automation_blocked']} automation-blocked)",
        f"- Newly failed checks: {summary['new_failures']}",
        f"- Tool claims currently missing an expected term: {summary['term_reviews']} ({summary['new_term_reviews']} new)",
        f"- Candidate links found: {summary['candidate_links_seen']} ({summary['candidate_links']} new)",
        "",
        "## Review Queue",
        "",
    ]
    queue = [
        item
        for item in report["results"]
        if item["change_status"] in {"changed", "new_baseline"} or item["new_failure"] or item["new_term_review"] or item["candidates"]
    ]
    if not queue:
        lines.append("No page changes or candidate links require review this month.")
    for item in queue:
        record = item["record"]
        check = item["check"]
        lines.extend(
            [
                f"### {record['name']}",
                "",
                f"- Kind: {record['kind']}",
                f"- URL: {record['url']}",
                f"- Check: {check.get('status', 'unknown')} / {item['change_status']}",
                f"- Expected-term hits: {', '.join(item['term_hits']) or 'none'}",
            ]
        )
        if check.get("error"):
            lines.append(f"- Error: {clean_text(check['error'])}")
        if item["candidates"]:
            lines.append("- Candidate links:")
            lines.extend(f"  - [{candidate['title']}]({candidate['url']})" for candidate in item["candidates"])
        lines.append("")
    lines.extend(
        [
            "## Human Review",
            "",
            "Before changing the public inventory, confirm the official page, current free-plan or nonprofit terms, eligibility, geographic availability, data-handling implications, and whether the tool still fits a small regional team.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(report: dict, state: dict, out_dir: Path, state_path: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    dated = date.today().isoformat()
    json_text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    markdown = markdown_report(report)
    (out_dir / "free-tools-latest.json").write_text(json_text, encoding="utf-8")
    (out_dir / "free-tools-latest.md").write_text(markdown, encoding="utf-8")
    (out_dir / f"free-tools-{dated}.json").write_text(json_text, encoding="utf-8")
    (out_dir / f"free-tools-{dated}.md").write_text(markdown, encoding="utf-8")
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Review free-tool and nonprofit-offer pages without auto-publishing claims.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args()

    payload = load_json(args.data, {})
    errors = validate_payload(payload)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 2
    previous_state = load_json(args.state, {"schema_version": 1, "pages": {}})
    results, summary, state = audit(payload, previous_state, max(1, args.timeout), args.no_network)
    report = {
        "schema_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "data_file": str(args.data),
        "summary": summary,
        "results": results,
    }
    write_outputs(report, state, args.out_dir, args.state)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
