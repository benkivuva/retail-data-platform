"""Create demo users in the local SQLite database.

    uv run python platform/seed_users.py
"""
from app import create_app
from app.auth.models import User
from app.extensions import db

USERS = [
    {"email": "admin@example.com",   "password": "admin123",   "role": "admin",   "display_name": "Admin"},
    {"email": "analyst@example.com", "password": "analyst123", "role": "analyst", "display_name": "Analyst"},
    {"email": "viewer@example.com",  "password": "viewer123",  "role": "viewer",  "display_name": "Viewer"},
]


def main() -> None:
    app = create_app()
    with app.app_context():
        for spec in USERS:
            existing = User.query.filter_by(email=spec["email"]).first()
            if existing:
                print(f"  [skip] {spec['email']} already exists")
                continue
            user = User(
                email=spec["email"],
                role=spec["role"],
                display_name=spec["display_name"],
            )
            user.set_password(spec["password"])
            db.session.add(user)
            print(f"  [add]  {spec['email']} ({spec['role']})")
        db.session.commit()
        print("\nDone.")


if __name__ == "__main__":
    main()