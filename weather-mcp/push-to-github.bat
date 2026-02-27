@echo off
cd /d "%~dp0"

where git >nul 2>&1
if errorlevel 1 (
    echo Git not found in PATH. Please run these commands in Git Bash or a terminal where 'git' works.
    echo.
    echo Open Git Bash from Start menu, then run:
    echo   cd "%cd%"
    echo   git init
    echo   git add .
    echo   git commit -m "Initial commit: Python MCP Weather Server"
    echo   git branch -M main
    echo   git remote add origin https://github.com/ArchanaChetan07/Python-MCP-Weather-Server.git
    echo   git push -u origin main
    pause
    exit /b 1
)

echo [1/6] Initializing git...
if not exist .git git init

echo [2/6] Adding remote...
git remote remove origin 2>nul
git remote add origin https://github.com/ArchanaChetan07/Python-MCP-Weather-Server.git

echo [3/6] Adding all files...
git add .

echo [4/6] Committing...
git commit -m "Initial commit: Python MCP Weather Server" 2>nul || git commit -m "Update: Python MCP Weather Server"

echo [5/6] Setting branch to main...
git branch -M main

echo [6/6] Pushing to GitHub - you may be asked for username and password...
echo        Username: ArchanaChetan07
echo        Password: paste your Personal Access Token
echo.
git push -u origin main

if errorlevel 1 (
    echo.
    echo If the repo already has a README, run:
    echo   git pull origin main --allow-unrelated-histories
    echo   git push -u origin main
) else (
    echo.
    echo Done. https://github.com/ArchanaChetan07/Python-MCP-Weather-Server
)
pause
