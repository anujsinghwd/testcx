-- =============================================================================
-- MySQL Database Initialization Script: policy_integration
-- Policy Integration Service - Policy Search Mock Repository
-- =============================================================================

-- 1. Create Database if not exists
CREATE DATABASE IF NOT EXISTS policy_integration
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE policy_integration;

-- 2. Policies Table
-- Stores core policy details adhering to the Five Sigma v2 PolicyApiPolicy schema
CREATE TABLE IF NOT EXISTS policies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    version INT NOT NULL DEFAULT 1,
    external_id VARCHAR(64) NOT NULL,
    policy_number VARCHAR(64) NOT NULL,
    lob VARCHAR(32) NOT NULL,
    org_external_id VARCHAR(64) NOT NULL,
    sub_organization_external_id VARCHAR(64) NULL,
    effective_date VARCHAR(32) NOT NULL,
    expiration_date VARCHAR(32) NOT NULL,
    policy_holder_contact_ref_id VARCHAR(64) NOT NULL,
    retroactive_date VARCHAR(32) NULL,
    cancelled_date VARCHAR(32) NULL,
    effective_time VARCHAR(32) NULL,
    expiration_time VARCHAR(32) NULL,
    cancelled_time VARCHAR(32) NULL,
    retroactive_time VARCHAR(32) NULL,
    is_claims_made BOOLEAN NULL,
    runoff_provision VARCHAR(255) NULL,
    extra_data TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uq_policies_external_id UNIQUE (external_id),
    INDEX idx_policies_policy_number (policy_number),
    INDEX idx_policies_lob (lob),
    INDEX idx_policies_org_external_id (org_external_id),
    INDEX idx_policies_suborg (sub_organization_external_id),
    INDEX idx_policies_lob_org (lob, org_external_id),
    INDEX idx_policies_search_composite (lob, org_external_id, policy_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Policy Contacts Table
-- Stores contacts associated with policies (insureds, claimants, companies)
CREATE TABLE IF NOT EXISTS policy_contacts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    policy_id INT NOT NULL,
    ref_id VARCHAR(64) NOT NULL,
    external_id VARCHAR(64) NULL,
    is_company BOOLEAN NOT NULL DEFAULT FALSE,
    company_name VARCHAR(255) NULL,
    first_name VARCHAR(100) NULL,
    middle_name VARCHAR(100) NULL,
    last_name VARCHAR(100) NULL,
    address1 VARCHAR(255) NULL,
    address2 VARCHAR(255) NULL,
    city VARCHAR(100) NULL,
    state VARCHAR(50) NULL,
    zipcode VARCHAR(30) NULL,
    country VARCHAR(100) NULL,

    CONSTRAINT fk_policy_contacts_policy
        FOREIGN KEY (policy_id) REFERENCES policies (id)
        ON DELETE CASCADE,
    INDEX idx_contacts_policy_id (policy_id),
    INDEX idx_contacts_ref_id (ref_id),
    INDEX idx_contacts_company_name (company_name),
    INDEX idx_contacts_person_name (last_name, first_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Contact Phones Table
-- Stores phone records belonging to contacts
CREATE TABLE IF NOT EXISTS contact_phones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contact_id INT NOT NULL,
    phone_number VARCHAR(50) NOT NULL,
    phone_type VARCHAR(50) NULL,

    CONSTRAINT fk_contact_phones_contact
        FOREIGN KEY (contact_id) REFERENCES policy_contacts (id)
        ON DELETE CASCADE,
    INDEX idx_phones_contact_id (contact_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Retrieval Tokens Table
-- Stores opaque retrieval tokens mapped to policies for Five Sigma FNOL handoff
CREATE TABLE IF NOT EXISTS retrieval_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    token VARCHAR(128) NOT NULL,
    policy_external_id VARCHAR(64) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_retrieval_tokens_token UNIQUE (token),
    CONSTRAINT fk_retrieval_tokens_policy
        FOREIGN KEY (policy_external_id) REFERENCES policies (external_id)
        ON DELETE CASCADE,
    INDEX idx_tokens_policy_external_id (policy_external_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

