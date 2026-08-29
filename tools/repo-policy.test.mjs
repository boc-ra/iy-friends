import assert from "node:assert/strict";
import test from "node:test";
import { inspectCandidate, normalizeRepoPath } from "./repo-policy.mjs";

test("normalizes Windows repository paths", () => {
  assert.equal(normalizeRepoPath(".\\src\\main.ts"), "src/main.ts");
});

test("allows environment examples", () => {
  assert.deepEqual(inspectCandidate({ filePath: "app/.env.example", content: "API_URL=\n" }), []);
});

test("rejects real environment files", () => {
  assert.equal(inspectCandidate({ filePath: "app/.env", content: "API_URL=value\n" })[0].code, "forbidden-env");
});

test("rejects high-confidence AWS credentials", () => {
  const credentialFixture = ["AK", "IA", "1234567890ABCDEF"].join("");
  const issues = inspectCandidate({ filePath: "notes.txt", content: `key=${credentialFixture}\n` });
  assert.equal(issues[0].code, "aws-access-key");
});

test("rejects local audit history", () => {
  assert.equal(inspectCandidate({ filePath: "aidlc-docs/audit.md", content: "local\n" })[0].code, "local-audit");
});

test("rejects unresolved merge conflict markers", () => {
  const issues = inspectCandidate({ filePath: "src/file.ts", content: "<<<<<<< HEAD\nvalue\n>>>>>>> branch\n" });
  assert.equal(issues.some((item) => item.code === "merge-conflict"), true);
});
