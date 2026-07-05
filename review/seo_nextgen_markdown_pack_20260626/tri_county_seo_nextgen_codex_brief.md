# Next-Gen SEO Implementation Brief for Codex

**Project:** Tri-County Regional Marketing Guide / Stateline Guide  
**Reviewed deploy:** `https://wonderful-kashata-6ed008.netlify.app/`  
**Prepared:** 2026-06-26  
**Primary counties:** Colfax County, NM; Las Animas County, CO; Huerfano County, CO  
**Primary hubs:** Raton, Trinidad, Walsenburg, La Veta, Cuchara, Angel Fire, Red River, Eagle Nest  
**Audience:** Codex / agentic implementation assistant

---

## 1. Implementation goal

Implement SEO as a **regional routing system**, not as generic keyword stuffing.

The site already has the right conceptual structure: it helps businesses, artists, nonprofits, galleries, programs, services, event organizers, and mentorships decide where to post, list, submit, verify, correct, and follow up across the tri-county area.

The next generation should add:

1. Stable canonical-domain configuration.
2. Unique metadata for every route.
3. A generated XML sitemap.
4. `robots.txt` with sitemap declaration.
5. Breadcrumbs and JSON-LD structured data.
6. Task-based local landing pages.
7. County-specific search-intent blocks.
8. Descriptive internal-link clusters.
9. User-facing FAQ/help sections without FAQ rich-result schema.
10. GitHub-versioned SEO notes.

---

## 2. Hard constraints

### Preserve positioning

Use this as the core positioning:

> A regional visibility routing guide for businesses, artists, nonprofits, event organizers, service providers, and community programs across Colfax, Las Animas, and Huerfano counties.

Do **not** reposition the site as a generic marketing blog, ad network, chamber replacement, or directory clone.

### Preserve verification language

Do not imply that any external channel guarantees:

- Free placement.
- Paid placement.
- Event acceptance.
- Newsletter inclusion.
- Advertising availability.
- Editorial coverage.
- Deadline stability.
- Audience size.
- Endorsement.
- Eligibility.

Use this pattern near channel tables, task pages, and submission flows:

> Open the source before spending money, printing materials, or promising placement.

### Preserve crawlability

The live site already says pages, tables, links, downloads, and appendix content work without JavaScript. Preserve that.

Required:

- One visible `<h1>` per page.
- Descriptive heading order.
- Descriptive anchor text.
- Core content visible in HTML.
- Search/filter UI as enhancement only.
- Keyboard-accessible controls.
- Reduced-motion support for decorative animation.

### Standardize naming

Use:

- **Stateline Guide** as the site/brand name.
- **Tri-County Regional Marketing Guide** as the main guide title.
- Page titles should usually end with `| Stateline Guide`.

---

## 3. Research basis

Use current Google Search guidance as implementation guardrails:

- SEO should help search engines understand content and help users decide whether to visit.  
  Source: `https://developers.google.com/search/docs/fundamentals/seo-starter-guide`

- Google recommends descriptive URLs and logical site organization.  
  Source: `https://developers.google.com/search/docs/fundamentals/seo-starter-guide`

- Every page should have a descriptive, concise, non-boilerplate `<title>`.  
  Source: `https://developers.google.com/search/docs/appearance/title-link`

- Pages should have unique meta descriptions.  
  Source: `https://developers.google.com/search/docs/appearance/snippet`

- XML sitemaps are the most versatile sitemap format; sitemap submission is a hint, not a guarantee.  
  Source: `https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap`

- `robots.txt` controls crawler access and is not a reliable way to keep pages out of Google.  
  Source: `https://developers.google.com/search/docs/crawling-indexing/robots/intro`

- Absolute canonical URLs help consolidate similar or duplicate URLs.  
  Source: `https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls`

- Structured data must describe visible page content.  
  Source: `https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data`

- Breadcrumb structured data can describe page hierarchy.  
  Source: `https://developers.google.com/search/docs/appearance/structured-data/breadcrumb`

