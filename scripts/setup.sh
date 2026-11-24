#!/bin/bash
set -e

echo "===================================================="
echo "  Setting up BHSI Policy Integration Environment    "
echo "===================================================="

# 1. Create virtual environment if missing
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment (.venv)..."
    python3 -m venv .venv
fi

# 2. Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# 3. Install dependencies
echo "Upgrading pip and installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

# 4. Copy .env configuration if missing
if [ ! -f ".env" ]; then
    echo "Creating .env configuration from .env.example..."
    cp .env.example .env
fi

# 5. Database Setup (Create DB, Tables, Migrations, and Mock Seed Data)
echo ""
echo "----------------------------------------------------"
echo "  MySQL Database Setup & Migrations                 "
echo "----------------------------------------------------"

set +e
echo "Running database creation, table init, and mock seeding..."
python scripts/init_mysql_db.py
if [ $? -eq 0 ]; then
    echo "Applying Alembic migrations..."
    alembic upgrade head
    echo "Database created, tables initialized, and mock data seeded successfully!"
else
    echo "Notice: Could not automatically connect to MySQL to initialize the database."
    echo "Once your MySQL service is running, run:"
    echo "  python scripts/init_mysql_db.py"
    echo "  alembic upgrade head"
    echo "Or execute: mysql -u root -p < database/init.sql && mysql -u root -p < database/seed.sql"
fi
set -e

# 6. Install Git hooks
echo ""
echo "Installing pre-commit hooks..."
pre-commit install || true

echo "Running initial quality checks..."
pre-commit run --all-files || true

echo ""
echo "===================================================="
echo "  Setup completed successfully!                     "
echo "===================================================="
