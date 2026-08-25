from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import ssl
import time
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCES = ROOT / "data" / "national-funding-watch-sources.json"
DEFAULT_STATE = ROOT / "data" / "national-funding-watch-state.json"
DEFAULT_OUT_DIR = ROOT / "review" / "national-funding-watch"
MAX_RESPONSE_BYTES = 2_000_000
SIGNAL_TERMS = (
    "deadline",
    "applications open",
    "apply by",
    "eligibility",
    "eligible applicant",
    "fiscal sponsor",
    "501(c)(3)",
    "501c3",
    "award amount",
    "funding range",
    "grant amount",
    "matching funds",
    "cost share",
    "application fee",
    "free to apply",
    "marketing",
    "advertising",
)
CONFIRMED_BROKEN = {"broken", "invalid_url", "missing_url"}
SCRIPT_LIMITS = {"access_blocked", "tls_error"}
SWEEP_TOPIC_LABELS = {
    "economic-development": "Economic development",
    "education": "Education",
    "healthcare": "Healthcare",
    "nonprofits": "Nonprofits",
    "arts-culture": "Arts & culture",
}


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "svg", "noscript", "template"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "svg", "noscript", "template"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth and data.strip():
            self.parts.append(data)


def normalize_page_text(markup: str) -> str:
    parser = VisibleTextParser()
    parser.feed(markup)
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def content_hash(text: str) -> str:
    return hashlib.sha256(text.casefold().encode("utf-8")).hexdigest()


def extract_signal_snippets(text: str, limit: int = 24) -> list[str]:
    if not text:
        return []
    fragments = re.split(r"(?<=[.!?])\s+|\s*[|]\s*", text)
    snippets: list[str] = []
    seen: set[str] = set()
    for fragment in fragments:
        clean = re.sub(r"\s+", " ", fragment).strip()
        lowered = clean.casefold()
        if not clean or not any(term.casefold() in lowered for term in SIGNAL_TERMS):
            continue
        clean = clean[:420].rstrip()
        key = clean.casefold()
        if key in seen:
            continue
        seen.add(key)
        snippets.append(clean)
        if len(snippets) >= limit:
            break
    return snippets


def fetch_source(source: dict, timeout: int) -> dict:
    url = str(source.get("url") or "").strip()
    if not url:
        return {"status": "missing_url", "status_code": None, "final_url": "", "error": "No URL configured."}
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {"status": "invalid_url", "status_code": None, "final_url": url, "error": "URL must include an http(s) scheme and host."}

    request = Request(
        url,
        headers={
            "User-Agent": "StatelineGuideFundingWatch/1.0 (+https://newmexicocoloradoguide.netlify.app/about/)",
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.7",
        },
        method="GET",
    )
    started = time.monotonic()
    try:
        with urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
            raw = response.read(MAX_RESPONSE_BYTES)
            encoding = response.headers.get_content_charset() or "utf-8"
            markup = raw.decode(encoding, errors="replace")
            text = normalize_page_text(markup)
            return {
                "status": "ok",
                "status_code": getattr(response, "status", None),
                "final_url": response.geturl(),
                "elapsed_ms": round((time.monotonic() - started) * 1000),
                "content_hash": content_hash(text),
                "text_length": len(text),
                "signal_snippets": extract_signal_snippets(text),
                "error": "",
            }
    except HTTPError as exc:
        status = "access_blocked" if exc.code in {401, 403, 406, 429} else "broken" if exc.code in {404, 410} else "http_error"
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


def load_json(path: Path, fallback: dict) -> dict:
    if not path.exists():
        return fallback
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return fallback
    return payload if isinstance(payload, dict) else fallback


