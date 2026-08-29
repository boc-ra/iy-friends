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
- [ ] Step 10: Create the public GitHub repository, configure the production Environment, commit, and push.
- [ ] Step 11: Create the AWS OIDC bootstrap stack with fresh production authorization.
- [ ] Step 12: Verify the first GitHub CI run and OIDC role assumption without deploying application resources.

## Boundaries

- `iyf-admin-web` is validated by CI and is not a production deployment target.
- No application stack or public web artifact is deployed during foundation verification.
- GitHub Actions use short-lived AWS credentials through OIDC; no long-lived AWS secret is stored in GitHub.
- The OIDC trust subject is limited to the exact public repository and the GitHub `production` Environment.
- AWS resource identifiers are resolved at runtime rather than committed to the public repository.
