# Average-User Substance Upgrade Implementation Notes

Date: 2026-06-28  
Package base: `NETLIFY_DEPLOY_Tri_County_Regional_Marketing_Guide_2026-06-28_Arts_Music_Routing_Update.zip`

## Purpose

This patch adds practical substance for four average end users:

1. Artist
2. Entrepreneur
3. Events organizer
4. Nonprofit board member

The update keeps the site's routing model intact: choose the job, prepare one packet, match the channel, verify details, and save proof.

## Updated Pages

### `/index.html`

Added `#persona-paths`:

- Artist route
- Business/entrepreneur route
- Events organizer route
- Nonprofit board route

Each card now gives three practical first steps and a relevant internal link.

### `/plan/index.html`

Added `#worked-examples`:

- New storefront launch
- Existing business expanding across county lines
- Art opening or gallery reception
- Nonprofit fundraiser or public program

Added `#nonprofit-proof-loop`:

- Action
- Proof to save
- Later use

### `/network/index.html`

Added `#search-recipes`:

- Goal-based search recipes for businesses, events, funding, visitors, partners, and creative-sector contacts.

Added `#after-finding-listing`:

- Verify the source
- Match the route
- Save useful proof

### `/amplifiers/index.html`

Added:

- `#event-promotion-timeline`
- `#paid-promotion-check`
- `#event-type-routes`

These sections help users decide when to submit, when to pay, and which channels fit which event types.

### `/posting/index.html`

Added `#choose-event-route`:

- Art opening
- Live music
- Fundraiser
- Class/workshop
- Public meeting/listening session
- Business launch

### `/templates/index.html`

Added:

- `#artist-templates`
- `#event-templates`
- `#nonprofit-templates`

Includes copy-ready templates for:

- Artist commission inquiry
- Gallery submission question
- Art opening calendar submission
- Live music calendar submission
- Business launch listing
- Nonprofit program listing request
- Sponsor or partner follow-up

### `/submit/index.html`

Added `#submission-examples`:

- Add a venue
- Correct a business listing
- Add an artist or gallery route
- Add a nonprofit program
- Add a music route

### `/local-music-arts/index.html`

Added `#creative-work-loop`:

- Prepare the packet
- Choose one route
- Contact selectively
- Track response
- Reuse what worked

### `/artist-gallery-promotion/index.html`

Added `#how-this-leads-to-work`:

- For artists and makers
- For buyers and businesses
- For galleries and venues
- For nonprofits and schools

### `/assets/styles.css`

Added lightweight card/grid styles for the new persona and implementation sections:

- `.quickstart-grid`
- `.quickstart-card`
- `.card-grid`
- `.info-card`
- `.text-link`

## QA Notes

- All updated pages retain a single `</main>` closing tag.
- All new section IDs were verified in the target files.
- No new pages were added, so `sitemap.xml` did not require new URL entries.
- The package remains a static Netlify deploy with no build step required.

## Recommended next pass

1. Replace placeholder submission contact with a real inbox or form endpoint.
2. Add anchor links to the main nav or page-local table of contents if pages become long.
3. Add filters/tags in directory data for the new persona routes.
4. Add analytics events for CTA links, directory searches, CSV downloads, and Submit clicks.
