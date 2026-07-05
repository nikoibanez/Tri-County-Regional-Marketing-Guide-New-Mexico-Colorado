# Directory Overhaul, Navigation, and LocalStash QA - 2026-07-01

## Implemented

- Rewrote directory card descriptions through the generator so generic import language is replaced with practical descriptions based on name, category, town/county, source type, and known links.
- Renamed public listing links away from `Source 1` / `Source 2` patterns and toward user-facing labels such as website, Facebook page, tourism listing, chamber directory, map, email, phone, and correction path.
- Expanded directory cards to show all available contact links and related pages instead of slicing contact/source arrays.
- Preserved a raw provenance snapshot at `review/DIRECTORY_RAW_PROVENANCE_SNAPSHOT_20260701.json`.
- Cleaned Netlify-shipped public HTML, JS, JSON, and CSV exports so old import labels do not appear in public files.
- Added LocalStash and Weekender/LocalStash Magazine as directory shortcuts and amplifier channels.
- Reworked navigation language so `Resources` is now a clearer `Directory` area and marketing instruction material has a separate `promote/index.html` playbook.
- Simplified legacy `network/index.html` structured data to a compact `CollectionPage` block instead of a huge item-level JSON-LD payload.
- Added metadata/JSON-LD backfill for older generated pages.

## LocalStash / Weekender Treatment

LocalStash and Weekender are included as routing channels, not guaranteed placement channels. Public copy should still ask users to verify current terms, rates, dates, eligibility, and acceptance before promising placement.

Included rows:

- LocalStash Free Biz Map Pins
- LocalStash Business Owner FAQ
- LocalStash Chamber, Visitor Center and Tourism Board FAQ
- LocalStash Magazine: SoCO & NoNM
- LocalStash town pages for Trinidad, Walsenburg/La Veta/Cuchara, Raton, Angel Fire, Cimarron, and Eagle Nest
- Weekender Magazines SoCO & NoNM
- Weekender Sample Issue and Rate Sheet

## Audit Results

- Public old labels removed across HTML/JS/JSON/CSV: `Source 1`, `Source 2`, `Visitor-facing listing from`, `Visitor-facing listing pulled`, `Use this as a starting contact`, `Open source`, `Open the source`, `Business type not clear`, `Yellow Pages bulk source`, `Resource hub`, `Search all resources`.
- Directory entries: 1,576.
- Exact duplicate name/county/town groups: 0.
- Entries with a contact path: 809.
- Entries with related pages: 1,414.
- Directory shortcuts: 112.
- LocalStash rows: 10.
- Weekender rows: 2.
- Page metadata/accessibility check: no missing page titles, meta descriptions, skip links, or JSON-LD on public content pages.
- Local smoke checks returned HTTP 200 for:
  - `http://127.0.0.1:8791/resources/index.html#everything-directory`
  - `http://127.0.0.1:8791/promote/index.html`
  - `http://127.0.0.1:8791/network/index.html`

## Files Changed By Generator

- `scripts/implement_resources_arts_audio_update.py`
- `C:\Users\Alyxx and Niko\TriCountyGuide_20260701_DirectorySweep_Site`
- public data exports under `C:\Users\Alyxx and Niko\TriCountyGuide_20260701_DirectorySweep_Site\data`
- public browser data at `C:\Users\Alyxx and Niko\TriCountyGuide_20260701_DirectorySweep_Site\assets\site-data.js`

