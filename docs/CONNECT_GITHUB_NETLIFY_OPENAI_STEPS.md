# Connect GitHub, Netlify, OpenAI, and Source Audits

This is the least-overwhelming order.

## Current local status

This project folder is already a Git repository.

GitHub remote already exists:

`https://github.com/nikoibanez/Tri-County-Regional-Marketing-Guide-New-Mexico-Colorado.git`

Current local branch:

`master`

## Step 1 - Push the site to GitHub

Open PowerShell in this folder:

`C:\Users\Alyxx and Niko\Documents\Northern New Mexico & Southern Colorado Tri-County Regional Marketing Guide For Businesses, Non-Profits, Entrepreneurs, and Artists`

Run:

```powershell
git status
git add .
git commit -m "Publish current tri-county guide site"
git push -u origin master
```

If Git asks you to sign in, use the browser/device-code prompt it provides.

If Git says there is nothing to commit, that is okay. Run:

```powershell
git push -u origin master
```

## Step 2 - Connect Netlify to GitHub

In Netlify:

1. Go to the Netlify dashboard.
2. Choose `Add new project`.
3. Choose `Import an existing project`.
4. Choose `GitHub`.
5. Authorize Netlify if it asks.
6. Pick this repo:

`nikoibanez/Tri-County-Regional-Marketing-Guide-New-Mexico-Colorado`

Use these build settings:

```text
Branch to deploy: master
Base directory: leave blank
Build command: echo 'Publishing prebuilt Stateline Guide from dist/site'
Publish directory: dist/site
```

The repo also has these settings in `netlify.toml`, so Netlify should auto-fill them after you connect the GitHub repo.

This uses the prebuilt site in `dist/site`. That is the simplest reliable path right now.

## Step 2 fallback - easiest Netlify setup

If Netlify build setup feels like too much, use manual deploy for now:

`C:\Users\Alyxx and Niko\Downloads\NETLIFY_DEPLOY_Tri_County_Regional_Marketing_Guide_2026-07-01_Mobile_Concise_Directory.zip`

The current `dist/site` folder is already copied from the latest mobile concise deploy.

Later, when the workflow feels easier, we can switch Netlify back to running the generator automatically.

## Step 3 - Add OpenAI only for automation

Do this after GitHub and Netlify work.

Never commit an API key.

Set a local environment variable:

```powershell
setx OPENAI_API_KEY "paste-key-here"
```

Then close and reopen PowerShell.

Check only that it exists, not the value:

```powershell
if ($env:OPENAI_API_KEY) { "OPENAI_API_KEY is set" } else { "OPENAI_API_KEY is missing" }
```

## Step 4 - Source audit automation later

Once GitHub, Netlify, and OpenAI are connected:

1. Run source-audit scripts locally.
2. Generate a review report.
3. Let a human approve changes.
4. Commit approved updates.
5. Push to GitHub.
6. Netlify deploys from GitHub.

Safe automation boundary:

The automation should watch sources, compare them, write reports, and draft changes. It should not silently publish new public claims, rates, deadlines, eligibility language, contact details, or civic/legal guidance without human review.
