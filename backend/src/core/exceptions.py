"""
Custom domain exceptions for the ICP Agent platform.

Extracted from agent/utils.py to allow any module to import them
without pulling in the full Toolbox dependency chain.
"""


class RateLimitError(Exception):
    """Raised when an external API returns a rate-limit response (HTTP 429)."""


class TimeoutError(Exception):  # noqa: A001 – shadows built-in intentionally
    """Raised when an external call exceeds its configured timeout."""


class ServiceUnavailableError(Exception):
    """Raised when the circuit breaker is OPEN for a given service."""
