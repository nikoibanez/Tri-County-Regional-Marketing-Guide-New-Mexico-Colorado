from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPAIRS = ROOT / "data" / "directory-link-repairs.json"
DEFAULT_CSV = ROOT / "data" / "tri_county_persona_resources.csv"
DEFAULT_JSON = ROOT / "data" / "tri_county_persona_resources.json"


def split_urls(value: object) -> list[str]:
    return [part.strip() for part in str(value or "").split(";") if part.strip()]


def repaired_urls(value: object, remove_urls: set[str], additions: list[str]) -> str:
    retained = [url for url in split_urls(value) if url not in remove_urls]
    return "; ".join(dict.fromkeys([*additions, *retained]))


def apply_repairs_to_rows(rows: list[dict], repairs: list[dict]) -> tuple[list[dict], list[str]]:
    rows_by_id = {str(row.get("id") or ""): row for row in rows}
    changed: list[str] = []
    missing: list[str] = []
    for repair in repairs:
        resource_id = str(repair.get("id") or "")
        row = rows_by_id.get(resource_id)
        if row is None:
            missing.append(resource_id)
            continue
        remove_urls = {str(url) for url in repair.get("remove_urls", []) if str(url)}
        replacement = str(repair.get("replacement_website") or "").strip()
        old_website = str(row.get("website") or "")
        old_source = str(row.get("source_url") or "")
        row["website"] = repaired_urls(old_website, remove_urls, [replacement] if replacement else [])
        row["source_url"] = repaired_urls(old_source, remove_urls, list(repair.get("add_source_urls", [])))
        if row["website"] != old_website or row["source_url"] != old_source:
            changed.append(resource_id)
    if missing:
        raise ValueError(f"Repair IDs not found: {', '.join(missing)}")
    return rows, changed


def load_repairs(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    repairs = payload.get("repairs")
    if not isinstance(repairs, list):
        raise ValueError(f"Expected a repairs list in {path}")
    return repairs


def load_csv(path: Path) -> tuple[list[dict], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)


def check_rows(rows: list[dict], repairs: list[dict], label: str) -> list[str]:
    rows_by_id = {str(row.get("id") or ""): row for row in rows}
    problems: list[str] = []
    for repair in repairs:
        resource_id = str(repair.get("id") or "")
        row = rows_by_id.get(resource_id)
        if row is None:
            problems.append(f"{label}: missing {resource_id}")
            continue
        combined = set(split_urls(row.get("website")) + split_urls(row.get("source_url")))
        stale = sorted(set(repair.get("remove_urls", [])) & combined)
        if stale:
            problems.append(f"{label}: {resource_id} still contains {', '.join(stale)}")
        replacement = str(repair.get("replacement_website") or "").strip()
        if replacement and replacement not in split_urls(row.get("website")):
            problems.append(f"{label}: {resource_id} is missing replacement website {replacement}")
        missing_sources = sorted(set(repair.get("add_source_urls", [])) - combined)
        if missing_sources:
            problems.append(f"{label}: {resource_id} is missing source URLs {', '.join(missing_sources)}")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply browser-reviewed directory link repairs to canonical CSV and JSON data.")
    parser.add_argument("--repairs", type=Path, default=DEFAULT_REPAIRS)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    repairs = load_repairs(args.repairs)
    csv_rows, fieldnames = load_csv(args.csv)
    json_rows = json.loads(args.json.read_text(encoding="utf-8-sig"))
    if not isinstance(json_rows, list):
        raise ValueError(f"Expected a JSON row list in {args.json}")

    if args.check:
        problems = check_rows(csv_rows, repairs, "CSV") + check_rows(json_rows, repairs, "JSON")
        if problems:
            raise SystemExit("\n".join(problems))
        print(json.dumps({"status": "ok", "repairs_checked": len(repairs)}, indent=2))
        return

    csv_rows, csv_changed = apply_repairs_to_rows(csv_rows, repairs)
    json_rows, json_changed = apply_repairs_to_rows(json_rows, repairs)
    write_csv(args.csv, csv_rows, fieldnames)
    args.json.write_text(json.dumps(json_rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "repairs": len(repairs),
                "csv_rows_changed": len(csv_changed),
                "json_rows_changed": len(json_changed),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
