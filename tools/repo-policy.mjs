import { execFileSync } from "node:child_process";
import { readFileSync, statSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

export const MAX_TRACKED_BYTES = 5 * 1024 * 1024;

const forbiddenPathRules = [
  { pattern: /(^|\/)\.env(?:\.|$)/i, code: "forbidden-env", message: "environment files must not be committed" },
  { pattern: /(^|\/)\.claude\/settings\.local\.json$/i, code: "local-settings", message: "local Claude settings must remain untracked" },
  { pattern: /^aidlc-docs\/audit\.md$/i, code: "local-audit", message: "the local AI-DLC audit log is not public" },
  { pattern: /(^|\/)(node_modules|dist|\.aws-sam|__pycache__|\.pytest_cache|\.hypothesis|\.venv|venv)(\/|$)/i, code: "generated-path", message: "generated content or dependencies must not be committed" },
  { pattern: /(^|\/)(credentials(?:\..*)?|id_rsa|id_ed25519)$/i, code: "credential-file", message: "credential files must not be committed" },
  { pattern: /\.(pem|p12|key)$/i, code: "private-key-file", message: "private key files must not be committed" },
];

const secretPatterns = [
  { pattern: /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/, code: "private-key", message: "private key material detected" },
  { pattern: /\b(?:AKIA|ASIA)[A-Z0-9]{16}\b/, code: "aws-access-key", message: "AWS access key ID detected" },
  { pattern: /\bgh[pousr]_[A-Za-z0-9_]{20,}\b/, code: "github-token", message: "GitHub token detected" },
  { pattern: /^<<<<<<< .+$|^>>>>>>> .+$/m, code: "merge-conflict", message: "unresolved merge conflict marker detected" },
];

export function normalizeRepoPath(filePath) {
  return String(filePath).replaceAll("\\", "/").replace(/^\.\//, "");
}

export function inspectCandidate({ filePath, content = Buffer.alloc(0), size }) {
  const normalized = normalizeRepoPath(filePath);
  const bytes = size ?? Buffer.byteLength(content);
  const issues = [];

  const isExampleEnv = /(^|\/)\.env\.example$/i.test(normalized);
  for (const rule of forbiddenPathRules) {
    if (rule.code === "forbidden-env" && isExampleEnv) continue;
    if (rule.pattern.test(normalized)) issues.push(issue(normalized, rule));
  }

  if (bytes > MAX_TRACKED_BYTES) {
    issues.push({ filePath: normalized, code: "oversized-file", message: `file exceeds ${MAX_TRACKED_BYTES} bytes` });
  }

  const buffer = Buffer.isBuffer(content) ? content : Buffer.from(String(content));
  if (!buffer.includes(0)) {
    const text = buffer.toString("utf8");
    for (const rule of secretPatterns) {
      if (rule.pattern.test(text)) issues.push(issue(normalized, rule));
    }
  }
  return issues;
}

export function inspectCandidates(candidates) {
  return candidates.flatMap(inspectCandidate);
}

function issue(filePath, rule) {
  return { filePath, code: rule.code, message: rule.message };
}

function git(args, encoding = "buffer") {
  return execFileSync("git", args, { encoding, stdio: ["ignore", "pipe", "pipe"] });
}

function nullSeparated(buffer) {
  return buffer.toString("utf8").split("\0").filter(Boolean);
}

function stagedCandidates() {
  const paths = nullSeparated(git(["diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"]));
  return paths.map((filePath) => {
    const content = git(["show", `:${filePath}`]);
    return { filePath, content, size: content.length };
  });
}

function trackedCandidates() {
  const paths = nullSeparated(git(["ls-files", "-z"]));
  return paths.map((filePath) => {
    const content = git(["show", `HEAD:${filePath}`]);
    return { filePath, content, size: content.length };
  });
}

function workingTreeCandidates(paths) {
  return paths.map((filePath) => ({ filePath, content: readFileSync(filePath), size: statSync(filePath).size }));
}

export function formatIssues(issues) {
  return issues.map((item) => `${item.filePath}: [${item.code}] ${item.message}`).join("\n");
}

function main() {
  const [mode = "--tracked", ...paths] = process.argv.slice(2);
  let candidates;
  if (mode === "--staged") candidates = stagedCandidates();
  else if (mode === "--tracked") candidates = trackedCandidates();
  else if (mode === "--files" && paths.length > 0) candidates = workingTreeCandidates(paths);
  else throw new Error("usage: repo-policy.mjs --staged | --tracked | --files <path...>");

  const issues = inspectCandidates(candidates);
  if (issues.length > 0) {
    process.stderr.write(`Repository policy rejected ${issues.length} issue(s):\n${formatIssues(issues)}\n`);
    process.exitCode = 1;
  } else {
    process.stdout.write(`Repository policy passed for ${candidates.length} file(s).\n`);
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main();
}
