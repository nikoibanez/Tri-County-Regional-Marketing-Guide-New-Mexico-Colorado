# Absolutely Everything Directory Dedup Quality Pass

Date: 2026-07-01

## Result

- Rebuilt `The Directory of Absolutely Everything` as a deduped, public-facing listing directory.
- Final count: 1,564 entries.
- Listings: 1,464.
- Directory shortcuts: 100.
- Entries with at least one contact path: 797.
- Website/listing links: 598 entries.
- Email links: 27 entries.
- Phone links: 178 entries.
- Address/map links: 467 entries.

## Duplicate Review

- Normalized duplicate groups by name + county + town: 0.
- `111 Park Espresso Bar` now appears once.
- The former `111 Park Espresso Bar / Enchanted Grounds Espresso Bar` row is merged as an alias on the `111 Park Espresso Bar` card.
- The `+ email 8 website` scrape artifact is removed from public output and merged into the `Thrift Shoppe` listing where the source fields indicated the shifted name/address.

## Public-Facing Field Review

Each exported entry now carries:

- Name and aliases.
- County, town, and state.
- Category and entry type.
- Short public description.
- Clickable websites, emails, phone numbers, source links, and map-search links when available.
- Public audience labels.
- Guide keywords.
- Possible marketing channels to ask about.
- A correction/update path.

## Language Cleanup

Removed visible source-sweep/internal wording from the public directory output:

- `lead-discovery`
- `source-check candidate`
- `spreadsheet-backed`
- `commercial-directory-only`
- `+ email 8 website`
- `Lead Sweep`

## Link Checks

- Missing local links across generated HTML files: 0.
- `resources/index.html` contains 1,564 rendered directory cards.
- CSV rows and JSON rows match exactly: 1,564.

## Remaining Caution

The directory still treats entries as practical starting points. Users should check current details with the listed source or organization before spending money, printing materials, promising placement, or treating outreach channels as available.
