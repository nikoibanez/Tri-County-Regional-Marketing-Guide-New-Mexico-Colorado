# Stateline Tri-County Guide

Static Netlify-ready guide for businesses, nonprofits, artists, creators, programs, and service providers working across Colfax County, Las Animas County, and Huerfano County.

Production origin: `https://newmexicocoloradoguide.netlify.app`

## Optional GitHub Pages Fallback

Netlify is the production deployment target. GitHub Pages remains available as a manually triggered fallback after Pages is enabled in the repository settings.

- Publish workflow: `.github/workflows/deploy-github-pages.yml`
- Trigger: manual `workflow_dispatch`
- Published folder: `dist/tri-county-netlify-guide-deep`

Routine pushes run the quality gate and let Netlify build from `master`; they do not attempt a second public deployment through GitHub Pages.

## Build

```powershell
python tools/build_netlify_deep_guide.py
python tools/apply_directory_exclusions.py --check
python scripts/validate_national_funding_data.py
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
- `data/national-funding-opportunities.json` - curated national grants, fellowships, free support programs, deadlines, applicant rules, funding ranges, fiscal-sponsor notes, and marketing-cost guidance.
- `scripts/audit_national_funding_sources.py` - compares ten national funding hubs with the previous successful snapshot and writes a human-review queue without changing public claims.
- `scripts/validate_national_funding_data.py` - checks every funding record for required decision fields, searchable keywords, URLs, and sane funding ranges.
- `data/resource-keyword-registry.json` - controlled phrases for grants, capital, fiscal sponsors, nonprofit directories, business directories, and artist opportunities.
- `data/resource-discovery-sources.json` - high-value public registries and search hubs with cadence, purpose, and automation mode.
- `scripts/audit_resource_discovery_sources.py` - watches those hubs and collects candidate links into a private review queue without changing public listings.
- `scripts/weekly_directory_query_check.py` - checks fifteen high-signal directory, tourism, events, food, venue, and chamber sources and writes an internal candidate-review queue.
- `scripts/sweep_listing_keywords.py` - refreshes controlled search-keyword suggestions from canonical fields and current public-page title, metadata, and heading signals.
- `scripts/audit_ui_accessibility.py` - checks generated HTML/CSS/JS for accessibility regressions in the assistant, skip link, images, and music bar.
- `scripts/normalize_netlify_submissions.py` - turns exported Netlify form submissions into a human review report.
- `scripts/audit_directory_quality.py` - blocks duplicate, non-entity, placeholder-description, and missing-metadata regressions.
- `scripts/audit_directory_connectivity.py` - classifies every published listing as a first-party website, hosted profile, contact-only entry, or missing online path and checks URL response status without treating bot blocks as confirmed failures.
- `scripts/audit_directory_outreach_channels.py` - reviews every published listing and directory shortcut for physical posting, directory, calendar, social-sharing, newsletter, advertising, media, sponsorship, and partner-outreach routes while separating confirmed routes from contact opportunities.
- `tools/directory_exclusions.py` - private permanent exclusion registry enforced by imports, builds, audits, and candidate sweeps.
- `tools/apply_directory_exclusions.py` - removes excluded rows from historical data artifacts and fails when public output contains one.
- `scripts/audit_internal_links.py` - checks generated routes, fragments, assets, and duplicate HTML IDs.
- `scripts/build_maintenance_dashboard.py` - combines audit counts into a private action queue.
- `scripts/smoke_test_site.py` - checks critical local or live routes without browser dependencies.
- `.github/workflows/quality-gate.yml` - builds and runs all deterministic checks on pull requests and pushes.
- `.github/workflows/source-audit.yml` - checks the complete source registry and opens a review pull request.
- `.github/workflows/weekly-national-funding-watch.yml` - checks ten national funding hubs and opens a draft review pull request when the report changes.
- `.github/workflows/weekly-resource-discovery.yml` - checks broader resource registries and opens a draft candidate-review pull request.
- `.github/workflows/weekly-directory-query-check.yml` - checks fifteen high-signal source groups and opens a candidate-review pull request.
- `.github/workflows/weekly-listing-keyword-sweep.yml` - rotates through public listing pages and opens a review pull request for search-keyword changes.
- `.github/workflows/live-site-smoke-test.yml` - checks the configured live site and opens or updates a failure issue.
- `.github/workflows/monthly-maintenance-snapshot.yml` - stores a canonical deploy zip, checksum, data files, and reports as a 90-day artifact.
- `.github/workflows/codex-update-proposal.yml` - disabled-by-default Codex proposal workflow.
- `docs/command-checklist.md` - local build, QA, grants-audit, GitHub, and Netlify commands.
- `docs/weekly-directory-query-check.md` - weekly business-directory watcher documentation.
- `docs/weekly-listing-keyword-sweep.md` - keyword taxonomy, rotation, review, and failure-retention rules.
- `docs/resource-discovery-automation.md` - source categories, review boundary, and local commands for broader resource discovery.
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
