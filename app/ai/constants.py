"""Shared AI constants, guardrails, and user-facing safe text."""

from __future__ import annotations


DEFAULT_PERPLEXITY_MODEL = "perplexity/sonar"
PERPLEXITY_API_KEY_ENV = "PERPLEXITY_API_KEY"

STANDARD_GUARDRAILS = """Allocadabra is an educational crypto treasury modelling tool.
Outputs are educational and technical, not financial advice.
No warranty is given as to the accuracy of data, modelling outputs, or AI explanations.
Do not recommend buying, selling, holding, or trading assets.
Do not imply guaranteed returns or certain outcomes.
Only reference supported model names when suggesting models.
In Configuration Mode, guide app setup and modelling configuration.
In Review Mode, explain results from a simple, neutral, technical perspective.
Keep responses short by default, normally one paragraph.
Expand to 3-5 paragraphs only when the user asks for more detail.
Admit uncertainty around model limitations, data quality, and unsupported requests.
If asked for financial advice, refuse and say users should consult a professional financial advisor before making investment decisions.
Do not cite external sources, reference live data, or use web search in V1."""

FIXED_FINANCIAL_ADVICE_REFUSAL = (
    "I cannot provide financial advice or recommend buying, selling, holding, or "
    "trading assets. Allocadabra is an educational crypto treasury modelling tool; "
    "its outputs are technical learning aids, not investment instructions, and no "
    "warranty is given as to the accuracy of the information. Please consult a "
    "professional financial advisor before making investment decisions."
)

GENERIC_SAFE_ERROR = (
    "The AI response could not be used safely. Please regenerate the response or "
    "ask for educational analysis in a different way."
)

MISSING_API_KEY_ERROR = (
    "Perplexity is not configured. Set PERPLEXITY_API_KEY before using AI-required "
    "steps."
)

PROVIDER_UNAVAILABLE_ERROR = (
    "Perplexity is temporarily unavailable. Please retry the AI step."
)