def audit_sources(sources: list[dict], previous_state: dict, timeout: int, no_network: bool = False) -> tuple[list[dict], dict]:
    previous_entries = previous_state.get("sources") if isinstance(previous_state.get("sources"), dict) else {}
    state_entries: dict[str, dict] = dict(previous_entries)
    results = []
    checked_at = datetime.now().astimezone().isoformat(timespec="seconds")

    for source in sources:
        source_id = str(source.get("id") or "")
        previous = previous_entries.get(source_id) if isinstance(previous_entries.get(source_id), dict) else {}
        check = (
            {"status": "not_checked", "status_code": None, "final_url": source.get("url", ""), "error": "Network checks were disabled."}
            if no_network
            else fetch_source(source, timeout)
        )
        prior_hash = str(previous.get("content_hash") or "")
        current_hash = str(check.get("content_hash") or "")
        change_status = "not_checked"
        if check.get("status") == "ok":
            change_status = "new_baseline" if not prior_hash else "changed" if prior_hash != current_hash else "unchanged"
            state_entries[source_id] = {
                "name": source.get("name", ""),
                "url": source.get("url", ""),
                "last_checked": checked_at,
                "last_status": "ok",
                "status_code": check.get("status_code"),
                "content_hash": current_hash,
                "text_length": check.get("text_length", 0),
                "signal_snippets": check.get("signal_snippets", []),
            }
        elif not no_network:
            retained = dict(previous)
            retained.update(
                {
                    "name": source.get("name", ""),
                    "url": source.get("url", ""),
                    "last_checked": checked_at,
                    "last_status": check.get("status", "error"),
                    "status_code": check.get("status_code"),
                    "last_error": check.get("error", ""),
                }
            )
            state_entries[source_id] = retained
            change_status = "check_failed"
        results.append({"source": source, "check": check, "change_status": change_status, "previous_hash": prior_hash})

    state = {
        "schema_version": 1,
        "updated_at": checked_at if not no_network else previous_state.get("updated_at"),
        "sources": state_entries,
    }
    return results, state


def validate_watch_registry(payload: dict) -> list[str]:
    errors: list[str] = []
    sources = payload.get("sources") or []
    required_sweeps = payload.get("required_sweeps") or []
    sweep_ids = {
        str(item.get("id") or "")
        for item in required_sweeps
        if isinstance(item, dict)
    }
    if sweep_ids != set(SWEEP_TOPIC_LABELS):
        errors.append("The watch registry must configure all five required subject sweeps.")
    if not sources:
        errors.append("The watch registry has no sources.")
    covered: set[str] = set()
    for source in sources:
        source_id = str(source.get("id") or "<missing id>")
        topics = source.get("sweep_topics") or []
        if not topics:
            errors.append(f"{source_id} has no sweep_topics values.")
            continue
        unsupported = sorted(set(topics) - set(SWEEP_TOPIC_LABELS))
        if unsupported:
            errors.append(f"{source_id} has unsupported sweep topics: {', '.join(unsupported)}.")
        covered.update(set(topics) & set(SWEEP_TOPIC_LABELS))
    missing = sorted(set(SWEEP_TOPIC_LABELS) - covered)
    if missing:
        errors.append(f"The source registry does not cover: {', '.join(missing)}.")
    return errors


