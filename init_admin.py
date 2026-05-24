from api.database import engine
from sqlmodel import Session, select
from api.models import User
from api.auth import get_password_hash


def init_admin():
    with Session(engine) as session:
        admin = session.exec(select(User).where(User.username == "admin")).first()
        if not admin:
            print("Creating default admin user...")
            new_admin = User(
                username="admin",
                hashed_password=get_password_hash("password123"),
                role="admin",
                employee_id="ADM001",
            )
            session.add(new_admin)
            session.commit()
            print("Admin user created: admin / password123")
        else:
            print("Admin user already exists.")


if __name__ == "__main__":
    init_admin()
