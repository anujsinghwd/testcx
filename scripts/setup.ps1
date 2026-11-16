
$ErrorActionPreference = "Stop"

Write-Host "Setting up development environment..."

# Create virtual environment if missing
if (-not (Test-Path ".venv")) {
    py -3.11 -m venv .venv
}

# Activate virtual environment
& .\.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

# Install Git hooks
pre-commit install

# Run initial checks
pre-commit run --all-files

Write-Host "Setup completed successfully!"