- FAQ rich results are no longer shown in Google Search as of May 7, 2026. Do not implement `FAQPage` schema for this site.  
  Source: `https://developers.google.com/search/updates#removing-faq-rich-result`

---

## 4. Existing live-site facts to preserve

The reviewed site already includes:

- Homepage H1: `Tri-County Regional Marketing Guide`.
- Purpose: use the guide when users need “a route, not just a search result.”
- Audience: new/existing businesses, artists, nonprofits, galleries, programs, services, and mentorships.
- Inventory: 456 listings and leads.
- Inventory split:
  - 153 Colfax.
  - 122 Huerfano.
  - 96 Las Animas.
  - 85 Regional.
- Primary sections:
  - Plan.
  - Network.
  - Amplify.
  - Post.
  - Region.
  - Colfax.
  - Las Animas.
  - Huerfano.
  - Templates.
  - Submit.
  - Appendix.
- Amplifier categories:
  - Event calendars.
  - Newsletters and mailing lists.
  - Business directories.
  - Tourism/visitor guides.
  - Anchor venue lineups.
  - Advertising or placement inquiries.
- County routing:
  - Colfax: Raton, MainStreet, GrowRaton, Explore Raton, arts, media, New Mexico support.
  - Las Animas: Trinidad, chamber, tourism, media, creative district, Colexico, Colorado support.
  - Huerfano: Walsenburg, La Veta, Spanish Peaks Country, HCED, chamber, creative district, World Journal.

---

## 5. Canonical URL model

Use one canonical origin after final domain setup.

Default placeholder:

```txt
https://statelineguide.org
```

If the final domain differs, replace every instance with the approved domain.

Use an environment variable where possible:

```txt
PUBLIC_SITE_ORIGIN=https://statelineguide.org
```

Example canonical tag:

```html
<link rel="canonical" href="https://statelineguide.org/counties/colfax/">
```

Do not redirect the Netlify preview domain until the final domain is live and verified.

---

## 6. Route architecture

### Existing routes

```txt
/
/plan/
/network/
/amplifiers/
/posting/
/region/
/counties/colfax/
/counties/las-animas/
/counties/huerfano/
/templates/
/submit/
/appendix/
```

### New task-based routes

```txt
/where-to-post-events-raton-nm/
/where-to-post-events-trinidad-co/
/where-to-post-events-walsenburg-la-veta-co/
/where-to-advertise-trinidad-co/
/colfax-county-business-resources/
/las-animas-county-nonprofit-resources/
/huerfano-county-event-calendars/
/artist-gallery-promotion-raton-trinidad-walsenburg/
/regional-newsletters-event-calendars-visitor-guides/
```

These pages must not be thin doorway pages. Each page needs useful local guidance, an action table, verification warnings, and links back into the guide.

---

## 7. SEO metadata matrix

Create a route metadata file such as:

```txt
src/lib/seo/site.ts
```

Use this data model or adapt to the stack:

```ts
export const SITE = {
  name: "Stateline Guide",
  guideTitle: "Tri-County Regional Marketing Guide",
  origin: process.env.PUBLIC_SITE_ORIGIN || "https://statelineguide.org",
  defaultDescription:
    "A regional visibility routing guide for businesses, artists, nonprofits, event organizers, services, and community programs across Colfax, Las Animas, and Huerfano counties."
};

export type SeoRoute = {
  path: string;
  title: string;
  description: string;
  h1?: string;
  schemaType?: "WebPage" | "CollectionPage" | "AboutPage";
  noindex?: boolean;
};
```

### Core route metadata

