"""MySQL-backed Mock Policy Repository adhering to Five Sigma v2 Policy Search contract."""

import json
import logging
import secrets
from typing import Any

from sqlalchemy import Engine, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.exceptions import DatabaseError
from app.data.mock_data import APPROVED_MOCK_POLICIES, DEFAULT_DISPLAY_SCHEMA
from app.database.connection import get_engine, get_session_factory, init_db
from app.database.models import (
    ContactModel,
    PhoneModel,
    PolicyModel,
    RetrievalTokenModel,
)
from app.integrations.policy_system.source import PolicySource
from app.schemas.policy import (
    PolicyApiDisplaySchemaField,
    PolicyApiPolicy,
    PolicyApiSearchResponse,
    PolicyApiSearchResult,
)

logger = logging.getLogger("app.repositories.policy_repository")


class MySQLPolicyRepository(PolicySource):
    """MySQL-backed policy repository implementing PolicySource interface for policy search."""

    def __init__(
        self,
        engine: Engine | None = None,
        db_url: str | None = None,
        auto_init: bool = True,
        auto_seed: bool = True,
    ) -> None:
        """Initializes the repository with an engine and session factory."""
        self.engine = engine or get_engine(db_url)
        self.session_factory: sessionmaker[Session] = get_session_factory(self.engine)
        if auto_init:
            init_db(self.engine)
        if auto_seed:
            self._ensure_mock_data_seeded()

    def _ensure_mock_data_seeded(self) -> None:
        """Seeds approved mock data if the policies table is currently empty."""
        try:
            with self.session_factory() as session:
                count = session.scalar(select(func.count(PolicyModel.id))) or 0
                if count == 0:
                    self.load_mock_data()
        except SQLAlchemyError as e:
            logger.warning("Could not auto-seed database (server may be offline): %s", e)

    def load_mock_data(self, records: list[dict[str, Any]] | None = None) -> int:
        """Loads approved mock policy records into the database.

        Validates each record against PolicyApiPolicy before persisting.
        """
        data_to_load = records if records is not None else APPROVED_MOCK_POLICIES
        loaded_count = 0
        try:
            for item in data_to_load:
                policy = PolicyApiPolicy.model_validate(item)
                org_ext_id = str(item.get("org_external_id", "BHSI-ORG-01"))
                self.save_policy(policy, org_external_id=org_ext_id)
                loaded_count += 1
            return loaded_count
        except SQLAlchemyError as e:
            logger.error("Failed to load mock policy records: %s", e)
            raise DatabaseError(
                message=f"Failed to load mock policy records: {e}",
                code="DATABASE_ERROR",
                status_code=500,
            ) from e

    def save_policy(self, policy: PolicyApiPolicy, org_external_id: str = "BHSI-ORG-01") -> None:
        """Saves or updates a policy record with its associated contacts and phone records."""
        try:
            with self.session_factory() as session, session.begin():
                # Check for existing policy
                stmt = select(PolicyModel).where(PolicyModel.external_id == policy.external_id)
                existing = session.scalar(stmt)
                if existing:
                    session.delete(existing)
                    session.flush()

                # Extract any extra fields for extra_data storage
                standard_fields = {
                    "version",
                    "external_id",
                    "policy_number",
                    "effective_date",
                    "expiration_date",
                    "policy_holder_contact_ref_id",
                    "contacts",
                    "lob",
                    "retroactive_date",
                    "cancelled_date",
                    "effective_time",
                    "expiration_time",
                    "cancelled_time",
                    "retroactive_time",
                    "sub_organization_external_id",
                    "is_claims_made",
                    "runoff_provision",
                }
                extra_fields = {
                    k: v for k, v in policy.model_dump().items() if k not in standard_fields
                }
                extra_data_json = json.dumps(extra_fields) if extra_fields else None

                policy_model = PolicyModel(
                    version=policy.version,
                    external_id=policy.external_id,
                    policy_number=policy.policy_number,
                    lob=policy.lob,
                    org_external_id=org_external_id,
                    suborg_external_id=policy.sub_organization_external_id,
                    effective_date=policy.effective_date,
                    expiration_date=policy.expiration_date,
                    policy_holder_contact_ref_id=policy.policy_holder_contact_ref_id,
                    retroactive_date=policy.retroactive_date,
                    cancelled_date=policy.cancelled_date,
                    effective_time=policy.effective_time,
                    expiration_time=policy.expiration_time,
                    cancelled_time=policy.cancelled_time,
                    retroactive_time=policy.retroactive_time,
                    is_claims_made=policy.is_claims_made,
                    runoff_provision=policy.runoff_provision,
                    extra_data=extra_data_json,
                )

                # Build child contact models
                contact_models: list[ContactModel] = []
                for c in policy.contacts:
                    contact_model = ContactModel(
                        ref_id=c.ref_id,
                        external_id=c.external_id,
                        is_company=c.is_company,
                        company_name=c.company_name,
                        first_name=c.first_name,
                        middle_name=c.middle_name,
                        last_name=c.last_name,
                        address1=c.address1,
                        address2=c.address2,
                        city=c.city,
                        state=c.state,
                        zipcode=c.zipcode,
                        country=c.country,
                    )
                    # Build phone models
                    phone_models = [
                        PhoneModel(
                            phone_number=p.phone_number,
                            phone_type=p.phone_type,
                        )
                        for p in c.phones
                    ]
                    contact_model.phones = phone_models
                    contact_models.append(contact_model)

                policy_model.contacts = contact_models
                session.add(policy_model)
        except SQLAlchemyError as e:
            logger.error("Failed to save policy record: %s", e)
            raise DatabaseError(
                message=f"Failed to save policy: {e}",
                code="DATABASE_ERROR",
                status_code=500,
            ) from e

    def create_retrieval_token(self, policy_external_id: str) -> str:
        """Generates and persists an opaque retrieval token associated with a policy."""
        token = secrets.token_urlsafe(32)
        try:
            with self.session_factory() as session, session.begin():
                token_model = RetrievalTokenModel(
                    token=token,
                    policy_external_id=policy_external_id,
                )
                session.add(token_model)
            return token
        except SQLAlchemyError as e:
            logger.error("Failed to persist retrieval token: %s", e)
            raise DatabaseError(
                message=f"Failed to create retrieval token: {e}",
                code="DATABASE_ERROR",
                status_code=500,
            ) from e

    async def search_policies(
        self,
        lob: str,
        org_external_id: str,
        suborg_external_id: str | None = None,
        search_fields: dict[str, Any] | None = None,
    ) -> PolicyApiSearchResponse:
        """Searches policies matching line of business and organization parameters in MySQL."""
        try:
            with self.session_factory() as session:
                stmt = select(PolicyModel).where(
                    func.lower(PolicyModel.lob) == lob.lower(),
                    PolicyModel.org_external_id == org_external_id,
                )
                if suborg_external_id:
                    stmt = stmt.where(PolicyModel.suborg_external_id == suborg_external_id)

                policies = list(session.scalars(stmt).all())

                results: list[PolicyApiSearchResult] = []
                display_schema: list[PolicyApiDisplaySchemaField] = DEFAULT_DISPLAY_SCHEMA

                for policy in policies:
                    # Apply organization-configured search filters if passed
                    if search_fields:
                        match = True
                        for field_key, field_val in search_fields.items():
                            if field_val is None:
                                continue
                            str_val = str(field_val).strip().lower()
                            if field_key == "policy_number":
                                if str_val not in policy.policy_number.lower():
                                    match = False
                                    break
                            elif field_key in ("first_name", "last_name", "company_name"):
                                found = False
                                for c in policy.contacts:
                                    if (
                                        (c.first_name and str_val in c.first_name.lower())
                                        or (c.last_name and str_val in c.last_name.lower())
                                        or (c.company_name and str_val in c.company_name.lower())
                                    ):
                                        found = True
                                        break
                                if not found:
                                    match = False
                                    break
                            elif (
                                field_key == "effective_date"
                                and str_val not in policy.effective_date.lower()
                            ):
                                match = False
                                break
                        if not match:
                            continue

                    # Determine policy holder display name
                    holder_name = "N/A"
                    for contact in policy.contacts:
                        if contact.ref_id == policy.policy_holder_contact_ref_id:
                            if contact.is_company and contact.company_name:
                                holder_name = contact.company_name
                            else:
                                parts = [p for p in (contact.first_name, contact.last_name) if p]
                                holder_name = " ".join(parts) if parts else "Unknown"
                            break

                    display_fields: dict[str, Any] = {
                        "policy_number": policy.policy_number,
                        "policy_holder": holder_name,
                        "effective_date": policy.effective_date,
                        "expiration_date": policy.expiration_date,
                        "lob": policy.lob,
                    }

                    # Generate and persist opaque retrieval token
                    token = self.create_retrieval_token(policy.external_id)
                    results.append(
                        PolicyApiSearchResult(
                            display_fields=display_fields,
                            retrieval_token=token,
                        )
                    )

                return PolicyApiSearchResponse(
                    total_results=len(results),
                    display_schema=display_schema,
                    results=results,
                )
        except SQLAlchemyError as e:
            logger.error("Database failure during search_policies: %s", e)
            raise DatabaseError(
                message=f"Database search failed: {e}",
                code="DATABASE_ERROR",
                status_code=500,
            ) from e


# Backward compatibility alias
MockPolicyRepository = MySQLPolicyRepository
