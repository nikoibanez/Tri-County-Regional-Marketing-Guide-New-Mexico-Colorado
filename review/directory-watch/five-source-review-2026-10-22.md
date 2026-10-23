# Five-source directory expansion review

Status: **pending human review before production**. Prepared 2026-10-22 from public source pages. Directory rows and contact details are proposed changes, not approved listings or endorsements.

## New watched sites

| County scope | Source | What it contributes |
| --- | --- | --- |
| Colfax | [Red River Chamber member listings](https://redriverchamber.org/business-listing/) | Individual Red River member profiles and contact paths |
| Regional, filter by town | [El Raton Media Works local businesses](https://www.elratonmediaworks.org/local-businesses) | Raton-area business profiles; also contains out-of-county places |
| Las Animas | [Canyons & Plains county attractions](https://canyonsandplains.org/destination-item/las-animas-county/) | Museum, heritage, and visitor destination links |
| Las Animas | [Trinidad Community Foundation](https://www.trinidadcf.org/organizations.html) | Fiscal sponsorship and local program leads |
| Huerfano | [Wheelhouse retailers](https://www.wheelhouseincubator.org/our-retailers) | Walsenburg makers and small retailers |

All six final seed pages across these five sites returned HTTP 200. The watch registry grows from 15 to 20 sources. El Raton Media Works and Wheelhouse were already public hub shortcuts; the other three are proposed new shortcuts. The Wheelhouse homepage was dropped from the seed set after it yielded non-retailer headings; only its retailer page is watched.

## Proposed listings

Nine source-linked rows were added to the review branch's canonical CSV and JSON: Bearly Awake Coffee Co., Mountain Body & Mind, Rio Colorado Cabins, Zancana Bakery (Colfax); Canyons & Plains Las Animas County Guide, Louden-Henritze Archaeology Museum, Trinidad Community Foundation Fiscal Sponsorship (Las Animas); SoapBox and O'BeDazzle Boutique (Huerfano). See [the import manifest](five-source-import-2026-10-22.json) for direct source paths and fields. The generated listing count rises from 1,362 to 1,371 in this branch; production is unchanged until review and merge.

Review business names, town/county, contact fields, descriptions, and fit before merge. Rows with `needs_follow_up=true` need an additional current primary-source check. The Canyons & Plains county travel page has no town assigned because it is a regional page, not a confirmed Trinidad office. No advertising acceptance, grant eligibility, or listing approval is inferred.

## Exclusions and watch limits

- El Raton Media Works also links to businesses outside the three counties, including Texas and Union County, NM; these were not imported.
- The Raton Motor Pass profile links to the Well Hotel site, so it was not imported as a distinct business without a current direct page.
- Patchwork Phoenix was already in the master data; the shared retailer page must not make every heading look like an existing record.
- The Canyons & Plains watch filters internal navigation and generic external review/news hosts. Wheelhouse retailer headings are low-confidence leads until checked against a business page.
- Two older Raton Chamber seed pages returned HTTP 403 to the automated watcher. That is an access limit, not evidence that those businesses closed or that the URLs are broken. The five new sites did not fail in the initial run.

Final watcher check: 20 sources, 38 pages, 2 access failures, 85 possible leads (15 priority and 70 low-confidence). These are review candidates, not 85 proposed public listings. The canonical build reports 1,371 local entries and 120 directory shortcuts; exclusion check, quality audit, canonical integration check, and 105 unit tests pass. Mobile directory search showed the new Bearly Awake entry with no horizontal overflow at 390px; production was not changed.
