# Five Sigma – BHSI Policy Search Integration Platform

> 📚 **Documentation Links:**
> - 🚀 **[Developer Setup Guide](setup.md)**: 5-minute setup, virtual environment, and daily commands.
> - 🧠 **[Architecture & Understanding Guide](Understand.md)**: Simplified walkthrough of the Policy Search API architecture.
> - 🤖 **[ChatGPT / LLM Handover Guide](undestand.md)**: Concise context, constraints, and confirmed models for AI coding assistants.

---

## 1. Project Overview

The **Five Sigma BHSI Integration Platform** is a streamlined FastAPI integration middleware connecting the Five Sigma Claims Management Platform with Policy Administration Systems (PAS).

### Current Scope: Policy Search API Only
- **Architecture:** `Five Sigma (FNOL) → FastAPI API → Policy Service → PolicySource Interface → MySQL Policy Repository → MySQL Database`.
- **Search Endpoint:** `GET /policies/search` (also mounted at `/api/v1/policies/search`).
- **Database Backend:** Relational storage using **MySQL 8.0+** and **SQLAlchemy 2.0 ORM** (tables: `policies`, `policy_contacts`, `contact_phones`, `retrieval_tokens`).
- **Authentication:** Inbound API key authentication via `X-API-Key` HTTP header.
- **PAS Independence:** The `PolicySource` interface ensures complete independence from the underlying database or future PAS adapters (such as Duck Creek or Socotra), allowing external systems to be replaced without changing the Five Sigma-facing API.

---

## 2. High-Level Architecture

```mermaid
flowchart TD
    A["Five Sigma (FNOL Caller)"] -->|"GET /policies/search (X-API-Key)"| B["FastAPI Application (app/main.py)"]
    B --> C["API Route (app/api/v1/policy.py)"]
    C --> D["Policy Service (app/services/policy_service.py)"]
    D --> E["PolicySource Interface (app/integrations/policy_system/source.py)"]
    E --> F["MySQL Policy Repository (app/repositories/policy_repository.py)"]
    F --> G["MySQL Database (policies, contacts, phones, tokens)"]

    H["Auth Dependency (app/core/auth.py)"] -.-> C
    I["Centralized Error Handlers (app/core/error_handlers.py)"] -.-> B
```

---

## 3. Project Directory Structure

```text
xc/
├── app/
│   ├── main.py                         # FastAPI application entry point
│   │
│   ├── api/
│   │   ├── router.py                   # Root API router
│   │   └── v1/
│   │       └── policy.py               # GET /policies/search route
│   │
│   ├── core/
│   │   ├── auth.py                     # Inbound API key authentication (X-API-Key)
│   │   ├── config.py                   # Pydantic Settings & environment variables
│   │   ├── error_handlers.py           # Centralized exception handlers
│   │   ├── exceptions.py               # Domain exceptions (AuthenticationError, DatabaseError)
│   │   ├── logger.py                   # Structured logging setup
│   │   └── middleware.py               # Correlation ID middleware
│   │
│   ├── data/
│   │   └── mock_data.py                # Approved mock policy records & display schema
│   │
│   ├── database/
│   │   ├── __init__.py                 # Database module exports
│   │   ├── connection.py               # SQLAlchemy engine & sessionmaker lifecycle
│   │   └── models.py                   # Normalized MySQL models (policies, contacts, phones, tokens)
│   │
│   ├── dependencies/
│   │   └── clients.py                  # FastAPI dependency injection providers
│   │
│   ├── integrations/
│   │   └── policy_system/
│   │       ├── __init__.py
│   │       └── source.py               # PolicySource abstract interface
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── policy_repository.py        # MySQLPolicyRepository implementation
│   │
│   ├── schemas/
│   │   ├── errors.py                   # Standard error response schemas
│   │   └── policy.py                   # Five Sigma v2 Policy Search models
│   │
│   └── services/
│       └── policy_service.py           # Decoupled PolicyService
│
├── docs/
│   ├── api_contracts/
│   │   └── policy.yaml                 # OpenAPI 3.0 specification for GET /policies/search
│   ├── architecture.md
│   └── integration_catalog.md
│
├── scripts/
│   ├── init_mysql_db.py                # Automated MySQL database initializer & mock seeder
│   ├── schema.sql                      # Pure MySQL 8.0 DDL migration script
│   ├── setup.ps1
│   └── setup.sh
│
├── tests/
│   ├── conftest.py                     # Pytest fixtures & isolated test database setup
│   ├── integration/
│   │   └── test_policy_api.py          # Integration tests for GET /policies/search
│   └── unit/
│       ├── test_policy.py              # Unit tests for PolicyService
│       └── test_policy_repository.py   # Unit tests for MySQLPolicyRepository
│
├── .env.example                         # Environment configuration template
├── pyproject.toml                       # Python project configuration (Ruff, MyPy, Pytest)
├── requirements.txt                     # Production dependencies (FastAPI, SQLAlchemy, PyMySQL)
├── README.md
├── Understand.md
└── undestand.md
```

