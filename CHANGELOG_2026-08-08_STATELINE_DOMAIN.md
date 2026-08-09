# Changelog — 2026-08-08

## Added

- Reusable `Stateline Tri-County Guide` SVG logo with accessible title and description.
- Organization-logo structured data.
- Open Graph and Twitter image alternative text.
- Verified integration report covering project/task reconciliation, responsive behavior, SEO, WCAG, directory research, and QA.

## Changed

- Made `https://statelineguide.org` the canonical build origin in Netlify, the generator, source audits, smoke tests, weekly checks, and deployment documentation.
- Unified visible branding, site metadata, JSON-LD, navigation labeling, home heading, route-title suffixes, and favicon labeling under **Stateline Tri-County Guide**.
- Preserved `Tri-County Regional Marketing Guide` as an alternate descriptive name for search context.
- Corrected the accessibility audit so it detects obsolete generated MP3 names without falsely rejecting the new `stateline-...` logo asset.
- Kept the GitHub quality gate's local smoke test local even when the canonical production-origin variable is set; live-domain smoke testing remains a separate deployment check.

## Preserved

- Existing responsive multi-page architecture.
- Super Eukarya palette and animated high-desert/yucca system.
- Reduced-motion handling, directory assistant, posting guidance, outreach classifications, source verification labels, and placeholder/exclusion safeguards.
- Pre-existing uncommitted generator work in a recoverable Git stash; it was not reapplied because part of its time-sensitive funding copy had expired.

## Deployment

- GitHub/Netlify deployment source: `master` in `nikoibanez/Tri-County-Regional-Marketing-Guide-New-Mexico-Colorado`.
- Netlify fallback: `https://newmexicocoloradoguide.netlify.app`.
- Custom domain: `https://statelineguide.org` after Netlify domain attachment and DNS configuration.
