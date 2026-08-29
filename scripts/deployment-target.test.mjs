import assert from "node:assert/strict";
import test from "node:test";
import { DEPLOYMENT_TARGETS, formatGitHubOutputs, selectDeploymentTarget } from "./deployment-target.mjs";

test("the deployment target allowlist never includes the admin web", () => {
  assert.deepEqual(DEPLOYMENT_TARGETS, ["infra", "backend", "public-web", "all"]);
  assert.equal(DEPLOYMENT_TARGETS.some((target) => target.includes("admin")), false);
});

test("each single target selects exactly one production component", () => {
  for (const target of DEPLOYMENT_TARGETS.filter((value) => value !== "all")) {
    const selectedCount = Object.values(selectDeploymentTarget(target)).filter(Boolean).length;
    assert.equal(selectedCount, 1, target);
  }
});

test("all preserves the required dependency order flags", () => {
  assert.deepEqual(selectDeploymentTarget("all"), {
    deploy_infra: true,
    deploy_backend: true,
    deploy_public_web: true,
  });
});

test("unknown targets fail closed", () => {
  assert.throws(() => selectDeploymentTarget("admin-web"), /Invalid deployment target/);
  assert.throws(() => selectDeploymentTarget(""), /Invalid deployment target/);
});

test("GitHub outputs are deterministic lowercase booleans", () => {
  assert.equal(
    formatGitHubOutputs(selectDeploymentTarget("infra")),
    "deploy_infra=true\ndeploy_backend=false\ndeploy_public_web=false",
  );
});
