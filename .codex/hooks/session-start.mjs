let input = "";
for await (const chunk of process.stdin) input += chunk;

try {
  if (input.trim()) JSON.parse(input);
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: "SessionStart",
      additionalContext: "IY Friends is a public monorepo. Never expose .env, local settings, or aidlc-docs/audit.md. Validate both frontends, backend tests, and SAM templates. The admin web is CI-only and must not be deployed. Production AWS changes require separate explicit authorization.",
    },
  }));
} catch {
  process.stderr.write("Invalid SessionStart Hook input JSON.\n");
  process.exitCode = 2;
}

