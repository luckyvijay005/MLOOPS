"""Database Schema Initialization module.

Executes DDL scripts idempotently to create schemas, tables, indexes, and views.
"""

import sys
from pathlib import Path
from sqlalchemy import text

# Ensure src can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.utils.config import Config
from src.utils.logger import logger
from src.database.connection import DatabaseManager

SQL_DIR = Config.ROOT_DIR / "sql"


def execute_sql_file(file_path: Path, engine) -> None:
    """Reads and executes a multi-statement SQL script."""
    logger.info(f"Executing SQL script: {file_path.name}...")
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split on semicolons or execute blocks safely
    statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

    with engine.begin() as conn:
        for stmt in statements:
            try:
                conn.execute(text(stmt))
            except Exception as exc:
                logger.error(f"Error executing statement in {file_path.name}: {exc}\nStatement:\n{stmt[:200]}")
                raise


def initialize_database() -> bool:
    """Runs all DDL migrations in order."""
    if not DatabaseManager.check_connection():
        logger.warning("Cannot initialize database: PostgreSQL is not reachable.")
        return False

    engine = DatabaseManager.get_engine()
    sql_files = [
        SQL_DIR / "01_create_schemas.sql",
        SQL_DIR / "02_create_tables.sql",
        SQL_DIR / "03_create_indexes.sql",
        SQL_DIR / "04_create_views.sql",
    ]

    for sql_file in sql_files:
        if not sql_file.exists():
            raise FileNotFoundError(f"Missing required DDL script: {sql_file}")
        execute_sql_file(sql_file, engine)

    logger.info("All database schemas, tables, indexes, and views initialized successfully.")
    return True


if __name__ == "__main__":
    initialize_database()
