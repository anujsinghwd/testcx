$ErrorActionPreference = "Stop"

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  Setting up BHSI Policy Integration Environment    " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# 1. Create virtual environment if missing
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment (.venv)..."
    py -3.11 -m venv .venv
}

# 2. Activate virtual environment
Write-Host "Activating virtual environment..."
& .\.venv\Scripts\Activate.ps1

# 3. Install dependencies
Write-Host "Upgrading pip and installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

# 4. Copy .env configuration if missing
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env configuration from .env.example..."
    Copy-Item ".env.example" ".env"
}

# 5. Database Setup (Create DB, Tables, Migrations, and Mock Seed Data)
Write-Host ""
Write-Host "----------------------------------------------------" -ForegroundColor Yellow
Write-Host "  MySQL Database Setup & Migrations                 " -ForegroundColor Yellow
Write-Host "----------------------------------------------------" -ForegroundColor Yellow

$dbSetupSuccess = $false

# Method A: Try python scripts/init_mysql_db.py and alembic
try {
    Write-Host "Running database creation, table init, and mock seeding..."
    python scripts/init_mysql_db.py
    Write-Host "Applying Alembic migrations..."
    alembic upgrade head
    Write-Host "Database created, tables initialized, and mock data seeded successfully!" -ForegroundColor Green
    $dbSetupSuccess = $true
} catch {
    Write-Warning "Python database initialization failed or MySQL server is not currently reachable: $_"
}

# Method B: Fallback to mysql CLI if available
if (-not $dbSetupSuccess) {
    if (Get-Command mysql -ErrorAction SilentlyContinue) {
        try {
            Write-Host "Attempting database setup using native mysql CLI..."
            Get-Content "database/init.sql" | mysql -u root
            Get-Content "database/seed.sql" | mysql -u root
            Write-Host "Database created and seeded via mysql CLI!" -ForegroundColor Green
            $dbSetupSuccess = $true
        } catch {
            Write-Warning "mysql CLI execution failed: $_"
        }
    }
}

if (-not $dbSetupSuccess) {
    Write-Host ""
    Write-Host "----------------------------------------------------" -ForegroundColor DarkYellow
    Write-Host "  NOTE: MySQL database could not be initialized now." -ForegroundColor DarkYellow
    Write-Host "  Once your MySQL server is running, you can run:   " -ForegroundColor DarkYellow
    Write-Host "    .\scripts\create_db.ps1                         " -ForegroundColor Cyan
    Write-Host "    or: python scripts/init_mysql_db.py             " -ForegroundColor Cyan
    Write-Host "----------------------------------------------------" -ForegroundColor DarkYellow
    Write-Host ""
}

# 6. Install Git hooks
Write-Host "Installing pre-commit hooks..."
try {
    pre-commit install
    Write-Host "Running initial pre-commit checks..."
    pre-commit run --all-files
} catch {
    Write-Warning "Pre-commit check warning: $_"
}

Write-Host ""
Write-Host "====================================================" -ForegroundColor Green
Write-Host "  Setup completed successfully!                     " -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green
