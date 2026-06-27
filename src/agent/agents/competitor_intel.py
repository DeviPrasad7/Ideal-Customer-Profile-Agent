from typing import Any
from ..state import GraphState
from ..utils import Toolbox
from services.memory_service import MemoryService
from ..base import AgentNode
from ..registry import register_agent

@register_agent("competitor_intel_node", description="Finds competitor info (Optional, requires tech stack)")
class CompetitorIntelNode(AgentNode):
    def __init__(self, toolbox: Toolbox, memory: MemoryService, config: dict):
        self.toolbox = toolbox
        self.memory = memory
        self.config = config

    async def __call__(self, state: GraphState) -> dict[str, Any]:
        tech_stack = state.get("data", {}).get("tech_stack", [])
        intel = {}
        for tech in tech_stack:
            name = tech.get("technology")
            comp_mapping = self.toolbox.get_competitor_info(name)
            if comp_mapping:
                intel[name] = comp_mapping.dict()
                
        if intel:
            return {
                "executed_agents": ["competitor_intel_node"],
                "data": {"competitor_intel": intel}
            }
        return {"executed_agents": ["competitor_intel_node"]}
