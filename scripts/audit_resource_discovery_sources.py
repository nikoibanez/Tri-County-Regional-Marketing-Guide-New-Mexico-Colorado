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
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCES = ROOT / "data" / "resource-discovery-sources.json"
DEFAULT_KEYWORDS = ROOT / "data" / "resource-keyword-registry.json"
DEFAULT_STATE = ROOT / "data" / "resource-discovery-state.json"
DEFAULT_OUT_DIR = ROOT / "review" / "resource-discovery"
MAX_RESPONSE_BYTES = 2_000_000
CONFIRMED_BROKEN = {"broken", "invalid_url", "missing_url"}
SCRIPT_LIMITS = {"access_blocked", "tls_error"}


def clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def phrase_pattern(value: str) -> re.Pattern[str]:
    parts = [re.escape(part) for part in clean_text(value).casefold().split() if part]
    return re.compile(r"(?<![a-z0-9])" + r"\s+".join(parts) + r"(?![a-z0-9])", re.IGNORECASE)


def contains_phrase(text: str, phrase: str) -> bool:
    return bool(phrase and phrase_pattern(phrase).search(text))


class DiscoveryPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden_depth = 0
        self.parts: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._anchor_href = ""
        self._anchor_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.casefold()
        if lowered in {"script", "style", "svg", "noscript", "template"}:
            self.hidden_depth += 1
            return
        if lowered == "a" and not self.hidden_depth:
            self._anchor_href = next((value or "" for key, value in attrs if key.casefold() == "href"), "")
            self._anchor_parts = []

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.casefold()
        if lowered in {"script", "style", "svg", "noscript", "template"} and self.hidden_depth:
            self.hidden_depth -= 1
            return
        if lowered == "a" and self._anchor_href:
            self.links.append((clean_text(" ".join(self._anchor_parts)), self._anchor_href))
            self._anchor_href = ""
            self._anchor_parts = []

    def handle_data(self, data: str) -> None:
        if self.hidden_depth or not data.strip():
            return
        self.parts.append(data)
        if self._anchor_href:
            self._anchor_parts.append(data)


def parse_page(markup: str) -> tuple[str, list[tuple[str, str]]]:
    parser = DiscoveryPageParser()
    parser.feed(markup)
    return clean_text(" ".join(parser.parts)), parser.links


def content_hash(text: str, links: list[tuple[str, str]]) -> str:
    link_text = "\n".join(f"{clean_text(label)}|{clean_text(url)}" for label, url in links)
    payload = f"{clean_text(text)}\n{link_text}".casefold()
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def category_terms(source: dict, keyword_groups: dict[str, dict]) -> tuple[list[str], list[str], list[str], list[str]]:
    group = keyword_groups.get(str(source.get("category") or ""), {})
    includes = [clean_text(item) for item in group.get("include_phrases") or [] if clean_text(item)]
    queries = [clean_text(item) for item in source.get("query_groups") or [] if clean_text(item)]
    decisions = [clean_text(item) for item in group.get("decision_terms") or [] if clean_text(item)]
    excludes = [clean_text(item) for item in group.get("exclude_phrases") or [] if clean_text(item)]
    return includes, queries, decisions, excludes


def extract_candidates(
    source: dict,
    base_url: str,
    links: list[tuple[str, str]],
    keyword_groups: dict[str, dict],
    limit: int = 24,
) -> list[dict]:
    includes, queries, decisions, excludes = category_terms(source, keyword_groups)
    candidates: list[dict] = []
    seen: set[str] = set()
    for label, href in links:
        absolute = urljoin(base_url, clean_text(href))
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            continue
        normalized_url = parsed._replace(fragment="").geturl()
        if normalized_url in seen or normalized_url.rstrip("/") == base_url.rstrip("/"):
            continue
        blob = f"{clean_text(label)} {parsed.path.replace('-', ' ').replace('_', ' ')}".casefold()
        if any(contains_phrase(blob, phrase) for phrase in excludes):
            continue
        matched = [phrase for phrase in includes if contains_phrase(blob, phrase)]
        query_hits = [phrase for phrase in queries if contains_phrase(blob, phrase)]
        decision_hits = [phrase for phrase in decisions if contains_phrase(blob, phrase)]
        query_only_allowed = source.get("automation_mode") == "bulk_csv" and bool(query_hits)
        if not matched and not query_only_allowed:
            continue
        seen.add(normalized_url)
        score = len(matched) * 3 + len(query_hits) * 2 + len(decision_hits)
        if parsed.netloc.casefold() == urlparse(base_url).netloc.casefold():
            score += 1
        candidates.append(
            {
                "title": clean_text(label) or parsed.path.rstrip("/").split("/")[-1] or parsed.netloc,
                "url": normalized_url,
                "score": score,
                "matched_terms": sorted(set(matched + query_hits + decision_hits), key=str.casefold)[:10],
            }
        )
    return sorted(candidates, key=lambda item: (-item["score"], item["title"].casefold(), item["url"]))[:limit]


