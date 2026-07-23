# GitHub Pages Deploy

This repository can publish the guide through GitHub Pages as an optional fallback. Netlify remains the production deployment target.

## Publishing model

- Source branch: `master`
- Deployment method: GitHub Actions
- Published artifact: `dist/tri-county-netlify-guide-deep`
- Workflow file: `.github/workflows/deploy-github-pages.yml`

## What to enable in GitHub

1. Open repository `Settings`.
2. Open `Pages`.
3. Under `Build and deployment`, choose `GitHub Actions`.
4. Open `Actions`, choose `Deploy GitHub Pages`, and run the workflow manually.

The fallback runs only when manually requested. Normal pushes are validated by the quality workflow and deployed through the connected Netlify site.

## Notes

- This workflow rebuilds the guide from the canonical generator before publishing `dist/tri-county-netlify-guide-deep`.
- If the site should eventually use a custom domain, add that in GitHub Pages settings and then update canonical URLs and sitemap origin if needed.
