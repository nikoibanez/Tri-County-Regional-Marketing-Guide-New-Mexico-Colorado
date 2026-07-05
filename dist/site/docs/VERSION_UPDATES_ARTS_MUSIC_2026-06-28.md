# Version Updates — Arts + Music Routing Pages

Date: 2026-06-28  
Release type: Static Netlify deploy update  
Scope: Creative-sector UX, SEO, and directory expansion

## Summary

This release updates the Tri-County Regional Marketing Guide’s arts and music pages so they function as integrated routing tools instead of supplemental topic pages.

## Updated pages

- `/local-music-arts/`
- `/artist-gallery-promotion/`

## Major additions

### Local Music + Arts page

- Reframed page as a creative-sector routing page for musicians, artists, venues, galleries, cafés, nonprofits, schools, businesses, tourism partners, and event organizers.
- Added a “Start with the job” routing table.
- Added a creative matchmaking matrix connecting users to practical next actions.
- Retained the opt-in archival audio player on the page.
- Added county route cards for Colfax, Las Animas, and Huerfano.
- Added packet checklists for:
  - music booking
  - arts collaboration
  - event organizers
- Added example pathways such as musician-to-venue-to-calendar and artist-to-gallery-to-tourism-channel.
- Added researched directory listings grouped by county.
- Added internal next-action links to Network, Amplifiers, Posting, Templates, Submit, and Artist + Gallery.

### Artist + Gallery Promotion page

- Reframed page as a visual arts, maker, gallery, and creative-service routing page.
- Added a user/outcome table for artists, galleries, businesses, nonprofits, schools, event organizers, and tourism/media partners.
- Added an arts route matrix for hiring, showing, selling, teaching, public programming, and event promotion.
- Added before-contact guidance for:
  - clients hiring artists
  - artists/makers contacting channels
  - galleries/venues managing submissions
- Added suggested listing tags and contact-readiness labels.
- Added researched artist/gallery listings grouped by county.
- Added practical outreach templates.
- Added internal next-action links to the broader guide system.

## Directory additions

Added 20 arts/music/venue/maker records to:

- `assets/site-data.js`
- `data/guide-data.json`
- `data/tri_county_persona_resources.json`
- `data/tri_county_persona_resources.csv`

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

## SEO updates

- Updated page titles.
- Updated meta descriptions.
- Added canonical URLs.
- Added `CollectionPage` JSON-LD.
- Updated sitemap `lastmod` values for the two target pages.

## UX principles used

- Keep the existing visual system.
- Use task-based routing before directory browsing.
- Make each page useful to both creators and clients/collaborators.
- Avoid overpromising; mark listings as starting points.
- Use packet checklists to improve first-contact quality.
- Route users back into the broader guide ecosystem.

## Follow-up recommendations

- Add a visible “Creative Routes” nav group if the next deployment cycle includes global navigation edits.
- Add a `/local-music-booking/` page only if enough verified venue, open mic, and performer records are available.
- Add a CSV export specifically for arts/music listings.
- Build a public correction form with arts/music-specific fields.
- Run external link checks quarterly.
