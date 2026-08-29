# IY Friends

IY Friendsの公開サイト、試作管理画面、サーバーレスAPI、AWS共有インフラをまとめたmonorepoです。

## Projects

| Path | Purpose | Production deployment |
|---|---|---|
| `iyf-public-web` | 公開React SPA | Yes |
| `iyf-admin-web` | 試作管理SPA | No; CI validation only |
| `iyf-backend-api` | Python Lambda/API/DynamoDB | Yes |
| `iyf-infra` | S3/CloudFront/Cognito/monitoring | Yes |

## Local prerequisites

- Git
- Node.js and npm
- Python 3.13
- Docker
- AWS CLI
- AWS SAM CLI
- GitHub CLI

## Repository checks

```powershell
node --test tools/repo-policy.test.mjs .codex/hooks/tool-policy.test.mjs scripts/deployment-target.test.mjs
node tools/repo-policy.mjs --tracked
node scripts/validate-delivery.mjs
```

Enable the repository Git hook after cloning:

```powershell
.\scripts\enable-git-hooks.ps1
```

Component setup and build commands remain documented in each project README. Production deployment is manual through the approved GitHub Actions workflow; the admin web is intentionally excluded.

## CI/CD

- `.github/workflows/ci.yml` validates repository policy, both frontends, backend tests including Hypothesis, all SAM templates, dependency audits, and SBOM generation.
- `.github/workflows/deploy-production.yml` is manual and uses the GitHub `production` Environment plus AWS OIDC.
- The deployment workflow defaults to OIDC verification only. Application deployment requires selecting a target and explicitly setting `deploy` to true.
- Valid production targets are `infra`, `backend`, `public-web`, and `all`. The admin web has no deployment path.

See `iyf-infra/README.md` for the one-time GitHub OIDC bootstrap and Environment variables.
