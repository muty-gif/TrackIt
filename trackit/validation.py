"""Request body parsing and field validation helpers."""

from __future__ import annotations

import re

from flask import current_app, request

from .errors import ApiError, ValidationError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def get_json_body() -> dict:
    """Return the request body as a dict or raise a descriptive ApiError."""
    if not request.is_json:
        raise ApiError(
            "Request body must be JSON.",
            status_code=415,
            code="unsupported_media_type",
        )
    data = request.get_json(silent=True)
    if data is None:
        raise ApiError(
            "Request body must contain valid JSON.",
            status_code=400,
            code="invalid_json",
        )
    if not isinstance(data, dict):
        raise ApiError(
            "Request body must be a JSON object.",
            status_code=400,
            code="invalid_json",
        )
    return data


class Validator:
    """Collects field-level errors, then reports them all at once."""

    def __init__(self) -> None:
        self.errors: dict[str, str] = {}

    def string(
        self,
        data: dict,
        field: str,
        *,
        required: bool = True,
        max_length: int | None = None,
        min_length: int | None = None,
        default=None,
        strip: bool = True,
    ):
        if field not in data or data[field] is None:
            if required:
                self.errors[field] = "This field is required."
            return default

        value = data[field]
        if not isinstance(value, str):
            self.errors[field] = "Must be text."
            return default

        if strip:
            value = value.strip()

        if required and not value:
            self.errors[field] = "This field is required."
            return default
        if min_length is not None and value and len(value) < min_length:
            self.errors[field] = f"Must be at least {min_length} characters."
            return default
        if max_length is not None and len(value) > max_length:
            self.errors[field] = f"Must be at most {max_length} characters."
            return default
        return value

    def email(self, data: dict, field: str = "email"):
        value = self.string(data, field, max_length=255)
        if field in self.errors or value is None:
            return None
        value = value.lower()
        if not EMAIL_RE.match(value):
            self.errors[field] = "Enter a valid email address."
            return None
        return value

    def password(self, data: dict, field: str = "password"):
        return self.string(
            data,
            field,
            strip=False,
            min_length=current_app.config["PASSWORD_MIN_LENGTH"],
            max_length=current_app.config["PASSWORD_MAX_LENGTH"],
        )

    def choice(self, data: dict, field: str, allowed, *, required: bool = True, default=None):
        if field not in data or data[field] is None:
            if required:
                self.errors[field] = "This field is required."
            return default
        value = data[field]
        if value not in allowed:
            allowed_text = ", ".join(allowed)
            self.errors[field] = f"Must be one of: {allowed_text}."
            return default
        return value

    def raise_if_errors(self) -> None:
        if self.errors:
            raise ValidationError(dict(self.errors))
