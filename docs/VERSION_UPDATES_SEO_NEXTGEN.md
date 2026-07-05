# Version Updates: Next-Gen SEO Redeploy

**Project:** Tri-County Regional Marketing Guide / Stateline Guide  
**Target deploy reviewed:** `https://wonderful-kashata-6ed008.netlify.app/`  
**Version label:** `v0.4.0-seo-nextgen`  
**Prepared:** 2026-06-26  
**Purpose:** GitHub-ready version note for SEO architecture, crawlability, metadata, structured data, and task-page expansion.

---

## Summary

This version adds a next-generation SEO layer to the Tri-County Regional Marketing Guide.

The update keeps the site positioned as a regional visibility routing guide, not a generic directory or marketing blog. It improves how search engines and local users can understand the site by town, county, task, and channel type.

Core search-intent shift:

> Help users find where to post, where to advertise, where to list, where to submit events, where to correct listings, and where to route public visibility across Colfax County, Las Animas County, and Huerfano County.

---

## Added

### SEO infrastructure

- Added route-level SEO metadata model.
- Added unique page titles.
- Added unique page descriptions.
- Added canonical URL support.
- Added Open Graph metadata.
- Added Twitter card metadata.
- Added default social sharing image path.
- Added generated or static `sitemap.xml`.
- Added `robots.txt` with sitemap declaration.
- Added canonical-origin support through `PUBLIC_SITE_ORIGIN`.

### Structured data

- Added `WebSite` JSON-LD.
- Added `Organization` JSON-LD.
- Added `BreadcrumbList` JSON-LD.
- Added `CollectionPage` JSON-LD for resource and county pages.
- Added optional `ItemList` JSON-LD for visible lists only.
- Added optional `Dataset` JSON-LD for public inventory downloads only.

### Content architecture

Added task-based landing page plan for:

- Where to post events in Raton, NM.
- Where to post events in Trinidad, CO.
- Where to post events in Walsenburg and La Veta, CO.
- Where to advertise in Trinidad, CO.
- Colfax County business resources.
- Las Animas County nonprofit resources.
- Huerfano County event calendars.
- Artist and gallery promotion across Raton, Trinidad, and Walsenburg.
- Regional newsletters, event calendars, and visitor guides.

### County-page SEO sections

- Added “What this county page helps with.”
- Added “Common searches this page answers.”
- Added county-specific search-intent language for:
  - Colfax / Raton.
  - Las Animas / Trinidad.
  - Huerfano / Walsenburg / La Veta / Spanish Peaks Country.

### Internal linking

- Added descriptive “Next action” link blocks.
- Replaced vague destination language with task-specific anchor text.
- Improved pathing between:
  - Plan.
  - Network.
  - Amplifiers.
  - Posting.
  - Region.
  - County pages.
  - Templates.
  - Submit.
  - Appendix.

### Human-facing help content

- Added FAQ/help section guidance for:
  - Amplifier channels.
  - Network inventory.
  - Submit/correction flow.

Important note:

- FAQ content is for user clarity and long-tail context.
- Do not add `FAQPage` structured data because Google no longer shows FAQ rich results in Search as of May 7, 2026.

---

## Changed

### Positioning

Clarified the site as:

> A regional visibility routing guide for businesses, artists, nonprofits, event organizers, service providers, and community programs across Colfax, Las Animas, and Huerfano counties.

### Metadata pattern

Updated page titles and descriptions to use:

```txt
Task or place + regional context | Stateline Guide
```

Examples:

```txt
Tri-County Regional Marketing Guide | Stateline Guide
Where to Post Events in Raton NM | Stateline Guide
Colfax County Business, Event & Promotion Resources | Stateline Guide
Regional Newsletters, Calendars, Directories & Visitor Guides | Stateline Guide
```

### Crawl model

Preserved the no-JavaScript baseline:

- Pages remain readable without JavaScript.
- Tables, links, downloads, and appendix content remain accessible.
- Search and filters remain progressive enhancement.

### Verification language

Reinforced warnings that users must verify current rules before:

- Spending money.
- Printing materials.
- Promising placement.
- Assuming free publication.
- Assuming ad availability.
- Assuming newsletter acceptance.
- Assuming eligibility.

---

## Removed or avoided

### Avoided `FAQPage` structured data

Reason:

- Google removed FAQ rich-result documentation in June 2026.
- FAQ rich results stopped appearing in Google Search as of May 7, 2026.

### Avoided unsupported claims

The update must not claim:

- Guaranteed ranking.
- Guaranteed indexing.
- Guaranteed placement in local channels.
- Confirmed advertising availability without a source.
- Confirmed audience size without a source.
- Confirmed editorial coverage without a source.

### Avoided thin doorway pages

Task pages must include useful local guidance, internal routing, verification steps, and page-specific content. They should not exist only to repeat keywords.

---

## Expected files to change

Exact paths may vary by stack.

