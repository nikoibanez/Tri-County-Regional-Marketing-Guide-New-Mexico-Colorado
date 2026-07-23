# Usefulness Reassessment

Date: 2026-07-07
Target reviewed: `dist/tri-county-netlify-guide-deep`
Preview URL used: `http://127.0.0.1:8792/index.html`
Deploy zip reviewed: `dist/Tri_County_Regional_Marketing_Guide_Netlify_Deep.zip`

## Evidence Used

- Current generated data: `dist/tri-county-netlify-guide-deep/data/guide-data.json`
- Current generated pages: 25 HTML files in `dist/tri-county-netlify-guide-deep`
- Rendered QA: Playwright with installed Chrome, desktop `1440x1000`, desktop `1280x900`, mobile `390x900`
- Local configuration: `netlify.toml`, `.github/workflows/*`, `git status`
- Data-quality checks: completeness, duplicate public names by town/county, generalized concept rows, entity/audience tagging consistency, contactability by category

Browser plugin note: the in-app Browser inspection tool was not directly callable in this session, so rendered checks used Playwright/Chrome fallback.

## Executive Read

The current site is substantially more useful than the earlier one-page/report-like drafts. The homepage explains the purpose clearly, major pages are split by user need, directory cards are searchable and practical, music is opt-in, and public verification/dev language is mostly out of sight.

The next improvement should not be more visual polish first. It should be directory trust and deployment reliability:

1. Remove or reclassify the remaining generalized concept rows that appear as listings.
2. Fix the organization/audience labeling so listings are not broadly marked as both for-profit and nonprofit.
3. Adjust mobile fixed controls so they do not cover secondary-page content.
4. Align Netlify/GitHub publishing with the current canonical build output.

## Rubric Scores

| Rubric | Score | Current Evidence | Best Next Fix |
| --- | ---: | --- | --- |
| Purpose clarity | 8/10 | Homepage leads with role, region, and route-based use. It states the guide helps users choose existing channels in the right order. | Shorten the “does not replace...” paragraph one more notch on mobile. |
| Directory usefulness | 7/10 | 1,466 rows, 101 shortcut sources, 18 amplifier channels. All rows have `public_description`, `public_best_for`, keywords, and no exact duplicate public names by town/county. | Remove six generic concept rows from public listing results or move them to strategy/templates. |
| Directory contactability | 6/10 | 88.9% have a link or source URL, but only 12.9% have phone, 1.8% email, and 31.4% physical address. | Add a visible “Contact info available” filter and prioritize enriching high-value rows. |
| Entity/audience labeling | 5/10 | 645 rows are tagged as both for-profit and nonprofit via broad audience fields. This weakens the “relationship to for/nonprofit” promise. | Split `audience_served` from `entity_type`; show entity type only when specific. |
| Navigation architecture | 7/10 | Top nav is clean: Home, Start, Find, Counties, Tasks, Tools. Resources are mostly under Find. | Rename “Find” submenu item `Network` to `Directory` or `All Directory` for first-time clarity. |
| Mobile concision | 6/10 | Home CTAs no longer collide; pages load at 390px without horizontal overflow. Secondary pages are still long, and fixed controls cover early body copy on Arts/Funding. | Hide/collapse fixed controls until scroll or make them one combined mobile tray. |
| Arts & Culture usefulness | 7/10 | Arts page has fast entries, creative pages, and searchable arts rows. It is much better than empty padding drafts. | Add top filters for artist, gallery, venue, maker, music, public art, and vendor routes. |
| Funding usefulness | 7/10 | Funding page is clear and legally cautious; 44 funding/support entries exist. | Add “grant/stipend/scholarship/loan/technical help” chips and reduce “latest review” phrasing. |
| Marketing instructions separation | 8/10 | Strategy lives mostly in Amplifiers, Posting, Templates, and task pages rather than polluting directory cards. | Keep trimming any page that reads like a methodology note instead of a next action. |
| Tone and public language | 7/10 | No public “Source 1,” verification status, Super Eukarya, or obvious developer-note language found in scans. | Replace phrases like “latest review,” “working list to confirm,” and “starting points” where they feel report-like. |
| Accessibility basics | 7/10 | Skip links exist, no duplicate IDs found, no unlabeled inputs found, no missing image alt found, no console errors. | Test with axe/NVDA later; fix mobile fixed-control overlap first. |
| SEO and metadata | 8/10 | Sitemap and robots exist; 25 pages have page-specific titles; directory metadata JSON exists. | Confirm canonical production domain before launch and ensure Netlify deploy uses the same build. |
| Visual/music taste | 8/10 | Hero animation is gentle; audio is opt-in, collapsed, and does not autoplay. | Keep music collapsed on mobile and reduce its footprint further on interior pages. |
| Automation/deployment readiness | 5/10 | Source-audit workflow and Codex proposal workflow exist. Grants audit exists. | `netlify.toml` and GitHub Pages publish `dist/site`, while canonical output is `dist/tri-county-netlify-guide-deep`. Fix before relying on GitHub-to-Netlify. |

