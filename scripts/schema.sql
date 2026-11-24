-- ==============================================================================
-- Five Sigma Policy Integration Database Schema (MySQL 8.0+)
-- Database: policy_db
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS policy_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE policy_db;

-- ------------------------------------------------------------------------------
-- 1. Table: policies
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS policies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    version INT NOT NULL DEFAULT 1,
    external_id VARCHAR(64) NOT NULL UNIQUE,
    policy_number VARCHAR(64) NOT NULL,
    lob VARCHAR(32) NOT NULL,
    org_external_id VARCHAR(64) NOT NULL,
    suborg_external_id VARCHAR(64) NULL,
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
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_policies_policy_number (policy_number),
    INDEX idx_policies_lob_org (lob, org_external_id),
    INDEX idx_policies_search_composite (lob, org_external_id, policy_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 2. Table: policy_contacts
-- ------------------------------------------------------------------------------
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
    INDEX idx_contacts_policy_id (policy_id),
    INDEX idx_contacts_ref_id (ref_id),
    CONSTRAINT fk_contacts_policy
        FOREIGN KEY (policy_id) REFERENCES policies(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 3. Table: contact_phones
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contact_phones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contact_id INT NOT NULL,
    phone_number VARCHAR(50) NOT NULL,
    phone_type VARCHAR(50) NULL,
    INDEX idx_phones_contact_id (contact_id),
    CONSTRAINT fk_phones_contact
        FOREIGN KEY (contact_id) REFERENCES policy_contacts(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 4. Table: retrieval_tokens
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS retrieval_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    token VARCHAR(128) NOT NULL UNIQUE,
    policy_external_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tokens_token (token),
    INDEX idx_tokens_policy_ext (policy_external_id),
    CONSTRAINT fk_tokens_policy
        FOREIGN KEY (policy_external_id) REFERENCES policies(external_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

