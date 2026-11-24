"""Database connection, engine configuration, and session lifecycle management."""

import logging
from collections.abc import Generator
from functools import lru_cache
from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.exceptions import DatabaseError
from app.database.models import Base

logger = logging.getLogger("app.database.connection")


@lru_cache
def get_engine(db_url: str | None = None) -> Engine:
    """Creates a cached SQLAlchemy Engine with connection pool management.

    Uses pool_pre_ping=True to guard against dropped MySQL connections.
    """
    url = db_url or settings.get_database_url()
    is_sqlite = url.startswith("sqlite")

    engine_kwargs: dict[str, Any] = {}
    if not is_sqlite:
        # Production MySQL connection pooling options
        engine_kwargs.update(
            {
                "pool_size": 10,
                "max_overflow": 20,
                "pool_pre_ping": True,
                "pool_recycle": 3600,
            }
        )
    else:
        # SQLite compatibility for isolated in-memory testing
        engine_kwargs.update({"connect_args": {"check_same_thread": False}})

    try:
        return create_engine(url, **engine_kwargs)
    except SQLAlchemyError as e:
        logger.error("Failed to create database engine for %s: %s", url, e)
        raise DatabaseError(
            message=f"Failed to create database engine: {e}",
            code="DATABASE_ERROR",
            status_code=500,
        ) from e


def get_session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    """Creates a sessionmaker factory bound to the active engine."""
    active_engine = engine or get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=active_engine)


def get_db(db_url: str | None = None) -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a managed database session."""
    engine = get_engine(db_url)
    session_local = get_session_factory(engine)
    session = session_local()
    try:
        yield session
    except SQLAlchemyError as e:
        session.rollback()
        logger.error("Database session transaction error: %s", e)
        raise DatabaseError(
            message=f"Database transaction error: {e}",
            code="DATABASE_ERROR",
            status_code=500,
        ) from e
    finally:
        session.close()


def init_db(engine: Engine | None = None) -> None:
    """Initializes tables in MySQL based on the SQLAlchemy models."""
    active_engine = engine or get_engine()
    try:
        Base.metadata.create_all(bind=active_engine)
        logger.info("Database tables successfully created or verified.")
    except SQLAlchemyError as e:
        logger.error("Database initialization failed: %s", e)
        raise DatabaseError(
            message=f"Database table initialization failed: {e}",
            code="DATABASE_ERROR",
            status_code=500,
        ) from e
