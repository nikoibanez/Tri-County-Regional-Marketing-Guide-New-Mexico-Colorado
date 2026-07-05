# QA Report

Generated: 2026-06-27

## Passed

- 23 HTML files present, including generated public pages and animation previews.
- 0 missing local href/src references in generated HTML.
- 100 researched directory shortcuts embedded.
- 17 amplifier channel rows embedded.
- 4 posting/public-notice pathway rows embedded.
- 632 local inventory rows embedded and copied to `/data`.
- Full directory metadata generated at `/data/directory-metadata.json` and embedded in Network page JSON-LD.
- Public pages use the animated landscape assets and HTML/CSS layout; no separate generated chart assets are required.
- Zip package generated for Netlify upload.

## Known Caveats

- Any automated external-link check can produce false failures for government/tourism sites that block scripted requests.
- Paid/free status, advertising availability, approval rules, print deadlines, and audience size remain direct-contact follow-up tasks unless explicitly stated in a source.
- Fresh scripted link verification is exported separately after build as `data/live_link_verification_20260622.json` and `data/LIVE_LINK_VERIFICATION_20260622.md` when the verification script is run.
- The stale Raton/Colfax directory paths from the added PDF sources were replaced with working official parent/category pages in the public shortcut layer.

## Manual Publication Check

Before public launch, open the deployed Netlify preview and check:

- Home hero yucca/mountain animation, reduced-motion behavior, and mobile title wrapping.
- Network search for `chamber`, `artist`, `media`, `grant`, `Raton`, `Trinidad`, and `Walsenburg`.
- Network filters for resource type and access mode.
- Amplifier page rows for source URL and practical channel use.
- Posting page language: no board, calendar, newsletter, or newspaper should be framed as guaranteed ad placement.
- County page nav paths.
- Footer logo scale.
- All high-priority external links.
- `data/LIVE_LINK_VERIFICATION_20260622.md` for bot-blocked, timed-out, or manually-confirmed URLs.
