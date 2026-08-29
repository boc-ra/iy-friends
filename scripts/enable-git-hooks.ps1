$ErrorActionPreference = "Stop"

$repoRoot = git rev-parse --show-toplevel
if (-not $repoRoot) {
    throw "Run this script from inside the IY Friends Git repository."
}

git -C $repoRoot config core.hooksPath .githooks
Write-Output "Git hooks enabled from .githooks"

