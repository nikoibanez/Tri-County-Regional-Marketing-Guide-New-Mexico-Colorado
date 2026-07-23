# Netlify From GitHub

Decision: Netlify should deploy from GitHub, not from repeated manual zip uploads.

## Why

- GitHub keeps history, branches, review, and rollback.
- Netlify Deploy Previews make page review easier before publication.
- Source-audit reports and future Codex proposals can become pull requests instead of loose files.

## Netlify Settings

Use the repository:

```text
https://github.com/nikoibanez/Tri-County-Regional-Marketing-Guide-New-Mexico-Colorado.git
```

Build settings:

```text
Build command: python tools/build_netlify_deep_guide.py
Publish directory: dist/tri-county-netlify-guide-deep
Python version: 3.11
```

The repo already includes `netlify.toml` with those settings.

## First Deploy Check

After connecting the repo:

1. Confirm the home page loads.
2. Open `/network/` and search for `grant`, `artist`, `Raton`, `Trinidad`, and `Walsenburg`.
3. Open `/appendix/` and confirm the table scrolls on smaller screens.
4. Open `/submit/`, send one test submission, and confirm Netlify Forms sees `listing-submission`.
5. Confirm `/sitemap.xml` and `/robots.txt` load.

## Later

Set `PUBLIC_SITE_ORIGIN` to the final public origin in both Netlify environment variables and GitHub repository variables. Example:

```text
https://statelineguide.org
```

The generator uses that value for canonical links, structured data, social metadata, `robots.txt`, and the sitemap. It defaults to `https://statelineguide.org` when the variable is absent. After the final domain is connected, rebuild and submit the sitemap in Google Search Console.
