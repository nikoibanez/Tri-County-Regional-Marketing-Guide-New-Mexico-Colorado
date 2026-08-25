from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
TRUSTED_ACTORS = {"nikoibanez"}
TRUSTED_BRANCH = re.compile(
    r"^(?:baby|luna)/[a-z0-9][a-z0-9._/-]*$|^codex/(?:baby|luna)-[a-z0-9][a-z0-9._-]*$"
)
SAFE_EXACT_PATHS = {
    ".gitignore",
    "README.md",
}
SAFE_PREFIXES = (
    "docs/",
    "review/",
    "scripts/",
    "tests/",
)
PUBLIC_REVIEW_PREFIXES = (
    ".github/",
    "assets/",
    "data/",
    "dist/",
    "netlify/functions/",
    "tools/",
)
PUBLIC_REVIEW_EXACT_PATHS = {
    "AGENTS.md",
    "docs/canonical-integration-workflow.md",
    "netlify.toml",
    "scripts/check_trusted_device_pr.py",
    "scripts/verify_canonical_integration.py",
}


def changed_files(base_sha: str, head_sha: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_sha}...{head_sha}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted({line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()})


def classify_paths(paths: list[str]) -> tuple[list[str], list[str]]:
    eligible: list[str] = []
    review_required: list[str] = []
    for path in paths:
        if path in PUBLIC_REVIEW_EXACT_PATHS:
            review_required.append(path)
            continue
        if path in SAFE_EXACT_PATHS or path.startswith(SAFE_PREFIXES):
            eligible.append(path)
            continue
        if path.startswith(PUBLIC_REVIEW_PREFIXES):
            review_required.append(path)
            continue
        review_required.append(path)
    return eligible, review_required


def policy_issues(
    *,
    actor: str,
    base_ref: str,
    head_ref: str,
    repo_full_name: str,
    head_repo_full_name: str,
    is_draft: bool,
    base_is_ancestor: bool,
    paths: list[str],
) -> list[str]:
    issues: list[str] = []
    if actor not in TRUSTED_ACTORS:
        issues.append(f"Actor {actor!r} is not in the trusted maintainer allowlist.")
    if base_ref != "master":
        issues.append(f"Base branch must be 'master'; found {base_ref!r}.")
    if not TRUSTED_BRANCH.fullmatch(head_ref):
        issues.append(
            "Head branch must identify the originating computer with baby/<topic>, "
            "luna/<topic>, codex/baby-<topic>, or codex/luna-<topic>."
        )
    if repo_full_name != head_repo_full_name:
        issues.append("Trusted-device review branches must come from this repository, not a fork.")
    if is_draft:
        issues.append("The pull request is still a draft.")
    if not base_is_ancestor:
        issues.append("The pull-request head does not contain the current canonical master checkpoint.")
    if not paths:
        issues.append("No changed files were found.")
    _, review_required = classify_paths(paths)
    if review_required:
        issues.append(
            "These paths can affect the public site, source data, claims, or publication behavior and need "
            "per-PR review: " + ", ".join(review_required)
        )
    return issues


def git_is_ancestor(base_sha: str, head_sha: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", base_sha, head_sha],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check whether a Baby/Luna pull request is eligible for the low-risk landing path."
    )
    parser.add_argument("--actor", required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--head-ref", required=True)
    parser.add_argument("--repo-full-name", required=True)
    parser.add_argument("--head-repo-full-name", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--draft", action="store_true")
    args = parser.parse_args()

    try:
        paths = changed_files(args.base_sha, args.head_sha)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"FAIL: could not inspect the pull-request diff: {exc}")
        return 1

    issues = policy_issues(
        actor=args.actor,
        base_ref=args.base_ref,
        head_ref=args.head_ref,
        repo_full_name=args.repo_full_name,
        head_repo_full_name=args.head_repo_full_name,
        is_draft=args.draft,
        base_is_ancestor=git_is_ancestor(args.base_sha, args.head_sha),
        paths=paths,
    )
    print(f"Trusted-device head: {args.head_ref} @ {args.head_sha}")
    print(f"Canonical base: {args.base_ref} @ {args.base_sha}")
    if issues:
        for issue in issues:
            print(f"REVIEW REQUIRED: {issue}")
        return 1
    print("PASS: trusted maintainer, device-marked branch, current master, and low-risk file scope agree.")
    print("This check establishes readiness only; landing still requires exact PR number and current head confirmation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
