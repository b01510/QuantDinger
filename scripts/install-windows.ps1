$ErrorActionPreference = "Stop"

Write-Host "QuantDinger personal installer" -ForegroundColor Cyan
Write-Host "Checking Docker..."

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is not installed or not available in PATH. Install Docker Desktop first."
}

$compose = docker compose version 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose v2 is required."
}

Write-Host "Docker detected: $compose" -ForegroundColor Green
Write-Host "Running official QuantDinger installer..." -ForegroundColor Yellow

irm https://raw.githubusercontent.com/OpenByteInc/QuantDinger/main/install.ps1 | iex

Write-Host ""
Write-Host "Installation command completed." -ForegroundColor Green
Write-Host "Web:       http://127.0.0.1:8888"
Write-Host "Mobile H5: http://127.0.0.1:8889"
Write-Host "API:       http://127.0.0.1:5000/api/health"
