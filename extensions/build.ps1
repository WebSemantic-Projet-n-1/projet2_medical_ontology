param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("chrome", "firefox")]
    [string]$Target
)

$dir = $PSScriptRoot
$activeManifest  = Join-Path $dir "manifest.json"
$chromeManifest  = Join-Path $dir "manifest-chrome.json"
$firefoxManifest = Join-Path $dir "manifest-firefox.json"

$source = if ($Target -eq "chrome") { $chromeManifest } else { $firefoxManifest }

if (-not (Test-Path $source)) {
    Write-Error "$source not found."
    exit 1
}

Copy-Item $source $activeManifest -Force
Write-Host "Switched to $Target. Load the 'extensions' folder in your browser." -ForegroundColor Green