import { appendFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

export const DEPLOYMENT_TARGETS = Object.freeze(["infra", "backend", "public-web", "all"]);

export function selectDeploymentTarget(target) {
  if (!DEPLOYMENT_TARGETS.includes(target)) {
    throw new Error(`Invalid deployment target: ${target}`);
  }

  return Object.freeze({
    deploy_infra: target === "infra" || target === "all",
    deploy_backend: target === "backend" || target === "all",
    deploy_public_web: target === "public-web" || target === "all",
  });
}

export function formatGitHubOutputs(selection) {
  return Object.entries(selection)
    .map(([key, value]) => `${key}=${String(value)}`)
    .join("\n");
}

function main() {
  const selection = selectDeploymentTarget(process.argv[2] ?? "");
  const output = `${formatGitHubOutputs(selection)}\n`;
  const githubOutput = process.env.GITHUB_OUTPUT;

  if (githubOutput) appendFileSync(githubOutput, output, { encoding: "utf8" });
  else process.stdout.write(output);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    main();
  } catch (error) {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  }
}
