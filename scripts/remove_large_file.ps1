<#
PowerShell helper: Quita del índice un archivo grande trackeado, commitea y empuja.
Usar desde la raíz del repositorio (donde está .git).

Ejemplo:
  powershell -ExecutionPolicy Bypass -File .\scripts\remove_large_file.ps1

Parámetros opcionales:
  -RepoRoot : carpeta del repo (por defecto '.')
  -FilePath : ruta relativa al archivo grande (por defecto 'data/raw/ARASAAC_ES.zip')
  -Branch   : rama a empujar (por defecto 'main')
#>

param(
    [string]$RepoRoot = ".",
    [string]$FilePath = "data/raw/ARASAAC_ES.zip",
    [string]$Branch = "main"
)

Push-Location $RepoRoot
try {
    if (-not (Test-Path .git)) {
        Write-Error "No veo un repositorio git aquí. Ejecuta el script desde la raíz del repo o pasa -RepoRoot <ruta>."
        exit 1
    }

    Write-Host "Comprobando existencia del archivo local: $FilePath"
    if (-not (Test-Path $FilePath)) {
        Write-Warning "El archivo '$FilePath' no existe en el working tree local. Puede que ya no esté, o que esté sólo en commits previos."
        Write-Host "Listado de archivos rastreados que coinciden (si los hay):"
        git ls-files | Select-String -Pattern ([regex]::Escape($FilePath)) -SimpleMatch | ForEach-Object { Write-Host $_ }
        Write-Host "Si el archivo aparece en git ls-files, intenta correr 'git rm --cached <ruta>' manualmente."
        Pop-Location
        exit 2
    }

    Write-Host "Ejecutando: git rm --cached '$FilePath'"
    git rm --cached -- "$FilePath"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "git rm falló (código $LASTEXITCODE). Comprueba permisos y que la ruta es correcta."
        Pop-Location
        exit $LASTEXITCODE
    }

    Write-Host "Creando commit que elimina el archivo del índice..."
    git commit -m "Remove large file $FilePath from repository"
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "git commit devolvió código $LASTEXITCODE. Puede que no hubiera cambios para commitear. Ejecuta 'git status' para verificar."
        Pop-Location
        exit $LASTEXITCODE
    }

    Write-Host "Intentando push a origin/$Branch..."
    git push origin $Branch
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "git push falló con código $LASTEXITCODE. Si el error indica archivos >100MB en la historia, debes reescribir la historia (git filter-repo/BFG) o migrar a Git LFS."
        Write-Host "Ver instrucciones en README o pide ayuda para reescribir la historia."
        Pop-Location
        exit $LASTEXITCODE
    }

    Write-Host "Operación completada: el archivo fue eliminado del índice, commiteado y push realizado."
    Pop-Location
    exit 0
}
finally {
    if (Test-Path -Path Variable:LASTEXITCODE) { }
}
