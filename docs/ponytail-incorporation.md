# Ponytail Incorporation Note

Date: 2026-06-26

Reviewed local uploads:

- `C:\Users\Alyxx and Niko\Downloads\ponytail-main.zip`
- `C:\Users\Alyxx and Niko\Downloads\plugin.json`
- `C:\Users\Alyxx and Niko\Downloads\plugin (1).json`
- `C:\Users\Alyxx and Niko\Downloads\plugin (2).json`

## Decision

Do not vendor Ponytail into the public website. The guide is a static Netlify site, not an agent plugin package. The useful incorporation is as a repo working rule: prefer the smallest correct change, reuse the existing generator/scripts, avoid new dependencies, and keep accessibility and human-review boundaries intact.

## Applied To This Repo

- Added the Ponytail review rule to `AGENTS.md`.
- Used the existing `update_domain` field instead of creating a separate grants-monitor system.
- Added one `--domain funding` flag to the existing audit script.
- Updated the existing GitHub workflow to monitor grants/funding sources first.
- Kept OpenAI source-audit summarization as a setup plan until the secure API-key flow is complete.

## Future Use

Before adding a new tool, ask:

1. Can the existing generator handle it?
2. Can an existing script take one flag?
3. Can Netlify, GitHub Actions, HTML, CSS, or the browser do it natively?
4. Does this change need a public-site edit, or only a review/report file?

If the answer is "one flag or one document," do that first.
