# No-Secret Maintenance Automation

The maintenance system uses Python, GitHub Actions, the built site, and repository data. It does not require an OpenAI key, a paid crawler, or a new runtime dependency.

## What Runs Automatically

| Workflow | Trigger | Work | Public effect |
| --- | --- | --- | --- |
| Build and quality gate | Pull requests and pushes to `master` | Builds the site; checks Python, JavaScript, accessibility markers, SEO, directory quality, local links, anchors, and critical routes | Blocks a broken change; does not edit directory data |
| Weekly directory query check | Monday at 15:00 UTC | Checks 15 high-signal source groups and compares candidates with canonical data | Opens a review pull request or fallback issue |
| Source registry audit | Tuesday at 15:23 UTC | Checks all registered directory, funding, events, civic, media, and creative URLs; records source-check history | Opens a review pull request or fallback issue |
| Live site smoke test | Daily at 16:17 UTC | Loads critical public pages, data, sitemap, and robots routes | Opens or updates one GitHub issue on failure |
| Monthly maintenance snapshot | First day of each month at 16:00 UTC | Builds the canonical deploy zip and stores data, reports, and a SHA-256 checksum | Creates a private GitHub Actions artifact retained for 90 days |

GitHub schedules use UTC and therefore shift by one local clock hour when Mountain Time enters or leaves daylight saving time.

## Autonomous Scope

The system may autonomously:

- build and test generated files;
- compare public source pages with current data;
- record check dates and HTTP status;
- produce maintenance reports and candidate queues;
- open review pull requests and failure issues;
- create deployment snapshots and checksums;
- test the configured live site.

The system must wait for human approval before changing:

- directory inclusion or removal;
- public contact details;
- grant eligibility, deadlines, rates, or application claims;
- advertising availability or placement guarantees;
- civic, legal, permit, licensing, or public-notice guidance;
- descriptions that assert facts not supported by a current public page.

## One-Time GitHub Settings

In the repository, open **Settings > Actions > General** and confirm:

1. Actions are allowed to run.
2. Workflow permissions allow read and write access.
3. GitHub Actions may create pull requests when that option is available.

If pull-request creation is disabled, the workflows still push a dedicated review branch and open an issue naming it.

Add this non-secret repository variable under **Settings > Secrets and variables > Actions > Variables**:

```text
PUBLIC_SITE_ORIGIN
```

Its value should be the one production URL or custom domain that users and search engines should treat as canonical.

## One-Time Netlify Setting

Connect Netlify to the `master` branch of this repository. The checked-in `netlify.toml` runs:

```text
python tools/build_netlify_deep_guide.py
```

and publishes:

```text
dist/tri-county-netlify-guide-deep
```

Set the same `PUBLIC_SITE_ORIGIN` value in Netlify. A pull request can receive a deploy preview, but production changes only after merge to `master`.

## Reports

The latest internal overview is:

```text
review/maintenance/maintenance-dashboard-latest.md
```

Supporting reports live under:

```text
review/maintenance/
review/directory-watch/
review/update-audits/
```

These files are maintenance evidence, not public-facing directory copy.
