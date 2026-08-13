# Stateline Guide UX and Navigation Review

Date: 2026-08-08

## Purpose Test

The site should help a new or established business, nonprofit, artist, venue, or program move quickly from a real task to a useful local contact. Directory search is the primary product. Funding, arts and culture, promotion, county routes, templates, and the submission form should support that task without competing with it.

## Implemented Findings

### 1. Give the header one clear information hierarchy

- Desktop navigation now uses six stable choices: Directory, Funding, Arts & Culture, Promote, Counties, and More.
- Mobile navigation uses four choices: Directory, Funding, Arts & Culture, and More.
- Secondary pages live in grouped menus rather than forcing horizontal or vertical navbar scrolling.
- Footer headings use the same concepts as the header: Guide, Find resources, Promote, Counties, and Data + updates.

### 2. Reduce page length without hiding essential routes

- Internal heroes are shorter and use a smaller page-title scale than the landing page.
- Long source, funding, and local-inventory lists reveal a useful first set, followed by a clear Show more action.
- Mobile starts with four registry or shortcut cards and four local entries.
- Funding starts with six opportunities on mobile and twelve on desktop.
- Directory results start with ten listings on mobile and twenty-four on desktop.

### 3. Make the arts page task-led

- The first content block now offers four direct actions: find artists, find arts funding, promote an event, and add creative work.
- County visual routes lead directly to filtered directory searches.
- External artist registries and open-call networks are separated from local creative listings.
- The local preview uses concrete identity fields, whole-word matching, and one card per normalized entity name.

### 4. Keep funding useful for first-time applicants

- The funding finder exposes applicant, timing, cost, fiscal-sponsor, and funding-range information.
- Funding details are collapsed initially so users can compare programs before reading every condition.
- External search hubs are balanced across grants, business capital, and fiscal sponsorship.
- Local and regional routes remain available after the national funding finder.

### 5. Correct directory taxonomy at the source

- Public type inference now gives priority to a concrete category, entity name, and resource type in that order.
- Whole-word matching prevents `art` from matching `Auto Parts` or `starting`.
- Incidental audience text no longer places a cafe in the arts preview.
- Curated previews suppress repeated normalized names without changing the underlying audit record.

### 6. Make public copy sound like a guide

- Repetitive “grouped routes” and implementation-style instructions were replaced with short descriptions of what the source is useful for.
- Public cards continue to avoid promising placement, eligibility, funding, or acceptance.
- Methodology and source-watching language remains in review and documentation files rather than the main user path.

### 7. Add a maintainable discovery layer

- A controlled keyword registry covers grants, business capital, fiscal sponsors, nonprofit directories, business directories, and artist opportunities.
- Thirty-four source hubs are configured for weekly review.
- The watcher produces a private candidate queue and preserves the last successful state when a site blocks automation.
- Candidate extraction requires a resource-type phrase; generic decision words and place names only improve ranking.
- No candidate is published without human review.

## Verification

- Mobile viewport checked at 390 x 844 with no horizontal overflow.
- Desktop viewport checked at 1440 x 900 with no horizontal overflow.
- Internal link audit: no missing targets, missing anchors, or duplicate IDs after the current build.
- Unit tests cover taxonomy boundaries, category balance, candidate quality, deduplication primitives, source-state preservation, accessibility assets, and directory behavior.
- The live source check found no confirmed broken registry URL. Pages that returned 403 or certificate-chain errors remain available as manual links and are identified as automation limits in private reports.

## Remaining Human Review

- Review newly collected source candidates before adding a public opportunity or organization.
- Confirm licensing or reuse terms before importing records from member, commercial, or donation-platform directories.
- Keep deadlines, eligibility, award ranges, fiscal-sponsor rules, fees, and contact details tied to the originating page.
