# BHSI Integration Platform – Integration Catalog

This catalog documents the enterprise integrations supported by the **BHSI Integration Platform**, detailing system ownership, protocols, message formats, adapter patterns, and integration status.

---

## Catalog Summary

| ID | Integration Name | Source System | Target System | Pattern / Protocol | Current Status |
|---|---|---|---|---|---|
| **INT-01** | Policy Lookup & Coverages | External Caller / Five Sigma | Duck Creek (Initial PAS) | Adapter Pattern / REST | **Structure & Signatures (TBC)** |
| **INT-02** | Claims Management | Five Sigma CMS | BHSI Enterprise Systems | REST / Event-driven | Planned |
| **INT-03** | Payments Processing | Five Sigma CMS | Payment Provider / Bank | REST / Asynchronous Batch | Planned (`jobs/payment_scheduler.py`) |
| **INT-04** | Document Management | Five Sigma CMS | Document System | REST / Multipart | Planned (`integrations/document_system/`) |
| **INT-05** | Webhooks & Claim Events | Five Sigma CMS | BHSI Integration Platform | Inbound Webhook / HMAC | Planned |

---

## 1. INT-01: Policy Lookup & Coverage Retrieval

### 1.1 Overview
Enables real-time retrieval of policy information, coverage details, and policy status from the Policy Administration System (PAS) for First Notice of Loss (FNOL) and claims handling.

### 1.2 Architectural Pattern
- **Pattern:** **Adapter Pattern**
- **Abstract Interface:** `PolicyAdapterBase` (`app/integrations/policy_system/base.py`)
- **Initial Implementation:** `DuckCreekAdapter` (`app/integrations/policy_system/duck_creek/adapter.py`)
- **Registry:** `PolicyAdapterRegistry` (`app/integrations/policy_system/registry.py`)
- **Service:** `PolicyService` (`app/services/policy_service.py`)

### 1.3 Exposed Endpoints
| HTTP Method | Route | Description | Response Schema |
|---|---|---|---|
| `POST` | `/policies/search` | Search policies by criteria | `PolicySearchResponse` (TBC) |
| `GET` | `/policies/{id}` | Retrieve comprehensive policy details | `PolicyResponse` |
| `GET` | `/policies/{id}/coverages` | Retrieve coverage information | `CoverageResponse` |

### 1.4 Confirmed Policy Response Fields
The policy response schema (`PolicyResponse` in `app/schemas/policy.py`) strictly uses the confirmed fields:

```text
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
  - Coverage/Exposure
  - Limits, Retentions
  - Dates, Retro Tail
```
*(All primitive types and exact JSON property names are marked `TBC` pending final interface specifications).*

### 1.5 Standardized Error Codes
- `NOT_FOUND` (HTTP 404): Policy or coverage does not exist.
- `MULTIPLE_MATCHES` (HTTP 409): Multiple records match criteria where unique policy required.
- `MAPPING_ERROR` (HTTP 502): External PAS payload cannot be transformed into canonical schema.
- `PAS_UNAVAILABLE` (HTTP 503): Duck Creek PAS is down or unreachable.
- `TIMEOUT` (HTTP 504): Duck Creek PAS request timed out.

---

## 2. INT-02: Claims Management Integration

### 2.1 Overview
Connects Five Sigma Claims Management System (CMS) with BHSI enterprise claim processing, reserve setting, and claim settlement systems.

### 2.2 Participating Systems
- **Originating System:** Five Sigma CMS
- **Middleware:** BHSI Integration Application
- **Enterprise Systems:** BHSI General Ledger, Core Claim Archives

### 2.3 Operations (Planned)
- Claim Creation & Assignment.
- Reserve Adjustments & Financial Tracking.
- Claim Closure & Reopening Handlers.
- Audit & History Synchronization.

---

## 3. INT-03: Payments & Financial Settlements

### 3.1 Overview
Handles claim payment processing, payee verification, bank integration, and payment status polling.

### 3.2 Participating Systems
- **Originating System:** Five Sigma CMS
- **Middleware:** BHSI Integration Platform
- **Target System:** Payment Provider / Banking Network

### 3.3 Operations & Background Jobs
- **Payment Initiation:** Synchronous API request to submit payment instructions.
- **Payment Status Reconciliation:** Asynchronous polling job (`jobs/payment_scheduler.py`) to verify clearing and settlement.
- **Idempotency:** Unique idempotency key enforcement per payment instruction.

---

## 4. INT-04: Document Management

### 4.1 Overview
Integrates policy documents, FNOL loss reports, damage photos, and legal correspondence between Five Sigma and BHSI's enterprise document repositories.

### 4.2 Participating Systems
- **Originating System:** Five Sigma CMS
- **Target System:** BHSI Document Management System (`app/integrations/document_system/`)

### 4.3 Operations (Planned)
- Document Upload & Attachment to Claim Records.
- Document Metadata Synchronization.
- Document Content Retrieval.

---

## 5. INT-05: Webhooks & Event Ingestion

### 5.1 Overview
Receives real-time asynchronous event notifications from Five Sigma for claim milestones, policy updates, and reserve approvals.

### 5.2 Key Requirements
- **Authentication:** HMAC signature verification on inbound webhooks.
- **Idempotency:** Event ID deduplication to prevent duplicate processing.
- **Delivery Strategy:** Immediate HTTP 200/202 acknowledgment with background event processing.

