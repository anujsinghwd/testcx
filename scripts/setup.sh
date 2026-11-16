
#!/bin/bash
set -e

echo "Setting up development environment..."

# Create virtual environment if missing
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate

# Install dependencies
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

# Install Git hooks
pre-commit install

echo "Running initial quality checks..."
pre-commit run --all-files

echo "Setup completed successfully!"
