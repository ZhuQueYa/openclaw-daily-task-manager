#Requires -Version 5.1
<#
.SYNOPSIS
  First-time setup: copy example config, create data dirs, seed markdown files.

.USAGE
  cd daily_task_manager
  powershell -ExecutionPolicy Bypass -File scripts\init.ps1 -ProjectRoot "C:\Users\YourName\daily_task_manager"
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectRoot
)

$ErrorActionPreference = "Stop"
$RepoToolRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

function Ensure-Dir([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-Host "created: $Path"
    }
}

$configDir = Join-Path $ProjectRoot "config"
$pathsFile = Join-Path $configDir "paths.json"
$exampleFile = Join-Path $RepoToolRoot "config\paths.example.json"

Ensure-Dir $ProjectRoot
Ensure-Dir $configDir
Ensure-Dir (Join-Path $ProjectRoot "app")
Ensure-Dir (Join-Path $ProjectRoot "scripts")
Ensure-Dir (Join-Path $ProjectRoot "logs")
Ensure-Dir (Join-Path $ProjectRoot "backup")
Ensure-Dir (Join-Path $ProjectRoot "data\life")
Ensure-Dir (Join-Path $ProjectRoot "data\taie")
Ensure-Dir (Join-Path $ProjectRoot "data\archive\daily_done")
Ensure-Dir (Join-Path $ProjectRoot "data\reminders")

if (-not (Test-Path -LiteralPath $pathsFile)) {
    if (-not (Test-Path -LiteralPath $exampleFile)) {
        throw "Missing example config: $exampleFile"
    }
    Copy-Item -LiteralPath $exampleFile -Destination $pathsFile
    Write-Host "copied: paths.example.json -> config\paths.json"
    Write-Warning "Edit config\paths.json so all paths point to: $ProjectRoot"
} else {
    Write-Host "exists: config\paths.json (skipped)"
}

$examples = Join-Path $RepoToolRoot "examples"
$seeds = @(
    @{ Src = "sample_TASKS.md"; Dst = "data\life\TASKS.md" },
    @{ Src = "sample_BACKLOG.md"; Dst = "data\life\BACKLOG.md" },
    @{ Src = "sample_TODAY.md"; Dst = "data\life\TODAY.md" },
    @{ Src = "sample_timed_reminders.json"; Dst = "data\reminders\timed_reminders.json" }
)

foreach ($item in $seeds) {
    $dst = Join-Path $ProjectRoot $item.Dst
    if (-not (Test-Path -LiteralPath $dst)) {
        Copy-Item -LiteralPath (Join-Path $examples $item.Src) -Destination $dst
        Write-Host "seeded: $($item.Dst)"
    }
}

$runExample = Join-Path $RepoToolRoot "scripts\run.cmd.example"
$runLocal = Join-Path $ProjectRoot "scripts\run.cmd"
if (-not (Test-Path -LiteralPath $runLocal)) {
    Ensure-Dir (Join-Path $ProjectRoot "scripts")
    Copy-Item -LiteralPath $runExample -Destination $runLocal
    Write-Host "copied: run.cmd.example -> scripts\run.cmd"
    Write-Warning "Edit scripts\run.cmd: set ROOT=$ProjectRoot and your Python path"
}

Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Edit $pathsFile"
Write-Host "  2. Edit $runLocal"
Write-Host "  3. Place your TAIE.xmind at data\taie\TAIE.xmind (optional)"
Write-Host "  4. Run: scripts\run.cmd check"