```txt
public/robots.txt
public/sitemap.xml
public/_redirects
public/_headers
public/assets/social/stateline-guide-og.png

src/lib/seo/site.ts
src/components/SeoHead.tsx
src/components/JsonLd.tsx
src/components/Breadcrumbs.tsx
src/components/CountySearchIntentBlock.tsx
src/components/NextActionLinks.tsx

src/pages/index.*
src/pages/plan.*
src/pages/network.*
src/pages/amplifiers.*
src/pages/posting.*
src/pages/region.*
src/pages/counties/colfax.*
src/pages/counties/las-animas.*
src/pages/counties/huerfano.*
src/pages/templates.*
src/pages/submit.*
src/pages/appendix.*

src/pages/where-to-post-events-raton-nm.*
src/pages/where-to-post-events-trinidad-co.*
src/pages/where-to-post-events-walsenburg-la-veta-co.*
src/pages/where-to-advertise-trinidad-co.*
src/pages/colfax-county-business-resources.*
src/pages/las-animas-county-nonprofit-resources.*
src/pages/huerfano-county-event-calendars.*
src/pages/artist-gallery-promotion-raton-trinidad-walsenburg.*
src/pages/regional-newsletters-event-calendars-visitor-guides.*

scripts/generate-sitemap.mjs
```

---

## Suggested commit messages

```txt
feat(seo): add route metadata and canonical URLs
feat(seo): add sitemap robots and structured data
feat(content): add local task landing pages for tri-county search intent
feat(content): add county search-intent blocks and next-action links
docs(seo): add next-gen SEO implementation brief
```

Single combined commit:

```txt
feat(seo): implement next-gen tri-county SEO architecture
```

---

## Suggested pull request title

```txt
Implement next-gen SEO architecture for Stateline Guide
```

---

## Suggested pull request body

```md
## Summary

Adds next-generation SEO architecture for the Tri-County Regional Marketing Guide / Stateline Guide.

This keeps the site positioned as a regional visibility routing guide, not a generic directory. The update improves crawlability, local search intent coverage, metadata, structured data, canonical URLs, sitemap generation, county search-intent content, and internal routing.

## Major changes

- Added per-route title and meta description model.
- Added canonical URL handling.
- Added Open Graph and Twitter card metadata.
- Added `robots.txt`.
- Added `sitemap.xml`.
- Added JSON-LD helpers for WebSite, Organization, BreadcrumbList, CollectionPage, and optional ItemList/Dataset.
- Added task-page route plan for Raton, Trinidad, Walsenburg/La Veta, county resources, artist/gallery promotion, and regional amplifier channels.
- Added county search-intent blocks.
- Added descriptive next-action internal links.
- Preserved crawlable no-JavaScript content.
- Avoided FAQPage structured data because FAQ rich results are no longer shown in Google Search.

## Validation checklist

- [ ] Every indexable route has a unique title.
- [ ] Every indexable route has a unique meta description.
- [ ] Every indexable route has one visible H1.
- [ ] Every indexable route has an absolute canonical URL.
- [ ] `/robots.txt` is available.
- [ ] `/sitemap.xml` is available.
- [ ] Sitemap URLs use the final canonical domain.
- [ ] Netlify preview redirects are active only after final domain is live.
- [ ] No production route is accidentally `noindex`.
- [ ] Structured data describes visible page content only.
- [ ] FAQPage schema is not present.
- [ ] County pages include search-intent blocks.
- [ ] Task pages are substantive and not thin doorway pages.
- [ ] All important content remains crawlable without JavaScript.
- [ ] Descriptive internal links are used instead of “click here” or “learn more.”
```

---

## Manual deployment notes

Before deployment:

- Confirm the final canonical domain.
- Replace placeholder origin:

```txt
https://statelineguide.org
```

with the approved final domain.

- Confirm whether the Netlify preview domain should redirect to the canonical domain.
- Confirm no production route uses `noindex`.

After deployment, open:

```txt
/
/robots.txt
/sitemap.xml
/counties/colfax/
/counties/las-animas/
/counties/huerfano/
/amplifiers/
/network/
```

Verify page source contains:

- `<title>`.
- `meta name="description"`.
- `link rel="canonical"`.
- Open Graph tags.
- JSON-LD script.
- Visible H1.

Then submit the sitemap in Google Search Console.

---

## Version QA checklist

```txt
[ ] Homepage title is not generic.
[ ] Homepage meta description mentions counties and use case.
[ ] Network page references the inventory and verification workflow.
[ ] Amplifiers page references calendars, newsletters, directories, visitor guides, and venue lineups.
[ ] Posting page separates official notices from community visibility.
[ ] Region page names the tri-county relationship.
[ ] Colfax page names Raton and relevant first hubs.
[ ] Las Animas page names Trinidad and relevant first hubs.
[ ] Huerfano page names Walsenburg, La Veta, Spanish Peaks Country, and relevant first hubs.
[ ] Submit page explains corrections are reviewed, not automatically published.
[ ] Appendix page remains crawlable.
[ ] New task pages link back to county, templates, submit, posting, and amplifier pages.
[ ] No task page makes unverifiable claims.
[ ] No FAQPage JSON-LD exists.
[ ] Sitemap includes all new task routes.
[ ] Canonical URLs use final domain.
[ ] Redirects are not activated until final domain is live.
```

---

## Known GitHub limitation during preparation

The GitHub connector returned zero accessible repositories. This file is prepared for manual placement into the repository, such as:

```txt
docs/VERSION_UPDATES_SEO_NEXTGEN.md
```

or:

```txt
CHANGELOG_SEO_NEXTGEN.md
```
