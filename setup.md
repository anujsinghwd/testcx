# Developer Setup Guide

This document explains how to set up the Five Sigma – BHSI Integration project on a new developer machine.

**Primary OS:** Windows 10 / Windows 11
**Shell:** PowerShell
**Python:** 3.11+

The setup process installs dependencies, configures the Python virtual environment, installs Git hooks and enables automated code-quality checks.

---

# 1. Prerequisites

Install the following software before starting.

| Software | Requirement |
|---|---|
| Python | 3.11 or higher |
| Git | Latest stable version |
| VS Code | Recommended |
| PowerShell | Windows PowerShell 5.1+ or PowerShell 7+ |

### Verify installations

Open PowerShell and execute:

```powershell
py --version
git --version
```

Expected Python version:

```text
Python 3.11.x
```

If Python is not recognized, install Python and enable the option to add Python to PATH.

---

# 2. Clone the Repository

Open PowerShell and navigate to your development directory.

```powershell
cd C:\Projects
```

Clone the repository:

```powershell
git clone <repository-url>
```

Navigate into the project:

```powershell
cd xc
```

Replace `<repository-url>` with the actual repository URL.

---

# 3. Python Virtual Environment Setup

We use a virtual environment to isolate project dependencies from globally installed Python packages.

### Create virtual environment

```powershell
py -3.11 -m venv .venv
```

### Activate virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

This execution policy change applies only to the current PowerShell session.

### Verify activation

Your terminal should show:

```text
(.venv) PS C:\Projects\xc>
```

---

# 4. Install Project Dependencies

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install application dependencies:

```powershell
pip install -r requirements.txt
```

Install development dependencies:

```powershell
pip install -r requirements-dev.txt
```

Development dependencies include tools such as:

- Ruff
- MyPy
- Pytest
- Pytest Coverage
- Pre-commit
- Bandit
- pip-audit
- Detect Secrets
- Import Linter

---

# 5. Environment Configuration

Create your local environment file.

```powershell
Copy-Item .env.example .env
```

Update `.env` with the configuration values provided through the team's approved secure channel.

Example:

```env
APP_NAME=Five Sigma BHSI Integration
ENVIRONMENT=development

FIVE_SIGMA_BASE_URL=
FIVE_SIGMA_API_KEY=

POLICY_API_URL=
POLICY_API_KEY=
```

Important:

- Never commit `.env`.
- Never put API keys or passwords in source code.
- Use `.env.example` for variable names and safe placeholder values.
- Obtain credentials through the approved team process.

---

# 6. Configure Pre-commit Hooks

Pre-commit automatically runs configured quality checks before a Git commit is created.

The repository contains:

```text
.pre-commit-config.yaml
.secrets.baseline
```

These files should already be committed to Git.

### Install Git hooks

```powershell
pre-commit install
```

### Run all checks manually

```powershell
pre-commit run --all-files
```

### Checks configured in the project

| Check | Purpose |
|---|---|
| Trailing whitespace | Removes unnecessary spaces |
| End-of-file fixer | Ensures correct file endings |
| YAML validation | Checks YAML syntax |
| TOML validation | Checks TOML syntax |
| Merge conflict check | Detects unresolved merge markers |
| Ruff | Python linting |
| Ruff Format | Python formatting |
| Detect Secrets | Detects possible exposed credentials |

Additional MyPy and Pytest checks may also be configured as local hooks.

### Important

Do not regenerate `.secrets.baseline` automatically during every developer setup.

The baseline is a shared, reviewed file. If a new secret is detected, investigate it before updating the baseline.

---

# 7. Run Quality Checks Manually

The following commands can be used during development.

### Ruff linting

```powershell
ruff check .
```

Automatically fix supported issues:

```powershell
ruff check . --fix
```

### Ruff formatting

```powershell
ruff format .
```

Check formatting without modifying files:

```powershell
ruff format . --check
```

### MyPy type checking

```powershell
mypy app
```

### Run unit and integration tests

```powershell
pytest -v
```

### Run tests with coverage

```powershell
pytest --cov=app --cov-report=term-missing
```

### Security checks

```powershell
bandit -r app
pip-audit
```

### Architecture checks

```powershell
lint-imports
```

---

# 8. Running the FastAPI Application

Make sure the virtual environment is activated.

Start the development server:

```powershell
uvicorn app.main:app --reload
```

