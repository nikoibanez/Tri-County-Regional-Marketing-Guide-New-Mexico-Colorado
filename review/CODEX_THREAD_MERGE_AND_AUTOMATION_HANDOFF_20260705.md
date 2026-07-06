# Codex Thread Merge + Site Automation Handoff

Date: 2026-07-05

## Current Shared Objective

Make the Tri-County Regional Marketing Guide easier to keep current by using GitHub, Netlify, local source-audit scripts, and optional OpenAI summarization in a review-first workflow.

The public site should not auto-publish changed civic, directory, grant, event, rate, eligibility, or contact claims without human review.

## Best Automation Order

1. Stabilize GitHub as the shared source of truth.
2. Connect Netlify to deploy from GitHub.
3. Run source-audit scripts locally in report-only mode.
4. Add OpenAI summarization only after the source audit produces reviewable diffs.
5. Add scheduled monitoring for grants, calendars, directories, and event-posting routes.
6. Publish only after a human approves the changed rows/copy.

## Why This Order Matters

GitHub and Netlify come first because they solve the transfer problem between desktop and laptop. Once both machines can pull the same repo, Codex threads do not need to be literally merged to share work. The repo becomes the merge point.

Source-audit automation comes next because it can watch pages, compare against the current registry, and write reports without making public claims.

OpenAI summarization comes after that because AI is best used to summarize “what changed and what needs review,” not to silently update public listings.

## Current Desktop State

Recent implemented work:

- Added an event-posting hub at `dist/site/resources/event-posting/index.html`.
- Expanded event-posting routes to all three counties.
- Event channel CSV is now `data/event_posting_channels_combined_20260705.csv`.
- Current event-channel count: 80.
- Duplicate event-channel names: 0.
- County coverage:
  - Colfax: 16.
  - Las Animas: 18.
  - Huerfano: 22.
  - Regional/spillover: 24.
- Latest deploy package:
  `dist/NETLIFY_DEPLOY_Tri_County_Regional_Marketing_Guide_2026-07-05_Event_Posting_All_Counties.zip`

## How To Combine A Laptop Codex Thread With This One

There is no safe one-click “merge two Codex conversations” step available from this desktop thread unless the other thread is visible to this host/account.

Use this practical merge method:

1. On the laptop Codex thread, ask:

   ```text
   Summarize this thread for another Codex session. Include: objective, files changed, scripts run, decisions made, unresolved questions, exact paths, and any warnings about user preferences.
   ```

2. Paste the laptop summary into this file under “Laptop Thread Summary.”

3. If the laptop changed files, push or copy those files into the same GitHub repo/branch, or place them in a dated transfer folder.

4. In this desktop thread, ask Codex:

   ```text
   Read review/CODEX_THREAD_MERGE_AND_AUTOMATION_HANDOFF_20260705.md and reconcile the laptop thread summary with the current repo. Do not overwrite newer files without checking timestamps and git diff.
   ```

5. Resolve conflicts through git diffs, not by memory.

## Laptop Thread Summary

Paste the laptop Codex summary here.

## Next Smallest Automation Task

Set up GitHub push from this workspace so Netlify can deploy from the repo instead of manual zip uploads.

After that, run the existing source-audit flow in report-only mode:

```powershell
python tools/build_netlify_deep_guide.py
python scripts/build_update_source_registry.py
python scripts/audit_update_sources.py --limit 120
```

## Human Review Boundary

Automation may:

- Watch source pages.
- Compare source changes.
- Draft a report.
- Suggest changed rows or copy.
- Open a reviewable branch or pull request.

Automation should not silently publish:

- Grant eligibility.
- Rates.
- Deadlines.
- Official contact details.
- Legal/civic guidance.
- Event acceptance or advertising availability.
- Directory inclusion/removal.

