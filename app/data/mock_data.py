from typing import Any

POLICIES: list[dict[str, Any]] = [
    {
        "policyNumber": "POL12345",
        "customerId": "CUST001",
        "insuredName": "John Smith",
        "policyStatus": "Active",
        "effectiveDate": "2026-01-01",
        "expirationDate": "2026-12-31",
        "subOrganization": "ORGCA",
        "lineOfBusiness": "Auto",
        "vin": "VIN123456789",
    },
    {
        "policyNumber": "POL67890",
        "customerId": "CUST002",
        "insuredName": "David Johnson",
        "policyStatus": "Expired",
        "effectiveDate": "2025-01-01",
        "expirationDate": "2025-12-31",
        "subOrganization": "ORGCA",
        "lineOfBusiness": "Auto",
        "vin": "VIN67846666",
    },
]

POLICY_HOLDERS: list[dict[str, Any]] = [
    {
        "customerId": "CUST001",
        "firstName": "John",
        "lastName": "Smith",
        "email": "john.smith@test.com",
        "phoneNumber": "9999999999",
    },
    {
        "customerId": "CUST002",
        "firstName": "David",
        "lastName": "Johnson",
        "email": "david@test.com",
        "phoneNumber": "8888888888",
    },
]

POLICY_COVERAGES: dict[str, list[dict[str, Any]]] = {
    "POL12345": [
        {
            "coverageCode": "BI",
            "coverageName": "Bodily Injury",
            "limit": 100000,
        },
        {
            "coverageCode": "PD",
            "coverageName": "Property Damage",
            "limit": 50000,
        },
    ],
    "POL67890": [
        {
            "coverageCode": "COMP",
            "coverageName": "Comprehensive",
            "limit": 25000,
        },
    ],
}
