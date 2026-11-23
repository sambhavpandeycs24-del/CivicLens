param(
    [string]$OutputDir = "backups",
    [string]$ComposeFile = "docker-compose.yml"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$archive = Join-Path $OutputDir "civiclens-$timestamp.dump"

docker compose -f $ComposeFile exec -T db pg_dump -Fc -U "$env:POSTGRES_USER" "$env:POSTGRES_DB" > $archive
if ($LASTEXITCODE -ne 0) { throw "PostgreSQL backup failed" }
Write-Host "Created PostgreSQL backup: $archive"
