# Comprehensive Deploy Zip Contrast Report

Date checked: 2026-07-06

## Scope

This audit compared every plausible Tri-County Guide deploy or site-related zip found under the obvious local shared locations on this device:

- `Documents`
- `Downloads`
- `Desktop`
- `OneDrive`, if present

It also checked the currently visible local Git repos, the known GitHub remotes, and the four Netlify URLs supplied in the thread.

Machine-readable inventory files were generated beside this report:

- `review/ALL_DEVICE_SITE_ZIP_INVENTORY_20260706.csv`
- `review/ALL_DEVICE_SITE_ZIP_INVENTORY_20260706.json`

## Inventory Counts

- Candidate zip files found: 35
- Unique zip archives after hash dedupe: 26
- Unique deployable site zips: 24
- Laptop handoff archives: 1 unique archive, 2 local copies
- Visual/style asset package: 1 unique archive, 2 local copies
- Unreadable zips after short-path retry: 0

## Best Current Version

Use this as the strongest current deploy snapshot:

`dist/NETLIFY_DEPLOY_Tri_County_Regional_Marketing_Guide_2026-07-05_Event_Posting_All_Counties.zip`

Why:

- 41 HTML files
- 27 data files
- 1,576 `Directory of Absolutely Everything` rows
- Funding page present
- Arts & Culture page present
- Resources page present
- Event-posting route present
- LocalStash / Weekender content present
- all-county event-posting expansion present
- `sitemap.xml` present
- `netlify.toml` present
- `index.html` at zip root

The current local generated directory, `dist/site`, appears aligned with this late-stage family. The repaired GitHub-ready extracted repo at `dist/NE362B~1.ZIP_v1` is also in the same family and has `index.html` at repo root.

## Live Site Contrast

| Netlify URL | Direct check status | What it most likely represents |
| --- | ---: | --- |
| `https://spontaneous-raindrop-55c1d4.netlify.app/` | 404 | Not currently serving a comparable public guide. |
| `https://darling-gecko-a7729a.netlify.app/` | 404 | Not currently serving a comparable public guide. |
| `https://wonderful-kashata-6ed008.netlify.app/` | 404 by direct curl/PowerShell check | Ambiguous: a browser/web fetch surfaced a multi-page Stateline Guide snapshot, but direct requests from this machine returned Netlify 404. Treat as stale, cached, or configuration-inconsistent until verified in a normal browser. |
| `https://deluxe-horse-207efc.netlify.app/` | 200 | Older single-page guide. Useful as a historical comparison, not the strongest current version. |

The live `deluxe-horse` page is not the current best candidate because it lacks the later multi-page resources structure and did not serve `/resources/index.html`, `/resources/event-posting/index.html`, or `/sitemap.xml` during this check.

## GitHub / Repo State

| Local repo | Remote | Branch | Head |
| --- | --- | --- | --- |
| main guide workspace | `https://github.com/nikoibanez/Tri-County-Regional-Marketing-Guide-New-Mexico-Colorado.git` | `master` | `bd20676 Add all-county event posting hub` |
| repaired extracted deploy repo | `https://github.com/nikoibanez/NE362B-1.ZIP_v1.git` | `main` | `5fc7ffc Publish extracted Netlify site files` |

Remote checks matched these heads:

- main guide repo: `bd20676913a889179c5cc00826c2caaa2e8aef34`
- repaired extracted repo: `5fc7ffc469e9d00c004cf65f69d068b4558f9a32`

The public GitHub API surfaced the main guide repo. `git ls-remote` could also see the repaired extracted repo.

## Version Lineage Table

