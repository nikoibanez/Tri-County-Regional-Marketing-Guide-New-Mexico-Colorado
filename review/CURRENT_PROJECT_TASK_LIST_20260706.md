# Current Project Task List

Date: 2026-07-06

## Current Baseline

The desktop repo and GitHub `master` are synced at:

`bd20676 Add all-county event posting hub`

The current shared baseline includes:

- GitHub repo connection.
- GitHub Pages deployment workflow commit.
- All-county event-posting hub.
- Event-posting CSV with 80 channels and no duplicate channel names.
- Event-posting page linked across the generated site.
- Laptop/desktop merge handoff note.

## Primary Project Scope

Build and maintain the Stateline Guide / Tri-County Regional Marketing Guide as a practical routing layer for businesses, nonprofits, artists, venues, programs, services, and event organizers across Colfax County, Las Animas County, and Huerfano County.

The guide should help users answer:

- Where should I list my business, event, service, program, nonprofit, class, gallery, or creative work?
- Which county, chamber, visitor route, arts route, public office, media outlet, or directory should I try first?
- What contact path should I use?
- What should I verify before spending money, printing materials, promising placement, or assuming eligibility?

## Still On The Task List

### 1. Netlify Deployment From GitHub

Status: Pending.

Why it matters: Netlify should build/deploy from the repo instead of relying on manual zip uploads.

Next action:

- Connect Netlify to `nikoibanez/Tri-County-Regional-Marketing-Guide-New-Mexico-Colorado`.
- Confirm the publish directory. Current deployable static site appears to be `dist/site`.
- Decide whether Netlify or GitHub Pages is the public production target.

### 2. Laptop/Desktop Codex Reconciliation

Status: Partially handled.

Why it matters: The repo is synced, but the laptop Codex conversation may still contain analysis, decisions, or files that are not in this desktop thread.

Next action:

- On laptop Codex, generate a summary of its thread.
- Paste that summary into `review/CODEX_THREAD_MERGE_AND_AUTOMATION_HANDOFF_20260705.md`.
- Reconcile through git diff, not memory.

### 3. Source-Audit Automation

Status: Designed, not fully activated.

Why it matters: Grants, calendars, directories, event routes, and contact details change. The site needs a repeatable way to detect likely changes without silently publishing them.

Next action:

Run locally in report-only mode:

```powershell
python tools/build_netlify_deep_guide.py
python scripts/build_update_source_registry.py
python scripts/audit_update_sources.py --limit 120
```

Then review the output before any public content changes.

### 4. OpenAI Summarization For Audits

Status: Pending.

Why it matters: OpenAI can summarize source-audit changes, flag conflicts, and draft review notes, but should not directly publish new civic, grant, rate, deadline, or directory claims.

Next action:

- Decide where the local `.env` file should live.
- Use existing key only through a secure local environment path.
- Add summarization after source-audit reports are already working.

### 5. Directory Quality Pass

Status: Ongoing.

Why it matters: The directory is the heart of the guide. Some cards still risk sounding generic, source-like, or overly cautious instead of being practical for users.

Next actions:

- Continue replacing generic descriptions with specific business/resource descriptions.
- Keep public cards focused on contact paths, useful-for tags, location, description, and correction links.
- Preserve verification/source metadata in CSV/JSON/internal notes instead of cluttering public cards.
- Continue duplicate-name review across directory data, especially arts, lodging, visitor, and scraped business listings.

### 6. Funding And Grants Expansion

Status: Needs recurring updates.

Why it matters: Funding programs, stipends, scholarships, grant windows, and eligibility are highly time-sensitive.

Next actions:

- Monitor regional, Colorado, New Mexico, arts, nonprofit, rural development, tourism, and small-business grant sources.
- Mark items as current only after source check.
- Keep the funding page separate and practical.

### 7. Arts & Culture Page Improvement

Status: Partially consolidated, still needs polish.

Why it matters: The arts pages should be useful to artists, galleries, makers, musicians, venues, and cultural organizers without feeling padded or report-like.

Next actions:

- Keep arts subpages consolidated under `Arts & Culture` where practical.
- Remove generic “public travel listing” style language where better descriptions can be generated.
- Make event, venue, gallery, artist, maker, and music routes easier to filter.
- Keep links to tools/services/programs that are useful but not otherwise directory entries.

### 8. Event-Posting Hub Follow-Up

Status: Implemented, needs future validation.

Why it matters: The new all-county event-posting hub is useful, but event routes are unstable.

Next actions:

- Manually verify social pages/groups and contact-only routes.
- Add missing municipal/library/school/community routes when found.
- Keep language careful: submit, ask, contact, verify fit.
- Do not imply guaranteed placement or free advertising.

### 9. Navigation And Mobile Simplification

Status: Improved, still worth reviewing after content growth.

Why it matters: Mobile users should reach directories, event routes, funding, submit update, and county pages without reading long marketing instruction text.

Next actions:

- Keep mobile pages short and route-first.
- Avoid duplicated nav concepts such as “All Resources” vs “Absolutely Everything” unless the distinction is obvious.
- Check the top nav and footer after each new page is added.

### 10. Visual And Animation QA

Status: Implemented in pieces, still needs visual review.

Why it matters: The animated hero/banner system is part of the site identity, but motion, opacity, contrast, and mobile performance need review.

Next actions:

- Confirm hero animation appears on relevant pages.
- Check reduced-motion behavior.
- Confirm no decorative animation hides text or creates eye strain.
- Continue using gentle colors, softer opacity, and readable contrast.

### 11. Accessibility QA

Status: Ongoing.

Why it matters: The guide is for broad public use, including people using mobile, keyboard navigation, assistive tech, and low-bandwidth contexts.

Next actions:

- Recheck skip links, headings, focus states, contrast, touch targets, form labels, and meaningful link text.
- Recheck chatbot/directory assistant accessibility before treating it as finished.
- Verify reduced-motion support.

### 12. SEO And Metadata

Status: Partially implemented.

Why it matters: Search should find specific regional pages such as Raton event posting, Trinidad advertising, Huerfano funding, arts routes, and county directories.

Next actions:

- Keep page-specific titles, descriptions, canonical URLs, and structured data current.
- Confirm sitemap includes new pages.
- Avoid stuffing metadata with every listing if it creates bloated or low-quality pages.

### 13. Deployment Package Discipline

Status: Needs standardization.

Why it matters: There are now multiple deploy zips and generated folders. The repo needs a clear canonical deployment path.

Next actions:

- Decide whether `dist/site` is the canonical public build.
- Keep deploy zips as release artifacts, not the primary source of truth.
- Document exactly what Netlify should deploy.

### 14. Human Review Boundary

Status: Established, must be preserved.

Why it matters: This project touches public/civic/resource guidance. Automation should support review, not replace judgment.

Always require human approval before publishing changes to:

- Grant eligibility.
- Rates.
- Deadlines.
- Official contact details.
- Civic/legal guidance.
- Event acceptance.
- Advertising availability.
- Directory inclusion or removal.

## Recommended Next Three Moves

1. Connect Netlify to GitHub and confirm `dist/site` deploys correctly.
2. Run source-audit scripts in report-only mode and review the output.
3. Ask laptop Codex for its thread summary and paste it into the merge handoff file.
