"""MySQL-backed Mock Policy Repository adhering to Five Sigma v2 Policy Search contract."""

import json
import logging
import secrets
from typing import Any

from sqlalchemy import Engine, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.exceptions import DatabaseError, PolicyNotFoundError
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
    PolicyApiContact,
    PolicyApiDisplaySchemaField,
    PolicyApiPhone,
    PolicyApiPolicy,
    PolicyApiRetrieveResponse,
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
                    sub_organization_external_id=policy.sub_organization_external_id,
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
        policy_number: str | None = None,
    ) -> PolicyApiSearchResponse:
        """Searches policies matching line of business and organization parameters in MySQL."""
        try:
            with self.session_factory() as session:
                stmt = select(PolicyModel).where(
                    func.lower(PolicyModel.lob) == lob.lower(),
                    PolicyModel.org_external_id == org_external_id,
                )
                if suborg_external_id:
                    stmt = stmt.where(
                        PolicyModel.sub_organization_external_id == suborg_external_id
                    )

                if policy_number is not None and policy_number.strip():
                    clean_pol_num = policy_number.strip().lower()
                    stmt = stmt.where(func.lower(PolicyModel.policy_number).contains(clean_pol_num))

                policies = list(session.scalars(stmt).all())

                results: list[PolicyApiSearchResult] = []
                display_schema: list[PolicyApiDisplaySchemaField] = DEFAULT_DISPLAY_SCHEMA

                for policy in policies:
                    # Determine insured display name
                    insured_name = "N/A"
                    for contact in policy.contacts:
                        if contact.ref_id == policy.policy_holder_contact_ref_id:
                            if contact.is_company and contact.company_name:
                                insured_name = contact.company_name
                            else:
                                parts = [p for p in (contact.first_name, contact.last_name) if p]
                                insured_name = " ".join(parts) if parts else "Unknown"
                            break

                    display_fields: dict[str, Any] = {
                        "policy_number": policy.policy_number,
                        "insured_name": insured_name,
                        "effective_date": policy.effective_date,
                        "expiration_date": policy.expiration_date,
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

    def _model_to_policy_schema(self, policy: PolicyModel) -> PolicyApiPolicy:
        """Converts a database PolicyModel into a canonical PolicyApiPolicy schema."""
        contacts: list[PolicyApiContact] = []
        for c in policy.contacts:
            phones = [
                PolicyApiPhone(
                    phone_number=p.phone_number,
                    phone_type=p.phone_type,
                )
                for p in c.phones
            ]
            contacts.append(
                PolicyApiContact(
                    ref_id=c.ref_id,
                    external_id=c.external_id,
                    is_company=c.is_company,
                    company_name=c.company_name,
                    first_name=c.first_name,
                    middle_name=c.middle_name,
                    last_name=c.last_name,
                    phones=phones,
                    address1=c.address1,
                    address2=c.address2,
                    city=c.city,
                    state=c.state,
                    zipcode=c.zipcode,
                    country=c.country,
                )
            )

        policy_dict: dict[str, Any] = {
            "version": policy.version,
            "external_id": policy.external_id,
            "policy_number": policy.policy_number,
            "effective_date": policy.effective_date,
            "expiration_date": policy.expiration_date,
            "policy_holder_contact_ref_id": policy.policy_holder_contact_ref_id,
            "contacts": contacts,
            "lob": policy.lob,
            "retroactive_date": policy.retroactive_date,
            "cancelled_date": policy.cancelled_date,
            "effective_time": policy.effective_time,
            "expiration_time": policy.expiration_time,
            "cancelled_time": policy.cancelled_time,
            "retroactive_time": policy.retroactive_time,
            "sub_organization_external_id": policy.sub_organization_external_id,
            "is_claims_made": policy.is_claims_made,
            "runoff_provision": policy.runoff_provision,
        }
        return PolicyApiPolicy.model_validate(policy_dict)

    async def retrieve_policy_by_token(self, retrieval_token: str) -> PolicyApiRetrieveResponse:
        """Retrieves a complete policy record associated with an opaque retrieval token."""
        try:
            with self.session_factory() as session:
                token_record = session.scalar(
                    select(RetrievalTokenModel).where(RetrievalTokenModel.token == retrieval_token)
                )
                if not token_record:
                    raise PolicyNotFoundError(
                        f"Policy retrieval token '{retrieval_token}' not found"
                    )

                policy_model = session.scalar(
                    select(PolicyModel).where(
                        PolicyModel.external_id == token_record.policy_external_id
                    )
                )
                if not policy_model:
                    raise PolicyNotFoundError(
                        f"Policy with external_id '{token_record.policy_external_id}' not found for token"
                    )

                policy_schema = self._model_to_policy_schema(policy_model)
                return PolicyApiRetrieveResponse(policy=policy_schema)
        except PolicyNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error("Database failure during retrieve_policy_by_token: %s", e)
            raise DatabaseError(
                message=f"Database retrieval failed: {e}",
                code="DATABASE_ERROR",
                status_code=500,
            ) from e

    @staticmethod
    def _is_in_force_on_date(policy: PolicyModel, date_of_loss: str) -> bool:
        """Determines whether a policy was in force on the supplied date of loss."""
        # Claims-made retroactive date check
        if (
            policy.is_claims_made
            and policy.retroactive_date
            and date_of_loss < policy.retroactive_date
        ):
            return False

        # Effective date check
        if date_of_loss < policy.effective_date:
            return False

        # Cancellation date check
        if policy.cancelled_date and date_of_loss > policy.cancelled_date:
            return False

        # Expiration date check
        return date_of_loss <= policy.expiration_date

    async def retrieve_policy_by_external_id(
        self,
        external_id: str,
        policy_number: str,
        date_of_loss: str,
        claim_number: str,
        lob: str,
        org_external_id: str,
        suborg_external_id: str,
    ) -> PolicyApiRetrieveResponse:
        """Retrieves policy by external ID and date of loss from MySQL mock tables."""
        try:
            with self.session_factory() as session:
                # 1. Look up policy by external_id
                policy = session.scalar(
                    select(PolicyModel).where(PolicyModel.external_id == external_id)
                )
                if not policy:
                    raise PolicyNotFoundError(f"Policy with external_id '{external_id}' not found")

                # 2. Validate context parameters
                if policy.policy_number != policy_number:
                    raise PolicyNotFoundError(
                        f"Policy number '{policy_number}' does not match policy with external_id '{external_id}'"
                    )

                if policy.lob.lower() != lob.lower():
                    raise PolicyNotFoundError(
                        f"Line of business '{lob}' does not match policy with external_id '{external_id}'"
                    )

                if policy.org_external_id != org_external_id:
                    raise PolicyNotFoundError(
                        f"Organization '{org_external_id}' does not match policy with external_id '{external_id}'"
                    )

                if policy.sub_organization_external_id != suborg_external_id:
                    raise PolicyNotFoundError(
                        f"Sub-organization '{suborg_external_id}' does not match policy with external_id '{external_id}'"
                    )

                # 3. Validate in-force status for date_of_loss
                if not self._is_in_force_on_date(policy, date_of_loss):
                    raise PolicyNotFoundError(
                        f"Policy '{external_id}' was not in force on date of loss '{date_of_loss}' "
                        f"(effective: {policy.effective_date}, expiration: {policy.expiration_date})"
                    )

                policy_schema = self._model_to_policy_schema(policy)
                return PolicyApiRetrieveResponse(policy=policy_schema)
        except PolicyNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error("Database failure during retrieve_policy_by_external_id: %s", e)
            raise DatabaseError(
                message=f"Database retrieval failed: {e}",
                code="DATABASE_ERROR",
                status_code=500,
            ) from e


# Backward compatibility alias
MockPolicyRepository = MySQLPolicyRepository
