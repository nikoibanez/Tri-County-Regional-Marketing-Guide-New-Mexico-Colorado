# Directory Metadata Implementation - 2026-06-26

## What Changed

- Added full machine-readable directory metadata for every public directory shortcut and local inventory row.
- Generated `dist/tri-county-netlify-guide-deep/data/directory-metadata.json`.
- Added a Network page JSON-LD `mainEntity` using `ItemList` with every metadata entry.
- Added a Network page JSON alternate link to `../data/directory-metadata.json`.
- Added `directory_metadata` counts and href into `data/guide-data.json`.
- Expanded the SEO static audit so it verifies the Network page JSON-LD count matches `directory-metadata.json`.

## Counts

- Directory shortcuts: 89.
- Local inventory rows: 456.
- Total metadata entries: 545.

## Publication Boundary

The metadata intentionally uses `Thing`, `ItemList`, and `PropertyValue` rather than `LocalBusiness` records. This keeps the entries useful to search and automation tools without falsely presenting every row as a verified active business, approved listing, or endorsed organization.

## Verification

- `python -m py_compile tools\build_netlify_deep_guide.py scripts\audit_seo_static.py scripts\audit_update_sources.py scripts\audit_ui_accessibility.py`
- `python tools\build_netlify_deep_guide.py`
- `python scripts\build_update_source_registry.py`
- `python scripts\audit_update_sources.py --domain funding --no-network`
- `node --check dist\tri-county-netlify-guide-deep\assets\app.js`
- `python scripts\audit_ui_accessibility.py`
- `python scripts\audit_seo_static.py`

