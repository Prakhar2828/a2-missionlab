$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "A2 MissionLab — validating final public experience..." -ForegroundColor Cyan
python scripts\validate_public_experience.py
if ($LASTEXITCODE -ne 0) {
    throw "A2 MissionLab validation failed. Fix the reported issue(s) before running the site."
}

Write-Host ""
Write-Host "Validation passed." -ForegroundColor Green
Write-Host "Starting local server at http://localhost:8000/" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor DarkGray
python -m http.server 8000
