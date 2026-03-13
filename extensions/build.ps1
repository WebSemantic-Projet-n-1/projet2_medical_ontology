param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("chrome", "firefox")]
    [string]$Target
)

$dir = $PSScriptRoot

$activeManifest  = Join-Path $dir "manifest.json"
$chromeManifest  = Join-Path $dir "manifest-chrome.json"
$firefoxManifest = Join-Path $dir "manifest-firefox.json"

# Detect which browser is currently active by reading the manifest_version field
function Get-ActiveBrowser {
    if (-not (Test-Path $activeManifest)) { return $null }
    $json = Get-Content $activeManifest -Raw | ConvertFrom-Json
    if ($json.manifest_version -eq 3) { return "chrome" }
    if ($json.manifest_version -eq 2) { return "firefox" }
    return $null
}

$current = Get-ActiveBrowser

if ($current -eq $Target) {
    Write-Host "Already set to $Target. Nothing to do." -ForegroundColor Green
    exit 0
}

# Save the current active manifest back to its named file
if ($current -eq "chrome") {
    Copy-Item $activeManifest $chromeManifest -Force
    Write-Host "Saved active manifest as manifest-chrome.json"
} elseif ($current -eq "firefox") {
    Copy-Item $activeManifest $firefoxManifest -Force
    Write-Host "Saved active manifest as manifest-firefox.json"
}

# Swap in the target manifest
if ($Target -eq "chrome") {
    if (-not (Test-Path $chromeManifest)) {
        Write-Error "manifest-chrome.json not found."
        exit 1
    }
    Copy-Item $chromeManifest $activeManifest -Force
    Write-Host "Switched to Chrome (MV3)" -ForegroundColor Cyan
} elseif ($Target -eq "firefox") {
    if (-not (Test-Path $firefoxManifest)) {
        Write-Error "manifest-firefox.json not found."
        exit 1
    }
    Copy-Item $firefoxManifest $activeManifest -Force
    Write-Host "Switched to Firefox (MV2)" -ForegroundColor Cyan
}

Write-Host "Done. Load the 'extensions' folder in your browser." -ForegroundColor Green
