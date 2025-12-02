# Dependency Management Scripts for Windows/PowerShell
# Save this file and run: .\manage-deps.ps1 <command>

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host @"
Dependency Management Commands
==============================

Usage: .\manage-deps.ps1 <command>

Commands:
  install       Install production dependencies
  install-dev   Install all dependencies (production + development)
  compile       Compile requirements files from .in files
  upgrade       Upgrade all dependencies to latest compatible versions
  sync          Sync environment to match requirements exactly
  sync-prod     Sync to production only (removes dev packages)
  check         Check if requirements are up to date
  help          Show this help message

Examples:
  .\manage-deps.ps1 install-dev
  .\manage-deps.ps1 compile
  .\manage-deps.ps1 upgrade
"@
}

function Install-Prod {
    Write-Host "Installing production dependencies..." -ForegroundColor Green
    pip install -r requirements.txt
}

function Install-Dev {
    Write-Host "Installing all dependencies (production + development)..." -ForegroundColor Green
    pip install -r requirements.txt -r requirements-dev.txt
}

function Compile-Requirements {
    Write-Host "Compiling requirements files..." -ForegroundColor Green
    pip-compile requirements.in
    pip-compile requirements-dev.in -c requirements.txt
    Write-Host "Done! Review the changes in requirements.txt and requirements-dev.txt" -ForegroundColor Green
}

function Upgrade-Dependencies {
    Write-Host "Upgrading all dependencies to latest compatible versions..." -ForegroundColor Yellow
    pip-compile --upgrade requirements.in
    pip-compile --upgrade requirements-dev.in -c requirements.txt
    Write-Host "Done! Review the changes and test thoroughly." -ForegroundColor Green
}

function Sync-Environment {
    Write-Host "Syncing environment to match requirements..." -ForegroundColor Green
    pip-sync requirements.txt requirements-dev.txt
}

function Sync-Prod {
    Write-Host "Syncing environment to production requirements only..." -ForegroundColor Green
    pip-sync requirements.txt
}

function Check-Requirements {
    Write-Host "Checking if requirements are up to date..." -ForegroundColor Green
    pip-compile --dry-run requirements.in
    if ($LASTEXITCODE -eq 0) {
        pip-compile --dry-run requirements-dev.in -c requirements.txt
    }
    if ($LASTEXITCODE -eq 0) {
        Write-Host "All requirements are up to date!" -ForegroundColor Green
    } else {
        Write-Host "Requirements need to be recompiled. Run: .\manage-deps.ps1 compile" -ForegroundColor Yellow
    }
}

# Main command dispatcher
switch ($Command) {
    "install" { Install-Prod }
    "install-dev" { Install-Dev }
    "compile" { Compile-Requirements }
    "upgrade" { Upgrade-Dependencies }
    "sync" { Sync-Environment }
    "sync-prod" { Sync-Prod }
    "check" { Check-Requirements }
    "help" { Show-Help }
    default { 
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host ""
        Show-Help
    }
}
