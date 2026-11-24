"""Initial migration: Create Policy Search tables

Revision ID: 001_initial_tables
Revises:
Create Date: 2026-11-24 15:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_initial_tables"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create policies, policy_contacts, contact_phones, and retrieval_tokens tables."""
    # 1. Policies Table
    op.create_table(
        "policies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("policy_number", sa.String(length=64), nullable=False),
        sa.Column("lob", sa.String(length=32), nullable=False),
        sa.Column("org_external_id", sa.String(length=64), nullable=False),
        sa.Column("sub_organization_external_id", sa.String(length=64), nullable=True),
        sa.Column("effective_date", sa.String(length=32), nullable=False),
        sa.Column("expiration_date", sa.String(length=32), nullable=False),
        sa.Column("policy_holder_contact_ref_id", sa.String(length=64), nullable=False),
        sa.Column("retroactive_date", sa.String(length=32), nullable=True),
        sa.Column("cancelled_date", sa.String(length=32), nullable=True),
        sa.Column("effective_time", sa.String(length=32), nullable=True),
        sa.Column("expiration_time", sa.String(length=32), nullable=True),
        sa.Column("cancelled_time", sa.String(length=32), nullable=True),
        sa.Column("retroactive_time", sa.String(length=32), nullable=True),
        sa.Column("is_claims_made", sa.Boolean(), nullable=True),
        sa.Column("runoff_provision", sa.String(length=255), nullable=True),
        sa.Column("extra_data", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id", name="uq_policies_external_id"),
    )
    op.create_index("idx_policies_external_id", "policies", ["external_id"])
    op.create_index("idx_policies_policy_number", "policies", ["policy_number"])
    op.create_index("idx_policies_lob", "policies", ["lob"])
    op.create_index("idx_policies_org_external_id", "policies", ["org_external_id"])
    op.create_index("idx_policies_suborg", "policies", ["sub_organization_external_id"])
    op.create_index("idx_policies_lob_org", "policies", ["lob", "org_external_id"])
    op.create_index(
        "idx_policies_search_composite",
        "policies",
        ["lob", "org_external_id", "policy_number"],
    )

    # 2. Policy Contacts Table
    op.create_table(
        "policy_contacts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("policy_id", sa.Integer(), nullable=False),
        sa.Column("ref_id", sa.String(length=64), nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=True),
        sa.Column("is_company", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("middle_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column("address1", sa.String(length=255), nullable=True),
        sa.Column("address2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=50), nullable=True),
        sa.Column("zipcode", sa.String(length=30), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(
            ["policy_id"], ["policies.id"], name="fk_policy_contacts_policy", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_contacts_policy_id", "policy_contacts", ["policy_id"])
    op.create_index("idx_contacts_ref_id", "policy_contacts", ["ref_id"])
    op.create_index("idx_contacts_company_name", "policy_contacts", ["company_name"])
    op.create_index("idx_contacts_person_name", "policy_contacts", ["last_name", "first_name"])

    # 3. Contact Phones Table
    op.create_table(
        "contact_phones",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("phone_number", sa.String(length=50), nullable=False),
        sa.Column("phone_type", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(
            ["contact_id"],
            ["policy_contacts.id"],
            name="fk_contact_phones_contact",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_phones_contact_id", "contact_phones", ["contact_id"])

    # 4. Retrieval Tokens Table
    op.create_table(
        "retrieval_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("policy_external_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["policy_external_id"],
            ["policies.external_id"],
            name="fk_retrieval_tokens_policy",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token", name="uq_retrieval_tokens_token"),
    )
    op.create_index("idx_tokens_policy_external_id", "retrieval_tokens", ["policy_external_id"])


def downgrade() -> None:
    """Drop retrieval_tokens, contact_phones, policy_contacts, and policies tables."""
    op.drop_table("retrieval_tokens")
    op.drop_table("contact_phones")
    op.drop_table("policy_contacts")
    op.drop_table("policies")
