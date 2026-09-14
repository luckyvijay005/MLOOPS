"""PostgreSQL database connection and session management module."""

import sys
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

# Ensure src can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.utils.config import Config
from src.utils.logger import logger


class DatabaseManager:
    """Manages PostgreSQL connections, engine creation, and connectivity checks."""

    _engine: Optional[Engine] = None

    @classmethod
    def get_engine(cls, pool_size: int = 5, max_overflow: int = 10) -> Engine:
        """Returns a singleton SQLAlchemy engine."""
        if cls._engine is None:
            db_url = Config.get_db_url()
            logger.info(f"Creating PostgreSQL engine for {Config.POSTGRES_USER}@{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{Config.POSTGRES_DB}")
            cls._engine = create_engine(
                db_url,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,
            )
        return cls._engine

    @classmethod
    def check_connection(cls) -> bool:
        """Tests if the PostgreSQL server is reachable."""
        try:
            engine = cls.get_engine()
            with engine.connect() as conn:
                res = conn.execute(text("SELECT 1;")).scalar()
                if res == 1:
                    logger.info("PostgreSQL database connection verified.")
                    return True
        except OperationalError as err:
            logger.warning(
                f"PostgreSQL connection failed (host={Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}): {err.orig}"
            )
            return False
        except Exception as exc:
            logger.warning(f"Unexpected error testing database connection: {exc}")
            return False
        return False

    @classmethod
    def close(cls):
        """Disposes the active engine connection pool."""
        if cls._engine is not None:
            cls._engine.dispose()
            cls._engine = None
            logger.info("PostgreSQL connection pool closed.")


if __name__ == "__main__":
    is_connected = DatabaseManager.check_connection()
    print(f"Database reachable: {is_connected}")
