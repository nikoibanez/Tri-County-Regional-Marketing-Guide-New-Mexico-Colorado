# Netlify Version Contrast Report

Date checked: 2026-07-06

## Short Answer

Of the four public Netlify URLs supplied, only `deluxe-horse-207efc` is publicly serving a guide page right now. It appears to be an older, single-page version. The more developed guide versions are present locally and in the repaired GitHub-ready package, but the other three Netlify URLs are currently returning 404 responses, so their live pages cannot be visually or structurally compared from the public web.

Best current base for publication: `dist/site` or the July 5 all-county event-posting package, not the currently live `deluxe-horse-207efc` site.

## Public URL Status

| URL | Public status | What it appears to be |
| --- | ---: | --- |
| `https://spontaneous-raindrop-55c1d4.netlify.app/` | 404 | No comparable public guide content available. |
| `https://darling-gecko-a7729a.netlify.app/` | 404 | No comparable public guide content available. |
| `https://wonderful-kashata-6ed008.netlify.app/` | 404 | No comparable public guide content available. |
| `https://deluxe-horse-207efc.netlify.app/` | 200 | Older live single-page guide. |

`deluxe-horse-207efc` served a page titled `Regional Marketing Guide & Business Support Resources` with the visible H1 `Tri-County Marketing Guide & Business Support Resources`. It did not serve `/resources/index.html`, `/resources/event-posting/index.html`, or `/sitemap.xml` publicly during this check.

## Local Version Lineage

These local deploy packages show the clearer development history:

| Version | HTML pages | Data files | Directory rows | Resource pages | Funding page | Arts & Culture | Event posting | LocalStash / Weekender references | Notes |
| --- | ---: | ---: | ---: | --- | --- | --- | --- | ---: | --- |
| `Tri_County_Regional_Marketing_Guide_Netlify_Deep.zip` | 23 | 5 | n/a | No | No | No | Yes | 0 | Earlier multi-page deep build. Has animations and some audio, but not the later resources structure. |
| `2026-06-30_Travel_Listings_Update.zip` | 36 | 9 | n/a | No | No | No | Yes | 0 | Adds travel/listing expansion, still before the later resource-directory restructure. |
| `2026-07-01_Directory_Sweep_Update.zip` | 36 | 22 | n/a | No | No | No | Yes | 0 | More data-heavy, but still not the final resources hub structure. |
| `tc-guide-20260701-resources-arts-audio.zip` | 39 | 24 | n/a | Yes | Yes | Yes | Yes | 0 | First strong resources/arts/audio structure. |
| `tc-guide-20260701-absolutely-everything.zip` | 39 | 26 | 1,591 | Yes | Yes | Yes | Yes | 0 | Adds the all-listings directory concept, but before later dedupe and description refinement. |
| `2026-07-01_Deduped_Rich_Directory_Update.zip` | 39 | 26 | 1,564 | Yes | Yes | Yes | Yes | 0 | Better deduped directory count. |
| `2026-07-01_Directory_Description_Overhaul.zip` | 39 | 26 | 1,564 | Yes | Yes | Yes | Yes | 0 | Better public-facing directory card language. |
| `2026-07-01_Directory_Overhaul_LocalStash.zip` | 40 | 26 | 1,576 | Yes | Yes | Yes | Yes | 76 | Adds LocalStash / Weekender channel work. |
| `2026-07-01_Mobile_Concise_Directory.zip` | 40 | 26 | 1,576 | Yes | Yes | Yes | Yes | 76 | Adds the mobile-concise direction while preserving directory depth. |
| `2026-07-05_Event_Posting_Update.zip` | 41 | 27 | 1,576 | Yes | Yes | Yes | Yes | 81 | Strongest event-posting expansion. |
| `2026-07-05_Event_Posting_All_Counties.zip` | 41 | 27 | 1,576 | Yes | Yes | Yes | Yes | 81 | Best deploy package found for all-county event posting. |
| `dist/site` | 41 | 27 | 1,576 | Yes | Yes | Yes | Yes | 81 | Current local generated site. |
| `dist/NE362B~1.ZIP_v1` | 41 | 25 | 1,576 | Yes | Yes | Yes | Yes | 81 | Repaired GitHub-ready extracted version with `index.html` at repo root and `netlify.toml` publishing from `.`. |

## Main Contrast

### 1. Publicly Live Version Is Not The Most Complete

`deluxe-horse-207efc` is the only live public URL, but it behaves like an older single-page version. It has a large standalone HTML payload, but the newer route structure is absent publicly:

- no public `/resources/index.html`
- no public `/resources/event-posting/index.html`
- no public `/sitemap.xml`
- no detected `Directory of Absolutely Everything`
- no detected LocalStash / Weekender content
- still contains multiple `Google` references
- still contains visible `Super Eukarya` references

This means it is useful as a working live preview of an earlier draft, but it should not be treated as the final site candidate.

### 2. Current Local Version Has The Better Information Architecture

The current local site and July 5 packages have the structure that matches the recent project direction:

- multi-page site instead of one long HTML file
- Resources hub
- Funding page
- Arts & Culture page
- Event-posting page
- directory data exports
- 1,576-row all-listings directory
- public-domain / rights-conscious audio assets
- animated regional SVG assets
- `robots.txt`
- `sitemap.xml`
- no visible Super Eukarya mentions in scanned HTML text

This is the cleaner foundation for Netlify/GitHub deployment.

### 3. Directory Evolution Is Clear

The directory grew in this sequence:

1. Travel and listing expansion.
2. Directory sweep data expansion.
3. Resources / arts / audio page structure.
4. `Directory of Absolutely Everything` concept.
5. Deduped richer directory.
6. Better listing descriptions.
7. LocalStash / Weekender channel references.
8. Mobile-concise directory structure.
9. All-county event-posting channels.

The best directory baseline is the July 5 all-county package or `dist/site`, because it keeps the deduped 1,576-entry directory while also retaining event-posting and LocalStash-related channel work.

### 4. The Three 404 Sites Cannot Be Content-Compared Publicly

The three 404 Netlify URLs may still have deploy history inside Netlify, but public access does not expose their guide content. To compare those exact Netlify versions, one of these is needed:

- Netlify deploy logs and deploy file browser for each site.
- The GitHub repo each Netlify site is connected to.
- The deploy zip or extracted deploy folder for each site.
- Netlify CLI login so the local machine can inspect site configuration and deploy history.

Without that, the honest public contrast is availability only: they are not serving their guide content.

## Recommendation

Use `dist/site` as the canonical working version and use the July 5 all-county event-posting package as the best portable deploy snapshot:

`dist/NETLIFY_DEPLOY_Tri_County_Regional_Marketing_Guide_2026-07-05_Event_Posting_All_Counties.zip`

For GitHub-connected Netlify:

- Main repo: publish `dist/site`.
- Repaired extracted repo: publish `.`.

Do not keep building from `deluxe-horse-207efc` unless the goal is to preserve an older single-page draft for reference.

## Next Useful Comparison

If the goal is editorial/design comparison rather than deployment comparison, the next report should compare:

1. current `dist/site`
2. `deluxe-horse-207efc` live page
3. July 5 all-county package
4. July 1 mobile-concise package

That would let the decision be less about which files exist and more about which user experience is clearest.
