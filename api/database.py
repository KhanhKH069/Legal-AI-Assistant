from sqlmodel import create_engine, Session

sqlite_file_name = "data/paraline.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)


def create_db_and_tables():
    # Deprecated in favor of Alembic migrations
    pass


def get_session():
    with Session(engine) as session:
        yield session
