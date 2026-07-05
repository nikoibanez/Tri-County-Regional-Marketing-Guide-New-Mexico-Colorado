# Arts + Music Routing Update — Implementation Notes

Date: 2026-06-28  
Target deploy: `NETLIFY_DEPLOY_Tri_County_Regional_Marketing_Guide_2026-06-27_Incorporated.zip`  
Updated pages:

- `/local-music-arts/`
- `/artist-gallery-promotion/`

## Implementation goal

The previous pages worked as contextual arts/music material, but they did not fully behave like the rest of the guide: a task-based routing system. This update makes the pages useful for artists, musicians, venues, galleries, businesses, nonprofits, schools, tourism partners, and event organizers by centering practical actions:

- Book music.
- Find a venue.
- Hire an artist.
- Promote an opening, show, workshop, market, or concert.
- Find collaborators.
- Submit or correct directory information.

## Files changed

- `local-music-arts/index.html`
- `artist-gallery-promotion/index.html`
- `assets/site-data.js`
- `data/guide-data.json`
- `data/tri_county_persona_resources.json`
- `data/tri_county_persona_resources.csv`
- `sitemap.xml`
- `docs/ARTS_MUSIC_IMPLEMENTATION_NOTES.md`
- `docs/VERSION_UPDATES_ARTS_MUSIC_2026-06-28.md`

## Page architecture changes

### `/local-music-arts/`

The page now functions as a broad creative-sector router. New sections:

1. Hero: “Local music, arts, venues, and creative collaborators.”
2. Start-with-the-job routing table.
3. Creative matchmaking matrix.
4. Opt-in archival music player retained on-page.
5. County creative route cards.
6. Music, arts, and event organizer packet checklists.
7. Example pathways.
8. Researched starting-point listings grouped by county.
9. Internal next-action links to Network, Amplifiers, Posting, Templates, Submit, and Artist + Gallery.

### `/artist-gallery-promotion/`

The page now functions as the visual arts / maker / gallery / client routing page. New sections:

1. Hero: “Artist, gallery, maker, and creative-service promotion routes.”
2. “What this page is for” user/outcome table.
3. Choose-the-arts-route matrix.
4. Before-contact cards for clients, artists, and galleries/venues.
5. Tags and contact-readiness labels.
6. Researched artist/gallery directory additions grouped by county.
7. Outreach templates.
8. Internal next-action links to related guide sections.

## Directory records added

Twenty source-backed arts/music/venue/maker route records were added to the client-side data so the assistant and directory search can surface them.

### Colfax / Raton

- Old Pass Gallery
- Raton Arts & Cultural District
- Shuler Theater
- The Raton Museum
- Santa Fe Trail School for the Performing Arts

### Las Animas / Trinidad

- Corazón Gallery / Corazón Art League
- A.R. Mitchell Museum of Western Art
- The Commons @ Space to Create
- East Street School
- 221B Gallery
- Tabula Rasa Gallery and Art Supply
- Pack Mule Mercantile

### Huerfano / La Veta / Walsenburg

- La Veta Creative District
- La Veta School of the Arts
- Museum of Friends
- SPACe Gallery / Spanish Peaks Arts Council
- Shalawalla Gallery & Batik Studio
- Artisans on Main
- La Veta Mercantile
- Walsenburg Studio

## Directory metadata pattern

Each new record includes:

- `id`
- `resource_name`
- `category`
- `town`
- `county`
- `state`
- `website`
- `contact_email`
- `contact_phone`
- `physical_address`
- `source_url`
- `source_type`
- `last_verified_date`
- `notes`
- `needs_follow_up`
- `resource_type`
- `audience_served`
- `cost_level`
- `access_mode`
- `goal_relevance`
- `has_public_source`

## Verification notes

These listings are intended as public starting points, not endorsements or guaranteed placement paths. The page copy repeatedly instructs users to confirm:

- current hours
- fees
- booking terms
- submission rules
- commission rules
- exhibition eligibility
- event-calendar lead time
- image rights
- accessibility requirements
- source/contact validity

## SEO changes

Updated page titles and meta descriptions:

- `Local Music, Arts, Venues & Creative Collaboration Routes | Stateline Guide`
- `Artist, Gallery, Maker & Creative Service Promotion Routes | Stateline Guide`

Canonical URLs were set to:

- `https://statelineguide.org/local-music-arts/`
- `https://statelineguide.org/artist-gallery-promotion/`

Added `CollectionPage` JSON-LD to both pages. FAQ schema was intentionally not added because Google no longer shows FAQ rich results in Search; visible FAQ/routing content remains useful for users and long-tail search.

## Sitemap changes

Updated `lastmod` for:

- `/local-music-arts/`
- `/artist-gallery-promotion/`

## Accessibility / UX notes

- Existing classes and layout system were reused instead of adding a new visual system.
- Tables use semantic table markup.
- Search inputs retain label text.
- Internal links use descriptive anchor text.
- The music player remains opt-in and page-specific.
- No autoplay behavior was added.

## Suggested post-deploy QA

1. Open `/local-music-arts/` and test layout at desktop, tablet, and mobile widths.
2. Open `/artist-gallery-promotion/` and test long table scrolling.
3. Search the full directory for: `Old Pass`, `221B`, `SPACe`, `Museum of Friends`, `Shuler`, `La Veta Mercantile`.
4. Confirm the music player still plays only after user interaction.
5. Confirm footer links still work.
6. Run a link check against new external URLs.
7. Submit updated sitemap in Google Search Console after the production deploy.
