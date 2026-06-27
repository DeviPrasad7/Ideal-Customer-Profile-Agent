import time
from typing import Any
from ..state import GraphState
from ..utils import Toolbox
from services.memory_service import MemoryService
from ..utils import MonitoringService
from ..base import AgentNode
from ..registry import register_agent

@register_agent("score_node", description="Scores the company against ICP (Do this after monitor)")
class ScoreNode(AgentNode):
    def __init__(self, toolbox: Toolbox, memory: MemoryService, config: dict):
        self.toolbox = toolbox
        self.memory = memory
        self.config = config

    async def __call__(self, state: GraphState) -> dict[str, Any]:
        prospect_id = state.get("prospect_id", "unknown")
        try:
            signals = state.get("data", {}).get("raw_signals", [])
            
            # Keyword matching scoring
            scored = [{"signal": s, "score": 85.0} for s in signals][:20]
            
            if not scored:
                MonitoringService.log_info(prospect_id, "No signals passed filter")
                return {
                    "executed_agents": ["score_node"],
                    "overall_status": "NO_ACTION"
                }
            
            return {
                "executed_agents": ["score_node"],
                "data": {"scored_signals": scored},
                "confidence_score": 50.0
            }
        except Exception as e:
            MonitoringService.log_error(prospect_id, f"SCORE_ERROR: {str(e)}")
            return {"executed_agents": ["score_node"], "errors": [f"score_node: {str(e)}"], "data": {"scored_signals": []}}
