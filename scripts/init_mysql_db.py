"""Database initialization and mock data loading CLI script for MySQL."""

import argparse
import logging
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url

from app.core.config import settings
from app.database.connection import get_engine, init_db
from app.repositories.policy_repository import MySQLPolicyRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("init_mysql_db")


def ensure_database_exists(db_url: str) -> None:
    """Creates the target MySQL database if it does not already exist."""
    url = make_url(db_url)
    if "mysql" in url.drivername and url.database:
        db_name = url.database
        server_url = url.set(database="")
        logger.info("Verifying/creating database '%s' on MySQL server...", db_name)
        server_engine = create_engine(server_url)
        try:
            with server_engine.connect() as conn:
                conn.execute(
                    text(
                        f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                    )
                )
                conn.commit()
            logger.info("Database '%s' is ready.", db_name)
        except Exception as e:
            logger.warning(
                "Could not auto-create database '%s' (server may be offline or permissions restricted): %s",
                db_name,
                e,
            )
        finally:
            server_engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize MySQL Policy Integration Database")
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Custom database connection URL (defaults to Settings)",
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Skip seeding approved mock policy records",
    )
    args = parser.parse_args()

    db_url = args.db_url or settings.get_database_url()
    logger.info("Target database URL: %s", db_url)

    try:
        ensure_database_exists(db_url)
        engine = get_engine(db_url)
        logger.info("Creating tables...")
        init_db(engine)

        if not args.skip_seed:
            logger.info("Seeding approved mock policy records...")
            repo = MySQLPolicyRepository(engine=engine, auto_init=False, auto_seed=False)
            count = repo.load_mock_data()
            logger.info("Successfully seeded %d mock policy records.", count)

        logger.info("Database initialization completed successfully.")
    except Exception as e:
        logger.error("Database initialization failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
