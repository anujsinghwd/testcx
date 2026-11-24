"""Database initialization and mock data loading CLI script for MySQL."""

import argparse
import logging
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.database.connection import get_engine, init_db
from app.repositories.policy_repository import MySQLPolicyRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("init_mysql_db")


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
    logger.info("Connecting to database: %s", db_url)

    try:
        engine = get_engine(db_url)
        logger.info("Creating tables...")
        init_db(engine)

        if not args.skip_seed:
            logger.info("Seeding approved mock policy records...")
            repo = MySQLPolicyRepository(engine=engine)
            count = repo.load_mock_data()
            logger.info("Successfully seeded %d mock policy records.", count)

        logger.info("Database initialization completed successfully.")
    except Exception as e:
        logger.error("Database initialization failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
