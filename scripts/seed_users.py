"""
Create the demo users (one per role) in Postgres.

    python -m scripts.seed_users
"""
import os

from dotenv import load_dotenv

from app.core.security import hash_password
from app.db.database import init_db
from app.db.users import upsert_user

load_dotenv()

DEMO_USERS = [
    ("alice_employee", "employee"),
    ("gina_manager", "manager"),
    ("carol_engineer", "engineer"),
    ("bob_hr", "hr"),
    ("dave_finance", "finance"),
    ("erin_security", "security"),
    ("frank_admin", "admin"),
]


def main():
    password = os.getenv("DEMO_PASSWORD", "Demo@12345")
    init_db()
    for username, role in DEMO_USERS:
        upsert_user(username, hash_password(password), role)
    print("Demo users created (password is DEMO_PASSWORD from .env, default Demo@12345):\n")
    for username, role in DEMO_USERS:
        print(f"  {username:16s} role = {role}")


if __name__ == "__main__":
    main()