def fetch_source(source: dict, keyword_groups: dict[str, dict], timeout: int) -> dict:
    url = clean_text(source.get("url"))
    if not url:
        return {"status": "missing_url", "status_code": None, "final_url": "", "error": "No URL configured.", "candidates": []}
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {"status": "invalid_url", "status_code": None, "final_url": url, "error": "URL must include an http(s) scheme and host.", "candidates": []}
    request = Request(
        url,
        headers={
            "User-Agent": "StatelineGuideResourceDiscovery/1.0 (+https://statelineguide.org/about/)",
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
            text, links = parse_page(markup)
            final_url = response.geturl()
            return {
                "status": "ok",
                "status_code": getattr(response, "status", None),
                "final_url": final_url,
                "elapsed_ms": round((time.monotonic() - started) * 1000),
                "content_hash": content_hash(text, links),
                "text_length": len(text),
                "link_count": len(links),
                "candidates": extract_candidates(source, final_url, links, keyword_groups),
                "error": "",
            }
    except HTTPError as exc:
        status = "access_blocked" if exc.code in {401, 403, 406, 429} else "broken" if exc.code in {404, 410} else "http_error"
        return {"status": status, "status_code": exc.code, "final_url": url, "error": str(exc), "candidates": []}
    except TimeoutError as exc:
        return {"status": "timeout", "status_code": None, "final_url": url, "error": str(exc), "candidates": []}
    except URLError as exc:
        reason_value = getattr(exc, "reason", exc)
        reason = str(reason_value)
        status = "tls_error" if isinstance(reason_value, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in reason else "network_error"
        return {"status": status, "status_code": None, "final_url": url, "error": reason, "candidates": []}
    except Exception as exc:
        return {"status": "error", "status_code": None, "final_url": url, "error": str(exc), "candidates": []}


def load_json(path: Path, fallback: dict) -> dict:
    if not path.exists():
        return fallback
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return fallback
    return payload if isinstance(payload, dict) else fallback


def keyword_group_map(payload: dict) -> dict[str, dict]:
    return {
        str(item.get("id") or ""): item
        for item in payload.get("groups") or []
        if isinstance(item, dict) and item.get("id")
    }


def audit_sources(
    sources: list[dict],
    keyword_groups: dict[str, dict],
    previous_state: dict,
    timeout: int,
    no_network: bool = False,
) -> tuple[list[dict], dict]:
    previous_entries = previous_state.get("sources") if isinstance(previous_state.get("sources"), dict) else {}
    state_entries: dict[str, dict] = dict(previous_entries)
    results: list[dict] = []
    checked_at = datetime.now().astimezone().isoformat(timespec="seconds")
    for source in sources:
        source_id = clean_text(source.get("id"))
        previous = previous_entries.get(source_id) if isinstance(previous_entries.get(source_id), dict) else {}
        check = (
            {"status": "not_checked", "status_code": None, "final_url": source.get("url", ""), "error": "Network checks were disabled.", "candidates": []}
            if no_network
            else fetch_source(source, keyword_groups, timeout)
        )
        prior_hash = clean_text(previous.get("content_hash"))
        current_hash = clean_text(check.get("content_hash"))
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
                "link_count": check.get("link_count", 0),
                "candidate_count": len(check.get("candidates") or []),
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
    return results, {
        "schema_version": 1,
        "updated_at": checked_at if not no_network else previous_state.get("updated_at"),
        "sources": state_entries,
    }


def summarize(results: list[dict]) -> dict:
    status_counts: dict[str, int] = {}
    change_counts: dict[str, int] = {}
    categories: dict[str, int] = {}
    for result in results:
        status = clean_text(result["check"].get("status")) or "error"
        change = clean_text(result.get("change_status")) or "unknown"
        category = clean_text(result["source"].get("category")) or "uncategorized"
        status_counts[status] = status_counts.get(status, 0) + 1
        change_counts[change] = change_counts.get(change, 0) + 1
        categories[category] = categories.get(category, 0) + 1
    return {
        "sources": len(results),
        "checked": sum(1 for result in results if result["check"].get("status") != "not_checked"),
        "changed": change_counts.get("changed", 0),
        "new_baselines": change_counts.get("new_baseline", 0),
        "candidate_links": sum(len(result["check"].get("candidates") or []) for result in results),
        "confirmed_broken": sum(1 for result in results if result["check"].get("status") in CONFIRMED_BROKEN),
        "script_access_limited": sum(1 for result in results if result["check"].get("status") in SCRIPT_LIMITS),
        "check_failures": change_counts.get("check_failed", 0),
        "categories": dict(sorted(categories.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "change_counts": dict(sorted(change_counts.items())),
    }


def write_markdown(payload: dict, path: Path, title: str = "Resource Discovery Review") -> None:
    summary = payload["summary"]
    lines = [
        f"# {clean_text(title) or 'Resource Discovery Review'}",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "This is a private candidate queue. A link or page change is not proof that a resource fits the guide or that an opportunity is open.",
        "",
        "## Summary",
        "",
        f"- Source hubs configured: {summary['sources']}",
        f"- Source hubs checked: {summary['checked']}",
        f"- Candidate links collected: {summary['candidate_links']}",
        f"- Changed pages: {summary['changed']}",
        f"- New baselines: {summary['new_baselines']}",
        f"- Confirmed broken URLs: {summary['confirmed_broken']}",
        f"- Script-access limitations: {summary['script_access_limited']}",
        f"- Other check failures: {summary['check_failures']}",
        "",
        "## Candidate Links",
        "",
    ]
    candidate_results = [result for result in payload["results"] if result["check"].get("candidates")]
    if not candidate_results:
        lines.append("No candidate link was collected in this run.")
    for result in candidate_results:
        source = result["source"]
        lines.extend(
            [
                f"### [{source['name']}]({source['url']})",
                "",
                f"Category: {source.get('category', 'uncategorized')}. Page status: {result['change_status']}.",
                "",
            ]
        )
        for candidate in result["check"].get("candidates") or []:
            terms = ", ".join(candidate.get("matched_terms") or [])
            lines.append(f"- [{candidate['title']}]({candidate['url']}) - matched: {terms or 'source query terms'}")
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
    parser = argparse.ArgumentParser(description="Watch resource hubs and collect review-only candidate links.")
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--keywords", type=Path, default=DEFAULT_KEYWORDS)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--timeout", type=int, default=18)
    parser.add_argument("--report-slug", default="resource-discovery")
    parser.add_argument("--report-title", default="Resource Discovery Review")
    parser.add_argument("--no-network", action="store_true")
    parser.add_argument("--fail-on-broken", action="store_true")
    args = parser.parse_args()

    report_slug = clean_text(args.report_slug).casefold()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", report_slug):
        raise SystemExit("Report slug must contain lowercase letters, numbers, or hyphens.")

    source_payload = load_json(args.sources, {})
    keyword_payload = load_json(args.keywords, {})
    sources = [item for item in source_payload.get("sources") or [] if isinstance(item, dict)]
    keyword_groups = keyword_group_map(keyword_payload)
    if not sources:
        raise SystemExit("No resource-discovery sources are configured.")
    missing_categories = sorted({clean_text(item.get("category")) for item in sources if clean_text(item.get("category")) not in keyword_groups})
    if missing_categories:
        raise SystemExit(f"Sources use missing keyword groups: {', '.join(missing_categories)}")

    previous_state = load_json(args.state, {"schema_version": 1, "sources": {}})
    results, state = audit_sources(sources, keyword_groups, previous_state, args.timeout, args.no_network)
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "review_policy": source_payload.get("review_policy", "Human review is required before public claims change."),
        "summary": summarize(results),
        "results": results,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    latest_json = args.out_dir / f"{report_slug}-latest.json"
    latest_md = args.out_dir / f"{report_slug}-latest.md"
    dated_json = args.out_dir / f"{report_slug}-{date.today().isoformat()}.json"
    dated_md = args.out_dir / f"{report_slug}-{date.today().isoformat()}.md"
    latest_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(payload, latest_md, args.report_title)
    shutil.copy2(latest_json, dated_json)
    shutil.copy2(latest_md, dated_md)
    if not args.no_network:
        args.state.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(latest_md), "summary": payload["summary"]}, indent=2))
    if args.fail_on_broken and payload["summary"]["confirmed_broken"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