| Date | Version / archive | HTML | Guide rows | Everything rows | Resources | Funding | Arts | Event posting | LocalStash refs | Event refs | Copies |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| 2026-06-20 | `tri-county-netlify-upload.zip` | 1 |  |  |  |  |  |  |  |  | 2 |
| 2026-06-21 | `Tri_County_Regional_Marketing_Guide_v2026-06-21_yucca-netlify` | 13 | 456 |  |  |  |  | Y |  |  | 1 |
| 2026-06-22 | `Tri_County_Regional_Marketing_Guide_v2026-06-22_verified-process-netlify` | 13 | 456 |  |  |  |  | Y |  |  | 1 |
| 2026-06-22 | `Tri_County_Regional_Marketing_Guide_v2026-06-22_stateline-cycle-tools` | 13 | 456 |  |  |  |  | Y |  |  | 1 |
| 2026-06-22 | `Tri_County_Regional_Marketing_Guide_v2026-06-22_infographic-cursor` | 13 | 456 |  |  |  |  | Y |  |  | 1 |
| 2026-06-22 | `Tri_County_Regional_Marketing_Guide_v2026-06-22_submit-routing-cursor` | 14 | 456 |  |  |  |  | Y |  |  | 1 |
| 2026-06-22 | `Tri_County_Regional_Marketing_Guide_v2026-06-22_svg-ui-methodology` | 14 | 456 |  |  |  |  | Y |  |  | 1 |
| 2026-06-22 | `Tri_County_Regional_Marketing_Guide_v2026-06-22_no-infographics-ellipse-heroes` | 14 | 456 |  |  |  |  | Y |  |  | 1 |
| 2026-06-22 | `Tri_County_Regional_Marketing_Guide_v2026-06-23_grouped-nav-human-copy` | 14 | 456 |  |  |  |  | Y |  |  | 1 |
| 2026-06-23 | `Tri_County_Regional_Marketing_Guide_v2026-06-23_geo-hero-variants` | 14 | 456 |  |  |  |  | Y |  |  | 1 |
| 2026-06-23 | `Tri_County_Regional_Marketing_Guide_v2026-06-23_softened-animation-audio` | 14 | 456 |  |  |  |  | Y |  |  | 1 |
| 2026-06-23 | `Tri_County_Regional_Marketing_Guide_v2026-06-23_piano-intro` | 14 | 456 |  |  |  |  | Y |  |  | 1 |
| 2026-06-24 | `2026-06-24_funding-directory-expansion` | 14 | 456 |  |  |  |  | Y |  |  | 1 |
| 2026-06-27 | `Tri_County_Regional_Marketing_Guide_Netlify_Deep.zip` | 23 | 632 |  |  |  |  | Y |  | 30 | 3 |
| 2026-06-27 | `Tri_County_Guide_Laptop_Codex_Handoff_2026-06-27.zip` | 24 |  |  |  |  |  | Y |  | 30 | 2 |
| 2026-06-30 | `2026-06-30_Travel_Listings_Update` | 36 | 895 |  |  |  |  | Y |  | 31 | 1 |
| 2026-07-01 | `2026-07-01_Directory_Sweep_Update` | 36 | 1,491 |  |  |  |  | Y |  | 31 | 1 |
| 2026-07-01 | `tc-guide-20260701-resources-arts-audio.zip` | 39 | 1,491 |  | Y | Y | Y | Y |  | 32 | 1 |
| 2026-07-01 | `tc-guide-20260701-absolutely-everything.zip` | 39 | 1,491 | 1,591 | Y | Y | Y | Y |  | 32 | 1 |
| 2026-07-01 | `2026-07-01_Deduped_Rich_Directory_Update` | 39 | 1,491 | 1,564 | Y | Y | Y | Y |  | 32 | 2 |
| 2026-07-01 | `2026-07-01_Directory_Description_Overhaul` | 39 | 1,491 | 1,564 | Y | Y | Y | Y |  | 32 | 2 |
| 2026-07-01 | `2026-07-01_Directory_Overhaul_LocalStash` | 40 | 1,491 | 1,576 | Y | Y | Y | Y | 76 | 35 | 2 |
| 2026-07-01 | `2026-07-01_Mobile_Concise_Directory` | 40 | 1,491 | 1,576 | Y | Y | Y | Y | 76 | 36 | 2 |
| 2026-07-04 | `2026-07-05_Event_Posting_Update` | 41 | 1,491 | 1,576 | Y | Y | Y | Y | 81 | 114 | 1 |
| 2026-07-04 | `2026-07-05_Event_Posting_All_Counties` | 41 | 1,491 | 1,576 | Y | Y | Y | Y | 81 | 114 | 1 |

