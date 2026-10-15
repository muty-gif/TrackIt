"""Authentication endpoints: /api/auth/*."""

from __future__ import annotations

from flask import Blueprint, g, jsonify

from ..errors import ConflictError, UnauthorizedError
from ..extensions import db
from ..models import User
from ..validation import Validator, get_json_body
from .utils import login_required, login_user, logout_user

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    data = get_json_body()

    validator = Validator()
    email = validator.email(data)
    password = validator.password(data)
    validator.raise_if_errors()

    existing = db.session.execute(
        db.select(User).where(User.email == email)
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("An account with this email already exists.")

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # Registration logs the new user straight in.
    login_user(user)
    return jsonify({"user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = get_json_body()

    validator = Validator()
    email = validator.email(data)
    password = validator.string(
        data, "password", strip=False, max_length=128, default=None
    )
    validator.raise_if_errors()

    user = db.session.execute(
        db.select(User).where(User.email == email)
    ).scalar_one_or_none()

    # Same generic message whether the email is unknown or the password is wrong.
    if user is None or password is None or not user.check_password(password):
        raise UnauthorizedError("Invalid email or password.", code="invalid_credentials")

    login_user(user)
    return jsonify({"user": user.to_dict()})


@auth_bp.post("/logout")
def logout():
    logout_user()
    return "", 204


@auth_bp.get("/me")
@login_required
def me():
    return jsonify({"user": g.current_user.to_dict()})
