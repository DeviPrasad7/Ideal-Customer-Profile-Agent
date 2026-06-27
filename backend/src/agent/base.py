from typing import Any, Dict, Protocol, TypedDict

from .state import GraphState


class AgentConfig(TypedDict, total=False):
    """Configuration passed to agents."""
    icp: Dict[str, Any]
    personas: Dict[str, Any]
    # Add other config fields as needed


class AgentNode(Protocol):
    """Formal interface for all agents in the platform."""

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        """
        Execute the agent's core logic.
        
        Args:
            state (GraphState): The current state of the workflow.
            
        Returns:
            Dict[str, Any]: The updates to apply to the state.
        """
        ...


class SafeAgentWrapper:
    """
    Wraps an AgentNode with a global try...except block to gracefully handle 
    unexpected exceptions without crashing the LangGraph workflow.
    """
    def __init__(self, agent: AgentNode, agent_name: str):
        self.agent = agent
        self.agent_name = agent_name

    async def __call__(self, state: GraphState) -> Dict[str, Any]:
        try:
            return await self.agent(state)
        except Exception as e:
            # LangGraph uses special exceptions for control flow (like interrupts). Let them propagate.
            if e.__class__.__name__ in ["GraphInterrupt", "NodeInterrupt"]:
                raise e
                
            from core.logging import logger
            logger.error(f"Agent {self.agent_name} failed with unhandled exception", error=str(e), agent=self.agent_name)
            
            # Increment retry count
            retry_counts = state.get("retry_counts", {})
            current_retries = retry_counts.get(self.agent_name, 0)
            
            return {
                "executed_agents": [self.agent_name],
                "errors": [f"{self.agent_name}: {str(e)}"],
                "retry_counts": {self.agent_name: current_retries + 1}
            }
