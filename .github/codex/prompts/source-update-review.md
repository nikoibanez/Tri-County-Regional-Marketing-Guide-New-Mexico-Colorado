# Tri-County Guide Source Update Review

You are reviewing the Tri-County Regional Marketing Guide source registry and generated site data. Start with source-audit summarization, especially grants, funding, scholarships, stipends, and related support resources.

Run:

```bash
python tools/build_netlify_deep_guide.py
python scripts/build_update_source_registry.py
python scripts/audit_update_sources.py --domain funding
```

Use these rules:

- Treat directory rows as leads unless a current public source verifies them.
- Do not infer ad availability, free placement, grant eligibility, event acceptance, submission deadlines, audience size, endorsement, or listing approval.
- Do not remove a local listing only because one automated URL check failed.
- If a funding source appears changed, summarize the issue first. Propose a small public update only when source evidence is clear and human approval is still expected.
- If a source is blocked, timed out, or ambiguous, mark it for manual verification.
- Keep public copy practical and direct.

Deliver:

1. A concise grants/funding source-audit summary.
2. A short list of sources needing human review.
3. Any proposed file changes, only if the evidence is clear and reviewable.
4. Manual verification tasks that should not be automated.
5. A clear note when no public-facing change should be made.
