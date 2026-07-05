# Tri-County Regional Marketing Guide

Static Netlify-ready guide for businesses, nonprofits, artists, creators, programs, and service providers working across Colfax County, Las Animas County, and Huerfano County.

## Build

```powershell
python tools/build_netlify_deep_guide.py
```

Generated site:

```text
dist/tri-county-netlify-guide-deep
```

## Update Automation Scaffold

This repo includes a conservative agentic-update scaffold:

- `data/update-source-registry.json` - generated source monitoring registry.
- `scripts/build_update_source_registry.py` - builds the monitoring registry from public guide data.
- `scripts/audit_update_sources.py` - checks monitored URLs and writes review reports.
- `scripts/audit_ui_accessibility.py` - checks generated HTML/CSS/JS for accessibility regressions in the assistant, skip link, images, and music bar.
- `scripts/normalize_netlify_submissions.py` - turns exported Netlify form submissions into a human review report.
- `.github/workflows/source-audit.yml` - scheduled non-AI grants/funding source audit.
- `.github/workflows/codex-update-proposal.yml` - disabled-by-default Codex proposal workflow.
- `docs/command-checklist.md` - local build, QA, grants-audit, GitHub, and Netlify commands.
- `docs/agentic-update-methodology.md` - governance and operating model.
- `docs/netlify-github-deploy.md` - Netlify-from-GitHub deployment path.
- `docs/openai-source-audit-summarization.md` - first OpenAI-backed feature plan.
- `docs/ponytail-incorporation.md` - how Ponytail was incorporated as a repo working rule.
- `docs/permission-setup-steps.md` - step-by-step account setup.
- `assets/audio/` - Library of Congress public-domain regional MP3 tracks used by the site music bar.

## Safe Rule

The guide should use automation to find and propose updates. It should not silently publish uncertain civic, legal, funding, contact, eligibility, or advertising claims without human approval.

## Immediate Directory Assistant

Every generated page includes a small client-side "Ask directory" assistant. It searches the same public guide data used by the Network page and returns directory shortcuts, lead-bank rows, amplifier channels, and posting paths with source links and update reminders. It does not use an API or invent answers.

## Music Bar

Every generated page includes a compact music bar with play/stop, track choice, progress, and volume controls. The tracks are public-domain regional field recordings from the Library of Congress Juan B. Rael Collection.