## What Changed Over Time

### Early single-file guide

The earliest `tri-county-netlify-upload.zip` is a deployable one-page site. It still contains visible Super Eukarya references and does not have the later multi-page resource architecture.

### June 21-24 version folder builds

These are useful design and implementation milestones:

- yucca/Netlify packaging
- verified-process language
- Stateline cycle tools
- cursor and infographic experiments
- submit/update routing
- SVG methodology
- removal of infographics and ellipse-style hero direction
- grouped navigation and more human copy
- geological hero variants
- softened animation/audio direction
- piano intro experiment
- funding-directory expansion

They remain older because they carry only 456 guide rows and do not include the later Resources, Funding, Arts & Culture, and Everything Directory structure.

### June 27 deep build and laptop handoff

This is the first stronger portable package family:

- 23 HTML files in the deploy zip
- 632 guide rows
- 16 animation assets
- 3 audio assets
- sitemap present
- event-posting page present

The laptop handoff zip is not itself a clean Netlify deploy root, but it preserves the deploy package and supporting files for transferring work across devices.

### June 30 travel listings update

This is a clear data expansion step:

- 36 HTML files
- 895 guide rows
- travel/listing expansion
- still before the consolidated Resources / Funding / Arts & Culture structure

### July 1 directory and resources restructuring

This is where the site became much closer to the current product:

- directory sweep increased the guide data to 1,491 rows
- resources/arts/audio package introduced the modern Resources, Funding, and Arts & Culture pages
- Everything Directory appeared with 1,591 rows
- dedupe reduced that to 1,564 rows
- description overhaul improved public-facing listing language
- LocalStash / Weekender work raised the Everything Directory to 1,576 rows
- mobile-concise version kept the richer directory while reducing mobile page burden

### July 5 all-county event-posting builds

These are the strongest deploy packages found:

- 41 HTML files
- 27 data files
- 1,576 Everything Directory rows
- 81 LocalStash / Weekender references
- 114 event-posting references
- all major resource pages present

The `All_Counties` package is the most complete named deploy package.

## Duplicate Groups Worth Knowing

Several archives are exact duplicate copies:

- `tri-county-netlify-upload.zip`: duplicated in both attachment review folders.
- `super_eukarya_site_visuals_and_codex_notes.zip`: duplicated in both attachment review folders.
- June 27 `Tri_County_Regional_Marketing_Guide_Netlify_Deep.zip`: duplicated in `dist`, the laptop handoff deploy folder, and the Desktop ready-for-Netlify folder.
- July 1 deduped rich directory, description overhaul, LocalStash, and mobile concise zips: each exists in both `dist` and `Downloads`.
- Laptop handoff archive: duplicated in `outputs` and Desktop ready-for-Netlify folder.

## Practical Recommendation

Do not publish from the older live `deluxe-horse` page except as a historical reference.

Publish one of these instead:

1. Main GitHub-connected Netlify site: use the main repo, branch `master`, publish directory `dist/site`.
2. Extracted deploy repo: use `nikoibanez/NE362B-1.ZIP_v1`, branch `main`, publish directory `.`.
3. Manual zip deploy: use `dist/NETLIFY_DEPLOY_Tri_County_Regional_Marketing_Guide_2026-07-05_Event_Posting_All_Counties.zip`.

If only one version should survive as canonical, keep `dist/site` as working source output and keep the July 5 all-county zip as the portable release artifact.

## Caveat

This report compares file structure, embedded content signals, local archive hashes, and live URL availability. It does not visually QA every page. A final publication review should still load the chosen version in desktop and mobile viewports and check the landing animation, directory search, submit-update page, Resources pages, Funding page, Arts & Culture page, and event-posting routes.
