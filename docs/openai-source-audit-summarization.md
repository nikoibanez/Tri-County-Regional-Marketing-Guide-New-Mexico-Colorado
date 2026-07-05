# OpenAI Source-Audit Summarization Plan

Decision: the first OpenAI-backed feature should summarize source-audit reports.

## Current Status

The secure OpenAI key setup widget could not complete target loading in the UI. The connector could see the `Personal` organization and `Default project`, but no new project-specific key was saved locally.

Until the key path is settled, keep this as a plan. Do not commit API keys or generated secrets.

## First AI Task

Input:

```text
review/update-audits/update-audit-latest.json
review/update-audits/update-audit-latest.md
```

Output:

```text
review/update-audits/source-audit-summary-latest.md
```

The summary should answer:

- What changed or failed?
- Which grant/funding sources need attention?
- Which items require human approval?
- Which items are likely bot-blocked or need normal browser review?
- What is the next smallest action?

## Safety Boundary

The AI may summarize, group, and draft proposed review notes. It should not directly publish changes to public pages, eligibility language, deadlines, rates, contact details, or civic/legal guidance.

## GitHub Setup Later

When ready, add `OPENAI_API_KEY` as a GitHub Actions repository secret. The first workflow should summarize the grants/funding audit artifact before any broader update automation is enabled.
