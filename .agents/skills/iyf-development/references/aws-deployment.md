# AWS Deployment Reference

Read this reference only for AWS infrastructure, deployment, production verification, or rollback work.

## Production ownership

- `iyf-infra` owns shared S3, CloudFront, Cognito, SNS, and CloudWatch resources.
- `iyf-backend-api` owns API Gateway, Lambda functions, and DynamoDB tables.
- `iyf-public-web` is deployed to the shared WebBucket and CloudFront distribution.
- `iyf-admin-web` is not hosted and must not be included in production deployment automation.

## Deployment order

For an all-target deployment:

1. Validate and deploy `iyf-infra`.
2. Validate, build, and deploy `iyf-backend-api`.
3. Build `iyf-public-web`, sync `dist` to the exported WebBucket, and invalidate CloudFront.

Stop on the first failure. Do not continue to dependent targets.

## Authorization boundary

- GitHub Actions uses OIDC with short-lived credentials.
- OIDC trust is limited to the exact GitHub repository and `production` Environment subject.
- The GitHub job needs only `contents: read` and `id-token: write`.
- A GitHub Environment approval must complete before the deploy job requests AWS credentials.
- Local production changes require a fresh, explicit user authorization immediately before execution.

## Production identifiers

Resolve stack outputs at runtime. Do not hardcode account IDs, bucket names, distribution IDs, API IDs, User Pool IDs, or client IDs in public workflow files.

