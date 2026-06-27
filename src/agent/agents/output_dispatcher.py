from typing import Any
from ..state import GraphState
from ..utils import Toolbox
from services.memory_service import MemoryService
from ..utils import MonitoringService
from ..base import AgentNode
from ..registry import register_agent

@register_agent("output_dispatcher_node", description="Sends final data (Do this after HITL APPROVED)")
class OutputDispatcherNode(AgentNode):
    def __init__(self, toolbox: Toolbox, memory: MemoryService, config: dict):
        self.toolbox = toolbox
        self.memory = memory
        self.config = config

    async def __call__(self, state: GraphState) -> dict[str, Any]:
        prospect_id = state.get("prospect_id", "unknown")
        try:
            export_record = {"prospect_id": prospect_id, "summary": state.get("data", {}).get("summary_object"), "status": state.get("overall_status")}
            
            event_hash = f"output_{prospect_id}"
            await self.memory.mark_event_processed(event_hash, prospect_id)
            await self.memory.save_prospect_state(prospect_id, state)
            
            self.toolbox.emit_event("PROSPECT_COMPLETED", export_record)
            self.toolbox.send_webhook("http://example.com/webhook", export_record)
            
            MonitoringService.log_success(prospect_id, "Execution completed successfully.")
            return {
                "executed_agents": ["output_dispatcher_node"]
            }
        except Exception as e:
            MonitoringService.log_error(prospect_id, "OUTPUT_FAILED")
            await self.memory.rollback_prospect_state(prospect_id)
            return {"executed_agents": ["output_dispatcher_node"], "overall_status": "FAILED", "errors": [f"output_dispatcher_node: {str(e)}"]}
