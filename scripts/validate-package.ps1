$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Required = @(
  '.github/copilot-instructions.md',
  'README-AI-TEAM.md',
  'docs/project/project-profile.md',
  'docs/ems/safety-checklist.md'
)
$Errors = @()
foreach ($Item in $Required) {
  if (-not (Test-Path (Join-Path $Root $Item) -PathType Leaf)) { $Errors += "Missing required file: $Item" }
}
$Agents = @(Get-ChildItem (Join-Path $Root '.github/agents') -Filter '*.agent.md')
$Instructions = @(Get-ChildItem (Join-Path $Root '.github/instructions') -Filter '*.instructions.md')
$Prompts = @(Get-ChildItem (Join-Path $Root '.github/prompts') -Filter '*.prompt.md')
if ($Agents.Count -ne 12) { $Errors += "Expected 12 agents, found $($Agents.Count)" }
if ($Instructions.Count -lt 10) { $Errors += "Expected at least 10 instruction files, found $($Instructions.Count)" }
if ($Prompts.Count -lt 8) { $Errors += "Expected at least 8 prompts, found $($Prompts.Count)" }
if ($Errors.Count -gt 0) { $Errors | ForEach-Object { Write-Error $_ }; exit 1 }
$Files = @(Get-ChildItem $Root -Recurse -File)
Write-Host "OK: $($Agents.Count) agents, $($Instructions.Count) instructions, $($Prompts.Count) prompts, $($Files.Count) files"
