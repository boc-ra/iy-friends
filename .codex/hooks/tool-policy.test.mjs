import assert from "node:assert/strict";
import test from "node:test";
import { analyzeToolCall } from "./tool-policy.mjs";

test("allows read-only AWS inspection", () => {
  assert.deepEqual(analyzeToolCall({ tool_name: "Bash", tool_input: { command: "aws cloudformation describe-stacks" } }), { deny: false });
});

test("blocks destructive Git reset", () => {
  assert.equal(analyzeToolCall({ tool_name: "Bash", tool_input: { command: "git reset --hard HEAD~1" } }).deny, true);
});

test("requires approval marker for SAM deploy", () => {
  assert.equal(analyzeToolCall({ tool_name: "Bash", tool_input: { command: "sam deploy" } }).deny, true);
  assert.equal(analyzeToolCall({ tool_name: "Bash", tool_input: { command: "IYF_PRODUCTION_CHANGE_APPROVED=1 sam deploy" } }).deny, false);
});

test("blocks edits to real env files but allows examples", () => {
  const realEnv = "*** Begin Patch\n*** Update File: app/.env\n*** End Patch";
  const example = "*** Begin Patch\n*** Update File: app/.env.example\n*** End Patch";
  assert.equal(analyzeToolCall({ tool_name: "apply_patch", tool_input: { command: realEnv } }).deny, true);
  assert.equal(analyzeToolCall({ tool_name: "apply_patch", tool_input: { command: example } }).deny, false);
});

