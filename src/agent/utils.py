from enum import Enum
from typing import Any

# ==============================================================================
# Domain Models (DTOs)
# ==============================================================================
class AgentStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    AWAITING_HUMAN = "AWAITING_HUMAN"

class ProspectStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    NO_ACTION = "NO_ACTION"
    FORCE_HITL = "FORCE_HITL"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    TIMEOUT = "TIMEOUT"

# ==============================================================================
# Emulated Toolbox and CircuitBreaker
# ==============================================================================
class CircuitBreakerState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    """Emulates a circuit breaker for external dependencies."""
    def __init__(self):
        self.service_states: dict[str, CircuitBreakerState] = {}
        
    def check_health(self, service_name: str) -> CircuitBreakerState:
        # In a real implementation, this would check failures/timeouts.
        return self.service_states.get(service_name, CircuitBreakerState.CLOSED)
        
    def record_success(self, service_name: str) -> None:
        self.service_states[service_name] = CircuitBreakerState.CLOSED
        
    def record_failure(self, service_name: str) -> None:
        self.service_states[service_name] = CircuitBreakerState.OPEN

class Toolbox:
    """Facade for external tool interactions."""
    def __init__(self):
        self.circuit_breaker = CircuitBreaker()
        
    def emit_event(self, event_type: str, payload: Any) -> None:
        print(f"[Toolbox] Emitting event: {event_type} - {payload}")

    def send_webhook(self, url: str, payload: Any) -> None:
        print(f"[Toolbox] Sending webhook to {url}")
        
    def generate_text(self, prompt: str, fallback: str) -> str:
        # Mock LLM generation
        return fallback

# ==============================================================================
# Emulated MonitoringService
# ==============================================================================
class MonitoringService:
    @staticmethod
    def log_success(prospect_id: str, message: str = ""):
        print(f"[Monitor] SUCCESS [{prospect_id}]: {message}")

    @staticmethod
    def log_error(prospect_id: str, error_code: str):
        print(f"[Monitor] ERROR [{prospect_id}]: {error_code}")
        
    @staticmethod
    def log_warning(prospect_id: str, message: str):
        print(f"[Monitor] WARNING [{prospect_id}]: {message}")

    @staticmethod
    def log_info(prospect_id: str, message: str):
        print(f"[Monitor] INFO [{prospect_id}]: {message}")
