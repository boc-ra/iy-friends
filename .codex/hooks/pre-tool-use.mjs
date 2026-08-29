import { analyzeToolCall } from "./tool-policy.mjs";

let input = "";
for await (const chunk of process.stdin) input += chunk;

let event = {};
try {
  event = input.trim() ? JSON.parse(input) : {};
} catch {
  process.stderr.write("Invalid Hook input JSON; repository policy did not make an allow decision.\n");
  process.exitCode = 2;
}

if (process.exitCode !== 2) {
  const result = analyzeToolCall(event);
  if (result.deny) {
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: result.reason,
      },
    }));
  }
}

