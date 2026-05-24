import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select
from api.database import engine
from api.models import User
from api.auth import get_password_hash


def fix_passwords():
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        # Update all users to password123
        new_hash = get_password_hash("password123")
        for u in users:
            u.hashed_password = new_hash
            session.add(u)
        session.commit()
        print(f"Updated {len(users)} users to password123")


if __name__ == "__main__":
    fix_passwords()
