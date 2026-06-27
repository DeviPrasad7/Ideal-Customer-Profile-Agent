import time
from typing import Any
from ..state import GraphState
from ..utils import Toolbox, CircuitBreakerState
from services.memory_service import MemoryService
from ..utils import MonitoringService
from ..base import AgentNode
from ..registry import register_agent

@register_agent("summarizer_node", description="Creates final summary (Do this when all data is gathered)")
class SummarizerNode(AgentNode):
    def __init__(self, toolbox: Toolbox, memory: MemoryService, config: dict):
        self.toolbox = toolbox
        self.memory = memory
        self.config = config

    async def __call__(self, state: GraphState) -> dict[str, Any]:
        prospect_id = state.get("prospect_id", "unknown")
        try:
            cb_state = self.toolbox.circuit_breaker.check_health("LLM_API")
            fallback_summary = '{"overview": "Fallback", "strengths": "Unknown", "risks": "Unknown", "recommendation": "Review manually"}'
            if cb_state == CircuitBreakerState.OPEN:
                MonitoringService.log_warning(prospect_id, "LLM circuit open, using fallback")
                return {
                    "executed_agents": ["summarizer_node"],
                    "data": {"summary_object": fallback_summary}
                }
            
            firmographics = state.get("data", {}).get("firmographics", {})
            prompt = f"Summarize this prospect: {firmographics}. Output JSON."
            summary = await self.toolbox.generate_text(prompt, fallback_summary)
            
            if summary == fallback_summary:
                self.toolbox.circuit_breaker.record_failure("LLM_API")
                MonitoringService.log_error(prospect_id, "LLM unavailable, using fallback")
            else:
                self.toolbox.circuit_breaker.record_success("LLM_API")
                
            return {
                "executed_agents": ["summarizer_node"],
                "data": {"summary_object": summary}
            }
        except Exception as e:
            self.toolbox.circuit_breaker.record_failure("LLM_API")
            return {
                "executed_agents": ["summarizer_node"],
                "data": {"summary_object": '{"overview": "Fallback", "strengths": "Unknown", "risks": "Unknown", "recommendation": "Review manually"}'},
                "errors": [f"summarizer_node: {str(e)}"]
            }
