## Summary

<!-- What changed and why? -->

## Validation

<!-- List the checks that were actually run. -->

- [ ] Relevant typechecks, tests, builds, or SAM lint passed
- [ ] `node tools/repo-policy.mjs --staged` passed
- [ ] No credentials, real `.env` files, generated builds, or local audit files are included

## Delivery safety

- [ ] This change does not deploy `iyf-admin-web`
- [ ] Production deployment is not required, or fresh production authorization will be obtained immediately before deployment
- [ ] Cross-component deployment order remains shared infrastructure, backend, then public web
