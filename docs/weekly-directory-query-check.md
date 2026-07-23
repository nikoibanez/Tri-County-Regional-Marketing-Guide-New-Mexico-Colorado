# Weekly Directory Query Check

This repo includes a weekly directory watcher for fifteen high-signal public directory, tourism, events, food, venue, and chamber sources used by the Tri-County Regional Marketing Guide.

## What It Does

The watcher:

- fetches configured chamber, tourism, and local business-directory pages;
- extracts likely listing names and linked listing pages;
- compares those names against the current guide directory CSVs;
- writes a human-review report of possible new leads and already represented listings;
- writes an internal pending-candidates feed for review;
- opens a GitHub pull request instead of committing candidate changes directly to production.

It does not merge candidates into the official directory, remove listings, or publish new contact claims as confirmed facts. Those changes still require human review.

## Watch Sources

The configured sources live in:

```text
data/directory-watch-sources.json
```

Current weekly watchlist:

- Five Colfax County source groups, including Raton Chamber, Angel Fire Chamber, Angel Fire food/catering/event-service categories, Visit Angel Fire, and Explore Raton.
- Five Las Animas County source groups, including Visit Trinidad business/visitor pages, events, venue routes, Colexico/TLAC chamber routes, and Southern Colorado Tourism.
- Five Huerfano County source groups, including Spanish Peaks Country business, dining/lodging/venue, events, La Veta business directory, and Huerfano County Chamber.

## Run Locally

From the project root:

```powershell
python scripts/weekly_directory_query_check.py
```

Dry run without network access:

```powershell
python scripts/weekly_directory_query_check.py --no-network
```

Reports are written to:

```text
review/directory-watch/directory-watch-latest.md
review/directory-watch/directory-watch-latest.json
```

Internal pending-candidate feed:

```text
data/directory-auto-update-candidates.json
```

The generator does not publish this candidate feed on the public Network page. Candidates become public listings only after a person confirms the linked page and intentionally updates canonical directory data.

## GitHub Actions

The workflow lives at:

```text
.github/workflows/weekly-directory-query-check.yml
```

It runs weekly and can also be started manually from GitHub Actions with `workflow_dispatch`. When candidate output changes, the workflow pushes a dedicated automation branch and opens a review pull request. If repository settings prevent Actions from opening pull requests, it opens a GitHub issue naming the ready review branch.

Netlify may create a deploy preview for the review branch, but production does not change until a person reviews and merges the pull request.

## Human Review Rule

Treat possible new leads as a review queue. Open the source link, confirm the listing is current and relevant, then update `data/tri_county_persona_resources.csv` or the canonical data pipeline by hand before promoting a candidate into the official directory.
