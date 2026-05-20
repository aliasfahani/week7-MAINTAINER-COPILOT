import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.infra.db import get_session_local
from app.repositories.users import get_user_by_email
from app.services.auth_service import register_user


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed an initial admin user.")
    parser.add_argument("--email", default="admin@example.com")
    parser.add_argument("--password", default="admin123")
    args = parser.parse_args()

    db = get_session_local()()
    try:
        if get_user_by_email(db, args.email):
            print(f"Admin already exists: {args.email}")
            return 0
        register_user(db, args.email, args.password, role="admin")
        print(f"Created admin user: {args.email}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
