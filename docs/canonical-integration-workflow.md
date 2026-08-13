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

## Weekly Coordination Review

The weekly Codex maintenance task uses a clean worktree and this document as its contract. It should inspect open automation and integration pull requests, identify overlapping files or superseded structures, and propose the smallest safe reconciliation. It may prepare a draft pull request for code and infrastructure changes, but it must not merge, deploy, or publish unreviewed public claims.
