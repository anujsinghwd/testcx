"""Unit tests for Alembic database migrations and table schemas."""

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.engine import Engine, create_engine

from alembic import command


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Generator[str, None, None]:
    """Provides a temporary SQLite database path for migration testing."""
    db_file = tmp_path / "test_migration.db"
    db_url = f"sqlite:///{db_file}"
    old_db_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = db_url

    yield db_url

    if old_db_url is not None:
        os.environ["DATABASE_URL"] = old_db_url
    else:
        os.environ.pop("DATABASE_URL", None)


@pytest.fixture
def alembic_config(temp_db_path: str) -> Config:
    """Provides an Alembic Config pointing to the project alembic.ini."""
    project_root = Path(__file__).resolve().parent.parent.parent
    ini_path = project_root / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option("sqlalchemy.url", temp_db_path)
    return cfg


def test_alembic_upgrade_and_downgrade(alembic_config: Config, temp_db_path: str) -> None:
    """Tests that Alembic can apply migrations (upgrade head) and revert (downgrade base)."""
    # 1. Apply all migrations
    command.upgrade(alembic_config, "head")

    engine: Engine = create_engine(temp_db_path)
    inspector = inspect(engine)

    # 2. Verify all expected tables exist
    tables = inspector.get_table_names()
    assert "policies" in tables
    assert "policy_contacts" in tables
    assert "contact_phones" in tables
    assert "retrieval_tokens" in tables
    assert "alembic_version" in tables

    # 3. Verify columns in `policies` table
    policy_columns = {col["name"]: col for col in inspector.get_columns("policies")}
    assert "version" in policy_columns
    assert "external_id" in policy_columns
    assert "policy_number" in policy_columns
    assert "lob" in policy_columns
    assert "org_external_id" in policy_columns
    assert "sub_organization_external_id" in policy_columns
    assert "effective_date" in policy_columns
    assert "expiration_date" in policy_columns
    assert "policy_holder_contact_ref_id" in policy_columns
    assert "retroactive_date" in policy_columns
    assert "is_claims_made" in policy_columns
    assert "runoff_provision" in policy_columns

    # 4. Verify columns in `policy_contacts` table
    contact_columns = {col["name"]: col for col in inspector.get_columns("policy_contacts")}
    assert "policy_id" in contact_columns
    assert "ref_id" in contact_columns
    assert "external_id" in contact_columns
    assert "is_company" in contact_columns
    assert "company_name" in contact_columns
    assert "first_name" in contact_columns
    assert "last_name" in contact_columns
    assert "address1" in contact_columns
    assert "city" in contact_columns
    assert "state" in contact_columns
    assert "zipcode" in contact_columns
    assert "country" in contact_columns

    # 5. Verify columns in `contact_phones` table
    phone_columns = {col["name"]: col for col in inspector.get_columns("contact_phones")}
    assert "contact_id" in phone_columns
    assert "phone_number" in phone_columns
    assert "phone_type" in phone_columns

    # 6. Verify columns in `retrieval_tokens` table
    token_columns = {col["name"]: col for col in inspector.get_columns("retrieval_tokens")}
    assert "token" in token_columns
    assert "policy_external_id" in token_columns

    # 7. Test downgrade to base
    command.downgrade(alembic_config, "base")
    inspector = inspect(engine)
    remaining_tables = inspector.get_table_names()
    assert "policies" not in remaining_tables
    assert "policy_contacts" not in remaining_tables
    assert "contact_phones" not in remaining_tables
    assert "retrieval_tokens" not in remaining_tables