```ts
export const seoRoutes: SeoRoute[] = [
  {
    path: "/",
    title: "Tri-County Regional Marketing Guide | Stateline Guide",
    description: "Find directories, calendars, media channels, tourism pages, public offices, and outreach routes for Colfax, Las Animas, and Huerfano counties.",
    h1: "Tri-County Regional Marketing Guide",
    schemaType: "WebPage"
  },
  {
    path: "/plan/",
    title: "Plan Local Growth Across Colfax, Las Animas & Huerfano | Stateline Guide",
    description: "Choose a goal, audience, outreach packet, channel set, and tracking loop before promoting a business, event, nonprofit, service, or program.",
    h1: "Choose the cycle before collecting links.",
    schemaType: "WebPage"
  },
  {
    path: "/network/",
    title: "Find Local Directories, Media, Funding & Support Leads | Stateline Guide",
    description: "Search public shortcuts and a 456-entry regional inventory of directories, media, funding, business, nonprofit, arts, and support leads.",
    h1: "Use the directories that already save time.",
    schemaType: "CollectionPage"
  },
  {
    path: "/amplifiers/",
    title: "Regional Newsletters, Calendars, Directories & Visitor Guides | Stateline Guide",
    description: "Compare event calendars, newsletters, business directories, tourism guides, venue lineups, and advertising inquiry routes across the tri-county area.",
    h1: "Newsletters, calendars, directories, and visitor guides.",
    schemaType: "CollectionPage"
  },
  {
    path: "/posting/",
    title: "Where to Post Events, Notices & Listings in the Tri-County Area | Stateline Guide",
    description: "Separate official notices from community visibility, then verify boards, calendars, newsletters, directories, and public office posting routes.",
    h1: "Separate official notices from community visibility.",
    schemaType: "WebPage"
  },
  {
    path: "/region/",
    title: "Tri-County Regional Visibility Map | Stateline Guide",
    description: "Understand how Raton, Trinidad, Walsenburg, La Veta, Colfax, Las Animas, Huerfano, and statewide support systems connect.",
    h1: "Regional growth means crossing county lines on purpose.",
    schemaType: "AboutPage"
  },
  {
    path: "/counties/colfax/",
    title: "Colfax County Business, Event & Promotion Resources | Stateline Guide",
    description: "Use Raton, MainStreet, GrowRaton, Explore Raton, arts, media, county, and New Mexico support routes before building a new contact list.",
    h1: "Use Raton as the first visible hub.",
    schemaType: "CollectionPage"
  },
  {
    path: "/counties/las-animas/",
    title: "Las Animas County Business, Event & Nonprofit Resources | Stateline Guide",
    description: "Use Trinidad, tourism, the chamber, Colexico, city economic development, creative district, media, grants, and Colorado support routes.",
    h1: "Use Trinidad as the chamber, tourism, media, and creative-district hub.",
    schemaType: "CollectionPage"
  },
  {
    path: "/counties/huerfano/",
    title: "Huerfano County Event, Tourism & Business Resources | Stateline Guide",
    description: "Use Walsenburg, La Veta, Spanish Peaks Country, HCED, chamber, creative district, World Journal, and rural Colorado support routes.",
    h1: "Use Walsenburg, La Veta, Spanish Peaks Country, HCED, the chamber, creative district, and the World Journal.",
    schemaType: "CollectionPage"
  },
  {
    path: "/templates/",
    title: "Outreach Templates for Listings, Events, Media & Partners | Stateline Guide",
    description: "Copy and adapt outreach language for directories, event calendars, newsletters, partner asks, media inquiries, and correction requests.",
    schemaType: "WebPage"
  },
  {
    path: "/submit/",
    title: "Submit a Correction or Suggest a Regional Channel | Stateline Guide",
    description: "Send source-backed corrections, listing updates, new channel suggestions, or changed contact paths for review.",
    schemaType: "WebPage"
  },
  {
    path: "/appendix/",
    title: "Tri-County Public Contact Appendix | Stateline Guide",
    description: "Browse public-contact appendix entries by county, community, source, access mode, resource type, and update status.",
    schemaType: "CollectionPage"
  }
];
```

### Task route metadata

