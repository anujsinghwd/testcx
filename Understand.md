# Five Sigma – BHSI Integration Application

## 1. Project Overview

This application acts as an integration layer between **Five Sigma (Claims Management System)** and BHSI's external enterprise systems.

The main responsibility of this application is to connect different systems, exchange data, transform API requests and responses, and coordinate business workflows.

Instead of allowing Five Sigma and external systems to communicate directly with each other, this application provides a centralized integration layer.

### Main responsibilities

- Integrate Five Sigma APIs with BHSI systems.
- Retrieve policy information from the policy administration system.
- Transform external API responses into Five Sigma-compatible payloads.
- Handle claim-related integration workflows.
- Coordinate payment-related integrations.
- Handle document-related integrations where required.
- Centralize authentication, validation, logging and error handling.

> Note: The exact integration scope, API contracts and ownership of individual workflows must be confirmed with the architecture lead and BHSI.

---

## 2. High-Level Architecture

The application follows a layered, modular FastAPI architecture.

### Architecture flow

```text
                  External Systems
                         |
          +--------------+--------------+
          |              |              |
      Policy System  Payment System  Document System
          |              |              |
          +--------------+--------------+
                         |
                         v
              FastAPI Integration Layer
                         |
              +----------+----------+
              |                     |
          API Layer             Core Layer
              |                     |
              v                     |
         Service Layer <------------+
              |
       +------+-------+
       |      |       |
       v      v       v
    Mapper  Schema  Integration Clients
       |      |       |
       +------+-------+
              |
              v
          Five Sigma
              |
              v
        Claims Management
```

The diagram represents the intended integration-layer responsibilities. Actual request direction and system ownership depend on each integration contract.

---

## 3. Why Do We Need This Architecture?

Without a dedicated integration layer:

- Every external system may need its own direct integration with Five Sigma.
- Business logic can become mixed with API endpoint code.
- Request and response transformations become difficult to maintain.
- Authentication and error handling may get duplicated.
- Changes in external APIs can affect multiple parts of the application.

With this architecture:

- Each integration has a clear responsibility.
- Business logic remains separate from HTTP handling.
- Data transformation is centralized.
- External API communication is isolated.
- Testing becomes easier.
- New integrations can be added without unnecessarily changing existing modules.

The main goal is **maintainability, separation of concerns, and easier integration management**.

---

## 4. Application Folder Structure

