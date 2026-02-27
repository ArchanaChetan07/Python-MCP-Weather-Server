# Run this in PowerShell from this folder (weather-mcp\weather-mcp)
# Or: right-click -> Open in Terminal, then: .\connect-to-github.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Initializing git (if needed)..." -ForegroundColor Cyan
if (-not (Test-Path .git)) { git init }

Write-Host "Adding remote (will replace if already set)..." -ForegroundColor Cyan
git remote remove origin 2>$null
git remote add origin https://github.com/ArchanaChetan07/Python-MCP-Weather-Server.git

Write-Host "Adding all files and committing..." -ForegroundColor Cyan
git add .
git status
git commit -m "Initial commit: Python MCP Weather Server" 2>$null
if ($LASTEXITCODE -ne 0) { git commit -m "Update: Python MCP Weather Server" }

Write-Host "Setting branch to main and pushing..." -ForegroundColor Cyan
git branch -M main
git push -u origin main

Write-Host "Done. Repo: https://github.com/ArchanaChetan07/Python-MCP-Weather-Server" -ForegroundColor Green