```ts
export const seoTaskRoutes: SeoRoute[] = [
  {
    path: "/where-to-post-events-raton-nm/",
    title: "Where to Post Events in Raton NM | Stateline Guide",
    description: "Find starting points for Raton event visibility, including city pages, tourism routes, media, calendars, public boards, partners, and verification steps.",
    h1: "Where to post events in Raton, New Mexico",
    schemaType: "CollectionPage"
  },
  {
    path: "/where-to-post-events-trinidad-co/",
    title: "Where to Post Events in Trinidad CO | Stateline Guide",
    description: "Use Trinidad tourism, city, chamber, creative district, venue, media, and community routes to submit or promote public events after verifying rules.",
    h1: "Where to post events in Trinidad, Colorado",
    schemaType: "CollectionPage"
  },
  {
    path: "/where-to-post-events-walsenburg-la-veta-co/",
    title: "Where to Post Events in Walsenburg & La Veta CO | Stateline Guide",
    description: "Find Huerfano County event routes through Spanish Peaks Country, Walsenburg, La Veta, libraries, media, arts, and tourism channels.",
    h1: "Where to post events in Walsenburg and La Veta",
    schemaType: "CollectionPage"
  },
  {
    path: "/where-to-advertise-trinidad-co/",
    title: "Where to Advertise in Trinidad CO | Stateline Guide",
    description: "Compare Trinidad-area promotion routes, including tourism channels, chamber options, media, venue lineups, newsletters, and paid-placement inquiries.",
    h1: "Where to advertise or promote something in Trinidad, Colorado",
    schemaType: "CollectionPage"
  },
  {
    path: "/colfax-county-business-resources/",
    title: "Colfax County Business Resources | Stateline Guide",
    description: "Start with Raton business services, licensing, GrowRaton, MainStreet, county resources, tourism, and New Mexico support before outreach.",
    h1: "Colfax County business resources",
    schemaType: "CollectionPage"
  },
  {
    path: "/las-animas-county-nonprofit-resources/",
    title: "Las Animas County Nonprofit Resources | Stateline Guide",
    description: "Find Trinidad and Las Animas nonprofit visibility, grant, partner, media, chamber, and community-resource routes with verification reminders.",
    h1: "Las Animas County nonprofit resources",
    schemaType: "CollectionPage"
  },
  {
    path: "/huerfano-county-event-calendars/",
    title: "Huerfano County Event Calendars & Visitor Listings | Stateline Guide",
    description: "Use Spanish Peaks Country, Walsenburg, La Veta, media, tourism, library, arts, and community calendars as Huerfano event starting points.",
    h1: "Huerfano County event calendars and visitor listings",
    schemaType: "CollectionPage"
  },
  {
    path: "/artist-gallery-promotion-raton-trinidad-walsenburg/",
    title: "Artist & Gallery Promotion in Raton, Trinidad & Walsenburg | Stateline Guide",
    description: "Route art shows, gallery events, makers, workshops, performances, and creative-sector announcements through arts, tourism, media, venue, and partner channels.",
    h1: "Artist and gallery promotion across the tri-county area",
    schemaType: "CollectionPage"
  },
  {
    path: "/regional-newsletters-event-calendars-visitor-guides/",
    title: "Regional Newsletters, Event Calendars & Visitor Guides | Stateline Guide",
    description: "Compare tri-county newsletters, event calendars, tourism guides, business directories, venue lineups, and placement inquiry paths.",
    h1: "Regional newsletters, event calendars, and visitor guides",
    schemaType: "CollectionPage"
  }
];
```

---

## 8. Head implementation

Create a component such as:

```txt
src/components/SeoHead.tsx
```

```tsx
import { SITE } from "../lib/seo/site";

export function absoluteUrl(path: string) {
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${SITE.origin}${cleanPath}`;
}

export function SeoHead({ path, title, description, image, noindex }) {
  const canonical = absoluteUrl(path);
  const ogImage = image ? absoluteUrl(image) : absoluteUrl("/assets/social/stateline-guide-og.png");

  return (
    <>
      <title>{title}</title>
      <meta name="description" content={description} />
      <link rel="canonical" href={canonical} />
      {noindex ? <meta name="robots" content="noindex, nofollow" /> : null}
      <meta property="og:site_name" content={SITE.name} />
      <meta property="og:type" content="website" />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={canonical} />
      <meta property="og:image" content={ogImage} />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={ogImage} />
    </>
  );
}
```

If the project is static HTML, inject equivalent tags directly into each page’s `<head>`.

---

## 9. Sitemap and robots

### `public/robots.txt`

```txt
User-agent: *
Allow: /

