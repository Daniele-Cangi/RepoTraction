param(
    [switch]$NoShortcut,
    [string]$Destination
)

$ErrorActionPreference = "Stop"
$SourceDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallDirectory = Join-Path ([Environment]::GetFolderPath("LocalApplicationData")) "RepoTraction"
if ($Destination) {
    $InstallDirectory = [System.IO.Path]::GetFullPath($Destination)
}
$LegacyInstallDirectory = Join-Path ([Environment]::GetFolderPath("LocalApplicationData")) "GitHubPulse"
$StaticDirectory = Join-Path $InstallDirectory "static"
$DataDirectory = Join-Path $InstallDirectory "data"
$MissingLinkDirectory = Join-Path $InstallDirectory "missing_link"
$AnalyticsDirectory = Join-Path $InstallDirectory "analytics"
$StorageDirectory = Join-Path $InstallDirectory "storage"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.10 or newer is required and must be available in PATH."
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI (gh) is required and must be available in PATH."
}

$requiredFiles = @("app.py", "start.ps1", "start.cmd", "README.md", "LICENSE", "uninstall.ps1", ".env.example")
foreach ($file in $requiredFiles) {
    $source = Join-Path $SourceDirectory $file
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Required installation file is missing: $file"
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $SourceDirectory "missing_link\service.py") -PathType Leaf)) {
    throw "Required Missing Link module directory is missing."
}
if (-not (Test-Path -LiteralPath (Join-Path $SourceDirectory "analytics\traffic.py") -PathType Leaf)) {
    throw "Required analytics module directory is missing."
}
if (-not (Test-Path -LiteralPath (Join-Path $SourceDirectory "analytics\events.py") -PathType Leaf)) {
    throw "Required analytics event module is missing."
}
if (-not (Test-Path -LiteralPath (Join-Path $SourceDirectory "analytics\repositories.py") -PathType Leaf)) {
    throw "Required repository analytics module is missing."
}
if (-not (Test-Path -LiteralPath (Join-Path $SourceDirectory "analytics\opportunities.py") -PathType Leaf)) {
    throw "Required opportunity analytics module is missing."
}
if (-not (Test-Path -LiteralPath (Join-Path $SourceDirectory "analytics\event_evidence.py") -PathType Leaf)) {
    throw "Required event evidence analytics module is missing."
}
foreach ($module in @("database.py", "migrations.py", "registry.py")) {
    if (-not (Test-Path -LiteralPath (Join-Path $SourceDirectory "storage\$module") -PathType Leaf)) {
        throw "Required storage module is missing: $module"
    }
}

New-Item -ItemType Directory -Path $InstallDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $StaticDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $DataDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $MissingLinkDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $AnalyticsDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $StorageDirectory -Force | Out-Null

$LegacyDataDirectory = Join-Path $LegacyInstallDirectory "data"
if (-not $Destination -and (Test-Path -LiteralPath $LegacyDataDirectory -PathType Container) -and
    -not (Get-ChildItem -LiteralPath $DataDirectory -Filter "*.sqlite3" -File -ErrorAction SilentlyContinue)) {
    Get-ChildItem -LiteralPath $LegacyDataDirectory -Filter "*.sqlite3*" -File | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $DataDirectory $_.Name) -Force
    }
}

foreach ($file in $requiredFiles) {
    Copy-Item -LiteralPath (Join-Path $SourceDirectory $file) -Destination (Join-Path $InstallDirectory $file) -Force
}
Get-ChildItem -LiteralPath (Join-Path $SourceDirectory "static") -File | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $StaticDirectory $_.Name) -Force
}
Get-ChildItem -LiteralPath (Join-Path $SourceDirectory "missing_link") -Filter "*.py" -File | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $MissingLinkDirectory $_.Name) -Force
}
Get-ChildItem -LiteralPath (Join-Path $SourceDirectory "analytics") -Filter "*.py" -File | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $AnalyticsDirectory $_.Name) -Force
}
Get-ChildItem -LiteralPath (Join-Path $SourceDirectory "storage") -Filter "*.py" -File | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $StorageDirectory $_.Name) -Force
}

# Ship optional tools and their documentation, never local .env or runtime/data.
foreach ($folder in @("scripts", "docs", "examples\missing-link")) {
    $sourceFolder = Join-Path $SourceDirectory $folder
    $targetFolder = Join-Path $InstallDirectory $folder
    New-Item -ItemType Directory -Path $targetFolder -Force | Out-Null
    Get-ChildItem -LiteralPath $sourceFolder -File | Where-Object {
        $_.Extension -in @(".py", ".md", ".json")
    } | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $targetFolder $_.Name) -Force
    }
}

if (-not $NoShortcut) {
    $ProgramsDirectory = [Environment]::GetFolderPath("Programs")
    $ShortcutPath = Join-Path $ProgramsDirectory "RepoTraction.lnk"
    $PowerShellPath = (Get-Command powershell.exe -ErrorAction Stop).Source
    $Shell = New-Object -ComObject WScript.Shell
    $Shortcut = $Shell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $PowerShellPath
    $Shortcut.Arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + (Join-Path $InstallDirectory "start.ps1") + '"'
    $Shortcut.WorkingDirectory = $InstallDirectory
    $Shortcut.Description = "Open the local RepoTraction dashboard"
    $Shortcut.Save()
}

Write-Host ""
Write-Host "RepoTraction is installed in $InstallDirectory" -ForegroundColor Green
Write-Host "Your local history will be stored in $DataDirectory"
if (-not $NoShortcut) {
    Write-Host "Open RepoTraction from the Windows Start menu."
} else {
    Write-Host "Run .\start.ps1 from the installation directory."
}
