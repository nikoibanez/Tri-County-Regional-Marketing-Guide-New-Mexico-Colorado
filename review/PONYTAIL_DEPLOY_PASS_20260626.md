# Ponytail Deploy Pass - 2026-06-26

## Scope

Applied the uploaded Ponytail principles to the current Netlify deploy generator without adding Ponytail as a public site dependency.

## Changes Made

- Removed unused chart-generation code from `tools/build_netlify_deep_guide.py`.
- Removed retired SVG infographic helper functions that were no longer called by any public page.
- Restored the one live helper that belonged in the kept site surface: `persona_route_controls`.
- Removed stale chart/infographic CSS selectors and old `hero--routing` animation selectors.
- Updated generated README/QA wording so the deploy describes the current animated-landscape site instead of old chart assets.
- Rebuilt `dist/tri-county-netlify-guide-deep`.
- Rebuilt `dist/Tri_County_Regional_Marketing_Guide_Netlify_Deep.zip`.

## Verification

- `python -m py_compile tools\build_netlify_deep_guide.py scripts\audit_update_sources.py scripts\audit_ui_accessibility.py scripts\audit_seo_static.py`
- `python tools\build_netlify_deep_guide.py`
- `python scripts\build_update_source_registry.py`
- `python scripts\audit_update_sources.py --domain funding --no-network`
- `node --check dist\tri-county-netlify-guide-deep\assets\app.js`
- `python scripts\audit_ui_accessibility.py`
- `python scripts\audit_seo_static.py`
- Confirmed `dist\tri-county-netlify-guide-deep\assets\charts` is absent.
- Confirmed removed chart/infographic helper names and stale CSS selectors no longer appear in the generator or deploy.
- Confirmed public data still excludes confidence-label and internal verification fields.

## Deploy Package

Latest zip:

`dist\Tri_County_Regional_Marketing_Guide_Netlify_Deep.zip`

Size after this pass: 1,895,784 bytes.