```text
xc/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── router.py
│   │   └── v1/
│   │       ├── health.py
│   │       ├── policy.py
│   │       ├── claims.py
│   │       ├── payments.py
│   │       ├── documents.py
│   │       └── webhooks.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── logger.py
│   │   ├── exceptions.py
│   │   └── middleware.py
│   │
│   ├── dependencies/
│   │   └── clients.py
│   │
│   ├── integrations/
│   │   ├── five_sigma/
│   │   ├── policy_system/
│   │   ├── payment_provider/
│   │   └── document_system/
│   │
│   ├── mappers/
│   │   ├── policy_mapper.py
│   │   ├── claim_mapper.py
│   │   └── payment_mapper.py
│   │
│   ├── schemas/
│   │   ├── policy.py
│   │   ├── claim.py
│   │   ├── payment.py
│   │   └── document.py
│   │
│   ├── services/
│   │   ├── policy_service.py
│   │   ├── claim_service.py
│   │   ├── payment_service.py
│   │   └── document_service.py
│   │
│   └── utils/
│       └── validators.py
│
├── framework/
├── jobs/
├── tests/
├── docs/
├── .github/
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── Dockerfile
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

---

## 5. Understanding Each Layer

### 5.1 Main Application – `app/main.py`

This is the entry point of the FastAPI application.

Responsibilities:

- Create the FastAPI application.
- Load application configuration.
- Register API routers.
- Configure application-level middleware.
- Initialize application lifecycle events when needed.

Why?

We need one central entry point to initialize the application and connect all modules.

### 5.2 API Layer – `app/api/`

This layer exposes HTTP endpoints.

Examples:

- `/api/v1/policies`
- `/api/v1/claims`
- `/api/v1/payments`
- `/api/v1/documents`
- `/api/v1/webhooks`

Responsibilities:

- Receive incoming requests.
- Validate request data using schemas.
- Call the appropriate service.
- Return HTTP responses.

Why?

API controllers should not contain complex business logic or direct external API communication.

They should delegate work to services.

### 5.3 Core Layer – `app/core/`

Contains application-wide functionality.

| File | Responsibility |
|---|---|
| config.py | Environment configuration |
| security.py | Authentication and security utilities |
| logger.py | Centralized logging |
| exceptions.py | Common application exceptions |
| middleware.py | Request-level middleware |

Why?

These capabilities are shared across multiple modules. Keeping them centralized avoids duplication.

### 5.4 Dependencies – `app/dependencies/`

Contains reusable dependency injection components.

Examples:

- External API clients.
- Authentication dependencies.
- Shared service dependencies.
- Request-scoped dependencies where required.

Why?

We should not create a new HTTP client or repeat dependency initialization in every endpoint.

### 5.5 Integrations – `app/integrations/`

This layer communicates with external systems.

Examples:

- Five Sigma API client.
- BHSI policy system client.
- Payment provider client.
- Document system client.

Responsibilities:

- Make HTTP requests.
- Handle authentication with external systems.
- Apply timeouts.
- Handle external API errors.
- Parse external responses.

Why?

External API communication should be isolated from business logic.

If an external API changes, we should primarily update its integration client and related mapping rather than modifying the entire application.

### 5.6 Services – `app/services/`

This layer contains application business logic and coordinates workflows.

Examples:

- `policy_service.py`
- `claim_service.py`
- `payment_service.py`
- `document_service.py`

Responsibilities:

- Coordinate integration clients.
- Apply business rules defined for the integration.
- Call mappers.
- Handle workflow-level decisions.
- Return processed results to API endpoints.

Why?

Services act as the bridge between API endpoints and external integrations.

They keep controllers thin and make business logic easier to test.

### 5.7 Mappers – `app/mappers/`

Responsible for transforming data between different system formats.

Example:

```text
BHSI Policy API Response
          |
          v
     Policy Mapper
          |
          v
Five Sigma Policy Payload
```

Why?

Different systems may use different field names and data structures.

For example:

```json
{
  "policy_number": "POL-1001",
  "insured_name": "ABC Limited"
}
```

May need to be transformed into a Five Sigma-compatible structure.

Mapping should remain separate from API communication and business workflow logic.

### 5.8 Schemas – `app/schemas/`

Defines request and response data structures using Pydantic.

Responsibilities:

- Validate incoming requests.
- Define expected response structures.
- Enforce field types and constraints.
- Provide consistent API contracts.

Why?

Validation at system boundaries helps prevent invalid data from entering business workflows.

### 5.9 Jobs – `jobs/`

Contains background or scheduled tasks where asynchronous processing is required.

Examples:

- Payment reconciliation.
- Retry processing.
- Scheduled integration tasks.

Why?

Some operations should not block the original API request.

The actual scheduling mechanism and job ownership need to be confirmed before implementation.

### 5.10 Tests – `tests/`

Contains automated tests.

```text
tests/
├── unit/
├── integration/
├── fixtures/
└── conftest.py
```

- Unit tests validate individual functions and services.
- Integration tests validate interactions between application components and external systems.
- Fixtures provide reusable test data and dependencies.

Why?

Automated tests help detect regressions before code reaches review or production.

---

## 6. Example: Policy Lookup Request Flow

Consider a scenario where Five Sigma needs policy information from BHSI.

### Step-by-step flow

1. A request reaches the FastAPI policy endpoint.
2. The API layer validates the request.
3. The policy endpoint calls `policy_service.py`.
4. The policy service invokes the BHSI policy integration client.
5. The integration client calls the external policy API.
6. The external system returns policy information.
7. The policy mapper transforms the response into the required Five Sigma format.
8. The service returns the transformed response.
9. The API layer sends the response to its caller.

### Flow diagram

```text
Incoming Request
       |
       v