Sitemap: https://statelineguide.org/sitemap.xml
```

### `public/sitemap.xml`

Generate from route metadata. If static generation is easier, create this file manually:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://statelineguide.org/</loc></url>
  <url><loc>https://statelineguide.org/plan/</loc></url>
  <url><loc>https://statelineguide.org/network/</loc></url>
  <url><loc>https://statelineguide.org/amplifiers/</loc></url>
  <url><loc>https://statelineguide.org/posting/</loc></url>
  <url><loc>https://statelineguide.org/region/</loc></url>
  <url><loc>https://statelineguide.org/counties/colfax/</loc></url>
  <url><loc>https://statelineguide.org/counties/las-animas/</loc></url>
  <url><loc>https://statelineguide.org/counties/huerfano/</loc></url>
  <url><loc>https://statelineguide.org/templates/</loc></url>
  <url><loc>https://statelineguide.org/submit/</loc></url>
  <url><loc>https://statelineguide.org/appendix/</loc></url>
  <url><loc>https://statelineguide.org/where-to-post-events-raton-nm/</loc></url>
  <url><loc>https://statelineguide.org/where-to-post-events-trinidad-co/</loc></url>
  <url><loc>https://statelineguide.org/where-to-post-events-walsenburg-la-veta-co/</loc></url>
  <url><loc>https://statelineguide.org/where-to-advertise-trinidad-co/</loc></url>
  <url><loc>https://statelineguide.org/colfax-county-business-resources/</loc></url>
  <url><loc>https://statelineguide.org/las-animas-county-nonprofit-resources/</loc></url>
  <url><loc>https://statelineguide.org/huerfano-county-event-calendars/</loc></url>
  <url><loc>https://statelineguide.org/artist-gallery-promotion-raton-trinidad-walsenburg/</loc></url>
  <url><loc>https://statelineguide.org/regional-newsletters-event-calendars-visitor-guides/</loc></url>
</urlset>
```

---

## 10. Netlify redirects

Add only after the final domain is live:

```txt
# public/_redirects
https://wonderful-kashata-6ed008.netlify.app/* https://statelineguide.org/:splat 301!
http://statelineguide.org/* https://statelineguide.org/:splat 301!
http://www.statelineguide.org/* https://statelineguide.org/:splat 301!
https://www.statelineguide.org/* https://statelineguide.org/:splat 301!
```

Optional headers:

```txt
# public/_headers
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin

/assets/*
  Cache-Control: public, max-age=31536000, immutable
```

---

## 11. Structured data

### Rules

Add only structured data that describes visible content. Do not add fake ratings, fake reviews, fake office locations, hidden services, or event schema for events the site does not host.

Do **not** add `FAQPage` JSON-LD.

### WebSite JSON-LD

```js
export function websiteJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: "Stateline Guide",
    alternateName: "Tri-County Regional Marketing Guide",
    url: SITE.origin,
    description: SITE.defaultDescription,
    inLanguage: "en-US"
  };
}
```

Only add `SearchAction` if `/network/?q=` actually preloads a search query.

### Organization JSON-LD

```js
export function organizationJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "Stateline Guide",
    url: SITE.origin,
    description: SITE.defaultDescription,
    areaServed: [
      { "@type": "AdministrativeArea", name: "Colfax County, New Mexico" },
      { "@type": "AdministrativeArea", name: "Las Animas County, Colorado" },
      { "@type": "AdministrativeArea", name: "Huerfano County, Colorado" }
    ]
  };
}
```

### BreadcrumbList JSON-LD

```js
export function breadcrumbJsonLd(items) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: `${SITE.origin}${item.path}`
    }))
  };
}
```

Example:

```js
breadcrumbJsonLd([
  { name: "Home", path: "/" },
  { name: "Counties", path: "/region/" },
  { name: "Colfax County", path: "/counties/colfax/" }
]);
```

### CollectionPage JSON-LD

