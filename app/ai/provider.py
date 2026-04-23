"""Perplexity Agent API provider wrapper."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

from app.ai.constants import (
    DEFAULT_PERPLEXITY_MODEL,
    MISSING_API_KEY_ERROR,
    PERPLEXITY_API_KEY_ENV,
)
from app.ai.errors import MissingAPIKeyError, ProviderUnavailableError


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AIProviderResponse:
    """Normalized provider response."""

    text: str
    raw: object
    model: str


class PerplexityProvider:
    """Shared Perplexity provider for Configuration and Review modes."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = DEFAULT_PERPLEXITY_MODEL,
    ) -> None:
        self.api_key = api_key or os.getenv(PERPLEXITY_API_KEY_ENV, "")
        self.model = model

        if not self.api_key:
            raise MissingAPIKeyError(MISSING_API_KEY_ERROR)

    def complete(
        self,
        *,
        instructions: str,
        input_text: str,
        max_output_tokens: int = 1200,
    ) -> AIProviderResponse:
        """Run one non-search Agent API response request."""
        logger.info("Starting Perplexity AI request with model %s", self.model)

        try:
            from perplexity import Perplexity
        except ImportError as exc:
            raise ProviderUnavailableError(
                "The perplexityai package is not installed in this environment."
            ) from exc

        try:
            client = Perplexity(api_key=self.api_key)
            response = client.responses.create(
                model=self.model,
                input=input_text,
                instructions=instructions,
                max_output_tokens=max_output_tokens,
                tools=[],
            )
        except Exception as exc:
            logger.warning("Perplexity AI request failed: %s", exc)
            raise ProviderUnavailableError("Perplexity request failed.") from exc

        text = _response_text(response).strip()
        if not text:
            raise ProviderUnavailableError("Perplexity returned an empty response.")

        logger.info("Completed Perplexity AI request")
        return AIProviderResponse(text=text, raw=_serialize_response(response), model=self.model)


def _response_text(response: object) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str):
        return output_text

    output = getattr(response, "output", None)
    if not isinstance(output, list):
        return ""

    chunks: list[str] = []
    for item in output:
        content = getattr(item, "content", None)
        if not isinstance(content, list):
            continue
        for part in content:
            text = getattr(part, "text", None)
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks)


def _serialize_response(response: object) -> object:
    if hasattr(response, "model_dump"):
        return response.model_dump()
    if hasattr(response, "dict"):
        return response.dict()
    if isinstance(response, (dict, list, str, int, float, bool)) or response is None:
        return response
    return {"type": type(response).__name__}
