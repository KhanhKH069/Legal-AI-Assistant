from contextlib import contextmanager
from typing import Iterator

from sqlmodel import Session, create_engine

from src.core.config import config

engine = create_engine(config.database_url, echo=False)


def init_db() -> None:
    """Create all tables if they don't exist."""

    # Do not call create_all() here, as Alembic will handle migrations
    pass


def get_session() -> Session:
    """Simple session factory for non-FastAPI usage."""
    return Session(engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context manager helper for scripts."""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