```js
export function collectionPageJsonLd(route) {
  return {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: route.title.replace(" | Stateline Guide", ""),
    url: `${SITE.origin}${route.path}`,
    description: route.description,
    isPartOf: {
      "@type": "WebSite",
      name: SITE.name,
      url: SITE.origin
    },
    about: [
      "regional marketing",
      "event promotion",
      "business directories",
      "local media",
      "visitor guides",
      "community resources",
      "Colfax County",
      "Las Animas County",
      "Huerfano County"
    ]
  };
}
```

### Optional Dataset JSON-LD

Use only for public downloadable inventory. Do not promise Google Search rich-result benefits.

```json
{
  "@context": "https://schema.org",
  "@type": "Dataset",
  "name": "Tri-County Regional Marketing Guide Inventory",
  "description": "A working inventory of local listings and leads across Colfax, Las Animas, Huerfano, and regional channels.",
  "url": "https://statelineguide.org/network/",
  "distribution": [
    {
      "@type": "DataDownload",
      "encodingFormat": "text/csv",
      "contentUrl": "https://statelineguide.org/assets/data/inventory.csv"
    },
    {
      "@type": "DataDownload",
      "encodingFormat": "application/json",
      "contentUrl": "https://statelineguide.org/assets/data/inventory.json"
    }
  ]
}
```

---

## 12. County-page additions

Add these blocks near the top of each county page.

### Colfax

```md
## What this county page helps with

Use this page to find public promotion, business-support, directory, calendar, media, tourism, funding, and partner routes in Colfax County. It is designed for businesses, artists, nonprofits, galleries, event organizers, service providers, and community programs that need a practical starting point.

### Common searches this page answers

- Raton business resources
- Colfax County business support
- Where to post events in Raton NM
- Raton tourism and visitor-facing listings
- Raton MainStreet and GrowRaton support routes
- Colfax County media and public-notice pathways
- New Mexico resources for local businesses and community programs
```

### Las Animas

```md
## What this county page helps with

Use this page to find public promotion, nonprofit, business, tourism, chamber, media, creative-district, event-calendar, grant, and partner routes in Las Animas County. Start with Trinidad-facing channels, then widen through Colexico, regional media, and Colorado support systems.

### Common searches this page answers

- Trinidad Colorado business resources
- Where to post events in Trinidad CO
- Las Animas County nonprofit resources
- Trinidad tourism event submission
- Trinidad chamber and Colexico routes
- Las Animas County grants and community resources
- Trinidad creative district and arts promotion channels
```

### Huerfano

```md
## What this county page helps with

Use this page to find public promotion, tourism, business, event-calendar, media, arts, chamber, economic-development, and partner routes in Huerfano County. Start with Walsenburg, La Veta, Spanish Peaks Country, HCED, the chamber, and regional media before building a manual contact list.

### Common searches this page answers

- Huerfano County event calendar
- Walsenburg business resources
- La Veta event promotion
- Spanish Peaks Country business directory
- Huerfano County visitor guide listings
- World Journal event and advertising inquiry
- Huerfano arts, gallery, and creative-district promotion
```

---

## 13. Task-page template

Use this template for all new task pages.

```md
# [Task + Place]

Short opening paragraph naming the place, audience, and why the page exists. Explain that users should verify rules before spending, printing, or promising placement.

## Best first routes

| Route type | Use first when | What to prepare | Verification note |
|---|---|---|---|
| Tourism/event calendar | The item is public and visitor-facing | Name, date, time, location, image, short description | Confirm eligibility and lead time |
| City/county source | The item involves official notices, permits, public meetings, or civic timing | Source link, official contact, legal name if needed | Confirm rules with office owner |
| Chamber/business directory | The item is a business, member update, or partner ask | Business name, category, website, address/service area | Confirm listing or member requirements |
| Media/newsletter | The item has public interest, event relevance, or community benefit | 50-word blurb, image, contact, deadline | Ask about editorial vs paid placement |
| Venue/partner channel | The item fits an existing audience or lineup | Flyer, description, target audience, public action | Ask before sending promotional assets |

## Use this sequence

1. Confirm whether the item is public, private, official, paid, nonprofit, visitor-facing, or partner-facing.
2. Prepare one clean packet.
3. Submit through the owner’s preferred form first.
4. Ask about deadlines, rates, and acceptance if the page does not say.
5. Save proof of submission, publication, or response.
6. Update the guide if a route changed.

## Next action

- [Find event calendars, newsletters, visitor guides, and directory channels](/amplifiers/)
- [Use copy-ready outreach templates](/templates/)
- [Separate official notices from community visibility](/posting/)
- [Submit a correction with a public source link](/submit/)
```

