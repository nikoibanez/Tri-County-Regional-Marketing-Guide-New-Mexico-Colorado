# Command Checklist

Use this from the project folder:

```powershell
cd "C:\Users\Alyxx and Niko\Documents\Northern New Mexico & Southern Colorado Tri-County Regional Marketing Guide For Businesses, Non-Profits, Entrepreneurs, and Artists"
```

## Local Build

```powershell
python tools/build_netlify_deep_guide.py
```

Output:

```text
dist/tri-county-netlify-guide-deep
dist/Tri_County_Regional_Marketing_Guide_Netlify_Deep.zip
```

## Local QA

```powershell
python -m py_compile tools/build_netlify_deep_guide.py scripts/audit_update_sources.py scripts/weekly_directory_query_check.py scripts/sweep_listing_keywords.py scripts/audit_ui_accessibility.py scripts/audit_seo_static.py scripts/audit_directory_quality.py scripts/audit_internal_links.py scripts/build_maintenance_dashboard.py scripts/smoke_test_site.py
python -m unittest discover -s tests -p "test_*.py"
node --check dist/tri-county-netlify-guide-deep/assets/app.js
python scripts/audit_ui_accessibility.py
python scripts/audit_seo_static.py
python scripts/audit_directory_quality.py --fail-on-blocking
python scripts/audit_internal_links.py --fail-on-broken
python scripts/smoke_test_site.py
python scripts/build_maintenance_dashboard.py
```

## Grants Monitor

Build the registry, then audit only grants/funding sources:

```powershell
python scripts/build_update_source_registry.py
python scripts/audit_update_sources.py --domain funding
```

For a dry run without live URL checks:

```powershell
python scripts/audit_update_sources.py --domain funding --no-network
```

Reports:

```text
review/update-audits/update-audit-latest.md
review/update-audits/update-audit-latest.json
```

## Full Source Registry Monitor

Check every registered directory, funding, event, civic, media, and creative source and persist its last-check state:

```powershell
python scripts/build_update_source_registry.py
python scripts/audit_update_sources.py
python scripts/build_maintenance_dashboard.py
```

Use `--no-update-registry` when testing URL checks without advancing source-maintenance dates.

## Weekly Directory Query Check

Check the fifteen high-signal directory, tourism, events, food, venue, and chamber sources and write a review queue:

```powershell
python scripts/weekly_directory_query_check.py
```

For a dry run without live URL checks:

```powershell
python scripts/weekly_directory_query_check.py --no-network
```

Reports:

```text
review/directory-watch/directory-watch-latest.md
review/directory-watch/directory-watch-latest.json
data/directory-auto-update-candidates.json
```

## Weekly Listing Keyword Sweep

Seed or validate every listing from canonical fields without using the network:

```powershell
python scripts/sweep_listing_keywords.py --no-network --write-index
```

Refresh the oldest 120 public source pages and write a reviewable index:

```powershell
python scripts/sweep_listing_keywords.py --limit 120 --write-index
python tools/build_netlify_deep_guide.py
```

Reports:

```text
review/keyword-sweep/keyword-sweep-latest.md
review/keyword-sweep/keyword-sweep-latest.json
data/listing-keyword-index.json
```

## GitHub Push

Only after reviewing changes:

```powershell
git status
git add .
git commit -m "Update tri-county guide build and monitoring"
git push
```

## Netlify

Netlify should deploy from GitHub with:

```text
Build command: python tools/build_netlify_deep_guide.py
Publish directory: dist/tri-county-netlify-guide-deep
```

Set the same final public origin in Netlify and GitHub:

```text
PUBLIC_SITE_ORIGIN=https://statelineguide.org
```

To test a live deployment locally without changing files:

```powershell
$env:PUBLIC_SITE_ORIGIN="https://your-live-site.example"
python scripts/smoke_test_site.py
Remove-Item Env:PUBLIC_SITE_ORIGIN
```

## Human Approval Gate

Do not publish public claims about grant eligibility, deadlines, rates, contact changes, listing removal, civic/legal guidance, or ad availability until a person has reviewed the source.
