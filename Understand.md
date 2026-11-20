# Five Sigma – BHSI Integration Application

## 1. Project Overview

This application acts as an integration middleware between **Five Sigma (Claims Management System)**, BHSI's external enterprise systems, and Policy Administration Systems (PAS).

The primary responsibility of this platform is to:
- Connect distinct enterprise systems.
- Abstract communication with external policy systems using the **Adapter Pattern**.
- Transform data between external systems and canonical application models.
- Coordinate business workflows while keeping API handling, business logic, and provider communication strictly decoupled.

> **Current Implementation State:**
> The Policy Integration has been rebuilt using the **Adapter Pattern** with **Duck Creek** as the initial policy system.
> At this stage, only the **file structure, classes, method signatures, schemas, and API route definitions** are established. No business logic, data retrieval, or actual external HTTP calls are implemented yet.

---

## 2. High-Level Architecture & The Adapter Pattern

The platform is organized around a layered, modular architecture. For Policy Integration, it applies the **Adapter Pattern** to ensure provider independence.

### Architecture Flow

```text
               External Callers (Five Sigma / UI)
                               |
                               v
                     FastAPI Application
                               |
                 +-------------+-------------+
                 |                           |
             API Layer                  Core Layer
         (app/api/v1/policy.py)    (config, exceptions, logger)
                 |
                 v
           Service Layer
     (app/services/policy_service.py)
                 |
                 v
        Policy Adapter Base
 (app/integrations/policy_system/base.py)
                 |
        +--------+--------+
        |                 |
        v                 v
 Duck Creek Adapter  (Future PAS Adapter)
 (duck_creek/adapter.py)
        |
        v
Duck Creek System / Mock Data (TBC)
```

---

## 3. Why the Adapter Pattern for Policy Integration?

Without the Adapter Pattern:
- The Policy Service would directly depend on specific Duck Creek endpoints or Five Sigma mock data.
- Introducing a future PAS system (e.g., Socotra or another BHSI PAS) would force modifications across controllers, services, and schemas.
- Vendor-specific payload quirks would leak into business workflows.

With the Adapter Pattern:
- **`PolicyAdapterBase`** defines an abstract contract (`search_policy`, `get_policy`, `get_coverages`).
- **`PolicyService`** coordinates workflows by talking solely to `PolicyAdapterBase`. It is completely agnostic to whether the underlying provider is Duck Creek or another system.
- **`DuckCreekAdapter`** encapsulates Duck Creek-specific communication, authentication, and endpoint logic.
- **`PolicyAdapterRegistry`** enables dynamic discovery and registration of adapters.
- Adding a new PAS in the future only requires adding a new adapter in `app/integrations/policy_system/<provider>/` without modifying the core API or service layer.

---

## 4. Application Folder Structure

```text
xc/
├── app/
│   ├── main.py                          # Application entry point
│   │
│   ├── api/                             # API routing layer
│   │   ├── router.py                    # Root API router
│   │   └── v1/
│   │       ├── health.py                # Health endpoints
│   │       └── policy.py                # Policy API endpoint definitions
│   │
│   ├── core/                            # Shared core utilities
│   │   ├── config.py                    # Configuration settings (TBC fields)
│   │   ├── error_handlers.py            # Centralized exception handlers
│   │   ├── exceptions.py                # Standard error catalog exceptions
│   │   ├── logger.py                    # Structured logging
│   │   └── middleware.py                # Correlation ID middleware
│   │
│   ├── data/                            # Mock data structures
│   │   └── mock_data.py                 # Confirmed policy field mock structure (TBC values)
│   │
│   ├── dependencies/                    # Dependency injection
│   │   └── clients.py                   # Injected adapter and service providers
│   │
│   ├── integrations/                    # Integration adapters
│   │   ├── document_system/             # Document integration placeholder
│   │   └── policy_system/               # Policy system integration package
│   │       ├── base.py                  # PolicyAdapterBase abstract class
│   │       ├── config.py                # General policy system config loader
│   │       ├── registry.py              # PolicyAdapterRegistry
│   │       └── duck_creek/              # Duck Creek provider package
│   │           ├── adapter.py           # DuckCreekAdapter class (skeleton)
│   │           └── config.py            # DuckCreekConfigLoader (skeleton)
│   │
│   ├── mappers/                         # Data mapping layer
│   │   └── policy_mapper.py             # Skeleton mapper functions
│   │
│   ├── schemas/                         # Pydantic data models
│   │   ├── errors.py                    # Error response schemas
│   │   └── policy.py                    # Confirmed policy response schemas
│   │
│   └── services/                        # Business orchestration layer
│       └── policy_service.py            # Provider-independent PolicyService
│
├── docs/                                # Project documentation & API contracts
│   ├── architecture.md
│   ├── integration_catalog.md
│   └── api_contracts/
│       ├── claim.yaml
│       ├── payment.yaml
│       └── policy.yaml                  # OpenAPI 3.0 contract for Policy API
│
├── jobs/                                # Background schedulers
│   ├── payment_scheduler.py
│   └── retry_scheduler.py
│
├── tests/                               # Automated tests
│   ├── conftest.py                      # Shared fixtures
│   ├── integration/
│   │   └── test_policy_api.py           # API integration test skeletons
│   └── unit/
│       ├── test_claim.py
│       ├── test_health.py               # Active health check tests
│       ├── test_payment.py
│       └── test_policy.py               # Unit test skeletons
│
├── timer_function/                      # Azure Timer Function configuration
│   ├── function.json
│   └── __init__.py
│
├── function_app.py                      # Azure Functions trigger entry points
├── .env.example                         # Environment variable template
├── pyproject.toml                       # Python package & quality tool configuration
├── README.md
└── Understand.md
```

