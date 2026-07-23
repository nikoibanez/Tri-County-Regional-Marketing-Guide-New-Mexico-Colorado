# Tri-County Regional Marketing Guide

Static Netlify-ready guide for businesses, nonprofits, artists, creators, programs, and service providers working across Colfax County, Las Animas County, and Huerfano County.

## Optional GitHub Pages Fallback

Netlify is the production deployment target. GitHub Pages remains available as a manually triggered fallback after Pages is enabled in the repository settings.

- Publish workflow: `.github/workflows/deploy-github-pages.yml`
- Trigger: manual `workflow_dispatch`
- Published folder: `dist/tri-county-netlify-guide-deep`

Routine pushes run the quality gate and let Netlify build from `master`; they do not attempt a second public deployment through GitHub Pages.

## Build

```powershell
python tools/build_netlify_deep_guide.py
```

Generated site:

```text
dist/tri-county-netlify-guide-deep
```

## Maintenance Automation

This repo includes a no-secret maintenance system. Deterministic scripts build, test, watch sources, and prepare review queues. They do not silently promote uncertain public claims into the guide.

- `data/update-source-registry.json` - generated source monitoring registry.
- `scripts/build_update_source_registry.py` - builds the monitoring registry from public guide data.
- `scripts/audit_update_sources.py` - checks monitored URLs and writes review reports.
- `scripts/weekly_directory_query_check.py` - checks fifteen high-signal directory, tourism, events, food, venue, and chamber sources and writes an internal candidate-review queue.
- `scripts/audit_ui_accessibility.py` - checks generated HTML/CSS/JS for accessibility regressions in the assistant, skip link, images, and music bar.
- `scripts/normalize_netlify_submissions.py` - turns exported Netlify form submissions into a human review report.
- `scripts/audit_directory_quality.py` - blocks duplicate, non-entity, placeholder-description, and missing-metadata regressions.
- `scripts/audit_internal_links.py` - checks generated routes, fragments, assets, and duplicate HTML IDs.
- `scripts/build_maintenance_dashboard.py` - combines audit counts into a private action queue.
- `scripts/smoke_test_site.py` - checks critical local or live routes without browser dependencies.
- `.github/workflows/quality-gate.yml` - builds and runs all deterministic checks on pull requests and pushes.
- `.github/workflows/source-audit.yml` - checks the complete source registry and opens a review pull request.
- `.github/workflows/weekly-directory-query-check.yml` - checks fifteen high-signal source groups and opens a candidate-review pull request.
- `.github/workflows/live-site-smoke-test.yml` - checks the configured live site and opens or updates a failure issue.
- `.github/workflows/monthly-maintenance-snapshot.yml` - stores a canonical deploy zip, checksum, data files, and reports as a 90-day artifact.
- `.github/workflows/codex-update-proposal.yml` - disabled-by-default Codex proposal workflow.
- `docs/command-checklist.md` - local build, QA, grants-audit, GitHub, and Netlify commands.
- `docs/weekly-directory-query-check.md` - weekly business-directory watcher documentation.
- `docs/maintenance-automation.md` - schedules, review boundaries, and account settings for the no-secret maintenance system.
- `docs/agentic-update-methodology.md` - governance and operating model.
- `docs/netlify-github-deploy.md` - Netlify-from-GitHub deployment path.
- `docs/openai-source-audit-summarization.md` - first OpenAI-backed feature plan.
- `docs/ponytail-incorporation.md` - how Ponytail was incorporated as a repo working rule.
- `docs/permission-setup-steps.md` - step-by-step account setup.
- `assets/audio/` - Library of Congress public-domain regional MP3 tracks used by the site music bar.

## Safe Rule

The guide should use automation to find and propose updates. It should not silently publish uncertain civic, legal, funding, contact, eligibility, or advertising claims without human approval.

GitHub Actions can autonomously rebuild the site, run checks, archive snapshots, open review pull requests, and report live failures. Merging public data changes remains a human decision.

## Immediate Directory Assistant

Every generated page includes a small client-side "Ask directory" assistant. It searches the same public guide data used by the Network page and returns directory shortcuts, lead-bank rows, amplifier channels, and posting paths with source links and update reminders. It does not use an API or invent answers.

## Music Bar

Every generated page includes a compact music bar with play/stop, track choice, progress, and volume controls. The tracks are public-domain regional field recordings from the Library of Congress Juan B. Rael Collection.
