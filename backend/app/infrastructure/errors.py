"""Typed application failures. Never converted into fake scientific values."""

from __future__ import annotations


class ApplicationError(Exception):
    def __init__(self, code: str, message: str, http_status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status


class NotFoundError(ApplicationError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, http_status=404)


class ConflictError(ApplicationError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, http_status=409)


class ValidationAppError(ApplicationError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, http_status=422)


class ForbiddenError(ApplicationError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, http_status=403)


class RateLimitError(ApplicationError):
    def __init__(self, message: str = "Too many mutating requests.") -> None:
        super().__init__("RATE_LIMITED", message, http_status=429)
