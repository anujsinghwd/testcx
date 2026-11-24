"""SQLAlchemy declarative models for MySQL Policy Storage.

Defines normalized schema matching the confirmed Five Sigma v2 contract:
- PolicyModel: policies table
- ContactModel: policy_contacts table
- PhoneModel: contact_phones table
- RetrievalTokenModel: retrieval_tokens table
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy database models."""

    pass


class PolicyModel(Base):
    """Policy master table storing core policy details."""

    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    external_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    policy_number: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    lob: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    org_external_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    suborg_external_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    effective_date: Mapped[str] = mapped_column(String(32), nullable=False)
    expiration_date: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_holder_contact_ref_id: Mapped[str] = mapped_column(String(64), nullable=False)

    # Optional fields
    retroactive_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cancelled_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    effective_time: Mapped[str | None] = mapped_column(String(32), nullable=True)
    expiration_time: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cancelled_time: Mapped[str | None] = mapped_column(String(32), nullable=True)
    retroactive_time: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_claims_made: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    runoff_provision: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Extra policy properties stored as JSON string conforming to extra="allow"
    extra_data: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    contacts: Mapped[list["ContactModel"]] = relationship(
        back_populates="policy",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    retrieval_tokens: Mapped[list["RetrievalTokenModel"]] = relationship(
        back_populates="policy",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_policies_lob_org", "lob", "org_external_id"),
        Index("idx_policies_search_composite", "lob", "org_external_id", "policy_number"),
    )


class ContactModel(Base):
    """Contacts associated with policies (insureds, claimants, companies)."""

    __tablename__ = "policy_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    policy_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ref_id: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_company: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    middle_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    zipcode: Mapped[str | None] = mapped_column(String(30), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    policy: Mapped["PolicyModel"] = relationship(back_populates="contacts")
    phones: Mapped[list["PhoneModel"]] = relationship(
        back_populates="contact",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PhoneModel(Base):
    """Phone records belonging to a contact."""

    __tablename__ = "contact_phones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contact_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("policy_contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False)
    phone_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    contact: Mapped["ContactModel"] = relationship(back_populates="phones")


class RetrievalTokenModel(Base):
    """Opaque search retrieval tokens mapped to policies."""

    __tablename__ = "retrieval_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    policy_external_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("policies.external_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    policy: Mapped["PolicyModel"] = relationship(back_populates="retrieval_tokens")
