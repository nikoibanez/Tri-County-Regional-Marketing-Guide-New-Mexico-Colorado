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
python -m py_compile tools/build_netlify_deep_guide.py scripts/audit_update_sources.py scripts/audit_ui_accessibility.py scripts/audit_seo_static.py
node --check dist/tri-county-netlify-guide-deep/assets/app.js
python scripts/audit_ui_accessibility.py
python scripts/audit_seo_static.py
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

## Human Approval Gate

Do not publish public claims about grant eligibility, deadlines, rates, contact changes, listing removal, civic/legal guidance, or ad availability until a person has reviewed the source.
