# Tri-County Common Directory Sweep — Starter Matrix

Generated as a supplement for extending the business-lead discovery pass beyond YellowPages.com.

## Scope

Primary municipalities and communities searched/queued:

- **Colfax County, NM:** Raton, Angel Fire, Cimarron, Eagle Nest, Maxwell, Springer, Ute Park, Miami, Folsom, Vermejo Park.
- **Las Animas County, CO:** Trinidad, Aguilar, Branson, Cokedale, Kim, Starkville, Hoehne, Jansen, Segundo, Valdez, Weston, Stonewall, Bon Carbo.
- **Huerfano County, CO:** Walsenburg, La Veta, Gardner, Cuchara, Badito, Farisita, Redwing.

## Directory sources queued

- YellowPages.com
- YellowPagesDirectory.com
- Manta
- MerchantCircle
- Cylex
- Hotfrog
- Brownbook
- ChamberofCommerce.com
- BBB
- Tripadvisor
- Yelp
- Google Business Profile / Maps
- Apple Maps / Apple Business Connect
- Bing Places / Bing Maps

## Current extraction status

YellowPages.com remains the strongest bulk source exposed in this environment. The current YellowPages export has **650** deduplicated rows already available.

Other large directories are queued with reusable municipality search URLs. Many did not expose stable bulk listing pages through this browsing environment and should be treated as manual/API/browser-assisted verification passes rather than direct import sources.

## Publication rule

Do not publish commercial-directory-only records as verified local business listings.

Use these labels:

- `commercial_directory_unverified`
- `needs_verification`
- `duplicate_candidate`
- `publish_candidate_after_confirmation`
- `do_not_publish_without_confirmation`

A record becomes a stronger publication candidate only when confirmed by at least one of:

- official city/county/chamber/tourism source
- business-owned website
- current public social page controlled by the business
- current venue/event/business listing controlled by the business or host organization

## Recommended next extraction order

1. Finish YellowPages.com remaining pages where accessible.
2. Use YellowPagesDirectory.com, Manta, MerchantCircle, Cylex, Hotfrog, Brownbook, and ChamberofCommerce.com as lead-discovery only.
3. Use BBB, Tripadvisor, Yelp, Google/Apple/Bing map pages as verification and category-strengthening layers.
4. Deduplicate by normalized business name + city, then review chains/public offices/churches/schools separately.
5. Only after verification, merge into the Netlify guide data.

## Files in this package

- `tri_county_directory_sweep_matrix.csv` — full directory × municipality sweep matrix.
- `priority_directory_sweep_queue.csv` — highest-priority checks first.
- `current_extracted_leads_summary.csv` — summary of the existing YellowPages export by city.
