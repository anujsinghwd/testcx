-- =============================================================================
-- MySQL Database Mock Data Seed Script: policy_integration
-- Seeds approved mock policy records and associated contacts and phone records
-- =============================================================================

USE policy_integration;

-- Clean existing mock data safely (cascading deletes clean contacts and phones)
DELETE FROM policies WHERE external_id IN (
    'POL-BHSI-001',
    'POL-BHSI-002',
    'POL-BHSI-003',
    'POL-BHSI-004'
);

-- -----------------------------------------------------------------------------
-- 1. Insert Approved Policy Records
-- -----------------------------------------------------------------------------
INSERT INTO policies (
    version,
    external_id,
    policy_number,
    lob,
    org_external_id,
    sub_organization_external_id,
    effective_date,
    expiration_date,
    policy_holder_contact_ref_id,
    retroactive_date,
    is_claims_made,
    runoff_provision
) VALUES
(
    1,
    'POL-BHSI-001',
    'BHSI-GL-2024-001',
    'GL',
    'BHSI-ORG-01',
    'BHSI-SUB-01',
    '2024-01-01',
    '2025-01-01',
    'CNT-001',
    NULL,
    0,
    NULL
),
(
    1,
    'POL-BHSI-002',
    'BHSI-PROP-2024-002',
    'PROPERTY',
    'BHSI-ORG-01',
    NULL,
    '2024-03-15',
    '2025-03-15',
    'CNT-002',
    NULL,
    0,
    NULL
),
(
    1,
    'POL-BHSI-003',
    'BHSI-GL-2024-003',
    'GL',
    'BHSI-ORG-01',
    NULL,
    '2024-06-01',
    '2025-06-01',
    'CNT-003',
    NULL,
    0,
    NULL
),
(
    1,
    'POL-BHSI-004',
    'BHSI-XS-2024-004',
    'EXCESS',
    'BHSI-ORG-02',
    'BHSI-SUB-02',
    '2024-09-01',
    '2025-09-01',
    'CNT-004',
    '2023-09-01',
    1,
    'Standard Runoff'
);

-- -----------------------------------------------------------------------------
-- 2. Insert Associated Contacts
-- -----------------------------------------------------------------------------
-- Contact for POL-BHSI-001 (Acme Corporation)
INSERT INTO policy_contacts (
    policy_id, ref_id, external_id, is_company, company_name, first_name, middle_name, last_name, address1, address2, city, state, zipcode, country
)
SELECT id, 'CNT-001', 'CUST-001', 1, 'Acme Corporation', NULL, NULL, NULL, '100 Financial Way', 'Suite 500', 'Boston', 'MA', '02110', 'USA'
FROM policies WHERE external_id = 'POL-BHSI-001';

-- Contact for POL-BHSI-002 (John Doe)
INSERT INTO policy_contacts (
    policy_id, ref_id, external_id, is_company, company_name, first_name, middle_name, last_name, address1, address2, city, state, zipcode, country
)
SELECT id, 'CNT-002', 'CUST-002', 0, NULL, 'John', 'A.', 'Doe', '250 Summer St', NULL, 'Boston', 'MA', '02210', 'USA'
FROM policies WHERE external_id = 'POL-BHSI-002';

-- Contact for POL-BHSI-003 (Apex Manufacturing LLC)
INSERT INTO policy_contacts (
    policy_id, ref_id, external_id, is_company, company_name, first_name, middle_name, last_name, address1, address2, city, state, zipcode, country
)
SELECT id, 'CNT-003', 'CUST-003', 1, 'Apex Manufacturing LLC', NULL, NULL, NULL, '450 Lexington Ave', 'Floor 12', 'New York', 'NY', '10017', 'USA'
FROM policies WHERE external_id = 'POL-BHSI-003';

-- Contact for POL-BHSI-004 (Global Logistics Inc)
INSERT INTO policy_contacts (
    policy_id, ref_id, external_id, is_company, company_name, first_name, middle_name, last_name, address1, address2, city, state, zipcode, country
)
SELECT id, 'CNT-004', 'CUST-004', 1, 'Global Logistics Inc', NULL, NULL, NULL, '100 S Wacker Dr', NULL, 'Chicago', 'IL', '60606', 'USA'
FROM policies WHERE external_id = 'POL-BHSI-004';

-- -----------------------------------------------------------------------------
-- 3. Insert Associated Phone Numbers
-- -----------------------------------------------------------------------------
-- Phone for Acme Corporation (CNT-001)
INSERT INTO contact_phones (contact_id, phone_number, phone_type)
SELECT pc.id, '+1-800-555-0100', 'work'
FROM policy_contacts pc
JOIN policies p ON pc.policy_id = p.id
WHERE pc.ref_id = 'CNT-001' AND p.external_id = 'POL-BHSI-001';

-- Phone for John Doe (CNT-002)
INSERT INTO contact_phones (contact_id, phone_number, phone_type)
SELECT pc.id, '+1-617-555-0199', 'mobile'
FROM policy_contacts pc
JOIN policies p ON pc.policy_id = p.id
WHERE pc.ref_id = 'CNT-002' AND p.external_id = 'POL-BHSI-002';

-- Phone for Apex Manufacturing LLC (CNT-003)
INSERT INTO contact_phones (contact_id, phone_number, phone_type)
SELECT pc.id, '+1-212-555-0144', 'work'
FROM policy_contacts pc
JOIN policies p ON pc.policy_id = p.id
WHERE pc.ref_id = 'CNT-003' AND p.external_id = 'POL-BHSI-003';

-- Phone for Global Logistics Inc (CNT-004)
INSERT INTO contact_phones (contact_id, phone_number, phone_type)
SELECT pc.id, '+1-312-555-0188', 'work'
FROM policy_contacts pc
JOIN policies p ON pc.policy_id = p.id
WHERE pc.ref_id = 'CNT-004' AND p.external_id = 'POL-BHSI-004';