### Raton page intro

```md
Use this page when a public event, class, fundraiser, art opening, business launch, civic program, performance, or community activity needs visibility in Raton or Colfax County. Start with the source that best matches the event: city or county channels for official/public information, tourism and visitor-facing routes for events that serve travelers, media for public-interest announcements, and partner channels for aligned audiences. Do not treat every board, page, or newsletter as open advertising space. Verify the current rules before printing materials or promising placement.
```

### Trinidad page intro

```md
Use this page when a public event, art show, performance, market, workshop, nonprofit program, business announcement, or visitor-facing activity needs visibility in Trinidad or Las Animas County. Start with Trinidad tourism and city-facing routes when the event is public or visitor-relevant. Use chamber, creative-district, venue, media, and partner channels when the event fits their audience. Confirm submission rules, review time, image requirements, and whether placement is editorial, free, paid, or member-only.
```

### Walsenburg / La Veta page intro

```md
Use this page when a Huerfano County event, art show, farmers market, workshop, nonprofit program, visitor activity, gallery reception, performance, or local announcement needs public visibility. Start with Spanish Peaks Country, town/city routes, libraries, chamber or economic-development contacts, arts channels, and regional media. Treat public boards and calendars as owner-controlled channels. Verify current rules, review time, and whether the event fits before assuming placement.
```

---

## 14. Human-facing FAQ/help sections

Add FAQ sections for clarity. Do **not** add `FAQPage` JSON-LD.

### Amplifiers FAQ

```md
## Common questions

### Where should I post a public event first?

Start with event calendars, tourism calendars, venue lineups, city or community calendars, and partner channels that already serve the event’s audience. Use media and newsletters after checking whether the item fits their rules.

### Can I assume a newsletter accepts outside promotions?

No. Ask first. Do not assume ad availability, free placement, deadlines, audience size, endorsement, or acceptance unless the source confirms it.

### What should I prepare before submitting an event?

Prepare the event name, date, time, location, short description, contact link, square image, vertical image, flyer, accessibility notes, and whether the event is free, ticketed, nonprofit, youth, tourism, business, or community-oriented.
```

### Network FAQ

```md
## Common questions

### Is the inventory a verified directory?

No. Treat it as a working inventory of public leads and shortcuts. Open the source before using a listing for outreach, spending, printing, or eligibility decisions.

### What should I do when a listing is outdated?

Use the correction form and include a public source link, corrected name, county, community, contact route, and the reason for the update.

### Should I build a new contact list first?

Usually no. Start with public directories, chambers, tourism pages, media pages, public offices, and support organizations before building a manual list.
```

---

## 15. Internal-link rule

Every page should end with a “Next action” block using descriptive anchors.

Bad:

```md
[Learn more](/amplifiers/)
[Click here](/submit/)
```

Good:

```md
[Find event calendars, newsletters, visitor guides, and directory channels](/amplifiers/)
[Submit a correction with a public source link](/submit/)
```

Recommended page endings:

### Home

```md
## Next action

- [Plan the right outreach cycle before collecting links](/plan/)
- [Search public directories and local leads](/network/)
- [Find event calendars, newsletters, visitor guides, and directory channels](/amplifiers/)
- [Choose a county starting point](/region/)
```

### County pages

```md
## Next action

- [Find regional amplifier channels](/amplifiers/)
- [Use copy-ready outreach templates](/templates/)
- [Submit a county listing correction](/submit/)
- [Understand how the three counties connect](/region/)
```

---

## 16. Social image

Add:

```txt
public/assets/social/stateline-guide-og.png
```

