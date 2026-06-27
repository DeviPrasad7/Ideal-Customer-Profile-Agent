import time
from typing import Any
from ..state import GraphState
from ..utils import Toolbox, CircuitBreakerState, MonitoringService
from services.memory_service import MemoryService
from ..base import AgentNode
from ..registry import register_agent

@register_agent("monitor_node", description="Fetches trigger events and discovers new companies")
class MonitorNode(AgentNode):
    def __init__(self, toolbox: Toolbox, memory: MemoryService, config: dict):
        self.toolbox = toolbox
        self.memory = memory
        self.config = config

    async def __call__(self, state: GraphState) -> dict[str, Any]:
        prospect_id = state.get("prospect_id", "unknown")
        try:
            cb_state = self.toolbox.circuit_breaker.check_health("RSS_SOURCE")
            if cb_state == CircuitBreakerState.OPEN:
                MonitoringService.log_warning(prospect_id, "RSS source unavailable, skipping")
                return {"executed_agents": ["monitor_node"]}
                
            # We simulate reading an external feed for triggers
            website_url = state.get("data", {}).get("website_url")
            if website_url:
                page = await self.toolbox.fetch_webpage(website_url, 10)
            
            event_hash = f"event_{prospect_id}"
            await self.memory.mark_event_processed(event_hash, prospect_id)
            self.toolbox.circuit_breaker.record_success("RSS_SOURCE")
            
            return {
                "executed_agents": ["monitor_node"],
                "data": {"raw_signals": [{"source": "RSS", "timestamp": time.time(), "content": "Trigger event detected"}]}
            }
        except Exception as e:
            self.toolbox.circuit_breaker.record_failure("RSS_SOURCE")
            MonitoringService.log_error(prospect_id, f"MONITOR_ERROR: {str(e)}")
            return {"executed_agents": ["monitor_node"], "errors": [f"monitor_node: {str(e)}"]}
