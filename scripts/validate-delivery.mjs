import { readFileSync } from "node:fs";

const ci = readFileSync(".github/workflows/ci.yml", "utf8");
const deploy = readFileSync(".github/workflows/deploy-production.yml", "utf8");
const bootstrap = readFileSync("iyf-infra/github-actions-bootstrap.yaml", "utf8");

const failures = [];
const requireMatch = (content, pattern, message) => {
  if (!pattern.test(content)) failures.push(message);
};

for (const [name, workflow] of [["CI", ci], ["deployment", deploy]]) {
  const uses = [...workflow.matchAll(/^\s*-?\s*uses:\s*([^\s#]+)(?:\s*#.*)?$/gm)].map((match) => match[1]);
  for (const action of uses) {
    if (!/@[a-f0-9]{40}$/.test(action)) failures.push(`${name}: Action is not pinned to a full commit SHA: ${action}`);
  }
}

requireMatch(ci, /^permissions:\s*\r?\n\s+contents:\s+read\s*$/m, "CI must default to contents: read");
requireMatch(ci, /iyf-admin-web/, "CI must validate the admin web");
requireMatch(ci, /pip-audit/, "CI must audit Python dependencies");
requireMatch(ci, /npm audit --audit-level=high/, "CI must audit npm dependencies");
requireMatch(ci, /cyclonedx-py/, "CI must generate a backend SBOM");

requireMatch(deploy, /workflow_dispatch:/, "deployment must be manually dispatched");
requireMatch(deploy, /environment:\s+production/, "deployment must use the production Environment");
requireMatch(deploy, /id-token:\s+write/, "deployment must grant OIDC token permission only to its deploy job");
requireMatch(deploy, /concurrency:\s*\r?\n\s+group:\s+iyf-production/, "deployment must serialize production changes");
requireMatch(deploy, /deploy:\s*\r?\n\s+description:.*false/m, "application deployment must default to verification-only");
if (/iyf-admin-web/.test(deploy)) failures.push("deployment workflow must never reference the admin web");

requireMatch(bootstrap, /GitHubOwnerId:/, "OIDC bootstrap must require the immutable owner ID");
requireMatch(bootstrap, /GitHubRepositoryId:/, "OIDC bootstrap must require the immutable repository ID");
requireMatch(
  bootstrap,
  /repo:\$\{GitHubOwner\}@\$\{GitHubOwnerId\}\/\$\{GitHubRepository\}@\$\{GitHubRepositoryId\}:environment:\$\{GitHubEnvironment\}/,
  "OIDC subject must use immutable IDs and the exact Environment",
);

if (failures.length > 0) {
  process.stderr.write(`Delivery validation failed:\n- ${failures.join("\n- ")}\n`);
  process.exitCode = 1;
} else {
  process.stdout.write("Delivery validation passed.\n");
}