## Data-Quality Findings

### Finding 1: Six Generic Concept Rows Still Appear As Listings

Severity: High
Confidence: High

These rows are not actual organizations, programs, businesses, or directories and should not appear as normal directory results:

- Community groups and digital bulletin boards
- Main Street/chamber pages
- Official city/county pages
- Tourism offices and visitor-facing pages
- Tourism pages
- Tourism websites, Google Business Profiles, social pages, and email newsletters

Impact: These cards recreate the “AI generated structure” feeling because they describe a category of channel as if it were a listing. They should become guidance rows on Amplifiers/Templates/About, or be hidden from the public inventory.

### Finding 2: For-Profit / Nonprofit Labeling Is Too Broad

Severity: High
Confidence: High

645 rows carry both for-profit and nonprofit audience signals. This does not necessarily mean the listing itself is both. It likely means the listing may be useful to both audiences.

Impact: The card tags can mislead users who need to know whether an entry is a business, nonprofit, public agency, artist, venue, program, or funding source.

Recommended data model:

- `entity_type`: business, nonprofit, public agency, artist, venue, media, funding program, directory, event channel, service provider, unknown
- `useful_for`: business, nonprofit, artist, visitor, resident, event organizer, startup, funder, tourism

### Finding 3: Contact Data Is Link-Heavy, Not Contact-Complete

Severity: Medium
Confidence: High

Current completeness:

- Website/source URL present: 1,303 of 1,466 rows
- Phone present: 189 rows
- Email present: 27 rows
- Physical address present: 461 rows

Impact: The directory is good for discovery and routing, but not yet a full contact directory. The interface should make that explicit through filters like “has website,” “has phone,” “has address,” and “has email.”

### Finding 4: Mobile Fixed Controls Cover Interior Page Content

Severity: Medium
Confidence: High

Rendered evidence at `390x900` showed no horizontal overflow and no home CTA overlap, but the fixed “Ask directory” and “Regional sound” controls cover early copy on Arts and Funding pages.

Impact: This is mildly hostile on mobile because a first-time visitor has to read around controls before they have used them.

Best fix: make mobile fixed controls a single compact tray, or hide “Regional sound” until the user opens a small accessibility/media menu.

### Finding 5: Deploy Automation Points At An Older Output Folder

Severity: High
Confidence: High

`netlify.toml` publishes `dist/site`. GitHub Pages workflow also uploads `./dist/site`. The canonical generator currently outputs `dist/tri-county-netlify-guide-deep`, and the current zip is built from that folder.

Impact: Manual zip deploy can be current while GitHub/Netlify deploys an older site. This is the biggest obstacle to agentic updates.

Best fix: either change Netlify/GitHub publish path to `dist/tri-county-netlify-guide-deep`, or make the canonical build copy the final site into `dist/site` as the single publish folder.

## What Is Working Well

- The site now has a real multi-page structure instead of a single long HTML document.
- The homepage mission is understandable for businesses, artists, nonprofits, galleries, programs, services, and mentorships.
- Directory cards are much more useful: natural descriptions, best-fit use cases, searchable keywords, and action links.
- LocalStash / Weekender is present in the shortcut and amplifier layers.
- Music is no longer forced on users.
- The public-facing scan found no stale `Source 1`, verification-status, Super Eukarya, or developer-note phrasing in the generated pages/data.
- Accessibility basics are much improved: skip link, labeled inputs, no duplicate IDs, no missing image alt in inspected pages, and no console errors.

## Recommended Next Implementation Order

