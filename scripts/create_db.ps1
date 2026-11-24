<#
.SYNOPSIS
    Standalone PowerShell script to initialize the MySQL database, create tables,
    apply Alembic migrations, and seed approved mock policy records.

.DESCRIPTION
    1. Ensures the target MySQL database exists (creates `policy_integration` if missing).
    2. Creates required tables (`policies`, `policy_contacts`, `contact_phones`, `retrieval_tokens`).
    3. Applies all pending Alembic migrations.
    4. Seeds approved mock policy records.

.EXAMPLE
    .\scripts\create_db.ps1
    .\scripts\create_db.ps1 -SkipSeed
#>

[CmdletBinding()]
param(
    [switch]$SkipSeed = $false,
    [string]$DbUrl = ""
)

$ErrorActionPreference = "Stop"

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  MySQL Database Setup & Migration                  " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# Ensure virtual environment is activated if present
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment (.venv)..."
    & .\.venv\Scripts\Activate.ps1
}

# Ensure .env exists
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "Creating .env from .env.example..."
        Copy-Item ".env.example" ".env"
    }
}

$dbSuccess = $false

# -----------------------------------------------------------------------------
# Method 1: Python CLI & Alembic (Recommended - uses PyMySQL & SQLAlchemy)
# -----------------------------------------------------------------------------
try {
    Write-Host "Initializing database, tables, and mock data via Python..." -ForegroundColor Yellow
    
    $pythonCmd = "python scripts/init_mysql_db.py"
    if ($DbUrl) {
        $pythonCmd += " --db-url `"$DbUrl`""
    }
    if ($SkipSeed) {
        $pythonCmd += " --skip-seed"
    }
    
    Invoke-Expression $pythonCmd

    Write-Host "Applying Alembic migrations..." -ForegroundColor Yellow
    alembic upgrade head

    Write-Host "Database created, tables initialized, and migrations applied successfully!" -ForegroundColor Green
    $dbSuccess = $true
} catch {
    Write-Warning "Python initialization encountered an error: $_"
}

# -----------------------------------------------------------------------------
# Method 2: Fallback to MySQL CLI (database/init.sql & database/seed.sql)
# -----------------------------------------------------------------------------
if (-not $dbSuccess) {
    if (Get-Command mysql -ErrorAction SilentlyContinue) {
        Write-Host "Attempting setup using native mysql CLI with database/init.sql..." -ForegroundColor Yellow
        try {
            Get-Content "database/init.sql" | mysql -u root
            if (-not $SkipSeed) {
                Get-Content "database/seed.sql" | mysql -u root
            }
            Write-Host "Database initialized and seeded via mysql CLI!" -ForegroundColor Green
            $dbSuccess = $true
        } catch {
            Write-Warning "mysql CLI execution failed: $_"
        }
    }
}

# -----------------------------------------------------------------------------
# Guidance if neither succeeded
# -----------------------------------------------------------------------------
if (-not $dbSuccess) {
    Write-Host ""
    Write-Host "----------------------------------------------------" -ForegroundColor DarkYellow
    Write-Host "  Could not connect to MySQL server.                " -ForegroundColor DarkYellow
    Write-Host "  Please ensure MySQL is running:                   " -ForegroundColor DarkYellow
    Write-Host "    1. Start MySQL service (e.g. net start MySQL80) " -ForegroundColor Cyan
    Write-Host "    2. Verify credentials in .env                   " -ForegroundColor Cyan
    Write-Host "    3. Re-run: .\scripts\create_db.ps1              " -ForegroundColor Cyan
    Write-Host "----------------------------------------------------" -ForegroundColor DarkYellow
    exit 1
} else {
    Write-Host "Database setup completed successfully!" -ForegroundColor Green
}

