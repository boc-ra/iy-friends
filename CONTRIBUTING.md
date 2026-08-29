# Contributing

## Branches

- `main` is the protected production source branch.
- Create a short-lived branch for changes and open a Pull Request into `main`.
- Do not place credentials or production data in issues, commits, workflow logs, or artifacts.

## Before committing

```powershell
.\scripts\enable-git-hooks.ps1
node tools/repo-policy.mjs --staged
```

The pre-commit hook intentionally performs fast repository-policy checks. Full builds, tests, SAM lint, dependency audits, and SBOM generation run in CI.

Dependency audit findings at `high` or `critical` severity block CI. Update direct dependencies and lock files deliberately; do not use an unreviewed forced audit fix.

## Production changes

Production deployment uses a manually triggered workflow, the GitHub `production` Environment, and AWS OIDC. Review the selected target and commit SHA before approval. The admin web is not a deployment target.

Keep the workflow in verification-only mode unless an application deployment has separate production authorization.
