# IY Friends Repository Guide

## Scope

This is a single monorepo with four deployable projects:

- `iyf-public-web`: public React/Vite SPA; the only frontend deployed to production.
- `iyf-admin-web`: prototype admin SPA; validate it in CI but do not deploy it.
- `iyf-backend-api`: Python 3.13 AWS SAM API, Lambda functions, and DynamoDB tables.
- `iyf-infra`: shared S3, CloudFront, Cognito, and monitoring infrastructure.

## Safe workflow

- Never commit `.env`, credentials, local settings, generated builds, SAM outputs, or `aidlc-docs/audit.md`.
- Run `node tools/repo-policy.mjs --tracked` before publishing changes.
- Use `npm ci`, not `npm install`, in reproducible validation and CI.
- Validate both SAM templates with `sam validate --lint`.
- Treat production AWS mutations as separately authorized actions. A code change or plan approval does not by itself authorize a deployment.
- Preserve the production order when multiple components are deployed: shared infra, backend, public web.
- Never include `iyf-admin-web` in a production deployment workflow.

## Verification commands

```text
node --test tools/repo-policy.test.mjs .codex/hooks/tool-policy.test.mjs
node tools/repo-policy.mjs --tracked
npm --prefix iyf-public-web run typecheck
npm --prefix iyf-public-web run build
npm --prefix iyf-admin-web run typecheck
npm --prefix iyf-admin-web run build
python -m pytest iyf-backend-api/tests
sam validate --lint --template-file iyf-backend-api/template.yaml
sam validate --lint --template-file iyf-infra/template.yaml
```

Repository-specific Codex guidance is available in the `iyf-development` skill. Read its AWS reference only for infrastructure or deployment work.
