# Five Sigma – BHSI Integration Application: Policy Search Architecture

## 1. Project Overview

This platform functions as an integration middleware between **Five Sigma (Claims Management Platform)** and underlying Policy Administration Systems (PAS).

During First Notice of Loss (FNOL), Five Sigma queries this service to search for existing policy records.

### Simplified Architecture: Policy Search Only
```text
Five Sigma (FNOL)
       │
       ▼ [GET /policies/search | Header: X-API-Key]
FastAPI Application (app/main.py)
       │
       ▼
Policy Service (app/services/policy_service.py)
       │
       ▼
PolicySource Interface (app/integrations/policy_system/source.py)
       │
       ▼
MySQL Policy Repository (app/repositories/policy_repository.py)
       │
       ▼
MySQL Database (policies, contacts, phones, tokens)
```

---

## 2. Why the PolicySource Interface?

The **`PolicySource`** interface (`app/integrations/policy_system/source.py`) isolates `PolicyService` and the FastAPI route from the data storage mechanism:
- In Phase 1, `MySQLPolicyRepository` implements `PolicySource`.
- When Duck Creek or another PAS is integrated later, a new adapter class (e.g. `DuckCreekPolicySource`) implements the same `PolicySource` contract.
- The Five Sigma-facing API route, request parameters, and response schemas remain completely unchanged.

---

## 3. Database Schema

The relational schema in `app/database/models.py` matches the confirmed Five Sigma v2 contract:
- **`policies`**: Master policy records (LOB, organization, policy number, dates, holder reference ID).
- **`policy_contacts`**: Relational contacts (insured companies, individual claimants) linked to `policies.id` (`ON DELETE CASCADE`).
- **`contact_phones`**: Phone numbers linked to `policy_contacts.id` (`ON DELETE CASCADE`).
- **`retrieval_tokens`**: Opaque search tokens linked to `policies.external_id` (`ON DELETE CASCADE`).

---

## 4. Inbound Authentication

All requests to `GET /policies/search` require the `X-API-Key` header verified by `app/core/auth.py`. Missing or invalid keys return `HTTP 401 Unauthorized`.
