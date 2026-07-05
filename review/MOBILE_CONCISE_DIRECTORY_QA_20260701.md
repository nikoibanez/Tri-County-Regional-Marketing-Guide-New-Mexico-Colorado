# Mobile Concise Directory QA - 2026-07-01

## Implemented

- Added a mobile-only concise layer for non-directory guide pages.
- On mobile, non-directory pages now show a short quick-route panel with 2-4 action links, while longer explanatory guide sections are hidden.
- Preserved directory, funding, arts/culture, appendix, submit, network, and amplifier/search pages as functional resource pages.
- Kept `Funding` as its own page.
- Combined the former music/venue and artist/gallery subpage functions into the main `Arts & Culture` page.
- Removed separate `Music + venues` and `Artists + galleries` links from the primary Directory nav.
- Tightened the `Marketing Playbook` into a short regional growth loop: list, post, partner, follow up.
- Hid generated page-hero explanatory paragraphs on mobile while keeping titles and action buttons.
- Kept home yucca hero before the mobile quick panel.

## Mobile Routing

- `resources/funding/index.html` remains its own funding page.
- `resources/arts-culture/index.html` now includes:
  - creative directory
  - music + venue entries
  - artist + gallery entries
- `local-music-arts/index.html` and `artist-gallery-promotion/index.html` remain available for compatibility, but mobile users are routed back to `Arts & Culture`.

## Audit Results

- Mobile concise pages: 32.
- Mobile quick panels: 32.
- Home hero appears before the quick panel: yes.
- Arts & Culture has `#music-directory`: yes.
- Arts & Culture has `#artist-directory`: yes.
- Header no longer exposes old music/gallery subpage links: yes.
- Public content pages missing title/meta/skip-link/JSON-LD: 0.
- Old public import phrases found in public HTML/JS/JSON/CSV exports: 0.
- Directory entries: 1,576.
- Exact duplicate name/county/town groups: 0.
- Local HTTP checks returned 200 for:
  - `/index.html`
  - `/resources/arts-culture/index.html`
  - `/promote/index.html`

## Note

Playwright is not installed in this workspace, so this pass used generator checks, static DOM/CSS audits, Node syntax validation, and local HTTP checks rather than browser screenshots.