def summarize(results: list[dict]) -> dict:
    status_counts: dict[str, int] = {}
    change_counts: dict[str, int] = {}
    for result in results:
        status = str(result["check"].get("status") or "error")
        change = str(result.get("change_status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        change_counts[change] = change_counts.get(change, 0) + 1
    sweep_counts: dict[str, dict[str, int]] = {}
    for topic_id, label in SWEEP_TOPIC_LABELS.items():
        topic_results = [
            result
            for result in results
            if topic_id in (result["source"].get("sweep_topics") or [])
        ]
        sweep_counts[topic_id] = {
            "label": label,
            "configured": len(topic_results),
            "checked": sum(1 for result in topic_results if result["check"].get("status") != "not_checked"),
            "ok": sum(1 for result in topic_results if result["check"].get("status") == "ok"),
            "changed": sum(1 for result in topic_results if result.get("change_status") == "changed"),
            "new_baselines": sum(1 for result in topic_results if result.get("change_status") == "new_baseline"),
            "check_failures": sum(1 for result in topic_results if result.get("change_status") == "check_failed"),
        }
    return {
        "sources": len(results),
        "checked": sum(1 for result in results if result["check"].get("status") != "not_checked"),
        "changed": change_counts.get("changed", 0),
        "new_baselines": change_counts.get("new_baseline", 0),
        "confirmed_broken": sum(1 for result in results if result["check"].get("status") in CONFIRMED_BROKEN),
        "script_access_limited": sum(1 for result in results if result["check"].get("status") in SCRIPT_LIMITS),
        "check_failures": change_counts.get("check_failed", 0),
        "status_counts": dict(sorted(status_counts.items())),
        "change_counts": dict(sorted(change_counts.items())),
        "sweep_counts": sweep_counts,
    }


def write_markdown(payload: dict, path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# Regional and National Funding Source Watch",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "This is a private review queue. A detected page change is not a verified deadline, eligibility rule, or award announcement.",
        "",
        "## Summary",
        "",
        f"- Sources configured: {summary['sources']}",
        f"- Sources checked: {summary['checked']}",
        f"- Pages changed since the previous successful check: {summary['changed']}",
        f"- New baselines: {summary['new_baselines']}",
        f"- Confirmed broken URLs: {summary['confirmed_broken']}",
        f"- Script-access limitations (not broken): {summary['script_access_limited']}",
        f"- Other check failures: {summary['check_failures']}",
        "",
        "## Separate Subject Sweeps",
        "",
    ]
    for topic_id, counts in summary["sweep_counts"].items():
        source_names = [
            result["source"].get("name", result["source"].get("id", "Unnamed source"))
            for result in payload["results"]
            if topic_id in (result["source"].get("sweep_topics") or [])
        ]
        lines.extend(
            [
                f"### {counts['label']}",
                "",
                (
                    f"Configured {counts['configured']}; checked {counts['checked']}; "
                    f"successful {counts['ok']}; changed {counts['changed']}; "
                    f"new baselines {counts['new_baselines']}; failed checks {counts['check_failures']}."
                ),
                "",
                "Sources: " + "; ".join(source_names) + ".",
                "",
            ]
        )
    lines.extend([
        "## Review First",
        "",
    ])
    review_items = [result for result in payload["results"] if result["change_status"] in {"changed", "new_baseline"}]
    if not review_items:
        lines.append("No changed page is waiting for funding-claim review.")
    else:
        for result in review_items:
            source = result["source"]
            check = result["check"]
            lines.append(f"### [{source['name']}]({source['url']})")
            lines.append("")
            sweep_labels = [SWEEP_TOPIC_LABELS[value] for value in source.get("sweep_topics") or []]
            lines.append(
                f"Change status: {result['change_status']}. "
                f"Sweeps: {', '.join(sweep_labels)}. Focus: {', '.join(source.get('focus') or [])}."
            )
            lines.append("")
            snippets = check.get("signal_snippets") or []
            if snippets:
                lines.append("Possible deadline, eligibility, fee, or award language to inspect:")
                lines.append("")
                lines.extend(f"- {snippet}" for snippet in snippets[:12])
            else:
                lines.append("The page changed, but the text extractor found no targeted funding phrase. Review the page normally.")
            lines.append("")
    lines.extend(["## Check Problems", ""])
    problems = [result for result in payload["results"] if result["change_status"] == "check_failed"]
    if not problems:
        lines.append("No source check failed.")
    else:
        for result in problems:
            source = result["source"]
            check = result["check"]
            lines.append(f"- [{source['name']}]({source['url']}) - {check.get('status')}; {check.get('error') or 'no error detail'}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run five subject-specific regional and national funding sweeps and create a human-review report.")
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--timeout", type=int, default=18)
    parser.add_argument("--no-network", action="store_true")
    parser.add_argument("--fail-on-broken", action="store_true")
    args = parser.parse_args()

    source_payload = load_json(args.sources, {})
    sources = source_payload.get("sources") or []
    registry_errors = validate_watch_registry(source_payload)
    if registry_errors:
        raise SystemExit("Invalid funding watch registry:\n- " + "\n- ".join(registry_errors))
    previous_state = load_json(args.state, {"schema_version": 1, "sources": {}})
    results, state = audit_sources(sources, previous_state, args.timeout, args.no_network)
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "review_policy": source_payload.get("review_policy", "Human review is required before public funding claims change."),
        "summary": summarize(results),
        "results": results,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    latest_json = args.out_dir / "national-funding-watch-latest.json"
    latest_md = args.out_dir / "national-funding-watch-latest.md"
    dated_json = args.out_dir / f"national-funding-watch-{date.today().isoformat()}.json"
    dated_md = args.out_dir / f"national-funding-watch-{date.today().isoformat()}.md"
    latest_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(payload, latest_md)
    shutil.copy2(latest_json, dated_json)
    shutil.copy2(latest_md, dated_md)
    if not args.no_network:
        args.state.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(latest_md), "summary": payload["summary"]}, indent=2))

    if args.fail_on_broken and payload["summary"]["confirmed_broken"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
