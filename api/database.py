from sqlmodel import create_engine, Session
from src.core.config import config

connect_args = {}
if config.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(config.database_url, echo=False, connect_args=connect_args)


def create_db_and_tables():
    # Deprecated in favor of Alembic migrations
    pass


def get_session():
    with Session(engine) as session:
        yield session
