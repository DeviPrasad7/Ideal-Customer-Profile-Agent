"""
Centralized structured logging configuration using structlog.

All modules should import ``logger`` from here:

    from core.logging import logger

The ``setup_logging`` shim is kept for backward compatibility with the
``main.py`` startup call, but it is a no-op now – structlog is configured
at module import time.
"""

import logging
import sys
import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """No-op shim kept for backward compatibility. Structlog is configured below."""
    # Silence noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.basicConfig(
        level=log_level,
        stream=sys.stdout,
        format="%(message)s",
    )


# ---------------------------------------------------------------------------
# Structlog configuration (single source of truth)
# ---------------------------------------------------------------------------
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Module-level logger – import this in every module that needs logging
logger = structlog.get_logger("icp_agent")
