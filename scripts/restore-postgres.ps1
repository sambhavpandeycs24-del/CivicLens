param(
    [Parameter(Mandatory = $true)][string]$BackupFile,
    [string]$ComposeFile = "docker-compose.yml"
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path $BackupFile)) { throw "Backup file does not exist: $BackupFile" }
Write-Warning "This restores into the selected PostgreSQL service. Verify the target first."
docker compose -f $ComposeFile exec -T db pg_restore --clean --if-exists -U "$env:POSTGRES_USER" -d "$env:POSTGRES_DB" < $BackupFile
if ($LASTEXITCODE -ne 0) { throw "PostgreSQL restore failed" }
Write-Host "PostgreSQL restore completed"