1. Remove/reclassify the six generic concept rows from public inventory cards.
2. Split `entity_type` from `useful_for` and stop showing both for-profit and nonprofit unless the entity itself is actually both.
3. Fix mobile fixed controls on interior pages.
4. Align `netlify.toml`, GitHub Pages workflow, and canonical generator output.
5. Add directory filters for contact completeness: has link, has phone, has email, has address.
6. Rename `Network` to clearer public language: `Directory`, `All Directory`, or `Find Listings`.
7. Add arts filters: artists, galleries, venues, makers, music, creative districts, vendor opportunities.
8. Add funding filters: grants, stipends, scholarships, loans, incentives, technical assistance, workforce.
9. Replace remaining report-ish phrases with user action phrases.
10. Run an accessibility tool pass with axe and a keyboard-only walkthrough.

## Tooling Notes

- Data Analytics lens was used as a local data-quality profile because the task was about usefulness, trust, duplicates, missing fields, and public data shape.
- Figma was not used because there is no specific Figma file/node to update; the more useful design evidence came from rendered screenshots.
- GitHub was inspected locally through remote/workflow/config state; no commit, push, or PR was made.
- OpenAI developer automation is scaffolded conceptually through workflows, but the deploy-path mismatch should be fixed before leaning on API/Codex automation.

## Objective Coverage Matrix

This section maps the requested reassessment scope to current evidence.

| Requested lens | Evidence inspected | Coverage result | Remaining action |
| --- | --- | --- | --- |
| Usefulness rubrics from recent guide work | Current rendered pages, current generated data, homepage, Network, Funding, Arts & Culture, Amplifiers, Posting, Templates, Submit, About | Covered. The report scores purpose clarity, directory usefulness, contactability, navigation, mobile concision, arts/funding usefulness, tone, accessibility basics, SEO, music, and automation readiness. | Use the recommended next implementation order as the next work queue. |
| Data Analytics / data quality | `guide-data.json`, row completeness, duplicate-name checks, category distribution, contactability by type, generalized-row scan, audience/entity consistency | Covered. The strongest findings are six generic concept rows, broad for-profit/nonprofit tagging, sparse phone/email/address, and contactability filter needs. | Implement entity-type split and remove/reclassify generic concept rows. |
| Figma / UI design | Rendered screenshots at desktop and mobile widths; layout, overlap, readable headings, fixed controls, nav shape, visual restraint | Covered by rendered evidence rather than a Figma-file update. No Figma file or node was provided to modify. | If a Figma design system is desired, create or provide a target Figma file, then import the current page states as design references. |
| GitHub / repository readiness | `git remote -v`, current branch, `.github/workflows/codex-update-proposal.yml`, `.github/workflows/source-audit.yml`, `netlify.toml`, current worktree status | Covered. Repo origin exists and automation scaffolds exist, but deployment config points to `dist/site` while canonical output is `dist/tri-county-netlify-guide-deep`. | Align `netlify.toml`, GitHub Pages workflow, and generator output before relying on automated deploys. |
| OpenAI Developers / agentic update readiness | Codex update proposal workflow, grants source-audit workflow, source registry/audit scripts, OpenAI key workflow requirement implied by `OPENAI_API_KEY` secret | Covered at architecture level. The site has a plausible human-reviewed automation boundary, but deploy-path mismatch and secret/config setup remain prerequisites. | Fix deploy path, confirm repo secrets/vars, then test a non-production source-audit proposal. |
| Public language and anti-AI-tell concern | Text scans for stale `Source 1`, verification labels, Super Eukarya, generic notes, and rendered page copy samples | Covered. Most obvious dev/report language is removed, but phrases like “latest review,” “working list,” and the remaining generic concept rows still weaken polish. | Rewrite those phrases and move concept rows into strategy pages. |
| Accessibility / WCAG basics | Rendered DOM checks for skip link, duplicate IDs, unlabeled inputs, missing image alt, console errors, and mobile horizontal overflow | Covered at smoke-test level. No axe or screen-reader pass was run. | Run axe and keyboard-only tests after mobile fixed-control cleanup. |
| SEO / Netlify publication | Sitemap, robots, page titles, directory metadata JSON, deploy zip, Netlify config | Covered. Metadata exists, but production publication path must be reconciled before judging live SEO. | Confirm production domain and publish path, then run live crawl after deploy. |

## Completion Judgment

The reassessment objective is complete as an audit deliverable: the current site was inspected through the requested usefulness lenses, the evidence is recorded, and the next implementation queue is explicit. The report does not claim the site itself is finished; it identifies what remains to improve.
