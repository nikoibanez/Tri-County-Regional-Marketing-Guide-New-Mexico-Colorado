# Appendix Page Review

Date: 2026-06-26

Reviewed page:

```text
dist/tri-county-netlify-guide-deep/appendix/index.html
```

## What The Page Is For

The Appendix should be the full contact/resource table for people who need the underlying list after the more guided pages have narrowed the job. It should not be the first place a new user starts unless they already know they need a table.

## What Works

- The page makes the full inventory available without hiding it behind the directory assistant.
- County/community grouping supports users who already know the local place they care about.
- Download buttons are useful for staff, reviewers, and partner organizations.
- The submission panel gives users a correction path instead of leaving outdated details as a dead end.

## What Hurts Usability

- The table is large enough that it can feel like the old one-long-HTML problem returning inside one page.
- The Appendix relies on the user tolerating horizontal table scanning, especially on mobile.
- It is not the best page for discovery; the Network page and directory assistant are better for that.
- Some category names came from working source language, so the generator should keep translating those into public-friendly terms.

## Recommended Framing

Use the Appendix as:

> The full table behind the guide. Use it when you need contact details, county/community grouping, or a spreadsheet-style view. For guided discovery, start with Network or Ask directory.

## Next Smallest Action

Keep the current page, but add a short top-of-page choice:

- "Search by need" -> Network
- "Ask the directory" -> assistant
- "Use full table" -> stay on Appendix
- "Submit a correction" -> Submit

This avoids redesigning the appendix while helping users avoid the table if they do not need it.

Status: implemented in `tools/build_netlify_deep_guide.py` and regenerated in `dist/tri-county-netlify-guide-deep/appendix/index.html`.

## Do Not Do Yet

- Do not add a second full search/filter UI to the Appendix until real users ask for it. Network already handles guided search.
- Do not split the Appendix into county pages yet. The county pages already summarize first stops, and the Appendix is useful precisely because it is one source table.
- Do not add more status/confidence labels to the table. Keep correction and source-check language calm and user-facing.
