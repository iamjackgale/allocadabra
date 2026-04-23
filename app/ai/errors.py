"""AI integration exceptions."""

from __future__ import annotations


class AIIntegrationError(RuntimeError):
    """Base exception for recoverable AI integration failures."""


class MissingAPIKeyError(AIIntegrationError):
    """Raised when PERPLEXITY_API_KEY is not configured."""


class ProviderUnavailableError(AIIntegrationError):
    """Raised when the Perplexity provider call cannot complete."""


class InvalidAIResponseError(AIIntegrationError):
    """Raised when AI output is unsafe or app-actable metadata is invalid."""
