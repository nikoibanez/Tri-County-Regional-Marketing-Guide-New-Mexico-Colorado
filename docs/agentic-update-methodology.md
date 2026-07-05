# Agentic Update Methodology

## Purpose

The guide should stay useful without pretending that automation can replace local judgment. Codex can watch sources, compare data, draft updates, and prepare review reports. Human reviewers approve public claims before production deployment.

## Operating Loop

1. Watch source pages and user submissions.
2. Compare against the current source registry.
3. Classify changes by risk.
4. Draft a review report, source-audit summary, or pull request.
5. Preview changes on Netlify.
6. Human reviewer approves, edits, or rejects.
7. Merge and deploy.

## Update Categories

### Safe To Automate As Reports

- Broken link checks.
- Redirect detection.
- Missing source URLs.
- Stale `last_checked` dates.
- New Netlify form submissions.
- Draft review queues.
- Proposed source-registry changes.

### Human Approval Required

- Grant eligibility.
- Award amounts or deadlines.
- Free vs paid placement.
- Advertising availability.
- Public notice rules.
- Business licensing or permit guidance.
- Contact changes.
- Listing removal.
- Claims that an organization is inactive.
- Any endorsement-like wording.

## Source Registry

The registry lives at:

```text
data/update-source-registry.json
```

Build it with:

```powershell
python tools/build_netlify_deep_guide.py
python scripts/build_update_source_registry.py
```

Audit it with:

```powershell
python scripts/audit_update_sources.py --limit 120
```

Reports are written to:

```text
review/update-audits/
```

The first active monitor group is grants/funding:

```powershell
python scripts/audit_update_sources.py --domain funding
```

## Submission Review

The public site already includes a Netlify-ready submission form on `/submit/`. Export Netlify form submissions as CSV, then run:

```powershell
python scripts/normalize_netlify_submissions.py path\to\netlify-submissions.csv
```

Reports are written to:

```text
review/submission-review/
```

## Recommended Cadence

- Daily or twice weekly: review submissions.
- Weekly: audit funding, grants, scholarships, and stipends first.
- Later weekly expansion: calendars, event paths, and media routes.
- Monthly: audit chambers, tourism, directories, economic-development resources, and creative districts.
- Quarterly: review public copy, labels, and methodology.

## Approval Model

Use GitHub pull requests for public changes. Use Netlify Deploy Previews for visual review. Merge only after a person confirms the change is accurate enough for public use.

## First OpenAI Feature

The first OpenAI-backed feature should summarize the source-audit report, starting with grants/funding sources. It should produce a review summary and next actions; it should not publish public claims or alter source data without human approval.