Recommended dimensions:

```txt
1200 x 630 px
```

Content:

- `Stateline Guide`
- `Tri-County Regional Marketing Guide`
- `Colfax NM + Las Animas CO + Huerfano CO`

Avoid fake official seals, unreadable tables, or claims of government affiliation.

---

## 17. Analytics hooks

If no analytics provider is installed, add semantic data attributes only.

Track these actions later:

```txt
download_inventory_csv
download_inventory_json
download_sources
submit_correction_click
external_channel_click
network_search
network_filter_county
network_filter_resource_type
task_page_next_action
```

Example:

```html
<a href="/assets/data/inventory.csv" data-analytics="download_inventory_csv">Download CSV</a>
<a href="/submit/" data-analytics="submit_correction_click">Submit a correction</a>
```

---

## 18. Acceptance criteria

Before redeploy, verify:

- [ ] Every indexable route has a unique `<title>`.
- [ ] Every indexable route has a unique meta description.
- [ ] Every indexable route has one visible `<h1>`.
- [ ] Every indexable route has one absolute canonical URL.
- [ ] `/robots.txt` exists.
- [ ] `/sitemap.xml` exists.
- [ ] Sitemap is referenced in robots.txt.
- [ ] Sitemap URLs use the final canonical domain.
- [ ] Netlify preview redirect is active only after the final domain is live.
- [ ] No production route is accidentally `noindex`.
- [ ] Structured data describes visible content only.
- [ ] No `FAQPage` structured data exists.
- [ ] County pages include search-intent blocks.
- [ ] Task pages contain useful local guidance.
- [ ] Important content remains crawlable without JavaScript.
- [ ] Descriptive internal links replace vague “learn more” links where practical.
- [ ] Tables are usable on mobile or converted to cards.
- [ ] Audio and decorative animation controls remain user-controllable.

---

## 19. Codex copy-paste prompt

```md
Implement next-generation SEO for the Tri-County Regional Marketing Guide / Stateline Guide.

Use the attached SEO implementation brief as the source of truth.

Core goals:
1. Preserve the site’s purpose as a regional visibility routing guide for Colfax County NM, Las Animas County CO, and Huerfano County CO.
2. Add per-route metadata, canonical URLs, sitemap.xml, robots.txt, Open Graph tags, Twitter card tags, BreadcrumbList JSON-LD, WebSite JSON-LD, Organization JSON-LD, and CollectionPage JSON-LD.
3. Add task-based landing pages for Raton, Trinidad, Walsenburg/La Veta, county business resources, nonprofit resources, event calendars, artist/gallery promotion, and regional amplifier channels.
4. Add county search-intent blocks and descriptive “Next action” internal links.
5. Do not add FAQPage JSON-LD because FAQ rich results are no longer shown in Google Search as of May 7, 2026.
6. Keep all important content crawlable without JavaScript.
7. Do not invent placement guarantees, rates, deadlines, eligibility, audience size, or endorsement.
8. Use verification language wherever the site mentions listings, calendars, newsletters, ads, media, public boards, or partner channels.
9. If the final domain is unknown, use `PUBLIC_SITE_ORIGIN` and default placeholder `https://statelineguide.org`.

After implementation:
- Show changed files.
- Show sitemap contents.
- Confirm every route has title, meta description, canonical URL, and one H1.
- Confirm production pages are not noindexed.
- Confirm all new links are descriptive.
```

---

## 20. Search Console steps after redeploy

1. Add the final domain as a Domain property in Google Search Console.
2. Verify DNS ownership.
3. Submit:

```txt
https://statelineguide.org/sitemap.xml
```

4. Inspect these URLs first:

```txt
https://statelineguide.org/
https://statelineguide.org/counties/colfax/
https://statelineguide.org/counties/las-animas/
https://statelineguide.org/counties/huerfano/
https://statelineguide.org/amplifiers/
https://statelineguide.org/network/
```

5. Request indexing only after canonical URLs and sitemap output are correct.
6. Monitor queries by town, county, and task. Use query data to decide future task pages.
