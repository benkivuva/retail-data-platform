"""User model and role-based permissions."""
from __future__ import annotations

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db


class User(UserMixin, db.Model):
    """A platform user with a role that gates dashboard access."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100), nullable=False, default="User")
    role = db.Column(db.String(20), nullable=False, default="viewer")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def can_view(self, dashboard: str) -> bool:
        """Role-based access: admin sees everything, analyst sees all dashboards,
        viewer sees operations and commercial only."""
        if self.role == "admin":
            return True
        if self.role == "analyst":
            return dashboard in {"operations", "commercial", "finance", "customers"}
        return dashboard in {"operations", "commercial"}