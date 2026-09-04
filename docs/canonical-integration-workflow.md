# Canonical Integration Workflow

This repository has one public site, one generator, and one generated deploy root. Multiple Codex tasks may work concurrently, but they must converge through the same source paths and the same review flow.

## Authoritative Paths

- Generator: `tools/build_netlify_deep_guide.py`
- Directory data: `data/tri_county_persona_resources.csv` and `data/tri_county_persona_resources.json`
- Shared scripts: `scripts/`
- Shared tests: `tests/`
- Generated site: `dist/tri-county-netlify-guide-deep`
- Deploy zip: `dist/Tri_County_Regional_Marketing_Guide_Netlify_Deep.zip`

Generated HTML, CSS, JavaScript, and data exports are build products. Change their source generator or canonical data, then rebuild. Do not maintain an alternate site root or edit generated files as the source of truth.

## Authoritative Page Skeleton

Keep this primary navigation order:

1. Home
2. Directory
3. Funding
4. Arts & Culture
5. Promote
6. Counties
7. Guide
8. Tools

The Promote menu is organized by user intent: Events, Advertising + media, Business visibility, Nonprofit outreach, Calendars, and Galleries + arts. Every intent exposes Colfax, Las Animas, and Huerfano county routes. Older Home / Guide / Find / Tasks structures and city-only task menus are superseded.

The optional regional audio player belongs only on Arts & Culture. A Draft preview watermark may appear on localhost and Netlify deploy-preview hosts, but not on the production hostname.

## Concurrent Task Rules

1. Fetch `origin` and inspect open pull requests before editing shared files.
2. Use a separate worktree or review branch for each active task. Do not let two tasks edit the same dirty checkout.
3. Reuse the authoritative paths above. A new source file is justified only when it owns distinct data or behavior.
4. Reconcile useful changes into one integration pull request. Do not publish two competing navigation systems or generated deploy folders.
5. If an older task contains useful behavior, port the behavior and its regression test onto the current integration branch. Do not copy obsolete structure wholesale.
6. Run the canonical build, exclusion check, tests, JavaScript syntax check, internal-link audit, directory-quality audit, and local smoke test before review.
7. Merge only after a person reviews public claims, directory changes, eligibility language, contacts, deadlines, rates, and civic or legal guidance.

## Luna Checkpoint Rule

Luna is not a separate version of the guide. Work completed on Luna counts once it is committed and merged into canonical `master`. Uncommitted files on one computer cannot be seen by GitHub Actions or another Codex task, so they must remain in a dedicated worktree until they are reviewed and integrated.

Every workflow that prepares an automated pull request or Codex proposal must:

1. Check out `master` with full history and refresh `origin/master`.
2. Refuse to continue unless `HEAD` equals the refreshed canonical checkpoint.
3. Run `scripts/verify_canonical_integration.py --require-current-master --source-only` before collecting updates.
4. Rebuild the canonical site and run `scripts/verify_canonical_integration.py` before returning a branch, pull request, issue, or AI proposal.
5. Read the current open pull-request queue with `scripts/capture_open_pr_context.py` so overlapping review work is visible.
6. Include the canonical base commit SHA and open-review context in the review text.

This proves which accepted Luna work the automation saw. It does not authorize publication of unreviewed directory, funding, eligibility, deadline, rate, contact, civic, or legal claims.

## Baby And Luna Review Branches

GitHub records the account, repository, branch, and commit; it cannot identify a physical computer. Use `baby/<topic>` or `luna/<topic>` for ordinary review branches. Codex work may use `codex/baby-<topic>` or `codex/luna-<topic>`.

`.github/workflows/trusted-device-pr-readiness.yml` uses a read-only pull-request token and checks those branches without executing pull-request code. It requires the trusted maintainer account, the same repository, `master` as the base, the current canonical checkpoint, a non-draft pull request, and a low-risk maintenance-only diff. Changes to canonical data, generated output, visual assets, Netlify functions, or generator/tool code remain on the normal reviewed path because they can alter public claims or publication behavior.

Repository auto-merge may be enabled so an exactly approved, check-passing pull request can wait for required checks. A device name is not standing approval: every landing request still names the PR and its current head SHA. A new push invalidates the earlier landing confirmation.

## Weekly Coordination Review

The weekly Codex maintenance task uses a clean worktree and this document as its contract. It should inspect open automation and integration pull requests, identify overlapping files or superseded structures, and propose the smallest safe reconciliation. It may prepare a draft pull request for code and infrastructure changes, but it must not merge, deploy, or publish unreviewed public claims.
