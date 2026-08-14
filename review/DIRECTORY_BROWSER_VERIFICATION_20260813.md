# Directory Browser Verification

Reviewed: 2026-08-13

This review separates current public pages, retired links, automation-only access failures, and misleading keyword inferences. A scripted 403, timeout, or certificate-chain error is not treated as proof that an organization or program is gone.

## Priority Directory Leads

The three high-priority candidates from the weekly directory watch are already represented in the canonical guide.

| Candidate | Existing directory entry | Match evidence | Decision |
| --- | --- | --- | --- |
| Kathy Hills Studio Gallery | Kathy Hills Studio Gallery / Spanish Peaks Art | Existing alias and current Spanish Peaks Country profile | Do not add a duplicate |
| Walsenburg Mining Museum | Walsenburg Mining Museum / Huerfano County Historical Society | Existing alias and current profile | Do not add a duplicate |
| World Journal | The World Journal | Existing listing URL and current profile | Do not add a duplicate |

The weekly watcher now compares aliases and normalized listing URLs as well as primary names.

## Retired Or Unsafe Public Links

Normal-browser checks confirmed that eleven individual Angel Fire Chamber profile URLs render the chamber's 404 page. Their directory category routes remain useful, and current direct or hosted profiles replace the retired URLs where one was confirmed.

| Listing | Retired or unsafe link | Public replacement |
| --- | --- | --- |
| Angel's Outback Adventure | Angel Fire Chamber profile | Visit Angel Fire entity profile |
| Big River Raft Trips | Angel Fire Chamber profile | `bigriverrafts.com` and Visit Angel Fire profile |
| Casa de Artesanias | Angel Fire Chamber profile | Category routes retained; no direct replacement confirmed |
| Enchanted Circle Pottery | Angel Fire Chamber profile | Angel Fire Studio Tour artist profile |
| Far Flung Adventures | Angel Fire Chamber profile | `farflung.com` |
| Golden Eagle RV Park & Resort | Angel Fire Chamber profile | `goldeneaglerv.com` |
| J & A's Cafe @ the Roadrunner | Angel Fire Chamber profile | Category routes retained; no first-party replacement confirmed |
| Monte Verde RV Park & Campground | Angel Fire Chamber profile | `monteverderv.com` and Village of Angel Fire page |
| Nuckolls Brewing Co. | Angel Fire Chamber profile | `nuckollsbrewing.com` |
| Taos Lifestyle | Angel Fire Chamber profile | `taoslifestyle.com` |
| Taty @ the Bump | Angel Fire Chamber profile | Existing business Facebook page |
| Walsenburg Studio | `walsenburgstudio.com` | Spanish Peaks Country entity profile; the former domain now shows an unrelated storefront |

The former Enchanted Circle Pottery direct site also has an invalid certificate. The current Angel Fire Studio Tour profile replaces it as the clickable public route.

## Automation-Blocked Pages

The post-repair source audit contains 21 `access_blocked` URLs. These pages rejected the unattended checker, but that result alone does not mean the page is broken.

| Page | URL | Script result |
| --- | --- | --- |
| Candid Funding Search and Learning | [Free access to Foundation Directory](https://learning.candid.org/free-access-to-foundation-directory) | HTTP 403 |
| Colorado Advanced Industries Accelerator Programs | [Program page](https://oedit.colorado.gov/advanced-industries-accelerator-programs) | HTTP 403 |
| Colorado Business Funding and Incentives | [Funding and incentives](https://oedit.colorado.gov/business-funding-and-incentives) | HTTP 403 |
| Colorado Rural Opportunity Office | [Rural Opportunity Office](https://oedit.colorado.gov/category/rural-opportunity-office) | HTTP 403 |
| Colorado Community Revitalization Grant | [Grant page](https://oedit.colorado.gov/colorado-community-revitalization-grant) | HTTP 403 |
| Colorado Creates Grant | [Grant page](https://oedit.colorado.gov/colorado-creates-grant) | HTTP 403 |
| Colorado Creative Industries | [Program page](https://oedit.colorado.gov/colorado-creative-industries) | HTTP 403 |
| Colorado SBDC Network | [SBDC network page](https://oedit.colorado.gov/colorado-small-business-development-center-network) | HTTP 403 |
| Folk and Traditional Arts Project Grant | [Grant page](https://oedit.colorado.gov/folk-and-traditional-arts-project-grant) | HTTP 403 |
| Colorado Rural Jump-Start Program | [Program page](https://oedit.colorado.gov/rural-jump-start-program) | HTTP 403 |
| Visit Angel Fire Events | [Events calendar](https://visitangelfirenm.com/events/) | HTTP 403 |
| Visit Angel Fire Get Listed | [Get-listed route](https://visitangelfirenm.com/get-listed/) | HTTP 403 |
| U.S. Economic Development Administration | [Funding opportunities](https://www.eda.gov/funding/funding-opportunities) | HTTP 403 |
| IFundWomen Grants | [Grant application route](https://www.ifundwomen.com/grants/apply-for-grants) | HTTP 403 |
| USDA Rural Development | [Programs and services](https://www.rd.usda.gov/programs-services) | HTTP 403 |
| USDA Rural Business Development Grants | [Grant page](https://www.rd.usda.gov/programs-services/business-programs/rural-business-development-grants) | HTTP 403 |
| USDA Rural Microentrepreneur Assistance Program | [Program page](https://www.rd.usda.gov/programs-services/business-programs/rural-microentrepreneur-assistance-program) | HTTP 403 |
| USDA Value-Added Producer Grants | [Grant page](https://www.rd.usda.gov/programs-services/business-programs/value-added-producer-grants) | HTTP 403 |
| City of Walsenburg agendas and minutes | [Agendas and minutes](https://www.walsenburg.org/city-clerks-office/page/agendas-and-minutes) | HTTP 403 |
| City of Walsenburg forms | [Forms and license applications](https://www.walsenburg.org/forms) | HTTP 403 |
| Yellow Pages Raton | [Raton business listings](https://www.yellowpages.com/raton-nm/business-listings/1) | HTTP 403 |

Normal-browser review confirmed that the Yellow Pages route loads its Raton business index. The other current entries were retained as automation-limited rather than marked broken; IFundWomen presents a Cloudflare challenge, and EDA required indexed-page confirmation when direct browser navigation failed. The retired OEDIT Arts in Society route is no longer in this list because the guide now uses RedLine's current application page.

## Keyword Review

The reviewed guardrail file is `data/keyword-inference-guardrails.json`. It blocks source-page terms without deleting editor-reviewed canonical keywords.

Rejected source inferences:

- Bobcat Pass Wilderness Adventures: `agriculture`
- Music from Angel Fire: `chamber of commerce`
- Mesalands CC Dinosaur Museum: `outdoor recreation`
- The Shuler Theater: `main street`
- DeWitt Enterprises: `artist`, `maker`, `writing`
- Huerfano County Heritage Center: `museum`, `newspaper`, `visitor center`
- Books & More Used Bookstore: `library`

Accepted examples from the same sweep include festival and workshop for Music from Angel Fire; education for Mesalands; retail for DeWitt Enterprises; nonprofit, education, and training for C Cubed Training; and advertising and newspaper for The World Journal.

## Maintenance Boundary

- Browser-confirmed replacements may update contact routes.
- Script-blocked pages stay in the registry and continue to receive periodic checks.
- Keyword guardrails apply before source-derived terms enter the review index.
- Public claims, legal status, eligibility, deadlines, and rates still require human review.
