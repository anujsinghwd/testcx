# Project Context & Architecture Handover: Policy Search API

> **Target Audience:** ChatGPT / AI Coding Assistants  
> **Repository:** `xc` (Five Sigma – BHSI Integration Middleware)  
> **Current Focus:** Policy Search API Only (`GET /policies/search`)  
> **Database:** MySQL 8.0+ / SQLAlchemy 2.0  

---

## 1. Executive Context & Scope

The application provides a clean integration layer between **Five Sigma** and underlying policy systems during FNOL:
- **Active Endpoint:** `GET /policies/search` (and `/api/v1/policies/search`).
- **Core Architecture:** `Five Sigma → FastAPI → PolicyService → PolicySource Interface → MySQLPolicyRepository → MySQL Database`.
- **Inbound Security:** `X-API-Key` header verified against environment configuration (`API_KEY`).
- **Decoupled Design:** All data access is abstracted behind `PolicySource(ABC)`. Duck Creek or any other future PAS can replace MySQL simply by implementing `PolicySource` without modifying API routes or services.

---

## 2. Confirmed Models & Schemas (`app/schemas/policy.py`)

- **`PolicyApiSearchResponse`**:
  - `total_results`: `int`
  - `display_schema`: `list[PolicyApiDisplaySchemaField]` (`id`, `desc`, `type`)
  - `results`: `list[PolicyApiSearchResult]` (`display_fields`, `retrieval_token`)
- **`PolicyApiPolicy`**, **`PolicyApiContact`**, **`PolicyApiPhone`**:
  - Used for storing and validating mock policy records in MySQL and calculating `display_fields`.

---

## 3. Database Schema (`app/database/models.py`)

- `policies` (primary key `id`, unique `external_id`, indexed on `lob`, `org_external_id`, `policy_number`).
- `policy_contacts` (primary key `id`, foreign key `policies.id` ON DELETE CASCADE).
- `contact_phones` (primary key `id`, foreign key `policy_contacts.id` ON DELETE CASCADE).
- `retrieval_tokens` (primary key `id`, unique `token`, foreign key `policies.external_id` ON DELETE CASCADE).

---

## 4. Quality Gates

- `ruff check . --fix`
- `ruff format .`
- `mypy app tests scripts`
- `pytest`
