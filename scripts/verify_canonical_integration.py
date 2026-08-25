from __future__ import annotations

import argparse
import ast
from pathlib import Path
import subprocess
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools" / "build_netlify_deep_guide.py"
NETLIFY_CONFIG = ROOT / "netlify.toml"
SITE = ROOT / "dist" / "tri-county-netlify-guide-deep"

CANONICAL_NAV = (
    "Home",
    "Directory",
    "Funding",
    "Arts & Culture",
    "Promote",
    "Counties",
    "Guide",
    "Tools",
)
PROMOTE_ROUTES = (
    "events",
    "advertising",
    "businesses",
    "nonprofits",
    "calendars",
    "galleries",
)
COUNTIES = ("Colfax", "Las Animas", "Huerfano")
CANONICAL_BUILD = "python tools/build_netlify_deep_guide.py"
CANONICAL_PUBLISH = "dist/tri-county-netlify-guide-deep"
CANONICAL_PREFLIGHT = "python scripts/verify_canonical_integration.py --source-only"
CANONICAL_POSTFLIGHT = "python scripts/verify_canonical_integration.py"


def command_output(*args: str) -> str:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def current_base_sha(base_ref: str) -> tuple[str, list[str]]:
    issues: list[str] = []
    try:
        head = command_output("git", "rev-parse", "HEAD")
        base = command_output("git", "rev-parse", "--verify", base_ref)
    except (OSError, subprocess.CalledProcessError) as exc:
        return "", [f"Could not resolve the canonical Git checkpoint: {exc}"]
    if head != base:
        issues.append(
            f"HEAD {head[:12]} is not the current {base_ref} checkpoint {base[:12]}. "
            "Refresh from canonical master before generating review output."
        )
    return base, issues


def assignment_literal(source: str, name: str):
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f"Could not find literal assignment for {name}")


def ordered_labels_present(block: str, labels: tuple[str, ...]) -> bool:
    cursor = -1
    for label in labels:
        position = block.find(f'"{label}"', cursor + 1)
        if position < 0:
            return False
        cursor = position
    return True


def source_issues(generator_source: str, netlify_source: str) -> list[str]:
    issues: list[str] = []
    try:
        config = tomllib.loads(netlify_source)
    except tomllib.TOMLDecodeError as exc:
        return [f"netlify.toml is invalid: {exc}"]

    build = config.get("build", {})
    command = str(build.get("command") or "")
    publish = str(build.get("publish") or "")
    preflight_position = command.find(CANONICAL_PREFLIGHT)
    build_position = command.find(CANONICAL_BUILD, preflight_position + len(CANONICAL_PREFLIGHT))
    postflight_position = command.find(CANONICAL_POSTFLIGHT, build_position + len(CANONICAL_BUILD))
    positions = [preflight_position, build_position, postflight_position]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        issues.append(
            "Netlify must run the canonical preflight, build, and post-build guard in that order; "
            f"found {command!r}."
        )
    if publish != CANONICAL_PUBLISH:
        issues.append(f"Netlify publish directory must be {CANONICAL_PUBLISH!r}; found {publish!r}.")

    if 'SOURCE_CSV = REPO_DATA / "tri_county_persona_resources.csv"' not in generator_source:
        issues.append("Canonical CSV source path is missing from the generator.")
    if 'SOURCE_JSON = REPO_DATA / "tri_county_persona_resources.json"' not in generator_source:
        issues.append("Canonical JSON source path is missing from the generator.")

    try:
        nav_block = generator_source.split("nav_structure = [", 1)[1].split("\n    ]", 1)[0]
    except IndexError:
        issues.append("Canonical primary navigation structure could not be found.")
    else:
        if not ordered_labels_present(nav_block, CANONICAL_NAV):
            issues.append("Primary navigation does not preserve the canonical eight-section order.")
        if '"Find"' in nav_block or '"Tasks"' in nav_block:
            issues.append("Superseded Find or Tasks navigation was reintroduced.")

    try:
        route_defs = assignment_literal(generator_source, "PROMOTE_ROUTE_DEFS")
        route_keys = tuple(item.get("key") for item in route_defs)
    except (SyntaxError, ValueError, TypeError) as exc:
        issues.append(f"Promote route definitions could not be checked: {exc}")
    else:
        if route_keys != PROMOTE_ROUTES:
            issues.append(f"Promote routes must remain {PROMOTE_ROUTES!r}; found {route_keys!r}.")

    return issues


def generated_issues(index_html: str, promote_html: str) -> list[str]:
    issues: list[str] = []
    try:
        nav = index_html.split('<nav class="site-nav" aria-label="Primary navigation">', 1)[1].split(
            "</nav>", 1
        )[0]
    except IndexError:
        issues.append("Generated homepage is missing the primary navigation landmark.")
    else:
        escaped_nav = nav.replace("&amp;", "&")
        cursor = -1
        for label in CANONICAL_NAV:
            position = escaped_nav.find(label, cursor + 1)
            if position < 0:
                issues.append(f"Generated primary navigation is missing {label!r} in canonical order.")
                break
            cursor = position
        if ">Find</summary>" in nav or ">Tasks</summary>" in nav:
            issues.append("Generated navigation contains a superseded Find or Tasks menu.")

    for route in PROMOTE_ROUTES:
        for county in COUNTIES:
            query = f"county={county.replace(' ', '+')}&amp;route={route}#promotion-results"
            if query not in index_html and query not in promote_html:
                issues.append(f"Missing Promote route for {county} County / {route}.")

    return issues


def print_results(base_sha: str, issues: list[str]) -> None:
    if base_sha:
        print(f"Canonical Luna/master checkpoint: {base_sha}")
    if issues:
        for issue in issues:
            print(f"FAIL: {issue}")
        return
    print("PASS: canonical source, navigation, Promote routes, and deploy paths agree.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refuse automation output built from a stale or competing Tri-County Guide structure."
    )
    parser.add_argument("--require-current-master", action="store_true")
    parser.add_argument("--base-ref", default="origin/master")
    parser.add_argument("--source-only", action="store_true")
    args = parser.parse_args()

    issues: list[str] = []
    base_sha = ""
    if args.require_current_master:
        base_sha, git_issues = current_base_sha(args.base_ref)
        issues.extend(git_issues)

    issues.extend(
        source_issues(
            GENERATOR.read_text(encoding="utf-8"),
            NETLIFY_CONFIG.read_text(encoding="utf-8"),
        )
    )
    if not args.source_only:
        index_path = SITE / "index.html"
        promote_path = SITE / "promote" / "index.html"
        if not index_path.exists() or not promote_path.exists():
            issues.append("Canonical generated pages are missing; run the canonical build first.")
        else:
            issues.extend(
                generated_issues(
                    index_path.read_text(encoding="utf-8"),
                    promote_path.read_text(encoding="utf-8"),
                )
            )

    print_results(base_sha, issues)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
