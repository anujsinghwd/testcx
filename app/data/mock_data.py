"""Mock policy data adhering strictly to the Five Sigma v2 data contract.

Contains approved mock policy records and default display schema definitions.
"""

from typing import Any

from app.schemas.policy import PolicyApiDisplaySchemaField

# Standard Five Sigma v2 display schema for policy search
DEFAULT_DISPLAY_SCHEMA: list[PolicyApiDisplaySchemaField] = [
    PolicyApiDisplaySchemaField(
        id="policy_number",
        desc="Policy Number",
        type="string",
    ),
    PolicyApiDisplaySchemaField(
        id="policy_holder",
        desc="Policy Holder",
        type="string",
    ),
    PolicyApiDisplaySchemaField(
        id="effective_date",
        desc="Effective Date",
        type="date",
    ),
    PolicyApiDisplaySchemaField(
        id="expiration_date",
        desc="Expiration Date",
        type="date",
    ),
    PolicyApiDisplaySchemaField(
        id="lob",
        desc="Line of Business",
        type="string",
    ),
]

# Approved mock policy records for the Mock Policy Repository
APPROVED_MOCK_POLICIES: list[dict[str, Any]] = [
    {
        "version": 1,
        "external_id": "POL-BHSI-001",
        "policy_number": "BHSI-GL-2024-001",
        "effective_date": "2024-01-01",
        "expiration_date": "2025-01-01",
        "policy_holder_contact_ref_id": "CNT-001",
        "lob": "GL",
        "sub_organization_external_id": "BHSI-SUB-01",
        "is_claims_made": False,
        "org_external_id": "BHSI-ORG-01",
        "contacts": [
            {
                "ref_id": "CNT-001",
                "external_id": "CUST-001",
                "is_company": True,
                "company_name": "Acme Corporation",
                "first_name": None,
                "middle_name": None,
                "last_name": None,
                "phones": [
                    {
                        "phone_number": "+1-800-555-0100",
                        "phone_type": "work",
                    }
                ],
                "address1": "100 Financial Way",
                "address2": "Suite 500",
                "city": "Boston",
                "state": "MA",
                "zipcode": "02110",
                "country": "USA",
            }
        ],
    },
    {
        "version": 1,
        "external_id": "POL-BHSI-002",
        "policy_number": "BHSI-PROP-2024-002",
        "effective_date": "2024-03-15",
        "expiration_date": "2025-03-15",
        "policy_holder_contact_ref_id": "CNT-002",
        "lob": "PROPERTY",
        "sub_organization_external_id": None,
        "is_claims_made": False,
        "org_external_id": "BHSI-ORG-01",
        "contacts": [
            {
                "ref_id": "CNT-002",
                "external_id": "CUST-002",
                "is_company": False,
                "company_name": None,
                "first_name": "John",
                "middle_name": "A.",
                "last_name": "Doe",
                "phones": [
                    {
                        "phone_number": "+1-617-555-0199",
                        "phone_type": "mobile",
                    }
                ],
                "address1": "250 Summer St",
                "address2": None,
                "city": "Boston",
                "state": "MA",
                "zipcode": "02210",
                "country": "USA",
            }
        ],
    },
    {
        "version": 1,
        "external_id": "POL-BHSI-003",
        "policy_number": "BHSI-GL-2024-003",
        "effective_date": "2024-06-01",
        "expiration_date": "2025-06-01",
        "policy_holder_contact_ref_id": "CNT-003",
        "lob": "GL",
        "sub_organization_external_id": None,
        "is_claims_made": False,
        "org_external_id": "BHSI-ORG-01",
        "contacts": [
            {
                "ref_id": "CNT-003",
                "external_id": "CUST-003",
                "is_company": True,
                "company_name": "Apex Manufacturing LLC",
                "first_name": None,
                "middle_name": None,
                "last_name": None,
                "phones": [
                    {
                        "phone_number": "+1-212-555-0144",
                        "phone_type": "work",
                    }
                ],
                "address1": "450 Lexington Ave",
                "address2": "Floor 12",
                "city": "New York",
                "state": "NY",
                "zipcode": "10017",
                "country": "USA",
            }
        ],
    },
    {
        "version": 1,
        "external_id": "POL-BHSI-004",
        "policy_number": "BHSI-XS-2024-004",
        "effective_date": "2024-09-01",
        "expiration_date": "2025-09-01",
        "policy_holder_contact_ref_id": "CNT-004",
        "lob": "EXCESS",
        "sub_organization_external_id": "BHSI-SUB-02",
        "is_claims_made": True,
        "retroactive_date": "2023-09-01",
        "runoff_provision": "Standard Runoff",
        "org_external_id": "BHSI-ORG-02",
        "contacts": [
            {
                "ref_id": "CNT-004",
                "external_id": "CUST-004",
                "is_company": True,
                "company_name": "Global Logistics Inc",
                "first_name": None,
                "middle_name": None,
                "last_name": None,
                "phones": [
                    {
                        "phone_number": "+1-312-555-0188",
                        "phone_type": "work",
                    }
                ],
                "address1": "100 S Wacker Dr",
                "address2": None,
                "city": "Chicago",
                "state": "IL",
                "zipcode": "60606",
                "country": "USA",
            }
        ],
    },
]

# Legacy mock data structure kept for backwards compatibility
POLICY_MOCK_DATA: list[dict[str, Any]] = [
    {
        "Policy Number": "TBC",
        "Effective Date": "TBC",
        "Expiration Date": "TBC",
        "Currency": "TBC",
        "Policy State": "TBC",
        "Policy Holder Company": "TBC",
        "UW Region": "TBC",
        "Writing Company": "TBC",
        "Booked As Value": "TBC",
        "Product Line/UW Area": "TBC",
        "Product Line Subtype": "TBC",
        "Section Code Name": "TBC",
        "ASL": "TBC",
        "Class Code (ISO)": "TBC",
        "Subline (ISO)": "TBC",
        "Deductible Codes (ISO)": "TBC",
        "Primary Involved Location Detail (ISO)": "TBC",
        "Coverage/Exposure": "TBC",
        "Limits, Retentions": "TBC",
        "Dates, Retro Tail": "TBC",
    }
]
