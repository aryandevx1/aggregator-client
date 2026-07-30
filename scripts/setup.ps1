$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$VirtualEnvironment = Join-Path $ProjectRoot ".venv"
$Python = Join-Path $VirtualEnvironment "Scripts\python.exe"

Write-Host "Setting up aggregator-client..."

if (-not (Test-Path $VirtualEnvironment)) {
    Write-Host "Creating virtual environment..."
    python -m venv $VirtualEnvironment

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the virtual environment."
    }
}

Write-Host "Installing dependencies..."
& $Python -m pip install --upgrade pip

if ($LASTEXITCODE -ne 0) {
    throw "Failed to upgrade pip."
}

& $Python -m pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    throw "Failed to install project dependencies."
}

Write-Host "Configuring Git hooks..."
git config core.hooksPath .githooks

if ($LASTEXITCODE -ne 0) {
    throw "Failed to configure Git hooks."
}

Write-Host "Running tests..."
& $Python -m pytest

if ($LASTEXITCODE -ne 0) {
    throw "Tests failed."
}

Write-Host ""
Write-Host "Setup complete."
Write-Host "Activate the environment using:"
Write-Host "  .\.venv\Scripts\Activate.ps1"