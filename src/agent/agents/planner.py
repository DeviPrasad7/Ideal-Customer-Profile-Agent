import json
from typing import Any
from ..state import GraphState
from ..utils import Toolbox
from services.memory_service import MemoryService
from ..utils import MonitoringService
from ..base import AgentNode
from ..registry import AgentRegistry

class PlannerNode(AgentNode):
    def __init__(self, toolbox: Toolbox, memory: MemoryService, config: dict, registry: AgentRegistry):
        self.toolbox = toolbox
        self.memory = memory
        self.config = config
        self.registry = registry

    async def __call__(self, state: GraphState) -> dict[str, Any]:
        prospect_id = state.get("prospect_id", "unknown")
        executed_agents = state.get("executed_agents", [])
        overall_status = state.get("overall_status", "PENDING")
        
        if overall_status in ["NO_ACTION", "REJECTED", "TIMEOUT", "APPROVED", "COMPLETED"]:
            return {"next_node": "__end__"}
            
        available_agents = self.registry.list_agents()
        
        agent_descriptions = []
        for name in available_agents:
            desc = self.registry.get_description(name)
            agent_descriptions.append(f"- {name}: {desc}")
            
        agents_str = "\n".join(agent_descriptions)
        
        prompt = f"""
You are the Planner Agent for a B2B SaaS Customer Discovery pipeline.
Your job is to decide the next agent to execute based on the current state.

Available Agents:
{agents_str}

Current State Summary:
- Executed Agents: {executed_agents}
- Overall Status: {overall_status}
- Has Company Name: {bool(state.get('data', {}).get('company_name'))}
- Has Summary: {bool(state.get('data', {}).get('summary_object'))}

Output ONLY a JSON object with a single key "next_node" containing the exact name of the next agent to run. If the workflow is complete, output "__end__".
"""
        
        fallback = '{"next_node": "__end__"}'
        
        try:
            response = await self.toolbox.generate_text(prompt, fallback)
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                next_node = data.get("next_node", "__end__")
            else:
                next_node = "__end__"
                
            if next_node not in available_agents and next_node != "__end__":
                next_node = "__end__"
                
            return {"executed_agents": ["planner_node"], "next_node": next_node}
        except Exception as e:
            MonitoringService.log_error(prospect_id, f"PLANNER_ERROR: {str(e)}")
            return {"next_node": "hitl_gateway_node"} # Fallback to human if planner fails
