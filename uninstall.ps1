param(
    [switch]$RemoveData
)

$ErrorActionPreference = "Stop"
$InstallDirectory = Join-Path ([Environment]::GetFolderPath("LocalApplicationData")) "RepoTraction"
$ExpectedDirectory = [IO.Path]::GetFullPath($InstallDirectory)
$ProgramsDirectory = [Environment]::GetFolderPath("Programs")
$ShortcutPath = Join-Path $ProgramsDirectory "RepoTraction.lnk"

if ([IO.Path]::GetFileName($ExpectedDirectory) -ne "RepoTraction") {
    throw "Refusing to uninstall from an unexpected directory: $ExpectedDirectory"
}

if (Test-Path -LiteralPath $ShortcutPath) {
    Remove-Item -LiteralPath $ShortcutPath -Force
}

$installedFiles = @("app.py", "github_cli.py", "start.ps1", "start.cmd", "README.md", "LICENSE", "uninstall.ps1")
foreach ($file in $installedFiles) {
    $target = Join-Path $ExpectedDirectory $file
    if (Test-Path -LiteralPath $target -PathType Leaf) {
        Remove-Item -LiteralPath $target -Force
    }
}

$StaticDirectory = Join-Path $ExpectedDirectory "static"
if (Test-Path -LiteralPath $StaticDirectory -PathType Container) {
    Remove-Item -LiteralPath $StaticDirectory -Recurse -Force
}

$AnalyticsDirectory = [IO.Path]::GetFullPath((Join-Path $ExpectedDirectory "analytics"))
if ([IO.Path]::GetDirectoryName($AnalyticsDirectory) -ne $ExpectedDirectory) {
    throw "Refusing to remove analytics outside the installation directory."
}
if (Test-Path -LiteralPath $AnalyticsDirectory -PathType Container) {
    if ((Get-Item -LiteralPath $AnalyticsDirectory -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw "Refusing to recursively remove an analytics link or junction."
    }
    Remove-Item -LiteralPath $AnalyticsDirectory -Recurse -Force
}

$StorageDirectory = [IO.Path]::GetFullPath((Join-Path $ExpectedDirectory "storage"))
if ([IO.Path]::GetDirectoryName($StorageDirectory) -ne $ExpectedDirectory) {
    throw "Refusing to remove storage outside the installation directory."
}
if (Test-Path -LiteralPath $StorageDirectory -PathType Container) {
    if ((Get-Item -LiteralPath $StorageDirectory -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw "Refusing to recursively remove a storage link or junction."
    }
    Remove-Item -LiteralPath $StorageDirectory -Recurse -Force
}

$DataDirectory = Join-Path $ExpectedDirectory "data"
if ($RemoveData -and (Test-Path -LiteralPath $DataDirectory -PathType Container)) {
    Remove-Item -LiteralPath $DataDirectory -Recurse -Force
}

if (Test-Path -LiteralPath $ExpectedDirectory -PathType Container) {
    $RemainingItems = Get-ChildItem -LiteralPath $ExpectedDirectory -Force
    if (-not $RemainingItems) {
        Remove-Item -LiteralPath $ExpectedDirectory -Force
    }
}

Write-Host ""
Write-Host "RepoTraction has been uninstalled." -ForegroundColor Green
if (-not $RemoveData -and (Test-Path -LiteralPath $DataDirectory)) {
    Write-Host "Local history was preserved in $DataDirectory"
    Write-Host "Delete that folder manually only if you also want to remove the collected history."
}
