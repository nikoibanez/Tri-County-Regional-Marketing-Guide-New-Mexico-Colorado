# Remaining Permission Setup

This page keeps the setup gentle. Do one section at a time.

## Current Status

- GitHub repository URL supplied: `https://github.com/nikoibanez/Tri-County-Regional-Marketing-Guide-New-Mexico-Colorado.git`
- Local `origin` remote configured.
- Local automation scaffold implemented.
- Netlify deployment direction confirmed: deploy from GitHub.
- First monitor group confirmed: grants/funding sources.
- First OpenAI-backed feature confirmed: source-audit summarization.
- No real secrets are stored in the repo.

## Step 1: GitHub Login On This Computer

Open PowerShell and run:

```powershell
gh auth status
```

If it says you are not logged in, run:

```powershell
gh auth login
```

Choose:

```text
GitHub.com
HTTPS
Login with a web browser
```

Stop after GitHub says authentication succeeded.

## Step 2: Push The Local Repo

Once GitHub login works, run this from the project folder:

```powershell
git add .
git commit -m "Add tri-county guide automation scaffold"
git branch -M main
git push -u origin main
```

If Git asks about identity, set:

```powershell
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

## Step 3: Connect Netlify

In Netlify:

1. Go to **Add new site**.
2. Choose **Import an existing project**.
3. Choose GitHub.
4. Pick `Tri-County-Regional-Marketing-Guide-New-Mexico-Colorado`.
5. Use these build settings:

```text
Build command: python tools/build_netlify_deep_guide.py
Publish directory: dist/tri-county-netlify-guide-deep
```

6. Deploy.

Use GitHub deploys as the normal path. The generated zip is still useful for backup handoff, but not the main deployment workflow.

## Step 4: Turn On Netlify Forms

The `/submit/` page already contains a Netlify-ready form. After Netlify deploys:

1. Open the deployed `/submit/` page.
2. Submit one test listing.
3. In Netlify, open **Forms**.
4. Confirm the `listing-submission` form appears.
5. Replace placeholder contact info in the site when the final intake inbox is chosen.

## Step 5: Add OpenAI API Key To GitHub

Do not paste the key into chat or commit it to files.

In GitHub:

1. Open the repository.
2. Go to **Settings**.
3. Go to **Secrets and variables**.
4. Choose **Actions**.
5. Add a new repository secret:

```text
Name: OPENAI_API_KEY
Value: your OpenAI API key
```

Use a project-specific key when possible because the repository may be shared. Do not commit `.env.local`.

## Step 6: Enable The Codex Proposal Workflow

The Codex workflow is disabled until you explicitly turn it on.

In GitHub:

1. Open **Settings**.
2. Go to **Secrets and variables**.
3. Choose **Actions**.
4. Open **Variables**.
5. Add:

```text
Name: ENABLE_CODEX_UPDATES
Value: true
```

Then open **Actions** and manually run:

```text
Codex update proposal
```

Start with source-audit summarization, especially grants/funding audit reports, before enabling broader update proposals.

## Step 7: Optional Review Queue

You can wait on this.

The simplest review queue is GitHub pull requests and Netlify Deploy Previews. Add Google Sheets or Airtable only if the director wants a less technical review surface.