---

## 4. Database Setup & Initialization

### 4.1 Prerequisites
- **MySQL 8.0+** running locally, on a server, or in Docker:
  ```bash
  docker run --name mysql-policy-db \
    -e MYSQL_ROOT_PASSWORD=rootpassword \
    -e MYSQL_DATABASE=policy_db \
    -e MYSQL_USER=policy_user \
    -e MYSQL_PASSWORD=password \
    -p 3306:3306 -d mysql:8.0
  ```

### 4.2 Automated Initialization & Mock Data Seeding
Run the provided CLI tool to create tables and seed approved mock policy records:
```bash
./.venv/bin/python scripts/init_mysql_db.py
```

### 4.3 Manual Schema Setup
Execute the MySQL DDL script directly:
```bash
mysql -u policy_user -p policy_db < scripts/schema.sql
```

---

## 5. Environment Configuration

Create a `.env` file from `.env.example`:

```bash
APP_NAME=BHSI Policy Search Integration
ENVIRONMENT=development

# Inbound API Key Authentication for Five Sigma
API_KEY=test-api-key
FIVE_SIGMA_INBOUND_API_KEY=test-five-sigma-key

# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=policy_db
MYSQL_USER=policy_user
MYSQL_PASSWORD=password
DATABASE_URL=mysql+pymysql://policy_user:password@localhost:3306/policy_db
```

---

## 6. Running the Application

Start the FastAPI application with Uvicorn:

```bash
./.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 7. Policy Search API Specification

### `GET /policies/search` (and `/api/v1/policies/search`)

- **Security:** `X-API-Key` header.
- **Required Query Parameters:**
  - `lob` *(string)*: Line of Business (exactly one, e.g. `GL`, `PROPERTY`, `EXCESS`).
  - `org_external_id` *(string)*: Organization external ID (e.g. `BHSI-ORG-01`).
- **Optional Query Parameters:**
  - `suborg_external_id` *(string)*: Sub-organization external ID.
  - *Organization-Configured Search Parameters:* Any additional filters (e.g. `policy_number`, `first_name`, `last_name`, `company_name`, `effective_date`).

#### Example Request:
```bash
curl -X GET "http://localhost:8000/policies/search?lob=GL&org_external_id=BHSI-ORG-01&policy_number=BHSI-GL-2024-001" \
  -H "X-API-Key: test-api-key"
```

#### Example Response (`HTTP 200 OK`):
```json
{
  "total_results": 1,
  "display_schema": [
    {"id": "policy_number", "desc": "Policy Number", "type": "string"},
    {"id": "policy_holder", "desc": "Policy Holder", "type": "string"},
    {"id": "effective_date", "desc": "Effective Date", "type": "date"},
    {"id": "expiration_date", "desc": "Expiration Date", "type": "date"},
    {"id": "lob", "desc": "Line of Business", "type": "string"}
  ],
  "results": [
    {
      "display_fields": {
        "policy_number": "BHSI-GL-2024-001",
        "policy_holder": "Acme Corporation",
        "effective_date": "2024-01-01",
        "expiration_date": "2025-01-01",
        "lob": "GL"
      },
      "retrieval_token": "9fyFmD8GCVo8VAE4-ZP_Kk4wLqtRbIGbuWc60JTTuHg"
    }
  ]
}
```

---

## 8. Quality Gates & Testing

Run all automated checks:

```bash
# Linting & code style
./.venv/bin/ruff check . --fix
./.venv/bin/ruff format .

# Strict static type analysis
./.venv/bin/mypy app tests scripts

# Unit and integration test suite
./.venv/bin/pytest
```
