from contextlib import contextmanager
from typing import Iterator
from sqlmodel import Session, create_engine
from src.core.config import config
connect_args = {}
if config.database_url.startswith('sqlite'):
    connect_args = {'check_same_thread': False}
engine = create_engine(config.database_url, echo=False, connect_args=connect_args)

def init_db() -> None:
    pass

def get_session() -> Session:
    return Session(engine)

@contextmanager
def session_scope() -> Iterator[Session]:
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()