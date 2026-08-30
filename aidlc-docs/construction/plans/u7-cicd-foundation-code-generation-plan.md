# U7 CI/CD Foundation Code Generation Plan

The approved development-environment execution plan and U7 start approval are the source approvals for this unit.

- [x] Step 1: Record the U7 infrastructure and security constraints.
- [x] Step 2: Install and verify Python 3.13 and GitHub CLI.
- [x] Step 3: Resolve immutable commit SHAs for third-party GitHub Actions.
- [x] Step 4: Add root CI for repository policy, both frontends, backend tests, SAM lint, dependency audits, and SBOM artifacts.
- [x] Step 5: Add the manual production deployment workflow with an explicit target allowlist, production Environment, OIDC, concurrency, ordered dependencies, and no admin deployment path.
- [x] Step 6: Add the AWS OIDC bootstrap template with exact repository/environment trust and least-privilege deployment roles.
- [x] Step 7: Add deterministic deployment helper scripts and tests.
- [x] Step 8: Remove the ineffective nested backend workflow after root CI coverage exists.
- [x] Step 9: Run local builds, tests, lint, dependency scans, workflow validation, and public-repository policy checks.
- [x] Step 10: Create the public GitHub repository, configure the production Environment, commit, and push.
- [x] Step 11: Create the AWS OIDC bootstrap stack with fresh production authorization.
- [x] Step 12: Verify the first GitHub CI run and OIDC role assumption without deploying application resources.

## Boundaries

- `iyf-admin-web` is validated by CI and is not a production deployment target.
- No application stack or public web artifact is deployed during foundation verification.
- GitHub Actions use short-lived AWS credentials through OIDC; no long-lived AWS secret is stored in GitHub.
- The OIDC trust subject is limited to the exact public repository and the GitHub `production` Environment.
- AWS resource identifiers are resolved at runtime rather than committed to the public repository.

## Verification

- Local repository and delivery tests: 15 passed.
- Backend: 79 pytest tests passed, including Hypothesis properties; dependency audit found no known vulnerabilities.
- Public and admin web: `npm ci`, typecheck, and Vite production builds passed; dependency audits found no vulnerabilities.
- SAM lint: backend, shared infrastructure, and GitHub OIDC bootstrap templates passed.
- First GitHub CI: all five jobs passed and produced short-lived SBOM artifacts.
- AWS bootstrap stack: `iyf-github-actions-prod` reached `CREATE_COMPLETE`.
- OIDC trust: immutable GitHub owner/repository IDs and the `production` Environment subject were verified from the deployed role.
- OIDC workflow verification: passed with `deploy=false`; all application deployment steps were skipped.

## Security Compliance

- **SECURITY-01**: Compliant. The artifact bucket uses server-side encryption, versioning, public access blocks, and an explicit non-TLS deny.
- **SECURITY-03/05/09/11/12/15**: Compliant. Logs avoid credentials, target inputs fail closed, local credentials remain excluded, controls are layered, credentials are short-lived, and dependent deploy steps stop on failure.
- **SECURITY-06**: Compliant. OIDC trust is exact, the GitHub role can pass only the dedicated execution role, and application stack/resource patterns are scoped. APIs without resource-level authorization have documented exceptions.
- **SECURITY-10/13**: Compliant. Dependencies and Actions are pinned, audits and SBOMs run in CI, main is protected, and production requires Environment approval.
- **SECURITY-02/04/07/08/14**: N/A to the delivery foundation; existing application traffic, headers, network, authorization, and application monitoring behavior were not changed.

No blocking Security Baseline finding remains for U7.
