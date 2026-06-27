"""
Circuit Breaker implementation for external service call protection.

Extracted from agent/utils.py to honour Single Responsibility Principle.
Import this where circuit-breaking logic is needed:

    from core.circuit_breaker import CircuitBreaker, CircuitBreakerState

NOTE: This is an in-memory circuit breaker suitable for single-worker
deployments. In a multi-worker cluster (e.g. Cloud Run with --workers > 1),
replace the in-memory state dictionaries with a Redis-backed store so that
all workers share the same failure counts.
"""

import time
from enum import Enum


class CircuitBreakerState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """Emulates a circuit breaker for external dependencies.

    Usage:
        breaker = CircuitBreaker(failure_threshold=3, reset_timeout_sec=30)
        state = breaker.check_health("openai_api")
        if state == CircuitBreakerState.OPEN:
            raise ServiceUnavailableError("openai_api is temporarily unavailable")
        try:
            result = await call_external()
            breaker.record_success("openai_api")
        except Exception:
            breaker.record_failure("openai_api")
            raise
    """

    def __init__(self, failure_threshold: int = 3, reset_timeout_sec: int = 30):
        self.service_states: dict[str, CircuitBreakerState] = {}
        self.failure_counts: dict[str, int] = {}
        self.last_failure_times: dict[str, float] = {}
        self.failure_threshold = failure_threshold
        self.reset_timeout_sec = reset_timeout_sec

    def check_health(self, service_name: str) -> CircuitBreakerState:
        state = self.service_states.get(service_name, CircuitBreakerState.CLOSED)
        if state == CircuitBreakerState.OPEN:
            last_time = self.last_failure_times.get(service_name, 0)
            if time.time() - last_time > self.reset_timeout_sec:
                self.service_states[service_name] = CircuitBreakerState.HALF_OPEN
                return CircuitBreakerState.HALF_OPEN
            return CircuitBreakerState.OPEN
        return state

    def record_success(self, service_name: str) -> None:
        self.failure_counts[service_name] = 0
        self.service_states[service_name] = CircuitBreakerState.CLOSED

    def record_failure(self, service_name: str) -> None:
        count = self.failure_counts.get(service_name, 0) + 1
        self.failure_counts[service_name] = count
        self.last_failure_times[service_name] = time.time()

        state = self.service_states.get(service_name, CircuitBreakerState.CLOSED)

        if state == CircuitBreakerState.HALF_OPEN or count >= self.failure_threshold:
            self.service_states[service_name] = CircuitBreakerState.OPEN