---

## 5. Layer Responsibilities in Detail

### 5.1 API Layer (`app/api/v1/policy.py`)
Exposes only the three confirmed policy endpoints:
- `POST /policies/search`: Search policies by criteria (TBC).
- `GET /policies/{id}`: Retrieve detailed policy information.
- `GET /policies/{id}/coverages`: Retrieve coverage details.

Controllers contain **no business logic** and only define routes and function signatures.

### 5.2 Service Layer (`app/services/policy_service.py`)
Provides `PolicyService` with methods:
- `search_policy(criteria: Any = None) -> Any`
- `get_policy(policy_id: str) -> Any`
- `get_coverages(policy_id: str) -> Any`

The service accepts a `PolicyAdapterBase` dependency. It contains **no Duck Creek-specific logic** and no transformations.

### 5.3 Integration Layer (`app/integrations/policy_system/`)
Contains the Adapter Pattern components:
- **`PolicyAdapterBase`** in `base.py`: Declares abstract async methods.
- **`PolicyAdapterRegistry`** in `registry.py`: Holds adapter classes.
- **`DuckCreekAdapter`** in `duck_creek/adapter.py`: Implements `PolicyAdapterBase` for Duck Creek with `raise NotImplementedError` / `pass`.
- **`DuckCreekConfigLoader`** in `duck_creek/config.py`: Loads connection settings (marked TBC).

### 5.4 Schema Layer (`app/schemas/policy.py`)
Declares `PolicyResponse` using **strictly confirmed reference fields**:
- Policy Number
- Effective Date
- Expiration Date
- Currency
- Policy State
- Policy Holder Company
- UW Region
- Writing Company
- Booked As Value
- Product Line/UW Area
- Product Line Subtype
- Section Code Name
- ASL
- Class Code (ISO)
- Subline (ISO)
- Deductible Codes (ISO)
- Primary Involved Location Detail (ISO)
- Document Information:
  - Coverage/Exposure (Coverage used instead of Line)
  - Limits, Retentions
  - Dates, Retro Tail

*No speculative canonical entities (such as separate PolicyVersion, Insured, Limit, Deductible, or SourceReference classes) are created.*

### 5.5 Core Layer (`app/core/`)
- `exceptions.py`: Defines the 5 standard error classes mapping to integration error codes:
  - `NOT_FOUND` -> `PolicyNotFoundError` (404)
  - `MULTIPLE_MATCHES` -> `MultiplePoliciesFoundError` (409)
  - `PAS_UNAVAILABLE` -> `PASUnavailableError` (503)
  - `TIMEOUT` -> `PASTimeoutError` (504)
  - `MAPPING_ERROR` -> `PolicyMappingError` (502)
- `config.py`: Declares Duck Creek environment parameters with `TBC` defaults.
- `error_handlers.py`, `logger.py`, `middleware.py`: Shared logging, correlation ID tracking, and centralized exception handling.

---

## 6. Current Implementation Rules & Boundaries

1. **Skeleton / Signatures Only:** Method and function bodies use `pass` or `raise NotImplementedError`.
2. **No HTTP Calls:** No external API requests to Duck Creek or any other PAS.
3. **No Business Logic:** No filtering, sorting, snapshot processing, or payload hashing.
4. **No Mock Logic:** `mock_data.py` contains only the data dictionary structure; no retrieval or filtering functions are implemented.
5. **No Invented Fields:** All unconfirmed field types, property casings, or API parameters are explicitly designated as **`TBC`**.

---

## 7. Next Steps in the Implementation Plan

Once Duck Creek API specifications, credentials, and contracts are confirmed:
1. Provide concrete configuration values in `.env` and `config.py`.
2. Populate `DuckCreekAdapter` with HTTP client calls using HTTPX.
3. Replace `TBC` types in `schemas/policy.py` with exact primitive and complex types.
4. Implement data transformation inside `mappers/policy_mapper.py` or adapter methods.
5. Implement unit and integration test scenarios in `tests/unit/test_policy.py` and `tests/integration/test_policy_api.py`.
