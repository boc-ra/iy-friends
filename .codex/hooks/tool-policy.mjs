const destructiveAlways = [
  /\bgit\s+reset\s+--hard\b/i,
  /\bgit\s+clean\s+-[^\s]*[fdx][^\s]*\b/i,
  /\bgit\s+(?:checkout|restore)\s+--\s+/i,
  /\baws\s+cloudformation\s+delete-stack\b/i,
  /\baws\s+s3\s+rm\b[^\r\n]*\s--recursive\b/i,
  /\bsam\s+delete\b/i,
];

const productionMutation = [
  /\bsam\s+deploy\b/i,
  /\baws\s+s3\s+sync\b[^\r\n]*\bs3:\/\/iyf-prod-/i,
  /\baws\s+cloudfront\s+create-invalidation\b/i,
  /\baws\s+cognito-idp\s+admin-(?:create|delete|disable|enable|add|remove|update)/i,
];

const localSecretRead = [
  /\b(?:cat|type|Get-Content)\b[^\r\n]*(?:^|[\\/])\.env(?:\s|$)/i,
  /\b(?:cat|type|Get-Content)\b[^\r\n]*settings\.local\.json/i,
];

export function analyzeToolCall(event) {
  const toolName = String(event?.tool_name ?? "");
  const command = String(event?.tool_input?.command ?? "");

  if (toolName === "Bash") {
    if (destructiveAlways.some((pattern) => pattern.test(command))) {
      return { deny: true, reason: "Destructive Git or AWS deletion commands are blocked by repository policy." };
    }
    if (localSecretRead.some((pattern) => pattern.test(command))) {
      return { deny: true, reason: "Reading local credential or environment files into tool output is blocked." };
    }
    if (productionMutation.some((pattern) => pattern.test(command)) && !/IYF_PRODUCTION_CHANGE_APPROVED=1/i.test(command)) {
      return { deny: true, reason: "Production mutation requires an explicit approval marker: IYF_PRODUCTION_CHANGE_APPROVED=1." };
    }
  }

  if (toolName === "apply_patch" && touchesProtectedLocalFile(command)) {
    return { deny: true, reason: "Edits to real .env or local settings files are blocked; edit the example configuration instead." };
  }
  return { deny: false };
}

function touchesProtectedLocalFile(patch) {
  const headers = patch.match(/^\*{3} (?:Add|Update|Delete) File: (.+)$/gm) ?? [];
  return headers.some((header) => {
    const filePath = header.replace(/^\*{3} (?:Add|Update|Delete) File: /, "").replaceAll("\\", "/");
    if (/(^|\/)\.env\.example$/i.test(filePath)) return false;
    return /(^|\/)\.env(?:\.|$)/i.test(filePath) || /(^|\/)\.claude\/settings\.local\.json$/i.test(filePath);
  });
}

