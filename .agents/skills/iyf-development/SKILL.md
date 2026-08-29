---
name: iyf-development
description: Develop, test, review, or deploy the IY Friends monorepo using its project-specific component boundaries, validation commands, public-repository policy, and AWS deployment order. Use for changes inside this repository; do not use for unrelated React, Python, or AWS projects.
---

# IY Friends Development

Treat the workspace root as one monorepo containing four projects:

- `iyf-public-web`: production public SPA.
- `iyf-admin-web`: prototype admin SPA; CI validation only, never production deployment.
- `iyf-backend-api`: Python 3.13 Lambda/API/DynamoDB SAM application.
- `iyf-infra`: shared S3, CloudFront, Cognito, and monitoring SAM application.

## Work safely

- Preserve unrelated and user-owned changes.
- Never read, edit, stage, or publish real `.env` files, local settings, credentials, generated output, or `aidlc-docs/audit.md`.
- Before committing or publishing, run `node tools/repo-policy.mjs --staged` or `--tracked` as appropriate.
- Keep the admin web in CI but out of every production deployment path.
- Require explicit authorization immediately before any production AWS mutation; plan approval alone is not deployment authorization.

## Validate proportionally

- Root policy and Hook changes: `node --test tools/repo-policy.test.mjs .codex/hooks/tool-policy.test.mjs`.
- Frontend changes: run typecheck and build in the affected frontend.
- Backend changes: run pytest, including existing Hypothesis properties.
- SAM changes: run `sam validate --lint` for every affected template.
- Cross-component or delivery changes: run the complete root validation documented in `AGENTS.md`.

## AWS work

For infrastructure, deployment, production verification, or rollback work, read [references/aws-deployment.md](references/aws-deployment.md) before acting. Do not load that reference for ordinary local code changes.

## Completion evidence

Report the files changed, checks actually run, any checks not run, and whether any external state changed. Never describe a workflow as deployable until its permissions and target exclusions have been verified.