Application:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

Health endpoint:

```text
http://127.0.0.1:8000/health
```

Versioned health endpoint:

```text
http://127.0.0.1:8000/api/v1/health
```

---

# 9. Daily Developer Workflow

Follow this workflow during development.

### Step 1: Activate virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 2: Create or switch to your feature branch

```powershell
git checkout -b feature/policy-integration
```

### Step 3: Write code

Implement the required functionality.

### Step 4: Run tests

```powershell
pytest -v
```

### Step 5: Run quality checks

```powershell
pre-commit run --all-files
```

### Step 6: Stage changes

```powershell
git add .
```

### Step 7: Commit changes

```powershell
git commit -m "Add policy integration"
```

Pre-commit hooks automatically execute configured checks during the commit.

If a check fails:

1. Review the error.
2. Fix the issue.
3. Stage the updated files again.
4. Retry the commit.

### Step 8: Push your branch

```powershell
git push -u origin feature/policy-integration
```

### Step 9: Create a Pull Request

Create a PR against the target development branch.

GitHub Actions should run the mandatory CI checks before merging.

---

# 10. Common Windows Troubleshooting

### Issue 1: Python is not recognized

Error:

```text
py is not recognized
```

Solution:

- Install Python 3.11 or later.
- Enable Python PATH configuration.
- Restart PowerShell.
- Verify using `py --version`.

### Issue 2: PowerShell blocks activation

Error:

```text
running scripts is disabled on this system
```

Solution:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Issue 3: Pre-commit command not found

Solution:

```powershell
python -m pip install pre-commit
```

Then:

```powershell
pre-commit install
```

### Issue 4: Detect Secrets baseline missing

Error:

```text
Invalid path: .secrets.baseline
```

Check whether the file exists:

```powershell
Test-Path .secrets.baseline
```

If it does not exist, check with the repository maintainer before generating or replacing the shared baseline.

### Issue 5: Dependencies are inconsistent

Reinstall development dependencies:

```powershell
python -m pip install --upgrade -r requirements-dev.txt
```

### Issue 6: Tests fail because of environment configuration

Verify:

- `.env` exists.
- Required environment variables are configured.
- The correct Python virtual environment is active.
- Required external service credentials are available.

---

# 11. Windows Command Prompt Alternative

If using CMD instead of PowerShell:

Create the virtual environment:

```cmd
py -3.11 -m venv .venv
```

Activate:

```cmd
.venv\Scripts\activate.bat
```

Install dependencies:

```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Install hooks:

```cmd
pre-commit install
```

Run tests:

```cmd
pytest -v
```

---

# 12. macOS / Linux Setup

For developers using macOS or Linux:

Create the virtual environment:

```bash
python3 -m venv .venv
```

Activate:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Install Git hooks:

```bash
pre-commit install
```

Run checks:

```bash
pre-commit run --all-files
```

---

# 13. Git and Quality Rules

Every developer must follow these rules:

1. Always work on a feature branch.
2. Never commit `.env` or credentials.
3. Do not bypass pre-commit checks using `--no-verify`.
4. Fix linting and formatting issues before creating a PR.
5. Add unit tests for new business logic.
6. Run relevant tests before pushing.
7. Keep integration clients and business logic separated.
8. Follow the existing project architecture.
9. Update documentation when introducing new integrations.
10. Ensure mandatory GitHub Actions checks pass before merging.

---

# 14. Quick Setup Checklist

Use this checklist when onboarding a new developer.

- [ ] Python 3.11+ installed
- [ ] Git installed
- [ ] Repository cloned
- [ ] Project virtual environment created
- [ ] Virtual environment activated
- [ ] Runtime dependencies installed
- [ ] Development dependencies installed
- [ ] `.env` created and configured
- [ ] `.pre-commit-config.yaml` available
- [ ] `.secrets.baseline` available
- [ ] Git pre-commit hooks installed
- [ ] Initial quality checks passed
- [ ] Unit tests executed successfully
- [ ] FastAPI application starts successfully

---

## Final Note

The purpose of this setup process is to ensure every developer follows the same development standards, regardless of their operating system.

Windows developers should primarily use the PowerShell commands in this document.

Pre-commit provides local code-quality validation, while GitHub Actions provides centralized CI validation before code is merged.

**Every developer should complete this setup before starting development.**
