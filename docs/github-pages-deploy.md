# GitHub Pages Deploy

This repository can publish the guide directly from GitHub Pages instead of consuming Netlify production deploy credits.

## Publishing model

- Source branch: `master`
- Deployment method: GitHub Actions
- Published artifact: `dist/site`
- Workflow file: `.github/workflows/deploy-github-pages.yml`

## What to enable in GitHub

1. Open repository `Settings`.
2. Open `Pages`.
3. Under `Build and deployment`, choose `GitHub Actions`.
4. Push to `master` or run the `Deploy GitHub Pages` workflow manually once.

After that, each push to `master` republishes the static site automatically.

## Notes

- This workflow does not rebuild the guide. It publishes the checked-in static output already stored in `dist/site`.
- If the site should eventually use a custom domain, add that in GitHub Pages settings and then update canonical URLs and sitemap origin if needed.
