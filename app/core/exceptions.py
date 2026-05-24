from typing import Any


class MedisyncError(Exception):
    """Base application exception."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(MedisyncError):
    """Resource not found."""


class ConflictError(MedisyncError):
    """Resource conflict (e.g. duplicate email)."""


class AuthenticationError(MedisyncError):
    """Authentication failed."""


class AuthorizationError(MedisyncError):
    """Insufficient permissions."""


class LLMServiceError(MedisyncError):
    """LLM provider failure."""


class ConfigurationError(MedisyncError):
    """Invalid or missing configuration."""
