# Tri-County Guide Agent Instructions

This repository builds the Northern New Mexico and Southern Colorado Tri-County Regional Marketing Guide.

## Canonical Build

- Source generator: `tools/build_netlify_deep_guide.py`
- Source data: `data/tri_county_persona_resources.csv` and `data/tri_county_persona_resources.json`
- Generated site: `dist/tri-county-netlify-guide-deep`
- Deploy zip: `dist/Tri_County_Regional_Marketing_Guide_Netlify_Deep.zip`

Run:

```powershell
python tools/build_netlify_deep_guide.py
python tools/apply_directory_exclusions.py --check
python scripts/build_update_source_registry.py
python scripts/audit_update_sources.py --limit 120
python scripts/sweep_listing_keywords.py --no-network
```

## Publication Rules

- Treat directory rows as leads unless a current public source verifies them.
- Do not infer ad availability, free placement, grant eligibility, event acceptance, submission deadlines, audience size, endorsement, or listing approval.
- AI may propose changes, write review reports, update source metadata, and draft pull requests.
- A human reviewer must approve changes to public claims, eligibility language, directory inclusion/removal, contact details, rates, deadlines, or civic/legal guidance.
- Keep public copy practical and direct. Avoid internal audit language on public pages unless it appears in the About or creation-process section.
- Never publish, suggest, import, or regenerate an entity blocked by `tools/directory_exclusions.py`. Run the exclusion check after every build and before every deploy.

## Review Labels

Use these verification labels in new data:

- Official source checked
- Source-linked lead
- User submitted, pending review
- Needs manual verification
- Older source, use carefully

## Safe Automation Boundary

Automations should default to:

1. Watch source pages.
2. Compare against the current registry.
3. Write a report.
4. Open or draft a reviewable change.
5. Wait for human approval before production publication.

Listing keyword automation may update the review index from controlled public-page signals, but it must preserve previous source keywords on fetch failure and use a review pull request before changing production search behavior.

## Ponytail Review Rule

The uploaded Ponytail materials are incorporated as a repo working rule, not as a site dependency.

- Prefer deletion, reuse, standard-library code, and native platform features before adding new abstractions.
- Do not add dependencies or scaffolding for future possibilities.
- Fix shared root causes instead of patching one visible symptom.
- Keep accessibility, security, input validation, and human-approval boundaries intact.
- Leave one small runnable check for non-trivial script logic.
