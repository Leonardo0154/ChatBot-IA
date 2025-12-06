param(
    [switch]$NoBackup
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$dataPath = Join-Path $repoRoot "data"

if (-not (Test-Path $dataPath)) {
    Write-Error "No se encontró la carpeta de datos en $dataPath"
    exit 1
}

if (-not $NoBackup) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupPath = Join-Path $repoRoot ("data-backup-" + $stamp)
    Copy-Item $dataPath $backupPath -Recurse -Force
    Write-Host "Backup creado en $backupPath"
}

$resetMap = @{
    "users.json" = "{}"
    "assignments.json" = "[]"
    "assignment_results.json" = "[]"
    "notes.json" = "[]"
}

foreach ($name in $resetMap.Keys) {
    $target = Join-Path $dataPath $name
    Set-Content -LiteralPath $target -Value $resetMap[$name] -Encoding UTF8
    Write-Host "Reiniciado $name"
}

$logFiles = @("logs/audit_logs.json", "logs/usage_logs.json")
foreach ($relative in $logFiles) {
    $target = Join-Path $dataPath $relative
    if (Test-Path $target) {
        Clear-Content -LiteralPath $target
        Write-Host "Vaciado $relative"
    }
}
