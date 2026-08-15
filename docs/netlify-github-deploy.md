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
Build command: python tools/build_netlify_deep_guide.py && python tools/inject_deluxe_legacy_context.py
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

Set `PUBLIC_SITE_ORIGIN` to the public origin in both Netlify environment variables and GitHub repository variables:

```text
https://deluxe-horse-207efc.netlify.app
```

The generator uses that value for canonical links, structured data, social metadata, `robots.txt`, and the sitemap. It defaults to `https://deluxe-horse-207efc.netlify.app`, the current production domain. Keep the same value in Netlify and GitHub. When a custom domain is ready, update the value, make that domain primary in Netlify, rebuild, and submit the replacement sitemap in Google Search Console.
