<#
.SYNOPSIS
    Charge les deux versions OWL de Gene Ontology dans Apache Jena Fuseki
    via le Graph Store Protocol (HTTP PUT). Equivalent Windows de load-data.sh.

.DESCRIPTION
    Requiert que Fuseki soit déjà en cours d'exécution (docker-compose up fuseki).
    Idempotent : ne recharge pas si le marqueur .data-loaded est présent.

.PARAMETER FusekiUrl
    URL de base du serveur Fuseki. Défaut : http://localhost:3030

.PARAMETER Dataset
    Nom du dataset Fuseki. Défaut : ds

.PARAMETER AdminPassword
    Mot de passe administrateur. Défaut : admin

.PARAMETER DataDir
    Répertoire contenant les fichiers OWL. Défaut : .\data

.EXAMPLE
    .\load-data.ps1
    .\load-data.ps1 -AdminPassword "monmotdepasse" -DataDir "C:\go-data"
#>

param(
    [string]$FusekiUrl     = "http://localhost:3030",
    [string]$Dataset       = "ds",
    [string]$AdminPassword = "admin",
    [string]$DataDir       = (Join-Path $PSScriptRoot "..\..\..\data")
    [string]$GraphOldDir   = "\gene-ontology-10-25\data\ontology",
    [string]$GraphNewDir   = "\gene-ontology-11-26\data\ontology",
)

$ErrorActionPreference = "Stop"

$GraphOld  = "http://purl.obolibrary.org/obo/go/version/2025-10"
$GraphNew  = "http://purl.obolibrary.org/obo/go/version/2026-01"
$FileOld   = Join-Path $DataDir $GraphOldDir "go.owl"
$FileNew   = Join-Path $DataDir $GraphNewDir "go.owl"
$Marker    = Join-Path $PSScriptRoot ".data-loaded"

# ── Idempotence ──────────────────────────────────────────────────────────────
if (Test-Path $Marker) {
    Write-Host "[loader] Les données sont déjà chargées ($Marker trouvé). Abandon."
    exit 0
}

# ── Vérification des fichiers source ─────────────────────────────────────────
$missing = $false
foreach ($f in @($FileOld, $FileNew)) {
    if (-not (Test-Path $f)) {
        Write-Warning "[loader] Fichier absent : $f"
        $missing = $true
    }
}
if ($missing) {
    Write-Error "Un ou plusieurs fichiers OWL sont manquants dans $DataDir.`nTéléchargez go_2025-10.owl et go_2026-01.owl depuis https://zenodo.org/records/18422732"
    exit 1
}

# ── Chargement via HTTP Graph Store Protocol (PUT) ───────────────────────────
function Load-Graph {
    param(
        [string]$File,
        [string]$Graph,
        [string]$Label
    )

    $url     = "$FusekiUrl/$Dataset/data?graph=$Graph"
    $creds   = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("admin:$AdminPassword"))
    $headers = @{
        "Content-Type"  = "application/rdf+xml"
        "Authorization" = "Basic $creds"
    }
    $size = [math]::Round((Get-Item $File).Length / 1MB, 1)

    Write-Host "[loader] Chargement $Label → $Graph"
    Write-Host "[loader]   Fichier   : $File ($size Mo)"
    Write-Host "[loader]   Endpoint  : $url"

    $bytes = [System.IO.File]::ReadAllBytes($File)
    Invoke-RestMethod -Uri $url -Method Put -Headers $headers -Body $bytes -TimeoutSec 7200 | Out-Null

    Write-Host "[loader] $Label chargé."
}

Load-Graph -File $FileOld -Graph $GraphOld -Label "version 2025-10"
Load-Graph -File $FileNew -Graph $GraphNew -Label "version 2026-01"

# ── Marqueur d'idempotence ────────────────────────────────────────────────────
New-Item -ItemType File -Path $Marker -Force | Out-Null
Write-Host "[loader] Chargement terminé. Marqueur créé : $Marker"