Policy API Endpoint
       |
       v
Request Validation
       |
       v
Policy Service
       |
       v
BHSI Policy Client
       |
       v
External Policy API
       |
       v
Policy Response
       |
       v
Policy Mapper
       |
       v
Five Sigma Compatible Payload
       |
       v
API Response
```

This separation makes it easier to test each step independently.

---

## 7. Why Separate Policy, Claims and Payments?

These are separate business capabilities.

### Policy

- Retrieve policy information.
- Validate policy details.
- Transform policy data for Five Sigma.

### Claims

- Handle claim-related integration requests.
- Transform claim information.
- Support agreed claim events and workflows.

### Payments

- Coordinate payment-related API operations.
- Handle payment requests and responses.
- Support retries or reconciliation where required.

### Documents

- Coordinate document-related integrations.
- Handle document metadata and transfer workflows where required.

Why separate them?

- Each module has its own business responsibility.
- Changes remain isolated.
- Unit tests are easier to organize.
- Multiple developers can work on different modules.
- Future integrations can be added independently.

---

## 8. Security and Reliability

Security and reliability should be implemented centrally wherever possible.

Important considerations:

- Environment-based configuration.
- Secrets stored outside source control.
- Authentication with external systems.
- Request validation.
- API timeouts.
- Consistent exception handling.
- Structured logging.
- Retry policies for eligible transient failures.
- Idempotency for operations where duplicate requests could cause problems.
- Avoid logging sensitive personal or policy information.

Retry behavior must be designed carefully, especially for payment operations.

---

## 9. Code Quality and CI/CD

The project uses automated quality checks to reduce manual review effort.

### Pre-commit checks

- Ruff linting.
- Ruff formatting.
- Trailing whitespace validation.
- Secret detection.

### CI checks

- MyPy type checking.
- Pytest.
- Test coverage.
- Bandit security scanning.
- Dependency vulnerability scanning.
- Architecture import checks.

Why?

Developers receive feedback before code is merged, allowing reviewers to focus more on design, business logic and integration correctness.

---

## 10. How to Explain This Architecture to the Team

You can explain it like this:

"Our application acts as middleware between Five Sigma and BHSI's external systems.

We have separated the application into different layers to keep responsibilities clear.

The API layer receives requests, the service layer coordinates business workflows, the integration layer communicates with external systems, and the mapper layer transforms data between different system formats.

Schemas validate incoming and outgoing data, while the core layer provides shared configuration, security, logging and exception handling.

We have separate modules for policy, claims, payments and documents because each represents a different integration capability.

This structure makes the application easier to maintain, test, extend and debug. If an external API changes, we can isolate most of that change within its integration client and mapper rather than affecting the entire application."

---

## 11. Architecture Decisions to Confirm

The following are questions for the architecture lead, not assumptions:

- Which system initiates each integration?
- Does Five Sigma own the end-to-end claim lifecycle, or does it hand off to another BHSI claims system?
- Which policy API and authentication mechanism are being used?
- What are the exact payment integration responsibilities?
- Are documents transferred directly or through an external document management system?
- Are webhooks required?
- Which operations need asynchronous jobs?
- What are the retry, idempotency and timeout requirements?
- What is the deployment and secrets-management approach?
- What are the actual API contracts and data-mapping rules?

---

## 12. Important Architecture Principle

The objective is not to create more folders or layers.

The objective is to give every component one clear responsibility:

- API = HTTP communication.
- Service = workflow coordination and business logic.
- Integration = external system communication.
- Mapper = data transformation.
- Schema = data validation.
- Core = shared application capabilities.
- Tests = automated quality validation.

**A good architecture makes it clear where new functionality belongs and minimizes the impact of future changes.**
