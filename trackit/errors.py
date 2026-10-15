"""Typed API errors and JSON error handling."""

from __future__ import annotations

from flask import jsonify, request
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """Base class for errors that should be returned to API clients as JSON."""

    status_code = 400
    code = "bad_request"

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        fields: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code
        self.fields = fields or {}

    def to_dict(self) -> dict:
        error = {"code": self.code, "message": self.message}
        if self.fields:
            error["fields"] = self.fields
        return {"error": error}


class ValidationError(ApiError):
    def __init__(self, fields: dict, message: str = "Validation failed.") -> None:
        super().__init__(message, status_code=422, code="validation_error", fields=fields)


class UnauthorizedError(ApiError):
    def __init__(self, message: str = "Authentication required.", *, code: str = "unauthorized") -> None:
        super().__init__(message, status_code=401, code=code)


class ForbiddenError(ApiError):
    def __init__(self, message: str = "You do not have access to this resource.") -> None:
        super().__init__(message, status_code=403, code="forbidden")


class NotFoundError(ApiError):
    def __init__(self, message: str = "Resource not found.") -> None:
        super().__init__(message, status_code=404, code="not_found")


class ConflictError(ApiError):
    def __init__(self, message: str = "Resource already exists.") -> None:
        super().__init__(message, status_code=409, code="conflict")


def register_error_handlers(app) -> None:  # noqa: ANN001
    @app.errorhandler(ApiError)
    def _handle_api_error(exc: ApiError):
        return jsonify(exc.to_dict()), exc.status_code

    @app.errorhandler(HTTPException)
    def _handle_http_exception(exc: HTTPException):
        # API routes always answer with JSON; page routes keep Flask's HTML.
        if request.path.startswith("/api/"):
            code = (exc.name or "error").lower().replace(" ", "_")
            return jsonify({"error": {"code": code, "message": exc.description}}), exc.code
        return exc

    @app.errorhandler(Exception)
    def _handle_unexpected(exc: Exception):
        # Let tests and the debugger see the real traceback.
        if app.config.get("PROPAGATE_EXCEPTIONS"):
            raise exc
        app.logger.exception("Unhandled exception")
        if request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "error": {
                            "code": "internal_error",
                            "message": "An unexpected error occurred.",
                        }
                    }
                ),
                500,
            )
        return "Internal Server Error", 500
