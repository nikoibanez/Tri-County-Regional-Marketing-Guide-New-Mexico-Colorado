# Twenty-Site Resource Sweep

Checked: 2026-11-04. This is a review artifact, not a claim that any grant, loan, scholarship, or venue is currently available.

## Added To The Watched Registry

- Regional foundations: Southern Colorado Community Foundation, Taos Community Foundation, Boettcher Foundation, Daniels Fund, Colorado Health Foundation.
- Nonprofit discovery: Colorado Trust grantee database, Gudsy Colfax County nonprofit records.
- Scholarships: Trinidad State, New Mexico Higher Education Department, Albuquerque Community Foundation.
- Individual artist awards: Foundation for Contemporary Arts, Pollock-Krasner Foundation.
- Business loans: DreamSpring, Colorado Enterprise Fund, Accion Opportunity Fund.
- Event venues: Destination Colorado's Trinidad facility guide, Shuler Theater, Main Street LIVE, Francisco Center for the Performing Arts, Cuchara Mountain Park.

These are twenty distinct new domains in `data/resource-discovery-sources.json`. The registry audit checked all 65 configured hubs: 53 returned usable HTML, 10 were access-blocked, one timed out, and one had a TLS error. Of the twenty additions, sixteen returned usable HTML. Colorado Health Foundation, Albuquerque Community Foundation, and Gudsy returned 403 to the script; Cuchara Mountain Park returned 429. Their public pages were readable through browser research, but the scheduled script must keep them in browser-review status. It must not bypass access controls or infer that a program closed.

The full registry produced 227 candidate links after excluding historical awards, reporting pages, and closed-cycle links. That is a queue across all 65 hubs, not 227 newly approved resources. The new sources are available in the guide's Funding, Events, and About routes. No scraped link has been inserted into the public funding or organization directory without a separate eligibility and duplicate review.

## Earlier PR Queue Decisions

- PR #83's one new TechSoup accounting-services link was not added to the free-tools directory: the link alone does not establish a free or nonprofit-discounted offer.
- Changed funding pages remain claim-review items. Current deadlines, eligibility, award size, fiscal-sponsor rules, loan rates, and fees require direct source confirmation before public copy changes.
- Directory watcher URL matches now require the entity name to agree; a shared municipal directory URL no longer marks unrelated businesses as already represented.
- Seven Angel Fire tourism-page keyword inferences were blocked where nearby template content misclassified individual businesses. The keyword index remains a reviewable proposal in this PR.
- Five previously researched listing contact/link repairs and the Anschutz grant-page URL repair were retained and checked against the canonical build.
- The Angel Fire Chamber's own site now displays a dissolution notice, so its old business pages are not current listing evidence. Three weekly directory-watch groups and the public directory shortcut now point to current Visit Angel Fire pages. The keyword sweep treats the chamber notice as unavailable and retains prior source keywords for review.
- Fifty-nine canonical rows still reference the former chamber host; thirty-nine have no Visit Angel Fire or social URL fallback in their stored website/source fields. These need entity-by-entity replacement links before claiming a current direct contact route.
- Visit Angel Fire pages are current and browser-readable, but all five replacement watcher URLs returned 403 to the local script on this pass. They remain source leads for browser review, not successful automated page scrapes. The directory watcher checked 36 seed pages and found 15 priority leads; eight pages had fetch issues, including those five.

## Next Review

Start with county-serving foundation and scholarship links, then confirm any proposed directory entity on its own current page. Do not treat the existence of a foundation's grant page as a current open cycle or guaranteed eligibility.
